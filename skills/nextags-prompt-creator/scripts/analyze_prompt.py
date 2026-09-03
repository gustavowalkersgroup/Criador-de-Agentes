#!/usr/bin/env python3
"""
analyze_prompt.py — Audita um prompt de agente de atendimento NexTags
contra as Regras Absolutas da plataforma.

Saída: JSON estruturado com findings (compacto e fácil de o Claude consumir).
Cada finding tem severity = "block" (quebra a plataforma → reprovar) ou
"warn" (estilo/recomendação → avisar, não reprova).

Checks de roteamento/handoff canônico (references/campos_canonicos.md):
  block — ia_grava_campo_de_roteamento (setor_agente / tipo_setor)
  block — prioridade_fora_do_enum (Seleção única: baixa|media|alta)
  warn  — motivo_fora_do_enum (enum §2.1; sugere o canônico)
  warn  — trio_handoff_incompleto (motivo + send_flow sem prioridade/resumo)
  warn  — send_flow_antes_de_set_field (send_flow é sempre a última action)
  warn  — avisos_ativos (bloco 📣 AVISOS ATIVOS ausente ou sem marcadores)
  warn  — nota_editor_longa (`> 🔧 NOTA PARA EDITORES:` acima de 220 chars)

ATENÇÃO: este arquivo tem 2 cópias byte-a-byte idênticas
(nextags-prompt-creator/scripts e nextags-prompt-fixer/scripts). Alterou uma,
copie para a outra — `test_analyzer_copies_in_sync` reprova se divergirem.

Uso:
    python analyze_prompt.py <path_to_prompt.md> [--output findings.json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ----------------------------------------------------------------------
# Configuração das regras
# ----------------------------------------------------------------------

# As 8 ações canônicas da plataforma (schema oficial). Qualquer "action" fora
# desta lista NÃO existe na plataforma → BLOCK (a ação simplesmente não roda).
CANONICAL_ACTIONS = {
    "add_tag", "remove_tag", "set_field_value", "unset_field_value",
    "send_flow", "transfer_conversation_to", "assign_conversation",
    "unassign_conversation",
}

# Ações de transferência que NÃO são o padrão recomendado (send_flow é), mas
# também NÃO são proibidas — decisão do cliente:
#   - transfer_conversation_to = FALLBACK quando não há flow configurado
#   - assign_conversation       = caso especial raro (atendente específico)
#   - unassign_conversation     = caso raro
# Detectá-las gera AVISO (warn), nunca bloqueio.
ADVISORY_TRANSFER_ACTIONS = [
    "transfer_conversation_to",
    "assign_conversation",
    "unassign_conversation",
]

# ---- Campos canônicos de roteamento e handoff -------------------------
# Fonte: references/campos_canonicos.md §2 e §3.
#
# Campos de ROTEAMENTO: `setor_agente` é gravado pelo ROTEADOR e `tipo_setor`
# pelo REVALIDADOR. Agente de atendimento NUNCA grava neles — o fluxo de entrada
# relê esses campos a cada mensagem, então a IA gravando ali se re-roteia
# (loop de transferência em produção, caso Veuske). `agente_setor` é o nome
# legado/invertido do mesmo campo.
ROUTING_FIELDS = {"setor_agente", "tipo_setor", "agente_setor"}

# Enum canônico de `motivo_transferencia` (campos_canonicos.md §2.1).
CANONICAL_MOTIVO_TRANSFERENCIA = {
    # Parcerias
    "ugc", "colaboracao", "influencer", "revenda", "atacado",
    # Comercial
    "vendas", "carrinho",
    # SAC (duvida = catch-all)
    "rastreio", "devolucao", "troca", "duvida",
}

# Valores legados/próximos → canônico sugerido no finding.
LEGACY_MOTIVO_MAP = {
    "duvidas": "duvida",
    "duvida_geral": "duvida",
    "sac_geral": "duvida",
    "sac": "duvida",
    "cancelamento": "duvida",
    "defeito": "duvida",
    "garantia": "duvida",
    "pagamento": "duvida",
    "parceria": "colaboracao",
    "parcerias": "colaboracao",
    "collab": "colaboracao",
    "influenciador": "influencer",
    "b2b": "atacado",
    "revender": "revenda",
    "lojista": "revenda",
    "rastreamento": "rastreio",
    "entrega": "rastreio",
    "comercial": "vendas",
    "checkout": "carrinho",
}

# `prioridade_pipeline` é Seleção única na conta modelo: valor fora da lista é
# rejeitado pela plataforma (o card fica sem prioridade) → block.
CANONICAL_PRIORIDADE_PIPELINE = {"baixa", "media", "alta"}

# Trio obrigatório antes de todo send_flow de transferência.
HANDOFF_TRIO = ("motivo_transferencia", "prioridade_pipeline", "resumo_pipeline")

# Marcador de nota para editores (SPEC §5.2). Linha começando com ele NUNCA é
# meta-doc (whitelist), mas passa a warn se ficar longa demais.
EDITOR_NOTE_RE = re.compile(r"^\s*>\s*(?:🔧\s*)?NOTA\s+PARA\s+EDITORES\s*:", re.IGNORECASE)
EDITOR_NOTE_MAX_LEN = 220

# Marcadores que indicam que um bloco é EXEMPLO NEGATIVO intencional
# (ex: o prompt está mostrando o que NÃO fazer). Quando precedem um
# bloco JSON em até ~5 linhas, ignoramos as violações dele.
NEGATIVE_EXAMPLE_MARKERS = [
    "❌", "🚫", "proibido", "nunca usar", "errado", "incorreto",
    "não usar", "nao usar", "don't", "wrong", "bad example",
    "exemplo errado", "exemplo ruim",
    # Padrões de checklist / meta-discussão sobre as regras
    "(erro", "error:", "erro —", "erro -",
    "está usando", "esta usando", "is using",
    "verificar", "validar se",
    "substituir por", "replace with",
]

# Seções de instrução obrigatórias que um prompt de agente NexTags deve ter.
# Cada seção tem uma lista de PADRÕES regex (case-insensitive, multiline);
# se qualquer um casar no conteúdo, a seção é considerada presente.
# "severity" indica se a ausência reprova (block) ou só avisa (warn).
REQUIRED_SECTIONS = {
    "bloco_oficial_nextags": {
        "label": "Bloco oficial NexTags (instruções canônicas de saída JSON)",
        "severity": "warn",
        "patterns": [
            r"deve\s+sempre\s+retornar\s+respostas?\s+em\s+json\s+v[áa]lido\s+seguindo\s+o\s+padr[ãa]o\s+da\s+messenger\s+messaging\s+platform",
            r"seguindo\s+o\s+(padr[ãa]o|esquema)\s+da\s+messenger\s+messaging\s+platform",
        ],
    },
    "anti_alucinacao": {
        "label": "Regras anti-alucinação",
        "severity": "block",
        "patterns": [
            r"anti[\s-]?aluc",
            # "não/nunca/jamais (pode/deve)? inventar" — \binvent evita casar "reinventar".
            r"(nunca|jamais|n[ãa]o)\s+(?:(?:pode|deve|podemos|devemos|posso)\s+)?\binvent",
            r"(nunca|jamais|n[ãa]o)\s+(?:(?:pode|deve|podemos|devemos)\s+)?(assum|chut|adivinh|prometa|prometer|garant)",
            # "É PROIBIDO inventar/prometer/garantir..."
            r"proib\w+[^.\n]{0,40}(invent|prometer|garant|chut|adivinh|confirmar?\s+sem)",
            r"(nunca|jamais|n[ãa]o)\s+confirmar?\s+(sem|aprova)",
            # proxies fortes de disciplina anti-alucinação (consultar a fonte em vez de inventar)
            r"sempre\s+consult\w+",
            r"fonte\s+de\s+verdade",
            r"never\s+(invent|make\s+up|hallucinat)",
        ],
    },
    # Decisão do cliente (Tema E): o padrão NÃO é negar ser IA — é OCULTAR O
    # STACK (não citar Shopify/MCP/flow_id/"FAQ"). Negar ser IA é opcional.
    # A seção é considerada presente se houver instrução de ocultar stack
    # OU de não revelar ser IA.
    "ocultar_stack": {
        "label": "Ocultar stack / não expor sistemas internos (Shopify, MCP, flow_id, FAQ)",
        "severity": "warn",
        "patterns": [
            # ocultar stack / não citar sistemas
            r"(nunca|jamais|n[ãa]o)\s+(mencion|cit|exp|revel|fal).{0,60}(shopify|mcp|n8n|api|flow_id|fluxo|ferramenta|tool|sistema|faq|base\s+de\s+conhecimento|documento)",
            r"(consult|busc).{0,30}(em\s+sil[êe]ncio|sem\s+(dizer|mencionar))",
            r"como\s+se\s+(simplesmente\s+)?soubesse",
            # negação de IA (opcional, mas também satisfaz)
            r"(nunca|jamais|n[ãa]o)\s+(revel|diga|fale|conte|admit).{0,40}\b(ia|i\.a\.|intelig[êe]ncia\s+artificial|bot|rob[ôo]|chatbot)\b",
            r"voc[êe]\s+[ée]\s+humana?",
            r"never\s+(reveal|say|admit|disclose|mention).{0,40}\b(ai|tool|system|backend)\b",
        ],
    },
    "json_obrigatorio": {
        "label": "Saída em JSON (obrigatória quando o agente AGE)",
        # severity é resolvida dinamicamente: block se o prompt usa actions,
        # warn se for agente puramente conversacional (texto é aceitável).
        "severity": "dynamic_json",
        "patterns": [
            r"(somente|apenas|sempre)\s+(em\s+)?json",
            r"json\s+v[áa]lido",
            r"retornar?\s+json",
            r"responder?\s+em\s+json",
            r"sem\s+texto\s+(antes|depois|fora)",
            r"toda\s+resposta\s+(sua\s+)?(é|deve\s+ser|e)\s+.{0,20}\bjson\b",
            r"obrigatori(o|a|amente).{0,15}\bjson\b",
            r"formato\s+de\s+sa[íi]da[\s\S]{0,100}\bjson\b",
            r"json\s+only|valid\s+json",
        ],
    },
    "send_flow_transferencia": {
        "label": "Transferência para humano (preferência: send_flow)",
        "severity": "block",
        "patterns": [
            r"send_flow",
            r"fluxo\s+de\s+transfer[êe]ncia",
            r"disparar?\s+(o\s+)?fluxo",
            r"transfer\s+flow",
            # intenção de transferência por QUALQUER mecanismo (mesmo "errado")
            # conta como presente — o "use send_flow" é recomendação à parte.
            r"transfer(ir|e|[êe]ncia)\b[^.\n]{0,40}(humano|atendente|equipe|time|setor|suporte)",
            r"encaminh\w+[^.\n]{0,40}(humano|atendente|equipe|time|setor)",
            r"(falar|conversar)\s+com\s+(um[ a]?\s+)?(atendente|humano|pessoa|consultor)",
            r"atendimento\s+humano",
            r"transfer_conversation_to|assign_conversation|connect_user_to_human",
        ],
    },
    "texto_padrao": {
        "label": "Texto simples como padrão de resposta",
        "severity": "warn",
        "patterns": [
            r"texto\s+simples",
            r"texto\s+(como\s+|[ée]\s+o\s+)?padr[ãa]o",
            r"padr[ãa]o\s+[ée]\s+texto",
            r"plain\s+text|default\s+text",
        ],
    },
    "fora_de_escopo": {
        "label": "Manter-se no escopo / não sair do contexto",
        "severity": "warn",
        "patterns": [
            r"fora\s+d[oa]\s+(escopo|contexto)",
            r"(sair|saia)\s+d[oa]\s+(escopo|contexto)",
            r"(manter|mantenha)[\s-]se\s+n[oa]\s+(escopo|contexto)",
            r"redirec(ionar|ione)",
            r"temas?\s+alheios?",
            r"fora\s+do\s+que\s+(posso|consigo)",
            r"out\s+of\s+scope",
        ],
    },
}


# ----------------------------------------------------------------------
# Parsing de blocos de código
# ----------------------------------------------------------------------

CODE_FENCE_RE = re.compile(r"^\s*```(\w*)\s*$")


def find_json_blocks(content: str) -> list[dict]:
    """Encontra trechos que parecem JSON da plataforma (objetos com
    "messages"/"actions"/etc.), tentando parsear progressivamente."""
    blocks: list[dict] = []
    lines = content.split("\n")
    n = len(lines)
    used_lines: set[int] = set()

    PLATFORM_KEYS = ('"messages"', '"actions"', '"action"', '"message"',
                     '"attachment"', '"template_type"', '"flow_id"',
                     '"tag_name"', '"field_name"')

    for start_idx in range(n):
        if start_idx in used_lines:
            continue
        line = lines[start_idx]
        stripped = line.lstrip()
        if not (stripped.startswith("{") or stripped.startswith("[")):
            continue

        accumulated = []
        for end_idx in range(start_idx, min(n, start_idx + 200)):
            accumulated.append(lines[end_idx])
            candidate = "\n".join(accumulated)
            opens = candidate.count("{") + candidate.count("[")
            closes = candidate.count("}") + candidate.count("]")
            if closes < opens or closes == 0:
                continue
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue

            text_check = candidate
            if not any(k in text_check for k in PLATFORM_KEYS):
                break

            is_marked = False
            if start_idx > 0:
                prev_line = lines[start_idx - 1].strip()
                if prev_line.endswith("```json") or prev_line == "```json":
                    is_marked = True

            ctx_lines = lines[max(0, start_idx - 5):start_idx]
            preceding = "\n".join(ctx_lines).lower()

            blocks.append({
                "start_line": start_idx + 1,
                "end_line": end_idx + 1,
                "text": candidate.strip(),
                "is_marked_json": is_marked,
                "preceding_context": preceding,
                "_parsed": parsed,
            })
            for u in range(start_idx, end_idx + 1):
                used_lines.add(u)
            break

    return blocks


def is_negative_example(block: dict) -> bool:
    ctx = block["preceding_context"]
    return any(marker in ctx for marker in NEGATIVE_EXAMPLE_MARKERS)


# ----------------------------------------------------------------------
# Validações dentro de um bloco JSON
# ----------------------------------------------------------------------

def find_actions_in_text(text: str) -> dict:
    """Acha ações no JSON cru (funciona mesmo com JSON inválido).
    Retorna {'advisory': [...], 'nonexistent': [...]}.
    - advisory: transfer_conversation_to / assign_conversation / unassign_conversation
      (válidas, mas não o padrão → warn).
    - nonexistent: qualquer "action":"X" com X fora das 8 canônicas → block."""
    advisory = []
    nonexistent = []
    for m in re.finditer(r'["\']action["\']\s*:\s*["\']([a-zA-Z_][\w]*)["\']', text):
        name = m.group(1)
        if name in ADVISORY_TRANSFER_ACTIONS:
            if name not in advisory:
                advisory.append(name)
        elif name not in CANONICAL_ACTIONS:
            if name not in nonexistent:
                nonexistent.append(name)
    return {"advisory": advisory, "nonexistent": nonexistent}


# Limite de título de botão: o passo "Filtro JSON" do fluxo (reparador de JSON)
# troca qualquer title com mais de 20 caracteres por "Comprar agora", sem erro.
TITULO_BOTAO_MAX = 20


def walk_json(obj, path: str = "$"):
    yield path, obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_json(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            yield from walk_json(item, f"{path}[{idx}]")


def check_buttons_misuse(parsed) -> list[dict]:
    """Valida botões. web_url precisa de url; postback precisa de payload
    (postback é PERMITIDO — decisão do cliente). Também avisa quando há mais
    de 1 botão web_url no mesmo template (restrição do WhatsApp p/ link) e
    bloqueia título com mais de 20 caracteres: o reparador de JSON do fluxo
    troca esse título por 'Comprar agora' sem avisar ninguém."""
    issues = []
    for path, node in walk_json(parsed):
        if isinstance(node, dict) and node.get("template_type") == "button":
            buttons = node.get("buttons") or []
            if not buttons:
                issues.append({
                    "path": path,
                    "problem": "template button sem botões",
                    "severity": "block",
                    "title_text": node.get("text", ""),
                })
                continue
            web_url_count = 0
            for idx, btn in enumerate(buttons):
                if not isinstance(btn, dict):
                    continue
                title = btn.get("title")
                if isinstance(title, str) and len(title) > TITULO_BOTAO_MAX:
                    issues.append({
                        "path": f"{path}.buttons[{idx}]",
                        "problem": (
                            f"título de botão com {len(title)} caracteres (limite {TITULO_BOTAO_MAX}) — "
                            "o reparador de JSON do fluxo substitui SILENCIOSAMENTE por 'Comprar agora'"
                        ),
                        "severity": "block",
                        "title": title,
                    })
                btn_type = btn.get("type")
                if btn_type == "web_url":
                    web_url_count += 1
                    if not btn.get("url"):
                        issues.append({
                            "path": f"{path}.buttons[{idx}]",
                            "problem": "botão web_url sem `url`",
                            "severity": "block",
                            "title": btn.get("title", ""),
                        })
                elif btn_type == "postback":
                    if not btn.get("payload"):
                        issues.append({
                            "path": f"{path}.buttons[{idx}]",
                            "problem": "botão postback sem `payload` (flow_id)",
                            "severity": "block",
                            "title": btn.get("title", ""),
                        })
                else:
                    issues.append({
                        "path": f"{path}.buttons[{idx}]",
                        "problem": f"tipo de botão inválido: '{btn_type}' (use web_url ou postback)",
                        "severity": "block",
                        "title": btn.get("title", ""),
                    })
            if web_url_count > 1:
                issues.append({
                    "path": f"{path}.buttons",
                    "problem": f"{web_url_count} botões web_url no mesmo template — WhatsApp permite só 1 botão de LINK por mensagem",
                    "severity": "warn",
                })
    return issues


def check_carousel_misuse(parsed) -> list[dict]:
    """Carrosséis (template_type=generic) precisam de 2+ elementos."""
    issues = []
    for path, node in walk_json(parsed):
        if isinstance(node, dict) and node.get("template_type") == "generic":
            elements = node.get("elements") or []
            if len(elements) < 2:
                issues.append({
                    "path": path,
                    "problem": "carrossel com menos de 2 elementos",
                    "severity": "block",
                    "element_count": len(elements),
                })
    return issues


# Formatos de imagem permitidos pela plataforma NexTags (só JPEG/PNG nos canais).
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
FORBIDDEN_IMAGE_EXTENSIONS = {".webp", ".avif", ".svg", ".gif", ".bmp",
                              ".tiff", ".ico", ".heic", ".heif"}


def check_type_inside_payload(parsed) -> list[dict]:
    """`type` deve ficar FORA de `payload` (mesmo nível). Type dentro do payload
    é o erro mais comum — o middleware o ignora e a imagem não vai. BLOCK."""
    issues = []
    for path, node in walk_json(parsed):
        if not isinstance(node, dict) or "attachment" not in node:
            continue
        att = node["attachment"]
        if not isinstance(att, dict):
            continue
        payload = att.get("payload")
        if isinstance(payload, dict) and "type" in payload and "type" not in att:
            issues.append({
                "path": f"{path}.attachment",
                "problem": "campo `type` dentro de `payload` — deve ficar FORA, no mesmo nível do payload",
                "severity": "block",
                "type_value": payload.get("type"),
            })
    return issues


def _image_url_status(url):
    """Retorna (status, motivo) — status em ok/forbidden/ambiguous/invalid."""
    if not isinstance(url, str) or not url.strip():
        return "invalid", "URL vazia"
    low = url.strip().lower()
    if not (low.startswith("http://") or low.startswith("https://")):
        return "invalid", "URL não-absoluta (sem http/https)"
    path = low.split("?", 1)[0].split("#", 1)[0]
    dot = path.rfind(".")
    if dot == -1:
        return "ambiguous", "URL sem extensão clara"
    ext = path[dot:]
    if ext in FORBIDDEN_IMAGE_EXTENSIONS:
        return "forbidden", f"formato proibido '{ext}' (NexTags só aceita JPEG/PNG)"
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return "ok", None
    return "ambiguous", f"extensão '{ext}' não-reconhecida"


def check_forbidden_image_formats(parsed) -> list[dict]:
    """URLs de imagem (image_url de carrossel, payload.url de attachment image)
    em formato não suportado. forbidden → block; ambiguous/invalid → warn.
    A plataforma só entrega JPEG/PNG nos canais (WhatsApp/Instagram/Messenger)."""
    issues = []
    for path, node in walk_json(parsed):
        if not isinstance(node, dict):
            continue
        if "image_url" in node and isinstance(node["image_url"], str):
            status, reason = _image_url_status(node["image_url"])
            if status in ("forbidden", "ambiguous", "invalid"):
                issues.append({
                    "path": f"{path}.image_url",
                    "url": node["image_url"][:120],
                    "status": status,
                    "reason": reason,
                    "severity": "block" if status == "forbidden" else "warn",
                })
        payload_dict = node.get("payload") if isinstance(node.get("payload"), dict) else None
        type_in_node = node.get("type")
        type_in_payload = payload_dict.get("type") if payload_dict else None
        if type_in_node == "image" or type_in_payload == "image":
            url = payload_dict.get("url") if payload_dict else None
            if isinstance(url, str):
                status, reason = _image_url_status(url)
                if status in ("forbidden", "ambiguous", "invalid"):
                    issues.append({
                        "path": f"{path}.payload.url",
                        "url": url[:120],
                        "status": status,
                        "reason": reason,
                        "severity": "block" if status == "forbidden" else "warn",
                    })
    return issues


# Markdown-PADRÃO que VAZA literal pro cliente (decisão do cliente):
# **negrito-duplo**, # título, [texto](url), bullets - /+, `code`, cercas.
# A marcação estilo WhatsApp (*negrito*, _itálico_, ~tachado~) NÃO entra aqui
# porque RENDERIZA na plataforma — é permitida.
MARKDOWN_PATTERNS = [
    (re.compile(r"\*\*[^*\n]+\*\*"), "negrito-duplo (**texto**)"),
    (re.compile(r"__[^_\n]+__"), "negrito-duplo (__texto__)"),
    (re.compile(r"\[[^\]\n]+\]\([^)\n]+\)"), "link markdown ([texto](url))"),
    (re.compile(r"^\s*#{1,6}\s+", re.MULTILINE), "título (# texto)"),
    (re.compile(r"`[^`\n]+`"), "código inline (`texto`)"),
    (re.compile(r"^\s*[-+]\s+", re.MULTILINE), "bullet de markdown (- item)"),
]


def check_markdown_in_text(parsed) -> list[dict]:
    """Procura markdown-PADRÃO dentro de campos 'text'/'subtitle'/'title'.
    WA-markup (*_~) é permitido e ignorado."""
    issues = []
    for path, node in walk_json(parsed):
        if not isinstance(node, dict):
            continue
        for field in ("text", "subtitle", "title"):
            value = node.get(field)
            if not isinstance(value, str):
                continue
            for pattern, label in MARKDOWN_PATTERNS:
                if pattern.search(value):
                    issues.append({
                        "path": f"{path}.{field}",
                        "markdown_type": label,
                        "severity": "block",
                        "snippet": value if len(value) <= 120 else value[:120] + "…",
                    })
                    break
    return issues


# Padrões de seções de meta-documentação que NÃO pertencem ao prompt.
FORBIDDEN_META_HEADER_PATTERNS = [
    (re.compile(r"^#{1,6}\s+.*\baudit(oria|or)\b", re.IGNORECASE | re.MULTILINE), "auditoria"),
    (re.compile(r"^#{1,6}\s+.*\bchangelog\b", re.IGNORECASE | re.MULTILINE), "changelog"),
    (re.compile(r"^#{1,6}\s+.*hist[óo]rico\s+de\s+(vers[ãa]o|mudan[çc]a)", re.IGNORECASE | re.MULTILINE), "historico_versao"),
    (re.compile(r"^#{1,6}\s+.*corre[çc][õo]es?\s+(v\d|da\s+v|aplicad)", re.IGNORECASE | re.MULTILINE), "correcoes_versao"),
    (re.compile(r"^#{1,6}\s+.*pend[êe]ncia(s)?(\s+(interna|humana|pra\s+confirmar|/\s*a\s+confirmar))?", re.IGNORECASE | re.MULTILINE), "pendencias"),
    (re.compile(r"^#{1,6}\s+.*\ba\s+confirmar\b", re.IGNORECASE | re.MULTILINE), "a_confirmar"),
    (re.compile(r"^#{1,6}\s+(?:[\d\.\s]+)?\bTODO(s)?\b", re.MULTILINE), "todo"),
    (re.compile(r"^#{1,6}\s+.*notas?\s+(internas?|pra\s+dev|t[ée]cnicas?)", re.IGNORECASE | re.MULTILINE), "notas_internas"),
    (re.compile(r"^#{1,6}\s+.*bug(s)?\s+(observad|conhecid|encontrad)", re.IGNORECASE | re.MULTILINE), "bugs_observados"),
    (re.compile(r"^#{1,6}\s+.*m[ée]tric(a|as)\s+do\s+prompt", re.IGNORECASE | re.MULTILINE), "metricas_prompt"),
    (re.compile(r"^#{2,6}\s+v\d+\.\d+\s*(\([^)]+\)|\s+\(|\s+→)", re.IGNORECASE | re.MULTILINE), "cabecalho_versionado"),
]

FORBIDDEN_HEADER_METADATA = [
    (re.compile(r"\*\*\s*vers[ãa]o\s*:?\s*\*\*", re.IGNORECASE), "versao_metadata"),
    (re.compile(r"\*\*\s*data\s*:?\s*\*\*", re.IGNORECASE), "data_metadata"),
    (re.compile(r"\*\*\s*respons[áa]vel\s*:?\s*\*\*", re.IGNORECASE), "responsavel_metadata"),
    (re.compile(r"\*\*\s*author(\(es\))?\s*:?\s*\*\*", re.IGNORECASE), "autor_metadata"),
]


def _line_containing(content: str, offset: int) -> str:
    """Linha inteira em que o offset cai (para whitelist por linha)."""
    start = content.rfind("\n", 0, offset) + 1
    end = content.find("\n", offset)
    if end == -1:
        end = len(content)
    return content[start:end]


def is_editor_note_line(line: str) -> bool:
    """Linha de nota para editores (`> 🔧 NOTA PARA EDITORES: …`) — whitelist:
    é conteúdo OPERACIONAL de manutenção, nunca meta-doc (SPEC §5.2)."""
    return bool(EDITOR_NOTE_RE.match(line))


def check_forbidden_meta_sections(content: str) -> list[dict]:
    issues = []
    for pattern, kind in FORBIDDEN_META_HEADER_PATTERNS:
        for m in pattern.finditer(content):
            if is_editor_note_line(_line_containing(content, m.start())):
                continue
            line_num = content[:m.start()].count("\n") + 1
            issues.append({"kind": kind, "line": line_num,
                           "severity": "warn",
                           "snippet": m.group(0).strip()[:120]})
    head = "\n".join(content.split("\n")[:10])
    for pattern, kind in FORBIDDEN_HEADER_METADATA:
        for m in pattern.finditer(head):
            if is_editor_note_line(_line_containing(head, m.start())):
                continue
            line_num = head[:m.start()].count("\n") + 1
            issues.append({"kind": kind, "line": line_num,
                           "severity": "warn",
                           "snippet": m.group(0).strip()[:120]})
            break
    return issues


def check_editor_notes(content: str) -> list[dict]:
    """Nota para editores longa demais → WARN. A nota é 1 linha curta de
    manutenção (até ~200 chars); nota que virou parágrafo é meta-doc disfarçada
    e gasta contexto em todo turno (SPEC §5.2)."""
    issues = []
    for idx, line in enumerate(content.split("\n"), 1):
        if not is_editor_note_line(line):
            continue
        stripped = line.strip()
        if len(stripped) > EDITOR_NOTE_MAX_LEN:
            issues.append({
                "kind": "nota_editor_longa",
                "line": idx,
                "length": len(stripped),
                "severity": "warn",
                "problem": (f"nota para editores com {len(stripped)} caracteres — o padrão "
                            f"é 1 linha de até ~200 (limite do check: {EDITOR_NOTE_MAX_LEN}). "
                            "Encurte: sem histórico, sem justificativa longa."),
                "snippet": stripped[:120] + "…",
            })
    return issues


# O bloco `📣 AVISOS ATIVOS` é obrigatório em todo prompt gerado (SPEC §5.1):
# é onde o cliente edita promoção/feriado/horário à mão. Ausência → warn.
AVISOS_ATIVOS_RE = re.compile(r"AVISOS\s+ATIVOS", re.IGNORECASE)
AVISOS_MARKERS_RE = re.compile(
    r"=+\s*IN[ÍI]CIO\s+DOS\s+AVISOS\s*=+[\s\S]{0,4000}?=+\s*FIM\s+DOS\s+AVISOS\s*=+",
    re.IGNORECASE)


def check_avisos_ativos(content: str) -> list[dict]:
    """Bloco AVISOS ATIVOS ausente → WARN (o creator é obrigado a gerar).
    Presente sem os marcadores `=== INÍCIO/FIM DOS AVISOS ===` → WARN separado:
    sem delimitador o cliente edita no lugar errado."""
    if not AVISOS_ATIVOS_RE.search(content):
        return [{
            "kind": "avisos_ativos_ausente",
            "severity": "warn",
            "problem": ("bloco `📣 AVISOS ATIVOS` ausente. É obrigatório em todo prompt "
                        "gerado (mesmo vazio): é o espaço que o cliente edita à mão para "
                        "promoção/feriado/horário. Formato em campos_canonicos.md §6.1."),
        }]
    if not AVISOS_MARKERS_RE.search(content):
        return [{
            "kind": "avisos_ativos_sem_marcadores",
            "severity": "warn",
            "problem": ("bloco AVISOS ATIVOS sem os marcadores `=== INÍCIO DOS AVISOS ===` "
                        "/ `=== FIM DOS AVISOS ===`. Sem delimitador explícito o cliente "
                        "edita fora do bloco e mexe em regra do prompt."),
        }]
    return []


GENERIC_PLACEHOLDER_PATTERNS = [
    (re.compile(r"\[(?:nome|primeiro\s*nome|sobrenome|cliente|usuario|usu[áa]rio|email|e-mail|telefone|cidade|estado|pa[íi]s|order_id|pedido|c[oó]digo[\s_]*do[\s_]*pedido|produto|valor|total|cep|endere[çc]o)\]", re.IGNORECASE), "[bracket]"),
    (re.compile(r"(?<!\{)\{[a-z_][a-z0-9_]{2,30}\}(?!\})"), "{single_brace}"),
    (re.compile(r"\$[a-zA-Z_][a-zA-Z0-9_]{2,30}\$"), "$dollar$"),
    (re.compile(r"<[A-Z_]{3,30}>"), "<SCREAMING>"),
]


def check_generic_placeholders(parsed) -> list[dict]:
    """Procura placeholders genéricos ([nome], {nome}, $first_name$, <NOME>)
    em campos visíveis. Campos `url` são excluídos (templates pro LLM)."""
    issues = []
    for path, node in walk_json(parsed):
        if not isinstance(node, dict):
            continue
        for field in ("text", "subtitle", "title"):
            value = node.get(field)
            if not isinstance(value, str):
                continue
            for pattern, label in GENERIC_PLACEHOLDER_PATTERNS:
                m = pattern.search(value)
                if m:
                    issues.append({
                        "path": f"{path}.{field}",
                        "placeholder_type": label,
                        "severity": "block",
                        "match": m.group(0),
                        "snippet": value if len(value) <= 120 else value[:120] + "…",
                    })
                    break
    return issues


# ----------------------------------------------------------------------
# Roteamento e handoff canônico (campos_canonicos.md §2 e §3)
# ----------------------------------------------------------------------

def _iter_action_objects(parsed):
    """Rende (path, dict) para todo objeto que parece uma action da plataforma."""
    for path, node in walk_json(parsed):
        if isinstance(node, dict) and isinstance(node.get("action"), str):
            yield path, node


def _field_name_of(node) -> str:
    field = node.get("field_name")
    return field.strip().lower() if isinstance(field, str) else ""


_PLACEHOLDER_VALUE_RE = re.compile(r"[<{]")


def _is_placeholder_value(value) -> bool:
    """`"<enum>"`, `"{motivo}"`, `"<baixa|media|alta>"` e vazio são gabaritos
    para o LLM preencher — não são valor de enum a validar."""
    if not isinstance(value, str) or not value.strip():
        return True
    return bool(_PLACEHOLDER_VALUE_RE.search(value))


def check_routing_field_writes(parsed) -> list[dict]:
    """A IA NUNCA grava `setor_agente` (roteador) nem `tipo_setor` (revalidador).
    O fluxo de entrada relê esses campos a cada mensagem: a IA gravando ali se
    re-roteia — loop de transferência em produção (evidência: Veuske). BLOCK."""
    issues = []
    for path, node in _iter_action_objects(parsed):
        if node.get("action") != "set_field_value":
            continue
        field = _field_name_of(node)
        if field in ROUTING_FIELDS:
            issues.append({
                "path": path,
                "field_name": node.get("field_name"),
                "severity": "block",
                "problem": ("a IA nunca grava campo de roteamento: `setor_agente` é do "
                            "ROTEADOR e `tipo_setor` é do REVALIDADOR "
                            "(campos_canonicos.md §3). A IA só transfere para HUMANO, "
                            "gravando o trio de handoff + send_flow do pipeline."),
            })
    return issues


def check_motivo_transferencia_enum(parsed) -> list[dict]:
    """`motivo_transferencia` fora do enum canônico → WARN (o cliente pode ter
    enum próprio; a skill registra a exceção no relatório)."""
    issues = []
    for path, node in _iter_action_objects(parsed):
        if node.get("action") != "set_field_value":
            continue
        if _field_name_of(node) != "motivo_transferencia":
            continue
        value = node.get("value")
        if _is_placeholder_value(value):
            continue
        norm = value.strip().lower()
        if norm in CANONICAL_MOTIVO_TRANSFERENCIA:
            continue
        issues.append({
            "path": path,
            "value": value,
            "severity": "warn",
            "suggestion": LEGACY_MOTIVO_MAP.get(norm, "duvida"),
            "problem": ("valor fora do enum canônico "
                        "(ugc|colaboracao|influencer|revenda|atacado|vendas|carrinho|"
                        "rastreio|devolucao|troca|duvida). O fluxo de pipeline filtra "
                        "estas strings exatas; valor desconhecido cai no `else` (SAC). "
                        "Legado: duvidas→duvida, sac_geral→duvida."),
        })
    return issues


def check_prioridade_pipeline_enum(parsed) -> list[dict]:
    """`prioridade_pipeline` é Seleção única (baixa|media|alta): valor fora da
    lista é rejeitado pela plataforma e o card fica sem prioridade. BLOCK."""
    issues = []
    for path, node in _iter_action_objects(parsed):
        if node.get("action") != "set_field_value":
            continue
        if _field_name_of(node) != "prioridade_pipeline":
            continue
        value = node.get("value")
        if _is_placeholder_value(value):
            continue
        if value.strip().lower() in CANONICAL_PRIORIDADE_PIPELINE:
            continue
        issues.append({
            "path": path,
            "value": value,
            "severity": "block",
            "problem": ("`prioridade_pipeline` é Seleção única e só aceita "
                        "baixa|media|alta (minúsculas, sem acento). Valor fora da "
                        "lista é descartado e o card entra sem prioridade."),
        })
    return issues


def check_handoff_trio(parsed) -> list[dict]:
    """Transferência que grava `motivo_transferencia` e dispara `send_flow` mas
    não grava `prioridade_pipeline` e/ou `resumo_pipeline` → WARN. Os campos
    persistem no contato: sem gravar, o fluxo lê o valor do atendimento anterior
    (campo stale) e o card cai na prioridade/fila errada."""
    issues = []
    for path, node in walk_json(parsed):
        if not isinstance(node, list):
            continue
        fields: set[str] = set()
        has_send_flow = False
        for item in node:
            if not isinstance(item, dict):
                continue
            act = item.get("action")
            if act == "set_field_value":
                name = _field_name_of(item)
                if name:
                    fields.add(name)
            elif act == "send_flow":
                has_send_flow = True
        if not has_send_flow or "motivo_transferencia" not in fields:
            continue
        missing = [f for f in HANDOFF_TRIO[1:] if f not in fields]
        if missing:
            issues.append({
                "path": path,
                "missing": missing,
                "severity": "warn",
                "problem": ("trio de handoff incompleto: gravou motivo_transferencia e "
                            "disparou send_flow sem " + " e sem ".join(missing) +
                            ". Os campos persistem no contato — sem gravar, o fluxo lê "
                            "o valor do atendimento anterior (campo stale)."),
            })
    return issues


# Promessa de envio sem a action que entrega. A IA escreve "vou te mandar o
# catálogo" e não emite send_flow nem attachment: o cliente nunca recebe e a
# frase vira mentira. Caso real: 3 turnos seguidos prometendo a tabela de
# medidas (DOLPS v1.7).
PROMESSA_DE_ENVIO = re.compile(
    r"\b(vou (te )?(enviar|mandar|passar)|já (te )?(envio|mando|passo)|"
    r"te (envio|mando|passo) (agora|já)|estou (te )?(enviando|mandando)|"
    r"segue (o|a|em) (anexo|seguida))\b",
    re.IGNORECASE,
)


def check_promessa_sem_entrega(parsed) -> list[dict]:
    """Mensagem promete enviar algo, mas o JSON não entrega nada: sem
    `send_flow` nas actions e sem attachment em nenhuma mensagem. WARN —
    o envio pode vir do fluxo disparado depois, mas na maioria dos casos
    é promessa que o cliente nunca vê cumprida."""
    if not isinstance(parsed, dict):
        return []
    messages = parsed.get("messages")
    if not isinstance(messages, list):
        return []

    tem_attachment = any(
        isinstance(m, dict)
        and isinstance(m.get("message"), dict)
        and m["message"].get("attachment")
        for m in messages
    )
    actions = parsed.get("actions")
    tem_send_flow = isinstance(actions, list) and any(
        isinstance(a, dict) and a.get("action") == "send_flow" for a in actions
    )
    if tem_attachment or tem_send_flow:
        return []

    issues = []
    for idx, m in enumerate(messages):
        if not isinstance(m, dict) or not isinstance(m.get("message"), dict):
            continue
        texto = m["message"].get("text")
        if not isinstance(texto, str):
            continue
        achado = PROMESSA_DE_ENVIO.search(texto)
        if achado:
            issues.append({
                "path": f"$.messages[{idx}].message.text",
                "problem": (
                    f'mensagem promete enviar algo ("{achado.group(0)}") mas o JSON não '
                    "tem `send_flow` nem attachment — o cliente não recebe nada"
                ),
                "severity": "warn",
                "title": texto[:80],
            })
    return issues


def check_send_flow_action_order(parsed) -> list[dict]:
    """`send_flow` antes de `set_field_value` no MESMO array → WARN. O fluxo
    dispara e lê o campo antes de ele existir (chega vazio ou com valor velho).
    send_flow é sempre a última action."""
    issues = []
    for path, node in walk_json(parsed):
        if not isinstance(node, list):
            continue
        first_send_flow = None
        for idx, item in enumerate(node):
            if not isinstance(item, dict):
                continue
            act = item.get("action")
            if act == "send_flow" and first_send_flow is None:
                first_send_flow = idx
            elif act == "set_field_value" and first_send_flow is not None:
                issues.append({
                    "path": f"{path}[{idx}]",
                    "severity": "warn",
                    "send_flow_index": first_send_flow,
                    "problem": (f"`send_flow` (índice {first_send_flow}) vem ANTES de "
                                f"`set_field_value` (índice {idx}) no mesmo array: o fluxo "
                                "dispara antes do campo existir e lê valor vazio ou velho. "
                                "Ordem canônica: set_field_value… → add_tag… → send_flow "
                                "por último."),
                })
                break
    return issues


# ----------------------------------------------------------------------
# Lints de estilo (warn) — detectores de "cara de IA"
# ----------------------------------------------------------------------

def check_style_lints(parsed) -> list[dict]:
    """Em-dash (—) e emoji 🤖 dentro de campos de texto = tique de IA → warn."""
    issues = []
    for path, node in walk_json(parsed):
        if not isinstance(node, dict):
            continue
        for field in ("text", "subtitle", "title"):
            value = node.get(field)
            if not isinstance(value, str):
                continue
            if "—" in value:
                issues.append({"path": f"{path}.{field}", "lint": "em-dash (—) — tique de IA; use vírgula, ponto ou 'e'", "severity": "warn"})
            if "🤖" in value:
                issues.append({"path": f"{path}.{field}", "lint": "emoji 🤖 — assume 'sou bot'", "severity": "warn"})
    return issues


# ----------------------------------------------------------------------
# Verificações no nível do prompt inteiro
# ----------------------------------------------------------------------

def find_advisory_actions_in_prose(content: str, json_blocks: list[dict]) -> list[dict]:
    """Acha ações de transferência mencionadas em prosa (fora de JSON).
    São AVISO (warn), não bloqueio — transfer/assign são fallback/caso especial."""
    issues = []
    lines = content.split("\n")
    json_line_ranges = [(b["start_line"], b["end_line"]) for b in json_blocks]

    def line_in_json_block(ln: int) -> bool:
        return any(s <= ln <= e for s, e in json_line_ranges)

    for ln_idx, line in enumerate(lines, 1):
        if line_in_json_block(ln_idx):
            continue
        for action in ADVISORY_TRANSFER_ACTIONS:
            if action in line:
                ctx = "\n".join(lines[max(0, ln_idx - 4):ln_idx]).lower()
                if any(m in ctx for m in NEGATIVE_EXAMPLE_MARKERS):
                    continue
                if any(m in line.lower() for m in NEGATIVE_EXAMPLE_MARKERS):
                    continue
                issues.append({"action": action, "line": ln_idx,
                               "severity": "warn",
                               "snippet": line.strip()[:160]})
    return issues


def prompt_uses_actions(content: str, blocks: list[dict]) -> bool:
    """O prompt usa actions (send_flow/set_field_value/tags)? Se sim, a saída
    PRECISA ser JSON (block se faltar json_obrigatorio). Se não (agente
    puramente conversacional), texto é aceitável (warn)."""
    for b in blocks:
        parsed = b.get("_parsed")
        if isinstance(parsed, dict) and isinstance(parsed.get("actions"), list) and parsed["actions"]:
            return True
    # fallback textual: menção a actions canônicas no corpo
    return bool(re.search(r'"action"\s*:\s*"(send_flow|set_field_value|add_tag|remove_tag|unset_field_value)"', content))


def check_required_sections(content: str, uses_actions: bool, mode: str = "creator") -> list[dict]:
    missing = []
    for key, info in REQUIRED_SECTIONS.items():
        present = any(
            re.search(pat, content, re.IGNORECASE | re.MULTILINE)
            for pat in info["patterns"]
        )
        if not present:
            severity = info["severity"]
            if severity == "dynamic_json":
                # JSON só é obrigatório (block) se o agente AGE.
                severity = "block" if uses_actions else "warn"
            # No fixer (audita prompt EXISTENTE), ausência de transferência via
            # send_flow é recomendação, não bloqueio — o prompt pode transferir
            # por outro mecanismo legítimo. No creator (prompt novo) segue block.
            if mode == "fixer" and key == "send_flow_transferencia":
                severity = "warn"
            missing.append({"key": key, "label": info["label"], "severity": severity})
    return missing


def check_text_outside_json_instruction(content: str) -> bool:
    cl = content.lower()
    signals = [
        "somente json", "apenas json", "sem texto antes",
        "sem texto fora do json", "no text outside",
        "json only", "responder somente em json",
    ]
    return any(s in cl for s in signals)


def check_tool_call_clarification(content: str) -> list[dict]:
    """Se o agente tem tools/MCP, o prompt PRECISA esclarecer que function call
    != saida JSON. Sem isso, o "so JSON" faz o modelo concluir que nao pode
    emitir function call e ele para de chamar as tools (caso Veuske 2026-06-11:
    log da OpenAI mostrou o agente raciocinando exatamente isso -> 0 tool calls).
    So aplica se o prompt tambem tem a instrucao 'so JSON' (senao nao ha conflito)."""
    low = content.lower()
    if not check_text_outside_json_instruction(content):
        return []
    has_tools = bool(re.search(
        r'(function\s*call|tool\s*call|cham\w+\s+(a\s+)?(tool|ferramenta|fun[cç][aã]o)|'
        r'\bmcp\b|\b(buscar|listar|obter|consultar)_[a-z]{3,}|ferramentas?\s+dispon)',
        low))
    if not has_tools:
        return []
    has_clar = bool(re.search(
        r'(function\s*call|chamar\s+(a\s+)?(tool|ferramenta|fun[cç][aã]o)).{0,90}'
        r'(canal\s+separad|n[aã]o\s+(impede|viola)|n[aã]o\s+[eé]\s+["\']?texto\s+fora|≠|canal)',
        low, re.DOTALL))
    if has_clar:
        return []
    return [{
        "type": "missing_tool_call_clarification",
        "severity": "warn",
        "label": ('Agente tem tools/MCP + instrucao "so JSON" mas falta a clausula '
                  '"function call != saida JSON" -> o "so JSON" pode suprimir as tool '
                  'calls (caso Veuske 2026-06-11). Inserir a clausula apos o bloco oficial.'),
    }]


# ----------------------------------------------------------------------
# Orquestração
# ----------------------------------------------------------------------

def find_invalid_json_candidates(content: str, valid_blocks: list[dict]) -> list[dict]:
    invalid = []
    lines = content.split("\n")
    n = len(lines)
    # Linhas já cobertas por QUALQUER bloco JSON válido (não só o start_line) —
    # evita falso-positivo ao reexaminar uma linha INTERNA de um array válido
    # (ex.: um `{"action":...},` solto dentro de um `actions` que parseia inteiro
    # no bloco-pai). Sem isso, cada elemento de um array multi-linha era lido em
    # isolado, falhava por "Extra data" (vírgula final) e virava invalid_json (block).
    covered = set()
    for b in valid_blocks:
        for ln in range(b["start_line"], b["end_line"] + 1):
            covered.add(ln)

    INVALID_TRIGGER_PATTERNS = [
        re.compile(r'^\s*\{\s*"messages"'),
        re.compile(r'^\s*\{\s*"actions"'),
        re.compile(r'^\s*\{\s*"action"\s*:'),
    ]

    for start_idx in range(n):
        if (start_idx + 1) in covered:
            continue
        line = lines[start_idx]
        if not any(p.match(line) for p in INVALID_TRIGGER_PATTERNS):
            continue
        accumulated = []
        for end_idx in range(start_idx, min(n, start_idx + 100)):
            accumulated.append(lines[end_idx])
            candidate = "\n".join(accumulated)
            opens = candidate.count("{") + candidate.count("[")
            closes = candidate.count("}") + candidate.count("]")
            if closes < opens:
                continue
            try:
                json.loads(candidate)
                break
            except json.JSONDecodeError as e:
                if closes == opens and opens > 0:
                    ctx_lines = lines[max(0, start_idx - 5):start_idx]
                    preceding = "\n".join(ctx_lines).lower()
                    invalid.append({
                        "start_line": start_idx + 1,
                        "end_line": end_idx + 1,
                        "text": candidate.strip(),
                        "syntax_error": f"linha {e.lineno}, col {e.colno}: {e.msg}",
                        "preceding_context": preceding,
                        "is_marked_json": False,
                    })
                    break
    return invalid


def analyze(content: str, mode: str = "creator") -> dict:
    findings: dict = {
        "summary": {
            "block_count": 0,
            "warn_count": 0,
            "total_json_blocks": 0,
            "json_blocks_with_issues": 0,
            "invalid_json_count": 0,
            "nonexistent_actions_count": 0,
            "advisory_actions_count": 0,
            "button_misuse_count": 0,
            "carousel_misuse_count": 0,
            "type_inside_payload_count": 0,
            "forbidden_image_formats_count": 0,
            "markdown_in_json_count": 0,
            "generic_placeholders_count": 0,
            "style_lints_count": 0,
            "forbidden_meta_sections_count": 0,
            "missing_sections_count": 0,
            "negative_examples_skipped": 0,
            # roteamento / handoff canônico (campos_canonicos.md §2 e §3)
            "ia_grava_campo_de_roteamento_count": 0,
            "motivo_fora_do_enum_count": 0,
            "prioridade_fora_do_enum_count": 0,
            "trio_handoff_incompleto_count": 0,
            "send_flow_antes_de_set_field_count": 0,
            "promessa_sem_entrega_count": 0,
            # blocos editáveis pelo cliente (SPEC §5.1 e §5.2)
            "avisos_ativos_missing_count": 0,
            "nota_editor_longa_count": 0,
        },
        "json_blocks": [],
        "advisory_actions_in_prose": [],
        "missing_sections": [],
        "forbidden_meta_sections": [],
        "avisos_ativos": [],
        "avisos_ativos_presente": False,
        "nota_editor_longa": [],
        "prompt_uses_actions": False,
        "json_only_instruction_present": False,
    }

    valid_blocks = find_json_blocks(content)
    invalid_blocks = find_invalid_json_candidates(content, valid_blocks)
    all_blocks = valid_blocks + invalid_blocks
    all_blocks.sort(key=lambda b: b["start_line"])

    findings["summary"]["total_json_blocks"] = len(all_blocks)
    uses_actions = prompt_uses_actions(content, valid_blocks)
    findings["prompt_uses_actions"] = uses_actions

    def bump(severity: str):
        if severity == "block":
            findings["summary"]["block_count"] += 1
        elif severity == "warn":
            findings["summary"]["warn_count"] += 1

    for block in all_blocks:
        is_invalid = "syntax_error" in block
        block_report = {
            "start_line": block["start_line"],
            "end_line": block["end_line"],
            "is_negative_example": is_negative_example(block),
            "valid_json": not is_invalid,
            "syntax_error": block.get("syntax_error"),
            "issues": [],
            "raw_text": block["text"],
        }
        skip = block_report["is_negative_example"]
        if skip:
            findings["summary"]["negative_examples_skipped"] += 1

        if is_invalid:
            if not skip:
                findings["summary"]["invalid_json_count"] += 1
                bump("block")
            acts = find_actions_in_text(block["text"])
            _record_actions(acts, block_report, findings, skip, bump)
        else:
            parsed = block.get("_parsed")
            if parsed is None:
                parsed = json.loads(block["text"])

            acts = find_actions_in_text(block["text"])
            _record_actions(acts, block_report, findings, skip, bump)

            for issues, key, summary_key in (
                (check_buttons_misuse(parsed), "button_misuse", "button_misuse_count"),
                (check_carousel_misuse(parsed), "carousel_misuse", "carousel_misuse_count"),
                (check_type_inside_payload(parsed), "type_inside_payload", "type_inside_payload_count"),
                (check_forbidden_image_formats(parsed), "forbidden_image_formats", "forbidden_image_formats_count"),
                (check_markdown_in_text(parsed), "markdown_in_json_text", "markdown_in_json_count"),
                (check_generic_placeholders(parsed), "generic_placeholders", "generic_placeholders_count"),
                (check_style_lints(parsed), "style_lints", "style_lints_count"),
                (check_routing_field_writes(parsed), "ia_grava_campo_de_roteamento", "ia_grava_campo_de_roteamento_count"),
                (check_motivo_transferencia_enum(parsed), "motivo_fora_do_enum", "motivo_fora_do_enum_count"),
                (check_prioridade_pipeline_enum(parsed), "prioridade_fora_do_enum", "prioridade_fora_do_enum_count"),
                (check_handoff_trio(parsed), "trio_handoff_incompleto", "trio_handoff_incompleto_count"),
                (check_send_flow_action_order(parsed), "send_flow_antes_de_set_field", "send_flow_antes_de_set_field_count"),
                (check_promessa_sem_entrega(parsed), "promessa_sem_entrega", "promessa_sem_entrega_count"),
            ):
                if issues:
                    block_report["issues"].append({"type": key, "details": issues})
                    if not skip:
                        findings["summary"][summary_key] += len(issues)
                        for it in issues:
                            bump(it.get("severity", "block"))

        if (block_report["issues"] or is_invalid) and not skip:
            findings["summary"]["json_blocks_with_issues"] += 1
        findings["json_blocks"].append(block_report)

    prose = find_advisory_actions_in_prose(content, all_blocks)
    findings["advisory_actions_in_prose"] = prose
    for p in prose:
        bump(p.get("severity", "warn"))

    missing = check_required_sections(content, uses_actions, mode)
    findings["missing_sections"] = missing
    findings["summary"]["missing_sections_count"] = len(missing)
    for m in missing:
        bump(m.get("severity", "warn"))

    forbidden_meta = check_forbidden_meta_sections(content)
    findings["forbidden_meta_sections"] = forbidden_meta
    findings["summary"]["forbidden_meta_sections_count"] = len(forbidden_meta)
    for fm in forbidden_meta:
        bump(fm.get("severity", "warn"))

    avisos = check_avisos_ativos(content)
    findings["avisos_ativos"] = avisos
    findings["avisos_ativos_presente"] = bool(AVISOS_ATIVOS_RE.search(content))
    findings["summary"]["avisos_ativos_missing_count"] = len(avisos)
    for av in avisos:
        bump(av.get("severity", "warn"))

    notas_longas = check_editor_notes(content)
    findings["nota_editor_longa"] = notas_longas
    findings["summary"]["nota_editor_longa_count"] = len(notas_longas)
    for nt in notas_longas:
        bump(nt.get("severity", "warn"))

    findings["json_only_instruction_present"] = check_text_outside_json_instruction(content)

    tool_clar = check_tool_call_clarification(content)
    findings["missing_tool_call_clarification"] = tool_clar
    findings["summary"]["missing_tool_call_clarification_count"] = len(tool_clar)
    for tc in tool_clar:
        bump(tc.get("severity", "warn"))

    return findings


def _record_actions(acts: dict, block_report: dict, findings: dict,
                    skip: bool, bump) -> None:
    """Registra ações inexistentes (block) e de transferência advisory (warn)."""
    if acts["nonexistent"]:
        block_report["issues"].append({
            "type": "nonexistent_actions",
            "severity": "block",
            "actions": acts["nonexistent"],
            "hint": "ação fora das 8 canônicas — a plataforma não a reconhece (não dispara)",
        })
        if not skip:
            findings["summary"]["nonexistent_actions_count"] += len(acts["nonexistent"])
            for _ in acts["nonexistent"]:
                bump("block")
    if acts["advisory"]:
        block_report["issues"].append({
            "type": "advisory_transfer_actions",
            "severity": "warn",
            "actions": acts["advisory"],
            "hint": "válida, mas send_flow é o padrão recomendado (transfer=fallback, assign=caso especial)",
        })
        if not skip:
            findings["summary"]["advisory_actions_count"] += len(acts["advisory"])
            for _ in acts["advisory"]:
                bump("warn")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audita prompts NexTags contra as Regras Absolutas."
    )
    parser.add_argument("prompt_file", help="Caminho do .md do prompt")
    parser.add_argument("--output", "-o", help="Salvar findings em JSON neste arquivo")
    parser.add_argument("--mode", choices=["creator", "fixer"], default="creator",
                        help="creator (default, estrito) ou fixer (afrouxa send_flow p/ warn)")
    args = parser.parse_args()

    path = Path(args.prompt_file)
    if not path.exists():
        print(f"Arquivo não encontrado: {path}", file=sys.stderr)
        return 1

    content = path.read_text(encoding="utf-8")
    findings = analyze(content, mode=args.mode)
    output = json.dumps(findings, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Findings salvos em: {args.output}")
    else:
        print(output)
    # exit 0 sempre (o consumidor lê block_count pra decidir reprovar)
    return 0


if __name__ == "__main__":
    sys.exit(main())

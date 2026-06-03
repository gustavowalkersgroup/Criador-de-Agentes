#!/usr/bin/env python3
"""
analyze_prompt.py — Audita um prompt de agente de atendimento NexTags
contra as Regras Absolutas da plataforma.

Saída: JSON estruturado com findings (compacto e fácil de o Claude consumir).
Cada finding tem severity = "block" (quebra a plataforma → reprovar) ou
"warn" (estilo/recomendação → avisar, não reprova).

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
            r"(nunca|jamais|n[ãa]o)\s+invent",
            r"(nunca|jamais|n[ãa]o)\s+assum",
            r"(nunca|jamais|n[ãa]o)\s+confirmar?\s+(sem|aprovação)",
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
        "label": "Transferência humana via send_flow",
        "severity": "block",
        "patterns": [
            r"send_flow",
            r"fluxo\s+de\s+transfer[êe]ncia",
            r"disparar?\s+(o\s+)?fluxo",
            r"transfer\s+flow",
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
    de 1 botão web_url no mesmo template (restrição do WhatsApp p/ link)."""
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


def check_forbidden_meta_sections(content: str) -> list[dict]:
    issues = []
    for pattern, kind in FORBIDDEN_META_HEADER_PATTERNS:
        for m in pattern.finditer(content):
            line_num = content[:m.start()].count("\n") + 1
            issues.append({"kind": kind, "line": line_num,
                           "severity": "warn",
                           "snippet": m.group(0).strip()[:120]})
    head = "\n".join(content.split("\n")[:10])
    for pattern, kind in FORBIDDEN_HEADER_METADATA:
        m = pattern.search(head)
        if m:
            line_num = head[:m.start()].count("\n") + 1
            issues.append({"kind": kind, "line": line_num,
                           "severity": "warn",
                           "snippet": m.group(0).strip()[:120]})
    return issues


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


def check_required_sections(content: str, uses_actions: bool) -> list[dict]:
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


# ----------------------------------------------------------------------
# Orquestração
# ----------------------------------------------------------------------

def find_invalid_json_candidates(content: str, valid_blocks: list[dict]) -> list[dict]:
    invalid = []
    lines = content.split("\n")
    n = len(lines)
    valid_starts = {b["start_line"] for b in valid_blocks}

    INVALID_TRIGGER_PATTERNS = [
        re.compile(r'^\s*\{\s*"messages"'),
        re.compile(r'^\s*\{\s*"actions"'),
        re.compile(r'^\s*\{\s*"action"\s*:'),
    ]

    for start_idx in range(n):
        if (start_idx + 1) in valid_starts:
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


def analyze(content: str) -> dict:
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
        },
        "json_blocks": [],
        "advisory_actions_in_prose": [],
        "missing_sections": [],
        "forbidden_meta_sections": [],
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

    missing = check_required_sections(content, uses_actions)
    findings["missing_sections"] = missing
    findings["summary"]["missing_sections_count"] = len(missing)
    for m in missing:
        bump(m.get("severity", "warn"))

    forbidden_meta = check_forbidden_meta_sections(content)
    findings["forbidden_meta_sections"] = forbidden_meta
    findings["summary"]["forbidden_meta_sections_count"] = len(forbidden_meta)
    for fm in forbidden_meta:
        bump(fm.get("severity", "warn"))

    findings["json_only_instruction_present"] = check_text_outside_json_instruction(content)
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
    args = parser.parse_args()

    path = Path(args.prompt_file)
    if not path.exists():
        print(f"Arquivo não encontrado: {path}", file=sys.stderr)
        return 1

    content = path.read_text(encoding="utf-8")
    findings = analyze(content)
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

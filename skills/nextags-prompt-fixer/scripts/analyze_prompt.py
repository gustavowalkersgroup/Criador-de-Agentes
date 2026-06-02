#!/usr/bin/env python3
"""
analyze_prompt.py — Audita um prompt de agente de atendimento NexTags
contra as Regras Absolutas da plataforma.

Saída: JSON estruturado com findings (compacto e fácil de o Claude consumir).

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

FORBIDDEN_ACTIONS = [
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
REQUIRED_SECTIONS = {
    "bloco_oficial_nextags": {
        "label": "Bloco oficial NexTags (instruções canônicas de saída JSON)",
        "patterns": [
            # frase-âncora do bloco oficial: a inteira ou parte dela
            r"deve\s+sempre\s+retornar\s+respostas?\s+em\s+json\s+v[áa]lido\s+seguindo\s+o\s+padr[ãa]o\s+da\s+messenger\s+messaging\s+platform",
            # variante: "seguindo o esquema do Messenger Messaging Platform"
            r"seguindo\s+o\s+(padr[ãa]o|esquema)\s+da\s+messenger\s+messaging\s+platform",
        ],
    },
    "anti_alucinacao": {
        "label": "Regras anti-alucinação",
        "patterns": [
            r"anti[\s-]?aluc",
            r"(nunca|jamais|n[ãa]o)\s+invent",
            r"(nunca|jamais|n[ãa]o)\s+assum",
            # phrasing comum: "NUNCA inventar prazos", "NUNCA confirmar..."
            r"(nunca|jamais|n[ãa]o)\s+confirmar?\s+(sem|aprovação)",
            r"never\s+(invent|make\s+up|hallucinat)",
        ],
    },
    "nao_revelar_ia": {
        "label": "Nunca revelar que é IA",
        "patterns": [
            # já existente: "nunca revelar que é IA"
            r"(nunca|jamais|n[ãa]o)\s+(revel|diz|admit|conf|inform).{0,40}\b(ia|i\.a\.|intelig[êe]ncia\s+artificial|bot|rob[ôo]|chatbot)\b",
            # forma comum nos prompts reais: "Nunca diga que é uma IA"
            r"(nunca|jamais|n[ãa]o)\s+(diga|fale|conte|comente)\s+que\s+(é|sou|e)\s+(uma?\s+)?(ia|intelig[êe]ncia|bot|rob[ôo]|sistema|assistente)",
            # "você é humana"
            r"voc[êe]\s+[ée]\s+humana?",
            # "Nunca revele que é IA" / "...você é IA"
            r"(nunca|jamais|n[ãa]o)\s+revele\s+que\s+[ée]\s+(uma?\s+)?(ia|intelig[êe]ncia|bot|rob[ôo])",
            # "REGRA ABSOLUTA: Nunca diga que é uma IA" — basta capturar essa estrutura
            r"\bregra\s+absoluta[\s\S]{0,80}(ia|intelig[êe]ncia\s+artificial|bot|rob[ôo]|sistema)",
            r"never\s+(reveal|say|admit|disclose).{0,40}\bai\b",
        ],
    },
    "json_obrigatorio": {
        "label": "Saída obrigatoriamente em JSON",
        "patterns": [
            r"(somente|apenas|sempre)\s+(em\s+)?json",
            r"json\s+v[áa]lido",
            r"retornar?\s+json",
            r"responder?\s+em\s+json",
            r"sem\s+texto\s+(antes|depois|fora)",
            # phrasing comum: "TODA resposta sua é JSON", "Toda resposta deve ser JSON"
            r"toda\s+resposta\s+(sua\s+)?(é|deve\s+ser|e)\s+.{0,20}\bjson\b",
            # "OBRIGATORIAMENTE um JSON"
            r"obrigatori(o|a|amente).{0,15}\bjson\b",
            # "FORMATO DE SAÍDA" + "JSON" próximos
            r"formato\s+de\s+sa[íi]da[\s\S]{0,100}\bjson\b",
            r"json\s+only|valid\s+json",
        ],
    },
    "send_flow_transferencia": {
        "label": "Transferência humana via send_flow",
        "patterns": [
            r"send_flow",
            r"fluxo\s+de\s+transfer[êe]ncia",
            r"disparar?\s+(o\s+)?fluxo",
            r"transfer\s+flow",
        ],
    },
    "texto_padrao": {
        "label": "Texto simples como padrão de resposta",
        "patterns": [
            r"texto\s+simples",
            r"texto\s+(como\s+|[ée]\s+o\s+)?padr[ãa]o",
            r"padr[ãa]o\s+[ée]\s+texto",
            r"plain\s+text|default\s+text",
        ],
    },
    "fora_de_escopo": {
        "label": "Manter-se no escopo / não sair do contexto",
        "patterns": [
            r"fora\s+d[oa]\s+(escopo|contexto)",
            r"(sair|saia)\s+d[oa]\s+(escopo|contexto)",
            r"(manter|mantenha)[\s-]se\s+n[oa]\s+(escopo|contexto)",
            r"redirec(ionar|ione)",
            # phrasing comum: "responder sobre temas alheios à marca"
            r"temas?\s+alheios?",
            # "fica fora do que posso ajudar"
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
    """
    Encontra todos os trechos no documento que parecem ser JSON da plataforma
    (objetos começando com {"messages": ...} ou {"actions": ...} ou listas).

    Estratégia: varre o texto procurando posições onde um JSON candidato pode
    começar (linha que tem `{` no começo, possivelmente após whitespace ou
    após ```json), e tenta parsear progressivamente até encontrar uma
    estrutura JSON válida (ou determinar que não é JSON).

    Isto é mais robusto que parser baseado em fences ``` porque funciona
    mesmo quando o prompt inteiro está dentro de um code block (padrão
    comum em prompts do meta-prompt NexTags onde o autor envolve toda a
    instrução em ``` para facilitar copy-paste).

    Retorna lista de dicts com:
        start_line, end_line (1-indexed),
        text (o JSON bruto),
        is_marked_json (True se imediatamente precedido por ```json),
        preceding_context (até 5 linhas antes, em lowercase, para detecção
                          de exemplos negativos)
    """
    blocks: list[dict] = []
    lines = content.split("\n")
    n = len(lines)
    used_lines: set[int] = set()  # linhas já cobertas por blocos detectados

    # Heurística de filtro: o JSON precisa parecer com payload da plataforma.
    # (Evita capturar JSON de exemplo de outra natureza, ex.: tabela de tools
    # que mencionam "id" ou "params".)
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

        # Tenta acumular linhas até formar JSON válido. Limite: 200 linhas
        # (mensagens da plataforma raramente passam disso).
        accumulated = []
        for end_idx in range(start_idx, min(n, start_idx + 200)):
            accumulated.append(lines[end_idx])
            candidate = "\n".join(accumulated)
            # Otimização: só tenta parsear se as chaves balançam grosseiramente
            opens = candidate.count("{") + candidate.count("[")
            closes = candidate.count("}") + candidate.count("]")
            if closes < opens or closes == 0:
                continue
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue

            # Parseou. Mas é JSON da plataforma? Aplica filtro:
            text_check = candidate
            if not any(k in text_check for k in PLATFORM_KEYS):
                # Não parece payload NexTags — pula.
                break

            # Detecta se foi precedido imediatamente por ```json
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
                "_parsed": parsed,  # cache pra evitar re-parse depois
            })
            for u in range(start_idx, end_idx + 1):
                used_lines.add(u)
            break  # achou um match completo, vai pro próximo start

    return blocks


def is_negative_example(block: dict) -> bool:
    """O bloco está marcado como exemplo do que NÃO fazer?"""
    ctx = block["preceding_context"]
    return any(marker in ctx for marker in NEGATIVE_EXAMPLE_MARKERS)


# ----------------------------------------------------------------------
# Validações dentro de um bloco JSON
# ----------------------------------------------------------------------

def validate_json_syntax(text: str) -> tuple[bool, str | None]:
    """Tenta parsear. Retorna (válido, mensagem_de_erro)."""
    try:
        json.loads(text)
        return True, None
    except json.JSONDecodeError as e:
        return False, f"linha {e.lineno}, col {e.colno}: {e.msg}"


def find_forbidden_actions_in_text(text: str) -> list[str]:
    """Procura ações proibidas como string (funciona mesmo com JSON inválido)."""
    found = []
    for action in FORBIDDEN_ACTIONS:
        # Match em formato JSON: "action":"transfer_conversation_to" ou variações
        if re.search(rf'["\']action["\']\s*:\s*["\']{action}["\']', text):
            found.append(action)
    return found


def walk_json(obj, path: str = "$"):
    """Itera recursivamente todos os nós, yielding (path, valor)."""
    yield path, obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_json(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            yield from walk_json(item, f"{path}[{idx}]")


def check_buttons_misuse(parsed) -> list[dict]:
    """Botões só são válidos com type=web_url e url presente."""
    issues = []
    for path, node in walk_json(parsed):
        if isinstance(node, dict) and node.get("template_type") == "button":
            buttons = node.get("buttons") or []
            if not buttons:
                issues.append({
                    "path": path,
                    "problem": "template button sem botões",
                    "title_text": node.get("text", ""),
                })
                continue
            for idx, btn in enumerate(buttons):
                if not isinstance(btn, dict):
                    continue
                btn_type = btn.get("type")
                btn_url = btn.get("url")
                if btn_type != "web_url" or not btn_url:
                    issues.append({
                        "path": f"{path}.buttons[{idx}]",
                        "problem": "botão sem web_url externo",
                        "type_used": btn_type,
                        "title": btn.get("title", ""),
                        "title_text": node.get("text", ""),
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
                    "element_count": len(elements),
                    "elements": elements,
                })
    return issues


MARKDOWN_PATTERNS = [
    (re.compile(r"\*\*[^*\n]+\*\*"), "negrito (**texto**)"),
    (re.compile(r"(?<!\*)\*[^*\n]+\*(?!\*)"), "itálico (*texto*)"),
    (re.compile(r"^\s*#{1,6}\s+", re.MULTILINE), "título (# texto)"),
    (re.compile(r"`[^`\n]+`"), "código inline (`texto`)"),
    (re.compile(r"^\s*[-*+]\s+", re.MULTILINE), "bullet de markdown (- item)"),
]


def check_markdown_in_text(parsed) -> list[dict]:
    """Procura markdown dentro de campos 'text' e 'subtitle' do JSON."""
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
                        "snippet": value if len(value) <= 120 else value[:120] + "…",
                    })
                    break  # um problema por campo basta
    return issues


# Padrões de seções de meta-documentação que NÃO pertencem ao prompt
# (vão pro relatório). Detecta em cabeçalhos markdown `#`, `##`, `###`.
FORBIDDEN_META_HEADER_PATTERNS = [
    # `.*` no meio do cabeçalho permite numerações tipo "## 14. AUDITORIA"
    (re.compile(r"^#{1,6}\s+.*\baudit(oria|or)\b", re.IGNORECASE | re.MULTILINE), "auditoria"),
    (re.compile(r"^#{1,6}\s+.*\bchangelog\b", re.IGNORECASE | re.MULTILINE), "changelog"),
    (re.compile(r"^#{1,6}\s+.*hist[óo]rico\s+de\s+(vers[ãa]o|mudan[çc]a)", re.IGNORECASE | re.MULTILINE), "historico_versao"),
    (re.compile(r"^#{1,6}\s+.*corre[çc][õo]es?\s+(v\d|da\s+v|aplicad)", re.IGNORECASE | re.MULTILINE), "correcoes_versao"),
    (re.compile(r"^#{1,6}\s+.*pend[êe]ncia(s)?(\s+(interna|humana|pra\s+confirmar|/\s*a\s+confirmar))?", re.IGNORECASE | re.MULTILINE), "pendencias"),
    (re.compile(r"^#{1,6}\s+.*\ba\s+confirmar\b", re.IGNORECASE | re.MULTILINE), "a_confirmar"),
    # TODO pode vir como cabeçalho direto ("## TODO") ou numerado ("## 16. TODO")
    (re.compile(r"^#{1,6}\s+(?:[\d\.\s]+)?\bTODO(s)?\b", re.MULTILINE), "todo"),
    (re.compile(r"^#{1,6}\s+.*notas?\s+(internas?|pra\s+dev|t[ée]cnicas?)", re.IGNORECASE | re.MULTILINE), "notas_internas"),
    (re.compile(r"^#{1,6}\s+.*bug(s)?\s+(observad|conhecid|encontrad)", re.IGNORECASE | re.MULTILINE), "bugs_observados"),
    (re.compile(r"^#{1,6}\s+.*m[ée]tric(a|as)\s+do\s+prompt", re.IGNORECASE | re.MULTILINE), "metricas_prompt"),
    # Cabeçalho com número de versão antiga ("## v2.5 (correções)", "### v1.0 → v2.0")
    (re.compile(r"^#{2,6}\s+v\d+\.\d+\s*(\([^)]+\)|\s+\(|\s+→)", re.IGNORECASE | re.MULTILINE), "cabecalho_versionado"),
]

# Padrões de metadado expandido no início do prompt (linha após o # título)
FORBIDDEN_HEADER_METADATA = [
    (re.compile(r"\*\*\s*vers[ãa]o\s*:?\s*\*\*", re.IGNORECASE), "versao_metadata"),
    (re.compile(r"\*\*\s*data\s*:?\s*\*\*", re.IGNORECASE), "data_metadata"),
    (re.compile(r"\*\*\s*respons[áa]vel\s*:?\s*\*\*", re.IGNORECASE), "responsavel_metadata"),
    (re.compile(r"\*\*\s*author(\(es\))?\s*:?\s*\*\*", re.IGNORECASE), "autor_metadata"),
]


def check_forbidden_meta_sections(content: str) -> list[dict]:
    """Detecta seções de meta-documentação (auditoria, changelog, pendências,
    TODOs, notas internas) que NÃO pertencem ao prompt — vão pro relatório."""
    issues = []
    # Cabeçalhos com padrões proibidos
    for pattern, kind in FORBIDDEN_META_HEADER_PATTERNS:
        for m in pattern.finditer(content):
            line_num = content[:m.start()].count("\n") + 1
            issues.append({
                "kind": kind,
                "line": line_num,
                "snippet": m.group(0).strip()[:120],
            })
    # Metadado expandido tipo **Versão:** v3.0 | **Data:** ...
    # Detecta apenas se aparece nas primeiras 10 linhas (cabeçalho do prompt)
    head = "\n".join(content.split("\n")[:10])
    for pattern, kind in FORBIDDEN_HEADER_METADATA:
        m = pattern.search(head)
        if m:
            line_num = head[:m.start()].count("\n") + 1
            issues.append({
                "kind": kind,
                "line": line_num,
                "snippet": m.group(0).strip()[:120],
            })
    return issues


# Padrões de placeholders genéricos NÃO interpolados pela NexTags.
# A plataforma SÓ interpola {{cuf_real}} (chaves duplas). Tudo abaixo aparece
# literal pra cliente.
GENERIC_PLACEHOLDER_PATTERNS = [
    # [nome], [cliente], [email], [primeiro nome], [order_id] etc.
    (re.compile(r"\[(?:nome|primeiro\s*nome|sobrenome|cliente|usuario|usu[áa]rio|email|e-mail|telefone|cidade|estado|pa[íi]s|order_id|pedido|c[oó]digo[\s_]*do[\s_]*pedido|produto|valor|total|cep|endere[çc]o)\]", re.IGNORECASE), "[bracket]"),
    # {nome_simples} (uma chave só — NexTags usa duplas)
    (re.compile(r"(?<!\{)\{[a-z_][a-z0-9_]{2,30}\}(?!\})"), "{single_brace}"),
    # $first_name$ ou $NOME$
    (re.compile(r"\$[a-zA-Z_][a-zA-Z0-9_]{2,30}\$"), "$dollar$"),
    # <NOME>, <EMAIL>, <PRIMEIRO_NOME> (placeholders SCREAMING)
    (re.compile(r"<[A-Z_]{3,30}>"), "<SCREAMING>"),
]


def check_generic_placeholders(parsed) -> list[dict]:
    """Procura placeholders genéricos ([nome], {nome}, $first_name$, <NOME>)
    em campos de texto VISÍVEIS pro cliente (`text`, `subtitle`, `title`).
    Campos `url` são intencionalmente excluídos — `<URL_PRODUTO>` etc. são
    placeholders de template pro LLM substituir com dados das tools."""
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
                        "match": m.group(0),
                        "snippet": value if len(value) <= 120 else value[:120] + "…",
                    })
                    break
    return issues


def check_send_flow_without_messages(parsed) -> list[dict]:
    """
    NexTags exige que o JSON tenha o campo `messages` com pelo menos 1 item
    quando há `send_flow` nas actions. Sem messages, a plataforma falha
    silenciosamente: set_field_value e tags rodam, mas send_flow NÃO dispara.

    Detecta o root-level: parsed deve ser um dict com:
    - "actions" contendo ao menos um item com action="send_flow"
    - "messages" ausente OU vazio ([])

    Apenas valida no nível raiz (não em nodes aninhados), porque é onde a
    plataforma processa o payload.
    """
    issues = []
    if not isinstance(parsed, dict):
        return issues

    actions = parsed.get("actions")
    if not isinstance(actions, list):
        return issues

    has_send_flow = any(
        isinstance(a, dict) and a.get("action") == "send_flow"
        for a in actions
    )
    if not has_send_flow:
        return issues

    messages = parsed.get("messages")
    if messages is None:
        issues.append({
            "problem": "send_flow presente sem campo 'messages' — fluxo NÃO disparará na plataforma",
            "fix_hint": "adicione 'messages' com pelo menos 1 item (frase de transição curta) antes das actions",
        })
    elif isinstance(messages, list) and len(messages) == 0:
        issues.append({
            "problem": "send_flow presente com 'messages' vazio ([]) — fluxo NÃO disparará na plataforma",
            "fix_hint": "preencha 'messages' com pelo menos 1 item (frase de transição curta)",
        })

    return issues


# Formatos de imagem permitidos pela plataforma NexTags.
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
FORBIDDEN_IMAGE_EXTENSIONS = {".webp", ".avif", ".svg", ".gif", ".bmp",
                              ".tiff", ".ico", ".heic", ".heif"}


def check_type_inside_payload(parsed) -> list[dict]:
    """
    Detecta o erro mais comum em prompts NexTags: colocar `type` DENTRO
    de `payload` em vez de ao lado dele.

    ✅ Correto: {"attachment":{"type":"image","payload":{"url":"..."}}}
    ❌ Errado:  {"attachment":{"payload":{"type":"image","url":"..."}}}

    A plataforma ignora o `type` quando ele está dentro do payload.
    """
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
                "type_value": payload.get("type"),
            })
    return issues


def _image_url_status(url: str) -> tuple[str, str | None]:
    """Retorna (status, motivo) — status ∈ ok/forbidden/ambiguous/invalid."""
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
    """
    Procura URLs em campos `image_url` (carrossel) e `payload.url`
    (attachments image) que apontam pra formatos NÃO suportados
    pela plataforma NexTags (.webp, .avif, .svg, .gif, etc.).

    Plataforma só entrega imagens em JPEG/PNG nos canais (WhatsApp,
    Instagram, Messenger). Outros formatos quebram a entrega.
    """
    issues = []
    for path, node in walk_json(parsed):
        if not isinstance(node, dict):
            continue
        # Carrossel elements têm image_url direto.
        if "image_url" in node and isinstance(node["image_url"], str):
            status, reason = _image_url_status(node["image_url"])
            if status in ("forbidden", "ambiguous", "invalid"):
                issues.append({
                    "path": f"{path}.image_url",
                    "url": node["image_url"][:120],
                    "status": status,
                    "reason": reason,
                })
        # Attachment image tem payload.url.
        # Aceita também `type` dentro do payload (forma errada, mas
        # ainda queremos flagar a URL).
        payload_dict = node.get("payload") if isinstance(node.get("payload"), dict) else None
        type_in_node = node.get("type")
        type_in_payload = payload_dict.get("type") if payload_dict else None
        if (type_in_node == "image" or type_in_payload == "image"):
            url = payload_dict.get("url") if payload_dict else None
            if isinstance(url, str):
                status, reason = _image_url_status(url)
                if status in ("forbidden", "ambiguous", "invalid"):
                    issues.append({
                        "path": f"{path}.payload.url",
                        "url": url[:120],
                        "status": status,
                        "reason": reason,
                    })
    return issues


# ----------------------------------------------------------------------
# Verificações no nível do prompt inteiro
# ----------------------------------------------------------------------

def find_forbidden_actions_in_prose(content: str, json_blocks: list[dict]) -> list[dict]:
    """
    Encontra ações proibidas mencionadas no texto FORA de blocos JSON
    (ex.: instrução em prosa dizendo 'use transfer_conversation_to').

    Ignora menções em blocos marcados como exemplo negativo, porque
    listas tipo '❌ NUNCA usar: transfer_conversation_to' são desejáveis.
    """
    issues = []
    lines = content.split("\n")
    json_line_ranges = [
        (b["start_line"], b["end_line"]) for b in json_blocks
    ]

    def line_in_json_block(ln: int) -> bool:
        return any(s <= ln <= e for s, e in json_line_ranges)

    for ln_idx, line in enumerate(lines, 1):
        if line_in_json_block(ln_idx):
            continue
        for action in FORBIDDEN_ACTIONS:
            if action in line:
                # Janela de contexto pra detectar exemplo negativo em prosa
                ctx = "\n".join(lines[max(0, ln_idx - 4):ln_idx]).lower()
                if any(m in ctx for m in NEGATIVE_EXAMPLE_MARKERS):
                    continue
                # Também ignora se na própria linha tem marcador
                if any(m in line.lower() for m in NEGATIVE_EXAMPLE_MARKERS):
                    continue
                issues.append({
                    "action": action,
                    "line": ln_idx,
                    "snippet": line.strip()[:160],
                })
    return issues


def check_required_sections(content: str) -> list[dict]:
    """Quais seções de instrução obrigatórias estão faltando?"""
    missing = []
    for key, info in REQUIRED_SECTIONS.items():
        present = any(
            re.search(pat, content, re.IGNORECASE | re.MULTILINE)
            for pat in info["patterns"]
        )
        if not present:
            missing.append({"key": key, "label": info["label"]})
    return missing


def check_text_outside_json_instruction(content: str) -> bool:
    """Heurística: o prompt instrui o agente a retornar APENAS JSON?"""
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
    """
    Encontra trechos que parecem ser tentativas de JSON da plataforma mas
    não parseiam (ex.: vírgula sobrando, aspas desbalanceadas).

    Heurística: linhas começando com `{"messages"`, `{"actions"`, ou similar,
    que não foram capturadas pelo find_json_blocks (que só pega válidos).
    """
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

        # Tenta ler até balancear chaves; se não parsear, é candidato inválido
        accumulated = []
        for end_idx in range(start_idx, min(n, start_idx + 100)):
            accumulated.append(lines[end_idx])
            candidate = "\n".join(accumulated)
            opens = candidate.count("{") + candidate.count("[")
            closes = candidate.count("}") + candidate.count("]")
            if closes < opens:
                continue
            # Tenta parsear
            try:
                json.loads(candidate)
                # Se parseou, já foi capturado por find_json_blocks ou
                # foi rejeitado por filtro de plataforma — pula.
                break
            except json.JSONDecodeError as e:
                # Ainda pode ser que faltem linhas. Mas se chaves balanceiam
                # e não parseou, é inválido.
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
            "total_json_blocks": 0,
            "json_blocks_with_issues": 0,
            "invalid_json_count": 0,
            "forbidden_actions_count": 0,
            "button_misuse_count": 0,
            "carousel_misuse_count": 0,
            "markdown_in_json_count": 0,
            "send_flow_without_messages_count": 0,
            "type_inside_payload_count": 0,
            "forbidden_image_formats_count": 0,
            "generic_placeholders_count": 0,
            "forbidden_meta_sections_count": 0,
            "missing_sections_count": 0,
            "negative_examples_skipped": 0,
        },
        "json_blocks": [],
        "forbidden_actions_in_prose": [],
        "missing_sections": [],
        "json_only_instruction_present": False,
    }

    valid_blocks = find_json_blocks(content)
    invalid_blocks = find_invalid_json_candidates(content, valid_blocks)
    all_blocks = valid_blocks + invalid_blocks
    all_blocks.sort(key=lambda b: b["start_line"])

    findings["summary"]["total_json_blocks"] = len(all_blocks)

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

        skip_counting = block_report["is_negative_example"]
        if skip_counting:
            findings["summary"]["negative_examples_skipped"] += 1

        if is_invalid:
            if not skip_counting:
                findings["summary"]["invalid_json_count"] += 1
            forbidden = find_forbidden_actions_in_text(block["text"])
            if forbidden:
                block_report["issues"].append({
                    "type": "forbidden_actions",
                    "actions": forbidden,
                })
                if not skip_counting:
                    findings["summary"]["forbidden_actions_count"] += len(forbidden)
        else:
            parsed = block.get("_parsed")
            if parsed is None:
                parsed = json.loads(block["text"])

            forbidden = find_forbidden_actions_in_text(block["text"])
            if forbidden:
                block_report["issues"].append({
                    "type": "forbidden_actions",
                    "actions": forbidden,
                })
                if not skip_counting:
                    findings["summary"]["forbidden_actions_count"] += len(forbidden)

            btn_issues = check_buttons_misuse(parsed)
            if btn_issues:
                block_report["issues"].append({
                    "type": "button_misuse",
                    "details": btn_issues,
                })
                if not skip_counting:
                    findings["summary"]["button_misuse_count"] += len(btn_issues)

            car_issues = check_carousel_misuse(parsed)
            if car_issues:
                block_report["issues"].append({
                    "type": "carousel_misuse",
                    "details": car_issues,
                })
                if not skip_counting:
                    findings["summary"]["carousel_misuse_count"] += len(car_issues)

            md_issues = check_markdown_in_text(parsed)
            if md_issues:
                block_report["issues"].append({
                    "type": "markdown_in_json_text",
                    "details": md_issues,
                })
                if not skip_counting:
                    findings["summary"]["markdown_in_json_count"] += len(md_issues)

            sfwm_issues = check_send_flow_without_messages(parsed)
            if sfwm_issues:
                block_report["issues"].append({
                    "type": "send_flow_without_messages",
                    "details": sfwm_issues,
                })
                if not skip_counting:
                    findings["summary"]["send_flow_without_messages_count"] += len(sfwm_issues)

            tip_issues = check_type_inside_payload(parsed)
            if tip_issues:
                block_report["issues"].append({
                    "type": "type_inside_payload",
                    "details": tip_issues,
                })
                if not skip_counting:
                    findings["summary"]["type_inside_payload_count"] += len(tip_issues)

            img_issues = check_forbidden_image_formats(parsed)
            if img_issues:
                block_report["issues"].append({
                    "type": "forbidden_image_formats",
                    "details": img_issues,
                })
                if not skip_counting:
                    findings["summary"]["forbidden_image_formats_count"] += len(img_issues)

            placeholder_issues = check_generic_placeholders(parsed)
            if placeholder_issues:
                block_report["issues"].append({
                    "type": "generic_placeholders",
                    "details": placeholder_issues,
                })
                if not skip_counting:
                    findings["summary"]["generic_placeholders_count"] += len(placeholder_issues)

        if (block_report["issues"] or is_invalid) and not skip_counting:
            findings["summary"]["json_blocks_with_issues"] += 1

        findings["json_blocks"].append(block_report)

    findings["forbidden_actions_in_prose"] = find_forbidden_actions_in_prose(
        content, all_blocks
    )

    missing = check_required_sections(content)
    findings["missing_sections"] = missing
    findings["summary"]["missing_sections_count"] = len(missing)

    forbidden_meta = check_forbidden_meta_sections(content)
    findings["forbidden_meta_sections"] = forbidden_meta
    findings["summary"]["forbidden_meta_sections_count"] = len(forbidden_meta)

    findings["json_only_instruction_present"] = check_text_outside_json_instruction(content)

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audita prompts NexTags contra as Regras Absolutas."
    )
    parser.add_argument("prompt_file", help="Caminho do .md do prompt")
    parser.add_argument(
        "--output", "-o", help="Salvar findings em JSON neste arquivo"
    )
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
    return 0


if __name__ == "__main__":
    sys.exit(main())

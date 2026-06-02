#!/usr/bin/env python3
"""
fix_json.py — Extrai, valida e corrige a saída JSON de um agente NexTags
contra o schema do Messenger Messaging Platform.

Uso:
    python fix_json.py <input> [--output fixed.json] [--report findings.json]

Saídas:
    fixed.json     — JSON corrigido pronto pra plataforma.
    findings.json  — Lista estruturada de correções aplicadas + pendências.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# ----------------------------------------------------------------------
# Constantes do schema
# ----------------------------------------------------------------------

VALID_ATTACHMENT_TYPES = {"image", "video", "audio", "file", "template"}
VALID_TEMPLATE_TYPES = {"generic", "button"}
VALID_BUTTON_TYPES = {"web_url", "postback"}
VALID_IMAGE_ASPECT_RATIOS = {"horizontal", "square"}

# Formatos de imagem PERMITIDOS pela plataforma NexTags. Qualquer outro
# (webp, avif, svg, gif) é rejeitado.
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
FORBIDDEN_IMAGE_EXTENSIONS = {".webp", ".avif", ".svg", ".gif", ".bmp",
                              ".tiff", ".ico", ".heic", ".heif"}

# Ações canônicas + campos obrigatórios.
CANONICAL_ACTIONS: dict[str, list[str]] = {
    "add_tag":                  ["tag_name"],
    "remove_tag":               ["tag_name"],
    "set_field_value":          ["field_name", "value"],
    "unset_field_value":        ["field_name"],
    "send_flow":                ["flow_id"],
    "transfer_conversation_to": ["value"],
    "assign_conversation":      ["admin_id"],
    "unassign_conversation":    [],
}

# Aliases que o agente costuma gerar errado → forma canônica.
ACTION_ALIASES: dict[str, str] = {
    "addtag":             "add_tag",
    "add-tag":            "add_tag",
    "tag_add":            "add_tag",
    "removetag":          "remove_tag",
    "remove-tag":         "remove_tag",
    "tag_remove":         "remove_tag",
    "setfield":           "set_field_value",
    "set_field":          "set_field_value",
    "setfieldvalue":      "set_field_value",
    "unsetfield":         "unset_field_value",
    "clear_field":        "unset_field_value",
    "unsetfieldvalue":    "unset_field_value",
    "sendflow":           "send_flow",
    "send-flow":          "send_flow",
    "trigger_flow":       "send_flow",
    "flow":               "send_flow",
    "transfer":           "transfer_conversation_to",
    "transfer_to_human":  "transfer_conversation_to",
    "transferhuman":      "transfer_conversation_to",
    "assign":             "assign_conversation",
    "assignto":           "assign_conversation",
    "assign_to":          "assign_conversation",
    "unassign":           "unassign_conversation",
    "unassign_admin":     "unassign_conversation",
}

# Markdown a remover de campos text/title/subtitle.
MARKDOWN_PATTERNS = [
    (re.compile(r"\*\*(.+?)\*\*"), r"\1"),         # **bold**
    (re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)"), r"\1"),  # *italic*
    (re.compile(r"__(.+?)__"), r"\1"),             # __bold__
    (re.compile(r"`([^`]+)`"), r"\1"),             # `code`
    (re.compile(r"^#{1,6}\s+", re.MULTILINE), ""), # # headings
    (re.compile(r"~~(.+?)~~"), r"\1"),             # ~~strike~~
]


# ----------------------------------------------------------------------
# Validação de URL de imagem
# ----------------------------------------------------------------------

def validate_image_url(url: str) -> tuple[str, str | None]:
    """
    Retorna ('ok', None) se URL é válida pra imagem JPEG/PNG, ou
    (status, motivo) caso contrário.

    status ∈ {'ok', 'invalid', 'forbidden_format', 'ambiguous'}
    """
    if not isinstance(url, str) or not url.strip():
        return "invalid", "URL vazia ou ausente"
    url = url.strip()
    low = url.lower()
    if not (low.startswith("http://") or low.startswith("https://")):
        return "invalid", f"URL não-absoluta (precisa começar com http:// ou https://): '{url[:80]}'"
    # Extrai parte antes de query/fragment.
    path = low.split("?", 1)[0].split("#", 1)[0]
    # Procura a última extensão reconhecível.
    dot = path.rfind(".")
    if dot == -1:
        # Sem extensão — CDN pode estar entregando qualquer formato.
        return "ambiguous", (
            f"URL sem extensão clara ('{url[:80]}') — risco de o servidor "
            f"entregar WebP/AVIF. Validar Content-Type ou substituir por "
            f"link com extensão .jpg/.jpeg/.png."
        )
    ext = path[dot:]
    if ext in FORBIDDEN_IMAGE_EXTENSIONS:
        return "forbidden_format", (
            f"Formato proibido '{ext}' ('{url[:80]}'). Plataforma NexTags "
            f"só aceita JPEG/PNG. Converter antes de enviar."
        )
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return "ok", None
    # Extensão não-reconhecida (ex.: .aspx, .php, query disfarçada).
    return "ambiguous", (
        f"Extensão não-reconhecida '{ext}' ('{url[:80]}'). Validar "
        f"Content-Type antes de enviar — risco de WebP."
    )


# ----------------------------------------------------------------------
# Extração: pegar JSON puro de input com markdown / prosa em volta
# ----------------------------------------------------------------------

def extract_json_candidates(raw: str) -> list[str]:
    """Retorna lista de strings candidatas a JSON (sem fences/prosa)."""
    raw = raw.lstrip("﻿").strip()
    candidates: list[str] = []

    # 1) Blocos em fence ```...```
    fence_re = re.compile(r"```(?:json|JSON)?\s*\n?(.+?)\n?```", re.DOTALL)
    for m in fence_re.finditer(raw):
        candidates.append(m.group(1).strip())

    if candidates:
        return candidates

    # 2) Sem fence: tenta achar o primeiro { ... } balanceado.
    start = raw.find("{")
    if start == -1:
        return [raw]
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(raw)):
        ch = raw[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidates.append(raw[start:i + 1])
                break
    if not candidates:
        candidates.append(raw)
    return candidates


# ----------------------------------------------------------------------
# Reparos seguros de sintaxe pré-parse
# ----------------------------------------------------------------------

def repair_syntax(s: str, fixes: list[str]) -> str:
    """Aplica reparos seguros sem mudar a intenção."""
    original = s
    # Aspas curvas → retas
    if any(c in s for c in "“”„‟"):
        s = s.translate(str.maketrans({"“": '"', "”": '"', "„": '"', "‟": '"'}))
        fixes.append("aspas curvas convertidas em aspas retas")
    if any(c in s for c in "‘’‚‛"):
        s = s.translate(str.maketrans({"‘": "'", "’": "'", "‚": "'", "‛": "'"}))
        fixes.append("apóstrofos curvos convertidos em apóstrofos retos")

    # Vírgula trailing antes de } ou ]
    new = re.sub(r",(\s*[}\]])", r"\1", s)
    if new != s:
        fixes.append("vírgula sobrando antes de `}` ou `]` removida")
        s = new

    # BOM ou whitespace exótico no início
    s = s.strip()

    # Comentários // e /* */ (LLM às vezes solta).
    # CUIDADO: o regex de `//` precisa evitar URLs (https://...). Só pega
    # `//` que está em início de linha (após whitespace) — não no meio
    # de strings.
    new = re.sub(r"^\s*//[^\n]*$", "", s, flags=re.MULTILINE)
    new = re.sub(r"/\*.*?\*/", "", new, flags=re.DOTALL)
    if new != s:
        fixes.append("comentários removidos (JSON não suporta)")
        s = new

    if s != original and not fixes:
        fixes.append("ajustes leves de whitespace")
    return s


# ----------------------------------------------------------------------
# Validação + correção semântica
# ----------------------------------------------------------------------

def strip_markdown(text: str) -> tuple[str, bool]:
    """Remove marcação Markdown de strings de campos de texto."""
    cleaned = text
    for pat, repl in MARKDOWN_PATTERNS:
        cleaned = pat.sub(repl, cleaned)
    return cleaned, cleaned != text


def normalize_action_name(name: str) -> str:
    """Mapeia variação → forma canônica."""
    key = name.strip().lower().replace(" ", "_")
    if key in CANONICAL_ACTIONS:
        return key
    return ACTION_ALIASES.get(key, name)


def fix_message_object(msg: Any, fixes: list[str], pending: list[str],
                       path: str) -> Any:
    """Corrige um objeto `message` (o conteúdo dentro de {message: ...})."""
    if not isinstance(msg, dict):
        pending.append(f"{path}: `message` não é objeto — não foi possível corrigir.")
        return msg

    # Texto simples
    if "text" in msg and isinstance(msg["text"], str):
        cleaned, changed = strip_markdown(msg["text"])
        if changed:
            fixes.append(f"{path}.text: markdown removido")
            msg["text"] = cleaned

    # Attachment
    if "attachment" in msg:
        att = msg["attachment"]
        if not isinstance(att, dict):
            pending.append(f"{path}.attachment: não é objeto.")
            return msg

        # Fix crítico: se `type` veio DENTRO de `payload`, mover pra FORA.
        # A plataforma NexTags exige `type` ao lado de `payload`, não dentro.
        payload = att.get("payload")
        if isinstance(payload, dict) and "type" in payload and "type" not in att:
            moved = payload.pop("type")
            att["type"] = moved
            fixes.append(
                f"{path}.attachment: campo `type` estava DENTRO de "
                f"`payload` — movido pra fora (regra NexTags)"
            )

        atype = att.get("type")
        if atype not in VALID_ATTACHMENT_TYPES:
            pending.append(
                f"{path}.attachment.type='{atype}' não é suportado. "
                f"Válidos: {sorted(VALID_ATTACHMENT_TYPES)}."
            )
            return msg

        if not isinstance(payload, dict):
            pending.append(f"{path}.attachment.payload: não é objeto.")
            return msg

        # Mídia simples (image/video/audio/file)
        if atype in {"image", "video", "audio", "file"}:
            url = payload.get("url")
            if not url or not isinstance(url, str) or not url.strip():
                pending.append(
                    f"{path}.attachment(payload).url ausente — "
                    f"necessário informar URL do {atype}."
                )
            elif atype == "image":
                # Valida formato — NexTags só aceita JPEG/PNG.
                status, reason = validate_image_url(url)
                if status == "forbidden_format":
                    pending.append(
                        f"{path}.attachment.payload.url: {reason} "
                        f"Recomenda-se REMOVER a imagem e manter só texto/botão."
                    )
                elif status == "ambiguous":
                    pending.append(
                        f"{path}.attachment.payload.url: {reason}"
                    )
                elif status == "invalid":
                    pending.append(
                        f"{path}.attachment.payload.url: {reason}"
                    )

        # Template
        if atype == "template":
            ttype = payload.get("template_type")
            if ttype not in VALID_TEMPLATE_TYPES:
                pending.append(
                    f"{path}.template_type='{ttype}' inválido. "
                    f"Válidos: {sorted(VALID_TEMPLATE_TYPES)}."
                )
                return msg

            if ttype == "generic":
                elements = payload.get("elements")
                if not isinstance(elements, list):
                    pending.append(f"{path}.elements: não é array.")
                    return msg
                if len(elements) == 0:
                    pending.append(
                        f"{path}: carrossel sem elementos — bloco precisa "
                        f"ser removido ou ter ≥ 2 cards."
                    )
                elif len(elements) == 1:
                    pending.append(
                        f"{path}: carrossel com 1 card só (plataforma exige ≥ 2). "
                        f"Considere converter pra attachment 'image' ou "
                        f"adicionar um segundo card."
                    )
                # aspect ratio
                ar = payload.get("image_aspect_ratio")
                if ar is not None and ar not in VALID_IMAGE_ASPECT_RATIOS:
                    fixes.append(
                        f"{path}.image_aspect_ratio='{ar}' → 'horizontal'"
                    )
                    payload["image_aspect_ratio"] = "horizontal"

                # Limpa cada elemento
                for idx, el in enumerate(elements):
                    el_path = f"{path}.elements[{idx}]"
                    if not isinstance(el, dict):
                        pending.append(f"{el_path}: não é objeto.")
                        continue
                    for field in ("title", "subtitle"):
                        if field in el and isinstance(el[field], str):
                            cleaned, changed = strip_markdown(el[field])
                            if changed:
                                fixes.append(f"{el_path}.{field}: markdown removido")
                                el[field] = cleaned
                    if "image_url" in el:
                        url = el["image_url"]
                        if not url or not isinstance(url, str):
                            pending.append(f"{el_path}.image_url ausente.")
                        else:
                            status, reason = validate_image_url(url)
                            if status != "ok":
                                pending.append(
                                    f"{el_path}.image_url: {reason}"
                                )
                    btns = el.get("buttons")
                    if isinstance(btns, list):
                        for bidx, b in enumerate(btns):
                            fix_button(b, fixes, pending,
                                       f"{el_path}.buttons[{bidx}]")

            elif ttype == "button":
                if "text" in payload and isinstance(payload["text"], str):
                    cleaned, changed = strip_markdown(payload["text"])
                    if changed:
                        fixes.append(f"{path}.text: markdown removido")
                        payload["text"] = cleaned
                btns = payload.get("buttons")
                if not isinstance(btns, list) or not btns:
                    pending.append(
                        f"{path}: template `button` sem botões — "
                        f"considere converter pra texto simples."
                    )
                else:
                    for bidx, b in enumerate(btns):
                        fix_button(b, fixes, pending,
                                   f"{path}.buttons[{bidx}]")
    return msg


def fix_button(btn: Any, fixes: list[str], pending: list[str],
               path: str) -> None:
    if not isinstance(btn, dict):
        pending.append(f"{path}: botão não é objeto.")
        return
    btype = btn.get("type")
    if btype not in VALID_BUTTON_TYPES:
        pending.append(
            f"{path}.type='{btype}' inválido. "
            f"Válidos: {sorted(VALID_BUTTON_TYPES)}."
        )
        return
    if btype == "web_url":
        if not btn.get("url"):
            pending.append(f"{path}: botão `web_url` sem `url`.")
    elif btype == "postback":
        if not btn.get("payload"):
            pending.append(f"{path}: botão `postback` sem `payload` (flow_id).")
    if "title" in btn and isinstance(btn["title"], str):
        cleaned, changed = strip_markdown(btn["title"])
        if changed:
            fixes.append(f"{path}.title: markdown removido")
            btn["title"] = cleaned


def fix_messages_array(messages: Any, fixes: list[str],
                       pending: list[str]) -> list[Any]:
    if not isinstance(messages, list):
        # tentar embrulhar se for um único objeto de mensagem
        if isinstance(messages, dict):
            fixes.append("`messages` era objeto único — embrulhado em array")
            messages = [messages]
        else:
            pending.append("`messages` não é array nem objeto — descartado.")
            return []

    out: list[Any] = []
    for idx, item in enumerate(messages):
        path = f"messages[{idx}]"
        # typing indicator
        if isinstance(item, bool):
            pending.append(f"{path}: booleano onde se esperava inteiro/objeto.")
            continue
        if isinstance(item, (int, float)) and not isinstance(item, bool):
            val = int(item)
            if val < 1:
                fixes.append(f"{path}: typing indicator < 1 → clampado em 1")
                val = 1
            elif val > 30:
                fixes.append(f"{path}: typing indicator > 30 → clampado em 30")
                val = 30
            out.append(val)
            continue
        if isinstance(item, str):
            # talvez seja "4" string — tenta numérico
            if item.strip().isdigit():
                val = max(1, min(30, int(item.strip())))
                fixes.append(f"{path}: typing indicator era string '{item}' → inteiro {val}")
                out.append(val)
                continue
            # string solta no array messages → embrulha como texto
            fixes.append(f"{path}: string solta embrulhada em {{message:{{text:...}}}}")
            out.append({"message": {"text": item}})
            continue
        if isinstance(item, dict):
            # Tentar identificar wrappers ausentes
            if "message" not in item:
                # talvez seja o objeto message direto
                if any(k in item for k in ("text", "attachment")):
                    fixes.append(f"{path}: faltava wrapper `message` — embrulhado")
                    item = {"message": item}
                else:
                    pending.append(f"{path}: sem chave `message` e sem campos reconhecíveis.")
                    continue
            item["message"] = fix_message_object(
                item["message"], fixes, pending, f"{path}.message"
            )
            out.append(item)
            continue
        pending.append(f"{path}: tipo inesperado ({type(item).__name__}).")
    return out


def fix_actions_array(actions: Any, fixes: list[str],
                      pending: list[str]) -> list[dict]:
    if not isinstance(actions, list):
        if isinstance(actions, dict):
            fixes.append("`actions` era objeto único — embrulhado em array")
            actions = [actions]
        else:
            pending.append("`actions` não é array — descartado.")
            return []
    out: list[dict] = []
    for idx, act in enumerate(actions):
        path = f"actions[{idx}]"
        if not isinstance(act, dict):
            pending.append(f"{path}: não é objeto.")
            continue
        name = act.get("action")
        if not isinstance(name, str):
            pending.append(f"{path}: campo `action` ausente ou não-string.")
            continue
        canonical = normalize_action_name(name)
        if canonical != name:
            fixes.append(f"{path}.action: '{name}' → '{canonical}'")
            act["action"] = canonical
            name = canonical
        if name not in CANONICAL_ACTIONS:
            pending.append(
                f"{path}.action='{name}' não é uma ação reconhecida. "
                f"Válidas: {sorted(CANONICAL_ACTIONS.keys())}."
            )
            continue
        # Campos obrigatórios
        for req in CANONICAL_ACTIONS[name]:
            if req not in act or act[req] in (None, "", []):
                pending.append(f"{path}: ação `{name}` sem campo obrigatório `{req}`.")
        # Caso especial: transfer_conversation_to.value deve ser "human"
        if name == "transfer_conversation_to" and act.get("value") not in (None, ""):
            if act["value"] != "human":
                fixes.append(
                    f"{path}.value='{act['value']}' → 'human' (único valor suportado)"
                )
                act["value"] = "human"
        out.append(act)
    return out


# ----------------------------------------------------------------------
# Pipeline principal
# ----------------------------------------------------------------------

def process_one(raw_json: str, fixes: list[str], pending: list[str],
                syntax_fixes: list[str]) -> dict | None:
    """Recebe string de um JSON; devolve objeto corrigido ou None."""
    repaired = repair_syntax(raw_json, syntax_fixes)
    try:
        data = json.loads(repaired)
    except json.JSONDecodeError as e:
        pending.append(
            f"JSON inválido mesmo após reparos automáticos: {e.msg} "
            f"(linha {e.lineno}, coluna {e.colno}). Revisar manualmente."
        )
        return None

    if not isinstance(data, dict):
        pending.append("Raiz do JSON não é objeto — esperado `{messages, actions}`.")
        return None

    fixed: dict[str, Any] = {}

    has_messages = "messages" in data
    has_actions = "actions" in data

    if not has_messages and not has_actions:
        # talvez seja o conteúdo de message direto (text / attachment)
        if any(k in data for k in ("text", "attachment")):
            fixes.append("Raiz era `message` solto — embrulhado em `{messages:[{message:…}]}`")
            data = {"messages": [{"message": data}]}
            has_messages = True
        else:
            pending.append(
                "Raiz não tem `messages` nem `actions`. Estrutura desconhecida — "
                "necessário rever manualmente."
            )
            return None

    if has_messages:
        new_messages = fix_messages_array(data["messages"], fixes, pending)
        if new_messages:
            fixed["messages"] = new_messages
    if has_actions:
        new_actions = fix_actions_array(data["actions"], fixes, pending)
        if new_actions:
            fixed["actions"] = new_actions

    if not fixed:
        pending.append("Após validação, nenhum bloco utilizável sobrou.")
        return None
    return fixed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="Arquivo de entrada (txt/json/md).")
    ap.add_argument("--output", default="fixed.json",
                    help="Caminho do JSON corrigido.")
    ap.add_argument("--report", default="findings.json",
                    help="Caminho do relatório estruturado.")
    args = ap.parse_args()

    raw = Path(args.input).read_text(encoding="utf-8", errors="replace")
    candidates = extract_json_candidates(raw)

    fixes: list[str] = []
    pending: list[str] = []
    syntax_fixes: list[str] = []
    fixed_blocks: list[dict] = []

    if len(candidates) > 1:
        fixes.append(f"{len(candidates)} blocos JSON detectados no input")
    for idx, cand in enumerate(candidates):
        block_fixes: list[str] = []
        block_pending: list[str] = []
        block_syntax: list[str] = []
        result = process_one(cand, block_fixes, block_pending, block_syntax)
        prefix = f"[bloco {idx + 1}] " if len(candidates) > 1 else ""
        fixes.extend(prefix + f for f in block_fixes)
        pending.extend(prefix + p for p in block_pending)
        syntax_fixes.extend(prefix + s for s in block_syntax)
        if result is not None:
            fixed_blocks.append(result)

    # Saída — se houver apenas 1 bloco, escreve direto; senão, array.
    if len(fixed_blocks) == 1:
        out_obj: Any = fixed_blocks[0]
    else:
        out_obj = fixed_blocks

    Path(args.output).write_text(
        json.dumps(out_obj, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    findings = {
        "summary": {
            "blocks_in":            len(candidates),
            "blocks_out":           len(fixed_blocks),
            "syntax_repairs":       len(syntax_fixes),
            "semantic_fixes":       len(fixes),
            "pending_human_review": len(pending),
        },
        "syntax_repairs":       syntax_fixes,
        "semantic_fixes":       fixes,
        "pending_human_review": pending,
    }
    Path(args.report).write_text(
        json.dumps(findings, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(findings["summary"], ensure_ascii=False, indent=2))
    return 0 if not pending else 0  # exit 0 mesmo com pendências


if __name__ == "__main__":
    sys.exit(main())

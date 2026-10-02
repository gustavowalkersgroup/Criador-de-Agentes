#!/usr/bin/env python3
"""
octobercut.py — conta, audita e funde mensagens de agentes NexTags para a
cobrança da Meta por mensagem de serviço (vigente desde 01/10/2026).

Subcomandos:
  audit    <prompt.md|.txt>   Varre o prompt: exemplos JSON (bolhas por exemplo)
                              e instruções em prosa que multiplicam mensagens.
  merge    <saida.json|->     Funde a saída JSON de runtime em menos bolhas,
                              sem inventar conteúdo.
  estimate --before N --after M [--rate R] [--volume V]
                              Estima economia em R$.

Só stdlib. Python 3.8+.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BUTTON_TEXT_MAX = 1024   # body de mensagem interativa no WhatsApp
TEXT_SOFT_MAX = 1000     # legibilidade (meta da regra OC-1)
TEXT_HARD_MAX = 4096     # limite de texto simples no WhatsApp
DEFAULT_RATE_BRL = 0.035
PARAGRAPH = "\n\n"
BLOCK_MARKER = "FORMATO ECONÔMICO DE RESPOSTA (OCTOBERCUT)"


# --------------------------------------------------------------------------
# Classificação de mensagens
# --------------------------------------------------------------------------

def kind_of(item: Any) -> str:
    """Tipo de um item de `messages`: typing | text | button | image | carousel | other."""
    if isinstance(item, bool):
        return "other"
    if isinstance(item, int):
        return "typing"
    if not isinstance(item, dict) or not isinstance(item.get("message"), dict):
        return "other"
    msg = item["message"]
    if set(msg.keys()) == {"text"} and isinstance(msg["text"], str):
        return "text"
    att = msg.get("attachment")
    if isinstance(att, dict):
        if att.get("type") == "template" and isinstance(att.get("payload"), dict):
            tt = att["payload"].get("template_type")
            if tt == "button":
                return "button"
            if tt == "generic":
                return "carousel"
        if att.get("type") in ("image", "video", "audio", "file"):
            return "image"
    return "other"


def count_bubbles(messages: List[Any]) -> int:
    """Mensagens cobradas = itens que não são typing indicator."""
    return sum(1 for m in messages if kind_of(m) != "typing")


def _button_text(item: Dict[str, Any]) -> str:
    return item["message"]["attachment"]["payload"].get("text") or ""


def _set_button_text(item: Dict[str, Any], text: str) -> None:
    item["message"]["attachment"]["payload"]["text"] = text


def _join(*parts: str) -> str:
    return PARAGRAPH.join(p.strip() for p in parts if p and p.strip())


# --------------------------------------------------------------------------
# merge
# --------------------------------------------------------------------------

def merge_messages(messages: List[Any]) -> Tuple[List[Any], List[str]]:
    """Funde `messages` no menor número de bolhas sem inventar conteúdo.

    Regras:
    - typing indicator (inteiro) é removido;
    - textos consecutivos viram um só, separados por parágrafo;
    - texto antes de um button template entra no começo do `text` do botão;
    - texto depois de um button template entra no fim do `text` do botão;
    - texto antes de imagem/carrossel passa para depois da mídia (vai para a
      próxima mensagem textual), porque o padrão é foto + 1 mensagem;
    - nada passa de 1024 (botão) ou 4096 (texto) caracteres: se não couber,
      a bolha fica separada.
    """
    notes: List[str] = []
    out: List[Any] = []
    buf: List[str] = []  # textos pendentes ainda não emitidos

    removed_typing = sum(1 for m in messages if kind_of(m) == "typing")
    if removed_typing:
        notes.append(f"Removido(s) {removed_typing} typing indicator(s).")

    def flush() -> None:
        if not buf:
            return
        text = buf[0]
        for nxt in buf[1:]:
            cand = _join(text, nxt)
            if len(cand) <= TEXT_HARD_MAX:
                text = cand
            else:
                out.append({"message": {"text": text}})
                text = nxt
        out.append({"message": {"text": text}})
        if len(buf) > 1:
            notes.append(f"Juntado(s) {len(buf)} textos consecutivos em uma bolha.")
        buf.clear()

    def last_button() -> Optional[Dict[str, Any]]:
        return out[-1] if out and kind_of(out[-1]) == "button" else None

    for item in messages:
        k = kind_of(item)
        if k == "typing":
            continue
        if k == "text":
            text = item["message"]["text"]
            btn = last_button()
            if btn is not None and not buf:
                cand = _join(_button_text(btn), text)
                if len(cand) <= BUTTON_TEXT_MAX:
                    _set_button_text(btn, cand)
                    notes.append("Texto seguinte embutido no text do button template.")
                    continue
            buf.append(text)
        elif k == "button":
            item = json.loads(json.dumps(item))
            if buf:
                pre = _join(*buf)
                cand = _join(pre, _button_text(item))
                if len(cand) <= BUTTON_TEXT_MAX:
                    _set_button_text(item, cand)
                    notes.append("Texto anterior embutido no text do button template.")
                    buf.clear()
                else:
                    flush()
            out.append(item)
        elif k in ("image", "carousel"):
            if buf:
                notes.append("Texto que vinha antes da mídia passou para depois dela.")
            out.append(item)
        else:
            flush()
            out.append(item)
    flush()
    return out, notes


def merge_payload(payload: Any) -> Tuple[Any, Dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("messages"), list):
        return payload, {"before": None, "after": None, "notes": ["Sem array messages; nada a fundir."]}
    before = count_bubbles(payload["messages"])
    merged, notes = merge_messages(payload["messages"])
    new = dict(payload)
    new["messages"] = merged
    return new, {"before": before, "after": count_bubbles(merged), "notes": notes}


# --------------------------------------------------------------------------
# audit
# --------------------------------------------------------------------------

def extract_json_examples(text: str) -> List[Tuple[int, str]]:
    """Acha objetos JSON que começam com {"messages" ou {"actions" (com espaços)."""
    found: List[Tuple[int, str]] = []
    for m in re.finditer(r'\{\s*"(?:messages|actions)"\s*:', text):
        start = m.start()
        if found and start < found[-1][0] + len(found[-1][1]):
            continue  # dentro de um exemplo já capturado
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            ch = text[i]
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
                    found.append((start, text[start:i + 1]))
                    break
    return found


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


NEGATION = re.compile(
    r"\b(nunca|não use|nao use|não divida|nao divida|proibid|evite|sem typing|"
    r"não mande|nao mande|não envie|nao envie|não pergunte|nao pergunte|"
    r"sem perguntar|sem pedir|não confundir|nao confundir|não fique|nao fique|no máximo|no maximo|em vez de|ao invés de|antes:|antigo|substitu)",
    re.IGNORECASE,
)

PROSE_RULES: List[Tuple[str, str, str, str]] = [
    # (id, severidade, regex, mensagem)
    ("typing_como_padrao", "block",
     r"separad[oa]s?\s+por\s+(o\s+)?(typing|4\b)|typing\s*(indicator\s*)?4\b.*(entre|pausa|bolha|bloco)"
     r"|pausa natural",
     "Instrui a separar a resposta com typing 4 (cada bolha é cobrada). OC-1."),
    ("blocos_multiplos", "block",
     r"\b(2|3|4|dois|três|tres|quatro)\s+(blocos|bolhas|balões|baloes|mensagens)\b",
     "Instrui a responder em vários blocos/bolhas. OC-1/OC-5."),
    ("nao_misturar_midia", "block",
     r"nunca\s+misture\s+texto\s+com\s+m[ií]dia",
     "Proíbe juntar texto e link no mesmo bloco; agora a frase vai dentro do botão. OC-5/OC-6."),
    ("perguntar_nome", "warn",
     r"pergunt\w*\s+(o\s+)?nome|qual\s+(é\s+)?(o\s+)?seu\s+nome|como\s+(você|vc)\s+se\s+chama",
     "Pede o nome do cliente; só peça se um processo exigir, junto com outros dados. OC-4."),
    ("uma_pergunta_por_vez", "warn",
     r"uma\s+pergunta\s+(relevante\s+)?(por\s+vez|de\s+cada\s+vez)|uma\s+coisa\s+por\s+vez",
     "Uma pergunta por vez multiplica as trocas; agrupe as perguntas. OC-3."),
    ("mensagem_de_espera", "warn",
     r"deixa\s+eu\s+(verificar|ver|checar|consultar)|um\s+momento|s[oó]\s+um\s+minut|aguarde\s+(um|enquanto)",
     "Mensagem de espera gera cobrança sem valor; consulte e responda uma vez. OC-7."),
    ("dividir_resposta", "warn",
     r"(divid|quebr|fracion)\w*\s+(a\s+|sua\s+)?(resposta|mensagem|texto)\s+em|nova\s+bolha|várias\s+mensagens|varias\s+mensagens",
     "Sugere dividir a resposta em várias bolhas. OC-1."),
    ("despedida_avulsa", "warn",
     r"posso\s+(te\s+)?ajudar\s+em\s+(algo|mais)|mais\s+alguma\s+coisa\s*\?",
     "Pergunta de encerramento costuma virar bolha extra; feche na própria resposta. OC-8."),
]


def audit_examples(text: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    findings: List[Dict[str, Any]] = []
    examples: List[Dict[str, Any]] = []
    for pos, raw in extract_json_examples(text):
        line = _line_of(text, pos)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            examples.append({"line": line, "parsed": False, "error": str(e)})
            continue
        msgs = data.get("messages") if isinstance(data, dict) else None
        if not isinstance(msgs, list):
            examples.append({"line": line, "parsed": True, "bubbles": 0, "merged_bubbles": 0})
            continue
        kinds = [kind_of(m) for m in msgs]
        bubbles = count_bubbles(msgs)
        merged, _ = merge_messages(msgs)
        merged_bubbles = count_bubbles(merged)
        examples.append({"line": line, "parsed": True, "bubbles": bubbles,
                         "merged_bubbles": merged_bubbles, "kinds": kinds})

        if "typing" in kinds:
            findings.append({"id": "exemplo_com_typing", "severity": "block", "line": line,
                             "message": f"Exemplo usa typing indicator ({kinds.count('typing')}x). OC-1."})
        if merged_bubbles < bubbles:
            findings.append({"id": "exemplo_fundivel", "severity": "block", "line": line,
                             "message": f"Exemplo com {bubbles} bolhas pode virar {merged_bubbles}. "
                                        "Rode `octobercut.py merge` nele. OC-1/OC-5/OC-6."})
        for m in msgs:
            k = kind_of(m)
            if k == "button" and len(_button_text(m)) > BUTTON_TEXT_MAX:
                findings.append({"id": "botao_texto_longo", "severity": "block", "line": line,
                                 "message": f"text do button template com {len(_button_text(m))} caracteres "
                                            f"(máx. {BUTTON_TEXT_MAX})."})
            if k == "text" and len(m["message"]["text"]) > TEXT_SOFT_MAX:
                findings.append({"id": "texto_longo", "severity": "warn", "line": line,
                                 "message": f"Texto com {len(m['message']['text'])} caracteres "
                                            f"(mire até ~{TEXT_SOFT_MAX})."})
    return findings, examples


def audit_prose(text: str) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    # Não varrer o JSON dos exemplos como prosa.
    masked = text
    for pos, raw in extract_json_examples(text):
        masked = masked[:pos] + re.sub(r"[^\n]", " ", raw) + masked[pos + len(raw):]
    for lineno, line in enumerate(masked.splitlines(), start=1):
        if not line.strip() or NEGATION.search(line):
            continue
        for rid, sev, rx, msg in PROSE_RULES:
            if re.search(rx, line, re.IGNORECASE):
                findings.append({"id": rid, "severity": sev, "line": lineno,
                                 "message": msg, "excerpt": line.strip()[:160]})
    return findings


def audit_text(text: str) -> Dict[str, Any]:
    ex_findings, examples = audit_examples(text)
    findings = ex_findings + audit_prose(text)
    if BLOCK_MARKER not in text:
        findings.append({"id": "sem_bloco_octobercut", "severity": "block", "line": None,
                         "message": "Prompt sem o bloco canônico 'FORMATO ECONÔMICO DE RESPOSTA "
                                    "(OCTOBERCUT)' (references/bloco_octobercut.md)."})
    findings.sort(key=lambda f: (f["line"] is None, f["line"] or 0))
    parsed = [e for e in examples if e.get("parsed") and e.get("bubbles")]
    return {
        "summary": {
            "blocks": sum(1 for f in findings if f["severity"] == "block"),
            "warnings": sum(1 for f in findings if f["severity"] == "warn"),
            "examples": len(examples),
            "bubbles_in_examples": sum(e["bubbles"] for e in parsed),
            "bubbles_after_merge": sum(e["merged_bubbles"] for e in parsed),
        },
        "findings": findings,
        "examples": examples,
    }


# --------------------------------------------------------------------------
# estimate
# --------------------------------------------------------------------------

def estimate(before: float, after: float, rate: float, volume: int) -> Dict[str, Any]:
    cost_b, cost_a = before * rate, after * rate
    pct = (1 - after / before) * 100 if before else 0.0
    return {
        "rate_brl": rate,
        "per_attendance": {"before": round(cost_b, 4), "after": round(cost_a, 4)},
        "reduction_pct": round(pct, 1),
        "volume": volume,
        "saving_brl": round((cost_b - cost_a) * volume, 2),
    }


def brl(v: float, digits: int = 2) -> str:
    return f"R$ {v:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def cmd_audit(args: argparse.Namespace) -> int:
    result = audit_text(_read(args.input))
    s = result["summary"]
    print(f"OctoberCut audit — {s['blocks']} bloqueio(s), {s['warnings']} aviso(s)")
    print(f"Exemplos JSON: {s['examples']} | bolhas nos exemplos: {s['bubbles_in_examples']}"
          f" → {s['bubbles_after_merge']} após fusão")
    for f in result["findings"]:
        where = f"L{f['line']}" if f["line"] else "--"
        tag = "BLOCK" if f["severity"] == "block" else "warn "
        print(f"  [{tag}] {where:>6} {f['id']}: {f['message']}")
        if f.get("excerpt"):
            print(f"           › {f['excerpt']}")
    if args.report:
        Path(args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if s["blocks"] else 0


def cmd_merge(args: argparse.Namespace) -> int:
    raw = _read(args.input)
    candidates = extract_json_examples(raw) or [(0, raw.strip())]
    outputs, total_b, total_a = [], 0, 0
    for _, chunk in candidates:
        try:
            data = json.loads(chunk)
        except json.JSONDecodeError as e:
            print(f"JSON inválido (rode a nextags-json-fixer antes): {e}", file=sys.stderr)
            return 2
        new, info = merge_payload(data)
        outputs.append(new)
        if info["before"] is not None:
            total_b += info["before"]
            total_a += info["after"]
        for n in dict.fromkeys(info["notes"]):
            print(f"  • {n}", file=sys.stderr)
    print(f"Bolhas: {total_b} → {total_a}", file=sys.stderr)
    text = "\n".join(json.dumps(o, ensure_ascii=False, separators=(",", ":")) for o in outputs)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


def cmd_estimate(args: argparse.Namespace) -> int:
    r = estimate(args.before, args.after, args.rate, args.volume)
    print(f"Por atendimento: {brl(r['per_attendance']['before'])} → {brl(r['per_attendance']['after'])}"
          f" (−{r['reduction_pct']}%)")
    print(f"Economia a cada {args.volume} atendimentos: {brl(r['saving_brl'])}"
          f" (tarifa {brl(args.rate, 3)}/msg — confirme no rate card vigente da Meta)")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("audit", help="audita um prompt .md")
    a.add_argument("input", help="arquivo do prompt ou - para stdin")
    a.add_argument("--report", help="grava o resultado completo em JSON")
    a.set_defaults(func=cmd_audit)

    m = sub.add_parser("merge", help="funde a saída JSON de runtime")
    m.add_argument("input", help="arquivo com 1+ JSONs de saída ou - para stdin")
    m.add_argument("--output", help="arquivo de saída (padrão: stdout)")
    m.set_defaults(func=cmd_merge)

    e = sub.add_parser("estimate", help="estima economia em R$")
    e.add_argument("--before", type=float, required=True, help="mensagens por atendimento antes")
    e.add_argument("--after", type=float, required=True, help="mensagens por atendimento depois")
    e.add_argument("--rate", type=float, default=DEFAULT_RATE_BRL, help="R$ por mensagem")
    e.add_argument("--volume", type=int, default=1000, help="atendimentos")
    e.set_defaults(func=cmd_estimate)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

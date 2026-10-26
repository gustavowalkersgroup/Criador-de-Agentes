#!/usr/bin/env python3
"""Cliente da API NexTags (https://app.nextagsai.com.br/api). So stdlib.

Token: env NEXTAGS_TOKEN ou --token. E POR CONTA (por cliente). Nunca e gravado em disco.
Escrita (POST/PUT/PATCH/DELETE) so e enviada com --yes; sem ele o script mostra o que enviaria (dry-run).

  call METHOD PATH [-q k=v] [--json '{...}' | --json-file f] [--form k=v] [--yes] [--out f]
  whoami                      GET /accounts/me (confirma em qual conta o token cai)
  snapshot --dir D            GET de leitura sem parametro em todos os recursos da conta -> D/*.json
  backup-agents --dir D       salva config + prompt (.md) de cada agente IA
  spec-check [--update]       compara o swagger oficial ao references/swagger.json (drift da doc)
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://app.nextagsai.com.br/api"
# A pagina /api/swagger/ carrega ESTE arquivo. O /api/swagger/swagger.json e a versao Chatrace (desatualizada).
SPEC_URL = "https://app.nextagsai.com.br/php/images.php?id=swagger.json"
SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
REF_DIR = SKILL_DIR / "references"
METHODS = ("get", "post", "put", "patch", "delete")
ROOTS = "accounts|agents|contacts|pipelines|products|calendars|broadcasts"
SNAPSHOT_GETS = [
    "/accounts/me", "/accounts/admins", "/accounts/teams", "/accounts/tags", "/accounts/flows",
    "/accounts/custom_fields", "/accounts/integrations", "/agents", "/agents/functions", "/agents/mcp",
    "/agents/files", "/pipelines", "/calendars", "/broadcasts",
]


def token_of(args):
    t = (args.token or os.environ.get("NEXTAGS_TOKEN") or "").strip()
    if not t:
        sys.exit("Falta o token: defina NEXTAGS_TOKEN ou use --token (o token e POR CONTA/cliente).")
    return t


def norm_path(p):
    """Aceita 'accounts/me' ou '/accounts/me'. Desfaz a conversao de caminho do Git Bash (C:/Program Files/Git/accounts/me)."""
    m = re.search(rf"(?:^|/)({ROOTS})(/.*)?$", p.replace("\\", "/"))
    if m and (":" in p or not p.startswith("/")):
        return "/" + m.group(1) + (m.group(2) or "")
    return p if p.startswith("/") else "/" + p


def http(method, url, token=None, body=None, form=None):
    headers = {"Accept": "application/json"}
    if token:
        headers["X-ACCESS-TOKEN"] = token
    data = None
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            status, raw = r.status, r.read()
    except urllib.error.HTTPError as e:
        status, raw = e.code, e.read()
    except urllib.error.URLError as e:
        sys.exit(f"ERRO de rede em {method} {url}: {e.reason}")
    text = raw.decode("utf-8", "replace")
    try:
        parsed = json.loads(text) if text.strip() else None
    except ValueError:
        parsed = text
    return status, parsed


def api(method, path, token, query=None, **kw):
    url = BASE + path + ("?" + urllib.parse.urlencode(query) if query else "")
    return http(method, url, token, **kw)


def unwrap(resp):
    return resp.get("data", resp) if isinstance(resp, dict) else resp


def kv(pairs):
    out = {}
    for s in pairs or []:
        if "=" not in s:
            sys.exit(f"Esperava k=v, recebi: {s}")
        k, v = s.split("=", 1)
        out[k] = v
    return out


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2) if not isinstance(obj, str) else obj


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:40] or "sem-nome"


# ---------------------------------------------------------------- comandos

def cmd_call(a):
    method = a.method.upper()
    path = norm_path(a.path)
    query = kv(a.query)
    body = form = None
    if a.json:
        body = json.loads(a.json)
    elif a.json_file:
        body = json.loads(pathlib.Path(a.json_file).read_text(encoding="utf-8-sig"))
    if a.form:
        form = kv(a.form)
    if method not in ("GET", "HEAD") and not a.yes:
        print(f"DRY-RUN (nada enviado). Enviaria: {method} {BASE}{path}" + (f"?{urllib.parse.urlencode(query)}" if query else ""))
        if body is not None:
            print(dump(body)[:4000])
        if form is not None:
            print("form:", form)
        print("Rode de novo com --yes SO depois que o usuario autorizar esta escrita.")
        return 0
    status, resp = api(method, path, token_of(a), query, body=body, form=form)
    text = dump(resp)
    if a.out:
        pathlib.Path(a.out).write_text(text, encoding="utf-8")
        print(f"HTTP {status} -> {a.out} ({len(text)} chars)")
    else:
        print(f"HTTP {status}")
        print(text if len(text) <= a.max_chars else text[: a.max_chars] + f"\n... [truncado: {len(text)} chars; use --out arquivo]")
    return 0 if status < 400 else 1


def cmd_whoami(a):
    status, resp = api("GET", "/accounts/me", token_of(a))
    print(f"HTTP {status}\n{dump(resp)}")
    return 0 if status < 400 else 1


def cmd_snapshot(a):
    token = token_of(a)
    d = pathlib.Path(a.dir)
    d.mkdir(parents=True, exist_ok=True)
    bad = 0
    for p in SNAPSHOT_GETS:
        status, resp = api("GET", p, token)
        data = unwrap(resp)
        n = len(data) if isinstance(data, list) else "-"
        (d / (p.strip("/").replace("/", "_") + ".json")).write_text(dump(resp), encoding="utf-8")
        print(f"{status}  itens={n!s:<4} {p}")
        bad += status >= 400
    print(f"Salvo em {d}. Falhas: {bad}")
    return 1 if bad else 0


def cmd_backup_agents(a):
    token = token_of(a)
    d = pathlib.Path(a.dir)
    d.mkdir(parents=True, exist_ok=True)
    status, resp = api("GET", "/agents", token)
    agents = unwrap(resp)
    if status >= 400 or not isinstance(agents, list):
        sys.exit(f"Falha ao listar agentes: HTTP {status} {dump(resp)[:300]}")
    stamp = datetime.date.today().isoformat()
    for ag in agents:
        st, full = api("GET", f"/agents/{ag['id']}", token)
        base = f"{ag['id']}_{slug(ag.get('name'))}_{stamp}"
        (d / f"{base}.json").write_text(dump(full), encoding="utf-8")
        cfg = unwrap(full)  # o prompt fica em full["data"]["prompt"] (confirmado ao vivo em 26/10/2026)
        prompt = cfg.get("prompt") if isinstance(cfg, dict) else None
        if prompt:
            (d / f"{base}.prompt.md").write_text(prompt, encoding="utf-8")
        print(f"{st}  {ag['id']}  {ag.get('name')}  prompt={len(prompt) if prompt else 'SEM'} chars")
    print(f"{len(agents)} agente(s) em {d}")
    return 0


# ---------------------------------------------------------------- spec / referencia

def ops_of(spec):
    return {(m.upper(), p): o for p, ms in spec["paths"].items() for m, o in ms.items() if m in METHODS}


def typ(v):
    if "$ref" in v:
        return v["$ref"].split("/")[-1]
    t = v.get("type", "object")
    return f"array<{typ(v.get('items', {}))}>" if t == "array" else t


def inline(s, depth=0):
    if not s:
        return ""
    if "$ref" in s:
        return s["$ref"].split("/")[-1]
    if s.get("type") == "array":
        return f"[{inline(s.get('items', {}), depth + 1)}]"
    if s.get("properties") and depth < 3:
        return "{" + ", ".join(f"{k}: {inline(v, depth + 1)}" for k, v in s["properties"].items()) + "}"
    return s.get("type", "object")


def prop_lines(schema, ind=0):
    out, pad = [], "  " * ind
    for k, v in (schema.get("properties") or {}).items():
        extra = []
        if v.get("enum"):
            extra.append(f"enum={v['enum']}")
        if "default" in v:
            extra.append(f"default={v['default']}")
        if v.get("required") is True:
            extra.append("obrigatorio")
        d = (v.get("description") or "").strip()
        out.append(f"{pad}- `{k}` ({typ(v)})" + (f" [{', '.join(extra)}]" if extra else "") + (f" — {d}" if d else ""))
        sub = v if v.get("properties") else (v.get("items") if (v.get("items") or {}).get("properties") else None)
        if sub and ind < 3:
            out += prop_lines(sub, ind + 1)
            if isinstance(sub.get("required"), list):
                out.append(f"{pad}  (obrigatorios: {', '.join(sub['required'])})")
    return out


def render(spec):
    ops = [(p, m, o) for p, ms in spec["paths"].items() for m, o in ms.items() if m in METHODS]
    L = [
        "# API NexTags — referencia completa (gerada do swagger oficial)",
        f"Fonte: {SPEC_URL} · host `{spec.get('host')}` · {len(ops)} operacoes · gerado em {datetime.date.today().isoformat()}",
        "Auth: header `X-ACCESS-TOKEN` (valor puro). `FORM` = application/x-www-form-urlencoded (`--form k=v`); `JSON` = body JSON (`--json`).",
        "O swagger documenta o contrato, nao tudo que a API devolve (ex.: GET /agents/{id} traz `data.prompt`/`data.model` que o schema nao lista; numeros voltam como string). Shapes reais: `live_shapes.md`.",
        "",
    ]
    groups = {}
    for p, m, o in ops:
        groups.setdefault(p.split("/")[1], []).append((p, m, o))
    for g, items in groups.items():
        L += [f"## /{g}", ""]
        for p, m, o in items:
            L.append(f"### {m.upper()} {p}")
            L.append(f"`{o.get('operationId')}` — {(o.get('description') or o.get('summary') or '').strip()}")
            cons = o.get("consumes") or []
            for x in o.get("parameters", []):
                req = "*" if x.get("required") else ""
                if x["in"] == "body":
                    L.append(f"- **body** `{x['name']}`{req} (JSON):")
                    sch = x.get("schema", {})
                    L += ["  " + s for s in prop_lines(sch)]
                    if isinstance(sch.get("required"), list):
                        L.append(f"  (obrigatorios: {', '.join(sch['required'])})")
                    if "example" in sch:
                        L.append("  exemplo: `" + json.dumps(sch["example"], ensure_ascii=False) + "`")
                else:
                    kind = "FORM" if x["in"] == "formData" else x["in"]
                    d = (x.get("description") or "").strip()
                    L.append(f"- {kind} `{x['name']}`{req} ({x.get('type', '?')})" + (f" — {d}" if d else ""))
            if any("form" in c for c in cons) and not any(x["in"] == "formData" for x in o.get("parameters", [])):
                L.append("- (consumes FORM, sem campos)")
            for code, r in o.get("responses", {}).items():
                sch = r.get("schema")
                if code.startswith("2") or code == "default":
                    L.append(f"- resp {code}: `{inline(sch) or '(sem schema)'}`" + (f" — {r['description']}" if r.get("description") else ""))
                    if sch and "example" in sch:
                        L.append("  exemplo: `" + json.dumps(sch["example"], ensure_ascii=False) + "`")
                else:
                    L.append(f"- resp {code}: {r.get('description', '')}")
            L.append("")
    L += ["## Modelos", ""]
    for n, df in spec.get("definitions", {}).items():
        L += [f"### {n}"] + prop_lines(df) + [""]
    return "\n".join(L)


def cmd_spec_check(a):
    status, live = http("GET", SPEC_URL)
    if status != 200 or not isinstance(live, dict):
        sys.exit(f"Nao consegui baixar o spec: HTTP {status}")
    local = json.loads((REF_DIR / "swagger.json").read_text(encoding="utf-8"))
    lo, no = ops_of(live), ops_of(local)
    added, removed = sorted(set(lo) - set(no)), sorted(set(no) - set(lo))
    changed = sorted(k for k in set(lo) & set(no) if json.dumps(lo[k], sort_keys=True) != json.dumps(no[k], sort_keys=True))
    defs = sorted(n for n in set(live.get("definitions", {})) | set(local.get("definitions", {}))
                  if live.get("definitions", {}).get(n) != local.get("definitions", {}).get(n))
    print(f"live={len(lo)} ops · local={len(no)} ops")
    for label, items in (("NOVOS", added), ("REMOVIDOS", removed), ("ALTERADOS", changed)):
        print(f"{label}: " + (", ".join(f"{m} {p}" for m, p in items) if items else "nenhum"))
    print("MODELOS alterados: " + (", ".join(defs) if defs else "nenhum"))
    drift = bool(added or removed or changed or defs)
    if a.update:
        (REF_DIR / "swagger.json").write_text(json.dumps(live, ensure_ascii=False, indent=2), encoding="utf-8")
        (REF_DIR / "endpoints.md").write_text(render(live), encoding="utf-8")
        print("references/swagger.json e references/endpoints.md atualizados. Revise o SKILL.md (tabela e 'nao existe na API').")
    elif drift:
        print("Houve drift. Rode com --update para regenerar a referencia.")
    return 0


def cmd_gen_ref(a):
    spec = json.loads((REF_DIR / "swagger.json").read_text(encoding="utf-8"))
    (REF_DIR / "endpoints.md").write_text(render(spec), encoding="utf-8")
    print("references/endpoints.md regenerado a partir do swagger local.")
    return 0


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--token", help="token da conta (ou env NEXTAGS_TOKEN)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("call", parents=[common], help="chamada generica a qualquer endpoint")
    c.add_argument("method")
    c.add_argument("path", help="ex.: accounts/me (sem '/' inicial evita a conversao de caminho do Git Bash)")
    c.add_argument("-q", "--query", action="append", metavar="k=v")
    c.add_argument("--json", help="body JSON inline")
    c.add_argument("--json-file", help="body JSON de arquivo (UTF-8)")
    c.add_argument("--form", action="append", metavar="k=v", help="body form-urlencoded")
    c.add_argument("--yes", action="store_true", help="envia a escrita (sem isso: dry-run)")
    c.add_argument("--out", help="grava a resposta num arquivo")
    c.add_argument("--max-chars", type=int, default=6000)
    c.set_defaults(fn=cmd_call)

    sub.add_parser("whoami", parents=[common]).set_defaults(fn=cmd_whoami)
    s = sub.add_parser("snapshot", parents=[common])
    s.add_argument("--dir", required=True)
    s.set_defaults(fn=cmd_snapshot)
    b = sub.add_parser("backup-agents", parents=[common])
    b.add_argument("--dir", required=True)
    b.set_defaults(fn=cmd_backup_agents)
    k = sub.add_parser("spec-check")
    k.add_argument("--update", action="store_true")
    k.set_defaults(fn=cmd_spec_check)
    sub.add_parser("gen-ref").set_defaults(fn=cmd_gen_ref)

    a = ap.parse_args()
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()

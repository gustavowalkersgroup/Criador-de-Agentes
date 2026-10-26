#!/usr/bin/env python3
"""Cliente da API NexTags (https://app.nextagsai.com.br/api). So stdlib.

Token: env NEXTAGS_TOKEN ou --token. E POR CONTA (por cliente). Nunca e gravado em disco.
Escrita (POST/PUT/PATCH/DELETE) so e enviada com --yes; sem ele o script mostra o que enviaria (dry-run).

  call METHOD PATH [-q k=v] [--json '{...}' | --json-file f] [--form k=v] [--yes] [--out f]
  whoami                      GET /accounts/me (confirma em qual conta o token cai)
  snapshot --dir D            GET de leitura sem parametro em todos os recursos da conta -> D/*.json
  backup-agents --dir D       salva config + prompt (.md) de cada agente IA
  doc URL_OU_CAMINHO          imprime o Markdown de uma pagina do docs/help (ex.: comecar/limites-e-erros)
  spec-check [--update]       compara docs.nextags.com.br/openapi.json e os llms.txt com references/
  gen-ref                     regenera references/endpoints.md a partir do openapi local
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://app.nextagsai.com.br/api"
# Contrato oficial (OpenAPI 3.1, em portugues, 86 operacoes). O swagger legado de /api/swagger/ tem so 69 e
# nao traz /tools/*: nao usar como fonte.
SPEC_URL = "https://docs.nextags.com.br/openapi.json"
INDEXES = {"docs": "https://docs.nextags.com.br/llms.txt", "help": "https://help.nextags.com.br/llms.txt"}
SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
REF_DIR = SKILL_DIR / "references"
METHODS = ("get", "post", "put", "patch", "delete")
ROOTS = "accounts|agents|contacts|pipelines|products|calendars|broadcasts|tools"
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


def http(method, url, token=None, body=None, form=None, raw=False):
    # O Cloudflare do docs/help devolve 403 para o User-Agent padrao do urllib.
    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 (compatible; nextags-api-skill/1.1)"}
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
            status, content = r.status, r.read()
    except urllib.error.HTTPError as e:
        status, content = e.code, e.read()
    except urllib.error.URLError as e:
        sys.exit(f"ERRO de rede em {method} {url}: {e.reason}")
    text = content.decode("utf-8", "replace")
    if raw:
        return status, text
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


# ---------------------------------------------------------------- comandos de API

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


def cmd_doc(a):
    u = a.url.strip()
    if not u.startswith("http"):
        u = "https://docs.nextags.com.br/" + u.lstrip("/")
    u = re.sub(r"/?(#.*)?$", "", u)
    if not u.endswith(".md"):
        u += ".md"
    status, text = http("GET", u, raw=True)
    if status != 200:
        sys.exit(f"HTTP {status} em {u} (confira o caminho em references/llms_docs.txt ou llms_help.txt)")
    print(text if len(text) <= a.max_chars else text[: a.max_chars] + f"\n... [truncado: {len(text)} chars; use --max-chars]")
    return 0


# ---------------------------------------------------------------- spec / referencia (OpenAPI 3.1)

def ops_of(spec):
    return {(m.upper(), p): o for p, ms in spec["paths"].items() for m, o in ms.items() if m in METHODS}


def deref(spec, s):
    """Segue $ref (#/components/...). Devolve (nome_ou_None, schema)."""
    name = None
    while isinstance(s, dict) and "$ref" in s:
        parts = s["$ref"].lstrip("#/").split("/")
        name = parts[-1]
        s = spec
        for p in parts:
            s = s[p]
    return name, s


def typ(spec, v):
    name, v = deref(spec, v)
    if name and v.get("type") == "object":
        return name
    t = v.get("type", "object")
    if isinstance(t, list):
        return "|".join(t)
    if t == "array":
        return f"array<{typ(spec, v.get('items', {}))}>"
    return t


def inline(spec, s, depth=0):
    if not s:
        return ""
    name, s = deref(spec, s)
    if name and depth > 0:
        return name
    if s.get("type") == "array":
        return f"[{inline(spec, s.get('items', {}), depth + 1)}]"
    if s.get("properties") and depth < 3:
        return "{" + ", ".join(f"{k}: {inline(spec, v, depth + 1)}" for k, v in s["properties"].items()) + "}"
    t = s.get("type", "object")
    return "|".join(t) if isinstance(t, list) else t


def prop_lines(spec, schema, ind=0, seen=()):
    out, pad = [], "  " * ind
    _, schema = deref(spec, schema)
    req = set(schema.get("required") or [])
    for k, v in (schema.get("properties") or {}).items():
        name, rv = deref(spec, v)
        extra = []
        if rv.get("enum"):
            extra.append(f"enum={rv['enum']}")
        if "default" in rv:
            extra.append(f"default={rv['default']}")
        if k in req:
            extra.append("obrigatorio")
        d = " ".join((rv.get("description") or v.get("description") or "").split())
        out.append(f"{pad}- `{k}` ({typ(spec, v)})" + (f" [{', '.join(extra)}]" if extra else "") + (f" — {d}" if d else ""))
        sub = rv if rv.get("properties") else None
        if not sub and rv.get("type") == "array":
            _, it = deref(spec, rv.get("items", {}))
            sub = it if it.get("properties") else None
        if sub and ind < 3 and (name or k) not in seen:
            out += prop_lines(spec, sub, ind + 1, seen + (name or k,))
    return out


def render(spec):
    ops = [(p, m, o) for p, ms in spec["paths"].items() for m, o in ms.items() if m in METHODS]
    L = [
        "# API NexTags — referencia completa (gerada do OpenAPI oficial)",
        f"Fonte: {SPEC_URL} · {len(ops)} operacoes · gerado em {datetime.date.today().isoformat()} · base `{BASE}`",
        "Auth: header `X-ACCESS-TOKEN` (valor puro). `FORM` = application/x-www-form-urlencoded (`--form k=v`); `JSON` = body JSON (`--json`).",
        "O contrato nao descreve tudo que a API devolve (ex.: `GET /agents/{id}` traz `data.prompt`/`data.model`, que ele nao lista; ids e numeros voltam como string). Formas reais: `live_shapes.md`.",
        "Os exemplos de codigo (cURL/JS/Python/PHP) de cada operacao estao no `x-codeSamples` de `openapi.json`.",
        "",
    ]
    groups = {}
    for p, m, o in ops:
        groups.setdefault((o.get("tags") or [p.split("/")[1]])[0], []).append((p, m, o))
    for g, items in groups.items():
        L += [f"## {g}", ""]
        for p, m, o in items:
            L.append(f"### {m.upper()} {p}")
            L.append(f"`{o.get('operationId')}` — {o.get('summary', '')}")
            desc = " ".join((o.get("description") or "").split())
            if desc:
                L.append(desc)
            for x in o.get("parameters", []):
                _, xs = deref(spec, x)
                req = "*" if x.get("required") else ""
                sch = x.get("schema", {})
                d = " ".join((x.get("description") or "").split())
                en = f" enum={deref(spec, sch)[1].get('enum')}" if deref(spec, sch)[1].get("enum") else ""
                L.append(f"- {x['in']} `{x['name']}`{req} ({typ(spec, sch)}{en})" + (f" — {d}" if d else ""))
            rb = o.get("requestBody")
            if rb:
                for mt, mo in rb.get("content", {}).items():
                    kind = "FORM" if "form" in mt else "JSON"
                    L.append(f"- **body {kind}**{'*' if rb.get('required') else ''}:")
                    sch = mo.get("schema", {})
                    L += ["  " + s for s in prop_lines(spec, sch)]
                    ex = mo.get("example") or (mo.get("examples") or {})
                    if ex:
                        L.append("  exemplo: `" + json.dumps(ex, ensure_ascii=False) + "`")
            else:
                if m == "post":
                    L.append("- (sem body)")
            for code, r in o.get("responses", {}).items():
                _, r = deref(spec, r)
                d = " ".join((r.get("description") or "").split())
                cont = (r.get("content") or {}).get("application/json")
                if str(code).startswith("2") and cont:
                    L.append(f"- resp {code}: `{inline(spec, cont.get('schema')) or '(sem schema)'}`" + (f" — {d}" if d else ""))
                    ex = cont.get("example") or cont.get("examples")
                    if ex:
                        L.append("  exemplo: `" + json.dumps(ex, ensure_ascii=False) + "`")
                else:
                    L.append(f"- resp {code}: {d}")
            L.append("")
    L += ["## Modelos", ""]
    for n, df in spec.get("components", {}).get("schemas", {}).items():
        L += [f"### {n}"] + prop_lines(spec, df) + [""]
    return "\n".join(L)


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def page_urls(text):
    return sorted(set(re.findall(r"\]\((https://[^)\s]+\.md)\)", text)))


def cmd_spec_check(a):
    status, live = http("GET", SPEC_URL)
    if status != 200 or not isinstance(live, dict):
        sys.exit(f"Nao consegui baixar o spec: HTTP {status}")
    local_p = REF_DIR / "openapi.json"
    local = json.loads(local_p.read_text(encoding="utf-8")) if local_p.exists() else {"paths": {}, "components": {}}
    lo, no = ops_of(live), ops_of(local)
    added, removed = sorted(set(lo) - set(no)), sorted(set(no) - set(lo))
    changed = sorted(k for k in set(lo) & set(no) if json.dumps(lo[k], sort_keys=True) != json.dumps(no[k], sort_keys=True))
    ls, ns = live.get("components", {}).get("schemas", {}), local.get("components", {}).get("schemas", {})
    defs = sorted(n for n in set(ls) | set(ns) if ls.get(n) != ns.get(n))
    print(f"openapi: live={len(lo)} ops · local={len(no)} ops")
    for label, items in (("NOVOS", added), ("REMOVIDOS", removed), ("ALTERADOS", changed)):
        print(f"{label}: " + (", ".join(f"{m} {p}" for m, p in items) if items else "nenhum"))
    print("MODELOS alterados: " + (", ".join(defs) if defs else "nenhum"))
    drift = bool(added or removed or changed or defs)
    fresh = {}
    for key, url in INDEXES.items():
        st, text = http("GET", url, raw=True)
        if st != 200:
            print(f"indice {key}: HTTP {st} (pulado)")
            continue
        fresh[key] = text
        lp = REF_DIR / f"llms_{key}.txt"
        old = lp.read_text(encoding="utf-8") if lp.exists() else ""
        nu, ou = set(page_urls(text)), set(page_urls(old))
        print(f"indice {key}: {len(nu)} paginas (antes {len(ou)}) · novas: {len(nu - ou)} · removidas: {len(ou - nu)}"
              + ("" if sha(text) == sha(old) else " · TEXTO MUDOU"))
        for u in sorted(nu - ou)[:15]:
            print("   + " + u)
        drift = drift or sha(text) != sha(old)
    if a.update:
        local_p.write_text(json.dumps(live, ensure_ascii=False, indent=1), encoding="utf-8")
        (REF_DIR / "endpoints.md").write_text(render(live), encoding="utf-8")
        for key, text in fresh.items():
            (REF_DIR / f"llms_{key}.txt").write_text(text, encoding="utf-8")
        print("references/ atualizada (openapi.json, endpoints.md, llms_*.txt). Revise o SKILL.md: tabela, 'nao existe' e armadilhas.")
    elif drift:
        print("Houve drift. Rode com --update para atualizar references/.")
    return 0


def cmd_gen_ref(a):
    spec = json.loads((REF_DIR / "openapi.json").read_text(encoding="utf-8"))
    (REF_DIR / "endpoints.md").write_text(render(spec), encoding="utf-8")
    print("references/endpoints.md regenerado a partir do openapi local.")
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
    d = sub.add_parser("doc", help="Markdown de uma pagina do docs/help")
    d.add_argument("url", help="URL completa ou caminho do docs (ex.: comecar/limites-e-erros)")
    d.add_argument("--max-chars", type=int, default=30000)
    d.set_defaults(fn=cmd_doc)
    k = sub.add_parser("spec-check")
    k.add_argument("--update", action="store_true")
    k.set_defaults(fn=cmd_spec_check)
    sub.add_parser("gen-ref").set_defaults(fn=cmd_gen_ref)

    a = ap.parse_args()
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()

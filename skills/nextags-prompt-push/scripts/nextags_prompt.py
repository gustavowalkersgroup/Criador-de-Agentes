"""Atualiza SO o prompt de um agente de IA no IA Hub da NexTags.

Nunca envia model, max_output_tokens nem outro campo: o corpo do POST e
sempre {"prompt": "..."}.

Uso:
  python nextags_prompt.py list  --token T
  python nextags_prompt.py show  --token T --agent Bia
  python nextags_prompt.py push  --token T --agent Bia --file prompt.md          (simulacao)
  python nextags_prompt.py push  --token T --agent Bia --file prompt.md --yes    (envia)

O token tambem pode vir da variavel NEXTAGS_TOKEN.
"""
import argparse
import datetime
import json
import os
import sys
import unicodedata
import urllib.error
import urllib.request

BASE = "https://app.nextagsai.com.br/api"


def call(method, path, token, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={
            "X-ACCESS-TOKEN": token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        sys.exit(f"ERRO HTTP {e.code} em {method} {path}: {e.read().decode('utf-8', 'replace')[:500]}")
    return json.loads(raw) if raw else {}


def unwrap(resp):
    return resp.get("data", resp) if isinstance(resp, dict) else resp


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return s.lower().strip()


def list_agents(token):
    agents = unwrap(call("GET", "/agents", token))
    return agents if isinstance(agents, list) else []


def resolve(token, agent):
    if agent.isdigit():
        return int(agent)
    agents = list_agents(token)
    exact = [a for a in agents if norm(a.get("name")) == norm(agent)]
    hits = exact or [a for a in agents if norm(agent) in norm(a.get("name"))]
    if len(hits) == 1:
        return hits[0]["id"]
    listing = "\n".join(f"  {a.get('id')}  {a.get('name')}" for a in agents)
    if not hits:
        sys.exit(f"Nenhum agente com nome parecido com '{agent}'. Agentes da conta:\n{listing}")
    names = "\n".join(f"  {a.get('id')}  {a.get('name')}" for a in hits)
    sys.exit(f"Mais de um agente bate com '{agent}', use --agent <id>:\n{names}")


def get_agent(token, agent_id):
    # Resposta real: {id, name, created_at, created_by, data: {prompt, model, aiPriority, ...}}.
    # Achata (topo + data) pra id/name nao virarem None; agente nunca salvo volta sem `data`.
    resp = call("GET", f"/agents/{agent_id}", token)
    if isinstance(resp, dict) and isinstance(resp.get("data"), dict):
        return {**{k: v for k, v in resp.items() if k != "data"}, **resp["data"]}
    return resp


def has_config(ag):
    # Agente nunca salvo no painel volta so com id/name; POST nele deixa o painel quebrado.
    return bool(ag.get("model")) and "aiPriority" in ag


def cmd_list(a):
    for ag in list_agents(a.token):
        print(f"{ag.get('id')}\t{ag.get('name')}")


def cmd_show(a):
    ag = get_agent(a.token, resolve(a.token, a.agent))
    prompt = ag.get("prompt") or ""
    print(f"id={ag.get('id')} nome={ag.get('name')} config_salva={has_config(ag)} prompt={len(prompt)} chars")
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(prompt)
        print(f"prompt salvo em {a.out}")


def cmd_push(a):
    with open(a.file, encoding="utf-8") as f:
        new = f.read().strip()
    if not new:
        sys.exit("Arquivo de prompt vazio, nada enviado.")

    agent_id = resolve(a.token, a.agent)
    before = get_agent(a.token, agent_id)
    name = before.get("name")
    if not has_config(before):
        sys.exit(
            f"ABORTADO: o agente {agent_id} ({name}) nunca teve a config salva no painel "
            "(GET sem model/aiPriority). Peca pro usuario abrir o agente no IA Hub, "
            "salvar uma vez, e rodar de novo."
        )

    old = before.get("prompt") or ""
    print(f"Agente: {agent_id} ({name})")
    print(f"Prompt atual: {len(old)} chars | novo: {len(new)} chars")
    if old.strip() == new:
        print("O prompt no painel ja e identico ao novo. Nada enviado.")
        return

    if not a.yes:
        print("SIMULACAO: nada foi enviado. Rode de novo com --yes para enviar.")
        return

    os.makedirs(a.backup_dir, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(a.backup_dir, f"backup-{agent_id}-{stamp}.md")
    with open(backup, "w", encoding="utf-8") as f:
        f.write(old)
    print(f"Backup do prompt anterior: {backup}")

    call("POST", f"/agents/{agent_id}", a.token, {"prompt": new})

    after = get_agent(a.token, agent_id)
    ok_prompt = (after.get("prompt") or "").strip() == new
    ok_model = after.get("model") == before.get("model")
    print(f"Conferencia: prompt {'OK' if ok_prompt else 'DIFERENTE'} | modelo {'intacto' if ok_model else 'MUDOU'}")
    if not (ok_prompt and ok_model):
        sys.exit(1)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("list", "show", "push"):
        s = sub.add_parser(name)
        s.add_argument("--token", default=os.environ.get("NEXTAGS_TOKEN"))
        if name != "list":
            s.add_argument("--agent", required=True, help="nome (ex.: Bia) ou id numerico")
        if name == "show":
            s.add_argument("--out", help="salva o prompt atual neste arquivo")
        if name == "push":
            s.add_argument("--file", required=True, help="arquivo .md/.txt com o prompt novo")
            s.add_argument("--yes", action="store_true", help="envia de verdade")
            s.add_argument("--backup-dir", default=".", help="onde salvar o backup do prompt anterior")
    a = p.parse_args()
    if not a.token:
        sys.exit("Falta o token da conta (--token ou NEXTAGS_TOKEN).")
    {"list": cmd_list, "show": cmd_show, "push": cmd_push}[a.cmd](a)


if __name__ == "__main__":
    main()

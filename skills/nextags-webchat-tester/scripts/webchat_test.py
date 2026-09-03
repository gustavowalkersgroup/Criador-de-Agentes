# -*- coding: utf-8 -*-
"""
NexTags Webchat Tester
======================
Conversa com um agente de webchat NexTags (plataforma tapthetable) AO VIVO, via WebSocket,
direto do Python. Testa o agente REALMENTE PUBLICADO end-to-end (modelo do NexTags + MCP +
APIs de backend), sem precisar da extensao do Chrome nem de simulacao "no cortex".

Uso:
  pip install websocket-client
  python webchat_test.py <page_id> "primeira mensagem" ["segunda mensagem" ...]

  - <page_id>: o valor de ?p=<id> na URL do webchat (ex.: a URL
    https://app.nextagsai.com.br/webchat/?p=2527130  ->  page_id = 2527130).
  - Cada mensagem extra e enviada EM SEQUENCIA na MESMA conversa (1 contato novo).
  - Para testar cenarios ISOLADOS (resetar contexto/CUFs de roteamento como setor_agente e
    tipo_setor), rode o script varias vezes: cada execucao cria um contato novo (createUser).
    Cada contato novo tem setor_agente vazio -> o roteador classifica de novo.

Saida: imprime "BOT[text]/[image]/[card]: ..." para cada resposta recebida.

Nota: mensagens "gibberish" podem cair no revalidador (tipo_setor humano|bot) e serem
arquivadas/bloqueadas. Use mensagens humanas e contextualizadas.
"""
import sys, json, ssl, time, io
import urllib.request, urllib.parse
import websocket  # pip install websocket-client

# --- Config (ajuste BASE se o painel for outro whitelabel) ---
BASE = "https://app.nextagsai.com.br"   # host do painel NexTags
CHANNEL = 9                              # canal do webchat (fixo no tapthetable)
PAGE = None                             # setado pelo argv

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
out = io.open(1, 'w', encoding='utf-8', closefd=False)
def log(*a): out.write(" ".join(str(x) for x in a) + "\n"); out.flush()

def post(path, param):
    body = urllib.parse.urlencode({"param": json.dumps(param)}).encode()
    req = urllib.request.Request(BASE + path, data=body, headers={
        "User-Agent": "Mozilla/5.0", "Origin": BASE,
        "Referer": BASE + "/webchat/?p=" + str(PAGE),
        "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, context=ctx, timeout=40) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))

def get_wsurl():
    # op=wt -> whitelabel; data.wsurl = endpoint do WebSocket (ex.: wss://ws.tapthetable.io/chat)
    j = post("/php/user.php", {"op": "wt", "account_id": PAGE})
    return j["data"]["wsurl"]

def new_user():
    # cria um "Guest" e devolve ms_id + hash (necessarios pro handshake)
    j = post("/php/no_login.php", {"config_id": None, "page_id": PAGE, "op": "webChat",
        "op1": "createUser", "data": {"timezoneOffset": -3, "timezoneName": "America/Sao_Paulo"}})
    return j["ms_id"], j["hash"]

def extract(frame):
    """Le um frame do WS e devolve [(tipo, texto)] das mensagens do bot."""
    parts = []
    try: d = json.loads(frame)
    except Exception: return parts
    for m in ((d.get("data") or {}).get("message") or []):
        if not isinstance(m, dict): continue
        if m.get("text"): parts.append(("text", m["text"]))
        att = m.get("attachment")
        if att:
            pl = att.get("payload", {}); t = att.get("type")
            if t == "image":
                parts.append(("image", pl.get("url", "")))
            elif t == "template":
                btns = [b.get("url") or b.get("title") for b in pl.get("buttons", [])]
                parts.append(("card", pl.get("text", "") + " | btn:" + ",".join(str(b) for b in btns)))
            else:
                parts.append((t or "att", json.dumps(pl, ensure_ascii=False)[:200]))
    return parts

def conversa(mensagens, espera=45):
    """Abre 1 conversa (contato novo) e envia as mensagens em sequencia, lendo as respostas."""
    wsurl = get_wsurl()
    ms_id, hsh = new_user()
    ws = websocket.create_connection(wsurl, sslopt={"cert_reqs": ssl.CERT_NONE},
        header=["User-Agent: Mozilla/5.0"], origin=BASE, timeout=30)
    # handshake (action -1) registra o usuario no WS
    ws.send(json.dumps({"action": -1, "data": {"dir": 1, "sentBy": ms_id,
        "channel": CHANNEL, "page_id": PAGE, "ms_id": ms_id, "hash": hsh}}))
    time.sleep(1.2)
    for msg in mensagens:
        log("\n>>> CLIENTE:", msg)
        ws.send(json.dumps({"action": 0, "webchat": True, "data": {"dir": 1, "sentBy": ms_id,
            "channel": CHANNEL, "page_id": PAGE, "ms_id": ms_id, "hash": hsh, "liveChat": False,
            "timestamp": int(time.time() * 1000),
            "message": [{"text": msg, "dir": 1, "channel": CHANNEL}]}}))
        # coleta respostas; respostas com MCP demoram -> manda ping pra nao cair a conexao
        ws.settimeout(3); t0 = time.time(); last = 0.0; last_ping = time.time()
        while time.time() - t0 < espera:
            if time.time() - last_ping > 6:
                try: ws.ping()
                except Exception: pass
                last_ping = time.time()
            try:
                frame = ws.recv()
            except websocket.WebSocketTimeoutException:
                if last and time.time() - last > 9: break   # ja respondeu e ficou quieto -> proxima
                continue
            except Exception as e:
                log("   (conexao caiu:", e, ")"); break
            got = False
            for k, v in extract(frame):
                log("   BOT[%s]:" % k, v[:400]); got = True
            if got: last = time.time()
    ws.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        log('uso: python webchat_test.py <page_id> "mensagem 1" ["mensagem 2" ...]')
        sys.exit(1)
    PAGE = sys.argv[1]
    conversa(sys.argv[2:])
    log("\n=== FIM ===")

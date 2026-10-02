#!/usr/bin/env python3
"""
Testes do octobercut.py. Roda standalone (`python test_octobercut.py`) ou com pytest.
"""
import json
import re
from pathlib import Path

import octobercut as oc

SKILL_DIR = Path(__file__).resolve().parent.parent


def T(s):
    return {"message": {"text": s}}


def IMG(u="https://x.com/a.jpg"):
    return {"message": {"attachment": {"type": "image", "payload": {"url": u}}}}


def BTN(text, url="https://x.com/p"):
    return {"message": {"attachment": {"type": "template", "payload": {
        "template_type": "button", "text": text,
        "buttons": [{"type": "web_url", "title": "Comprar agora", "url": url}]}}}}


# ---- merge -----------------------------------------------------------

def test_rastreio_4_bolhas_vira_1():
    msgs = [T("Boa notícia, Camila! ✨"), 4, T("Seu pedido #5432 tá a caminho."), 4,
            T("Rastreio: (link)"), 4, T("Qualquer coisa, tô por aqui, tá?")]
    out, _ = oc.merge_messages(msgs)
    assert oc.count_bubbles(msgs) == 4
    assert len(out) == 1
    assert out[0]["message"]["text"] == (
        "Boa notícia, Camila! ✨\n\nSeu pedido #5432 tá a caminho.\n\n"
        "Rastreio: (link)\n\nQualquer coisa, tô por aqui, tá?")


def test_frase_do_carrinho_vai_para_dentro_do_botao():
    msgs = [T("Prontinho! Montei seu carrinho 💙"), BTN("")]
    out, _ = oc.merge_messages(msgs)
    assert len(out) == 1
    assert oc.kind_of(out[0]) == "button"
    assert out[0]["message"]["attachment"]["payload"]["text"] == "Prontinho! Montei seu carrinho 💙"


def test_vitrine_imagem_botao_pergunta_vira_2():
    msgs = [IMG(), 4, BTN("Produto, R$ 0,00"), 4, T("Qual cor você prefere?")]
    out, _ = oc.merge_messages(msgs)
    assert [oc.kind_of(m) for m in out] == ["image", "button"]
    assert out[1]["message"]["attachment"]["payload"]["text"].endswith("Qual cor você prefere?")


def test_texto_antes_da_imagem_passa_para_depois():
    msgs = [T("Olha esse:"), IMG(), BTN("Produto, R$ 0,00")]
    out, _ = oc.merge_messages(msgs)
    assert [oc.kind_of(m) for m in out] == ["image", "button"]
    assert out[1]["message"]["attachment"]["payload"]["text"].startswith("Olha esse:")


def test_botao_nao_passa_de_1024():
    msgs = [T("a" * 900), BTN("b" * 200)]
    out, _ = oc.merge_messages(msgs)
    assert [oc.kind_of(m) for m in out] == ["text", "button"]
    assert out[1]["message"]["attachment"]["payload"]["text"] == "b" * 200


def test_merge_nao_altera_entrada():
    btn = BTN("x")
    oc.merge_messages([T("y"), btn])
    assert btn["message"]["attachment"]["payload"]["text"] == "x"


def test_merge_payload_preserva_actions():
    payload = {"messages": [T("a"), 4, T("b")], "actions": [{"action": "add_tag", "tag_name": "x"}]}
    new, info = oc.merge_payload(payload)
    assert new["actions"] == payload["actions"]
    assert (info["before"], info["after"]) == (2, 1)


def test_merge_sem_messages_nao_quebra():
    new, info = oc.merge_payload({"actions": [{"action": "send_flow", "flow_id": "1"}]})
    assert info["before"] is None and "messages" not in new


# ---- audit -----------------------------------------------------------

def test_extract_multilinha():
    text = 'Exemplo:\n{"messages":[\n  {"message":{"text":"a } b"}},\n  4,\n  {"message":{"text":"c"}}\n]}\nfim'
    found = oc.extract_json_examples(text)
    assert len(found) == 1
    assert json.loads(found[0][1])["messages"][1] == 4


def test_audit_pega_typing_e_instrucoes_antigas():
    prompt = (
        "Ao apresentar um produto, use 3 blocos separados por typing 4.\n"
        "Pergunte o nome UMA vez.\n"
        '{"messages":[{"message":{"text":"Deixa eu ver"}},4,{"message":{"text":"Achei"}}]}\n'
    )
    r = oc.audit_text(prompt)
    ids = {f["id"] for f in r["findings"]}
    assert {"typing_como_padrao", "blocos_multiplos", "perguntar_nome",
            "exemplo_com_typing", "exemplo_fundivel", "sem_bloco_octobercut"} <= ids
    # o texto do JSON não pode disparar regra de prosa
    assert "mensagem_de_espera" not in ids


def test_audit_ignora_linhas_negadas():
    r = oc.audit_text("Nunca use o typing indicator entre textos.\nNão pergunte o nome só por perguntar.\n")
    ids = {f["id"] for f in r["findings"]}
    assert "typing_como_padrao" not in ids and "perguntar_nome" not in ids


def test_bloco_canonico_passa_limpo():
    ref = (SKILL_DIR / "references" / "bloco_octobercut.md").read_text(encoding="utf-8")
    block = re.search(r"```\n(## FORMATO ECONÔMICO.*?)```", ref, re.S).group(1)
    r = oc.audit_text(block)
    assert r["summary"]["blocks"] == 0, r["findings"]
    assert r["summary"]["warnings"] == 0, r["findings"]
    assert r["summary"]["examples"] == 4


# ---- estimate --------------------------------------------------------

def test_estimate_bate_com_numeros_internos():
    r = oc.estimate(7, 2, 0.035, 1000)
    assert r["per_attendance"]["before"] == 0.245
    assert r["per_attendance"]["after"] == 0.07
    assert r["reduction_pct"] == 71.4
    assert r["saving_brl"] == 175.0


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"\n{len(tests)} testes passaram")

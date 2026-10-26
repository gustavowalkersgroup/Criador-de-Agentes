#!/usr/bin/env python3
"""
Testes do fix_json.py — focam nas decisões do cliente: WA-markup preservado,
markdown-padrão removido, postback válido, send_flow sem messages não forçado.

Roda standalone (`python test_fix_json.py`) ou com pytest.
"""
import fix_json as fj


# ---- Markdown: preservar WA-markup, remover markdown-padrão -----------

def test_strip_keeps_whatsapp_markup():
    for s in ("*negrito*", "_itálico_", "~tachado~", "oi *bold* e _it_ aqui"):
        out, changed = fj.strip_markdown(s)
        assert out == s, f"WA-markup alterado: {s!r} -> {out!r}"
        assert changed is False


def test_strip_removes_double_bold():
    out, changed = fj.strip_markdown("Preço **R$ 99** hoje")
    assert out == "Preço R$ 99 hoje"
    assert changed is True


def test_strip_removes_double_underscore_and_tilde():
    assert fj.strip_markdown("__b__")[0] == "b"
    assert fj.strip_markdown("~~s~~")[0] == "s"


def test_strip_converts_markdown_link():
    out, changed = fj.strip_markdown("Acesse [aqui](https://x.com)")
    assert out == "Acesse aqui: https://x.com"
    assert changed is True


def test_strip_removes_heading():
    out, _ = fj.strip_markdown("# Título\nlinha")
    assert out == "Título\nlinha"


# ---- Botões: postback é válido ----------------------------------------

def test_postback_button_valid():
    fixes, pending = [], []
    fj.fix_button({"type": "postback", "payload": "123", "title": "Ver"},
                  fixes, pending, "b")
    assert pending == []


def test_postback_without_payload_pending():
    fixes, pending = [], []
    fj.fix_button({"type": "postback", "title": "Ver"}, fixes, pending, "b")
    assert any("payload" in p for p in pending)


def test_web_url_without_url_pending():
    fixes, pending = [], []
    fj.fix_button({"type": "web_url", "title": "Ver"}, fixes, pending, "b")
    assert any("url" in p for p in pending)


# ---- send_flow sem messages: NÃO forçar messages ----------------------

def test_send_flow_only_actions_ok():
    fixes, pending = [], []
    out = fj.process_one('{"actions":[{"action":"send_flow","flow_id":"1"}]}',
                         fixes, pending, [])
    assert out is not None
    assert "actions" in out
    # não deve haver pendência exigindo messages
    assert not any("messages" in p.lower() and "send_flow" in p.lower() for p in pending)


def test_transfer_action_preserved():
    # json-fixer NÃO converte transfer→send_flow (só valida); deve preservar
    fixes, pending = [], []
    out = fj.process_one('{"messages":[{"message":{"text":"oi"}}],'
                         '"actions":[{"action":"transfer_conversation_to","value":"human"}]}',
                         fixes, pending, [])
    assert out is not None
    assert out["actions"][0]["action"] == "transfer_conversation_to"


def test_action_alias_normalized():
    fixes, pending = [], []
    out = fj.process_one('{"actions":[{"action":"sendFlow","flow_id":"1"}]}',
                         fixes, pending, [])
    assert out["actions"][0]["action"] == "send_flow"


def test_text_message_markdown_link_fixed_in_pipeline():
    fixes, pending = [], []
    out = fj.process_one('{"messages":[{"message":{"text":"Veja [aqui](http://x)"}}]}',
                         fixes, pending, [])
    assert out["messages"][0]["message"]["text"] == "Veja aqui: http://x"


def test_text_message_whatsapp_markup_preserved_in_pipeline():
    fixes, pending = [], []
    out = fj.process_one('{"messages":[{"message":{"text":"Olha o *negrito*"}}]}',
                         fixes, pending, [])
    assert out["messages"][0]["message"]["text"] == "Olha o *negrito*"


# ---- OctoberCut: aviso de custo, sem alterar o JSON -------------------

def test_octobercut_avisa_typing_sem_alterar():
    data = {"messages": [{"message": {"text": "a"}}, 4, {"message": {"text": "b"}}]}
    fixes, pending = [], []
    fixed = fj.process_one(fj.json.dumps(data), fixes, pending, [])
    assert fixed["messages"][1] == 4  # schema válido: não remove
    w = fj.octobercut_warnings(fixed)
    assert w and "2 mensagens" in w[0]
    assert any("typing" in x for x in w)


def test_octobercut_uma_bolha_sem_aviso():
    assert fj.octobercut_warnings({"messages": [{"message": {"text": "a\n\nb"}}]}) == []


def test_octobercut_imagem_mais_botao_sem_aviso():
    msgs = [{"message": {"attachment": {"type": "image", "payload": {"url": "https://x.com/a.jpg"}}}},
            {"message": {"attachment": {"type": "template", "payload": {
                "template_type": "button", "text": "x",
                "buttons": [{"type": "web_url", "title": "Comprar", "url": "https://x.com"}]}}}}]
    assert fj.octobercut_warnings({"messages": msgs}) == []


# ---- Doc oficial: formatos válidos que o fixer NÃO pode mexer ----------
# Fonte: https://docs.nextags.com.br/comecar/mensagens-e-acoes/

def _run_one(data):
    fixes, pending = [], []
    out = fj.process_one(fj.json.dumps(data), fixes, pending, [])
    return out, fixes, pending


def _btn_msg(buttons, text="x"):
    return {"messages": [{"message": {"attachment": {"type": "template", "payload": {
        "template_type": "button", "text": text, "buttons": buttons}}}}]}


def test_transfer_bot_preservado():
    # `bot` devolve a conversa ao robô; reescrever para `human` manda o cliente
    # para a fila errada.
    out, fixes, pending = _run_one(
        {"actions": [{"action": "transfer_conversation_to", "value": "bot"}]})
    assert out["actions"][0]["value"] == "bot"
    assert fixes == [] and pending == []


def test_transfer_human_inalterado():
    out, fixes, _ = _run_one(
        {"actions": [{"action": "transfer_conversation_to", "value": "human"}]})
    assert out["actions"][0]["value"] == "human" and fixes == []


def test_transfer_caixa_alta_normalizada_sem_virar_human():
    out, fixes, _ = _run_one(
        {"actions": [{"action": "transfer_conversation_to", "value": "BOT"}]})
    assert out["actions"][0]["value"] == "bot"
    assert fixes and "caixa baixa" in fixes[0]


def test_transfer_valor_desconhecido_segue_virando_human():
    out, fixes, _ = _run_one(
        {"actions": [{"action": "transfer_conversation_to", "value": "agent"}]})
    assert out["actions"][0]["value"] == "human" and fixes


def test_botao_phone_number_valido():
    out, fixes, pending = _run_one(_btn_msg(
        [{"type": "phone_number", "title": "Ligar", "payload": "+551133445566"}]))
    assert pending == [] and fixes == []
    assert out["messages"][0]["message"]["attachment"]["payload"]["buttons"][0]["type"] == "phone_number"


def test_botao_phone_number_sem_payload_pendencia():
    _, _, pending = _run_one(_btn_msg([{"type": "phone_number", "title": "Ligar"}]))
    assert any("phone_number" in p and "payload" in p for p in pending)


def test_postback_com_acoes_em_json_no_payload_valido():
    payload = fj.json.dumps({"actions": [{"action": "add_tag", "tag_name": "vip"}]})
    out, fixes, pending = _run_one(_btn_msg([{"type": "postback", "title": "Quero", "payload": payload}]))
    assert pending == [] and fixes == []
    assert out["messages"][0]["message"]["attachment"]["payload"]["buttons"][0]["payload"] == payload


def test_mensagem_so_whatsapp_interativa_passa_intacta():
    wa = {"messaging_product": "whatsapp", "recipient_type": "individual", "to": None,
          "type": "interactive", "interactive": {"type": "button", "body": {"text": "Confirma?"},
          "action": {"buttons": [{"type": "reply", "reply": {"id": "1000001", "title": "Confirmo"}}]}}}
    out, fixes, pending = _run_one({"messages": [wa]})
    assert out == {"messages": [wa]}
    assert fixes == [] and pending == []


def test_mensagem_so_whatsapp_com_text_nao_e_embrulhada():
    # tem a chave `text`, mas é Cloud API (text.body), não `message`
    wa = {"messaging_product": "whatsapp", "to": None, "type": "text", "text": {"body": "oi"}}
    out, fixes, _ = _run_one({"messages": [wa]})
    assert out["messages"][0] == wa and fixes == []


def test_mensagem_so_whatsapp_misturada_com_mensagem_normal():
    wa = {"messaging_product": "whatsapp", "to": None, "type": "interactive", "interactive": {}}
    normal = {"message": {"text": "oi"}}
    out, _, _ = _run_one({"messages": [normal, 3, wa]})
    assert out["messages"] == [normal, 3, wa]


def test_quick_replies_preservadas():
    qr = [{"content_type": "text", "title": "Chocolate", "payload": "1000001"}]
    out, fixes, pending = _run_one({"messages": [{"message": {"text": "Qual?", "quick_replies": qr}}]})
    assert out["messages"][0]["message"]["quick_replies"] == qr
    assert fixes == [] and pending == []


def test_quick_replies_acima_de_11_avisa():
    qr = [{"content_type": "text", "title": f"o{i}", "payload": str(i)} for i in range(12)]
    out, _, pending = _run_one({"messages": [{"message": {"text": "Qual?", "quick_replies": qr}}]})
    assert any("12 respostas rápidas" in p for p in pending)
    assert len(out["messages"][0]["message"]["quick_replies"]) == 12  # não corta


def test_mais_de_3_botoes_avisa_sem_cortar():
    btns = [{"type": "postback", "title": f"b{i}", "payload": str(i)} for i in range(4)]
    out, _, pending = _run_one(_btn_msg(btns))
    assert any("4 botões" in p for p in pending)
    assert len(out["messages"][0]["message"]["attachment"]["payload"]["buttons"]) == 4


def test_tres_botoes_sem_aviso():
    btns = [{"type": "postback", "title": f"b{i}", "payload": str(i)} for i in range(3)]
    _, _, pending = _run_one(_btn_msg(btns))
    assert pending == []


def test_titulo_de_botao_acima_de_20_avisa():
    _, _, pending = _run_one(_btn_msg(
        [{"type": "postback", "title": "Acompanhar meu pedido", "payload": "1"}]))
    assert any("21 caracteres" in p for p in pending)


def _cartao(n, title="Bolo", subtitle="R$ 89,90"):
    return {"messages": [{"message": {"attachment": {"type": "template", "payload": {
        "template_type": "generic", "image_aspect_ratio": "square",
        "elements": [{"title": title, "subtitle": subtitle,
                      "image_url": "https://x.com/a.jpg", "buttons": []} for _ in range(n)]}}}}]}


def test_galeria_acima_de_10_cartoes_avisa():
    _, _, pending = _run_one(_cartao(11))
    assert any("11 cartões" in p for p in pending)


def test_galeria_de_10_cartoes_ok():
    _, _, pending = _run_one(_cartao(10))
    assert pending == []


def test_cartao_titulo_e_subtitulo_acima_de_80_avisa():
    _, _, pending = _run_one(_cartao(2, title="t" * 81, subtitle="s" * 81))
    assert any(".title com 81" in p for p in pending)
    assert any(".subtitle com 81" in p for p in pending)


def test_cartao_com_4_botoes_avisa():
    data = _cartao(2)
    data["messages"][0]["message"]["attachment"]["payload"]["elements"][0]["buttons"] = [
        {"type": "postback", "title": f"b{i}", "payload": str(i)} for i in range(4)]
    _, _, pending = _run_one(data)
    assert any("4 botões (limite 3 por cartão)" in p for p in pending)


def test_typing_3_segundos_valido():
    # a doc usa `3` no exemplo; o número solto é a pausa em segundos
    out, fixes, pending = _run_one(
        {"messages": [{"message": {"text": "a"}}, 3, {"message": {"text": "b"}}]})
    assert out["messages"][1] == 3 and fixes == [] and pending == []


def test_set_field_value_em_campo_de_sistema_valido():
    for f in ("phone", "email", "first_name", "last_name", "full_name"):
        out, fixes, pending = _run_one(
            {"actions": [{"action": "set_field_value", "field_name": f, "value": "x"}]})
        assert pending == [] and fixes == [], f


def test_flow_id_e_admin_id_inteiros_ou_texto():
    out, fixes, pending = _run_one({"actions": [
        {"action": "send_flow", "flow_id": 1000001},
        {"action": "send_flow", "flow_id": "1000001"},
        {"action": "assign_conversation", "admin_id": 10001}]})
    assert pending == [] and fixes == [] and len(out["actions"]) == 3


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {fn.__name__}  — {e}")
        except Exception as e:  # noqa
            failed += 1
            print(f"  ERROR {fn.__name__}  — {type(e).__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} testes passaram.")
    return 1 if failed else 0


if __name__ == "__main__":
    import sys
    sys.exit(_run())

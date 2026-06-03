#!/usr/bin/env python3
"""
Testes do analyze_prompt.py — focam nas decisões do cliente (Tema A–J),
em especial as 3 reversões: send_flow sem messages é válido, postback é
permitido, e WA-markup (*_~) não é violação (só markdown-padrão vaza).

Roda standalone (`python test_analyze_prompt.py`) ou com pytest.
"""
import analyze_prompt as ap


def _types(findings):
    t = set()
    for b in findings["json_blocks"]:
        for it in b["issues"]:
            t.add(it["type"])
    return t


def _first_block(findings):
    return findings["json_blocks"][0] if findings["json_blocks"] else {"issues": []}


def _issue(findings, type_):
    for b in findings["json_blocks"]:
        for it in b["issues"]:
            if it["type"] == type_:
                return it
    return None


# ---- REVERSÃO 1: send_flow sem messages é VÁLIDO ----------------------

def test_send_flow_without_messages_is_valid():
    content = 'Exemplo:\n{"actions":[{"action":"send_flow","flow_id":"1775096402729"}]}\n'
    f = ap.analyze(content)
    # a checagem antiga não existe mais
    assert "send_flow_without_messages_count" not in f["summary"]
    # o bloco com só send_flow não gera nenhuma issue
    assert _first_block(f)["issues"] == []
    assert f["prompt_uses_actions"] is True


def test_messages_empty_with_send_flow_is_valid():
    content = '{"messages":[],"actions":[{"action":"send_flow","flow_id":"123"}]}\n'
    f = ap.analyze(content)
    assert _first_block(f)["issues"] == []


# ---- REVERSÃO 2: postback é PERMITIDO ---------------------------------

def test_postback_with_payload_ok():
    content = ('{"messages":[{"message":{"attachment":{"type":"template","payload":'
               '{"template_type":"button","text":"Confira","buttons":'
               '[{"type":"postback","payload":"123456","title":"Ver"}]}}}}]}\n')
    f = ap.analyze(content)
    assert "button_misuse" not in _types(f)


def test_postback_without_payload_blocks():
    content = ('{"messages":[{"message":{"attachment":{"type":"template","payload":'
               '{"template_type":"button","text":"x","buttons":'
               '[{"type":"postback","title":"Ver"}]}}}}]}\n')
    f = ap.analyze(content)
    assert "button_misuse" in _types(f)


def test_web_url_without_url_blocks():
    content = ('{"messages":[{"message":{"attachment":{"type":"template","payload":'
               '{"template_type":"button","text":"x","buttons":'
               '[{"type":"web_url","title":"Ver"}]}}}}]}\n')
    f = ap.analyze(content)
    it = _issue(f, "button_misuse")
    assert it is not None
    assert any(d.get("severity") == "block" for d in it["details"])


def test_two_web_url_buttons_warns():
    content = ('{"messages":[{"message":{"attachment":{"type":"template","payload":'
               '{"template_type":"button","text":"x","buttons":'
               '[{"type":"web_url","url":"http://a","title":"A"},'
               '{"type":"web_url","url":"http://b","title":"B"}]}}}}]}\n')
    f = ap.analyze(content)
    it = _issue(f, "button_misuse")
    assert it is not None
    assert any(d.get("severity") == "warn" for d in it["details"])


# ---- REVERSÃO 3: WA-markup OK, markdown-padrão vaza -------------------

def test_whatsapp_markup_not_flagged():
    content = '{"messages":[{"message":{"text":"Olha o *negrito* e _itálico_ e ~tachado~ 🔥"}}]}\n'
    f = ap.analyze(content)
    assert "markdown_in_json_text" not in _types(f)


def test_standard_bold_blocks():
    content = '{"messages":[{"message":{"text":"Preço **R$ 99**"}}]}\n'
    f = ap.analyze(content)
    assert "markdown_in_json_text" in _types(f)


def test_markdown_link_blocks():
    content = '{"messages":[{"message":{"text":"Acesse [aqui](https://x.com)"}}]}\n'
    f = ap.analyze(content)
    assert "markdown_in_json_text" in _types(f)


# ---- Transferência: transfer/assign = AVISO (não bloqueio) ------------

def test_transfer_conversation_to_is_advisory_warn():
    content = ('{"messages":[{"message":{"text":"vou transferir"}}],'
               '"actions":[{"action":"transfer_conversation_to","value":"human"}]}\n')
    f = ap.analyze(content)
    assert "advisory_transfer_actions" in _types(f)
    assert "nonexistent_actions" not in _types(f)
    it = _issue(f, "advisory_transfer_actions")
    assert it["severity"] == "warn"


def test_assign_conversation_is_advisory_warn():
    content = '{"actions":[{"action":"assign_conversation","admin_id":"99"}]}\n'
    f = ap.analyze(content)
    assert "advisory_transfer_actions" in _types(f)


# ---- Ação inexistente (inventada/legada) = BLOCK ----------------------

def test_nonexistent_action_blocks():
    content = '{"actions":[{"action":"connect_user_to_human"}]}\n'
    f = ap.analyze(content)
    assert "nonexistent_actions" in _types(f)
    it = _issue(f, "nonexistent_actions")
    assert it["severity"] == "block"


# ---- Placeholder genérico = BLOCK -------------------------------------

def test_generic_placeholder_blocks():
    content = '{"messages":[{"message":{"text":"Oi [nome], tudo bem?"}}]}\n'
    f = ap.analyze(content)
    assert "generic_placeholders" in _types(f)


# ---- Carrossel com 1 card = BLOCK -------------------------------------

def test_carousel_one_card_blocks():
    content = ('{"messages":[{"message":{"attachment":{"type":"template","payload":'
               '{"template_type":"generic","elements":[{"title":"X","image_url":"http://i"}]}}}}]}\n')
    f = ap.analyze(content)
    assert "carousel_misuse" in _types(f)


# ---- JSON obrigatório é dinâmico: block se age, warn se só conversa ---

def test_json_required_is_block_when_agent_acts():
    # tem actions → json_obrigatorio ausente deve ser block
    content = '{"actions":[{"action":"set_field_value","field_name":"x","value":"y"}]}\n'
    f = ap.analyze(content)
    js = [m for m in f["missing_sections"] if m["key"] == "json_obrigatorio"]
    if js:  # se ausente, deve ser block
        assert js[0]["severity"] == "block"


def test_style_lint_em_dash_warns():
    content = '{"messages":[{"message":{"text":"Tudo certo — vamos lá"}}]}\n'
    f = ap.analyze(content)
    assert "style_lints" in _types(f)
    it = _issue(f, "style_lints")
    assert all(d.get("severity") == "warn" for d in it["details"])


# ---- Validação de imagem (portada do main) ---------------------------

def test_type_inside_payload_blocks():
    content = '{"messages":[{"message":{"attachment":{"payload":{"type":"image","url":"http://x/a.jpg"}}}}]}\n'
    f = ap.analyze(content)
    assert "type_inside_payload" in _types(f)
    it = _issue(f, "type_inside_payload")
    assert all(d.get("severity") == "block" for d in it["details"])


def test_webp_image_blocks():
    content = '{"messages":[{"message":{"attachment":{"type":"image","payload":{"url":"http://x/a.webp"}}}}]}\n'
    f = ap.analyze(content)
    it = _issue(f, "forbidden_image_formats")
    assert it is not None
    assert any(d.get("severity") == "block" and d.get("status") == "forbidden" for d in it["details"])


def test_jpg_image_ok():
    content = '{"messages":[{"message":{"attachment":{"type":"image","payload":{"url":"http://x/a.jpg"}}}}]}\n'
    f = ap.analyze(content)
    assert "forbidden_image_formats" not in _types(f)
    assert "type_inside_payload" not in _types(f)


def test_ambiguous_image_warns():
    content = '{"messages":[{"message":{"attachment":{"type":"image","payload":{"url":"http://x/img.aspx"}}}}]}\n'
    f = ap.analyze(content)
    it = _issue(f, "forbidden_image_formats")
    assert it is not None
    assert all(d.get("severity") == "warn" for d in it["details"])


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

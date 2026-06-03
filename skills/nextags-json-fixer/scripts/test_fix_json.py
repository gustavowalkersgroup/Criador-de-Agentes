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

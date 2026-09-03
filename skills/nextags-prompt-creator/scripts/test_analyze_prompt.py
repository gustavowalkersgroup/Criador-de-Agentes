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


# ---- Promessa de envio sem a action que entrega -----------------------

def test_promessa_sem_send_flow_warns():
    content = '{"messages":[{"message":{"text":"Claro! Vou te enviar a tabela de medidas."}}]}\n'
    f = ap.analyze(content)
    it = _issue(f, "promessa_sem_entrega")
    assert it is not None
    assert it["details"][0]["severity"] == "warn"


def test_promessa_com_send_flow_ok():
    content = ('{"messages":[{"message":{"text":"Vou te enviar a tabela de medidas."}}],'
               '"actions":[{"action":"send_flow","flow_id":"123"}]}\n')
    f = ap.analyze(content)
    assert "promessa_sem_entrega" not in _types(f)


def test_promessa_com_attachment_ok():
    content = ('{"messages":[{"message":{"text":"Já te mando a tabela."}},'
               '{"message":{"attachment":{"type":"image","payload":{"url":"http://a.jpg"}}}}]}\n')
    f = ap.analyze(content)
    assert "promessa_sem_entrega" not in _types(f)


def test_mensagem_sem_promessa_nao_dispara():
    content = '{"messages":[{"message":{"text":"O prazo de entrega é de 5 dias úteis."}}]}\n'
    f = ap.analyze(content)
    assert "promessa_sem_entrega" not in _types(f)


# ---- Limite de 20 caracteres no título do botão -----------------------
# O passo "Filtro JSON" do fluxo (reparador de JSON) troca title > 20 chars
# por "Comprar agora" sem sinalizar — num bot de SAC isso é absurdo.

def test_button_title_20_chars_ok():
    content = ('{"messages":[{"message":{"attachment":{"type":"template","payload":'
               '{"template_type":"button","text":"x","buttons":'
               '[{"type":"web_url","url":"http://a","title":"Rastrear meu pedido"}]}}}}]}\n')
    f = ap.analyze(content)
    it = _issue(f, "button_misuse")
    assert it is None or not any("caracteres" in d.get("problem", "") for d in it["details"])


def test_button_title_over_20_chars_blocks():
    content = ('{"messages":[{"message":{"attachment":{"type":"template","payload":'
               '{"template_type":"button","text":"x","buttons":'
               '[{"type":"web_url","url":"http://a","title":"Acompanhar meu pedido agora"}]}}}}]}\n')
    f = ap.analyze(content)
    it = _issue(f, "button_misuse")
    assert it is not None
    d = [x for x in it["details"] if "caracteres" in x.get("problem", "")]
    assert d and d[0]["severity"] == "block"
    assert "Comprar agora" in d[0]["problem"]


def test_button_title_over_20_chars_in_postback_blocks():
    content = ('{"messages":[{"message":{"attachment":{"type":"template","payload":'
               '{"template_type":"button","text":"x","buttons":'
               '[{"type":"postback","payload":"123","title":"Falar com um atendente humano"}]}}}}]}\n')
    f = ap.analyze(content)
    it = _issue(f, "button_misuse")
    assert any("caracteres" in d.get("problem", "") for d in it["details"])


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


# ---- anti_alucinação: padrões ampliados (do teste de corpus) ---------

def _missing_keys(f):
    return {m["key"] for m in f["missing_sections"]}


def test_anti_aluc_nao_pode_inventar_presente():
    c = '{"messages":[{"message":{"text":"oi"}}]}\nÉ ESTRITAMENTE PROIBIDO prometer verificar; você não pode inventar um status.\n'
    assert "anti_alucinacao" not in _missing_keys(ap.analyze(c))


def test_anti_aluc_sempre_consulte_presente():
    c = '{"messages":[{"message":{"text":"oi"}}]}\nSempre consulte a base antes de citar qualquer produto.\n'
    assert "anti_alucinacao" not in _missing_keys(ap.analyze(c))


def test_anti_aluc_reinventar_nao_conta():
    # "não reinventar texto" não é anti-alucinação de dados → deve seguir faltando
    c = '{"messages":[{"message":{"text":"oi"}}]}\nAo transferir, não reinventar texto ou lógica.\n'
    assert "anti_alucinacao" in _missing_keys(ap.analyze(c))


def test_anti_aluc_genuinamente_ausente():
    c = '{"messages":[{"message":{"text":"oi, tudo bem?"}}]}\n'
    assert "anti_alucinacao" in _missing_keys(ap.analyze(c))


# ---- send_flow_transferencia: intenção de transferência + modo fixer --------

def _missing_sev(f):
    return {m["key"]: m["severity"] for m in f["missing_sections"]}


def test_transfer_intent_counts_as_present():
    c = '{"messages":[{"message":{"text":"oi"}}]}\nSe não resolver, vou te encaminhar para um atendente humano.\n'
    assert "send_flow_transferencia" not in _missing_keys(ap.analyze(c))


def test_send_flow_missing_is_block_in_creator():
    c = '{"messages":[{"message":{"text":"oi, tudo bem?"}}]}\n'  # sem mecanismo de transferência
    assert _missing_sev(ap.analyze(c, mode="creator")).get("send_flow_transferencia") == "block"


def test_send_flow_missing_is_warn_in_fixer():
    c = '{"messages":[{"message":{"text":"oi, tudo bem?"}}]}\n'
    assert _missing_sev(ap.analyze(c, mode="fixer")).get("send_flow_transferencia") == "warn"


# ---- Roteamento canônico: a IA nunca grava setor_agente / tipo_setor -------

def test_ia_grava_setor_agente_blocks():
    content = ('{"messages":[{"message":{"text":"vou te passar pro SAC"}}],'
               '"actions":[{"action":"set_field_value","field_name":"setor_agente","value":"sac"}]}\n')
    f = ap.analyze(content)
    assert "ia_grava_campo_de_roteamento" in _types(f)
    it = _issue(f, "ia_grava_campo_de_roteamento")
    assert all(d.get("severity") == "block" for d in it["details"])
    assert f["summary"]["ia_grava_campo_de_roteamento_count"] == 1


def test_ia_grava_tipo_setor_blocks():
    content = '{"actions":[{"action":"set_field_value","field_name":"tipo_setor","value":"bot"}]}\n'
    f = ap.analyze(content)
    assert "ia_grava_campo_de_roteamento" in _types(f)


def test_handoff_canonico_nao_flagra_roteamento():
    # trio canônico completo: nenhum campo de roteamento → sem finding
    content = ('{"messages":[{"message":{"text":"Vou te conectar com o time agora!"}}],'
               '"actions":['
               '{"action":"set_field_value","field_name":"motivo_transferencia","value":"rastreio"},'
               '{"action":"set_field_value","field_name":"prioridade_pipeline","value":"media"},'
               '{"action":"set_field_value","field_name":"resumo_pipeline","value":"Ana, pedido 1188, sem movimentacao no rastreio. Nao consigo abrir reclamacao; escalo."},'
               '{"action":"send_flow","flow_id":"<ID_DO_FLUXO_PIPELINE>"}]}\n')
    f = ap.analyze(content)
    assert "ia_grava_campo_de_roteamento" not in _types(f)
    assert "trio_handoff_incompleto" not in _types(f)
    assert "motivo_fora_do_enum" not in _types(f)
    assert "prioridade_fora_do_enum" not in _types(f)
    assert "send_flow_antes_de_set_field" not in _types(f)


# ---- motivo_transferencia fora do enum canônico = WARN ---------------------

def test_motivo_fora_do_enum_warns_e_sugere_canonico():
    content = ('{"actions":[{"action":"set_field_value","field_name":"motivo_transferencia",'
               '"value":"duvidas"},{"action":"send_flow","flow_id":"1"}]}\n')
    f = ap.analyze(content)
    it = _issue(f, "motivo_fora_do_enum")
    assert it is not None
    assert it["details"][0]["severity"] == "warn"
    assert it["details"][0]["suggestion"] == "duvida"


def test_motivo_sac_geral_sugere_duvida():
    content = '{"actions":[{"action":"set_field_value","field_name":"motivo_transferencia","value":"sac_geral"}]}\n'
    f = ap.analyze(content)
    assert _issue(f, "motivo_fora_do_enum")["details"][0]["suggestion"] == "duvida"


def test_motivo_canonico_nao_warna():
    for valor in ("ugc", "colaboracao", "influencer", "revenda", "atacado",
                  "vendas", "carrinho", "rastreio", "devolucao", "troca", "duvida"):
        content = ('{"actions":[{"action":"set_field_value","field_name":"motivo_transferencia",'
                   f'"value":"{valor}"}}]}}\n')
        assert "motivo_fora_do_enum" not in _types(ap.analyze(content)), valor


def test_motivo_placeholder_nao_warna():
    # gabarito para o LLM preencher não é valor de enum a validar
    content = '{"actions":[{"action":"set_field_value","field_name":"motivo_transferencia","value":"<enum>"}]}\n'
    assert "motivo_fora_do_enum" not in _types(ap.analyze(content))


# ---- prioridade_pipeline fora de baixa|media|alta = BLOCK -----------------

def test_prioridade_fora_do_enum_blocks():
    content = '{"actions":[{"action":"set_field_value","field_name":"prioridade_pipeline","value":"urgente"}]}\n'
    f = ap.analyze(content)
    it = _issue(f, "prioridade_fora_do_enum")
    assert it is not None
    assert all(d.get("severity") == "block" for d in it["details"])


def test_prioridade_com_acento_blocks():
    # "média" com acento não bate com a opção cadastrada (Seleção única)
    content = '{"actions":[{"action":"set_field_value","field_name":"prioridade_pipeline","value":"média"}]}\n'
    assert "prioridade_fora_do_enum" in _types(ap.analyze(content))


def test_prioridade_canonica_ok():
    for valor in ("baixa", "media", "alta"):
        content = ('{"actions":[{"action":"set_field_value","field_name":"prioridade_pipeline",'
                   f'"value":"{valor}"}}]}}\n')
        assert "prioridade_fora_do_enum" not in _types(ap.analyze(content)), valor


# ---- trio de handoff incompleto = WARN -----------------------------------

def test_trio_handoff_incompleto_warns():
    content = ('{"messages":[{"message":{"text":"Vou te conectar!"}}],'
               '"actions":[{"action":"set_field_value","field_name":"motivo_transferencia","value":"troca"},'
               '{"action":"send_flow","flow_id":"1775096402729"}]}\n')
    f = ap.analyze(content)
    it = _issue(f, "trio_handoff_incompleto")
    assert it is not None
    assert it["details"][0]["severity"] == "warn"
    assert set(it["details"][0]["missing"]) == {"prioridade_pipeline", "resumo_pipeline"}


def test_trio_handoff_sem_resumo_warns():
    content = ('{"actions":[{"action":"set_field_value","field_name":"motivo_transferencia","value":"vendas"},'
               '{"action":"set_field_value","field_name":"prioridade_pipeline","value":"alta"},'
               '{"action":"send_flow","flow_id":"1"}]}\n')
    f = ap.analyze(content)
    assert _issue(f, "trio_handoff_incompleto")["details"][0]["missing"] == ["resumo_pipeline"]


def test_send_flow_sem_motivo_nao_dispara_trio():
    # disparo silencioso (NPS) não é transferência — não exige trio
    content = '{"actions":[{"action":"send_flow","flow_id":"<ID_DO_FLUXO_NPS>"}]}\n'
    assert "trio_handoff_incompleto" not in _types(ap.analyze(content))


# ---- ordem das actions: send_flow por último ------------------------------

def test_send_flow_antes_de_set_field_warns():
    content = ('{"actions":[{"action":"send_flow","flow_id":"1"},'
               '{"action":"set_field_value","field_name":"resumo_pipeline","value":"contexto"}]}\n')
    f = ap.analyze(content)
    it = _issue(f, "send_flow_antes_de_set_field")
    assert it is not None
    assert it["details"][0]["severity"] == "warn"


def test_set_field_antes_de_send_flow_ok():
    content = ('{"actions":[{"action":"set_field_value","field_name":"resumo_pipeline","value":"contexto"},'
               '{"action":"add_tag","tag_name":"humano"},'
               '{"action":"send_flow","flow_id":"1"}]}\n')
    assert "send_flow_antes_de_set_field" not in _types(ap.analyze(content))


# ---- AVISOS ATIVOS (SPEC §5.1) -------------------------------------------

_AVISOS_BLOCO = (
    "📣 AVISOS ATIVOS\n"
    "> 🔧 NOTA PARA EDITORES: edite SÓ as linhas entre os marcadores. Vazio = sem aviso.\n"
    "=== INÍCIO DOS AVISOS ===\n"
    "(nenhum aviso ativo)\n"
    "=== FIM DOS AVISOS ===\n"
)


def test_avisos_ativos_ausente_warna():
    f = ap.analyze('{"messages":[{"message":{"text":"oi"}}]}\n')
    assert f["avisos_ativos_presente"] is False
    assert f["summary"]["avisos_ativos_missing_count"] == 1
    assert f["avisos_ativos"][0]["severity"] == "warn"


def test_avisos_ativos_presente_ok():
    f = ap.analyze(_AVISOS_BLOCO + '{"messages":[{"message":{"text":"oi"}}]}\n')
    assert f["avisos_ativos_presente"] is True
    assert f["avisos_ativos"] == []
    assert f["summary"]["avisos_ativos_missing_count"] == 0


def test_avisos_ativos_sem_marcadores_warna():
    f = ap.analyze("📣 AVISOS ATIVOS\n(nenhum aviso ativo)\n")
    assert f["avisos_ativos_presente"] is True
    assert f["avisos_ativos"][0]["kind"] == "avisos_ativos_sem_marcadores"


# ---- Nota para editores: whitelist de meta-doc + limite de tamanho -------

def test_nota_editor_nao_e_meta_doc():
    # sem a whitelist, "**Versão:**" dentro da nota viraria versao_metadata (warn)
    content = ("# PROMPT — AGENTE X\n"
               "> 🔧 NOTA PARA EDITORES: troque só o id, mantenha o nome da chave. Sem **Versão:** aqui.\n")
    f = ap.analyze(content)
    assert [i for i in f["forbidden_meta_sections"] if i["kind"] == "versao_metadata"] == []


def test_meta_doc_fora_da_nota_continua_flagrada():
    content = "# PROMPT — AGENTE X\n**Versão:** v3.0\n"
    f = ap.analyze(content)
    assert [i for i in f["forbidden_meta_sections"] if i["kind"] == "versao_metadata"]


def test_nota_editor_longa_warna():
    longa = "> 🔧 NOTA PARA EDITORES: " + ("mantenha os valores exatamente como estão " * 8)
    f = ap.analyze(longa + "\n")
    assert f["summary"]["nota_editor_longa_count"] == 1
    assert f["nota_editor_longa"][0]["kind"] == "nota_editor_longa"
    assert f["nota_editor_longa"][0]["severity"] == "warn"


def test_nota_editor_curta_ok():
    f = ap.analyze("> 🔧 NOTA PARA EDITORES: não altere os valores: o fluxo filtra estas strings.\n")
    assert f["summary"]["nota_editor_longa_count"] == 0


# ---- Sincronia das 2 cópias do analyzer (creator == fixer) ------------------

def test_analyzer_copies_in_sync():
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    a = open(os.path.join(here, "analyze_prompt.py"), encoding="utf-8").read()
    b_path = os.path.join(here, "..", "..", "nextags-prompt-fixer", "scripts", "analyze_prompt.py")
    b = open(b_path, encoding="utf-8").read()
    assert a == b, "as 2 cópias de analyze_prompt.py divergiram — re-sincronize (cp creator → fixer)"


# ---- Sincronia das 2 cópias de cufs_nextags.md (creator == fixer) ----------

def test_cufs_nextags_copies_in_sync():
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    a_path = os.path.join(here, "..", "references", "cufs_nextags.md")
    b_path = os.path.join(here, "..", "..", "nextags-prompt-fixer", "references", "cufs_nextags.md")
    a = open(a_path, encoding="utf-8").read()
    b = open(b_path, encoding="utf-8").read()
    assert a == b, "as 2 cópias de cufs_nextags.md divergiram — re-sincronize (cp creator → fixer)"


# ---- Sincronia das 4 cópias de campos_canonicos.md -------------------------
# (creator == fixer == mcp-builder == webhook-builder)

def test_campos_canonicos_copies_in_sync():
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    source_path = os.path.join(here, "..", "references", "campos_canonicos.md")
    source = open(source_path, encoding="utf-8").read()
    other_skills = ["nextags-prompt-fixer", "nextags-mcp-builder", "nextags-webhook-builder"]
    for skill in other_skills:
        other_path = os.path.join(here, "..", "..", skill, "references", "campos_canonicos.md")
        other = open(other_path, encoding="utf-8").read()
        assert source == other, (
            f"campos_canonicos.md de {skill} divergiu do nextags-prompt-creator "
            "— re-sincronize (edite a cópia do creator e copie para as outras 3)"
        )


# ---- invalid_json: não flagar linha interna de array válido (achado no smoke e2e) ----

def test_multiline_actions_no_false_invalid_json():
    # actions multi-linha (um {"action":...}, por linha) num bloco que parseia
    # inteiro NÃO pode gerar invalid_json (cada elemento isolado falharia por
    # vírgula final — era falso-positivo block).
    content = (
        '{\n'
        '  "messages":[{"message":{"text":"ok"}}],\n'
        '  "actions":[\n'
        '    {"action":"set_field_value","field_name":"first_name","value":"x"},\n'
        '    {"action":"set_field_value","field_name":"Email","value":"y"},\n'
        '    {"action":"send_flow","flow_id":"123"}\n'
        '  ]\n'
        '}\n'
    )
    assert ap.analyze(content)["summary"]["invalid_json_count"] == 0


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

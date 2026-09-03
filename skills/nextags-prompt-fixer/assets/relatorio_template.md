# Relatório de Correção — {NOME_DO_PROMPT}

**Versão original:** `{ARQUIVO_ORIGINAL}`
**Versão corrigida:** `{ARQUIVO_CORRIGIDO}`
**Data:** {DATA}
**Skill:** nextags-prompt-fixer

---

## Resumo

- **Correções aplicadas automaticamente:** {N_FIX}
- **Pendências para revisão humana:** {N_PENDING}
- **Funções preservadas:** persona, fluxos, base de conhecimento, regras de negócio.

> {RESUMO_NARRATIVO_CURTO}

---

## ✅ Correções aplicadas

> Cada item lista exatamente o que foi mudado e por quê. Use os números de
> linha para conferir no diff.

### 1. {TITULO_CORRECAO_1}

- **Tipo:** {TIPO_VIOLACAO_1}
- **Linha:** {LINHA_1}
- **Por quê:** {JUSTIFICATIVA_1}

**Antes:**
```{LINGUAGEM_1}
{TRECHO_ANTES_1}
```

**Depois:**
```{LINGUAGEM_1}
{TRECHO_DEPOIS_1}
```

### 2. {TITULO_CORRECAO_2}

…

---

## ⚠️ Pendências para revisão humana

> Nestes pontos, a correção não pôde ser aplicada de forma segura sem
> conhecer informações que só você tem (ex.: ID de fluxo, URL de produto,
> regra de negócio específica). Resolva antes de subir em produção.

### 1. {TITULO_PENDENCIA_1}

- **Tipo:** {TIPO_PENDENCIA_1}
- **Localização:** {LOCALIZACAO_1}
- **O que falta:** {DESCRICAO_FALTA_1}
- **Sugestão:** {SUGESTAO_1}

### 2. …

---

## 🔍 Verificações executadas

- [x] Validação de sintaxe JSON em todos os blocos `json` do prompt.
- [x] Detecção de ações proibidas (`transfer_conversation_to`,
      `assign_conversation`, `unassign_conversation`).
- [x] Uso de botões apenas com `web_url` externo.
- [x] Carrosséis com pelo menos 2 elementos.
- [x] `attachment.type` FORA de `payload` (no mesmo nível).
- [x] URLs de imagem em JPEG/PNG apenas — WebP/AVIF/SVG/GIF flagados.
- [x] Ausência de markdown (`**`, `#`, `` ` ``, etc.) dentro de campos
      `text`, `subtitle` e `title` do JSON.
- [x] Presença das seções de instrução obrigatórias:
      anti-alucinação, não-revelar-IA, JSON obrigatório, transferência via
      `send_flow`, texto como padrão, manter-se no escopo.
- [x] Menções a ações proibidas em prosa fora de blocos JSON.
- [x] Bloco `📣 AVISOS ATIVOS` presente no formato canônico
      (`avisos_ativos_presente`).
- [x] Notas `> 🔧 NOTA PARA EDITORES:` dentro do limite de 1 linha
      (`nota_editor_longa`).
- [x] A IA nunca grava `setor_agente`/`tipo_setor`
      (`ia_grava_campo_de_roteamento` — bloqueante).
- [x] `motivo_transferencia` dentro do enum canônico por setor
      (`motivo_fora_do_enum`).
- [x] `prioridade_pipeline` em `baixa|media|alta`
      (`prioridade_pipeline` fora do enum — bloqueante).
- [x] Trio de handoff completo antes de `send_flow`: `motivo_transferencia`
      + `prioridade_pipeline` + `resumo_pipeline` (`trio_handoff_incompleto`).
- [x] Ordem das actions: `set_field_value` sempre antes de `send_flow`
      (`send_flow_antes_de_set_field`).

*(Exceção: prompts de Roteador/Revalidador — saída de 1 palavra — não são
avaliados pelos itens acima que pressupõem JSON/handoff; ver Regra 23 de
`regras_absolutas.md`.)*

---

## 📋 Estatísticas

| Métrica | Valor |
|---|---|
| Blocos JSON encontrados | {TOTAL_JSON_BLOCKS} |
| Blocos JSON com problemas | {JSON_BLOCKS_WITH_ISSUES} |
| JSONs inválidos (sintaxe) | {INVALID_JSON_COUNT} |
| Ações proibidas em JSON | {FORBIDDEN_ACTIONS_COUNT} |
| Botões usados sem `web_url` | {BUTTON_MISUSE_COUNT} |
| Carrosséis com menos de 2 itens | {CAROUSEL_MISUSE_COUNT} |
| Markdown dentro de JSON | {MARKDOWN_IN_JSON_COUNT} |
| `type` dentro de `payload` (deve ficar fora) | {TYPE_INSIDE_PAYLOAD_COUNT} |
| Imagens em formato proibido (WebP/AVIF/SVG/GIF) | {FORBIDDEN_IMAGE_FORMATS_COUNT} |
| Seções obrigatórias faltando | {MISSING_SECTIONS_COUNT} |
| Exemplos negativos preservados (não contados) | {NEGATIVE_EXAMPLES_SKIPPED} |
| Campos de roteamento gravados pela IA (`setor_agente`/`tipo_setor` — bloqueante) | {IA_GRAVA_CAMPO_ROTEAMENTO_COUNT} |
| `motivo_transferencia` fora do enum canônico | {MOTIVO_FORA_DO_ENUM_COUNT} |

---

## Próximos passos sugeridos

1. Revisar as pendências listadas acima e preencher os placeholders.
2. Testar o prompt corrigido em um ambiente de staging antes de produção.
3. Se houver mais ajustes, rodar a skill novamente — ela é idempotente.

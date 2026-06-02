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

---

## Próximos passos sugeridos

1. Revisar as pendências listadas acima e preencher os placeholders.
2. Testar o prompt corrigido em um ambiente de staging antes de produção.
3. Se houver mais ajustes, rodar a skill novamente — ela é idempotente.

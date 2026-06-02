# Relatório de Correção — Saída JSON do Agente NexTags

**Arquivo corrigido:** `{ARQUIVO_CORRIGIDO}`
**Data:** {DATA}
**Skill:** nextags-json-fixer

---

## Resumo

- **Blocos JSON detectados no input:** {BLOCOS_IN}
- **Blocos válidos após correção:** {BLOCOS_OUT}
- **Reparos de sintaxe:** {N_SYNTAX}
- **Correções semânticas:** {N_SEMANTIC}
- **Pendências para revisão humana:** {N_PENDING}

> {RESUMO_NARRATIVO_CURTO}

---

## 🩹 Reparos de sintaxe

> Ajustes aplicados antes do parse para que o JSON virasse válido.
> Não mudam intenção — só forma.

{LISTA_SYNTAX_FIXES}

*(Se não houver, escreva: "Nenhum — o JSON já estava sintaticamente válido.")*

---

## ✅ Correções semânticas aplicadas

> Cada item descreve uma violação estrutural que foi corrigida
> automaticamente, sem inventar conteúdo.

{LISTA_SEMANTIC_FIXES}

*(Se não houver, escreva: "Nenhuma — a estrutura semântica já estava conforme schema.")*

---

## ⚠️ Pendências para revisão humana

> Nestes pontos a correção exigiria inventar conteúdo (URL, flow_id,
> texto, segundo card do carrossel). Resolva antes de testar em produção.

{LISTA_PENDING}

*(Se não houver, escreva: "Nenhuma — JSON corrigido está pronto para uso.")*

---

## 🔍 Verificações executadas

- [x] Extração de JSON de markdown/prosa em volta.
- [x] Reparos seguros de sintaxe (aspas curvas, vírgula trailing,
      comentários, BOM).
- [x] Estrutura raiz: presença de `messages` e/ou `actions`.
- [x] `messages` é array; cada item é objeto com `message` ou inteiro
      typing indicator.
- [x] Wrapper `message` ausente: embrulho automático.
- [x] `attachment.type` ∈ {image, video, audio, file, template}.
- [x] `attachment.type` está FORA de `payload` (move pra fora se estiver dentro).
- [x] URLs de imagem são absolutas (http://, https://) e em JPEG/PNG (rejeita WebP/AVIF/SVG/GIF).
- [x] `template_type` ∈ {generic, button}.
- [x] Carrossel com ≥ 2 elementos.
- [x] Botões `web_url` com `url`; `postback` com `payload`.
- [x] Typing indicator é inteiro entre 1–30 segundos.
- [x] Markdown removido de `text`/`title`/`subtitle`.
- [x] Nomes de ações normalizados (8 ações canônicas).
- [x] Ações com campos obrigatórios presentes.

---

## Próximos passos sugeridos

1. Revisar e preencher cada pendência listada acima.
2. Testar a saída corrigida no ambiente de staging da NexTags antes de
   produção.
3. Se o agente continua gerando JSON quebrado pelo mesmo motivo,
   considere ajustar o **prompt do agente** com a skill
   `nextags-prompt-fixer` — esta skill aqui corrige saída em runtime,
   não a causa raiz.

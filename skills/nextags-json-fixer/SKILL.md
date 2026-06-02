---
name: nextags-json-fixer
description: "Valida e corrige a SAÍDA JSON do agente NexTags Messenger Messaging Platform — não o prompt, mas o JSON devolvido em runtime. Use quando o usuário cola output do bot quebrado: markdown vazando, sem chave `messages`, attachment type inválido, botão sem `url`, carrossel com <2 cards, ação com nome errado (`addTag`, `transfer_to_human`), JSON inválido (vírgula sobrando, aspa curva, fence ```json). Triggers PT-BR ('corrigir json do agente', 'json do bot quebrado', 'validar saída do agente', 'consertar resposta do bot') e EN ('fix nextags agent json', 'validate messenger platform json'). Devolve JSON corrigido + relatório PT-BR. Segue o schema oficial: chaves `messages`/`actions`, tipos text/image/video/audio/file/template generic|button, typing indicator inteiro, e as 8 ações (add_tag, remove_tag, set/unset_field_value, send_flow, transfer_conversation_to, assign/unassign_conversation). Diferente da nextags-prompt-fixer (corrige o .md do prompt), esta atua no JSON de runtime."
---

# NexTags JSON Fixer

Valida e corrige a **saída JSON do agente IA** da plataforma NexTags
Messenger Messaging Platform — o JSON que o agente devolve em runtime e
que o middleware da NexTags consome pra renderizar mensagens, mídias,
carrosséis, botões e disparar ações.

## O que essa skill NÃO faz

- **Não corrige o prompt** do agente. Pra isso use `nextags-prompt-fixer`.
- **Não inventa conteúdo** que não estava no JSON original (textos, URLs,
  flow_ids, image_url). Se faltar, vira placeholder + pendência.
- **Não altera a intenção** da resposta. Se o agente quis enviar um
  carrossel com 1 card, a skill vira pendência (não inventa o segundo
  card) — opcionalmente sugere converter pra imagem simples.

## Quando essa skill se aplica

Use sempre que o usuário trouxer um JSON gerado por agente NexTags que:

- Está **inválido sintaticamente** (vírgula sobrando, aspa curva `"`,
  chave duplicada, fence ` ```json ` em volta).
- Veio embrulhado em **markdown / texto explicativo** ("Aqui está o JSON: …").
- **Falta a chave `messages`** ou tem estrutura achatada (ex.:
  `{"text":"oi"}` direto, sem o wrapper `{messages:[{message:{...}}]}`).
- Usa **tipo de attachment não suportado** (ex.: `"type":"sticker"`).
- Tem **botão `web_url` sem `url`**, ou `postback` sem `payload`.
- Tem **carrossel com menos de 2 elementos** (a plataforma exige ≥ 2).
- Usa **ação com nome errado** (ex.: `"addTag"` em vez de `"add_tag"`,
  `"transfer_to_human"` em vez de `"transfer_conversation_to"`).
- Tem **typing indicator inválido** (string em vez de inteiro, ou valor
  fora do range razoável 1–30s).

## Fluxo de trabalho

### 1. Captura do input

O input pode chegar de três formas:

- **Texto colado no chat** (mais comum) → salve em
  `/home/claude/input_json.txt` antes de processar.
- **Arquivo `.json` / `.txt` enviado** → leia direto de
  `/mnt/user-data/uploads/<nome>`.
- **JSON embutido no meio de uma mensagem** → extraia primeiro o(s)
  bloco(s); o script `fix_json.py` faz isso (suporta fence markdown e
  prosa em volta).

### 2. Roda o corretor

```bash
# Substitua <SKILL_DIR> pelo diretório desta skill.
python <SKILL_DIR>/scripts/fix_json.py \
    <caminho_do_input> \
    --output /tmp/fixed.json \
    --report /tmp/findings.json
```

`fix_json.py` faz tudo em um passo:

1. Extrai o(s) bloco(s) JSON do input (remove fences, prosa em volta).
2. Tenta parsear; se falhar, aplica reparos seguros (aspas curvas →
   retas, vírgula trailing, BOM, single-quotes → double-quotes em chaves).
3. Valida cada bloco contra o schema do Messenger Messaging Platform.
4. Aplica correções automáticas pra violações estruturais que **não
   exigem inventar conteúdo**.
5. Marca como **pendência** tudo que exige decisão humana (URL faltando,
   flow_id faltando, segundo card do carrossel faltando).
6. Escreve `fixed.json` (JSON corrigido pronto) e `findings.json`
   (estruturado, com lista de correções + pendências).

### 3. Apresenta resultado

Sempre nessa ordem:

1. **Resumo curto no chat** (3–6 linhas): quantas correções, quantas
   pendências, principais mudanças.
2. **JSON corrigido em bloco de código** dentro do chat (não em fence
   ` ```json ` — em fence simples, pra evitar que o usuário copie o fence
   junto). Se for muito grande (> 80 linhas), salve em
   `/mnt/user-data/outputs/fixed.json` e use `present_files`.
3. **Relatório completo** em
   `/mnt/user-data/outputs/relatorio-json.md`, usando
   `assets/relatorio_template.md`. Apresente via `present_files`.

## Princípios de correção

Consulte **sempre `references/schema.md`** antes de aplicar fixes — ele
documenta o schema oficial completo com exemplos validados.

| Violação | Estratégia |
|---|---|
| JSON inválido (sintaxe) | Reparos seguros automáticos (vírgula, aspa, fence). Se ambíguo → pendência. |
| Markdown / prosa em volta do JSON | Extrair só o JSON; descartar o resto. |
| Estrutura achatada (sem `messages`) | Embrulhar em `{"messages":[{"message":<original>}]}` se o conteúdo for um único `message`. |
| Tipo de attachment não suportado | Converter pra texto simples ou marcar como pendência (depende do contexto). |
| Botão `web_url` sem `url` | Converter botão pra texto inline na mensagem; OU pendência se intenção for ambígua. |
| Botão `postback` sem `payload` | Pendência (precisa do flow_id). |
| Carrossel com 1 elemento | Converter pra `message` com `attachment` `image` + texto; OU pendência. |
| Carrossel com 0 elementos | Remover bloco; pendência. |
| Nome de ação errado | Mapear pra nome canônico (ver `references/schema.md`). |
| Ação com campo faltando (ex.: `set_field_value` sem `value`) | Pendência. |
| Typing indicator string | Converter pra inteiro se for numérico (`"4"` → `4`); senão remover. |
| Typing indicator fora do range | Clampar em [1, 30]. |
| Markdown em campos `text`/`title`/`subtitle` (`**bold**`, `# H1`) | Remover marcação, preservar conteúdo. |

## Idempotência

Rodar a skill duas vezes sobre o mesmo input no segundo run deve produzir
zero correções. Se não, é bug — investigue antes de entregar.

## Idioma

Relatório **sempre em PT-BR**. O JSON corrigido preserva o idioma dos
textos originais.

## Estrutura desta skill

```
nextags-json-fixer/
├── SKILL.md                     (este arquivo)
├── scripts/
│   └── fix_json.py              extrator + validador + corretor
├── references/
│   └── schema.md                schema Messenger Messaging Platform
└── assets/
    └── relatorio_template.md    template do relatório PT-BR
```

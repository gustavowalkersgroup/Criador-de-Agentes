---
name: nextags-prompt-fixer
description: "Audit and fix customer service AI prompts written for the NexTags Messenger Messaging Platform. Use whenever the user wants to review, validate, lint, audit or correct a NexTags-style prompt — uploaded as `.md` or pasted as text. Triggers in Portuguese ('corrigir prompt', 'validar prompt', 'auditar prompt', 'revisar prompt do bot', 'JSON do prompt quebrado') and English ('fix nextags prompt', 'lint bot prompt'). Catches and repairs invalid JSON, transfer actions (recommends `send_flow` as the default; `transfer_conversation_to`/`assign_conversation` stay valid as fallback/special cases), `web_url` buttons without `url`, carousels with under 2 items, standard-markdown leaking into JSON text fields (WhatsApp markup `*bold*`/`_italic_`/`~strike~` renders and is allowed), and missing required sections (anti-hallucination, JSON-only output, `send_flow` transfers, text-as-default). Preserves persona, flows, knowledge base and business rules — only fixes structural violations. Outputs corrected `.md` plus Portuguese change report. Trigger any time NexTags, attendance bots or customer service prompts come up, even without the words 'lint' or 'fix'."
---

# NexTags Prompt Fixer

Audita e corrige prompts de agentes de atendimento da plataforma NexTags
contra as **Regras Absolutas** da Messenger Messaging Platform.

## O que essa skill faz

Recebe um prompt (`.md` ou texto colado) e devolve:

1. Uma **versão corrigida** do prompt (`.md`).
2. Um **relatório em Markdown** descrevendo cada mudança e cada pendência.

A skill **só toca em violações estruturais**. Ela jamais altera persona,
fluxos, base de conhecimento, IDs de fluxos, URLs, tom de voz ou qualquer
regra de negócio. Quando uma correção exige decisão de produto que só o
humano dono do projeto pode tomar (ex.: "qual é o ID do fluxo de
transferência?"), a skill **deixa um placeholder marcado** e lista no
relatório como pendência.

**Relação com a `nextags-json-fixer`.** As duas tratam
`transfer_conversation_to`/`assign_conversation`/`unassign_conversation`
como **válidas** — nenhuma as proíbe. A json-fixer valida o JSON que a
plataforma ACEITA em runtime; esta skill cuida do prompt e apenas **recomenda
`send_flow` como padrão** (porque 100% das transferências de qualidade nos 25
prompts de produção usam `send_flow`). Mas `transfer_conversation_to` é
fallback legítimo quando não há fluxo de transferência, e `assign_conversation`
é caso especial raro (atendente específico). São camadas complementares, sem
conflito. Ver Regra 2 em `regras_absolutas.md`.

## Quando essa skill se aplica

Use sempre que o usuário mencionar:

- Um prompt de agente NexTags / Messenger Messaging Platform.
- Erros em prompts de atendimento, bots, chatbots para WhatsApp/Messenger.
- "Corrigir / validar / auditar / revisar / lintar" um prompt.
- JSON quebrado em exemplos de resposta.
- Suspeita de uso indevido de botões, carrosséis ou ações da plataforma.

## Fluxo de trabalho

### 1. Captura o input

O input pode chegar de duas formas:

- **Arquivo `.md` enviado** → caminho em `/mnt/user-data/uploads/<nome>.md`.
- **Texto colado no chat** → salve em `/home/claude/input_prompt.md` antes
  de prosseguir.

Se o input for ambíguo (ex.: o usuário descreveu um problema mas não enviou
o prompt), peça o conteúdo antes de continuar.

### 2. Roda a análise

A skill traz um analisador determinístico em Python que detecta todos os
problemas de uma vez. Use-o sempre — não tente reinventar a auditoria
"no olho".

```bash
# Substitua <SKILL_DIR> pelo diretório desta skill (onde este SKILL.md vive).
python <SKILL_DIR>/scripts/analyze_prompt.py \
    <caminho_do_prompt.md> \
    --mode fixer \
    --output /tmp/findings.json
```

O script produz um JSON estruturado com:

- `summary` — contadores agregados.
- `json_blocks` — cada bloco JSON do prompt, marcado como válido/inválido,
  com a lista de violações encontradas e se é um exemplo negativo
  intencional (esses são preservados, não contam como erro).
- `forbidden_actions_in_prose` — menções a ações proibidas no texto fora
  dos blocos JSON.
- `missing_sections` — seções de instrução obrigatórias ausentes.
- `json_only_instruction_present` — booleano: o prompt instrui o agente a
  responder somente em JSON?

Leia o `findings.json` antes de propor correções.

### 3. Aplica correções com critério

**Sempre consulte `references/regras_absolutas.md` antes de corrigir** —
ele descreve o padrão de fix para cada tipo de violação, com exemplos antes
e depois.

Princípios:

- **Preserve a função, corrija só a forma.** Se uma correção mudaria o
  comportamento do agente (não só a estrutura do JSON), vira pendência.
- **Não invente valores.** Se faltar um `flow_id`, uma URL, ou texto que
  não está no prompt, deixe placeholder explícito (ex.:
  `<ID_DO_FLUXO_DE_TRANSFERENCIA>`) e liste no relatório.
- **Exemplos negativos são intocáveis.** Quando o autor mostra um JSON
  precedido de "❌ ERRADO" ou "🚫 NUNCA", esse bloco é didático. O analisador
  já marca esses como `is_negative_example: true` — não corrija.
- **Idempotência.** Rodar a skill duas vezes seguidas sobre o mesmo prompt
  no segundo run deve produzir zero correções (porque a primeira já
  resolveu tudo que dava pra resolver).
- **Idioma do prompt = idioma do output.** Se o prompt está em PT-BR, o
  arquivo corrigido continua em PT-BR. Relatório sempre em PT-BR (foi o
  combinado com o usuário).

Tabela rápida de correções (detalhes em `references/regras_absolutas.md`):

| Violação | Estratégia |
|---|---|
| JSON inválido | Reescreva com sintaxe válida, mantendo intenção. Se ambíguo → pendência. |
| `transfer_conversation_to` / `assign_conversation` | NÃO são proibidas. `send_flow` é o padrão recomendado; `transfer_conversation_to` é fallback válido quando não há fluxo de transferência, `assign_conversation` é caso especial raro (atendente específico). Só sugerir `send_flow` quando houver fluxo disponível. Ver Regra 2. |
| Botão `web_url` sem `url` | Pendência (precisa da URL) ou converter em texto. `postback` é válido (dispara fluxo) — preservar. Ver Regra 3. |
| Carrossel com 1 item | Quebrar em mensagem de texto + attachment de imagem. |
| Markdown em `text`/`subtitle` | WA-markup (`*negrito*`, `_itálico_`, `~tachado~`) RENDERIZA e é OK — não tocar. Remover só markdown-PADRÃO que vaza (`**duplo**`, `# título`, `[texto](url)`, bullets `-`, cercas ```` ``` ````). Ver Regra 5. |
| **`send_flow` sem `messages`** (regra #10) | NÃO é erro. `send_flow` DISPARA NORMALMENTE — o fluxo assume a comunicação. `messages` é transição OPCIONAL por UX, nunca obrigatória. Preservar disparo silencioso; só sugerir transição se agregar à experiência. |
| **Exemplos JSON em fence `` ```json ``** (regra #11) | Remover os fences dos exemplos. LLM em runtime copia o padrão e quebra a plataforma. |
| Menção em prosa a `transfer_conversation_to`/`assign_conversation` | Não é violação por si só (ação válida). Se houver fluxo de transferência, SUGERIR `send_flow`; senão, deixar. Ver Regra 6. |
| Seção obrigatória faltando | Inserir placeholder com bloco-padrão sugerido (não inventar regras de negócio) + listar como pendência. |
| **Seção proibida no prompt** (Auditoria, Changelog, Pendências, TODO, Notas internas, metadata expandido `**Versão:**`, `**Data:**`) | **Remover INTEIRA do prompt**. Migrar o conteúdo pro relatório (seção "Histórico de mudanças", "Pendências para revisão humana" ou "Notas técnicas/TODO"). Ver Regra 15 em `regras_absolutas.md`. |
| Função de transferência inventada/legada (`connect_user_to_human`, `transferir_suporte`, `Rotativo()`) | Converter pra `send_flow` + placeholder de `flow_id`; funções de DADO viram pendência (tool/MCP). Ver Regra 2b. |
| `send_flow` SÓ-actions (NPS/descadastro/mockup/etc.) | **NÃO corrigir** — disparo silencioso é o comportamento normal de `send_flow` (Regra 10). O fluxo fala. |
| `assign_conversation` com `admin_id` = nome ("Estela.") | `admin_id` inválido → pendência (precisa do ID real) ou `send_flow` se o intuito era roteamento genérico; nunca adivinhar o ID. A ação em si não é proibida. Ver Regra 2. |
| Ordem `send_flow` antes de `set_field_value` | Reordenar: campos PRIMEIRO, `send_flow` por último (senão campos chegam vazios). Ver Regra 16. |
| `>1` botão `web_url` / CTA >20 chars / botão de carrinho pra produto | Ver Regra 17. `postback` é PERMITIDO (até 3, raro); 1 só botão `web_url` por mensagem (limite WhatsApp). |
| Data fixa que apodrece ("28/02", "até hoje") / preço literal em exemplo com tool | Ver Regra 18 (datas e preço literal). |

### 4. Versionamento do arquivo corrigido

Use o esquema do meta-prompt do usuário:

- Se o nome original era `prompt-atendimento-v1.0.md` → corrigida
  `prompt-atendimento-v1.1.md` (correções estruturais leves).
- Se não havia versionamento no nome → adicione `-corrigido` no nome.

Salve em `/mnt/user-data/outputs/`.

### 5. Gera o relatório

Use `assets/relatorio_template.md` como base e preencha os placeholders.
Salve em `/mnt/user-data/outputs/relatorio-<nome>.md`.

O relatório precisa, no mínimo:

- Resumir quantas correções foram feitas e quantas pendências sobraram.
- Listar cada correção com **antes/depois** e justificativa em uma frase.
- Listar cada pendência com **localização**, **o que falta**, e
  **sugestão** do que fazer.
- Trazer a tabela de estatísticas (vem direto do `summary` do findings).
- Confirmar explicitamente que persona, fluxos, base de conhecimento e
  regras de negócio foram preservados.

### 6. Apresenta os arquivos

Use `present_files` com o `.md` corrigido **primeiro** e o relatório em
seguida. Na resposta, escreva uma síntese curta (3–5 linhas) do que mudou
no nível mais alto, citando os números do summary. Não repita o relatório
no chat — o arquivo já cobre.

## Edge cases que merecem atenção

**Prompt parcial / fragmento.** Se o usuário enviou só uma parte (ex.: só
um bloco JSON), corrija o que foi enviado, mas avise no relatório que a
auditoria não cobre as seções obrigatórias (porque não há prompt inteiro).

**Meta-prompt em vez de agent prompt.** Às vezes o usuário envia o
**meta-prompt** (o que gera prompts de agente) em vez do prompt do agente
em si. Esses arquivos *contêm intencionalmente* exemplos negativos e
discussões sobre as regras — o analisador tenta detectar via marcadores
(`❌`, `🚫`, "proibido"), mas pode haver falsos positivos. Se o conteúdo
parecer ser um meta-prompt (ex.: tem seções como "Modo Auditor", "Hierarquia
de Verdade", "Inputs Obrigatórios"), pergunte ao usuário se ele quer mesmo
corrigir esse arquivo ou se enviou o errado.

**Conflito entre violações.** Quando duas violações apontam para correções
opostas (ex.: tem botão sem URL dentro de um carrossel com 1 item só), não
tente resolver as duas ao mesmo tempo — vira pendência composta com
descrição clara das opções.

**Diff muito grande.** Se o número de correções passar de ~15, alerte o
usuário no resumo: o prompt provavelmente precisa ser refeito do zero, não
remendado.

**Prompt inchado (>30 KB).** Sempre meça `wc -c` no início e reporte no
relatório. Prompts NexTags ideais ficam em 15-20 KB. Acima de 30 KB,
**sugira redução** com base nas estratégias da Regra 13
(`references/regras_absolutas.md`): remover changelog/histórico de versões,
remover pendências internas, consolidar fluxos similares (Troca/Devolução/
Defeito/Cancelamento), converter prosa em tabela, cortar exemplos negativos
redundantes, cortar regras duplicadas. Acima de 45 KB, recomendar reescrita
do zero. NÃO faça redução automática sem confirmação humana — alta chance
de cortar algo que o dono considera essencial.

## Estrutura desta skill

```
nextags-prompt-fixer/
├── SKILL.md                              (este arquivo)
├── scripts/
│   └── analyze_prompt.py                 análise determinística
├── references/
│   └── regras_absolutas.md               regras + padrões de fix
└── assets/
    └── relatorio_template.md             template do relatório
```

# Regras Absolutas NexTags & Padrões de Correção

> Esta referência documenta cada violação que o `analyze_prompt.py` detecta e
> a estratégia de correção apropriada. Use ao consolidar as correções no
> prompt final.

---

## Princípio orientador

**Preservar a função do agente, corrigir só a forma.**

A persona, fluxos, base de conhecimento e regras de negócio são intocáveis.
Você só altera o que viola uma Regra Absoluta da plataforma. Quando uma
correção exigir decisão de produto (qual `flow_id` usar, por exemplo),
**deixe placeholder explícito** e marque como pendente no relatório, em vez
de inventar valor.

---

## 1. JSON inválido (sintaxe)

**Detecção:** o parser do Python falhou ao ler o bloco JSON.

**Como corrigir:**
1. Leia o erro reportado (`syntax_error` no findings) — geralmente é vírgula
   sobrando, aspa não-fechada, chave duplicada ou aspas curvas (`"` em vez de `"`).
2. Reescreva o bloco com sintaxe válida, **mantendo a intenção original**:
   mesmas mensagens, mesmas ações, mesmas tags.
3. Se o conteúdo da mensagem for ambíguo (ex.: um campo cortado no meio),
   **não chute** — marque como pendente e peça revisão humana.

**Antes:**
```json
{"messages":[{"message":{"text":"Olá!",}}]}
```

**Depois:**
```json
{"messages":[{"message":{"text":"Olá!"}}]}
```

---

## 2. Ações de transferência: send_flow é o padrão recomendado (as outras não são proibidas)

> **Camadas em relação à skill `nextags-json-fixer`.**
> A `nextags-json-fixer` (`references/schema.md`, linhas 123-126) afirma que
> as 8 ações — incluindo `transfer_conversation_to`, `assign_conversation`,
> `unassign_conversation` — são "válidas conforme a documentação oficial".
> Isso está correto: o validador de RUNTIME não quebra o JSON se essas ações
> aparecerem. Esta skill atua no PROMPT (o que o agente deve *escrever*), mas
> também NÃO bloqueia essas ações — apenas recomenda `send_flow` por padrão:
>
> | Camada | Skill | Veredito sobre transfer_conversation_to/assign/unassign |
> |---|---|---|
> | JSON aceito pela plataforma (runtime) | json-fixer | Sintaticamente VÁLIDAS — não remover de output já em produção |
> | Prompt que se escreve (boa prática) | **prompt-fixer (esta)** | `send_flow` é o padrão recomendado; as outras são fallback/caso especial — não proibidas |
>
> **Evidência (25 prompts em produção):** 100% das transferências de
> QUALIDADE são via `send_flow` com `flow_id` real, e é por isso que
> `send_flow` é o **padrão recomendado**. Mas `transfer_conversation_to` e
> `assign_conversation` continuam **válidas** e têm usos legítimos (abaixo).
> Não as remover nem tratar como erro bloqueante.

Padrão recomendado: **`send_flow`** apontando ao fluxo de transferência do
projeto. As demais ações de transferência **não são proibidas**:

- **`transfer_conversation_to`** — PERMITIDA como **fallback** quando NÃO há
  fluxo de transferência configurado no projeto. É a rede de segurança: se
  não existe `flow_id` de transferência, usar essa ação é correto. Quando
  houver fluxo, prefira `send_flow`, mas não bloqueie.
- **`assign_conversation`** — caso especial **raro e válido**: atribuir a
  conversa a um atendente específico (admin). Uso definido pelo humano dono
  do projeto. Não é o padrão e não se sugere por default, mas é legítima
  quando aparece com `admin_id` válido.
- **`unassign_conversation`** — válida; remove a atribuição. Não é o caminho
  comum de transferência, mas não é erro.

**Validação extra de `admin_id` (quando aparecer `assign_conversation`):**
se o valor de `admin_id` não for um ID numérico/hash válido — ex.: um nome
como `"Estela."` (caso real, Gabriela) — aí sim há problema: o `admin_id`
está inválido. Trate o `admin_id` malformado como pendência (precisa do ID
real do admin) ou converta pra `send_flow` se o intuito era roteamento
genérico; nunca tentar adivinhar o ID do admin.

**Como corrigir / quando agir:**
- Se um prompt usa `transfer_conversation_to` e existe um `flow_id` de
  transferência no projeto → **sugira** (não obrigue) migrar pra `send_flow`.
- Se NÃO há fluxo de transferência → `transfer_conversation_to` é válida;
  deixar como está.
- `assign_conversation` com `admin_id` válido → preservar.
- Só converta para `send_flow` quando for o padrão recomendado E houver
  fluxo disponível:

**Antes:**
```json
{"messages":[{"message":{"text":"Vou te transferir."}}],
 "actions":[{"action":"transfer_conversation_to","value":"human"}]}
```

**Depois:**
```json
{"messages":[{"message":{"text":"Vou te transferir."}}],
 "actions":[{"action":"send_flow","flow_id":"<ID_DO_FLUXO_DE_TRANSFERENCIA>"}]}
```

⚠️ Se o `flow_id` correto não estiver definido no prompt, **mantenha o
placeholder** `<ID_DO_FLUXO_DE_TRANSFERENCIA>` e adicione no relatório:
"⚠️ Definir o ID do fluxo de transferência antes de subir em produção."

---

## 2b. Funções de transferência inventadas ou legadas (fora do schema)

**Regra:** qualquer "ação" cujo nome não esteja no conjunto oficial de 8
(`add_tag`, `remove_tag`, `set_field_value`, `unset_field_value`,
`send_flow`, `transfer_conversation_to`, `assign_conversation`,
`unassign_conversation`) é inválida. A plataforma não a reconhece — a
transferência simplesmente NÃO acontece, porque o nome da ação não existe
no schema (diferente de `send_flow`, que dispara normalmente).

**Evidência (6/25 prompts):** `connect_user_to_human` (Luna),
`transferir_atendimento` (Dani), `transferir_suporte` (Ayla),
`buscar_pedido` (Dani), e funções de plataforma legada com sintaxe `()` /
`{{}}` como `Rotativo()`, `Rastreio_Shp()`, `{{NumeroPedidoShopify}}`
(Clara-SAC). São MAIS comuns que as ações proibidas oficiais.

**Detecção:** em `actions`, qualquer `"action"` fora das 8 oficiais. Em
prosa, verbos de função tipo `transferir_*`, `connect_*`, `*_atendimento`,
ou chamadas com parênteses `Nome()`.

**Como corrigir:**
- Transferência (`connect_user_to_human`, `transferir_suporte/atendimento`)
  → `send_flow` + `<ID_DO_FLUXO_DE_TRANSFERENCIA>` (placeholder se o ID não
  está no prompt). Uma `messages` de transição é opcional por UX (ver
  Regra 10) — o `send_flow` dispara com ou sem ela.
- Função de dado legada (`buscar_pedido`, `Rotativo()`) → marcar PENDÊNCIA:
  precisa virar tool/MCP real; não é ação de JSON. Não inventar substituto.

**Princípio:** a técnica de "transferência disfarçada" (não dizer ao cliente
que vai transferir — ver Karol/Nalu/Ju) é BOA e deve ser preservada no texto;
só o MECANISMO (a ação) é que está errado.

---

## 3. Botão `web_url` sem `url` (link sem destino)

**Regra:** um botão de LINK (`type: "web_url"`) precisa de uma `url` válida.
Botão `web_url` sem `url` é inválido. (Botões `postback`, que disparam um
fluxo ao clicar, são PERMITIDOS — ver Regra 17 — e não exigem `url`.)

**Detecção do script:** bloco com `template_type: "button"` que tem botão
`type: "web_url"` sem `url`.

**Como corrigir:**
- Botão `web_url` sem `url` → marque como pendente (precisa que alguém
  forneça a URL do link).
- Botão `postback` → **válido, preservar** (dispara fluxo ao clicar).
- Para confirmações simples (sim/não), texto livre costuma ser melhor que
  botão — mas é **recomendação de UX**, não obrigação. Se preferir converter
  um menu de confirmação em texto, faça a pergunta na própria mensagem e
  aguarde resposta livre do cliente.

**Antes (botão `web_url` sem `url` — ERRADO):**
```json
{"messages":[{"message":{"attachment":{"payload":{"buttons":[
  {"title":"Ver produto","type":"web_url"}
],"template_type":"button","text":"Confira:"},"type":"template"}}}]}
```

**Depois (com a `url`, ou texto simples se não houver link):**
```json
{"messages":[{"message":{"text":"Quer prosseguir? É só me responder com sim ou não."}}]}
```

---

## 17. Limites de UI do template button

`postback` é **PERMITIDO**. A regra real de limite é por TIPO de botão:

- **Botão de LINK (`web_url`): no máximo 1 por mensagem** (restrição do
  WhatsApp para link — Uni, Hidratei, Bela).
- **Botões `postback`** (disparam um fluxo ao clicar): **permitidos, até 3
  por mensagem**, mas a IA **raramente** usa (o padrão é texto + `send_flow`,
  ou 1 botão `web_url`). Não bloquear quando aparecer.
- **CTA ≤ 20 caracteres** ("Comprar Agora", "Finalizar Pedido", "Quero o meu").
- **Campo `text` no payload é OBRIGATÓRIO** (descrição/preço). Sem `text` =
  card inválido.
- **Botão de carrinho aponta pro CHECKOUT, nunca pra URL de produto**
  (Duda-vendas: "no carrinho, botão sempre pro checkout").
- **Fechamento com 3 chaves `}}}`** no bloco de botão é o erro de sintaxe
  mais comum (Duda-vendas: "dois `}}` = JSON inválido").

**Como corrigir:** se houver >1 botão `web_url` → manter o primeiro, virar
texto o resto. Se houver >3 botões `postback` → manter 3, virar texto o resto.
Se faltar `text` → pendência (precisa da descrição). Se CTA >20 chars →
encurtar mantendo sentido. `postback` **não é violação** — preservar.

---

## 4. Carrossel com menos de 2 itens

**Regra:** carrosséis (`template_type: "generic"`) servem para listar 2+
produtos com imagem. Para 1 item, use texto + attachment de imagem.

**Como corrigir:** transforme em uma sequência de mensagens com texto e a
imagem como attachment.

**Antes:**
```json
{"messages":[{"message":{"attachment":{"payload":{"elements":[
  {"title":"Produto X","subtitle":"Descrição","image_url":"https://...","buttons":[]}
],"template_type":"generic","image_aspect_ratio":"horizontal"},"type":"template"}}}]}
```

**Depois:**
```json
{"messages":[
  {"message":{"text":"Produto X — Descrição"}},
  {"message":{"attachment":{"payload":{"url":"https://..."},"type":"image"}}}
]}
```

---

## 5. Markdown dentro do JSON

**Regra:** WA-markup OK; markdown-padrão vaza. A marcação estilo WhatsApp
— `*negrito*` (asterisco único), `_itálico_`, `~tachado~` — **RENDERIZA**
na plataforma (o cliente TESTOU) e é **PERMITIDA** nos campos `text`,
`subtitle` ou `title`. Só o **markdown-padrão VAZA literal e é proibido**:
`**negrito duplo**`, `# título`, link `[texto](url)`, bullets `- item`, e
cercas de código `` ``` ``. Esse markdown-padrão aparece cru pro cliente.

**Como corrigir:** retire SOMENTE o markdown-padrão (asterisco-duplo,
hashtag-título, `[texto](url)`, bullets com hífen, cercas de código).
**NÃO mexa** em `*negrito*`, `_itálico_` ou `~tachado~` — eles são válidos.
Ao reescrever um trecho com markdown-padrão, prefira a frase crua ou
converta para a marcação WhatsApp equivalente (ex.: `**x**` → `*x*`).

**Antes (markdown-padrão — VAZA):**
```json
{"messages":[{"message":{"text":"O prazo é **3 a 5 dias úteis**."}}]}
```

**Depois (WA-markup OK ou texto cru):**
```json
{"messages":[{"message":{"text":"O prazo é *3 a 5 dias úteis*."}}]}
```

---

## 6. Menções a ações de transferência em prosa

`transfer_conversation_to` e `assign_conversation` **não são proibidas**
(ver Regra 2 — são fallback / caso especial válido). Uma menção em prosa
como "use a ação `transfer_conversation_to` quando…" **não é violação por si
só**. Só vale a pena olhar quando o projeto JÁ tem um fluxo de transferência
configurado e o padrão recomendado (`send_flow`) seria melhor.

**Exceção:** se a menção está em uma seção explicitamente marcada como
"❌ NÃO FAZER" / "PROIBIDO" / "Errado", o autor está ensinando o que evitar.
O analisador já tenta detectar isso (procura marcadores como `❌`, `🚫`,
`proibido`, `nunca usar` nas linhas anteriores).

**Como corrigir:** quando o analisador apontar uma menção em prosa, leia o
contexto. Se houver fluxo de transferência disponível, **sugira** (não
obrigue) trocar a referência por `send_flow` com o ID apropriado. Se não
houver fluxo, a menção a `transfer_conversation_to` como fallback é
legítima — não mexer.

---

## 7. Seções obrigatórias faltando

Um prompt NexTags precisa instruir explicitamente o agente sobre:

| Chave | Por quê |
|---|---|
| `anti_alucinacao` | Sem essa instrução, o modelo vai inventar dados. |
| `nao_revelar_ia` | Cliente não pode saber que é bot — quebra a experiência. |
| `json_obrigatorio` | A plataforma só processa JSON. Texto solto trava o fluxo. |
| `send_flow_transferencia` | Sem isso, o modelo tenta usar ações proibidas. |
| `texto_padrao` | Sem isso, o modelo abusa de botões/carrossel. |
| `fora_de_escopo` | Sem isso, o agente sai do contexto da empresa. |

**Como corrigir:** **não invente** o conteúdo da seção sem confirmar com
quem está usando a skill. Em vez disso:
1. Adicione um placeholder claramente marcado, ex.:

   ```
   ## ⚠️ Seção pendente: Regras anti-alucinação

   <!-- Adicionado automaticamente pelo nextags-prompt-fixer.
        Preencha com as regras anti-alucinação antes de subir em produção. -->

   - Nunca inventar informações que não estejam na base de conhecimento.
   - Nunca assumir dados não confirmados.
   - Quando faltar informação, informar honestamente e disparar fluxo de
     transferência via send_flow.
   ```

2. Liste cada seção pendente no relatório, na seção "Pendências para
   revisão humana".

O objetivo é não deixar o prompt rodar sem essas instruções (risco
operacional alto), mas também não inventar regras de negócio que só o
humano dono do projeto sabe.

---

## 8. Quando NÃO corrigir

Há situações em que a skill deve **flagar e parar** em vez de auto-corrigir:

- Bloco JSON muito complexo cuja intenção não está clara após o erro.
- Conflito entre duas violações que exigem decisões opostas (ex.: tem
  carrossel com 1 item, mas o item tem botão sem URL — qual estratégia
  vence?).
- Texto que parece ser parte da persona/fluxo mas viola alguma regra (pode
  ser intencional pelo autor).
- Casos onde a correção mudaria o comportamento do agente, não só a forma.

Nesses casos: **inclua no relatório com explicação** e deixe a parte
problemática inalterada.

---

## 10. `send_flow` sem `messages` (DISPARA NORMALMENTE — `messages` é opcional)

**Regra:** `send_flow` sem `messages` **DISPARA NORMALMENTE**. O fluxo assume
a comunicação com o cliente — é ele quem fala a partir do handoff. NÃO é
falha silenciosa, NÃO é violação: é comportamento **padrão e válido**.

- `set_field_value` **roda** ✅
- Tags **rodam** ✅
- `send_flow` **dispara** ✅ (mesmo sem `messages`)

O campo `messages` junto de `send_flow` é uma **transição OPCIONAL** — uma
frase curta por UX ("Já vou te conectar com nosso time!"), nunca uma
exigência técnica. Adicionar `messages` é uma escolha de experiência, não
uma correção obrigatória. O que antes era tratado como "exceção
whitelistada" (NPS, descadastro, mockup) é, na verdade, o comportamento
normal de qualquer disparo de fluxo.

**Detecção:** o `analyze_prompt.py` pode reportar
`send_flow_without_messages_count`. Trate isso como **informativo**, não
como erro: o disparo funciona com ou sem `messages`.

**Como corrigir:** em geral, **NÃO há o que corrigir** — `send_flow` sem
`messages` é válido. Só **sugira** (nunca force) uma transição curta quando
houver ganho de UX: o cliente está esperando uma resposta e uma linha breve
antes do handoff melhora a experiência. Mesmo assim:

1. A transição é **opcional**. Se o autor deixou `send_flow` sozinho de
   propósito (o fluxo fala), **preserve** como está.
2. Se for sugerir uma transição por UX, mantenha-a curta e "meta" (só anuncia
   a passagem, não conversa sobre o problema):

   **Sem transição (válido — o fluxo fala):**
   ```json
   {
     "actions": [
       {"action":"set_field_value","field_name":"resumo","value":"..."},
       {"action":"send_flow","flow_id":"123"}
     ]
   }
   ```

   **Com transição opcional por UX (também válido):**
   ```json
   {
     "messages": [
       {"message":{"text":"Já vou te conectar com nosso time!"}}
     ],
     "actions": [
       {"action":"set_field_value","field_name":"resumo","value":"..."},
       {"action":"send_flow","flow_id":"123"}
     ]
   }
   ```

### Casos em que a ausência de `messages` é claramente intencional

Disparos só-`actions` (com `messages:[]` ou omitido) são comuns e corretos.
Exemplos reais onde adicionar mensagem PIORARIA a experiência (não tocar):

| Caso | Evidência | Por quê não tem messages |
|---|---|---|
| NPS pós-encerramento | Duda-SAC, Let (flow `1775096402729`) | O fluxo NPS já comunica; mensagem do agente causaria despedida duplicada |
| Descadastro confirmado | Bia (passo 2) | Já confirmou no passo 1; passo 2 só executa |
| Mockup/coleta de mídia | Uni (`"messages":[]`, flow `1780170720912`) | O fluxo coleta o upload; o LLM não gerencia imagem |

Verbatim (Let): *"NPS — disparo silencioso pós-encerramento, somente actions
sem messages."* Verbatim (Duda-SAC): *"Nunca envie uma mensagem de despedida
antes do NPS."*

**Princípio:** `send_flow` sempre dispara. `messages` só entra quando uma
linha de transição agrega à experiência do cliente — e mesmo aí é sugestão,
não obrigação. Na dúvida, preserve o disparo silencioso.

---

## 16. Ordem das actions e qualidade do handoff (preservar, não achatar)

**Regra de ORDEM (load-bearing — não reordenar ao "limpar" o JSON):**
quando há `set_field_value` + `send_flow` no mesmo array, o(s)
`set_field_value` vêm SEMPRE ANTES do `send_flow`. O fluxo lê os campos no
momento em que executa; se `send_flow` vier antes, os campos chegam vazios.

Verbatim (Uni): *"O fluxo lê os campos no momento em que executa — se
send_flow vier antes, os campos chegam vazios."*
Verbatim (Flora): ordem fixa exigida — (a) mensagem ao cliente, (b)
`set_field_value` com `assunto_ticket`, (c) `send_flow`.

**Handoff com contexto (preservar se já existir; não inventar se não):**
prompts-ouro gravam um briefing pro humano via `set_field_value` ANTES de
transferir (Flora: `assunto_ticket`; Nex: `nex_resumo`). Se o prompt já faz
isso, NUNCA remover — é padrão-ouro. Se não faz, NÃO inventar conteúdo de
campo (vira pendência opcional, não correção).

**Silêncio total pós-handoff (preservar):** ~13/25 instruem o agente a não
responder nada após o `send_flow` de transferência ("mesmo que a cliente
responda 'ok' ou 'obrigada'"). Isso NÃO é violação — é intencional. Não
"completar" essas respostas.

**Pipeline monotônico (preservar):** campos de estágio (`stage_pipeline`,
`nex_pipeline`) só avançam, nunca regridem; resumo é acumulativo. Não
normalizar/resetar.

---

## 15. Seções de meta-documentação dentro do prompt

**Regra:** o prompt do agente NUNCA pode conter seções de meta-documentação (auditoria, changelog, pendências internas, TODOs, notas técnicas pra dev, justificativas de decisões passadas, métricas). Tudo isso vai pro **relatório de auditoria**, não pro prompt.

**Por quê:** o prompt é lido pelo LLM A CADA TURNO em runtime. Cada parágrafo que o LLM lê:
- Consome janela de contexto (compartilhada com histórico + tool returns)
- Dilui a atenção do modelo entre o que importa (regras de atendimento) e o que não importa (versões antigas)
- Aumenta custo por turno
- Pode confundir o LLM ("a regra atual é v2.4 ou v2.5?")

Meta-documentação serve só pro humano. Não tem nenhum ganho operacional incluí-la no prompt.

**Padrões a detectar (case-insensitive, em cabeçalhos `#`, `##`, `###`):**

| Padrão | Exemplos |
|---|---|
| `audit(oria)?` | "Auditoria", "Auditoria — Correções v1.0 → v2.0" |
| `changelog` | "Changelog v2.0" |
| `hist[óo]rico\s+de\s+vers[ãa]o` | "Histórico de versões" |
| `vers[ãa]o\s+(anterior|antiga)` | "Versão anterior" |
| `corre[çc][ãa]o(es)?\s+(da|de\s+vers|aplicada)` | "Correções da v2.0", "Correções aplicadas" |
| `pend[êe]ncia(s)?(\s+(interna|humana|pra\s+confirmar))?` | "Pendências internas", "Pendências a confirmar" |
| `\ba\s+confirmar\b` | "A confirmar" |
| `\btodo(s)?\b` (cabeçalho) | "TODO", "TODOs" |
| `notas?\s+(internas?|pra\s+dev|t[ée]cnicas?)` | "Notas internas", "Notas técnicas" |
| `bug(s)?\s+(observad|conhecid)` | "Bugs observados" |
| `m[ée]tric(a|as)\s+do\s+prompt` | "Métricas do prompt" |
| Cabeçalho versionado `v\d+\.\d+\b` | "## v2.5 (correções)" — quando é cabeçalho |

**Heurística adicional:** se um cabeçalho contém "v1.0", "v2.0", "v2.5" e está acompanhado de tabela com "antes/depois" ou "problema/correção", é changelog.

**Cabeçalho do prompt:** uma linha curta tipo `# PROMPT — AGENTE X` está OK. O que NÃO está OK é metadado expandido: `**Versão:** v3.0 | **Data:** Maio/2026 | **Responsável:** Dev X`. Esse metadado vira ruído pro LLM.

**Como corrigir:**

1. Identificar todas as seções que batem nos padrões acima.
2. **Removê-las inteiras** do prompt.
3. **Migrar o conteúdo pro relatório** (`relatorio-<nome>.md`) na seção apropriada:
   - Auditoria/changelog → seção "Histórico de mudanças" do relatório
   - Pendências → seção "Pendências para revisão humana" do relatório
   - Notas técnicas → seção "Notas técnicas / TODO" do relatório
4. **Manter intacto** o que é regra operacional ativa (regras absolutas, fluxos, base de conhecimento, tools).

**Exemplo prático:**

```
# PROMPT — MAYA (WAZZU)
**Versão:** v3.0 enxuta | **Data:** Maio/2026 | **Responsável:** Marcella

## 15. AUDITORIA — CORREÇÕES v1.0 → v2.0 → v2.5
...

## 16. PENDÊNCIAS / A CONFIRMAR
- Pipeline silencioso para produto esgotado: criar flow_id
- Renomear tools com sufixo `1`
```

Vira:

```
# PROMPT — MAYA (WAZZU)
```

(E todo o conteúdo de auditoria/pendência vai pro relatório separado.)

**Princípio:** se o LLM em runtime não precisa daquela informação pra atender uma cliente, ela NÃO pertence ao prompt.

---

## 14. Placeholders genéricos em vez de CUFs nativos

**Regra:** prompts NexTags NUNCA devem usar placeholders genéricos como `[nome]`, `[cliente]`, `[email]`, `[primeiro nome]`, `[telefone]`, `{nome_do_cliente}`, `$first_name$`, `<NOME>`, etc. nos exemplos do prompt. A plataforma NexTags tem um conjunto rico de **Custom User Fields (CUFs)** nativos que são interpolados em runtime — `{{first_name}}`, `{{email}}`, `{{order_id}}`, etc.

**Why:** a plataforma NÃO interpola nada que não seja `{{cuf_real}}`. Qualquer placeholder com colchetes `[ ]`, chaves simples `{ }`, ou cifrões `$ $` aparece literalmente pra cliente — quebrando totalmente a personalização.

**Detecção manual:** procurar por padrões `\[\w+\]`, `\{[a-z_]+\}` (chave única, não dupla), `\$\w+\$`, `<[A-Z_]+>` dentro de campos `text` de exemplos JSON no prompt. Se encontrar, é violação.

**Estratégia de correção:**

1. Identificar o equivalente em `references/cufs_nextags.md` (cobertura completa: contatos, Instagram, Messenger, e-commerce, pedidos).
2. Substituir `[nome]` → `{{first_name}}`, `[email]` → `{{email}}`, `[order_id]` → `{{order_id}}`, etc.
3. Se NÃO existir CUF equivalente (ex: o prompt usa `[código de produto interno]` que não bate com nenhum CUF), **reformule** a frase pra não precisar de interpolação OU marque como pendência humana (talvez precise criar um Custom Field na conta).

**Quando `[nome]`/nome-literal NÃO é violação (não corrigir):**
~17/25 prompts não usam `{{first_name}}` — e muitos estão CERTOS. Distinguir:

- **É violação** (corrigir → CUF): colchete `[nome]`/`[email]` ou chave
  simples `{nome}`/`{first_name}` DENTRO de um campo `text` num ponto em que
  o agente *quer* interpolar o dado real do cliente. Ex.: Nex `[Nome]`,
  Flora `{first_name}` → `{{first_name}}`.
- **NÃO é violação** (preservar): a marca trata o cliente por apelido fixo
  ("hidratada" — Hidratei; "goxxxtosa" — Bia; "Beleza" — Bela) ou por "você",
  por identidade de marca. Aqui a ausência de CUF é coerente; forçar
  `{{first_name}}` descaracteriza a persona.
- **Cuidado com `{{first\_name}}`** (underscore escapado, caso Ayla): o
  escape `\_` QUEBRA a interpolação. Corrigir para `{{first_name}}`.
- **NÃO normalizar cegamente** quando 3 convenções coexistem por design
  (`{{}}` runtime, `<placeholder>` "preencher manualmente", `[x]` exemplo
  didático). Olhar o contexto antes de trocar.

4. **Considere fallback:** se substituiu por `{{first_name}}` numa saudação, ofereça variante neutra "sem nome" no caso de cliente sem cadastro:

```
Abertura com nome: {"messages":[{"message":{"text":"Oi, {{first_name}}! Tudo bem?"}}]}
Abertura sem nome: {"messages":[{"message":{"text":"Oi! Tudo bem? Como posso te ajudar?"}}]}
```

**Princípio:** use CUFs SOMENTE quando necessário. Não force `{{first_name}}` em toda mensagem — saudação e momentos-chave bastam.

---

## 13. Prompt inchado (tamanho excessivo)

**Regra:** prompts NexTags ideais ficam entre **15-20 KB**. Acima disso, há quase sempre redundância eliminável. Acima de **30 KB**, considerar revisão agressiva. Acima de **45 KB**, sinal vermelho.

**Por quê:** prompts inchados:
- Desperdiçam context window (compartilhado com histórico + tool returns)
- Aumentam custo por turno
- **Pioram aderência do LLM às regras** — atenção dilui em conteúdo repetido
- Aumentam latência de resposta

**Detecção (manual, não automatizada):**
- `wc -c` no arquivo. >30 KB = revisar.
- Conferir se a mesma regra aparece em múltiplos lugares (ex: "sem markdown" em Regras Absolutas + Regras de Formato + Regras Críticas).
- Conferir se há seções de histórico/changelog/auditoria de versões (v1.0 → v2.0...). Essas NÃO servem ao LLM.
- Conferir se há "pendências internas" / TODOs / notas pro dev — tudo isso deve sair.

**Estratégia de redução (em ordem de impacto):**

1. **Remover seções de auditoria/changelog/histórico de versões.** ~10-15% do peso típico.
2. **Remover "Pendências" / "A confirmar" / notas internas.** Não ajudam o LLM em runtime.
3. **Consolidar fluxos similares.** Troca/Devolução/Defeito/Cancelamento que compartilham 90% da estrutura → UMA seção com tabela de variações. ~15-20% do peso.
4. **Converter prosa em tabela** pra listas de gatilhos, tools, tratamento de erros. ~10% do peso.
5. **Cortar exemplos negativos redundantes.** Manter 2-3 por regra, não 6-8.
6. **Cortar regras duplicadas.** Cada regra é dita UMA vez no lugar mais lógico.
7. **Cortar tools/fluxos/regras herdadas que não se aplicam.** Ex: agente de vendas não precisa de detalhes de política de troca se transfere pra outro agente.
8. **Eliminar palavras de preenchimento** ("obrigatoriamente", "absolutamente", "completamente" repetidos).
9. **Reduzir testes de 8-10 → 4-6 essenciais.**

**Como aplicar (no fluxo do fixer):**

- Medir tamanho atual e reportar no relatório.
- Se >30 KB: sugerir reescrita enxuta como pendência. NÃO refazer automaticamente sem confirmação humana — alta chance de cortar algo que o dono do prompt considera essencial.
- Se >45 KB: marcar como "Diff muito grande — sugerir reescrita do zero" no relatório (já mencionado em "Edge cases" do SKILL.md).

**Princípio:** se uma seção pode ser removida sem mudar o comportamento esperado em runtime, ela DEVE ser removida.

---

## 12. Bloco oficial NexTags ausente

**Regra:** todo prompt de IA da plataforma NexTags Messenger Messaging Platform DEVE conter o bloco oficial de instruções de saída JSON. É um padrão da plataforma, copiado literal.

**Texto canônico do bloco (procurar por estas frases-âncora):**

```
Você é uma IA que deve sempre retornar respostas em JSON válido seguindo o padrão da Messenger Messaging Platform.

Regras:
1 - O JSON deve conter um array "messages" ou um array "actions" (ou ambos).
2 - "messages" é um array de objetos. Cada objeto deve conter um objeto "message".
3 - O objeto "message" deve seguir o schema de mensagens da Messenger Messaging Platform.
4 - Tipos de mensagem suportados:
   - Texto ("text")
   - Texto com botões
   - Imagens
   - Vídeos
   - Carrossel (templates do tipo "generic")
   - Arquivos
5 - Sempre retorne somente JSON válido. Não retornar explicações, comentários, markdown ou qualquer texto fora do JSON.
```

**Detecção:** procurar literalmente pela frase `"deve sempre retornar respostas em JSON válido seguindo o padrão da Messenger Messaging Platform"` (sem acentos opcionais, case-insensitive). Se ausente, é violação.

**Quando aplicar — verificar PRIMEIRO se o prompt usa JSON.** Este bloco só é
exigido em prompts cujo agente PRODUZ JSON — que têm `messages`/`actions`, exemplos
de saída JSON, `send_flow`, `set_field_value` ou tags (o `analyze_prompt.py` expõe
isso em `prompt_uses_actions` e na detecção de blocos JSON). Agente puramente
conversacional, sem nenhuma ação → dispensável (mas, se for agir, deveria ter).

**Como corrigir:**
1. **Nenhum bloco de formato de saída** → inserir o bloco LITERAL (sem parafrasear)
   como primeiro conteúdo de uma seção "FORMATO DE SAÍDA — JSON OBRIGATÓRIO".
2. **Já existe uma VARIANTE** (o prompt descreve o formato com texto próprio —
   "FORMATO DE SAÍDA (Nextags Messenger)", "⚙️ FORMATO OBRIGATÓRIO", etc.) →
   **NORMALIZAR para o bloco canônico, substituindo a variante**. "Renovar as
   instruções sem repetir": o prompt fica com **UMA** única instrução de formato (a
   canônica) — NUNCA o bloco canônico + a variante coexistindo (duplicação confunde o
   LLM e incha o prompt). As regras ESPECÍFICAS do projeto (tools, fluxos, exemplos,
   typing `4`, botões) ficam DEPOIS do bloco, não dentro dele nem no lugar dele.

**Por quê:** padronização. Toda IA NexTags que age responde com o mesmo contrato JSON.
Sem o bloco (ou com uma variante divergente), o agente pode confundir o esquema,
especialmente em primeiras chamadas (cache frio). Esse bloco é a especificação
canônica que o time NexTags fornece como referência oficial.

**Não parafrasear o bloco em si:** o texto canônico vai literal; só o conteúdo
ESPECÍFICO do projeto vem depois.

### ⚙️ OBRIGATÓRIO quando o agente tem TOOLS/MCP — esclarecer "function call ≠ saída JSON"

**Regra:** se o agente tem tools (MCP, function calling), **logo após** o bloco oficial DEVE vir uma cláusula esclarecendo que chamar ferramenta é um canal separado e NÃO viola o "só JSON". Sem isso, o modelo interpreta "retorne só JSON / nada fora do JSON" como **"proibido emitir function call"** e para de chamar as tools — fingindo, qualificando em loop ou fabricando dado.

**Texto a inserir (após o bloco oficial):**

> ⚙️ A regra "retorne só JSON" vale para a sua MENSAGEM ao cliente — NÃO impede você de chamar ferramentas. Chamar uma tool (function call) é um canal SEPARADO: você chama a função, recebe o resultado, e só então monta o JSON da mensagem. Function call nunca é "texto fora do JSON" e nunca viola o formato. Se você tem ferramentas e precisa de um dado (preço, produto, pedido), CHAME a função — é o esperado. Ferramentas são reais e chamáveis, não "conceito".

**Detecção:** prompt tem tools/MCP (menciona function/tool/MCP, ou `analyze_prompt.py` marca tool-uso) MAS não tem essa cláusula → flag e inserir.

**Why (caso real Veuske 2026-06-11):** o log de reasoning da OpenAI mostrou o agente concluindo *"the instruction 'Return only JSON' implies that I shouldn't call a tool function directly"* e *"tool might just be a mental model, not actual function calls"*. Resultado: 0 tool calls em 5 modelos diferentes. A causa-raiz tinha 2 camadas — (1) este texto do prompt suprimindo a chamada [corrigível aqui] e (2) possível `response_format: json_object` forçado na API NexTags [fora do prompt, lado da plataforma]. Esta cláusula resolve a camada 1. Ver [[no-hardcode-with-tools]] e quirk de tool-call suprimido.

---

## 11. Exemplos JSON envolvidos em fences markdown (`` ```json ``)

**Regra:** ao **gerar** um prompt (creator) ou **mostrar exemplos de saída** em qualquer seção do prompt, **NÃO envolva os exemplos JSON em fences de markdown** (`` ```json `` ... `` ``` ``).

**Why:** o LLM em runtime aprende muito mais pelo padrão dos exemplos do que pelas regras textuais. Se cada exemplo de saída esperada está envolvido em fences `` ```json ``, o modelo conclui "JSON sai assim" e copia os fences no output real — fazendo a plataforma tratar tudo como texto e vazar o JSON cru na conversa.

**Detecção manual:** ao revisar/auditar um prompt, conte quantos blocos JSON de exemplo estão dentro de fences `` ```json `` na seção "FORMATO DE RESPOSTA" ou "Exemplos". Se houver fences, isso é uma violação latente (não pega no `analyze_prompt.py` ainda, mas afeta o comportamento em runtime).

**Como corrigir:**

- Remover os `` ```json `` e `` ``` `` antes/depois dos blocos de exemplo.
- Usar separadores de prosa entre exemplos: `— Exemplo 1 — Categoria X:` em texto cru, seguido do JSON diretamente, sem fence.
- O auditor `analyze_prompt.py` continua reconhecendo o JSON pela estrutura (linhas começando com `{`), não precisa de fence pra detectar.

**Princípio geral:** examples > rules. Quando uma regra textual é repetidamente violada apesar de instruções claras, suspeite dos exemplos antes de adicionar mais regras.

---

## 16. Campo `type` dentro de `payload` (erro mais comum em attachments)

**Regra:** em qualquer `attachment`, o campo `type` fica **FORA** de
`payload`, no mesmo nível dele. A plataforma NexTags ignora o `type`
quando ele aparece dentro do `payload` — o middleware não consegue
descobrir que tipo de attachment processar e a mensagem falha.

**Detecção do script:** `analyze_prompt.py` reporta
`type_inside_payload_count` quando encontra `attachment.payload.type`
sem `attachment.type` correspondente.

**Antes (errado — `type` dentro do payload):**
```json
{"messages":[{"message":{"attachment":{"payload":{"type":"image","url":"https://..."}}}}]}
```

**Depois (correto — `type` ao lado do payload):**
```json
{"messages":[{"message":{"attachment":{"type":"image","payload":{"url":"https://..."}}}}]}
```

A mesma regra vale pra templates:
```
✅ {"attachment":{"type":"template","payload":{"template_type":"button",...}}}
❌ {"attachment":{"payload":{"type":"template","template_type":"button",...}}}
```

**Como corrigir:** mover o `type` pra fora do payload, sem alterar mais
nada. É uma transformação puramente estrutural.

---

## 17. Formato de imagem proibido (`.webp`, `.avif`, `.svg`, `.gif`)

**Regra:** a plataforma NexTags entrega imagens nos canais (WhatsApp,
Instagram, Messenger) e **só aceita JPEG e PNG**. Imagens em outros
formatos quebram a entrega em pelo menos um canal.

- ✅ Permitidos: `.jpg`, `.jpeg`, `.png` (Content-Type `image/jpeg` ou `image/png`).
- ❌ Proibidos: `.webp`, `.avif`, `.svg`, `.gif`, `.bmp`, `.tiff`, `.heic`, `.heif`.

**Detecção do script:** `analyze_prompt.py` reporta
`forbidden_image_formats_count` quando encontra URLs em
`payload.url` (attachment image) ou `image_url` (carrossel) com
extensão proibida, ambígua (sem extensão clara) ou não-absoluta.

**Cuidado com CDN.** Muitas CDNs servem `.jpg` na URL respondendo
`Content-Type: image/webp`. A URL parece OK, o canal rejeita. Quando
a extensão é ambígua (`.aspx`, `.php`, sem extensão), o prompt deve
instruir o agente a validar o Content-Type via tool MCP — ou,
preferencialmente, omitir a imagem.

**Como corrigir no prompt:**

1. Se o exemplo de JSON no prompt mostra URL `.webp`/`.avif`/`.svg`/`.gif`:
   substituir pelo placeholder `<URL_JPG_OU_PNG>` ou por uma URL válida.
2. Se o prompt menciona `image/webp` ou WebP como permitido:
   reescrever pra deixar claro que só JPEG/PNG é aceito.
3. Se o prompt usa imagens via tool MCP: incluir as 4 etapas de
   validação de imagem (URL absoluta → extensão → Content-Type → falha
   → omitir). O `prompt_skeleton.md` do creator tem o texto canônico.

**Princípio:** na dúvida sobre formato, REMOVER A IMAGEM. A ausência
da imagem é preferível a quebrar o envio inteiro no canal.

---

## 9. O que JAMAIS alterar

- Nome do agente, persona, tom de voz.
- Conteúdo da base de conhecimento (produtos, preços, políticas).
- Estrutura ou nomes dos fluxos.
- IDs de fluxos, tags, campos personalizados que já estiverem definidos.
- Regras de negócio específicas (ex.: "só ofereça desconto se cliente VIP").
- URLs e mídias já configuradas.
- Idioma, regionalismos, gírias da marca.
- O separador/typing indicator inteiro `4` solto dentro do array `messages`
  (inclusive quando aparece NO INÍCIO do array — pausa de abertura, padrão
  Uni). NÃO é lixo de JSON; é convenção da plataforma. Nunca remover.
- `flow_id`s reais de 13 dígitos (`17xxxxxxxxxxx`). 0/25 prompts de produção
  usam placeholder — todos têm ID real. Placeholder `<ID_DO_FLUXO>` é só
  estado INTERMEDIÁRIO do fixer; nunca substituir um ID real por placeholder.
- `"messages":[]` EXPLÍCITO (vazio intencional para disparo silencioso —
  padrão Uni). Não "preencher" nem remover a chave.
- A convenção de placeholder/tratamento do cliente escolhida pela marca
  ("hidratada", "você", "goxxxtosa", nome literal). Quando a marca não usa
  nome dinâmico de propósito, NÃO forçar `{{first_name}}`.
- Confirmação em 2 passos antes de ação destrutiva (descadastro, remoção —
  padrão Bia). Não colapsar em 1 passo.
- Regra anti-loop do prompt (não repetir mensagem >70% igual; não perguntar
  "posso ajudar em algo mais" em loop) — se já existir, PRESERVAR; é padrão-ouro.

Se uma correção exigiria tocar em qualquer uma dessas coisas, ela vira
**pendência humana** automaticamente.

---

## 18. Data/validade fixa hardcoded (conteúdo que apodrece)

**Regra:** nunca deixar data absoluta fixa em promoção/cupom/programa dentro do
texto do agente. Ela "apodrece" — vira mentira no dia seguinte.

**Evidência:** Luna-vendas "o programa de pontos encerra em 28/02" (já passou);
Gabi "válido só até hoje às 00:00" (sempre dirá "hoje").

**Detecção:** datas fixas (`\d{2}/\d{2}`, "até hoje", "válido até <data>") em
campos `text`, quando não vêm de tool.

**Como corrigir:** preço de SKU sempre via tool. Campanha/cupom pode ser hardcoded
SE a validade for relativa/dinâmica ou removida — nunca "28/02" nem "válido só até
hoje". Na dúvida → pendência (regra de negócio).

**Exceção — bloco "AVISOS ATIVOS":** o espaço reservado de avisos manuais
(promoções/feriados, ver `prompt_skeleton.md` §1.5) PODE conter datas — é conteúdo
OPERACIONAL editado à mão pelo dono do projeto. NÃO remova esse bloco nem suas
datas; só sinalize no relatório se houver aviso visivelmente VENCIDO (data já
passada), para o humano atualizar.

**Preço literal em exemplo JSON com tool de catálogo:** se o prompt tem tool de preço
mas os exemplos mostram um preço real (ex.: "R$ 129,90"), troque por placeholder
`R$ 0,00` — o LLM copia o exemplo como valor real. Preço sempre da tool.

---

## 19. Lints opcionais (avisar, não bloquear)

- Travessão / em-dash (`—`) em campos `text` — sinal de "cara de IA"; sugerir trocar
  por vírgula, ponto ou "e". Idem diminutivos forçados ("rapidinho", "horinha").
- Emoji 🤖 em mensagem — assume "sou bot"; sugerir remover.

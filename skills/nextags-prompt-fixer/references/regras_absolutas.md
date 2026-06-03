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

## 2. Ações de transferência: send_flow é o ÚNICO caminho correto

> **Resolução da contradição com a skill `nextags-json-fixer`.**
> A `nextags-json-fixer` (`references/schema.md`, linhas 123-126) afirma que
> as 8 ações — incluindo `transfer_conversation_to`, `assign_conversation`,
> `unassign_conversation` — são "válidas conforme a documentação oficial".
> Isso está CORRETO no nível dela: o validador de RUNTIME não quebra o JSON
> se essas ações aparecerem. Esta skill atua em camada diferente — o PROMPT,
> o que o agente deve *escrever*. As duas não se contradizem; são camadas
> distintas:
>
> | Camada | Skill | Veredito sobre transfer_conversation_to/assign/unassign |
> |---|---|---|
> | JSON aceito pela plataforma (runtime) | json-fixer | Sintaticamente VÁLIDAS — não remover de output já em produção |
> | Prompt que se escreve (boa prática) | **prompt-fixer (esta)** | DESENCORAJADAS — converter para `send_flow` |
>
> **Evidência decisiva (25 prompts em produção):** 0/25 usam
> `transfer_conversation_to` ou `unassign_conversation`. Apenas 2/25 usam
> `assign_conversation` (Gabriela, Ju) — e ambos foram flagados como desvio
> (`uses_forbidden_actions: true`). 100% das transferências de QUALIDADE são
> via `send_flow` com `flow_id` real. Logo: ao corrigir um PROMPT, sempre
> converter para `send_flow`; ao corrigir um JSON de runtime já entregue,
> a json-fixer pode mantê-las.

As ações abaixo **não devem ser ESCRITAS num prompt novo** — converter para
`send_flow` apontando ao fluxo de transferência do projeto:

- `transfer_conversation_to`
- `assign_conversation`
- `unassign_conversation`

**Validação extra de `admin_id` (quando aparecer `assign_conversation`):**
se o valor de `admin_id` não for um ID numérico/hash válido — ex.: um nome
como `"Estela."` (caso real, Gabriela) — é violação dupla. Converter a ação
inteira para `send_flow` + placeholder de `flow_id`; nunca tentar adivinhar
o ID do admin.

**Como corrigir:** substitua por `send_flow` apontando para o fluxo de
transferência configurado no projeto.

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
transferência simplesmente NÃO acontece (falha silenciosa, igual à Regra 10).

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
  está no prompt) + `messages` de transição (ver Regra 10).
- Função de dado legada (`buscar_pedido`, `Rotativo()`) → marcar PENDÊNCIA:
  precisa virar tool/MCP real; não é ação de JSON. Não inventar substituto.

**Princípio:** a técnica de "transferência disfarçada" (não dizer ao cliente
que vai transferir — ver Karol/Nalu/Ju) é BOA e deve ser preservada no texto;
só o MECANISMO (a ação) é que está errado.

---

## 3. Botões sem `web_url`

**Regra:** botões só existem para abrir links externos. Tudo mais (sim/não,
menus, confirmações) deve ser texto simples.

**Detecção do script:** bloco com `template_type: "button"` que tem botão
sem `type: "web_url"` ou sem `url`.

**Como corrigir:**
- Se o botão era para abrir um link externo mas faltou a URL → marque como
  pendente (precisa que alguém forneça a URL).
- Se o botão era pra qualquer outra coisa → **converta o JSON inteiro em
  texto simples**, fazendo a pergunta na própria mensagem e aguardando
  resposta livre do cliente.

**Antes (botão sendo usado como menu — ERRADO):**
```json
{"messages":[{"message":{"attachment":{"payload":{"buttons":[
  {"title":"Sim","type":"postback","payload":"YES"},
  {"title":"Não","type":"postback","payload":"NO"}
],"template_type":"button","text":"Quer prosseguir?"},"type":"template"}}}]}
```

**Depois (texto simples, deixando o cliente responder livre):**
```json
{"messages":[{"message":{"text":"Quer prosseguir? É só me responder com sim ou não."}}]}
```

---

## 17. Limites de UI do template button (web_url)

Todo template button em produção (7/7 dos que usam botão) segue:

- **Tipo `web_url` SEMPRE; NUNCA `postback`** (Duda-vendas, Bia explícitos).
- **Máximo 1 botão** por mensagem (Uni, Hidratei, Bela).
- **CTA ≤ 20 caracteres** ("Comprar Agora", "Finalizar Pedido", "Quero o meu").
- **Campo `text` no payload é OBRIGATÓRIO** (descrição/preço). Sem `text` =
  card inválido.
- **Botão de carrinho aponta pro CHECKOUT, nunca pra URL de produto**
  (Duda-vendas: "no carrinho, botão sempre pro checkout").
- **Fechamento com 3 chaves `}}}`** no bloco de botão é o erro de sintaxe
  mais comum (Duda-vendas: "dois `}}` = JSON inválido").

**Como corrigir:** se houver >1 botão → manter o primeiro, virar texto o
resto. Se faltar `text` → pendência (precisa da descrição). Se CTA >20 chars
→ encurtar mantendo sentido. `postback` → converter o JSON em texto simples
(Regra 3) OU `web_url` se houver URL.

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

**Regra:** mensagens são texto puro, como WhatsApp. Nada de `**negrito**`,
`# títulos`, `` `código` `` ou bullets `- item` dentro dos campos `text`,
`subtitle` ou `title`.

**Como corrigir:** retire o markdown e deixe o texto cru. Para ênfase,
prefira reescrever a frase ou usar pausas com mensagens separadas.

**Antes:**
```json
{"messages":[{"message":{"text":"O prazo é **3 a 5 dias úteis**."}}]}
```

**Depois:**
```json
{"messages":[{"message":{"text":"O prazo é de 3 a 5 dias úteis."}}]}
```

---

## 6. Ações proibidas mencionadas em prosa

Mesmo fora de blocos JSON, instruções como "use a ação
`transfer_conversation_to` quando…" são problema, porque podem induzir o
modelo a usá-la em runtime.

**Exceção:** se a menção está em uma seção explicitamente marcada como
"❌ NÃO FAZER" / "PROIBIDO" / "Errado", está tudo bem — o autor está
ensinando o que evitar. O analisador já tenta detectar isso (procura
marcadores como `❌`, `🚫`, `proibido`, `nunca usar` nas linhas anteriores).

**Como corrigir:** quando o analisador apontar uma menção em prosa, leia o
contexto. Se for instrução real, substitua a referência por `send_flow` com
o ID apropriado.

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

## 10. `send_flow` sem `messages` (a regra que NÃO está documentada)

**Regra:** todo JSON de saída que contém `send_flow` em `actions` **precisa** ter o campo `messages` com pelo menos 1 item. Sem `messages`, a plataforma NexTags falha silenciosamente:

- `set_field_value` **roda** ✅
- Tags **rodam** ✅
- `send_flow` **NÃO dispara** ❌

Isso significa que o agente parece estar funcionando (campos preenchidos, tags aplicadas), mas a conversa NUNCA é encaminhada pro fluxo. É a violação mais traiçoeira porque o erro é mudo.

**Detecção:** o `analyze_prompt.py` reporta `send_flow_without_messages_count` quando encontra um bloco JSON com `send_flow` mas sem `messages` (ou com `messages: []`).

**Como corrigir:**

1. Para agentes conversacionais normais: o prompt provavelmente já manda `messages` — esse erro raramente acontece em prompts gerados pelo creator.
2. Para agentes **silenciosos/triadores/classificadores** (que tentam ser puramente actions): adicionar uma **frase de transição curta predefinida por categoria**. Exemplo:

   **Antes (quebra a plataforma — send_flow não dispara):**
   ```json
   {
     "actions": [
       {"action":"set_field_value","field_name":"resumo","value":"..."},
       {"action":"send_flow","flow_id":"123"}
     ]
   }
   ```

   **Depois (funciona):**
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

⚠️ **Se estiver corrigindo um prompt de agente silencioso e o cliente afirma que o agente não pode falar nada com o usuário:** explique ao cliente que essa frase de transição é exigência da plataforma para o `send_flow` funcionar. Ela é curta, "meta" (só anuncia a transferência, não conversa sobre o problema), e pode ser predefinida — o agente não improvisa. É o menor compromisso possível para destravar o roteamento.

### Exceção legítima: disparo silencioso (só-actions)

⚠️ **NEM TODO `send_flow` sem `messages` é erro.** 3-4 prompts-ouro usam
só-`actions` (com `messages:[]` ou omitido) DE PROPÓSITO, e corrigir isso
QUEBRA o comportamento. Casos whitelistados (NÃO adicionar mensagem):

| Caso | Evidência | Por quê não tem messages |
|---|---|---|
| NPS pós-encerramento | Duda-SAC, Let (flow `1775096402729`) | O fluxo NPS já comunica; mensagem do agente causaria despedida duplicada |
| Descadastro confirmado | Bia (passo 2) | Já confirmou no passo 1; passo 2 só executa |
| Mockup/coleta de mídia | Uni (`"messages":[]`, flow `1780170720912`) | O fluxo coleta o upload; o LLM não gerencia imagem |

Verbatim (Let): *"NPS — disparo silencioso pós-encerramento, somente actions
sem messages."* Verbatim (Duda-SAC): *"Nunca envie uma mensagem de despedida
antes do NPS."*

**Como distinguir erro de exceção:**
- É **erro** (adicionar messages) quando o `send_flow` é o handoff PRINCIPAL
  pra um humano e o cliente está esperando resposta.
- É **exceção legítima** (deixar sem messages) quando: (a) o prompt rotula
  como NPS / pós-encerramento / disparo silencioso / mockup / descadastro
  confirmado, OU (b) há `"messages":[]` EXPLÍCITO (sinaliza intenção, não
  esquecimento), OU (c) é um passo 2 de uma confirmação de 2 etapas.
- Na dúvida → **PENDÊNCIA**, não auto-corrigir. Pergunte se o flow comunica
  sozinho.

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

**Como corrigir:** inserir o bloco LITERAL (sem parafrasear) no início da seção "FORMATO DE RESPOSTA" / "FORMATO DE SAÍDA" / equivalente. Se o prompt não tem essa seção, criar uma seção "FORMATO DE SAÍDA — JSON OBRIGATÓRIO" e colocar o bloco como primeiro conteúdo.

**Por quê:** padronização. Toda IA NexTags responde com o mesmo contrato JSON. Sem o bloco, o agente pode confundir o esquema, especialmente em primeiras chamadas (cache frio). Esse bloco é a especificação canônica que o time NexTags fornece como referência oficial.

**Não substituir nem parafrasear:** o prompt pode ter mais regras adicionais DEPOIS desse bloco, mas o bloco em si vai literal.

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

**Preço literal em exemplo JSON com tool de catálogo:** se o prompt tem tool de preço
mas os exemplos mostram um preço real (ex.: "R$ 129,90"), troque por placeholder
`R$ 0,00` — o LLM copia o exemplo como valor real. Preço sempre da tool.

---

## 19. Lints opcionais (avisar, não bloquear)

- Travessão / em-dash (`—`) em campos `text` — sinal de "cara de IA"; sugerir trocar
  por vírgula, ponto ou "e". Idem diminutivos forçados ("rapidinho", "horinha").
- Emoji 🤖 em mensagem — assume "sou bot"; sugerir remover.

---
name: nextags-mcp-builder
description: Constrói o servidor MCP no n8n (NexTags) que liga um agente IA às APIs do cliente (Tray, VTEX, Shopify, Nuvemshop, Bling, Martz, Yampi, Yever, RD Station, etc.). Foco EXCLUSIVO em infraestrutura — não toca em prompt, persona, flow_ids nem regras de atendimento (responsabilidade da skill nextags-prompt-creator). Use quando o usuário diz "criar MCP", "plugar API no agente", "configurar n8n pra cliente novo" ou similar.
type: tool
---

# nextags-mcp-builder

Fabrica a **infraestrutura MCP** completa no n8n pra um cliente novo da NexTags. Recebe uns poucos inputs e entrega workflows ativos prontos pra serem consumidos por qualquer agente.

## 🚨 O MCP mora no n8n — não se constrói servidor à parte

Não proponha (nem aceite briefing pedindo) servidor MCP standalone em Node/Express/TypeScript
com `server.tool()` e Zod. Todo MCP desta operação é n8n: MCP Server Trigger v2 + tools +
backends. Já houve rascunho pedindo servidor externo "seguindo o padrão da Mayuí" quando o MCP
real da Mayuí é 100% n8n — o rascunho tinha entendido errado a própria referência que citava.

## 🚨 Regra inegociável — pasta no n8n antes de qualquer workflow

**Antes de criar qualquer workflow, confirmar a pasta do cliente no n8n.**

1. Chamar `search_folders` com o nome do cliente
2. Se encontrar → usar o `folderId` retornado
3. Se não encontrar → **perguntar ao usuário**: *"Não encontrei a pasta '[Nome]' no n8n. Ela já existe com outro nome, ou você cria agora na interface?"*
4. ⚠️ **Não existe `create_folder` no MCP do n8n** — a criação de pasta é manual, na interface web. Peça ao usuário e espere. Enquanto a pasta não existir, o fallback é: criar os workflows, aplicar **tag com o nome do cliente** em todos, e **`move_workflows_to_folder`** assim que a pasta existir. Esse caminho é pendência de entrega, não pode ficar esquecido (Nalisa 2026-07-03 e Cantarola ficaram soltos no projeto pessoal; Otogama idem).
5. Passar `folderId` em **todos** os `create_workflow_from_code` quando a pasta existir — sem exceção
6. O **nome do cliente DEVE aparecer no nome de todos os workflows** — MCP, backends, smoke test, refresh, reset

Exemplos corretos:
- `Veuske MCP` ✅
- `Veuske Backend — Buscar Cliente` ✅
- `Veuske Smoke Test (manual)` ✅

Errado:
- `ZOPPY Backend — Buscar Cliente` ❌ (falta o nome do cliente)
- `MCP` ❌ (genérico demais)

## 🚨 Regra inegociável — transporte do MCP

**Todo MCP Server criado por esta skill DEVE usar Streamable HTTP. Nunca SSE.**

- Sempre force `version: 2` no node `@n8n/n8n-nodes-langchain.mcpTrigger`
- Mesmo que o SDK typedef reporte v1.1, force `version: 2` (validator aceita; servidor resolve)
- NexTags **não conecta** com SSE legacy. v1.1 expõe só `GET /mcp/<slug>/sse` → NexTags retorna 404 ao tentar POST
- v2 expõe `POST /mcp/<slug>` (Streamable HTTP, MCP spec 2025-03-26) que é o único caminho funcional
- Se herdar workflow legacy com v1.1, **upgrade pra v2 antes de qualquer outra mudança**
- Teste pós-deploy obrigatório: `curl -X POST` no endpoint deve devolver 200 + JSON-RPC `initialize` válido. Se vier 404 "did you mean DELETE?" → v1.1, corrige

Detalhes técnicos completos: `references/quirks_n8n.md` §1.

## 🚨 Regra inegociável — n8n sempre via API/MCP, nunca via navegador/UI

Toda criação/edição de workflow n8n passa pelo MCP do n8n, nesta ordem:

```
search_workflows → validate_workflow → create_workflow_from_code / update_workflow → publish_workflow
```

**Nunca** automação de UI (clicar em nodes, arrastar, colar JSON manualmente no editor
web). `search_workflows` primeiro pra checar se já existe (idempotência); `validate_workflow`
antes de criar/atualizar pra pegar erro de schema cedo; `create_workflow_from_code` ou
`update_workflow` pra aplicar; `publish_workflow`/ativar ao final. Se alguma dessas tools
falhar ou não cobrir um caso, pare e pergunte — não tente contornar abrindo o n8n no
browser.

## 🚨 Regra inegociável — sticky note explicativo em TODO workflow

Todo workflow criado por essa skill leva **1 sticky note no topo do canvas**, como
`n8n-nodes-base.stickyNote`. É documentação executável: fica junto do workflow, não numa
wiki externa que ninguém abre de novo.

**Modelo canônico** (adaptado de Degan/Nordmann/Poé, corpus de 21 workflows n8n em produção):

```
## <Cliente> <Sistema> — <o que é>
Endpoint: <URL pública completa>
ESTADO EM dd/mm
  <o que está confirmado por chamada real / o que falta>
CREDENCIAIS
  <Nome do header, Bearer ou valor puro, de que conta>
PENDENTE / NÃO ATIVAR antes de…
  <lista do que falta preencher antes de ligar>
ARMADILHAS (com evidência)
  <"confirmado por chamada real em dd/mm": ...>
DE ONDE VEIO a lista de campos
  <"não foi de memória" — cite a fonte real>
Decisões negativas
  <"não usar X de propósito, porque…">
```

**Exemplo real curto** (Degan MCP, `Wt3SsrCxQ2zwwnOo`):

```
## Degan MCP - Praticx + BW
Endpoint: https://nextags.app.br/mcp/degan-mcp
ESTADO EM 02/09
  BW  -> slug degan1 CONFIRMADO por chamada real. Falta a credencial.
  Praticx -> host ainda PENDENTE nas 3 tools de catalogo (servidor local da Degan).
CREDENCIAIS
  BW Commerce Token -> Header Auth, header 'Token', valor puro. NAO e Bearer.
  Praticx API Token -> Bearer.
ENVELOPE DA BW (a spec esta errada nisso)
  Toda resposta: { registros: [...], erros: [...], totalRegistros: N }
  Sempre HTTP 200, inclusive em falha de autenticacao.
PrecoCusto fica FORA das tools de catalogo de proposito - nao adicionar em fields.
```

Nunca deixe a sticky dizer "pronto"/"ativo" enquanto ainda há placeholder no código — isso
é contradição a ser flagrada em auditoria, não um detalhe cosmético.

## 🚨 Regra inegociável — Data Table de dedup/estado + heartbeat pra automação crítica

Todo workflow que pode receber **replay**, faz **polling**, ou processa uma **fila** leva
uma Data Table de dedup/estado — nome `<Cliente> <Plataforma> Orders State` (ou `...
Carrinho Dedup`). A gravação do dedup só acontece **depois** do sucesso do POST na NexTags,
nunca antes/em paralelo — gravar antes marca o cliente como "notificado" pra sempre mesmo
quando a chamada falhou (evidência: Nordmann v2/v3, Meiskin v1/v2 — 51 clientes reais que
nunca seriam notificados; `references/quirks_n8n.md` Quirk #32). Para automação **agendada
crítica** (lembretes, confirmações, cron transacional), o par heartbeat+watchdog+error
workflow é obrigatório, não opcional: um Error Workflow (`settings.errorWorkflow`) cobre
falha que gerou exceção capturável, mas **não** cobre o worker do n8n morrendo antes do
primeiro node rodar — só um Watchdog (cron que lê uma tabela de heartbeat e detecta
ausência) cobre esse caso. Padrão de referência: Otogama Watchdog (`Gtxxg7YTbApcT4tE`) +
Otogama Error Handler (`W7cuLshLtted1VPz`), motivados pelo mesmo incidente real (worker
morto, `startedAt: null`, nenhum alerta interno disparou). Detalhe de implementação:
`references/arquitetura_padrao.md` §"Convenção de Data Tables de estado/dedup/heartbeat".

## 🚨 Regra inegociável — campos nativos Nextags no payload `/api/contacts`

Toda vez que um workflow n8n fizer `POST https://app.nextagsai.com.br/api/contacts`, estes campos vão **diretamente no root** do JSON — **nunca** como `set_field_value` na array `actions`:

| Campo raiz   | Valor                             |
|--------------|-----------------------------------|
| `first_name` | Primeiro nome do contato          |
| `last_name`  | Sobrenome(s) do contato           |
| `email`      | E-mail                            |
| `phone`      | Telefone E164 (`+5511999999999`)  |

O restante (CPF/CNPJ, número do pedido, status, valor, rastreio, etc.) vai em `actions` como `set_field_value`.

```json
// ❌ Errado — email/nome como CUF
{ "actions": [{ "action": "set_field_value", "field_name": "ClienteEmailNS", "value": "..." }] }

// ✅ Certo — campos nativos no root
{ "first_name": "João", "last_name": "Silva", "email": "j@x.com", "phone": "+5511999999999", "actions": [...] }
```

Criar CUFs para nome/email/telefone/documento é redundante, polui o admin da NexTags e quebra filtros nativos da plataforma. Lição aprendida em neuroFood 2026-06-24.

## 🔌 Como expor as tools para a NexTags enxergar

Doutrina consolidada de como uma tool sai do n8n e chega visível/chamável pela NexTags:

1. **Trigger:** MCP Server Trigger **v2**, path `/mcp/<slug>` — Streamable HTTP (ver regra
   de transporte acima e `quirks_n8n.md` §1).
2. **Tools:** sempre `n8n-nodes-base.httpRequestTool` v4.4/v4.5, com `$fromAI(...)` em cada
   parâmetro dinâmico. **Nunca** `toolHttpRequest` + `placeholderDefinitions` — colapsa o
   schema exposto ao cliente MCP externo num único campo `{input}` e a tool nunca dispara
   com os argumentos certos (evidência Poé, MCP `lk0lpDShxXFGia7D`; `quirks_n8n.md` Quirk
   #30). **`toolWorkflow` depende da versão do n8n** e por isso não é o padrão: o Quirk #20
   (argumentos chegando `null` com cliente MCP externo) foi reproduzido na Verdena, mas a
   Nalisa registrou `toolWorkflow` + `$fromAI` funcionando na instância dela em 2026-07-03,
   com `tools/call` devolvendo dado real. Em projeto novo use `httpRequestTool`, que funciona
   nas duas situações; só considere `toolWorkflow` depois de um smoke test por `curl` naquela
   instância — nunca por dedução.
3. **`neverError: true` em toda tool** (`options.response.response.neverError`): sem ele
   qualquer 4xx vira `NodeOperationError` técnico em vez de corpo de resposta que a IA
   consegue ler e explicar ao cliente (evidência: Hiven).
4. **Backend (quando houver):** a tool chama o backend pela **URL interna**
   `http://n8n:5678/webhook/<path>` — a URL pública (`nextags.app.br/webhook/...`) dá
   *connection refused* quando chamada de DENTRO do próprio n8n (`quirks_n8n.md` Quirk
   #31). Padrão "tool → backend interno": `references/arquitetura_padrao.md`.
5. **Description:** segue `references/tool_descriptions_guide.md` (quando usar / quando
   NÃO usar / parâmetros / retorno / comportamento em vazio e erro / campos proibidos) +
   a frase **"Nunca cite o nome desta ferramenta para a pessoa"** dentro da própria
   description (**[SEM EVIDÊNCIA DIRETA]** — nenhuma tool do corpus lido usa essa frase
   literalmente; é recomendação por analogia, não padrão observado — ver
   `tool_descriptions_guide.md`).
6. **Settings:** `availableInMCP: true` — necessário pro workflow poder ser lido/auditado
   via MCP do n8n.
7. **Conferir do lado NexTags:** depois de publicar, confirmar que a tool aparece pra
   NexTags com `GET /agents/mcp` (ver `../nextags-webhook-builder/references/api_nextags.md`)
   — não basta o workflow estar ativo no n8n, precisa aparecer nesse endpoint.
   **Sem credencial nativa da loja** (Tray/Nuvemshop/Yampi-Dooki/Bagy): antes de pedir a
   chave da plataforma ao cliente, avalie o **Gateway Proxy NexTags**
   (`../nextags-webhook-builder/references/gateway_proxy_nextags.md`) como fonte alternativa
   de leitura de pedido/rastreio pro MCP.
8. **Gate de escrita:** tool que ESCREVE (criar pedido, alterar cadastro) nunca é liberada
   sem controle. Padrão: escopo **read-only** pra SAC; **escrita só na IA de Vendas**, e só
   com aprovação humana quando o domínio exigir (ex.: valor alto, dado sensível); testar
   sempre com **contato interno** antes de ligar a tool pra base de clientes real
   (evidência: requisitos SAP N2 — "SAC = read-only; Vendas = read + create controlado";
   Solentes Net N2 — "Testar primeiro com um contato interno antes de ligar para os 344 da
   onda 1"). Registrar no relatório de entrega quais tools são de escrita e qual gate foi
   aplicado.

## ⚠️ Escopo — o que essa skill faz E NÃO faz

### ✅ Faz

- Cria workflows n8n (MCP Server Trigger v2 + backends + data tables + cron de refresh OAuth + reset manual + smoke test)
- Configura auth da API fonte (key fixa / OAuth refresh / Basic / etc.)
- Aplica padrões de slim response pra economizar tokens
- Documenta a infra entregue (URL do MCP, IDs dos workflows, credenciais usadas)

### ❌ NÃO faz

- **Não cria prompt do agente** — isso é da skill `nextags-prompt-creator`
- **Não pergunta sobre persona, tom de voz, nome do bot** — irrelevante pra infra
- **Não pergunta flow_ids da NexTags** — flow_id de SAC, pipeline, tabela de medidas etc. são do prompt, não do MCP
- **Não pergunta sobre cupons, políticas de envio/troca** — regras de negócio, não da infra
- **Não gera bateria de testes do agente** — também `nextags-prompt-creator`

Se o usuário precisa de **infra + prompt + testes** pra cliente novo, use as 3 skills em sequência:
1. `nextags-mcp-builder` (esta) — infra
2. `nextags-prompt-creator` — gera o prompt
3. `nextags-prompt-fixer` — audita o prompt antes de subir

## 📋 Brief mínimo — só 3 perguntas

Quando o usuário invocar essa skill, pergunte **apenas estes 3 inputs**:

### 1. Nome da loja / cliente
Pra naming dos workflows no n8n e geração do slug (kebab-case) que vai no path do MCP. Exemplo: "Mayuí Fit Wear" → slug `mayui-fit-wear` → MCP em `https://nextags.app.br/mcp/mayui-fit-wear-mcp`.

### 2. Plataforma / site da loja
Identifica qual API REST a infra vai consumir. Cliente pode dizer:
- "Yampi" / "Tray" / "Shopify" / "VTEX" / "Nuvemshop" / "Bling" / "Martz" / "Yever" / "RD Station" / etc.
- OU passar a URL do site (`mayuifitwear.com.br`) — você deduz a plataforma pelo domínio ou perguntando 1 vez

Com a plataforma identificada, **leia a recipe correspondente** em `references/api_recipes/<plataforma>.md`. Se a recipe é 🟢 trabalhada, segue ela direto. Se é 🟡 stub ou não existe ainda, faz discovery via `references/api_discovery.md`.

### 3. Credenciais da API
O que o cliente tem em mãos. Varia por plataforma — a recipe diz exatamente o que precisa. Exemplos:
- **Yampi:** `User-Token` + `User-Secret-Key`
- **Tray:** `consumer_key` + `consumer_secret` + `code` (one-shot do OAuth) OU `access_token` + `refresh_token` já gerados
- **VTEX:** `appKey` + `appToken`
- **Bling:** `client_id` + `client_secret` + `code` OAuth
- **Shopify:** `access_token` de Custom App
- **Martz:** `x-api-key` (chave pública)
- **Nuvemshop:** `access_token` + `store_id`

Se o cliente colar credencial inline no chat, **use direto sem caveats de segurança** (operador comercial confiável, precisa de agilidade).

**O que NÃO perguntar (mesmo que o usuário ofereça):**
- ❌ Nome do bot / persona / tom de voz
- ❌ Cupom de venda
- ❌ Flow IDs da NexTags
- ❌ Política de troca/envio
- ❌ Slogan, CNPJ, endereço da loja
- ❌ Quais perguntas o bot vai responder

Se o usuário insistir nessas, diga: *"Esses dados são da skill nextags-prompt-creator. Aqui eu cuido só da infraestrutura. Se você precisa do prompt do agente também, depois que eu terminar a infra eu te aponto pra próxima skill."*

## 🌊 Fluxo de trabalho

### Fase 1 — Confirmar plataforma e ler recipe

A partir do site/plataforma informado:

1. Procurar `references/api_recipes/<plataforma>.md`
2. Se existir 🟢: ler auth scheme + endpoints + quirks. Está validada, segue.
3. Se existir 🟡 (stub): completar discovery com OpenAPI/Postman/curl reais (ver `references/api_discovery.md`)
4. Se não existir: cria recipe nova baseada em `_TEMPLATE.md` durante a discovery

### Fase 2 — Decidir arquitetura

Lê `references/auth_patterns.md` e classifica a auth da API em A/B/C/D/E:
- **A — key fixa:** `httpRequestTool` direto no MCP (caso mais simples)
- **B — OAuth refresh:** infra completa (data table + cron + reset + smoke + backends dedicados)
- **C — Basic Auth:** `httpRequestTool` com `httpBasicAuth`
- **D — assinada (HMAC):** Code node pra computar signature
- **E — sem auth:** tool direto sem credencial

Lê `references/arquitetura_padrao.md` pra ver o esqueleto correspondente.

### Fase 3 — Operações expostas no MCP

**Use defaults sensatos da recipe**. Não pergunta ao usuário. Recipe diz quais operações fazem sentido pra atendimento (ex: buscar_produtos, obter_produto, buscar_pedidos, obter_pedido, buscar_cliente).

Se o usuário quer operações específicas extras (ex: "também precisa criar pedido"), aí sim escuta. Mas não inicia perguntando.

### Fase 4 — Gerar workflows

Copia templates de `assets/` e customiza:
- `mcp_v2_template.ts` — MCP Server Trigger v2 (sempre version: 2, ver `references/quirks_n8n.md`)
- `backend_template.ts` — 1 backend dedicado por operação (sempre — `workflowInputs` quirk)
- `refresh_oauth_template.ts` — se auth for B (OAuth)

Antes de criar, **valida com `validate_workflow`** do MCP n8n. Depois cria com `create_workflow_from_code`.

**Ordem de criação:**
0. **Pasta do cliente** — `search_folders` → se não existir, pedir ao usuário que crie na interface (não há `create_folder` na API) → guardar `folderId`
1. Data table de tokens (se OAuth)
2. Refresh Token workflow (se OAuth) — nome: `<Cliente> Refresh Token — <API>`
3. Reset Token workflow manual (se OAuth) — nome: `<Cliente> Reset Token — <API> (manual)`
4. Smoke Test workflow manual — nome: `<Cliente> Smoke Test — <API> (manual)`
5. N Backends dedicados (1 por operação) — nome: `<Cliente> Backend — <Operação>`
6. MCP Server Trigger workflow — nome: `<Cliente> MCP`

Todos os `create_workflow_from_code` devem incluir o `folderId` da pasta do cliente.

### Fase 4.4 — REGRA UNIVERSAL: links com UTM (TODOS os clientes)

**Leia OBRIGATORIAMENTE** `references/link_envio_pattern.md` SEMPRE que o brief mencionar:

- Agente de **Vendas** (vai enviar link de produto/kit)
- Webhook transacional com **link no payload** (pedido pago, carrinho abandonado, recompra)
- Cron de **campanha** (D+80 refil, reativação, recuperação)
- Qualquer fluxo onde o cliente recebe URL clicável da loja

**Padrão obrigatório** em todos os casos (já com valores hardcoded por cliente):

```
https://<dominio-do-cliente>/products/{handle}?utm_source=whatsapp&utm_medium=<nome_agente>_<funcao>&utm_campaign=<contexto>
```

Exemplo Veuske: `https://veuske.com.br/products/kit-vk100/?utm_source=whatsapp&utm_medium=pedro_vendas&utm_campaign=indicacao_consultiva`

Sem UTM = sem atribuição = lojista não consegue medir ROI do agente IA. **Inegociável.**

⚠️ **Cuidado com placeholders.** A tool description vai pra IA em runtime. Hardcode TODOS os valores (`dominio`, `medium`, `campaign`) na string da description — só `{handle}` permanece como placeholder (porque ESSE valor vem do retorno da tool). Ver §"Distinção crítica" em `link_envio_pattern.md`.

A tool description que retorna `handle`/`slug` DEVE conter literalmente a frase de como montar URL. Workflows transacionais e crons concatenam o UTM no Code node antes de mandar pra NexTags.

### Fase 4.45 — Se o brief inclui múltiplos agentes ou handoff humano

**Leia OBRIGATORIAMENTE** `references/handoff_pattern.md` (reescrito) e
`references/campos_canonicos.md` quando o brief tem:
- 2+ agentes IA (Vendas + SAC, por exemplo)
- Handoff IA → humano (fila de atendimento)
- Necessidade de contexto pro pipeline (`resumo_pipeline`)

**Modelo canônico atual** (substitui o padrão de flows dedicados por destino):

- **UM roteador único** roda a cada mensagem e é o ÚNICO que grava `setor_agente`
  (`vendas` \| `sac` \| `ignorar`). Um **revalidador** (2ª camada, só no
  `else`) grava `tipo_setor` (`humano` \| `bot`).
- **Nenhuma IA transfere para outra IA.** A IA só transfere pra HUMANO, gravando o trio
  `motivo_transferencia` + `prioridade_pipeline` + `resumo_pipeline` e disparando **UM**
  `flow_id` de pipeline (nunca um flow por fila/agente).
- Esta skill **não decide** nada disso (enum, prioridade, texto do resumo são do prompt —
  `nextags-prompt-creator`/`nextags-prompt-fixer`). O que cabe ao MCP-builder é **garantir
  a infra**: os CUFs canônicos existem na conta, com o tipo certo (`setor_agente` Texto,
  `tipo_setor` Seleção única, `motivo_transferencia` Texto, `prioridade_pipeline` Seleção
  única, `resumo_pipeline` Texto/Long Text). Setup idempotente por API:
  `GET /accounts/custom_fields` → diff → `POST /accounts/custom_fields {name, type}` (ver
  `campos_canonicos.md` §7.5). A API não tem DELETE — dry-run antes de criar.

Diagrama completo do fluxo de entrada, fluxo de pipeline, enum por painel e checklist de
auditoria: `references/handoff_pattern.md`. Guard contra o loop do roteador (Quirk #27):
mesmo arquivo, §4.

### Fase 4.5 — Se o brief inclui webhooks transacionais (pedido pago/enviado/entregue, carrinho abandonado)

O padrão vigente pra webhook transacional está na skill **`nextags-webhook-builder`**, não
mais nesta skill. Aponte o usuário pra lá quando o brief incluir transacional:

- Naming canônico **snake_case** + campo `origem_pedido` (nunca a plataforma no nome do
  campo) — ver `campos_canonicos.md` §5.
- **Dedup só grava depois do sucesso** do POST na NexTags, nunca antes/em paralelo (ver
  regra inegociável de Data Table acima e `quirks_n8n.md` Quirk #32).

`references/webhook_transactional_pattern.md`, nesta skill, é **histórico** (padrão
Rafa/Veuske, CamelCase + sufixo de origem) — mantido só de referência, carrega banner no
topo apontando pro padrão vigente. **Não copiar** esse arquivo em projeto novo.

### Fase 4.6 — Cliente sem ERP/API: MCP com GitHub como banco

Quando o cliente não tem sistema com API pra consultar catálogo de mídias, FAQ ou tabela de
preços estável, **leia OBRIGATORIAMENTE** `references/mcp_github_repo_pattern.md` antes de
desenhar a infra. Resumo: repo GitHub com `catalogo.json`, lido via jsDelivr (nunca
`raw.githubusercontent` — MIME errado quebra mídia no WhatsApp, Quirk #29), backend n8n
filtra e devolve ação explícita (`disponivel:false` → "não prometa"; `erro_tecnico:true` →
só texto). Trocar mídia/preço = commit no repo, nada muda no n8n nem no prompt.

### Fase 5 — Slim response em todo backend

Aplica Code node de slim em CADA backend (ver `references/slim_response_patterns.md`). Reduz payload em 80-95%. Padrão:
- Detecta erro 4xx/5xx → retorna `{error, code}` estruturado
- Unwrap (data/list/Products/etc.)
- Extrai só campos essenciais
- Limpa HTML em descrições
- Pega só URL https principal de imagens (descarta thumbs)
- Classifica campos: exibível / `_internal` (classificação) / PII mascarada (ver `slim_response_patterns.md`)
- Traduz enums técnicos para label PT (`in_transit`→"Em trânsito") mantendo o cru em `_internal`
- Distingue vazio (`empty:true`) de erro técnico (`transient:true`)
- Preserva identificadores opacos (`cart_id`/`phash`/`customer_id`) byte a byte
- **Imagens: validar formato E tamanho.** A NexTags só entrega JPEG/PNG nos canais, e a **Meta bloqueia acima de 5 MB (imagem) e 15 MB (vídeo)** — 1 MB a mais e a mensagem não sai, sem erro visível. PNG 16-bit é rejeitado mesmo pequeno. Conversão é na URL (parâmetro do CDN ou proxy Cloudinary `f_jpg,q_auto`), não no n8n: os bytes nunca passam pelo workflow. CDNs (Shopify, VTEX, Nuvemshop, Cloudinary) servem WebP por padrão e quebram WhatsApp/Instagram. Estratégias detalhadas: `references/image_validation.md`. No mínimo, anexar campo `image_format_hint` na resposta do slim baseado em heurística de extensão (`likely_jpeg_or_png` / `forbidden_format` / `unknown_validate_before_send`); preferível incluir uma tool `validate_image_url` que faz HEAD HTTP e devolve Content-Type. Sempre avisar o usuário se a API fonte serve WebP — pra que o prompt do agente seja calibrado pra omitir imagem na dúvida.

**Nunca use `optimize_response` do n8n** — entrega JSON cru via MCP Streamable HTTP (quirk #18) e quando funciona, corta com heurísticas genéricas que não conhecem o contexto do atendimento (lição DOLPS). Use sempre Code node manual.

**Critério de "essencial":** a pergunta não é "esse campo parece técnico?", é "um cliente pode perguntar sobre isso?". Quando em dúvida, manter. Veja `slim_response_patterns.md` §"O critério que define essencial" para tabela completa de campos obrigatórios por pergunta de cliente.

### Fase 6 — Configurar credenciais no n8n

A skill NÃO consegue criar credenciais via API direto. Apenas:
1. Define no SDK qual credencial cada nó usa (via `newCredential('Nome')`)
2. **Avisa o usuário** ao final: "Crie a credencial X com tipo Y e valor Z, e vincule aos nós listados"

Lista clara dos nós que ficaram pendentes de credencial (vem da resposta da API n8n).

### Fase 7 — Entrega

Salva relatório em `Z:\WALKERS\<cliente>\relatorio-mcp.md` — caminho **confirmado**: é onde
estão os 75 relatórios de maio a setembro/2026. Fallback se `Z:\` não existir na máquina do
operador: `C:\Users\User\Documents\WALKERS\<cliente>\relatorio-mcp.md`. Conteúdo:
- URL do MCP exposto (`https://nextags.app.br/mcp/<slug>`)
- IDs dos workflows criados
- Credencial(is) que o usuário precisa criar/vincular
- **"PASSOS PRA COLOCAR EM PÉ"** — runbook numerado, separado do "como testar": criar
  credencial → vincular nos N nodes (listar quais) → smoke test → ativar → configurar webhook
  externo → preencher placeholders. É a seção que o operador segue na mão; sem ela o relatório
  descreve o que existe mas não diz o que fazer a seguir (formato recorrente no corpus:
  AnaGrow, Amo Calçados, Hiven, Alto Giro)
- Como testar (curl no endpoint, ou via Smoke Test workflow)
- **Metadados de governança pro prompt-creator** (por tool):
  - `classe` semântica (leitura/catalogo/transacional/logistica-FdV/cadastro/auxiliar)
  - campos PROIBIDOS de exibir e campos de USO INTERNO
  - mapa de tradução de enums aplicado no slim
  - pipeline de encadeamento (saída→entrada) com chaves opacas a copiar literal
  - frases de AUSÊNCIA de capacidade (ex: "não há tool de cotação de frete")
  - boilerplate "nunca exponha o nome técnico da tool" (dentro da description E no relatório)
- **CUFs e tags criados/necessários** (nomes canônicos — `campos_canonicos.md` §3, §4, §7):
  - Quais CUFs já existiam na conta vs. quais foram criados agora (com tipo: Texto,
    Seleção única, etc.)
  - Se algum CUF necessário ainda falta criar (ex.: `setor_agente`, `motivo_transferencia`)
    e ficou pendente de decisão do dono
  - Tags necessárias (transacional, prioridade) e se já existem na conta
- **Tools expostas + como conferir:**
  - Lista de tools com nome técnico, `classe` semântica e se é leitura ou escrita (com gate
    aplicado, se houver)
  - Como conferir no painel NexTags e via API: `GET /agents/mcp` (ver
    `../nextags-webhook-builder/references/api_nextags.md`) pra confirmar que a NexTags
    enxerga o MCP; `curl` direto no endpoint do MCP pra confirmar handshake
- Próximos passos sugeridos:
  - **Se cliente também precisa de prompt:** "use `nextags-prompt-creator` em seguida — passa nome da loja, site, descrição do negócio"
  - **Se infra é pra plugar num prompt existente:** "URL do MCP acima — configura na NexTags como conector"

### Fase 8 — Checklist de config de modelo (OBRIGATÓRIO antes de "pronto")

**Leia OBRIGATORIAMENTE** `references/model_config_checklist.md` e passe pelo user a config canônica do agente no NexTags ANTES de marcar projeto entregue:

- Modelo: **Claude Sonnet 4.6** (ou GPT 5.4 não-mini) — NUNCA "mini" com prompt longo
- Temperature: **2** (escala 0-10) — máximo 3
- Verbosity: média
- Reasoning: alta
- Max tokens: máximo

Sintomas de config errada (agente pula tool, parafraseia 7x, inventa dado, loop de transferência) custam mais horas pra debugar do que mudar config corretamente no setup. Lição cara aprendida na Veuske 2026-06-11: temp 8 + GPT mini fez Pedro mandar 404 pro cliente e travar em loop. Mudou pra temp 2 + Sonnet 4.6 → resolvido no primeiro teste.

**Não marque entregue sem confirmar config com o user.**

## 📜 Princípios

### Agilidade > paranoia com credenciais

Operador compartilha keys/tokens inline no chat porque precisa velocidade. **Não dê caveats de segurança redundantes**. Use direto, registre na credencial n8n apropriada ou na data table, siga em frente.

### 🔐 Mas NUNCA escreva tokens reais em docs da skill

Esta skill é versionada no GitHub. **Qualquer arquivo em `references/`, `assets/` ou `api_recipes/` é público.** Tokens reais nesses arquivos:

- ❌ São bloqueados pelo Secret Scanning do GitHub na hora do push
- ❌ Quando passam, ficam expostos no histórico git pra sempre (mesmo após `git rm`)
- ❌ Exigem revogação + rotação do token comprometido

**Regra absoluta:** quando documentar um exemplo em recipe/quirks/pattern que envolve token, use placeholder no formato `<tipo>_<descrição>`. Exemplos:

| ❌ Errado (token literal de produção) | ✅ Certo (placeholder) |
|---|---|
| `value: 'shpat_<TOKEN_LITERAL_AQUI>'` | `value: 'shpat_<32-hex-do-cliente>'` |
| `Client Secret: shpss_<SECRET_LITERAL>` | `Client Secret: shpss_<32-hex>` (não colar em docs) |
| `X-ACCESS-TOKEN: <NEXTAGS_LITERAL>` | `X-ACCESS-TOKEN: <NEXTAGS_ACCESS_TOKEN>` |
| `User-Token: <YAMPI_LITERAL>` | `User-Token: <YAMPI_USER_TOKEN>` |

**Onde tokens reais ficam:**
- ✅ Workflows n8n (hardcoded em `headerParameters` — privado da instância n8n)
- ✅ Data tables n8n (`Shopify Tokens`, `<Cliente> API Keys`, etc.)
- ✅ Memórias de projeto (`C:\Users\User\.claude\projects\<projeto>\memory\*.md`) — fica só na sua máquina, fora do git da skill
- ✅ Relatórios do cliente (`C:\Users\User\Documents\WALKERS\<cliente>\*.md`) — fora do git da skill

**Auto-check antes de comitar mudanças na skill:**

```bash
grep -rE 'shpat_[a-f0-9]{32}|shpss_[a-f0-9]{32}|shpca_[a-f0-9]+|atkn_|TR56[a-zA-Z0-9]{30,}|sk_[a-zA-Z0-9]{30,}|[0-9]{7}\.[a-zA-Z0-9]{30,}' references/ assets/
```

Se retornar algo, mascara antes de comitar.

### Fronteira IA ↔ fluxo — tool devolve SLIM, fluxo faz o pesado

A tool/MCP entrega dados **SLIM** (o mínimo pra IA conversar e decidir). A
**apresentação pesada** (catálogo grande, vários carrosséis, PDF/documento) e a
**coleta estruturada complexa** (medidas, formulário) são de **FLUXOS de bot**:
a IA dispara `send_flow` pro fluxo pré-montado — ela **não** monta payload
gigante e a tool **não** devolve tudo cru. É o que justifica o slim e a economia
de token (ver `references/slim_response_patterns.md`). Coleta de 1-2 campos = IA
grava com `set_field_value`; coleta complexa = fluxo.

### Descrições de tools são vida ou morte

LLM escolhe tool só pela descrição. Toda tool gerada deve seguir `references/tool_descriptions_guide.md` — quando usar / quando NÃO usar / formato de IDs / quirks. Antes de finalizar, valida que descrições estão claras.

### Não chuta valores

Doc REST mente. Sempre teste endpoint real antes de gerar tool. Aprendido na marra: Martz tem endpoints fantasma, Tray exige `%termo%`, etc.

### Mínimo de workflows no n8n

Antes de criar um workflow novo, pergunte: **"esse trabalho pode entrar em um workflow já existente?"**

- **Webhooks:** múltiplos eventos do mesmo sistema (aprovado/enviado/entregue) → 1 único webhook com Switch/IF, não 1 workflow por evento
- **Backends:** operações similares podem ser consolidadas com Switch (ex: `buscar_pedido` e `listar_pedidos` juntos se a lógica é próxima)
- **Cron:** 1 refresh de token por API, não 1 por operação
- **Smoke test:** 1 por cliente, não 1 por tool

Meta por perfil:
- Auth key fixa → **N+2** workflows (N backends + 1 MCP + 1 smoke)
- OAuth → **N+4** workflows (adiciona refresh + reset)

Qualquer coisa além disso precisa de justificativa explícita. O home do n8n não é lixeira.

### Idempotente

Roda 2x sobre o mesmo cliente com mesmo brief = mesmo resultado. Use `search_workflows` antes de criar pra detectar se já existe e atualizar em vez de duplicar.

## 📂 Estrutura desta skill

```
nextags-mcp-builder/
├── SKILL.md                              ← este arquivo
├── references/
│   ├── campos_canonicos.md               ← fonte de verdade do método (cópia idêntica em 4 skills — não editar aqui)
│   ├── arquitetura_padrao.md             ← 4 padrões (key/OAuth/híbrido/GitHub-como-banco) + Data Tables de estado
│   ├── quirks_n8n.md                     ← bugs documentados do n8n+NexTags (35 quirks)
│   ├── auth_patterns.md                  ← 5 tipos de auth → mapeamento n8n
│   ├── api_discovery.md                  ← descoberta de API a partir de doc
│   ├── tool_descriptions_guide.md        ← descrições perfeitas pra LLM + regras de domínio repetidas em produção
│   ├── slim_response_patterns.md         ← heurísticas de slim por entidade
│   ├── webhook_transactional_pattern.md  ← ⚠️ HISTÓRICO — padrão vigente é `nextags-webhook-builder`
│   ├── link_envio_pattern.md             ← UTM obrigatório em TODOS os links
│   ├── handoff_pattern.md                ← roteamento canônico (roteador único + revalidador) e handoff IA→humano, pro n8n
│   ├── mcp_github_repo_pattern.md        ← 🆕 GitHub como banco (cliente sem ERP/API) — padrão Poé
│   ├── model_config_checklist.md         ← config canônica de modelo (Sonnet/temp 2/verbosity média)
│   ├── no_hardcode_with_tools.md         ← NUNCA hardcode no prompt o dado que a tool retorna (causa #1 de "agente não usa tool")
│   ├── image_validation.md               ← JPEG/PNG só; limites da Meta (5 MB imagem, 15 MB vídeo) e como converter
│   └── api_recipes/                      ← recipes específicas
│       ├── _TEMPLATE.md
│       ├── vtex.md       🟢
│       ├── tray.md       🟢
│       ├── martz.md      🟢
│       ├── nuvemshop.md  🟢
│       ├── bling.md      🟢
│       ├── shopify.md    🟢
│       ├── yampi.md      🟢
│       ├── bw.md         🟢  ← pedido/cliente; responde 200 até em erro
│       ├── yever.md      🟡
│       ├── rd_station_crm.md  🟡
│       ├── appmax.md     🟢
│       ├── troquecommerce.md  🟡
│       ├── zoppy.md      🟢
│       └── zoppy_docs_oficial.md      ← doc oficial da Zoppy (apoio ao zoppy.md, sem status próprio)
├── assets/
│   ├── mcp_v2_template.ts                ← SDK do MCP Trigger v2
│   ├── backend_template.ts               ← SDK de 1 backend dedicado
│   └── refresh_oauth_template.ts         ← SDK de cron de refresh
└── scripts/
    ├── parse_openapi.py                  ← parser OpenAPI 3.x
    └── validate_brief.py                 ← valida brief mínimo
```

## 🤝 Skills complementares

- **`nextags-prompt-creator`** — gera o prompt do agente a partir de briefing + scraping. Inclui `prompt_template.md` (com flow_ids, persona, modos) e `stress_test_battery_template.md`
- **`nextags-prompt-fixer`** — audita o prompt criado contra regras absolutas NexTags
- **`nextags-webhook-builder`** — padrão vigente pra webhooks/disparos transacionais (pedido pago/enviado/entregue, carrinho abandonado). Use em vez de `references/webhook_transactional_pattern.md` (histórico) desta skill

Pipeline completo pra cliente novo: **mcp-builder → webhook-builder (se houver transacional) → prompt-creator → prompt-fixer**.

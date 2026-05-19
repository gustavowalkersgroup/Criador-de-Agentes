# Quirks do n8n + NexTags

Lista exaustiva dos bugs, comportamentos não-óbvios e gotchas que já mordemos. Sempre leia ANTES de gerar workflows.

---

## 1. MCP Trigger v1.1 só fala SSE legacy — use v2 sempre (REGRA INEGOCIÁVEL)

> 🚨 **Streamable HTTP é a única opção válida para MCP da NexTags. SSE legacy não conecta.** Esta regra está duplicada no topo de `SKILL.md` por ser crítica — qualquer workflow que apareça com v1.1 deve ser corrigido imediatamente, sem exceção.

### O que acontece

`@n8n/n8n-nodes-langchain.mcpTrigger` tem 2 versões:

- **v1.1** (default no SDK quando você não especifica): só expõe `GET /mcp/<path>/sse` (Server-Sent Events). NexTags **não conecta** com SSE.
- **v2**: expõe `POST /mcp/<path>` (Streamable HTTP, MCP spec 2025-03-26) E `GET /mcp/<path>/sse` (backward compat). **NexTags só conecta com Streamable HTTP.**

### Como evitar

Sempre force `version: 2` no SDK code:

```ts
const mcpTrigger = trigger({
  type: '@n8n/n8n-nodes-langchain.mcpTrigger',
  version: 2,  // ← OBRIGATÓRIO
  config: { ... }
});
```

O SDK ainda tem typedefs só pra v1.1 mas o validator aceita `version: 2` (descoberto testando). O n8n server resolve a versão real e ativa Streamable HTTP.

### Como detectar o bug se aparecer

Cliente diz "não consigo conectar o MCP na NexTags" e curl mostra:

```bash
$ curl -X POST https://nextags.app.br/mcp/<slug>
{"code":404,"message":"This webhook is not registered for POST requests. Did you mean to make a DELETE request?"}
```

→ Workflow está em v1.1. Atualize pra v2 e reative.

### Teste pós-deploy

```bash
curl -X POST -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}' \
  https://nextags.app.br/mcp/<slug>
```

Esperado:
```
event: message
data: {"result":{"protocolVersion":"2025-03-26",...}}
```

Se retornar 404 → v1.1. Se retornar 200 + JSON-RPC → v2 OK.

---

## 2. toolWorkflow descarta valores estáticos em workflowInputs

### O que acontece

Em `@n8n/n8n-nodes-langchain.toolWorkflow`, o `workflowInputs.value` só passa adiante valores que vêm via `$fromAI(...)`. Valores literais (strings hardcoded) chegam como `null` no workflow chamado.

Exemplo que **NÃO funciona**:

```ts
workflowInputs: {
  mappingMode: 'defineBelow',
  value: {
    operation: 'search_products',  // ← chega como null no backend
    query: expr('{{ $fromAI("query", "termo") }}')  // ← OK
  }
}
```

Tentativas de "consertar" que tampouco funcionam:
- `operation: expr('{{ "search_products" }}')` → null
- `operation: '=search_products'` → null

### Como evitar

**1 workflow backend por operação.** Cada um tem seu próprio Execute Workflow Trigger com inputs só dinâmicos. Não tente fazer 1 backend com router por `operation`.

Estrutura correta:

```
MCP Trigger v2
  ├─ tool "buscar_produtos"    → workflowId: backend1, inputs: { query }
  ├─ tool "obter_produto"      → workflowId: backend2, inputs: { product_id }
  └─ tool "obter_variacao"     → workflowId: backend3, inputs: { variant_id }
```

NÃO:

```
MCP Trigger v2
  └─ tool com switch interno por operation  ← QUEBRA
```

### Como detectar o bug se aparecer

Execução do backend chamado pelo toolWorkflow mostra:

```json
{"operation": null, "product_id": null, "query": "legging"}
```

Mesmo que você tenha hardcoded `operation: "search_products"` no workflowInputs.

---

## 3. Credenciais auto-vinculadas pelo n8n após `update_workflow` frequentemente erram

### O que acontece

Quando você atualiza workflow via `mcp__29c672c2-...__update_workflow` ou `create_workflow_from_code`, e o código usa `newCredential('Nome')`, o n8n tenta auto-vincular uma credencial existente do mesmo tipo. Frequentemente pega a **errada** — qualquer credencial httpHeaderAuth pode ser usada, mesmo que não seja a do projeto.

Exemplo real: criei `mcpAuthCred = newCredential('MCP Mayuí Fit Wear - Bearer Token')` e o n8n vinculou `Melhor Envio - AlongNails` automaticamente.

### Como evitar

Após cada `update_workflow`/`create_workflow_from_code` que envolva credenciais:

1. Olhe a resposta da tool — campo `autoAssignedCredentials` mostra o que ele vinculou
2. Se a credencial não bater com o esperado, avise o usuário
3. Usuário precisa abrir o workflow no n8n e re-vincular manualmente

A resposta também lista nodes que ficaram sem credencial:
```
"note": "HTTP Request nodes (X, Y, Z) were skipped during credential auto-assignment. Their credentials must be configured manually."
```

Esses nodes precisam ter credencial atribuída na UI antes do workflow funcionar.

### Como detectar o bug se aparecer

Workflow ativa mas execuções mostram erro 401 ou "Credentials not found". Sempre verifique credenciais antes de testar.

---

## 4. NexTags só aceita header customizado, não Bearer padrão

### O que acontece

NexTags, ao configurar conector MCP, aceita:
- **API key / Access token** (1 campo só)
- **Custom** (campo Header + campo Valor)
- ❌ **Bearer Token** — opção não existe ou não funciona

Tentamos com Bearer no MCP Trigger e NexTags não consegue conectar. Funciona com Custom + header customizado tipo `x-api-key`.

### Como evitar

Quando configurar auth no MCP Trigger:

- ✅ `authentication: 'headerAuth'` + credencial `httpHeaderAuth` com Name `x-api-key`
- ❌ `authentication: 'bearerAuth'` — não funciona com NexTags

Ou simplesmente:

- ✅ `authentication: 'none'` — gate fica via infra NexTags (URL pública mas não pra mundo)

### Default recomendado

`authentication: 'none'`. Cliente raramente exige auth no MCP (a NexTags em si já tem auth da própria plataforma).

Se cliente exigir, use headerAuth com `x-api-key` + token random de 64 hex chars (`openssl rand -hex 32`).

---

## 5. Workflow precisa estar ATIVO pra production URL funcionar

### O que acontece

n8n tem 2 URLs por workflow:
- **Test URL** (`/webhook-test/<path>` ou similar): funciona quando workflow está aberto no editor
- **Production URL** (`/mcp/<path>`): só funciona quando workflow está ativo (toggle "Active")

Bug comum: criar workflow, não ativar, tentar conectar NexTags na production URL → 404.

### Como evitar

Ao final do fluxo de criação, lembre o usuário:

1. Save workflow (Ctrl+S)
2. Toggle Active no canto superior direito

E pra refresh de OAuth, o workflow de cron também precisa estar ativo (senão o cron não dispara).

---

## 6. SDK aceita versions não-documentadas

### O que acontece

`get_node_types` retorna typedefs só pra versão mais recente que o SDK conhece. Mas n8n no servidor pode ter versões mais novas.

Exemplo: SDK retorna typedef de `mcpTrigger v1.1`, mas o n8n servidor tem v2. Se você usar `version: 2` no SDK, **passa pelo validator** (que apenas confere se o number é número), e funciona em runtime.

### Como evitar

Quando descobrir que a versão SDK não tem feature X mas a real tem, force a version superior. Use o `MCP Server Trigger version: 2` mesmo que typedef diga 1.1.

Outras versões a forçar (descobertas no caminho):
- httpRequestTool: sempre 4.4 (SDK pode default pra menos)

---

## 7. Tray e Martz têm IDs em formatos incompatíveis

### O que acontece

- Tray: IDs numéricos curtos (`101`, `369`)
- Martz: IDs UUID (formato `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

Se IA passar ID Tray (`101`) num endpoint Martz que espera UUID, PostgreSQL retorna erro 22P02 ("invalid_text_representation"). Não é 4xx HTTP — é 500 com mensagem específica.

### Como evitar

No prompt do agente, regra explícita:

> `customer_id` e `order_id` da Martz são UUID. Sempre obtenha via `buscar_cliente` ou `buscar_pedidos` antes de chamar `obter_cliente`/`obter_pedido`. Nunca use email/telefone/CPF/número como ID direto.

Vale pra qualquer API que misture ID format com IDs externos.

---

## 8. Tray search precisa `%termo%` explícito

### O que acontece

`/products?name=legging` retorna **zero resultados** mesmo se houver leggings. Tray usa SQL LIKE direto: sem wildcards explícitos, faz match exato.

`/products?name=%legging%` retorna todas. (`%` URL-encoded vira `%25%legging%25` — n8n cuida do encoding automaticamente.)

### Como evitar

No backend de search, wrap o termo automaticamente:

```ts
queryParameters: {
  parameters: [
    { name: 'name', value: expr('%{{ $fromAI("query", "termo") }}%') }
  ]
}
```

A IA passa termo "limpo" e o backend acrescenta wildcards. Documente no prompt que "o backend cuida disso, IA não precisa adicionar %".

Outras APIs podem ter quirks similares. Sempre teste um search de verdade antes de fechar a tool.

---

## 9. Resposta da API é verbosa por padrão

### O que acontece

APIs e-commerce retornam objetos GIGANTES por produto/pedido:
- HTML cru em descrições (`<p>`, `&oacute;`)
- 3-4 versões de thumbs por imagem
- Campos vazios duplicados
- HTML formatado de payment options
- Metadata interna não-relevante

Tudo isso pesa nos tokens enviados pra LLM. Mayuí: cada produto Tray vinha em ~10-15 KB. 20 produtos = 200-300 KB → 80k+ tokens.

### Como evitar

Code node de slim em todo backend. Padrão:

```js
const body = $input.first().json;
if (body && body.code && body.code >= 400) {
  return [{ json: { error: body.causes ? body.causes.join("; ") : body.name || "API error", code: body.code } }];
}
// ... extrair só campos essenciais e limpar HTML
return [{ json: { ... } }];
```

Veja exemplos em `slim_response_patterns.md` (próxima iteração da skill).

Resultado típico: 85% redução de payload.

---

## 10. Endpoints "documentados" podem não existir

### O que acontece

Docs Readme.io/GitBook frequentemente listam endpoints no menu lateral que **não existem na API real**. Exemplos vistos na Martz (Mayuí):
- `/v1/categories` → 404 `E_ROUTE_NOT_FOUND`
- `/v1/carts/{id}` → 404
- `/v1/utils/health` → 404

A doc lista, mas a API retorna `E_ROUTE_NOT_FOUND`. Pode ser endpoint planejado mas não deployed, ou doc copy-paste de outro produto.

### Como evitar

**SEMPRE faça uma chamada de teste real** antes de incluir uma tool no MCP. Use o workflow `Smoke Test (manual)` pra cada endpoint:

```bash
curl -X GET -H "<auth>" https://<api>/v1/<endpoint>
```

Se retornar 404, NÃO crie tool pra esse endpoint. Anote como pendência no relatório final.

---

## 11. Endpoints podem confundir path-params com query-params

### O que acontece

Convencionalmente:
- `/resource/{id}` → ID no path
- `/resource?id={id}` → ID em query

Algumas APIs usam padrão diferente:
- Tray stocks: NÃO é `/products/stocks/{id}` (testei, 401). NÃO é `/products/{id}/stocks` (404). Acabou que stock vem **embutido** em `/products/variants/{variant_id}.available`.

### Como evitar

Quando doc é ambígua, teste todos os formatos comuns:
1. `/resource/{id}/subresource`
2. `/resource/subresource/{id}`
3. `/subresource?resource_id={id}`
4. Embutido no objeto pai

Marque no relatório qual variação a API real aceita.

---

## 12. NexTags JSON output — campos com markdown quebram

### O que acontece

NexTags renderiza `messages[].message.text` como texto puro no WhatsApp. Markdown vira lixo visível:
- `**negrito**` → renderiza literal `**negrito**`
- `# título` → renderiza `# título`
- ``` `código` ``` → renderiza ``` `código` ```
- `[link](url)` → renderiza inteiro

### Como evitar

Regra explícita no prompt do agente: NUNCA usar markdown nos campos `text`, `title`, `subtitle` do JSON. Para ênfase, reescreva a frase ou use mensagens separadas.

---

## 13. Carrossel exige no mínimo 2 elements

### O que acontece

`template_type: "generic"` com 1 element no array `elements[]` resulta em renderização quebrada no WhatsApp (depende do canal).

### Como evitar

Regra no prompt: se só há 1 produto pra mostrar, use `texto + attachment image`. Carrossel só pra 2+ produtos.

```json
// ❌ Errado: carrossel com 1 item
{"elements": [{"title": "Único produto"...}]}

// ✅ Certo: texto + imagem
{"messages": [
  {"message": {"text": "Olha que linda!"}},
  {"message": {"attachment": {"type": "image", "payload": {"url": "..."}}}}
]}
```

---

## 14. Botões em NexTags só com `web_url`

### O que acontece

Botões `postback` (quick reply tipo Sim/Não) **não funcionam** no NexTags. Só `type: "web_url"`.

### Como evitar

Quando IA quer perguntar Sim/Não, faz em texto livre, não em botão. Botões só pra abrir páginas externas (produto, checkout, rastreio).

```json
// ❌ Errado: botão de menu
{"buttons": [{"type": "postback", "title": "Sim", "payload": "YES"}]}

// ✅ Certo: pergunta em texto
{"messages": [{"message": {"text": "Confirma? Responde sim ou não"}}]}

// ✅ Certo: botão web_url
{"buttons": [{"type": "web_url", "url": "https://...", "title": "Ver e comprar"}]}
```

---

## 15. Ações proibidas em NexTags (não use no JSON)

### O que acontece

NexTags **rejeita** ações:
- `transfer_conversation_to`
- `assign_conversation`
- `unassign_conversation`

Use `send_flow` com `flow_id` pré-configurado na plataforma:

```json
{"actions": [{"action": "send_flow", "flow_id": "<FLOW_ID_SAC>"}]}
```

### Como evitar

Sempre `send_flow`. Brief do cliente deve listar os flow_ids disponíveis.

---

---

## 16. MCP Trigger e Webhook Trigger compartilham namespace de path

### O que acontece

`@n8n/n8n-nodes-langchain.mcpTrigger` (path `<slug>`, exposto em `/mcp/<slug>`) e `n8n-nodes-base.webhook` (path `<slug>`, exposto em `/webhook/<slug>`) **NÃO podem usar a mesma string de path no mesmo n8n**, mesmo que os prefixos de URL pareçam diferentes.

Internamente o n8n registra ambos no mesmo "webhook namespace". Tentar ativar o segundo dá erro:

```
Conflicting Webhook Path
A webhook trigger 'X' in the workflow 'Y' uses a conflicting URL path,
so this workflow cannot be activated.
URL: https://<host>/webhook/<slug>
```

Bug típico: cliente novo, slug `acme-magento`. MCP em `/mcp/acme-magento` + Webhook receiver em `/webhook/acme-magento` → conflito.

### Como evitar

Path do webhook receiver **diferente** do path do MCP. Convenção sugerida:

| Trigger | Path | URL final |
|---|---|---|
| MCP | `<slug>` | `/mcp/<slug>` |
| Webhook | `<slug>-webhook` | `/webhook/<slug>-webhook` |

Ex: MCP `anagrow-appmax` + Webhook `anagrow-appmax-webhook`. URLs ficam `/mcp/anagrow-appmax` e `/webhook/anagrow-appmax-webhook`.

Se houver mais de 1 webhook no mesmo cliente, sufixe com a função: `anagrow-appmax-webhook`, `anagrow-appmax-chargeback`, `anagrow-shopify-cart-abandono`, etc.

### Como detectar o bug se aparecer

Mensagem literal "Conflicting Webhook Path" ao tentar ativar workflow. Ou erro silencioso no log do n8n. Sempre cheque os paths em workflows do mesmo cliente antes de ativar.

---

## 17. n8n Executions UI esconde tool calls em Streamable HTTP

### O que acontece

Com MCP Server Trigger v2 em modo Streamable HTTP (NexTags), a UI de "Executions" do n8n mostra **só o handshake inicial** (POST `/mcp/<slug>`) como uma execution de 6-36ms com `runData` só do trigger. Os `tools/call` subsequentes trafegam dentro da mesma conexão e **não aparecem como executions separadas**, mesmo com:

```json
"saveDataSuccessExecution": "all",
"saveExecutionProgress": true,
"saveManualExecutions": true
```

ligados. A execução pelo botão "Execute Workflow" (manual) capta tudo porque usa pipeline diferente — por isso dá pra ser enganado pensando "só manual funciona, webhook não".

Isso confunde MUITO no debugging: parece que a tool nunca foi chamada, mas o cliente MCP (LLM no Playground/agent) recebeu o response real da API.

### Como detectar o bug se aparecer

Sintoma: cliente diz "Luna não tá usando as tools" baseado só no que vê na UI do n8n. Confirma se realmente não foi chamada via:

1. **OpenAI Playground response** — procura blocos `mcp_call` com `status: "completed"` no JSON da response. Se tiver, a tool foi chamada.
2. **WhatsApp/produção** — se o agente retorna dado VERIFICÁVEL (preço atual, status de pedido real, código de rastreio de 44 dígitos), e não tem como ele alucinar isso, foi chamada.
3. **Curl direto no endpoint MCP** — devolve o response real, confirma que o caminho funciona.

### Como evitar a confusão

- **Nunca diagnostique "tools não chamadas" só pela UI do n8n** em workflow Streamable HTTP. Sempre confirme pelo cliente.
- Se precisa de auditoria real (compliance, debug profundo), adicione logging customizado **dentro** das tools/backends — Code node escrevendo em Postgres/Sheets/Webhook externo. É a única forma confiável de ter trilha de chamadas em Streamable HTTP.
- Avise o cliente: "a UI de executions do n8n não é trustworthy pra MCP em produção. Pra rastreio, use [logging externo / response do agente]."

### Confirmado em

2026-05-18, debugging Luna/Dolps. Prova: response do Playground tinha bloco completo `mcp_call` com `vtex_get_order_status` retornando JSON real da VTEX, enquanto n8n Executions mostrava 0 executions >100ms no mesmo intervalo.

---

## 18. `optimizeResponse + fieldsToInclude: 'selected'` no httpRequestTool entrega payload cru via MCP

### O que acontece

Em `n8n-nodes-base.httpRequestTool`, mesmo configurando:

```ts
optimizeResponse: true,
dataField: 'list',
fieldsToInclude: 'selected',
fields: 'orderId,status,value,items,clientProfileData.firstName,...'
```

Quando o tool é chamado via MCP Server Trigger v2 (Streamable HTTP), o cliente MCP **recebe o JSON cru completo** da API, incluindo TODOS os campos não listados — inclusive arrays profundos com sub-campos (`items[].attachments`, `items[].priceTags`, `items[].additionalInfo.dimension.cubicweight`, `paymentData.transactions[].payments[].connectorResponses`, `billingAddress.geoCoordinates`, etc.).

Já era documentado que `fieldsToInclude=selected` não filtra paths dentro de arrays (`items.X.Y`). Agora está confirmado que **mesmo no top-level a filtragem não chega na LLM via MCP** — o response sai sem filtro real.

### Como evitar

Dois caminhos, conforme o peso do payload:

**Payload leve / agente sabe ignorar via instrução:**
- Mantém `httpRequestTool` direto
- Lista campos lixo EXPLICITAMENTE no `toolDescription` (sintaxe: "USE APENAS X, Y, Z. IGNORE: A, B, C")
- LLM consegue se virar, mas paga em tokens consumidos no input

**Payload pesado / quer slim real:**
- Migra tool de `httpRequestTool` direto pra `toolWorkflow` apontando pra backend dedicado
- Backend faz HTTP request + Code node de slim antes do return
- 1 backend por operação (quirk #2 do `workflowInputs` continua valendo)
- Trade-off: arquitetura mais complexa, mas slim real (80-95% redução de payload)

Pra e-commerce com `items[]` grande (VTEX/Tray/Shopify), recomenda-se o caminho 2.

### Como detectar

Veja o `output` de um `mcp_call` no response do Playground/cliente MCP. Se aparecem campos que você LISTOU pra IGNORE no toolDescription (uniqueId, ean, attachments, etc.), confirmou: a LLM tá recebendo o JSON cru.

### Confirmado em

2026-05-18, debugging Luna/Dolps. `vtex_get_order_status` configurado com `fields="orderId,status,statusDescription,..."` entregou items[] completos com attachments, priceTags, additionalInfo, billingAddress.geoCoordinates pro Playground.

---

## Lista crescente

Quando descobrir novo quirk, adicione aqui com:
- **O que acontece** (sintoma)
- **Como evitar** (correção)
- **Como detectar** (como diagnosticar se aparecer)

Esse arquivo é o principal blocker de bug repetido. Mantenha atualizado.

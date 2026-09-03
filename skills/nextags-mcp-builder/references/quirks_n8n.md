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

## 19. `executeWorkflow` com `defineBelow` — valores estáticos chegam como `null` no sub-workflow

### O que acontece

Ao usar `n8n-nodes-base.executeWorkflow` v1.1 com `mappingMode: "defineBelow"`, valores literais no `value` object chegam como `null` no `executeWorkflowTrigger` v1.1 do workflow chamado. Isso vale tanto para strings estáticas quanto para `expr("{{ 'string_literal' }}")`.

Exemplo que **NÃO funciona** no smoke test:

```ts
// Smoke test chamando backend via executeWorkflow
workflowInputs: {
  mappingMode: 'defineBelow',
  value: {
    phone: '31983635636',              // ← chega como null
    phone: expr("{{ '31983635636' }}") // ← também chega como null
  }
}
```

No backend, `$('Entrada').item.json.phone` → `null`.

**ATENÇÃO**: Isso afeta o smoke test (executeWorkflow com valores estáticos). Ver também Quirk #20 — `toolWorkflow` + `$fromAI()` em `defineBelow` também falha com clientes MCP externos (OpenAI, NexTags).

### Como evitar

**Para smoke tests e testes manuais**: use `passThrough` + Set node anterior:

```ts
// Set node define todos os valores de teste
const setTestData = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Dados do Teste',
    parameters: {
      mode: 'manual',
      assignments: { assignments: [
        { id: 'a1', name: 'phone', value: '31983635636', type: 'string' },
        { id: 'a2', name: 'order_id', value: 'uuid-aqui', type: 'string' }
      ]}
    }
  }
});

// executeWorkflow usa passThrough — o Set node's output flui direto pro backend
const teste = node({
  type: 'n8n-nodes-base.executeWorkflow',
  version: 1.1,
  config: {
    name: 'Teste: buscar_cliente',
    parameters: {
      source: 'database',
      workflowId: { __rl: true, mode: 'id', value: 'WORKFLOW_ID' },
      workflowInputs: { mappingMode: 'passThrough' }  // ← KEY: passThrough não o defineBelow
    }
  }
});
```

**Para produção com clientes MCP externos (OpenAI, NexTags)**: use `passThrough` no `toolWorkflow` — ver Quirk #20.

### Como detectar

Sub-execução do backend chamado mostra `{"phone": null}` (ou outro campo como null) na saída do nó `Entrada`, mesmo você tendo passado o valor no executeWorkflow caller.

Consequências visíveis:
- URL com parâmetro vazio: `GET /customers/phone//` → 404
- URL com "null" string: `GET /customers/phone/null` → 422 "not found"
- Erros genéricos "Invalid input" da API

Confirmado em 2026-05-26, debugging smoke test Veuske ZOPPY. `buscar_cupom` recebia `{phone: null}` mesmo com `phone: "31983635636"` no defineBelow. Fix com passThrough + Set node funcionou.

---

## 20. `toolWorkflow` pode não propagar argumentos de clientes MCP externos (depende da versão do n8n)

### O que acontece

`@n8n/n8n-nodes-langchain.toolWorkflow` v2.2 **não entregou os argumentos da tool call ao backend em nenhuma configuração testada** quando o MCP é chamado por cliente externo (NexTags, OpenAI Playground, qualquer cliente HTTP).

> ⚠️ **Não é universal.** A Nalisa registrou em 2026-07-03 as 3 tools do MCP com
> `toolWorkflow` + `$fromAI` (`defineBelow`) **propagando corretamente** naquela instância,
> com `tools/call consultar_pedido` devolvendo dado real. A Verdena, na mesma janela,
> reproduziu a falha. Trate como **dependente de versão/instância**, não como lei: o padrão
> continua sendo `httpRequestTool` (funciona nos dois casos); `toolWorkflow` só depois de
> smoke test por `curl` naquela instância. Nunca decida por dedução.

**Ambos os modos falham:**

```ts
// FALHA 1 — defineBelow + $fromAI()
workflowInputs: {
  mappingMode: 'defineBelow',
  value: { values: [{ name: 'phone', stringValue: "={{ $fromAI('phone', '...') }}" }] }
}
// → backend recebe {"phone": null}

// FALHA 2 — passThrough
workflowInputs: { mappingMode: 'passThrough' }
// → backend recebe {"phone": null} (ou {"input": null})
// o executeWorkflowTrigger cria campos nulos a partir do schema declarado
// nenhum argumento da tool call chega no item JSON do backend
```

### Por quê

O MCP trigger v2 (Streamable HTTP) não injeta os argumentos da `tools/call` no item JSON que o `toolWorkflow` recebe. O `$fromAI()` só funciona dentro do contexto de um AI agent nativo n8n (Claude/OpenAI interno). Para clientes externos, nenhum contexto de resolução existe.

Com `passThrough`, o item passado ao backend é vazio (`{}`). O `executeWorkflowTrigger` v1.1 com schema declarado (`workflowInputs.values`) cria campos nulos para cada input declarado — nunca popula com dados reais da tool call.

### Diagnóstico

```json
// Execução do backend (modo integrated) mostra em "Entrada":
{"phone": null}
// parentExecution aponta pro MCP workflow
// contextData: {} — vazio, sem argumentos da tool call
```

Debug confirmatório: trocar schema para `[{name: 'input'}]` e chamar com qualquer argumento → resultado sempre `{"input": null}`. Nem `{"arguments": {"input": "..."}}` funciona.

### Fix definitivo — use `httpRequestTool` diretamente no MCP (sem backend, sem credential)

**Padrão preferido (Naah Store / Veuske Shopify):** token hardcoded em `headerParameters`. Sem credencial vinculada — elimina toda a fricção de "credential not assigned", "wrong credential auto-linked", "credential value outdated".

```ts
const minhaFerramenta = tool({
  type: 'n8n-nodes-base.httpRequestTool',  // ← NÃO toolWorkflow
  version: 4.4,
  config: {
    name: 'buscar_cliente',
    parameters: {
      toolDescription: '...',
      method: 'GET',
      url: 'https://veuske.myshopify.com/admin/api/2025-01/customers/search.json',
      authentication: 'none',          // ← sem credential
      sendHeaders: true,
      headerParameters: { parameters: [
        { name: 'X-Shopify-Access-Token', value: 'shpat_...' },  // ← token literal
        { name: 'Accept', value: 'application/json' },
      ]},
      sendQuery: true,
      queryParameters: { parameters: [
        // $fromAI() FUNCIONA aqui para clientes externos
        { name: 'query', value: "=phone:{{ $fromAI('phone', 'Telefone') }}" }
      ]}
    }
  }
});
```

`$fromAI()` em parâmetros de `httpRequestTool` resolve corretamente para clientes MCP externos. É o mesmo mecanismo que o ZOPPY usa.

**Quando usar credential em vez de hardcoded:**
- Token expira/rotaciona com frequência (OAuth com refresh) — aí faz sentido a indireção
- Mesma credencial reusada em 10+ workflows — manter sync vale a centralização
- Auditoria/compliance exige que tokens estejam isolados em credential store

Caso contrário, hardcoded é mais robusto. Ver Quirk #22.

### Quando `toolWorkflow` ainda é válido

Apenas quando o MCP é consumido por um **AI agent interno do n8n** (node `@n8n/n8n-nodes-langchain.agent`). Nesses casos `$fromAI()` funciona porque existe contexto LLM nativo.

### Limitação do `httpRequestTool`

Cada `httpRequestTool` faz **1 HTTP request**. Para operações multi-step (ex: buscar customer_id → listar pedidos), divida em 2 tools separadas. O LLM orquestra a sequência naturalmente.

```
buscar_cliente(phone) → retorna customer_id
listar_pedidos(customer_id) → retorna orders
```

Isso espelha a arquitetura do ZOPPY MCP (5 tools unitárias), que funciona em produção na NexTags.

### Confirmado em

2026-05-27, Veuske Shopify MCP:
- `toolWorkflow` + `defineBelow` + `$fromAI()` → `{phone: null}` ✗
- `toolWorkflow` + `passThrough` → `{phone: null}` (debug com schema `[{name:'input'}]` → `{input: null}`) ✗
- `httpRequestTool` com `$fromAI('phone')` no query param → **FUNCIONA** ✓

2026-05-26, Veuske ZOPPY MCP:
- `toolWorkflow` + `defineBelow` + `$fromAI()` → `{phone: null}` ✗ (execution #21433253)
- `httpRequestTool` direto → funciona em produção na NexTags ✓

---

## 21. HTTP Request v4.4 — como enviar JSON array (ou string JSON) como body

### O que acontece

Enviar um array JSON como body (ex: `[{shop: "...", access_token: "..."}]`) via HTTP Request v4.4 é confuso porque o SDK tem parâmetros conflitantes dependendo do `contentType`.

Tentativas que **NÃO funcionam** (validator retorna `valid: true` mas com warnings):
```ts
// ❌ Falha: body só permitido com contentType='raw' + specifyBody='string'
contentType: 'json',
specifyBody: 'string',
body: expr('={{ $json.rowBody }}')

// ❌ Falha: specifyBody não permitido com contentType='raw'
contentType: 'raw',
specifyBody: expr('"string"'),
body: expr('={{ $json.rowBody }}')

// ❌ Falha: body não permitido sem specifyBody quando contentType='raw'
contentType: 'raw',
rawContentType: 'application/json',
body: expr('={{ $json.rowBody }}')
```

### Fix — `jsonParameters: true` + `bodyParametersJson`

```ts
// ✅ Funciona: 0 warnings, valid: true
sendBody: true,
contentType: 'json',
jsonParameters: true,
bodyParametersJson: expr('={{ $json.rowBody }}'),
// rowBody = JSON.stringify([row]) — string como "[{...}]"
```

Com `jsonParameters: true`, o campo `bodyParametersJson` aceita uma expressão que retorna uma string JSON válida (objeto ou array). O n8n serializa diretamente como body com Content-Type: application/json.

### Onde usar

Sempre que precisar enviar um JSON body que:
- É um array (não pode ser representado como key-value pairs)
- Vem de uma expressão dinâmica
- É uma string JSON já serializada (resultado de `JSON.stringify(...)`)

### Confirmado em

2026-05-27, Shopify OAuth Callback — endpoint `POST /api/v1/data-tables/{id}/rows` da n8n REST API exige body `[{shop, access_token, scope, installed_at}]`. Resolvido com `jsonParameters: true` + `bodyParametersJson: expr('={{ $json.rowBody }}')` onde `rowBody = JSON.stringify([row])`.

---

## 22. Token hardcoded em `headerParameters` > credential `httpHeaderAuth` (padrão Naah Store)

### O que acontece

Configurar `httpRequestTool` com `authentication: 'genericCredentialType'` + `newCredential('X')` no SDK abre 3 portas pra coisa quebrar:

1. **`autoAssignedCredentials: []`** — n8n quase nunca auto-vincula a credencial correta após `update_workflow`. User precisa abrir UI e linkar manualmente. Toda vez que o workflow é atualizado, repete.
2. **Credencial errada auto-linkada** (Quirk #3) — n8n às vezes pega outra credencial httpHeaderAuth qualquer do projeto.
3. **Valor da credencial desatualizado** — credencial foi criada com token X há 3 sessions; user e dev acham que está atualizada, mas continua com X. Erros de auth viram pesadelo de debug.

### Como evitar

Quando o token/key é **estático** (não OAuth com refresh), bote direto em `headerParameters`:

```ts
{
  authentication: 'none',
  sendHeaders: true,
  headerParameters: { parameters: [
    { name: 'X-Shopify-Access-Token', value: 'shpat_abc123...' },
    { name: 'Accept', value: 'application/json' },
  ]},
  ...
}
```

Vantagens:
- 0 dependência de credencial UI — workflow funciona imediatamente após update
- Token visível direto no código (auditável em git diff)
- Sem ambiguidade sobre "qual credencial está vinculada agora"
- Re-runs de update_workflow não quebram nada

### Quando ainda usar credential

- **OAuth com refresh** — token muda automaticamente, precisa indireção
- **Múltiplos workflows compartilham mesma key** — alterar em 1 lugar > alterar em N
- **Compliance / auditoria** — empresa exige que secrets fiquem em credential store, não em workflow JSON

### Padrão de mercado: Naah Store (Shopify)

```ts
// MCP Shopify Naah Store — funciona em produção há meses
headerParameters: { parameters: [
  { name: 'X-Shopify-Access-Token', value: 'shpat_<32-hex-tokens-vão-aqui-em-prod>' },
  { name: 'Accept', value: 'application/json' }
]}
```

Adotado também em Veuske Shopify MCP após bug de credencial desatualizada (atkn_/shpat_ confusion + valor antigo persistido).

### Confirmado em

2026-05-27, Veuske Shopify. Refactor de credential httpHeaderAuth → hardcoded eliminou 3 sessions de debug travado em "Invalid API key or access token". Padrão validado tb na Naah Store.

---

## 23. Shopify removeu o "token estático fácil" — apps novos exigem OAuth flow

### O que acontece

Shopify mudou o processo de criação de apps custom em 2026. Apps **novos** criados via Dev Dashboard ou Partner Dashboard:

- **NÃO mostram** o `shpat_` access token diretamente
- Mostram apenas: `Client ID`, `Client Secret` (`shpss_...`), scopes e install link
- Pra obter o `shpat_`, é **obrigatório completar o OAuth flow** (instalar o app na loja)

Apps antigos (Custom Apps legacy criados antes) ainda têm `shpat_` revelado no admin → API credentials → "Reveal token once".

### Confusão comum

`shpss_` aparece na config do app e é fácil confundir com token. **NÃO é.** É o `client_secret` — usado APENAS no fluxo OAuth pra trocar `code` por `access_token`. Nunca use direto como `X-Shopify-Access-Token`.

Formatos:
| Prefixo | O que é | Onde usar |
|---|---|---|
| `shpat_` | Admin API access token | Header `X-Shopify-Access-Token` ← este é o que queremos |
| `shpss_` | Client secret do app | Body do POST `/admin/oauth/access_token` (parâmetro `client_secret`) |
| `shppa_` | Partner Access Token | API do Partner Dashboard, não API da loja |
| `atkn_` | ❌ não existe | Não é formato Shopify válido |

### Como obter o shpat_ (apps novos)

Precisa montar OAuth flow no n8n. 2 workflows webhook:

**1. Página de Instalação** (`/webhook/shopify` ou similar)
   - Recebe `?shop=loja.myshopify.com&host=...`
   - Gera URL `https://{shop}/admin/oauth/authorize?client_id=...&scope=...&redirect_uri=...&state=...`
   - Responde HTML com redirect JS (top-level via App Bridge se possível)

**2. OAuth Callback** (`/webhook/shopify-callback`)
   - Recebe `?shop=...&code=...&state=...`
   - POST `https://{shop}/admin/oauth/access_token` com body:
     - `client_id` (hex 32 chars)
     - `client_secret` (`shpss_...`)
     - `code` (do query string)
   - Resposta tem `{access_token: "shpat_...", scope: "..."}`
   - Salva na data table + responde HTML com token visível

Template completo: ver Veuske `a2srjFLrwL8RqQey` e `kdgW81VzXjm714xY` na pasta `Veuske` do n8n.

### Pré-requisitos no Partner Dashboard

- App criado em **partners.shopify.com → Apps → Create app**
- **Configuration → URLs**:
  - **App URL:** `https://nextags.app.br/webhook/<cliente>-shopify-install`
  - **Allowed redirection URL(s):** `https://nextags.app.br/webhook/<cliente>-shopify-callback`
- **API access → Admin API → Scopes:** `read_orders, read_customers, read_products, read_inventory` (ou o que precisar)
- Loja precisa estar listada em **Test stores** ou ser **Development store**

### Fluxo de uso

1. User abre no browser: `https://nextags.app.br/webhook/<cliente>-shopify-install?shop=loja.myshopify.com`
2. Redireciona pro `https://loja.myshopify.com/admin/oauth/authorize?...`
3. User loga (se precisar) e clica **Install app**
4. Shopify redireciona pro callback com `?code=...`
5. Callback troca code por `shpat_`, salva, exibe na tela
6. Dev pega o `shpat_` e cola hardcoded nos headerParameters do MCP (Quirk #22)

### Confirmado em

2026-05-27, Veuske Shopify. Tentamos por horas usar `atkn_...` (que não é formato válido) achando que era o token. OAuth flow funcionou e retornou `shpat_<32-hex>` (token armazenado na data table `Shopify Tokens` do projeto, não em docs).

---

## 24. `jsonParameters + bodyParametersJson` double-encoda o body — use `specifyBody: 'json'` + `jsonBody`

### O que acontece

Em `n8n-nodes-base.httpRequest` v4.4, ao usar:
```ts
sendBody: true,
contentType: 'json',
jsonParameters: true,
bodyParametersJson: expr('={{ $json.payloadJson }}')
```
onde `$json.payloadJson` é uma string JSON (ex: `'{"phone":"+5511..."}'`), o n8n **double-encoda** o body. A API recebe uma string JSON escapada em vez de um objeto JSON, e não consegue ler os campos corretamente.

Sintoma típico: API retorna erro de campo inválido (ex: `"Invalid phone number"`) mesmo com valor correto, porque o body chegou como `"{\\"phone\\":\\"+5511...\\"}"` (string) em vez de `{"phone":"+5511..."}` (objeto).

### Como evitar

Use `specifyBody: 'json'` + `jsonBody` em vez de `jsonParameters + bodyParametersJson`:

```ts
// ✅ Funciona — padrão Casa Marquez / NexTags
sendBody: true,
contentType: 'json',
specifyBody: 'json',
jsonBody: expr('={{ $json.nextagsPayload }}')
// nextagsPayload = JSON.stringify({phone, email, first_name, ...})
```

No Code node que prepara o payload:
```js
return [{ json: { nextagsPayload: JSON.stringify({ phone, email, actions }) } }];
```

No HTTP Request node:
```ts
specifyBody: 'json',
jsonBody: '={{ $json.nextagsPayload }}'
```

### Quando `jsonParameters + bodyParametersJson` funciona

Funciona para arrays (ex: `[{shop, access_token}]`) onde o body É um array — ver Quirk #21. Mas para objetos simples com campos de API, use `specifyBody: 'json'`.

### Confirmado em

2026-05-28, Verdena MARTZ → NexTags. API retornava `"Invalid phone number"` com body correto. Fix: trocar para `specifyBody: 'json'` + `jsonBody`. Passou a retornar `{success: true, contact_created: true}` para 2 contatos novos + 1 existente no mesmo teste.

---

## 25. NexTags `/api/contacts` — formato correto de telefone brasileiro

### O que acontece

A NexTags usa um normalizador específico para telefones brasileiros que remove o nono dígito (9) para DDDs fora da região SE (11–29). Enviar o número "cru" com 9 dígitos causa `"Invalid phone number"` mesmo para números válidos.

### Como evitar

Use a função `fone()` antes de enviar qualquer telefone:

```js
function fone(t) {
  if (!t) return '';
  let d = String(t).replace(/\D/g, '');
  if (!d.startsWith('55')) d = '55' + d;
  const ddd = d.slice(2, 4), dddN = parseInt(ddd, 10);
  let local = d.slice(4);
  if (local.length < 8) return '';
  if (dddN >= 11 && dddN <= 29) {
    if (/^[2345]/.test(local)) { if (local.length === 9 && local[0]==='9') local = local.slice(1); local = local.slice(-8); }
    else if (local.length === 8) local = '9' + local;
  } else { if (local.length === 9 && local[0]==='9') local = local.slice(1); local = local.slice(-8); }
  return '+55' + ddd + local;
}

// Uso: fone(phone_country_code + phone)
// Ex: fone('55' + '92990000000') → '+559290000000' (DDD 92, fora de SE)
// Ex: fone('55' + '22990000000') → '+5522990000000' (DDD 22, dentro de SE)
```

### Detalhes

- DDDs 11–29 (SP, RJ, ES, MG): números móveis mantêm 9 dígitos (prefixo 9 ativo)
- DDDs 30+ (restante do Brasil): remove o 9 inicial → 8 dígitos locais
- NexTags retorna `"Invalid phone number"` se receber 9 dígitos locais para DDD 30+
- Resultado final sempre: `+55DDD8dígitos` ou `+55DDD9dígitos` dependendo do DDD

### Confirmado em

2026-05-28, Verdena MARTZ. DDD 92 (Manaus) com phone `92990000000` → `fone()` produz `+559290000000` (8 dígitos locais) → `contact_created: true`. Sem `fone()`, `+5592990000000` (9 dígitos) → `"Invalid phone number"`.

---

## 26. NexTags `/api/contacts` — tags e CUFs via `actions[]`, não campos diretos

### O que acontece

A NexTags rejeita corpos com `tags: [...]` ou `custom_fields: {...}` diretos. Esses dados precisam ir dentro de um array `actions[]`.

### Como evitar

```json
{
  "phone": "+5511999999999",
  "email": "...",
  "first_name": "...",
  "last_name": "...",
  "actions": [
    { "action": "add_tag", "tag_name": "verdena" },
    { "action": "set_field_value", "field_name": "martz_order_id", "value": "uuid" },
    { "action": "send_flow", "flow_id": 12345 }
  ]
}
```

### Confirmado em

2026-05-28, Verdena MARTZ. Swagger `POST /api/contacts` mostra esse schema. Padrão também usado em produção no workflow Casa Marquez (ID: TeoaE5eh2HInESNJ).

---

## 27. Flow router NexTags que reseta `setor_agente` causa loop de transferência

### O que acontece

Cliente entra → flow de entrada/router NexTags força `setor_agente=<agente_default>` em toda mensagem. Quando o agente IA tenta transferir (`set_field_value setor_agente=humano` + `send_flow <router>`), o router **executa de novo** e RESETA `setor_agente` pro default ao invés de respeitar o valor "humano" que o agente acabou de setar.

Resultado: o mesmo cliente recebe a mesma mensagem do agente IA várias vezes ("vou direcionar pro time", "vou confirmar com o time", "perfeito, vou te direcionar...") porque cada vez que o agente tenta transferir, o flow ressuscita ele.

### Como detectar

Sintoma na produção:
- Cliente envia 1 mensagem
- Agente envia 5-15 balões de mensagens parecidas no WhatsApp
- Logs mostram alternância repetida: `setor_agente=humano` → `setor_agente=PEDRO` → `setor_agente=humano` → ...
- Cada `resposta_ia` do agente contém `set_field_value setor_agente=humano + send_flow <router>` repetido

Confirmado em produção Veuske 2026-06-04 — Pedro respondeu 7+ vezes pra mesma mensagem do cliente.

### Causas comuns no flow

1. **Flow de entrada sem condicional** — força default no início de toda mensagem, ignora estado prévio
2. **Router com case mismatch** — `setor_agente="humano"` (lowercase) não bate com `if setor_agente == "Humano"` (capitalize), cai no default
3. **Router com convenção mista** — agente seta `humano`, router escreve `PEDRO` ao rotear, comparações ficam inconsistentes

### Fix no NexTags

1. **Flow de entrada com guard**:
   ```
   IF setor_agente IS NULL OR EMPTY:
     set setor_agente = "<default>"  // só na primeira vez
   ELSE:
     keep current value             // preserva transferências
   ```

2. **Router (`send_flow` destino) precisa de branch "humano"**:
   ```
   IF setor_agente == "humano":
     atribuir fila humana, parar
   ELIF setor_agente == "vendas":
     rotear pra Pedro
   ELIF setor_agente == "sac":
     rotear pra Sophia
   DEFAULT (não bateu nada):
     atribuir fila humana, parar    // NÃO setar agente IA aqui
   ```

3. **Padronizar case** — escolha lowercase (`vendas`, `sac`, `humano`) e use em TODOS os pontos:
   - Prompts dos agentes
   - Flow de entrada
   - Router
   - Default values
   - Field validators do CUF

### Mitigação no prompt (defesa em profundidade)

Mesmo com flow correto, adicione no prompt de TODO agente uma cláusula anti-loop:

```
🛑 ANTI-LOOP — se você já emitiu mensagem do tipo "vou direcionar"
nas últimas 2-3 respostas: NÃO TRANSFIRA DE NOVO. Loop indica bug no
roteamento NexTags. Responda 1 mensagem curta admitindo limitação e
PARE de responder até o cliente mandar mensagem nova.
```

Sem isso, o agente continua tentando transferir mesmo o flow bagunçado, e o cliente vê todas as tentativas.

### Confirmado em

2026-06-04, Veuske Pedro. Pedro tentou transferir 7 vezes pra mesma mensagem ("quero o link pra comprar VK1000 + Couro & Tabaco" — produto que não existe como SKU único). Flow router resetava `setor_agente=PEDRO` toda vez que Pedro setava `humano`. Cliente recebeu 7+ balões idênticos no WhatsApp.

---

## 28. Shopify search casa por TOKEN inteiro — `title:*vk luxe*` e `title:*Luxe*` dão 0

### O que acontece

A query `title:*{termo}*` (usada nas tools de busca de produto Shopify) casa quando o termo é um **token inteiro** do título, mas FALHA com:
- **Espaço no meio:** `title:*vk luxe*` → 0, mesmo o produto existindo como "...VKLUXE". O espaço vira separador de termos.
- **Substring dentro de token:** `title:*Luxe*` → 0, porque "Luxe" está DENTRO do token "VKLUXE" e o índice não acha substring mid-token.
- **Multi-palavra vira OR amplo:** `title:*refil bamboo*` → traz TODOS os refis (qualquer um com "refil" OU "bamboo"), o produto certo se perde.

`title:*VK1000*` funciona porque "VK1000" é o token inteiro. Por isso VK1000 funcionava e VKLUXE não — confundiu o debug por horas no caso Veuske.

### Como evitar

Não dá pra consertar 100% na query (full-text plain `{termo}` resolve VKLUXE mas perde precisão em fragrância). Conserte na **descrição da tool** + prompt, instruindo o agente a montar o termo certo:

- **Modelos VK:** cole o código SEM espaço/hífen. "vk luxe" → buscar `VKLUXE`; "vk 1000" → `VK1000`.
- **Fragrâncias:** busque UMA palavra distintiva do nome, nunca "refil X". "refil bamboo" → `bamboo`; "refil couro e tabaco" → `couro tabaco`.

### Como detectar

Cliente pede produto que existe → tool volta `edges: []` → agente trava ("vou confirmar a referência") ou transfere. Teste a query direto no Shopify GraphQL com e sem espaço pra confirmar.

### Confirmado em

2026-06-11, Veuske. "VKLUXE" (uma palavra no título) não achava com "vk luxe"/"Luxe". Corrigido via descrição da tool + seção COMO BUSCAR no prompt. Ver `no_hardcode_with_tools.md`.

---

## 29. `raw.githubusercontent.com` serve `.mp4` como `application/octet-stream` — WhatsApp rejeita

### O que acontece

Ao usar GitHub como banco de mídia (ver `mcp_github_repo_pattern.md`), servir o arquivo direto de `raw.githubusercontent.com/<owner>/<repo>/main/<path>` entrega o Content-Type genérico `application/octet-stream` para binários (`.mp4`, `.ogg`, etc.), independente da extensão real. O WhatsApp rejeita vídeo entregue com esse Content-Type — o anexo não abre ou a mensagem falha.

### Como evitar

Nunca usar `raw.githubusercontent.com` para servir mídia que vai pro WhatsApp. Ler pelo jsDelivr:

```
https://cdn.jsdelivr.net/gh/<owner>/<repo>@main/<path>
```

jsDelivr serve o Content-Type correto (`video/mp4`, `image/jpeg`, `audio/ogg`) a partir do mesmo repositório GitHub, sem mudar nada no conteúdo.

### Confirmado em

Medido em 2026-08-31. Documentado na sticky note de produção do Poé Backend Buscar Mídia (`kyLZitHeBz7PXXwp`): *"O catálogo é lido a cada chamada via cdn.jsdelivr.net — NUNCA via raw.githubusercontent, que serve .mp4 como application/octet-stream e faz o WhatsApp rejeitar o vídeo."*

---

## 30. `toolHttpRequest` + `placeholderDefinitions` colapsa o schema da tool em `{input}` — nunca dispara

### O que acontece

Declarar os parâmetros de uma tool MCP usando `@n8n/n8n-nodes-langchain.toolHttpRequest` com `placeholderDefinitions` (em vez de `n8n-nodes-base.httpRequestTool` com `$fromAI(...)` por parâmetro) faz o n8n colapsar o schema JSON exposto ao cliente MCP externo (NexTags) num único campo genérico `{input}` (string). O cliente MCP não consegue mapear os parâmetros reais — a tool nunca dispara com os argumentos corretos em produção.

### Como evitar

Usar sempre `n8n-nodes-base.httpRequestTool` v4.4/v4.5 com `$fromAI(...)` diretamente em cada parâmetro (query/header/body). **Nunca** `toolHttpRequest` + `placeholderDefinitions` para tool consumida por cliente MCP externo.

### Confirmado em

Evidência Poé (MCP `lk0lpDShxXFGia7D`) — tool configurada com `toolHttpRequest` + `placeholderDefinitions` nunca disparava corretamente contra o backend; migrada pra `httpRequestTool` + `$fromAI`.

---

## 31. URL pública do próprio n8n dá connection refused quando chamada de DENTRO do n8n

### O que acontece

Um workflow n8n (tipicamente uma tool MCP no padrão "tool → backend interno") que chama a URL PÚBLICA do próprio n8n (`https://nextags.app.br/webhook/...`) pra acionar outro workflow recebe connection refused / timeout. A URL pública passa por proxy/túnel externo e não permite a instância chamar a si mesma por esse caminho.

### Como evitar

Chamar o backend pela URL INTERNA, resolvida dentro da rede do próprio n8n:

```
http://n8n:5678/webhook/<path>
```

Só usar a URL pública (`nextags.app.br/webhook/...`) quando o CHAMADOR é externo (o NexTags em si, ou serviço fora da rede do n8n).

### Confirmado em

Padrão de produção Cantarola Backend — a tool MCP chama `http://n8n:5678/webhook/cantarola-*` (URL interna); a URL pública é reservada pros backends expostos diretamente ao mundo (ex: Poé, Meiskin `montar-carrinho`).

---

## 32. Dedup gravado ANTES do sucesso marca o cliente como "notificado" pra sempre

### O que acontece

Se o node de dedup (Data Table upsert/insert) roda em paralelo com a chamada à NexTags, ou antes dela confirmar sucesso, uma falha transitória (token placeholder, 401, instabilidade) grava o registro como "já notificado" mesmo a mensagem nunca tendo saído. Corrigir a causa da falha depois não resolve — o dedup já bloqueia qualquer reenvio, e o cliente real nunca recebe a notificação.

### Como evitar

Sempre nesta ordem: `Notificar NexTags (onError: continueErrorOutput)` → `IF sucesso?` → **só no ramo de sucesso** grava a Data Table de dedup.

### Confirmado em

Nordmann Meling Webhook Pedidos v3 (`ln7ZTWGwTyV2KVRQ`), corrigindo bug da v2. Meiskin PIX Expirado v2 (`bvR8NeB5e4BdOzyD`): a 1ª execução automática rodou com token placeholder, as 51 notificações falharam (401) mas o dedup foi gravado do mesmo jeito — os 51 clientes reais jamais seriam notificados ao colocar o token real. Tabela de dedup recriada limpa após o fix.

---

## 33. BW Commerce sempre responde HTTP 200 (mesmo em erro) — envelope `{registros, erros}` precisa estar na tool description

### O que acontece

A API da BW Commerce nunca retorna status HTTP de erro (4xx/5xx), mesmo com credencial errada ou rota inválida — ela sempre responde `200` com `{registros: [], erros: [...], totalRegistros: N}`. Um backend/tool que trata "200 = sucesso" e ignora `erros[]` confunde falha de credencial com "pedido não existe": o agente diz ao cliente "não encontrei seu pedido" quando na verdade é falha técnica de autenticação.

### Como evitar

Não usar `dataField`/otimização automática nessas tools — o agente precisa VER `erros[]`. A tool description tem que explicar o envelope de forma explícita:

```
FORMATO DA RESPOSTA - leia antes de concluir qualquer coisa:
A BW responde SEMPRE HTTP 200, mesmo quando falha.
- registros vazio E erros vazio  -> o pedido realmente não foi encontrado.
- erros COM conteúdo             -> problema TÉCNICO. NUNCA peça pro cliente
  conferir o número nesse caso: avise que o sistema está instável e transfira.
```

### Confirmado em

Degan MCP (`Wt3SsrCxQ2zwwnOo`), sticky note "Nota" — "ENVELOPE DA BW (a spec está errada nisso)": as 3 tools de BW não usam `dataField` de propósito, exatamente por isso.

---

## 34. `/api/users` é variante legada de `/api/contacts` — não usar em projeto novo

### O que acontece

Existe pelo menos 1 workflow de produção (AliveMed Dispatcher — PIX e Carrinho) chamando `POST https://app.nextagsai.com.br/api/users` em vez do endpoint canônico `POST /api/contacts`, sem documentação de por quê. Parece uma variante/alias mais antigo da mesma funcionalidade — [SEM EVIDÊNCIA DIRETA] de diferença real de schema ou comportamento entre os dois.

### Como evitar

Em projeto novo, sempre `POST /api/contacts`. Se herdar um fluxo de cliente já rodando com `/api/users` e funcionando, **não trocar** sem confirmar com o dono antes — pode não ser 100% equivalente.

### Confirmado em

AliveMed Dispatcher — PIX/Carrinho: único workflow do corpus de 21 lidos usando `/api/users`.

---

## 35. Rate limit NexTags ~100 requisições/60s

### O que acontece

A API NexTags tem um limite de aproximadamente 100 requisições por 60 segundos por conta. Disparo em lote (broadcast, reativação de base, campanha) sem throttle esbarra nesse limite e passa a falhar/perder requisições no meio do lote.

### Como evitar

Padrão "pesca-e-marca": cron de baixa frequência que processa 1 (ou N calculado) registro pendente por vez de uma Data Table e marca como enviado antes do próximo tick, respeitando o rate limit. Ajustar `batchInterval`/`limit` do HTTP Request pra nunca ultrapassar ~100 req/60s — e reavaliar a arquitetura (não só o cron) quando o volume crescer.

### Confirmado em

Privilège Broadcast (`b9IJblHOEurFgj6o`) — sticky note: *"ajustar N e batchInterval do HTTP Request pra respeitar rate limit real da API NexTags (100 req/60s — ver workflow EXPORTAR CONVERSAS v5)."*

---

## Lista crescente

Quando descobrir novo quirk, adicione aqui com:
- **O que acontece** (sintoma)
- **Como evitar** (correção)
---

## 36. Sessão MCP perdida atrás de proxy/CDN — `Server not initialized` e a cascata de alucinação

### O que acontece

O cliente MCP externo lista as tools normalmente, mas toda `tools/call` falha com
`Bad Request: Server not initialized`. O Streamable HTTP do MCP Trigger v2 é **com estado**:
o `initialize` devolve um `Mcp-Session-Id` que precisa voltar em toda requisição seguinte, e
todas elas precisam cair na **mesma instância**. Um proxy ou CDN stateless na frente (ex.:
Cloudflare sem sticky session) rebobina o `initialize` e o `tools/call` chega numa sessão que
não existe.

### Por que é pior do que parece

A falha não vira erro visível pro cliente final: o agente **inventa em cima do vazio**. No caso
documentado (Wazzu), com as tools listadas mas nenhuma chamável, a IA respondeu com nome de
produto "provavelmente" tirado da memória, "consulte no site" no lugar do preço que a tool
traria, e um link de busca genérico em vez do `canonical_url` real. Da perspectiva de quem lê o
log da NexTags, o agente estava conversando normalmente.

### Como detectar

`curl` do fluxo completo, guardando o header entre as chamadas: `initialize` → pegar
`Mcp-Session-Id` → `tools/list` → `tools/call` com o mesmo id. Se `tools/list` passa e
`tools/call` devolve `Server not initialized`, é sessão, não tool. Confirme se há proxy/CDN na
frente do n8n e se ele mantém afinidade de sessão.

---

## 37. Roteador que devolve o JSON da plataforma estoura "Max Flow — Too many blocks"

### O que acontece

Prompt de roteador/classificador escrito com o bloco oficial da NexTags acaba respondendo
`{"messages":[...],"actions":[...]}` em vez da palavra única. A produção devolve
`"Max Flow — Too many blocks sent in a single response"` e o roteamento não acontece.

### Por que é útil saber

Essa mensagem é **sinal diagnóstico**: quem a vê num fluxo de entrada quase sempre tem um
roteador com o formato errado, não um problema de volume de mensagem. Roteador e revalidador
respondem **texto puro, 1 palavra, sem JSON** — ver `campos_canonicos.md` §1 e a exceção de
roteador/revalidador nas regras do `nextags-prompt-fixer`.

(evidência: Hiven, Orquestrador v1.0)

---

- **Como detectar** (como diagnosticar se aparecer)

Esse arquivo é o principal blocker de bug repetido. Mantenha atualizado.

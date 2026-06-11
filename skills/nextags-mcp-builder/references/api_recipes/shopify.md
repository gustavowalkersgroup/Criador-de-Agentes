# Shopify

> Status: 🟢 trabalhada (uso em produção — ANAGROW, Veuske, Naah Store, Casa Marquez, Anagrow)
> Última atualização: 2026-05-27
> Cliente(s) usando: ANAGROW, Veuske, Naah Store, Casa Marquez

## 🔗 Base URL

- **Produção:** `https://{shop}.myshopify.com/admin/api/{version}/`
- **`{shop}`:** subdomínio da loja (descobrir via `https://veuske.myshopify.com` → 200/redirect = válido)
- **`{version}`:** ex `2025-01` (Shopify atualiza versão trimestralmente; mantenha 1 versão estável por cliente)

## 🔐 Autenticação — leia ANTES de pedir credenciais ao cliente

### Formato dos tokens — não confunda

| Prefixo | É | Onde usar | Origem |
|---|---|---|---|
| `shpat_<32-hex>` | **Admin API access token** | Header `X-Shopify-Access-Token` ← este é o que queremos | OAuth flow (apps novos) OU "Reveal token once" (Custom Apps legacy) |
| `shpss_<32-hex>` | **Client secret** do app | Body do `POST /admin/oauth/access_token` (parâmetro `client_secret`) — só no flow OAuth, NÃO no header | Partner Dashboard → app config → API credentials |
| Hex 32 chars sem prefixo | **Client ID / API Key** do app | Body do `POST /admin/oauth/access_token` (parâmetro `client_id`) — só no flow OAuth | Partner Dashboard → app config → API credentials |
| `shppa_<32-hex>` | **Partner Access Token** | Partner Dashboard API (não API da loja) | Partner Dashboard → API access — **NÃO confundir com client_id de app** |
| `atkn_*` | ❌ inexistente | — | Não é formato Shopify válido. Provavelmente confusão com algum identificador interno. |

### Caminho A — Token estático via Custom App legacy (deprecated)

Se o cliente tem uma loja antiga com Custom App criado **antes de jan/2026**:
- Admin Shopify → Apps → seleciona o Custom App → API credentials → **Reveal token once**
- Copia o `shpat_<32-hex>` revelado
- Pula pra "Como cravar no MCP" abaixo

⚠️ Apps novos **não permitem mais** revelar o token desse jeito. Vão pro Caminho B.

### Caminho B — OAuth flow (apps novos, **caminho principal hoje**)

Shopify removeu o "token estático fácil". Pra apps criados em 2026+:

**O que o cliente tem em mãos:**
- `Client ID` — hex 32 chars (sem prefixo). Ex: `d7c1c9ad334cb3d2a4fcc4f095b8a4bc`
- `Client Secret` — `shpss_<32-hex>`. (não colar em docs — sempre buscar do Partner Dashboard direto)
- Scopes ativos no app config (ex: `read_orders, read_customers, read_products, read_inventory`)
- Domínio da loja (ex: `veuske.myshopify.com`)

**O que NÃO tem:** o `shpat_`. A gente vai gerar via OAuth flow.

**Pré-requisitos no Partner Dashboard** antes de tudo:
1. `partners.shopify.com` → Apps → seleciona o app
2. **Configuration → URLs**:
   - **App URL:** `https://nextags.app.br/webhook/<cliente>-shopify-install`
   - **Allowed redirection URL(s):** `https://nextags.app.br/webhook/<cliente>-shopify-callback`
3. **Distribution → Test stores:** adicionar `<cliente>.myshopify.com` (ou a loja precisa ser dev store)

**Setup do flow no n8n** — 2 webhooks:

### Workflow 1: Página de Instalação (`<cliente>-shopify-install`)

Gera o redirect pro `/admin/oauth/authorize` da loja. Template (substitua `{CLIENT_ID}` e `<cliente>`):

```ts
import { workflow, trigger, node } from '@n8n/workflow-sdk';

const webhook = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: { name: 'Webhook GET', position: [0, 0],
    parameters: { httpMethod: 'GET', path: '<cliente>-shopify-install', responseMode: 'responseNode' }
  }
});

const gerarUrl = node({
  type: 'n8n-nodes-base.code', version: 2,
  config: { name: 'Gerar URL OAuth', position: [224, 0],
    parameters: { jsCode: `
const query = ($input.first().json.query) || {};
const shop = query.shop || '';
const host = query.host || '';
if (!shop) return [{ json: { html: '<h2>Erro: shop nao informado</h2>' } }];

const clientId = '{CLIENT_ID}';  // hex 32 chars do Partner Dashboard
const state = Math.random().toString(36).substring(2, 15);
const oauthUrl = 'https://' + shop + '/admin/oauth/authorize' +
  '?client_id=' + clientId +
  '&scope=read_orders%2Cread_customers%2Cread_products%2Cread_inventory' +
  '&redirect_uri=https%3A%2F%2Fnextags.app.br%2Fwebhook%2F<cliente>-shopify-callback' +
  '&state=' + state;

const html = '<!DOCTYPE html><html><head><title>Instalando...</title>' +
  '<script src="https://cdn.shopify.com/shopifycloud/app-bridge.js" data-api-key="' + clientId + '"><\\\\/script>' +
  '</head><body style="font-family:sans-serif;padding:40px;">' +
  '<p>Redirecionando...</p>' +
  '<p>Se nao redirecionar, <a href="' + oauthUrl + '" target="_top">clique aqui</a>.</p>' +
  '<script>window.location.href = "' + oauthUrl + '";<\\\\/script>' +
  '</body></html>';
return [{ json: { html } }];
` } }
});

const responder = node({
  type: 'n8n-nodes-base.respondToWebhook', version: 1.4,
  config: { name: 'Responder', position: [448, 0],
    parameters: { respondWith: 'text', responseBody: '={{ $json.html }}',
      options: { responseHeaders: { entries: [{ name: 'Content-Type', value: 'text/html; charset=utf-8' }] } }
    }
  }
});

export default workflow('<cliente>-shopify-install', '<Cliente> Shopify — Página de Instalação')
  .add(webhook).to(gerarUrl).to(responder);
```

### Workflow 2: OAuth Callback (`<cliente>-shopify-callback`)

Recebe `?code=...&shop=...` do Shopify, troca por `shpat_`, salva, exibe na tela.

Pré-requisito: criar data table `<Cliente> Shopify Tokens` com colunas:
- `shop` (string)
- `access_token` (string)
- `scope` (string)
- `installed_at` (string)

```ts
import { workflow, trigger, node } from '@n8n/workflow-sdk';

const webhook = trigger({
  type: 'n8n-nodes-base.webhook', version: 2.1,
  config: { name: 'Webhook', position: [0, 0],
    parameters: { httpMethod: 'GET', path: '<cliente>-shopify-callback', responseMode: 'responseNode', options: {} }
  }
});

const extrairParams = node({
  type: 'n8n-nodes-base.code', version: 2,
  config: { name: 'Extrair Params', position: [224, 0],
    parameters: { jsCode: `
const q = ($input.first().json.query) || {};
return [{ json: { shop: q.shop || '', code: q.code || '', state: q.state || '' } }];
` } }
});

const trocarCode = node({
  type: 'n8n-nodes-base.httpRequest', version: 4.4,
  config: { name: 'Trocar Code', position: [448, 0],
    parameters: {
      method: 'POST',
      url: '=https://{{ $json.shop }}/admin/oauth/access_token',
      sendBody: true,
      bodyParameters: { parameters: [
        { name: 'client_id', value: '{CLIENT_ID}' },        // hex
        { name: 'client_secret', value: '{CLIENT_SECRET}' }, // shpss_...
        { name: 'code', value: '={{ $json.code }}' }
      ]},
      options: { response: { response: { neverError: true } } }
    }
  }
});

const prepararToken = node({
  type: 'n8n-nodes-base.code', version: 2,
  config: { name: 'Preparar Token', position: [672, 0],
    parameters: { jsCode: `
const shop = $('Extrair Params').first().json.shop;
const accessToken = $input.first().json.access_token || '';
const scope = $input.first().json.scope || '';
const errorMsg = $input.first().json.error_description || $input.first().json.error || '';
return [{ json: { shop, accessToken, scope, installed_at: new Date().toISOString(), errorMsg } }];
` } }
});

const salvarToken = node({
  type: 'n8n-nodes-base.dataTable', version: 1.1,
  config: { name: 'Salvar Token', position: [896, 0],
    parameters: {
      resource: 'row', operation: 'insert',
      dataTableId: { __rl: true, mode: 'id', value: '{DATATABLE_ID}', cachedResultName: '<Cliente> Shopify Tokens' },
      columns: { mappingMode: 'defineBelow', value: {
        shop: '={{ $json.shop }}',
        access_token: '={{ $json.accessToken }}',
        scope: '={{ $json.scope }}',
        installed_at: '={{ $json.installed_at }}'
      }},
      options: {}
    }
  }
});

const buildHtml = node({
  type: 'n8n-nodes-base.code', version: 2,
  config: { name: 'Build HTML', position: [1120, 0],
    parameters: { jsCode: `
const t = $('Preparar Token').first().json;
if (!t.accessToken) {
  return [{ json: { html:
    '<!DOCTYPE html><html><body style="font-family:sans-serif;padding:40px;">' +
    '<h1 style="color:red">Erro na instalacao</h1>' +
    '<p>Loja: ' + t.shop + '</p>' +
    '<p>Detalhe: <code>' + (t.errorMsg || 'token nao retornado') + '</code></p>' +
    '</body></html>'
  } }];
}
return [{ json: { html:
  '<!DOCTYPE html><html><head><title>Instalado!</title>' +
  '<style>body{font-family:sans-serif;padding:40px;max-width:600px;margin:auto;}' +
  'input{width:100%;padding:10px;font-family:monospace;margin-top:8px;}' +
  'button{margin-top:12px;padding:10px 20px;background:#5c6ac4;color:white;border:none;border-radius:4px;cursor:pointer;}</style>' +
  '</head><body>' +
  '<h1>Instalado!</h1><p>Loja: <strong>' + t.shop + '</strong></p>' +
  '<p><strong>Access Token:</strong></p>' +
  '<input type="text" value="' + t.accessToken + '" onclick="this.select()" readonly />' +
  '<br><button onclick="navigator.clipboard.writeText(\\'' + t.accessToken + '\\')">Copiar</button>' +
  '</body></html>'
} }];
` } }
});

const responder = node({
  type: 'n8n-nodes-base.respondToWebhook', version: 1.4,
  config: { name: 'Responder', position: [1344, 0],
    parameters: { respondWith: 'text', responseBody: '={{ $json.html }}',
      options: { responseHeaders: { entries: [{ name: 'Content-Type', value: 'text/html; charset=utf-8' }] } }
    }
  }
});

export default workflow('<cliente>-shopify-callback', '<Cliente> Shopify — OAuth Callback')
  .add(webhook).to(extrairParams).to(trocarCode).to(prepararToken).to(salvarToken).to(buildHtml).to(responder);
```

### Fluxo pra capturar o token

1. Cliente já tem app criado no Partner Dashboard com URLs corretas (ver pré-requisitos)
2. Você abre no browser: `https://nextags.app.br/webhook/<cliente>-shopify-install?shop=<cliente>.myshopify.com`
3. Shopify mostra "Install <Nome do App> on <Loja>?" — clique **Install app**
4. Shopify redireciona pro callback com `?code=...`
5. Callback troca code por `shpat_`, salva na data table, exibe HTML com token num input
6. Copia o `shpat_<32-hex>` e usa nos MCPs

⚠️ **Token é por loja.** Se o cliente tem 2 lojas, cada uma gera um `shpat_` diferente pelo mesmo fluxo (basta mudar o `?shop=`).

## 📦 Como cravar no MCP

Após ter o `shpat_<32-hex>`, **hardcode direto em `headerParameters`** dos `httpRequestTool` (padrão Naah Store / Veuske). Sem credencial — ver Quirks #22.

```ts
const buscarCliente = tool({
  type: 'n8n-nodes-base.httpRequestTool',
  version: 4.4,
  config: {
    name: 'buscar_cliente',
    parameters: {
      toolDescription: 'Busca cliente Shopify pelo telefone...',
      method: 'GET',
      url: 'https://veuske.myshopify.com/admin/api/2025-01/customers/search.json',
      authentication: 'none',
      sendHeaders: true,
      headerParameters: { parameters: [
        { name: 'X-Shopify-Access-Token', value: 'shpat_<32-hex-do-cliente>' },
        { name: 'Accept', value: 'application/json' },
      ]},
      sendQuery: true,
      queryParameters: { parameters: [
        { name: 'query', value: "=phone:{{ $fromAI('phone', 'Telefone, soh digitos com DDD') }}" },
        { name: 'limit', value: '1' },
        { name: 'fields', value: 'id,first_name,last_name,email,phone' },
      ]},
      options: { response: { response: { neverError: true } } },
    }
  }
});
```

**NÃO** use `toolWorkflow` (Quirk #20 — não propaga argumentos pra cliente MCP externo).
**NÃO** use credential `httpHeaderAuth` (Quirk #22 — auto-vinculação ruim, valor desatualizado).

## 📦 Endpoints essenciais

Shopify usa REST + GraphQL. **Use REST** pra MCPs de atendimento.

### Clientes
- `GET /customers/search.json?query=phone:31983635636&limit=1&fields=id,first_name,last_name,email,phone` — buscar por telefone
- `GET /customers/search.json?query=email:foo@bar.com&limit=1` — buscar por email
- `GET /customers/{id}.json` — detalhe
- `GET /customers/{id}/orders.json?status=any&limit=10&fields=id,name,...` — pedidos do cliente

### Pedidos
- `GET /orders.json?status=any&email={email}&limit=10` — listar por email
- `GET /orders.json?status=any&name=%23{numero}` — buscar por número (com `%23` = `#` URL-encoded)
- `GET /orders/{id}.json?fields=...` — detalhe

### Catálogo

⚠️ **REST `?title=X` é EXACT match, não substring.** Pra busca por palavra-chave, use **GraphQL**.

- `GET /products.json?title={titulo_exato}` — match exato (raramente útil)
- `GET /products.json?handle={handle}` — match por handle
- `GET /products/{id}.json` — detalhe
- `GET /products/{id}/variants.json` — variações

**Pra busca por palavra-chave (substring/fulltext):** GraphQL Admin API com wildcards:

```graphql
{
  products(first: 5, query: "title:*VK100*") {
    edges {
      node {
        id title handle status productType
        variants(first: 1) {
          edges { node { price availableForSale inventoryQuantity } }
        }
      }
    }
  }
}
```

⚠️ **Wildcards `*X*` são OBRIGATÓRIOS** — `title:VK100` (sem wildcards) retorna 0 resultados no GraphQL. `title:*VK100*` retorna matches por substring.

POST `https://{shop}.myshopify.com/admin/api/{version}/graphql.json` com body `{"query": "..."}` — autenticação igual REST (header `X-Shopify-Access-Token`).

## 🛍️ Tools de catálogo pra Vendas (padrão Veuske 2026-06-02)

Quando o cliente tem agente de **VENDAS** que precisa indicar produtos (e enviar links com UTM), o MCP Shopify deve expor essas 3 tools de catálogo:

### 1. `buscar_produto_<cliente>(termo)` — descoberta por palavra-chave

GraphQL com wildcards. Cobre 90% dos casos.

```ts
{
  type: 'n8n-nodes-base.httpRequestTool',
  version: 4.4,
  config: {
    name: 'buscar_produto_<cliente>',
    parameters: {
      toolDescription: 'Busca produtos no catálogo por palavra-chave (match parcial no título). Use SEMPRE antes de mandar link...',
      method: 'POST',
      url: 'https://<shop>.myshopify.com/admin/api/2025-01/graphql.json',
      authentication: 'none',
      sendHeaders: true,
      headerParameters: { parameters: [
        { name: 'X-Shopify-Access-Token', value: 'shpat_<32-hex>' },
        { name: 'Content-Type', value: 'application/json' },
      ]},
      sendBody: true,
      specifyBody: 'json',
      jsonBody: `={ "query": "{ products(first: 5, query: \\"title:*{{ $fromAI('termo', 'palavra-chave', 'string') }}*\\") { edges { node { id title handle status productType variants(first: 1) { edges { node { price availableForSale } } } } } } }" }`,
      options: { response: { response: { neverError: true } } },
    }
  }
}
```

### 2. `obter_produto_<cliente>(handle)` — detalhe + todas as variantes

Quando cliente quer saber "esse produto vem em quais tamanhos?", "qual o preço do 1L?", etc.

```graphql
{
  productByHandle(handle: "X") {
    id title handle descriptionHtml productType status
    variants(first: 20) {
      edges { node { id title price availableForSale inventoryQuantity sku } }
    }
  }
}
```

### 3. `listar_<categoria>_<cliente>` — listagem por categoria (sem param)

Quando cliente pede sugestão ("quais fragrâncias vocês têm?"). Usar `title:*<palavra-chave-categoria>*`.

```graphql
{ products(first: 50, query: "title:*Refil*") { edges { ... } } }
```

### Padrão de URL pra envio (UTM obrigatório)

O agente monta o link assim:

```
https://<dominio-loja>.com.br/products/{handle}?utm_source=whatsapp&utm_medium=<agente_origem>&utm_campaign=<campanha>
```

Exemplo Veuske:
```
https://veuske.com.br/products/kit-equipamento-vk100-1l-fragrancia?utm_source=whatsapp&utm_medium=pedro_vendas&utm_campaign=indicacao_consultiva
```

### Regras do tool description pra o agente seguir

Sempre incluir nas descrições:
- "NUNCA invente URL ou cite a homepage"
- "Monte a URL como `https://<dominio>/products/{handle}?utm_source=...&utm_medium=...&utm_campaign=...`"
- "NUNCA indique produto com `availableForSale: false`"
- "Use match parcial — `kit VK100 1L` retorna mais opções que `VK100`"

## 🛡️ Operações → endpoints (validadas em produção)

| Operação MCP | Endpoint | Notas |
|---|---|---|
| `buscar_cliente(phone)` | `GET /customers/search.json?query=phone:{phone}&limit=1&fields=id,first_name,last_name,email,phone` | retorna `{customers: [{...}]}` |
| `listar_pedidos(customer_id)` | `GET /customers/{customer_id}/orders.json?status=any&limit=10&fields=...` | retorna `{orders: [{...}]}` |
| `buscar_produto_<cliente>(termo)` | `POST /graphql.json` com `products(first:5, query:"title:*{termo}*")` | substring search via GraphQL wildcard |
| `obter_produto_<cliente>(handle)` | `POST /graphql.json` com `productByHandle(handle:"{handle}")` | todas variantes + estoque |
| `listar_<categoria>_<cliente>` | `POST /graphql.json` com `products(first:50, query:"title:*<categoria>*")` | catálogo por palavra-chave |
| `obter_pedido(order_id)` | `GET /orders/{order_id}.json?fields=...` | `order_id` é o `id` numérico interno |
| `buscar_produto(query)` | `GET /products.json?title={query}` | match parcial por título |
| `obter_produto(product_id)` | `GET /products/{id}.json` | — |

**Arquitetura recomendada:** 3 tools `httpRequestTool` diretas (buscar_cliente → listar_pedidos → obter_pedido). LLM orquestra a sequência (telefone → customer_id → order_id).

## ⚠️ Quirks documentados

- **Preço:** string com decimal (ex: `"129.90"`). NÃO centavos. Slim deve `parseFloat()` se converter.
- **Paginação:** `?limit=N` funciona. Cursor-based (`page_info`) disponível mas não necessário pra SAC.
- **Rate limit:** 2 requests/segundo (REST) — mais apertado que outras APIs. Não fazer bulk.
- **`financial_status` valores:** `paid`, `pending`, `refunded`, `partially_refunded`, `voided`.
- **`fulfillment_status` valores:** `null` (aguardando envio), `fulfilled` (enviado), `partial`.
- **`name` vs `id`:** `name` = `"#11488"` (exibir pro cliente, sempre com `#`); `id` = numérico grande tipo `6942885806296` (usar em chamadas à API).
- **Busca REST por título:** `GET /products.json?title=X` faz **match EXATO**, não substring (confirmado Veuske 2026-06-02). Pra fulltext use GraphQL com `query: "title:*X*"` (wildcards obrigatórios).
- **GraphQL search precisa de wildcards:** `query: "title:VK100"` retorna 0; `query: "title:*VK100*"` retorna matches por substring. Sem `*` o GraphQL trata como busca exata.
- **Busca por telefone:** `query=phone:31983635636` — dígitos sem `+55`, sem parênteses. Retorna `{customers: []}` (array, mesmo sem resultados).
- **Busca por número de pedido:** `query=name=%23{numero}` — sempre com `%23` (URL encoding do `#`).
- **Rastreio por fulfillment:** `order.fulfillments[0].tracking_number` + `tracking_urls[0]` — null até despacho. Use `estimated_delivery_at` do fulfillment como alternativa.
- **`fulfillments[]` vazio:** pedido pago mas não despachado. Status visível ao cliente: "Aguardando envio".
- **`note_attributes` Appmax (ANAGROW específico):** pedidos via Appmax aparecem com `note_attributes: [{name: "appmax_order_id", value: 12345}, ...]`. Mesmo pedido existe nos 2 sistemas.

## 📋 Padrão de arquitetura (sempre seguir)

```
MCP Server Trigger v2
  ├─ buscar_cliente   (httpRequestTool 4.4, hardcoded token)
  ├─ listar_pedidos   (httpRequestTool 4.4, hardcoded token)
  └─ obter_pedido     (httpRequestTool 4.4, hardcoded token)
```

**NÃO use:**
- `toolWorkflow` + backends (Quirk #20 — args não propagam)
- Credential `httpHeaderAuth` (Quirk #22 — auto-vinculação ruim)
- `optimizeResponse: true` no httpRequestTool (Quirk #18 — não filtra de verdade via MCP)
- API version diferente entre tools do mesmo cliente

**Use:**
- 3 (ou 4 se incluir produtos) tools unitárias com `$fromAI()` nos parâmetros
- Token `shpat_` hardcoded em `headerParameters`
- `authentication: 'none'`
- `options: { response: { response: { neverError: true } } }` pra ver corpo de erro 4xx no agente
- `fields=...` em query pra reduzir payload sem precisar de Code node de slim

## 🔗 Links úteis

- Doc: https://shopify.dev/docs/api
- Admin API REST: https://shopify.dev/docs/api/admin-rest
- OAuth flow: https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/authorization-code-grant
- Partner Dashboard: https://partners.shopify.com

## 📝 Notas históricas

- **ANAGROW (2026-05-20):** primeira integração Shopify NexTags. Loja `714efc.myshopify.com`. Partner App "Nextags" com credencial OAuth2 do n8n (`shopifyOAuth2Api` + `predefinedCredentialType`). Funcionou mas a credencial era do n8n, não embutida — quebra no padrão Naah Store.
- **Naah Store (2026-04-08):** primeiro MCP Shopify estável em produção. Padrão de token hardcoded em headerParameters (sem credential) — funciona meses sem manutenção. Adotado como referência.
- **VEUSKE (2026-05-27):** terceira integração Shopify. Loja `veuske.myshopify.com`. App novo via Partner Dashboard com OAuth obrigatório (Shopify removeu Custom App legacy). Setup completo:
  - Workflows OAuth: `a2srjFLrwL8RqQey` (install) + `kdgW81VzXjm714xY` (callback)
  - Data table tokens: `V5B6zIlrnKWk9ejC`
  - Token capturado: `shpat_<32-hex>` (armazenado na data table `V5B6zIlrnKWk9ejC` do projeto, não em docs)
  - MCP: `Psaq5LWv1wHGw5uP` em `https://nextags.app.br/mcp/veuske-shopify-mcp`
  - Tools: `buscar_cliente(phone)`, `listar_pedidos(customer_id)`, `obter_pedido(order_id)` — todas `httpRequestTool` com token hardcoded
  - **Lições caras:** confundiu `atkn_` (formato inexistente) com token real; perdeu sessions tentando consertar credencial vinculada quando o valor dela é que estava errado. Refactor pra hardcoded resolveu tudo.

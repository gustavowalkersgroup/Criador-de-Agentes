# Appmax (Legacy v3)

> Status: 🟢 trabalhada (uso em produção — ANAGROW)
> Última atualização: 2026-05-14
> Cliente(s) usando: ANAGROW

## ⚠️ Existem 2 APIs Appmax — esta recipe é da LEGACY

| | **Legacy v3 (esta)** | Nova (OAuth) |
|---|---|---|
| Base | `https://admin.appmax.com.br/api/v3` | `https://api.appmax.com.br` |
| Auth | `access-token` estático (não expira) | OAuth 2.0 client credentials (1h) |
| Token | hex segmentado 4 blocos `XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX` | JWT Bearer |
| Comprar | painel Appmax → Configurações → API | painel → Aplicativos → API |

**Token Legacy nunca expira** (até cliente revogar/regerar). Sem refresh, sem cron, Pattern A puro.

Se o token do cliente bate no formato `XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX` (4 blocos de 8 hex separados por hífen) → **é Legacy**, usa essa recipe.

## 🔗 Base URL e ambientes

- **Produção:** `https://admin.appmax.com.br/api/v3`
- **Sandbox/Homologação:** não documentado publicamente — todas as integrações vistas em produção usam direto a base prod.
- **Versão atual:** `v3`
- **Variação por loja?** não — base URL é único.

## 🔐 Autenticação

- **Tipo:** **A — key fixa** (token estático passado em todo request)
- **Como mandar:**
  ```
  GET:  ?access-token=<TOKEN>          (query string)
  POST: body JSON com campo "access-token": "<TOKEN>"
  ```
  Ambos os métodos aceitam o token em query string — testado e funciona.
  Para uniformizar no n8n, **passe sempre em query** (vale também pra POST).

- **Credencial n8n:** `httpQueryAuth` (Generic Credential Type → Query Auth)
  - Name: `access-token`
  - Value: o token de 4 blocos hex

- **Como obter:** painel Appmax → Configurações → API → criar/copiar `access-token`. Atenção: depois de salvar a integração no Appmax, o token não fica mais visível — se o cliente perder, tem que regerar.

- **NÃO existe** Bearer header, `Authorization` header, `x-api-key` header — só o campo `access-token` em query ou body.

## 📦 Endpoints essenciais (confirmados ao vivo em 2026-05-14 com token ANAGROW)

### `GET /order`
- **Função:** listar pedidos paginados
- **Params:** `page`, `per_page` (default 10), filtros aceitos mas sem documentação — `email`, `customer_id`, `status`, `created_at` foram aceitos sem erro (não dá pra validar funcionalidade na conta de teste vazia)
- **Response shape:**
  ```json
  {
    "success": true,
    "text": "",
    "data": {
      "total": N, "per_page": 10, "current_page": 1, "last_page": N,
      "next_page_url": "...", "prev_page_url": null,
      "from": 1, "to": 10,
      "data": [ {...pedido}, ... ]
    },
    "status": 200
  }
  ```
- **Quirks:** wrap duplo — `response.data.data[]` (não `response.data[]`)

### `GET /order/{id}`
- **Função:** detalhe do pedido por ID
- **Params:** `id` numérico no path
- **Response shape:**
  ```json
  // sucesso: data é o objeto do pedido com campos status, total, customer, products, payment_method etc.
  { "success": true, "text": "", "data": { ...pedido }, "status": 200 }

  // not found: HTTP 200 mas success:false
  { "success": false, "text": "Failed to get order: 999", "data": 400, "status": 200 }
  ```
- **Quirks:**
  - **Erro de pedido inexistente vem como HTTP 200 com `success:false`** — slim node tem que olhar `success`, não status code
  - `data` pode ser objeto (sucesso) OU número 400/etc (erro). Defensive parsing obrigatório.

### `GET /customer`
- **Função:** listar clientes paginados (default 100 per_page)
- **Response shape:** mesmo wrap duplo do `/order`

### `GET /product`
- **Função:** listar produtos paginados
- **Params:** `page`, `per_page`
- **Response shape:**
  ```json
  {
    "message": "Get All products",
    "data": {
      "total": 912, "per_page": 10, "current_page": 1, "last_page": 92,
      "next_page_url": "...", "prev_page_url": null,
      "from": 1, "to": 10,
      "data": [{ "sku": "000002", "price": "139.90", "name": "..." }, ...]
    }
  }
  ```
- **⚠️ Quirks principais:**
  - **Filtros de query NÃO funcionam** — `?sku=X`, `?name=Y` são ignorados; sempre retorna lista completa paginada. Verificado.
  - Response **NÃO tem `success`** — usa `message` no topo. Inconsistente com `/order`.
  - Preço vem como **string** (`"139.90"`), não number. Slim deve converter.

### `GET /product/{sku}`
- **Função:** detalhe do produto por SKU (não por id numérico!)
- **Params:** SKU no path (ex: `/product/000002`)
- **Response shape:**
  ```json
  // sucesso
  { "message": "Get product", "data": { "sku": "...", "price": "...", "name": "..." } }
  // not found (ex: /product/1)
  { "message": "Get product", "data": null }
  ```
- **Quirks:** path usa SKU. `/product/1` retorna `data:null` mesmo havendo produto com id interno 1 — só SKU exato funciona.

### `POST /customer` (não usado no MCP atual, documentado pra referência)
- Body inclui `"access-token": "<TOKEN>"` + campos do cliente
- Usado pra criar/atualizar cliente; provavelmente upsert por email
- Ver código fonte: `ecomplus/app-appmax` → `functions/lib/appmax/customer.js`

### `POST /order` (não usado no MCP atual)
- Body inclui `"access-token": "<TOKEN>"` + items + customer_id + amount
- Ver `ecomplus/app-appmax` → `functions/lib/appmax/order.js`

## ⚠️ Quirks documentados

- **Tudo retorna HTTP 200** — mesmo erro. Lógica de erro é em `success: false` (em `/order`, `/customer`) ou em `data: null` (em `/product/{sku}`). Slim node deve detectar ambos.
- **Wrap duplo de paginação:** `response.data.data[]`. Esquecer = bug.
- **Shape diferente entre recursos:** `/order` usa `success`+`text`, `/product` usa `message`. Não dá pra ter slim genérico — um por endpoint.
- **Preços como string** em `/product`. Converter.
- **Filtros `/product` ignorados** — search por nome é inviável via API. Pra busca de catálogo natural ("ferritin", "antiqueda"), o agente precisaria de outra fonte (data table do n8n, ou full scan paginado se catálogo for pequeno).
- **`/product/{path}` usa SKU literal**, não ID numérico.
- **IDs de pedido:** numéricos sequenciais (int), não UUID.
- **Datas:** formato `YYYY-MM-DD HH:MM:SS` (timezone BR provável). Confirmar quando houver dados reais.
- **Sem rate-limit documentado**; não observei 429 nos testes (10 requests/min).
- **Status do pedido vem em PT-BR:** `aprovado`, `cancelado`, `estornado`, `autorizado`, `integrado` — e em EN: `processing`, `analyzing`, `waiting_payment`, `pending_refund`. Mistura. Ver mapping em `ecomplus/app-appmax/functions/lib/payments/parse-status.js`.

## 🪝 Webhook (envia eventos do Appmax → nosso n8n)

- **Onde configurar:** painel Appmax → Configurações → Webhook → Novo Webhook
- **Cliente cola a URL do nosso n8n Webhook Trigger** — Appmax POSTa eventos lá quando muda status de pedido
- **Eventos disparados** (correspondem a transições de status do pedido):
  - Pedido criado / processando
  - Análise antifraude
  - Aprovado / Pago / Integrado
  - Recusado (banco / risco)
  - Pendente de pagamento (boleto/pix gerado)
  - Expirado
  - Estornado
  - Chargeback / Chargeback recuperado
  - Cancelado
- **Formato do payload:**
  ```json
  {
    "data": { "id": <transaction_id>, ...possivelmente mais campos },
    "event": "<nome do evento>"   // formato não confirmado em prod
  }
  ```
  Estratégia padrão: receber webhook → fazer **GET /order/{data.id}** pra enriquecer com dados completos → processar.

## 🛡️ Mapeamento operações comuns

| Caso de uso | Endpoint Appmax |
|---|---|
| Detalhe pedido por número | `GET /order/{id}` |
| Listar pedidos (paginado) | `GET /order?page=N` |
| Pedidos de cliente por email | `GET /order?email=X` ⚠️ filtro não-verificado |
| Detalhe produto por SKU | `GET /product/{sku}` |
| Catálogo paginado | `GET /product?page=N&per_page=50` |
| Busca produto por nome | ❌ não suportado pela API |
| Listar clientes | `GET /customer?page=N` |
| Detalhe cliente | ❌ endpoint singular `/customer/{id}` retorna "Not Found" — só via lista |

## 📋 Decisão de arquitetura recomendada

**Caso A — key fixa simples.** Tools direto no MCP via `httpRequestTool`, credencial `httpQueryAuth` (Name=`access-token`, Value=`<token>`).

Sem data table de tokens, sem cron de refresh, sem reset manual. **Mais simples possível.**

Recomendações de tools (5 essenciais pra SAC):
1. `obter_pedido_por_id` → `GET /order/{id}`
2. `listar_pedidos` → `GET /order` (com filtros opcionais — page, per_page, email)
3. `obter_produto_por_sku` → `GET /product/{sku}`
4. `listar_produtos` → `GET /product?page=N` (catálogo paginado)
5. `listar_clientes` → `GET /customer` (consulta histórica)

**Webhook receiver:** workflow separado com `Webhook Trigger` + `HTTP Request` (GET /order/{id} pra enriquecer) + lógica de roteamento (ex: chamar NexTags pra mandar mensagem ao cliente).

⚠️ **Path do webhook ≠ path do MCP.** n8n compartilha namespace de path entre MCP Trigger e Webhook Trigger. Convenção: MCP usa `<slug>`, webhook usa `<slug>-webhook`. Ver `quirks_n8n.md` #16.

## 🔗 Links

- Doc oficial (Readme.io, parcial): `https://appmax.readme.io/reference/faq`
- Central de ajuda: `https://help.appmax.com.br/pt-br/central-de-ajuda/integrando-por-api`
- Integrador open-source de referência: `https://github.com/ecomplus/app-appmax`
  - `functions/lib/appmax/customer.js` — exemplo POST /customer
  - `functions/lib/appmax/order.js` — exemplo POST /order
  - `functions/routes/appmax/webhook.js` — exemplo de webhook receiver
- Última visita: 2026-05-14
- Confiabilidade do que está aqui: **alta** — auth + 4 endpoints GET testados ao vivo com token real do cliente ANAGROW. Filtros e POSTs documentados mas não verificados com dados reais (conta de teste vazia em pedidos/clientes).

## 📝 Notas históricas

- **ANAGROW (2026-05-14):** primeiro cliente NexTags integrando Appmax. Catálogo de 912 produtos (nutracêuticos: Ferritin12, OSA, Vitamina D, Follistin, Kit Antiqueda etc.). Conta sem pedidos ainda no momento da integração — endpoints de pedido testados retornam empty list válida.
- **Doc oficial Appmax é fragmentada:** Readme.io documenta a API NOVA (OAuth), enquanto a API Legacy v3 quase não tem doc pública. Maioria do conhecimento veio de engenharia reversa do `ecomplus/app-appmax` + testes ao vivo.
- **Cuidado ao confundir as duas APIs:** se o token for JWT Bearer (3 segmentos base64), é a API nova; se for hex 4-blocos, é Legacy v3.

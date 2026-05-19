# VTEX

> Status: 🟢 trabalhada (recipe completa a partir da doc oficial)
> Última atualização: Maio/2026
> Cliente(s) usando: (em planejamento)

## 🔗 Base URL e ambientes

- **Produção:** `https://{accountName}.vtexcommercestable.com.br`
- **Homologação:** `https://{accountName}.vtexcommercebeta.com.br`
- **`{accountName}`:** identificador da loja na VTEX (cada cliente tem o seu)
- **Versão atual:** APIs variam por módulo — Catalog v1, Orders v1, Master Data v1/v2, Promotions v1/v2

## 🔐 Autenticação

**Tipo: A — key fixa em 2 headers**

VTEX exige DOIS headers em todo request:

```
X-VTEX-API-AppKey: <appKey>
X-VTEX-API-AppToken: <appToken>
```

**Credencial n8n:** `httpHeaderAuth` **não funciona sozinho** porque manda só 1 header. Solução:

**Opção 1 (recomendada):** `httpCustomAuth` com JSON que injeta os 2 headers:

```json
{
  "headers": {
    "X-VTEX-API-AppKey": "<value>",
    "X-VTEX-API-AppToken": "<value>",
    "Content-Type": "application/json",
    "Accept": "application/json"
  }
}
```

No SDK n8n:
```ts
authentication: 'genericCredentialType',
genericAuthType: 'httpCustomAuth',
credentials: { httpCustomAuth: newCredential('VTEX <cliente> AppKey+Token') }
```

**Opção 2:** Dois headerParameters hardcoded no node (menos seguro, expõe credenciais no workflow). NÃO usar em produção.

**Como o cliente obtém:**
- Admin VTEX → License Manager → Application Keys
- Cria uma App Key com role específico pro MCP (mínimo necessário: Catalog Read, Order Read, Customer Read)
- Salva `appKey` e `appToken` (token só é exibido uma vez)

⚠️ **Best practice:** cada integração tem sua própria App Key com role mínimo. NÃO compartilhar key entre projetos.

## 📦 Endpoints essenciais (para atendimento de e-commerce)

VTEX tem **65 APIs**. Pra MCP de atendimento, foco em ~10 endpoints distribuídos em 4 APIs principais:

### Catalog API (catálogo)

#### `GET /api/catalog_system/pub/products/search?ft={termo}`
- **Função:** busca produtos por full-text
- **Params:** `ft` (texto), `_from`, `_to` (paginação), `O` (ordenação)
- **Response shape:** array direto `[{...produto}]` (sem wrapper)
- **Campos úteis:** `productId`, `productName`, `linkText`, `items[].itemId` (SKU), `items[].sellers[0].commertialOffer.Price`, `items[].images`
- **Auth:** público (não exige X-VTEX-API)

#### `GET /api/catalog_system/pub/products/search/{linkText}/p`
- **Função:** detalhe do produto pelo slug
- **Auth:** público

#### `GET /api/catalog_system/pvt/products/{productId}`
- **Função:** detalhe completo via Catalog API privada
- **Auth:** exige X-VTEX-API

### Orders API (pedidos)

#### `GET /api/oms/pvt/orders?q={termo}`
- **Função:** lista pedidos com filtro
- **Params:**
  - `q` (busca livre)
  - `f_creationDate` (range de datas)
  - `f_status` (status do pedido)
  - `clientEmail` (filtro por email do cliente)
  - `per_page` (default 15, máx 100)
- **Response shape:** `{ list: [...pedidos], paging: {total, pages, currentPage} }`
- **Auth:** exige X-VTEX-API

#### `GET /api/oms/pvt/orders/{orderId}`
- **Função:** detalhe completo de pedido
- **Response shape:** `{ orderId, status, items: [...], clientProfileData, shippingData, paymentData, packageAttachment.packages[].trackingNumber, ... }`
- **Auth:** exige X-VTEX-API

### Profile System / Customer (clientes)

VTEX usa Master Data v1 com entidade `CL` (clients) pra storage de clientes.

#### `GET /api/dataentities/CL/search?_where=email={email}&_fields=email,firstName,lastName,document,homePhone,userId`
- **Função:** buscar cliente por email
- **Params:** `_where` (filtro), `_fields` (campos a retornar), `_from`/`_to` (paginação)
- **Response shape:** array `[{...cliente}]`
- **Header obrigatório:** `REST-Range: resources=0-9` (paginação custom)
- **Auth:** X-VTEX-API
- **Quirk:** `_fields` é OBRIGATÓRIO. Sem ele retorna campos mínimos.

#### `GET /api/dataentities/CL/documents/{userId}`
- **Função:** detalhe completo do cliente
- **Auth:** X-VTEX-API

### Logistics API (rastreio)

#### `GET /api/oms/pvt/orders/{orderId}/packages`
- **Função:** packages e tracking de um pedido
- **Response:** lista de packages com `trackingNumber`, `courier`, `trackingUrl`
- **Auth:** X-VTEX-API

(Geralmente já vem em `GET /api/oms/pvt/orders/{orderId}.packageAttachment.packages[]` — então essa segunda chamada raramente é necessária.)

## ⚠️ Quirks documentados

- **Preço em centavos** — Catalog API retorna `Price: 12990` = R$ 129,90. Dividir por 100.
- **`linkText` ≠ `productId`** — busca pública usa slug; busca privada usa ID numérico. Documentar bem nas tools.
- **Master Data exige `_fields`** — sem isso, retorna shape minimalista sem o que você precisa.
- **Master Data paginação via header** — `REST-Range: resources=0-9` em vez de `?page=`. Quirk feio.
- **Sales channels** — produtos têm `items[].sellers[]` com `commertialOffer` por seller. Pra storefront simples, pega `sellers[0]`.
- **Specifications dinâmicas** — atributos de produto (cor, tamanho) vêm como `specificationGroups`, não campo fixo. Cada conta VTEX tem suas. Documentar caso a caso por cliente.
- **APIs `pub/`** (públicas) **vs `pvt/`** (privadas) — `pub/` não exige auth e é mais leve; `pvt/` tem mais campos mas exige X-VTEX-API. Use `pub/` quando dá.

## 🛡️ Mapeamento operações comuns → endpoints VTEX

| Caso de uso | Endpoint VTEX recomendado | Auth |
|---|---|---|
| Buscar produto por nome | `GET /api/catalog_system/pub/products/search?ft=` | pub |
| Detalhe produto (slug) | `GET /api/catalog_system/pub/products/search/{slug}/p` | pub |
| Detalhe produto (id) | `GET /api/catalog_system/pvt/products/{id}` | pvt |
| Estoque/disponibilidade SKU | `GET /api/logistics/pvt/inventory/skus/{skuId}` | pvt |
| Buscar pedido (texto/email) | `GET /api/oms/pvt/orders?q=` ou `?clientEmail=` | pvt |
| Detalhe pedido | `GET /api/oms/pvt/orders/{orderId}` | pvt |
| Listar pedidos do cliente | `GET /api/oms/pvt/orders?clientEmail=` | pvt |
| Buscar cliente | `GET /api/dataentities/CL/search?_where=email=` | pvt |
| Detalhe cliente | `GET /api/dataentities/CL/documents/{userId}` | pvt |
| Rastreio | já em `orders/{id}.packageAttachment.packages[].trackingNumber` | pvt |
| Cupom específico | `GET /api/rnb/pvt/coupon/{coupon}` (Promotions v1) | pvt |

## 📋 Decisão de arquitetura recomendada

**Caso A — Key fixa.** Não precisa OAuth/refresh.

- `httpRequestTool` direto no MCP (sem backends dedicados)
- 1 credencial `httpCustomAuth` (com os 2 headers em JSON)
- Slim response em cada tool via `optimizeResponse: true` + `fieldsToInclude: selected`
- Sem data table, sem cron

**MCP típico VTEX:** 8-10 tools cobrindo catálogo+pedidos+clientes+rastreio.

## 🔗 Links

- Doc oficial: https://developers.vtex.com/docs/api-reference
- OpenAPI schemas: https://github.com/vtex/openapi-schemas
- License Manager (criar App Key): https://help.vtex.com/en/tutorial/api-keys--4bFEmcHXgpNksoePchZyy6
- Best practices API keys: https://help.vtex.com/en/tutorial/best-practices-api-keys--7b6nD1VMHa49aI5brlOvJm
- Última visita: Maio/2026
- Confiabilidade: **ALTA** — OpenAPI público completo no GitHub

## 📝 Notas históricas

- VTEX é a API mais complexa do mercado BR. Documentação é boa mas vasta (65 APIs).
- Pra MCP de atendimento simples, **NUNCA** exponha mais de 10-12 tools — IA fica confusa entre `pub/` vs `pvt/` se tiver muita variação.
- Cliente VTEX-puro tem `accountName` único; cliente VTEX-via-FastStore ou VTEX IO pode ter URL custom — confirme antes.
- Pra MCPs futuros: usar OpenAPI schema do GitHub diretamente pra autogerar tools com `scripts/parse_openapi.py`.

# Shopify

> Status: 🟡 stub (já fizemos MCP antes, mas falta documentar quirks específicos)
> Última atualização: Maio/2026
> Cliente(s) usando: (anteriores — preencher quando aparecer o próximo)

## 🔗 Base URL e ambientes

- **Produção:** `https://{shop}.myshopify.com/admin/api/{version}/`
- **`{shop}`:** subdomínio da loja
- **`{version}`:** ex `2025-01` (Shopify atualiza versão trimestralmente; mantenha 1 versão estável por cliente)

## 🔐 Autenticação

**Tipo: A — Access Token via header**

- **Header:** `X-Shopify-Access-Token: <token>`
- **Como obter:** loja gera via Admin → Apps → Develop apps → cria Custom App → instala → copia Admin API access token
- **Credencial n8n:** `httpHeaderAuth` com Name=`X-Shopify-Access-Token`, Value=token

⚠️ Há também OAuth (Caso B) pra apps públicos na App Store, mas pra MCPs internos sempre usar Custom App + token fixo (mais simples).

## 📦 Endpoints essenciais

Shopify usa REST + GraphQL. **Recomendado REST** pra MCPs de atendimento (mais simples).

### Catálogo
- `GET /products.json?title={termo}` — buscar produto por título
- `GET /products/{id}.json` — detalhe
- `GET /products/{id}/variants.json` — variações (SKUs)

### Pedidos
- `GET /orders.json?status=any&email={email}` — listar pedidos
- `GET /orders/{id}.json` — detalhe

### Clientes
- `GET /customers/search.json?query=email:{email}` — buscar
- `GET /customers/{id}.json` — detalhe
- `GET /customers/{id}/orders.json` — pedidos do cliente

## ⚠️ Quirks (preencher na primeira integração real)

- **Preço:** string com decimal, em moeda da loja (ex: `"129.90"`). NÃO centavos.
- **Paginação:** `?limit=` + `?page_info=` (cursor-based, não `page=N`). Header `Link` traz próximo cursor.
- **Rate limit:** 2 requests/segundo (REST) — bem mais apertado que VTEX/Martz. Considerar batching.
- **Webhooks:** se for usar pra transacionais, não passa pela MCP — fica em workflow separado.

## 📋 Decisão de arquitetura

Caso A — key fixa. Tools `httpRequestTool` direto. Sem backends.

## 🔗 Links

- Doc: https://shopify.dev/docs/api
- Admin API REST: https://shopify.dev/docs/api/admin-rest
- Última visita: Maio/2026 (resumida)

## 📝 Notas

- Stub. Preencher Endpoints/Quirks com chamadas reais quando aparecer próximo cliente Shopify.

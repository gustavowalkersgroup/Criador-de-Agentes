# Nuvemshop / Tiendanube

> Status: 🟢 trabalhada (uso em produção via Neurofood)
> Última atualização: Maio/2026
> Cliente(s) usando: Neurofood Shop

## 🔗 Base URL e ambientes

- **Produção:** `https://api.tiendanube.com/{version}/{store_id}/...`
- **`{store_id}`:** ID numérico único da loja (fornecido após cliente instalar o app Nuvemshop)
- **`{version}`:** atual `2025-03` (Nuvemshop versiona como YYYY-MM)
- **Ambiente único** (sem sandbox separado)

## 🔐 Autenticação

**Tipo: A — Bearer token fixo (disfarçado)**

```
Authentication: bearer <access_token>
User-Agent: <Nome do app> (<email contato>)
```

⚠️ Importante: header é `Authentication` (sem L final), NÃO `Authorization`. Erro comum.

- **Credencial n8n:** `httpHeaderAuth` com Name=`Authentication`, Value=`bearer <token>` (sim, espaço + token)
- **User-Agent** também é obrigatório — algum n8n pode precisar setar como header separado

**Como obter token:**
1. Cliente cria app no Partner Portal Nuvemshop
2. Lojista instala o app
3. Token vem no callback OAuth (mas o token NÃO expira — uma vez gerado fica válido)
4. Por isso tratamos como key fixa (Caso A) e não OAuth com refresh (Caso B)

## 📦 Endpoints essenciais (validados na Neurofood)

### Catálogo

#### `GET /v1/{store_id}/products?q={termo}&per_page=10&language=pt&published=true`
- **Função:** buscar produtos
- **Params:** `q` (texto livre), `page`, `per_page` (default 30, máx 200), `language`, `published`
- **Response shape:** array direto `[{...produto}]` (sem wrapper)
- **Campos úteis:** `id`, `name.pt`, `price`, `variants[]`, `images[].src`, `permalink`

#### `GET /v1/{store_id}/products/{product_id}`
- **Função:** detalhe completo
- **Inclui:** variantes, imagens, descrição (HTML), preço promocional, stock

### Pedidos

#### `GET /v1/{store_id}/orders?q={termo}&status={status}&per_page=10`
- **Função:** buscar pedidos
- **Params:**
  - `q` (texto — email, nome, número do pedido)
  - `status` (open / closed / cancelled)
  - `payment_status` (pending / authorized / paid / abandoned / refunded / voided)
  - `shipping_status` (unpacked / unfulfilled / fulfilled)
  - `customer_ids` (filtrar por cliente)
- **Response:** array `[{...pedidos}]`

#### `GET /v1/{store_id}/orders/{order_id}`
- **Função:** detalhe completo
- **Inclui:** items, valores, cliente, endereço, pagamento, rastreio, histórico

### Clientes

#### `GET /v1/{store_id}/customers?q={termo}&per_page=10`
- **Função:** buscar cliente
- **Params:** `q` aceita CPF, email, nome

#### `GET /v1/{store_id}/customers/{customer_id}`
- **Função:** detalhe completo do cliente

### Cupons

#### `GET /v1/{store_id}/coupons?valid=true`
- **Função:** lista cupons ativos

## ⚠️ Quirks documentados

- **Header é `Authentication`** (sem L final) — quebra header parsing em algumas libs
- **`name` é objeto com idiomas:** `{ pt: "Produto X", es: "Producto X", en: "Product X" }` — não é string
- **Preço em string com decimal:** `"129.90"` (NÃO centavos)
- **`store_id` no path** — não em header. Diferente da maioria das APIs SaaS
- **Versão `2025-03`** no path — atualização versionada anual/trimestral; mantenha 1 versão estável por cliente
- **Não tem `per_page > 200`** — pra catálogos grandes, paginar
- **`customer_ids`** aceita array via query: `customer_ids=1,2,3`

## 🛡️ Mapeamento operações comuns → endpoints

| Caso de uso | Endpoint |
|---|---|
| Buscar produto | `GET /products?q=` |
| Detalhe produto | `GET /products/{id}` |
| Buscar pedido | `GET /orders?q=` |
| Detalhe pedido | `GET /orders/{id}` |
| Listar pedidos do cliente | `GET /orders?customer_ids={id}` |
| Buscar cliente | `GET /customers?q=` |
| Detalhe cliente | `GET /customers/{id}` |
| Cupons ativos | `GET /coupons?valid=true` |

## 📋 Decisão de arquitetura

Caso A — token fixo. Tools `httpRequestTool` direto. Sem backends.

## 🔗 Links

- Doc: https://dev.nuvemshop.com.br/docs/developer-tools/nuvemshop-api
- Última visita: Maio/2026
- Confiabilidade: alta (estável, sem endpoints fantasma vistos)

## 📝 Notas históricas

- Implementado pela primeira vez em cliente BR de suplementos (8 tools no MCP).
- Implementação serve de **referência canônica** pra MCP v2 com API simples (sem OAuth refresh).

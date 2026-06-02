# Yampi

> Status: 🟢 validada
> Última atualização: 2026-05-27
> Cliente(s) usando: Veuske (alias: veuske)

## 🔗 Base URL e ambientes

- **Produção:** `https://api.dooki.com.br/v2/{alias}/`
- **`{alias}`:** identificador da loja na Yampi (subdomínio)
- **Doc:** https://docs.yampi.com.br/introduction

## 🔐 Autenticação

**Tipo: A — duas chaves fixas em 2 headers separados**

```
User-Token: <token>
User-Secret-Key: <secret>
```

- **Credencial n8n:** `httpCustomAuth` com JSON:
  ```json
  {
    "headers": {
      "User-Token": "<token>",
      "User-Secret-Key": "<secret>"
    }
  }
  ```
- **Como obter:** Admin Yampi → Aplicativos → criar app → copiar `User-Token` e `User-Secret-Key`
- **Tipo n8n:** `genericCredentialType` + `genericAuthType: 'httpCustomAuth'`

## 📦 Endpoints validados

### Clientes

```
GET /{alias}/customers?q={termo}&per_page=1
```
- `q` faz match relax — busca em nome, email, telefone, **CPF**, CNPJ simultaneamente
- O parâmetro `searchFields` é só uma dica; mesmo `searchFields=phone` retorna match por CPF (confirmado Veuske 2026-05-27)
- Retorna `{ data: [ customer ] }` — array mesmo para 1 resultado
- Campos úteis: `id`, `generic_name`, `first_name`, `last_name`, `email`, `phone.full_number`, `cpf`

### Pedidos — Listar por cliente

```
GET /{alias}/orders?customer_id={id}&includes=status,items&per_page=10&order_by=id&sort=desc
```
- **ÚNICO filtro que funciona para clientes:** `customer_id` (integer)
- **Filtros que NÃO funcionam:** `customer_phone`, `customer_name`, `customer_email`, `q` — API ignora silenciosamente e retorna todos os pedidos
- Retorna `{ data: [ order ], meta: { pagination: {...} } }`
- `includes=items` carrega `items.data[]` com `sku.data.title` (nome do produto)
- `includes=status` carrega `status.data` com `name` e `alias`

### Pedidos — Detalhe

```
GET /{alias}/orders/{order_id}?includes=status,items,customer
```
- `order_id`: ID numérico interno Yampi (ex: `163409544`)
- Retorna `{ data: { order } }` (wrapped em data)
- O `number` do pedido é longo (ex: `113842683109974`) — usar últimos 8 dígitos para exibição
- Campos de rastreio: `track_code`, `track_url` (null até pedido ser despachado)
- Entrega prevista: `date_delivery.date` (formato: `"2026-06-11 00:00:00.000000"`)
- Status: `status.data.alias` (ex: `paid`, `handling_products`, `on_carriage`, `delivered`, `cancelled`)
- Pagamento: `payments[]` array com `name` (ex: `"Mastercard"`)

### Itens de pedido

Disponível em `order.items.data[]`:
```json
{
  "product_id": 45148789,
  "sku_id": 299016791,
  "item_sku": "MAQ002",
  "quantity": 1,
  "price": 649,
  "sku": {
    "data": {
      "title": "Aromatizador Automático Marketing Olfativo - VK50 Branco",
      "total_in_stock": 258,
      "variations": [{ "name": "Cor", "value": "Branco" }]
    }
  }
}
```
Nome do produto = `item.sku.data.title`. Variações = `item.sku.data.variations[].name + ': ' + value`.

### Catalog/Produtos — SEM ACESSO

```
GET /{alias}/catalog/products → 403 Forbidden
GET /{alias}/catalog/products/{id} → 403 Forbidden
```
⚠️ API Key padrão NÃO tem permissão de catálogo. Para buscar produtos, criar token com permissão de catálogo separada no admin Yampi.

## ⚠️ Quirks confirmados (Veuske, 2026-05-27)

| Quirk | Detalhe |
|---|---|
| Filtros de orders ignorados | Apenas `customer_id` filtra por cliente. Outros params (`customer_phone`, `customer_email`, `q`, `customer_name`) são silenciosamente ignorados — retornam todos os pedidos |
| Número do pedido longo | `order.number` é um inteiro enorme (ex: `113842683109974`). Exibir últimos 6-8 dígitos como referência curta |
| Rastreio nulo antes do despacho | `track_code` e `track_url` são null até o pedido ser despachado. Informar data de entrega estimada (`date_delivery.date`) nesse caso |
| Nome do produto em `sku.data.title` | Não existe `item.name` direto — nome vem de `item.sku.data.title` |
| Catalog 403 | Credencial padrão não tem permissão de catálogo. Pedido de produto deve ser respondido via base de conhecimento do agente |
| Preços em reais | `price`, `value_total`, `value_shipment` já são float em reais (não centavos) |
| `date_delivery.date` format | `"2026-06-11 00:00:00.000000"` — splitar em `' '` e pegar `[0]` |
| Auth: 2 headers fixos | Requer `httpCustomAuth` com JSON de headers. NÃO usar `httpHeaderAuth` (só aceita 1 header) |

## 🛡️ Operações → endpoints (validadas)

| Operação MCP | Endpoint | Notas |
|---|---|---|
| `buscar_pedidos(phone)` | Step 1: `GET /customers?q={phone}&per_page=1` → Step 2: `GET /orders?customer_id={id}&includes=status,items&per_page=10&order_by=id&sort=desc` | 2 chamadas em sequência |
| `obter_pedido(order_id)` | `GET /orders/{order_id}?includes=status,items,customer` | `order_id` é o `id` Yampi numérico |
| ~~`buscar_produto`~~ | N/A | 403 — sem permissão de catálogo |

## 📋 Decisão de arquitetura (FINAL 2026-05-27 — refatorada)

**Padrão `httpRequestTool` direto com tokens hardcoded** — mesmo padrão Shopify Naah Store/Veuske. Sem backends, sem credential.

```ts
const buscarClienteYampi = tool({
  type: 'n8n-nodes-base.httpRequestTool',
  version: 4.4,
  config: {
    name: 'buscar_cliente_yampi',
    parameters: {
      method: 'GET',
      url: 'https://api.dooki.com.br/v2/{alias}/customers',
      authentication: 'none',
      sendHeaders: true,
      headerParameters: { parameters: [
        { name: 'User-Token', value: '<token>' },
        { name: 'User-Secret-Key', value: '<secret>' },
        { name: 'Accept', value: 'application/json' },
      ]},
      sendQuery: true,
      queryParameters: { parameters: [
        { name: 'q', value: "={{ $fromAI('phone', 'Telefone com DDD, soh digitos') }}" },
        { name: 'searchFields', value: 'phone' },
        { name: 'limit', value: '1' },
      ]},
      options: { response: { response: { neverError: true } } }
    }
  }
});
```

**Dividir multi-step em tools separadas:**
- `buscar_cliente_yampi(phone)` → 1 request → retorna `customer_id`
- `listar_pedidos_yampi(customer_id)` → 1 request → retorna pedidos
- `obter_pedido_yampi(order_id)` → 1 request → retorna detalhe

LLM orquestra a sequência. **NÃO use `toolWorkflow`** (Quirk #20).
**NÃO use credential `httpCustomAuth`** (Quirk #22 — auto-vinculação ruim, valor desatualiza). Hardcode os 2 headers direto.

### Histórico — versão antiga (deprecated)

Antes (2026-05-27 manhã) usávamos `toolWorkflow + passThrough` com backends dedicados (`BxtQK2fznpWHkapL`, `wz7pjt8mcpSUXGdt`). Nunca testamos end-to-end via NexTags — depois confirmamos que `toolWorkflow` não propaga argumentos pra cliente MCP externo (Quirk #20). Refatorado pra `httpRequestTool` direto, backends arquivados.

## 🔔 Webhooks transacionais Yampi

> 📖 **Padrão completo:** ver `webhook_transactional_pattern.md` (arquitetura, helpers JS, dedup, etc.)
>
> Esta seção tem o que é específico do payload Yampi.

### Arquitetura recomendada (Rafa @Walkers / Veuske 2026-05-28)

```
POST /webhook/{cliente}/yampi/pedidos
  ↓
Code (extrair + normalizar phone)
  ↓
Data Table get por order_id (dedup)
  ↓
IF "já existe?" → IF "status mudou?" → Switch (status)
                                          ├─ pending  → HTTP NexTags + UPDATE banco
                                          ├─ paid     → HTTP NexTags + UPDATE banco
                                          ├─ shipped  → HTTP NexTags + UPDATE banco
                                          └─ delivered→ HTTP NexTags + UPDATE banco
```

E pra carrinho:

```
POST /webhook/{cliente}/yampi/carrinho-abandonado
  ↓
Code (extrair + normalizar)
  ↓
HTTP NexTags (sem dedup — cada cart é único)
```

### URL pattern

✅ **Use hierárquico:** `/webhook/{cliente}/yampi/pedidos` e `/webhook/{cliente}/yampi/carrinho-abandonado`
❌ Evite traços: `/webhook/{cliente}-yampi-pedidos`

### Eventos Yampi disponíveis (cadastrar na admin Yampi)

| Evento | Quando dispara | Cadastrar pra | Endpoint sugerido |
|---|---|---|---|
| `Order.Created` | Pedido criado (ainda sem pagamento) | (opcional) | `/webhook/{cliente}/yampi/pedidos` |
| `Order.Paid` | Pagamento confirmado | ✅ obrigatório | `/webhook/{cliente}/yampi/pedidos` |
| `Order.Invoiced` | Nota fiscal emitida | (opcional) | `/webhook/{cliente}/yampi/pedidos` |
| `Order.Shipped` | Pedido despachado (com `track_code`) | ✅ obrigatório | `/webhook/{cliente}/yampi/pedidos` |
| `Order.Delivered` | Entregue ao cliente | ✅ obrigatório | `/webhook/{cliente}/yampi/pedidos` |
| `Order.Cancelled` | Cancelado | recomendado | `/webhook/{cliente}/yampi/pedidos` |
| `Cart.Updated` (ou similar) | Yampi sinaliza carrinho abandonado | ✅ obrigatório | `/webhook/{cliente}/yampi/carrinho-abandonado` |

> ⚠️ **Correção de doc anterior:** Yampi **EMITE webhook de carrinho abandonado** (não precisa cron). Confirme o nome exato do evento na admin Yampi — pode ser `Cart.Updated`, `Cart.Abandoned` ou similar dependendo da versão. Confirmado em produção na Veuske (Rafa, 2026-05-28).

### Switch por STATUS (não por EVENT)

Use `body.resource.status.data.alias` como discriminador no Switch — mais robusto que `body.event`. Exemplo de aliases Yampi:

| `status.data.alias` | Significado | Equivale ao evento |
|---|---|---|
| `pending` / `aguardando_pagamento` | Aguardando pagamento | Order.Created |
| `paid` / `pagamento_aprovado` | Pago | Order.Paid |
| `invoiced` / `nota_emitida` | NF emitida | Order.Invoiced |
| `on_carriage` / `enviado` | Em transporte | Order.Shipped |
| `delivered` / `entregue` | Entregue | Order.Delivered |
| `cancelled` / `cancelado` | Cancelado | Order.Cancelled |

> ⚠️ Aliases variam por loja — confirme com `GET /v2/{alias}/orders/statuses` ou olhando um pedido real via `obter_pedido_yampi`.

### Payload do webhook (`body.resource = order`)

Campos úteis (use com `verificarDado()` pra evitar undefined):

```js
order.id                                       // ID numérico interno (usar em dedup)
order.number                                   // número exibido pro cliente (#11488 ou longo)
order.value_total                              // R$ total (string decimal)
order.created_at.date                          // "2026-05-27 13:53:13" (string)
order.customer.data.first_name                 // nome
order.customer.data.last_name
order.customer.data.phone.full_number          // pode vir com OU sem 55 (use formatarTelefone)
order.customer.data.email
order.customer.data.cpf
order.shipping_address.data.{street,number,complement,neighborhood,city,uf,zip_code}
order.items.data[].quantity
order.items.data[].sku.data.title              // nome do produto
order.items.data[].item_value                  // preço unitário
order.items.data[].price                       // alternativa (depende da versão)
order.status.data.name                         // "Pago" (display pro cliente)
order.status.data.alias                        // "paid" (use no Switch)
order.track_code                               // null até despacho
order.track_url
order.shipment_service                         // transportadora
order.estimated_delivery_date
order.totalizers.total                         // total em float (carrinho)
order.spreadsheet.data.purchase_url            // URL checkout (carrinho)
```

### CUFs sugeridos pra criar na NexTags

Padrão CamelCase + sufixo YMP (Rafa):

| CUF | Origem no payload |
|---|---|
| `StatusPedidoYMP` | `order.status.data.name` |
| `NumeroPedidoYMP` | `order.number` ou `order.id` |
| `ValorPedidoYMP` | `R$ ${order.value_total}` |
| `ProdutosPedidoYMP` | items.map(...).join(', ') |
| `RastreioPedidoYMP` | `order.track_code` |
| `LinkRastreioYMP` | `order.track_url` |
| `TransportadoraYMP` | `order.shipment_service` |
| `DataEntregaPrevistaYMP` | `order.estimated_delivery_date` |
| `EnderecoEntregaYMP` | concat shipping_address |
| `LinkCarrinho` | `cart.spreadsheet.data.purchase_url` |
| `ValorCarrinho` | `R$ ${cart.totalizers.total}` |

### Templates de produção (referência)

- **Veuske - Pedidos** (`o9B8mwRlhrfES6sz`) — webhook com dedup + 4 status + data table
- **Veuske - Carrinho Abandonado** (`jK590pipUMKfe7qy`) — webhook simples + Code normalizador

Esses 2 são o padrão ouro. Pra novo cliente Yampi, copiar e adaptar (URLs, flow_ids, token NexTags).

## 🔗 Links

- Doc oficial: https://docs.yampi.com.br/introduction
- Validado em: 2026-05-27 com alias `veuske`

## 📝 Notas históricas

- **VEUSKE (2026-05-27 manhã):** infra inicial com backends + toolWorkflow + passThrough. Nunca foi testada end-to-end.
- **VEUSKE (2026-05-27 tarde):** refatorado pra `httpRequestTool` direto com tokens hardcoded. Tools `buscar_cliente_yampi`, `listar_pedidos_yampi`, `obter_pedido_yampi`. Testado com Leonir (`243986834`) — funcionou.
- **VEUSKE (2026-05-27 noite):** adicionados webhooks transacionais: `Veuske Yampi — Transacionais de Pedido` (`l3xpBFI8xW7Ffcvr`) + `Veuske Yampi — Carrinho Abandonado` (`Rub1CAJX1xDdYddy`). Placeholders pros flow_ids + NEXTAGS_VEUSKE_ACCESS_TOKEN.

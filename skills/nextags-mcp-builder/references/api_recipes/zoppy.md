# Recipe — ZOPPY Partners API 🟢

CRM de Giftback. Gerencia clientes, pedidos, cupons, produtos e carrinhos abandonados.

---

## Auth

**Tipo:** A — Key fixa (Bearer JWT)

```
Authorization: Bearer <jwt_token>
```

Token obtido em: Plataforma ZOPPY → menu superior direito → Chave de API.
Token não tem `exp` no payload (sem expiração definida).

**Credencial n8n:**
- Tipo: `httpHeaderAuth`
- Name: `Authorization`
- Value: `Bearer <token>`

---

## Base URL (ATENÇÃO — docs vs realidade)

**Docs dizem:** `https://api-partners.zoppy.com.br` + sufixo `/api`
**Confirmado empiricamente:** paths funcionam SEM o `/api`

```
✅ https://api-partners.zoppy.com.br/customers
❌ https://api-partners.zoppy.com.br/api/customers  ← retorna 404
```

Use sempre sem `/api`.

---

## Paginação (obrigatória em todos os list endpoints)

Todos os campos são **obrigatórios**:

| Param | Tipo | Formato aceito |
|---|---|---|
| `after` | date | `YYYY-MM-DD` ou `YYYY-MM-DDTHH:MM:SSZ` (SEM milissegundos) |
| `page` | number | `1` |
| `pageSize` | number | `10` a `50` |

⚠️ `after=2000-01-01T00:00:00.000Z` (com `.000Z`) → 422 "Invalid after date"
✅ `after=2020-01-01T00:00:00Z` funciona
✅ `after=2020-01-01` funciona

**Shape do response paginado:**
```json
{
  "pagination": { "page": 1, "pageSize": 10, "totalRecords": 13438, "totalPages": 1344 },
  "data": [...]
}
```

---

## Clientes — `/customers`

### Endpoints úteis pra atendimento

| Endpoint | Descrição | Paginação? |
|---|---|---|
| `GET /customers/phone/:phone` | Busca por telefone (11 dígitos BR) | Não |
| `GET /customers/:id` | Detalhe por UUID (inclui `coupon` embutido) | Não |
| `GET /customers/` | Lista todos (só pra discovery, não pra busca) | Sim |

### Modelo slim (campos úteis)
```json
{
  "id": "UUID",
  "email": "email@...",
  "phone": "11999999999",
  "firstName": "Nome",
  "lastName": "Sobrenome",
  "position": "loyal",
  "coupon": { "code": "GIFT10", "amount": 10, "type": "percent", "isValid": true, "expiryDate": "..." },
  "createdAt": "...",
  "updatedAt": "..."
}
```

`position` = segmentação RFM: `promising`, `loyal`, `sleeping`, `possible-loyal`, `at-risk`
`coupon` = null se cliente não tem cupom ativo

**Phone format:** 11 dígitos, sem +55, sem espaço, sem traço. Ex: `31983635636`

---

## Pedidos — `/orders`

### Endpoints úteis

| Endpoint | Descrição | Paginação? |
|---|---|---|
| `GET /orders/` | Lista pedidos (aceita `customerId` como filtro?) | Sim |
| `GET /orders/:id` | Detalhe por UUID | Não |

⚠️ Docs não documentam filtro por `customerId` no list. Testar `GET /orders?customerId=UUID`. Se não funcionar, usar `GET /orders/` e filtrar no Code node (custo alto com base grande).

### Modelo slim (campos úteis)
```json
{
  "id": "UUID",
  "externalId": "...",
  "status": "completed",
  "subtotal": 250.00,
  "total": 225.00,
  "discount": 25.00,
  "couponCode": "GIFT10",
  "completedAt": "...",
  "customerId": "UUID",
  "customer": { "firstName": "...", "email": "..." },
  "lineItems": [
    { "product": { "name": "..." }, "quantity": 1, "unitPrice": 250.00 }
  ],
  "createdAt": "..."
}
```

---

## Cupons — `/coupons`

### Endpoints úteis pra atendimento (sem lista geral)

| Endpoint | Descrição |
|---|---|
| `GET /coupons/phone/:phone` | 1 cupom pelo telefone |
| `GET /coupons/phone/:phone/many` | Todos os cupons pelo telefone ✅ |
| `GET /coupons/:id` | Cupom por UUID |
| `GET /coupons/code/:code` | Cupom por código |

**Não existe** `GET /coupons/` (lista geral com paginação) pra cupons.

### Modelo slim
```json
{
  "id": "UUID",
  "code": "GIFT10",
  "type": "percent",
  "amount": 10,
  "used": false,
  "isValid": true,
  "minPurchaseValue": 100.00,
  "expiryDate": "2026-12-31T...",
  "startDate": "2026-01-01T..."
}
```

---

## Arquitetura recomendada pra atendimento

```
MCP Trigger
  ├─ buscar_cliente(phone)         → GET /customers/phone/:phone
  ├─ obter_cliente(customer_id)    → GET /customers/:id  [inclui coupon]
  ├─ listar_pedidos(customer_id)   → GET /orders?customerId=:id + paginação
  ├─ obter_pedido(order_id)        → GET /orders/:id
  └─ buscar_cupom(phone)           → GET /coupons/phone/:phone/many
```

`buscar_cupom` é separado de `obter_cliente` porque `obter_cliente` retorna só 1 cupom. `/coupons/phone/:phone/many` retorna todos (cliente pode ter vários).

---

## Quirks confirmados

1. **`/api` prefix não funciona** — docs erradas, use sem o prefixo
2. **`after` com milissegundos falha** — use `2020-01-01T00:00:00Z` (sem `.000Z`)
3. **Busca de cliente só por telefone** — não existe endpoint de busca por nome/email
4. **Cupom embutido no customer** — `GET /customers/:id` já inclui o `coupon` (pode evitar chamada extra)
5. **`GET /coupons/` sem lista geral** — sempre use path param `:phone` ou `:id`

---

## Campos do cliente que NÃO vêm na lista (só no detalhe)

- `coupon` — só em `GET /customers/:id`
- `address` completo (vem na lista, mas não é útil pra atendimento)
- `customFields` — só em endpoint dedicado `/custom-field/customer/:id`

# Padrão de Webhook Transacional (produção)

> ⚠️ **HISTÓRICO** — o padrão vigente pra webhooks transacionais novos está na skill
> `nextags-webhook-builder` (naming canônico snake_case + `origem_pedido`; dedup APÓS
> sucesso do POST, nunca antes — ver `campos_canonicos.md` §5 e Quirk #32 desta skill). Use
> `nextags-webhook-builder` para qualquer transacional novo (pedido pago/enviado/entregue,
> carrinho abandonado). Este arquivo fica como registro do padrão anterior (Rafa/Veuske) e
> não deve ser copiado em projeto novo — os pontos ainda válidos (retry+onError,
> `formatarTelefone`, dedup via Data Table) já foram herdados e refinados na skill vigente.

> **Referência:** Rafa @Walkers (refatoração do Veuske, 2026-05-28)
> Use este padrão pra TODOS os webhooks transacionais novos (Yampi, Shopify, etc.)

Padrão evoluído após observar limitações da v1 (sem dedup, sem retry, payload acoplado ao `event`). A v2 abaixo é robusta a replay, falhas de NexTags e payloads incompletos.

---

## 🎯 Princípios

1. **Idempotência via dedup** — Yampi/Shopify às vezes mandam o mesmo webhook 2-3x (replay automático). Sem dedup, o cliente recebe a mesma mensagem várias vezes.
2. **Switch por STATUS, não por EVENT** — `body.resource.status.data.alias` é mais confiável que `body.event`. Cobre casos onde plataforma manda 1 evento genérico com status variável (ex: `Order.Updated` em vez de `Order.Paid/Shipped/Delivered`).
3. **Resiliência a payload incompleto** — clientes às vezes deletam endereço, telefone, etc. Helpers defensivos evitam crash do workflow.
4. **NexTags pode falhar** — token expira, fila ficou cheia, etc. Retry + continueErrorOutput salvam.
5. **URL hierárquica** — `/webhook/{cliente}/{plataforma}/{evento}` lê mais fácil que `/webhook/{cliente}-{plataforma}-{evento}`.

---

## 🏗️ Arquitetura

```
Webhook                            ← POST /webhook/{cliente}/{plataforma}/{evento}
  ↓
Code (extrair + normalizar)        ← formata phone, extrai campos do payload
  ↓
Verifica se existe (Data Table)    ← busca pedido pelo id
  ↓
Retornou algo? (IF)
  ├─ TRUE  → Status é igual? (IF)
  │           ├─ TRUE  → fim (já disparado, ignora)
  │           └─ FALSE → Switch por status
  └─ FALSE → Switch por status     ← novo pedido
        ↓
        Switch (status)
        ├─ pending   → HTTP NexTags → Cria/Atualiza no banco
        ├─ paid      → HTTP NexTags → Cria/Atualiza no banco
        ├─ shipped   → HTTP NexTags → Cria/Atualiza no banco
        └─ delivered → HTTP NexTags → Cria/Atualiza no banco
```

### Carrinho abandonado (mais simples — não precisa dedup)

```
Webhook → Code (normalizar) → HTTP NexTags
```

Cada carrinho abandonado é único (Yampi dispara 1x por cart), então dedup é desnecessário. Mas ainda use `retryOnFail` no HTTP.

---

## 🧰 Helpers JS (copy-paste no Code node)

### `formatarTelefone(raw)` — normalizador BR completo

```js
function formatarTelefone(rawNumber) {
  if (!rawNumber) return '';
  let digits = String(rawNumber).replace(/\D/g, '');
  if (!digits) return '';

  // Caso 1: já vem com DDI 55 (12 ou 13 dígitos)
  if (digits.startsWith('55') && (digits.length === 12 || digits.length === 13)) {
    const ddd = digits.substring(2, 4);
    const dddInt = parseInt(ddd, 10);
    let localNumber = digits.substring(4);

    if (dddInt >= 11 && dddInt <= 29) {
      // DDD do Sudeste/Sul: fixo começa 2-5; celular começa 6-9
      if (/^[2345]/.test(localNumber)) {
        // Fixo: remover 9 se veio errado
        if (localNumber.length === 9 && localNumber.startsWith('9')) {
          localNumber = localNumber.substring(1);
        }
      } else {
        // Celular: adicionar 9 se faltou
        if (!localNumber.startsWith('9')) {
          localNumber = '9' + localNumber;
        }
      }
    } else if (dddInt >= 30 && dddInt <= 99) {
      // DDD do Norte/Nordeste/Centro-Oeste: alguns ainda usam 8 dígitos sem 9
      if (localNumber.length === 9 && localNumber.startsWith('9')) {
        localNumber = localNumber.substring(1);
      }
    }
    return '55' + ddd + localNumber;
  }

  // Caso 2: sem DDI (10 ou 11 dígitos só com DDD + local)
  const ddd = digits.substring(0, 2);
  const dddInt = parseInt(ddd, 10);
  let localNumber = digits.substring(2);

  if (dddInt >= 11 && dddInt <= 29) {
    if (/^[2345]/.test(localNumber)) {
      if (localNumber.length === 9 && localNumber.startsWith('9')) {
        localNumber = localNumber.substring(1);
      }
    } else {
      if (!localNumber.startsWith('9')) {
        localNumber = '9' + localNumber;
      }
    }
  } else if (dddInt >= 30 && dddInt <= 99) {
    if (localNumber.length === 9 && localNumber.startsWith('9')) {
      localNumber = localNumber.substring(1);
    }
  }
  return '55' + ddd + localNumber;
}
```

**Por que tão detalhado?**
- DDD 11-29 (capitais grandes): celulares OBRIGATORIAMENTE com 9 prefix; fixos NUNCA com 9. Confundir = mensagem não entrega.
- DDD 30-99 (interior): alguns ainda usam 8 dígitos sem o 9 prefix. Adicionar 9 = mensagem não entrega.
- Yampi às vezes manda `5519930000000`, às vezes `(19) 99000-0000`, às vezes só `19930000000`. Normalizador unifica.

### `verificarDado(valor, padrao)` — default safe

```js
function verificarDado(dado, valorPadrao = "Não informado") {
  return dado ? dado : valorPadrao;
}
```

Use pra cada campo que vai virar CUF. Evita `null` ou `undefined` no payload pra NexTags (que rejeita).

### `separarNomeSobrenome(nomeCompleto)` — split nome

```js
function separarNomeSobrenome(nomeCompleto) {
  if (!nomeCompleto || typeof nomeCompleto !== "string") {
    return { nome: "", sobrenome: "" };
  }
  const partes = nomeCompleto.trim().split(/\s+/);
  const nome = partes.shift() || "";
  const sobrenome = partes.join(" ") || "";
  return { nome, sobrenome };
}
```

NexTags `/api/contacts` espera `first_name` e `last_name` separados. Yampi às vezes manda só `customer.data.name` consolidado.

---

## 📊 Data Table de dedup

Criar uma data table por cliente: `<Cliente> <Plataforma> Orders State` com colunas:

| Coluna | Tipo | Função |
|---|---|---|
| `order_id` | string | ID do pedido (Yampi `id` numérico longo) |
| `status` | string | último status disparado (`pending`, `paid`, `shipped`, `delivered`, `cancelled`) |
| `updated_at` | string | ISO timestamp do último update |
| `customer_phone` | string | telefone do cliente (debug) |

**Fluxo:**
1. **Verifica se existe** — Get row por `order_id`
2. **Retornou algo?** — IF
   - **Sim:** compara status atual (do payload) com status no banco
     - Igual → fim (já disparado, dedup)
     - Diferente → continua pra Switch (novo status)
   - **Não:** continua pra Switch (pedido novo)
3. **Switch por status** — 4 branches (pending/paid/shipped/delivered/cancelled)
4. **HTTP Request** — dispara flow NexTags
5. **Cria ou Atualiza** — IF
   - Linha existia → UPDATE status no banco
   - Linha nova → INSERT no banco

**Resultado:** mesmo evento Yampi disparado 5x = 1 mensagem pro cliente.

---

## 🌐 HTTP Request pra NexTags — config robusta

```ts
{
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    parameters: {
      method: 'POST',
      url: 'https://app.nextagsai.com.br/api/contacts',
      sendHeaders: true,
      headerParameters: { parameters: [
        { name: 'accept', value: 'application/json' },
        { name: 'Content-Type', value: 'application/json' },
        { name: 'X-ACCESS-TOKEN', value: '<NEXTAGS_TOKEN>' },
      ]},
      sendBody: true,
      specifyBody: 'json',
      jsonBody: '={{ $json.payload }}',
      options: {},
    },
    retryOnFail: true,            // ← obrigatório
    waitBetweenTries: 5000,       // 5s entre retries
    onError: 'continueErrorOutput' // ← obrigatório, não trava chain
  }
}
```

Sem `retryOnFail` + `onError`, um erro transiente da NexTags trava todo o workflow e o pedido nunca vai pro banco — perdendo dedup pra sempre.

---

## 🏷️ Naming convention pra CUFs

### Padrão Rafa (Veuske)

CamelCase com sufixo de origem:
- `StatusPedidoYMP` (YMP = Yampi)
- `ProdutosPedidoYMP`
- `ValorPedidoYMP`
- `RastreioPedidoYMP`
- `LinkCarrinho`
- `StatusPedidoSHP` (SHP = Shopify)

### Padrão alternativo (snake_case)

snake_case com prefixo de origem:
- `yampi_status_pedido`
- `yampi_resumo_itens`
- `yampi_valor_total`

**Qual usar?** Manter consistência com o que o cliente já tem. Se é greenfield, use o padrão Rafa (CamelCase + sufixo YMP/SHP) — fica visualmente mais limpo no admin NexTags.

---

## 🌐 URL pattern

| Pattern | Exemplo | Quando usar |
|---|---|---|
| `/webhook/{cliente}/{plataforma}/{evento}` | `/webhook/veuske/yampi/pedidos` | ✅ Preferido (Rafa) |
| `/webhook/{cliente}-{plataforma}-{evento}` | `/webhook/veuske-yampi-pedidos` | Aceitável, menos legível |

Padrão hierárquico ajuda quando lê logs do nginx: agrupa por cliente naturalmente.

---

## 📦 Mapeamento Yampi payload → NexTags actions

### Order events (Pago/Enviado/Entregue)

```js
const order = body.resource;
const customer = (order.customer && order.customer.data) || {};
const items = (order.items && order.items.data) || [];

const itensTexto = items.length
  ? items.map(i => 
      `${verificarDado((i.sku && i.sku.data && i.sku.data.title) || i.title)} ` +
      `(Quantidade: ${verificarDado(i.quantity)}, ` +
      `Preço: R$${verificarDado(i.item_value || i.price)})`
    ).join(", ")
  : "Nenhum item";

const nomeCompleto = verificarDado(customer.first_name + ' ' + (customer.last_name || ''));
const { nome, sobrenome } = separarNomeSobrenome(nomeCompleto);

const payload = {
  phone: formatarTelefone((customer.phone && customer.phone.full_number) || customer.phone),
  first_name: nome,
  last_name: sobrenome,
  actions: [
    { action: 'set_field_value', field_name: 'StatusPedidoYMP', value: verificarDado(order.status && order.status.data && order.status.data.name) },
    { action: 'set_field_value', field_name: 'NumeroPedidoYMP', value: verificarDado(order.number || order.id) },
    { action: 'set_field_value', field_name: 'ValorPedidoYMP', value: 'R$ ' + verificarDado(order.value_total) },
    { action: 'set_field_value', field_name: 'ProdutosPedidoYMP', value: itensTexto },
    { action: 'set_field_value', field_name: 'RastreioPedidoYMP', value: verificarDado(order.track_code) },
    { action: 'set_field_value', field_name: 'LinkRastreioYMP', value: verificarDado(order.track_url) },
    { action: 'send_flow', flow_id: <FLOW_ID_DO_STATUS> }
  ]
};
```

### Cart events (Carrinho abandonado)

```js
const cart = body.resource;
const customer = (cart.customer && cart.customer.data) || {};
const items = (cart.items && cart.items.data) || [];

const itensCarrinho = items.length
  ? items.map(i => 
      `${verificarDado((i.sku && i.sku.data && i.sku.data.title) || i.title)} ` +
      `(Quantidade: ${verificarDado(i.quantity)}, Preço: R$${verificarDado(i.price)})`
    ).join(", ")
  : "Não há itens no carrinho";

const linkCheckout = verificarDado(cart.spreadsheet && cart.spreadsheet.data && cart.spreadsheet.data.purchase_url, '').replace(/\s+/g, '');
const valor = verificarDado(cart.totalizers && cart.totalizers.total);
const { nome, sobrenome } = separarNomeSobrenome(verificarDado(customer.name));

const payload = {
  phone: formatarTelefone((customer.phone && customer.phone.full_number) || customer.phone),
  first_name: nome,
  last_name: sobrenome,
  actions: [
    { action: 'set_field_value', field_name: 'StatusPedidoYMP', value: 'Carrinho' },
    { action: 'set_field_value', field_name: 'ProdutosPedidoYMP', value: itensCarrinho },
    { action: 'set_field_value', field_name: 'ValorCarrinho', value: 'R$ ' + valor },
    { action: 'set_field_value', field_name: 'LinkCarrinho', value: linkCheckout },
    { action: 'send_flow', flow_id: <FLOW_ID_CARRINHO_ABANDONADO> }
  ]
};
```

---

## ✅ Checklist de revisão antes de publicar

- [ ] URL hierárquica `/webhook/{cliente}/{plataforma}/{evento}`
- [ ] Code node usa `formatarTelefone`, `verificarDado`, `separarNomeSobrenome`
- [ ] Data table de dedup criada (`order_id`, `status`, `updated_at`)
- [ ] IF "Status é igual?" antes de disparar — evita replay
- [ ] HTTP Request tem `retryOnFail: true` + `waitBetweenTries: 5000` + `onError: continueErrorOutput`
- [ ] Switch por `status.alias`/`status.name` do payload, não por `body.event`
- [ ] CUFs com naming consistente (CamelCase+YMP ou snake_case+yampi_)
- [ ] Token NexTags hardcoded em header (não credential — ver Quirk #22)
- [ ] Pedido novo INSERT no banco; pedido existente UPDATE
- [ ] Carrinho abandonado: workflow separado, sem dedup (cada cart é único)

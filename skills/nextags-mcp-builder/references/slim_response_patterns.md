# Padrões de Slim Response

Heurísticas pra escrever o Code node de slim em backend de qualquer API. Reduz payload em 80-95%, economiza tokens, evita IA confundir com lixo.

---

## Princípio

Toda response da API tem 3 camadas de informação:

1. **Estrutural** (wrappers, paging, meta) — descartar
2. **Essencial** (id, name, price, available, image) — manter
3. **Descritivo** (description, specs, extras) — limpar HTML e manter SE LLM precisar

O Code node faz essa triagem ANTES de devolver ao MCP.

---

## ⚠️ O critério que define "essencial": perspectiva do atendimento

**Essencial não é o que parece importante tecnicamente. É o que um cliente pode perguntar.**

Antes de cortar qualquer campo, faça esta pergunta:

> *"Se um cliente mandar mensagem perguntando sobre isso, a IA consegue responder sem esse campo?"*

- **Não** → manter, independente do peso
- **Talvez** → manter
- **Nunca** → cortar

### O erro do DOLPS (lição aprendida)

`optimize_response` do n8n foi usado pra reduzir payload. Cortou campos que pareciam "metadata" mas eram essenciais pro atendimento (status de pagamento, data estimada de entrega, itens do pedido). A IA deu respostas incompletas ou erradas. Cliente ficou insatisfeito.

**Conclusão: não use `optimize_response` do n8n. É uma caixa preta que não conhece o contexto do atendimento.** Use sempre Code node manual — você decide o que corta.

### Campos que NUNCA devem ser cortados (por pergunta de cliente)

| Pergunta frequente | Campo obrigatório |
|---|---|
| "Qual o status do meu pedido?" | `status`, `status_name` |
| "Onde está minha encomenda?" | `tracking_code`, `tracking_url` |
| "Quando chega?" | `estimated_delivery`, `delivery_date`, `shipping_date` |
| "Meu pagamento foi confirmado?" | `payment_status`, `payment_method` |
| "Quanto foi meu pedido?" | `total` |
| "O que comprei?" | `items[].name`, `items[].quantity`, `items[].price` |
| "Tenho desconto / cashback?" | `coupon.code`, `coupon.value`, `coupon.expires_at`, `giftback.value`, `giftback.expires_at` |
| "Esse produto tem no estoque?" | `available`, `stock_quantity` |
| "Quanto custa?" | `price`, `promotional_price` |
| "Tem no meu tamanho?" | variante `name`/`sku_value` + `available` por variante |

### Campos que podem ser cortados com segurança

- HTML em qualquer campo (limpar, não cortar o campo — ver seção Limpeza de HTML)
- Múltiplas versões de thumbnail (manter 1 URL https)
- Campos de auditoria interna (`created_by`, `updated_by`, `audit_log`, `request_id`)
- Campos de gateway de pagamento internos (`connector_response`, chaves técnicas de transação)
- Metadados de API (`api_version`, `x_request_id`, paging interno já processado)
- Campos vazios, null, "0", "0000-00-00", arrays vazios `[]`
- Campos repetidos que duplicam informação já presente (ex: `status_id` quando `status_name` já diz tudo)
- Dados geográficos técnicos (`geoCoordinates`, lat/lon) — endereço de entrega em texto já basta

### Regra do "talvez"

Se não tem certeza se o cliente vai perguntar sobre aquele campo: **mantém**. O custo de manter campo desnecessário (alguns tokens extras) é muito menor que o custo de esconder informação necessária (resposta errada do agente, cliente insatisfeito, suporte manual).

O slim deve ser agressivo com lixo técnico — e conservador com dados do cliente/pedido/produto.

---

## Template base (TODOS os slim Code nodes seguem isso)

```js
const body = $input.first().json;

// 1. Detecta erro HTTP da API
if (body && body.code && body.code >= 400) {
  return [{
    json: {
      error: body.causes ? body.causes.join("; ") : body.name || body.message || "API error",
      code: body.code
    }
  }];
}

// 2. Detecta erro alternativo (algumas APIs usam shape diferente)
if (body && body.error) {
  return [{
    json: {
      error: typeof body.error === 'string' ? body.error : (body.error.message || JSON.stringify(body.error)),
      code: body.status || body.statusCode || 500
    }
  }];
}

// 3. Extrai e slim
const items = unwrap(body);
const slim = items.map(extractEssentials);

return [{ json: { /* meta + slim */ } }];
```

A IA recebe `{error, code}` em caso de falha (sabe que deu "soluço") ou `{products: [...]}` em caso de sucesso.

---

## Detectando o wrapper da API

| Shape da response | Como unwrap |
|---|---|
| `{data: [...], meta: {...}}` (REST padrão) | `body.data` |
| `{Products: [{Product: {...}}, ...]}` (Tray) | `body.Products.map(x => x.Product)` |
| `{list: [...], paging: {...}}` (VTEX Orders) | `body.list` |
| `{result: [...]}` (algumas APIs custom) | `body.result` |
| `{items: [...]}` (RD Station) | `body.items` |
| Array direto `[{...}, {...}]` (VTEX Catalog público, Nuvemshop) | `body` |
| Objeto direto `{id, name, ...}` (detalhe de 1 item) | `[body]` (envelope em array p/ uniformizar) |

Detecção heurística no Code node:

```js
function unwrap(body) {
  if (Array.isArray(body)) return body;
  if (body.data && Array.isArray(body.data)) return body.data;
  if (body.list && Array.isArray(body.list)) return body.list;
  if (body.items && Array.isArray(body.items)) return body.items;
  if (body.result && Array.isArray(body.result)) return body.result;
  if (body.Products && Array.isArray(body.Products)) {
    return body.Products.map(x => x.Product || x);
  }
  // Detalhe de 1 item
  if (body.Product) return [body.Product];
  if (body.Variant) return [body.Variant];
  // Fallback: trata como item único
  return [body];
}
```

---

## Campos essenciais por entidade

Padrão do que slim mantém vs descarta, por tipo de objeto.

### Produto

**Manter:**
- `id`
- `name` (se for objeto multilíngua, pegar `.pt` ou `.default`)
- `slug` ou `linkText` (pra URLs)
- `price` (e converter — ver seção de preço)
- `promotional_price` se diferente de zero
- `available` ou `availability`
- `category_id` / `category_name` se houver
- `image` (primeira URL `https`, descartando thumbs múltiplas)
- `variant_ids` (lista de IDs de variações, se houver)
- `url` (link da página do produto)

**Descartar:**
- `description` se HTML (a menos que a tool seja de "detalhes" — aí limpar HTML)
- `description_small`
- `ProductImage[].thumbs` (3 versões redundantes)
- `payment_option_html` (HTML cru)
- `payment_option_details` (raramente útil)
- `Properties` se vazio
- `additional_button`, `additional_message` se vazios
- `kit_has_variation`, `is_kit`, `id_campaign` se zerados
- `created`, `release_date`, `activation_date` (a menos que filtragem temporal)
- `metatag`, `related_categories`, `related_products`
- `payment_option_html` em variant também
- Qualquer campo `*_id` redundante com `id` principal
- Campos vazios (`""`, `"0"`, `[]`, `null`, `"0000-00-00"`)

### Pedido

**Manter:**
- `id` (ou `orderId` em VTEX)
- `status` / `status_id` + `status_name`
- `created_at` / `creationDate`
- `total` (com conversão de moeda)
- `items` (slim: nome, sku, qtd, preço por item — não os 30 campos por item)
- `customer` ou `clientProfileData` (slim: nome, email, telefone, document)
- `shipping_address` ou `shippingData` (slim: rua/cidade/cep)
- `tracking_code`, `tracking_url` (se já enviado)
- `payment_method` (slim: tipo, status)

**Descartar:**
- Items com 50+ campos por item (manter ~6 essenciais)
- `paymentData.transactions[].fields[].name` (metadata interna)
- `customFields`, `marketingData` (raramente relevante)
- `commercialConditionData` (B2B só)
- HTML em mensagens internas
- `changesAttachment` (histórico interno)

### Cliente

**Manter:**
- `id` (UUID)
- `email`
- `first_name` + `last_name` (ou `name` se for único campo)
- `phone` (com `country_code` se separado)
- `document` (CPF/CNPJ)
- `last_order_date`
- `order_amount` (total de pedidos, se a API tem)

**Descartar:**
- Histórico de logins
- Sessões
- Cookies/tracking IDs
- Campos de marketing automation
- Tags se vazias

### Variação (variant/SKU)

**Manter:**
- `id` / `sku_id` / `variant_id`
- `sku` (código)
- `product_id` (referência ao pai)
- `name` (ex: "Tamanho G") OU `sku_value` (ex: "G")
- `price` (se diferir do pai)
- `available` (1/0)
- `stock_quantity` se a API expõe
- `image` (se variant tem foto própria)
- `ean` se relevante

**Descartar:**
- `payment_option_html`
- `created`/`updated` (a menos que relevante)
- `dimension` (peso/medida só se atendimento precisa)
- `properties` (a menos que cliente tenha attribute system)

---

## Conversão de preço (CRÍTICO)

| Formato da API | Como tratar | Exemplo |
|---|---|---|
| String em centavos | `parseInt(price) / 100` → number | `"17990"` → `179.90` |
| Number em centavos | `price / 100` | `17990` → `179.90` |
| String em reais decimal | `parseFloat(price)` → number | `"269.90"` → `269.90` |
| Number em reais decimal | passar direto | `269.90` → `269.90` |
| Múltiplas moedas | extrair do field BR/`pt` | depende da API |

Após conversão, slim devolve `price: 269.90` (number) — IA formata como "R$ 269,90" no output.

NUNCA devolva o formato cru se causar ambiguidade.

---

## Limpeza de HTML

Quando o campo `description`/`description_html` vem com tags + entities:

```js
function stripHtml(s) {
  if (!s) return "";
  return String(s)
    .replace(/<[^>]+>/g, " ")          // tags
    .replace(/&nbsp;/gi, " ")           // entities comuns
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/gi, "'")
    .replace(/&[a-z]+;/gi, "")          // qualquer outra entity
    .replace(/\s+/g, " ")               // espaços múltiplos
    .trim();
}
```

Aplicar em `description`, `description_small`, `description_html` se houverem.

---

## Imagens — não retornar lixo

APIs típicas devolvem cada imagem em 3-4 versões (thumb 30, 90, 180, full). LLM só precisa de **1 URL utilizável**.

```js
function pickImageUrl(imageObj) {
  if (!imageObj) return null;
  if (typeof imageObj === 'string') return imageObj;
  // padrão: { http, https, thumbs: { ... } }
  if (imageObj.https) return imageObj.https;
  if (imageObj.url) return imageObj.url;
  if (imageObj.src) return imageObj.src;
  return null;
}

function pickFirstImage(imageArray) {
  if (!Array.isArray(imageArray) || imageArray.length === 0) return null;
  return pickImageUrl(imageArray[0]);
}
```

Pra lista de produtos: `image: pickFirstImage(p.ProductImage)` → 1 URL só.
Pra detalhe de produto (onde cliente pode querer ver várias fotos): `images: p.ProductImage.map(pickImageUrl).filter(Boolean)` → array de URLs.

---

## Casos especiais por API conhecida

### Tray — search com paginação meta

```js
return [{ json: {
  total: (body.paging && body.paging.total) || products.length,
  count_returned: products.length,
  products
}}];
```

### Martz — envelope simples

```js
return [{ json: { data: items, total: body.meta?.total }}];
// OU se a tool é single-item:
return [{ json: items[0] || { error: "Not found", code: 404 }}];
```

### VTEX — duas camadas (publicas vs privadas)

Lembrar: Catalog `pub/` retorna array direto sem wrapper; `pvt/` pode ter wrapper. Detectar com:

```js
const items = Array.isArray(body) ? body : (body.list || [body]);
```

### Nuvemshop — name multilíngua

```js
const name = (typeof item.name === 'object') ? (item.name.pt || item.name.default) : item.name;
```

---

## Como saber quando aplicar slim

Sempre. Mesmo APIs "leves" tendem a engrossar com o tempo. Custo de adicionar Code node é zero. Custo de não adicionar (LLM caro processando 30KB de JSON) é alto.

Exceção: tool de health check (`status_api_*`) onde a IA só precisa saber se API tá viva. Aí slim trivial:

```js
return [{ json: { ok: $input.first().json.status === 'ok' || ($json && !$json.error) }}];
```

---

## Tamanho-alvo da response slim

| Tipo de operação | Tamanho típico antes | Alvo depois |
|---|---|---|
| Busca lista (20 itens) | 10-30 KB | <3 KB |
| Detalhe de 1 item | 5-15 KB | <2 KB |
| Lista catálogo completo (50-300 itens) | 50-200 KB | <15 KB |
| Pedido com 5+ items | 20-50 KB | <5 KB |

Se o slim ainda passa de 5 KB pra busca simples, revise — está deixando lixo.

# Tray Commerce

> Status: 🟢 trabalhada (uso em produção via Mayuí Fit Wear)
> Última atualização: Maio/2026
> Cliente(s) usando: Mayuí Fit Wear

## 🔗 Base URL e ambientes

- **Produção:** `https://{loja-dominio}/web_api/` (varia por loja)
- **`{loja-dominio}`:** domínio público da loja (ex: `www.mayuifitwear.com.br`)
- **Como descobrir:** retornado no OAuth como `api_host`
- **Sem sandbox separado** (Tray usa loja compartilhada de homologação fornecida durante credenciamento)

## 🔐 Autenticação

**Tipo: B — OAuth com refresh**

### Fluxo completo

1. **Credenciamento app** — Tray emite `consumer_key` + `consumer_secret` ao desenvolvedor parceiro
2. **Lojista autoriza** — `GET {api_host}/auth.php?response_type=code&consumer_key={key}&callback={url}` → callback recebe `code` (one-shot, expira ~5min)
3. **Troca de code** — `POST {api_host}/auth` com `{consumer_key, consumer_secret, code}` → retorna `access_token` + `refresh_token` + `api_host` + `store_id`
4. **Refresh** — `GET {api_host}/auth?refresh_token={refresh}` com `Authorization: Bearer {access_token atual}` → renova tokens

### Durações

- `access_token`: **3 horas**
- `refresh_token`: **30 dias**

### Catch-22 crítico

Refresh exige `access_token` VIVO como Bearer. Se ambos expirarem, **full re-OAuth necessário** (cliente reautoriza no admin).

### Implementação n8n

**Caso B completo:**
- Data table `tray_tokens_{cliente}` armazena estado
- Workflow cron 60min faz refresh
- Workflow reset manual pra recovery
- Backends dedicados leem token da data table

Veja exemplo de produção: cliente Tray BR de moda fitness — 8 workflows (1 MCP + 4 backends + 1 refresh cron + 1 reset manual + 1 smoke test).

### Como o app NexTags é criado

A NexTags já é **parceira Tray aprovada** com `consumer_key`/`consumer_secret` próprios. Cada cliente novo Tray:
1. Vai no admin Tray e instala o app NexTags na loja
2. Tray gera `code` específico pra essa loja
3. App NexTags troca code → tokens
4. Cliente recebe `api_host` + tokens, que ele cola na sua infra

**NÃO** precisamos criar app Tray novo por cliente — usamos o app NexTags Tray existente (app_id privado da NexTags).

## 📦 Endpoints essenciais (validados na Mayuí)

Tray tem **endpoints fantasma** na doc (`/products/stocks/{id}`, `/products/{id}/variants`, etc.) que retornam 404. Lista abaixo SÓ inclui endpoints **testados e funcionando**:

### Catálogo

#### `GET {api_host}/products?name=%{termo}%&limit=20`
- **Função:** buscar produtos por nome
- **⚠️ Wildcard `%...%` é OBRIGATÓRIO** — Tray faz SQL LIKE literal sem auto-wildcard
- **Response:** `{ paging, sort, availableFilters, appliedFilters, Products: [{Product: {...}}] }`
- **Dupla camada:** array de `{Product: {...}}`, não array direto

#### `GET {api_host}/products/{id}`
- **Função:** detalhe completo
- **Response:** `{ Product: {...} }` (singular)
- **Campos:** `name`, `description` (HTML), `price`, `category_name`, `ProductImage[]` (com https), `Variant[]` (só IDs)

#### `GET {api_host}/products/variants/{variant_id}`
- **Função:** UMA variação por ID
- **⚠️ `variant_id` ≠ `product_id`** — Variant 101 pode ser de Product 33
- **Response:** `{ Variant: {...} }`
- **Campos:** `Sku: [{type, value}]` (tamanho), `available` (1=estoque, 0=esgotado), `price`, `VariantImage[]`

#### Endpoints fantasma (NÃO USE — retornam 404)
- `/products/{id}/variants`
- `/products/{id}/stocks`
- `/products/stocks/{id}`
- `/stocks?product_id={id}`
- `/categories/{id}`

Para listar variações de um produto, **iterar N+1**: pegar `Variant[].id` do `obter_produto` e chamar `obter_variacao` em cada.

## ⚠️ Quirks documentados

- **Preço em REAIS com decimal** (`"269.90"`), NÃO centavos
- **`available: "0"` = ESGOTADO mas produto existe** (não confundir com "produto removido")
- **`deactivation_date` no passado** = produto removido do catálogo
- **`description` vem com HTML cru** (`<p>`, `&oacute;`) — slim Code node deve limpar
- **Search exige `%...%`** explícito
- **`payment_option_html`** é gigante (HTML escapado) — descartar no slim
- **`ProductImage[].thumbs`** tem 3 tamanhos por imagem — descartar no slim, manter só `https` principal
- **Rate limit:** 180 req/min, 10k req/dia (loja padrão), 50k req/dia (loja corporativa)
- **Catch-22 do refresh** (ver seção Auth)

## 🛡️ Mapeamento operações comuns → endpoints

| Caso de uso | Endpoint Tray |
|---|---|
| Buscar produto por nome | `GET /products?name=%termo%` |
| Detalhe produto | `GET /products/{id}` |
| Listar TODO catálogo (índice) | `GET /products?limit=50&page=N` (paginar) |
| Detalhe variação (tamanho + stock) | `GET /products/variants/{variant_id}` |
| Buscar pedido | `GET /orders?...` (a validar — Mayuí usa Martz pra pedidos) |
| Detalhe pedido | `GET /orders/{id}` (a validar) |

## 📋 Decisão de arquitetura

**Caso B — OAuth com refresh.** Setup completo necessário:

1. Data table `tray_tokens_{cliente}`
2. Workflow Refresh Token (cron 60min)
3. Workflow Reset Token (manual)
4. Workflow Smoke Test (manual)
5. N Backends (1 por operação)
6. MCP com `toolWorkflow` apontando pros backends

**NÃO use `httpRequestTool` direto pra Tray** — sem o backend, não há como ler token vivo da data table.

## 🔗 Links

- Doc: https://developers.tray.com.br/
- Painel parceiros: https://www.tray.com.br/parceiros/
- Última visita: Maio/2026
- Confiabilidade: **MÉDIA** — doc tem endpoints fantasma; sempre validar com chamada real

## 📝 Notas históricas

- **Mayuí Fit Wear** foi a primeira implementação completa Tray na NexTags
- Catálogo tem ~50 produtos pra Mayuí; padrão de "índice completo" (`listar_indice_catalogo`) carrega tudo em 1 call e funciona bem até ~300 produtos
- **Pedidos Mayuí ficam na Martz** (que sincroniza Tray via webhooks deles). Tray API pra pedidos só usar se não tiver Martz como proxy.
- App NexTags Tray ID: `8053` — reutilizado para todos os clientes Tray

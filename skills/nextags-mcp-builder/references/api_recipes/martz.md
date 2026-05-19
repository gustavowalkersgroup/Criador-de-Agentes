# Martz StoreSync

> Status: 🟢 trabalhada (uso em produção via Mayuí Fit Wear)
> Última atualização: Maio/2026
> Cliente(s) usando: Mayuí Fit Wear

## 🔗 Base URL e ambientes

- **Produção:** `https://public.martzapis.com.br/v1/`
- **Sem multi-tenant no path** — a chave API identifica a loja
- **Sem sandbox separado**

## 🔐 Autenticação

**Tipo: A — key fixa via header customizado**

```
x-api-key: <chave-64-hex>
```

- **Credencial n8n:** `httpHeaderAuth` com Name=`x-api-key`, Value=chave
- **Como obter:** Painel Martz → Configurações → Chaves de Acesso → "Chave da API pública"

Token NÃO expira (key estável). Sem OAuth refresh.

## 📦 Endpoints essenciais (validados na Mayuí)

⚠️ Martz tem **endpoints fantasma** na doc Readme.io. Lista abaixo SÓ inclui validados em produção:

### Catálogo (limitado)

#### `GET /products?search={termo}&per_page=10`
- **Função:** buscar produtos sincronizados
- **Response:** `{ data: [...], meta: { total, current_page, last_page, per_page } }`
- **Campos por item (minimalista):** `id`, `name`, `sku`, `integration_id`, `integration_name` (ex: `"vnda"`), `price` (CENTAVOS string), `created_at`
- **⚠️ Lista enxuta** — sem descrição, imagens, estoque, variações

#### `GET /products/{id}`
- **Função:** detalhe (também minimalista)
- **Adiciona:** `categories: [{id, name}]`, `updated_at`
- **NÃO traz:** descrição/HTML/estoque/imagens

**Conclusão sobre catálogo Martz:** usar pouco. Pra catálogo rico, ir direto à API fonte (Tray/Nuvemshop/Shopify). Martz pra catálogo só serve pra IDs e preços simples.

### Pedidos

#### `GET /orders?search={termo}&per_page=10`
- **Função:** busca por nome/email/CPF/telefone (texto livre)
- **Response:** `{ data: [...orders], meta: {...} }`
- **Filtros adicionais:** `product_name`, `customer_id` (UUID), `status`

#### `GET /orders/{order_id}`
- **Função:** detalhe completo
- **⚠️ `order_id` é UUID** — passar número curto retorna 401 ou erro PostgreSQL 22P02

### Clientes

#### `GET /customers?search={termo}&per_page=5`
- **Função:** busca por email/telefone/CPF/nome
- **Response:** `{ data: [...customers], meta: {...} }`
- **Campos:** `id` (UUID), `email`, `first_name`, `last_name`, `phone`, `phone_country_code`, `last_order_date`, `order_amount`, `is_valid_whatsapp_number`

#### `GET /customers/{customer_id}`
- **Função:** detalhe completo
- **⚠️ `customer_id` é UUID**

## ⚠️ Quirks documentados

- **Preço em CENTAVOS string** — `"17990"` = R$ 179,90. Dividir por 100. **Diferente da Tray** (que é decimais em reais)
- **`integration_name`** identifica plataforma fonte (visto: `"vnda"`). Mesmo cliente Tray, Martz pode sincronizar via vnda historicamente — não usar pra inferir tecnologia atual
- **IDs UUID** — `customer_id`, `order_id`, `product_id` são todos UUID. Não passe int/email/telefone como ID — causa erro PostgreSQL 22P02
- **Endpoints fantasma na doc:** `/categories`, `/carts`, `/utils/health` aparecem mas retornam **404 E_ROUTE_NOT_FOUND**
- **Search livre:** o parâmetro `search` em `/orders` e `/customers` aceita qualquer texto (email, nome, telefone, CPF, número de pedido). Bem útil.
- **Envelope `{data, meta}`** padronizado — `optimizeResponse: true` com `dataField: 'data'` no n8n strip o wrapper

## 🛡️ Mapeamento operações comuns → endpoints

| Caso de uso | Endpoint Martz |
|---|---|
| Buscar produto (mínimo) | `GET /products?search=` (lista pobre) |
| Detalhe produto (mínimo) | `GET /products/{id}` |
| Buscar pedido por texto | `GET /orders?search=` |
| Detalhe pedido | `GET /orders/{uuid}` |
| Listar pedidos do cliente | `GET /orders?customer_id={uuid}` |
| Pedidos contendo produto | `GET /orders?product_name=` |
| Buscar cliente | `GET /customers?search=` |
| Detalhe cliente | `GET /customers/{uuid}` |
| Rastreio | já em `/orders/{uuid}` (campo `tracking_code`/`tracking_url`) |
| Categorias | ❌ não existe |
| Carrinhos | ❌ não existe |
| Health check | ❌ não existe |

## 📋 Decisão de arquitetura

Caso A — key fixa. Tools `httpRequestTool` direto. Sem backends, sem data table.

**Quando usar Martz vs API fonte direto:**

- **Use Martz pra pedidos + clientes** — normaliza, tem search livre rico, recebe webhooks da API fonte automaticamente
- **Use API fonte (Tray/Nuvemshop/Shopify) pra catálogo rico** — descrição, imagens, estoque, variações
- **Híbrido é o padrão** — visto na Mayuí (Tray catálogo + Martz pedidos/clientes)

## 🔗 Links

- Doc: https://martz-api-docs.readme.io/reference
- Painel: (a confirmar com cliente)
- Última visita: Maio/2026
- Confiabilidade: **MÉDIA** — Readme.io tem endpoints fantasma; sempre validar com chamada real

## 📝 Notas históricas

- **Mayuí Fit Wear** foi o primeiro uso de Martz na NexTags. Aprendemos os endpoints fantasma na marra.
- Martz funciona como **proxy normalizador multi-plataforma** — uma API consistente independente da plataforma de origem (Tray, Shopify, vnda, etc.)
- Pedidos transacionais (novo, enviado, entregue, carrinho abandonado) já saem por webhooks Martz pra NexTags — **não precisa montar webhooks próprios**

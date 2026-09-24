# FácilZap

> Status: 🟡 documentada a partir do OpenAPI oficial — **ainda sem validação em produção**
> Última atualização: Setembro/2026
> Cliente(s) usando: — (primeiro cliente ainda não implantado)
> Confiabilidade da fonte: **alta** (OpenAPI 3.1 oficial, 141 paths, servido pela própria API)

## 🔗 Base URL e ambientes

- **Produção (API):** `https://api.facilzap.app.br`
- **Painel:** `https://facilzap.app.br`
- **Spec OpenAPI:** `https://api.facilzap.app.br/docs/lojista/v1.json`
- **Swagger UI:** `https://api.facilzap.app.br/docs/lojista/v1`
- **Versão:** path `/docs/lojista/v1`, mas os endpoints **não têm prefixo de versão** (`GET /produtos`, não `/v1/produtos`)
- **Sandbox:** ❌ não existe. Só produção. Sem homologação obrigatória.
- **Variação por loja?** Não — host único para todas as contas.

⚠️ **A doc oficial de autenticação erra o domínio:** mostra `api.facilzap.com.br` no exemplo curl. O correto é **`.app.br`** (confirmado na página de Ambientes e em `servers[0].url` do OpenAPI).

## 🔐 Autenticação

**Tipo: A — Bearer token fixo**

```
Authorization: Bearer <token>
Accept: application/json
```

- **Credencial n8n:** `httpHeaderAuth` com Name=`Authorization`, Value=`Bearer <token>`
- **Token não expira.** Revogação manual no painel.
- **Escopo:** acesso total à conta. Não há escopos/permissões granulares.
- **Só perfil Lojista tem API.** Vendedor/Promotor/Conferente/Afiliado = painel apenas.

**Como obter:**
1. Painel FácilZap → menu lateral **Integrações**
2. Submenu **FácilZap API** → botão **Adicionar API Token**
3. Nomear → **Salvar** → **copiar** (exibido uma única vez)

Revogar: mesma tela → **Remover**.

## 📦 Endpoints essenciais (atendimento)

### Catálogo

#### `GET /produtos`
- **Função:** listar/buscar produtos
- **Params:** `page`, `length`, `search[column]` + `search[value]`, `filtros[...]`
- **`search.column` (enum):** `id` · `nome` · `sku` · `cod_barras`
- **`filtros`:** `catalogo_id`, `catalogo_padrao`, `categoria_id`, `grupo_variacoes_id`, `variacao_id`, `status` (`0`|`1`)
- **Response:** `{ "data": [ ... ] }`
- **Campos úteis:** `id`, `nome`, `descricao`, `sku`, `cod_barras{tipo,numero,numero_interno}`, `imagens[]`, `estoque{}`, `variacoes[]`, `dimensoes{}`, `categorias`, `catalogos[]`, `ativado`, `destaque`, `qualidade_score`

#### `GET /produtos/{id}`
- **Função:** detalhe do produto

#### `GET /variacoes` · `GET /variacoes/{id}`
- **Função:** variações (nível SKU). Também `GET /grupos_variacoes`

#### `GET /categorias` · `GET /catalogos`
- **Função:** taxonomia e catálogos da loja

### Pedidos

#### `GET /pedidos`
- **Função:** listar/buscar pedidos
- **Params:** `page`, `length`, `search[column]` + `search[value]`, `filtros[...]`
- **`search.column` (enum):** `id` · `cliente_id` · `cliente_nome` · `cliente_cpf_cnpj` · `cliente_whatsapp` · `cliente_cep` · `campanha_id`
- **`filtros`:** `data_inicial`, `data_final`, `status`, `status_pagamento`, `vendedor`, `catalogo`, `origem`, `revendedor_id`, `incluir_produtos` (`0`|`1`), `somente_orcamentos` (`0`|`1`)
- 🚨 **Sem `data_inicial`/`data_final` retorna SÓ os pedidos de HOJE.** Documentado. Toda sync histórica precisa do range.
- **Para atendimento:** buscar por `cliente_whatsapp` é o caminho natural (o contato chega pelo WhatsApp)

#### `GET /pedidos/{id}`
- **Função:** detalhe com produtos (`PedidoListagemProdutosResource`)
- **Erros:** `400` "Não foi possível obter os dados do pedido." · `403` "Você não tem permissão para visualizar este pedido."

#### `PATCH /pedidos/{id}/codigo_rastreio`
- **Body:** `{ "codigo_rastreio": "..." }`
- **Função:** gravar rastreio (único write de pedido relevante pra operação)

### Clientes

#### `GET /clientes`
- **Params:** `page`, `length`, `origem`, `ordem`, `search[...]`, `filtros[...]`
- **`search.column` (enum):** `nome` · `cpf_cnpj` · `whatsapp` · `email`
- **`filtros`:** `grupo_id`, `vendedor_id`, `data_ultima_compra`, `aniversariantes`

#### `GET /clientes/{id}` · `POST /clientes`
- **`POST` obrigatório:** `nome`. Opcionais: `cpf_cnpj`, `email`, `whatsapp`, `whatsapp_ddi`, `whatsapp_e164`, `data_nascimento`, `origem` (enum inclui `api`), `status`, `grupos[]`, `demais_dados{}`

## ⚠️ Quirks documentados

- 🚨 **Update é `POST /recurso/{id}`**, não PUT/PATCH — na maior parte da API. Exceções: `PATCH /produtos/{id}`, `PATCH /pedidos/{id}/codigo_rastreio`, `PATCH /pedidos/{id}/fotos/{fotoId}`, `PUT /{marketplace}/.../status`. Gerar cliente do spec sem ler isso quebra.
- 🚨 **Rate limit 2 req/s** (172.800/dia) por conta. É baixo. `429` no excedente. Headers `x-ratelimit-limit` / `x-ratelimit-remaining`. Backoff exponencial obrigatório; nada de paralelismo.
- 🚨 **`GET /pedidos` sem range de data = só hoje.**
- 🚨 **Não existe `POST /pedidos`.** A API não cria pedido. Só leitura + rastreio/fotos/nota/comissão.
- **Sem meta de paginação.** Schema 200 só garante `data`. Paginar até vir vazio.
- **`search`/`filtros` são objetos** → query aninhada estilo Laravel: `?search[column]=nome&search[value]=x&filtros[status]=1`.
- **Tipagem mista de `id`:** pedido é `integer`, carrinho abandonado é `uuid` string. Tratar como string na dedup.
- **`taxa` saiu do `subtotal`** em 15/07/2025 (breaking). `desconto_total` = `desconto` + `desconto_sistema`.
- **Preço em string decimal** nos resources de pedido (`"subtotal": "90"`), mas **number** no payload de webhook (`"subtotal": 90`). Normalizar sempre.
- **`cod_barras` tem externo e interno:** `{tipo, numero, numero_interno}`.
- **Sem sandbox.** Testes em produção — usar catálogo/produto oculto.
- **Erro de validação:** `422` com `{message, errors:{campo:[msgs]}}` (Laravel).

## 🛡️ Mapeamento operações comuns → endpoints

| Caso de uso | Endpoint |
|---|---|
| Buscar produto por nome | `GET /produtos?search[column]=nome&search[value]=` |
| Buscar produto por SKU | `GET /produtos?search[column]=sku&search[value]=` |
| Detalhe de produto | `GET /produtos/{id}` |
| Listar variações (SKU) | `GET /variacoes` ou `variacoes[]` do produto |
| Estoque | campo `estoque{}` do produto/variação |
| Buscar pedido do cliente | `GET /pedidos?search[column]=cliente_whatsapp&search[value]=&filtros[data_inicial]=&filtros[data_final]=` |
| Detalhe do pedido | `GET /pedidos/{id}` |
| Pedidos por CPF | `GET /pedidos?search[column]=cliente_cpf_cnpj&search[value]=` |
| Buscar cliente | `GET /clientes?search[column]=whatsapp&search[value]=` |
| Detalhe do cliente | `GET /clientes/{id}` |
| Rastreio (ler) | `GET /pedidos/{id}` |
| Rastreio (gravar) | `PATCH /pedidos/{id}/codigo_rastreio` |
| Categorias / catálogos | `GET /categorias` · `GET /catalogos` |

## 📋 Decisão de arquitetura recomendada

**Caso A — token fixo.** Tools `httpRequestTool` direto no MCP, sem backend de refresh.

⚠️ **Mas com ressalva de rate limit:** 2 req/s é baixo para um MCP que faz fan-out. Se o agente encadeia buscar_pedidos → obter_pedido → buscar_produto numa mesma volta, estoura. Prefira **backend dedicado por operação** (padrão da skill) e faça a composição no backend, devolvendo slim ao modelo.

Operações sugeridas no MCP:
`buscar_produtos` · `obter_produto` · `buscar_pedidos` · `obter_pedido` · `buscar_cliente` · `obter_rastreio`

## 🔔 Webhooks (ver `nextags-webhook-builder`)

- **Configuração só pelo painel** (Integrações → Webhooks). **Não há API de CRUD de webhook** — `GET /webhooks` devolve o **log de entregas**, não a config.
- Eventos documentados: `pedido_criado` · `carrinho_abandonado_criado`
- Envelope: `{ id (uuid da entrega), evento, dados }`
- Exige HTTP **200**; até **3 tentativas**; **excesso de falhas desativa o webhook sozinho**
- **Sem HMAC.** Proteger por segredo na URL.
- Estágio do pedido vem em flags booleanas: `status_pago`, `status_em_separacao`, `status_separado`, `status_despachado`, `status_entregue`
- Telefone já normalizado em `cliente.whatsapp_e164`

## 🔗 Links

- Doc: https://docs.facilzap.app.br/introducao.md
- Referência: https://api.facilzap.app.br/docs/lojista/v1
- Spec: https://api.facilzap.app.br/docs/lojista/v1.json
- Última visita: 2026-09-22
- Confiabilidade: **alta** (OpenAPI servido pela própria API, não HTML de portal)

## 📝 Notas históricas

- Recipe criada a partir da leitura integral da doc pública (16 páginas) + spec OpenAPI. **Nenhum cliente em produção ainda** — promover para 🟢 após a primeira implantação validada.
- A plataforma cobre muito além de catálogo: PDV/caixa, NF-e/NFC-e, kanban/leads/cashback, campanhas de mensagem e marketplaces (Mercado Livre, Shopee, TikTok Shop). Para atendimento, só o subconjunto acima interessa.
- Existe trilha de **personalização de tema** (HTML/CSS no painel, sem API) — irrelevante para MCP, mas pode aparecer em brief de cliente.

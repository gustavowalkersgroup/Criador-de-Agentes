# Arquitetura Padrão — MCP NexTags

Mapeia o esqueleto comum de TODO MCP construído com essa skill. Decisões variam só nas dimensões marcadas como "depende".

## Esqueleto base (sempre presente)

```
       ┌──────────────────────────────────┐
       │  Cliente (WhatsApp/web)           │
       └────────────┬─────────────────────┘
                    │
       ┌────────────▼─────────────────────┐
       │  NexTags (agente IA + prompt v2.x)│
       └────────────┬─────────────────────┘
                    │  MCP Streamable HTTP
                    ▼
       ┌──────────────────────────────────┐
       │  n8n MCP Server Trigger v2        │
       │  path: /mcp/<slug>                │
       │  auth: none (default) | headerAuth│
       └─┬────────────────────────────────┘
         │
         │  N tools subnodes (httpRequestTool OU toolWorkflow)
         │
         ▼ depende do tipo de auth (ver abaixo)
```

## Decisão 1: tipo de auth da API fonte

### Caso A — Auth simples (API key fixa)

API tem 1 chave que não precisa renovar. Exemplos: Martz (`x-api-key`), Nuvemshop (`Authentication: bearer <fixed>`).

**Arquitetura:**

```
MCP Trigger v2
   │
   ├─ tool 1 (httpRequestTool com credencial → API)
   ├─ tool 2 (httpRequestTool com credencial → API)
   └─ tool N ...
```

Sem backends, sem data table, sem cron. **Mais simples possível.**

**Tools usam:**
- `authentication: 'genericCredentialType'`
- `genericAuthType: 'httpHeaderAuth'` ou `httpQueryAuth`
- `credentials: { httpHeaderAuth: newCredential('<Nome>') }`

### Caso B — OAuth com refresh

API exige fluxo OAuth com `access_token` curto + `refresh_token` longo. Exemplos: Tray (3h/30d), Bling, MercadoLibre.

**Arquitetura:**

```
                Data Table: <slug>_tokens
                (store_id, api_host, access_token, refresh_token,
                 expires_at, refresh_expires_at, last_refresh_at)
                   ▲                    ▲
                   │ lê                 │ atualiza
                   │                    │
MCP Trigger v2     │           Workflow: Refresh Token
   │               │           (Schedule 60min)
   │               │
   ├─ tool 1 (toolWorkflow → Backend 1 → lê token → API)
   ├─ tool 2 (toolWorkflow → Backend 2 → lê token → API)
   └─ tool N ...

Workflow auxiliar: Reset Token (manual, recovery)
Workflow auxiliar: Smoke Test (manual, diagnóstico)
```

**Por que backends dedicados em vez de tool direto:**

`@n8n/n8n-nodes-langchain.toolWorkflow.workflowInputs` descarta valores estáticos — só passa adiante o que vem via `$fromAI`. Não dá pra usar router único com parâmetro `operation`. Solução: 1 workflow backend por operação. Cada um tem seu próprio Execute Workflow Trigger com 1 input dinâmico.

Veja `quirks_n8n.md` pra detalhes.

### Caso C — Híbrido multi-API

Cliente tem várias APIs (ex: Tray pra catálogo + Martz pra pedidos). Combine A e B no mesmo MCP.

**Arquitetura:**

```
MCP Trigger v2
   ├─ [Tray] tool 1 → Backend Tray 1 → token (data table)
   ├─ [Tray] tool 2 → Backend Tray 2 → token (data table)
   ├─ [Tray] tool 3 → Backend Tray 3 → token (data table)
   ├─ [Martz] tool 4 (httpRequestTool direto, x-api-key)
   └─ [Martz] tool 5 (httpRequestTool direto, x-api-key)

Cron de Refresh + Reset Manual + Smoke Test só pro lado Tray.
```

Cada API tem credencial separada. Data table só pras com refresh. Tools no MCP misturam tipos.

## Decisão 2: granularidade das tools

### Princípio: 1 endpoint → 1 tool

Não combine. Não crie tools "multi-uso" com `operation` param — fica difícil pro LLM decidir e o `workflowInputs` quirk piora isso.

### Princípio: nomes pt-BR snake_case

A IA fala português com o cliente. Nomes em PT facilitam decisão da IA. Use snake_case (`buscar_produtos`, não `BuscarProdutos`).

### Princípio: descrição que ensina QUANDO usar

Cada tool tem `description` que explica:
- Quando usar (gatilhos na fala do cliente)
- Quando NÃO usar (caso contrário comum)
- O que retorna (campos principais)
- Dependências (ex: "use após `buscar_cliente` pra obter o UUID")

Bom exemplo (Mayuí):

> Busca produtos por nome ou parte do nome (LIKE no nome). Use quando o cliente DISSE explicitamente o nome do produto/coleção (ex: "Legging Groove"). Se for busca por cor/categoria genérica, prefira listar_indice_catalogo antes.

Ruim (genérico):

> Busca produtos na API.

### Quantidade ideal: 5-15 tools por MCP

Menos de 5 = IA fica limitada.
Mais de 15 = IA tem dificuldade de escolher; risco de duplicidade. Se cliente pediu 25 operações, agrupe (ex: `buscar_pedidos` que aceita filtro vs criar 5 tools de busca-com-filtro-X).

## Decisão 3: slim response

TODO backend tem Code node ao final que:

1. **Detecta erro 4xx/5xx** da API e retorna `{error, code}` estruturado (IA usa pra dizer "soluço")
2. **Extrai só campos essenciais** (drop HTML cru, thumbs múltiplas, metadata interna, payment_option_html, etc.)
3. **Limita tamanho** (paginação interna, max items)
4. **Converte tipos** se necessário (preço string → number formatado, datas → ISO)

Sem slim, payloads chegam a 30 KB+ por chamada — caro em tokens. Com slim, fica <2 KB típico.

Veja `slim_response_patterns.md` (próxima iteração).

## Decisão 4: estratégia de busca de catálogo (e-commerce)

Se a API serve catálogo e clientes falam em português mas catálogo tem nomes em inglês fashion (situação comum em moda):

**Adicione tool `listar_indice_catalogo`** que retorna o catálogo inteiro com (id, name, price, available, image, slug). IA usa como first-pass pra match semântico ("marrom" → encontra "Coffee/Mocha/Expresso") sem precisar de dicionário PT→EN no prompt.

Funciona pra catálogos até ~300 produtos. Acima disso, considerar busca vetorial (fora do escopo dessa skill).

Veja a estratégia completa na memória do projeto Mayuí (`estrategia_busca_catalogo.md`).

## Convenção de nomes de workflows

| Tipo | Nome | Exemplo |
|---|---|---|
| MCP Trigger | `<Cliente> MCP` | `Mayuí Fit Wear MCP` |
| Backend de operação | `<API> Backend — <Operação>` | `Tray Backend — Obter Produto` |
| Refresh token | `<API> Refresh Token — <Cliente>` | `Tray Refresh Token — Mayuí` |
| Reset manual | `<API> Reset Token — <Cliente> (manual)` | `Tray Reset Token — Mayuí (manual)` |
| Smoke test | `<API> Smoke Test — <Cliente> (manual)` | `Tray Smoke Test — Mayuí (manual)` |

## Convenção de nomes de data tables

`<api>_tokens_<slug-cliente>` — ex: `tray_tokens_mayui`, `bling_tokens_skinlab`.

Colunas padrão pra data table de OAuth:

| Coluna | Tipo | Origem |
|---|---|---|
| `store_id` | string | resposta do OAuth (ou identificador único da loja na API) |
| `api_host` | string | resposta do OAuth (base URL) |
| `access_token` | string | `access_token` do OAuth |
| `refresh_token` | string | `refresh_token` do OAuth |
| `expires_at` | date | conversão de `date_expiration_access_token` pra ISO |
| `refresh_expires_at` | date | conversão de `date_expiration_refresh_token` pra ISO |
| `last_refresh_at` | date | quando o último refresh rodou |

## Convenção de paths MCP

`/mcp/<slug-cliente-kebab-case>` — ex: `mayui-fit-wear-mcp`, `neurofood-nextags-nuvemshop`.

URL final: `https://nextags.app.br/mcp/<slug>`.

⚠️ NEVER use `/sse` no path final pra NexTags. O n8n MCP Trigger v2 expõe `POST` direto no path base (Streamable HTTP). `/sse` é GET pra clients legados (OpenAI agent).

## CORS

MCP Trigger v2 expõe parâmetro de CORS em `Allow Origins`. Default = `*` (permite qualquer origem). Mantenha assim a menos que o cliente exija restrição.

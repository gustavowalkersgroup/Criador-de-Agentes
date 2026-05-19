# Descoberta da API a partir da Doc

Como descobrir base URL, endpoints, params e shape de resposta de QUALQUER API REST, com qualquer formato de doc.

---

## Hierarquia de fontes (em ordem de preferência)

### 1. OpenAPI / Swagger spec (melhor caso)

**Pistas que existe:**
- Doc tem botão "Download OpenAPI" / "Swagger JSON"
- URL tipo `/openapi.json`, `/swagger.json`, `/api-docs`
- Doc renderizada com Redoc, Swagger UI, ou Stoplight

**Como usar:**

```bash
curl <doc-url>/openapi.json > spec.json
# ou
curl <doc-url>/openapi.yaml > spec.yaml
```

Depois roda `scripts/parse_openapi.py` (a ser implementado) que extrai:
- `servers[].url` → base URL
- `paths[].{method}.parameters[]` → params
- `paths[].{method}.responses` → shape esperado
- `components.securitySchemes` → auth scheme

Determinístico, rápido, completo.

### 2. Postman Collection

**Pistas:**
- Doc oferece "Run in Postman" button
- Cliente envia arquivo `.json` exportado do Postman

**Como usar:** `scripts/parse_postman.py` (a implementar). Extrai mesma info da OpenAPI mas no formato Postman.

### 3. Doc HTML estática (Readme.io, GitBook, custom)

**Pistas:**
- URL tipo `<api>.readme.io/reference/...`
- `docs.<api>.com.br`
- Wikis/GitBook

**Como usar:** WebFetch + análise interativa. Cada página de endpoint tem que ser visitada. Frequentemente esconde curl atrás de login.

Procedimento:
1. WebFetch da home da doc → pega lista de endpoints (menu lateral)
2. Pra cada endpoint relevante, WebFetch da página específica
3. Extrai: path, method, params (query/header/body), exemplos de curl
4. Salva em `references/api_recipes/<api>.md`

**Limitação real:** docs BR frequentemente listam endpoints que NÃO existem na API real (visto na Martz). Sempre confirme com chamada real.

### 4. Chamada de teste real

**Quando usar:** doc incompleta ou ambígua. Sempre como último passo de validação.

Procedimento:
1. Faça GET no endpoint candidato
2. Veja a resposta:
   - 200 com payload → endpoint existe, payload é fonte de verdade pro shape
   - 401/403 → endpoint existe, problema de auth
   - 404 → endpoint não existe (ou path errado)
   - 500/502 → bug na API, marca pendência
3. Documente shape real em `references/api_recipes/<api>.md`

**Nota:** a IA explorando endpoints deve usar credenciais reais que o usuário forneceu — não chuta tokens.

### 5. Engenharia reversa do frontend (último recurso)

Se doc é zero e API tem frontend público (loja, painel), inspecione network tab do browser:
- Vê requests reais
- Extrai endpoints, headers, body
- Replica no n8n

**Casos onde isso já salvou:** algumas APIs Tray, paineis Magazord.

**Cuidado:** ToS de algumas plataformas proíbe automação não-autorizada. Use com discernimento e só pra clientes que têm relação contratual com a API fonte.

---

## Mapeamento da descoberta → workflows

Depois de descobrir tudo, prepare:

### 1. Base URL

Vai em variável global do workflow ou hardcoded:
```ts
const API_BASE = 'https://api.<service>.com.br/v1';
```

Se mudar entre stores (ex: Tray devolve `api_host` por loja no OAuth), vai como coluna na data table.

### 2. Auth scheme

Decide caso A/B/C/D/E (ver `auth_patterns.md`).

### 3. Endpoints relevantes

Filtre. Não exponha tudo. Pra cada operação que IA precisa, escolhe 1 endpoint primário.

| Caso de uso comum | Endpoints típicos |
|---|---|
| Busca produto por nome | `GET /products?search=` ou `?name=` |
| Detalhe de produto | `GET /products/{id}` |
| Listar variações | `GET /products/{id}/variants` ou similar |
| Buscar pedido | `GET /orders?search=` |
| Detalhe pedido | `GET /orders/{id}` |
| Listar pedidos do cliente | `GET /orders?customer_id=` ou `GET /customers/{id}/orders` |
| Buscar cliente | `GET /customers?search=` |
| Detalhe cliente | `GET /customers/{id}` |

### 4. Shape de resposta

Documente em recipe:

```markdown
**`GET /products?search=X`:**
Wrapper: `{ data: [...], meta: {total, page} }` OU `{ Products: [{Product: {...}}] }` OU `{ result: [...] }`

Campos por produto:
- `id` (formato: int/string/UUID)
- `name`
- `price` (formato: cents/reais, string/number)
- ...
```

Isso vira input pra:
- Decidir o slim Code node
- Documentar `output` em `tool.config` no SDK
- Escrever descrição da tool com clareza

### 5. Quirks observados

Anote tudo que destoa do esperado:
- Search precisa de wildcard explícito? (Tray)
- IDs são UUID, int, ou slug? (Martz UUID)
- Preço em centavos ou reais? (Martz cents, Tray reais)
- Existem endpoints fantasma na doc? (Martz /categories, /carts)
- Rate limit? (Tray 180/min, 10k/dia)
- Paginação por `page+limit` ou `cursor`? Default size?
- Resposta de erro tem shape padronizado?

Vai pro recipe `references/api_recipes/<api>.md`.

---

## Quando perguntar ao usuário em vez de descobrir

A IA não deve perder tempo descobrindo coisas que o usuário sabe de cabeça. Pergunte direto:

- ✅ Quais operações exatas a IA precisa fazer (escopo)
- ✅ Credenciais do cliente (key, OAuth code)
- ✅ Flow IDs NexTags (SAC, pipeline, tabela medidas)
- ✅ URL base se não estiver óbvia na doc

Descubra:
- 🔍 Auth scheme (a partir da doc)
- 🔍 Path/method de cada endpoint
- 🔍 Params (obrigatórios e opcionais)
- 🔍 Shape real de resposta (teste real)
- 🔍 Quirks (teste real)

Princípio: o usuário decide o **negócio** (quais tools, qual persona, qual flow), a IA descobre a **técnica** (como falar com a API).

---

## Template de recipe

Quando descobrir uma API nova, salve em `references/api_recipes/<api>.md` com esse template:

```markdown
# <Nome da API>

## Base URL
`https://...`

## Auth
- Tipo: A (key fixa) / B (OAuth) / C (Basic) / D (assinada) / E (sem auth)
- Header/Query: `<nome>: <valor>`
- Exemplo curl: `curl -H "..." <base>/...`

## Endpoints úteis

### GET /...
- Params: ...
- Response shape: ...
- Quirks: ...

### GET /.../{id}
- ...

## Quirks gerais
- Preço: centavos/reais
- IDs: UUID/int/slug
- Search: precisa wildcard?
- Rate limit: ...
- Paginação: ...

## Doc oficial
- URL: ...
- Última visita: ...
- Confiabilidade: alta/média/baixa (Readme.io tem endpoints fantasma; OpenAPI é confiável)
```

Recipe vira referência pra próxima vez que essa API aparecer em outro cliente. Só precisa atualizar quirks específicos do cliente (URL/store_id) ao reaproveitar.

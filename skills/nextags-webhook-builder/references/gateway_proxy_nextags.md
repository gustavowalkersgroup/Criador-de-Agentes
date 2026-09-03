# NexTags API Gateway Proxy — integração sem credencial nativa

> Adaptação fiel do documento oficial "Guia de Integração: NexTags API Gateway Proxy & Conversor
> para LLMs" (enviado pelo dono do projeto, 2026-09-03). Todo valor que parecia credencial real
> foi trocado por placeholder: `<SESSION_BEARER_TOKEN>`, `<NEXTAGS_GATEWAY_TOKEN>`, `<IP_N8N>`.
>
> **Evidência de produção:** Cantarola Backend — Buscar Produtos chama
> `https://api.nextags.com.br/v1/gateway/stores/{storeId}/products` (corpus de 21 workflows n8n em produção). O proxy
> não é teoria: já roda como fonte de dados de um MCP em cliente ativo.

⚠️ Não confundir as duas bases:

| Base | Para quê | Header |
|---|---|---|
| `https://api.nextags.com.br/v1/gateway/...` | **Proxy** para a API da plataforma de e-commerce (Tray, Nuvemshop, Yampi, Bagy) | `Authorization: Bearer <NEXTAGS_GATEWAY_TOKEN>` |
| `https://app.nextagsai.com.br/api/...` | **API da NexTags** (contatos, CUFs, tags, flows) — ver `api_nextags.md` | `X-ACCESS-TOKEN: <NEXTAGS_ACCESS_TOKEN>` |

---

## 0. Quando usar (e quando não)

**Use o Gateway Proxy quando:**

| Situação | Por quê |
|---|---|
| MCP de leitura (buscar pedido, rastreio, produto) e o cliente **não entregou** a credencial nativa da plataforma | O integrador NexTags já guarda o `access_token`/`refresh_token` da loja em Vault e faz auto-renovação. O n8n nunca vê a credencial. |
| A credencial nativa **expira/rotaciona** e ninguém quer manter refresh token no n8n | O proxy renova sozinho. Um token `nxt_live_...` no n8n em vez de OAuth. |
| **Polling transacional** (carrinho abandonado, status de pedido) numa plataforma já integrada ao integrador NexTags | Mesma rota, mesmo token, sem segundo cadastro de credencial. |
| Precisa de trilha de auditoria por chamada (IP, User-Agent, latência) | O gateway registra tudo; a API nativa não. |

**NÃO use quando:**

- A loja **não está cadastrada** no integrador NexTags (sem `storeId` não há proxy) → use a API nativa com credencial do cliente.
- A plataforma não tem adaptador (`501 PLATFORM_NOT_SUPPORTED`) → API nativa.
- O que você quer é a **API da NexTags** (criar contato, setar CUF, disparar flow) → isso é `app.nextagsai.com.br/api/`, não o gateway. Ver `api_nextags.md`.
- Volume alto de backfill sem throttle → o gateway tem rate limit por minuto e coloca o token em **quarentena** se você estourar 2x o limite.

---

## 1. Arquitetura

O Gateway Proxy (`/v1/gateway/stores/:store_id/*`) é um intermediário transparente entre robôs,
automações, agentes de IA e as APIs das plataformas de e-commerce integradas.

| Vantagem | Detalhe |
|---|---|
| **Zero vazamento de credencial nativa** | A automação não conhece `access_token`/`refresh_token` da Tray, Nuvemshop ou Yampi. O integrador guarda em Vault AES-256-GCM e auto-renova. |
| **Acesso a 100% dos endpoints** | Qualquer rota suportada pela plataforma de origem passa pelo proxy (mais de 1.000 endpoints). |
| **Gateway Shield** | Rate limiting por minuto via Redis, proteção anti-scraping de dados de cliente (LGPD), isolamento estrito de loja (*store isolation*). |
| **Trilha de auditoria** | Cada requisição registra IP de origem, User-Agent, latência, método e endpoint. |

### Fluxo de execução de uma chamada

```
LLM / Robô externo
   │  GET /v1/gateway/stores/6/products
   │  Authorization: Bearer <NEXTAGS_GATEWAY_TOKEN>
   ▼
NexTags Gateway Proxy
   │──► Gateway Shield + Redis : valida hash do token, IP, status e escopos (proxy:passthrough)
   │◄── autorizado, rate limit OK
   │──► Vault (AES-256-GCM)    : descriptografa o access token nativo da loja #6
   │◄── credenciais válidas (auto-refresh se necessário)
   │──► API da plataforma      : repassa a chamada com a auth nativa injetada
   │◄── resposta original
   ▼
Resposta em JSON com o status HTTP real da plataforma
```

Dois formatos de rota são aceitos:

- **Direto:** `https://api.nextags.com.br/v1/gateway/stores/:store_id/:endpoint_nativo`
- **Explícito:** `https://api.nextags.com.br/v1/gateway/stores/:store_id/proxy/:endpoint_nativo`

---

## 2. Criar o Gateway Token via API

### Passo 1 — Login administrativo

Token de sessão com privilégio de `admin`, `integrador` ou `operador`:

```bash
curl -X POST "https://api.nextags.com.br/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "<EMAIL_ADMIN>",
    "password": "<SENHA_ADMIN>"
  }'
```

Resposta:

```json
{
  "message": "Login realizado com sucesso.",
  "token": {
    "type": "bearer",
    "token": "<SESSION_BEARER_TOKEN>",
    "expires_at": "2026-08-21T11:47:00.000-03:00"
  },
  "user": { "id": 1, "email": "<EMAIL_ADMIN>", "role": "admin" }
}
```

### Passo 2 — Emitir o Gateway Token

**Endpoint:** `POST /v1/admin/gateway-tokens`
**Headers:** `Authorization: Bearer <SESSION_BEARER_TOKEN>` + `Content-Type: application/json`

```json
{
  "storeId": 6,
  "name": "Robo_Conversor_LLM",
  "scopes": ["proxy:passthrough", "products:read", "orders:read"],
  "rateLimitPerMinute": 60,
  "dailyCustomerLimit": 100,
  "allowedIps": []
}
```

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `storeId` | number | **Sim** | ID interno da loja no NexTags Integrador (ex.: `6`). |
| `name` | string | **Sim** | Nome do robô/agente. A API anexa o sufixo de rastreabilidade `_{plataforma}_{storeId}_{userId}`. |
| `scopes` | array[string] | **Sim** | Permissões. Para proxy transparente, **`proxy:passthrough` é obrigatório** (ou `*`). |
| `rateLimitPerMinute` | number | Não | Requisições por minuto (padrão `60`). Só `admin` customiza. |
| `dailyCustomerLimit` | number | Não | Cota diária de consultas sensíveis de cliente (padrão `100`). |
| `allowedIps` | array[string] | Não | IPs permitidos, ex.: `["<IP_N8N>"]`. Vazio `[]` = qualquer IP. |
| `expiresAt` | string (ISO) | Não | Expiração opcional, ex.: `"2026-12-31T23:59:59Z"`. |

```bash
curl -X POST "https://api.nextags.com.br/v1/admin/gateway-tokens" \
  -H "Authorization: Bearer <SESSION_BEARER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "storeId": 6,
    "name": "Agente_LLM_Conversor",
    "scopes": ["proxy:passthrough", "products:read", "orders:read"],
    "rateLimitPerMinute": 120
  }'
```

Resposta `201 Created`:

```json
{
  "token": {
    "id": 14,
    "userId": 1,
    "storeId": 6,
    "name": "Agente_LLM_Conversor_tray_123456_1",
    "tokenPrefix": "<PREFIXO_DO_TOKEN>",
    "scopes": ["proxy:passthrough", "products:read", "orders:read"],
    "status": "active",
    "rateLimitPerMinute": 120,
    "dailyCustomerLimit": 100,
    "createdAt": "2026-08-20T11:50:00.000Z"
  },
  "secretKey": "<NEXTAGS_GATEWAY_TOKEN>",
  "message": "Token gerado com sucesso. Guarde o segredo em local seguro, ele não será exibido novamente."
}
```

### Passo 3 — Guardar a chave

⚠️ O valor de **`secretKey`** (formato `nxt_live_...`) é exibido **uma única vez**. Guarde em
variável de ambiente `NEXTAGS_GATEWAY_TOKEN` ou em **credencial nomeada do n8n** (preferível a
hardcode no node — corpus de 21 workflows n8n em produção). Se perder, regenere com
`POST /v1/admin/gateway-tokens/:id/regenerate-secret`.

⚠️ **Nunca** escreva o valor real num arquivo desta skill, num sticky note ou num relatório.
Placeholder sempre.

---

## 3. De-para: URL nativa → URL do proxy

### Algoritmo de parsing

1. **Loja (`:store_id`)** — o ID numérico da loja **no NexTags** (ex.: `6`), não o id da loja na plataforma.
2. **Remover protocolo e host** — `https://api.tray.net`, `https://api.tiendanube.com`, `https://api.nuvemshop.com.br`, `https://api.dooki.com.br`, `https://api.bagy.com.br`.
3. **Remover o prefixo de raiz da plataforma:**
   - **Tray / Bagy** → remover `/web_api` do início do path.
   - **Nuvemshop / Tiendanube** → remover `/v1/{id_loja_nuvemshop}` ou `/v1`.
   - **Yampi / Dooki** → remover `/v2`.
4. **Remover parâmetros de auth da query string** — `access_token`, `token`, `app_token`, `auth`, `user_token`, `user_secret_key`. **Manter todos os filtros legítimos** (`page`, `limit`, `sort`, `status`, `created_at_min`, `fields`).
5. **Montar:** `URL_FINAL = https://api.nextags.com.br/v1/gateway/stores/{store_id}/{PATH_LIMPO}`
6. **Injetar headers:** `Authorization: Bearer <NEXTAGS_GATEWAY_TOKEN>` + `Content-Type: application/json`.

Método HTTP e body JSON originais são mantidos intactos.

### Tabela de transformação por plataforma

| Plataforma | URL nativa original | URL no Gateway Proxy (loja #6) |
|---|---|---|
| **Tray Commerce** | `GET https://api.tray.net/web_api/products?access_token=xyz&page=1` | `GET https://api.nextags.com.br/v1/gateway/stores/6/products?page=1` |
| **Tray Commerce** | `POST https://api.tray.net/web_api/products/123/variants?access_token=xyz` | `POST https://api.nextags.com.br/v1/gateway/stores/6/products/123/variants` |
| **Tray Commerce** | `GET https://api.tray.net/web_api/orders/999/payments?access_token=xyz` | `GET https://api.nextags.com.br/v1/gateway/stores/6/orders/999/payments` |
| **Nuvemshop** | `GET https://api.nuvemshop.com.br/v1/458721/products?limit=20` | `GET https://api.nextags.com.br/v1/gateway/stores/6/products?limit=20` |
| **Nuvemshop** | `PUT https://api.nuvemshop.com.br/v1/458721/orders/88/fulfill` | `PUT https://api.nextags.com.br/v1/gateway/stores/6/orders/88/fulfill` |
| **Yampi / Dooki** | `GET https://api.dooki.com.br/v2/orders?status=paid` | `GET https://api.nextags.com.br/v1/gateway/stores/6/orders?status=paid` |
| **Yampi / Dooki** | `GET https://api.dooki.com.br/v2/products/555/skus` | `GET https://api.nextags.com.br/v1/gateway/stores/6/products/555/skus` |
| **Bagy 3.0** | `GET https://api.bagy.com.br/web_api/customers/10` | `GET https://api.nextags.com.br/v1/gateway/stores/6/customers/10` |

---

## 4. System prompt do conversor (quando o de-para é feito por LLM)

Prompt oficial para instanciar um agente conversor (GPT, Gemini, Claude). Use quando o volume de
rotas a converter é grande; para 3-4 rotas fixas de um transacional, converta na mão pela tabela
acima e escreva a URL final no node.

```
# ROLE AND PURPOSE
Você é o "NexTags Gateway Converter AI", um especialista em integração de APIs de e-commerce.
Seu objetivo é receber uma URL nativa de API (Tray, Nuvemshop, Yampi, Bagy, etc.), o método HTTP,
os parâmetros de consulta e o corpo da requisição, e convertê-los precisamente em uma chamada
para o Gateway Proxy Centralizado da NexTags.

# CONTEXT & BASE CONFIGURATION
- Base URL do Integrador: {{NEXTAGS_API_BASE_URL}} (ex.: https://api.nextags.com.br)
- Header de Autenticação do Gateway: Authorization: Bearer {{NEXTAGS_GATEWAY_TOKEN}}
- Formato padrão da rota proxy: {{NEXTAGS_API_BASE_URL}}/v1/gateway/stores/{{STORE_ID}}{{ENDPOINT_LIMPO}}

# PARSING RULES
1. Extração do endpoint:
   - Tray ou Bagy: remova o host e o prefixo /web_api.
   - Nuvemshop / Tiendanube: remova o host e o prefixo /v1/{id_loja_nativo} ou /v1.
   - Yampi / Dooki: remova o host e o prefixo /v2.
2. Query params:
   - Remova as chaves de autenticação: access_token, token, app_token, auth, user_token, user_secret_key.
   - Preserve paginação, filtros e ordenação (page, limit, status, created_at_min, fields, sort).
3. Método e payload:
   - Mantenha exatamente o método HTTP original (GET, POST, PUT, PATCH, DELETE).
   - Se houver payload JSON, mantenha-o intacto.
4. Segurança:
   - Nunca inclua tokens nativos da plataforma na URL ou nos headers de saída.
     Use exclusivamente o Bearer token do NexTags Gateway.

# OUTPUT FORMAT
Sempre retorne um JSON estruturado com as chaves:
  target_url, http_method, headers (Authorization + Content-Type), body, curl_command
```

Exemplo de saída esperada do conversor (texto cru, não vai dentro de fence no prompt do agente):

{"target_url":"https://api.nextags.com.br/v1/gateway/stores/6/products?page=2","http_method":"GET","headers":{"Authorization":"Bearer <NEXTAGS_GATEWAY_TOKEN>","Content-Type":"application/json"},"body":null,"curl_command":"curl -X GET ..."}

---

## 5. Exemplos práticos (cURL)

### Tray Commerce — GET produtos com filtro

Nativa: `https://api.tray.net/web_api/products?access_token=old_token_xyz&page=2&limit=50&sort=desc` (loja #6)

```bash
curl -X GET "https://api.nextags.com.br/v1/gateway/stores/6/products?page=2&limit=50&sort=desc" \
  -H "Authorization: Bearer <NEXTAGS_GATEWAY_TOKEN>" \
  -H "Content-Type: application/json"
```

### Tray Commerce — POST criar variante com body

Nativa: `https://api.tray.net/web_api/products/123/variants?access_token=old_token_xyz` (loja #6)

```bash
curl -X POST "https://api.nextags.com.br/v1/gateway/stores/6/products/123/variants" \
  -H "Authorization: Bearer <NEXTAGS_GATEWAY_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "Variant": {
      "product_id": "123",
      "price": "59.90",
      "stock": 10,
      "reference": "VAR-AZUL-G"
    }
  }'
```

### Nuvemshop — GET pedidos pagos

Nativa: `https://api.nuvemshop.com.br/v1/987654/orders?payment_status=paid&fields=id,total,status` (loja #12)

```bash
curl -X GET "https://api.nextags.com.br/v1/gateway/stores/12/orders?payment_status=paid&fields=id,total,status" \
  -H "Authorization: Bearer <NEXTAGS_GATEWAY_TOKEN>" \
  -H "Content-Type: application/json"
```

### Yampi / Dooki — GET detalhe de pedido

Nativa: `https://api.dooki.com.br/v2/orders/105492` (loja #15)

```bash
curl -X GET "https://api.nextags.com.br/v1/gateway/stores/15/orders/105492" \
  -H "Authorization: Bearer <NEXTAGS_GATEWAY_TOKEN>" \
  -H "Content-Type: application/json"
```

---

## 6. Snippets

### Node.js / TypeScript (fetch nativo)

```typescript
import fetch from "node-fetch";

async function consultarProdutosProxy() {
  const STORE_ID = 6;
  const GATEWAY_URL = `https://api.nextags.com.br/v1/gateway/stores/${STORE_ID}/products?page=1`;
  const GATEWAY_TOKEN = process.env.NEXTAGS_GATEWAY_TOKEN!;

  try {
    const response = await fetch(GATEWAY_URL, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${GATEWAY_TOKEN}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Erro Gateway (${response.status}): ${JSON.stringify(errorData)}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Falha ao consumir Proxy:", error);
  }
}
```

### Python 3 (requests)

```python
import os
import requests

def executar_proxy_post():
    store_id = 6
    gateway_url = f"https://api.nextags.com.br/v1/gateway/stores/{store_id}/products/123/variants"
    gateway_token = os.getenv("NEXTAGS_GATEWAY_TOKEN")

    headers = {
        "Authorization": f"Bearer {gateway_token}",
        "Content-Type": "application/json"
    }
    payload = {"Variant": {"price": "49.90", "stock": 25}}

    response = requests.post(gateway_url, json=payload, headers=headers, timeout=30)
    if response.status_code >= 400:
        print(f"Erro {response.status_code}: {response.text}")
        response.raise_for_status()
    return response.json()
```

### n8n (HTTP Request node)

- **URL:** `https://api.nextags.com.br/v1/gateway/stores/{{ $json.store_id }}/orders/{{ $json.order_id }}`
- **Authentication:** `genericCredentialType` → `httpBearerAuth`, credencial nomeada
  `<Cliente> Gateway NexTags` (preferível ao Bearer hardcoded — corpus de 21 workflows n8n em produção).
- **Options:** `retryOnFail: true`, `waitBetweenTries: 3000`, `onError: continueRegularOutput`
  (chamada a terceiro; a chamada final à NexTags usa `continueErrorOutput` — ver
  `padrao_transacional.md` §7).
- ⚠️ Não repasse `access_token` da plataforma em query nem em header. O gateway injeta a auth nativa.

---

## 7. Segurança, escopos e erros

### Gateway Shield

1. **Isolamento de loja** — cada Gateway Token é atrelado a **uma** `storeId`. Token da loja #6
   chamando `/v1/gateway/stores/12/...` recebe `403 CROSS_STORE_ACCESS_PROHIBITED` **e o token vai
   para quarentena automática**. Em cliente multi-loja: **um token por loja**, nunca reaproveitar.
2. **Validação de escopo** — proxy transparente exige `proxy:passthrough` (ou `*`).
3. **Rate limiting por minuto** — acima da taxa configurada retorna `429`. Passar de **2x** a taxa
   em curto período coloca o token em quarentena por detecção de flood. Em polling/backfill:
   `batchSize 1` + intervalo, exponential backoff no 429.

### Tabela de erros

| HTTP | Código | Causa provável | Ação corretiva |
|---|---|---|---|
| `401` | `MISSING_GATEWAY_TOKEN` | Header `Authorization` não foi enviado. | Enviar `Authorization: Bearer <NEXTAGS_GATEWAY_TOKEN>`. |
| `401` | `INVALID_GATEWAY_TOKEN` | Chave inválida ou digitada errado. | Conferir o segredo ou emitir novo token. |
| `403` | `INSUFFICIENT_SCOPE` | Token sem o escopo `proxy:passthrough`. | Atualizar via `PUT /v1/admin/gateway-tokens/:id`. |
| `403` | `CROSS_STORE_ACCESS_PROHIBITED` | `:store_id` da URL difere da loja do token. | Usar o ID correto ou criar token da loja certa. **O token entra em quarentena.** |
| `403` | `TOKEN_QUARANTINED_ABUSE` | Token em quarentena de segurança. | Painel `/admin/gateway-tokens` ou `toggle-status`, depois de sanar a causa. |
| `429` | `RATE_LIMIT_EXCEEDED` | Frequência acima do limite. | Exponential backoff ou pedir aumento do limite. |
| `501` | `PLATFORM_NOT_SUPPORTED` | Plataforma da loja sem adaptador de proxy. | Conferir a plataforma cadastrada; cair para a API nativa. |

⚠️ **Armadilha de diagnóstico:** `403 CROSS_STORE_ACCESS_PROHIBITED` num workflow que "funcionava"
quase sempre é workflow clonado de outro cliente com o `storeId` antigo na URL — mesma classe de bug
do token clonado (Wazzu usando conta da Hebreus Doze, `antipadroes.md` §6). E o efeito aqui é pior:
além de falhar, **queima o token da loja certa por quarentena**.

---

## 8. Checklist antes de usar o proxy num workflow

- [ ] A loja está cadastrada no integrador NexTags e você tem o `storeId` **correto** (confirmado, não inferido).
- [ ] Gateway Token emitido **para essa loja**, com escopo `proxy:passthrough`.
- [ ] Token guardado em credencial nomeada do n8n (ou env var), **nunca** em arquivo da skill.
- [ ] URL montada pelo algoritmo do §3 (prefixo da plataforma removido, params de auth removidos, filtros preservados).
- [ ] `rateLimitPerMinute` compatível com a frequência do cron; throttle no polling.
- [ ] Tratamento explícito de `401`/`403`/`429`/`501` (não tratar "resposta vazia" como erro de credencial — ver a lição da sonda Degan, corpus de 21 workflows n8n em produção: `registros: []` pode ser resultado legítimo).
- [ ] Sticky note registra: `storeId`, plataforma, escopos do token e "de onde veio" o store_id.

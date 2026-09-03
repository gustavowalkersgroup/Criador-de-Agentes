# Padrões de Autenticação — mapeamento API → n8n

Como reconhecer cada tipo de auth na doc REST de uma API qualquer e implementar no n8n.

---

## Como identificar o tipo de auth a partir da doc

Procure por essas pistas no doc da API:

| Pista | Provável tipo |
|---|---|
| "API key in header `X-API-Key`" / "Authorization: Bearer <fixed>" sem menção a refresh | **A — Key fixa** |
| "OAuth 2.0", "Authorization Code Flow", `/auth?response_type=code` | **B — OAuth com refresh** |
| "Basic Auth", `Authorization: Basic <base64>` | **C — Basic Auth** |
| "Signed request" / HMAC / signature com timestamp | **D — Assinada** (raro, complexo) |
| Vários endpoints públicos sem auth | **E — Sem auth** |
| "Bearer Token" mas com `Authorization: Bearer <fixed-token>` que nunca expira | **A** (key fixa disfarçada de Bearer) |

Se a doc não for clara — faça chamada de teste sem auth e veja o erro:
- `401 Unauthorized` → exige auth
- `403 Forbidden` → exige auth mas escopo errado
- Resposta normal → sem auth (E)

---

## A — Key fixa (header ou query)

**Como funciona:** cliente recebe 1 string, manda em todo request, não expira (ou expira em meses).

**Variações:**
- Header customizado: `x-api-key: <key>`, `Api-Key: <key>`, `X-Tenant-Token: <key>`
- Authorization header com prefixo fixo: `Authorization: Bearer <fixed-key>` (Bearer é só prefixo, não OAuth)
- Query param: `?api_key=<key>`, `?token=<key>`

### Implementação n8n

**Tools direto no MCP** (sem backends). Use `httpRequestTool` com credencial genérica:

```ts
const apiCred = newCredential('<Nome> API key');

const tool1 = tool({
  type: 'n8n-nodes-base.httpRequestTool',
  version: 4.4,
  config: {
    name: 'buscar_produtos',
    parameters: {
      method: 'GET',
      url: '<base>/products',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',  // ← ou httpQueryAuth se for query
      // ... outros params
    },
    credentials: { httpHeaderAuth: apiCred }
  }
});
```

**Tipo de credencial conforme a variação:**

| Variação | `genericAuthType` | Configurar credencial com |
|---|---|---|
| Header customizado | `httpHeaderAuth` | Name = nome do header (ex: `x-api-key`), Value = key |
| `Authorization: Bearer <fixed>` | `httpHeaderAuth` | Name = `Authorization`, Value = `Bearer <key>` |
| Query `?api_key=X` | `httpQueryAuth` | Name = `api_key`, Value = key |
| `Authorization: <key>` (sem prefixo) | `httpHeaderAuth` | Name = `Authorization`, Value = key |

**Exemplos reais:**
- Martz: `x-api-key` → `httpHeaderAuth(Name=x-api-key, Value=<64hex>)`
- Nuvemshop: `Authentication: bearer <fixed>` → `httpHeaderAuth(Name=Authentication, Value=bearer <token>)`
- Shopify Admin: `X-Shopify-Access-Token` → `httpHeaderAuth(Name=X-Shopify-Access-Token, Value=<token>)`

### Brief check pra esse caso

Cliente deve fornecer:
- A string da key
- Onde foi gerada (admin do serviço, dashboard de dev, etc.)
- Validade prevista (se houver)

---

## B — OAuth com refresh

**Como funciona:**
1. Cliente autoriza app via página de consent → API devolve `code` curtinho
2. App troca `code` + `consumer_key` + `consumer_secret` por `access_token` + `refresh_token`
3. `access_token` expira rápido (1h-24h tipicamente)
4. Antes de expirar, app usa `refresh_token` pra renovar e ganhar `access_token` novo
5. `refresh_token` expira em dias-meses; se vencer, refaz OAuth completo

**Pistas na doc:**
- Mencionar "OAuth 2.0", "Authorization Code Grant"
- Endpoint tipo `/auth?response_type=code&client_id=...`
- Resposta de troca tem `access_token` + `refresh_token` + `expires_in`
- Refresh endpoint (`/auth/refresh`, `/oauth/token`, etc.)

### Implementação n8n

**Setup completo (5 workflows + 1 data table):**

1. **Data table `<api>_tokens_<slug>`** com colunas: `store_id`, `api_host`, `access_token`, `refresh_token`, `expires_at`, `refresh_expires_at`, `last_refresh_at`

2. **Workflow Refresh Token** (Schedule + read DT + HTTP refresh + Set + write DT)
   - Cron: cada 60 min (ou metade do tempo de validade do access_token, o que for menor)
   - Chama refresh endpoint com `refresh_token`
   - Atualiza data table com novos tokens

3. **Workflow Reset Token (manual)** — pra recovery quando refresh quebra (>30d sem refresh, etc.). Tem Set com tokens hardcoded (usuário cola valores novos), e update na data table.

4. **Workflow Smoke Test (manual)** — testa endpoints da API com token vivo, sem passar pelo MCP. Diagnóstico.

5. **N Workflows Backend** (1 por operação) — chamados pelo MCP via `httpRequestTool` na URL interna `http://n8n:5678/webhook/<path>`:
   - Webhook Trigger (o `httpRequestTool` chama por HTTP interno)
   - Data table get (lê token vivo)
   - HTTP request à API com `Authorization: Bearer {{ token }}`
   - Code node de slim

6. **Workflow MCP** com nodes `httpRequestTool` apontando pros backends (não `toolWorkflow` — ver `arquitetura_padrao.md`, Caso B)

**Exemplo de produção:** cliente Tray (moda fitness). Setup típico = 8 workflows no n8n: 1 MCP + 4 backends (índice, search, detalhe, variação) + 1 refresh cron + 1 reset manual + 1 smoke test. IDs específicos são gerados na criação — consulte o painel n8n do cliente.

### Brief check pra esse caso

Cliente deve fornecer:
- `consumer_key` e `consumer_secret` do app cadastrado na API fonte
- `code` gerado após autorização do lojista (one-shot, expira rápido)
- URL base / api_host (geralmente devolvida no OAuth)
- Documentação da API
- Confirmação de validade do `access_token` e `refresh_token`

Se faltar, oriente o cliente sobre como obter (cada API tem fluxo diferente).

### Catch-22 conhecido

Algumas APIs (ex: Tray) exigem o `access_token` atual VIVO como Bearer no momento de fazer refresh. Se o access_token expirar antes do cron rodar, refresh falha. Mitigation:
- Cron a cada 60min (com access_token de 3h, isso dá 3 janelas de refresh dentro da validade)
- Reset Token manual sempre disponível pra recovery

---

## C — Basic Auth

**Como funciona:** `Authorization: Basic <base64(user:password)>` em todo request.

**Pistas na doc:** "HTTP Basic Auth", "username + password" como credencial.

### Implementação n8n

`httpRequestTool` com:

```ts
authentication: 'genericCredentialType',
genericAuthType: 'httpBasicAuth',
credentials: { httpBasicAuth: newCredential('<Nome> Basic') }
```

Credencial n8n pede username + password separados. n8n monta o header.

### Quando aparece

Raro em APIs modernas. Comum em ERPs legados (TOTVS, SAP), serviços de email transacional antigos.

---

## D — Assinada (HMAC, signature)

**Como funciona:** cliente compute uma assinatura por request usando chave secreta + payload + timestamp. Ex: AWS Sig V4, Shopify webhook signature.

**Pistas na doc:** referências a "signature", "HMAC-SHA256", "compute the signature using your secret".

### Implementação n8n

n8n não tem suporte nativo robusto pra HMAC custom. Opções:
1. **Code node** que computa a assinatura em JS antes do request HTTP
2. **Node específico** se a API tiver (ex: Shopify tem node nativo)

**Esforço:** alto. Se possível, oriente o cliente a pedir endpoint não-assinado da API.

### Quando aparece

AWS, alguns gateways de pagamento (Cielo, Stone), Shopify (pra webhooks).

---

## E — Sem auth

**Como funciona:** API pública. Qualquer chamada passa.

**Pistas na doc:** documentação tipo "open API", "public endpoints", ausência de header de auth nos exemplos.

### Implementação n8n

Tools direto com `authentication: 'none'`:

```ts
{
  parameters: {
    method: 'GET',
    url: '<base>/endpoint',
    authentication: 'none',
    // ...
  }
}
```

### Quando aparece

APIs gov-BR (BrasilAPI, ViaCEP), API de cotação de moeda, Google Maps Places (com restrições por API key separada às vezes).

---

## Decisão final: qual estratégia usar

Fluxo de decisão da skill:

```
1. Brief lista N APIs com docs.
2. Para cada API:
   a. WebFetch da doc / parse OpenAPI / parse Postman
   b. Identifica tipo de auth (A/B/C/D/E)
   c. Salva em `references/api_recipes/<api>.md` (se já não existir)
3. Decide arquitetura no MCP:
   - Todas APIs são A/C/E → tools direto, sem backends
   - Pelo menos 1 API é B → backends + data table + refresh + reset + smoke
   - Mix → híbrido
4. Gera workflows conforme arquitetura
5. Lista pendências de credenciais ao usuário
```

---

## Não testado / fora do escopo

- **OAuth client_credentials grant** (sem user authorization) — pode ser tratado como Caso A (key fixa) se o token não expira; se expira, vira Caso B simplificado (sem refresh_token, só client_id + secret pra renovar).
- **mTLS** (certificado cliente) — fora do escopo dessa skill v1.
- **Token rotation com refresh por request** (rotativo a cada chamada) — extremamente raro, exigirá custom code.

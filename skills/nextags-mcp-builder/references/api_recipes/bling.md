# Bling ERP v3

> Status: 🟢 trabalhada (doc oficial Bling v3 + cross-check com doc interna)
> Última atualização: Maio/2026
> Cliente(s) usando: (nenhum em produção ainda, mas doc validada)

## 🔗 Base URL e ambientes

- **Produção:** `https://api.bling.com.br/Api/v3`
- **Sem sandbox separado** — usar conta de teste do cliente
- **Versão atual:** v3 (Bling deprecou v2 — não usar)

## 🔐 Autenticação

**Tipo: B — OAuth 2.0 com refresh**

### URLs

- **Authorize:** `https://www.bling.com.br/Api/v3/oauth/authorize`
- **Token:** `https://www.bling.com.br/Api/v3/oauth/token`
- **Grant types suportados:** `authorization_code`, `refresh_token`

### Fluxo Authorization Code

1. **Redirect do lojista:**
   ```
   GET https://www.bling.com.br/Api/v3/oauth/authorize
       ?response_type=code
       &client_id=<client_id>
       &state=<csrf_token>
       &redirect_uri=<callback_url>
   ```
2. **Callback recebe** `?code=XXX&state=YYY`
3. **App troca code por tokens:**
   ```
   POST https://www.bling.com.br/Api/v3/oauth/token
   Authorization: Basic <base64(client_id:client_secret)>
   Content-Type: application/x-www-form-urlencoded

   grant_type=authorization_code&code=XXX
   ```

### Resposta de Token

```json
{
  "access_token": "...",
  "token_type": "Bearer",
  "expires_in": 21600,
  "refresh_token": "...",
  "scope": "..."
}
```

- **`access_token` dura 6 horas** (21600 segundos — confirmado)
- **`refresh_token` dura 30 dias**

### Headers padrão nos requests à API

```
Authorization: Bearer <access_token>
Accept: application/json
Content-Type: application/json
```

### Refresh do token

```
POST https://www.bling.com.br/Api/v3/oauth/token
Authorization: Basic <base64(client_id:client_secret)>
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&refresh_token=<refresh_token>
```

⚠️ **Quirk vs Tray:** Bling usa **Basic Auth no header** (client_id:client_secret em base64) NA HORA do refresh, diferente da Tray que usa Bearer do access_token vivo. Não há catch-22 — refresh funciona mesmo com access_token expirado.

### Implementação n8n

**Caso B completo, padrão:**
- Data table `bling_tokens_<cliente>` com colunas: `tenant_id`, `client_id`, `client_secret_encrypted`, `access_token`, `refresh_token`, `expires_at`, `refresh_expires_at`, `last_refresh_at`
- Workflow Refresh Token — cron 4h (margem confortável sobre os 6h de validade)
- Workflow Reset Token (manual)
- Workflow Smoke Test (manual)
- Backends dedicados por operação

**Cadência de refresh recomendada:** 4h (ou 240 min) — `access_token` dura 6h, então 4h dá 1.5 janelas de retry dentro da validade.

## 🚦 Rate Limit

- **3 requisições por segundo** por usuário/app — **MUITO apertado**
- Resposta de excesso: `429 Too Many Requests`
- **Implementar backoff exponencial** em retries
- Cuidado em buscas que paginam — não dispare paralelo

## 📦 Endpoints essenciais (confirmados na doc)

### Pedidos (Vendas)

| Método | Path | Função |
|---|---|---|
| GET | `/pedidos/vendas` | Listar com filtros |
| GET | `/pedidos/vendas/{id}` | Detalhe |
| POST | `/pedidos/vendas` | Criar pedido |
| PUT | `/pedidos/vendas/{id}` | Atualizar |
| DELETE | `/pedidos/vendas/{id}` | Deletar |
| PATCH | `/pedidos/vendas/{id}/situacoes/{idSituacao}` | **Mudar situação (útil pra cancelar/concluir)** |

### Produtos

| Método | Path |
|---|---|
| GET/POST | `/produtos` |
| GET/PUT/DELETE | `/produtos/{id}` |
| GET/POST | `/produtos/variacoes` |
| GET/POST | `/produtos/estruturas` |
| GET/POST | `/produtos/fornecedores` |
| GET/POST | `/produtos/lojas` |

### Contatos (clientes + fornecedores)

| Método | Path |
|---|---|
| GET/POST | `/contatos` |
| GET/PUT/DELETE | `/contatos/{id}` |
| GET | `/contatos/tipos` |

### Notas Fiscais

| Path | Descrição |
|---|---|
| `/nfe` | NF-e (produto físico) |
| `/nfce` | NFC-e (consumidor final) |
| `/nfse` | NFS-e (serviço) |
| `POST /nfe/{id}/enviar` | Emitir |
| `POST /nfe/{id}/cancelar` | Cancelar |

### Estoques

| Método | Path |
|---|---|
| GET | `/estoques/saldos` |
| POST | `/estoques` (lançamento) |
| GET/POST | `/depositos` |

### Financeiro

| Path | Função |
|---|---|
| `/contas/pagar` | Contas a pagar |
| `/contas/receber` | Contas a receber |
| `/contas-contabeis` | Plano de contas |
| `/borderos` | Borderôs bancários |
| `/categorias/receitas-despesas` | Categorias |
| `/formas-de-pagamento` | Formas de pagamento |

## 🔍 Paginação e filtros padrão

Todos os endpoints de listagem usam:

```
?pagina=1
&limite=100             # máx 100
&dataEmissaoInicial=YYYY-MM-DD
&dataEmissaoFinal=YYYY-MM-DD
&idSituacao=<código>
&idVendedor=<id>
&numero=<numero>
```

⚠️ **Atenção:** é `pagina` e `limite` (português), não `page` e `limit`.

## 🪝 Webhooks

### Validação obrigatória

- Header: `X-Bling-Signature-256`
- Valor: **HMAC-SHA256 do raw body, usando `client_secret` como chave**
- **NUNCA confiar nos dados do payload** — sempre buscar via API com o `id` do evento
- Garantir idempotência via `eventId` (chave de cache tipo `bling:event:{eventId}`)
- **Resposta:** HTTP 200 em até **5 segundos**

### Eventos típicos

- `pedido_venda.criado`
- `pedido_venda.alterado`
- `pedido_venda.deletado`
- `nfe.emitida`
- `nfe.cancelada`
- `estoque.alterado`
- `produto.criado`
- `produto.alterado`
- `produto.deletado`

### Padrão de processamento

```
Webhook chega → valida HMAC → confere idempotência → busca dados via API → processa → 200
```

## 📨 Formato de erros

```json
{
  "error": {
    "type": "VALIDATION_ERROR",
    "message": "Mensagem curta",
    "description": "Descrição detalhada",
    "fields": [
      { "msg": "Campo inválido", "element": "nomeDoCampo" }
    ]
  }
}
```

### Códigos HTTP

| Código | Significado |
|---|---|
| 400 | Bad request |
| 401 | Token inválido/expirado |
| 403 | Sem escopo (role insuficiente) |
| 404 | Não encontrado |
| 422 | Erro de validação |
| 429 | Rate limit (3 req/seg) |
| 5xx | Erro interno Bling |

## ⚠️ Quirks documentados

- **Bling NÃO permite key fixa** — só OAuth. Sempre Caso B.
- **Rate limit muito apertado** (3 req/seg) — backoff exponencial obrigatório
- **Refresh usa Basic Auth**, não Bearer (diferente da Tray)
- **Paginação em português:** `pagina` + `limite` (não `page`/`limit`)
- **IDs internos vs SKU:** `idProduto` (interno Bling) ≠ `codigo` (SKU). Documentar bem em descrição de tools
- **Situação de pedido:** códigos numéricos (`idSituacao`) — buscar lista de mapeamento na conta do cliente. Geralmente: 6=Em aberto, 9=Atendido, 12=Cancelado, mas varia
- **3 tipos de "pedido":** `/pedidos/vendas`, `/pedidos/compras`, `/pedidos/de-trocas` — pra atendimento e-commerce, sempre `/pedidos/vendas`
- **Webhook payload NÃO é confiável** — sempre fazer GET na API com o ID do evento
- **Webhook requer HMAC validation** — implementar em Code node n8n com `crypto.createHmac('sha256', clientSecret).update(rawBody).digest('hex')`

## 🛡️ Mapeamento operações comuns → endpoints

| Caso de uso | Endpoint Bling |
|---|---|
| Buscar produto por nome | `GET /produtos?nome=...` |
| Detalhe produto | `GET /produtos/{idProduto}` |
| Estoque produto | `GET /estoques/saldos?idsProdutos[]={id}` |
| Buscar pedido | `GET /pedidos/vendas?numero=...` ou `?dataEmissaoInicial=` |
| Detalhe pedido | `GET /pedidos/vendas/{idPedidoVenda}` |
| Pedidos do cliente | `GET /pedidos/vendas?idContato={idContato}` |
| Buscar cliente/fornecedor | `GET /contatos?pesquisa=...` |
| Detalhe cliente | `GET /contatos/{idContato}` |
| Cancelar pedido | `PATCH /pedidos/vendas/{id}/situacoes/12` (cód cancelado) |
| NFe de pedido | (geralmente em `pedidos/vendas/{id}` no campo `nfe`) |

## 📋 Decisão de arquitetura

**Caso B — OAuth com refresh.** Setup completo necessário:

1. **Data table** `bling_tokens_<cliente>`
2. **Workflow Refresh Token** — cron 4h (margem sobre 6h do access_token)
3. **Workflow Reset Token** — manual, recovery se ambos tokens expirarem
4. **Workflow Smoke Test** — manual, testa endpoints isoladamente
5. **N Backends** — 1 por operação (drible workflowInputs quirk)
6. **MCP** com toolWorkflow apontando pros backends

**Diferença vs Tray no refresh workflow:**
```ts
// Tray (Bearer atual + refresh_token na query)
url: expr('{{ $json.api_host }}/auth?refresh_token={{ $json.refresh_token }}'),
headers: { Authorization: 'Bearer {{ $json.access_token }}' }

// Bling (Basic Auth client + refresh_token no body x-www-form-urlencoded)
url: 'https://www.bling.com.br/Api/v3/oauth/token',
method: 'POST',
headers: { Authorization: 'Basic <base64(client_id:client_secret)>' },
contentType: 'form-urlencoded',
body: { grant_type: 'refresh_token', refresh_token: '...' }
```

## 🔗 Links

- Doc oficial: https://developer.bling.com.br/referencia
- Cadastro de app Bling: https://www.bling.com.br/Api/v3/aplicativos
- Última visita: Maio/2026
- Confiabilidade: **alta** (doc oficial OpenAPI + PR interno validado)

## 📝 Notas históricas

- **Status passou de 🟡 stub pra 🟢 trabalhada em 2026-05-12** após cross-check de doc interna confirmar especificações que estavam em conhecimento geral.
- **Doc complementar de integração n8n específica** pode existir conforme o setup — vale documentar quirks adicionais (validação HMAC, refresh, etc.) na primeira integração real.
- **Casos de uso típicos:** lojas que usam Bling pra emissão de NFe + controle de estoque + integração com marketplaces (ML, Shopee, próprio site). Cliente NexTags com Bling provavelmente é loja física+online integrada querendo atendimento unificado.
- **Pedidos de venda no Bling têm `numero` (humano) e `id` (interno)** — clientes mencionam `numero`, IA precisa buscar com filtro.

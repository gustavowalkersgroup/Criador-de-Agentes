# <Nome da API>

> Status: 🟢 trabalhada (uso em produção) | 🟡 stub (precisa exploração) | 🔴 abandonada
> Última atualização: <data>
> Cliente(s) usando: <lista>

## 🔗 Base URL e ambientes

- **Produção:** `https://...`
- **Homologação/Sandbox:** `https://...`
- **Versão atual:** `v1` / `v2` / `2025-03` / etc.
- **Variação por loja?** sim/não (se sim, como descobrir o host correto)

## 🔐 Autenticação

- **Tipo:** A (key fixa) / B (OAuth refresh) / C (Basic) / D (assinada) / E (sem auth)
- **Como mandar:**
  ```
  Header: <nome>: <valor>
  OU Query: ?<param>=<valor>
  ```
- **Credencial n8n:** `<credentialType>` com Name=`<header>`, Value=`<valor>`
- **Como obter credenciais:** (admin do serviço, processo de OAuth, etc.)
- **OAuth flow (se aplicável):**
  - Authorize URL: `...`
  - Token URL: `...`
  - Refresh URL: `...`
  - access_token dura: `...`
  - refresh_token dura: `...`

## 📦 Endpoints essenciais

### `GET /<caminho>`
- **Função:** ...
- **Params:** ...
- **Response shape:** `{ ... }`
- **Quirks:** ...

### `GET /<caminho>/{id}`
- **Função:** ...
- **Params:** ...
- **Response shape:** `{ ... }`
- **Quirks:** ...

(adicione tantos quanto forem relevantes pra atendimento — produto, pedido, cliente, carrinho, etc.)

## ⚠️ Quirks documentados

- Preço em centavos ou reais? Como?
- IDs: UUID / int / slug?
- Search: precisa wildcard explícito?
- Rate limit: ...
- Paginação: `page+limit` / cursor / offset?
- Resposta de erro: shape padronizado?
- Endpoints fantasma na doc oficial?
- HTML cru em descrições?
- Outros gotchas...

## 🛡️ Mapeamento operações comuns → endpoints

| Caso de uso | Endpoint VTEX equivalente |
|---|---|
| Buscar produto por nome | `GET ...` |
| Detalhe de produto | `GET .../{id}` |
| Listar variações (SKU) | `GET .../{id}/...` |
| Estoque por SKU | `GET ...` |
| Buscar pedido | `GET .../orders?search=` |
| Detalhe pedido | `GET .../orders/{id}` |
| Listar pedidos cliente | `GET ...` |
| Buscar cliente | `GET ...` |
| Detalhe cliente | `GET ...` |
| Rastreio | `GET ...` |

## 📋 Decisão de arquitetura recomendada

(Caso A/B/C — ver `arquitetura_padrao.md`)

- Se Caso A: lista as N tools como `httpRequestTool` direto no MCP
- Se Caso B: lista os N backends (1 por op) + cron de refresh + reset manual

## 🔗 Links

- Doc oficial: ...
- Última visita: ...
- Confiabilidade: alta (OpenAPI) / média (HTML mas verificada) / baixa (Readme.io com endpoints fantasma)

## 📝 Notas históricas

- (Bugs encontrados em produção, decisões importantes, casos especiais)

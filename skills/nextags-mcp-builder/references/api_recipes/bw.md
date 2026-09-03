# BW Commerce

> Status: 🟢 trabalhada (uso em produção)
> Última atualização: 2026-09-03
> Cliente(s) usando: Joias Degan (catálogo no Praticx, pedido e cliente na BW)

A BW é a fonte de **pedido e cliente**. Em cliente que também tem Praticx, o catálogo fica no
Praticx — a divisão de fonte de verdade entra no relatório, para ninguém depois procurar
produto na BW nem pedido no Praticx.

## 🔗 Base URL e ambientes

- **Produção:** varia por cliente — **peça a base URL e confirme com uma chamada real antes de
  montar as tools.** Não existe host único; na entrega do Degan a base URL da BW ficou como
  pendência bloqueante justamente por isso.
- **Versão:** conforme a spec OpenAPI entregue pelo cliente.
- **Variação por loja?** Sim. Nunca deduza o host a partir de outro cliente BW.

## 🔐 Autenticação

- **Tipo:** A (key fixa, via header).
- **Como mandar:** header de token da BW, com o nome exato que a spec do cliente indicar.
- **Credencial n8n:** credencial nomeada (`<Cliente> BW Commerce Token`) — padrão desde
  2026-09-03. Confira o vínculo depois de **todo** `update_workflow` (Quirk #22 e #3).
- **Como obter:** com o admin da loja, no painel BW.

## ⚠️ Quirks documentados

### A BW responde HTTP 200 **sempre**, inclusive em erro

Esse é o quirk que define o desenho de toda tool BW. Credencial errada, rota inválida, token
vencido: tudo volta `200` com o envelope

```json
{ "registros": [], "erros": [ ... ], "totalRegistros": 0 }
```

Uma tool que trate "200 = sucesso" e ignore `erros[]` faz o agente dizer **"não encontrei seu
pedido"** quando o que houve foi falha de autenticação. O cliente ouve uma informação errada e
ninguém vê erro nenhum no log.

- **Não use `dataField`** nas tools de BW: o envelope precisa chegar inteiro ao slim, para o
  Code node olhar `erros[]` antes de olhar `registros[]` (é o que as 3 tools do MCP Degan
  fazem, `Wt3SsrCxQ2zwwnOo`, e a sticky do workflow diz por quê: *"a spec está errada nisso"*).
- No slim: `erros.length > 0` → `{error: true, transient: true}`; `registros.length === 0`
  com `erros` vazio → `{encontrado: false}`. São coisas diferentes e o prompt trata cada uma
  de um jeito.

### Status de pedido: rotear por **id**, nunca por texto

`"Em Entrega"` é id 8 e `"Entregue"` é id 9. Um `/entreg/` casa com os dois — em produção isso
disparou a mensagem de "entregue" cedo **e** gravou o dedup, o que bloqueou a notificação
verdadeira quando o pedido foi mesmo entregue (Degan, `rroCGCrCnb9R1U5s`). Um bug, dois erros.
Mapeie `status.id → estágio` numa constante do Code node.

### Enum de webhook só existe no `example` do OpenAPI

O campo `tipo` do webhook aparece na spec como inteiro genérico; os valores válidos estão só no
`example`. Ler apenas `properties` faz você inventar o enum. **Leia o `example`.**

### A BW não documenta HMAC

Não há `signature`/`hmac` na spec. Implementar verificação chutando o nome do header falha
100% das vezes — pior que não ter. Entregue **sem validação de assinatura e com o risco
registrado** no relatório, em vez de uma validação inventada que rejeita tudo.

### `GET /webhooks` antes de criar webhook

O webhook de um `tipo` é singleton. Criar por cima de um que já existe **derruba a integração
daquele sistema em silêncio** — pode não ser sua. Liste antes, e se já houver um, pare e
pergunte.

### Limites operacionais

| Limite | Valor |
|---|---|
| Rate limit | ~180 req/min |
| Origem das chamadas | só Brasil e EUA |
| TLS | 1.2 ou superior |

Rate limit da BW é **diferente** do rate limit da NexTags (~100 req/60s, Quirk #35). Num
transacional em lote, os dois valem ao mesmo tempo — o menor manda.

## 🛡️ Mapeamento operações comuns → endpoints

⚠️ **Não há mapa fixo aqui de propósito.** Os caminhos variam com a spec entregue pelo cliente,
e chutar rota na BW é caro: a rota errada volta `200` com `erros[]`, então o teste "parece que
funcionou" mente. Monte o mapa lendo a spec do cliente e validando cada rota com **uma chamada
real** antes de escrever a tool.

| Caso de uso | Fonte |
|---|---|
| Buscar pedido / detalhe / pedidos do cliente | BW |
| Buscar cliente / detalhe | BW |
| Rastreio, nota fiscal, previsão de entrega | BW |
| Catálogo, preço, estoque, variação | **Praticx** (quando o cliente tem os dois) |

## 📋 Decisão de arquitetura recomendada

**Caso A** (key fixa) — `httpRequestTool` direto no MCP, sem backends dedicados, sem data
table, sem cron. Com `neverError: true` em toda tool e slim em Code node manual (nunca
`optimizeResponse`, Quirk #18).

## 🔗 Links

- Doc oficial: spec OpenAPI fornecida pelo cliente.
- Confiabilidade: **média** — a spec existe e é útil, mas erra no envelope de resposta e não
  tipa o enum de webhook. Validar com chamada real.

## 📝 Notas históricas

- **Joias Degan (2026-09)** foi a primeira BW da operação: catálogo no Praticx (auth Bearer),
  pedido e cliente na BW (auth header). Quatro pendências bloquearam a virada de chave, duas
  delas base URL e duas credencial — colete isso no começo, não no fim.
- Os CUFs daquele projeto nasceram no padrão legado CamelCase + sufixo (`StatusPedidoBW`,
  `NumeroPedidoBW`, `RastreioPedidoBW`…). **Não replique em projeto novo:** o canônico é
  snake_case sem sufixo, com `origem_pedido: bw` (`campos_canonicos.md` §5). Em cliente que já
  roda com os nomes antigos, só registre a equivalência no relatório — não renomeie.

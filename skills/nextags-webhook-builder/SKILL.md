---
name: nextags-webhook-builder
description: Constrói e audita webhooks/disparos TRANSACIONAIS NexTags no n8n — notificação proativa de pedido (pago/aprovado, enviado, entregue, pronto p/ retirada) e carrinho abandonado, via webhook nativo ou polling/cron, roteando pra NexTags com dedup, CUFs e send_flow. Use quando o usuário diz "criar transacional", "webhook de pedido pago/enviado/entregue", "notificação de carrinho abandonado", "disparo proativo", "plugar Yampi/Shopify/Nuvemshop/Bling/Tray/Martz/VTEX no NexTags". Padrão validado por auditoria de produção. Foco em disparo proativo — NÃO cobre backend de atendimento sob demanda (isso é da nextags-mcp-builder). Complementar à mcp-builder; use as duas juntas.
type: tool
---

# nextags-webhook-builder

Fabrica **disparos transacionais** de produção no n8n: evento de e-commerce (pedido/carrinho) → normaliza → dedup → `POST /api/contacts` com `actions[]` (`set_field_value` + `add_tag` + `send_flow`) → mensagem proativa chega no cliente pelo WhatsApp/Instagram.

É a skill-irmã da `nextags-mcp-builder`. A mcp-builder faz o **atendimento sob demanda** (cliente pergunta, tool responde); esta faz o **disparo proativo** (evento acontece, NexTags avisa o cliente). Use as duas juntas num cliente completo.

O padrão aqui não é opinião — foi **validado por auditoria** de 29 fluxos de produção legíveis + 45 episódios de conversa. Detalhe completo com matriz de evidências em `references/padrao_transacional.md`.

## 🚨 Regra inegociável nº1 — `send_flow`, NUNCA texto direto

A plataforma NexTags **nunca processa texto solto** — toda saída fora do JSON estruturado **trava o fluxo**. Disparo proativo = `send_flow` de um flow pré-montado. O n8n **não** monta a mensagem em texto; ele seta CUFs e dispara o flow.

Erros reais que isso já causou (todos custaram horas — ver `references/antipadroes.md`):
- JSON de `send_flow` **preso em fences ` ```json `** vazou como texto cru pro cliente (Closet FIT).
- Agente devolveu dado cru (chave NF-e) em **texto** em vez de rotear via `send_flow` (DOLPS).
- `text` mandado como `{body:...}` (formato interno WhatsApp Cloud API) em vez de **string direta** (Wazzu).

**Ordem obrigatória:** `set_field_value` **SEMPRE antes** de `send_flow` no mesmo `actions[]` — senão os CUFs chegam vazios no destino (DOLPS "Regra 16").

## 🚨 Regra inegociável nº2 — dedup via Data Table (nunca in-memory)

Todo fluxo que pode receber replay (webhook Yampi/Shopify/Nuvemshop reenvia 2-3x) e **todo polling** precisa de dedup por **Data Table** — chave `order_id` interno + `status`, só dispara se o status mudou. Objeto em memória (`sd.seen`) **não persiste** e quebra o dedup (bug real: Viens). Schema canônico em `references/padrao_transacional.md` §3.

## ⚠️ Escopo — o que essa skill faz E NÃO faz

### ✅ Faz
- Webhook transacional de status de pedido (pago/aprovado, enviado, entregue, pronto p/ retirada, cancelado)
- Carrinho abandonado (webhook nativo OU polling/cron quando a plataforma não tem webhook)
- Dedup (Data Table / tag de controle), normalização de payload (telefone BR, itens, nome), guards
- Roteamento correto (1-por-status / endpoint-único-com-switch / flow-router-único) conforme a plataforma
- Auditoria de fluxos transacionais existentes contra o padrão validado

### ❌ NÃO faz
- **Backend de atendimento sob demanda** (buscar/obter pedido quando o cliente pergunta) → `nextags-mcp-builder`
- **Prompt/persona do agente**, flow_ids de conversa → `nextags-prompt-creator`
- **Campanhas em massa / broadcast** (disparo segmentado pra base) → fora de escopo (skill futura)
- **Criar os flows dentro do NexTags** — esta skill dispara `send_flow` pra um flow_id que já existe; montar o flow no NexTags é trabalho no painel

Se o cliente precisa de infra completa: **`nextags-mcp-builder` (atendimento) + `nextags-webhook-builder` (disparo) + `nextags-prompt-creator` (prompt)**.

## 📋 Brief mínimo

1. **Cliente + plataforma(s)** — pra naming, pasta no n8n e escolha do gatilho (ver tabela §2 do padrão).
2. **Eventos a notificar** — pago? enviado? entregue? carrinho? (define quantos disparos e o roteamento).
3. **Credenciais** — token da plataforma (pra buscar detalhe do pedido) + `X-ACCESS-TOKEN` do NexTags + `flow_id`(s) já criados no NexTags para cada evento.

Se o usuário não tem os `flow_id` ainda: **pare e avise** — sem flow_id real não há disparo (placeholder `11111111111`/`COLE_O_FLOW_ID` em produção é red flag real; ver antipadrões).

## 🌊 Fluxo de trabalho

### Fase 0 — Pasta e naming (igual mcp-builder)
`search_folders` → criar pasta com nome exato do cliente → nome do cliente em TODOS os workflows (`<Cliente> Webhook — Pedido Enviado`).

### Fase 1 — Escolher o roteamento (decisão, não gosto)
Leia `references/padrao_transacional.md` §1. Regra:
- Plataforma emite **eventos distintos por status** (Nuvemshop, Shopify, Martz) → **1 workflow por status**.
- Plataforma manda **1 evento genérico** (Bling `pedido_venda.alterado`, VTEX, Tray) → **endpoint único + Switch por `status.alias`**.
- Quer a lógica de mensagem **dentro do NexTags** → **flow router único** (n8n seta `StatusPedido` + dispara 1 flow_id). É o "1 fluxo de roteamento".

### Fase 2 — Escolher o gatilho (webhook vs polling)
Leia §2 (tabela por plataforma). **Não invente webhook onde não existe** (Magazord, Conecta Venda = só polling) nem faça cron onde há push (Yampi emite webhook de carrinho).

### Fase 3 — Gerar o workflow a partir do template
Copie de `assets/`:
- `webhook_por_status.js` — 1 endpoint por status (webhook nativo)
- `endpoint_unico.js` — 1 endpoint + Switch por status
- `polling_carrinho.js` — cron de carrinho abandonado (plataformas sem webhook)

Todo template já traz: helpers `formatarTelefone`/`verificarDado`/`separarNomeSobrenome`, dedup por Data Table, `POST /api/contacts` atômico com `actions[]`, e HTTP config resiliente. Customize CUFs, `flow_id`s e chaves.

### Fase 4 — Dedup
Crie a Data Table `<Cliente> <Plataforma> Orders State` (schema em §3). Chave = `order_id` interno; compare `status` pra evitar replay. Carrinho por webhook push único não precisa; carrinho por polling **precisa**.

### Fase 5 — Número de pedido / multi-plataforma
§4. Separe `order_id` (dedup) de `order_number` (CUF de exibição). Cliente com 2+ plataformas: **Data Tables de dedup separadas por origem** + CUF por origem (ou genérico + `OrigemPedido`).

### Fase 6 — Resiliência, segurança, CUFs (checklist)
- HTTP: `retryOnFail:true` + `waitBetweenTries:5000` + `onError:continueErrorOutput` + `specifyBody:'json'`.
- Anti-429 em polling/backfill; guard de telefone (e idade/conversão no carrinho).
- HMAC no webhook de entrada onde a plataforma assina (Bling/Martz).
- CUFs tipo **TEXTO** no NexTags (tipo NÚMERO descarta valor silenciosamente); todas as variáveis do template preenchidas (var vazia = #131008 derruba o flow).
- UTM em todo link (`link_envio_pattern.md` da mcp-builder).

### Fase 7 — Validar E2E (não confie na API)
`/send/{flow_id}` retorna `success:true` **até pra flow_id falso** — validar com **recebimento real no WhatsApp**. Testar replay (mandar o mesmo webhook 2x → cliente recebe 1x).

## 📜 Princípios
- **Disparo proativo = `send_flow`.** Texto solto trava o NexTags. (Regra nº1)
- **Dedup sempre persistente** (Data Table), nunca in-memory. (Regra nº2)
- **Clonou de outro cliente? Troque TUDO** — token, Data Table, `field_name`, `flow_id`. Copy-paste sem trocar referências é a causa nº1 de disparo fantasma (Wazzu usou conta da Hebreus Doze; Vitabe herdou `RENOVABE-`).
- **Roteamento e gatilho seguem a plataforma**, não o gosto.
- **Idempotente:** `search_workflows` antes de criar; atualize em vez de duplicar.
- **Token real nunca em arquivo da skill** (igual mcp-builder) — placeholder `<NEXTAGS_ACCESS_TOKEN>`.

## 📂 Estrutura desta skill
```
nextags-webhook-builder/
├── SKILL.md                          ← este arquivo
├── references/
│   ├── padrao_transacional.md        ← o padrão completo validado (arquitetura, dedup, número, entrega, resiliência, matriz de evidências)
│   └── antipadroes.md                ← catálogo de erros reais (send_flow vs texto, copy-paste, placeholders, CUF número, dedup in-memory)
└── assets/
    ├── webhook_por_status.js          ← template: 1 endpoint por status
    ├── endpoint_unico.js              ← template: 1 endpoint + Switch por status
    └── polling_carrinho.js            ← template: cron de carrinho abandonado
```

## 🤝 Skills complementares
- **`nextags-mcp-builder`** — atendimento sob demanda (MCP + backends). A Fase 4.5 dela aponta pra cá.
- **`nextags-prompt-creator`** / **`nextags-prompt-fixer`** — prompt do agente.
- **`nextags-json-fixer`** — valida o JSON de saída do agente (o mesmo schema `messages`/`actions` usado aqui).

Pipeline de cliente completo: **mcp-builder (atendimento) → nextags-webhook-builder (disparo) → prompt-creator → prompt-fixer**.

---
name: nextags-webhook-builder
description: Constrói e audita webhooks/disparos TRANSACIONAIS NexTags no n8n — notificação proativa de pedido (pago/aprovado, enviado, entregue, pronto p/ retirada) e carrinho abandonado, via webhook nativo, polling/cron ou Gateway Proxy NexTags, roteando pra NexTags com dedup, CUFs canônicos e send_flow. Use quando o usuário diz "criar transacional", "webhook de pedido pago/enviado/entregue", "notificação de carrinho abandonado", "disparo proativo", "plugar Yampi/Shopify/Nuvemshop/Bling/Tray/Martz/VTEX/Bagy no NexTags". Padrão validado por auditoria de produção. Foco em disparo proativo — NÃO cobre backend de atendimento sob demanda (isso é da nextags-mcp-builder). Complementar à mcp-builder; use as duas juntas.
type: tool
---

# nextags-webhook-builder

Fabrica **disparos transacionais** de produção no n8n: evento de e-commerce (pedido/carrinho) → normaliza → dedup → `POST /api/contacts` com `actions[]` (`set_field_value` + `add_tag` + `send_flow`) → mensagem proativa chega no cliente pelo WhatsApp/Instagram.

É a skill-irmã da `nextags-mcp-builder`. A mcp-builder faz o **atendimento sob demanda** (cliente pergunta, tool responde); esta faz o **disparo proativo** (evento acontece, NexTags avisa o cliente). Use as duas juntas num cliente completo.

O padrão aqui não é opinião — foi **validado por auditoria** de 29 fluxos de produção legíveis + 45 episódios de conversa, e refinado com 21 workflows n8n recentes (2026-09). Detalhe completo com matriz de evidências em `references/padrao_transacional.md`.

## 🚨 Regra inegociável nº1 — `send_flow`, NUNCA texto direto

A plataforma NexTags **nunca processa texto solto** — toda saída fora do JSON estruturado **trava o fluxo**. Disparo proativo = `send_flow` de um flow pré-montado. O n8n **não** monta a mensagem em texto; ele seta CUFs e dispara o flow.

Erros reais que isso já causou (todos custaram horas — ver `references/antipadroes.md`):
- JSON de `send_flow` **preso em fences ` ```json `** vazou como texto cru pro cliente (Closet FIT).
- Agente devolveu dado cru (chave NF-e) em **texto** em vez de rotear via `send_flow` (DOLPS).
- `text` mandado como `{body:...}` (formato interno WhatsApp Cloud API) em vez de **string direta** (Wazzu).

**Ordem obrigatória:** `set_field_value`… → `add_tag`… → `send_flow` **por último** no mesmo `actions[]` — senão os CUFs chegam vazios no destino (DOLPS "Regra 16"; ordem confirmada em 100% do corpus n8n).

## 🚨 Regra inegociável nº2 — dedup em Data Table, gravado SÓ depois do sucesso

Todo fluxo que pode receber replay (webhook Yampi/Shopify/Nuvemshop reenvia 2-3x) e **todo polling** precisa de dedup por **Data Table**. Objeto em memória (`sd.seen`) **não persiste** e quebra o dedup (bug real: Viens).

**O refinamento que vale mais que o resto:** o node que grava o dedup só roda **no ramo de sucesso** do POST na NexTags.

```
Notificar NexTags (httpRequest, onError: continueErrorOutput)
   → IF "Notificação OK?"  ({{ $json.error ? 'erro' : 'ok' }} == 'ok')
        ├─ true  → Salvar Estado (Data Table upsert)   ← só aqui grava o dedup
        └─ false → Falhou (NoOp, NÃO grava)            ← segue sem marcar
```

Gravar antes ou em paralelo marca o cliente como "notificado" para sempre quando a chamada falhou. Evidência: Nordmann v3 (`ln7ZTWGwTyV2KVRQ`) — na v2 o dedup gravava mesmo com 401 do token placeholder, e ao colocar o token real os clientes **jamais** seriam notificados; Carrinho v2 (`bvR8NeB5e4BdOzyD`) — 51 notificações falharam com 401, dedup gravado do mesmo jeito, tabela teve que ser recriada limpa.

Mais três regras de chave (detalhe em `padrao_transacional.md` §3):
- **Compare estágio anterior × novo** (`stored.status === stage`), não "existe linha" — senão Pago bloqueia Enviado e Entregue (Degan BW `rroCGCrCnb9R1U5s`).
- **Chave por `fulfillment_id`** quando a plataforma tem envio parcial, não `order_id` (Alto Giro `w1KeVwUnJGdwpidU`).
- **`rowNotExists`** (operação nativa do node Data Table) quando só importa a existência da linha, em vez de `get` + IF manual (Alto Giro "Dedup Gate").

## 🚨 Regra inegociável nº3 — roteamento de estágio por ID de status, nunca por texto

Quando a API do cliente expõe status como `{id, descricao}`, roteie por **`id`**. A `descricao` é texto livre que o lojista edita no painel.

Evidência (Degan BW `rroCGCrCnb9R1U5s`, comentário no Code "Decidir"): o status **"Em Entrega" (id 8) casava com a regex `/entreg/`** e virava "entregue" prematuramente — e pior, o dedup gravava "entregue" e **bloqueava a notificação real do id 9**. Fallback por texto só quando o payload não traz `id`, e mesmo assim com word-boundary (`\bentregue\b`), nunca substring.

Corolário: audite drift de configuração. A sonda Degan (`sL14eAen2XAuAn6h`) confere os IDs de status lidos no painel contra o que a API devolve e reporta divergência — sem isso, o cliente reconfigura um status e o roteamento por ID fica errado em silêncio.

## 🚨 Regra inegociável nº4 — n8n sempre via API/MCP, nunca via navegador

Nenhuma automação de UI, nenhum "abra o n8n e clique". Sequência canônica:

```
search_workflows        → o workflow já existe? (idempotência: atualize, não duplique)
search_folders          → pasta do cliente
get_workflow_details    → estado atual, se for auditoria
validate_workflow       → valida ANTES de criar/atualizar
create_workflow_from_code | update_workflow
publish_workflow        → só depois do checklist da Fase 6
```

Sem `validate_workflow` antes, o erro só aparece com o workflow já no ar (SPEC §6.1).

## 🚨 Regra inegociável nº5 — sticky note em TODO workflow

Sticky note é **documentação executável**: fica no canvas, é lida por quem auditar, e é o único lugar onde o "porquê" sobrevive a uma reescrita. Modelo canônico (SPEC adendo §9, a partir dos cards reais de Degan/Nordmann/Poé):

```
## <Cliente> — <Evento> (<Plataforma>) — v<N>
Endpoint: https://<host-n8n>/webhook/<cliente>/<plataforma>/<evento>
ESTADO EM dd/mm
  <o que está confirmado por chamada real e o que ainda é suposição>
CREDENCIAIS
  <Nome da credencial> -> Header Auth, header 'X-ACCESS-TOKEN', valor puro. NAO e Bearer.
  <Credencial da plataforma> -> Bearer.
NÃO ATIVAR antes de: <lista do que falta preencher: token, flow_ids, store_id, url_loja>
ARMADILHAS
  <armadilha> (confirmado por chamada real em dd/mm)
DE ONDE VEIO a lista de campos: <doc/rota/chamada real — nunca "de memória">
DECISÕES NEGATIVAS
  <o que foi deixado de fora de propósito e por quê>
```

Exemplo curto, baseado no card real do Nordmann v3 (`ln7ZTWGwTyV2KVRQ`):

```
## Nordmann Meling — Webhook Pedidos (Nuvemshop) — v3
Detecção por CAMPO, não por evento. Compara payment_status/shipping_status reais
do pedido contra o último estado salvo:
  payment_status == "paid" (novo)      -> Pago
  shipping_status == "shipped" (novo)  -> Enviado
⚠️ v3 — fix crítico: o dedup (Salvar Estado) só grava se a notificação pra NexTags
teve SUCESSO. Na v2 gravava mesmo com a chamada falhando (401 do token placeholder):
ao colocar o token real, os clientes JAMAIS seriam notificados. Corrigido.
⚠️ NÃO ATIVAR antes de substituir <NEXTAGS_ACCESS_TOKEN> e os 3 <FLOW_ID_...>.
```

⚠️ **Sticky/descrição não pode dizer "pronto/ativo" enquanto houver placeholder no código.** Workflow `qRIs9L07G5auvhRM` está `active:true` com a descrição dizendo "Auth pendente" — contradição que a auditoria tem que flagrar (`antipadroes.md` §20).

## 🚨 Regra inegociável nº6 — `flow_id = 0` como fail-safe, nunca id fictício

Enquanto o `flow_id` real não existe, use `0` (ou string vazia) **com guard**:

```js
const flow = FLOW_BY_STAGE[stage];
if (!flow) return skip(base, 'flow_id_ausente:' + stage);   // não dispara, registra o motivo
```

Evidência: Degan BW (`flow_pago/enviado/entregue: 0`) e Degan Carrinho (`flow_carrinho: 0`) entregam o workflow funcional com o estágio simplesmente **não disparando** até alguém preencher. Id fictício "funcional" (`11111111111`, `COLE_O_FLOW_ID`) dispara para o lugar errado ou vira no-op silencioso (Dolps v1, Viens). O que falta preencher vai no `NÃO ATIVAR antes de…` do sticky.

Corolário — **todo skip carrega `_motivo`**. Skip silencioso (`if(!phone) return [];`) é indepurável. Padrão maduro do corpus (Degan Carrinho Polling), já pronto em `assets/_helpers.js` como `skip(item, motivo)`:

```js
function skip(item, motivo){ return [{ json: Object.assign({}, item || {}, { _skip: true, _motivo: motivo }) }]; }
```

Motivos canônicos: `sem_telefone`, `telefone_invalido`, `telefone_fixo`, `flow_id_ausente:<stage>`, `estagio_desconhecido:<id>`, `fora_da_janela`, `ja_convertido`, `dedup`.

Regra fina de erro: erro **global** (credencial, rota) → `throw` (tem que aparecer); erro **pontual** de 1 item dentro de um loop → `skip` com motivo, para não derrubar os demais.

## 🚨 Regra inegociável nº7 — telefone: normalize sempre, e FIXO não recebe

Use o snippet canônico único `formatarTelefone` de `assets/_helpers.js` (não reescreva: o corpus tem 4 implementações divergentes da mesma lógica) e **valide o resultado final**:

```js
const g = guardTelefone(bruto);          // normaliza + valida /^55\d{10,11}$/ + barra fixo
if (!g.ok) return skip(base, g.motivo);  // sem_telefone | telefone_invalido | telefone_fixo
const phone = g.phone;
```

A validação final por regex `/^55\d{10,11}$/` é a do AliveMed, a implementação mais defensiva do corpus: se não bater, o telefone é descartado em vez de enviado "como deu".

**Número FIXO não recebe `send_flow`/mensagem via API:** ao entrar na plataforma o número ganha o 9 extra e vira inválido (evidência: dono do projeto, 2026-09-03; Alto Giro/ChatRace adiciona o `9` cegamente). Fixo = DDD + local de 8 dígitos começando em 2-5. Nunca "tentar mesmo assim" — descarte com `_motivo: 'telefone_fixo'` e registre a contagem no relatório.

## 🧾 CUFs e tags canônicos — a fonte é `campos_canonicos.md`

Os nomes de campo do transacional **não são escolha do projeto**. Tabela completa em
`references/campos_canonicos.md` §5 (CUFs transacionais) e §4 (tags). Resumo do que muda no dia a dia:

| Regra | Detalhe |
|---|---|
| **snake_case, sem sufixo de plataforma** | `numero_pedido`, `status_pedido`, `valor_pedido`, `produtos_pedido`, `rastreio_codigo`, `rastreio_url`, `previsao_entrega`, `produtos_carrinho`, `link_carrinho`… — iguais em QUALQUER integração |
| **A plataforma vai em `origem_pedido`** | `yampi` \| `shopify` \| `nuvemshop` \| `tray` \| `bagy` \| `bling` \| `vtex` \| `martz` \| `woocommerce` \| `bw` … Não entra no nome do campo. |
| **Tudo tipo Texto (`type: 0`)** | Tipo Número descarta o valor em silêncio (Mayuí, reincidente em Degan). |
| **Tags no mesmo `actions[]`** | `transacional` + `Pedido Aprovado` / `Pedido Enviado` / `Pedido Entregue`. |
| **Legado não se renomeia** | `StatusPedidoYMP`, `NumeroPedidoBW`, `RastreioNS` (CamelCase + sufixo): em cliente rodando, o flow lê esses nomes — registrar como legado no relatório, **não renomear**. Projeto novo = canônico. |

## ⚠️ Escopo — o que essa skill faz E NÃO faz

### ✅ Faz
- Webhook transacional de status de pedido (pago/aprovado, enviado, entregue, pronto p/ retirada, cancelado)
- Carrinho abandonado (webhook nativo OU polling/cron quando a plataforma não tem webhook)
- Dedup (Data Table / tag de controle), normalização de payload (telefone BR, itens, nome), guards
- Roteamento correto (1-por-status / endpoint-único-com-switch / flow-router-único) conforme a plataforma
- **Fonte de dados via Gateway Proxy NexTags** quando não há credencial nativa da loja (`references/gateway_proxy_nextags.md`)
- Setup idempotente de CUFs/tags por API antes de ativar (`assets/setup_cufs_canonicos.js`, `references/api_nextags.md`)
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
3. **Credenciais** — token da plataforma **ou** `storeId` + Gateway Token NexTags; `X-ACCESS-TOKEN` do NexTags; `flow_id`(s) já criados no NexTags para cada evento.

Se o usuário não tem os `flow_id` ainda: **não pare o trabalho — entregue com `flow_id = 0` + guard** (Regra nº6) e liste no `NÃO ATIVAR antes de…` do sticky. O que nunca se faz é inventar um id.

## 🌊 Fluxo de trabalho

### Fase 0 — Pasta e naming (igual mcp-builder)
`search_folders` → criar pasta com nome exato do cliente → nome do cliente em TODOS os workflows (`<Cliente> Webhook — Pedido Enviado`). Tudo por API/MCP (Regra nº4).

### Fase 1 — Escolher o roteamento (decisão, não gosto)
Leia `references/padrao_transacional.md` §1. Regra:
- Plataforma emite **eventos distintos por status** (Nuvemshop, Shopify, Martz) → **1 workflow por status**.
- Plataforma manda **1 evento genérico** (Bling `pedido_venda.alterado`, VTEX, Tray) → **endpoint único + Switch por `status.alias`** (ou por **id de status**, se a API expuser — Regra nº3).
- Quer a lógica de mensagem **dentro do NexTags** → **flow router único** (n8n seta `status_pedido` + dispara 1 flow_id).

### Fase 2 — Escolher o gatilho e a fonte de dados
Leia §2 (tabela por plataforma). **Não invente webhook onde não existe** (Magazord, Conecta Venda = só polling) nem faça cron onde há push (Yampi emite webhook de carrinho).
Sem credencial nativa da loja? Confira se a loja está no integrador NexTags e use o **Gateway Proxy** (`references/gateway_proxy_nextags.md`) — evidência de produção: Cantarola Backend consome `…/v1/gateway/stores/{storeId}/products`.

### Fase 3 — Gerar o workflow a partir do template
Copie de `assets/`:
- `webhook_por_status.js` — 1 endpoint por status (webhook nativo)
- `endpoint_unico.js` — 1 endpoint + Switch por status
- `polling_carrinho.js` — cron de carrinho abandonado (plataformas sem webhook)
- `setup_cufs_canonicos.js` — workflow de setup idempotente de CUFs (rodar ANTES de ativar)

Todo template já traz: helpers `formatarTelefone`/`ehTelefoneFixo`/`verificarDado`/`separarNomeSobrenome`/`skip`, `field_name` canônicos, dedup gravado só no sucesso, `POST /api/contacts` atômico e HTTP config resiliente. Customize `flow_id`s, chaves e o parsing do payload.

### Fase 4 — Dedup
Crie a Data Table `<Cliente> <Plataforma> Orders State` (schema em §3). Chave = `order_id` interno (ou `fulfillment_id` se houver envio parcial); compare **estágio anterior × novo**; grave **só no ramo de sucesso**. Carrinho por webhook push único não precisa; carrinho por polling **precisa**.

### Fase 5 — Número de pedido / multi-plataforma
§4. Separe `order_id` (dedup) de `numero_pedido` (CUF de exibição, número visível ao cliente, sem `#`). Cliente com 2+ plataformas: **Data Tables de dedup separadas por origem** + `origem_pedido` como discriminador (os nomes de CUF continuam os mesmos).

### Fase 6 — Checklist antes de ativar
- [ ] **CUFs canônicos criados na conta** (`campos_canonicos.md` §5) — rodar `setup_cufs_canonicos.js` em dry-run, conferir, depois criar. A API **não tem DELETE** de CUF.
- [ ] **Tags canônicas** criadas: `transacional` + `Pedido Aprovado`/`Pedido Enviado`/`Pedido Entregue` (`POST /accounts/tags`).
- [ ] **`GET /accounts/flows`** para validar que cada `flow_id` existe de verdade (`/send/{flow_id}` devolve `success:true` até para id falso).
- [ ] **`GET /accounts/me`** para confirmar que o token é da conta certa (token errado = 200 na conta errada).
- [ ] CUFs tipo **TEXTO** (`type: 0`); todas as variáveis do template preenchidas (var vazia = `#131008` derruba o flow).
- [ ] HTTP: `retryOnFail:true` + `waitBetweenTries:5000` + `onError:continueErrorOutput` + `specifyBody:'json'`.
- [ ] Anti-429: rate limit NexTags ~**100 req/60s** (Privilège); throttle em polling/backfill.
- [ ] Guard de telefone (inválido e **fixo**) + guards de idade/conversão no carrinho.
- [ ] HMAC no webhook de entrada onde a plataforma assina (Bling/Martz).
- [ ] UTM em todo link (`link_envio_pattern.md` da mcp-builder).
- [ ] Sticky note preenchido pelo modelo da Regra nº5, incluindo `NÃO ATIVAR antes de…`.

### Fase 7 — Validar E2E (não confie na API)
`/send/{flow_id}` retorna `success:true` **até pra flow_id falso** — validar com **recebimento real no WhatsApp** (contato celular real; webchat não tem telefone, fixo não recebe). Testar replay (mandar o mesmo webhook 2x → cliente recebe 1x) e testar a transição de estágio (Pago → Enviado dispara os dois).

## 📜 Princípios
- **Disparo proativo = `send_flow`.** Texto solto trava o NexTags. (Regra nº1)
- **Dedup persistente e gravado só no sucesso.** (Regra nº2)
- **Estágio por ID, não por texto.** (Regra nº3)
- **n8n por API/MCP, com sticky note.** (Regras nº4 e nº5)
- **Fail-safe explícito** (`flow_id = 0` + guard + `_motivo`) em vez de placeholder funcional. (Regra nº6)
- **Fixo não recebe.** (Regra nº7)
- **Nomes de campo são canônicos**, não escolha do projeto (`campos_canonicos.md`).
- **Clonou de outro cliente? Troque TUDO** — token, `storeId`, Data Table, `field_name`, `flow_id`. Copy-paste sem trocar referências é a causa nº1 de disparo fantasma (Wazzu usou conta da Hebreus Doze; Vitabe herdou `RENOVABE-`).
- **Idempotente:** `search_workflows` antes de criar; atualize em vez de duplicar.
- **Token real nunca em arquivo da skill** — placeholders `<NEXTAGS_ACCESS_TOKEN>`, `<NEXTAGS_GATEWAY_TOKEN>`, `<TELEFONE>`, `<IP_N8N>`, `<FLOW_ID_...>`.

## 📂 Estrutura desta skill
```
nextags-webhook-builder/
├── SKILL.md                          ← este arquivo
├── references/
│   ├── campos_canonicos.md           ← fonte de verdade dos campos/tags (cópia idêntica em 4 skills)
│   ├── padrao_transacional.md        ← o padrão completo validado (arquitetura, dedup, número, entrega, resiliência, matriz de evidências)
│   ├── antipadroes.md                ← catálogo de erros reais (22 antipadrões)
│   ├── gateway_proxy_nextags.md      ← Gateway Proxy NexTags (Tray/Nuvemshop/Yampi/Bagy sem credencial nativa)
│   └── api_nextags.md                ← endpoints da API NexTags + receitas (CUF idempotente, tag, flows, disparo atômico)
└── assets/
    ├── _helpers.js                   ← helpers compartilhados (telefone, fixo, skip, UTM)
    ├── webhook_por_status.js         ← template: 1 endpoint por status
    ├── endpoint_unico.js             ← template: 1 endpoint + Switch por status
    ├── polling_carrinho.js           ← template: cron de carrinho abandonado
    └── setup_cufs_canonicos.js       ← template: setup idempotente de CUFs (dry-run + diff + laudo)
```

## 🤝 Skills complementares
- **`nextags-mcp-builder`** — atendimento sob demanda (MCP + backends). A Fase 4.5 dela aponta pra cá.
- **`nextags-prompt-creator`** / **`nextags-prompt-fixer`** — prompt do agente.
- **`nextags-json-fixer`** — valida o JSON de saída do agente (o mesmo schema `messages`/`actions` usado aqui).

Pipeline de cliente completo: **mcp-builder (atendimento) → nextags-webhook-builder (disparo) → prompt-creator → prompt-fixer**.

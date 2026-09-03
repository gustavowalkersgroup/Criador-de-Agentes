# Padrão Real de Webhooks Transacionais NexTags

> **Validado por auditoria** de 29 fluxos de produção legíveis no n8n (de um universo de 159 workflows transacionais em 101 clientes) + mineração de 13 projetos de conversa (45 episódios, 9 incidentes de `send_flow` vs texto).
> Data: 2026-07-16. **Revisão 2026-09-03:** leitura completa de 21 workflows n8n recentes (Cantarola, Nordmann, Degan, Poé, Meiskin, Alto Giro, WL, Otogama, AliveMed, Privilège) trouxe §3.5 (dedup só após sucesso), §3.6 (estágio por id), §4.3 (naming canônico) e o rate limit real de §7.
> Toda regra aqui carrega evidência (cliente/workflow) na [Matriz de evidências](#matriz-de-evidências). O que é recomendação sem lastro em produção está marcado **[SEM EVIDÊNCIA DIRETA]**.
> Os nomes de campo e tag são os de `references/campos_canonicos.md` — este arquivo aponta para lá, não duplica a tabela.

Transacional = **disparo proativo** ao cliente quando um evento de pedido/carrinho acontece (pago, enviado, entregue, pronto p/ retirada, carrinho abandonado). Não confundir com backend de atendimento sob demanda (o cliente pergunta "cadê meu pedido") — isso é território da `nextags-mcp-builder`.

---

## 0. Nota de cobertura (honestidade sobre a auditoria)

Dos 159 workflows transacionais inventariados, **72 clientes retornaram `unreadable`** — não por falha de análise, mas porque o workflow tem `availableInMCP:false` no n8n (erro determinístico `"Workflow is not available in MCP"`). O padrão abaixo se apoia nos **29 clientes legíveis**, que por sorte cobrem **todos os arquétipos** (todas as formas de roteamento, todos os tipos de gatilho, 13 plataformas, dedup presente e ausente). Para auditar os 72 restantes seria preciso habilitar MCP neles no n8n primeiro. [Certeza]

---

## 1. Decisão de arquitetura — as 3 formas de roteamento

Existem **três** padrões em produção. A escolha depende de **como a plataforma emite o evento**, não de gosto.

| Padrão | Quando usar | Evidência |
|---|---|---|
| **1 workflow por status** | Plataforma emite **eventos distintos por status** (`order/paid`, `order/fulfilled`, `fulfillment_order/status_updated`; Shopify `orders/paid`/`orders/fulfilled`; Martz `order.*`). Cada evento → 1 webhook. | Exclusiva (Nuvemshop, 4 wf: aprovado/enviado/entregue/retirada), Mania Brasil (Martz), Divinnah Gaia (Martz/Shopify), Alto Giro (Shopify) |
| **Endpoint único + Switch por status** | Plataforma manda **1 evento genérico** com status variável (`Order.Updated`, Bling `pedido_venda.alterado`, VTEX, Tray `order_changed`). 1 webhook decide internamente. | Veuske (Yampi — referência Rafa), Amo Calçados ("Bling → WhatsApp Transacional"), Dolps (VTEX), Zencial (Yampi), BB (Tray) |
| **Flow router único no NexTags** | n8n só normaliza e seta CUFs, e dispara **1 único `flow_id`** que ramifica por CUF de status dentro do NexTags. É o "1 fluxo de roteamento". | Neurofood (roteador `1782312754895`), Nalisa (`1780321795848`), Mayuí, IMP |

**Regra de decisão validada:**
1. A plataforma emite eventos separados por status? → **1 workflow por status**.
2. A plataforma manda 1 evento genérico? → **endpoint único + Switch por `status.alias`** (nunca por `body.event` — ver §7).
3. Quer manter a lógica de qual mensagem enviar **dentro do NexTags** (não no n8n)? → **flow router único**: n8n seta `StatusPedido` como CUF + dispara 1 flow_id, e o flow ramifica.

> **Switch por `status.alias`/`status.name`, nunca por `body.event`.** Mais robusto a mudanças de payload. — Veuske (referência Rafa), lição consolidada.

---

## 2. Gatilho — webhook nativo vs polling/cron (por plataforma)

| Plataforma | Status de pedido | Carrinho abandonado | Observação |
|---|---|---|---|
| **Yampi** | webhook nativo (`order.paid`/`updated`) | **webhook nativo** | ⚠️ Yampi EMITE webhook de carrinho — **não fazer cron**. Erro real corrigido na Veuske (doc antiga mandava cron). |
| **Shopify** | webhook (`orders/paid`, `orders/fulfilled`, `fulfillments/update`) | **cron** (`GET /checkouts`) | Não há webhook nativo de carrinho abandonado. Casa Marquez, Alto Giro. |
| **Nuvemshop/Tiendanube** | webhook (`order/paid`, `order/fulfilled`, `fulfillment_order/status_updated`) | **cron** (`GET /checkouts`) | Exclusiva, Neurofood. Cart precisa polling + dedup. |
| **Bling** | webhook (`pedido_venda.alterado`) + **HMAC** | — (sem loja própria) | 1 evento genérico → Switch por situação. Amo, HIVEN. |
| **VTEX** | webhook (order hook) → `GET` OMS p/ detalhe | cron (orderForm) | Dolps, Iorane. |
| **Martz** | webhook (`order.*`, `customer.*`, `bonus.*`) | webhook (`abandoned-cart`) | Mania, Divinnah, Verdena, Mayuí. |
| **Tray** | webhook (`order_placed/paid/changed`) | webhook (`abandoned_cart`) | BB. |
| **Magazord** | **polling** (sem webhook) | **polling** | Wazzu — feeder de polling POSTa no webhook de disparo. |
| **Conecta Venda** | **polling** (cron 5min) | **polling** (cron 2h) | Privilège Semijoias. |
| **Loja Integrada** | webhook | cron | Amo (carrinho). |
| **Melhor Envio** | polling (rastreio) | — | Cantarola. |

> **Regra:** nunca assuma cron sem confirmar na doc da plataforma se existe webhook push equivalente. E nunca assuma webhook onde não existe (Magazord/Conecta Venda **só** têm polling). [Certeza]

---

## 3. Dedup via Data Table

### 3.1 Schema canônico (referência Rafa — confirmado em Neurofood, Mania, Divinnah)

Data Table `<Cliente> <Plataforma> Orders State`:

| Coluna | Tipo | Função |
|---|---|---|
| `order_id` | string | ID **interno** da plataforma — a chave de match |
| `status` | string | último status disparado (`pending`/`paid`/`shipped`/`delivered`/`cancelled`) |
| `updated_at` | string (ISO) | timestamp do último update |
| `customer_phone` | string | telefone (debug) |

**Lógica:** lookup por `order_id` → existe e status **igual**? → fim (dedup). Status **diferente**? → dispara + UPDATE. Não existe? → dispara + INSERT.

### 3.2 Variantes validadas de chave

- **Chave composta** (quando o número pode repetir ou a plataforma manda status no mesmo evento): Veuske (`nPedido + idPedido`), Dolps (`orderId|lastChange`), Mayuí (`order_id|evento`), BB (`store_id|order_id|status`), Exclusiva (`order:{id}:{status}` p/ pedido, `cart:{checkout_id}` p/ carrinho).
- **Chave por REMESSA (`fulfillment_id`), não por pedido**, quando a plataforma tem envio parcial: um pedido pode gerar várias fulfillments e cada uma merece seu aviso de "enviado". Evidência: Alto Giro Notif Enviado, tabela `w1KeVwUnJGdwpidU`, chave `fulfillment_id` (não `order_id`).
- **Chave composta por ETAPA dentro do mesmo pedido**, quando há régua/funil: Meiskin funil PIX (`FsnnAiE2LADC91aZ`) guarda `order_id` + colunas booleanas `etapa_30_enviada` / `etapa_65_enviada` / `etapa_120_enviada` — permite reenviar em vários momentos sem duplicar.
- **Dedup por TAG de controle** (semântica "notificar 1x na vida"): Alto Giro usa a tag `ag-entregue-notif` em vez de Data Table no fluxo Entregue. Válido.
- **`rowNotExists`** (operação nativa do node Data Table) quando só importa se a linha existe, em vez de `get` + IF manual. Evidência: Alto Giro, node "Dedup Gate":
  `{"resource":"row","operation":"rowNotExists","dataTableId":"w1KeVwUnJGdwpidU","matchType":"anyCondition","filters":{"conditions":[{"keyName":"fulfillment_id","condition":"eq","keyValue":"={{ $json.fulfillment_id }}"}]}}`
  Os dois padrões (`get`+IF e `rowNotExists`) coexistem no corpus; use `rowNotExists` quando não precisa **ler** o conteúdo da linha anterior.

### 3.3 Quando é obrigatório vs dispensável

- **Obrigatório:** qualquer fonte que faz replay (Yampi/Shopify/Nuvemshop reenviam o mesmo webhook 2-3x) e **todo polling/cron** (Nalisa, Exclusiva cron, Wazzu feeder). Sem dedup = cliente recebe a mesma mensagem 2-5x.
- **Dispensável:** carrinho abandonado por **webhook push único** (Martz/Yampi disparam 1x por cart) — Mania Brasil cart não tem dedup e está correto.

### 3.4 Antipadrão de dedup (RED FLAG real)

- **Viens:** dedup feito com objeto **em memória** `sd.seen = {[order_id]:true}`, sobrescrito a cada execução → **não persiste**, dedup quebrado. Sempre Data Table, nunca variável in-memory. [Certeza]

### 3.5 O dedup só grava DEPOIS do sucesso do POST na NexTags

**A regra mais importante de todo o corpus.** O node que grava o dedup (Data Table upsert/insert) só pode rodar **depois** de confirmar que o `POST /api/contacts` teve sucesso — nunca em paralelo, nunca antes.

**Por quê:** se o dedup grava independente do resultado, uma falha transitória (token placeholder, 401, instabilidade) marca o cliente como "já notificado" **para sempre**. O cliente real nunca recebe a mensagem, nem depois do bug corrigido — e o sintoma não aparece em lugar nenhum, porque tudo "rodou".

**Implementação padrão** (Nordmann Pedidos, Nordmann Carrinho, Meiskin PIX Expirado):

```
Notificar NexTags (httpRequest, onError: continueErrorOutput)
   → Notificação OK? (IF: {{ $json.error ? 'erro' : 'ok' }} == 'ok')
        ├─ true  → Salvar Estado (dataTable upsert)     ← só aqui grava dedup
        └─ false → Falhou (não salva dedup) (noOp)      ← segue sem gravar
```

**Evidência — dois incidentes documentados nos próprios workflows:**

| Workflow | O que aconteceu |
|---|---|
| Nordmann Meling Webhook Pedidos v3 (`ln7ZTWGwTyV2KVRQ`) | "Na v2, o dedup gravava mesmo com a chamada falhando (401 do token placeholder) — isso significava que, ao colocar o token real, os clientes JAMAIS seriam notificados." |
| Nordmann Meling Carrinho v2 (`bvR8NeB5e4BdOzyD`) | "Na v1, a 1ª execução automática rodou com token placeholder, todas as 51 notificações falharam (401) mas o dedup foi gravado do mesmo jeito — esses 51 clientes reais JAMAIS seriam notificados ao colocar o token real. Corrigido + tabela de dedup recriada limpa." |

⚠️ Consequência operacional: quando esse bug já rodou, **corrigir o fluxo não basta** — a tabela de dedup precisa ser recriada/limpa, senão os clientes marcados continuam mudos.

### 3.6 Estágio por ID de status, nunca por texto

Quando a API do cliente expõe status como objeto `{id, descricao}`, o roteamento de estágio (pago/enviado/entregue) usa **`id`**. A `descricao` é texto livre editável no painel do lojista.

**Evidência** — Degan BW (`rroCGCrCnb9R1U5s`), comentário no Code node "Decidir":

```js
// Roteamento por ID do status. A descricao e texto livre que a loja edita no painel:
// "Em Entrega" (id 8) casava com /entreg/ e virava "entregue" -> mensagem errada E o dedup
// gravava "entregue", bloqueando o Entregue real (id 9). Por isso ID, nao texto.
```

Note o efeito duplo: além da mensagem errada, o dedup gravou o estágio errado e **bloqueou a notificação certa**. Regras derivadas:

- Fallback por texto **só** quando o payload não traz `id`, e mesmo assim com word-boundary (`\bentregue\b`), nunca substring.
- **Audite drift de configuração:** a sonda Degan (`sL14eAen2XAuAn6h`) confere os IDs de status lidos manualmente no painel contra o que a API devolve e reporta divergência explícita — sem isso, o cliente reconfigura um status e o roteamento por ID fica errado em silêncio.
- Compare o **estágio anterior salvo × o novo** (`stored.status === stage`), não "existe linha": o mesmo pedido passa por Pago → Enviado → Entregue, e dedup binário bloquearia os estágios seguintes (`rroCGCrCnb9R1U5s`).

---

## 4. Número de pedido & concatenação multi-plataforma

**Descoberta central:** a esmagadora maioria dos clientes é **mono-plataforma**, então não há tratamento de colisão — e vários auditores sinalizaram isso como **risco latente** ("sem prefixo/CUF de origem; colidiria se entrar uma 2ª plataforma").

### 4.1 Regra validada (vale pra todos)

**Separe `order_id` de `numero_pedido`:**
- `order_id` = ID **interno** da plataforma → usado **só** na chave de dedup. Globalmente único por loja. Nunca vira CUF.
- `numero_pedido` = número **visível ao cliente** (sem `#`) → usado **só** na CUF de exibição.
- **Nunca** use o número visível como chave de dedup (pode repetir). Veuske resolve com chave composta `nPedido + idPedido` — o ID interno desambigua.

Normalização comum: remover `#` do `order.name` do Shopify (Casa Marquez, Alto Giro, Mania); Divinnah corta em `.` (`#1234.1` → `1234`).

### 4.2 Multi-plataforma no mesmo contato (a "concatenação")

Só **2 casos reais** auditados — e eles definem o padrão:

- **HIVEN** (Bling + Yampi + Shopify): o workflow Bling grava em **CUFs separados por origem** (`numero_pedido_bling`, `pedido_id_bling`); o workflow Yampi/Shopify tem um node **"Detectar e Normalizar"** que lê de Yampi **OU** Shopify (pelos headers/body) e grava em **campos genéricos** com discriminador de plataforma.
- **Amo Calçados** (Bling + Loja Integrada): **Data Tables de dedup separadas por plataforma** — cada origem tem seu próprio namespace de `order_id`/`pedido_id`.

**Recomendação consolidada para multi-plataforma (canônico atual):**
1. **Data Table de dedup separada por plataforma** (sempre — evidência Amo). [Certeza]
2. **CUFs canônicos únicos** (`numero_pedido`, `status_pedido`, …) **+ `origem_pedido`** como discriminador. A variante "CUF por origem" (`NumeroPedidoBling`, `NumeroPedidoShopify` — HIVEN) é o padrão **legado**: continua funcionando onde já roda, mas não se cria mais (§4.3).
3. Prefixo no número (ex.: `SHP-1234`/`YMP-5678`) é uma opção limpa **[SEM EVIDÊNCIA DIRETA]** — nenhum cliente auditado usa; se adotar, é greenfield.

### 4.3 Naming canônico de CUF — snake_case sem sufixo de plataforma

**Regra atual (SPEC §4):** o nome do campo é o mesmo em QUALQUER integração, em `snake_case`,
minúsculas, sem acento e **sem sufixo de plataforma**. A plataforma vai no campo `origem_pedido`.
Tabela completa (conteúdo e obrigatoriedade por evento) em `references/campos_canonicos.md` §5 —
não duplicar aqui.

```
numero_pedido  status_pedido  data_pedido  valor_pedido  qtd_itens_pedido  produtos_pedido
rastreio_codigo  rastreio_url  rastreio_transportadora  previsao_entrega  nota_fiscal
link_pagamento  origem_pedido
produtos_carrinho  valor_carrinho  qtd_itens_carrinho  link_carrinho
```

**Por que mudamos** (não foi gosto): o corpus real não tem convenção única. Sufixo de 2-3 letras da
origem (`NUV` Nuvemshop, `BW` BW Commerce, `YMP` Yampi) aparece quando o cliente tem mais de um
canal, some quando só tem um, e **o casing é inconsistente dentro do mesmo workflow** —
`StatusPedidoYMP` (PascalCase) convive com `produtosyampi` (lowercase) no AliveMed Dispatcher.
Isso é inconsistência real do corpus, não convenção a copiar (corpus de 21 workflows n8n em produção). Consequências
práticas: colisão ao entrar uma 2ª plataforma, prompt que precisa listar N nomes para ler o mesmo
dado, e CUF criado com typo que **não pode ser apagado** (a API não tem DELETE).

**Matriz do legado (histórico — o que existe em produção hoje):**

| Workflow | Sufixo | `field_name` legados | Canônico correspondente |
|---|---|---|---|
| Nordmann Meling Webhook Pedidos | NUV | `StatusPedidoNUV`, `NumeroPedidoNUV`, `ValorPedidoNUV`, `ProdutosPedidoNUV`, `RastreioPedidoNUV`, `LinkRastreioNUV` | `status_pedido`, `numero_pedido`, `valor_pedido`, `produtos_pedido`, `rastreio_codigo`, `rastreio_url` + `origem_pedido: nuvemshop` |
| Nordmann Meling Carrinho | NUV | `StatusPedidoNUV` (fixo `"Carrinho abandonado"`), `ProdutosCarrinhoNUV`, `ValorCarrinhoNUV`, `LinkCarrinhoNUV` | `status_pedido`, `produtos_carrinho`, `valor_carrinho`, `link_carrinho` |
| Degan BW Status de Pedido | BW | `StatusPedidoBW`, `StatusDescricaoBW`, `NumeroPedidoBW`, `DataPedidoBW`, `ValorPedidoBW`, `QtdItensPedidoBW`, `RastreioPedidoBW`, `PrevisaoEntregaBW`, `NotaFiscalBW` | `status_pedido`, `numero_pedido`, `data_pedido`, `valor_pedido`, `qtd_itens_pedido`, `rastreio_codigo`, `previsao_entrega`, `nota_fiscal` + `origem_pedido: bw` |
| Degan BW Carrinho (polling) | BW | `StatusPedidoBW` (fixo `"Carrinho"`), `ProdutosCarrinhoBW`, `ValorCarrinhoBW`, `QtdItensCarrinhoBW`, `LinkCarrinhoBW` | `produtos_carrinho`, `valor_carrinho`, `qtd_itens_carrinho`, `link_carrinho` |
| AliveMed Dispatcher PIX | YMP | `StatusPedidoYMP`, `NumeroPedidoYMP`, `ProdutosPedidoYMP`, `TotalPedidoYMP`, `ChavePixYMP` | `status_pedido`, `numero_pedido`, `produtos_pedido`, `valor_pedido`, `link_pagamento` + `origem_pedido: yampi` |
| AliveMed Dispatcher Carrinho | YMP | `StatusPedidoYMP` (fixo `"Carrinho"`), `produtosyampi`, `linkcarrinhoyampi` | `produtos_carrinho`, `link_carrinho` |
| Meiskin PIX Expirado | — | `carrinho_itens`, `carrinho_qtd_itens`, `carrinho_total`, `carrinho_link`, `pix_pago` | `produtos_carrinho`, `qtd_itens_carrinho`, `valor_carrinho`, `link_carrinho` |
| Alto Giro Notif Pedido Enviado | — | `numero_pedido`, `valor_pedido`, `data_pedido`, `codigo_rastreio`, `link_rastreio`, `transportadora` | já quase canônico: renomeia só `codigo_rastreio`→`rastreio_codigo`, `link_rastreio`→`rastreio_url`, `transportadora`→`rastreio_transportadora` |
| WL The Ladies / Seu Acompanhamento | — | `Last_Order_Product`, `order_url_2`, `order_paid_at` | `produtos_pedido`, `rastreio_url`, `data_pedido` |

⚠️ **Regra dura: em cliente rodando, NÃO renomear.** O flow do NexTags lê o nome antigo; renomear o
CUF sem tocar no flow quebra a mensagem em silêncio (o disparo retorna sucesso e não faz nada).
Em auditoria: registrar como legado no relatório, migrar só em janela combinada, campo e flow na
mesma mudança. **Projeto novo = canônico, sem exceção.**

⚠️ Tags do transacional também são canônicas: `transacional` + `Pedido Aprovado` / `Pedido Enviado` /
`Pedido Entregue` (`campos_canonicos.md` §4). O corpus legado usa nomes ad-hoc (`PIX Expirado` na
Meiskin, `pedido-enviado` no Alto Giro, `COMPRADOR` na WL) — mesma regra: não renomear em cliente
rodando, não criar novos assim.

---

## 5. Entrega ao NexTags & ANTIPADRÃO Nº1 (texto direto vs `send_flow`)

### 5.1 Como disparar (padrão atômico)

**Um único `POST /api/contacts`** com `actions[]` consolidando tudo (Alto Giro substituiu 3 chamadas separadas por 1):

```
phone / first_name / last_name / email  →  no ROOT do body (campos nativos, nunca CUF)
actions: [
  { action:'set_field_value', field_name:'status_pedido',   value:'enviado' },
  { action:'set_field_value', field_name:'numero_pedido',   value:'11488' },
  { action:'set_field_value', field_name:'rastreio_codigo', value:'<codigo>' },
  { action:'set_field_value', field_name:'rastreio_url',    value:'<url_com_utm>' },
  { action:'set_field_value', field_name:'origem_pedido',   value:'nuvemshop' },
  { action:'add_tag',   tag_name:'transacional' },
  { action:'add_tag',   tag_name:'Pedido Enviado' },
  { action:'send_flow', flow_id: <FLOW_ID_ENVIADO> }
]
```

- **Ordem fixa: `set_field_value`… → `add_tag`… → `send_flow` por último.** Em 100% do corpus, sem exceção. Fora de ordem, os CUFs chegam **vazios** no destino. (DOLPS "Regra 16".) [Certeza]
- `send_flow` é **o** mecanismo de disparo proativo. É o flow pré-montado no NexTags que renderiza a mensagem — o n8n **não** monta texto.
- Nomes canônicos, não do cliente (§4.3). `flow_id` aparece como number e como string em workflows diferentes; a API aceita ambos, mas **fixe um tipo por projeto**.

### 5.2 ANTIPADRÃO Nº1 — mandar TEXTO em vez de `send_flow`

> **"A plataforma NexTags NUNCA processa texto solto — toda resposta fora do JSON estruturado trava o fluxo."** (regra explícita, projeto DOLPS)

Casos reais que custaram tempo:

| Caso | O que aconteceu | Causa raiz | Como evitar |
|---|---|---|---|
| **Closet FIT** | JSON de `send_flow` **preso em fences ` ```json `** vazou como texto cru pro cliente | Few-shot dominance: todos os exemplos do prompt estavam dentro de fences → modelo copiou o fence no runtime | **Nunca** envolver exemplos JSON em fences markdown no prompt; usar separadores em prosa |
| **DOLPS** | Agente devolveu a chave de NF-e (44 díg.) como **texto** + instrução manual, em vez de rotear via `send_flow` p/ suporte | Lógica assumia que expor o dado cru resolvia; link SEFAZ quebra (captcha) | Quando o dado cru não resolve, **rotear pra humano via `send_flow`**, não despejar texto |
| **Wazzu** | "JSON virou texto bruto" na 2ª execução | Causa estava no **pipeline do n8n** (onde a resposta da IA é salva/reenviada), não no formato | Investigar o pipeline antes de mexer no formato. `text` é **string direta**, nunca `{body:...}` (esse é formato interno do WhatsApp Cloud API) |
| **Veuske** | "Transferência fantasma": IA **dizia** "vou te direcionar" mas o `send_flow` não disparava | Anti-loop checava o **texto** da resposta, não o estado gravado | Detecção de transferência deve se basear no **CUF gravado no momento em que o `send_flow` dispara**, não em heurística de texto |
| **Amo Calçados** (n8n) | 1 workflow envia texto livre direto ao cliente em vez de disparar flow | — | Sempre `send_flow`; texto é tipo de mensagem dentro do flow, não saída livre |

### 5.3 `send_flow` — armadilha de validação

- **`/send/{flow_id}` retorna `success:true` até pra `flow_id` inexistente/falso** (Alto Giro). **Nunca** confie na resposta da API como prova de entrega — valide com recebimento real no WhatsApp.
- `/send/{flow_id}` exige `Content-Length > 0` → retorna **411** se o corpo vier vazio; sempre mandar body mínimo.
- **Placeholder de `flow_id` shippado em produção é RED FLAG:** Dolps v1 tinha `flow_id=11111111111` nas 4 branches; Viens tinha `COLE_O_FLOW_ID`. Sempre preencher e validar E2E.

---

## 6. Normalização de payload

### 6.1 Telefone — snippet único, validação final, e FIXO não recebe

O corpus tem **pelo menos 4 implementações independentes** da mesma normalização BR (Nordmann `fone()`, Degan `fone()`, Meiskin `formatarTelefone`, WL Shopify, AliveMed `formatarTelefone`), replicadas por Code node com pequenas divergências. **Consolidado num snippet só:** `assets/_helpers.js`.

Lógica: extrai dígitos, garante prefixo `55`, separa DDD e decide o `9` do local:

```js
if (dddN >= 11 && dddN <= 29) {
  if (/^[2345]/.test(local)) {                                        // 2-5 => FIXO
    if (local.length === 9 && local[0] === '9') local = local.slice(1); // remove 9 indevido
    local = local.slice(-8);
  } else if (local.length === 8) {
    local = '9' + local;                                              // celular sem 9 => adiciona
  }
} else {                                                              // DDD fora de 11-29
  if (local.length === 9 && local[0] === '9') local = local.slice(1);
  local = local.slice(-8);
}
```

**Validação final obrigatória** (padrão AliveMed, a implementação mais defensiva do corpus): `/^55\d{10,11}$/`. Não bateu → `skip(item, 'telefone_invalido')`, nunca mandar o que sobrou.

⚠️ **Número FIXO não recebe `send_flow`/mensagem via API.** Ao entrar na plataforma o número ganha o 9 extra e vira inválido — a NexTags/ChatRace adiciona o `9` cegamente a fixo, corrompendo o ID do contato (fixo `55DD3XXXXXXX` vira `55DD93XXXXXXX`, que não existe). Evidência: dono do projeto (2026-09-03) + Alto Giro/ChatRace.

Regra: guard **antes** do disparo, `ehTelefoneFixo()` = DDD + local de 8 dígitos começando em 2-5 → `skip(item, 'telefone_fixo')`, e a contagem de descartes vai no relatório. Nunca "tentar mesmo assim". Vale também para o `nextags-webchat-tester`: fixo não serve como contato de teste (e webchat não tem telefone nenhum).

### 6.2 Demais normalizações

- **`verificarDado(valor, 'Não informado')`**: NexTags rejeita `null`/`undefined` no payload. Todo campo que vira CUF passa por isso. ⚠️ E nenhum CUF que alimenta variável de template do WhatsApp pode ir vazio: erro Meta `#131008` **derruba o template inteiro**, não só o campo (Meiskin, Code "Preparar PIX").
- **`separarNomeSobrenome`**: `/api/contacts` espera `first_name` + `last_name` separados.
- **Concatenação de itens** do pedido numa string legível (`Produto (Qtd: 2, R$ X)`).
- ⚠️ **Query string em link/CUF**: nunca concatenar `&utm_...` sem checar se já existe `?` (bug real quebrou `link_checkout_abandono` na Mayuí). Ver `link_envio_pattern.md` da mcp-builder — **UTM é obrigatório** em todo link.

---

## 7. Resiliência & rate limit

**Config canônica do HTTP Request (padrão Rafa — maioria dos legíveis):**
```
retryOnFail: true
waitBetweenTries: 5000     // 5s
onError: continueErrorOutput   // não trava a chain nem perde o INSERT de dedup
```
- **n8n httpRequest v4.4:** usar `specifyBody:'json'` + `jsonBody`. `jsonParameters`/`bodyParametersJson` **não serializa** → gera falso `"Invalid phone number"` no POST /contacts. (Alto Giro) [Certeza]
- **Anti-429:** o rate limit da **API NexTags é ~100 req/60s** (evidência: Privilège `b9IJblHOEurFgj6o`, *"ajustar N e batchInterval do HTTP Request pra respeitar rate limit real da API NexTags (100 req/60s — ver workflow EXPORTAR CONVERSAS v5)"*). Martz ~60/min. Zencial detecta `error.code==429` e re-tenta; em loops de enriquecimento, `batchSize 1` + intervalo ~500ms. Nunca rodar backfill sem throttle.
- **Disparo em lote → "pesca-e-marca"** em vez de loop rápido: cron de baixa frequência (Privilège usa `*/3 8-19 * * *`), `limit: 1`, `orderBy id ASC`, filtro `enviado != true`, marca a linha antes do próximo tick. Nasceu de marcação de SPAM pela Meta em broadcast nativo. ⚠️ Desativar o workflow quando a fila esvaziar, senão roda vazio para sempre. ⚠️ Escalar volume **muda a arquitetura** (limit=N + `splitInBatches` + update em lote), não é editar o cron.
- **Trio de resiliência para cron crítico** (padrão Otogama): `settings.errorWorkflow` (pega falha que rodou pelo menos um node) **+** Data Table de heartbeat escrita pelo próprio fluxo **+** um Watchdog em cron separado que lê o heartbeat e alerta pela **ausência**. O Error Trigger não pega o caso "o worker do n8n morreu antes de qualquer node" (execução com `startedAt: null`) — só o watchdog externo vê. Alerta em transição de estado (ok→fora, fora→ok), nunca a cada tick, e toda falha terminal de fila de retry precisa de canal humano ("desistir precisa doer em alguém").
- **Guards antes do disparo:** telefone presente/válido (Neurofood, Mayuí, Exclusiva, Casa Marquez, Veuske). Para carrinho: idade (1-48h) + conversão (checar se não virou pedido) + dedup (Alto Giro espera 1h e confere conversão).
- **RED FLAGS de resiliência:** sem `retryOnFail` (Alto Giro, Amo, Privilège, HIVEN, Iorane, Boca Rosa, Bem Beleza); sem guard de telefone (Iorane, Bem Beleza, Wazzu, Vitabe, BB); `optional chaining` incompleto que derruba o Code node (Cantarola: `data?.invoice.number`).

---

## 8. Segurança & token

- **Endpoint canônico é `POST /api/contacts`.** `/api/users` aparece só no AliveMed Dispatcher, sem explicação na sticky — variante **legada**, não usar em projeto novo. (corpus de 21 workflows n8n em produção)
- **Token NexTags:** `X-ACCESS-TOKEN` **hardcoded em texto puro** no header do HTTP Request é a convenção quase universal (27 de 29). Fica na instância privada do n8n (não vaza no git da skill). Só Uniformizeei e Verdanda usam credential do n8n. Aceitável pela convenção Walkers, mas **credential nomeada é mais segura** — permite rotação sem editar N nodes; preferir onde der. [Provável]
- **Token é por conta.** Token errado retorna `200` e escreve na conta errada, sem erro visível (Wazzu com token da Hebreus Doze). Rodar `GET /accounts/me` antes de qualquer setup e anotar o nome da conta no sticky.
- **Nada de credencial em arquivo da skill nem em sticky:** placeholders `<NEXTAGS_ACCESS_TOKEN>`, `<NEXTAGS_GATEWAY_TOKEN>`, `<TELEFONE>`, `<IP_N8N>`, `<FLOW_ID_...>`.
- **HMAC:** validar assinatura no webhook de entrada **onde a plataforma assina** — Bling (Amo, HIVEN), Martz, SuaAgenda. Responder 200 rápido e validar HMAC antes de processar.
- **CUFs tipo TEXTO:** CUF criado como tipo **NÚMERO** faz `set_field_value` **descartar o valor silenciosamente** (sem erro). Todo CUF setado via `/api/contacts` deve ser **TEXTO** no NexTags. (Mayuí) [Certeza]
- **Variável de template vazia = flow quebrado:** WhatsApp `#131008` derruba o template inteiro se **qualquer** CUF interpolado estiver vazio. Garanta 100% das variáveis preenchidas antes do `send_flow` (ou tenha variante neutra). (Mayuí)

---

## 9. Antipadrão transversal — copy-paste entre clientes

Clonar workflow de outro cliente **sem trocar todas as referências** é a causa nº1 de "disparo fantasma":

- **Wazzu:** usou token `X-ACCESS-TOKEN` da conta **Hebreus Doze** (1636393) e apontou a Data Table de dedup pra tabela da Hebreus Doze → `send_flow` retornava success mas era **no-op silencioso** na conta errada.
- **Vitabe:** função `formatarNPedido` removia prefixo `RENOVABE-` (nome de **outro** cliente) — código copiado sem adaptar; corrompe números de pedido.

> **Ao clonar workflow, trocar TODAS as referências:** token/conta, Data Table de dedup, `field_name` dos CUFs, e `flow_id`. [Certeza]

---

## 10. Checklist de revisão (antes de ativar)

**Arquitetura**
- [ ] Workflow criado/atualizado **por API/MCP do n8n**, nunca por navegador: `search_workflows` → `validate_workflow` → `create_workflow_from_code`/`update_workflow` → `publish_workflow`
- [ ] Roteamento escolhido pela **forma de emissão** da plataforma (§1), não por gosto
- [ ] Gatilho correto por plataforma (§2) — webhook onde existe, polling onde não existe
- [ ] Estágio roteado por **id de status** (§3.6); fallback por texto só sem id, com word-boundary
- [ ] Switch por `status.alias`, nunca por `body.event`
- [ ] Sem credencial nativa da loja? Gateway Proxy conferido (`gateway_proxy_nextags.md`): `storeId` certo, escopo `proxy:passthrough`

**Dedup**
- [ ] Dedup via **Data Table** (nunca in-memory), chave `order_id` interno — ou `fulfillment_id` se houver envio parcial
- [ ] Compara **estágio anterior × novo**, não "existe linha"
- [ ] **Dedup gravado SÓ no ramo de sucesso** do POST na NexTags (§3.5)
- [ ] `order_id` (dedup) separado de `numero_pedido` (CUF de exibição, sem `#`)
- [ ] Multi-plataforma: Data Tables separadas por origem + `origem_pedido` como discriminador

**Campos e disparo**
- [ ] `field_name` **canônicos** em snake_case, sem sufixo de plataforma (`campos_canonicos.md` §5); legado do cliente **não renomeado**
- [ ] Tags canônicas: `transacional` + `Pedido Aprovado`/`Pedido Enviado`/`Pedido Entregue`
- [ ] CUFs criados na conta antes de ativar (setup idempotente, `assets/setup_cufs_canonicos.js`); todos tipo **TEXTO** (`type: 0`)
- [ ] `GET /accounts/me` confirma a conta do token; `GET /accounts/flows` confirma que cada `flow_id` existe
- [ ] Disparo atômico: 1 `POST /api/contacts` com `actions[]` na ordem `set_field_value` → `add_tag` → `send_flow`
- [ ] `send_flow` (nunca texto direto); `flow_id` real e validado E2E — ou `0` + guard + `NÃO ATIVAR antes de…` no sticky
- [ ] Todas as variáveis do template preenchidas (var vazia = `#131008` derruba o flow)
- [ ] UTM em todo link (`link_envio_pattern.md`)

**Guards e resiliência**
- [ ] `formatarTelefone` + validação `/^55\d{10,11}$/` + `ehTelefoneFixo` (fixo **não** dispara) + `verificarDado` + `separarNomeSobrenome`
- [ ] Todo skip carrega `_motivo`; erro global → `throw`, erro pontual em loop → `skip`
- [ ] HTTP: `retryOnFail:true` + `waitBetweenTries:5000` + `onError:continueErrorOutput` + `specifyBody:'json'`
- [ ] Anti-429 (NexTags ~100 req/60s); guards de idade/conversão em carrinho
- [ ] HMAC validado onde a plataforma assina (Bling/Martz)
- [ ] Cron crítico: `errorWorkflow` + heartbeat + watchdog

**Entrega**
- [ ] Sticky note pelo modelo canônico (título, endpoint, ESTADO EM dd/mm, CREDENCIAIS, NÃO ATIVAR antes de…, ARMADILHAS com evidência, DE ONDE VEIO a lista de campos, decisões negativas)
- [ ] Sticky/descrição **não** diz "pronto/ativo" se ainda há placeholder no código
- [ ] Clonou de outro cliente? Trocou token + `storeId` + Data Table + `field_name` + `flow_id` + nomes de node
- [ ] Naming: nome do cliente em todos os workflows e na Data Table

---

## Matriz de evidências

| Regra | Evidência (cliente / workflow) |
|---|---|
| Endpoint único + Switch p/ evento genérico | Veuske (`single_endpoint_switch`, Yampi), Amo Calçados (`p0wnwlfQOmk5JTMI` Bling), Dolps (VTEX), BB (Tray), Zencial |
| 1 workflow por status p/ eventos distintos | Exclusiva (4 wf Nuvemshop), Mania Brasil, Divinnah Gaia, Alto Giro (Shopify) |
| Flow router único ("1 fluxo de roteamento") | Neurofood (`1782312754895`), Nalisa (`1780321795848`), Mayuí, IMP |
| Switch por `status.alias` não `body.event` | Veuske (referência Rafa) |
| Yampi emite webhook de carrinho (não cron) | Veuske (correção 2026) |
| Schema de dedup `order_id/status/updated_at/phone` | Neurofood, Mania Brasil, Divinnah Gaia |
| Chave composta de dedup | Veuske (`nPedido+idPedido`), Dolps (`orderId\|lastChange`), Mayuí (`order_id\|evento`), BB, Exclusiva |
| Dedup por tag | Alto Giro (`ag-entregue-notif`) |
| Dedup in-memory quebrado (RED FLAG) | Viens (`sd.seen`) |
| **Dedup só grava após sucesso do POST** | Nordmann v3 (`ln7ZTWGwTyV2KVRQ`), Nordmann Carrinho v2 (`bvR8NeB5e4BdOzyD`, 51 clientes), Meiskin PIX Expirado |
| **Estágio por id de status, não por texto** | Degan BW (`rroCGCrCnb9R1U5s`: "Em Entrega" id 8 casava com `/entreg/`) |
| Compara estágio anterior × novo | Degan BW (`stored.status === stage`) |
| Chave por `fulfillment_id` (envio parcial) | Alto Giro (`w1KeVwUnJGdwpidU`) |
| Chave composta por etapa de funil | Meiskin (`FsnnAiE2LADC91aZ`, `etapa_30/65/120_enviada`) |
| `rowNotExists` como dedup gate | Alto Giro (node "Dedup Gate") |
| Naming legado CamelCase + sufixo (casing inconsistente) | Nordmann (NUV), Degan (BW), AliveMed (`StatusPedidoYMP` × `produtosyampi` no mesmo workflow) |
| `flow_id = 0` como fail-safe deliberado | Degan BW (`flow_pago/enviado/entregue: 0`), Degan Carrinho (`flow_carrinho: 0`) |
| Skip com `_motivo` (padrão maduro) | Degan Carrinho Polling (`skip(motivo)`), Meiskin |
| Sticky "pronto" com placeholder no código | `qRIs9L07G5auvhRM` (`active:true`, descrição diz "Auth pendente") |
| Rate limit NexTags ~100 req/60s | Privilège (`b9IJblHOEurFgj6o`) |
| Broadcast "pesca-e-marca" (anti-SPAM Meta) | Privilège (cron `*/3 8-19 * * *`, `limit: 1`) |
| Heartbeat + watchdog + errorWorkflow | Otogama (`Gtxxg7YTbApcT4tE`, `W7cuLshLtted1VPz`, `AYlX3rF3ZeLePrqn`) |
| Gateway Proxy NexTags em produção | Cantarola Backend (`…/v1/gateway/stores/{storeId}/products`) |
| Telefone fixo não recebe (9 extra) | dono do projeto 2026-09-03; Alto Giro/ChatRace |
| Validação final `/^55\d{10,11}$/` | AliveMed (`formatarTelefone`, a mais defensiva do corpus) |
| `/api/users` como variante legada | AliveMed Dispatcher (único do corpus; resto usa `/api/contacts`) |
| `order_id` interno ≠ `order_number` exibido | Veuske, Neurofood, Mania, Divinnah, Cabelos Rainha |
| Multi-plataforma: CUF por origem / genérico+discriminador | HIVEN (Bling separado; Yampi/Shopify normalizado) |
| Multi-plataforma: Data Table dedup por origem | Amo Calçados (Bling + Loja Integrada) |
| POST atômico único com `actions[]` | Alto Giro (substituiu 3 chamadas) |
| `set_field_value` antes de `send_flow` | DOLPS (Regra 16) |
| Texto direto em vez de `send_flow` (antipadrão) | Closet FIT (fences), DOLPS (NF-e), Wazzu (`{body}`), Veuske (transf. fantasma), Amo (n8n) |
| `success:true` mente / 411 sem body | Alto Giro |
| Placeholder de flow_id em produção | Dolps v1 (`11111111111`), Viens (`COLE_O_FLOW_ID`) |
| `retryOnFail+waitBetweenTries+onError` | Cabelos Rainha, Neurofood, Nalisa, Veuske, Mania, Divinnah, Exclusiva, Zencial (maioria) |
| httpRequest v4.4 `specifyBody:'json'` | Alto Giro (falso "Invalid phone number") |
| Anti-429 explícito | Zencial (detecta `error.code==429`), Martz ~60/min (Mayuí) |
| Telefone: ChatRace adiciona 9 a fixo | Alto Giro |
| CUF tipo NÚMERO descarta valor | Mayuí |
| Template var vazia quebra flow (#131008) | Mayuí |
| HMAC onde a plataforma assina | Amo (Bling), HIVEN (Bling) |
| Copy-paste cross-cliente (RED FLAG) | Wazzu (token/table Hebreus Doze), Vitabe (`RENOVABE-`) |
| Token hardcoded no header (convenção) | 27/29 clientes; credential só em Uniformizeei, Verdanda |

---

## Questões em aberto (precisam de confirmação humana)

1. **Prefixo de número multi-plataforma** (`SHP-`/`YMP-`) não existe em produção — adotar como padrão greenfield? [SEM EVIDÊNCIA DIRETA]
2. **Token via credential vs hardcoded** — migrar a convenção pra credential do n8n? (mais seguro, mais fricção de auto-vínculo — ver quirk Veuske na mcp-builder).
3. **72 clientes `unreadable`** — habilitar `availableInMCP` neles pra completar a auditoria numa 2ª rodada?
4. ~~**Enum de `status_pedido`**~~ — **fechado pelo dono em 2026-09-03**: `aprovado|enviado|entregue|cancelado|pronto_retirada|pix_gerado|pix_expirado` é o enum canônico (`campos_canonicos.md` §5 e §9).
5. **Tipo de `flow_id`** (number ou string): a API aceita os dois no corpus, não há decisão oficial — **confirmar com o dono** qual fixar.
6. **`/api/users` (AliveMed)** — é equivalente a `/api/contacts` ou outra API? Sem explicação na sticky; tratado como legado até o dono confirmar. [SEM EVIDÊNCIA DIRETA]

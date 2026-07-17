# Padrão Real de Webhooks Transacionais NexTags

> **Validado por auditoria** de 29 fluxos de produção legíveis no n8n (de um universo de 159 workflows transacionais em 101 clientes) + mineração de 13 projetos de conversa (45 episódios, 9 incidentes de `send_flow` vs texto).
> Data: 2026-07-16. Toda regra aqui carrega evidência (cliente/workflow) na [Matriz de evidências](#matriz-de-evidências). O que é recomendação sem lastro em produção está marcado **[SEM EVIDÊNCIA DIRETA]**.

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
- **Dedup por TAG de controle** (semântica "notificar 1x na vida"): Alto Giro usa a tag `ag-entregue-notif` em vez de Data Table no fluxo Entregue. Válido. 

### 3.3 Quando é obrigatório vs dispensável

- **Obrigatório:** qualquer fonte que faz replay (Yampi/Shopify/Nuvemshop reenviam o mesmo webhook 2-3x) e **todo polling/cron** (Nalisa, Exclusiva cron, Wazzu feeder). Sem dedup = cliente recebe a mesma mensagem 2-5x.
- **Dispensável:** carrinho abandonado por **webhook push único** (Martz/Yampi disparam 1x por cart) — Mania Brasil cart não tem dedup e está correto.

### 3.4 Antipadrão de dedup (RED FLAG real)

- **Viens:** dedup feito com objeto **em memória** `sd.seen = {[order_id]:true}`, sobrescrito a cada execução → **não persiste**, dedup quebrado. Sempre Data Table, nunca variável in-memory. [Certeza]

---

## 4. Número de pedido & concatenação multi-plataforma

**Descoberta central:** a esmagadora maioria dos clientes é **mono-plataforma**, então não há tratamento de colisão — e vários auditores sinalizaram isso como **risco latente** ("sem prefixo/CUF de origem; colidiria se entrar uma 2ª plataforma").

### 4.1 Regra validada (vale pra todos)

**Separe `order_id` de `order_number`:**
- `order_id` = ID **interno** da plataforma → usado **só** na chave de dedup. Globalmente único por loja.
- `order_number` = número **visível ao cliente** → usado **só** na CUF de exibição (`NumeroPedidoYMP` etc.).
- **Nunca** use `order_number` como chave de dedup (pode repetir). Veuske resolve com chave composta `nPedido + idPedido` — o ID interno desambigua.

Normalização comum: remover `#` do `order.name` do Shopify (Casa Marquez, Alto Giro, Mania); Divinnah corta em `.` (`#1234.1` → `1234`).

### 4.2 Multi-plataforma no mesmo contato (a "concatenação")

Só **2 casos reais** auditados — e eles definem o padrão:

- **HIVEN** (Bling + Yampi + Shopify): o workflow Bling grava em **CUFs separados por origem** (`numero_pedido_bling`, `pedido_id_bling`); o workflow Yampi/Shopify tem um node **"Detectar e Normalizar"** que lê de Yampi **OU** Shopify (pelos headers/body) e grava em **campos genéricos** com discriminador de plataforma.
- **Amo Calçados** (Bling + Loja Integrada): **Data Tables de dedup separadas por plataforma** — cada origem tem seu próprio namespace de `order_id`/`pedido_id`.

**Recomendação consolidada para multi-plataforma:**
1. **Data Table de dedup separada por plataforma** (sempre — evidência Amo). [Certeza]
2. CUF: ou **por origem** (`NumeroPedidoBling`, `NumeroPedidoShopify` — evidência HIVEN), ou **genérica + CUF `OrigemPedido`** discriminador (evidência HIVEN).
3. Prefixo no número (ex.: `SHP-1234`/`YMP-5678`) é uma opção limpa **[SEM EVIDÊNCIA DIRETA]** — nenhum cliente auditado usa; se adotar, é greenfield.

---

## 5. Entrega ao NexTags & ANTIPADRÃO Nº1 (texto direto vs `send_flow`)

### 5.1 Como disparar (padrão atômico)

**Um único `POST /api/contacts`** com `actions[]` consolidando tudo (Alto Giro substituiu 3 chamadas separadas por 1):

```
actions: [
  { action:'set_field_value', field_name:'StatusPedidoYMP', value:'Enviado' },
  { action:'set_field_value', field_name:'RastreioPedidoYMP', value:'<code>' },
  { action:'add_tag', tag_name:'pedido-enviado' },
  { action:'send_flow', flow_id: <FLOW_ID_ENVIADO> }
]
```

- **`set_field_value` SEMPRE antes de `send_flow`** no mesmo array — senão os CUFs chegam **vazios** no destino. (DOLPS "Regra 16", regra confirmada e repetida.) [Certeza]
- `send_flow` é **o** mecanismo de disparo proativo. É o flow pré-montado no NexTags que renderiza a mensagem — o n8n **não** monta texto.

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

- **Telefone BR** (`formatarTelefone`): adiciona/remove o `9` corretamente por DDD. ⚠️ O ChatRace/NexTags **adiciona `9` cegamente a fixos**, corrompendo o ID do contato (fixo `551930971505` vira `5519930971505`) — normalizar **antes** de enviar. (Alto Giro)
- **`verificarDado(valor, 'Não informado')`**: NexTags rejeita `null`/`undefined` no payload. Todo campo que vira CUF passa por isso.
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
- **Anti-429:** NexTags e Martz têm rate limit (~60/min na Martz). Zencial detecta `error.code==429` e re-tenta; em loops de enriquecimento, usar `batchSize 1` + intervalo ~500ms. Nunca rodar backfill sem throttle.
- **Guards antes do disparo:** telefone presente/válido (Neurofood, Mayuí, Exclusiva, Casa Marquez, Veuske). Para carrinho: idade (1-48h) + conversão (checar se não virou pedido) + dedup (Alto Giro espera 1h e confere conversão).
- **RED FLAGS de resiliência:** sem `retryOnFail` (Alto Giro, Amo, Privilège, HIVEN, Iorane, Boca Rosa, Bem Beleza); sem guard de telefone (Iorane, Bem Beleza, Wazzu, Vitabe, BB); `optional chaining` incompleto que derruba o Code node (Cantarola: `data?.invoice.number`).

---

## 8. Segurança & token

- **Token NexTags:** `X-ACCESS-TOKEN` **hardcoded em texto puro** no header do HTTP Request é a convenção quase universal (27 de 29). Fica na instância privada do n8n (não vaza no git da skill). Só Uniformizeei e Verdanda usam credential do n8n. Aceitável pela convenção Walkers, mas **credential é mais seguro** — preferir onde der. [Provável]
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

- [ ] Roteamento escolhido pela **forma de emissão** da plataforma (§1), não por gosto
- [ ] Gatilho correto por plataforma (§2) — webhook onde existe, polling onde não existe
- [ ] Switch por `status.alias`, nunca por `body.event`
- [ ] Dedup via **Data Table** (nunca in-memory) com `order_id` interno como chave; status_compare pra evitar replay
- [ ] `order_id` (dedup) separado de `order_number` (CUF de exibição)
- [ ] Multi-plataforma: Data Tables separadas por origem + CUF por origem ou discriminador
- [ ] Disparo atômico: 1 `POST /api/contacts` com `actions[]`, **`set_field_value` antes de `send_flow`**
- [ ] `send_flow` (nunca texto direto); `flow_id` real e validado E2E (não placeholder)
- [ ] `formatarTelefone` + `verificarDado` + `separarNomeSobrenome` no Code node
- [ ] HTTP: `retryOnFail:true` + `waitBetweenTries:5000` + `onError:continueErrorOutput` + `specifyBody:'json'`
- [ ] Anti-429 em polling/backfill; guard de telefone (e idade/conversão em carrinho)
- [ ] HMAC validado onde a plataforma assina (Bling/Martz)
- [ ] CUFs tipo **TEXTO**; todas as variáveis do template preenchidas
- [ ] UTM em todo link (`link_envio_pattern.md`)
- [ ] Clonou de outro cliente? Trocou token + Data Table + field_names + flow_id
- [ ] Naming: nome do cliente em todos os workflows; CUF CamelCase+sufixo de origem

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

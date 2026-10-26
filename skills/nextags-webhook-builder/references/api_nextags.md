# API NexTags — inventário de endpoints e receitas usadas pelas skills

> Adaptação do documento oficial "Nextags AI API Reference (Optimized for Claude Code)" v1.1
> (enviado pelo dono do projeto, 2026-09-03), acrescido da seção **§3 Receitas** — o que as skills
> realmente chamam, em que ordem e com que armadilha.
>
> **Conferido em 2026-10-26 contra o contrato oficial** (`https://docs.nextags.com.br/openapi.json`,
> OpenAPI 3.1, 86 operações). Em divergência, vale o contrato e a doc (`docs.nextags.com.br`): corrija
> aqui. A referência completa, com body, enums e exemplos de cada endpoint, está na skill `nextags-api`
> (`references/endpoints.md` e `live_shapes.md`). Onde esta página traz evidência de produção que a doc
> não cobre, ela vem marcada como tal.
>
> **Base:** `https://app.nextagsai.com.br/api/` · **Auth:** header `X-ACCESS-TOKEN: <NEXTAGS_ACCESS_TOKEN>`
>
> ⚠️ Não confundir com o **Gateway Proxy** (`https://api.nextags.com.br/v1/gateway/...`, header
> `Authorization: Bearer`), que é proxy para a API da plataforma de e-commerce. Ver `gateway_proxy_nextags.md`.

---

## 0. Regras transversais

| Regra | Detalhe | Evidência |
|---|---|---|
| **Endpoint canônico de disparo é `POST /api/contacts`** | Um único POST atômico com `actions[]`. ⚠️ A doc oficial documenta só a **criação** (`phone` obrigatório) e diz que não sabe o que acontece com telefone já existente; o corpus usa o mesmo POST para contato existente (CUFs e flow rodam normalmente): isso é comportamento de produção, **não documentado**. A doc recomenda procurar antes (`find_by_custom_field?field_id=phone`). A resposta da criação também não é descrita: para obter o `contact_id`, busque pelo telefone. | 8 clientes do corpus (Nordmann, Degan BW, Meiskin, Alto Giro, WL, Otogama, Privilège); doc: `guias/criar-ou-atualizar-contato` |
| **`/api/users` é variante legada** | Só o AliveMed Dispatcher usa, sem explicação na sticky. **Não usar em projeto novo.** | AliveMed (único no corpus) |
| **Header sempre `X-ACCESS-TOKEN`** | Formato do token: `<id numérico>.<string alfanumérica>`. **Credencial nomeada do n8n é o padrão** (decisão do dono, 2026-09-03): rotaciona sem editar N nodes e não vaza em export. Hardcoded é o que existe em cliente antigo — não copiar em projeto novo. Conferir o vínculo depois de todo `update_workflow`. | corpus de 21 workflows |
| **Token é por conta** | Token errado retorna `200` e escreve na **conta errada**, sem erro visível. Conferir a conta com `GET /accounts/me` antes de rodar setup. | Wazzu com token da Hebreus Doze |
| **Rate limit ~100 req/min por conta, somando todas as integrações** | A conta tem uma chave só: n8n, Zapier, Make e o sistema do cliente dividem o mesmo teto. A doc não confirma o código devolvido ao estourar: trate `429` e `5xx` com espera crescente (1, 2, 4, 8 s, até ~5 tentativas), nunca em laço imediato. Disparo em lote precisa de throttle (~1 chamada/s deixa folga; "pesca-e-marca": cron de baixa frequência, `limit: 1`, marca antes do próximo tick). | Privilège (`b9IJblHOEurFgj6o`); doc: `comecar/limites-e-erros` |
| **Ordem de `actions[]`** | `set_field_value`… → `add_tag`… → `send_flow` **por último**, sem exceção em todo o corpus. | corpus de 21 workflows / DOLPS "Regra 16" |
| **`success:true` mente** | `/send/{flow_id}` retorna sucesso até para `flow_id` inexistente. Validar com recebimento real no WhatsApp. | Alto Giro |
| **Timeout em escrita não é "falhou"** | Se um `POST` que cria ou envia estourar o tempo, a NexTags pode ter feito a operação. Antes de repetir: criar contato → procurar pelo telefone; enviar flow/texto/conteúdo → **não repetir às cegas** (o contato recebe de novo). Consulta (`GET`) pode repetir sempre. O trade-off com `retryOnFail` está em §3.4. | doc: `comecar/limites-e-erros` ("Repetir sem duplicar") |
| **Erro `401` vem com `Content-Type: text/html`** | O corpo é JSON (`{"error":{"code":401,"message":"No valid API key provided."}}`), mas o cabeçalho diz HTML: leia o corpo como JSON sem depender do cabeçalho. O corpo de `400`, `402` e `404` não está documentado: guarde inteiro no log. | doc: `comecar/limites-e-erros` |
| **Formatos** | Telefone só dígitos com DDI (`5511988776655`, sem `+`). IDs são inteiros no contrato mas **voltam como string** na prática; `order_id` é texto. Datas de objeto em UTC `AAAA-MM-DD HH:MM:SS`; `last_*` do contato em Unix **ms**; valor de CUF Data/Data e hora em Unix **segundos** (ms vira data errada); sim/não = `1`/`0`. Dinheiro: `total`, `subtotal`, `coupon_discount` e `amount_received` em **centavos**; `price` de item/produto e `value` de oportunidade em **reais**. | doc: `comecar/visao-geral`, `comecar/campos-e-variaveis`; IDs como string: verificado ao vivo em 2026-10-26 (skill `nextags-api`, `live_shapes.md`) |

---

## 1. Modelos (schemas) relevantes

### `Custom_field`

| Propriedade | Tipo | Descrição |
|---|---|---|
| `id` | integer | |
| `name` | string | |
| `type` | integer | ver tabela §1.1 |
| `value` | string | `type == 0` → string; senão número |

#### 1.1 Tipos de CUF

| `type` | Nome | Uso nas skills |
|---|---|---|
| `0` | Text | **padrão de tudo** que a IA ou o n8n escreve via `set_field_value` |
| `1` | Number | ⚠️ `set_field_value` em campo tipo Número **descarta o valor em silêncio** (sem erro). Só `nota_nps`. (evidência: Mayuí; reincidente em Degan `rroCGCrCnb9R1U5s`) |
| `2` | Date | timestamp Unix **em segundos** (para Data, meia-noite de Brasília; ms vira data errada) |
| `3` | Date & Time | timestamp Unix **em segundos** — `data_inicial_pipeline`, `data_vencimento`, `Data_atual`, `data_nps` |
| `4` | Boolean | `1` ou `0` (textos como `sim`/`true` podem não virar o valor esperado) |
| `5` | Long Text | alternativa para `resumo_pipeline` |
| `6` | Select | `tipo_setor`, `prioridade_pipeline` — valor gravado tem que bater EXATAMENTE com a opção cadastrada |
| `7` | Multi Select | |

⚠️ **Pela API só se criam os tipos `0` a `4`** (`POST /accounts/custom_fields`). `5` Long Text, `6` Select e
`7` Multi Select nascem no painel: por isso `tipo_setor` e `prioridade_pipeline` (tipo 6) não saem do setup por
API. O tipo não muda depois de criado. (doc: `referencia/campos-personalizados/criar-campo-personalizado`,
`comecar/campos-e-variaveis`.)

### `Contact`

`id`, `page_id`, `first_name`, `last_name`, `channel` (0 Messenger, 5 WhatsApp, 8 Telegram,
9 Webchat, 10 Instagram, 17 TikTok), `profile_pic`, `locale`, `gender`, `timezone`,
`last_sent`, `last_delivered`, `last_seen`, `last_interaction` (os quatro em Unix ms), `subscribed_date` (UTC),
`subscribed` (1 inscrito, 2 inscrição cancelada: não recebe Broadcasts), `tags[]`, `custom_fields[]`.
(Contrato oficial, modelo `Contact`; a lista de canais antiga com SMS e Google Business Message não consta mais.)

⚠️ `channel: 9` (Webchat) não tem número de telefone — por isso o webchat **não serve** para testar
fluxo transacional/`send_flow` por API (SPEC §7).

### `Order` / `Cart` / `ProductCart`

⚠️ O contrato atual **não tem o modelo `Order`**: `GET /contacts/{id}/order/{order_id}` devolve o formato
`Cart` abaixo, com `total`, `subtotal` e `coupon_discount` em **centavos** (e `price` de cada item em reais).
O `Order` a seguir é do contrato antigo (v1.1 de 2026-09-03): não conte com `shipping_cost`, `total_taxes`,
`total_discounts` nem `status` na resposta sem testar.
`Order` (legado): `id`, `page_id`, `user_id` (contact id), `created_at`, `created_timestamp`, `currency`,
`total`, `subtotal`, `shipping_cost`, `total_taxes`, `total_discounts`, `total_items`,
`coupon_discount`, `coupon`, `status`, `line_items[]`, `contact`.
`Cart`: `order_id`, `page_id`, `user_id`, `currency`, `total`, `subtotal`, `total_items`,
`coupon_discount`, `coupon`, `line_items[]`, `contact`.
`ProductCart`: `id`, `name`, `img`, `price` (não é em centavos), `amount` (quantidade),
`descr_min`, `manufacturer` (vendor id), `variant`, `user_msg`.

⚠️ Este é o **carrinho nativo da NexTags**, não o carrinho da loja. Carrinho abandonado de
Shopify/Nuvemshop/Yampi vem da plataforma (ou do Gateway Proxy), não daqui.

### `Opportunity` / `OpportunityComment` / `Pipeline` / `PipelineStage`

`Opportunity`: `id`, `contact_id`, `title`, `description`, `value`, `status`, `priority`, `stage`,
`assigned_admins[]`, `created_at/by`, `updated_at/by`.
`OpportunityComment`: `id`, `data`, `created_at`, `created_by`.

### Outros

`Admin` (`id`, `email`, `first_name`, `last_name`, `full_name`, `profile_pic`, `available`),
`Team`, `Tag` (`id`, `name`), `Product`, `Calendar`, `Agent`, `Broadcast` (`id`, `name`, `status`:
`DRAFT|NOT_SENT|SENTING|SENT|CANCELLED`, `sent_at`, `created_at`, `created_by`).

`GET /accounts/me` devolve `{page_id, name, active, created, total_users}`: **não há `id`**, o ID da conta é
`page_id`. Os modelos `Appointment` e `Account` (com `fb_page_id`, `waba_id`, `plan`…) do contrato antigo não
constam mais no contrato oficial.

---

## 2. Inventário de endpoints

Contrato oficial (2026-10-26): 86 operações — Conta (4), Contatos (3), Mensagens (4), Etiquetas (8), Campos
personalizados (8), Campos do bot (3), Fluxos e modelos (3), Pipelines (13), Agentes de IA (7), E-commerce (10),
Disparos (4), Agenda (2), Ferramentas (17). As tabelas abaixo listam o que as skills usam, no agrupamento antigo.

### Accounts

| Método | Rota | O que faz |
|---|---|---|
| GET | `/accounts/me` | detalhes da conta — **use para conferir que o token é da conta certa** |
| GET | `/accounts/admins` | lista de admins |
| GET | `/accounts/teams` | lista de times |
| GET | `/accounts/tags` | todas as tags |
| POST | `/accounts/tags` | cria tag (`name`, formData) |
| GET | `/accounts/tags/{tag_id}` | tag por id |
| DELETE | `/accounts/tags/{tag_id}` | apaga tag |
| GET | `/accounts/tags/name/{tag_name}` | **tag por nome** (idempotência) |
| GET | `/accounts/flows` | **todos os flows — valida `flow_id` real** |
| GET | `/accounts/custom_fields` | todos os CUFs |
| POST | `/accounts/custom_fields` | cria CUF (body `{name, type}`) |
| GET | `/accounts/custom_fields/{custom_field_id}` | CUF por id |
| GET | `/accounts/custom_fields/name/{custom_field_name}` | **CUF por nome** (idempotência) |
| GET/POST/DELETE | `/accounts/bot_fields/{bot_field_id}` | ler / setar / limpar bot field |
| GET | `/accounts/integrations` | integrações da conta |
| POST | `/accounts/templates/{template_id}/generateSingleUseLink` | link de template de uso único |

⚠️ **Não existe DELETE de custom field.** Nome errado fica para sempre — dry-run antes.

### Contacts

| Método | Rota | O que faz |
|---|---|---|
| POST | `/contacts` | **cria contato (e, na prática de produção, atualiza o existente pelo telefone — ver §0) e roda `actions[]` — o endpoint do transacional** |
| GET | `/contacts/{contact_id}` | contato por id |
| GET | `/contacts/find_by_custom_field` | acha contatos por valor de CUF (`field_id`, `value`; máx. 100, ordenado pela última atualização do campo). `field_id` aceita também `phone` e `email`; o telefone vai completo e só com dígitos |
| GET | `/contacts/{contact_id}/tags` | tags do contato |
| POST/DELETE | `/contacts/{contact_id}/tags/{tag_id}` | adiciona / remove tag |
| GET | `/contacts/{contact_id}/custom_fields` | CUFs do contato |
| GET | `/contacts/{contact_id}/custom_fields/{custom_field_id}` | valor de um CUF |
| POST/DELETE | `/contacts/{contact_id}/custom_fields/{custom_field_id}` | seta / remove valor |
| POST | `/contacts/{contact_id}/send/{flow_id}` | dispara flow avulso. Contrato: **sem corpo**, entrega a versão **publicada** do flow, resposta não descrita. Corpus (Alto Giro): **411** com corpo vazio quando o cliente HTTP não manda `Content-Length` — mande um corpo mínimo |
| POST | `/contacts/{contact_id}/send/text` | envia texto |
| POST | `/contacts/{contact_id}/send/file` | envia arquivo |
| POST | `/contacts/{contact_id}/send_content` | múltiplas ações e mensagens, todos os canais |
| POST | `/contacts/{contact_id}/ai/save_messages` | grava mensagem no histórico (IA) |

### AI Agents

| Método | Rota | O que faz |
|---|---|---|
| GET | `/agents/` | lista de agentes de IA |
| GET/POST | `/agents/{agent_id}` | lê / atualiza agente |
| GET | `/agents/functions` | **funções visíveis para o agente** |
| GET | `/agents/mcp` | **MCPs visíveis para o agente** |
| GET | `/agents/files` | arquivos do agente |

### Pipelines

| Método | Rota | O que faz |
|---|---|---|
| GET | `/pipelines` | lista (`offset`, `limit`) |
| GET | `/pipelines/{pipeline_id}` | um pipeline |
| GET | `/pipelines/{pipeline_id}/stages` | etapas |
| GET | `/pipelines/{pipeline_id}/custom_fields` | CUFs do pipeline |
| GET/POST | `/pipelines/{pipeline_id}/opportunities` | lista (`contact_id`, `offset`, `limit`) / cria card |
| GET/POST/DELETE | `/pipelines/{pipeline_id}/opportunities/{opportunity_id}` | lê / atualiza / apaga card |
| POST | `.../opportunities/{opportunity_id}/transfer-to-pipeline` | move card de pipeline |
| GET/POST | `.../opportunities/{opportunity_id}/comments` | lista / cria comentário |
| DELETE | `.../opportunities/{opportunity_id}/comments/{comment_id}` | apaga comentário |

### Ecommerce (carrinho nativo NexTags)

`POST /contacts/{id}/send/products` · `GET|DELETE /contacts/{id}/cart` ·
`POST|DELETE /contacts/{id}/cart/{product_id}` · `POST /contacts/{id}/pay/{order_id}` ·
`GET|POST /contacts/{id}/order/{order_id}` · `GET|POST /products/{product_id}`

### Appointment Management / Templates

`GET /calendars` · `GET /calendars/{calendar_id}` · `POST /accounts/templates/{template_id}/install`

### Disparos (Broadcasts) — só consulta, reenvio e cancelamento

`GET /broadcasts` · `GET /broadcasts/{broadcast_id}` · `POST /broadcasts/{broadcast_id}/resend` ·
`POST /broadcasts/{broadcast_id}/cancel`. **Não há rota para criar Broadcast** (é na tela). `resend` manda de
novo para todos: nunca repetir sem consultar o estado. O contrato diz `{data: [...]}` na lista, mas ao vivo
(2026-10-26) `GET /broadcasts` devolveu array direto. Fora do escopo desta skill (broadcast em massa); listado
aqui para ninguém concluir "não existe".

### Ferramentas (`/tools/*`) — 17 utilitários para a Requisição externa do fluxo

`POST /tools/` + `format_number` · `split` · `urlencode` · `urldecode` · `rawurlencode` · `rawurldecode` ·
`qrcode` · `text_to_lower` · `text_to_upper` · `text_length` · `substring` · `text_replace` · `text_replaces` ·
`get_url_parameters` · `echo` · `hash` · `location_distance`. Corpo **form-urlencoded** (menos `echo`, que recebe
JSON); resposta em `data` na maioria. `echo` devolve o JSON recebido: dá para montar `{messages, actions}`
dinâmicos num flow **sem servidor próprio** (doc `webhooks/seguranca-e-testes`). `hash` (SHA-256 por padrão)
serve para mandar o e-mail com hash a APIs de conversão.

---

## 3. Receitas que as skills usam

### 3.1 Criar CUFs de forma idempotente (setup de conta nova)

Padrão Degan (`Qwv3YTg9SbVPIqAn`). Template de Code node em `assets/setup_cufs_canonicos.js`.

```
1. GET /accounts/me                  → confere que o token é da conta certa (`name` e `page_id` no laudo; não há `id`)
2. GET /accounts/custom_fields       → lista o que JÁ existe
3. diff (DESEJADOS − EXISTENTES)     → só o que falta
4. DRY-RUN: imprime o diff e para    → humano confere a lista
5. POST /accounts/custom_fields {"name":"numero_pedido","type":0}   → um por campo faltante
6. Laudo: criados / já existiam / EXISTE MAS COM TIPO ERRADO
```

⚠️ **A API não tem DELETE de custom field.** Nome errado (typo, plural, CamelCase) fica na conta
para sempre. Por isso o dry-run é obrigatório, não opcional.
⚠️ **Alerta de tipo:** campo que já existe com `type != 0` e vai receber `set_field_value` de texto
entra no laudo como falha — `set_field_value` em tipo Número **descarta em silêncio** (Mayuí/Degan).
⚠️ **Token é por conta.** Token errado = `200` + campos criados na conta errada (Wazzu/Hebreus Doze).
⚠️ **Só tipos `0` a `4` saem por API** (§1.1): campo de tipo 5, 6 ou 7 entra no laudo como "criar no painel", não
no POST. O body aceita também `description`; com `isBotField: true` + `value` cria um **bot field** (não existe
listagem de bot fields: guarde o `id` devolvido). `POST /accounts/custom_fields` é JSON.

A lista canônica de CUFs a criar está em `references/campos_canonicos.md` §5 (transacionais) e §7.1
(conta completa). Não redigite a tabela: leia de lá.

### 3.2 Criar / consultar tag

```
GET  /accounts/tags/name/{tag_name}   → existe? usa o id
POST /accounts/tags  name=transacional   (form-urlencoded, NÃO JSON; no n8n: Body Content Type = Form Urlencoded) → cria e devolve {"id": ...}
```

Tags canônicas do transacional: `transacional` + `Pedido Aprovado` / `Pedido Enviado` /
`Pedido Entregue` (e `Pedido Aprovado 30 dias` quando há régua de cross-sell).
Nomes com maiúscula e espaço são **o nome real na conta** — não normalizar
(`campos_canonicos.md` §4).

### 3.3 Validar `flow_id` real antes de disparar

```
GET /accounts/flows   → confere que cada flow_id do workflow existe de verdade
```

Obrigatório porque `/send/{flow_id}` retorna `success:true` **até para id inexistente**
(evidência: Alto Giro). O sticky note do workflow anota de onde veio cada `flow_id`.
No JSON, `flow_id` vai **sempre como string** (`"1788450035680"`) — id da NexTags passa de
2^53 e number perde precisão em JS, silenciosamente.

Enquanto o id real não existir: sentinela `flow_id = 0` **como número** no código, com guard
`if (!flow) return skip(base, 'flow_id_ausente')`, e `String(flow)` só na hora de montar o
payload. ⚠️ Não troque a sentinela pela string `"0"`: `"0"` é **truthy** em JS, o guard
deixa passar e o disparo vira no-op silencioso.
— nunca um id fictício "funcional" (`padrao_transacional.md` §5.3, `antipadroes.md` §19).

O flow chega ao contato na versão **publicada** (rascunho não vale: publique antes de testar). No WhatsApp,
fora da janela de 24 h só entra mensagem de **Modelo aprovado**: o flow de destino precisa **começar com o
Modelo** (ou com uma Condição `Interagiu nas últimas 24h` que separe texto livre × Modelo). Transacional é quase
sempre fora da janela (doc `guias/enviar-fluxo`; help `canais/janela-de-24-horas`; `antipadroes.md` §23).

### 3.4 Disparo atômico — `POST /contacts` com `actions[]`

Um único POST faz tudo (Alto Giro trocou 3 chamadas separadas por 1). Campos **nativos no root**,
CUFs em `actions[]`:

```json
{
  "phone": "55DDNNNNNNNNN",
  "first_name": "Maria",
  "last_name": "Silva",
  "email": "maria@exemplo.com",
  "actions": [
    {"action": "set_field_value", "field_name": "numero_pedido",  "value": "11488"},
    {"action": "set_field_value", "field_name": "status_pedido",  "value": "enviado"},
    {"action": "set_field_value", "field_name": "origem_pedido",  "value": "nuvemshop"},
    {"action": "set_field_value", "field_name": "rastreio_codigo","value": "AA123456789BR"},
    {"action": "add_tag", "tag_name": "transacional"},
    {"action": "add_tag", "tag_name": "Pedido Enviado"},
    {"action": "send_flow", "flow_id": "1788450035680"}
  ]
}
```

| Regra | Detalhe |
|---|---|
| Ordem | `set_field_value` → `add_tag` → `send_flow`. Sem exceção no corpus. Fora de ordem, os CUFs chegam vazios no destino. |
| Nativos | `first_name`, `last_name`, `email`, `phone` no **root**, nunca como CUF. |
| `flow_id` | Aparece como number e como string em clientes diferentes; a API aceita ambos. **Fixe um tipo por projeto** (recomendado: string, para não perder precisão em id longo). |
| Nada de `null` | A NexTags rejeita `null`/`undefined` no payload — passar tudo por `verificarDado()`. |
| Vazio quebra template | Variável de template do WhatsApp vazia derruba o template inteiro (erro Meta `#131008`). |
| HTTP no n8n | `specifyBody:'json'` + `jsonBody`; `jsonParameters`/`bodyParametersJson` **não serializa** e gera falso `"Invalid phone number"` (Alto Giro). |
| Resiliência | `retryOnFail: true`, `waitBetweenTries: 5000`, `onError: continueErrorOutput` — e o dedup só grava no ramo de sucesso (`padrao_transacional.md` §3.5). ⚠️ Doc oficial: retry automático só em consulta ou em chamada que não duplica. `POST /contacts` com `send_flow` **não é idempotente**: se a NexTags processar e a resposta se perder (timeout), o retry reenvia o flow ao cliente, e o dedup (gravado só após sucesso) não cobre esse caso. Limite conhecido do padrão: ver `padrao_transacional.md` §7. |
| Janela de 24 h | Fora da janela, o flow de destino tem que começar com Modelo de Mensagem aprovado; `send_flow` segue a mesma regra. Mensagem livre fora da janela não chega (a API aceita o envio e o erro fica em Fluxos › Registro de Erros). | doc: `comecar/mensagens-e-acoes`, `guias/enviar-fluxo` |
| Canais (`send_content`) | `messenger`, `whatsapp`, `telegram`, `instagram` (o contrato antigo listava também `sms`, `googleBM`, `viber`, `omnichannel`; não constam mais). | doc: contrato `POST /contacts/{id}/send_content` |

### 3.5 Conferir que o MCP está visível para o agente

```
GET /agents/mcp         → o MCP Server Trigger do n8n aparece aqui?
GET /agents/functions   → as funções/tools estão listadas?
```

Se o MCP não aparece, o agente não enxerga a tool — o problema está na exposição (path do MCP
Server Trigger v2, `availableInMCP`), não no prompt. Detalhe na `nextags-mcp-builder`.

### 3.6 Auditar o fluxo de pipeline (handoff)

Para conferir se o handoff da IA está de fato criando card:

```
GET  /pipelines                                      → id do pipeline (Parcerias / Comercial / SAC)
GET  /pipelines/{id}/stages                          → etapas
GET  /pipelines/{id}/opportunities?contact_id={cid}  → o contato tem card aberto?
GET  /pipelines/{id}/opportunities/{oid}/comments    → o resumo_pipeline virou comentário?
POST /pipelines/{id}/opportunities/{oid}/transfer-to-pipeline  → mover card de painel
```

Isso audita o efeito do trio `motivo_transferencia` + `prioridade_pipeline` + `resumo_pipeline`
(`campos_canonicos.md` §2). O transacional não escreve em pipeline — esta receita é de auditoria.

### 3.7 Achar o contato por campo transacional

```
GET /contacts/find_by_custom_field?field_id=<id_do_numero_pedido>&value=11488
```

Útil para "quem é o dono deste pedido?" em investigação de disparo. Máx. 100 resultados,
ordenados pela última atualização do campo.

Para achar pelo telefone: `?field_id=phone&value=5511988776655` (também `field_id=email`). A doc avisa que contato
salvo noutro formato (sem `55`, com `+` ou sem o 9) pode não ser achado: use o formato completo que o
`formatarTelefone` de `assets/_helpers.js` devolve (doc `guias/buscar-contato-por-campo`,
`guias/criar-ou-atualizar-contato`).

---

## 4. Perguntas em aberto

> Fechado pelo dono em 2026-09-03: o enum de `status_pedido` é
> `aprovado|enviado|entregue|cancelado|pronto_retirada|pix_gerado|pix_expirado`
> (`campos_canonicos.md` §5 e §9). Não é mais pergunta.

1. ~~`flow_id` como number ou string~~ — **fechado pelo dono em 2026-09-03: string** (`padrao_transacional.md`,
   "Questões em aberto", nº 5). O contrato aceita `integer` ou `string` na ação `send_flow`.
2. Por que o AliveMed usa `/api/users` em vez de `/api/contacts` — sem explicação na sticky.
   Tratado como legado até o dono confirmar. [SEM EVIDÊNCIA DIRETA]

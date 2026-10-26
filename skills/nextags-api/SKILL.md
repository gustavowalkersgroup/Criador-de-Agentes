---
name: nextags-api
description: "Guia completo da API REST da NexTags (app.nextagsai.com.br/api, 69 endpoints, swagger oficial): agentes IA (listar, ler e SUBIR prompt, backup), contatos (buscar por telefone/email/CUF, tags, send_flow, send_content), custom fields (CUF), bot fields, tags, flows, pipelines/oportunidades (CRM), e-commerce nativo (carrinho/pedido/produto), broadcasts, templates, calendários. Use SEMPRE que a tarefa tocar a API da NexTags: 'subir/atualizar/baixar prompt do agente', 'criar CUF/tag em lote', 'achar contato', 'disparar flow/mensagem pela API', 'listar agentes/flows/MCPs', 'o que dá pra fazer pela API', 'conferir a doc da API', 'auditar conta NexTags'. ANTES de dizer que algo não dá pra fazer na NexTags, consulte esta skill."
metadata:
  type: reference
---

# API NexTags — o que dá pra fazer e como

**Regra 1:** antes de dizer "não dá pra fazer pela API" ou "só pelo painel", dar grep em `references/endpoints.md` (69 operações, com body, enums e exemplos). Em 26/10/2026 se confirmou que subir prompt (`POST /agents/{id}` com `{"prompt": "..."}`) sempre foi possível; a doc antiga mostrava só `data (body:object)`, sem campos, e ninguém viu.

## Conexão

- Base `https://app.nextagsai.com.br/api` · header `X-ACCESS-TOKEN: <token>` (valor puro, **não** Bearer).
- Token é **POR CONTA** (por cliente). Pedir ao usuário ou ler de `NEXTAGS_TOKEN`. Nunca gravar em arquivo, relatório ou memória.
- Token de outra conta **não dá erro**: responde 200 e escreve na conta errada. Antes de qualquer escrita rode `whoami` e confira o `name` com o cliente.
- Spec real: `https://app.nextagsai.com.br/php/images.php?id=swagger.json` (é o que a página `/api/swagger/` carrega). ⚠️ `/api/swagger/swagger.json` é a versão Chatrace, desatualizada (sem `/accounts/me`, sem `rcs`, host `api.chatrace.com`). Não usar.

## Script helper (só stdlib)

`S=~/.claude/skills/nextags-api/scripts/nextags_api.py` — rodar com `python -I $S ...`

| Comando | Faz |
|---|---|
| `whoami` | `GET /accounts/me` (nome, page_id, total_users) |
| `call GET accounts/tags` | qualquer endpoint. Ex.: `call POST contacts/123/custom_fields/9 --form value=abc --yes` |
| `snapshot --dir D` | GET de leitura em todos os recursos da conta, salva JSON em D |
| `backup-agents --dir D` | config + prompt `.md` de cada agente |
| `spec-check [--update]` | compara o swagger vivo com `references/swagger.json`; `--update` regenera a referência |

- **Escrita sem `--yes` = dry-run** (mostra método, URL e body, não envia). Só passar `--yes` depois da autorização do usuário.
- Body: `--json '{...}'` ou `--json-file f.json` (JSON) · `--form k=v` (endpoints FORM, marcados na referência). Query: `-q k=v`.
- Respostas grandes (ex.: `GET /agents/{id}` com prompt): `--out arquivo`.
- Path sem `/` inicial (`accounts/me`) evita a conversão de caminho do Git Bash.

## Quero fazer X → chamada

| Quero | Chamada |
|---|---|
| Confirmar a conta | `GET /accounts/me` |
| Listar agentes IA / ler prompt e config | `GET /agents` · `GET /agents/{id}` |
| **Subir só o prompt** | `POST /agents/{id}` `{"prompt":...}` → usar a skill `nextags-prompt-push` (backup + conferência) |
| Backup de todos os prompts | `backup-agents` |
| Functions / MCPs / arquivos do IA Hub | `GET /agents/functions` · `/agents/mcp` · `/agents/files` |
| LLMs e integrações ativas | `GET /accounts/integrations` |
| Flows (ids pro `send_flow`) | `GET /accounts/flows` |
| CUF: listar / criar / ler | `/accounts/custom_fields` · `/{id}` · `/name/{nome}` |
| Bot field (variável global) | `/accounts/bot_fields/{id}` GET · POST (form `value`) · DELETE |
| Tags | `/accounts/tags` GET/POST(form `name`) · `/{id}` GET/DELETE · `/name/{nome}` |
| Admins / times | `/accounts/admins` · `/accounts/teams` |
| Achar contato | `GET /contacts/find_by_custom_field?field_id=phone\|email\|<id>&value=` (máx 100) |
| Criar contato (+ ações) | `POST /contacts` (`phone` com DDI; `actions` = add_tag, set_field_value, send_flow...) |
| Ler contato / CUFs / tags | `GET /contacts/{id}` · `/custom_fields` · `/tags` |
| Setar / limpar CUF do contato | `POST` (form `value`) · `DELETE /contacts/{id}/custom_fields/{cuf_id}` |
| Tag no contato | `POST` · `DELETE /contacts/{id}/tags/{tag_id}` |
| Disparar flow | `POST /contacts/{id}/send/{flow_id}` |
| Mandar mensagem | `/send/text` · `/send/file` · `/send_content` (`messages` + `actions` = mesmo JSON que o agente devolve; ver `nextags-json-fixer`) |
| Gravar mensagem no histórico da IA | `POST /contacts/{id}/ai/save_messages` (role user/assistant/developer) |
| CRM | `/pipelines` · `/{id}/stages` · `/{id}/opportunities` CRUD · `/comments` · `/transfer-to-pipeline` |
| E-commerce nativo | `/contacts/{id}/cart` · `/order/{order_id}` · `/pay/{order_id}` · `/products/{id}` |
| Calendários | `GET /calendars` (só leitura) |
| Broadcasts | `GET /broadcasts` · `/{id}` · `POST /{id}/resend` · `/{id}/cancel` |
| Templates do marketplace | `POST /accounts/templates/{id}/install` · `/generateSingleUseLink` |

Combos úteis: auditar conta (`snapshot`) · clonar CUFs de um cliente pra outro (GET numa conta, POST na outra, com `whoami` nas duas) · sincronizar prompts do repo para o IA Hub (`nextags-prompt-push`) · achar contato por telefone e inspecionar CUFs/tags para depurar um atendimento.

## Não existe na API (não consta nos 69 endpoints)

Criar/deletar agente · criar/editar/deletar flow · **deletar CUF** · editar tag · ler histórico de mensagens/conversas · listar todos os contatos (só `find_by_custom_field`, máx 100) · criar broadcast · criar template WhatsApp · agendamentos (existe o modelo `Appointment`, sem rota) · webhooks e execuções. Path inventado dá 404 limpo e engana (`/api/custom_fields` não existe; o certo é `/accounts/custom_fields`). Não adivinhar path.

## Armadilhas (verificadas no spec e em incidentes reais)

1. **Agente: só `prompt`.** O spec também aceita `max_output_tokens` e `model`, mas o incidente de 23/10/2026 com `model` + `max_output_tokens` travou o painel, a API ignora `null` e o Roteador e o Revalidador tiveram que ser recriados. No spec, `model` é um **objeto** com as 5 chaves (`openAI`, `gemini`, `claude`, `xAI`, `deepseek`) marcadas obrigatórias, e o exemplo oficial é só `{"prompt": ...}`. Causa do travamento [Especulação]: `model` enviado como string ou objeto incompleto. Modelo/tokens/raciocínio: o usuário configura no painel; Claude só recomenda.
2. **Agente sem config salva** (GET devolve só `id`/`name`, sem `data.model`/`data.aiPriority`): não dar POST. Pedir ao usuário para abrir e salvar o agente no IA Hub uma vez.
3. **O swagger subdocumenta respostas.** `Agent` lista 4 campos; o `GET /agents/{id}` real traz a config **dentro de `data`**: `resp["data"]["prompt"]`, `data.model` (6 chaves, inclui `metaAI` que o spec não lista), `data.aiPriority`, `data.reasoning`. Shapes verificados ao vivo: `references/live_shapes.md`.
4. **Números voltam como string** (`id`, `page_id`, `created`, `total_users`, `value`); `stage.id` vem int. Comparar com `str()`. **Envelope inconsistente:** `{data:[...]}` em agents, functions, mcp, files, pipelines, stages, opportunities, calendars; array direto em admins, teams, tags, flows, custom_fields e **broadcasts** (o spec diz `{data}`, mas voltou array). Tratar os dois.
5. **CUF:** criar sempre `type` 0 (Text). Number (1) gravado pela IA via `set_field_value` é descartado sem erro. O create documenta só `type` 0-4 (os tipos 5-7 existem na leitura; criação via API não testada). **Não há DELETE de CUF:** criou errado, fica. Fazer `GET` + dry-run antes de criar em lote. Typo em nome de CUF falha em silêncio dos dois lados.
6. **Content-Type muda por endpoint.** FORM: criar tag, `bot_fields` POST, CUF do contato POST, `send/{flow_id}`, `pay`, `cart/{product_id}` POST. O resto é JSON.
7. **Unidades:** `amount_received` em `pay` é em **centavos**; `price` em `ProductCart` **não** é. Status de pedido: escrita numérica (6 Processing, 7 Shipped, 10 Completed, 13 Canceled; 402 se igual ao atual), leitura em texto (`Not processed`, `Accepted`, `Delivering`, `Completed`, `Canceled`). `gender`: escrita `male|female|unknown`, leitura 0/1/2.
8. **Canais:** `send/text` não aceita `googleBM`; `send/file` e `send_content` aceitam. `send_content` aceita também `rcs`.
9. **Bugs da doc:** `GET /pipelines/{id}/custom_fields` não declara o path param; `GET /calendars/{id}` tem operationId `getProductById`; `POST /contacts/{id}/custom_fields/{cuf_id}` declara `cuf_id` como string (aceitar nome é hipótese não testada).
10. **Paginação:** só `offset`/`limit` em pipelines, oportunidades e comentários. Broadcasts devolve no máximo 100.

## Nível de cuidado por ação

- **Leitura (GET):** livre.
- **Config reversível** (prompt com backup, tag, CUF, bot field): o pedido do usuário já autoriza; mostrar o dry-run quando o alvo não for óbvio.
- **Externa ou irreversível:** confirmar em chat, com alvo exato e quantidade, antes do `--yes`: mensagem/flow/arquivo para contato real (a Meta cobra por mensagem desde 01/10/2026; testar só com contato de teste), `resend`/`cancel` de broadcast, `pay`/status de pedido (notifica o cliente), preço/estoque/`active` de produto, todo `DELETE`, criação de CUF em conta de cliente.
- Em lote: dry-run do primeiro item, conferir, depois o resto. Registrar o que foi criado.

## Manutenção

`python -I $S spec-check` mostra drift do swagger. Com `--update` regenera `references/`; depois revisar a tabela e a seção "não existe" deste arquivo. Spec baixado em 26/10/2026 (69 ops). Verificado ao vivo em 26/10/2026: `whoami`, `snapshot` (14 GETs) e `GET` de agente, stages e oportunidades, todos 200. **Nunca testado ao vivo:** qualquer POST/DELETE, `find_by_custom_field`, `send_*`, e o `backup-agents` (corrigido para ler `data.prompt`, mas não reexecutado).

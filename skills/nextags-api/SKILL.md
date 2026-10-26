---
name: nextags-api
description: "Guia completo da API REST da NexTags (app.nextagsai.com.br/api, 86 endpoints, contrato oficial do docs.nextags.com.br) e da documentação oficial (docs + help): agentes IA (listar, ler e SUBIR prompt, backup), contatos (buscar por telefone/email/CUF, tags, send_flow, send_content, mensagens e ações em JSON), custom fields (CUF), bot fields, tags, flows, pipelines/oportunidades (CRM), e-commerce nativo (carrinho/pedido/produto), broadcasts, templates, calendários, /tools, limites, erros e retry. Use SEMPRE que a tarefa tocar a API da NexTags: 'subir/atualizar/baixar prompt do agente', 'criar CUF/tag em lote', 'achar contato', 'disparar flow/mensagem pela API', 'listar agentes/flows/MCPs', 'o que dá pra fazer pela API', 'conferir a doc da API', 'auditar conta NexTags', 'como a NexTags faz X'. ANTES de dizer que algo não dá pra fazer na NexTags, consulte esta skill."
metadata:
  type: reference
---

# API NexTags — o que dá pra fazer e como

**Regra 1:** antes de dizer "não dá pra fazer pela API" ou "só pelo painel", dar grep em `references/endpoints.md` (86 operações, com body, enums e exemplos) e na seção "Não existe" abaixo. Em 26/10/2026 se confirmou que subir prompt (`POST /agents/{id}` com `{"prompt": "..."}`) sempre foi possível; a doc antiga mostrava só `data (body:object)`, sem campos, e ninguém viu.

## Onde consultar (nesta ordem)

1. `references/endpoints.md` — contrato oficial gerado do OpenAPI (body, enums, exemplo, erros). `references/openapi.json` tem os exemplos de código (`x-codeSamples`).
2. `references/live_shapes.md` — o que a API **realmente devolve** (o contrato diverge em pontos importantes).
3. Doc oficial, sempre atual: cada página tem versão `.md` (troque a `/` final por `.md`).
   - `python -I $S doc comecar/limites-e-erros` ou `doc https://help.nextags.com.br/tutoriais/ia/ia-hub/`.
   - Se o MCP da doc estiver ligado (`mcp__*__search`, `fetch`, `detalhar_endpoint`, `listar_endpoints`), usar — é a mesma base.
   - Achar a página: `grep -i <tema> references/llms_docs.txt` (134 páginas de API/webhooks/guias) e `references/llms_help.txt` (422 de tutoriais de tela: IA, fluxos, canais, pipelines...).
   - Arquivos para IA: `docs.nextags.com.br/llms-full.txt`, `help.nextags.com.br/llms-full.txt`, `/nextags.postman_collection.json`.
4. Existe uma skill oficial da NexTags para montar agente por entrevista (`criar-agente-ia`, plugin `guiipego/nextags`); não confundir com as skills deste repo.

## Conexão

- Base `https://app.nextagsai.com.br/api` · header `X-ACCESS-TOKEN: <token>` (valor puro, **não** Bearer). Sem chave: `401 {"error":{"code":401,"message":"No valid API key provided."}}` (corpo JSON, mas `Content-Type: text/html`).
- Token é **POR CONTA** (por cliente). Pedir ao usuário ou ler de `NEXTAGS_TOKEN`. Nunca gravar em arquivo, relatório ou memória.
- Token de outra conta **não dá erro**: responde 200 e escreve na conta errada. Antes de qualquer escrita rode `whoami` e confira o `name` com o cliente.
- Chamar do servidor/CLI, nunca de navegador. A API só usa GET, POST e DELETE (sem PUT/PATCH; "atualizar" é POST).
- ⚠️ O swagger legado `app.nextagsai.com.br/api/swagger/` (69 ops, host `api.chatrace.com`) está **desatualizado** (sem `/tools`, canais antigos). A fonte é `https://docs.nextags.com.br/openapi.json`.

## Script helper (só stdlib)

`S=~/.claude/skills/nextags-api/scripts/nextags_api.py` — rodar com `python -I $S ...`

| Comando | Faz |
|---|---|
| `whoami` | `GET /accounts/me` (nome, page_id, total_users) |
| `call GET accounts/tags` | qualquer endpoint. Ex.: `call POST contacts/123/custom_fields/9 --form value=abc --yes` |
| `snapshot --dir D` | GET de leitura em todos os recursos da conta, salva JSON em D |
| `backup-agents --dir D` | config + prompt `.md` de cada agente |
| `doc <caminho\|url>` | Markdown de uma página do docs/help |
| `spec-check [--update]` | compara o OpenAPI e os `llms.txt` vivos com `references/`; `--update` regenera tudo |

- **Escrita sem `--yes` = dry-run** (mostra método, URL e body, não envia). Só passar `--yes` depois da autorização do usuário.
- Body: `--json '{...}'` ou `--json-file f.json` (JSON) · `--form k=v` (endpoints FORM, marcados na referência). Query: `-q k=v`. Respostas grandes: `--out arquivo`.
- Path sem `/` inicial (`accounts/me`) evita a conversão de caminho do Git Bash.

## Quero fazer X → chamada

| Quero | Chamada |
|---|---|
| Confirmar a conta | `GET /accounts/me` |
| Listar agentes IA / ler prompt e config | `GET /agents` · `GET /agents/{id}` (config em `data`) |
| **Subir só o prompt** | `POST /agents/{id}` `{"prompt":...}` → skill `nextags-prompt-push` (backup + conferência) |
| Backup de todos os prompts | `backup-agents` |
| Functions / MCPs / arquivos do IA Hub | `GET /agents/functions` · `/agents/mcp` · `/agents/files` (só lista; criar e ligar é no AI Hub) |
| Gravar contexto na memória da IA do contato | `POST /contacts/{id}/ai/save_messages` (role `user`/`assistant`/`developer`; não envia nada ao contato) |
| LLMs e integrações ativas | `GET /accounts/integrations` |
| Flows (ids pro `send_flow`) | `GET /accounts/flows` |
| CUF: listar / criar / ler | `/accounts/custom_fields` · `/{id}` · `/name/{nome}` |
| Bot field: criar | `POST /accounts/custom_fields` com `isBotField:true` e `value`. **Não há listagem de bot fields**: guardar o id que a criação devolve (ou "Obter ID" na tela) |
| Bot field: ler / gravar / limpar | `/accounts/bot_fields/{id}` GET · POST (form `value`) · DELETE |
| Tags | `/accounts/tags` GET/POST(form `name`) · `/{id}` GET/DELETE · `/name/{nome}` (nome codificado na URL) |
| Admins / times | `/accounts/admins` · `/accounts/teams` |
| Achar contato | `GET /contacts/find_by_custom_field?field_id=phone\|email\|<id>&value=` (telefone completo, só dígitos, ex. `5511988776655`; máx 100) |
| Criar contato (+ ações) | `POST /contacts` (`phone` obrigatório; `actions` = as 8 ações) |
| **Mudar nome/telefone/email do contato** | Não há "atualizar contato". `POST /contacts/{id}/send_content` com `{"messages":[],"actions":[{"action":"set_field_value","field_name":"phone"\|"email"\|"first_name"\|"last_name"\|"full_name","value":"..."}]}` |
| Ler contato / CUFs / tags | `GET /contacts/{id}` · `/custom_fields` · `/tags` |
| Setar / limpar CUF do contato | `POST /contacts/{id}/custom_fields/{cuf_id}` (form `value`) · `DELETE` — ou a ação `set_field_value` pelo **nome** |
| Tag no contato | `POST` · `DELETE /contacts/{id}/tags/{tag_id}` |
| Disparar flow | `POST /contacts/{id}/send/{flow_id}` (sem body; versão publicada) |
| Mandar mensagem | `/send/text` · `/send/file` · `/send_content` (`messages`+`actions`, formato abaixo) |
| CRM | `/pipelines` · `/{id}/stages` · `/{id}/custom_fields` · `/{id}/opportunities` CRUD · `/comments` · `/transfer-to-pipeline` |
| E-commerce nativo | `/contacts/{id}/cart` · `/order/{order_id}` · `/pay/{order_id}` · `/products/{id}` |
| Calendários | `GET /calendars` (só leitura) |
| Broadcasts | `GET /broadcasts` · `/{id}` · `POST /{id}/resend` · `/{id}/cancel` |
| Templates do marketplace | `POST /accounts/templates/{id}/install` (`template_key`) · `/generateSingleUseLink` |
| Utilitários de texto/URL/QR/hash/distância | `POST /tools/*` (17, corpo FORM exceto `echo`): feitos para a **Requisição externa do fluxo**. `/tools/echo` devolve o JSON enviado: dá para montar `{messages, actions}` dinâmicos no fluxo **sem servidor próprio** |

Combos úteis: auditar conta (`snapshot`) · clonar CUFs de um cliente pra outro (GET numa conta, POST na outra, `whoami` nas duas) · sincronizar prompts do repo para o IA Hub (`nextags-prompt-push`) · achar contato por telefone e inspecionar CUFs/tags para depurar um atendimento.

## Mensagens e ações em JSON (`send_content`, `POST /contacts`, agente de IA, requisição externa)

Corpo `{"messages":[...],"actions":[...]}`, as duas listas podem ir vazias. Detalhe completo: `doc comecar/mensagens-e-acoes`.
- Mensagem = `{"message":{...}}`: `text`; `attachment` `template`/`button` (até 3 botões, título ≤20 car.), `generic` (cartão: título e subtítulo ≤80, até 3 botões; galeria até 10 cartões), mídia `image|video|audio|file` com `payload.url` público; `quick_replies` (até 11). Um número solto entre mensagens = pausa "digitando" (segundos).
- Botão `postback`: `payload` = ID do fluxo/etapa **ou** string JSON `{"actions":[...]}` com aspas escapadas (montar com `json.dumps`). Só-WhatsApp: objeto da Cloud API com `"to": null`.
- 8 ações: `add_tag`/`remove_tag` (`tag_name`), `set_field_value`/`unset_field_value` (`field_name`, `value`), `send_flow` (`flow_id`), `transfer_conversation_to` (`value`: `human`|`bot`), `assign_conversation` (`admin_id`), `unassign_conversation`. Ordem da lista importa (preencher campo antes do flow que o usa).
- **Janela de 24 h (WhatsApp):** mensagem livre só até 24 h após a última do contato; fora disso só Modelo aprovado, via flow que **começa** com o modelo (`send/{flow_id}` ou ação `send_flow`). Instagram/Messenger: 24 h para automáticas.

## Formatos

- **IDs** são inteiros no contrato, mas **voltam como string** na prática (`"id":"599066"`): comparar com `str()`. `order_id` é texto.
- **Datas** de objetos: texto UTC `AAAA-MM-DD HH:MM:SS`. `last_sent`/`last_seen`/... do contato: Unix **ms**. CUF Data/Data e hora: Unix **segundos** (ms vira data errada; para Data, meia-noite de Brasília).
- **Dinheiro:** `total`, `subtotal`, `coupon_discount`, `amount_received` em **centavos** (`17980` = R$ 179,80). `price` de item, `price`/`sale_price` de produto e `value` de oportunidade em **reais**.
- **CUF `type`:** 0 Text · 1 Number · 2 Date · 3 Date&Time · 4 Bool (`1`/`0`, não "sim"/"true") · 5 Long Text · 6 Select · 7 Multi. Pela API só se **cria** 0–4 (5–7 só na tela). O tipo não muda depois. Nos nossos projetos: criar sempre 0 (Text).

## Limites, erros, retry

- **~100 req/min por conta, somados** (nosso sistema + Zapier + Make + n8n...). Em lote: ~1 chamada/s. O código ao estourar não foi confirmado: tratar `429`/`5xx` com espera crescente (1, 2, 4, 8 s, ~5 tentativas), nunca em laço imediato.
- Códigos: `400` dado errado · `401` chave · `402` operação não feita (só `pay` e `order`) · `404` não existe. O corpo de 400/402/404 não está documentado: guardar inteiro no log.
- Sempre `timeout` no cliente. **Timeout em escrita não é "falhou"**: a NexTags pode ter feito. Conferir antes de repetir.
- Repetir sem duplicar: GET sempre pode. Criar contato/tag/CUF/oportunidade/comentário → buscar antes (a API não recusa duplicata). **Nunca repetir** envio de flow/texto/arquivo/conteúdo/produtos (o contato recebe de novo) nem `resend` de broadcast. Tag/CUF/etapa/status → consultar antes. Repetir o mesmo `status` de pedido dá 402.
- Paginação `offset`/`limit` (padrão 0/100) só em pipelines, oportunidades e comentários; ler até vir página com menos que `limit`. Agentes, calendários, broadcasts e `find_by_custom_field` trazem no máximo 100, sem paginação.

## Não existe na API (não consta nos 86 endpoints)

Criar/deletar agente · criar/editar/deletar flow, pipeline, etapa ou produto · **deletar CUF** (e criar CUF tipo 5–7) · editar tag · **ler conversas/histórico da Caixa de Entrada** · listar todos os contatos (só busca; exportar na tela) · atualizar contato (só via `set_field_value`) · apagar contato · listar pedidos ou produtos · criar broadcast · criar template de WhatsApp · criar agendamento · listar bot fields · inscrever em sequência. Para eventos da conta: webhooks de saída (tela). Path inventado dá 404 limpo e engana (`/api/custom_fields` não existe; o certo é `/accounts/custom_fields`).

## Armadilhas (verificadas no contrato, na doc e em produção)

1. **Agente: só `prompt`.** O contrato também aceita `max_output_tokens` (1–32768) e `model`, mas no incidente de 23/10/2026 um POST com `model` + `max_output_tokens` travou o painel; a API ignora `null`, então não dá pra desfazer, e Roteador e Revalidador foram recriados. A doc exige o objeto `model` com as 5 chaves (`openAI`, `gemini`, `claude`, `xAI`, `deepseek`), mas o GET real devolve **6** (`metaAI` a mais), então "mandar os cinco" pode não equivaler a "mandar tudo". Causa do travamento: [Especulação]. Só mexer em modelo/tokens se o usuário pedir explicitamente, em agente de teste, copiando o objeto `data.model` inteiro do GET.
2. **Agente sem config salva** (GET devolve só `id`/`name`, sem `data.model`/`data.aiPriority`): não dar POST. Pedir ao usuário para abrir e salvar o agente no IA Hub uma vez.
3. **O contrato subdocumenta respostas.** `GET /agents/{id}` real traz a config **dentro de `data`**: `resp["data"]["prompt"]`, `data.model`, `data.aiPriority`, `data.reasoning`, `data.tools`; a doc diz que só vêm `id`, `name`, `created_by`, `created_at`. Confirmar o shape com um GET real: `references/live_shapes.md`.
4. **Envelope inconsistente:** `{data:[...]}` em agents, functions, mcp, files, pipelines, stages, opportunities, calendars; array direto em admins, teams, tags, flows, custom_fields e **broadcasts** (a doc diz `{data}`, mas voltou array). `POST /pipelines/{id}/opportunities` responde `{data:[Opportunity]}`. Tratar os dois formatos.
5. **CUF:** número (1) gravado pela IA via `set_field_value` é descartado sem erro e variável vazia derruba template de WhatsApp (`#131008`). **Não há DELETE de CUF**: criou errado, fica. GET + dry-run antes de criar em lote. Typo em nome de CUF falha em silêncio dos dois lados. Nome sem acento e fixo (`set_field_value` acha pelo nome exato).
6. **Content-Type muda por endpoint.** FORM: criar tag, `bot_fields` POST, CUF do contato POST, `pay`, `cart/{product_id}` POST e todas as `/tools/*` (menos `echo`). Sem body: `send/{flow_id}`, `resend`, `cancel`, `generateSingleUseLink`. O resto é JSON.
7. **Canais** (`channel`): `send/text` aceita `messenger|whatsapp|webchat|telegram|instagram`; `send/file` e `send_content` não aceitam `webchat`. `sms`, `googleBM`, `viber`, `omnichannel` e `rcs` **não constam mais** (o swagger antigo ainda os listava).
8. **Pedido:** `status` escrita 6 Aceito · 7 Entregando · 10 Concluído · 13 Cancelado (4 "Não processado" não pode ser escolhido; 400 fora disso; 402 se igual ao atual). Leitura volta em texto. `pay` notifica o cliente. `gender`: escrita `male|female|unknown`, leitura 0/1/2.
9. **Webhook de entrada não usa chave** (o link é o segredo); webhook de saída exige `https://`. Quatro formas de integrar: webhook de entrada, webhook de saída, requisição externa do fluxo, API. Ver `doc webhooks/visao-geral`.

## Nível de cuidado por ação

- **Leitura (GET):** livre.
- **Config reversível** (prompt com backup, tag, CUF, bot field): o pedido do usuário já autoriza; mostrar o dry-run quando o alvo não for óbvio.
- **Externa ou irreversível:** confirmar em chat, com alvo exato e quantidade, antes do `--yes`: mensagem/flow/arquivo para contato real (a Meta cobra por mensagem desde 01/10/2026; testar só com contato de teste), `resend`/`cancel` de broadcast, `pay`/status de pedido, preço/estoque/`active` de produto, todo `DELETE`, criação de CUF em conta de cliente, `transfer_conversation_to`/`assign_conversation`.
- Em lote: dry-run do primeiro item, conferir, depois o resto. Respeitar ~1 req/s. Registrar o que foi criado.

## Manutenção

`python -I $S spec-check` mostra drift do OpenAPI e dos índices `llms.txt`; com `--update` regenera `references/`, e depois revisar a tabela, "Não existe" e as armadilhas deste arquivo. Estado em 26/10/2026: 86 ops, 134 páginas docs, 422 help. Verificado ao vivo: `whoami`, `snapshot` (14 GETs), GET de agente/stages/oportunidades e `backup-agents`, todos 200. **Nunca testado ao vivo:** qualquer POST/DELETE, `find_by_custom_field`, `send_*`, `/tools/*`.

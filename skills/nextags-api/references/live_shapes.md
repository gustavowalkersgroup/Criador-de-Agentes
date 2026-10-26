# Shapes REAIS da API (verificados ao vivo em 26/10/2026, só GET, conta de teste)

O contrato (OpenAPI) diverge da resposta real nos pontos abaixo. Em caso de dúvida, um GET real vale mais que `endpoints.md`. (Checado contra o contrato de docs.nextags.com.br em 26/10/2026).

## Regras gerais
- **Números voltam como string**: `id`, `page_id`, `created`, `total_users`, `size`, `value` (`"17.00"`). Exceção vista: `stage.id` é int. Comparar ids com `str()`.
- **Envelope inconsistente**:
  - `{"data": [...]}`: `/agents`, `/agents/functions`, `/agents/mcp`, `/agents/files`, `/pipelines`, `/pipelines/{id}/stages`, `/pipelines/{id}/opportunities`, `/calendars`, `/contacts/find_by_custom_field` (esta última pelo spec, não testada).
  - Array direto: `/accounts/admins`, `/teams`, `/tags`, `/flows`, `/custom_fields`, `/broadcasts` (o spec diz `{data}`, mas voltou array).
  - Objeto direto: `/accounts/me`, `/accounts/integrations`.
- Campo de sistema em CUF: `id` negativo e `type: "-1"` (ex.: Email `-12`). Tipos de CUF vistos na conta: `0` Text, `1` Number, `3` Date&Time, `5` Long Text, `6` Select, `-1` sistema.
- `GET /accounts/custom_fields` não devolveu `description` (o spec lista o campo; provavelmente só aparece quando preenchido).

## Formas
```
GET /accounts/me            {page_id, name, active, created (unix, string), total_users}
GET /accounts/admins        [{id, full_name, first_name, last_name, email, profile_pic, available,
                              messenger_id, whatsapp_id, viber_id, telegram_id, sms_id, google_bm_id, instagram_id}]
GET /accounts/teams         [{id, name}]
GET /accounts/tags          [{id, name}]
GET /accounts/flows         [{id, name}]            # ids longos (13 dígitos)
GET /accounts/custom_fields [{id, name, type}]
GET /accounts/integrations  {openai|gemini|claude|xai|deepseek|google_sheets|email: {active}}
GET /agents                 {data: [{id, name, created_at, created_by}]}      # sem prompt
GET /agents/functions       {data: [{id, name, created_at, created_by, active}]}
GET /agents/files           {data: [{id, external_id, name, size, url, created_at}]}
GET /pipelines              {data: [{id, name, created_at, created_by}]}
GET /pipelines/{id}/stages  {data: [{id (int), name}]}
GET /pipelines/{id}/opportunities
                            {data: [{id, contact_id, title, value, priority, status, assigned_admins,
                                     created_at, updated_at, created_by, updated_by, stage: {id, name}}]}
GET /broadcasts             [{id, name, status (ex.: SENT), sent_at, created_at, created_by}]
```

## Agente (GET /agents/{id}) — config fica DENTRO de `data`
```
{id, name, created_at, created_by,
 data: {prompt, model: {openAI, gemini, claude, xAI, deepseek, metaAI},
        max_output_tokens, reasoning: {effort}, aiPriority: [{id: "openAI"}], messages: [], tools: []}}
```
- O spec descreve `Agent` só com `id, name, created_by, created_at`. Prompt e config **não** estão no topo: usar `resp["data"]["prompt"]`.
- `model` real tem 6 chaves (`metaAI` não consta no spec, que lista 5). Valores observados: strings de modelo por provedor.
- Agente criado no painel e nunca salvo: sem `data.model`/`data.aiPriority` → não fazer POST.
- Não testado: o formato do corpo aceito pelo POST além de `{"prompt": ...}`.

# API NexTags — referencia completa (gerada do swagger oficial)
Fonte: https://app.nextagsai.com.br/php/images.php?id=swagger.json · host `app.nextagsai.com.br/api` · 69 operacoes · gerado em 2026-10-26
Auth: header `X-ACCESS-TOKEN` (valor puro). `FORM` = application/x-www-form-urlencoded (`--form k=v`); `JSON` = body JSON (`--json`).
O swagger documenta o contrato, nao tudo que a API devolve (ex.: GET /agents/{id} traz `data.prompt`/`data.model` que o schema nao lista; numeros voltam como string). Shapes reais: `live_shapes.md`.

## /accounts

### GET /accounts/me
`getAccountInformation` — Get business account details.
- resp 200: `{page_id: integer, name: string, active: boolean, created: integer, total_users: integer}` — successful operation

### GET /accounts/admins
`getAccountAdmins` — Get all admins from a business account.
- resp 200: `[Admin]` — successful operation

### GET /accounts/teams
`getAccountTeams` — Get all teams from a bot account.
- resp 200: `[Team]` — successful operation

### GET /accounts/tags
`getAccountTags` — Get all tags from a business account.
- resp 200: `[Tag]` — successful operation

### POST /accounts/tags
`createTag` — Create a new tag
- FORM `name`* (string)
- resp 200: `{id: integer}` — successful operation
  exemplo: `{"id": 1995}`

### GET /accounts/tags/{tag_id}
`getTagById` — Get tag by id
- path `tag_id`* (integer)
- resp 200: `Tag` — successful operation

### DELETE /accounts/tags/{tag_id}
`deleteTag` — Delete a tag
- path `tag_id`* (integer)
- resp 200: `{success: boolean}` — successful operation
  exemplo: `{"success": true}`

### GET /accounts/tags/name/{tag_name}
`getTagByName` — Get a tag by name
- path `tag_name`* (string)
- resp 200: `Tag` — successful operation

### GET /accounts/flows
`getAccountFlows` — Get all flows from a business account.
- resp 200: `[{id: integer, name: string}]` — successful operation

### GET /accounts/custom_fields
`getAccountCustomFields` — Get all custom fields from a business account.
- resp 200: `[{id: integer, name: string, type: integer, description: string}]` — successful operation

### POST /accounts/custom_fields
`createCustomField` — Create a custom field
- **body** `content`* (JSON):
  - `name` (string) [obrigatorio]
  - `type` (integer) [enum=[0, 1, 2, 3, 4], obrigatorio] — 0 - text | 1 - number | 2 - date | 3 - datetime | 4 - true/false
  - `isBotField` (boolean) [default=False]
  - `value` (string) — The value of the bot field. It is ignored for the contact custom field.
  - `description` (string)
  exemplo: `{"name": "lead_score", "type": 1}`
- resp 200: `{id: integer, name: string}` — successful operation
  exemplo: `{"id": 1995, "name": "lead_score"}`

### GET /accounts/custom_fields/{custom_field_id}
`getCustomFieldById` — Get custom field by id
- path `custom_field_id`* (integer)
- resp 200: `{id: integer, name: string, type: integer, description: string}` — successful operation

### GET /accounts/custom_fields/name/{custom_field_name}
`getCustomFieldByName` — Get custom field by name
- path `custom_field_name`* (string)
- resp 200: `{id: integer, name: string, type: integer, description: string}` — successful operation

### GET /accounts/bot_fields/{bot_field_id}
`getBFieldValue` — Get bot field value by id
- path `bot_field_id`* (integer)
- resp 200: `{id: integer, type: integer, name: string, value: string}` — successful operation
  exemplo: `{"id": 2334, "name": "age", "type": 1, "value": 25}`

### POST /accounts/bot_fields/{bot_field_id}
`setBField` — Set a bot field value
- path `bot_field_id`* (integer)
- FORM `value`* (string)
- resp 200: `{success: boolean}` — successful operation
  exemplo: `{"success": true}`

### DELETE /accounts/bot_fields/{bot_field_id}
`removeBField` — Unset the value of a bot field
- path `bot_field_id`* (integer)
- resp 200: `{success: boolean}` — successful operation
  exemplo: `{"success": true}`

### GET /accounts/integrations
`getAccountIntegrations` — Get all integrations from a business account.
- resp 200: `{openai: {active: boolean}, gemini: {active: boolean}, claude: {active: boolean}, xai: {active: boolean}, deepseek: {active: boolean}, google_sheets: {active: boolean}, email: {active: boolean}}` — List of available integrations and their status

### POST /accounts/templates/{template_id}/install
`installTemplate` — Install a template to your account
- path `template_id`* (number) — You can get template ID from the template link.
- **body** `content`* (JSON):
  - `template_key` (string) [obrigatorio] — The template key from the template link.
  exemplo: `{"template_key": "asa823mkAkdk394kdsjs"}`
- resp 200: `{success: boolean}` — successful operation
  exemplo: `{"success": true}`

### POST /accounts/templates/{template_id}/generateSingleUseLink
`generateTemplateLink` — Generate single-use template link
- path `template_id`* (integer) — You can get template ID from the template link
- resp 200: `{link: string}` — successful operation
  exemplo: `{"link": "https://..."}`

## /contacts

### GET /contacts/{contact_id}
`getUserByName` — Get contact by contact id
- path `contact_id`* (integer)
- resp 200: `Contact` — successful operation
- resp 400: Invalid username supplied
- resp 404: User not found

### GET /contacts/find_by_custom_field
`findByCustomField` — Find contacts by custom field value. It will return maximum 100 contacts. The results are sorted by the last custom field value update for a contact.
- query `field_id`* (string) — Custom field ID. Use 'phone' or 'email' as custom field id if you want to find the contact by phone or email
- query `value`* (string)
- resp 200: `{data: [Contact]}`
- resp 400: Invalid parameters

### GET /contacts/{contact_id}/tags
`getUserTags` — Get all tags added to this contact
- path `contact_id`* (integer)
- resp 200: `[Tag]` — successful operation

### POST /contacts/{contact_id}/tags/{tag_id}
`addTagToUser` — Add a tag to the contact
- path `contact_id`* (integer)
- path `tag_id`* (integer)
- resp 200: `{success: boolean}` — successful operation
  exemplo: `{"success": true}`

### DELETE /contacts/{contact_id}/tags/{tag_id}
`removeTagFromUser` — remove a tag from the contact
- path `contact_id`* (integer)
- path `tag_id`* (integer)
- resp 200: `{success: boolean}` — successful operation
  exemplo: `{"success": true}`

### POST /contacts
`createNewContact` — Creates a new contact.
- **body** `content`* (JSON):
  - `phone` (string) [obrigatorio] — The phone number with country code
  - `email` (string) — The contact email
  - `first_name` (string)
  - `last_name` (string)
  - `gender` (string) [enum=['male', 'female', 'unknown']]
  - `actions` (array<object>) — Actions can be send flow, add/remove tags, set/unset custom field ...
  exemplo: `{"phone": "+1234567890", "email": "test@test.com", "first_name": "John", "last_name": "Smith", "gender": "male", "actions": [{"action": "add_tag", "tag_name": "YOU_TAG_NAME"}, {"action": "set_field_value", "field_name": "YOU_CUSTOM_FIELD_NAME", "value": "ANY_VALUE"}, {"action": "send_flow", "flow_id": 11111}]}`
- resp default: `(sem schema)` — successful operation

### GET /contacts/{contact_id}/custom_fields
`getUserFields` — Get all custom fields from a contact
- path `contact_id`* (integer)
- resp 200: `[Custom_field]` — successful operation

### GET /contacts/{contact_id}/custom_fields/{custom_field_id}
`getFieldValue` — Get custom field value by id
- path `contact_id`* (integer)
- path `custom_field_id`* (integer)
- resp 200: `{id: integer, type: integer, name: string, value: string}` — successful operation
  exemplo: `{"id": 2334, "name": "age", "type": 1, "value": 25}`

### POST /contacts/{contact_id}/custom_fields/{custom_field_id}
`addFieldToUser` — Set a contact custom field
- path `contact_id`* (integer)
- path `custom_field_id`* (string)
- FORM `value`* (string)
- resp 200: `{success: boolean}` — successful operation
  exemplo: `{"success": true}`

### DELETE /contacts/{contact_id}/custom_fields/{custom_field_id}
`removeFieldFromUser` — remove a custom field from the contact
- path `contact_id`* (integer)
- path `custom_field_id`* (integer)
- resp 200: `{success: boolean}` — successful operation
  exemplo: `{"success": true}`

### POST /contacts/{contact_id}/send/{flow_id}
`sendFlowToUser` — Send a flow to contact
- path `contact_id`* (integer)
- path `flow_id`* (integer)
- (consumes FORM, sem campos)
- resp default: `(sem schema)` — successful operation

### POST /contacts/{contact_id}/send/text
`sendTextMessage` — Send text message to the contact
- path `contact_id`* (integer)
- **body** `content`* (JSON):
  - `text` (string) [obrigatorio]
  - `channel` (string) [enum=['messenger', 'whatsapp', 'sms', 'webchat', 'telegram', 'instagram', 'viber', 'omnichannel']]
  exemplo: `{"text": "This is a text message", "channel": "messenger"}`
- resp 200: `{success: boolean}` — successful operation
  exemplo: `{"success": true}`

### POST /contacts/{contact_id}/send/file
`sendFile` — Send file
- path `contact_id`* (integer)
- **body** `content`* (JSON):
  - `url` (string) [obrigatorio]
  - `type` (string) [enum=['file', 'image', 'audio', 'video'], obrigatorio]
  - `channel` (string) [enum=['messenger', 'sms', 'whatsapp', 'googleBM', 'telegram', 'instagram', 'viber', 'omnichannel']]
  exemplo: `{"url": "https://...", "type": "image", "channel": "messenger"}`
- resp 200: `{success: boolean}` — successful operation
  exemplo: `{"success": true}`

### POST /contacts/{contact_id}/send_content
`sendContent` — Allows to run multiple actions and send multiple messages. Works for all channels.
- path `contact_id`* (integer)
- **body** `content`* (JSON):
  - `messages` (array<object>)
  - `actions` (array<object>)
  - `channel` (string) [enum=['messenger', 'sms', 'whatsapp', 'googleBM', 'telegram', 'instagram', 'rcs', 'viber', 'omnichannel']]
  exemplo: `{"messages": [{"message": {"text": "Hello world"}}], "actions": [], "channel": "messenger"}`
- resp default: `(sem schema)` — successful operation

### POST /contacts/{contact_id}/ai/save_messages
`aiSaveMessages` — Save a message to the contact message history (AI)
- path `contact_id`* (number)
- **body** `content`* (JSON):
  - `messages` (array<object>)
    - `text` (string)
    - `type` (string) [enum=['text', 'image', 'file', 'audio']]
    - `role` (string) [enum=['assistant', 'user', 'developer']]
    (obrigatorios: text, role)
  exemplo: `{"messages": [{"text": "Hi there! How can I assist you today?", "type": "text", "role": "assistant"}]}`
- resp default: `(sem schema)` — successful operation

### POST /contacts/{contact_id}/send/products
`sendProduct` — Send a product message to the contact
- path `contact_id`* (integer)
- **body** `data`* (JSON):
  - `product_id` (array<object>) [obrigatorio] — The product_id  field could be a single product id, an array of product ids, or multiple product ids separated by a comma
  exemplo: `{"product_id": [1111, 222, 3333]}`
- resp default: `(sem schema)` — successful operation

### GET /contacts/{contact_id}/cart
`getUserCart` — Get the contact cart ready for checkout
- path `contact_id`* (integer)
- resp 200: `Cart` — successful operation

### DELETE /contacts/{contact_id}/cart
`clearUserCart` — Clear the contact cart
- path `contact_id`* (integer)
- resp 200: `{success: boolean}` — successful operation
  exemplo: `{"success": true}`

### POST /contacts/{contact_id}/pay/{order_id}
`payOrder` — Mark an order as Paid.
- path `contact_id`* (integer)
- path `order_id`* (string)
- FORM `amount_received`* (integer) — Total value the contact paid in cents.
- resp 200: `{success: boolean}` — successful operation
  exemplo: `{"success": true}`
- resp 400: The amount received is less than the total value of the order.
- resp 402: The contact received a message on Messenger why the checkout failed.
- resp 404: The order ID doesn't existe

### GET /contacts/{contact_id}/order/{order_id}
`getUserOrder` — Get order information
- path `contact_id`* (integer)
- path `order_id`* (string)
- resp 200: `Cart` — successful operation

### POST /contacts/{contact_id}/order/{order_id}
`changeOrder` — Change order status.
- path `contact_id`* (integer)
- path `order_id`* (string)
- **body** `content`* (JSON):
  - `status` (integer) [enum=[6, 7, 10, 13]] — The new order status. 6 - Processing, 7 - Shipped, 10 - Completed, 13 - Canceled.
  - `name` (string)
  - `phone` (string)
  - `email` (string)
  - `country` (string)
  - `state` (string)
  - `city` (string)
  - `zip_code` (string)
  - `address` (string)
  - `street_1` (string)
  - `street_2` (string)
  - `note` (string)
  exemplo: `{"status": 7}`
- resp 200: `{success: boolean}` — successful operation
  exemplo: `{"success": true}`
- resp 400: Order status must be 6, 7, 10, or 13
- resp 402: The order status is the same as the previous status
- resp 404: The order ID doesn't existe

### POST /contacts/{contact_id}/cart/{product_id}
`addProductCart` — Add a product to contact cart
- path `contact_id`* (integer)
- path `product_id`* (integer)
- FORM `quantity`* (integer)
- resp 200: `{success: boolean}` — successful operation
  exemplo: `{"success": true}`

### DELETE /contacts/{contact_id}/cart/{product_id}
`removeProductCart` — remove a product from contact cart
- path `contact_id`* (integer)
- path `product_id`* (integer)
- resp 200: `{success: boolean}` — successful operation
  exemplo: `{"success": true}`

## /pipelines

### GET /pipelines
`getPipelines` — Get list of pipelines
- query `offset` (integer) — Specifies the starting position of the first record to return in a paginated response.
- query `limit` (integer) — Sets the maximum number of records to return per request.
- resp 200: `{data: [Pipeline]}` — successful operation

### GET /pipelines/{pipeline_id}
`getPipeline` — Get list of pipelines
- path `pipeline_id`* (number)
- resp 200: `Pipeline` — successful operation

### GET /pipelines/{pipeline_id}/stages
`getPipelineStages` — Get list of pipeline stages
- path `pipeline_id`* (number)
- resp 200: `{data: [PipelineStage]}` — successful operation

### GET /pipelines/{pipeline_id}/custom_fields
`getPipelineCustomFields` — Get all custom fields from a pipeline.
- resp 200: `[{id: number, name: string, type: string, description: string}]` — successful operation

### GET /pipelines/{pipeline_id}/opportunities
`pipelinesGetCards` — Get list of opportunities / tickets
- path `pipeline_id`* (number)
- query `contact_id` (number) — The ID of the contact to filter the opportunities.
- query `offset` (integer) — Specifies the starting position of the first record to return in a paginated response.
- query `limit` (integer) — Sets the maximum number of records to return per request.
- resp 200: `{data: [Opportunity]}` — successful operation

### POST /pipelines/{pipeline_id}/opportunities
`pipelinesAddCard` — Creates an opportunity / ticket.
- path `pipeline_id`* (number)
- **body** `content`* (JSON):
  - `contact_id` (number) [obrigatorio]
  - `title` (string) [obrigatorio]
  - `description` (string)
  - `stage_id` (number) — if omitted, the the contact is added to first stage.
  - `value` (number) [default=0]
  - `status` (string) [enum=['open', 'won', 'lost'], default=open] — won is positive and lost is negative
  - `priority` (string) [enum=['low', 'medium', 'high'], default=medium]
  - `assigned_admins` (array<object>) [default=[]]
  exemplo: `{"contact_id": "12345678", "title": "This is a test opportunity", "description": "...", "stage_id": 12334, "value": 300, "status": "open", "priority": "low", "assigned_admins": [55446563], "custom_fields": [{"id": 1234, "value": "Any data"}]}`
- resp default: `{data: [Opportunity]}` — successful operation

### GET /pipelines/{pipeline_id}/opportunities/{opportunity_id}
`pipelinesGetCard` — Get an opportunity / ticket
- path `pipeline_id`* (number)
- path `opportunity_id`* (number)
- resp 200: `Opportunity` — successful operation

### POST /pipelines/{pipeline_id}/opportunities/{opportunity_id}
`pipelinesUpdateCard` — Updates an opportunity / ticket.
- path `pipeline_id`* (number)
- path `opportunity_id`* (number)
- **body** `content`* (JSON):
  - `title` (string) [obrigatorio]
  - `description` (string)
  - `stage_id` (number) — if omitted, the the contact is added to first stage.
  - `value` (number) [default=0]
  - `status` (string) [enum=['open', 'won', 'lost'], default=open] — won is positive and lost is negative
  - `priority` (string) [enum=['low', 'medium', 'high'], default=medium]
  - `assigned_admins` (array<object>) [default=[]]
  exemplo: `{"title": "This is a test opportunity", "description": "...", "stage_id": 12334, "value": 300, "status": "open", "priority": "low", "assigned_admins": [55446563], "custom_fields": [{"id": 1234, "value": "Any data"}, {"name": "Age", "value": 30}]}`
- resp 200: `{success: boolean}` — successful operation
  exemplo: `{"success": true}`

### DELETE /pipelines/{pipeline_id}/opportunities/{opportunity_id}
`pipelinesDeleteCard` — Delete an opportunity / ticket
- path `pipeline_id`* (number)
- path `opportunity_id`* (number)
- resp 200: `{success: boolean}` — successful operation
  exemplo: `{"success": true}`

### POST /pipelines/{pipeline_id}/opportunities/{opportunity_id}/transfer-to-pipeline
`pipelinesTransferCard` — Transfer an opportunity / ticket to another pipeline.
- path `pipeline_id`* (number)
- path `opportunity_id`* (number)
- **body** `content`* (JSON):
  - `target_pipeline_id` (number) [obrigatorio]
  - `target_stage_id` (number) [obrigatorio]
  exemplo: `{"target_pipeline_id": 123456, "target_stage_id": 654321}`
- resp 200: `{success: boolean}` — successful operation
  exemplo: `{"success": true}`

### GET /pipelines/{pipeline_id}/opportunities/{opportunity_id}/comments
`pipelinesGetComments` — Get list of comments of an opportunity / ticket
- path `pipeline_id`* (number)
- path `opportunity_id`* (number)
- query `offset` (integer) — Specifies the starting position of the first record to return in a paginated response.
- query `limit` (integer) — Sets the maximum number of records to return per request.
- resp default: `{data: [OpportunityComment]}` — successful operation

### POST /pipelines/{pipeline_id}/opportunities/{opportunity_id}/comments
`pipelinesAddComment` — Creates a new comment on an opportunity / ticket.
- path `pipeline_id`* (number)
- path `opportunity_id`* (number)
- **body** `content`* (JSON):
  - `content` (string) [obrigatorio]
  exemplo: `{"content": "This is a comment"}`
- resp 200: `OpportunityComment` — successful operation

### DELETE /pipelines/{pipeline_id}/opportunities/{opportunity_id}/comments/{comment_id}
`pipelinesDeleteComment` — Delete a comment of an opportunity / ticket
- path `pipeline_id`* (number)
- path `opportunity_id`* (number)
- path `comment_id`* (number)
- resp 200: `{success: boolean}` — successful operation
  exemplo: `{"success": true}`

## /agents

### GET /agents/
`getAIAgents` — Get list of AI agents
- resp 200: `{data: [Agent]}`
- resp 400: Invalid parameters

### GET /agents/{agent_id}
`getAIById` — Get AI agent by id
- path `agent_id`* (number)
- resp 200: `Agent` — successful operation

### POST /agents/{agent_id}
`updateAIById` — Update AI agent by id
- path `agent_id`* (number)
- **body** `data`* (JSON):
  - `prompt` (string) — The prompt field for the AI agent
  - `max_output_tokens` (number) — The max_output_tokens field for the AI agent
  - `model` (object)
    - `openAI` (string) [obrigatorio]
    - `gemini` (string) [obrigatorio]
    - `claude` (string) [obrigatorio]
    - `xAI` (string) [obrigatorio]
    - `deepseek` (string) [obrigatorio]
  exemplo: `{"prompt": "Your prompt here"}`
- resp 200: `Agent`
- resp 400: 

### GET /agents/functions
`getAIFunctions` — Get list of AI Functions
- resp 200: `{data: [{id: number, name: string, created_by: number, created_at: string}]}`

### GET /agents/mcp
`getAIMCPs` — Get list of AI MCPs
- resp 200: `{data: [{id: number, name: string, created_by: number, created_at: string}]}`

### GET /agents/files
`getAIFiles` — Get list of AI Files
- resp 200: `{data: [{id: number, name: string, size: number, url: string, created_by: number, created_at: string}]}`

## /calendars

### GET /calendars
`getCalendars` — Get list of calendars
- resp 200: `{data: [Calendar]}`
- resp 400: Invalid parameters

### GET /calendars/{calendar_id}
`getProductById` — Get product by id
- path `calendar_id`* (number)
- resp 200: `Calendar` — successful operation

## /products

### GET /products/{product_id}
`getProductById` — Get product by id
- path `product_id`* (integer)
- resp 200: `Product` — successful operation

### POST /products/{product_id}
`updateProduct` — Update product.
- path `product_id`* (number)
- **body** `content`* (JSON):
  - `price` (number)
  - `active` (boolean) — if contacts can buy the product.
  - `stock` (number)
  exemplo: `{"active": false, "stock": 500, "price": 40}`
- resp 200: `{success: boolean, updated: boolean}` — successful operation
  exemplo: `{"success": true, "updated": true}`

## /broadcasts

### GET /broadcasts
`getBroadcasts` — Get list of broadcasts
- resp 200: `{data: [Broadcast]}`
- resp 400: Invalid parameters

### GET /broadcasts/{broadcast_id}
`getBroadcastById` — Get broadcast by id
- path `broadcast_id`* (number)
- resp 200: `Broadcast` — successful operation
- resp 404: Broadcast not found

### POST /broadcasts/{broadcast_id}/resend
`resendBroadcastById` — Resend a broadcast by id
- path `broadcast_id`* (number)
- resp 200: `{success: boolean}` — successful operation
  exemplo: `{"success": true}`

### POST /broadcasts/{broadcast_id}/cancel
`cancelBroadcastById` — Cancel a broadcast by id
- path `broadcast_id`* (number)
- resp 200: `{success: boolean}` — successful operation
  exemplo: `{"success": true}`

## Modelos

### Cart
- `order_id` (string)
- `page_id` (integer)
- `user_id` (integer) — The contact ID
- `currency` (string)
- `total` (integer)
- `subtotal` (integer)
- `total_items` (integer)
- `coupon_discount` (integer)
- `coupon` (string)
- `line_items` (array<ProductCart>)
- `contact` (Contact)

### Order
- `id` (string)
- `page_id` (integer)
- `user_id` (integer) — The contact ID
- `created_at` (string) — Subscribed date in UTC. Example 2022-10-12 14:40:00
- `created_timestamp` (integer) — Date of the order in epoch/Unix timestamp
- `currency` (string)
- `total` (integer)
- `subtotal` (integer)
- `shipping_cost` (integer)
- `total_taxes` (integer)
- `total_discounts` (integer)
- `total_items` (integer)
- `coupon_discount` (integer)
- `coupon` (string)
- `status` (string) [enum=['Not processed', 'Accepted', 'Delivering', 'Completed', 'Canceled']]
- `line_items` (array<ProductCart>)
- `contact` (Contact)

### ProductCart
- `id` (integer)
- `name` (string)
- `img` (string)
- `price` (number) — the price is not in cents
- `amount` (integer) — quantity
- `descr_min` (string)
- `manufacturer` (integer) — The vendor ID
- `variant` (string)
- `user_msg` (string)

### Custom_field
- `id` (integer)
- `name` (string)
- `type` (integer) [enum=[0, 1, 2, 3, 4, 5, 6, 7]] — 0 - Text, 1 - Number, 2- Date (Unix timestamp), 3 - Date & Time (Unix timestamp), 4 - Boolean(0 or 1), 5- Long Text, 6 - Select, 7 - Multi Select
- `value` (string) — type == 0 then value is string, else value is a number

### Admin
- `id` (integer)
- `email` (string)
- `first_name` (string)
- `last_name` (string)
- `full_name` (string)
- `profile_pic` (string)
- `available` (boolean) — Whether the admin has the availability status set on/off.

### Team
- `id` (number)
- `name` (string)

### Tag
- `id` (integer)
- `name` (string)

### Pipeline
- `id` (number)
- `name` (string)

### PipelineStage
- `id` (number)
- `name` (string)

### OpportunityComment
- `id` (number)
- `data` (string)
- `created_at` (string) — UTC
- `created_by` (number) — Admin ID

### Opportunity
- `id` (number)
- `contact_id` (number)
- `title` (string)
- `description` (string)
- `value` (number)
- `status` (string)
- `priority` (string)
- `stage` (object)
  - `id` (number)
  - `name` (string)
- `assigned_admins` (array<number>)
- `created_at` (string) — UTC
- `created_by` (number) — Admin ID
- `updated_at` (string) — UTC
- `updated_by` (number) — Admin ID

### Product
- `id` (integer)
- `name` (string)
- `price` (number)
- `sale_price` (number)
- `category_id` (integer)
- `category_name` (string)
- `stock` (integer)
- `short_description` (string)
- `image` (string)
- `created_at` (string) — Subscribed date in UTC. Example 2022-10-12 14:40:00

### Calendar
- `id` (number)
- `name` (string)
- `duration` (number)
- `created_by` (number)
- `created_at` (string) — Date in UTC. Example 2022-10-12 14:40:00

### Agent
- `id` (number)
- `name` (string)
- `created_by` (number)
- `created_at` (string) — Date in UTC. Example 2022-10-12 14:40:00

### Appointment
- `id` (number)
- `name` (string)
- `contact_id` (number)
- `calendar_id` (number)
- `start_date` (string) — When the appointment starts. Date in UTC. Example 2022-10-12 14:40:00
- `end_date` (string) — When the appointment ends. Date in UTC. Example 2022-10-12 14:40:00
- `status` (string) [enum=['PENDING', 'CONFIRMED', 'DONE', 'CANCELED']]
- `created_at` (string) — Date in UTC. Example 2022-10-12 14:40:00

### Contact
- `id` (integer)
- `page_id` (integer)
- `first_name` (string)
- `last_name` (string)
- `channel` (integer) — 0 - Messenger, 2 - SMS, 5 - WhatsApp, 7 - Google Business Message, 8 - Telegram, 9 - Webchat
- `profile_pic` (string)
- `locale` (string)
- `gender` (integer) — 0 - Female, 1 - Male, 2 - Unknown
- `timezone` (integer)
- `last_sent` (integer) — Unix timestamp in milliseconds
- `last_delivered` (integer) — Unix timestamp in milliseconds
- `last_seen` (integer) — Unix timestamp in milliseconds
- `last_interaction` (integer) — Unix timestamp in milliseconds
- `subscribed_date` (string) — Subscribed date in UTC. Example 2022-10-12 14:40:00
- `subscribed` (integer) — 1 - Subscribed, 2 - Unsubscribed
- `tags` (array<Tag>)
- `custom_fields` (array<Custom_field>)

### Account
- `id` (integer)
- `name` (string)
- `fb_page_id` (integer)
- `instagram_id` (integer)
- `waba_id` (integer)
- `wa_phone_id` (integer)
- `viber_id` (integer)
- `active` (integer) [enum=[0, 1]] — 0 - False, 1 True
- `plan` (integer) [enum=[1, 4, 6, 13, 15]] — 1 - Pro Subscription, 4 - FREE, 6 - Pro No Subscription, 11 - LTD, 12 - LTD, 13 - PRO Trial - Downgrade to FREE at the end, 15 - PRO Trial - Force to pay at the end
- `created` (string) — The date (UTC) when the account was created

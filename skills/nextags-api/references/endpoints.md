# API NexTags — referencia completa (gerada do OpenAPI oficial)
Fonte: https://docs.nextags.com.br/openapi.json · 86 operacoes · gerado em 2026-10-26 · base `https://app.nextagsai.com.br/api`
Auth: header `X-ACCESS-TOKEN` (valor puro). `FORM` = application/x-www-form-urlencoded (`--form k=v`); `JSON` = body JSON (`--json`).
O contrato nao descreve tudo que a API devolve (ex.: `GET /agents/{id}` traz `data.prompt`/`data.model`, que ele nao lista; ids e numeros voltam como string). Formas reais: `live_shapes.md`.
Os exemplos de codigo (cURL/JS/Python/PHP) de cada operacao estao no `x-codeSamples` de `openapi.json`.

## Conta

### GET /accounts/me
`getAccountInformation` — Consultar a conta
Devolve os dados da conta dona da chave de API: o ID, o nome, se o acesso ao painel está liberado, quando a conta foi criada e quantos contatos ela tem. É a chamada mais simples da API: use para conferir se a chave funciona. Veja [Sua primeira requisição](https://docs.nextags.com.br/comecar/primeira-requisicao/).
- resp 200: `{page_id: integer, name: string, active: boolean, created: integer, total_users: integer}` — Os dados da conta.
  exemplo: `{"page_id": 123456, "name": "Loja Exemplo", "active": true, "created": 1735700000, "total_users": 5230}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /accounts/admins
`getAccountAdmins` — Listar administradores
Lista os administradores da conta, as pessoas da equipe que entram no painel, com o ID de cada um. Outras chamadas pedem esse ID: por exemplo, os responsáveis de uma oportunidade (`assigned_admins`) e a ação `assign_conversation`, que atribui a conversa a alguém. Veja [Administradores e permissões](https://help.nextags.com.br/tutoriais/configuracoes/administradores-e-permissoes/).
- resp 200: `[Admin]` — A lista de administradores.
  exemplo: `[{"id": 10001, "email": "ana@exemplo.com.br", "first_name": "Ana", "last_name": "Souza", "full_name": "Ana Souza", "profile_pic": "https://exemplo.com.br/fotos/ana.jpg", "available": true}]`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /accounts/teams
`getAccountTeams` — Listar equipes
Lista as equipes de atendimento da conta (as equipes da Caixa de Entrada), com o ID e o nome de cada uma. Veja [Equipes de caixa de entrada](https://help.nextags.com.br/tutoriais/caixa-de-entrada/equipes-de-atendimento/).
- resp 200: `[Team]` — A lista de equipes.
  exemplo: `[{"id": 501, "name": "Vendas"}, {"id": 502, "name": "Suporte"}]`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /accounts/integrations
`getAccountIntegrations` — Listar integrações da conta
Mostra quais integrações estão ligadas na conta: os provedores de IA (OpenAI, Gemini, Claude, xAI e DeepSeek), o Google Sheets e o e-mail. Cada uma vem com `active`: `true` quando está conectada. Veja [A aba Integrações](https://help.nextags.com.br/tutoriais/configuracoes/integracoes/).
- resp 200: `{openai: {active: boolean}, gemini: {active: boolean}, claude: {active: boolean}, xai: {active: boolean}, deepseek: {active: boolean}, google_sheets: {active: boolean}, email: {active: boolean}}` — Cada integração com o seu estado.
  exemplo: `{"openai": {"active": true}, "gemini": {"active": false}, "claude": {"active": false}, "xai": {"active": false}, "deepseek": {"active": false}, "google_sheets": {"active": true}, "email": {"active": false}}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

## Etiquetas

### GET /accounts/tags
`getAccountTags` — Listar etiquetas
Lista as etiquetas da conta, com o ID e o nome de cada uma. Use o ID para pôr ou tirar a etiqueta de um contato.
- resp 200: `[Tag]` — As etiquetas da conta.
  exemplo: `[{"id": 2001, "name": "cliente-vip"}, {"id": 2002, "name": "lead-quente"}]`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /accounts/tags
`createTag` — Criar etiqueta
Cria uma etiqueta na conta e devolve o ID dela. O nome vai em formulário (`application/x-www-form-urlencoded`), não em JSON.
- **body FORM***:
  - `name` (string) [obrigatorio] — O nome da etiqueta.
  exemplo: `{"name": "cliente-vip"}`
- resp 200: `{id: integer}` — A etiqueta criada.
  exemplo: `{"id": 2001}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /accounts/tags/{tag_id}
`getTagById` — Consultar etiqueta
Devolve o nome de uma etiqueta a partir do ID.
- path `tag_id`* (integer) — O ID da etiqueta.
- resp 200: `{id: integer, name: string}` — A etiqueta.
  exemplo: `{"id": 2001, "name": "cliente-vip"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### DELETE /accounts/tags/{tag_id}
`deleteTag` — Apagar etiqueta
Apaga a etiqueta da conta, sem volta. Antes, confira os fluxos e os acionadores que usam a etiqueta. Para só tirar a etiqueta de um contato, use [Remover etiqueta do contato](https://docs.nextags.com.br/referencia/etiquetas/remover-etiqueta-do-contato/).
- path `tag_id`* (integer) — O ID da etiqueta.
- resp 200: `{success: boolean}` — A etiqueta foi apagada.
  exemplo: `{"success": true}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /accounts/tags/name/{tag_name}
`getTagByName` — Buscar etiqueta pelo nome
Encontra uma etiqueta pelo nome e devolve o ID dela. O nome vai no caminho, codificado para URL: `lead quente` vira `lead%20quente`.
- path `tag_name`* (string) — O nome da etiqueta, codificado para URL.
- resp 200: `{id: integer, name: string}` — A etiqueta.
  exemplo: `{"id": 2001, "name": "cliente-vip"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /contacts/{contact_id}/tags
`getUserTags` — Listar etiquetas do contato
Lista as etiquetas que o contato tem. O contato inteiro, com os campos personalizados, sai de [Consultar contato](https://docs.nextags.com.br/referencia/contatos/consultar-contato/).
- path `contact_id`* (integer) — O ID do contato.
- resp 200: `[Tag]` — As etiquetas do contato.
  exemplo: `[{"id": 2001, "name": "cliente-vip"}]`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /contacts/{contact_id}/tags/{tag_id}
`addTagToUser` — Adicionar etiqueta ao contato
Põe a etiqueta no contato, como a ação **Adicionar Etiqueta** de um fluxo. Para usar o nome da etiqueta no lugar do ID, mande a ação `add_tag` em [Enviar conteúdo](https://docs.nextags.com.br/referencia/mensagens/enviar-conteudo/). Veja [Etiquetar contatos e preencher campos](https://docs.nextags.com.br/guias/etiquetas-e-campos/).
- path `contact_id`* (integer) — O ID do contato.
- path `tag_id`* (integer) — O ID da etiqueta.
- (sem body)
- resp 200: `{success: boolean}` — A etiqueta foi aplicada.
  exemplo: `{"success": true}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### DELETE /contacts/{contact_id}/tags/{tag_id}
`removeTagFromUser` — Remover etiqueta do contato
Tira a etiqueta do contato, como a ação **Remover Etiqueta** de um fluxo. A etiqueta continua na conta.
- path `contact_id`* (integer) — O ID do contato.
- path `tag_id`* (integer) — O ID da etiqueta.
- resp 200: `{success: boolean}` — A etiqueta foi tirada do contato.
  exemplo: `{"success": true}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

## Fluxos e modelos

### GET /accounts/flows
`getAccountFlows` — Listar fluxos
Lista os fluxos da conta, com o ID e o nome de cada um. Use o ID em [Enviar fluxo](https://docs.nextags.com.br/referencia/mensagens/enviar-fluxo/) e na ação `send_flow`.
- resp 200: `[{id: integer, name: string}]` — Os fluxos da conta.
  exemplo: `[{"id": 1000001, "name": "Boas-vindas"}, {"id": 1000002, "name": "Recuperar carrinho"}]`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /accounts/templates/{template_id}/install
`installTemplate` — Instalar modelo na conta
Instala um modelo de **Templates** na conta dona da chave de API, sem abrir o link de instalação. O ID e a chave saem do link que o **Obter Link** copia, em **Ferramentas** › **Templates** › **⋮**: ele termina em `store/template?id=9001&key=b7Xk29QpLm4R`, e o `id` vai no caminho e o `key` vai em `template_key`. No app, a conta que criou o modelo não pode instalá-lo.
- path `template_id`* (integer) — O ID do modelo: o `id` do link de instalação.
- **body JSON***:
  - `template_key` (string) [obrigatorio] — A chave do modelo: o `key` do link de instalação.
  exemplo: `{"template_key": "b7Xk29QpLm4R"}`
- resp 200: `{success: boolean}` — O modelo foi instalado.
  exemplo: `{"success": true}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /accounts/templates/{template_id}/generateSingleUseLink
`generateTemplateLink` — Gerar link de uso único do modelo
Gera um link de instalação do modelo que vale para um uso só. Use para entregar o modelo a uma pessoa sem passar o link fixo do **Obter Link**. O `template_id` é o `id` do link de instalação: veja [Instalar modelo na conta](https://docs.nextags.com.br/referencia/fluxos/instalar-modelo-na-conta/).
- path `template_id`* (integer) — O ID do modelo: o `id` do link de instalação.
- (sem body)
- resp 200: `{link: string}` — O link gerado.
  exemplo: `{"link": "https://app.nextagsai.com.br/store/template?id=9001&key=Q4mZ81xTr6Wd"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

## Campos personalizados

### GET /accounts/custom_fields
`getAccountCustomFields` — Listar campos personalizados
Lista os campos personalizados da conta. Cada campo traz o ID (`id`), o nome (`name`), o tipo (`type`: 0 texto, 1 número, 2 data, 3 data e hora, 4 sim/não, 5 texto longo, 6 seleção única, 7 seleção múltipla) e a descrição (`description`). Use o ID para ler ou preencher o valor de um contato.
- resp 200: `[{id: integer, name: string, type: integer, description: string}]` — Os campos da conta.
  exemplo: `[{"id": 3001, "name": "cidade", "type": 0, "description": "Cidade de entrega"}, {"id": 3002, "name": "data_nascimento", "type": 2, "description": ""}]`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /accounts/custom_fields
`createCustomField` — Criar campo personalizado
Cria um campo personalizado na conta e devolve o ID dele. Pela API, o tipo vai de 0 a 4 (texto, número, data, data e hora e sim/não); texto longo e seleções se criam no app. Com `isBotField: true`, o campo nasce como [campo do bot](https://help.nextags.com.br/tutoriais/fluxos/campos-do-bot/), com um valor só para a conta toda, que vai em `value`. Use um nome novo: no app, um nome repetido ou reservado é recusado.
- **body JSON***:
  - `name` (string) [obrigatorio] — O nome do campo, como ele aparece nas listas e nas variáveis das mensagens (`{{cidade}}`).
  - `type` (integer) [enum=[0, 1, 2, 3, 4], obrigatorio] — O tipo: 0 texto, 1 número, 2 data, 3 data e hora, 4 sim/não. Depois de criado, o campo não muda de tipo.
  - `isBotField` (boolean) [default=False] — `true` cria um campo do bot (um valor para a conta toda) no lugar de um campo do contato.
  - `value` (string) — O valor do campo do bot, no formato do tipo. Num campo do contato, é ignorado.
  - `description` (string) — Uma descrição, que aparece embaixo do nome na lista de campos.
  exemplo: `{"name": "cidade", "type": 0, "description": "Cidade de entrega"}`
- resp 200: `{id: integer, name: string}` — O campo criado.
  exemplo: `{"id": 3001, "name": "cidade"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /accounts/custom_fields/{custom_field_id}
`getCustomFieldById` — Consultar campo personalizado
Devolve o nome, o tipo e a descrição de um campo personalizado a partir do ID.
- path `custom_field_id`* (integer) — O ID do campo personalizado.
- resp 200: `{id: integer, name: string, type: integer, description: string}` — O campo.
  exemplo: `{"id": 3001, "name": "cidade", "type": 0, "description": "Cidade de entrega"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /accounts/custom_fields/name/{custom_field_name}
`getCustomFieldByName` — Buscar campo pelo nome
Encontra um campo personalizado pelo nome e devolve o ID, o tipo e a descrição. O nome vai no caminho, codificado para URL: `data de nascimento` vira `data%20de%20nascimento`.
- path `custom_field_name`* (string) — O nome do campo, codificado para URL.
- resp 200: `{id: integer, name: string, type: integer, description: string}` — O campo.
  exemplo: `{"id": 3001, "name": "cidade", "type": 0, "description": "Cidade de entrega"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /contacts/{contact_id}/custom_fields
`getUserFields` — Listar campos do contato
Lista os campos personalizados do contato, com o valor de cada um. O contato inteiro, com as etiquetas, sai de [Consultar contato](https://docs.nextags.com.br/referencia/contatos/consultar-contato/).
- path `contact_id`* (integer) — O ID do contato.
- resp 200: `[Custom_field]` — Os campos do contato, com o valor.
  exemplo: `[{"id": 3001, "name": "cidade", "type": 0, "value": "São Paulo"}, {"id": 3002, "name": "data_nascimento", "type": 2, "value": 642643200}]`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /contacts/{contact_id}/custom_fields/{custom_field_id}
`getFieldValue` — Consultar campo do contato
Devolve o valor de um campo personalizado do contato. Data e data e hora vêm em Unix timestamp, em segundos; sim/não vem como 1 ou 0.
- path `contact_id`* (integer) — O ID do contato.
- path `custom_field_id`* (integer) — O ID do campo personalizado.
- resp 200: `{id: integer, type: integer, name: string, value: string|number}` — O campo, com o valor do contato.
  exemplo: `{"id": 3001, "name": "cidade", "type": 0, "value": "São Paulo"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /contacts/{contact_id}/custom_fields/{custom_field_id}
`addFieldToUser` — Preencher campo do contato
Grava um valor num campo personalizado do contato, como a ação **Definir Campo Personalizado** de um fluxo. O valor vai em formulário, no formato do tipo do campo: data e data e hora em Unix timestamp (segundos) e sim/não como `1` ou `0`. Para preencher pelo nome do campo no lugar do ID, mande a ação `set_field_value` em [Enviar conteúdo](https://docs.nextags.com.br/referencia/mensagens/enviar-conteudo/). Veja [Etiquetar contatos e preencher campos](https://docs.nextags.com.br/guias/etiquetas-e-campos/).
- path `contact_id`* (integer) — O ID do contato.
- path `custom_field_id`* (string) — O ID do campo personalizado.
- **body FORM***:
  - `value` (string) [obrigatorio] — O valor, no formato do tipo do campo.
  exemplo: `{"value": "São Paulo"}`
- resp 200: `{success: boolean}` — O valor foi gravado.
  exemplo: `{"success": true}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### DELETE /contacts/{contact_id}/custom_fields/{custom_field_id}
`removeFieldFromUser` — Limpar campo do contato
Apaga o valor de um campo personalizado do contato, como a ação **Limpar Campo Personalizado** de um fluxo. O campo continua na conta.
- path `contact_id`* (integer) — O ID do contato.
- path `custom_field_id`* (integer) — O ID do campo personalizado.
- resp 200: `{success: boolean}` — O valor foi apagado.
  exemplo: `{"success": true}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

## Campos do bot

### GET /accounts/bot_fields/{bot_field_id}
`getBFieldValue` — Consultar campo do bot
Devolve o nome, o tipo e o valor de um campo do bot.
- path `bot_field_id`* (integer) — O ID do campo do bot.
- resp 200: `{id: integer, type: integer, name: string, value: string|number}` — O campo do bot, com o valor.
  exemplo: `{"id": 3101, "name": "Horário de atendimento", "type": 0, "value": "Seg a sex, das 9h às 18h"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /accounts/bot_fields/{bot_field_id}
`setBField` — Preencher campo do bot
Troca o valor de um campo do bot: todos os fluxos que usam o campo passam a mostrar o valor novo. Use quando o valor vem de outro sistema, como o preço do dia ou o cupom da semana. O valor vai em formulário, no formato do tipo do campo: data e data e hora em Unix timestamp (segundos) e sim/não como `1` ou `0`.
- path `bot_field_id`* (integer) — O ID do campo do bot.
- **body FORM***:
  - `value` (string) [obrigatorio] — O valor novo, no formato do tipo do campo.
  exemplo: `{"value": "Seg a sex, das 9h às 18h"}`
- resp 200: `{success: boolean}` — O valor foi gravado.
  exemplo: `{"success": true}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### DELETE /accounts/bot_fields/{bot_field_id}
`removeBField` — Limpar campo do bot
Apaga o valor de um campo do bot. O campo continua na conta, sem valor.
- path `bot_field_id`* (integer) — O ID do campo do bot.
- resp 200: `{success: boolean}` — O valor foi apagado.
  exemplo: `{"success": true}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

## Contatos

### GET /contacts/{contact_id}
`getContactById` — Consultar contato
Devolve um contato, com os dados do perfil, as etiquetas e os campos personalizados. Vêm o nome, o canal atual, o gênero, o idioma, o fuso, as datas da última mensagem e da última interação e a inscrição. Para achar o ID a partir do telefone ou do e-mail, use [Buscar contato por campo personalizado](https://docs.nextags.com.br/referencia/contatos/buscar-contato-por-campo-personalizado/).
- path `contact_id`* (integer) — O ID do contato.
- resp 200: `{id: integer, page_id: integer, first_name: string, last_name: string, channel: integer, profile_pic: string, locale: string, gender: integer, timezone: integer, last_sent: integer, last_delivered: integer, last_seen: integer, last_interaction: integer, subscribed_date: string, subscribed: integer, tags: [Tag], custom_fields: [Custom_field]}` — O contato.
  exemplo: `{"id": 123456789, "page_id": 123456, "first_name": "Ana", "last_name": "Souza", "channel": 5, "profile_pic": "https://exemplo.com.br/fotos/ana.jpg", "locale": "pt_BR", "gender": 0, "timezone": -3, "last_sent": 1792936930000, "last_delivered": 1792936932000, "last_seen": 1792937020000, "last_interaction": 1792936680000, "subscribed_date": "2026-10-12 14:40:00", "subscribed": 1, "tags": [{"id": 2001, "name": "cliente-vip"}], "custom_fields": [{"id": 3001, "name": "cidade", "type": 0, "value": "São Paulo"}]}`
- resp 400: O `contact_id` não é um ID válido.
- resp 401: A chave de API não veio no cabeçalho ou não vale.
- resp 404: Não existe contato com esse ID nesta conta.

### GET /contacts/find_by_custom_field
`findByCustomField` — Buscar contato por campo personalizado
Encontra contatos pelo valor de um campo: o telefone, o e-mail ou um campo personalizado. Devolve no máximo 100 contatos, os mais recentes primeiro, pela última mudança do campo. É o jeito de achar o `contact_id` de quem você conhece pelo telefone ou pelo e-mail: veja [Encontrar um contato pelo e-mail ou telefone](https://docs.nextags.com.br/guias/buscar-contato-por-campo/).
- query `field_id`* (string) — Onde procurar: `phone` (telefone), `email` (e-mail) ou o ID de um campo personalizado.
- query `value`* (string) — O valor procurado. O telefone vai completo e só com números, como `5511988776655`.
- resp 200: `{data: [Contact]}` — Os contatos encontrados, em `data`.
  exemplo: `{"data": [{"id": 123456789, "page_id": 123456, "first_name": "Ana", "last_name": "Souza", "channel": 5, "profile_pic": "https://exemplo.com.br/fotos/ana.jpg", "locale": "pt_BR", "gender": 0, "timezone": -3, "last_sent": 1792936930000, "last_delivered": 1792936932000, "last_seen": 1792937020000, "last_interaction": 1792936680000, "subscribed_date": "2026-10-12 14:40:00", "subscribed": 1, "tags": [{"id": 2001, "name": "cliente-vip"}], "custom_fields": [{"id": 3001, "name": "cidade", "type": 0, "value": "São Paulo"}]}]}`
- resp 400: Faltou `field_id` ou `value`, ou um deles não vale.
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /contacts
`createNewContact` — Criar contato
Cria um contato e, na mesma chamada, roda ações nele: etiquetar, preencher campos e enviar um fluxo. O telefone vai completo, com o código do país e o DDD, só com números, como `5511988776655`: veja [O formato certo do telefone](https://help.nextags.com.br/tutoriais/contatos/formato-do-telefone/). Para não criar o mesmo contato duas vezes, procure antes pelo telefone ou pelo e-mail em [Buscar contato por campo personalizado](https://docs.nextags.com.br/referencia/contatos/buscar-contato-por-campo-personalizado/). Veja [Criar ou atualizar um contato](https://docs.nextags.com.br/guias/criar-ou-atualizar-contato/). Se o contato nunca mandou mensagem para a conta, a janela de 24 horas do WhatsApp está fechada: o fluxo da ação `send_flow` precisa começar com um Modelo de Mensagem aprovado. Veja [A janela de 24 horas](https://help.nextags.com.br/tutoriais/canais/janela-de-24-horas/).
- **body JSON***:
  - `phone` (string) [obrigatorio] — O telefone com o código do país (DDI) e o DDD, só com números.
  - `email` (string) — O e-mail do contato.
  - `first_name` (string) — O nome.
  - `last_name` (string) — O sobrenome.
  - `gender` (string) [enum=['male', 'female', 'unknown']] — O gênero: `male` (masculino), `female` (feminino) ou `unknown` (desconhecido).
  - `actions` (array<Acao>) — Ações para rodar no contato, na ordem da lista: `add_tag`, `set_field_value`, `send_flow` e as outras de [Mensagens e ações em JSON](https://docs.nextags.com.br/comecar/mensagens-e-acoes/).
    - `action` (string) [enum=['add_tag', 'remove_tag', 'set_field_value', 'unset_field_value', 'send_flow', 'transfer_conversation_to', 'assign_conversation', 'unassign_conversation'], obrigatorio]
    - `tag_name` (string) — O nome da etiqueta (add_tag, remove_tag).
    - `field_name` (string) — O nome do campo (set_field_value, unset_field_value).
    - `value` (string) — O valor do campo (set_field_value) ou human/bot (transfer_conversation_to).
    - `flow_id` (integer|string) — O ID do fluxo (send_flow).
    - `admin_id` (integer|string) — O ID do administrador (assign_conversation).
  exemplo: `{"phone": "5511988776655", "email": "ana@exemplo.com.br", "first_name": "Ana", "last_name": "Souza", "gender": "female", "actions": [{"action": "add_tag", "tag_name": "cliente-vip"}, {"action": "set_field_value", "field_name": "cidade", "value": "São Paulo"}, {"action": "send_flow", "flow_id": 1000001}]}`
- resp 200: Deu certo: o contato foi criado.
- resp 401: A chave de API não veio no cabeçalho ou não vale.

## Mensagens

### POST /contacts/{contact_id}/send/{flow_id}
`sendFlowToUser` — Enviar fluxo
Envia um fluxo ao contato, como o **Enviar Fluxo** da Caixa de Entrada: o contato recebe as mensagens e passa pelas ações do fluxo, na versão publicada. É o jeito mais completo de mandar conteúdo pela API, porque o fluxo pode ter botões, perguntas e o Modelo de Mensagem do WhatsApp. O ID do fluxo sai de [Listar fluxos](https://docs.nextags.com.br/referencia/fluxos/listar-fluxos/). Veja [Enviar um fluxo para um contato](https://docs.nextags.com.br/guias/enviar-fluxo/). No WhatsApp, a mensagem livre só sai até 24 horas depois da última mensagem do contato. Fora dessa janela, o fluxo precisa começar com um Modelo de Mensagem aprovado: veja [Modelo de mensagem do WhatsApp no fluxo](https://help.nextags.com.br/tutoriais/fluxos/modelos-no-fluxo/) e [A janela de 24 horas](https://help.nextags.com.br/tutoriais/canais/janela-de-24-horas/). Para o Instagram e o Messenger, veja [Mensagens fora da janela](https://help.nextags.com.br/tutoriais/instagram-e-facebook/mensagens-fora-da-janela/).
- path `contact_id`* (integer) — O ID do contato que recebe.
- path `flow_id`* (integer) — O ID do fluxo.
- (sem body)
- resp 200: O envio do fluxo foi aceito.
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /contacts/{contact_id}/send/text
`sendTextMessage` — Enviar texto
Envia uma mensagem de texto ao contato. Para mandar mais de uma mensagem, botões ou ações na mesma chamada, use [Enviar conteúdo](https://docs.nextags.com.br/referencia/mensagens/enviar-conteudo/). Veja [Enviar texto, imagem e arquivo](https://docs.nextags.com.br/guias/enviar-texto-e-arquivos/). No WhatsApp, a mensagem livre só sai até 24 horas depois da última mensagem do contato. Fora dessa janela, use [Enviar fluxo](https://docs.nextags.com.br/referencia/mensagens/enviar-fluxo/) com um fluxo que comece com um Modelo de Mensagem aprovado. Veja [A janela de 24 horas](https://help.nextags.com.br/tutoriais/canais/janela-de-24-horas/) e, para o Instagram e o Messenger, [Mensagens fora da janela](https://help.nextags.com.br/tutoriais/instagram-e-facebook/mensagens-fora-da-janela/).
- path `contact_id`* (integer) — O ID do contato que recebe.
- **body JSON***:
  - `text` (string) [obrigatorio] — O texto da mensagem.
  - `channel` (string) [enum=['messenger', 'whatsapp', 'webchat', 'telegram', 'instagram']] — Por qual canal a mensagem sai.
  exemplo: `{"text": "Oi, Ana! Seu pedido PED-1001 saiu para entrega.", "channel": "whatsapp"}`
- resp 200: `{success: boolean}` — O envio foi aceito.
  exemplo: `{"success": true}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /contacts/{contact_id}/send/file
`sendFile` — Enviar arquivo
Envia ao contato uma imagem, um vídeo, um áudio ou um documento, a partir do endereço do arquivo. Os formatos e os tamanhos aceitos mudam de canal para canal: veja [Tipos de arquivo e limites por canal](https://help.nextags.com.br/tutoriais/canais/tipos-de-arquivo-e-limites/) e [Enviar texto, imagem e arquivo](https://docs.nextags.com.br/guias/enviar-texto-e-arquivos/). No WhatsApp, a mensagem livre só sai até 24 horas depois da última mensagem do contato. Fora dessa janela, use [Enviar fluxo](https://docs.nextags.com.br/referencia/mensagens/enviar-fluxo/) com um fluxo que comece com um Modelo de Mensagem aprovado. Veja [A janela de 24 horas](https://help.nextags.com.br/tutoriais/canais/janela-de-24-horas/) e, para o Instagram e o Messenger, [Mensagens fora da janela](https://help.nextags.com.br/tutoriais/instagram-e-facebook/mensagens-fora-da-janela/).
- path `contact_id`* (integer) — O ID do contato que recebe.
- **body JSON***:
  - `url` (string) [obrigatorio] — O endereço público do arquivo, que abra sem login.
  - `type` (string) [enum=['file', 'image', 'audio', 'video'], obrigatorio] — O tipo do arquivo: `image` (imagem), `video` (vídeo), `audio` (áudio) ou `file` (documento).
  - `channel` (string) [enum=['messenger', 'whatsapp', 'telegram', 'instagram']] — Por qual canal o arquivo sai.
  exemplo: `{"url": "https://exemplo.com.br/arquivos/catalogo.pdf", "type": "file", "channel": "whatsapp"}`
- resp 200: `{success: boolean}` — O envio foi aceito.
  exemplo: `{"success": true}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /contacts/{contact_id}/send_content
`sendContent` — Enviar conteúdo
Envia várias mensagens e roda ações no contato, numa chamada só. As mensagens (texto, botões, respostas rápidas, mídia e cartões) e as ações (`add_tag`, `set_field_value`, `send_flow` e as outras) seguem o formato de [Mensagens e ações em JSON](https://docs.nextags.com.br/comecar/mensagens-e-acoes/), e a NexTags converte cada mensagem para o canal do contato. No WhatsApp, `messages` aceita também mensagens no formato da API do WhatsApp (lista, localização, contatos), com `"to": null`: a NexTags preenche o número. No WhatsApp, a mensagem livre só sai até 24 horas depois da última mensagem do contato. Fora dessa janela, use [Enviar fluxo](https://docs.nextags.com.br/referencia/mensagens/enviar-fluxo/) com um fluxo que comece com um Modelo de Mensagem aprovado. Veja [A janela de 24 horas](https://help.nextags.com.br/tutoriais/canais/janela-de-24-horas/) e, para o Instagram e o Messenger, [Mensagens fora da janela](https://help.nextags.com.br/tutoriais/instagram-e-facebook/mensagens-fora-da-janela/).
- path `contact_id`* (integer) — O ID do contato que recebe.
- **body JSON***:
  - `messages` (array<Mensagem>) — As mensagens, na ordem de envio.
  - `actions` (array<Acao>) — As ações para rodar no contato, na ordem da lista.
    - `action` (string) [enum=['add_tag', 'remove_tag', 'set_field_value', 'unset_field_value', 'send_flow', 'transfer_conversation_to', 'assign_conversation', 'unassign_conversation'], obrigatorio]
    - `tag_name` (string) — O nome da etiqueta (add_tag, remove_tag).
    - `field_name` (string) — O nome do campo (set_field_value, unset_field_value).
    - `value` (string) — O valor do campo (set_field_value) ou human/bot (transfer_conversation_to).
    - `flow_id` (integer|string) — O ID do fluxo (send_flow).
    - `admin_id` (integer|string) — O ID do administrador (assign_conversation).
  - `channel` (string) [enum=['messenger', 'whatsapp', 'telegram', 'instagram']] — Por qual canal as mensagens saem.
  exemplo: `{"messages": [{"message": {"text": "Oi, Ana! Seu pedido PED-1001 saiu para entrega."}}, {"message": {"attachment": {"type": "template", "payload": {"template_type": "button", "text": "Quer falar com a equipe?", "buttons": [{"type": "postback", "title": "Falar com a equipe", "payload": "1000001"}]}}}}], "actions": [{"action": "add_tag", "tag_name": "cliente-vip"}, {"action": "set_field_value", "field_name": "cidade", "value": "São Paulo"}], "channel": "whatsapp"}`
- resp 200: O envio foi aceito.
- resp 401: A chave de API não veio no cabeçalho ou não vale.

## Pipelines e oportunidades

### GET /pipelines
`getPipelines` — Listar pipelines
Lista os pipelines da conta, com o ID e o nome de cada um. É daqui que sai o `pipeline_id` das outras chamadas. A lista vem em páginas: ande por ela com `offset` e `limit`.
- query `offset` (integer) — Quantos registros pular antes do primeiro da página. Comece em 0 e some o `limit` a cada página.
- query `limit` (integer) — Quantos registros trazer por página.
- resp 200: `{data: [Pipeline]}` — Os pipelines, em `data`.
  exemplo: `{"data": [{"id": 4001, "name": "Funil de vendas"}, {"id": 4002, "name": "Onboarding de clientes"}]}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /pipelines/{pipeline_id}
`getPipeline` — Consultar pipeline
Devolve um pipeline pelo ID: o ID e o nome. As colunas do quadro vêm em [Listar etapas do pipeline](https://docs.nextags.com.br/referencia/pipelines/listar-etapas-do-pipeline/).
- path `pipeline_id`* (integer) — O ID do pipeline (veja [Listar pipelines](https://docs.nextags.com.br/referencia/pipelines/listar-pipelines/)).
- resp 200: `{id: integer, name: string}` — O pipeline.
  exemplo: `{"id": 4001, "name": "Funil de vendas"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /pipelines/{pipeline_id}/stages
`getPipelineStages` — Listar etapas do pipeline
Lista as etapas do pipeline (as colunas do quadro), com o ID e o nome de cada uma. O ID da etapa vai em `stage_id`, para criar a oportunidade numa etapa ou mudá-la de etapa, e em `target_stage_id`, para transferir. Veja [Etapas: criar, ordenar e configurar](https://help.nextags.com.br/tutoriais/pipelines/etapas/).
- path `pipeline_id`* (integer) — O ID do pipeline (veja [Listar pipelines](https://docs.nextags.com.br/referencia/pipelines/listar-pipelines/)).
- resp 200: `{data: [PipelineStage]}` — As etapas, em `data`.
  exemplo: `{"data": [{"id": 4101, "name": "Novo lead"}, {"id": 4102, "name": "Proposta enviada"}, {"id": 4103, "name": "Fechamento"}]}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /pipelines/{pipeline_id}/custom_fields
`getPipelineCustomFields` — Listar campos do pipeline
Lista os campos do pipeline: os campos próprios das oportunidades, criados nas definições do pipeline em **Campo Personalizados**. Não são os campos personalizados do contato. Use o `id` ou o `name` deles em `custom_fields`, ao criar ou atualizar uma oportunidade. Veja [Comentários, anexos e campos do pipeline](https://help.nextags.com.br/tutoriais/pipelines/comentarios-e-anexos/).
- path `pipeline_id`* (integer) — O ID do pipeline (veja [Listar pipelines](https://docs.nextags.com.br/referencia/pipelines/listar-pipelines/)).
- resp 200: `[{id: integer, name: string, type: integer|string, description: string}]` — A lista de campos, sem `data` em volta.
  exemplo: `[{"id": 3201, "name": "Origem do lead", "type": 0, "description": ""}, {"id": 3202, "name": "Previsão de fechamento", "type": 2, "description": ""}]`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /pipelines/{pipeline_id}/opportunities
`pipelinesGetCards` — Listar oportunidades
Lista as oportunidades de um pipeline, em páginas (`offset` e `limit`). Com `contact_id`, traz só as de um contato: o jeito de saber se o cliente já tem uma oportunidade aberta antes de criar outra.
- path `pipeline_id`* (integer) — O ID do pipeline (veja [Listar pipelines](https://docs.nextags.com.br/referencia/pipelines/listar-pipelines/)).
- query `contact_id` (number) — O ID de um contato: traz só as oportunidades dele.
- query `offset` (integer) — Quantos registros pular antes do primeiro da página. Comece em 0 e some o `limit` a cada página.
- query `limit` (integer) — Quantos registros trazer por página.
- resp 200: `{data: [Opportunity]}` — As oportunidades, em `data`.
  exemplo: `{"data": [{"id": 4201, "contact_id": 123456789, "title": "Plano Pro anual", "description": "Quer começar em novembro, com 3 atendentes.", "value": 1500, "status": "open", "priority": "high", "stage": {"id": 4101, "name": "Novo lead"}, "assigned_admins": [10001], "created_at": "2026-10-20 14:30:00", "created_by": 10001, "updated_at": "2026-10-22 18:05:00", "updated_by": 10001}]}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /pipelines/{pipeline_id}/opportunities
`pipelinesAddCard` — Criar oportunidade
Cria uma oportunidade (ou um ticket, nos pipelines de suporte) para um contato. Sem `stage_id`, ela entra na primeira etapa do pipeline. Os IDs vêm de [Listar etapas do pipeline](https://docs.nextags.com.br/referencia/pipelines/listar-etapas-do-pipeline/), [Listar administradores](https://docs.nextags.com.br/referencia/conta/listar-administradores/) e [Listar campos do pipeline](https://docs.nextags.com.br/referencia/pipelines/listar-campos-do-pipeline/). Veja o guia [Criar e mover oportunidades no pipeline](https://docs.nextags.com.br/guias/oportunidades-no-pipeline/).
- path `pipeline_id`* (integer) — O ID do pipeline (veja [Listar pipelines](https://docs.nextags.com.br/referencia/pipelines/listar-pipelines/)).
- **body JSON***:
  - `contact_id` (integer) [obrigatorio] — O ID do contato dono da oportunidade.
  - `title` (string) [obrigatorio] — O nome da oportunidade (o **Nome da Oportunidade** da tela), como "Plano Pro anual".
  - `description` (string) — A descrição (a **Descrição da Oportunidade**).
  - `stage_id` (integer) — O ID da etapa onde a oportunidade entra. Sem ele, a primeira etapa do pipeline.
  - `value` (number) [default=0] — O **Valor da Oportunidade**, na moeda da conta. Não é em centavos: `1500` = R$ 1.500,00.
  - `status` (string) [enum=['open', 'won', 'lost'], default=open] — O **Estado**: `open` (Aberto), `won` (Ganho) ou `lost` (Perdido). Nos pipelines de suporte e nos personalizados, `won` aparece como **Resolvido** e `lost` como **Não Resolvido**.
  - `priority` (string) [enum=['low', 'medium', 'high'], default=medium] — A **Prioridade**: `low` (Baixa), `medium` (Média) ou `high` (Alta).
  - `assigned_admins` (array<integer>) [default=[]] — Os **Administradores atribuídos**: uma lista de IDs de administradores (veja [Listar administradores](https://docs.nextags.com.br/referencia/conta/listar-administradores/)).
  - `custom_fields` (array<object>) — Os valores dos campos do pipeline (veja [Listar campos do pipeline](https://docs.nextags.com.br/referencia/pipelines/listar-campos-do-pipeline/)). Cada item leva o `id` ou o `name` do campo e o `value`.
    - `id` (integer) — O ID do campo do pipeline.
    - `name` (string) — O nome do campo do pipeline, no lugar do `id`.
    - `value` (string|number) — O valor do campo: texto ou número, conforme o tipo.
  exemplo: `{"contact_id": 123456789, "title": "Plano Pro anual", "description": "Quer começar em novembro, com 3 atendentes.", "stage_id": 4101, "value": 1500, "status": "open", "priority": "high", "assigned_admins": [10001], "custom_fields": [{"id": 3201, "value": "Anúncio no Instagram"}]}`
- resp 200: `{data: [Opportunity]}` — A oportunidade criada, em `data`.
  exemplo: `{"data": [{"id": 4201, "contact_id": 123456789, "title": "Plano Pro anual", "description": "Quer começar em novembro, com 3 atendentes.", "value": 1500, "status": "open", "priority": "high", "stage": {"id": 4101, "name": "Novo lead"}, "assigned_admins": [10001], "created_at": "2026-10-20 14:30:00", "created_by": 10001, "updated_at": "2026-10-22 18:05:00", "updated_by": 10001}]}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /pipelines/{pipeline_id}/opportunities/{opportunity_id}
`pipelinesGetCard` — Consultar oportunidade
Devolve uma oportunidade: o contato, o título, o valor, o estado, a prioridade, a etapa, os responsáveis e as datas.
- path `pipeline_id`* (integer) — O ID do pipeline (veja [Listar pipelines](https://docs.nextags.com.br/referencia/pipelines/listar-pipelines/)).
- path `opportunity_id`* (integer) — O ID da oportunidade (veja [Listar oportunidades](https://docs.nextags.com.br/referencia/pipelines/listar-oportunidades/)).
- resp 200: `{id: integer, contact_id: integer, title: string, description: string, value: number, status: string, priority: string, stage: {id: integer, name: string}, assigned_admins: [integer], created_at: string, created_by: integer, updated_at: string, updated_by: integer}` — A oportunidade.
  exemplo: `{"id": 4201, "contact_id": 123456789, "title": "Plano Pro anual", "description": "Quer começar em novembro, com 3 atendentes.", "value": 1500, "status": "open", "priority": "high", "stage": {"id": 4101, "name": "Novo lead"}, "assigned_admins": [10001], "created_at": "2026-10-20 14:30:00", "created_by": 10001, "updated_at": "2026-10-22 18:05:00", "updated_by": 10001}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /pipelines/{pipeline_id}/opportunities/{opportunity_id}
`pipelinesUpdateCard` — Atualizar oportunidade
Muda uma oportunidade: o título, a descrição, a etapa, o valor, o estado, a prioridade, os responsáveis e os campos do pipeline. Para mudar de etapa, mande o `stage_id` novo; para fechar, o `status` com `won` (ganha) ou `lost` (perdida); para reabrir, `open`. O `title` vai sempre, mesmo quando não muda. Veja [Valor, prioridade, vencimento e responsáveis](https://help.nextags.com.br/tutoriais/pipelines/campos-do-card/).
- path `pipeline_id`* (integer) — O ID do pipeline (veja [Listar pipelines](https://docs.nextags.com.br/referencia/pipelines/listar-pipelines/)).
- path `opportunity_id`* (integer) — O ID da oportunidade (veja [Listar oportunidades](https://docs.nextags.com.br/referencia/pipelines/listar-oportunidades/)).
- **body JSON***:
  - `title` (string) [obrigatorio] — O nome da oportunidade. Vai sempre: mande o atual quando não for mudar.
  - `description` (string) — A descrição (a **Descrição da Oportunidade**).
  - `stage_id` (integer) — O ID da etapa para onde a oportunidade vai.
  - `value` (number) [default=0] — O **Valor da Oportunidade**, na moeda da conta. Não é em centavos: `1500` = R$ 1.500,00.
  - `status` (string) [enum=['open', 'won', 'lost'], default=open] — O **Estado**: `open` (Aberto), `won` (Ganho) ou `lost` (Perdido). Nos pipelines de suporte e nos personalizados, `won` aparece como **Resolvido** e `lost` como **Não Resolvido**.
  - `priority` (string) [enum=['low', 'medium', 'high'], default=medium] — A **Prioridade**: `low` (Baixa), `medium` (Média) ou `high` (Alta).
  - `assigned_admins` (array<integer>) [default=[]] — Os **Administradores atribuídos**: uma lista de IDs de administradores (veja [Listar administradores](https://docs.nextags.com.br/referencia/conta/listar-administradores/)).
  - `custom_fields` (array<object>) — Os valores dos campos do pipeline (veja [Listar campos do pipeline](https://docs.nextags.com.br/referencia/pipelines/listar-campos-do-pipeline/)). Cada item leva o `id` ou o `name` do campo e o `value`.
    - `id` (integer) — O ID do campo do pipeline.
    - `name` (string) — O nome do campo do pipeline, no lugar do `id`.
    - `value` (string|number) — O valor do campo: texto ou número, conforme o tipo.
  exemplo: `{"title": "Plano Pro anual", "stage_id": 4103, "status": "won", "value": 1800, "custom_fields": [{"name": "Origem do lead", "value": "Indicação"}]}`
- resp 200: `{success: boolean}` — A oportunidade foi atualizada.
  exemplo: `{"success": true}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### DELETE /pipelines/{pipeline_id}/opportunities/{opportunity_id}
`pipelinesDeleteCard` — Apagar oportunidade
Apaga a oportunidade do pipeline, como o **Excluir** do menu do cartão.
- path `pipeline_id`* (integer) — O ID do pipeline (veja [Listar pipelines](https://docs.nextags.com.br/referencia/pipelines/listar-pipelines/)).
- path `opportunity_id`* (integer) — O ID da oportunidade (veja [Listar oportunidades](https://docs.nextags.com.br/referencia/pipelines/listar-oportunidades/)).
- resp 200: `{success: boolean}` — A oportunidade foi apagada.
  exemplo: `{"success": true}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /pipelines/{pipeline_id}/opportunities/{opportunity_id}/transfer-to-pipeline
`pipelinesTransferCard` — Transferir oportunidade de pipeline
Leva a oportunidade para outro pipeline, numa etapa escolhida, como o **Transferir para o Pipeline** do cartão. A etapa é do pipeline de destino: pegue o ID dela em [Listar etapas do pipeline](https://docs.nextags.com.br/referencia/pipelines/listar-etapas-do-pipeline/), com o ID do pipeline novo. Veja [Oportunidades e tickets](https://help.nextags.com.br/tutoriais/pipelines/oportunidades/).
- path `pipeline_id`* (integer) — O ID do pipeline onde a oportunidade está agora.
- path `opportunity_id`* (integer) — O ID da oportunidade (veja [Listar oportunidades](https://docs.nextags.com.br/referencia/pipelines/listar-oportunidades/)).
- **body JSON***:
  - `target_pipeline_id` (integer) [obrigatorio] — O ID do pipeline de destino.
  - `target_stage_id` (integer) [obrigatorio] — O ID da etapa do pipeline de destino onde a oportunidade entra.
  exemplo: `{"target_pipeline_id": 4002, "target_stage_id": 4111}`
- resp 200: `{success: boolean}` — A oportunidade mudou de pipeline.
  exemplo: `{"success": true}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /pipelines/{pipeline_id}/opportunities/{opportunity_id}/comments
`pipelinesGetComments` — Listar comentários da oportunidade
Lista os comentários de uma oportunidade (a seção **Comentários** do cartão), em páginas (`offset` e `limit`). Veja [Comentários, anexos e campos do pipeline](https://help.nextags.com.br/tutoriais/pipelines/comentarios-e-anexos/).
- path `pipeline_id`* (integer) — O ID do pipeline (veja [Listar pipelines](https://docs.nextags.com.br/referencia/pipelines/listar-pipelines/)).
- path `opportunity_id`* (integer) — O ID da oportunidade (veja [Listar oportunidades](https://docs.nextags.com.br/referencia/pipelines/listar-oportunidades/)).
- query `offset` (integer) — Quantos registros pular antes do primeiro da página. Comece em 0 e some o `limit` a cada página.
- query `limit` (integer) — Quantos registros trazer por página.
- resp 200: `{data: [OpportunityComment]}` — Os comentários, em `data`.
  exemplo: `{"data": [{"id": 4301, "data": "Proposta enviada por e-mail: Plano Pro anual com 10% de desconto.", "created_at": "2026-10-21 13:15:00", "created_by": 10001}]}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /pipelines/{pipeline_id}/opportunities/{opportunity_id}/comments
`pipelinesAddComment` — Comentar na oportunidade
Escreve um comentário na oportunidade, como o **Adicionar Comentário** do cartão. Serve para registrar no pipeline o que aconteceu no seu sistema, como uma proposta enviada ou um pagamento.
- path `pipeline_id`* (integer) — O ID do pipeline (veja [Listar pipelines](https://docs.nextags.com.br/referencia/pipelines/listar-pipelines/)).
- path `opportunity_id`* (integer) — O ID da oportunidade (veja [Listar oportunidades](https://docs.nextags.com.br/referencia/pipelines/listar-oportunidades/)).
- **body JSON***:
  - `content` (string) [obrigatorio] — O texto do comentário.
  exemplo: `{"content": "Proposta enviada por e-mail: Plano Pro anual com 10% de desconto."}`
- resp 200: `{id: integer, data: string, created_at: string, created_by: integer}` — O comentário criado.
  exemplo: `{"id": 4301, "data": "Proposta enviada por e-mail: Plano Pro anual com 10% de desconto.", "created_at": "2026-10-21 13:15:00", "created_by": 10001}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### DELETE /pipelines/{pipeline_id}/opportunities/{opportunity_id}/comments/{comment_id}
`pipelinesDeleteComment` — Apagar comentário
Apaga um comentário da oportunidade, como o **Excluir** do menu do comentário.
- path `pipeline_id`* (integer) — O ID do pipeline (veja [Listar pipelines](https://docs.nextags.com.br/referencia/pipelines/listar-pipelines/)).
- path `opportunity_id`* (integer) — O ID da oportunidade (veja [Listar oportunidades](https://docs.nextags.com.br/referencia/pipelines/listar-oportunidades/)).
- path `comment_id`* (integer) — O ID do comentário (veja [Listar comentários da oportunidade](https://docs.nextags.com.br/referencia/pipelines/listar-comentarios-da-oportunidade/)).
- resp 200: `{success: boolean}` — O comentário foi apagado.
  exemplo: `{"success": true}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

## Agentes de IA

### POST /contacts/{contact_id}/ai/save_messages
`aiSaveMessages` — Salvar mensagens no histórico da IA
Põe mensagens no histórico de conversa que a IA guarda do contato, sem enviar nada a ele. Use para dar contexto à IA sobre uma conversa que aconteceu fora da NexTags, como um atendimento por telefone, por e-mail ou na loja: nas próximas respostas, ela já sabe o que foi dito. Nos fluxos, a ação **Excluir histórico de mensagens** apaga o histórico da IA do contato; veja [Chamar a IA no fluxo](https://help.nextags.com.br/tutoriais/fluxos/ia-no-fluxo/).
- path `contact_id`* (integer) — O ID do contato.
- **body JSON***:
  - `messages` (array<object>) — As mensagens, na ordem em que aconteceram.
    - `text` (string) [obrigatorio] — O texto da mensagem.
    - `type` (string) [enum=['text', 'image', 'file', 'audio']] — O tipo: `text` (texto), `image` (imagem), `file` (arquivo) ou `audio` (áudio).
    - `role` (string) [enum=['assistant', 'user', 'developer'], obrigatorio] — Quem falou: `user` (o contato), `assistant` (a IA ou a sua equipe, respondendo) ou `developer` (uma instrução para a IA, que não é fala de ninguém).
  exemplo: `{"messages": [{"role": "user", "type": "text", "text": "Liguei ontem para trocar o tamanho do tênis do pedido PED-1001."}, {"role": "assistant", "type": "text", "text": "Combinado, Ana! A troca para o 38 foi aberta e o novo par sai amanhã."}]}`
- resp 200: As mensagens entraram no histórico da IA do contato.
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /agents/
`getAIAgents` — Listar agentes de IA
Lista os agentes de IA da conta (a aba **Agentes de IA** do AI Hub), com o ID e o nome de cada um. O endereço termina com barra: `/agents/`. Veja [Conheça o AI Hub](https://help.nextags.com.br/tutoriais/ia/ia-hub/).
- resp 200: `{data: [Agent]}` — Os agentes, em `data`.
  exemplo: `{"data": [{"id": 5001, "name": "Bia - Loja Exemplo", "created_by": 10001, "created_at": "2026-09-15 13:20:00"}, {"id": 5002, "name": "Suporte pós-venda", "created_by": 10001, "created_at": "2026-10-02 17:45:00"}]}`
- resp 400: Parâmetros inválidos.
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /agents/{agent_id}
`getAIById` — Consultar agente de IA
Devolve um agente de IA pelo ID: o nome, quem criou e quando. Veja [Criar um agente de IA](https://help.nextags.com.br/tutoriais/ia/criar-agente/).
- path `agent_id`* (integer) — O ID do agente (veja [Listar agentes de IA](https://docs.nextags.com.br/referencia/agentes-de-ia/listar-agentes-de-ia/)).
- resp 200: `{id: integer, name: string, created_by: integer, created_at: string}` — O agente.
  exemplo: `{"id": 5001, "name": "Bia - Loja Exemplo", "created_by": 10001, "created_at": "2026-09-15 13:20:00"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /agents/{agent_id}
`updateAIById` — Atualizar agente de IA
Muda a configuração de um agente: a **Mensagem do sistema (Prompt)**, o **Max tokens** e o modelo de cada provedor. Os três campos são opcionais. Veja [Escrever a mensagem do sistema](https://help.nextags.com.br/tutoriais/ia/escrever-o-prompt/) e [Modelo, temperatura e limite de tokens](https://help.nextags.com.br/tutoriais/ia/modelo-e-parametros/).
- path `agent_id`* (integer) — O ID do agente (veja [Listar agentes de IA](https://docs.nextags.com.br/referencia/agentes-de-ia/listar-agentes-de-ia/)).
- **body JSON***:
  - `prompt` (string) — A **Mensagem do sistema (Prompt)**: as instruções que o agente segue em todas as respostas. O texto novo substitui o atual.
  - `max_output_tokens` (integer) — O **Max tokens**: o tamanho máximo de cada resposta, em tokens. Na tela, de 1 a 32768; o agente novo vem com 2048.
  - `model` (object) — O modelo de cada provedor, os campos **Modelo (OpenAI)**, **Modelo (Gemini)**, **Modelo (Claude)**, **Modelo (xAI)** e **Modelo (DeepSeek)** dos ajustes do agente. Use o nome do modelo como o provedor chama; os exemplos são os modelos com que um agente novo começa. Mande os cinco, mesmo os de provedores que a conta não usa.
    - `openAI` (string) [obrigatorio] — O modelo da OpenAI, como `gpt-6-luna`.
    - `gemini` (string) [obrigatorio] — O modelo do Google Gemini, com o prefixo `models/`, como `models/gemini-3.5-flash-lite`.
    - `claude` (string) [obrigatorio] — O modelo do Claude, como `claude-haiku-4-5-20251001`.
    - `xAI` (string) [obrigatorio] — O modelo do xAI, como `grok-4.3`.
    - `deepseek` (string) [obrigatorio] — O modelo do DeepSeek, como `deepseek-v4-flash`.
  exemplo: `{"prompt": "Você é a Bia, atendente da Loja Exemplo. Responda em português, em até 3 frases. Quando o cliente pedir troca, passe para a equipe.", "max_output_tokens": 2048, "model": {"openAI": "gpt-6-luna", "gemini": "models/gemini-3.5-flash-lite", "claude": "claude-haiku-4-5-20251001", "xAI": "grok-4.3", "deepseek": "deepseek-v4-flash"}}`
- resp 200: `{id: integer, name: string, created_by: integer, created_at: string}` — O agente, depois da mudança.
  exemplo: `{"id": 5001, "name": "Bia - Loja Exemplo", "created_by": 10001, "created_at": "2026-09-15 13:20:00"}`
- resp 400: A mudança não foi aceita: confira os campos do corpo.
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /agents/functions
`getAIFunctions` — Listar funções dos agentes
Lista as **Funções de IA** da conta (AI Hub › **Ferramentas de IA**): as tarefas que o agente executa durante a conversa, como coletar dados e acionar um fluxo. Cada função é ligada ao agente na lista **Ferramentas de IA** do editor dele. Veja [Funções de IA: coletar dados e acionar fluxos](https://help.nextags.com.br/tutoriais/ia/funcoes-do-agente/).
- resp 200: `{data: [{id: integer, name: string, created_by: integer, created_at: string}]}` — As funções, em `data`.
  exemplo: `{"data": [{"id": 5101, "name": "agendar_horario", "created_by": 10001, "created_at": "2026-09-15 13:40:00"}]}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /agents/mcp
`getAIMCPs` — Listar servidores MCP
Lista os **Servidores MCP** da conta (AI Hub › **Ferramentas de IA**): os sistemas externos que o agente consulta pelo protocolo MCP, como o estoque de uma loja. A aba aparece com a OpenAI, o xAI, o Claude ou o Gemini conectados. Veja [Servidores MCP no agente](https://help.nextags.com.br/tutoriais/ia/mcp-no-agente/).
- resp 200: `{data: [{id: integer, name: string, created_by: integer, created_at: string}]}` — Os servidores, em `data`.
  exemplo: `{"data": [{"id": 5201, "name": "estoque_loja", "created_by": 10001, "created_at": "2026-09-20 11:00:00"}]}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /agents/files
`getAIFiles` — Listar arquivos dos agentes
Lista os **Arquivos** da conta (AI Hub › **Ferramentas de IA**): a base de conhecimento que o agente consulta para responder. A aba **Arquivos** só aparece com a OpenAI conectada. Veja [Arquivos: a base de conhecimento do agente](https://help.nextags.com.br/tutoriais/ia/base-de-conhecimento/).
- resp 200: `{data: [{id: integer, name: string, size: number, url: string, created_by: integer, created_at: string}]}` — Os arquivos, em `data`.
  exemplo: `{"data": [{"id": 5301, "name": "politica-de-trocas.pdf", "size": 248000, "url": "https://exemplo.com.br/arquivos/politica-de-trocas.pdf", "created_by": 10001, "created_at": "2026-09-16 10:00:00"}]}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

## Agenda

### GET /calendars
`getCalendars` — Listar calendários
Lista os calendários da conta, com o ID, o nome e a duração de cada um. A API não lista os agendamentos: eles ficam na aba **Agendamentos** ([Ver e cancelar agendamentos](https://help.nextags.com.br/tutoriais/agenda/ver-agendamentos/)).
- resp 200: `{data: [Calendar]}` — Os calendários, em `data`.
  exemplo: `{"data": [{"id": 8001, "name": "Avaliação gratuita", "duration": 30, "created_by": 10001, "created_at": "2026-08-01 12:00:00"}, {"id": 8002, "name": "Reunião de implantação", "duration": 60, "created_by": 10001, "created_at": "2026-08-12 15:30:00"}]}`
- resp 400: Parâmetros inválidos.
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /calendars/{calendar_id}
`getCalendarById` — Consultar calendário
Devolve um calendário pelo ID: o nome, a duração de cada agendamento, quem criou e quando. Para usar o calendário numa conversa, veja [Agendar pela conversa](https://help.nextags.com.br/tutoriais/agenda/agendar-pelo-fluxo/).
- path `calendar_id`* (integer) — O ID do calendário (veja [Listar calendários](https://docs.nextags.com.br/referencia/agenda/listar-calendarios/)).
- resp 200: `{id: integer, name: string, duration: integer, created_by: integer, created_at: string}` — O calendário.
  exemplo: `{"id": 8001, "name": "Avaliação gratuita", "duration": 30, "created_by": 10001, "created_at": "2026-08-01 12:00:00"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

## E-commerce

### POST /contacts/{contact_id}/send/products
`sendProduct` — Enviar produtos ao contato
Manda ao contato uma mensagem com um ou mais produtos do E-commerce, como o **Enviar Produtos** da Caixa de Entrada. Veja [Enviar produtos na conversa](https://help.nextags.com.br/tutoriais/ecommerce/enviar-produtos-na-conversa/). No WhatsApp, no Instagram e no Messenger, a mensagem só chega dentro da [janela de 24 horas](https://help.nextags.com.br/tutoriais/canais/janela-de-24-horas/).
- path `contact_id`* (integer) — O ID do contato.
- **body JSON***:
  - `product_id` (integer|string|array) [obrigatorio] — O produto ou os produtos: um ID (`6001`), uma lista de IDs (`[6001, 6002]`) ou IDs separados por vírgula (`"6001,6002"`).
  exemplo: `{"product_id": [6001, 6002]}`
- resp 200: O envio foi aceito.
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /contacts/{contact_id}/cart
`getUserCart` — Consultar carrinho
Devolve o carrinho do contato: os itens, a quantidade de cada um, o cupom e os totais. Os totais vêm em centavos; o `price` de cada item, não.
- path `contact_id`* (integer) — O ID do contato.
- resp 200: `{order_id: string, page_id: integer, user_id: integer, currency: string, total: integer, subtotal: integer, total_items: integer, coupon_discount: integer, coupon: string, line_items: [ProductCart], contact: Contact}` — O carrinho.
  exemplo: `{"order_id": "PED-1001", "page_id": 123456, "user_id": 123456789, "currency": "BRL", "total": 8082, "subtotal": 8980, "total_items": 2, "coupon_discount": 898, "coupon": "BEMVINDO10", "line_items": [{"id": 6001, "name": "Camiseta Básica Preta", "img": "https://exemplo.com.br/produtos/camiseta-preta.jpg", "price": 49.9, "amount": 1, "descr_min": "Camiseta 100% algodão, gola redonda.", "manufacturer": 0, "variant": "M", "user_msg": ""}, {"id": 6002, "name": "Boné Aba Curva", "img": "https://exemplo.com.br/produtos/bone.jpg", "price": 39.9, "amount": 1, "descr_min": "Boné ajustável de algodão.", "manufacturer": 0, "variant": "", "user_msg": "Embrulhar para presente."}], "contact": {"id": 123456789, "page_id": 123456, "first_name": "Ana", "last_name": "Souza", "channel": 5, "profile_pic": "https://exemplo.com.br/fotos/ana.jpg", "locale": "pt_BR", "gender": 0, "timezone": -3, "last_sent": 1792933200000, "last_delivered": 1792933202000, "last_seen": 1792933500000, "last_interaction": 1792933560000, "subscribed_date": "2026-03-10 14:22:00", "subscribed": 1, "tags": [{"id": 2001, "name": "cliente-vip"}], "custom_fields": [{"id": 3001, "name": "cidade", "type": 0, "value": "São Paulo"}]}}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### DELETE /contacts/{contact_id}/cart
`clearUserCart` — Esvaziar carrinho
Tira todos os itens do carrinho do contato, como a operação **Limpar Carrinho de Compras** da ação **Ecommerce** dos fluxos.
- path `contact_id`* (integer) — O ID do contato.
- resp 200: `{success: boolean}` — O carrinho ficou vazio.
  exemplo: `{"success": true}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /contacts/{contact_id}/pay/{order_id}
`payOrder` — Marcar pedido como pago
Marca um pedido como pago, quando o contato pagou fora da NexTags (Pix, link de pagamento, na loja). O valor recebido precisa cobrir o total do pedido. O corpo vai em formulário (`application/x-www-form-urlencoded`). Veja [Receber pagamentos no e-commerce](https://help.nextags.com.br/tutoriais/ecommerce/pagamentos/). O `amount_received` vai em centavos: R$ 80,82 = `8082`.
- path `contact_id`* (integer) — O ID do contato.
- path `order_id`* (string) — O ID do pedido (texto). Ele vem em `order_id`, no carrinho e no pedido.
- **body FORM***:
  - `amount_received` (integer) [obrigatorio] — O valor que o contato pagou, em centavos (`8082` = R$ 80,82).
  exemplo: `{"amount_received": 8082}`
- resp 200: `{success: boolean}` — O pedido foi marcado como pago.
  exemplo: `{"success": true}`
- resp 400: O `amount_received` é menor que o total do pedido.
- resp 401: A chave de API não veio no cabeçalho ou não vale.
- resp 402: O checkout falhou, e o contato recebeu uma mensagem explicando por quê.
- resp 404: O pedido não existe para este contato.

### GET /contacts/{contact_id}/order/{order_id}
`getUserOrder` — Consultar pedido
Devolve um pedido do contato, no mesmo formato do carrinho: os itens, o cupom e os totais em centavos (menos o `price` de cada item). Veja [Pedidos, cupons e vendedores](https://help.nextags.com.br/tutoriais/ecommerce/pedidos-cupons-e-vendedores/).
- path `contact_id`* (integer) — O ID do contato.
- path `order_id`* (string) — O ID do pedido (texto). Ele vem em `order_id`, no carrinho e no pedido.
- resp 200: `{order_id: string, page_id: integer, user_id: integer, currency: string, total: integer, subtotal: integer, total_items: integer, coupon_discount: integer, coupon: string, line_items: [ProductCart], contact: Contact}` — O pedido.
  exemplo: `{"order_id": "PED-1001", "page_id": 123456, "user_id": 123456789, "currency": "BRL", "total": 8082, "subtotal": 8980, "total_items": 2, "coupon_discount": 898, "coupon": "BEMVINDO10", "line_items": [{"id": 6001, "name": "Camiseta Básica Preta", "img": "https://exemplo.com.br/produtos/camiseta-preta.jpg", "price": 49.9, "amount": 1, "descr_min": "Camiseta 100% algodão, gola redonda.", "manufacturer": 0, "variant": "M", "user_msg": ""}, {"id": 6002, "name": "Boné Aba Curva", "img": "https://exemplo.com.br/produtos/bone.jpg", "price": 39.9, "amount": 1, "descr_min": "Boné ajustável de algodão.", "manufacturer": 0, "variant": "", "user_msg": "Embrulhar para presente."}], "contact": {"id": 123456789, "page_id": 123456, "first_name": "Ana", "last_name": "Souza", "channel": 5, "profile_pic": "https://exemplo.com.br/fotos/ana.jpg", "locale": "pt_BR", "gender": 0, "timezone": -3, "last_sent": 1792933200000, "last_delivered": 1792933202000, "last_seen": 1792933500000, "last_interaction": 1792933560000, "subscribed_date": "2026-03-10 14:22:00", "subscribed": 1, "tags": [{"id": 2001, "name": "cliente-vip"}], "custom_fields": [{"id": 3001, "name": "cidade", "type": 0, "value": "São Paulo"}]}}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /contacts/{contact_id}/order/{order_id}
`changeOrder` — Alterar pedido
Muda a situação de um pedido e os dados de entrega. A situação vai em `status`, pelo código: `6` **Aceito** (em processamento), `7` **Entregando** (enviado), `10` **Concluído** e `13` **Cancelado**. O **Não processado** (código 4) não pode ser escolhido aqui. Veja [Pedidos, cupons e vendedores](https://help.nextags.com.br/tutoriais/ecommerce/pedidos-cupons-e-vendedores/).
- path `contact_id`* (integer) — O ID do contato.
- path `order_id`* (string) — O ID do pedido (texto). Ele vem em `order_id`, no carrinho e no pedido.
- **body JSON***:
  - `status` (integer) [enum=[6, 7, 10, 13]] — A situação nova: `6` Aceito, `7` Entregando, `10` Concluído ou `13` Cancelado.
  - `name` (string) — O nome de quem recebe a entrega.
  - `phone` (string) — O telefone para a entrega.
  - `email` (string) — O e-mail para a entrega.
  - `country` (string) — O país da entrega.
  - `state` (string) — O estado.
  - `city` (string) — A cidade.
  - `zip_code` (string) — O CEP.
  - `address` (string) — O endereço de entrega.
  - `street_1` (string) — A primeira linha do endereço: rua e número.
  - `street_2` (string) — A segunda linha do endereço, como o complemento.
  - `note` (string) — Uma observação sobre o pedido.
  exemplo: `{"status": 7, "name": "Ana Souza", "phone": "5511988776655", "city": "São Paulo", "state": "SP", "zip_code": "01310-100", "street_1": "Av. Paulista, 1578", "street_2": "Apto 45", "note": "Entregar na portaria."}`
- resp 200: `{success: boolean}` — O pedido foi alterado.
  exemplo: `{"success": true}`
- resp 400: O `status` não é 6, 7, 10 nem 13.
- resp 401: A chave de API não veio no cabeçalho ou não vale.
- resp 402: O pedido já está nessa situação.
- resp 404: O pedido não existe para este contato.

### POST /contacts/{contact_id}/cart/{product_id}
`addProductCart` — Adicionar produto ao carrinho
Põe um produto no carrinho do contato, com a quantidade. O corpo vai em formulário (`application/x-www-form-urlencoded`), não em JSON.
- path `contact_id`* (integer) — O ID do contato.
- path `product_id`* (integer) — O ID do produto.
- **body FORM***:
  - `quantity` (integer) [obrigatorio] — Quantas unidades do produto.
  exemplo: `{"quantity": 2}`
- resp 200: `{success: boolean}` — O produto entrou no carrinho.
  exemplo: `{"success": true}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### DELETE /contacts/{contact_id}/cart/{product_id}
`removeProductCart` — Remover produto do carrinho
Tira um produto do carrinho do contato.
- path `contact_id`* (integer) — O ID do contato.
- path `product_id`* (integer) — O ID do produto.
- resp 200: `{success: boolean}` — O produto saiu do carrinho.
  exemplo: `{"success": true}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /products/{product_id}
`getProductById` — Consultar produto
Devolve um produto do E-commerce: o nome, os preços, o estoque, a categoria, a descrição curta e a imagem. Os preços vêm na moeda da loja, não em centavos. Veja [Cadastrar produtos](https://help.nextags.com.br/tutoriais/ecommerce/cadastrar-produtos/).
- path `product_id`* (integer) — O ID do produto.
- resp 200: `{id: integer, name: string, price: number, sale_price: number, category_id: integer, category_name: string, stock: integer, short_description: string, image: string, created_at: string}` — O produto.
  exemplo: `{"id": 6001, "name": "Camiseta Básica Preta", "price": 49.9, "sale_price": 39.9, "category_id": 6101, "category_name": "Camisetas", "stock": 120, "short_description": "Camiseta 100% algodão, gola redonda.", "image": "https://exemplo.com.br/produtos/camiseta-preta.jpg", "created_at": "2026-07-10 18:00:00"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /products/{product_id}
`updateProduct` — Atualizar produto
Muda o preço, o estoque e o **Ativo** de um produto, para a loja acompanhar o seu sistema de estoque. Os três campos são opcionais. Veja [Cadastrar produtos](https://help.nextags.com.br/tutoriais/ecommerce/cadastrar-produtos/).
- path `product_id`* (integer) — O ID do produto.
- **body JSON***:
  - `price` (number) — O preço novo, na moeda da loja. Não é em centavos: `44.9` = R$ 44,90.
  - `active` (boolean) — O **Ativo** da lista de produtos: `true` deixa o produto à venda; `false` tira da venda.
  - `stock` (integer) — O estoque novo (a coluna **Inventário** da lista de produtos).
  exemplo: `{"price": 44.9, "stock": 85, "active": true}`
- resp 200: `{success: boolean, updated: boolean}` — O produto foi atualizado.
  exemplo: `{"success": true, "updated": true}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

## Disparos

### GET /broadcasts
`getBroadcasts` — Listar disparos
Lista os Broadcasts da conta, com o nome, o estado e as datas de cada um. Não há chamada para criar um Broadcast: ele é criado na tela, em **Broadcasts** › **Enviar** ([Criar um Broadcast](https://help.nextags.com.br/tutoriais/disparos/criar-disparo/)).
- resp 200: `{data: [Broadcast]}` — Os Broadcasts, em `data`.
  exemplo: `{"data": [{"id": 7001, "name": "Black Friday - clientes VIP", "status": "SENT", "sent_at": "2026-10-20 15:00:00", "created_by": 10001, "created_at": "2026-10-20 14:45:00"}, {"id": 7002, "name": "Lançamento da coleção de verão", "status": "SENT", "sent_at": "2026-10-05 13:00:00", "created_by": 10001, "created_at": "2026-10-05 12:40:00"}]}`
- resp 400: Parâmetros inválidos.
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### GET /broadcasts/{broadcast_id}
`getBroadcastById` — Consultar disparo
Devolve um Broadcast pelo ID, com o estado: use para acompanhar um envio até `SENT`. Os números de entregues, vistos, cliques e falhas não vêm aqui: ficam na lista **Broadcasts** ([Resultados: entregues, abertos, clicados e falhas](https://help.nextags.com.br/tutoriais/disparos/resultados-e-custos/)).
- path `broadcast_id`* (integer) — O ID do Broadcast (veja [Listar disparos](https://docs.nextags.com.br/referencia/disparos/listar-disparos/)).
- resp 200: `{id: integer, name: string, status: string, sent_at: string, created_by: integer, created_at: string}` — O Broadcast.
  exemplo: `{"id": 7001, "name": "Black Friday - clientes VIP", "status": "SENT", "sent_at": "2026-10-20 15:00:00", "created_by": 10001, "created_at": "2026-10-20 14:45:00"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.
- resp 404: O Broadcast não existe nesta conta.

### POST /broadcasts/{broadcast_id}/resend
`resendBroadcastById` — Reenviar disparo
Manda o Broadcast de novo, como o **Reenviar** do menu da lista, que aparece em qualquer estado. Antes de reenviar, pense em quem já recebeu: mensagem repetida aumenta os bloqueios e as denúncias. Veja [Reenviar, cancelar e exportar um Broadcast](https://help.nextags.com.br/tutoriais/disparos/reenviar-e-cancelar/).
- path `broadcast_id`* (integer) — O ID do Broadcast (veja [Listar disparos](https://docs.nextags.com.br/referencia/disparos/listar-disparos/)).
- (sem body)
- resp 200: `{success: boolean}` — O reenvio foi aceito.
  exemplo: `{"success": true}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /broadcasts/{broadcast_id}/cancel
`cancelBroadcastById` — Cancelar disparo
Para um Broadcast que ainda não saiu, como o **Cancelar** do menu da lista. Na tela, o **Cancelar** só aparece enquanto o Broadcast está **Agendado**, **Pendente** ou no começo do envio; depois disso, não dá mais para parar. Cancelado, o estado vira `CANCELLED`. Veja [Reenviar, cancelar e exportar um Broadcast](https://help.nextags.com.br/tutoriais/disparos/reenviar-e-cancelar/).
- path `broadcast_id`* (integer) — O ID do Broadcast (veja [Listar disparos](https://docs.nextags.com.br/referencia/disparos/listar-disparos/)).
- (sem body)
- resp 200: `{success: boolean}` — O Broadcast foi cancelado.
  exemplo: `{"success": true}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

## Ferramentas

### POST /tools/format_number
`format_number` — Formatar número
Formata um número com as casas decimais e os separadores que você escolher: `1995.5` vira `1.995,50`. Use para mostrar um valor em reais numa mensagem.
- **body FORM***:
  - `number` (number) [obrigatorio] — O número, com ponto decimal (`1995.5`).
  - `decimals` (integer) — Quantas casas decimais, como `2`.
  - `decimal_separator` (string) — O separador decimal, como `,`.
  - `thousands_separator` (string) — O separador de milhar, como `.`.
  exemplo: `{"number": 1995.5, "decimals": 2, "decimal_separator": ",", "thousands_separator": "."}`
- resp 200: `{data: string|number}` — O número formatado, em `data`.
  exemplo: `{"data": "1.995,50"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /tools/split
`split` — Dividir um texto em partes
Divide um texto em partes a cada separador e devolve a lista e o total: `Camiseta,Boné,Meia` com o separador `,` vira três partes. No **Mapeamento de resposta**, `$.data[0]` é a primeira parte.
- **body FORM***:
  - `text` (string) [obrigatorio] — O texto.
  - `delimiter` (string) [obrigatorio] — O separador, como `,` ou `;`.
  exemplo: `{"text": "Camiseta,Boné,Meia", "delimiter": ","}`
- resp 200: `{total: integer, data: [string]}` — As partes, em `data`, e o total.
  exemplo: `{"total": 3, "data": ["Camiseta", "Boné", "Meia"]}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /tools/urlencode
`urlencode` — Codificar texto para URL
Codifica um texto para usar numa URL, no formato de formulário: o espaço vira `+`, e os acentos e os outros caracteres especiais viram `%XX`. Use no valor de um parâmetro, depois do `?`. Para `%20` no lugar do `+`, use [Codificar para URL (RFC 3986)](https://docs.nextags.com.br/referencia/ferramentas/codificar-para-url-rfc-3986/).
- **body FORM***:
  - `text` (string) [obrigatorio] — O texto.
  exemplo: `{"text": "Olá, quero o pedido PED-1001"}`
- resp 200: `{data: string}` — O texto codificado, em `data`.
  exemplo: `{"data": "Ol%C3%A1%2C+quero+o+pedido+PED-1001"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /tools/urldecode
`urldecode` — Decodificar texto de URL
Desfaz a codificação de URL: troca as sequências `%XX` pelos caracteres e o `+` por espaço. Use para ler um valor que chegou codificado, como um parâmetro de link.
- **body FORM***:
  - `text` (string) [obrigatorio] — O texto codificado.
  exemplo: `{"text": "Ol%C3%A1%2C+quero+o+pedido+PED-1001"}`
- resp 200: `{data: string}` — O texto decodificado, em `data`.
  exemplo: `{"data": "Olá, quero o pedido PED-1001"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /tools/rawurlencode
`rawurlencode` — Codificar para URL (RFC 3986)
Codifica um texto para URL pela RFC 3986: o espaço vira `%20`, e não `+`. Use quando o outro sistema não aceita o `+`, como num trecho do caminho da URL.
- **body FORM***:
  - `text` (string) [obrigatorio] — O texto.
  exemplo: `{"text": "Olá, quero o pedido PED-1001"}`
- resp 200: `{data: string}` — O texto codificado, em `data`.
  exemplo: `{"data": "Ol%C3%A1%2C%20quero%20o%20pedido%20PED-1001"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /tools/rawurldecode
`rawurldecode` — Decodificar de URL (RFC 3986)
Desfaz a codificação da RFC 3986: troca as sequências `%XX` pelos caracteres. O `+` continua `+`; para virar espaço, use [Decodificar texto de URL](https://docs.nextags.com.br/referencia/ferramentas/decodificar-texto-de-url/).
- **body FORM***:
  - `text` (string) [obrigatorio] — O texto codificado.
  exemplo: `{"text": "S%C3%A3o%20Paulo%20-%20SP"}`
- resp 200: `{data: string}` — O texto decodificado, em `data`.
  exemplo: `{"data": "São Paulo - SP"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /tools/qrcode
`qrcode` — Gerar QR Code
Gera um QR Code com o texto ou o link que você mandar e devolve o endereço da imagem, para enviar como imagem numa mensagem. Para o QR Code de um fluxo, a tela tem o [Gerador de Código QR](https://help.nextags.com.br/tutoriais/ferramentas/qr-code/).
- **body FORM***:
  - `text` (string) [obrigatorio] — O texto ou o link que vai no QR Code.
  exemplo: `{"text": "https://wa.me/5511988776655"}`
- resp 200: `{data: string}` — O endereço da imagem, em `data`.
  exemplo: `{"data": "https://exemplo.com.br/qrcode.png"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /tools/text_to_lower
`text_to_lower` — Converter texto para minúsculas
Passa o texto para letras minúsculas. Use para padronizar um e-mail antes de comparar, salvar ou gerar um hash.
- **body FORM***:
  - `text` (string) [obrigatorio] — O texto.
  exemplo: `{"text": "ANA@EXEMPLO.COM.BR"}`
- resp 200: `{data: string}` — O texto em minúsculas, em `data`.
  exemplo: `{"data": "ana@exemplo.com.br"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /tools/text_to_upper
`text_to_upper` — Converter texto para maiúsculas
Passa o texto para letras maiúsculas. Use para padronizar códigos, como o de um cupom ou de um pedido.
- **body FORM***:
  - `text` (string) [obrigatorio] — O texto.
  exemplo: `{"text": "bemvindo10"}`
- resp 200: `{data: string}` — O texto em maiúsculas, em `data`.
  exemplo: `{"data": "BEMVINDO10"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /tools/text_length
`text_length` — Contar os caracteres de um texto
Conta os caracteres de um texto. Use para conferir um dado antes de seguir, como o celular com DDI e DDD, que tem 13 dígitos no Brasil.
- **body FORM***:
  - `text` (string) [obrigatorio] — O texto.
  exemplo: `{"text": "5511988776655"}`
- resp 200: `{data: integer}` — O tamanho, em `data`.
  exemplo: `{"data": 13}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /tools/substring
`substring` — Recortar parte de um texto
Recorta um pedaço do texto: a partir da posição `offset` (o primeiro caractere é a posição 0), com `length` caracteres; sem `length`, vai até o fim. No celular `5511988776655`, o DDD está na posição 2, com 2 caracteres.
- **body FORM***:
  - `text` (string) [obrigatorio] — O texto.
  - `offset` (integer) [obrigatorio] — A posição onde o recorte começa, contando do 0.
  - `length` (integer) — Quantos caracteres recortar. Sem ele, vai até o fim do texto.
  exemplo: `{"text": "5511988776655", "offset": 2, "length": 2}`
- resp 200: `{data: string}` — O pedaço recortado, em `data`.
  exemplo: `{"data": "11"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /tools/text_replace
`text_replace` — Substituir um texto
Troca, no texto, todas as vezes que um trecho aparece por outro: com `.` trocado por `,`, o preço `49.90` vira `49,90`. Para várias trocas de uma vez, use [Substituir vários textos](https://docs.nextags.com.br/referencia/ferramentas/substituir-varios-textos/).
- **body FORM***:
  - `text` (string) [obrigatorio] — O texto.
  - `search` (string) [obrigatorio] — O trecho a procurar.
  - `replace` (string) [obrigatorio] — O que entra no lugar.
  exemplo: `{"text": "49.90", "search": ".", "replace": ","}`
- resp 200: `{data: string}` — O texto com as trocas, em `data`.
  exemplo: `{"data": "49,90"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /tools/text_replaces
`text_replaces` — Substituir vários textos
Faz várias trocas de uma vez: cada item de `search` é trocado pelo item na mesma posição de `replace`. No formulário, cada item da lista vai num par próprio, com o nome seguido de colchetes: `search[]=...&search[]=...` (veja os exemplos de código).
- **body FORM***:
  - `text` (string) [obrigatorio] — O texto.
  - `search` (array<string>) [obrigatorio] — Os trechos a procurar, na ordem.
  - `replace` (array<string>) [obrigatorio] — O que entra no lugar de cada trecho, na mesma ordem de `search`.
  exemplo: `{"text": "Olá, {nome}! Seu pedido {pedido} saiu para entrega.", "search": ["{nome}", "{pedido}"], "replace": ["Ana", "PED-1001"]}`
- resp 200: `{data: string}` — O texto com as trocas, em `data`.
  exemplo: `{"data": "Olá, Ana! Seu pedido PED-1001 saiu para entrega."}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /tools/get_url_parameters
`get_url_parameters` — Ler os parâmetros de uma URL
Lê os parâmetros de uma URL (o que vem depois do `?`) e devolve cada um com o seu valor. Use para pegar a origem de quem chegou por um link com UTM, como `utm_source` e `utm_campaign`.
- **body FORM***:
  - `url` (string) [obrigatorio] — A URL completa, com os parâmetros.
  exemplo: `{"url": "https://loja.exemplo.com.br/?utm_source=instagram&utm_campaign=black-friday&ref=ana"}`
- resp 200: `{data: object}` — Os parâmetros, em `data`: um campo para cada parâmetro da URL, com o nome e o valor.
  exemplo: `{"data": {"utm_source": "instagram", "utm_campaign": "black-friday", "ref": "ana"}}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /tools/echo
`echo` — Devolver o JSON enviado (eco)
Devolve, igual, o JSON que você mandar. Serve para gerar mensagens dinâmicas na [requisição externa](https://help.nextags.com.br/tutoriais/fluxos/requisicao-externa/) do fluxo sem ter um servidor seu: monte no corpo o JSON de [mensagens e ações](https://docs.nextags.com.br/comecar/mensagens-e-acoes/), com as variáveis do contato, e a resposta traz esse JSON de volta. Veja [Requisição externa: o fluxo chama o seu sistema](https://docs.nextags.com.br/webhooks/requisicao-externa-no-fluxo/).
- **body JSON***:
  - `messages` (array<Mensagem>) — Por exemplo, as mensagens do conteúdo dinâmico. O eco aceita qualquer JSON e devolve igual: estes campos são só o uso mais comum.
  - `actions` (array<Acao>) — Por exemplo, as ações do conteúdo dinâmico.
    - `action` (string) [enum=['add_tag', 'remove_tag', 'set_field_value', 'unset_field_value', 'send_flow', 'transfer_conversation_to', 'assign_conversation', 'unassign_conversation'], obrigatorio]
    - `tag_name` (string) — O nome da etiqueta (add_tag, remove_tag).
    - `field_name` (string) — O nome do campo (set_field_value, unset_field_value).
    - `value` (string) — O valor do campo (set_field_value) ou human/bot (transfer_conversation_to).
    - `flow_id` (integer|string) — O ID do fluxo (send_flow).
    - `admin_id` (integer|string) — O ID do administrador (assign_conversation).
  exemplo: `{"messages": [{"message": {"text": "Oi, Ana! Seu pedido PED-1001 saiu para entrega."}}], "actions": [{"action": "add_tag", "tag_name": "cliente-vip"}]}`
- resp 200: `{messages: [Mensagem], actions: [Acao]}` — O mesmo JSON que veio no corpo.
  exemplo: `{"messages": [{"message": {"text": "Oi, Ana! Seu pedido PED-1001 saiu para entrega."}}], "actions": [{"action": "add_tag", "tag_name": "cliente-vip"}]}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /tools/hash
`hash` — Gerar um hash
Gera o hash de um texto com o algoritmo escolhido; sem `algo`, usa o SHA-256. Use, por exemplo, para mandar o e-mail do contato com hash SHA-256, como a API de Conversões da Meta pede (antes, passe o e-mail para minúsculas com [Converter texto para minúsculas](https://docs.nextags.com.br/referencia/ferramentas/converter-texto-para-minusculas/)).
- **body FORM***:
  - `data` (string) [obrigatorio] — O texto.
  - `algo` (string) [default=sha256] — O algoritmo, como `sha256`, `sha1` ou `md5`. Sem ele, `sha256`.
  exemplo: `{"data": "ana@exemplo.com.br", "algo": "sha256"}`
- resp 200: `{data: string}` — O hash, em `data`.
  exemplo: `{"data": "9908ab973926622870fbcc257bf5c75e507d89d24698137563dab84b1e2cb423"}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

### POST /tools/location_distance
`location_distance` — Calcular a distância entre duas coordenadas
Calcula a distância entre dois pontos de latitude e longitude, em metros e em milhas. Use para saber se o contato está na área de entrega ou para calcular o frete a partir da localização que ele mandou ([Pedir e enviar localização](https://help.nextags.com.br/tutoriais/fluxos/localizacao/)). Com uma chave da API do Google Maps em `googleMapsApiKey`, o cálculo é feito pelo Google Maps.
- **body FORM***:
  - `source_latitude` (number) [obrigatorio] — A latitude do ponto de partida, com ponto decimal (`-23.5614`).
  - `source_longitude` (number) [obrigatorio] — A longitude do ponto de partida (`-46.6559`).
  - `destination_latitude` (number) [obrigatorio] — A latitude do destino.
  - `destination_longitude` (number) [obrigatorio] — A longitude do destino.
  - `googleMapsApiKey` (string) — Opcional: uma chave da API do Google Maps. Com ela, a distância é calculada pelo Google Maps.
  exemplo: `{"source_latitude": -23.5614, "source_longitude": -46.6559, "destination_latitude": -23.5505, "destination_longitude": -46.6333}`
- resp 200: `{meters: number, miles: number}` — A distância, em metros e em milhas.
  exemplo: `{"meters": 2603, "miles": 1.617424}`
- resp 401: A chave de API não veio no cabeçalho ou não vale.

## Modelos

### Admin
- `id` (integer) — O ID do administrador.
- `email` (string) — O e-mail de acesso.
- `first_name` (string) — O nome.
- `last_name` (string) — O sobrenome.
- `full_name` (string) — O nome completo.
- `profile_pic` (string) — O endereço da foto do perfil.
- `available` (boolean) — Se a pessoa está como **Disponível** para receber conversas.

### Team
- `id` (integer) — O ID da equipe.
- `name` (string) — O nome da equipe.

### Tag
- `id` (integer) — O ID da etiqueta.
- `name` (string) — O nome da etiqueta.

### Contact
- `id` (integer) — O ID do contato: o `contact_id` das outras chamadas.
- `page_id` (integer) — O ID da conta.
- `first_name` (string) — O nome.
- `last_name` (string) — O sobrenome.
- `channel` (integer) — O canal atual do contato: 0 Messenger, 5 WhatsApp, 8 Telegram, 9 Webchat, 10 Instagram, 17 TikTok.
- `profile_pic` (string) — O endereço da foto de perfil.
- `locale` (string) — O idioma do contato, como `pt_BR`.
- `gender` (integer) — O gênero: 0 feminino, 1 masculino, 2 desconhecido.
- `timezone` (integer) — O fuso horário do contato, em horas em relação ao UTC (-3 em Brasília).
- `last_sent` (integer) — Quando a última mensagem foi enviada ao contato, em Unix timestamp em milissegundos.
- `last_delivered` (integer) — Quando a última mensagem foi entregue ao contato, em Unix timestamp em milissegundos.
- `last_seen` (integer) — Quando o contato foi visto pela última vez (**Visto pela última vez**, no app), em Unix timestamp em milissegundos.
- `last_interaction` (integer) — Quando o contato interagiu com a conta pela última vez, em Unix timestamp em milissegundos.
- `subscribed_date` (string) — Quando o contato entrou na conta, em UTC, no formato `2026-10-12 14:40:00`.
- `subscribed` (integer) — 1 inscrito; 2 inscrição cancelada (o contato saiu das transmissões e não recebe Broadcasts). Veja [Contatos que pediram para sair das transmissões](https://help.nextags.com.br/tutoriais/contatos/cancelar-inscricao/).
- `tags` (array<Tag>) — As etiquetas do contato.
  - `id` (integer) — O ID da etiqueta.
  - `name` (string) — O nome da etiqueta.
- `custom_fields` (array<Custom_field>) — Os campos personalizados do contato, com o valor de cada um.
  - `id` (integer) — O ID do campo.
  - `name` (string) — O nome do campo.
  - `type` (integer) [enum=[0, 1, 2, 3, 4, 5, 6, 7]] — O tipo: 0 texto, 1 número, 2 data, 3 data e hora, 4 sim/não, 5 texto longo, 6 seleção única, 7 seleção múltipla.
  - `value` (string|number) — O valor do contato, no formato do tipo: texto nos campos de texto e de texto longo; número nos de número, de data e de data e hora (Unix timestamp, em segundos) e de sim/não (1 ou 0).

### Acao
- `action` (string) [enum=['add_tag', 'remove_tag', 'set_field_value', 'unset_field_value', 'send_flow', 'transfer_conversation_to', 'assign_conversation', 'unassign_conversation'], obrigatorio]
- `tag_name` (string) — O nome da etiqueta (add_tag, remove_tag).
- `field_name` (string) — O nome do campo (set_field_value, unset_field_value).
- `value` (string) — O valor do campo (set_field_value) ou human/bot (transfer_conversation_to).
- `flow_id` (integer|string) — O ID do fluxo (send_flow).
- `admin_id` (integer|string) — O ID do administrador (assign_conversation).

### Custom_field
- `id` (integer) — O ID do campo.
- `name` (string) — O nome do campo.
- `type` (integer) [enum=[0, 1, 2, 3, 4, 5, 6, 7]] — O tipo: 0 texto, 1 número, 2 data, 3 data e hora, 4 sim/não, 5 texto longo, 6 seleção única, 7 seleção múltipla.
- `value` (string|number) — O valor do contato, no formato do tipo: texto nos campos de texto e de texto longo; número nos de número, de data e de data e hora (Unix timestamp, em segundos) e de sim/não (1 ou 0).

### Mensagem

### Pipeline
- `id` (integer) — O ID do pipeline.
- `name` (string) — O nome do pipeline.

### PipelineStage
- `id` (integer) — O ID da etapa: o `stage_id` das oportunidades.
- `name` (string) — O nome da etapa.

### Opportunity
- `id` (integer) — O ID da oportunidade.
- `contact_id` (integer) — O ID do contato.
- `title` (string) — O nome da oportunidade.
- `description` (string) — A descrição.
- `value` (number) — O valor, na moeda da conta. Não é em centavos: `1500` = R$ 1.500,00.
- `status` (string) [enum=['open', 'won', 'lost']] — O estado: `open` (Aberto), `won` (Ganho; Resolvido nos pipelines de suporte e nos personalizados) ou `lost` (Perdido; Não Resolvido).
- `priority` (string) [enum=['low', 'medium', 'high']] — A prioridade: `low` (Baixa), `medium` (Média) ou `high` (Alta).
- `stage` (object) — A etapa onde a oportunidade está.
  - `id` (integer) — O ID da etapa.
  - `name` (string) — O nome da etapa.
- `assigned_admins` (array<integer>) — Os IDs dos administradores atribuídos.
- `created_at` (string) — Quando a oportunidade foi criada, em UTC.
- `created_by` (integer) — O ID do administrador que criou.
- `updated_at` (string) — A última mudança, em UTC.
- `updated_by` (integer) — O ID do administrador que fez a última mudança.

### OpportunityComment
- `id` (integer) — O ID do comentário.
- `data` (string) — O texto do comentário.
- `created_at` (string) — Quando o comentário foi escrito, em UTC.
- `created_by` (integer) — O ID do administrador que escreveu.

### Agent
- `id` (integer) — O ID do agente.
- `name` (string) — O nome do agente, como aparece na lista do AI Hub.
- `created_by` (integer) — O ID do administrador que criou.
- `created_at` (string) — Quando o agente foi criado, em UTC.

### Calendar
- `id` (integer) — O ID do calendário.
- `name` (string) — O nome do calendário.
- `duration` (integer) — A **Duração do evento**: quanto dura cada agendamento, em minutos (na tela, de 5 minutos a 23 horas).
- `created_by` (integer) — O ID do administrador que criou.
- `created_at` (string) — Quando o calendário foi criado, em UTC.

### Cart
- `order_id` (string) — O ID do pedido (texto).
- `page_id` (integer) — O ID da conta.
- `user_id` (integer) — O ID do contato.
- `currency` (string) — A moeda da loja, como `BRL`.
- `total` (integer) — O total, em centavos.
- `subtotal` (integer) — A soma dos itens, em centavos.
- `total_items` (integer) — Quantos itens o carrinho tem.
- `coupon_discount` (integer) — O desconto do cupom, em centavos.
- `coupon` (string) — O código do cupom aplicado (o **Código de desconto** da aba **Cupons**).
- `line_items` (array<ProductCart>) — Os itens do carrinho.
  - `id` (integer) — O ID do produto.
  - `name` (string) — O nome do produto.
  - `img` (string) — O endereço da imagem do produto.
  - `price` (number) — O preço de uma unidade, na moeda da loja. Não é em centavos: `49.9` = R$ 49,90.
  - `amount` (integer) — A quantidade.
  - `descr_min` (string) — A descrição curta do produto.
  - `manufacturer` (integer) — O ID do vendedor do produto (aba **Vendedores**).
  - `variant` (string) — A variante escolhida, como o tamanho ou a cor.
  - `user_msg` (string) — O pedido especial que o contato anotou no item, quando o produto permite anexar notas.
- `contact` (Contact) — Uma pessoa que fala com a conta, com o canal, os dados do perfil, as datas da conversa, as etiquetas e os campos personalizados.
  - `id` (integer) — O ID do contato: o `contact_id` das outras chamadas.
  - `page_id` (integer) — O ID da conta.
  - `first_name` (string) — O nome.
  - `last_name` (string) — O sobrenome.
  - `channel` (integer) — O canal atual do contato: 0 Messenger, 5 WhatsApp, 8 Telegram, 9 Webchat, 10 Instagram, 17 TikTok.
  - `profile_pic` (string) — O endereço da foto de perfil.
  - `locale` (string) — O idioma do contato, como `pt_BR`.
  - `gender` (integer) — O gênero: 0 feminino, 1 masculino, 2 desconhecido.
  - `timezone` (integer) — O fuso horário do contato, em horas em relação ao UTC (-3 em Brasília).
  - `last_sent` (integer) — Quando a última mensagem foi enviada ao contato, em Unix timestamp em milissegundos.
  - `last_delivered` (integer) — Quando a última mensagem foi entregue ao contato, em Unix timestamp em milissegundos.
  - `last_seen` (integer) — Quando o contato foi visto pela última vez (**Visto pela última vez**, no app), em Unix timestamp em milissegundos.
  - `last_interaction` (integer) — Quando o contato interagiu com a conta pela última vez, em Unix timestamp em milissegundos.
  - `subscribed_date` (string) — Quando o contato entrou na conta, em UTC, no formato `2026-10-12 14:40:00`.
  - `subscribed` (integer) — 1 inscrito; 2 inscrição cancelada (o contato saiu das transmissões e não recebe Broadcasts). Veja [Contatos que pediram para sair das transmissões](https://help.nextags.com.br/tutoriais/contatos/cancelar-inscricao/).
  - `tags` (array<Tag>) — As etiquetas do contato.
    - `id` (integer) — O ID da etiqueta.
    - `name` (string) — O nome da etiqueta.
  - `custom_fields` (array<Custom_field>) — Os campos personalizados do contato, com o valor de cada um.
    - `id` (integer) — O ID do campo.
    - `name` (string) — O nome do campo.
    - `type` (integer) [enum=[0, 1, 2, 3, 4, 5, 6, 7]] — O tipo: 0 texto, 1 número, 2 data, 3 data e hora, 4 sim/não, 5 texto longo, 6 seleção única, 7 seleção múltipla.
    - `value` (string|number) — O valor do contato, no formato do tipo: texto nos campos de texto e de texto longo; número nos de número, de data e de data e hora (Unix timestamp, em segundos) e de sim/não (1 ou 0).

### Product
- `id` (integer) — O ID do produto.
- `name` (string) — O nome do produto.
- `price` (number) — O preço, como na coluna **Preço** da lista (`49.9` = R$ 49,90).
- `sale_price` (number) — O preço promocional.
- `category_id` (integer) — O ID da categoria (aba **Categorias**).
- `category_name` (string) — O nome da categoria.
- `stock` (integer) — O estoque, como na coluna **Inventário** da lista.
- `short_description` (string) — A descrição curta.
- `image` (string) — O endereço da imagem.
- `created_at` (string) — Quando o produto foi criado, em UTC.

### Broadcast
- `id` (integer) — O ID do Broadcast.
- `name` (string) — O nome do Broadcast, como na coluna **Nome** da lista.
- `status` (string) [enum=['DRAFT', 'NOT_SENT', 'SENTING', 'SENT', 'CANCELLED']] — O estado: `DRAFT` (rascunho; *Draft* na lista), `NOT_SENT` (ainda não saiu, como um Broadcast **Pendente** ou **Agendado**), `SENTING` (**Enviando**; o nome é escrito assim mesmo), `SENT` (**Enviado**) ou `CANCELLED` (**Cancelado**).
- `sent_at` (string) — Quando o envio saiu, em UTC.
- `created_by` (integer) — O ID do administrador que criou.
- `created_at` (string) — Quando o Broadcast foi criado, em UTC.

### ProductCart
- `id` (integer) — O ID do produto.
- `name` (string) — O nome do produto.
- `img` (string) — O endereço da imagem do produto.
- `price` (number) — O preço de uma unidade, na moeda da loja. Não é em centavos: `49.9` = R$ 49,90.
- `amount` (integer) — A quantidade.
- `descr_min` (string) — A descrição curta do produto.
- `manufacturer` (integer) — O ID do vendedor do produto (aba **Vendedores**).
- `variant` (string) — A variante escolhida, como o tamanho ou a cor.
- `user_msg` (string) — O pedido especial que o contato anotou no item, quando o produto permite anexar notas.

### Erro
- `error` (object)
  - `code` (integer) — O código HTTP.
  - `message` (string) — A mensagem, em inglês.

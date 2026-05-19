# Schema — NexTags Messenger Messaging Platform

Schema oficial do JSON que o agente IA da NexTags deve devolver. O
middleware da plataforma consome esse JSON e renderiza nos canais
(WhatsApp, Instagram, Messenger, etc.). Alguns formatos podem não
estar disponíveis em todos os canais.

---

## Estrutura raiz

O JSON raiz é um objeto que contém **`messages`** e/ou **`actions`** (ou
ambos):

```
{
  "messages": [ ... ],   // opcional se tiver actions
  "actions":  [ ... ]    // opcional se tiver messages
}
```

Pelo menos uma das duas chaves deve existir. Se ambas estiverem
ausentes, o JSON é inválido.

---

## `messages` — array de mensagens

Cada item do array é:

- **Um objeto** `{"message": { ...payload... }}` (mensagem real), OU
- **Um inteiro** entre 1 e 30 (typing indicator: segundos de "digitando…"
  entre a mensagem anterior e a próxima).

### 1. Texto simples

```json
{"messages":[{"message":{"text":"Olá Mundo"}}]}
```

### 2. Múltiplas mensagens (com typing indicator opcional)

```json
{"messages":[
  {"message":{"text":"Olá Mundo"}},
  4,
  {"message":{"text":"Essa é a segunda mensagem"}}
]}
```

O `4` significa 4 segundos de "digitando…" antes da próxima mensagem.

### 3. Attachments (imagem, vídeo, áudio, arquivo)

```json
{"messages":[{"message":{"attachment":{"type":"image","payload":{"url":"<IMAGE_URL>"}}}}]}
```

Valores válidos de `type`: `"image"`, `"video"`, `"audio"`, `"file"`.

Qualquer outro valor (`sticker`, `gif`, `location`, etc.) é inválido.

### 4. Carrossel (generic template)

```json
{"messages":[{"message":{"attachment":{"type":"template","payload":{
  "template_type":"generic",
  "image_aspect_ratio":"horizontal",
  "elements":[
    {"title":"Título do Card 1","subtitle":"Subtítulo Card 1","image_url":"<IMAGE_URL>","buttons":[]},
    {"title":"Título do Card 2","subtitle":"Subtítulo Card 2","image_url":"<IMAGE_URL>","buttons":[]}
  ]
}}}}]}
```

Regras:
- **`elements` deve ter ≥ 2 itens.** Plataforma rejeita carrossel com 1 só.
- `image_aspect_ratio` aceita `"horizontal"` ou `"square"`.
- Cada elemento pode ter `buttons` vazio ou com até 3 botões.

### 5. Texto com botões (button template)

```json
{"messages":[{"message":{"attachment":{"type":"template","payload":{
  "template_type":"button",
  "text":"Olá Mundo",
  "buttons":[
    {"title":"Abrir o site","type":"web_url","url":"<URL>"},
    {"title":"Send Flow","type":"postback","payload":"3344556611"}
  ]
}}}}]}
```

Tipos de botão válidos:

| `type`     | Campo obrigatório | Função |
|------------|-------------------|--------|
| `web_url`  | `url`             | Abre link externo |
| `postback` | `payload`         | Dispara flow_id na plataforma (igual `send_flow`) |

Botão sem o campo obrigatório → violação.

---

## `actions` — array de ações automáticas

Executadas pelo middleware após enviar as `messages`. Cada item é um
objeto com a chave `action` + campos específicos.

### Lista completa de ações

| Ação | JSON | Campos obrigatórios |
|---|---|---|
| Adicionar tag | `{"action":"add_tag","tag_name":"<nome>"}` | `tag_name` |
| Remover tag | `{"action":"remove_tag","tag_name":"<nome>"}` | `tag_name` |
| Definir campo personalizado | `{"action":"set_field_value","field_name":"<campo>","value":"<valor>"}` | `field_name`, `value` |
| Limpar campo personalizado | `{"action":"unset_field_value","field_name":"<campo>"}` | `field_name` |
| Disparar fluxo | `{"action":"send_flow","flow_id":"<ID>"}` | `flow_id` |
| Transferir para humano | `{"action":"transfer_conversation_to","value":"human"}` | `value` |
| Atribuir a admin | `{"action":"assign_conversation","admin_id":"<id>"}` | `admin_id` |
| Remover atribuição | `{"action":"unassign_conversation"}` | nenhum |

**Importante:** TODAS as 8 ações acima são válidas conforme a
documentação oficial da NexTags. Esta skill segue à risca esse
schema — não trata `transfer_conversation_to` / `assign_conversation` /
`unassign_conversation` como proibidas.

### Aliases comuns que o agente costuma errar

Mapeie pra forma canônica:

| Variação incorreta | Forma correta |
|---|---|
| `addTag`, `add-tag`, `tag_add` | `add_tag` |
| `removeTag`, `remove-tag`, `tag_remove` | `remove_tag` |
| `setField`, `set_field`, `setFieldValue` | `set_field_value` |
| `unsetField`, `clear_field`, `unsetFieldValue` | `unset_field_value` |
| `sendFlow`, `send-flow`, `trigger_flow`, `flow` | `send_flow` |
| `transfer`, `transfer_to_human`, `transferHuman` | `transfer_conversation_to` (com `value:"human"`) |
| `assign`, `assignTo`, `assign_to` | `assign_conversation` |
| `unassign`, `unassign_admin` | `unassign_conversation` |

---

## Exemplo combinado (messages + actions)

```json
{
  "messages":[{"message":{"text":"Olá mundo"}}],
  "actions":[
    {"action":"add_tag","tag_name":"lead"},
    {"action":"set_field_value","field_name":"lead_value","value":"89"},
    {"action":"send_flow","flow_id":"5854739484"}
  ]
}
```

---

## Regras gerais de validação

1. **Saída exclusivamente JSON.** Sem markdown, sem fence ` ```json `,
   sem prosa antes/depois.
2. **Sempre JSON válido** — vírgulas, aspas, chaves balanceadas.
3. **Aspas retas** `"` — não aspas curvas `"` `"`.
4. **Sem campos `text`/`title`/`subtitle` com markdown** (`**bold**`,
   `# H1`, ` `code` `, etc.). O middleware envia o texto cru, marcação
   aparece literal pro cliente.
5. **Carrossel ≥ 2 elementos.**
6. **Botões `web_url` precisam de `url`.** Botões `postback` precisam de
   `payload`.
7. **`attachment.type` apenas:** `image`, `video`, `audio`, `file`,
   `template`.
8. **Typing indicator** é inteiro (não string) e fica entre 1 e 30
   segundos.

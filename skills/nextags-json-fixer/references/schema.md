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

### Disparo silencioso (só-`actions`, sem texto ao cliente) — VÁLIDO

É legítimo emitir apenas `actions`, com `messages` ausente OU
`"messages": []` explícito. Usos reais (4/25): NPS pós-encerramento,
descadastro pós-confirmação, mockup por IA.

```json
{"messages":[],"actions":[{"action":"send_flow","flow_id":"1775096402729"}]}
```

Regra do fixer:
- `"messages":[]` + `actions` não-vazio → **VÁLIDO**, não inventar mensagem.
- `messages` ausente + `actions` presente → **VÁLIDO**.
- Ambas ausentes/vazias → inválido (pendência).
- ATENÇÃO: `send_flow` "mudo" só é correto para dispara-e-esquece pós-conversa
  (NPS/mockup/descadastro confirmado). Como mecanismo de HANDOFF principal,
  a transferência deve vir com `messages` (texto de confirmação). O fixer não
  reescreve a intenção — apenas registra a observação no relatório quando o
  único `send_flow` vem sem `messages`.

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

O inteiro (`4`) é o typing indicator: segundos de "digitando…". Posições válidas:
- **Entre** dois objetos de mensagem (cria nova bolha com pausa).
- **No início** do array `messages` (pausa de abertura, encadeia com o turno
  anterior do mesmo atendimento) — VÁLIDO, não remover como "órfão".

`\n` dentro de `text` = multilinha na MESMA bolha (listas, blocos de rastreio).
`4` = NOVA bolha. São coisas distintas: nunca converter `\n` em `4` nem vice-versa.

> O typing indicator é SEMPRE o inteiro `4`. "3-5 segundos" é só a descrição
> semântica, não um valor alternativo — nunca usar `3` nem `5`.

### 3. Attachments (imagem, vídeo, áudio, arquivo)

```json
{"messages":[{"message":{"attachment":{"type":"image","payload":{"url":"<IMAGE_URL>"}}}}]}
```

Valores válidos de `type`: `"image"`, `"video"`, `"audio"`, `"file"`.

Qualquer outro valor (`sticker`, `gif`, `location`, etc.) é inválido.

> Nota de produção: `video`/`audio`/`file` são suportados pelo schema mas SEM
> precedente nos 25 prompts reais (0 exemplos) — não gere exemplos inventados
> desses tipos; `image` é o único attachment com uso real.

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

> Nota de produção: carrossel `generic` NÃO aparece em nenhum dos 25 prompts
> reais — o padrão real é botão único `web_url`. Validar continua certo, mas
> não é comum.

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
| `web_url`  | `url`             | Abre link externo (ÚNICO usado em produção: 7/7) |
| `postback` | `payload`         | Dispara flow_id (sintaticamente válido, mas 0% de uso real; preferir `send_flow`) |

Botão sem o campo obrigatório → violação.

**Limites de UI (button template) — observados em produção, validar:**
- **`text` é OBRIGATÓRIO** no payload do button. Button sem `text` → pendência.
- **Máximo 1 botão** no array `buttons` de um button template. >1 botão →
  aviso (estoura UI do Messenger); manter o 1º, listar os demais no relatório.
- **CTA (`title`) ≤ 20 caracteres.** Acima → aviso (não trunca
  automaticamente; sinaliza).
- `postback` em button → aviso: "produção usa só `web_url`; postback de
  transferência deve ser `send_flow` em `actions`."
- Duas ordens de chave são ambas válidas (não corrigir):
  `type`→`payload` e `payload`→`type`.

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

> `unset_field_value` e `remove_tag` são oficiais mas raríssimas (0 uso no
> corpus real). Usar só para LIMPAR um campo/tag ao reverter um estado; não
> fazem parte do fluxo normal.

**Validade vs. boa prática (duas camadas).** As 8 ações acima são
sintaticamente válidas no runtime — esta skill NÃO quebra um JSON só por
usar `transfer_conversation_to` / `assign_conversation` /
`unassign_conversation`. PORÉM, evidência de produção (25 prompts reais):
**0% dos prompts-ouro usam essas 3 ações**; 100% das transferências de
qualidade usam `send_flow` com `flow_id`. Os únicos casos com
`assign_conversation` são exatamente os marcados como desvio.

Regra do fixer:
- NÃO remover/converter automaticamente `transfer_conversation_to` /
  `assign_conversation` / `unassign_conversation` (são válidas em runtime).
- SEMPRE emitir **aviso (não-erro)** no relatório: "Ação X é válida no
  schema, mas 0% dos prompts-ouro a usam; transferência recomendada =
  `send_flow`. Se for handoff para humano, considere converter."
- `admin_id` deve ser um ID/valor limpo. Valor sujo (ex.: `"Estela."` com
  ponto/espaço/nome em vez de ID) → pendência.
- A conversão real para `send_flow` é responsabilidade da
  `nextags-prompt-fixer` (corrige o prompt); aqui só sinalizamos.

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
| `connect_user_to_human` | `send_flow` (flow de transferência → pendência de `flow_id`) |
| `transferir_atendimento`, `transferir_suporte`, `transfer_support` | `send_flow` (→ pendência de `flow_id`) |
| `buscar_pedido`, `Rastreio_Shp()`, `Rotativo()` | função legada de plataforma antiga — não é ação NexTags. Remover do `actions` → pendência (lógica deve vir do MCP/flow) |

**Sintaxe legada com `()` ou `{{...}}` em valor de ação** (ex.: `Rotativo()`,
`{{NumeroPedidoShopify}}`) → não é JSON-action válido. Marcar como pendência;
não tentar "consertar" para uma ação inventada.

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
   `*bold*` (asterisco único, sintaxe Messenger), `_italic_`, `# H1`,
   `> blockquote`, ` `code` `, links `[txt](url)`). O middleware envia o texto
   cru, marcação aparece literal pro cliente. Emojis NÃO são markdown — preservar.
5. **Carrossel ≥ 2 elementos.**
6. **Botões `web_url` precisam de `url`.** Botões `postback` precisam de
   `payload`.
7. **`attachment.type` apenas:** `image`, `video`, `audio`, `file`,
   `template`.
8. **Typing indicator** é inteiro (não string) e fica entre 1 e 30
   segundos.

---

## Convenções de produção que o fixer NÃO deve "corrigir"

1. **Placeholders dinâmicos** — `{nome}`, `{{first_name}}`,
   `{{current_user_time}}`, `<CHECKOUT_URL>`, `[nome]` são intencionais
   (dados vindos de CUF/tool/MCP). NÃO normalizar nem flaggar como "valor
   faltando". Só sinalizar se houver MISTURA de 4 estilos no mesmo bloco
   (aviso de inconsistência, não erro).
2. **`flow_id` numérico de 13 dígitos** (`17xxxxxxxxxxx`) é o formato real;
   não confundir com placeholder.
3. **Ordem de ações** — convenção-ouro (Nex/Uni): `set_field_value` ANTES de
   `send_flow`. NÃO reordenar automaticamente; opcionalmente sugerir no
   relatório se `send_flow` vier antes de `set_field_value` no mesmo array.
4. **`set_field_value` com resumo/briefing pro humano** (ex.:
   `field_name:"assunto_ticket"`) antes de `send_flow` é padrão recomendado,
   não erro.

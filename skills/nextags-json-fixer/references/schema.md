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

### `send_flow` sem `messages` (só-`actions`) — DISPARA NORMAL, é VÁLIDO

É legítimo e padrão emitir apenas `actions`, com `messages` ausente OU
`"messages": []` explícito. O `send_flow` **dispara normalmente** e **o
fluxo assume a comunicação** com o cliente. NÃO é "falha silenciosa", NÃO é
exceção restrita a NPS — é um padrão válido sempre que o fluxo de destino já
fala com o cliente (handoff, catálogo, coleta, NPS, descadastro, mockup,
etc.).

```json
{"messages":[],"actions":[{"action":"send_flow","flow_id":"1775096402729"}]}
```

`messages` junto de um `send_flow` é uma **transição OPCIONAL** — uma frase
curta de UX ("já vou te conectar!"), por boa prática. Nunca é
tecnicamente obrigatória: se o fluxo já comunica, o `send_flow` sozinho
basta.

Regra do fixer:
- `"messages":[]` + `actions` não-vazio → **VÁLIDO**, não inventar mensagem.
- `messages` ausente + `actions` presente → **VÁLIDO**.
- `send_flow` sem `messages` → **VÁLIDO, dispara normal**. NÃO marcar como
  erro, NÃO exigir texto de confirmação. No máximo um lembrete opcional de
  UX (uma transição curta costuma melhorar a experiência), nunca pendência.
- Ambas (`messages` e `actions`) ausentes/vazias → inválido (pendência).
- O fixer não reescreve a intenção nem inventa mensagem de transição.

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

#### ⚠️ Posição do campo `type` (regra mais comum quebrada)

`type` fica **FORA** de `payload`, no mesmo nível dele:

```
✅ CORRETO:
{"attachment":{"type":"image","payload":{"url":"..."}}}

❌ ERRADO (type dentro do payload — middleware não reconhece):
{"attachment":{"payload":{"type":"image","url":"..."}}}
```

O corretor detecta automaticamente o caso errado e move o `type` pra fora.

#### ⚠️ Formato de imagem permitido

A plataforma NexTags entrega imagens nos canais (WhatsApp, Instagram,
Messenger) e **só aceita JPEG e PNG**. Outros formatos quebram a entrega
em pelo menos um canal:

- ✅ Permitidos: `.jpg`, `.jpeg`, `.png` (Content-Type `image/jpeg` ou `image/png`).
- ❌ Proibidos: `.webp`, `.avif`, `.svg`, `.gif`, `.bmp`, `.tiff`, `.heic`, `.heif`.

**Cuidado com CDN.** Muito site/e-commerce serve a mesma URL `.jpg`
respondendo com `Content-Type: image/webp`. A URL parece OK, mas o
servidor entrega WebP — e o canal rejeita. Quando a extensão for
ambígua (`.aspx`, `.php`, sem extensão), a skill marca como pendência:
validar Content-Type antes de enviar ou substituir a URL.

**Regra de ouro:** se não dá pra garantir que é JPEG/PNG, **remova a
imagem** e mantenha só texto + botão. A ausência de imagem é preferível
a quebrar o envio inteiro no canal.

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
| `web_url`  | `url`             | Abre link externo. É o tipo mais comum em produção (7/7); o WhatsApp limita a **1 botão `web_url` por mensagem**. |
| `postback` | `payload`         | Dispara um `flow_id` ao clicar. **PERMITIDO e válido** (até 3 num button template). A IA raramente usa, mas não é proibido. |

Botão sem o campo obrigatório → violação.

**Limites de UI (button template) — observados em produção, validar:**
- **`text` é OBRIGATÓRIO** no payload do button. Button sem `text` → pendência.
- **Máximo 1 botão `web_url` por mensagem** (restrição do WhatsApp para
  link). >1 botão `web_url` → aviso; manter o 1º, listar os demais no
  relatório. Botões `postback` (que disparam fluxo) podem chegar a 3 — não
  são limitados a 1.
- **CTA (`title`) ≤ 20 caracteres.** Acima → aviso (não trunca
  automaticamente; sinaliza).
- `postback` em button → **válido, não é violação**. Dispara um `flow_id` ao
  clicar; a IA raramente usa, mas é permitido. (Para handoff de transferência
  o padrão recomendado continua sendo `send_flow` em `actions`.)
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
sintaticamente válidas no runtime — esta skill NÃO quebra um JSON por
usar `transfer_conversation_to` / `assign_conversation` /
`unassign_conversation`. Todas são **válidas**:
- **`send_flow`** com `flow_id` é o mecanismo oficial e o padrão de handoff
  para humano.
- **`transfer_conversation_to`** (`value:"human"`) é válida **como fallback**
  quando o projeto NÃO tem um flow de transferência configurado. É rede de
  segurança, não erro.
- **`assign_conversation`** (`admin_id`) é válida como **caso especial**
  (atribuir a um atendente específico que o humano define). Uso raro, não é
  o padrão — mas legítima.

Regra do fixer:
- NÃO remover/converter automaticamente `transfer_conversation_to` /
  `assign_conversation` / `unassign_conversation` (são válidas em runtime).
- Quando aparecerem, emitir no máximo um **aviso (não-erro)** lembrando que o
  padrão de handoff é `send_flow` — sem tratar como violação. O fixer só
  avisa; **não converte**.
- `admin_id` deve ser um ID/valor limpo. Valor sujo (ex.: `"Estela."` com
  ponto/espaço/nome em vez de ID) → pendência.
- A conversão real para `send_flow` (quando desejada) é responsabilidade da
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
   sem prosa antes/depois. Resposta começa com `{` e termina com `}`.
2. **Sempre JSON válido** — vírgulas, aspas, chaves balanceadas.
3. **Aspas retas** `"` — não aspas curvas `"` `"`.
4. **Sem MARKDOWN-PADRÃO em campos `text`/`title`/`subtitle`** — o que
   VAZA literal pro cliente: `**bold**` (asterisco DUPLO), `# H1` (hashtag-
   título), `> blockquote`, ` `code` ` / cercas ` ``` `, bullets com hífen
   (`- item`), links `[txt](url)`. Essa marcação o middleware envia crua e
   aparece literal pro cliente → remover, preservando o conteúdo.
   **WA-markup é PERMITIDO e PRESERVADO:** marcação estilo WhatsApp
   `*negrito*` (asterisco ÚNICO), `_itálico_`, `~tachado~` RENDERIZA na
   plataforma (testado pelo cliente) — NÃO remover, NÃO tratar como
   violação. Emojis também NÃO são markdown — preservar.
5. **Carrossel ≥ 2 elementos.**
6. **Botões `web_url` precisam de `url`.** Botões `postback` precisam de
   `payload`.
7. **`attachment.type` apenas:** `image`, `video`, `audio`, `file`,
   `template`.
8. **`attachment.type` FORA de `payload`** (no mesmo nível). Type dentro
   do payload é o erro mais comum — o middleware ignora.
9. **Imagens só em JPEG/PNG.** WebP/AVIF/SVG/GIF quebram pelo menos um
   canal. Quando a extensão é ambígua, validar Content-Type ou remover.
10. **Typing indicator** é inteiro (não string) e fica entre 1 e 30
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

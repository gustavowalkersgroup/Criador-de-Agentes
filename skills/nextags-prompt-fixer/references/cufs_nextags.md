# CUFs (Custom User Fields) da Plataforma NexTags

> Lista completa dos campos personalizados nativos do sistema NexTags. Use estes campos em vez de placeholders genéricos (`[nome]`, `[email]`, etc.) ao gerar exemplos no prompt.

---

## REGRA DE OURO

**NUNCA use placeholders genéricos** como `[nome]`, `[cliente]`, `[email]`, `[primeiro nome]`, `[telefone]` etc. nos exemplos do prompt.

**SEMPRE use os CUFs nativos** quando existir um campo equivalente no sistema, com a sintaxe `{{nome_do_campo}}` (duas chaves). A plataforma NexTags interpola automaticamente em runtime.

**Use somente se for necessário.** Não force interpolação onde texto neutro funciona melhor (ex: "Oi! Como posso te ajudar?" pode ser mais natural que "Oi, {{first_name}}! Como posso te ajudar?" em alguns contextos).

**Fallback quando o CUF estiver vazio:** sempre que usar `{{first_name}}` ou similar, considere o caso "campo vazio" (cliente sem cadastro). Para isso, ou ofereça uma variante neutra no prompt, ou confie que a plataforma renderiza vazio sem o nome (e a frase deve continuar fazendo sentido).

---

## Gerenciamento de contatos e contas

| CUF | Descrição |
|---|---|
| `{{first_name}}` | Primeiro nome do usuário. Personalização amigável. |
| `{{last_name}}` | Sobrenome. Personalização mais formal. |
| `{{full_name}}` | Nome completo (primeiro + sobrenome). |
| `{{email}}` | E-mail do usuário. |
| `{{phone}}` | Telefone do usuário. |
| `{{user_country}}` | País do usuário. |
| `{{user_state}}` | Estado/região do usuário. |
| `{{user_city}}` | Cidade do usuário. |
| `{{gender}}` | Gênero do usuário. |
| `{{locale}}` | Localidade completa (ex: `en_US`). |
| `{{locale2}}` | Idioma abreviado (ex: `en`). |
| `{{username}}` | Username do Instagram. |
| `{{profile_pic}}` | URL da foto de perfil. |
| `{{timezone}}` | Fuso horário do usuário. |
| `{{user_id}}` | ID interno NexTags. |
| `{{subscribed_date}}` | Data de inscrição. |
| `{{fb_chat_link}}` | Link direto da inbox do Messenger. |
| `{{inbox_link}}` | Link da inbox NexTags (acesso de admin/agente). |
| `{{me}}` | Link de visualização/exclusão de dados (GDPR). |
| `{{webchat}}` | Link de chat na web. |
| `{{user_code}}` | Código único de rastreamento. |
| `{{user_hash}}` | Hash único do usuário. |
| `{{user_external_id}}` | ID externo (Messenger/Instagram). |
| `{{user_source}}` | Origem do usuário (ex: anúncio, comentário). |
| `{{user_channel}}` | Canal principal (Messenger, Webchat). |
| `{{user_tags}}` | Lista de tags do usuário. |
| `{{current_user_time}}` | Hora local atual do usuário. |
| `{{last_seen}}` | Última vez visto. |
| `{{last_interaction}}` | Timestamp da última interação. |
| `{{last_text_input}}` | Última mensagem de texto enviada. |
| `{{last_input}}` | Última entrada (texto/imagem/vídeo/áudio/arquivo). |
| `{{last_input_type}}` | Tipo da última entrada. |
| `{{last_btt_title}}` | Título do último botão clicado. |
| `{{last_ref}}` | Último link de referência clicado. |
| `{{last_ad}}` | ID do último anúncio (Facebook). |
| `{{consecutive_failed_reply}}` | Nº de respostas com falha consecutivas. |
| `{{chat_history}}` | Últimas 50 mensagens trocadas. |
| `{{chat_history_large}}` | Últimas 200 mensagens trocadas. |
| `{{chat_history_details}}` | 50 últimas mensagens + detalhes do remetente. |
| `{{chat_history_details_large}}` | 200 últimas mensagens + detalhes do remetente. |
| `{{last_points}}` | Pontuação mais recente de questionário. |
| `{{user_notes}}` | Todas as notas adicionadas ao perfil. |
| `{{last_user_note}}` | Nota/comentário mais recente do perfil. |
| `{{last_call_recorded}}` | URL da última chamada gravada (Twilio). |
| `{{last_step}}` | ID do PASSO da última etapa em fluxo publicado. |
| `{{current_step}}` | ID do PASSO atualmente ativo. |
| `{{assigned_admin_name}}` | Nome do admin atribuído. |
| `{{assigned_admin_id}}` | ID do admin atribuído. |
| `{{account_name}}` | Nome da conta NexTags. |
| `{{account_id}}` | ID da conta NexTags. |
| `{{account_image}}` | Imagem da conta. |
| `{{api_key}}` | Chave API da conta. |

## Instagram

| CUF | Descrição |
|---|---|
| `{{ig_user_name}}` | Username do Instagram do usuário. |
| `{{ig_followers}}` | Total de seguidores. |
| `{{ig_verified}}` | Conta verificada (true/false). |
| `{{ig_follow_business}}` | Usuário segue a conta business (true/false). |
| `{{ig_business_follow_user}}` | Conta business segue o usuário (true/false). |
| `{{last_story_id}}` | ID da última story respondida. |
| `{{last_fb_comment}}` | Texto do último comentário (cross IG/FB). |
| `{{last_post_id}}` | ID do último post comentado (cross IG/FB). |
| `{{last_comment_id}}` | ID do último comentário (cross IG/FB). |
| `{{last_commented_post_text}}` | Legenda completa do post comentado. |

## Facebook Messenger

| CUF | Descrição |
|---|---|
| `{{page_user_name}}` | Username de quem interage via Messenger. |
| `{{total_new_tagged}}` | Nº de usuários novos marcados em comentário. |
| `{{total_tagged}}` | Nº total de usuários marcados em comentário. |

## Localização

| CUF | Descrição |
|---|---|
| `{{last_latitude}}` | Última latitude conhecida (se compartilhou localização). |
| `{{last_longitude}}` | Última longitude conhecida. |

## Agendamentos

| CUF | Descrição |
|---|---|
| `{{booking_date}}` | Data do agendamento. |
| `{{booking_link}}` | Link de confirmação/detalhes do agendamento. |
| `{{booking_id}}` | ID único do agendamento. |
| `{{booking_calendar}}` | Calendário associado. |

## Ecommerce (Catálogo META)

| CUF | Descrição |
|---|---|
| `{{cart_checkout_link}}` | Link de checkout do carrinho. |
| `{{cart_last_item_name}}` | Nome do último item adicionado ao carrinho. |
| `{{cart_last_item_quantity}}` | Quantidade do último item. |
| `{{cart_num_items}}` | Total de itens no carrinho. |
| `{{cart_other_fees}}` | Taxas adicionais. |
| `{{cart_shipping_cost}}` | Custo de envio. |
| `{{cart_subtotal}}` | Subtotal antes de impostos/taxas. |
| `{{cart_total}}` | Total final do carrinho. |
| `{{shop_link}}` | Link da loja. |
| `{{money_symbol}}` | Símbolo da moeda. |
| `{{order_coupon_code}}` | Código do cupom aplicado. |
| `{{order_coupon_discount}}` | Desconto do cupom. |
| `{{order_date_account_timezone}}` | Data do pedido (fuso da conta). |
| `{{order_date_timestamp}}` | Timestamp do pedido. |
| `{{order_date_utc}}` | Hora UTC do pedido. |
| `{{order_discount}}` | Total de desconto. |
| `{{order_email}}` | E-mail do pedido. |
| `{{order_id}}` | ID único do pedido. |
| `{{order_name}}` | Nome de quem fez o pedido. |
| `{{order_payment_method}}` | Método de pagamento. |
| `{{order_phone}}` | Telefone do pedido. |
| `{{order_products}}` | Lista de produtos. |
| `{{order_shipping_type}}` | Tipo de envio. |
| `{{order_shipping_address1}}` | Linha 1 do endereço. |
| `{{order_shipping_address2}}` | Linha 2 (apto, complemento). |
| `{{order_shipping_city}}` | Cidade do envio. |
| `{{order_shipping_cost}}` | Custo de envio do pedido. |
| `{{order_shipping_state}}` | Estado do envio. |
| `{{order_shipping_zip}}` | CEP. |
| `{{order_shipping_country}}` | País do envio. |
| `{{order_shipping}}` | Informações completas de envio. |
| `{{order_status}}` | Status do pedido. |
| `{{order_subtotal}}` | Subtotal antes de impostos/envio. |
| `{{order_taxes}}` | Total de impostos. |
| `{{order_total}}` | Valor total do pedido. |
| `{{product_name}}` | Nome do produto (uso com gatilhos). |
| `{{product_quantity}}` | Quantidade do produto. |
| `{{product_id}}` | ID único do produto. |

---

## Como aplicar no prompt

### ✅ Certo

```
{"messages":[{"message":{"text":"Oi, {{first_name}}! Como posso te ajudar hoje? 😊"}}]}
```

A plataforma interpola `{{first_name}}` com o primeiro nome do contato em runtime. Se o cliente não tem nome cadastrado, a plataforma renderiza vazio.

### ❌ Errado

```
{"messages":[{"message":{"text":"Oi, [nome]! Como posso te ajudar hoje? 😊"}}]}
{"messages":[{"message":{"text":"Oi, [cliente]! Como posso te ajudar hoje? 😊"}}]}
{"messages":[{"message":{"text":"Oi, {nome_do_cliente}! Como posso te ajudar hoje? 😊"}}]}
{"messages":[{"message":{"text":"Oi, $first_name$! Como posso te ajudar hoje? 😊"}}]}
```

Placeholders entre colchetes `[ ]`, ou com nomes que não são CUFs reais (`{nome_do_cliente}`, `$first_name$`), aparecem literalmente pra cliente. A plataforma NÃO interpola nada que não seja `{{cuf_real}}`.

### ⚠️ Quando NÃO interpolar

Não force o uso de CUFs onde texto neutro funciona melhor:

- **Saudação genérica** (sem nome): "Oi! Tudo bem? Como posso te ajudar?" — funciona pra cliente sem cadastro.
- **Mensagens curtas de pausa/confirmação**: "Tô olhando aqui pra você!" — não precisa de nome.
- **Quando o CUF pode estar vazio E não tem fallback**: "Olá, {{first_name}}!" sem alternativa pode virar "Olá, !" se o cliente não tem nome.

**Regra prática:** use CUF em saudações iniciais e em momentos-chave (entrega de info importante, fechamento). Não use em toda mensagem.

---

## Fallback pra CUFs vazios

Quando o prompt usa `{{first_name}}` numa saudação, considere oferecer uma variante neutra no caso "campo vazio". Exemplo no prompt:

```
**Abertura com nome:**
{"messages":[{"message":{"text":"Oi, {{first_name}}! Tudo bem?"}}]}

**Abertura sem nome (cliente sem cadastro):**
{"messages":[{"message":{"text":"Oi! Tudo bem? Como posso te ajudar?"}}]}
```

A plataforma decide qual usar baseado em se o CUF tá preenchido. Se você não der variante, a frase "Oi, ! Tudo bem?" pode aparecer (estranho mas não quebra).

---

## ⚠️ Achado — como a IA REALMENTE "lê" um CUF (não é uma ferramenta, é substituição de texto)

Testado e confirmado em produção (cliente Otogama, 11/08/2026): um agente de IA sem NENHUM prompt de negócio, contendo só a lista literal de tags (`{{campo1}},{{campo2}},...`), respondeu corretamente com o conteúdo real desses campos do contato. Atualizando os valores do contato (`POST /contacts` + `set_field_value`) e perguntando de novo na mesma conversa, o agente devolveu os valores NOVOS — nunca os antigos.

**Conclusão:** CUFs são substituídos (merge/interpolação) diretamente no TEXTO do prompt, no servidor, ANTES da chamada ao modelo. Não é uma tool que o modelo "chama" pra buscar dado ao vivo — é um find-and-replace no texto do prompt. A substituição acontece a cada requisição, sem cache.

**Implicação crítica ao auditar/corrigir um prompt:** um CUF só é visível pro agente se o texto literal `{{nome_do_campo}}` aparecer EM ALGUM LUGAR do prompt. Se o prompt instrui o agente a "usar os dados do cliente" ou "verificar {{campo}}" sem a tag estar de fato escrita ali, ou se o cliente reclama que "a IA não está vendo o campo X" — confira primeiro se `{{X}}` está literalmente no texto do prompt, antes de investigar CRM, flow ou webhook. Campo populado no contato mas sem a tag escrita no prompt = o agente nunca sabe que o dado existe.

**Regra prática de correção:** sempre que o prompt depender do agente RACIOCINAR sobre um dado de contato (decidir, comparar, responder pergunta aberta sobre ele) — não só repetir numa frase pronta — garanta um bloco explícito de dados no prompt, tipo:

```
### Dados do contato (usar se preenchidos, ignorar se vazio)
Nome: {{nomesocial}}
Data de nascimento: {{nascimento}}
Agendamento: {{data_agendamento}} às {{hora_agendamento}} com {{medico}}
```

Liste TODOS os CUFs relevantes aí, mesmo os que não aparecem em nenhuma mensagem de exemplo — é a PRESENÇA da tag no texto, não o uso estético dela numa fala, que libera a leitura pro modelo.
---

## 🏛️ CUFs de ESCRITA canonicos do metodo (padrao em TODO cliente)

Todos os CUFs listados acima sao de **LEITURA** - nativos da plataforma. Os tres abaixo sao
de **ESCRITA** e fazem parte do metodo, nao da plataforma: **crie-os em toda conta nova e
use estes nomes**, mudando so se o cliente pedir.

| CUF | Tipo | Quem escreve | Papel |
|---|---|---|---|
| `resumo_pipeline` | Text (0) | **a IA**, antes de todo `send_flow` | contexto do caso; viaja com a conversa no handoff |
| `motivo_transferencia` | Text (0) | **a IA**, antes de todo `send_flow` | qual fila **HUMANA** recebe - e o filtro do flow rotativo |
| `setor_agente` | Text (0) | **o FLOW, NUNCA a IA** | qual **AGENTE IA** atende - lido pelo Flow de Entrada a cada mensagem |

⚠️ **`setor_agente` e a excecao: a IA NUNCA grava nele.** O Flow de Entrada le esse campo em
CADA mensagem para decidir quem atende, entao se a IA escrever nele ela pode se re-rotear
para si mesma - loop infinito. Bug real em producao (cliente Veuske). Quem grava e o flow
dedicado de destino. Detalhes em `handoff_pattern.md` da skill `nextags-mcp-builder`.

**As duas camadas nao se misturam:**

```
IA <-> IA          (qual agente atende)  -> setor_agente, N flows dedicados, 1 por destino
IA  -> fila humana (qual fila recebe)    -> motivo_transferencia, UM flow rotativo
```

### `motivo_transferencia` - enum canonico

```
vendas | rastreio | devolucao | troca | duvidas
```

Mais o ramo **`else` do flow, que cai na fila de SAC geral**. O `else` e o default e cobre
tudo o que nao e um dos cinco: defeito, reacao na pele/produto, pagamento, cancelamento,
reputacional, juridico. Nesses casos grave **`sac_geral`** explicitamente no prompt - cai no
mesmo destino do `else` e deixa o motivo legivel no contato.

Minusculas, sem acento. **So mude os valores se o cliente pedir** - o flow dele ja esta
filtrando por estas strings exatas.

⚠️ **`troca` vs `devolucao` precisa de regra escrita no prompt**, senao a IA escolhe no
chute: use a palavra que a cliente usou; se ela usou as duas ou nenhuma, quer outra peca e
`troca`, quer o dinheiro de volta e `devolucao`. Cancelar antes de receber nao e nenhum dos
dois - e `sac_geral`.

⚠️ **Cada valor do enum precisa de pelo menos um exemplo JSON verbatim no prompt.** Enum sem
exemplo e enum que a IA erra: a galeria de exemplos e o mecanismo mais forte de aderencia.
Ao gerar, confira a cobertura - se um valor nao aparece em nenhum exemplo, escreva um.

⚠️ **Ao colapsar N flows em 1, procure linhas de tabela AGRUPADAS.** Situacoes que iam para
o mesmo flow costumam estar juntas numa linha ("Troca, devolucao, cancelamento"). Se o enum
separa esses casos, a linha agrupada faz a IA escolher no chute - precisa split.

### O modo de falha e CAMPO STALE, e e pior que campo vazio

`resumo_pipeline` e `motivo_transferencia` **persistem no contato**. Se a IA disparar o flow
sem grava-los, o filtro le o valor do atendimento ANTERIOR da mesma pessoa e ela cai na fila
errada - parecendo funcionar. Campo vazio cai no `else` (aceitavel); campo velho cai no lugar
errado (pior, porque nao aparece como erro).

Por isso, ao gerar o prompt:
1. Escreva a regra de gravar os dois em TODA transferencia, **com a consequencia explicita**.
2. Nao deixe **nenhum** exemplo de `send_flow` sem os dois `set_field_value` antes.
3. `send_flow` sempre por ultimo no array de `actions`.

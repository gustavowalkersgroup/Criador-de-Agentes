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

## 🏛️ CUFs de ESCRITA canônicos do método (padrão em TODO cliente)

> ⚠️ **Esta seção foi superada por `references/campos_canonicos.md`** (§1-§3), fonte de
> verdade única. O que mudou em relação à versão anterior desta referência: o enum de
> `motivo_transferencia` cresceu (parcerias + comercial + SAC), o catch-all passou a ser
> `duvida` (singular) e **`sac_geral` deixou de existir**; `prioridade_pipeline` entra como
> 3º campo do trio (junto de `motivo_transferencia` e `resumo_pipeline`); `tipo_setor` e
> `resposta_ia` entram na tabela como campos que a IA nunca grava. Ao auditar/corrigir um
> prompt, use o resumo operacional abaixo e o detalhe completo (critério de cada valor,
> tabela de legado, exemplos) em `references/campos_canonicos.md`.

Todos os CUFs listados acima são de **LEITURA** — nativos da plataforma. Os CUFs abaixo são
de **ESCRITA** e fazem parte do método, não da plataforma: existem em toda conta nova com
estes nomes, mudando só se o cliente pedir.

| CUF | Tipo | Quem escreve | Papel |
|---|---|---|---|
| `setor_agente` | Texto | **o ROTEADOR, NUNCA a IA** | qual **AGENTE IA** atende (`vendas`\|`sac`\|`analisar_humano_bot`) — lido pelo Fluxo de Entrada a CADA mensagem |
| `tipo_setor` | Seleção única | **o REVALIDADOR, NUNCA a IA** | `humano`\|`bot` — 2ª camada de classificação, só roda no `else` do roteador |
| `motivo_transferencia` | Texto | **a IA**, antes de todo `send_flow` de pipeline | enum canônico por setor (abaixo) — é o filtro que decide a fila HUMANA |
| `prioridade_pipeline` | Seleção única | **a IA**, antes de todo `send_flow` | `baixa`\|`media`\|`alta` |
| `resumo_pipeline` | Texto | **a IA**, antes de todo `send_flow` | contexto do caso (2-4 frases); viaja com a conversa no handoff |
| `resposta_ia` | Texto | **o FLUXO** (passo Filtro JSON), NUNCA a IA | resposta já filtrada, enviada por `{{resposta_ia}}`; o prompt não menciona esse campo |

⚠️ **`setor_agente` e `tipo_setor` são as exceções mais graves: a IA NUNCA grava neles.** O
Fluxo de Entrada lê `setor_agente` em CADA mensagem para decidir quem atende — se um agente
escrever nesse campo (ex.: tentando "passar para o SAC"), ele pode se re-rotear para si
mesmo, criando loop infinito (bug real em produção, cliente Veuske). Ao auditar/corrigir um
prompt e encontrar `set_field_value` com `field_name` `setor_agente` ou `tipo_setor` num JSON
de agente: **bloquear e remover a action** — padrão de fix completo (inclusive o caso em que
a intenção era "trocar de IA") na Regra 21 de `references/regras_absolutas.md`.

**As duas camadas não se misturam:**

```
IA <-> IA          (qual agente atende)  -> setor_agente (só o Roteador grava)
IA  -> fila humana (qual fila recebe)    -> motivo_transferencia + prioridade_pipeline
                                             + resumo_pipeline (só a IA grava, nesta ordem)
```

### `motivo_transferencia` — enum canônico por setor

```
Parcerias: ugc | colaboracao | influencer | revenda | atacado
Comercial: vendas | carrinho
SAC:       rastreio | devolucao | troca | duvida   (duvida = catch-all)
```

Minúsculas, sem acento, sem plural (`duvida`, não `duvidas`). **`sac_geral` não existe
mais** — o catch-all é `duvida`, que cai no mesmo destino do `else` do fluxo de pipeline
(painel SAC). Critério completo de quando usar cada valor, tabela de legado
(`duvidas`→`duvida`, `sac_geral`→`duvida`, `assunto_ticket`/`resumo_lead`/`sac_resumo`→
`resumo_pipeline`, `sac_prioridade`→`prioridade_pipeline`, `sac_categoria`→
`motivo_transferencia`) e exemplos: ver `references/campos_canonicos.md` §2.1 e §8, e Regra
21 de `references/regras_absolutas.md`.

⚠️ **`troca` vs `devolucao` precisa de regra escrita no prompt**, senão a IA escolhe no
chute: use a palavra que a cliente usou — quer outra peça é `troca`, quer o dinheiro de
volta é `devolucao`. Cancelar antes de receber não é nenhum dos dois — é `duvida`.

⚠️ **Cada valor do enum que o agente pode usar precisa de pelo menos um exemplo JSON
verbatim no prompt.** Enum sem exemplo é enum que a IA erra: a galeria de exemplos é o
mecanismo mais forte de aderência. Ao auditar, confira a cobertura — se um valor não aparece
em nenhum exemplo, sugerir adicionar.

⚠️ **Ao colapsar situações numa tabela, procure linhas AGRUPADAS.** Situações que iam para o
mesmo destino costumam estar juntas numa linha ("Troca, devolução, cancelamento"). Se o enum
separa esses casos, a linha agrupada faz a IA escolher no chute — precisa split.

### O modo de falha é CAMPO STALE, e é pior que campo vazio

Os três campos do trio (`motivo_transferencia`, `prioridade_pipeline`, `resumo_pipeline`)
**persistem no contato**. Se a IA disparar `send_flow` sem gravá-los, o fluxo lê o valor do
atendimento ANTERIOR da mesma pessoa e ela cai na fila/prioridade errada — parecendo
funcionar. Campo vazio cai no `else` (aceitável); campo velho cai no lugar errado (pior,
porque não aparece como erro em lugar nenhum).

Ao auditar/corrigir:
1. Confira que os TRÊS campos são gravados em TODA transferência, com a consequência
   explícita escrita no prompt caso falte.
2. Nenhum exemplo de `send_flow` de transferência pode ficar sem os três `set_field_value`
   antes.
3. `send_flow` sempre por último no array de `actions`.
4. Nunca `setor_agente`/`tipo_setor` num JSON de agente (bloqueio — ver acima).

### CUFs transacionais — leitura para o SAC

Os CUFs transacionais (`numero_pedido`, `status_pedido`, `rastreio_url`, `previsao_entrega`
etc., gravados pelo webhook-builder — ver `references/campos_canonicos.md` §5) são de
**LEITURA** para o agente de SAC: se estiverem escritos como `{{campo}}` no bloco `## DADOS
DESTA CONVERSA` do prompt (§6.3), o agente responde "onde está meu pedido" sem precisar de
tool, porque o transacional já populou o contato. Ao auditar um prompt de SAC com tool de
rastreio mas sem esses `{{campo}}` no texto, sugerir adicioná-los (ver "Achado" acima nesta
mesma referência).

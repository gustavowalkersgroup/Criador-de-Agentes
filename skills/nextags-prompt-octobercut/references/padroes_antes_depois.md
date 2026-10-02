# Padrões antes → depois (JSON)

Exemplos reais do ajuste feito nos 6 agentes do grupo (Comercial e Suporte da
Hidratei, Beleza Brasileira e Imunehair). Use como modelo ao reescrever os
exemplos JSON de um prompt. O número entre parênteses é a quantidade de
mensagens cobradas.

## 1. Suporte: status do pedido

**Antes (4):**

```json
{"messages":[{"message":{"text":"Boa notícia, Camila! ✨"}},4,{"message":{"text":"Seu pedido #5432 tá a caminho — previsão de entrega: 08/10."}},4,{"message":{"text":"Aqui o link de rastreio pra você acompanhar: (link)"}},4,{"message":{"text":"Qualquer coisa, tô por aqui, tá?"}}]}
```

**Depois (1):**

```json
{"messages":[{"message":{"text":"Boa notícia, Camila! ✨ Seu pedido #5432 tá a caminho — previsão de entrega: 08/10.\n\nAqui o link de rastreio pra você acompanhar: (link)\n\nQualquer coisa, tô por aqui, tá?"}}]}
```

## 2. Comercial: cliente manda "Oi"

**Antes (2):**

```json
{"messages":[{"message":{"text":"Oi, hidratada. 💙"}},4,{"message":{"text":"Que bom ter você aqui! Me conta, o que seus fios estão precisando?"}}]}
```

**Depois (1), já mostrando os caminhos:**

```json
{"messages":[{"message":{"text":"Oi, hidratada. 💙 Por aqui eu te ajudo a escolher a rotina certa pros seus fios, tiro suas dúvidas sobre os produtos, te conto as promoções e já monto seu pedido.\n\nMe conta: o que seu cabelo está pedindo hoje — hidratação, brilho, menos frizz ou reconstrução? Se for sobre um pedido que você já fez, é só me falar."}}]}
```

## 3. Comercial: link de compra

**Antes (2):**

```json
{"messages":[{"message":{"text":"Prontinho! Montei seu carrinho 💙"}},{"message":{"attachment":{"type":"template","payload":{"template_type":"button","text":"Clique abaixo para finalizar","buttons":[{"type":"web_url","title":"Finalizar compra","url":"<URL_CHECKOUT>"}]}}}}]}
```

**Depois (1), a frase vai dentro do botão:**

```json
{"messages":[{"message":{"attachment":{"type":"template","payload":{"template_type":"button","text":"Prontinho! Montei seu carrinho 💙","buttons":[{"type":"web_url","title":"Finalizar compra","url":"<URL_CHECKOUT>"}]}}}}]}
```

## 4. Comercial: vitrine de produto

**Antes (4):** imagem → 4 → texto+botão → 4 → pergunta de follow-up (padrão
antigo do `prompt_skeleton.md` §6B.5).

```json
{"messages":[{"message":{"attachment":{"type":"image","payload":{"url":"<URL_IMAGEM>"}}}},4,{"message":{"attachment":{"type":"template","payload":{"template_type":"button","text":"<produto>, R$ 0,00\n<pitch curto>","buttons":[{"type":"web_url","title":"Comprar agora","url":"<URL_PRODUTO>"}]}}}},4,{"message":{"text":"Qual cor você prefere?"}}]}
```

**Depois (2):** imagem + 1 template de botão com a pergunta dentro.

```json
{"messages":[{"message":{"attachment":{"type":"image","payload":{"url":"<URL_IMAGEM>"}}}},{"message":{"attachment":{"type":"template","payload":{"template_type":"button","text":"<produto>, R$ 0,00\n<pitch curto>\n\nQual cor você prefere?","buttons":[{"type":"web_url","title":"Comprar agora","url":"<URL_PRODUTO>"}]}}}}]}
```

Fotos das variações (cores, tamanhos) só se a cliente pedir.

## 5. Suporte: mensagem de espera

**Antes (2):**

```json
{"messages":[{"message":{"text":"Deixa eu verificar isso pra você..."}},4,{"message":{"text":"Encontrei! O prazo é de 3 a 5 dias úteis."}}]}
```

**Depois (1):** a IA chama a tool antes de responder.

```json
{"messages":[{"message":{"text":"O prazo de entrega pro seu CEP é de 3 a 5 dias úteis. Quer que eu já te mande o link pra finalizar?"}}]}
```

## 6. Suporte: coleta de dados

**Antes (3 trocas da empresa):** "Qual seu nome?" → "Qual seu CPF?" → "E o
número do pedido?"

**Depois (1):**

```json
{"messages":[{"message":{"text":"Consigo ver isso agora pra você! Me manda, numa mensagem só, o CPF usado na compra e, se tiver à mão, o número do pedido."}}]}
```

## 7. Handoff para humano

Se o fluxo de pipeline já envia mensagem ao cliente, a IA não precisa de
transição:

```json
{"actions":[{"action":"set_field_value","field_name":"motivo_transferencia","value":"troca_devolucao"},{"action":"set_field_value","field_name":"prioridade_pipeline","value":"media"},{"action":"set_field_value","field_name":"resumo_pipeline","value":"Ana, pedido 11488, quer trocar tamanho M por G. Produto sem uso. Prazo de troca ok."},{"action":"send_flow","flow_id":"<ID_DO_FLUXO_PIPELINE>"}]}
```

Se o fluxo **não** fala nada, use uma bolha só de transição, curta.

> Nos prompts, os exemplos JSON vão **sem** fence ```` ```json ```` (Regra
> Absoluta #11). As cercas aqui são só para leitura desta referência.

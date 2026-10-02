# Cobrança da Meta para mensagens não-template (H2 2026)

Resumo da página "Pricing for non-template messages" da documentação da
WhatsApp Business Platform e do que ela significa para os agentes NexTags.

## Linha do tempo

| Data | O que muda |
|---|---|
| 01/07/2026 | Meta lança a Meta Business Agent Platform (agente de IA da própria Meta). |
| 01/08/2026 | Mensagens do Meta Business Agent passam a ser cobradas **por token** (US$ 2,00 por 1M tokens, ~4–5 centavos de dólar por mensagem). |
| **01/10/2026** | Mensagens de **serviço** passam a ser cobradas **por mensagem**. Estavam grátis desde nov/2024. |
| **01/10/2026** | Mensagens de **utilidade** enviadas dentro da janela de 24h passam a ser cobradas. Estavam grátis desde jul/2025. |

## O que é "mensagem de serviço"

Toda mensagem **não-template** que a empresa manda em resposta ao cliente
dentro da janela de atendimento de 24h, escrita por:

- um atendente humano; ou
- uma IA de terceiros (é o caso dos agentes NexTags).

Ou seja: **toda resposta do agente NexTags e todo texto do atendente humano é
mensagem de serviço**, e cada uma é cobrada.

## Regras de cobrança relevantes

- **Uma cobrança por mensagem.** Cada mensagem tem uma categoria só. Mensagem
  não-template com conteúdo promocional continua sendo `service` (não leva
  cobrança extra de marketing).
- **Preço da mensagem de serviço = preço de utilidade/autenticação do
  mercado**, sem faixas de volume. Referência Brasil usada pela Meta: 0,68
  centavo de dólar por mensagem. A Meta pode revisar o valor a cada trimestre.
- **Janela grátis de 72h (entry point)** continua valendo: conversa iniciada
  por anúncio Click-to-WhatsApp ou botão de CTA do Facebook não paga entrega
  de mensagem nesse período.
- Mensagem enviada pelo cliente não é cobrada.
- Webhook de status: mensagens cobradas chegam com
  `"pricing": {"billable": true, "pricing_model": "PMP", "type": "regular", "category": "service"}`.
  Dá para contar o volume real pela Pricing Analytics API com
  `pricing_category: "SERVICE"`.

## O que isso significa na prática

1. **Cada bolha custa.** Uma resposta quebrada em 4 balões custa 4×.
2. **Typing indicator `4` custa uma mensagem** porque cria bolha nova.
3. **Imagem, botão, carrossel e cada mensagem de um fluxo** também contam.
4. **Pingue-pongue custa.** Perguntar uma coisa por vez gera mais respostas da
   empresa. Conversa conduzida por perguntas agrupadas fecha em menos turnos.
5. **Mensagem de espera** ("só um minuto que vou verificar") é cobrança sem
   valor para o cliente.

## Estimativa interna (agentes do grupo, out/2026)

| Cenário | Antes | Depois | Custo antes | Custo depois | Redução |
|---|---|---|---|---|---|
| Rastreio de pedido (Suporte) | ~7 msgs | ~2 msgs | R$ 0,25 | R$ 0,07 | −71% |
| Venda completa (Comercial) | ~10 msgs | ~5 msgs | R$ 0,35 | R$ 0,18 | −50% |

Cerca de **R$ 175 a menos a cada 1.000 atendimentos**. A economia real tende
a ser maior porque o agente também deixou de perguntar o nome e de fazer uma
pergunta por vez. Esses números são estimativa e devem ser confirmados nas
conversas reais.

Custo por mensagem implícito nessas contas: ~R$ 0,035. Use-o como padrão do
`octobercut.py estimate`, mas confirme no rate card vigente da Meta.

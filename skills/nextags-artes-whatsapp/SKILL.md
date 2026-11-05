---
name: nextags-artes-whatsapp
description: Cria e revisa artes 1:1 e modelos de mensagens da Nextags AI para demonstrar transacionais e campanhas no WhatsApp, como pedido, Pix vencido, carrinho, atendimento, contrato, upsell e cross-sell.
---

# Artes de WhatsApp da Nextags AI

Identifique o evento, a ação esperada e o que a pessoa pediu: arte, texto, prompt portátil ou pacote completo. Siga o exemplo aprovado da conversa quando houver. Se o usuário pedir uma amostra antes da série, entregue apenas a amostra.

## Série padrão em lote

Para pedidos da série completa, leia [o prompt mestre](references/prompt-geracao.txt). Faça a coleta inicial em uma só rodada, solicitando logo, arte aprovada, foto da modelo ou pessoa, captura do WhatsApp e condições das ofertas que ainda estiverem faltando. Use os dados já fornecidos. Após o briefing, gere todas as sete peças na mesma entrega: pedido aprovado, pedido enviado, pedido entregue, recuperação de pagamento, carrinho abandonado, cross-sell com cashback e upsell com produto e frete grátis. Se o usuário pedir apenas uma peça, siga esse recorte.

## Mensagem e arte

- Separe a peça de apresentação, o anexo estático e o corpo da mensagem. Em uma demonstração, a peça mostra o dispositivo com a conversa. Use dados fictícios no balão de texto. Para operação, use variáveis como `{{nome}}` e `{{numero_pedido}}` somente no texto, deixando o anexo reutilizável.
- Escreva em português do Brasil. Use título curto, uma frase de apoio e os botões necessários para a ação. Exemplo: Pix vencido oferece “Gerar novo Pix”. Trate recuperação de carrinho, upsell, cross-sell e ofertas como exemplos comerciais, sem pressupor categoria ou aprovação de um template pela Meta.
- No upsell, ofereça uma versão superior do item ou serviço. No cross-sell, ofereça um complemento. Na série padrão, use cashback no cross-sell e frete grátis no upsell, com a condição fornecida no briefing. Use preços, prazos e condições fornecidos pelo usuário ou identifique os dados como ilustrativos.

## Geração visual

- Use o layout quadrado 1:1, logo Nextags com selo AI em azul e nome em preto, fundo claro com lilás discreto e o WhatsApp em destaque. Use a [peça de referência](assets/pedido-aprovado.png) quando não houver outra arte aprovada.
- No iPhone 17, mostre a frente e a tela inteira. Para notebook, use tela horizontal e escala natural. Para totem interativo, use tela vertical com pedestal visível. Varie a pose ou cenário quando fizer parte do pedido.
- Ao revisar uma arte, preserve a composição aprovada e altere os elementos pedidos. Confira visualmente logo, proporções, nomes, acentos, dígitos e botões. Se o gerador errar a grafia, corrija a região do texto ou componha o texto separadamente, conforme as ferramentas disponíveis.
- Para um prompt portátil, entregue os insumos e a descrição visual de forma que possam ser usados tanto por um LLM com geração de imagens quanto por um gerador separado.

## Referências e entrega

- [Modelos de mensagens](references/modelos-transacionais.txt) para copiar ou adaptar textos e botões.
- [Prompt portátil](references/prompt-geracao.txt) para gerar peças em outras ferramentas.
- Quando solicitado um pacote final, entregue os PNGs com nomes claros, prompt mestre e TXT com os modelos e variáveis. Use as últimas versões aprovadas e deixe as peças de resenha de fora do pacote profissional. A skill prepara artes e modelos. Disparo ou publicação requer pedido explícito.

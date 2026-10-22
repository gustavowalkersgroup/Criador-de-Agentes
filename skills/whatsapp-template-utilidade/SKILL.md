---
name: whatsapp-template-utilidade
description: "Criar e cadastrar modelos (templates) de WhatsApp no WhatsApp Manager da Meta na categoria Utilidade (coringa, carrinho, PIX, reativação, transacionais e disparos). Use ao cadastrar, variar ou analisar templates e ao entender por que a Meta reclassificou um modelo para Marketing."
---

# Templates WhatsApp aprovados como Utilidade (método Walkers)

Base: modelos aprovados e reclassificados lidos em contas de clientes NexTags e em testes internos. Idioma sempre Portuguese (BR). Versão 1: será refinada conforme chegarem mais modelos aprovados.

## Regra central
A Meta decide a categoria olhando principalmente (1) o texto fixo do corpo e (2) os EXEMPLOS das variáveis. Por isso:
- Texto fixo curto e neutro: saudação, variáveis, assinatura. Sem palavras comerciais (oferta, desconto, ganhou, cashback, confira, compre, quer ver?).
- As variáveis carregam o conteúdo (frases inteiras são aceitas no formato coringa).
- Os exemplos têm cara de aviso de conta, pedido, cadastro, rastreio ou agendamento.
- Exemplos com linguagem comercial ou genéricos ('nome', 'mensagem') levam à reclassificação para Marketing.

## Padrões que passaram (Utilidade, com entregas reais)
| Tipo | Texto fixo | Exemplos | Botão |
|---|---|---|---|
| Transacional real (pedido enviado) | 'Seu pedido {{2}} foi enviado e já está em transporte. Código: {{3}}. Prazo: {{4}}' | Ana Paula / #57275 / NL123456789BR / 5 dias | Rastrear Pedido + Preciso de Ajuda |
| Pedido aprovado com confirmação | 'Parabéns! O seu pedido {{1}} foi aprovado. Você confirma esse pedido feito por {{2}}?' | X2645 / nome / rodapé com a marca | Confirmar + Preciso de Ajuda |
| Coringa | 'Olá {{1}}, tudo bem? {{2}} {{3}} Atenciosamente, equipe X' | aviso de entrega ('Seu produto saiu para entrega') ou agendamento | Continuar |
| Carrinho | 'Atualização sobre {{2}}. O {{3}}. Clique no botão abaixo para receber' | aviso de cadastro/agendamento (SNS, exame agendado) | Continuar ou Pagar agora |
| PIX | 'Seu pedido de {{2}} {{3}} Clique no botão abaixo para receber o código' | 'pedido aprovado e será enviado' + endereço | PIX copia-e-cola |
| Reativação/confirmação | 'Um tempo atrás você realizou {{2}}. Falamos com {{3}} neste telefone?' | 'um cadastro no nosso sistema' / nome completo | Sim + Não |

Capa com imagem ou vídeo não muda a categoria. Rodapé com 'Digite STOP para sair' ou 'MARCA | BRASIL' não impediu aprovação.

## O que foi reclassificado para Marketing (evitar)
- Exemplo com conteúdo de oferta: 'jeito lindo de completar esse look, e você ganhou R$ de cashback'.
- Fixo com convite comercial: 'Quer ver as sugestões?', 'Toque no botão abaixo e confere qual é', 'saber mais'.
- Exemplos vazios ou genéricos ('nome', 'mensagem') e fixo só com 'Aguardo seu retorno'.

## Cadastro no WhatsApp Manager (passo a passo)
1. Modelos de mensagens > Criar modelo > aba Utilidade > tipo Padrão > Avançar.
2. Nome: minúsculas com underline, prefixo wl_ e sufixo de versão (wl_tipo_v2, v3...). Idioma: pesquisar 'Portuguese' e escolher Portuguese (BR).
3. Amostra de mídia: Nenhum, Imagem ou Vídeo. Para anexar, localizar o input de arquivo na página e enviar o arquivo (JPG para imagem; MP4 H.264/AAC curto para vídeo). Não clicar no botão de upload.
4. Corpo: o editor duplica chaves ao digitar {{1}} (vira {{1}}1}}). Definir o texto por script, usando o setter nativo do textarea e disparando o evento input. Fazer o mesmo para exemplos e rodapé.
5. Exemplos: um por variável, sempre diferentes entre as versões (pedido enviado, rastreio X54646, entregue, pagamento aprovado, cadastro aprovado).
6. Rodapé opcional. Botão: Adicionar botão > Personalizado > trocar 'Quick Reply' pelo texto.
7. Validade da mensagem: deixar desligada, salvo pedido contrário.
8. Enviar para análise. Se aparecer 'A categoria não corresponde', MANTER Utilidade selecionada e clicar Continuar (nunca trocar para Marketing sem ordem).
9. Se a Meta reclassificar para Marketing, há 24h para pedir reanálise de categoria; o responsável pela conta pede depois.

## Lotes de teste
Quando pedido um lote, gerar variações sutis do mesmo modelo (nome v2, v3...), mudando exemplos, saudação ('Olá' / 'Olá,'), 'Clique' / 'Toque' e texto do botão. Padrão: 3 sem mídia, 3 com imagem, 3 com vídeo. Antes de enviar, ler os valores do formulário para conferir.

## Riscos (avisar o responsável pela conta)
- Exemplo que não representa o envio real pode levar a reclassificação posterior, queda de qualidade do número e restrição da conta (já houve restrição de 30 dias em outro cliente).
- Mensagem de pós-venda ('seu pedido foi aprovado') enviada com pagamento ainda pendente pode confundir o cliente e gerar bloqueios.
- Não alterar nem enviar nada em conta de cliente sem pedido explícito; ler o editor e sair sem salvar.

## Conformidade
- Use Utilidade só para conteúdo realmente transacional ou de relacionamento já em andamento (pedido, pagamento, entrega, cadastro, agendamento, confirmação). O formato coringa serve para variar a mensagem real, não para fazer oferta passar por aviso.
- Os exemplos das variáveis precisam representar o que será enviado de verdade. Divulgação, cupom ou convite de compra vai em modelo de Marketing.
- Reclassificações e quedas de qualidade repetidas podem limitar o número, então teste em lote pequeno.

## Integração com as outras skills
- Disparos transacionais pelo webhook (pedido, rastreio, PIX): quem monta o endpoint é `nextags-webhook-builder`; esta skill cuida só do modelo aprovado na Meta.
- Custo: modelo de Utilidade enviado fora da janela de 24h é cobrado, e dentro da janela também passou a ser cobrado desde 01/10/2026. Para a conversa em si (mensagens de serviço do agente de IA), use `nextags-prompt-octobercut`.

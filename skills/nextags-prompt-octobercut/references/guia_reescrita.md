# Guia de reescrita de prompt (OctoberCut)

Passo a passo para adaptar um prompt NexTags existente. Trabalhe seção por
seção; não reescreva o prompt inteiro de uma vez, senão a persona se perde.

## 0. Antes de mexer

- Rode `octobercut.py audit` e guarde o resultado como "antes".
- Liste os cenários principais do agente (abertura, diagnóstico, vitrine,
  checkout, status de pedido, troca/devolução, handoff, encerramento) e conte
  quantas mensagens a empresa manda em cada um hoje. Isso vira a tabela de
  economia do relatório.

## 1. Formato JSON

- Insira o bloco de `bloco_octobercut.md` logo depois do bloco oficial de
  formato NexTags.
- Troque a descrição antiga do typing indicator ("use 4 para pausas
  naturais") por: "o typing indicator existe, mas não use: cada bolha é
  cobrada".
- Mantenha a explicação de que `\n` quebra linha na mesma bolha. Ela passa a
  ser a forma principal de organizar a resposta.

## 2. Exemplos JSON

Reescreva **todos** os exemplos no padrão de 1 mensagem. Prioridade:

1. Exemplos com typing `4` entre textos → juntar num `text` com `\n\n`.
2. Texto seguido de button template → texto vai para o `text` do botão.
3. Imagem + texto + botão → imagem + botão (texto no `text` do botão).
4. Pergunta de follow-up em bolha própria → para dentro do `text` anterior.
5. Exemplo de "pausa natural" ou "deixa eu verificar" → apagar ou reescrever
   como resposta única.

Use `octobercut.py merge` num exemplo para gerar a versão fundida
automaticamente e depois revise o texto à mão (ajuste conectivos, tire
repetição de saudação).

## 3. Identidade e abertura

- A frase-assinatura continua sendo o começo da primeira mensagem.
- Logo depois dela, na mesma bolha: o que o agente faz (3–4 caminhos) e uma
  pergunta com opções ou o pedido do dado necessário.
- Remova "pergunte o nome UMA vez". Substitua por: "se `{{first_name}}` for
  inválido, cumprimente sem nome e siga".

## 4. Framework de conversa / diagnóstico

- Troque "uma pergunta por vez" por "uma rodada de perguntas agrupadas".
- Diagnóstico de vendas: no máximo **uma** rodada antes de indicar produto.
  Se o cliente já disse a dor na primeira mensagem, indique direto.
- Atalhos de lead quente ("quero o link", "quanto custa") pulam o
  diagnóstico.

## 5. Vitrine e checkout

- Produto: 1 imagem + 1 button template. Descrição, preço, pergunta seguinte
  e CTA no mesmo template.
- Variações (cores, tamanhos, kits): listar em texto dentro do template;
  fotos só se pedirem.
- Vários produtos: até 2–3 indicações numa mensagem de texto só, ou
  carrossel (≥ 2 cards, validar render no WhatsApp), ou fluxo de catálogo.
- Checkout: frase de confirmação vai no `text` do button template.

## 6. Suporte (rastreio, troca, segunda via)

- Peça todos os identificadores de uma vez (CPF + nº do pedido).
- Resposta de status numa bolha só: status, previsão, link e fechamento.
- Nada de "vou consultar" antes da consulta.

## 7. Handoff

- O trio canônico de handoff continua obrigatório.
- Se o fluxo de destino já fala com o cliente: só `actions`.
- Se não fala: 1 bolha curta de transição.

## 8. Encerramento

- Fechamento ("qualquer coisa, tô por aqui") no fim da última resposta útil.
- Não mandar mensagem de despedida avulsa quando o cliente agradece. Se o
  cliente só disse "obrigado", uma resposta curta e única basta; se o prompt
  já previa não responder agradecimento final, mantenha.

## 9. Depois de mexer

- `octobercut.py audit` sem bloqueios.
- `nextags-prompt-fixer` sem violação nova.
- Se possível, `nextags-webchat-tester` nos cenários principais, contando as
  bolhas reais de cada resposta.
- Relatório com a tabela "cenário | antes | depois | economia".

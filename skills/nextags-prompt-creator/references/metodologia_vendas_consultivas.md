# Metodologia de Vendas Consultiva

> Leia esta referência **antes de escrever a seção 6B (CAMADA DE VENDAS)** do
> `prompt_skeleton.md`, sempre que o tipo do agente for **Vendas/consultora**,
> **Comercial/SDR** ou **Misto**. Ela existe porque a seção 6B, sozinha, tende a
> sair genérica: "cumprimenta → empurra produto → menciona cupom". As tabelas
> abaixo dão critério de avanço, gancho por etapa e regra de gatilho ético —
> o que transforma um vendedor de catálogo num consultor.
>
> **Fontes:** síntese aplicada de SPIN Selling (Rackham), The Challenger Sale
> (Dixon & Adamson), Influence (Cialdini), Never Split the Difference (Voss),
> Building a StoryBrand (Miller) e Inbound Selling (Signorelli). São frameworks
> profissionais e heurísticas — **não são citação literal nem garantia de
> conversão para todo produto/canal**. Adapte ao negócio real do cliente.

---

## 1. Princípio central: diagnosticar antes de demonstrar

A recomendação de produto responde a uma necessidade **confirmada**, não a uma
suposição do agente. Antes de indicar, o agente precisa saber, no mínimo, **um
critério real** (uso, ocasião, o que mais pesa na decisão) — vindo do que o
cliente disse, nunca inventado.

Duas exceções em que se pula direto pra recomendação:
- O cliente já citou o produto/critério explícito ("quero a legging preta P").
- É lead de anúncio que clicou num produto específico — aí o "diagnóstico" é
  1 pergunta de confirmação, não uma sabatina.

**O objetivo não é fabricar dor pra criar pressão** — é verificar se existe
encaixe real e se a recomendação é proporcional. Quando não há encaixe, dizer
isso é parte do papel do agente, não uma falha dele.

---

## 2. Quando usar cada framework

| Framework | Usar quando | Cuidado ao aplicar |
|---|---|---|
| **SPIN** (Situação → Problema → Implicação → Necessidade) | Descoberta antes de recomendar — mais relevante em B2B, ticket alto, serviço | Não é interrogatório: 1 pergunta por turno, guiada pelo que já foi dito |
| **Challenger** (hipótese/insight) | Cliente ainda não sabe bem o que precisa; há "status quo" caro | O insight tem que ter fonte e ser hipótese testável — nunca afirmado como fato |
| **Voss** (rotulagem, perguntas calibradas) | Objeção, hesitação, "vou pensar", negociação de prazo/preço | Rótulo é hipótese ("parece que..."), nunca diagnóstico definitivo da emoção do cliente |
| **StoryBrand** (cliente = herói, marca = guia) | Frases de abertura e CTA — clareza de quem resolve o quê | Heurística de clareza, não prova de conversão. Não prometer transformação que o produto não sustenta |
| **Cialdini** (gatilhos de influência) | Revisar como evidência/prova social/urgência são apresentadas | Gatilho só é válido se verdadeiro e verificável — nunca depoimento ou contagem regressiva inventados |
| **Inbound Selling** (identify/connect/explore/advise) | Lead que já pesquisou ou chegou pelo anúncio/direct — a maioria do tráfego real | Clique em anúncio/produto é indício de interesse, não prova de intenção de compra — ainda assim diagnostica |

Regra de seleção rápida: **SPIN** dá a lógica de pergunta; **Challenger** só
entra quando há uma hipótese bem sustentada; **Voss** serve pra objeção, nunca
pra "vencer" o cliente; **StoryBrand** simplifica a mensagem; **Cialdini**
audita a apresentação de evidências reais.

---

## 3. Funil de 7 etapas (adaptado a chat/JSON, turno a turno)

> O agente não conduz a conversa inteira de uma vez — ele decide, a CADA turno,
> em que etapa está e responde de acordo. O critério de avanço é o que
> diferencia "fez uma pergunta" de "avançou de verdade".

| Etapa | Objetivo | O agente faz neste turno | Critério de avanço |
|---|---|---|---|
| **1. Abertura** | Responder ao gatilho que trouxe o cliente e ganhar espaço pra uma pergunta | Reconhece a origem (produto, anúncio, dúvida) + 1 pergunta objetiva | Cliente respondeu ou já disse o que quer |
| **2. Diagnosticar** | Entender uso/objetivo antes de indicar | Pergunta o suficiente pra indicar com segurança — nunca despeja catálogo | Há critério mínimo pra recomendar |
| **3. Aprofundar** (só se necessário) | Confirmar o que mais pesa na decisão | Pergunta prioridade (preço, prazo, modelo) só se a resposta ainda não for óbvia | Critério declarado pelo cliente, não suposto pelo agente |
| **4. Validar** | Confirmar entendimento antes de recomendar | Resume em 1 frase e pede correção | Cliente confirmou ou corrigiu |
| **5. Indicar** | Recomendar com evidência, proporcional ao critério | Consulta a tool, mostra 1-2 opções que respondem ao critério | Cliente vê a recomendação como resposta ao que pediu (ou o agente diz que não há encaixe) |
| **6. Conduzir** | Transformar interesse em próximo passo, sem fechamento presumido | CTA proporcional (link, pergunta, aviso de indisponibilidade) | Cliente segue o link, pede mais informação, ou adia — as três são avanço válido |
| **7. Follow-up** | Retomar com motivo real, preservando confiança | Só reengaja com gatilho real (carrinho, promoção real) — nunca "só passando" | Cliente responde, ou pede pra não ser mais contatado (opt-out respeitado) |

**Nota B2B/SDR:** nesse tipo, as etapas 3-4 pesam mais (mapear quem decide,
critério de orçamento/prazo) e a Etapa 6 vira estágio de pipeline
(`set_field_value` monotônico) em vez de link direto — combine esta tabela com
a Árvore de Decisão por Turno (`prompt_skeleton.md` §8D).

**Nota e-commerce/venda rápida:** a Etapa 3 costuma ser pulada — o critério da
Etapa 2 já basta pra recomendar (ex.: "uso diário" → linha básica).

---

## 4. Ganchos por etapa (biblioteca de exemplos — adapte ao tom da marca)

Escolha 2-3 por etapa, nunca encadeie duas perguntas na mesma mensagem.

| Etapa | Ganchos de exemplo |
|---|---|
| Abertura | "Oi! Buscando pra uso do dia a dia ou pra uma ocasião específica?" · "Vi que você chegou pelo anúncio de {produto} — quer ver os modelos mais pedidos ou já tem um em mente?" |
| Diagnosticar | "Pra qual ocasião você tá buscando?" · "Já usou algo parecido antes ou é a primeira vez?" |
| Aprofundar | "O que mais pesa pra você: preço, prazo ou o modelo específico?" · "Tem alguma cor ou tamanho que já sabe que funciona?" |
| Validar | "Só confirmando: você quer algo mais {X}, é isso?" |
| Indicar | "Baseado no que você me disse, esse aqui atende — quer ver?" · "Pelo que descreveu, talvez {produto A} sirva melhor que {produto B} — te mostro os dois?" |
| Conduzir | "Fica assim: {link}. Quer que eu separe outra opção também?" · "Qualquer dúvida de tamanho, é só chamar." |
| Follow-up | "Vi que você chegou a olhar {produto} — ainda tá pensando nele?" · "Se não for mais prioridade, posso parar de retomar por aqui, sem problema." |

---

## 5. Gatilhos de influência — só verdadeiros e verificáveis

> Aplicação de Cialdini: um gatilho só é legítimo quando é **verdadeiro,
> relevante para a decisão do cliente e verificável**. Gatilho fabricado
> (depoimento inventado, contagem regressiva falsa, "só hoje" sem base real)
> é proibido — mina confiança e pode configurar propaganda enganosa.

| Gatilho | Fonte permitida no prompt gerado |
|---|---|
| **Reciprocidade** | Entregar algo de valor real (comparação, dica, resposta completa) antes de pedir decisão — nunca criar dívida artificial |
| **Prova social** | Só caso/depoimento que está na base de conhecimento (vindo do briefing/site, autorizado pelo cliente) |
| **Autoridade** | Só credencial ou tempo de mercado real da marca (do briefing/site) |
| **Compromisso** | Pedir um passo pequeno e reversível ("quer ver o modelo?") antes de pedir a compra |
| **Escassez/urgência** | Só o que está em 📣 AVISOS ATIVOS ou é regra confirmada do site (ex.: frete grátis com prazo real, estoque realmente baixo informado pela tool) |

Se a informação de prova social, autoridade ou escassez **não estiver
confirmada** no briefing/site/AVISOS ATIVOS: **não preencha a lacuna** — omita
a frase em vez de inventar. Isso já está coberto pelas regras 8 e 14 do
anti-alucinação (seção 3/4 do skeleton); esta tabela só torna explícito o
motivo por trás de cada uma.

---

## 6. Objeções: rotular antes de contornar

> Técnica de Voss: nomeie a preocupação em 1 frase curta **antes** do contorno.
> O rótulo é uma hipótese — se o cliente corrigir, siga a correção dele. Pular
> direto pro contorno faz o cliente sentir que não foi ouvido.

| Objeção | Rótulo (1 frase, hipótese) | Contorno (só depois do rótulo) |
|---|---|---|
| "Tá caro" | "Parece que o que pesa é o investimento, é isso?" | Valor/benefício real — nunca desconto inventado |
| "Já tentei de tudo" | "Parece que outras opções não resolveram, certo?" | Diferencial real do produto (da base de conhecimento) |
| "Funciona mesmo?" | "Parece que o receio é não ter certeza do resultado, é isso?" | Prova social autorizada — nunca inventada (ver seção 5) |
| "Vou pensar" | "Faz sentido. O que ainda falta pra decidir?" | Oferecer informação específica que falta — nunca pressionar |
| "Preciso falar com outra pessoa" (B2B) | "Como essa decisão costuma ser tomada aí?" | Oferecer resumo compartilhável, sem forçar o contato a "vender" internamente |

---

## 7. Antes vs. Depois (adaptado a bot NexTags)

| Situação | Antes (seco ou precipitado) | Depois (consultivo) |
|---|---|---|
| Interesse inicial mínimo | "Temos sim." | "Temos sim! Pra te indicar certinho: é pro dia a dia ou pra treino pesado?" |
| Apresentação precoce | Mostra carrossel inteiro sem perguntar nada | Faz 1 pergunta de critério, DEPOIS consulta a tool e mostra 1-2 opções |
| Abertura fria (anúncio) | "Oi, quero te apresentar nossa coleção nova!" | "Oi! Vi que você chegou pelo anúncio da coleção nova — quer ver os mais pedidos ou já tem um em mente?" |
| Objeção de preço | "Tá com desconto, é barato!" | "Entendo, o investimento precisa valer a pena. O que pesa mais: parcelamento ou comparar com outro modelo?" |
| Prova social | "Milhares já compraram!" | "Esse é um dos modelos mais pedidos da coleção atual" (só se a base confirmar — senão, omitir a frase) |
| Fechamento presumido | "Então já vou confirmar seu pedido?" | "Fica assim: {link}. Quer que eu separe outra opção também, ou prefere seguir com esse?" |
| Follow-up sem contexto | "Oi, só passando, viu?" | "Vi que você chegou a ver o modelo X ontem — ficou alguma dúvida de tamanho ou cor?" |

---

## 8. Checklist rápido antes de cada resposta de vendas

- Respondi com base no que o cliente disse, sem presumir dor ou urgência?
- Fiz no máximo 1 pergunta principal neste turno?
- Só recomendei depois de ter critério mínimo (ou o cliente já pediu produto específico)?
- Todo gatilho de prova social/autoridade/escassez usado é real e vem da base ou de AVISOS ATIVOS?
- O próximo passo é claro (link, pergunta ou aviso), sem fechamento presumido?
- Se não há encaixe real, eu disse isso em vez de empurrar uma recomendação fraca?

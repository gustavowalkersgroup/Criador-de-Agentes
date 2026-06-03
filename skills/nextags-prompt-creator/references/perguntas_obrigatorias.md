# Checklist de Perguntas Obrigatórias

> Antes de gerar o prompt, valide TODAS as perguntas abaixo com o humano. Cada
> uma é uma decisão de produto que **só o humano pode tomar**. Se ficar sem
> resposta, **mantenha como pendência explícita** no prompt final (placeholder
> `<...>`) e liste no relatório — **nunca chute** o valor.

---

## Como conduzir as perguntas

Use `ask_user_input_v0` para perguntas de múltipla escolha (mais ergonômico
para mobile). Use prosa para as abertas (IDs, URLs, listas). **Agrupe em até
3 perguntas por chamada do tool** — esse é o limite. Se precisar de mais,
faça uma segunda rodada após a primeira ser respondida.

Sugestão de divisão por rodadas:

- **Rodada 1 — Persona e tom:** tom de voz, público-alvo, canais.
- **Rodada 2 — Tools e fluxos:** uso de MCP, IDs de fluxos, fluxo de
  transferência humana.
- **Rodada 3 — Conteúdo:** mídias, restrições comerciais, tratamento de
  reclamações.

Pule rodadas cujas respostas já estejam no briefing.

---

## 1. Persona e voz

### 1.1 Nome do agente
Exemplo de pergunta: "Como o agente vai se chamar?"
Tipo: aberta.

### 1.2 Tom de voz
Pergunta multipla-escolha:
```
options: ["Formal e corporativo", "Informal e próximo", "Consultivo/técnico",
          "Energético/motivacional", "Acolhedor/empático", "Outro (descrever)"]
```

### 1.3 Público-alvo
Pergunta aberta: "Quem é o cliente típico? (idade aproximada, perfil, dor
que está resolvendo)"

### 1.4 Canais de atendimento
```
type: multi_select
options: ["WhatsApp", "Instagram Direct", "Facebook Messenger",
          "Site/webchat", "TikTok"]
```

---

## 1.0 Tipo de agente (PERGUNTA-CHAVE — define quais seções gerar)
```
options: ["Vendas/consultora", "SAC/pós-venda", "Triagem/roteador",
          "Comercial/SDR (B2B)", "Misto (vendas + SAC)"]
```

## 1.5 Perguntas condicionais por tipo

**Se VENDAS:** frase de abertura assinatura? produto-hero a priorizar? há cupom —
e em que momento mencionar? lead de anúncio entra direto no produto ou diagnóstico?

**Se SAC:** quais MOTIVOS de contato atende (rastreio/troca/devolução/avaria/...)?
há flow_id por motivo ou um geral? qual a tool/sistema que é fonte de verdade de
ENVIO (≠ e-commerce)? há fluxo de NPS pós-atendimento (flow_id)?

**Se COMERCIAL/SDR:** quais campos do CRM capturar via set_field_value (pipeline,
resumo, faturamento)? horário de expediente?

**Todos:** há horário de atendimento humano (expediente)? respostas fixas para
casos sensíveis (atacado, parceria, vagas)?

---

## 2. Tools e fluxos

### 2.1 O agente vai usar tools (MCP)?
```
options: ["Sim — vou listar quais", "Não usa tools",
          "Não sei ainda (pendência)"]
```

Se "Sim", pergunta aberta: "Liste as tools disponíveis e o que cada uma faz
(nome + 1-2 linhas descrevendo input/output)."

### 2.2 ID do fluxo de transferência humana
Pergunta aberta: "Qual o `flow_id` configurado na NexTags para encaminhar
para um atendente humano? (algo como `flow_12345` ou similar)"

⚠️ Se o humano não souber agora: **mantenha o placeholder
`<ID_DO_FLUXO_TRANSFERENCIA>` no prompt** e liste como pendência crítica.

### 2.3 Outros fluxos específicos?
Pergunta aberta: "Há outros fluxos da NexTags que o agente deve disparar
em situações pontuais? (ex.: fluxo de carrinho abandonado com ID `flow_xxx`,
fluxo de avaliação pós-atendimento, etc.) Liste cada um."

⚠️ Mesma regra: sem ID confirmado → placeholder + pendência.

---

## 3. Conteúdo e regras

### 3.1 Restrições comerciais
Pergunta aberta: "Há regras comerciais ou restrições absolutas? Ex.: 'não
oferecer desconto fora de PIX', 'nunca prometer cura', 'não comparar com
concorrentes', etc. Liste tudo."

### 3.2 Tratamento de reclamações
```
options: ["Tentar resolver com autonomia até 2 tentativas, depois transferir",
          "Sempre transferir reclamações para humano",
          "Resolver com autonomia, transferir só Procon/processo",
          "Outro (descrever)"]
```

### 3.3 Mídias disponíveis
Pergunta aberta: "Há imagens, áudios ou vídeos para o agente usar nas
respostas? Liste cada URL e em que situação usar (ou diga que vem das tools
dinamicamente, ou que não tem)."

⚠️ Sem URLs → o prompt **não** pode prometer envio de mídia (caia em texto
simples).

---

## 4. Verificação final antes de gerar

Antes de chamar `analyze_prompt.py`, confirme com o humano:

- ✅ Briefing entendido
- ✅ Site escaneado (homepage + páginas-chave)
- ✅ Inconsistências entre briefing e site reportadas
- ✅ Todas as 3 rodadas de perguntas respondidas (ou marcadas como pendência)
- ✅ Pelo menos um `flow_id` de transferência humana fornecido (ou explicitamente
  marcado como pendência crítica)

Só então prossiga para a geração + auditoria.

---

## O que NÃO perguntar

Não desperdice rodada com coisas que o briefing/site já cobrem:

- Endereço, contatos, horário → vem do site
- Catálogo de produtos → vem do site (e/ou tools)
- Políticas (troca, garantia, frete) → vem do site
- Diferenciais da marca → vem do site
- "Quem somos" → vem do site

Se algo dessas coisas não estiver no site E não estiver no briefing, **aí sim**
pergunte — mas só nesse caso.

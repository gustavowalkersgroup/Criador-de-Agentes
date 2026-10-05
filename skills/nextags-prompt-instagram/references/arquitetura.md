# Arquitetura da automação de comentários (NexTags)

## 1. Configuração do gatilho de comentário
Tela "Instagram > comentários":
- **Acompanhar comentários em:** Todas as publicações.
- **Envie mensagem privada com:** AI Agent -> agente `Classificação DM`.
- **Responder ao comentário com um comentário público:** AI Agent -> agente `Prompt INSTAGRAM`.
- **Responder a:** Todos os comentários.
- Mais opções (decisão do cliente): "Responda apenas uma vez a cada usuário em uma postagem" (limita também a resposta pública), "Excluir comentários com palavras-chave" (spam), "Responder depois" (Imediatamente).
- Observação: dá para usar `Fluxo` direto na mensagem privada, mas o agente classificador é necessário para decidir e gravar os campos.

## 2. Agente 1: Prompt INSTAGRAM (resposta pública)
- Saída: texto puro, 1 a 3 frases, começando com `@autor`.
- Variáveis: `{{ig_user_name}}`, `{{username}}`, `{{first_name}}`, `{{last_fb_comment}}`, `{{last_commented_post_text}}`.
- MCP: só tools de catálogo (busca e detalhe). Nunca tools de cliente/pedido.
- Responde todos os comentários; reclamação é amenizada em público e levada ao direct.
- Template: `assets/prompt-resposta-publica.md`.

## 3. Agente 2: Classificação DM
- Não fala com o cliente (`"messages": []`).
- Decide `CHAMAR` ou `NAO` e escreve `resumo_atendimento` (para a IA de vendas).
- Saída (NexTags):
  - CHAMAR: `set_field_value resumo_atendimento` -> `set_field_value decisao_dm=CHAMAR` -> `send_flow {{FLOW_ABERTURA}}`.
  - NAO: só `set_field_value decisao_dm=NAO`.
- Template: `assets/prompt-classificador.md`.

## 4. Fluxo de abertura ("Filtrar DM")
Blocos, em ordem:
1. **Condição:** `decisao_dm` é `CHAMAR` (segurança extra; saída "não corresponde" fica sem destino).
2. **Ações #1 > OpenAI:** `Gerar texto - Agentes`, agente = prompt de vendas do cliente, **Mensagem do usuário = mini prompt** (`assets/mini-prompt-fluxo.md`), salvar resposta no campo `resposta_ia`, `Lembrar conversa` = Sim.
3. **Enviar Mensagem:** `{{resposta_ia}}`.
Por que assim: o mini prompt é uma instrução injetada no agente de vendas (no lugar da fila de mensagens). O agente de vendas já traz persona, MCP e regras; o mini prompt só diz "esta conversa nasceu de um comentário".

## 5. Campos personalizados (CUFs) necessários
| Campo | Quem grava | Uso |
|---|---|---|
| `decisao_dm` | Classificação DM | `CHAMAR`/`NAO`, lido pela condição |
| `resumo_atendimento` | Classificação DM | briefing para a IA de vendas |
| `resposta_ia` | Ações > OpenAI | texto da abertura enviado ao cliente |
| `motivo_transferencia` | IA de vendas | parcerias / ugc / influencer / motivo do pipeline |
| `prioridade_pipeline` | IA de vendas | baixa / media / alta |
| `resumo_pipeline` | IA de vendas | resumo para o humano |

## 6. Parceria, UGC, influencer e reclamação (dentro da abertura)
Ordem: grava `motivo_transferencia` -> `prioridade_pipeline` -> `resumo_pipeline` -> `send_flow {{FLOW_TRANSFERENCIA}}` por último.
Reclamação: empatia, sem defender a marca nem prometer solução; `prioridade_pipeline` = `alta`.

## 7. Limites da Meta (conferir sempre)
- Resposta privada: 1 mensagem por comentário, até 7 dias; em Live, só durante a transmissão.
- Depois que o cliente responde, abre janela de 24 h.

## 8. Variáveis NexTags usadas
`{{ig_user_name}}`, `{{username}}`, `{{first_name}}`, `{{last_fb_comment}}`, `{{last_commented_post_text}}`, `{{last_post_id}}`, `{{last_comment_id}}`, `{{decisao_dm}}`, `{{resumo_atendimento}}`, `{{resposta_ia}}`.
Se alguma não resolver no gatilho, o prompt trata como ausente (nunca inventa).

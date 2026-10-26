# Modo nativo do AI Hub e lições da skill oficial da NexTags

Fonte: skill oficial `criar-agente-ia` (plugin `guiipego/nextags`, analisada em 26/10/2026) e a
documentação `help.nextags.com.br/tutoriais/ia/` (`respostas-elaboradas`, `acoes-do-agente`,
`escrever-o-prompt`, `agente-padrao`, `testar-agente`) e `docs.nextags.com.br/ia/respostas-do-agente-em-json/`.

## O que é

A plataforma passou a oferecer duas peças que fazem o trabalho do JSON no prompt:

| Peça | Onde | O que faz |
|---|---|---|
| **Tipo de resposta da IA** | Ajustes do agente | Liga Texto, Imagem/Vídeo/Áudio/Arquivo, Texto + Botões e Carrossel. A NexTags converte por trás; o prompt só diz **quando** usar cada tipo e não pede JSON. |
| **Ações de IA** | Editor do agente | Regras com título, **Quando** (situação da conversa, texto livre) e **O que a IA deve fazer?** (lista ordenada de ações). |
| **Prompt da ação** | Ícone de ajustes das Ações de IA | Instruções gerais para decidir quais regras disparam e como preencher valores. |

Ações disponíveis: Enviar Fluxo, Atribuir/Remover atribuição, Transferir para humano, Transferir para bot,
Adicionar/Remover Etiqueta, Definir/Limpar Campo Personalizado, Seguir/Remover do acompanhamento, Arquivar,
Bloquear contato.

## Status no nosso método

O padrão Walkers **continua** sendo o JSON de runtime com `send_flow` e o trio canônico (`motivo_transferencia`,
`prioridade_pipeline`, `resumo_pipeline`). O modo nativo é uma **alternativa a pilotar**, não um substituto:
não migrar agente em produção sem teste A/B.

Mapeamento do handoff para uma regra de Ações de IA (mesma ordem do trio): Definir Campo `motivo_transferencia`
→ Definir Campo `prioridade_pipeline` → Definir Campo `resumo_pipeline` → Enviar Fluxo (pipeline).

Diferenças e riscos a testar antes de adotar:
- A regra dispara por **leitura da conversa** (o "Quando" é avaliado contra a conversa e a resposta atual), não por
  uma ação que o próprio agente escreveu. Se a regra não casar, **não há handoff e não há erro**.
- Mais de uma regra pode disparar na mesma resposta.
- Campo continua sendo sobrescrito: o risco de estado antigo (stale) continua.
- O OctoberCut (uma resposta = uma mensagem) depende de como a NexTags converte o tipo de resposta: medir as bolhas.

## Lições da skill oficial que valem nos dois modos

1. **Aprovação vale só para o último resumo.** O resumo enviado não é aprovação; o "sim" do cliente ao resumo mais
   recente é. Se ele mudou algo depois, enviar resumo novo.
2. **Frase de transferência fixa.** Se o disparo depende de texto, a mensagem do agente tem que ser fixa e o
   "Quando" cita entre aspas o começo exato dela (o validador deles confere que a frase existe no prompt).
3. **Um mecanismo de transferência só.** A função `connect_user_to_human` ligada junto com regras de Ações de IA que
   transferem pode transferir duas vezes, ou sem etiqueta e sem campos. Escolher um.
4. **Não automatizar Bloquear contato nem Arquivar.** Um erro afeta cliente real.
5. **Campo condicional em regra separada** (ex.: endereço só na entrega), para que um caso diferente não apague o
   valor salvo.
6. **Ferramenta ligada precisa de instrução no prompt** (Image Reader, Document Reader, Web Search, Arquivos,
   Funções, MCP): quando usar e o que nunca fazer (ex.: não confirmar pagamento por comprovante).
7. **`**` no corpo do prompt tende a ser copiado.** O modelo imita a formatação que vê e o `**` sai literal no
   WhatsApp. Destacar com MAIÚSCULAS ou *um asterisco*. (Não é problema hoje na Degan: só 8 ocorrências no
   vendas v3.0, nenhuma no SAC e no Instagram.)
8. **Imagem no WhatsApp: png ou jpeg até 5 MB** (WebP não chega como imagem). O `nextags-json-fixer` já cobre isso.
9. **`[A DEFINIR]` em vez de inventar:** o que o cliente não soube responder vira placeholder e o agente diz que a
   equipe confirma.

## Decisão do dono (26/10/2026): não mover o bloco dinâmico para o fim

A skill oficial põe `{{current_user_time}}`, `{{first_name}}` e os CUFs no **fim** do prompt, para favorecer o cache de
prefixo do provedor. O dono avaliou e decidiu que mover o `## DADOS DESTA CONVERSA` não muda nada: **fica no início,
como no skeleton**. Não criar cópia de teste com o bloco no fim.

**Histórico (`{{chat_history*}}`): confirmado pelo dono em 26/10/2026.** O agente **já acumula o histórico** conforme conversa
com a pessoa. A variável só serve para puxar o histórico **uma vez** (resumir, ou uma automação específica), e em prompt
sem memória (roteador/revalidador). Num agente conversacional ela duplica tokens a cada chamada: **não usar**. O analisador
avisa (`historico_no_prompt`). Os prompts da Degan traziam a variável e a chamavam de "única memória"; as versões vendas v3.1
e SAC v1.8 a removem.

## Configuração recomendada pela skill oficial (agente sem MCP)

GPT-6 Luna, Max tokens 32768, Reasoning effort Média, Verbosity Baixa, os 4 tipos de resposta ligados. A
temperatura não existe mais no painel (padrão do provedor, ~0,98). O usuário configura no painel; nunca enviar
`model` nem `max_output_tokens` pela API (incidente de 23/10/2026).

## Prompt da ação (padrão da plataforma, em inglês)

```
- Match a rule only when its description is clearly satisfied by the conversation.
- Do not match a rule based on assumptions.
- Multiple rules may match in the same response.
- When a matched rule requires values from the conversation, populate them using information available in the conversation.
- Never invent missing values.
- Never mention rule IDs, rule matching, structured output, or internal configuration to the customer.
```

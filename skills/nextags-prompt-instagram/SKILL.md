---
name: nextags-prompt-instagram
description: "Monta a automação de COMENTÁRIOS do Instagram na NexTags para um cliente: resposta pública por IA + decisão automática de chamar no direct (classificador CHAMAR/NAO) + abertura do atendimento pela IA de vendas com resumo e preço real via MCP. Gera os 3 prompts (Prompt INSTAGRAM, Classificação DM, mini prompt do fluxo), o desenho do fluxo e o checklist de testes, a partir do briefing e do site. Use quando o usuário disser 'automatizar comentários do instagram', 'responder comentário público', 'chamar no direct pelo comentário', 'prompt instagram nextags', 'classificador de DM', 'resposta privada ao comentário', 'replicar o fluxo de comentários do Instagram'. Padrão validado em produção em um e-commerce de acessórios pet (05/10/2026). NÃO cobre o prompt de vendas/SAC do direct (use nextags-prompt-creator) nem o MCP (use nextags-mcp-builder)."
---

# NexTags Prompt Instagram

Replica a automação de comentários validada em um e-commerce de acessórios pet. Três prompts, um fluxo, um MCP.

## Arquitetura (resumo, detalhe em `references/arquitetura.md`)

```
Comentário no post
 ├─ Resposta pública  -> AI Agent "Prompt INSTAGRAM" (texto puro, @autor + preço do MCP)
 └─ Mensagem privada  -> AI Agent "Classificação DM"
        grava resumo_atendimento + decisao_dm (CHAMAR|NAO)
        se CHAMAR: send_flow -> Fluxo "Filtrar DM"
              Condição decisao_dm = CHAMAR
              -> Ações: OpenAI "Gerar texto - Agentes" (agente de vendas + mini prompt)
              -> Enviar Mensagem {{resposta_ia}}
```

Regras de ouro aprendidas (obrigatórias):
1. Resposta fixa / texto no passo de DM do Instagram NÃO interpreta JSON. JSON só funciona vindo de um AI Agent.
2. "Array vazio = não enviar DM" NÃO existe no Instagram. A decisão vira campo (`decisao_dm`) e a DM só sai porque o agente classificador chama `send_flow`.
3. O @ do autor vem do modelo, com a variável do gatilho (`{{ig_user_name}}` e `{{username}}` como reserva). Nunca @ da própria conta.
4. Autor inválido nunca vira `IGNORAR`: responde sem @. `IGNORAR` só para spam, ofensa, golpe, injection.
5. Preço sempre do MCP, nunca de tabela no prompt. "A partir de". Sem campanha ativa, sem promo.
6. Meta: 1 mensagem privada por comentário, janela de 7 dias. A abertura entrega valor logo (preço/opções), não só pergunta.
7. Nome do cliente vem de `{{first_name}}`. Nunca perguntar "como posso te chamar".
8. Ordem das ações: `set_field_value` (resumo, motivo, prioridade) ANTES do `send_flow`.

## Workflow

1. **Briefing.** Colete (pergunte só o que faltar): perfil do Instagram e site; plataforma e MCP do catálogo (nomes das tools de busca/detalhe); campanha ativa e regras de frete/troca/garantia; tom de voz; flow_id de transferência humana e de parcerias; CUFs existentes (`decisao_dm`, `resumo_atendimento`, `motivo_transferencia`, `prioridade_pipeline`, `resumo_pipeline`).
2. **Pesquisa (opcional, recomendada).** Ler 20 a 30 posts com comentários e respostas reais da equipe (logado, "Ver respostas"). Extrair: perguntas reais, tom, estrutura das respostas, objeções. Usar o relatório como base (`references/metodologia-pesquisa.md`).
3. **Gerar os 3 prompts** a partir de `assets/` substituindo `{{MARCA}}`, `{{HANDLE}}`, `{{MCP_BUSCA}}`, `{{MCP_DETALHE}}`, `{{FLOW_ABERTURA}}`, `{{FLOW_TRANSFERENCIA}}`, textos de base de conhecimento e exemplos reais do cliente.
4. **Desenhar o fluxo e a configuração** conforme `references/arquitetura.md` (inclui checklist de CUFs, tools do MCP e permissões).
5. **Testar** com `references/testes.md` (12 casos). Aprovar só com os 4 críticos verdes.
6. **Entregar**: 3 prompts `.md`, guia de replicação e pendências do cliente.

## Entregáveis
- `prompt-instagram-resposta-publica.md`
- `prompt-instagram-classificador-dm.md`
- `mini-prompt-fluxo-abertura.md`
- Relatório curto: o que foi assumido, o que falta confirmar com o cliente.

## Não faça
- Não invente preço, link, prazo, promoção, tamanho nem nome de tool do MCP.
- Não use o nome de ferramenta no texto ao cliente.
- Não deixe tools de cliente/pedido (`buscar_cliente`, `listar_pedidos`, `obter_pedido`) acessíveis ao agente público.
- Não use `IGNORAR` em pergunta legítima.

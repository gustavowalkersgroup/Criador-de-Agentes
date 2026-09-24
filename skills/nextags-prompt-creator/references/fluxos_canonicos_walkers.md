# Fluxos canônicos Walkers — conta NexTags 1512865

**Fonte da consulta:** NexTags, conta `1512865`, pasta raiz `942028`, consultada em 24/09/2026 pelo navegador autenticado.
**URL da pasta raiz:** `https://app.nextagsai.com.br/en/flows?acc=1512865&folder=942028`

Este inventário é específico da conta Walkers. Os nomes e IDs devem ser tratados como catálogo operacional da conta, não como catálogo universal da plataforma. Antes de gravar um ID em um prompt ou dispará-lo via integração, valide-o na API/conta atual. Um `flow_id` errado pode falhar silenciosamente.

## Regra de decisão

A IA deve distinguir quatro classes:

1. **Transacionais:** disparados por evento confirmado de pedido, pagamento, expedição, entrega ou carrinho. A IA normalmente não dispara esses fluxos manualmente. Ela lê os CUFs que o fluxo populou e responde com base neles.
2. **Disparos:** mensagens proativas ou campanhas iniciadas pela operação. A IA não deve iniciar um disparo por conta própria, nem responder a uma mensagem proativa sem interação genuína do cliente.
3. **Instagram:** fluxos ligados a origem, captura de lead ou migração de conversa entre Instagram e WhatsApp. Só usar quando o canal, a origem e o consentimento forem compatíveis.
4. **Padrões:** fluxos operacionais reutilizáveis, como entrada, boas-vindas, NPS, carteira comercial, listas e transferência humana. Podem ser acionados somente quando o prompt, a tool e o briefing autorizarem o caso.

O agente não deve inventar que um fluxo foi executado. Se a ação não estiver disponível nesta execução, deve explicar a limitação ou transferir conforme o handoff canônico.

## Inventário por pasta

### Disparos — pasta `21083`

| Nome exibido | ID observado | Uso operacional |
|---|---:|---|
| `Walkers Reativação de Base` | `1780948283287` | Reativação proativa de contatos/base. Não iniciar a partir de uma conversa comum sem autorização de campanha e regra de consentimento. |
| `Walkers - Disparo Padrão 4 partes` | `1788378902538` | Modelo de disparo em quatro partes. É campanha proativa; não é resposta de atendimento nem substituto do agente de vendas. |

### Instagram — pasta `40785`

| Nome exibido | ID observado | Uso operacional |
|---|---:|---|
| `Walkers disparo promo whatsapp<-instagram` | `1783524662099` | Origem Instagram para uma ação promocional no WhatsApp. Exige canal/origem compatíveis e consentimento ou regra de campanha válida. |
| `Walkers Captura de Leads Instagram` | `1781624361246` | Captura e qualificação de leads originados no Instagram. Não presumir conteúdo da story; `{{last_story_id}}` é apenas um ID, não o texto da story. |

### Padrões — pasta `234912`

| Nome exibido | ID observado | Uso operacional |
|---|---:|---|
| `Walkers Fluxo Transferencia Humana` | `1782490224812` | Transferência operacional para atendimento humano. Deve receber os CUFs do handoff antes do disparo: `motivo_transferencia`, `prioridade_pipeline` e `resumo_pipeline`. |
| `Walkers Boas Vindas Com IA` | `1784235955139` | Entrada/boas-vindas quando a conversa deve ser atendida por IA. Não reapresentar a IA depois de um handoff. |
| `Walkers NPS atendimento` | `1775756196785` | Coleta de avaliação pós-atendimento. Não disparar durante reclamação ativa nem usar como substituto da resolução. |
| `Walkers Carteira Comercial` | `1736429988129` | Operação de carteira/comercial. Usar somente quando a regra comercial ou o fluxo de pipeline direcionar o caso. |
| `Walkers - Inscrever em voltar pro bot` | `1788374645915` | Inscrição para retornar ao atendimento automatizado. Não deve ser usada para atropelar um pedido de humano. |
| `Walkers Boa Vindas Sem IA` | `1735820514571` | Entrada/boas-vindas sem IA. Não enviar conteúdo de IA se o contato estiver nesse ramo. |
| `Walkers - Sair da Lista` | `1757284326148` | Remoção de uma lista. Associar a opt-out ou regra operacional correspondente; nunca usar para apagar dados sem autorização. |
| `Walkers Voltar pro BOT` | `1784234987833` | Retorno ao atendimento automatizado após condição autorizada. Só usar quando a conversa estiver apta a voltar ao bot. |
| `Walkers - Entrar na Lista` | `1757284414006` | Inscrição em lista operacional. Exige finalidade, regra e consentimento compatíveis quando envolver comunicação proativa. |

### Transacionais — pasta `542937`

| Nome exibido | ID observado | Evento esperado |
|---|---:|---|
| `Walkers Pedido Aprovado` | `1777900417748` | Pedido/pagamento aprovado. Alimenta a comunicação de confirmação pós-compra. |
| `Walkers Pedido Enviado (rastreio)` | `1777902657447` | Pedido expedido ou enviado. Alimenta rastreio, código e previsão quando disponíveis. |
| `Walkers Pedido Entregue` | `1777901985648` | Pedido entregue. Pode iniciar confirmação ou avaliação pós-compra conforme regra da operação. |
| `Walkers Recuperação de carrinho` | `1777903191628` | Carrinho abandonado ou checkout não concluído. É automação transacional/comercial baseada em evento, não uma justificativa para pressionar o cliente. |

> **Nota sobre IDs observados:** a interface exibiu os IDs nas linhas da tabela. Valide os IDs via inventário/API da conta antes de publicar prompt ou workflow, principalmente se a plataforma tiver ambientes, cópias ou duplicações.

## Como a IA deve usar cada classe

### Em mensagens recebidas do cliente

O agente deve responder à mensagem recebida normalmente. Se o cliente responder a um disparo, trate a mensagem como uma nova conversa real e não repita automaticamente o disparo. Se a mensagem for apenas uma mensagem proativa sem interação genuína, aguarde; não invada a conversa com uma resposta automática.

### Em atendimento de pedido

Use os CUFs transacionais quando estiverem presentes no bloco `DADOS DESTA CONVERSA`, por exemplo `{{numero_pedido}}`, `{{status_pedido}}`, `{{rastreio_codigo}}`, `{{rastreio_url}}`, `{{previsao_entrega}}`, `{{produtos_carrinho}}`, `{{valor_carrinho}}` e `{{link_carrinho}}`. Campo vazio significa que o dado não está disponível. Campo antigo ou stale não deve ser tratado como atualização atual.

A IA não deve disparar `Pedido Aprovado`, `Pedido Enviado`, `Pedido Entregue` ou `Recuperação de carrinho` só porque o cliente perguntou sobre o pedido. Esses fluxos pertencem à automação de eventos. Para consulta atual não coberta pelos CUFs, use a tool autorizada ou faça handoff.

### Em transferência para humano

A transferência humana usa o fluxo `Walkers Fluxo Transferencia Humana` quando esse for o fluxo confirmado da conta. Antes do `send_flow`, grave nesta ordem:

```json
{"actions":[{"action":"set_field_value","field_name":"motivo_transferencia","value":"vendas"},{"action":"set_field_value","field_name":"prioridade_pipeline","value":"media"},{"action":"set_field_value","field_name":"resumo_pipeline","value":"Cliente demonstrou interesse no produto e pediu apoio humano para decidir. A IA esclareceu as informações disponíveis, mas não concluiu o atendimento. Escalo para continuidade comercial."},{"action":"send_flow","flow_id":"1782490224812"}]}
```

O exemplo acima é operacional para a conta observada. Se o projeto usar outro fluxo de pipeline confirmado, prevalece o ID validado no briefing e no inventário atual.

### Em boas-vindas, listas e NPS

Fluxos de boas-vindas, entrada/saída de listas, retorno ao bot e NPS são ações operacionais. O agente só deve acioná-los quando a regra do projeto explicar o gatilho, os campos necessários e o momento correto. Não transformar um pedido de opt-out em nova campanha, nem enviar NPS antes de resolver uma reclamação.

## Regras de não utilização

A IA não deve:

- disparar campanha sem autorização explícita do fluxo, da tool ou do briefing;
- executar um transacional sem evento confirmado;
- usar fluxo de carrinho para pressionar quem já recusou contato;
- enviar NPS durante uma reclamação ativa;
- mandar o cliente para outro canal sem regra autorizada;
- dizer “um humano assumiu” antes de executar o fluxo;
- continuar vendendo depois do handoff;
- tratar o nome de um fluxo como prova de que ele foi executado;
- usar um ID copiado de outro ambiente sem validação;
- colocar todos os IDs no prompt de toda IA por precaução.

## Checklist de integração

Antes de usar um fluxo em um prompt, confirme:

- o nome e o ID ainda existem na conta `1512865`;
- o fluxo está ativo e pertence à pasta correta;
- o gatilho é inbound, proativo, transacional ou operacional;
- os CUFs necessários foram populados antes da execução;
- a IA tem autorização para dispará-lo;
- o fluxo não duplica o roteador, o revalidador ou o handoff canônico;
- a mensagem não cria loop entre IA, humano e bot;
- o relatório registra o ID e a finalidade escolhida.

Leia esta referência sempre que o projeto envolver a conta Walkers, os fluxos da URL canônica, campanhas, automações de pedido, carrinho, Instagram, listas, NPS ou transferência humana.

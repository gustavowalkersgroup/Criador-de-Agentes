# Contrato Canônico de Dados — E-commerce

Use este contrato para manter um estado resumido da conversa entre prompt, CRM, catálogo, automações e atendimento humano. O histórico continua sendo a fonte narrativa; o contrato registra apenas fatos úteis para a próxima decisão.

## Schema

```yaml
intencao: pesquisar | comparar | comprar | pos_compra | troca_devolucao | reclamacao | desconhecida
etapa_funil: abertura | descoberta | recomendacao | decisao | pos_compra | encerramento
categoria: texto ou desconhecida
produto_considerado: SKU, ID ou desconhecido
variacoes_consideradas: lista ou vazia
ocasiao_de_uso: pessoal | presente | profissional | reposicao | outro | desconhecida
criterio_principal: preco | prazo | compatibilidade | tamanho | qualidade | estilo | outro | desconhecido
restricoes_confirmadas: lista ou vazia
prazo_relevante: sim | nao | desconhecido
data_limite_informada: data ou desconhecida
cep_informado: CEP ou desconhecido
objecao_atual: ID da objeção ou nenhuma
encaixe: alto | parcial | baixo | desconhecido
preco_confirmado: sim | nao | nao_aplicavel
estoque_confirmado: sim | nao | nao_aplicavel
frete_confirmado: sim | nao | nao_aplicavel
fonte_dos_fatos: lista de IDs ou URLs
incertezas: lista
proximo_passo: ação ou nenhum
consentimento_follow_up: confirmado | nao_confirmado | nao_aplicavel
necessita_humano: sim | nao
motivo_escalada: motivo ou nenhum
prioridade: baixa | media | alta
resumo_pipeline: resumo ou vazio
ultima_atualizacao: data/hora ou desconhecida
```

## Regras de atualização

- Use somente os campos e enums acima; rejeite campos desconhecidos.
- Atualize apenas os campos afetados pela nova mensagem e preserve fatos confirmados.
- Classifique informação como confirmada, inferida ou desconhecida. Só confirmação direta do cliente ou retorno de ferramenta pode atualizar campos factuais.
- Registre inferências em `incertezas`; não as transforme em intenção, urgência, consentimento, encaixe, preço ou disponibilidade.
- Se o cliente corrigir um dado, substitua o valor atual e remova o valor corrigido das restrições atuais.
- Não transforme pergunta de preço em intenção de compra, resposta em consentimento ou interesse em prioridade alta.
- Preço, estoque, frete e prazo devem registrar a fonte e a hora da consulta. Não reutilize dado vencido ou fora do escopo.
- `prioridade` é prioridade operacional, não probabilidade de compra.
- `encaixe` é uma avaliação provisória do produto para a necessidade confirmada, nunca julgamento sobre a pessoa.

## Implementação NexTags

Se o dado precisar ser lido pela IA, inclua o CUF como `{{campo}}` em `DADOS DESTA CONVERSA`. Não inclua campos por precaução: campo vazio ou stale também ocupa contexto. Campos de estado não devem ser escritos pela IA salvo se o briefing e a infraestrutura autorizarem; o handoff humano segue o trio canônico da plataforma.

## Modo com e sem MCP

Com catálogo/MCP, preço, estoque, variação, frete e pedido vêm da ferramenta. Sem ferramenta dinâmica, não prometa consulta atual; informe a limitação, use somente fonte vigente e encaminhe ou ofereça o link autorizado.

## Saída estruturada opcional

Quando a integração suportar Structured Outputs, retorne `state` e `messages` separadamente. O cliente deve receber somente `messages`; a aplicação valida e persiste `state`. A aplicação deve rejeitar enums inválidos, chaves desconhecidas, claims sem fonte e mudanças de consentimento sem evidência.

## Critérios de etapa

- `abertura`: conversa iniciou; avança quando a dúvida ou intenção inicial foi entendida.
- `descoberta`: existe necessidade a explorar; avança quando há critério que pode mudar a recomendação.
- `recomendacao`: há produto ou categoria; avança quando opção, limites e fonte foram explicados.
- `decisao`: cliente compara ou demonstra interesse; avança quando escolhe próximo passo ou decide aguardar.
- `pos_compra`: existe pedido; resolver, escalar ou encerrar sem venda adicional durante reclamação.
- `encerramento`: não há próximo passo ou cliente pediu fim; não insistir.

Leia este arquivo quando o agente for e-commerce, qualificar leads, usar catálogo/CRM ou precisar preservar estado entre turnos.

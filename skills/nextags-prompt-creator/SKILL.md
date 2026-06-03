---
name: nextags-prompt-creator
description: "Generate production-ready customer service AI prompts for the NexTags Messenger Messaging Platform from a human briefing plus a company URL. Use whenever the user wants to CREATE a new agent prompt from scratch — triggers in Portuguese ('criar prompt', 'gerar prompt', 'novo agente', 'fazer prompt do bot', 'criar atendente IA') and English ('create nextags prompt', 'build agent prompt', 'generate customer service bot'). The skill scrapes the company website with web_fetch, asks the obligatory questions (tools/MCP, tom de voz, flow_ids, mídias, restrições), generates the complete prompt covering all required sections (identity, anti-hallucination, JSON format, flows, transfer via send_flow), then chains into the auditor (analyze_prompt.py) so the output is rules-compliant on first delivery. Outputs the finished `.md` plus a Portuguese audit report. Trigger any time NexTags agent prompt creation is requested, even without the words 'create' or 'generate'."
---

# NexTags Prompt Creator

Cria do zero prompts de agentes de atendimento da plataforma NexTags a partir
de **briefing humano + URL da empresa**, e encadeia automaticamente com a
auditoria estrutural antes de entregar.

## O que essa skill faz

Recebe um briefing (texto, arquivo ou conversa) e a URL do site da empresa,
e devolve:

1. Um **prompt completo** em `.md` (`prompt-atendimento-vX.X.md`).
2. Um **relatório de auditoria** mostrando o que a auditoria caçou e
   corrigiu durante a geração — para o humano ter visibilidade do que mexeu.

A skill segue **a hierarquia de verdade do meta-prompt**:

1. 🥇 Briefing humano (fonte principal)
2. 🥈 Site (fonte complementar via scraping)
3. 🚫 Suposições são proibidas

Em conflito, briefing **sempre** ganha. Quando algo não está em nenhum dos
dois, vira **pendência humana** explícita — nunca chute.

## Quando essa skill se aplica

Use sempre que o usuário mencionar:

- "Criar/gerar/fazer prompt" para um agente de atendimento NexTags.
- "Novo agente" ou "novo bot" para uma empresa específica.
- "Preciso de um prompt para [marca/empresa]".
- Mostrar briefing + URL e pedir um prompt.

**Não use** para corrigir prompts já existentes — para isso, a skill é
`nextags-prompt-fixer`.

## Fluxo de trabalho

### 1. Captura inputs

Você precisa de duas coisas:

- **Briefing** — texto do humano descrevendo: empresa, agente desejado,
  objetivo principal, restrições conhecidas. Pode ser conversa, arquivo
  `.md`/`.txt`, ou texto colado.
- **URL do site da empresa** — para o scraping.

Se faltar qualquer um dos dois, **peça antes de começar**. Não tente fazer
sem briefing (vira invenção) nem sem URL (vira pobreza de contexto).

### 2. Faz scraping do site

Use `web_fetch` para baixar o conteúdo das páginas-chave. Estratégia:

1. **Sempre** comece pela homepage (URL fornecida).
2. A partir dela, identifique e busque até **5 páginas-chave** entre:
   `/sobre`, `/quem-somos`, `/faq`, `/perguntas-frequentes`,
   `/politica-de-troca`, `/troca-e-devolucao`, `/garantia`, `/frete`,
   `/pagamento`, `/contato`, `/atendimento`, e uma amostra de página de
   produto se for e-commerce.
3. **Não** explore o catálogo inteiro — uma amostra de 1-2 produtos basta
   para identificar padrão de descrição, preço, foto.
4. Se uma página falhar (404, timeout): pule e siga.

Budget: **máximo 6 fetches**. Se o site não cobre tudo nesse orçamento,
documente o que faltou no relatório.

### 3. Compara briefing × site (análise de inconsistências)

Categorize divergências:

- 🔴 **Crítica** — afeta venda ou informação sensível (ex.: briefing diz
  "frete grátis acima de R$ 199" mas site diz "R$ 299").
- 🟡 **Moderada** — diferenças de descrição (ex.: tom mais formal no site
  vs. informal no briefing).
- 🔵 **Leve** — branding, estilo.

Para cada divergência, **siga o briefing** e mencione no relatório de
auditoria final.

### 4. Roda as perguntas obrigatórias

Leia `references/perguntas_obrigatorias.md` para a lista completa e o
roteiro recomendado de chunking (até 3 perguntas por chamada de
`ask_user_input_v0`). As essenciais:

- Persona: nome do agente, tom de voz, canais.
- Tools/MCP: quais existem? inputs?
- IDs de fluxos: especialmente o **fluxo de transferência humana**.
- Mídia: imagens/áudios/vídeos disponíveis.
- Restrições comerciais e tratamento de reclamações.

⚠️ **Não pergunte coisas que o site/briefing já cobrem** — desperdiça
rodada e irrita o humano.

⚠️ **Sem resposta = pendência.** Mantenha placeholder explícito no prompt
(`<ID_DO_FLUXO_TRANSFERENCIA>`, `<URL_IMAGEM_X>`, etc.) e liste no
relatório. **Nunca chute.**

### 5. Gera o prompt

**5.0 — Classifique o TIPO de agente ANTES de montar o esqueleto.**

Decida (pelo briefing + perguntas) entre:
- **Vendas/consultora** → inclua seção 6B (Vendas). Não inclua SAC pesado.
- **SAC/pós-venda** → inclua seção 8B (SAC). Não inclua framework de vendas.
- **Triagem/roteador** → use seção 8C (Triagem). REMOVA KB detalhada, vendas, SAC, MCP.
- **Comercial/SDR (B2B, qualifica lead)** → inclua 6B simplificado + pipeline via
  set_field_value (stage monotônico + resumo acumulativo) + checklist final.
- **Misto (vendas + SAC)** → inclua 6B e 8B com uma regra de troca de modo.

Seções universais (TODOS os tipos, bloqueantes): Identidade, Tom de Voz,
Escopo (com fora-de-escopo→flow_id), Transferência via send_flow, Anti-alucinação,
Formato JSON. Sem qualquer uma dessas, reprovar.

Ordem recomendada: Contexto Temporal ({{current_user_time}}) primeiro quando houver
lógica de prazo/saudação; Exemplos JSON verbatim por último (galeria de 5-12 casos).

Use `references/prompt_skeleton.md` como esqueleto e preencha cada seção com:

- **Conteúdo do briefing** para identidade, objetivo, restrições, persona.
- **Conteúdo do scraping** para base de conhecimento, FAQ, políticas,
  diferenciais. Reescreva no contexto do agente, **não copie literal**.
- **Respostas das perguntas obrigatórias** para tools, fluxos, mídias.
- **Padrões da `references/regras_absolutas.md`** para garantir que cada
  seção sai conforme as regras (texto-padrão, send_flow, sem
  `transfer_conversation_to`, sem botões sem `web_url`, etc.).

**Princípios de geração:**

- Tom da empresa (do scraping) influencia voz das mensagens-exemplo.
- Briefing manda em conflitos.
- Mantenha base de conhecimento **enxuta** — se a empresa tem tools, NÃO
  hardcode preços/estoque (eles ficam stale; usa as tools).
- Nome de versão inicial: `v1.0`. Salve como `prompt-atendimento-v1.0.md`
  ou `prompt-{nome-empresa}-v1.0.md`.

**🚫 SEÇÕES PROIBIDAS NO PROMPT — vai pro RELATÓRIO, não pro prompt:**

O prompt do agente é a instrução que o LLM lê a cada turno em runtime. Tudo que o LLM lê deveria ajudá-lo a responder melhor o cliente. Seções de meta-documentação atrapalham (diluem atenção, gastam contexto) sem nenhum ganho operacional.

**NUNCA inclua no prompt gerado:**

1. **Auditoria / Changelog / Histórico de versões** — "v1.0 → v2.0 mudou X", "v2.5 (correções pós-teste)", tabelas com "Bug observado / Correção aplicada", etc. Isso é histórico pro dev, não pro agente.
2. **Pendências internas / TODOs / "a confirmar"** — "Pendente: criar flow_id de fallback", "TODO: validar se canonical_url está estável", notas pro dev.
3. **Notas técnicas pra implementação futura** — "Considerar criar campo personalizado X", "Renomear tools no MCP".
4. **Comentários sobre versões do próprio prompt** — "Versão: v3.0 enxuta", "Data: maio/2026", "Responsável: dev X".
5. **Justificativas sobre decisões passadas** — "Removemos o carrossel porque quebrava", "Antes era X, agora Y porque...".
6. **Métricas / análises** — "redução de 65%", "passou no analyzer", "0 violações".

**Onde isso DEVE ir:** no **relatório de auditoria** (`relatorio-<nome>.md`), gerado separadamente.

**Cabeçalho do prompt:** pode ter no MÁXIMO uma linha curta de identificação (`# PROMPT — AGENTE X`). Sem versão, sem data, sem responsável.

**Como aplicar na geração:**

- Gerou o prompt? Cheque se tem alguma seção tipo "Auditoria", "Histórico", "Pendências", "Changelog", "Notas internas", "A confirmar", "TODO" — REMOVA. Vai pro relatório.
- O `analyze_prompt.py` detecta automaticamente essas seções (chave `forbidden_meta_sections`) e flagra como violação.
- Toda informação útil pra DEV vai no relatório. Prompt = só o que o LLM precisa pra atender.

---

**🏷️ CUFs do sistema — use `{{first_name}}` em vez de `[nome]`:**

A plataforma NexTags tem um conjunto rico de **Custom User Fields (CUFs)** nativos que são interpolados automaticamente em runtime — primeiro nome, e-mail, telefone, status de pedido, dados do carrinho, e muito mais. **Lista completa em `references/cufs_nextags.md`.**

**Regra absoluta:**
- NUNCA use placeholders genéricos como `[nome]`, `[cliente]`, `[email]`, `[primeiro nome]`, `[telefone]`, `[order_id]`, `{nome_do_cliente}`, `$first_name$`, ou variações com `<>`/`{}`/`[]` nos exemplos do prompt.
- SEMPRE use a sintaxe oficial `{{nome_do_cuf}}` (duas chaves) quando existir um campo nativo equivalente.
- A plataforma NÃO interpola nada além de `{{cuf_real}}` — qualquer outra forma aparece literalmente pra cliente.

**CUFs mais comuns em prompts de atendimento:**

| Uso | CUF |
|---|---|
| Primeiro nome do cliente | `{{first_name}}` |
| Nome completo | `{{full_name}}` |
| E-mail | `{{email}}` |
| Telefone | `{{phone}}` |
| Cidade / estado | `{{user_city}}` / `{{user_state}}` |
| Último pedido | `{{last_order}}` |
| ID do pedido | `{{order_id}}` |
| Status do pedido | `{{order_status}}` |
| Total do pedido | `{{order_total}}` |
| Link de checkout | `{{cart_checkout_link}}` |
| Hora local do cliente (âncora de prazo/saudação) | `{{current_user_time}}` |
| Última mensagem | `{{last_text_input}}` |

**CUFs de ESCRITA via `set_field_value` (agentes que capturam lead/pipeline):**
Grave dados SANITIZADOS: telefone sem `+` (`5511XXXXXXXXX`), e-mail em minúsculas,
valores como `'379.00'` (ponto decimal, sem `R$`). Campos de classificação usam
enums fechados (ex.: `stage_pipeline: '1'/'2'/'3'`, só avança nunca regride;
`resumo_comercial` acumulativo: anterior + novo). `set_field_value` SEMPRE antes
de `send_flow` no array de actions (o flow lê os campos no momento que dispara).

**Regra de Contexto Temporal:** quando houver qualquer lógica de prazo ou saudação
por horário, use `{{current_user_time}}` e proíba o agente de inventar data/hora.

**Use somente se for necessário.** Não force `{{first_name}}` em toda mensagem — saudação inicial e momentos-chave bastam.

**Sempre considere o caso "campo vazio"**: cliente sem cadastro não tem `{{first_name}}` preenchido. Se a frase ficar estranha ("Oi, ! Tudo bem?"), ofereça uma variante neutra no prompt:

```
Abertura com nome: {"messages":[{"message":{"text":"Oi, {{first_name}}! Tudo bem?"}}]}
Abertura sem nome: {"messages":[{"message":{"text":"Oi! Tudo bem? Como posso te ajudar?"}}]}
```

Consulte `references/cufs_nextags.md` para a lista completa (~80 campos) cobrindo: contatos, Instagram, Messenger, localização, agendamentos, e-commerce, carrinho, pedidos.

---

**📏 ENXUTO POR PADRÃO — tamanho importa:**

Prompts NexTags rodam em janela de contexto compartilhada com histórico da conversa, retornos de tools, e múltiplos turnos. **Prompts inchados desperdiçam contexto, aumentam custo por turno e pioram aderência do LLM às regras** (modelo dilui atenção entre muita coisa repetida).

**Meta de tamanho:**
- **15-20 KB por prompt** (~5.000-7.000 palavras) é o ideal.
- Acima de **30 KB** → revisar agressivamente. Provavelmente tem redundância.
- Acima de **45 KB** → sinal vermelho. Quase certo que tem 3+ versões da mesma regra.

**Como manter enxuto:**

1. **Uma regra dita UMA vez.** Não repetir a mesma regra em "Regras Absolutas", "Regras de Formato" e "Regras Críticas". Coloca uma vez no lugar mais lógico e referencia.
2. **Tabelas em vez de prosa.** Pra listas de gatilhos, tools, fluxos, tratamento de erros — tabela. Economiza 60-70% de linhas vs. prosa.
3. **Sem auditoria/changelog dentro do prompt.** Versões anteriores (v1, v2, etc.) e correções históricas NÃO ajudam o LLM em runtime — só servem pro humano. Mantenha em arquivo separado se quiser.
4. **Sem "pendências internas".** Notas pra TODO/futuro/dev → outro arquivo, não no prompt.
5. **Consolidar fluxos similares.** Se Troca/Devolução/Defeito/Cancelamento têm o mesmo template com pequenas variações, usar UMA seção com tabela de variações.
6. **Testes: 4-6 essenciais.** Não precisa 10+ testes que repetem o mesmo princípio.
7. **Exemplos negativos: 2-3 por regra-chave.** Não precisa ERRADO 1, ERRADO 2, ERRADO 3... ERRADO 8 da mesma coisa.
8. **Eliminar palavras de preenchimento** ("obrigatoriamente", "absolutamente", "completamente", "totalmente" repetidos).
9. **Cortar regras herdadas que não se aplicam.** Ex: Maya não atende SAC — não precisa ter "Política de Trocas e Devoluções" detalhada (Sara tem).

**Princípio:** se uma seção pode ser removida sem mudar o comportamento esperado do agente em runtime, ela DEVE ser removida.

---

**⚓ OBRIGATÓRIO — Bloco oficial NexTags:**

Todo prompt gerado DEVE incluir, literalmente (sem parafrasear), o bloco oficial
de instruções de saída JSON, no início da seção FORMATO DE RESPOSTA:

```
Você é uma IA que deve sempre retornar respostas em JSON válido seguindo o padrão da Messenger Messaging Platform.

Regras:
1 - O JSON deve conter um array "messages" ou um array "actions" (ou ambos).
2 - "messages" é um array de objetos. Cada objeto deve conter um objeto "message".
3 - O objeto "message" deve seguir o schema de mensagens da Messenger Messaging Platform.
4 - Tipos de mensagem suportados:
   - Texto ("text")
   - Texto com botões
   - Imagens
   - Vídeos
   - Carrossel (templates do tipo "generic")
   - Arquivos
5 - Sempre retorne somente JSON válido. Não retornar explicações, comentários, markdown ou qualquer texto fora do JSON.
```

Esse bloco é a especificação canônica da plataforma NexTags. Pode haver
regras complementares no prompt (cada agente tem suas tools, fluxos,
persona específica), mas esse bloco vai LITERAL como ponto de partida.
O analyzer `analyze_prompt.py` valida a presença via `bloco_oficial_nextags`.

### 6. Roda auditoria com `analyze_prompt.py`

Etapa **obrigatória**, mesmo se você está confiante. Salve o prompt
gerado em `/tmp/generated.md`, então:

```bash
python <SKILL_DIR>/scripts/analyze_prompt.py /tmp/generated.md \
    --output /tmp/findings.json
```

Leia o `findings.json`. Se ele reportar:

- **Violação estrutural** (JSON inválido, ação proibida, botão sem URL,
  carrossel pequeno, markdown em JSON): **corrija direto no prompt** antes
  de entregar. Use `references/regras_absolutas.md` para o padrão de fix.
- **Seção obrigatória faltando**: revise — talvez você tenha esquecido
  mesmo de gerar. Se sim, adicione com base no skeleton. Se foi falso
  positivo (você gerou mas o detector não pegou o phrasing), tudo bem —
  documente isso no relatório.

Re-rode o analyzer no prompt corrigido. Repita até **0 violações reais**
(idempotência).

### 7. Gera o relatório de auditoria

Use `assets/relatorio_template.md` como base. **O relatório aqui é
ligeiramente diferente do relatório do fixer:** em vez de "antes/depois"
(que não faz sentido — o prompt nasceu já corrigido), o relatório do
criador deve ter:

- **Resumo da geração:** quantas seções, quantos blocos JSON, quantas
  pendências humanas.
- **Inconsistências briefing × site** que foram resolvidas a favor do
  briefing (com referências às fontes).
- **Correções aplicadas durante geração:** quais ajustes a auditoria
  pediu (mesmo que a primeira passada já tenha saído limpa, vale registrar
  "0 violações detectadas — geração já saiu rules-compliant").
- **Pendências humanas:** lista clara de cada placeholder
  `<ID_DO_FLUXO_*>`, `<URL_*>` ou seção marcada para revisão. Sempre com
  sugestão concreta do que preencher.
- **Estatísticas finais:** mesma tabela do relatório do fixer.

### 8. Apresenta os arquivos

Use `present_files` com o `.md` corrigido **primeiro** e o relatório em
seguida:

```
present_files([
  "/mnt/user-data/outputs/prompt-atendimento-v1.0.md",
  "/mnt/user-data/outputs/relatorio-criacao-v1.0.md",
])
```

Na resposta de chat, escreva uma síntese curta (3-5 linhas):

- Empresa atendida + nome do agente gerado.
- Quantas pendências humanas precisam ser resolvidas antes de subir
  produção.
- Convite explícito: "Resolveu as pendências e quer revisar de novo?
  É só rodar o `nextags-prompt-fixer` no resultado."

## Edge cases

**Briefing muito raso (menos de 3 frases).** Não tente preencher os
buracos no escuro. Pergunte ao humano por mais detalhes específicos antes
de prosseguir. Lista mínima: o que a empresa vende/oferece, qual o objetivo
principal do agente, se já tem tools/MCP configurados.

**Site bloqueando scraping (paywall, rate limit, JS-rendered).** Avise o
humano, peça para colar manualmente o conteúdo das páginas-chave (Sobre,
FAQ, Políticas). Continue com o que tiver.

**Empresa sem produtos (serviço, agência, B2B).** Pule a seção de catálogo,
adapte a base de conhecimento para serviços (descrições, modelos de
contratação, prazos, casos de sucesso).

**Empresa multi-marca / multi-canal.** Pergunte se é UM agente para tudo
ou múltiplos. Skill cria UM por vez — se for múltiplos, gere um, depois
rode de novo.

**Conflito briefing × site não-resolvível.** Se o briefing diz X e o site
diz Y e nenhum parece estar errado, **siga o briefing** e flag no
relatório como "✋ Confirmar com cliente: site mostra Y, briefing diz X.
Preciso confirmar qual está correto."

**Site em outro idioma.** O agente segue o idioma do briefing (geralmente
PT-BR). O scraping pode estar em qualquer idioma — você traduz/adapta.

## Estrutura desta skill

```
nextags-prompt-creator/
├── SKILL.md                          (este arquivo)
├── scripts/
│   └── analyze_prompt.py             auditor (mesmo do fixer)
├── references/
│   ├── prompt_skeleton.md            esqueleto + guia por seção
│   ├── perguntas_obrigatorias.md     checklist de perguntas
│   └── regras_absolutas.md           regras + padrões de fix (mesmo do fixer)
└── assets/
    └── relatorio_template.md         template do relatório
```

## Relação com `nextags-prompt-fixer`

Os dois skills são pares:

- `nextags-prompt-creator` → cria do zero, com auditoria embutida no fim.
- `nextags-prompt-fixer` → audita e corrige prompts já existentes.

Eles compartilham `analyze_prompt.py` e `regras_absolutas.md`. Se você
atualizar uma regra no fixer, atualize também no creator (ou vice-versa)
para manter consistência. Os dois skills funcionam independente um do
outro, mas o fluxo completo é: criar com o creator → editar manualmente
ao longo do tempo → quando ficar incerto se ainda está rules-compliant,
rodar o fixer.

# Changelog

Todas as mudanças notáveis das **NexTags Tools** são documentadas aqui.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o
projeto adota [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.5.0] - 2026-09-03

Rodada de **padronização canônica** das 6 skills, a partir de decisões formais do dono do
projeto: a arquitetura real de roteador+revalidador em produção, o
handoff IA→humano dirigido por 3 CUFs e UM fluxo de pipeline (substitui o modelo de
flow-rotativo da rodada anterior, ainda não lançada), uma referência de campos canônicos
compartilhada entre 4 skills, e as lições da leitura de 21 workflows n8n recentes (Cantarola,
Nordmann, Degan, Poé, Meiskin, Alto Giro, Otogama, AliveMed, Privilège) mais dois documentos
do dono (API Gateway Proxy, API NexTags). **Contém uma mudança de ruptura**: o enum de
`motivo_transferencia` introduzido (ainda não lançado) na 1.4.0 é substituído — `sac_geral`
deixa de existir.

### Adicionado

**Referência compartilhada `campos_canonicos.md`** (nova — cópia idêntica em
`nextags-prompt-creator`, `nextags-prompt-fixer`, `nextags-mcp-builder` e
`nextags-webhook-builder`)
- Fonte de verdade única do método: arquitetura roteador/revalidador, handoff IA→humano,
  campos padrão da conta modelo (quem grava o quê), etiquetas (tags) por grupo, CUFs
  transacionais, ponteiros para `gateway_proxy_nextags.md`/`api_nextags.md`, telefone fixo,
  formato de notas para editores e §9 com as perguntas em aberto do dono. Novo teste
  `test_campos_canonicos_copies_in_sync` (em `test_analyze_prompt.py`) trava as 4 cópias
  idênticas — a suíte de sincronia agora cobre 3 famílias de arquivo (`analyze_prompt.py`,
  `cufs_nextags.md`, `campos_canonicos.md`).

**Arquitetura canônica roteador/revalidador** (transversal — creator, fixer, mcp-builder)
- Documentado o fluxo de entrada real em produção: ROTEADOR ("Classificador Inteligente", 1
  palavra, GPT-4.1 nano, temperatura 0) grava `setor_agente` (`vendas|sac|analisar_humano_bot`
  — legado `ignorar` aceito no `else`), rodando a cada mensagem sobre o histórico inteiro; no
  ramo `analisar_humano_bot`, REVALIDADOR (2ª camada, lê `{{chat_history_details_large}}`,
  últimas 200 mensagens) grava `tipo_setor` (`humano|bot`) com regra de ouro "na dúvida →
  humano" (assimetria de risco); ramo `bot` arquiva a conversa, tira da IA, aguarda 1h
  (cancelado se o contato responder antes) e bloqueia o contato. Texto integral do prompt do
  revalidador incorporado verbatim (evidência: doc "PROMPT — REVALIDADOR (HUMANO x BOT)",
  Drive, 2026-07-21) como §8G do skeleton do creator e como referência de auditoria do fixer.
  Regra explícita: nenhum Agente (Vendas/SAC/extra) grava `setor_agente` ou `tipo_setor` —
  são campos exclusivos do roteador e do revalidador.

**Trio `motivo_transferencia`/`prioridade_pipeline`/`resumo_pipeline` + UM fluxo de pipeline**
- Substitui o modelo de flow-por-destino/flow-rotativo (branch `feat/handoff-canonico`) por
  UM único `<ID_DO_FLUXO_PIPELINE>` — quem escolhe a fila é o VALOR de `motivo_transferencia`,
  filtrado dentro do próprio fluxo (não mais N flow_ids no prompt). Enum canônico por setor:
  Parcerias (`ugc|colaboracao|influencer|revenda|atacado`), Comercial (`vendas|carrinho`),
  SAC (`rastreio|devolucao|troca|duvida` — `duvida` é o catch-all, mesmo destino do `else`).
  `prioridade_pipeline` (`baixa|media|alta`) com critério padrão por gravidade (jurídico/
  prejuízo financeiro/prazo vencido → `alta`). `resumo_pipeline` (texto, 2-4 frases, sem
  markdown, com 4 partes obrigatórias: quem é e dados que passou; o problema na palavra do
  cliente; o que a IA já tentou; por que escalou) com exemplo verbatim. Documentado o modo de
  falha "campo STALE": os 3 campos persistem no contato — transferir sem gravá-los usa o
  valor do atendimento anterior e o card cai na fila/prioridade errada em silêncio.

**Bloco `📣 AVISOS ATIVOS` + notas para editores**
- Formato fixo com marcadores `=== INÍCIO DOS AVISOS ===`/`=== FIM DOS AVISOS ===`, gerado
  sempre pelo creator (mesmo vazio) e checado pelo analyzer (`avisos_ativos_presente`).
  Marcador `> 🔧 NOTA PARA EDITORES:` (1 linha, ~200 caracteres) para humanos ou outras LLMs
  em pontos de edição frequente: tabela de `motivo_transferencia`, tabela de `flow_ids`,
  tabela de tools, bloco `DADOS DESTA CONVERSA`, base de conhecimento — whitelisted no check
  de meta-documentação proibida (changelog/versão/pendência/TODO continuam bloqueados).

**Bloco `## DADOS DESTA CONVERSA` + regra do nome canônica em todos os canais**
- Gerado sempre logo após IDENTIDADE/AVISOS, com os CUFs de leitura interpolados
  literalmente (`{{first_name}}`, `{{phone}}`, `{{email}}`, `{{current_user_time}}` + campos
  de pedido quando SAC/transacional). Regra do nome generalizada para TODOS os canais (antes
  cobria só o caso "Guest" do webchat, como sugestão opcional): `{{first_name}}` vazio,
  literalmente `"Guest"` ou que não parece nome de pessoa → saudação neutra + pergunta o nome
  UMA vez + `{"action":"set_field_value","field_name":"first_name","value":"<nome>"}`; não
  repete a pergunta se a pessoa não responder.

**Analyzer — 7 checks novos + suíte de testes** (`nextags-prompt-creator` e
`nextags-prompt-fixer`, cópias idênticas de `analyze_prompt.py`)
- `check_avisos_ativos` (bloco ausente → warn, obrigatório no modo creator); whitelist do
  marcador de nota de editor dentro de `check_forbidden_meta_sections`;
  `check_routing_field_writes` (**block** — a IA nunca grava `setor_agente`/`tipo_setor`);
  `check_motivo_transferencia_enum` (warn se valor fora do enum canônico por setor);
  `check_prioridade_pipeline_enum` (**block** se fora de `baixa|media|alta` — é campo
  "Seleção única" e a plataforma rejeita valor fora da lista); `check_handoff_trio` (warn se
  um `send_flow` de pipeline aparece sem o trio completo); `check_send_flow_action_order`
  (warn se `send_flow` vem antes de algum `set_field_value` no mesmo array). Suíte
  `test_analyze_prompt.py` (creator) passou de 29 para **53 testes** — 53/53 verde nesta
  entrega — cobrindo cada check novo além das sincronias já existentes.

**`nextags-webhook-builder` — referências e asset novos**
- `references/gateway_proxy_nextags.md`: Gateway Proxy NexTags
  (`https://api.nextags.com.br/v1/gateway/stores/:store_id/<path_limpo>`, header
  `Authorization: Bearer nxt_live_...`, escopo `proxy:passthrough`) para Tray/Nuvemshop/
  Yampi-Dooki/Bagy sem credencial nativa — de-para de path por plataforma, tabela de erros
  (401/403/429/501). Evidência de produção: Cantarola Backend Buscar Produtos.
- `references/api_nextags.md`: inventário de endpoints da API NexTags
  (`https://app.nextagsai.com.br/api/`, header `X-ACCESS-TOKEN`) usados pelas skills —
  `custom_fields`/`tags` (GET/POST/by name), `flows` (`GET /accounts/flows` para validar
  `flow_id` real antes de disparar), `contacts`, `pipelines`, `/agents/mcp`, tipos de CUF
  (0 Text … 7 Multi Select).
- `assets/setup_cufs_canonicos.js`: template de workflow n8n de setup idempotente de CUFs
  por API (`GET /accounts/custom_fields` → diff → dry-run → `POST /accounts/custom_fields`),
  inspirado no workflow real da Degan — dry-run obrigatório porque a API **não tem DELETE**
  (nome errado fica na conta para sempre) e o token é por conta (token errado retorna 200 e
  cria campos na conta errada, caso Wazzu/Hebreus Doze).
- `references/antipadroes.md` §16-22 (leitura de 21 workflows n8n recentes, 2026-09-03):
  dedup gravado antes/independente do sucesso do POST (Nordmann Meling Pedidos v2 e Carrinho
  v1 — 51 clientes que jamais seriam notificados), roteamento de estágio por texto em vez de
  id (Degan BW `rroCGCrCnb9R1U5s`: "Em Entrega" id 8 casava com `/entreg/` e bloqueou o id 9
  real), telefone fixo, `flow_id` placeholder "funcional" (`11111111111`), workflow
  `active:true` com sticky dizendo "pendente", skip silencioso sem `_motivo`, `/api/users`
  como variante legada de `/api/contacts`.

**`nextags-mcp-builder` — regras de n8n e MCP via GitHub**
- Regras inegociáveis novas: n8n sempre via API/MCP do n8n, **nunca navegador**
  (`search_workflows → validate_workflow → create_workflow_from_code/update_workflow →
  publish_workflow`); sticky note obrigatório em todo workflow, com modelo canônico (ESTADO
  EM dd/mm / CREDENCIAIS / PENDENTE-NÃO ATIVAR antes de… / ARMADILHAS com evidência / DE ONDE
  VEIO a lista de campos, evidência Degan `Wt3SsrCxQ2zwwnOo`); Data Table de dedup/estado +
  trio heartbeat+watchdog+error workflow para automação agendada crítica (evidência Otogama —
  worker morto sem `startedAt`, nenhum alerta interno disparou).
- Nova seção "Como expor as tools para a NexTags enxergar": MCP Server Trigger **v2**
  (Streamable HTTP) em `/mcp/<slug>`; tools sempre `httpRequestTool` v4.4/4.5 com
  `$fromAI(...)` por parâmetro (nunca `toolHttpRequest`+`placeholderDefinitions`, que
  colapsa o schema exposto num único campo `{input}` — evidência Poé `lk0lpDShxXFGia7D`);
  backend chamado por URL **interna** `http://n8n:5678/webhook/...` (a pública dá *connection
  refused* de dentro do próprio n8n); `availableInMCP: true`; conferir em `GET /agents/mcp`.
- Gate de escrita: tools que ESCREVEM (criar pedido, alterar cadastro) exigem escopo
  **read-only para SAC**, escrita só na IA de Vendas (com aprovação humana quando o domínio
  exigir) e teste com **contato interno** antes de ligar a tool na base real (evidência:
  requisitos SAP N2, Solentes N2 — "testar com 1 contato antes dos 344 da onda 1").
- `references/mcp_github_repo_pattern.md` (novo): MCP com repositório GitHub como banco para
  cliente sem ERP/API (padrão Poé Mídias) — catálogo lido via jsDelivr (**nunca**
  `raw.githubusercontent`, que serve `.mp4` como `application/octet-stream` e o WhatsApp
  rejeita o vídeo); atualizar catálogo/preço/mídia é commit no repo — nada muda no n8n nem
  no prompt.

**`nextags-webchat-tester` — seção "O que TESTA e o que NÃO testa"**
- Nova seção explícita: TESTA prompt/persona, roteamento (`setor_agente`), render de
  card/imagem, transferência fantasma e tool calling via MCP; NÃO testa fluxos n8n que
  dependem de telefone (transacionais, disparos, `send_flow` por API para um número — o
  contato de webchat não tem número) nem serve para validar telefone fixo como contato de
  teste (nunca recebe `send_flow`/mensagem via API).

### Alterado

**Enum de `motivo_transferencia` — substitui o da rodada anterior (ainda não lançada)**
- `sac_geral` **deixa de existir**; o catch-all agora é `duvida` (singular), mesmo destino do
  `else`. Entram os valores de Parcerias (`ugc`, `colaboracao`, `influencer`, `revenda`,
  `atacado`) e `carrinho` em Comercial. Regra de desambiguação: quer outra peça → `troca`;
  quer o dinheiro → `devolucao`; cancelar antes de receber → `duvida`.
- Nova **Regra 21** em `regras_absolutas.md` (fixer) com o mapeamento legado→canônico ao
  auditar prompt existente: `duvidas`→`duvida`, `assunto_ticket`/`resumo_lead`/`sac_resumo`→
  `resumo_pipeline`, `sac_prioridade`→`prioridade_pipeline`, `sac_categoria`→
  `motivo_transferencia`. Nova **Regra 22** formaliza o bloco AVISOS ATIVOS e as notas de
  editor. Adendo **Regra 20b** (sugestão, não bloqueante): handoff sem fricção — nunca
  empurrar o cliente para outro número, agente não se reapresenta após handoff (evidência
  Cantarola/Nivaldo).
- `perguntas_obrigatorias.md` §2.2 reescrita: pergunta UM `flow_id` de pipeline (não mais
  "rotativo" com N flow_ids) + confirma os valores do enum por setor; nova §2.2b (horário de
  atendimento + SLA do card) e §2.2c (quais CUFs a IA deve ler).

**`nextags-mcp-builder`: `handoff_pattern.md` reescrito**
- O padrão de "flows dedicados por destino" (1.4.0) é substituído pelo modelo roteador
  único + revalidador + trio de handoff. A versão anterior (flows dedicados IA↔IA, padrão
  Veuske) passa a "histórico/legado: por que abandonamos". Quirk do router que reseta
  `setor_agente` continua válido como explicação do bug de loop, renumerado de #24 para #27.

**`nextags-mcp-builder`: `webhook_transactional_pattern.md` marcado como histórico**
- O padrão vigente de transacional (CUFs snake_case canônicos + `origem_pedido`) agora mora
  em `nextags-webhook-builder`. Este arquivo (CamelCase + sufixo de origem, sem a regra de
  dedup-após-sucesso) ganha banner apontando para o padrão vigente — não copiar mais em
  projeto novo.

**`nextags-webhook-builder`: naming canônico de CUF (`padrao_transacional.md` §4.3)**
- CUFs passam de "por origem" (`NumeroPedidoBling`, `StatusPedidoYMP`) ou ad hoc para
  snake_case único (`numero_pedido`, `status_pedido`, …) + `origem_pedido` como
  discriminador de plataforma. Matriz de legado documentada (Nordmann NUV, Degan BW,
  AliveMed YMP, Meiskin, Alto Giro, WL) — regra dura: **não renomear** em cliente já rodando
  (o flow lê o nome antigo em silêncio), projeto novo é canônico sem exceção.
- Dedup: chave por **remessa** (`fulfillment_id`) quando há envio parcial (Alto Giro);
  comparação de **estágio anterior × novo** em vez de "existe linha" (evita bloquear os
  estágios seguintes do mesmo pedido — `rroCGCrCnb9R1U5s`); `rowNotExists` documentado como
  alternativa nativa a `get`+IF manual quando só importa a existência da linha.

**`nextags-webchat-tester`: lição do caso Veuske corrigida**
- A conclusão anterior ("webchat pode não disparar MCP; nunca conclua a partir dele apenas")
  estava incompleta: o incidente de 2026-06-11 foi **config de modelo** (temperature alta +
  modelo mini), não limitação do canal. MCP/tool calling **é válido no webchat**; o alerta
  agora é "revise temperature/modelo/prompt antes de culpar o MCP, e valide no WhatsApp real
  só se persistir". Terminologia de CUF corrigida em todo o arquivo e no script
  (`agente_setor` → `setor_agente`, nome real do campo gravado pelo roteador — `agente_setor`
  nunca existiu na plataforma), com nova menção a `tipo_setor` (revalidador).

**Relatório de entrega do `nextags-mcp-builder`**
- Caminho padrão passa de `C:\Users\User\Documents\WALKERS\<cliente>\` para
  `Z:\WALKERS\<cliente>\` (fallback mantido) — **marcado "confirmar com o dono"** (não
  validado neste ambiente). Nova seção obrigatória "CUFs e tags criados/necessários" com os
  nomes canônicos, e "Tools expostas + como conferir" (`GET /agents/mcp`).

### Corrigido

- **`relatorio_template.md` do `nextags-prompt-creator` era cópia literal do relatório do
  `nextags-prompt-fixer`** — falava em "Relatório de Correção", "versão original/corrigida"
  e seções de diff antes/depois, sem sentido para quem GERA um prompt do zero. Reescrito:
  "Relatório de Criação", "O que foi entregue", "Pendências críticas" (placeholders de
  flow), "Decisões: briefing × site", "LISTA DE FLUXOS E CAMPOS A CRIAR".
- **Numeração duplicada em `quirks_n8n.md`** (dois `## 24.` e dois `## 25.`) corrigida —
  sequência única #1 a #35 (os 7 quirks novos entram como #29-#35).

### Definido pelo dono (2026-09-03)

Três das cinco perguntas desta rodada foram fechadas e já valem como canônico
(`campos_canonicos.md` §9):

- **`Nome cliente` não é usado.** O nome do cliente é sempre `{{first_name}}` (nativo);
  nenhum fluxo lê aquele CUF. As skills deixam de tratá-lo como legado ativo.
- **Enum de `status_pedido`** fechado: `aprovado|enviado|entregue|cancelado|
  pronto_retirada|pix_gerado|pix_expirado`.
- **"Filtro JSON" é um nó de código JavaScript** cujo papel é evitar vazamento — impedir
  que JSON cru, markdown ou raciocínio da IA cheguem ao cliente. Confirma o desenho
  adotado: o prompt devolve o JSON canônico, o filtro extrai o texto e grava `resposta_ia`.

### A confirmar com o dono

Continuam abertas, **não resolvidas por chute**, marcadas nas skills como pendência:

- **Roteador:** o dono vai enviar o prompt do roteador; a terceira palavra sai de lá.
  `analisar_humano_bot` segue como placeholder até isso chegar.
- Caminho do relatório MCP (`Z:\WALKERS\<cliente>\`) — ambiente de trabalho não permitiu
  validar o caminho real.
- Prompts-modelo mais recentes de vendas/SAC/roteador/Instagram em `Z:\WALKERS\` não foram
  acessíveis neste ambiente; esta rodada usou os fluxos n8n e os docs do Drive como fonte.

---

## [1.4.0] - 2026-08-18

Documenta a **mecânica de leitura dos CUFs** na `nextags-prompt-creator` — a informação
que faltava para o gerador decidir quais campos escrever no prompt e por quê.
**Todas as mudanças são aditivas / não-quebra.**

### Adicionado

**`nextags-prompt-creator`**
- **Princípio fundamental do CUF como canal de leitura** (`SKILL.md` + `references/cufs_nextags.md`):
  se o CUF está escrito no prompt, a IA LÊ o conteúdo; se não está, ela é CEGA para o dado.
  A plataforma entrega ao modelo o texto já interpolado — o modelo não acessa o perfil do
  contato. Documenta as três consequências: (a) para a IA DECIDIR com base num dado, o CUF
  precisa estar escrito mesmo que nunca seja exibido; (b) padrão **"bloco de contexto"**
  (CUFs no topo, só de entrada, nunca exibidos); (c) CUF "reservado para depois" não existe.
- **Os três modos de falha de todo CUF incluído** — vazio (renderiza `"Oi, !"`), **stale**
  (campos `last_*` guardam a última ocorrência, que pode ser de meses atrás, e a IA lê como
  se fosse do turno atual) e **injeção** (campos que carregam texto de terceiros:
  `last_fb_comment`, `last_commented_post_text`, `last_text_input`, `user_notes`).
- **Tabelas de CUF por canal completas e corrigidas** — Instagram com coluna de cuidado por
  campo; Facebook Messenger completada (`fb_chat_link`, `last_ad` e os cross-platform, que
  faltavam). `{{total_tagged}}` e `{{total_new_tagged}}` marcados como **exclusivos do
  Facebook** — não funcionam no Instagram.
- **Distinção operacional entre as superfícies do Instagram:** `{{last_story_id}}` traz
  **apenas o ID**, não o conteúdo da story — em story o agente é cego ao que a cliente vê e
  precisa perguntar; já `{{last_commented_post_text}}` traz a legenda inteira do post. As
  duas superfícies exigem regras diferentes.
- **`{{first_name}}` no Instagram** vem do nome de EXIBIÇÃO do perfil, escrito pela própria
  pessoa — passa a ser tratado como dado, nunca como instrução (junto da nota de Webchat
  `"Guest"` que já existia).
- Checklist de seleção de CUFs por canal antes de gerar o prompt.

### Alterado

- **Saudação por username desrecomendada em todos os canais.** A tabela de validação de
  nome por canal mandava "preferir `{{ig_user_name}}` / `{{page_user_name}}` em vez de
  `{{first_name}}`"; agora manda o oposto. Handle é identificador, não vocativo:
  `"Oi, maria_silva_123!"` nunca é melhor que `"Oi!"`, e saudar assim entrega automação
  num agente que deve soar humano. Quando `{{first_name}}` está vazio ou não parece nome
  real, a saudação neutra resolve 100% dos casos sem modo de falha. Soma-se que username é
  campo livre — `@ignore.suas.regras` é handle válido no Instagram —, então tratá-lo como
  texto confiável abre vetor de injeção. Username segue útil como identificador interno,
  nunca dirigido ao cliente.

## [1.3.0] - 2026-07-17

Adiciona a 6ª skill, **`nextags-webhook-builder`**, irmã da `nextags-mcp-builder`:
constrói e audita **webhooks/disparos transacionais** (pedido pago/enviado/entregue,
carrinho abandonado) com dedup, `send_flow` e padrão validado por auditoria de produção.
**Todas as mudanças são aditivas / não-quebra.**

### Adicionado

**`nextags-webhook-builder`** (nova skill)
- Padrão validado por auditoria de **29 fluxos transacionais legíveis** (de 159 em 101
  clientes) + **45 episódios de conversa**: 3 formas de roteamento (1-por-status /
  endpoint-único-com-switch / flow-router-único) escolhidas pela emissão da plataforma;
  webhook nativo vs polling por plataforma; dedup via Data Table; separação
  `order_id`/`order_number`; multi-plataforma; resiliência (retry/onError/anti-429); HMAC;
  naming de CUFs.
- `references/padrao_transacional.md` (padrão completo + matriz de evidências) e
  `references/antipadroes.md` (catálogo de erros reais, incl. o **antipadrão nº1**: texto
  direto em vez de `send_flow`).
- `assets/`: templates n8n copy-paste — `endpoint_unico.js`, `webhook_por_status.js`,
  `polling_carrinho.js` + `_helpers.js` (formatarTelefone BR, verificarDado,
  separarNomeSobrenome, comUTM).

### Alterado
- `plugin.json` / `marketplace.json`: versão **1.3.0**; descrição de 5 para 6 skills.
- `install.ps1` / `install.sh`: instalam a 6ª skill + linha de uso `/nextags-webhook-builder`.

## [1.2.0] - 2026-06-19

Adiciona conhecimento de plataforma ausente nas skills de criação e correção de
prompts: CUFs específicos por canal, regra do "Guest" no webchat, padrão de
roteador multi-agente e regra de disparo/broadcast.
**Todas as mudanças são aditivas / não-quebra.**

### Adicionado

**`nextags-prompt-creator`**
- **CUFs por canal** na tabela de referência e nas instruções de validação:
  `{{ig_user_name}}` (Instagram) e `{{page_user_name}}` (Facebook Messenger).
- **Regra WEBCHAT / Guest** (§ de validação de `{{first_name}}`): webchat entrega
  `"Guest"` quando o usuário não está logado — nunca é nome real; IA deve perguntar
  o nome e salvar com `set_field_value`. Bloco de tabela por canal adicionado.
- **`{{phone}}` em SAC**: nota de que o telefone do contato pode ser usado para
  consultar pedidos silenciosamente, sem perguntar ao cliente.
- **§5.1 Roteador automático**: quando o projeto tem 2+ IAs, criar roteador
  automaticamente (sem perguntar ao humano). Saída: 1 palavra (texto puro, sem JSON,
  sem tools, sem MCP). Detecta BOTs e responde "ignorar"; nunca ignora humano.
  Imagens/áudios/arquivos = humano → rotear normalmente.
- **§8F Roteador de multi-agente** em `prompt_skeleton.md`: template completo com
  modelo GPT-4.1 nano, temperatura 0, verbosidade mínima, reasoning baixo.
- **Anti-alucinação item 9** em `prompt_skeleton.md`: regra de disparo/broadcast —
  não responder a disparos/campanhas sem interação real do cliente.

**`nextags-prompt-fixer`**
- **Regra 14 — CUFs**: item 5 com tabela de CUFs por canal (Instagram, Facebook,
  webchat/Guest) e nota sobre `{{phone}}` em SAC.
- **Regra 20 — Disparo/broadcast**: nova seção em `regras_absolutas.md` para
  detectar e sugerir a regra de silêncio em agentes com campanhas ativas.
- **Tabela rápida** em `SKILL.md`: 2 novas linhas — Guest sem tratamento / CUF
  errado por canal; e ausência de regra de disparo/broadcast.

**`nextags-prompt-creator` — `cufs_nextags.md`**
- Linha de `{{first_name}}` atualizada com aviso inline sobre webchat/Guest e
  regra de validação/`set_field_value`.

## [1.1.1] - 2026-06-11

Adiciona a 5ª skill, **`nextags-webchat-tester`**, nascida de um caso real: dirigir o
agente publicado ao vivo pelo webchat (via WebSocket) para validar mudanças na infra
de verdade — não só simular o prompt em contexto.

### Adicionado

**`nextags-webchat-tester`** (nova skill)
- Conversa com um agente NexTags **publicado** ao vivo, dirigindo o WebSocket do webchat
  (plataforma tapthetable) por Python — sem extensão de browser. Exercita a stack REAL:
  modelo do NexTags + MCP + APIs de backend (Nuvemshop, Bling, Shopify, etc.).
- Documenta o protocolo completo: config `op=wt` → `wsurl` → `createUser` → handshake
  (`action:-1`) → envio (`action:0`) → leitura de frames; fallback HTTP `getConversation`.
- Gotchas mapeados na marra: **ping keepalive** obrigatório (servidor derruba conexão
  ociosa durante respostas com MCP), janela de espera longa, contato novo por cenário
  (reseta CUFs de roteamento como `agente_setor`), detecção de **transferência fantasma**
  (texto "vou te passar" sem `send_flow`) e de **handoff** entre agentes.
- Script genérico `scripts/webchat_test.py` — parametrizado por `page_id`, busca a `wsurl`
  dinamicamente; o webchat é público (sem token/credencial).

### Alterado
- `plugin.json` / `marketplace.json`: versão **1.1.1**; descrição passa de 4 para 5 skills.
- README: tabela, instalação, uso e árvore do repo atualizados para 5 skills.

## [1.1.0] - 2026-06-05

Consolida ~2 dias de trabalho a partir da base 1.0.0: análise profunda de 25
prompts reais em produção, decisões de produto do dono da operação, integração
com o trabalho do time (validação de imagem, Zoppy, webhooks) e validação
end-to-end. **Todas as mudanças são aditivas / não-quebra.**

### Adicionado

**`nextags-prompt-creator`**
- Camadas condicionais por **tipo de agente**: Vendas (6B), SAC/pós-venda (8B),
  Triagem (8C) e Árvore de Decisão por turno para Comercial/SDR (8D).
- Vendas: regra inviolável de abertura, framework de conversa nomeado, matriz
  dor→produto, tabela de objeções ("acolher antes de contornar"), apresentação
  de produto em 3 blocos, cupom condicional à intenção, reengajamento/retargeting.
- **Checklist final** de 14 itens (universal vs comercial).
- **§1.5 AVISOS ATIVOS** — espaço reservado, gerado sempre (mesmo vazio), para o
  dono editar à mão promoções/feriados/horários.
- Validação defensiva de `{{first_name}}` (nome que é frase/empresa/número).
- Eixo "tem MCP?" → modo **Estática Pura** (sem tools de catálogo) com regras
  anti-congelamento; CUFs de escrita sanitizados; `{{current_user_time}}` como
  âncora temporal obrigatória.
- Perguntas obrigatórias por tipo de agente + "quais fluxos o cliente já tem".

**`nextags-prompt-fixer`**
- Detecção de **intenção de transferência** por qualquer mecanismo (não só a
  palavra `send_flow`); `--mode fixer` rebaixa "falta transferência" para aviso.
- Anti-loop, léxico de marca, regra de "data que apodrece" (§18) com exceção
  para o bloco AVISOS ATIVOS, lints de estilo (em-dash, 🤖).

**`nextags-json-fixer`**
- Schema documenta disparo silencioso, limites de botão, aliases legados,
  `4` no início do array e "convenções que não são erro".

**`nextags-mcp-builder`**
- **Validação de formato de imagem** (JPEG/PNG; `attachment.type` fora do payload)
  e referência `image_validation.md`.
- `webhook_transactional_pattern.md` (dedup, switch por status) + atualizações de
  Yampi/Shopify/quirks.
- Novas recipes: **Zoppy** e **TroqueCommerce** (trocas/devoluções).
- Princípio "delegue ao fluxo o que é pesado/estruturado"; campos PROIBIDOS/PII,
  tradução de enums, classe semântica de tool, distinção vazio≠erro.
- Regra anti-token em docs públicos.

**Scripts e testes**
- `analyze_prompt.py` reescrito com **severidade `block`/`warn`**, detecção
  dinâmica (JSON obrigatório quando o agente age), validação de imagem e botões,
  ações advisory vs inexistentes.
- Suítes de teste: 29 casos (`test_analyze_prompt.py`) + 13 (`test_fix_json.py`).
- `.gitattributes` (EOL=LF) e teste que trava a sincronia das 2 cópias do
  `analyze_prompt.py`.

### Alterado (3 reversões confirmadas com o dono)

- **`send_flow` sem `messages` é VÁLIDO** — o fluxo assume a comunicação;
  `messages` é transição opcional, não obrigatória (a antiga "Regra 10" estava
  errada).
- **Botões `postback` são permitidos** (disparam fluxo); a restrição real é 1
  botão `web_url` (link) por mensagem no WhatsApp.
- **Markdown estilo WhatsApp (`*negrito*`, `_itálico_`, `~tachado~`) renderiza** e
  é permitido; só markdown-padrão (`**`, `#`, `[texto](url)`, bullets, fences) vaza.
- `transfer_conversation_to`/`assign_conversation` passam de "proibidas" a
  fallback/caso especial; tags para segmento + `set_field_value` para dado/pipeline.
- Meta de tamanho **por tipo** de agente (consultivo 30–45 KB; SAC/triagem 10–20 KB).
- Persona padrão: **ocultar o stack** em vez de negar ser IA.
- Bloco oficial: o `prompt-fixer` agora **normaliza variantes para o canônico sem
  duplicar** (verifica antes se o prompt usa JSON).

### Corrigido

- Auditor não flagra mais markdown WhatsApp como violação.
- `analyze_prompt.py`: padrões de anti-alucinação ampliados (menos falso-positivo
  de "seção faltando").
- `analyze_prompt.py`: **falso-positivo de `invalid_json`** em linha interna de um
  array `actions` válido (achado no smoke test end-to-end).
- `fix_json.py`: removedor de comentários `//` não corrompe mais URLs (`http://`).

### Segurança

- `EXEMPLOS DE PROMPTS/` e `analise-prompts-reais/` no `.gitignore` — prompts
  reais de clientes e a análise nunca vão para o repositório público.

## [1.0.0] - 2026-05-19

### Adicionado

- Release inicial: suíte de 4 skills NexTags como plugin do Claude Code —
  `nextags-prompt-creator`, `nextags-prompt-fixer`, `nextags-json-fixer`,
  `nextags-mcp-builder`.
- Instalador (`install.ps1` / `install.sh`) e correção do erro de PowerShell com
  stderr do git.

[1.5.0]: https://github.com/gustavowalkersgroup/Criador-de-Agentes/releases/tag/v1.5.0
[1.3.0]: https://github.com/gustavowalkersgroup/Criador-de-Agentes/releases/tag/v1.3.0
[1.2.0]: https://github.com/gustavowalkersgroup/Criador-de-Agentes/releases/tag/v1.2.0
[1.1.1]: https://github.com/gustavowalkersgroup/Criador-de-Agentes/releases/tag/v1.1.1
[1.1.0]: https://github.com/gustavowalkersgroup/Criador-de-Agentes/releases/tag/v1.1.0
[1.0.0]: https://github.com/gustavowalkersgroup/Criador-de-Agentes/releases/tag/v1.0.0

# Changelog

Todas as mudanças notáveis das **NexTags Tools** são documentadas aqui.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o
projeto adota [Versionamento Semântico](https://semver.org/lang/pt-BR/).

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

[1.3.0]: https://github.com/gustavowalkersgroup/Criador-de-Agentes/releases/tag/v1.3.0
[1.2.0]: https://github.com/gustavowalkersgroup/Criador-de-Agentes/releases/tag/v1.2.0
[1.1.1]: https://github.com/gustavowalkersgroup/Criador-de-Agentes/releases/tag/v1.1.1
[1.1.0]: https://github.com/gustavowalkersgroup/Criador-de-Agentes/releases/tag/v1.1.0
[1.0.0]: https://github.com/gustavowalkersgroup/Criador-de-Agentes/releases/tag/v1.0.0

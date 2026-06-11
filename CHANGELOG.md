# Changelog

Todas as mudanças notáveis das **NexTags Tools** são documentadas aqui.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o
projeto adota [Versionamento Semântico](https://semver.org/lang/pt-BR/).

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

[1.1.0]: https://github.com/gustavowalkersgroup/Criador-de-Agentes/releases/tag/v1.1.0
[1.0.0]: https://github.com/gustavowalkersgroup/Criador-de-Agentes/releases/tag/v1.0.0

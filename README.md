# NexTags Tools — Suite de Skills para Claude Code e Codex

Coleção de 8 skills profissionais para acelerar a criação, auditoria e correção de agentes de IA da plataforma **NexTags Messenger Messaging Platform**.

| Skill | O que faz |
|---|---|
| `nextags-prompt-creator` | Gera pacotes de agentes NexTags a partir de briefing + URL. Usa a Arquitetura Suprema V7, separa intenção de projeto da verdade de runtime, classifica risco e módulos, gera roteador/revalidador quando necessário, define estado/tools/handoff, inclui inventário Walkers, bateria adversarial e audita automaticamente. |
| `nextags-prompt-fixer` | Audita/corrige prompts existentes contra as Regras Absolutas da plataforma. Detecta JSON inválido, ações proibidas, markdown vazado, placeholders genéricos, seções de meta-documentação, campo de roteamento gravado pela IA (deveria ser só do roteador/revalidador) e enum de transferência fora do canônico. |
| `nextags-json-fixer` | Valida e corrige a SAÍDA JSON gerada pelo agente em runtime. Útil quando o bot retorna JSON quebrado, com fence ```json em volta, sem `messages`, etc. |
| `nextags-mcp-builder` | Constrói o servidor MCP no n8n que liga o agente IA às APIs do cliente (Tray, VTEX, Shopify, Bling, Martz, etc.) — atendimento sob demanda. Garante a infra dos campos canônicos (roteador/revalidador/handoff) sem decidir prompt. |
| `nextags-webhook-builder` | Constrói e audita webhooks/disparos **transacionais** (pedido pago/enviado/entregue, carrinho abandonado) no n8n, com CUFs canônicos, dedup e `send_flow`. Irmã da mcp-builder (disparo proativo). Padrão validado por auditoria de produção. |
| `nextags-prompt-octobercut` | Adapta prompts (e atendimento humano) à cobrança da Meta por mensagem de serviço, vigente desde 01/10/2026: uma resposta = uma mensagem, abertura proativa, perguntas agrupadas, vitrine com 1 foto + 1 mensagem com botão. Audita o prompt, funde o JSON de runtime e estima a economia. |
| `nextags-prompt-instagram` | Monta a automação de **comentários do Instagram**: resposta pública por IA (@autor, preço do MCP), classificador `CHAMAR`/`NAO` que decide sozinho se chama no direct, e abertura do atendimento com resumo e preço real. Gera os 3 prompts, o desenho do fluxo e a bateria de 12 testes. Padrão validado em produção. |
| `nextags-webchat-tester` | Testa o agente PUBLICADO ao vivo, dirigindo o WebSocket do webchat por Python (sem extensão de browser). Exercita a stack real (NexTags + MCP + backend); pega erro de MCP, handoff, transferência fantasma, renderização de card. |

Todas as skills compartilham a mesma referência de **campos canônicos** (`campos_canonicos.md` — roteador, revalidador, handoff e CUFs transacionais), replicada de forma idêntica entre `nextags-prompt-creator`, `nextags-prompt-fixer`, `nextags-mcp-builder` e `nextags-webhook-builder`.

---

## 🚀 Instalação

### Opção 1 — Via Plugin Claude Code (recomendado)

```bash
# Adiciona o marketplace
/plugin marketplace add gustavowalkersgroup/Criador-de-Agentes

# Instala todas as 8 skills de uma vez
/plugin install nextags-tools@nextags-marketplace
```

Atualizações futuras via `/plugin marketplace update`.

### Opção 2 — Script de instalação (fallback)

**Linux/macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/gustavowalkersgroup/Criador-de-Agentes/main/install.sh | bash
```

**Windows PowerShell:**
```powershell
irm https://raw.githubusercontent.com/gustavowalkersgroup/Criador-de-Agentes/main/install.ps1 | iex
```

Os scripts copiam as 8 skills pra `~/.claude/skills/` e, se o Codex estiver instalado (`~/.codex`), também pra `~/.codex/skills/`. Versões anteriores vão pra `skills-backup/` ao lado de cada destino. Para forçar a instalação no Codex: `INSTALL_CODEX=1` (bash) ou `$env:INSTALL_CODEX = '1'` (PowerShell).

### Opção 3 — Instalação manual (controle total)

```bash
git clone https://github.com/gustavowalkersgroup/Criador-de-Agentes.git
cd Criador-de-Agentes
cp -r skills/* ~/.claude/skills/
cp -r skills/* ~/.codex/skills/   # Codex (opcional)
```

### Codex

As skills usam o formato padrão `SKILL.md` (frontmatter `name` + `description`), lido também pelo Codex. Depois de instalar em `~/.codex/skills/`, reinicie o Codex e chame com `$nextags-prompt-octobercut` (ou descreva a tarefa).

---

## 📋 Pré-requisitos

- **Claude Code** instalado e funcional
- **Python 3.8+** (usado pelos analyzers das skills prompt-creator e prompt-fixer)
- **Git** (apenas se for usar script de install remoto)

---

## 🎯 Como usar

Após instalar, reinicia o Claude Code e usa qualquer uma das 8 skills:

```bash
/nextags-prompt-creator   # gerar prompt do zero
/nextags-prompt-fixer     # auditar/corrigir prompt existente
/nextags-json-fixer       # validar JSON de saída do agente
/nextags-mcp-builder      # construir MCP no n8n pra ligar APIs (atendimento)
/nextags-webhook-builder  # construir/auditar webhooks transacionais (disparo proativo)
/nextags-webchat-tester   # testar o agente publicado ao vivo no webchat
/nextags-prompt-octobercut # agrupar respostas (cobrança Meta por mensagem de serviço)
/nextags-prompt-instagram # automação de comentários do Instagram (resposta pública + DM)
```

Para alinhar as skills antigas ao OctoberCut, use o prompt pronto em [`prompts/ajustar-skills-octobercut.md`](prompts/ajustar-skills-octobercut.md).

Cada skill responde a triggers em português e inglês — pode chamar diretamente ou descrever a tarefa naturalmente.

---

## 🧠 Filosofia

As skills compartilham princípios comuns:

- **Bloco oficial NexTags obrigatório** — toda IA gerada inclui as instruções canônicas de saída JSON.
- **Sem markdown vazando** — proibido fences ` ```json `, asteriscos, bullets, headers dentro dos campos de texto.
- **CUFs do sistema** — placeholders devem usar `{{first_name}}` etc., nunca `[nome]`.
- **Prompts enxutos, meta por tipo** — consultivo (Vendas) mira 30-45 KB; SAC/triagem mira 10-20 KB. Auditoria/changelog/pendências vão pro RELATÓRIO, não pro prompt.
- **IA nunca roteia entre agentes** — o roteador (1 palavra, roda a cada mensagem) grava `setor_agente`; a IA só transfere para humano, e faz isso gravando `motivo_transferencia` + `prioridade_pipeline` + `resumo_pipeline` e disparando UM fluxo de pipeline (`send_flow`).
- **OctoberCut** — desde 01/10/2026 a Meta cobra cada mensagem de serviço. Cada bolha custa: uma resposta = uma mensagem, sem typing `4` entre textos.
- **Campos canônicos compartilhados** (`campos_canonicos.md`) — nome exato, minúsculas, snake_case, sem acento; o mesmo em qualquer cliente, salvo exceção registrada no relatório.

---

## 📦 Estrutura do repo

```
Criador-de-Agentes/
├── .claude-plugin/
│   ├── plugin.json              # manifesto do plugin
│   └── marketplace.json         # marketplace de 1 plugin
├── skills/
│   ├── nextags-prompt-creator/
│   ├── nextags-prompt-fixer/
│   ├── nextags-json-fixer/
│   ├── nextags-mcp-builder/
│   ├── nextags-webhook-builder/
│   ├── nextags-webchat-tester/
│   ├── nextags-prompt-octobercut/
│   └── nextags-prompt-instagram/
├── prompts/
│   └── ajustar-skills-octobercut.md  # prompt p/ alinhar as skills ao OctoberCut
├── install.sh                   # instalador Linux/macOS
├── install.ps1                  # instalador Windows
└── README.md
```

---

## 🐛 Reportar problemas

Abra uma issue em [github.com/gustavowalkersgroup/Criador-de-Agentes/issues](https://github.com/gustavowalkersgroup/Criador-de-Agentes/issues).

---

## 📝 Licença

MIT — veja `LICENSE`.

---

Made with 💚 by [Gustavo Walkers Group](https://github.com/gustavowalkersgroup) para a plataforma NexTags.

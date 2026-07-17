# NexTags Tools — Suite de Skills para Claude Code

Coleção de 6 skills profissionais para acelerar a criação, auditoria e correção de agentes de IA da plataforma **NexTags Messenger Messaging Platform**.

| Skill | O que faz |
|---|---|
| `nextags-prompt-creator` | Gera prompts de atendimento NexTags do zero a partir de briefing + URL da empresa. Faz scraping, faz perguntas obrigatórias, audita automaticamente. |
| `nextags-prompt-fixer` | Audita/corrige prompts existentes contra as Regras Absolutas da plataforma. Detecta JSON inválido, ações proibidas, markdown vazado, placeholders genéricos, seções de meta-documentação no prompt. |
| `nextags-json-fixer` | Valida e corrige a SAÍDA JSON gerada pelo agente em runtime. Útil quando o bot retorna JSON quebrado, com fence ```json em volta, sem `messages`, etc. |
| `nextags-mcp-builder` | Constrói o servidor MCP no n8n que liga o agente IA às APIs do cliente (Tray, VTEX, Shopify, Bling, Martz, etc.) — atendimento sob demanda. |
| `nextags-webhook-builder` | Constrói e audita webhooks/disparos **transacionais** (pedido pago/enviado/entregue, carrinho abandonado) no n8n, roteando pra NexTags com dedup e `send_flow`. Irmã da mcp-builder (disparo proativo). Padrão validado por auditoria de produção. |
| `nextags-webchat-tester` | Testa o agente PUBLICADO ao vivo, dirigindo o WebSocket do webchat por Python (sem extensão de browser). Exercita a stack real (NexTags + MCP + backend); pega erro de MCP, handoff, transferência fantasma, renderização de card. |

---

## 🚀 Instalação

### Opção 1 — Via Plugin Claude Code (recomendado)

```bash
# Adiciona o marketplace
/plugin marketplace add gustavowalkersgroup/Criador-de-Agentes

# Instala todas as 6 skills de uma vez
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

Os scripts copiam as 6 skills pra `~/.claude/skills/` e fazem backup das versões anteriores (se existirem) com sufixo `.bak`.

### Opção 3 — Instalação manual (controle total)

```bash
git clone https://github.com/gustavowalkersgroup/Criador-de-Agentes.git
cd Criador-de-Agentes
cp -r skills/* ~/.claude/skills/
```

---

## 📋 Pré-requisitos

- **Claude Code** instalado e funcional
- **Python 3.8+** (usado pelos analyzers das skills prompt-creator e prompt-fixer)
- **Git** (apenas se for usar script de install remoto)

---

## 🎯 Como usar

Após instalar, reinicia o Claude Code e usa qualquer uma das 6 skills:

```bash
/nextags-prompt-creator   # gerar prompt do zero
/nextags-prompt-fixer     # auditar/corrigir prompt existente
/nextags-json-fixer       # validar JSON de saída do agente
/nextags-mcp-builder      # construir MCP no n8n pra ligar APIs (atendimento)
/nextags-webhook-builder  # construir/auditar webhooks transacionais (disparo proativo)
/nextags-webchat-tester   # testar o agente publicado ao vivo no webchat
```

Cada skill responde a triggers em português e inglês — pode chamar diretamente ou descrever a tarefa naturalmente.

---

## 🧠 Filosofia

As skills compartilham princípios comuns:

- **Bloco oficial NexTags obrigatório** — toda IA gerada inclui as instruções canônicas de saída JSON.
- **Sem markdown vazando** — proibido fences ` ```json `, asteriscos, bullets, headers dentro dos campos de texto.
- **CUFs do sistema** — placeholders devem usar `{{first_name}}` etc., nunca `[nome]`.
- **Prompts enxutos** — meta de 15-20 KB por prompt. Auditoria/changelog/pendências vão pro RELATÓRIO, não pro prompt.
- **Ações permitidas explícitas** — só `send_flow` pra humano e `set_field_value` pra roteamento entre agentes.

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
│   └── nextags-webchat-tester/
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

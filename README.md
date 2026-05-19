# NexTags Tools — Suite de Skills para Claude Code

Coleção de 4 skills profissionais para acelerar a criação, auditoria e correção de agentes de IA da plataforma **NexTags Messenger Messaging Platform**.

| Skill | O que faz |
|---|---|
| `nextags-prompt-creator` | Gera prompts de atendimento NexTags do zero a partir de briefing + URL da empresa. Faz scraping, faz perguntas obrigatórias, audita automaticamente. |
| `nextags-prompt-fixer` | Audita/corrige prompts existentes contra as Regras Absolutas da plataforma. Detecta JSON inválido, ações proibidas, markdown vazado, placeholders genéricos, seções de meta-documentação no prompt. |
| `nextags-json-fixer` | Valida e corrige a SAÍDA JSON gerada pelo agente em runtime. Útil quando o bot retorna JSON quebrado, com fence ```json em volta, sem `messages`, etc. |
| `nextags-mcp-builder` | Constrói o servidor MCP no n8n que liga o agente IA às APIs do cliente (Tray, VTEX, Shopify, Bling, Martz, etc.). |

---

## 🚀 Instalação

### Opção 1 — Via Plugin Claude Code (recomendado)

```bash
# Adiciona o marketplace
/plugin marketplace add gustavowalkersgroup/Criador-de-Agentes

# Instala todas as 4 skills de uma vez
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

Os scripts copiam as 4 skills pra `~/.claude/skills/` e fazem backup das versões anteriores (se existirem) com sufixo `.bak`.

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

Após instalar, reinicia o Claude Code e usa qualquer uma das 4 skills:

```bash
/nextags-prompt-creator   # gerar prompt do zero
/nextags-prompt-fixer     # auditar/corrigir prompt existente
/nextags-json-fixer       # validar JSON de saída do agente
/nextags-mcp-builder      # construir MCP no n8n pra ligar APIs
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
│   └── nextags-mcp-builder/
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

#!/usr/bin/env bash
# install.sh — instala as 7 skills NexTags no ~/.claude/skills/ (Claude Code) e, se o Codex
# estiver instalado (~/.codex) ou INSTALL_CODEX=1, também em ~/.codex/skills/.
# Uso: curl -fsSL https://raw.githubusercontent.com/gustavowalkersgroup/Criador-de-Agentes/main/install.sh | bash
#      ou: bash install.sh (rodando localmente após clone)

set -euo pipefail

REPO_URL="https://github.com/gustavowalkersgroup/Criador-de-Agentes.git"
SKILLS=("nextags-prompt-creator" "nextags-prompt-fixer" "nextags-json-fixer" "nextags-mcp-builder" "nextags-webchat-tester" "nextags-webhook-builder" "nextags-prompt-octobercut")
CLAUDE_DIR="${HOME}/.claude/skills"
CODEX_HOME_DIR="${CODEX_HOME:-${HOME}/.codex}"
TARGETS=("$CLAUDE_DIR")
if [ -d "$CODEX_HOME_DIR" ] || [ "${INSTALL_CODEX:-0}" = "1" ]; then
    TARGETS+=("${CODEX_HOME_DIR}/skills")
fi

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   NexTags Tools — Instalação de 7 Skills      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""

# 1. Detecta ambiente local vs. via curl
if [ -d "./skills" ] && [ -d "./.claude-plugin" ]; then
    echo -e "${GREEN}✓${NC} Detectado clone local. Usando skills locais."
    SRC_DIR="./skills"
    NEED_CLEANUP=false
else
    echo -e "${YELLOW}→${NC} Modo remoto. Clonando repo temporariamente..."
    TMP_DIR=$(mktemp -d)
    git clone --depth 1 "$REPO_URL" "$TMP_DIR" > /dev/null 2>&1
    SRC_DIR="$TMP_DIR/skills"
    NEED_CLEANUP=true
fi

# 2. Verifica deps
echo -e "${YELLOW}→${NC} Verificando dependências..."
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}✗${NC} Python não encontrado. As skills prompt-creator/prompt-fixer usam analyzer Python."
    echo "   Instale Python 3.8+ e tente de novo."
    exit 1
fi
echo -e "${GREEN}✓${NC} Python OK"

# 3/4. Copia cada skill para cada destino (Claude Code e, se houver, Codex)
for TARGET_DIR in "${TARGETS[@]}"; do
    mkdir -p "$TARGET_DIR"
    BACKUP_DIR="$(dirname "$TARGET_DIR")/skills-backup"
    echo ""
    echo -e "${YELLOW}→${NC} Instalando skills em $TARGET_DIR..."
    for skill in "${SKILLS[@]}"; do
        if [ ! -d "$SRC_DIR/$skill" ]; then
            echo -e "${RED}✗${NC} Skill não encontrada no repo: $skill"
            continue
        fi
        if [ -d "$TARGET_DIR/$skill" ]; then
            # Backups ficam FORA da pasta de skills pra não aparecerem no agente
            mkdir -p "$BACKUP_DIR"
            TIMESTAMP=$(date +%Y%m%d-%H%M%S)
            echo -e "${YELLOW}⚠${NC}  Já existe: $skill — backup em $BACKUP_DIR/"
            mv "$TARGET_DIR/$skill" "$BACKUP_DIR/$skill-$TIMESTAMP"
        fi
        cp -r "$SRC_DIR/$skill" "$TARGET_DIR/"
        echo -e "${GREEN}✓${NC} Instalada: $skill"
    done
done

# 5. Cleanup
if [ "$NEED_CLEANUP" = true ]; then
    rm -rf "$TMP_DIR"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         Instalação concluída! 🎉              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo "Skills instaladas em: ${TARGETS[*]}"
if [ "${#TARGETS[@]}" -eq 1 ]; then
    echo "(Codex não detectado. Para instalar no Codex também: INSTALL_CODEX=1 bash install.sh)"
fi
echo ""
echo "Como usar no Claude Code:"
echo "  /nextags-prompt-creator   # gerar prompt do zero"
echo "  /nextags-prompt-fixer     # auditar/corrigir prompt"
echo "  /nextags-json-fixer       # validar saída JSON do agente"
echo "  /nextags-mcp-builder      # construir MCP no n8n (atendimento sob demanda)"
echo "  /nextags-webhook-builder  # construir/auditar webhooks transacionais (disparo proativo)"
echo "  /nextags-webchat-tester   # testar o agente publicado no webchat"
echo "  /nextags-prompt-octobercut # agrupar respostas (cobrança Meta por mensagem)"
echo ""
echo "No Codex: \$nextags-prompt-octobercut (ou descreva a tarefa; a skill é escolhida pela descrição)"
echo ""
echo "Backup das skills anteriores (se existirem): pasta skills-backup/ ao lado de cada destino."

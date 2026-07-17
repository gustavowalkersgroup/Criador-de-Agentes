#!/usr/bin/env bash
# install.sh — instala as 6 skills NexTags no ~/.claude/skills/ sem precisar de marketplace.
# Uso: curl -fsSL https://raw.githubusercontent.com/gustavowalkersgroup/Criador-de-Agentes/main/install.sh | bash
#      ou: bash install.sh (rodando localmente após clone)

set -euo pipefail

REPO_URL="https://github.com/gustavowalkersgroup/Criador-de-Agentes.git"
SKILLS=("nextags-prompt-creator" "nextags-prompt-fixer" "nextags-json-fixer" "nextags-mcp-builder" "nextags-webchat-tester" "nextags-webhook-builder")
TARGET_DIR="${HOME}/.claude/skills"

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   NexTags Tools — Instalação de 6 Skills      ║${NC}"
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

# 3. Cria pasta destino
mkdir -p "$TARGET_DIR"

# 4. Copia cada skill
echo ""
echo -e "${YELLOW}→${NC} Instalando skills em $TARGET_DIR..."
for skill in "${SKILLS[@]}"; do
    if [ ! -d "$SRC_DIR/$skill" ]; then
        echo -e "${RED}✗${NC} Skill não encontrada no repo: $skill"
        continue
    fi
    if [ -d "$TARGET_DIR/$skill" ]; then
        # Move backups pra FORA de ~/.claude/skills/ pra não aparecerem no Claude Code
        BACKUP_DIR="${HOME}/.claude/skills-backup"
        mkdir -p "$BACKUP_DIR"
        TIMESTAMP=$(date +%Y%m%d-%H%M%S)
        echo -e "${YELLOW}⚠${NC}  Já existe: $skill — backup em ~/.claude/skills-backup/"
        mv "$TARGET_DIR/$skill" "$BACKUP_DIR/$skill-$TIMESTAMP"
    fi
    cp -r "$SRC_DIR/$skill" "$TARGET_DIR/"
    echo -e "${GREEN}✓${NC} Instalada: $skill"
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
echo "Skills instaladas em: $TARGET_DIR"
echo ""
echo "Como usar no Claude Code:"
echo "  /nextags-prompt-creator   # gerar prompt do zero"
echo "  /nextags-prompt-fixer     # auditar/corrigir prompt"
echo "  /nextags-json-fixer       # validar saída JSON do agente"
echo "  /nextags-mcp-builder      # construir MCP no n8n (atendimento sob demanda)"
echo "  /nextags-webhook-builder  # construir/auditar webhooks transacionais (disparo proativo)"
echo "  /nextags-webchat-tester   # testar o agente publicado no webchat"
echo ""
echo "Backup das skills anteriores (se existirem): *.bak na mesma pasta."

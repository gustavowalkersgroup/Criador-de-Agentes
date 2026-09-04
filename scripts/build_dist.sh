#!/usr/bin/env bash
# Regenera dist/<skill>.zip com pasta raiz <skill>/ (SKILL.md em <skill>/SKILL.md),
# layout exigido pelo upload de skill no claude.ai. Uso: bash scripts/build_dist.sh (de qualquer diretório)
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
for dir in skills/*/; do
  skill=$(basename "$dir")
  zip_path="dist/${skill}.zip"
  rm -f "$zip_path"
  (cd skills && zip -qr -X "../$zip_path" "$skill" -x '*/__pycache__/*' -x '*.pyc')
  echo "$zip_path: $(unzip -Z1 "$zip_path" | wc -l) arquivos"
done

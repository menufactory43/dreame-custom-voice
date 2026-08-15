#!/usr/bin/env bash
# Télécharge la voix GLaDOS-FR pré-entraînée (ONNX + config) depuis la Release.
# Ensuite : python3 scripts/02-generate-voice.py --all --backend piper
set -euo pipefail
cd "$(dirname "$0")/.."

REPO="menufactory43/dreame-custom-voice"
TAG="${GLADOS_FR_TAG:-glados-fr-v1}"
BASE="https://github.com/${REPO}/releases/download/${TAG}"
OUT=dist
mkdir -p "$OUT"

for f in fr_FR-glados_fr-medium.onnx fr_FR-glados_fr-medium.onnx.json; do
  [ -f "$OUT/$f" ] && [ -s "$OUT/$f" ] && { echo "déjà présent : $OUT/$f"; continue; }
  echo "Téléchargement $f..."
  curl -sSL -o "$OUT/$f" "$BASE/$f"
done

ls -lh "$OUT"/fr_FR-glados_fr-medium.onnx*
echo
echo "Puis :"
echo "  export PIPER_MODEL=$PWD/$OUT/fr_FR-glados_fr-medium.onnx"
echo "  export PIPER_CONFIG=$PWD/$OUT/fr_FR-glados_fr-medium.onnx.json"
echo "  python3 scripts/02-generate-voice.py --all --backend piper"
echo "  bash scripts/03-build-pack.sh && bash scripts/04-serve.sh && bash scripts/05-install.sh"

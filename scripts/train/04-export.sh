#!/usr/bin/env bash
# Exporte le meilleur checkpoint (val_mos) en modèle ONNX prêt pour piper,
# en appliquant le correctif des assert non-traçables (torch.export).
set -euo pipefail
cd "$(dirname "$0")/../.."
ROOT="$PWD"

WORK="${PIPER_WORK:-$ROOT/build/piper}"
OUT_DIR="${PIPER_OUT:-$ROOT/dist}"
mkdir -p "$OUT_DIR"
cd "$WORK/piper1-gpl"

CKPT=$(ls -t lightning_logs/*/checkpoints/epoch=*-val_mos=*.ckpt 2>/dev/null | head -1)
[ -n "$CKPT" ] || CKPT=$(ls -t lightning_logs/*/checkpoints/last.ckpt 2>/dev/null | head -1)
[ -n "$CKPT" ] || { echo "Aucun checkpoint trouvé dans lightning_logs/"; exit 1; }
echo "Checkpoint retenu : $CKPT"

# L'assert data-dependent de rational_quadratic_spline n'est pas traçable par
# torch.export. On le neutralise pendant la compilation (il reste actif à l'inférence).
grep -q "torch.compiler.is_compiling()" src/piper/train/vits/transforms.py || {
  sed -i 's/        assert (discriminant >= 0).all(), discriminant/        if not torch.compiler.is_compiling():\n            assert (discriminant >= 0).all(), discriminant/' \
    src/piper/train/vits/transforms.py
}

./.venv/bin/python "$ROOT/scripts/train/export_onnx_fixed.py" \
  --checkpoint "$CKPT" \
  --output-file "$OUT_DIR/fr_FR-glados_fr-medium.onnx"

cp "$ROOT/build/glados_fr_config.json" "$OUT_DIR/fr_FR-glados_fr-medium.onnx.json" 2>/dev/null \
  || echo "ATTENTION : config.json introuvable — copie-la manuellement à côté du .onnx"

ls -lh "$OUT_DIR"/fr_FR-glados_fr-medium.onnx*
echo
echo "Pour générer le pack avec cette voix :"
echo "  export PIPER_MODEL=$OUT_DIR/fr_FR-glados_fr-medium.onnx"
echo "  export PIPER_CONFIG=$OUT_DIR/fr_FR-glados_fr-medium.onnx.json"
echo "  python3 scripts/02-generate-voice.py --all --backend piper"
echo "  bash scripts/03-build-pack.sh && bash scripts/05-install.sh"

#!/usr/bin/env bash
# Fine-tune de la voix sur le dataset préparé (build/train), à partir du
# checkpoint français siwis/medium.
#
# Sur une A40 (~46 Go VRAM) : ~35 s/époque avec batch 16. Pour imprimer le
# caractère GLaDOS sur ~25 min d'audio, visez 500 à 1000 époques.
#
# Interruption/redémarrage : les checkpoints sont sauvegardés en continu dans
# build/piper/piper1-gpl/lightning_logs/*/checkpoints/ ; relancez avec
# --ckpt_path sur le dernier `last.ckpt`.
set -euo pipefail
cd "$(dirname "$0")/../.."

WORK="${PIPER_WORK:-$PWD/build/piper}"
DS="$PWD/build/train"
CACHE="$PWD/build/train_cache"
CFG="$PWD/build/glados_fr_config.json"
VOICE="${VOICE_NAME:-glados_fr}"
EPOCHS="${MAX_EPOCHS:-1000}"
BATCH="${BATCH_SIZE:-16}"

cd "$WORK/piper1-gpl"
[ -f "$DS/metadata.csv" ] || { echo "Lance d'abord scripts/train/01-prepare-dataset.py"; exit 1; }
[ -f base_fr_v2.ckpt ] || { echo "Lance d'abord scripts/train/02-install-piper.sh"; exit 1; }

mkdir -p "$CACHE"
./.venv/bin/python -m piper.train fit \
  --data.voice_name "$VOICE" \
  --data.csv_path "$DS/metadata.csv" \
  --data.audio_dir "$DS/audio" \
  --model.sample_rate 22050 \
  --data.espeak_voice fr \
  --data.cache_dir "$CACHE" \
  --data.config_path "$CFG" \
  --data.batch_size "$BATCH" \
  --data.num_workers 4 \
  --ckpt_path "$WORK/base_fr_v2.ckpt" \
  --trainer.accelerator gpu \
  --trainer.devices 1 \
  --trainer.precision 16-mixed \
  --trainer.max_epochs "$EPOCHS" \
  --trainer.check_val_every_n_epoch 5 \
  | tee "$PWD/build/train.log"

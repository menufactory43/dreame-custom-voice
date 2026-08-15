#!/usr/bin/env bash
# Installe l'environnement d'entraînement piper1-gpl et télécharge le checkpoint
# français de départ (siwis/medium). À lancer sur une machine avec GPU CUDA
# (RunPod, Vast.ai, machine locale...) — voir docs/TRAINING.md.
set -euo pipefail
cd "$(dirname "$0")/../.."

WORK="${PIPER_WORK:-$PWD/build/piper}"
mkdir -p "$WORK"
export DEBIAN_FRONTEND=noninteractive

echo "== 1. Dépendances système =="
sudo apt-get update -qq
sudo apt-get install -y -qq build-essential cmake ninja-build espeak-ng git ffmpeg python3-venv

echo "== 2. piper1-gpl =="
cd "$WORK"
[ -d piper1-gpl/.git ] || git clone --depth 1 https://github.com/OHF-voice/piper1-gpl.git
cd piper1-gpl
python3 -m venv .venv
./.venv/bin/pip -q install --upgrade pip
./.venv/bin/pip -q install -e ".[train]"
# espeakbridge est compilé par CMake via scikit-build, mais l'extra "dev" seul le
# fournit ; on l'installe puis on build l'extension.
./.venv/bin/pip -q install "scikit-build<1"
bash build_monotonic_align.sh
./.venv/bin/python setup.py build_ext --inplace >/dev/null 2>&1 || {
  echo "build_ext a échoué (espeakbridge). Détail :"; cat /tmp/piper_build.log 2>/dev/null; exit 1; }
./.venv/bin/python -c "from piper import espeakbridge; print('espeakbridge OK')"
./.venv/bin/python -c "from piper.train.vits import monotonic_align; print('monotonic_align OK')"

echo "== 3. Checkpoint français de départ (siwis/medium) =="
CKPT="epoch%3D3304-step%3D2050940.ckpt"
URL="https://huggingface.co/datasets/rhasspy/piper-checkpoints/resolve/main/fr/fr_FR/siwis/medium/$CKPT"
[ -f base_fr.ckpt ] || curl -sSL -o base_fr.ckpt "$URL"
curl -sSL -o base_fr_config.json \
  "https://huggingface.co/datasets/rhasspy/piper-checkpoints/resolve/main/fr/fr_FR/siwis/medium/config.json"

echo "== 4. Conversion du checkpoint (Lightning 1.x -> 2.x, torch 2.6+) =="
./.venv/bin/python - <<'PY'
import torch, lightning
from piper.train.vits.lightning import VitsModel

old = torch.load("base_fr.ckpt", map_location="cpu", weights_only=False)
hp = dict(old["hyper_parameters"])
sig = VitsModel.__init__.__code__.co_varnames[:VitsModel.__init__.__code__.co_argcount]
sel = {k: v for k, v in hp.items() if k in sig}
sel.pop("dataset", None)  # contient un PosixPath : incompatible weights_only

m = VitsModel(**sel)
m.load_state_dict(old["state_dict"], strict=True)
print("poids chargés (strict) :", len(old["state_dict"]))

torch.save({
    "state_dict": old["state_dict"],
    "hyper_parameters": sel,
    "pytorch-lightning_version": lightning.__version__,
    "epoch": 0, "global_step": 0,
    "optimizer_states": [], "lr_schedulers": [],
}, "base_fr_v2.ckpt")
torch.load("base_fr_v2.ckpt", map_location="cpu", weights_only=True)
print("base_fr_v2.ckpt prêt")
PY

echo "Terminé. Lance ensuite : bash scripts/train/03-train.sh"

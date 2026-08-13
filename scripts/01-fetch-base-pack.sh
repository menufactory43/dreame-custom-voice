#!/usr/bin/env bash
# Récupère un pack de base complet (514 sons) servant de squelette.
# Les .ogg ne sont PAS redistribués ici : on les prend à la source.
set -euo pipefail
cd "$(dirname "$0")/.."

SRC="https://github.com/sproft/dreame-x40-glados-voice-pack.git"
if [ -d base_pack/.git ]; then
  git -C base_pack pull --quiet
else
  git clone --depth 1 --quiet "$SRC" base_pack
fi

N=$(ls base_pack/voice_pack/*.ogg | wc -l | tr -d ' ')
echo "Pack de base : $N fichiers .ogg"
echo "Transcriptions : base_pack/docs/transcriptions.csv"
[ "$N" -ge 500 ] || { echo "ATTENTION: pack incomplet ($N fichiers)"; exit 1; }

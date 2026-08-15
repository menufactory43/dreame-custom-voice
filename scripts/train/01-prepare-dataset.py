#!/usr/bin/env python3
"""Prépare le dataset d'entraînement piper depuis le pack de base + traductions FR.

Utilise les 514 sons GLaDOS du pack de base (audio GLaDOS anglais, licence MIT) avec
leurs traductions françaises (data/transcriptions_fr.tsv). Les slots non parlés
(marqués COPY) sont écartés : on ne veut pas entraîner la voix sur du silence/bruit.

Sortie :
  build/train/audio/<id>.wav     (22050 Hz mono)
  build/train/metadata.csv       (fichier.wav|texte)
"""
import csv, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BASE = ROOT / "base_pack" / "voice_pack"
TSV = ROOT / "data" / "transcriptions_fr.tsv"
OUT_AUDIO = ROOT / "build" / "train" / "audio"
META = ROOT / "build" / "train" / "metadata.csv"


def read_fr_tsv(path):
    rows = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        i = line.index("\t")
        rows[line[:i]] = line[i + 1:]
    return rows


def main():
    if not BASE.is_dir():
        sys.exit("Lance d'abord scripts/01-fetch-base-pack.sh")
    if not TSV.exists():
        sys.exit(f"Traductions manquantes : {TSV}")

    fr = read_fr_tsv(TSV)
    OUT_AUDIO.mkdir(parents=True, exist_ok=True)

    meta = []
    skipped = 0
    for ogg in sorted(BASE.glob("*.ogg")):
        sid = ogg.stem
        text = fr.get(sid)
        if text is None or text == "COPY" or not text.strip():
            skipped += 1
            continue
        wav = OUT_AUDIO / f"{sid}.wav"
        if not wav.exists() or wav.stat().st_size < 1000:
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-i", str(ogg),
                 "-ac", "1", "-ar", "22050", str(wav)],
                check=True,
            )
        meta.append(f"{wav.name}|{text}")

    META.write_text("\n".join(meta) + "\n")
    print(f"{len(meta)} échantillons d'entraînement écrits dans {OUT_AUDIO.parent}")
    print(f"   ({skipped} slots non parlés écartés)")
    print(f"Durée totale : ~{len(meta) * 3 / 60:.1f} min (estimée)")
    print("Lance ensuite : bash scripts/train/02-install-piper.sh")


if __name__ == "__main__":
    main()

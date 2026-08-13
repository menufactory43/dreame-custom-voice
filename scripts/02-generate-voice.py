#!/usr/bin/env python3
"""Génère des .ogg (Vorbis mono 16 kHz) via l'API TTS d'OpenAI.

Deux modes :
  --id N --text "..."   remplace un son précis
  --all                 régénère les 514 sons en français depuis transcriptions.csv

Nécessite ffmpeg compilé avec libvorbis (`ffmpeg -encoders | grep libvorbis`).
"""
import argparse, csv, json, os, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "voice"
API = "https://api.openai.com/v1"


def env(key, default=None):
    v = os.environ.get(key, default)
    if v is None:
        sys.exit(f"Variable d'environnement manquante : {key}")
    return v


def post(path, payload, key, raw=False):
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read() if raw else json.loads(r.read())


def synth(text, dest, key):
    """TTS -> wav -> ogg vorbis mono 16 kHz (format exigé par le firmware Dreame)."""
    wav = post("/audio/speech", {
        "model": env("TTS_MODEL", "gpt-4o-mini-tts"),
        "voice": env("TTS_VOICE", "shimmer"),
        "input": text,
        "instructions": env("TTS_INSTRUCTIONS", ""),
        "response_format": "wav",
    }, key, raw=True)

    tmp = dest.with_suffix(".wav")
    tmp.write_bytes(wav)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp),
         "-ac", "1", "-ar", "16000", "-c:a", "libvorbis", "-q:a", "4", str(dest)],
        check=True,
    )
    tmp.unlink()


def translate(texts, key):
    """Traduit en une passe, en conservant l'ordre et le nombre de lignes."""
    numbered = "\n".join(f"{i}\t{t}" for i, t in enumerate(texts))
    r = post("/chat/completions", {
        "model": "gpt-4o-mini",
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content":
             "Tu traduis des annonces vocales d'aspirateur robot vers le français. "
             "Registre : vouvoiement, sobre et naturel, comme une annonce d'appareil. "
             "Réponds UNIQUEMENT avec les mêmes lignes 'index<TAB>traduction', "
             "même nombre de lignes, même ordre, aucun commentaire."},
            {"role": "user", "content": numbered},
        ],
    }, key)
    out = dict(texts and {})
    for line in r["choices"][0]["message"]["content"].splitlines():
        if "\t" in line:
            i, _, t = line.partition("\t")
            if i.strip().isdigit():
                out[int(i)] = t.strip()
    return [out.get(i, texts[i]) for i in range(len(texts))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", type=int, help="ID du son à générer")
    ap.add_argument("--text", help="Texte à prononcer")
    ap.add_argument("--all", action="store_true", help="Régénérer tous les sons parlés en français")
    ap.add_argument("--max-no-speech", type=float, default=0.3,
                    help="Au-dessus de ce no_speech_prob, le son n'est pas de la parole : on le laisse tel quel")
    a = ap.parse_args()

    key = env("OPENAI_API_KEY")
    OUT.mkdir(parents=True, exist_ok=True)

    if a.id is not None:
        if not a.text:
            sys.exit("--text est requis avec --id")
        synth(a.text, OUT / f"{a.id}.ogg", key)
        print(f"OK  {a.id}.ogg  <- {a.text!r}")
        return

    if not a.all:
        sys.exit("Choisis --id/--text ou --all")

    csv_path = ROOT / "base_pack" / "docs" / "transcriptions.csv"
    if not csv_path.exists():
        sys.exit("Lance d'abord scripts/01-fetch-base-pack.sh")

    rows = [r for r in csv.DictReader(csv_path.open())]
    speech = [r for r in rows if float(r["no_speech_prob"]) <= a.max_no_speech and r["transcription"].strip()]
    print(f"{len(speech)} sons parlés sur {len(rows)} (les autres gardent l'audio d'origine)")

    # Traduction par lots pour rester dans la fenêtre de contexte
    texts = [r["transcription"] for r in speech]
    fr = []
    B = 60
    for i in range(0, len(texts), B):
        fr += translate(texts[i:i + B], key)
        print(f"  traduit {min(i + B, len(texts))}/{len(texts)}")

    for r, text in zip(speech, fr):
        dest = OUT / f"{r['id']}.ogg"
        synth(text, dest, key)
        print(f"OK  {dest.name}  {text}")


if __name__ == "__main__":
    main()

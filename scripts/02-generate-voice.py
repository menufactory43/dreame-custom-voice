#!/usr/bin/env python3
"""Génère des .ogg (Vorbis mono 16 kHz) pour le pack de voix.

Deux modes :
  --id N --text "..."   remplace un son précis
  --all                 régénère les sons parlés en français

Deux backends de synthèse :
  --backend openai      (défaut) API TTS d'OpenAI ; --all traduit via gpt-4o-mini
  --backend piper       moteur local piper (voix entraînée) ; --all lit
                        data/transcriptions_fr.tsv (traductions déjà faites)

Pour le backend piper, renseigne dans .env :
  PIPER_MODEL=/chemin/fr_FR-glados_fr-medium.onnx
  PIPER_CONFIG=/chemin/fr_FR-glados_fr-medium.onnx.json

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


def synth_openai(text, dest, key):
    """OpenAI TTS -> wav -> ogg vorbis mono 16 kHz (format exigé par le firmware)."""
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


def synth_piper(text, dest):
    """Piper local -> wav -> ogg vorbis mono 16 kHz."""
    tmp = dest.with_suffix(".wav")
    subprocess.run(
        [env("PIPER_BIN", "piper"), "--model", env("PIPER_MODEL"),
         "--config", env("PIPER_CONFIG"), "--output_file", str(tmp)],
        input=text.encode(), check=True,
    )
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


def read_fr_tsv(path):
    """Lit data/transcriptions_fr.tsv : id<TAB>texte, 'COPY' = garder l'audio d'origine."""
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        i = line.index("\t")
        rows.append((line[:i], line[i + 1:]))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", type=int, help="ID du son à générer")
    ap.add_argument("--text", help="Texte à prononcer")
    ap.add_argument("--all", action="store_true", help="Régénérer tous les sons parlés en français")
    ap.add_argument("--backend", choices=("openai", "piper"), default="openai",
                    help="Moteur de synthèse (défaut: openai)")
    ap.add_argument("--max-no-speech", type=float, default=0.3,
                    help="Au-dessus de ce no_speech_prob, le son n'est pas de la parole : on le laisse tel quel")
    a = ap.parse_args()

    key = env("OPENAI_API_KEY") if a.backend == "openai" else None
    OUT.mkdir(parents=True, exist_ok=True)

    if a.id is not None:
        if not a.text:
            sys.exit("--text est requis avec --id")
        if a.backend == "openai":
            synth_openai(a.text, OUT / f"{a.id}.ogg", key)
        else:
            synth_piper(a.text, OUT / f"{a.id}.ogg")
        print(f"OK  {a.id}.ogg  <- {a.text!r}")
        return

    if not a.all:
        sys.exit("Choisis --id/--text ou --all")

    csv_path = ROOT / "base_pack" / "docs" / "transcriptions.csv"
    if not csv_path.exists():
        sys.exit("Lance d'abord scripts/01-fetch-base-pack.sh")

    rows = [r for r in csv.DictReader(csv_path.open())]

    if a.backend == "piper":
        fr_path = ROOT / "data" / "transcriptions_fr.tsv"
        if not fr_path.exists():
            sys.exit(f"Traductions manquantes : {fr_path}")
        fr = dict(read_fr_tsv(fr_path))
        speech = [r for r in rows
                  if r["id"] in fr and fr[r["id"]] != "COPY" and fr[r["id"]].strip()]
        print(f"{len(speech)} sons parlés sur {len(rows)} (les autres gardent l'audio d'origine)")
        for r in speech:
            dest = OUT / f"{r['id']}.ogg"
            text = fr[r["id"]]
            synth_piper(text, dest)
            print(f"OK  {dest.name}  {text}")
        return

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
        synth_openai(text, dest, key)
        print(f"OK  {dest.name}  {text}")


if __name__ == "__main__":
    main()

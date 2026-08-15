# Entraîner sa propre voix (pipeline piper1-gpl)

Le pack de base contient **514 sons GLaDOS en anglais**. Pour qu'un robot Dreame
parle **français avec une voix GLaDOS**, on fine-tune un modèle TTS [piper][piper]
depuis le checkpoint français [siwis/medium][siwis], sur le dataset
« audio GLaDOS + traduction française ».

Ce pipeline a produit la voix pré-entraînée publiée en
[Release](https://github.com/menufactory43/dreame-custom-voice/releases)
(`fr_FR-glados_fr-medium.onnx` + pack prêt à installer). Si tu ne veux pas
entraîner toi-même, saute à [Utiliser la voix publiée](#utiliser-la-voix-publiée).

## Principe

1. **Dataset** — les 514 `.ogg` du pack de base (licence MIT, audio GLaDOS)
   appariés à nos traductions françaises (`data/transcriptions_fr.tsv`).
   Les slots non parlés (bruits/silence, marqués `COPY`) sont écartés.
2. **Fine-tune** — piper1-gpl depuis `siwis/medium` (voix française neutre),
   ~25 min d'audio. C'est ce qui imprime le timbre GLaDOS sur la prononciation
   française.
3. **Export ONNX** — un seul `.onnx` dynamique, compatible avec `piper` et
   avec le backend `--backend piper` de `02-generate-voice.py`.

## Matériel

Un GPU CUDA d'au moins 8 Go de VRAM. Sur une A40 (~46 Go) : **~35 s/époque**
avec batch 16. Pour ~25 min d'audio :
- **500 époques ≈ 5 h** — voix correcte, caractère GLaDOS marqué
- **1000 époques ≈ 10 h** — qualité de référence (celle du pack publié)

Options rentables : [RunPod](https://www.runpod.io) (~0,35 $/h en pool communautaire),
Vast.ai, ou un PC local.

## Étapes

```bash
# 0. Récupère le pack de base (514 sons GLaDOS anglais, MIT)
bash scripts/01-fetch-base-pack.sh

# 1. Construit build/train/ (audio 22050 Hz + metadata.csv fr)
python3 scripts/train/01-prepare-dataset.py

# 2. Installe piper1-gpl + télécharge le checkpoint siwis/medium
#    (sur la machine GPU ; te laisse quelques minutes pour compiler espeakbridge)
bash scripts/train/02-install-piper.sh

# 3. Entraîne. Interruptible : relance avec --ckpt_path sur le dernier last.ckpt.
MAX_EPOCHS=1000 bash scripts/train/03-train.sh

# 4. Exporte le meilleur checkpoint (val_mos) en ONNX
bash scripts/train/04-export.sh
```

À l'issue, tu as `dist/fr_FR-glados_fr-medium.onnx` + `.onnx.json`.

## Générer le pack avec ta voix

```bash
export PIPER_MODEL="$PWD/dist/fr_FR-glados_fr-medium.onnx"
export PIPER_CONFIG="$PWD/dist/fr_FR-glados_fr-medium.onnx.json"
pip install piper-tts            # moteur d'inférence (léger, pas torch)

python3 scripts/02-generate-voice.py --all --backend piper   # les 504 sons parlés
bash scripts/03-build-pack.sh     # assemble base + personnalisés, md5, taille
bash scripts/04-serve.sh          # sert dist/ sur le LAN
bash scripts/05-install.sh        # le robot télécharge et installe
```

## Utiliser la voix publiée (sans entraîner)

Si le modèle pré-entraîné est publié en Release, télécharge-le :

```bash
bash scripts/00-fetch-glados-fr.sh    # récupère ONNX + config depuis la Release
```

puis lance les 4 commandes de la section précédente avec les variables `PIPER_*`
pointant sur `dist/fr_FR-glados_fr-medium.onnx`.

## Pièges rencontrés (tous contournés dans les scripts)

| Symptôme | Cause | Correctif |
|---|---|---|
| `ModuleNotFoundError: skbuild` | espeakbridge est compilé par CMake via scikit-build, absent de l'extra `train` | `pip install "scikit-build<1"` puis `setup.py build_ext --inplace` |
| `Failed to set voice: fr-fr` | l'espeak-ng embarqué nomme la voix `fr` | utiliser `--data.espeak_voice fr` |
| `Weights only load failed (PosixPath)` | checkpoint Lightning 1.9 + torch 2.6+ (`weights_only=True`) | conversion en ckpt 2.x propre (dans `02-install-piper.sh`) |
| `Trying to restore optimizer state...` | ckpt de départ sans `optimizer_states` | y mettre des listes vides (fine-tune = optimizer neuf) |
| Assertion `discriminant` non-traçable | assert data-dependent bloquant `torch.export` | le garder à l'inférence, le désactiver sous `torch.compiler.is_compiling()` |
| Voix muette au-delà d'une courte phrase | exporteur dynamo de torch 2.13 fige l'axe des phonèmes | export legacy `dynamo=False` + `dynamic_axes` (`export_onnx_fixed.py`) |

## Références

- [piper1-gpl / docs/TRAINING.md][piper-train]
- [rhasspy/piper-checkpoints][siwis] — checkpoints de départ par langue
- [sproft/dreame-x40-glados-voice-pack][x40] — pack de base (MIT)

[piper]: https://github.com/OHF-voice/piper1-gpl
[piper-train]: https://github.com/OHF-voice/piper1-gpl/blob/main/docs/TRAINING.md
[siwis]: https://huggingface.co/datasets/rhasspy/piper-checkpoints
[x40]: https://github.com/sproft/dreame-x40-glados-voice-pack

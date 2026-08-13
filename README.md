# Voix personnalisée pour aspirateur Dreame (sans root)

Faire dire ce qu'on veut à un robot Dreame récent — **sans Valetudo, sans rooter la machine**,
en passant par Home Assistant et le cloud officiel.

Testé et validé sur un **Dreame L40 Ultra** (`dreame.vacuum.r2492j`), firmware d'usine,
appairé dans l'app **Dreamehome**.

> Le robot télécharge lui-même l'archive depuis une machine de ton réseau local,
> l'installe, et joue tes fichiers. Réversible en une manipulation.

## Ce qu'il faut

- Un robot Dreame géré par **Home Assistant** via l'intégration
  [`Tasshack/dreame-vacuum`](https://github.com/Tasshack/dreame-vacuum) — **branche `dev` (v2.x)**, voir pièges ci-dessous
- Un compte Dreamehome avec **email + mot de passe** (voir pièges : la connexion Apple ne marche pas)
- Une machine sur le **même réseau que le robot** pour servir un fichier en HTTP (un NAS, un Raspberry Pi, la machine HA…)
- `ffmpeg` avec **libvorbis**, `python3`, `docker` (pour le serveur HTTP), et une clé API OpenAI pour la synthèse

## Démarrage

```bash
git clone <ce-repo> && cd dreame-custom-voice
cp config.example.env .env && $EDITOR .env    # renseigne tes valeurs

./scripts/01-fetch-base-pack.sh               # récupère un pack de base complet (514 sons)

# Ta phrase sur l'ID 12 = "nettoyage terminé"
python3 scripts/02-generate-voice.py --id 12 --text "La tâche est terminée, Maître. Une chartreuse, maintenant ?"

./scripts/03-build-pack.sh                    # assemble l'archive + md5 + taille
./scripts/04-serve.sh                         # sert dist/ sur le LAN
./scripts/05-install.sh                       # le robot télécharge et installe
```

Pour tout passer en français d'un coup :

```bash
python3 scripts/02-generate-voice.py --all
./scripts/03-build-pack.sh && ./scripts/05-install.sh
```

## Entendre le résultat sans lancer de ménage

Le firmware n'expose aucune commande « joue le son N ». Mais `locate` joue les IDs **45/246**.
Il suffit d'y placer temporairement ton audio :

```bash
python3 scripts/02-generate-voice.py --id 45  --text "..."
python3 scripts/02-generate-voice.py --id 246 --text "..."
./scripts/03-build-pack.sh && ./scripts/05-install.sh
./scripts/06-test-speak.sh
```

## Revenir en arrière

App **Dreamehome → ton robot → Paramètres → Voix / Langue → choisis une langue**.
Le robot retélécharge le pack officiel depuis le cloud Dreame. Rien n'est définitif.

## Documentation

- [`docs/FINDINGS.md`](docs/FINDINGS.md) — le protocole, les formats, et tous les pièges rencontrés
- [`docs/SOUND_IDS.md`](docs/SOUND_IDS.md) — les identifiants de sons utiles

## Crédits

- [`Tasshack/dreame-vacuum`](https://github.com/Tasshack/dreame-vacuum) — l'intégration Home Assistant qui rend tout ceci possible
- [`sproft/dreame-x40-glados-voice-pack`](https://github.com/sproft/dreame-x40-glados-voice-pack) — pack de base 514 sons et table des transcriptions (MIT)
- [`Ilshidur/vacuum-voice-gen`](https://github.com/Ilshidur/vacuum-voice-gen) — pack français d'une génération antérieure, utile pour recouper la numérotation

Les fichiers audio tiers ne sont pas redistribués ici : les scripts les récupèrent à la source.

## Licence

MIT — voir [LICENSE](LICENSE).

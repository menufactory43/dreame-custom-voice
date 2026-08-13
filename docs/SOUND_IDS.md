# Identifiants de sons

Numérotation valable pour les modèles Dreame récents (514 sons, 0→694).
**Recoupée sur deux packs indépendants** de générations différentes : les IDs 1 et 12 concordent,
ce qui donne une bonne confiance dans l'ensemble.

## Les plus utiles

| ID | Texte d'origine | Remarque |
|---|---|---|
| **12** | *Cleaning task completed.* | **la cible habituelle** — fin de nettoyage |
| 1 | *Waiting for the network configuration.* | sert de repère pour valider la numérotation |
| 45 | *I am here.* | joué par `locate` |
| 246 | *I'm here.* | joué par `locate` (variante courte) |
| 13 | retour à la base pour recharger | |
| 14 | batterie faible, retour à la base | |

## Table complète

`base_pack/docs/transcriptions.csv` après `scripts/01-fetch-base-pack.sh` :

```csv
id,filename,transcription,no_speech_prob,duration
12,12.ogg,Cleaning task completed.,0.176,2.0
```

La colonne `no_speech_prob` distingue les vraies annonces des jingles et bips.
Au-delà de ~0.3, ce n'est pas de la parole : **conserve le fichier d'origine**
plutôt que d'y synthétiser une voix.

## Vérifier la numérotation sur ton modèle

Sans lancer de ménage : place un audio reconnaissable sur les IDs 45 et 246, installe, déclenche `locate`.
Si tu l'entends, ta numérotation correspond.

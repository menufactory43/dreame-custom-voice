# Notes techniques et pièges

Tout ce qui suit a été mesuré sur un **Dreame L40 Ultra** (`dreame.vacuum.r2492j`) en firmware d'usine,
compte **Dreamehome**, cloud européen. Les points marqués ⚠️ sont ceux qui coûtent des heures.

## Format du pack

- `tar.gz` **strictement plat** — que des `N.ogg` à la racine, aucun dossier, aucun manifeste
- **OGG Vorbis, mono, 16 kHz** — vérifie avec `ffprobe -show_entries stream=codec_name,sample_rate,channels`
- Numérotation de 0 à 694 sur les modèles récents (514 fichiers ; la suite est trouée)
- Les générations plus anciennes sont plus petites (~97 sons sur un p2009, ~188 sur un pack de 2022)

## ⚠️ Un pack est exhaustif, jamais différentiel

Installer une archive ne contenant qu'un seul fichier **ne l'ajoute pas** au pack existant :
elle **remplace tout**. Le robot devient muet sur tous les autres événements.

Il télécharge, valide le md5, répond `success`… et ne dit plus rien. Rien dans les logs ne le signale.
**Il faut toujours livrer un pack complet.**

## ⚠️ Intégration : la v1 ne parle qu'au cloud Xiaomi

La branche `master` (v1.0.11) ne contient que des endpoints `account.xiaomi.com` / `sts.api.io.mi.com`.
Un robot appairé dans **Dreamehome** y est invisible, et sa liste blanche de modèles s'arrête vers `r2355`.

La branche **`dev` (v2.0.0b25+)** ajoute le type de compte *Dreamehome Account* (ainsi que Mova et Trouver)
et reconnaît 705 modèles. C'est celle qu'il faut.

Installation manuelle : copier `custom_components/dreame_vacuum/` dans la config HA, puis redémarrer.

## ⚠️ La connexion « Se connecter avec Apple » est une impasse

Le formulaire exige un couple email/mot de passe : un compte créé via Apple SSO n'en a pas.
Aucun contournement par jeton n'existe — l'`auth_key` du code est **produit par** un login réussi,
ce n'est pas une entrée alternative.

Solution : dans l'app, *Compte et sécurité* → définir un mot de passe, ou passer par
« mot de passe oublié » sur l'adresse rattachée (y compris un relais `@privaterelay.appleid.com`,
qui fait suivre). Ajouter un mot de passe **ne dépaire pas** le robot.

## ⚠️ « Prefer cloud connection » doit rester coché

Dans `protocol.py`, si `prefer_cloud` est faux, `device_cloud` reste à `None`.
Les modèles récents n'ayant **aucun protocole local** (miio abandonné, aucun port TCP ouvert),
l'intégration se retrouve alors sans le moindre canal vers le robot.

Pays à choisir pour un compte Dreamehome européen : **`eu`** (le `de` ne concerne que le chemin Xiaomi).

## Le pack officiel n'est pas récupérable

Toutes les pistes ont été fermées, dans l'ordre :

| Piste | Résultat |
|---|---|
| Deviner l'URL sur le bucket produit | `403` — signature obligatoire |
| Faire signer une URL par l'API Dreame (`getOss1dDownloadUrl`) | `404 NoSuchKey` — ne couvre que l'espace fichiers de l'appareil |
| Écouter le MQTT | le robot ne republie jamais la propriété `7.4` qui porte l'URL |
| Historique des propriétés (`getDeviceData`) | vide |
| Accès local au robot | inexistant sur ce modèle |

Conséquence : impossible de partir du pack officiel pour n'en changer qu'une phrase.
Il faut fournir un pack complet, généré ou emprunté.

## Propriétés MIoT utiles

| Propriété | siid.piid | Rôle |
|---|---|---|
| `VOICE_PACKET_ID` | 7.2 | identifiant du pack installé (`EN`, `FR`, ou le tien) |
| `VOICE_CHANGE_STATUS` | 7.3 | `{"id":...,"state":"downloading|success|fail","progress":N}` |
| `VOICE_CHANGE` | 7.4 | écriture de `{"id","url","md5","size"}` — déclenche le téléchargement |
| `VOICE_ASSISTANT_LANGUAGE` | 7.10 | langue de l'assistant vocal — **sans effet sur le pack de sons** |
| action `LOCATE` | 7.1 | joue les IDs 45/246 |
| action `PLAY_SOUND` | 7.2 | son de test du volume, aucun paramètre |

## Diagnostic

Activer les logs :

```yaml
# via l'outil de développement, service logger.set_level
custom_components.dreame_vacuum: debug
```

Puis suivre `Message Callback:` — le robot y publie sa progression de téléchargement en direct.

Vérifier que le robot est bien venu chercher le fichier :

```bash
docker logs dreame-voice-http | grep voice_pack
# <ip-du-robot> - - [...] "GET /voice_pack.tar.gz" 200 ... "Wget/1.20.3 (linux-gnu)"
```

Le `User-Agent` `Wget/1.20.3 (linux-gnu)` est la signature du robot.

## Le silence n'est pas toujours un échec

Avant de conclure qu'un pack est cassé, vérifie que l'événement testé **produit un son à l'origine**.
Un robot posé sur sa base peut très bien ne rien dire sur `locate`.
Sans mesure de référence prise avant toute modification, le silence n'apporte aucune information.

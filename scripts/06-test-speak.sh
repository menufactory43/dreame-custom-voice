#!/usr/bin/env bash
# Fait parler le robot SANS lancer de nettoyage.
# Astuce : le firmware n'expose pas "joue le son N", mais `locate` joue les IDs 45/246.
# En y plaçant ton audio, tu l'entends à la demande.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
: "${HA_URL:?}"; : "${HA_TOKEN:?}"; : "${VACUUM_ENTITY:?}"

api() { curl -sS -o /dev/null -w "%{http_code}\n" -X POST "${HA_URL}/api/services/$1" \
        -H "Authorization: Bearer ${HA_TOKEN}" -H "Content-Type: application/json" -d "$2"; }

echo -n "volume 100 : "; api number/set_value "{\"entity_id\":\"number.${VACUUM_ENTITY#vacuum.}_volume\",\"value\":100}"
sleep 5
echo -n "locate     : "; api vacuum/locate "{\"entity_id\":\"${VACUUM_ENTITY}\"}"
echo "Tu devrais entendre le son des IDs 45/246."

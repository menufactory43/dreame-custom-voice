#!/usr/bin/env bash
# Demande au robot de télécharger et d'installer le pack, puis suit la progression.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
[ -f dist/pack.env ] && set -a && . ./dist/pack.env && set +a

: "${HA_URL:?}"; : "${HA_TOKEN:?}"; : "${VACUUM_ENTITY:?}"; : "${HTTP_HOST:?}"
: "${PACK_MD5:?Lance scripts/03-build-pack.sh}"; : "${PACK_SIZE:?}"

URL="http://${HTTP_HOST}:${HTTP_PORT:-8099}/voice_pack.tar.gz"
echo "Installation de $URL (md5 $PACK_MD5, $PACK_SIZE octets)"

curl -sS -X POST "${HA_URL}/api/services/dreame_vacuum/vacuum_install_voice_pack" \
  -H "Authorization: Bearer ${HA_TOKEN}" -H "Content-Type: application/json" \
  -d "{\"entity_id\":\"${VACUUM_ENTITY}\",\"lang_id\":\"${LANG_ID:-T2}\",\"url\":\"${URL}\",\"md5\":\"${PACK_MD5}\",\"size\":${PACK_SIZE}}" \
  -w "\nHTTP %{http_code}\n"

echo "Suivi (voice_packet_id doit passer à ${LANG_ID:-T2}) :"
for i in $(seq 1 20); do
  sleep 10
  ID=$(curl -sS "${HA_URL}/api/states/${VACUUM_ENTITY}" -H "Authorization: Bearer ${HA_TOKEN}" \
       | python3 -c "import sys,json;print(json.load(sys.stdin)['attributes'].get('voice_packet_id'))" 2>/dev/null || echo "?")
  echo "  voice_packet_id = $ID"
  [ "$ID" = "${LANG_ID:-T2}" ] && { echo "Installé."; exit 0; }
done
echo "Pas confirmé — vérifie les logs HA et que le robot joint bien ${HTTP_HOST}."

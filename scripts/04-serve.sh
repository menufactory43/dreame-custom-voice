#!/usr/bin/env bash
# Sert dist/ en HTTP sur le LAN. Le ROBOT doit pouvoir joindre cette adresse.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a

PORT="${HTTP_PORT:-8099}"
docker rm -f dreame-voice-http >/dev/null 2>&1 || true
docker run -d --name dreame-voice-http -p "${PORT}:80" \
  -v "$(pwd)/dist:/usr/share/nginx/html:ro" nginx:alpine >/dev/null

sleep 2
echo "Servi sur http://${HTTP_HOST:-<ip>}:${PORT}/voice_pack.tar.gz"
curl -s -o /dev/null -w "Vérification locale : HTTP %{http_code}\n" "http://127.0.0.1:${PORT}/voice_pack.tar.gz"
echo "Arrêt : docker rm -f dreame-voice-http"

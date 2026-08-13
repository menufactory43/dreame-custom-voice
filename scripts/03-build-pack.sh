#!/usr/bin/env bash
# Assemble le pack final : base complète + sons personnalisés par-dessus.
# IMPÉRATIF : archive PLATE (aucun dossier), sinon le robot reste muet.
set -euo pipefail
cd "$(dirname "$0")/.."

[ -d base_pack/voice_pack ] || { echo "Lance d'abord scripts/01-fetch-base-pack.sh"; exit 1; }

rm -rf build/pack && mkdir -p build/pack dist
cp base_pack/voice_pack/*.ogg build/pack/

CUSTOM=0
if [ -d build/voice ]; then
  for f in build/voice/*.ogg; do
    [ -e "$f" ] || continue
    cp "$f" build/pack/
    CUSTOM=$((CUSTOM + 1))
  done
fi

# Contrôle de format : le firmware n'accepte que Vorbis mono 16 kHz
BAD=0
for f in build/pack/*.ogg; do
  S=$(ffprobe -v error -show_entries stream=codec_name,sample_rate,channels -of csv=p=0 "$f" 2>/dev/null || true)
  case "$S" in
    vorbis,16000,1) ;;
    *) echo "  format inattendu: $(basename "$f") -> $S"; BAD=$((BAD + 1));;
  esac
done
[ "$BAD" -eq 0 ] || { echo "$BAD fichier(s) hors format — abandon"; exit 1; }

( cd build/pack && tar czf ../../dist/voice_pack.tar.gz *.ogg )

MD5=$(md5sum dist/voice_pack.tar.gz 2>/dev/null | awk '{print $1}' || md5 -q dist/voice_pack.tar.gz)
SIZE=$(stat -c%s dist/voice_pack.tar.gz 2>/dev/null || stat -f%z dist/voice_pack.tar.gz)

cat > dist/pack.env <<EOF2
PACK_MD5=$MD5
PACK_SIZE=$SIZE
EOF2

echo "Fichiers   : $(ls build/pack/*.ogg | wc -l | tr -d ' ')  (dont $CUSTOM personnalisés)"
echo "Archive    : dist/voice_pack.tar.gz"
echo "MD5        : $MD5"
echo "Taille     : $SIZE"

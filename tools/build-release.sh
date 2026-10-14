#!/usr/bin/env bash
# Construit le paquet Arch d'ES-NE avec les clés développeur intégrées au binaire (pour une release publique).
#   tools/build-release.sh /chemin/vers/keys.conf
# keys.conf: même format que ~/.config/esne/keys.conf (SCREENSCRAPER_SOFTNAME, SCREENSCRAPER_DEV_LOGIN, GAMESDB_APIKEY,
# HFS_DEV_LOGIN, CHEEVOS_DEV_LOGIN). Le fichier n'est jamais copié dans le dépôt ni dans le paquet; seules les valeurs masquées
# se retrouvent dans le binaire /usr/bin/emulationstation. Sortie: dist/release/*.pkg.tar.zst + somme SHA-256.
set -euo pipefail

keys=${1:-}
if [ -z "$keys" ] || [ ! -f "$keys" ]; then
    echo "usage: $0 /chemin/vers/keys.conf" >&2
    exit 2
fi
keys=$(realpath "$keys")

root=$(cd "$(dirname "$0")/.." && pwd)
out="$root/dist/release"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

command -v makepkg >/dev/null || { echo "makepkg est introuvable (Arch Linux ou dérivé requis)" >&2; exit 1; }

echo ">> les clés suivantes seront intégrées au binaire (valeurs masquées):"
sed -E 's/^[[:space:]]*#.*//; /^[[:space:]]*$/d; s/=.*/=…/' "$keys"
echo ">> toute personne qui reçoit le paquet peut retrouver ces clés en analysant le binaire."
if [ -t 0 ]; then
    read -r -p "Continuer ? [o/N] " answer
    [ "$answer" = "o" ] || [ "$answer" = "O" ] || exit 1
fi

cp -r "$root/packaging/arch/." "$work/"
mkdir -p "$out"
(cd "$work" && ESNE_KEYS_FILE="$keys" PKGDEST="$out" BUILDDIR="$work/build" SRCDEST="$work/src" makepkg -sf --noconfirm)

(cd "$out" && for f in *.pkg.tar.zst; do sha256sum "$f" | tee "$f.sha256"; done)
echo ">> paquet(s) dans $out: à joindre à la release GitHub (ne pas committer dist/)."

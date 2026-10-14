#!/usr/bin/env bash
# Construit le paquet Arch de release: tools/build-release.sh /chemin/vers/keys.conf (sortie: dist/release/).
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

echo ">> clés utilisées pour ce build (valeurs masquées):"
sed -E 's/^[[:space:]]*#.*//; /^[[:space:]]*$/d; s/=.*/=…/' "$keys"
if [ -t 0 ]; then
    read -r -p "Continuer ? [o/N] " answer
    [ "$answer" = "o" ] || [ "$answer" = "O" ] || exit 1
fi

cp -r "$root/packaging/arch/." "$work/"
mkdir -p "$out"
(cd "$work" && ESNE_KEYS_FILE="$keys" PKGDEST="$out" BUILDDIR="$work/build" SRCDEST="$work/src" makepkg -sf --noconfirm)

(cd "$out" && for f in *.pkg.tar.zst; do sha256sum "$f" | tee "$f.sha256"; done)
echo ">> paquet(s) dans $out: à joindre à la release GitHub (ne pas committer dist/)."

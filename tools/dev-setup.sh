#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Prépare un environnement de test minimal pour ES-NE (développement, pas une installation):
#  - ~/.config/esne/es_systems.cfg avec un seul système "snes" lancé par es-launcher (prérequis: retroarch et le core snes9x, et es-launcher dans le PATH)
#  - une ROM factice dans ~/esne/roms/snes
#  - le thème ES-NE du dépôt (themes/es-ne), lié dans ~/esne/themes
# Usage: sh tools/dev-setup.sh [--force]    (--force: réécrit es_systems.cfg)
set -eu

CONFIG="${ESNE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/esne}"
DATA="${ESNE_DATA_DIR:-$HOME/esne}"
CFG="$CONFIG/es_systems.cfg"

mkdir -p "$CONFIG" "$DATA/roms/snes" "$DATA/themes"
[ -e "$DATA/roms/snes/test.sfc" ] || : > "$DATA/roms/snes/test.sfc"

if command -v es-genconfig >/dev/null 2>&1 && { [ "${1:-}" = "--force" ] || ! grep -q "<systemList" "$CFG" 2>/dev/null; }; then
    es-genconfig            # tous les systèmes du catalogue (+ dossiers de roms)
elif [ "${1:-}" = "--force" ] || ! grep -q "<systemList" "$CFG" 2>/dev/null; then
    cat > "$CFG" <<XML
<?xml version="1.0"?>
<systemList>
  <system>
    <name>snes</name>
    <fullname>Super Nintendo</fullname>
    <manufacturer>Nintendo</manufacturer>
    <release>1990</release>
    <hardware>console</hardware>
    <path>$DATA/roms/snes</path>
    <extension>.sfc .smc .zip</extension>
    <command>es-launcher %CONTROLLERSCONFIG% -system %SYSTEM% -rom %ROM% -gameinfoxml %GAMEINFOXML% -systemname %SYSTEMNAME%</command>
    <platform>snes</platform>
    <theme>snes</theme>
  </system>
</systemList>
XML
    echo "écrit: $CFG"
else
    echo "conservé: $CFG (--force pour le réécrire)"
fi

REPO="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$DATA/themes"
if [ ! -e "$DATA/themes/es-ne" ]; then
    ln -s "$REPO/themes/es-ne" "$DATA/themes/es-ne"
    echo "thème lié: $DATA/themes/es-ne -> $REPO/themes/es-ne"
else
    echo "thème déjà présent: $DATA/themes/es-ne"
fi
echo "ok"

#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Prépare un environnement de test minimal pour ES-NE (développement, pas une installation):
#  - ~/.config/esne/es_systems.cfg avec un seul système "snes" (la commande se contente d'afficher ses arguments)
#  - une ROM factice dans ~/.local/share/esne/roms/snes
#  - le thème "carbon" (RetroPie/es-theme-carbon) dans ~/.local/share/esne/themes
# Usage: sh tools/dev-setup.sh [--force]    (--force: réécrit es_systems.cfg)
set -eu

CONFIG="${ESNE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/esne}"
DATA="${ESNE_DATA_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/esne}"
CFG="$CONFIG/es_systems.cfg"

mkdir -p "$CONFIG" "$DATA/roms/snes" "$DATA/themes"
[ -e "$DATA/roms/snes/test.sfc" ] || : > "$DATA/roms/snes/test.sfc"

if [ "${1:-}" = "--force" ] || ! grep -q "<systemList" "$CFG" 2>/dev/null; then
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
    <command>echo %ROM% %SYSTEM% %EMULATOR%</command>
    <platform>snes</platform>
    <theme>snes</theme>
  </system>
</systemList>
XML
    echo "écrit: $CFG"
else
    echo "conservé: $CFG (--force pour le réécrire)"
fi

if [ ! -d "$DATA/themes/es-theme-carbon" ]; then
    git clone --depth 1 https://github.com/RetroPie/es-theme-carbon.git "$DATA/themes/es-theme-carbon"
else
    echo "thème déjà présent: $DATA/themes/es-theme-carbon"
fi
echo "ok"

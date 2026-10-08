#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Inventaire des dépendances Batocera dans le code source d'ES.
# Usage: tools/audit_hardcoded.sh [dossier_ES] [fichier_sortie]
set -euo pipefail
SRC="${1:-third_party/emulationstation}"
OUT="${2:-docs/audit/HARDCODED.md}"
[ -d "$SRC" ] || { echo "Dossier introuvable: $SRC" >&2; exit 1; }
mkdir -p "$(dirname "$OUT")"

SCAN=(es-app es-core resources CMake CMakeLists.txt emulationstation.sh)
EXCL=(--exclude-dir=external --exclude-dir=locale --exclude-dir=.git --exclude=*.po --exclude=*.png --exclude=*.svg --exclude=*.ttf)

section() {  # titre, regex
  local title="$1" re="$2" n
  {
    echo; echo "## $title"; echo; echo "Regex: \`$re\`"; echo
  } >> "$OUT"
  n=$(cd "$SRC" && grep -rnIE "${EXCL[@]}" -- "$re" "${SCAN[@]}" 2>/dev/null | wc -l || true)
  echo "**$n occurrence(s)**" >> "$OUT"; echo >> "$OUT"
  echo '```' >> "$OUT"
  (cd "$SRC" && grep -rnIE "${EXCL[@]}" -- "$re" "${SCAN[@]}" 2>/dev/null | sed -E 's/[[:space:]]+/ /g' | cut -c1-220) >> "$OUT" || true
  echo '```' >> "$OUT"
}

{
  echo "# Audit des dépendances Batocera"
  echo
  echo "- Source: \`$SRC\`"
  echo "- Commit: \`$(git -C "$SRC" rev-parse --short HEAD 2>/dev/null || echo inconnu)\`"
  echo "- Généré: $(date -u +%F)"
} > "$OUT"

section "1. Chemins /userdata"                         '/userdata'
section "2. Chemins /usr/share/batocera, /recalbox"    '/usr/share/batocera|/recalbox|/boot/'
section "3. Chemins /etc/emulationstation, /usr/share/emulationstation" '/etc/emulationstation|/usr/share/emulationstation'
section "4. Dossier ~/.emulationstation"               '\.emulationstation'
section "5. Appels batocera-*"                         'batocera-[a-z0-9_-]+'
section "6. Fichiers de config batocera.conf / settings" 'batocera\.conf|batocera-settings|system\.conf'
section "7. Fichiers drapeaux /tmp (restart, shutdown...)" '/tmp/'
section "8. Exécutables en dur (/usr/bin, /bin, /sbin)" '"/(usr/)?(s?bin)/[a-zA-Z0-9_.-]+'
section "9. sudo / reboot / poweroff / shutdown"       '\bsudo\b|reboot|poweroff|shutdown'
section "10. Exécution de commandes (system, popen, exec)" '\b(system|popen|execl?p?|executeScript|executeEnumerationScript)\s*\('
section "11. Services réseau (wifi, bluetooth, ssh, samba)" 'wifi|bluetooth|\bssh\b|samba|nmcli|connman'
section "12. Mises à jour / OS (upgrade, overlay, mount)" 'upgrade|overlay|mount|umount|fstab|filesystem'
section "13. Webserver / API HTTP interne"              'HttpServer|webserver|localhost|127\.0\.0\.1'

echo "Rapport écrit dans $OUT"

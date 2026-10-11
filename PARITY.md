# Matrice de parité avec RetroBat
Légende: ❌ non fait · 🚧 en cours · ✅ fait · ⛔ masqué volontairement

## 1. Systèmes et émulateurs (lanceur `es-launcher`)
| Système | Émulateur | Lancement | Shaders | Ratio | Rewind | Bezels | Manettes |
|---|---|---|---|---|---|---|---|
| snes | libretro/snes9x | 🚧 | ❌ | ❌ | ❌ | ❌ | ❌ |

## 2. Menus du frontend ES
Un ✅ = branché dans `LinuxApiSystem` et vérifié à la compilation; **aucun menu n'a été testé dans ES lancé**.
Les menus liés à `esctl` apparaissent seulement si `esctl has <commande>` réussit (voir `docs/ESCTL_CONTRACT.md`).

| Fonction ES | Batocera (script) | ES-NE | État |
|---|---|---|---|
| Résolution | `batocera-resolution` | `esctl resolution` (xrandr, wlr-randr, kscreen-doctor) | ✅ code + tests; format kscreen-doctor -j capturé sur KDE réel; ❌ GNOME Wayland; setMode non essayé sur machine |
| Sortie audio | `batocera-audio` | `esctl audio` (pactl) | ✅ code + tests; non essayé sur machine |
| Fuseau horaire | `batocera-timezone` | `esctl timezone` | 🚧 côté ES prêt, `esctl` ❌ |
| BIOS / systèmes | `batocera-systems` | `esctl systems` | 🚧 côté ES prêt, `esctl` ❌ |
| Infos manettes | `batocera-padsinfo` | `esctl padsinfo` | 🚧 côté ES prêt, `esctl` ❌ |
| The Bezel Project | `batocera-es-thebezelproject` | `esctl thebezelproject` | 🚧 côté ES prêt, `esctl` ❌ |
| Version affichée | `batocera-version` | `esctl version` (`share/esne.version`, sinon version du package) | ✅ |
| Décorations / shaders | (dossiers) | menu visible si les dossiers existent | ✅ code; ❌ données à fournir |
| Netplay | `7zr` | `7zz`, `7z`, `7za` ou `7zr` dans le `PATH` | ✅ |
| Kodi | `batocera-kodi` | `kodi --standalone` direct | ✅ code, non testé |
| Veille | `pm-suspend` | `systemctl suspend` | ✅ code, non testé |
| Manuel PDF | `pdftoppm`, `pdfinfo` | cherchés dans le `PATH` | ✅ |
| Thèmes (téléchargement) | — | inchangé | ✅ code d'ES |
| Raccourcis, clavier → manette | `batocera-hotkeys`, `batocera-keyboard`, `evmapy` | — | ❌ |
| Arrêt / redémarrage | `batocera-shutdown`, drapeaux `/tmp` | — | ❌ patch 7 |
| Wi-Fi, Bluetooth | `batocera-wifi`, `batocera-bluetooth` | NetworkManager, BlueZ | ⛔ |
| Mises à jour, installation, formatage, overclock, sauvegarde | `batocera-upgrade`, `-install`, `-format`, `-overclock`, `-sync` | gestionnaire de paquets | ⛔ |
| Store, services, mode avion, backglass, NFC | `batocera-store`, `-services`, `-planemode`, `-backglass`, `-nfc` | — | ⛔ |

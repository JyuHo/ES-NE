# Chemins en dur et dépendances Batocera dans ES

Statut: **confirmé** = lu dans le dépôt upstream (README, `emulationstation.sh`);
**à vérifier** = connaissance générale, à confirmer avec `tools/audit_hardcoded.sh`.

## Confirmé (README et `emulationstation.sh` upstream, branche master)
| Élément | Détail | Remplacement ES-NE |
|---|---|---|
| `/etc/emulationstation/` | `es_systems.cfg`, `es_input.cfg`, thèmes (`themes/`) | `/usr/share/esne/` (lecture seule) + `~/.config/esne/` |
| `/usr/share/emulationstation/` | ressources copiées vers `/etc/` | `/usr/share/esne/resources/` |
| `/userdata` | doit exister avec les données de `datainit` (`/usr/share/batocera/datainit/*`) | `~/.local/share/esne/` |
| `~/.emulationstation/` | présent dans le README (variante historique); option `--home` annoncée pour Windows | `~/.config/esne/` (option `--home` à étendre à Linux) |
| `/tmp/es-restart`, `/tmp/es-sysrestart`, `/tmp/es-shutdown` | fichiers drapeaux lus par `emulationstation.sh` | `$XDG_RUNTIME_DIR/esne/` |
| `sudo reboot` / `sudo poweroff` | dans `emulationstation.sh` | `systemctl reboot/poweroff` ou polkit |
| Tags de `es_systems.cfg` | `%ROM%`, `%BASENAME%`, `%ROM_RAW%`, `%HOME%`, `%SYSTEM%`, `%EMULATOR%`, `%CORE%` | conservés tels quels |
| Fonctions « hors Batocera » | README upstream: lancement d'émulateurs, musique de fond, webserver ne fonctionnent pas hors Batocera | à réimplémenter via `es-launcher` / `esctl` |
| Thème par défaut | ES-Carbon, dans `/etc/emulationstation/themes` | paquet de thème séparé |
| Options CLI | `--resolution`, `--windowed`, `--fullscreen-borderless`, `--gamelist-only`, `--no-splash`, `--vsync`, `--max-vram`, `--force-kiosk`... | inchangées |
| Dépendances de build | CMake, SDL2, SDL2_mixer, FreeImage, FreeType, cURL, RapidJSON, LibVLC, Boost, gettext; `-DGLES2/-DGLES3` pour Raspberry Pi | paquets Arch équivalents |

## À vérifier avec le script d'audit
Je n'ai pas pu lire les sources C++ (GitHub bloque l'accès automatisé aux arborescences),
donc les points suivants sont des hypothèses:
- Un fichier central de chemins (probablement `es-core/src/Paths.cpp`) définit la plupart des constantes.
- Les appels système passent par des helpers (probablement `es-app/src/ApiSystem.cpp`) qui lancent des scripts `batocera-*`.
- Lecture et écriture de `batocera.conf` pour les options des menus.
- Menus OS: Wi-Fi, Bluetooth, mises à jour, overlay, stockage, services.
- Le serveur web interne.

## Méthode
```bash
tools/audit_hardcoded.sh third_party/emulationstation docs/audit/HARDCODED.md
```
Le rapport classe les occurrences en 13 catégories. Le traiter dans l'ordre:
1. chemins (catégories 1 à 4), à centraliser dans un seul fichier configurable au build;
2. appels `batocera-*` (5, 6, 10), à router vers `esctl`;
3. drapeaux `/tmp` et `sudo` (7, 9);
4. menus OS à masquer ou à désactiver (11, 12, 13).

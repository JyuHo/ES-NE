# Chemins en dur et dépendances Batocera dans ES

Statut: **confirmé** = lu dans le dépôt upstream (README, `emulationstation.sh`, code source);
**non vérifié** = pas encore examiné.

Ce document est la vue d'ensemble de départ. Le détail ligne par ligne, l'état des patchs et les corrections
sont dans `docs/AUDIT_ANALYSIS.md`; le rapport brut dans `docs/audit/HARDCODED.md`.

## Confirmé (README et `emulationstation.sh` upstream, branche master)
| Élément | Détail | Remplacement ES-NE |
|---|---|---|
| `/etc/emulationstation/` | `es_systems.cfg`, `es_input.cfg`, thèmes (`themes/`) | `/usr/share/esne/` (lecture seule) + `~/.config/esne/` |
| `/usr/share/emulationstation/` | ressources copiées vers `/etc/` | `/usr/share/esne/resources/` |
| `/userdata` | doit exister avec les données de `datainit` (`/usr/share/batocera/datainit/*`) | `~/esne/` |
| `~/.emulationstation/` | présent dans le README (variante historique); option `--home` annoncée pour Windows | `~/.config/esne/` (option `--home` à étendre à Linux) |
| `/tmp/es-restart`, `/tmp/es-sysrestart`, `/tmp/es-shutdown` | fichiers drapeaux lus par `emulationstation.sh`. **Doublon** avec `/tmp/restart.please`, `reboot.please`, `shutdown.please` créés par `Platform.cpp:262-273` | `$XDG_RUNTIME_DIR/esne/`, un seul mécanisme (patch 7, fait: `systemctl` et `execv`) |
| `sudo reboot` / `sudo poweroff` | dans `emulationstation.sh` | `systemctl reboot/poweroff` ou polkit |
| Tags de `es_systems.cfg` | `%ROM%`, `%BASENAME%`, `%ROM_RAW%`, `%HOME%`, `%SYSTEM%`, `%EMULATOR%`, `%CORE%` | conservés tels quels |
| Fonctions « hors Batocera » | README upstream: lancement d'émulateurs, musique de fond, webserver ne fonctionnent pas hors Batocera | à réimplémenter via `es-launcher` / `esctl` |
| Thème par défaut | ES-NE (`themes/es-ne`, livré dans `/usr/share/esne/themes`) | paquet de thème séparé |
| Options CLI | `--resolution`, `--windowed`, `--fullscreen-borderless`, `--gamelist-only`, `--no-splash`, `--vsync`, `--max-vram`, `--force-kiosk`... | inchangées |
| Dépendances de build | CMake, SDL2, SDL2_mixer, FreeImage, FreeType, cURL, RapidJSON, LibVLC, Boost, gettext | paquets Arch équivalents |

## Hypothèses de départ, vérifiées par l'audit
| Hypothèse | Résultat |
|---|---|
| Un fichier central définit les chemins | ✅ `es-core/src/Paths.cpp`: les 12 occurrences de `/userdata` et presque tous les chemins `/usr/share/...` |
| Les appels système passent par des helpers | ✅ `es-app/src/ApiSystem.cpp` (168 des 191 occurrences `batocera-*`) et `Win32ApiSystem.cpp` pour Windows. Certaines fonctions contournent les helpers (`popen`/`system` directs) |
| `batocera.conf` est lu et écrit pour les options | ✅ chemin défini par `Paths::getSystemConfFilePath()`, clés lues et écrites via `SystemConf` |
| Les menus OS (Wi-Fi, Bluetooth, mises à jour, stockage, services) existent | ✅ ils sont conditionnés par `ApiSystem::isScriptingSupported()` (test de `/usr/bin/<script>`) |
| Le serveur web interne est à traiter | ❌ non vérifié (`HttpServerThread`, `ZaparooSupport`) |

## Méthode
L'audit a été exécuté sur le fork (base `5b1764c9a`); pour le refaire après une mise à jour d'upstream:
```bash
tools/audit_hardcoded.sh third_party/emulationstation docs/audit/HARDCODED.md
```
Le rapport classe les occurrences en 13 catégories. Ordre de traitement suivi:
1. chemins (catégories 1 à 4), centralisés dans `Paths.cpp` ✅;
2. appels `batocera-*` (5, 6, 10), routés vers `esctl` par `LinuxApiSystem` 🚧;
3. drapeaux `/tmp` et `sudo` (7, 9) ❌;
4. menus OS à masquer ou à désactiver (11, 12, 13) 🚧.

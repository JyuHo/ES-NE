# Analyse de l'audit (ES commit `5b1764c9a`, généré le 2026-10-08)

Source: `docs/audit/HARDCODED.md`. Les hypothèses de `HARDCODED_PATHS.md` sont maintenant confirmées ou corrigées.

## 1. Constats clés

| Constat | Détail | Conséquence |
|---|---|---|
| Les chemins sont centralisés | `es-core/src/Paths.cpp` contient les 12 occurrences de `/userdata` et la plupart des chemins `/usr/share/...` | Un seul fichier à patcher pour les chemins |
| Une branche « non-Batocera » existe déjà | `Paths.cpp:31-41` et `:80-87` utilisent `~/.emulationstation`, `<user>/batocera.conf` et `/tmp/overlays/bezels` (probablement sous `#ifdef WIN32`, à confirmer) | On ajoute une 3e branche `ESNE` (XDG) sur ce modèle |
| Les appels système sont centralisés | `ApiSystem.cpp` contient 168 des ~191 occurrences `batocera-*` | Un seul fichier de logique à adapter |
| **ES a déjà une sous-classe pour un autre OS** | `Win32ApiSystem.cpp` (15 occurrences) est ce que RetroBat utilise | On crée `LinuxApiSystem` (ou `EsneApiSystem`) sur ce modèle, sans toucher `ApiSystem.cpp` |
| Les menus dépendent des exécutables présents | `ApiSystem.cpp:2146-2209` pousse `batocera-wifi`, `-bluetooth`, `-resolution`... dans une liste `executables` (probablement testée dans le `PATH`) | Sans le script, le menu disparaît: pas besoin de stubs partout (à confirmer en lisant la fonction) |
| Lancement des jeux | `FileData.cpp:578` écrit `/tmp/game.xml` (donné au lanceur via `-gameinfoxml`), `:675` lit `/tmp/launch_error.log` | Contrat avec `es-launcher`: à relire (voir §4) |
| Redémarrage / arrêt | `Platform.cpp:262-273` crée `/tmp/restart.please`, `reboot.please`, `shutdown.please`; `emulationstation.sh` utilise `es-restart`, `es-sysrestart`, `es-shutdown` | Deux mécanismes: ES-NE doit n'en garder qu'un |

## 2. Appels `batocera-*`: tri par décision

Total: 43 commandes distinctes. Classement proposé:

### A. À implémenter dans `esctl` (cœur, nécessaires pour la parité)
| Commande | Occ. | Usage dans ES | Implémentation Linux |
|---|---|---|---|
| `batocera-resolution` | 5 | `listModes`, `--screen X listModes`, set | `xrandr` / `wlr-randr` / `kscreen-doctor` |
| `batocera-audio` | 8 | `list`, `get`, `set`, `list-profiles`, `get/set-profile` | `wpctl` (PipeWire) ou `pactl` |
| `batocera-info` | 2 | `--full` | `uname`, `/proc`, `lscpu`, `lspci` |
| `batocera-systems` | 4 | liste systèmes / BIOS (`--filter`) | `esctl systems` basé sur `systems.yml` |
| `batocera-padsinfo` | 4 | infos manettes | `evdev` / `udev` |
| `batocera-version` | 2 | version affichée | lecture de la version du paquet |
| `batocera-es-swissknife` | 2 | `--emukill` (tuer l'émulateur) | `pkill` ciblé, ou `esctl emukill` |
| `batocera-timezone` | 5 | `get`, `detect`, set | `timedatectl` |
| `batocera-keyboard` | 4 | layouts / variants | `localectl`, `setxkbmap` / `kbd` |
| `batocera-hotkeys`, `-joysticks-hotkeys` | 10 | config des raccourcis | à voir plus tard (dépend du mécanisme choisi) |
| `batocera-es-thebezelproject` | 5 | liste et install des bezels | script Python (réutilise l'API du Bezel Project) |
| `batocera-preupdate-gamelists-hook` | 3 | hook avant maj des gamelists | no-op ou hook utilisateur |

### B. Optionnel / fonctionnalités avancées (reporter après M5)
`batocera-store` (10), `batocera-services` (5), `batocera-wifi` (8), `batocera-bluetooth` (14), `batocera-scraper` (3), `batocera-ports` (4), `batocera-wine-runners` (1), `batocera-nfc` (3), `batocera-backglass` (3), `batocera-planemode` (3), `batocera-kodi` (2), `batocera-led-handheld` (10), `batocera-gameforce` (3).
Wi-Fi et Bluetooth: sur un poste Arch, ils sont gérés par NetworkManager/BlueZ. Mieux vaut **masquer** ces menus que les réimplémenter.

### C. À supprimer / masquer (sans objet hors de l'OS Batocera)
`batocera-upgrade` (17), `-upgrade-torrent` (5), `-install` (6), `-format` (5), `-storage-manager` (5), `-config` (8), `-sync` (6), `-overclock` (4), `-mitigations` (2), `-support` (3), `-shutdown` (1), `-architecture-compatibility` (1), `-controlcenter` (1), `-linux`, `-scripts`.
Remplacements: `systemctl reboot/poweroff` pour l'arrêt, le gestionnaire de paquets pour les mises à jour.

## 3. Chemins à patcher (`Paths.cpp`)

| Ligne(s) | Valeur actuelle | Cible ES-NE |
|---|---|---|
| 49-51, 53 | `/userdata`, `.../configs/emulationstation`, `.../logs` | `$XDG_CONFIG_HOME/esne`, `$XDG_STATE_HOME/esne/logs` |
| 50, 58 | `/usr/share/emulationstation[/themes]` | `/usr/share/esne[/themes]` |
| 54, 55 | screenshots, saves | `$XDG_DATA_HOME/esne/{screenshots,saves}` |
| 56, 57 | musique système / utilisateur | `/usr/share/esne/music`, `$XDG_DATA_HOME/esne/music` |
| 59 | `/userdata/themes` | `$XDG_DATA_HOME/esne/themes` |
| 61 | `/userdata/system/configs/evmapy` | `$XDG_CONFIG_HOME/esne/evmapy` (ou supprimer: dépend de `evmapy`, un outil Batocera) |
| 62-65 | décorations, shaders | `/usr/share/esne/{decorations,shaders}` + dossier utilisateur |
| 68 | sons RetroAchievements | `$XDG_DATA_HOME/esne/sounds/retroachievements` |
| 70 | `/userdata/system/batocera.conf` | `$XDG_CONFIG_HOME/esne/esne.conf` |
| 71, 72 | `notice.pdf`, `batocera.version` | `/usr/share/esne/` |
| 73 | `/usr/bin/kodi` | `findExecutable("kodi")` dans le `PATH` |

Autres chemins hors `Paths.cpp`:
- `ThemeData.cpp:1859` (`/recalbox/share_init/...`) → supprimer.
- `ThemeData.cpp:2370`, `ApiSystem.cpp:1128`, `SystemData.cpp:1347` (`/etc/emulationstation/...`, « compatibilité RetroPie ») → à garder ou supprimer, sans importance.
- `ApiSystem.cpp:2702` (`/boot/boot/batocera.board`), `Platform.cpp:685` (`batocera.arch`) → remplacer par `uname -m`.
- `GuiMenu.cpp:1507, 1526, 1548, 1568`: `/usr/bin/batocera-keyboard` en chemin absolu → recherche dans le `PATH`.
- `ApiSystem.cpp:2727-2745, 3259`: `/usr/bin/batocera-shutdown`, `virtual-sindenlightgun-remap`, `virtual-wii-mouse-bar-remap`, `steamdeckgun-remap`, `batocera-backglass` → rendre optionnels.
- `ApiSystem.cpp:2207`: `pm-suspend` → `systemctl suspend`.
- `VideoPlayerComponent.cpp:243`: `omxplayer` (Raspberry Pi uniquement) → ignorer.

## 4. Points à confirmer (une lecture ciblée suffit)
1. La commande de lancement dans `FileData.cpp` (autour de `:578` et `:675`): comment `%CONTROLLERSCONFIG%`, `-gameinfoxml` et le code retour sont construits. Ça fixe le contrat de `es-launcher`.
2. La fonction qui teste la liste `executables` (`ApiSystem.cpp` ~2140-2215): si elle utilise bien le `PATH`, les menus se masquent d'eux-mêmes.
3. La fonction `executeScript` / `executeEnumerationScript` (`ApiSystem.cpp:2072`): elle passe par `popen` / `/bin/sh -c` (`Platform.cpp:177`).
4. Si `Paths.cpp:31-41` et `:80-87` sont bien sous `#ifdef WIN32`.
5. `HttpServerThread` (serveur web) et `ZaparooSupport` (port 7497): à garder tels quels, avec un port configurable.

## 5. Plan de patchs (un commit par ligne, sur la branche `esne`)

| # | Préfixe | Changement |
|---|---|---|
| 1 | `esne: build:` | option CMake `-DESNE=ON` + define `ESNE` |
| 2 | `esne: paths:` | branche `ESNE` dans `Paths.cpp` (XDG + `ESNE_*_DIR`) |
| 3 | `esne: paths:` | supprimer `/recalbox`, `batocera.board`, `batocera.arch` |
| 4 | `esne: syscalls:` | `LinuxApiSystem` calquée sur `Win32ApiSystem`, choisie à la compilation |
| 5 | `esne: syscalls:` | résolution, audio, info, systems, version via `esctl` |
| 6 | `esne: menus:` | masquer les menus du groupe C |
| 7 | `esne: syscalls:` | arrêt / redémarrage direct (`Platform.cpp`) et `emulationstation.sh` allégé |
| 8 | `esne: syscalls:` | `GuiMenu.cpp`: `batocera-keyboard` via `PATH` |
| 9 | `esne: launch:` | adapter le lancement d'`FileData.cpp` à `es-launcher` |
| 10 | `esne: menus:` | groupe B: activer au cas par cas |

## 6. Ce que ça change dans ES-NE
- **`esctl`** (Python, dans ce dépôt) remplace seulement le groupe A: 12 commandes, pas 43.
- **Pas de stubs en masse**: le groupe C est masqué côté ES, le groupe B simplement absent.
- **Un seul fichier C++ nouveau** (`LinuxApiSystem`) plutôt que des centaines de modifications dans `ApiSystem.cpp`. Les mises à jour upstream resteront faciles à rebaser.

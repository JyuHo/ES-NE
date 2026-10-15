# Analyse de l'audit (ES commit `5b1764c9a`, généré le 2026-10-08)

Source: `docs/audit/HARDCODED.md`. Les hypothèses de `HARDCODED_PATHS.md` sont confirmées ou corrigées ci-dessous.

**État au 2026-10-12** : les patchs 1 à 5 du fork sont poussés sur la branche `esne` (voir `docs/UPSTREAM.md`).
Légende : ✅ fait · 🚧 partiel · ❌ à faire · ⛔ masqué volontairement.
Un ✅ côté ES signifie « code en place et vérifié à la compilation (syntaxe) », pas « testé dans ES lancé ». Depuis, ES a été compilé et lancé sur CachyOS, et les menus principaux validés (voir `PARITY.md`).

## 1. Constats clés

| Constat | Détail | Conséquence |
|---|---|---|
| Les chemins sont centralisés | `es-core/src/Paths.cpp` contient les 12 occurrences de `/userdata` et la plupart des chemins `/usr/share/...` | Un seul fichier à patcher pour les chemins |
| Une branche « non-Batocera » existe déjà | `Paths.cpp:31-41` (`~/.emulationstation`) est la **branche générique**, pas une branche Windows. Seule la ligne `batocera.conf` est sous `WIN32 && _DEBUG`. ✅ confirmé à la lecture | Une branche `ESNE` (XDG) ajoutée après la branche générique (patch 2) |
| ES sait déjà surcharger ses chemins | `emulationstation.ini` (`emulatorLauncher.cfg` sous Windows), lu par `loadCustomConfiguration()` après les chemins par défaut | Conservé tel quel: les chemins ESNE restent surchargeables sans recompiler |
| Trois variantes de build | `BATOCERA`, `RETROBAT` existaient. `BATOCERA` active du code propre à l'OS (raccourcis globaux dans `main.cpp`, centre de contrôle, mise en page du splash) | `ESNE` est une 3e variante, **sans** `BATOCERA`; exclusive avec les deux autres (patch 1) |
| Macros d'architecture | `X86`/`X86_64` ne sont définies nulle part dans le CMake: c'est le build Batocera qui les passe | Définies depuis `CMAKE_SYSTEM_PROCESSOR` pour ESNE (patch 4). Elles règlent des défauts de bureau (`HideWindow`) |
| Les appels système sont centralisés | `ApiSystem.cpp` contient 168 des ~191 occurrences `batocera-*` | Un seul fichier de logique à adapter |
| **ES a déjà une sous-classe pour un autre OS** | `Win32ApiSystem.cpp` (15 occurrences) est ce que RetroBat utilise | On crée `LinuxApiSystem` (ou `EsneApiSystem`) sur ce modèle, sans toucher `ApiSystem.cpp` |
| Les menus dépendent des exécutables présents | `ApiSystem::isScriptingSupported()` pousse `batocera-wifi`, `-bluetooth`, `-resolution`... dans une liste `executables`, **testée en chemin absolu `/usr/bin/<nom>`** (pas dans le `PATH`). ✅ lu. Les `ScriptId` absents du `switch` (GAMESETTINGS, DECORATIONS, SHADERS, VIDEOFILTERS...) renvoient `true` par défaut | `LinuxApiSystem` surcharge la fonction: menus `esctl` conditionnés à `esctl has <cmd>`, menus Batocera masqués (patch 5) |
| Des appels contournent les méthodes virtuelles | 22 appels `popen`/`system` directs dans `ApiSystem.cpp` (dont `canUpdate`, torrent, `launchKodi`) | La traduction `batocera-*` → `esctl` ne les couvre pas. ✅ surchargés (patch 5): `canUpdate`, `launchKodi`... ✅ corrigés (`3bdea9b`): les 4 fonctions audio, sans quoi le menu audio s'affichait mais échouait. ❌ restent directs: `getCurrentStorage`, `getRootPassword`, scraper, `batocera-upgrade*`, `batocera-controlcenter` (menus masqués ou code sous `BATOCERA`), à confirmer dans `GuiMenu.cpp` |
| Lancement des jeux | `FileData.cpp:578` écrit `/tmp/game.xml` (donné au lanceur via `-gameinfoxml`), `:675` lit `/tmp/launch_error.log` | Contrat avec `es-launcher`: à relire (voir §4) |
| Redémarrage / arrêt | `Platform.cpp:262-273` crée `/tmp/restart.please`, `reboot.please`, `shutdown.please`; `emulationstation.sh` utilise `es-restart`, `es-sysrestart`, `es-shutdown` | Deux mécanismes: ES-NE doit n'en garder qu'un. ✅ patch 7 (systemctl + execv) |

## 2. Appels `batocera-*`: tri par décision

Total: 43 commandes distinctes. Classement proposé. Dans ES, les groupes A sont **déjà branchés** (patch 5, via `esctl`); l'outil `esctl` lui-même reste à écrire (contrat: `docs/ESCTL_CONTRACT.md`).

### A. À implémenter dans `esctl` (cœur, nécessaires pour la parité)
Côté ES: ✅ traduction `batocera-x` → `esctl x` et menus conditionnés à `esctl has x` (patch 5). Côté `esctl`: ✅ `resolution`, `audio`, `version`, `config lsoutputs`; ❌ `systems`, `padsinfo`, `timezone`, `thebezelproject`, `info`, `swissknife`, `preupdate-gamelists-hook`.

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
Côté ES: ⛔ masqués par `LinuxApiSystem` pour Wi-Fi, Bluetooth, store, services, plane mode, backglass, NFC. `kodi`: ⛔ absent d'ES-NE, entrées de menu masquées. Les autres (scraper, ports, LED, gameforce...) ne sont pas encore traités: 🚧 patch 6 (voir `docs/UPSTREAM.md`).
`batocera-store` (10), `batocera-services` (5), `batocera-wifi` (8), `batocera-bluetooth` (14), `batocera-scraper` (3), `batocera-ports` (4), `batocera-wine-runners` (1), `batocera-nfc` (3), `batocera-backglass` (3), `batocera-planemode` (3), `batocera-kodi` (2), `batocera-led-handheld` (10), `batocera-gameforce` (3).
Wi-Fi et Bluetooth: sur un poste Arch, ils sont gérés par NetworkManager/BlueZ. Mieux vaut **masquer** ces menus que les réimplémenter.

### C. À supprimer / masquer (sans objet hors de l'OS Batocera)
Côté ES: ✅ menus protégés par `isScriptingSupported` masqués (upgrade, install, format, sync/backup, support). ✅ `canUpdate`, `canLocalUpdate`, `canArchitectureUpdate`, `updateSystem` désactivées. ✅ Vérifié (patch 6, voir `docs/ROADMAP.md`): aucun appel direct atteignable dans `GuiMenu.cpp` pour les entrées qui appellent directement `batocera-config`, `batocera-storage-manager`, `batocera-support` sans passer par `isScriptingSupported` (patch 6).
`batocera-upgrade` (17), `-upgrade-torrent` (5), `-install` (6), `-format` (5), `-storage-manager` (5), `-config` (8), `-sync` (6), `-overclock` (4), `-mitigations` (2), `-support` (3), `-shutdown` (1), `-architecture-compatibility` (1), `-controlcenter` (1), `-linux`, `-scripts`.
Remplacements: `systemctl reboot/poweroff` pour l'arrêt, le gestionnaire de paquets pour les mises à jour.

## 3. Chemins à patcher (`Paths.cpp`)

| Ligne(s) | Valeur actuelle | Cible ES-NE |
|---|---|---|
| 49-51, 53 | `/userdata`, `.../configs/emulationstation`, `.../logs` | `$XDG_CONFIG_HOME/esne`, `$XDG_STATE_HOME/esne/logs` |
| 50, 58 | `/usr/share/emulationstation[/themes]` | `/usr/share/esne[/themes]` |
| 54, 55 | screenshots, saves | `~/esne/{screenshots,saves}` |
| 56, 57 | musique système / utilisateur | `/usr/share/esne/music`, `~/esne/music` |
| 59 | `/userdata/themes` | `~/esne/themes` |
| 61 | `/userdata/system/configs/evmapy` | `$XDG_CONFIG_HOME/esne/evmapy` (ou supprimer: dépend de `evmapy`, un outil Batocera) |
| 62-65 | décorations, shaders | `/usr/share/esne/{decorations,shaders}` + dossier utilisateur |
| 68 | sons RetroAchievements | `~/esne/sounds/retroachievements` |
| 70 | `/userdata/system/batocera.conf` | `$XDG_CONFIG_HOME/esne/esne.conf` |
| 71, 72 | `notice.pdf`, `batocera.version` | `/usr/share/esne/` |
| 73 | `/usr/bin/kodi` | sans objet: Kodi retiré d'ES-NE |

**Réalisé dans le patch 2** (`Paths.cpp`, branche `#if ESNE`). Écarts par rapport à la proposition ci-dessus:
- les dossiers sont répartis en quatre racines: `share` (`ESNE_SHARE_DIR`, défaut `/usr/share/esne`), `config`, `data`, `state` (logs dans `~/.local/state/esne/logs`), chacune surchargeable par `ESNE_{SHARE,CONFIG,DATA,STATE}_DIR`;
- les mappages clavier (`padtokey`) restent dans `share/padtokey` et `config/padtokey` (pas d'`evmapy`, outil Batocera);
- les shaders gardent le sous-dossier `shaders/configs` pour rester compatibles avec `batocera-shaders`;
- les sons RetroAchievements sont dans `share/sounds/retroachievements` et `data/sounds/retroachievements` (et non `/usr/share/libretro/assets/sounds`);
- `kodi`: sans objet, Kodi n'est pas fourni (entrées de menu masquées par `LinuxApiSystem`);
- `emulationstation.ini` garde la priorité finale.

Autres chemins hors `Paths.cpp` (état):
- ✅ `ThemeData.cpp:1859` (`/recalbox/share_init/...`): ignoré sous ESNE (patch 3).
- ❌ `ThemeData.cpp:2370`, `ApiSystem.cpp:1128`, `SystemData.cpp:1347` (`/etc/emulationstation/...`, « compatibilité RetroPie ») → à garder ou supprimer, sans importance.
- ✅ `ApiSystem.cpp:2702` (`/boot/boot/batocera.board`): `getRunningBoard()` renvoie une chaîne vide (patch 5). ✅ `Platform.cpp:685` (`batocera.arch`): non lu sous ESNE, repli sur les macros d'architecture (patch 3 + 4).
- ✅ `GuiMenu.cpp`: `/usr/bin/batocera-keyboard` remplacé par `esctl keyboard` (patch 8, commit `88507e6`).
- 🚧 `ApiSystem.cpp:2727-2745, 3259`: `/usr/bin/batocera-shutdown` ✅ (remplacé par `systemctl suspend` dans `suspend()`); `virtual-sindenlightgun-remap`, `virtual-wii-mouse-bar-remap`, `steamdeckgun-remap` ❌ (`replugControllers_*`, encore appelés tels quels); `batocera-backglass` ⛔ masqué.
- ✅ `ApiSystem.cpp:2207`: `pm-suspend` remplacé par un test de `systemctl` dans le `PATH` (patch 5).
- ❌ `VideoPlayerComponent.cpp:243`: `omxplayer` (Raspberry Pi uniquement) → ignorer.

## 4. Points à confirmer
1. ❌ **Ouvert.** La commande de lancement dans `FileData.cpp` (autour de `:578` et `:675`): comment `%CONTROLLERSCONFIG%`, `-gameinfoxml` et le code retour sont construits. Ça fixe le contrat de `es-launcher`. Pas encore lu.
2. ✅ **Résolu.** `isScriptingSupported()` teste `/usr/bin/<nom>` en chemin absolu, pas le `PATH`. Les `ScriptId` hors `switch` valent `true` par défaut. Conséquence: un script installé dans `/usr/local/bin` n'est pas détecté (d'où la surcharge dans `LinuxApiSystem`).
3. ✅ **Résolu.** `executeScript` / `executeEnumerationScript` passent par `popen` / `system` et sont `virtual protected`: c'est le point d'accroche de la traduction `batocera-*` → `esctl`. Mais plusieurs fonctions appellent `popen`/`system` directement et contournent ce point (voir §1).
4. ✅ **Résolu.** `Paths.cpp:31-41` n'est pas sous `#ifdef WIN32` (branche générique).
5. ❌ **Ouvert.** `HttpServerThread` (serveur web) et `ZaparooSupport` (port 7497): à garder tels quels, avec un port configurable. Pas encore examinés.

## 5. Plan de patchs (un commit par ligne, sur la branche `esne`)

Le plan initial a été regroupé à l'exécution: le patch 5 livré (`LinuxApiSystem`) couvre les lignes 4, 5 et une grande partie de 6 du plan. Un patch « X86 » s'est ajouté.

| Plan | Préfixe | Changement | État | Commit du fork |
|---|---|---|---|---|
| 1 | `esne: build:` | option CMake `-DESNE=ON` + define `ESNE` (+ `ESNE_SHARE_DIR`) | ✅ | `99b711a` |
| 2 | `esne: paths:` | branche `ESNE` dans `Paths.cpp` (XDG + `ESNE_*_DIR`) | ✅ | `e142310` |
| 3 | `esne: paths:` | supprimer `/recalbox`, `batocera.board`, `batocera.arch` | ✅ | `e28606c` (+ `b935f4c` pour `batocera.board`) |
| (ajout) | `esne: build:` | définir `X86`/`X86_64` depuis `CMAKE_SYSTEM_PROCESSOR` | ✅ | `67167a7` |
| 4 | `esne: syscalls:` | `LinuxApiSystem` calquée sur `Win32ApiSystem`, choisie à la compilation | ✅ | `b935f4c` |
| 5 | `esne: syscalls:` | résolution, audio, info, systems, version via `esctl` | 🚧 côté ES ✅; `esctl`: version, résolution, audio ✅, le reste ❌ | `b935f4c`, `3bdea9b` (audio) |
| 6 | `esne: menus:` | masquer les menus du groupe C | 🚧 menus protégés par `isScriptingSupported` ✅; appels directs dans `GuiMenu.cpp` ❌ | `b935f4c` (partiel) |
| 7 | `esne: syscalls:` | arrêt / redémarrage direct (`Platform.cpp`) et `emulationstation.sh` allégé | ✅ (`2c029de`) | |
| 8 | `esne: syscalls:` | `GuiMenu.cpp`: `batocera-keyboard` → `esctl keyboard` | ✅ | `88507e6` |
| 9 | `esne: launch:` | adapter le lancement d'`FileData.cpp` à `es-launcher` | ✅ (sans objet, sauf l'installation d'un core manquant: `b567ac1`) | |
| 10 | `esne: menus:` | groupe B: activer au cas par cas | ❌ | |

## 6. Ce que ça change dans ES-NE
- **`esctl`** (Python, dans ce dépôt) remplace seulement le groupe A: 12 commandes, pas 43.
- **Pas de stubs en masse**: le groupe C est masqué côté ES, le groupe B simplement absent.
- **Une seule classe C++ nouvelle** (`LinuxApiSystem`, deux fichiers) plutôt que des centaines de modifications dans `ApiSystem.cpp`, qui n'est touché que sur 6 lignes (include et sélection dans `getInstance()`). Les mises à jour upstream restent faciles à rebaser.
- **`ESNE` n'est pas `BATOCERA`**: le code propre à l'OS (raccourcis globaux, centre de contrôle) reste désactivé. Si une de ces fonctions devient utile, elle devra être réactivée explicitement sous `ESNE`.

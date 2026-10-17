# Roadmap
Légende: ✅ fait · 🚧 en cours · ❌ à faire. Un ✅ côté ES = code en place et vérifié à la compilation (syntaxe), pas encore testé dans ES lancé.

## M0 — ES compilé avec chemins patchés, `esctl` minimal, 1 système ✅
- ✅ option CMake `-DESNE=ON` (variante sans `BATOCERA`)
- ✅ chemins (`Paths.cpp`): config/état/cache XDG, données dans `~/esne` (roms, bios, saves, thèmes, décorations)
- ✅ `LinuxApiSystem`: traduction `batocera-*` → `esctl`, menus conditionnés, mises à jour désactivées
- ✅ build complet d'ES sur CachyOS et lancement (KDE Wayland)
- ✅ `esctl` minimal: `has`, `version`, `resolution`, `audio`, `config lsoutputs` (résolution et audio testés sur sorties simulées)
- ✅ `esctl` suite: `timezone`, `padsinfo`, `info`
- ✅ `esctl thebezelproject` (liste, installation, suppression)
- ✅ `esctl systems` (état des BIOS, catalogue `bios.yml`), `swissknife --emukill` (pid de l'émulateur écrit par `es-launcher`), `preupdate-gamelists-hook`: testés sur la machine
- ✅ appels audio d'ES routés par la traduction `batocera-*` → `esctl` (sinon le menu audio échouait)
- ✅ de bout en bout (ES → `es-launcher` → RetroArch/Dolphin): SNES, N64, GameCube, Wii validés

## M1 — `es-launcher` + générateur RetroArch ✅
- ✅ contrat de lancement lu (`FileData.cpp`): ES construit la ligne depuis la balise `<command>` d'`es_systems.cfg`, puis lit le code de sortie (200-205: messages fixes; 250/299: message dans `/tmp/launch_error.log`)
- ✅ CLI compatible avec la ligne d'ES (`-system -rom -emulator -core -gameinfoxml -systemname -p<N>index/guid/path/name/nbbuttons/nbhats/nbaxes`), options d'ES non interprétées conservées
- ✅ choix émulateur/core: arguments d'ES > `esne.conf` (en couches) > catalogue `systems.yml` (27 systèmes, surchargeable dans `~/.config/esne/systems.yml`)
- ✅ RetroArch: configuration complémentaire `--appendconfig` (le `retroarch.cfg` de l'utilisateur n'est jamais modifié): plein écran, dossiers de sauvegarde/BIOS, `smooth`, `ratio`, `rewind`, `autosave`, `integerscale`, `shaderset` (`--set-shader`, pilote vulkan ou glcore), pilote joypad `sdl2`, raccourcis Select+Start / Select+R3
- ✅ codes de sortie 200-205 et 299 vers ES, journal `<state>/logs/es-launcher.log`
- 🚧 validé avec un vrai RetroArch: shaders, ratio 4/3, rewind; table des ratios (`aspect_ratio_index`) en partie non validée
- ✅ manettes: pilote `sdl2` (pas d'autoconfig); raccourci pour quitter, aussi pour les émulateurs autonomes (`hotkey.py`)
- ✅ validés en jeu: états de sauvegarde (`-state_slot`, `-state_file`, `-autosave`; stockés sans sous-dossier par core), jeux compressés (extraction zip/7z pour les cores qui ne lisent pas les archives)
- 🚧 écrits, tests unitaires, pas encore validés en jeu: netplay (`--host`/`--connect`, réglages `netplay_*`, `netplay="true"` dans `es_systems.cfg`), `-monitor` (`video_monitor_index`)

## M2 — config en couches + génération `es_systems.cfg` / `es_features.cfg` ✅
- ✅ résolution en couches (`<système>["rom"].clé` > `<système>.clé` > `global.clé`), tests unitaires seulement: pas validée en jeu, pas de couche par core
- ✅ `es-genconfig`: `es_systems.cfg`, `es_features.cfg`, jeux de shaders, dossiers de roms (catalogue `systems.yml`, options `featurescfg.py`)

## M3 — manettes (es_input, SDL DB, multi-joueurs) 🚧
Pad 1 via `sdl2` et raccourcis OK; multi-joueurs validé avec 2 manettes sur Cemu, Eden, RPCS3 et Dolphin (GameCube; Wii en Classic Controller et Wiimote + Nunchuk); reste à tester sur RetroArch; manettes Xbox: voir plus bas; configuration par jeu (`<système>["rom"].clé`): écrite et testée en unitaire, pas validée en jeu; pas de couche par core (seul le choix du core est par jeu ou par système).
## M4 — émulateurs standalone 🚧
Dolphin validé; umu (jeux Windows, émulateur par défaut du système `windows`): générateur `umu.py` et réglages ES écrits (GE-Proton, préfixe par jeu avec le nom du jeu pour `GAMEID`, DXVK/VKD3D-Proton ou WineD3D, esync/fsync, FSR, bureau virtuel, MangoHud, Gamemode, limite d'images), à valider en jeu (lancement, fermeture par Select+Start de l'arbre Wine/pressure-vessel, valeur de `GAMEID`); Wine seul non essayé; Steam: lancement, manette, raccourci Select+Start (arbre de processus du jeu fermé) et fermeture du client validés avec Cuphead (`esne-steam-run`). Réglages internes: Cemu (profils de manette SDL + API graphique; langue, VSync, filtre, volume, FPS) validé en jeu avec 2 manettes; PCSX2 (manettes SDL + résolution) validé en jeu; RPCS3 (manettes SDL + vidéo) validé en jeu avec 2 manettes; Eden (recopie du mappage joueur 1; mode, résolution, anisotrope, VSync, AA, filtre, format, langue, région, anisotrope automatique/défaut) validé en jeu avec 2 manettes; xemu: validé en jeu (résolution et format d'image choisis dans ES; fichiers BIOS reconnus à leur taille dans `bios/xbox`, manettes dans `xemu.toml`, AppImage); Redream (Dreamcast): lancement, plein écran, manette et réglages ES (région, langue, câble, standard TV, format, résolution, VSync, rendu, frame skip, compteur d'images) dans `redream.cfg` validés en jeu; Xenia Canary (Xbox 360, AppImage du fork Linux natif): lancement d'un `.iso`, plein écran (`--fullscreen=true`) et manette validés en jeu, réglages vidéo, son, langue et région de la console choisis dans ES (ligne de commande, et octets de `xconfig.settings` pour la langue et la région): validés en jeu; RMG (N64: réglages vidéo, manette configurée automatiquement) et PPSSPP (PSP: réglages vidéo, son, langue): validés en jeu; DuckStation (PS1: réglages vidéo, manettes, options de fermeture) et Snes9x (SNES: réglages vidéo, manettes Sony automatiques, croix ou joystick gauche): validés en jeu; Dolphin (API, résolution, format, AA, anisotrope, VSync, FPS, hack 16:9, shaders, langue GameCube; langue, TV et barre capteur de la Wii dans la SYSCONF; manettes SDL: GameCube à 2 joueurs, Wii en Classic Controller et en Wiimote + Nunchuk émulés): validé en jeu; options PCSX2 supplémentaires (anisotrope, filtre, CAS, dithering, patchs 16:9 et sans entrelacement, FPS, volume, son coupé, VSync, FXAA): validées en jeu; les autres émulateurs restent à faire.
## M5 — bezels, shaders, scraper, RetroAchievements, netplay 🚧
Shaders ✅. Bezels ✅ (un par système, The Bezel Project): installation, désinstallation, aperçu et affichage RetroArch validés en jeu sur SNES et N64; bezels par jeu (téléchargés à la demande, repli sur le système) validés sur SNES, N64, PSX et GBA; reste un écran 16:9. Scraper ScreenScraper ✅ (clés lues dans `keys.conf`, scrape validé). Reste: tatouages, RetroAchievements (clé à tester), netplay.
## M6 — PKGBUILD, session (Gamescope, Wayland/X11) 🚧
Dans `packaging/arch/` (PKGBUILD `es-ne-git`, `es-ne-session`, `es-ne.desktop`, règles polkit `50-es-ne.rules` et `org.esne.install-core.policy`, aides root `esne-install-core` / `esne-install-aur-core`). ✅ `makepkg`, installation et session de connexion (Plasma Login Manager, `gamescope -f` sans `-e`, journal `~/.local/state/esne/session.log`) validés sur CachyOS (BC-250). Reste: SDDM/autres gestionnaires, session X11.

## Chantiers ES hors jalons (voir `docs/AUDIT_ANALYSIS.md` §5)
- ✅ patch 6 sans objet: `GuiMenu.cpp` n'appelle plus aucun `batocera-*` directement. Le code propre aux consoles portables (overscan, LED, GameForce, RK3326, RPi) est derrière des drapeaux de compilation absents d'`ESNE`, la luminosité (écran de Steam Deck, portables x86) lit `/sys/class/backlight` sans script, stockage, mises à jour, services et le reste sont masqués par `isScriptingSupported` (faux dans `LinuxApiSystem`); les `popen` restants d'`ApiSystem.cpp` (mises à jour, scraper Batocera, contrôle center) ne sont atteints que par ces menus masqués
- ✅ traductions françaises complètes; installation en un clic d'un core manquant (dépôts officiels et AUR, `esctl install-core`)
- ✅ patch 7: arrêt / redémarrage via `systemctl`, redémarrage d'ES par `execv`
- ✅ patch 8: `batocera-keyboard` remplacé par `esctl keyboard` (`localectl`), validé
- ✅ patch 9 sans objet: ES lance déjà la commande de `es_systems.cfg`; le travail est côté `es-launcher` et dans la génération de `es_systems.cfg` (M2)
- ❌ patch 10: fonctions optionnelles (scraper, ports...)

## Prochaines étapes
- Steam: piste Batocera: fin de partie lue dans `console_log.txt` de Steam
- Autres émulateurs autonomes possibles: melonDS, Flycast (DuckStation et Snes9x faits). Manettes Snes9x: seul le profil Sony est intégré (autres modèles: mappage du joueur 1 recopié)
- Autres ports PortMaster (OpenTyrian, SDLPoP, OpenGGS), Ryujinx
- RetroArch: netplay, `-monitor`, RetroAchievements en jeu
- Réglages dans ES: Dolphin et PCSX2 validés en jeu. RPCS3: pas d'autres options, les jeux se règlent au cas par cas dans RPCS3; Redream et Xenia: options principales faites, le reste volontairement laissé à la configuration de l'émulateur
- README en français, anglais et allemand ✅ (1.0.8); interface d'ES: les 17 chaînes d'ES-NE ou récentes d'upstream sont traduites dans toutes les langues (1.0.8); restent les langues incomplètes d'upstream (`cy_GB`, `he`, `nn_NO`, `oc_FR`, `uk_UA`, `fi_FI`, `el`: 300 à 1100 chaînes) et les menus matériels masqués dans ES-NE; bezels sur écran 16:9; option pour garder le ratio du bezel avec bandes noires en 16:10

## Thème ES-NE ✅ (remplace Carbon dans le paquet)
Fait: `themes/es-ne` livré par le `PKGBUILD` (Carbon retiré, `es-theme-carbon` n'est plus téléchargé) et choisi par défaut dans le fork (`ThemeSet`, commit `af40479`). 27 systèmes + collections, assets générés par `tools/theme/gen_assets.py`, deux ambiances (Nuit, Braise), fond animé partagé par toutes les vues (une seule image de bandes, 0,8 Mo; l'animation reste continue d'un système à l'autre grâce à l'horloge globale du fork), carrousel des systèmes centré avec le système actif agrandi, icônes de touches Xbox/PlayStation de Kenney (CC0), heure, réseau et activité des manettes en haut à droite, pastilles (savestate, succès, favori, joueurs, région), menus sombres. Logos de consoles: HVR88/Monochrome-Gaming-Logos (usage non commercial). Aperçu sans machine graphique: `tools/theme/preview.py`.
Idées: troisième ambiance, variante Nintendo des icônes de touches, thèmes par système plus poussés (vue détaillée avec vidéo), traduction des mots « FAVORITES / ALL GAMES » des collections.

## Versions

Une release par avancée notable (nouvel émulateur, série d'options): 1.0.1 à 1.0.10, puis 1.1.0 et la suite 1.1.1 à 1.1.10, etc. 1.0.1: Xbox 360 (Xenia Canary) avec réglages vidéo dans ES, logo ES-NE. 1.0.2: réglages dans ES pour Eden, Cemu, xemu et Xenia (langue, région, son), validés en jeu. 1.0.3: Dreamcast (Redream), validée en jeu. 1.0.4: Dolphin (réglages ES, manettes GameCube et Wii, langues, barre capteur), options PCSX2 et options de rendu de Redream, validés en jeu. 1.0.5: Xenia (langues coréen/russe/chinois, régions NL/RU/CZ, mode vidéo `avpack`) et anisotrope automatique/défaut d'Eden, validés en jeu. 1.0.6: RMG (N64) et PPSSPP (PSP) en standalone, réglages vidéo dans ES, manettes RMG configurées automatiquement (chemin hidraw/evdev retrouvé par le lanceur), validés en jeu. 1.0.7: DuckStation (PS1) en standalone, réglages vidéo et manettes dans `settings.ini`, validé en jeu. 1.0.8: Snes9x (SNES) en standalone (réglages ES, manettes Sony automatiques, croix ou joystick gauche), validé en jeu; audit du code (catalogue en cache, lecture tolérante des fichiers de réglages); README en français, anglais et allemand. 1.0.9: interface d'ES traduite dans toutes les langues pour les chaînes d'ES-NE (redémarrage, installation d'un core, AUR) et les nouveautés d'upstream, `eu_ES` corrigé. 1.0.10: thème ES-NE par défaut (Carbon retiré du paquet), icônes Kenney, fond animé continu, indicateurs réseau/manettes/heure, carrousel recentré; fork: aide des menus (SELECT, barre de navigation) et animations « forever » synchronisées.

## Licence
Le projet est en GPL-3.0-or-later (voir `docs/LICENSING.md`): du code de batocera-configgen (GPL-3) peut être repris.
Le fork d'EmulationStation reste sous MIT.

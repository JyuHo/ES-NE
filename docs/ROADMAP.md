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
- ✅ choix émulateur/core: arguments d'ES > `esne.conf` (en couches) > catalogue `systems.yml` (24 systèmes, surchargeable dans `~/.config/esne/systems.yml`)
- ✅ RetroArch: configuration complémentaire `--appendconfig` (le `retroarch.cfg` de l'utilisateur n'est jamais modifié): plein écran, dossiers de sauvegarde/BIOS, `smooth`, `ratio`, `rewind`, `autosave`, `integerscale`, `shaderset` (`--set-shader`, pilote vulkan ou glcore), pilote joypad `sdl2`, raccourcis Select+Start / Select+R3
- ✅ codes de sortie 200-205 et 299 vers ES, journal `<state>/logs/es-launcher.log`
- 🚧 validé avec un vrai RetroArch: shaders, ratio 4/3, rewind; table des ratios (`aspect_ratio_index`) en partie non validée
- ✅ manettes: pilote `sdl2` (pas d'autoconfig); raccourci pour quitter, aussi pour les émulateurs autonomes (`hotkey.py`)
- ❌ netplay, états de sauvegarde (`-state_slot`), jeux compressés (zip/7z), `-monitor`

## M2 — config en couches + génération `es_systems.cfg` / `es_features.cfg` ✅
- ✅ résolution en couches (`<système>["rom"].clé` > `<système>.clé` > `global.clé`)
- ✅ `es-genconfig`: `es_systems.cfg`, `es_features.cfg`, jeux de shaders, dossiers de roms (catalogue `systems.yml`, options `featurescfg.py`)

## M3 — manettes (es_input, SDL DB, multi-joueurs) 🚧
Pad 1 via `sdl2` et raccourcis OK; multi-joueurs et configuration par jeu non faits.
## M4 — émulateurs standalone 🚧
Dolphin validé; PCSX2, RPCS3, Cemu, Eden/Ryujinx, xemu, Steam, Wine/umu décrits dans `emulators.yml` mais non essayés. Réglages internes: Cemu (profils de manette SDL + API graphique) validé en jeu avec 2 manettes; PCSX2 (manettes SDL + réglages graphiques) écrit, non testé; Eden (recopie du mappage joueur 1) validé en jeu avec 2 manettes; les autres émulateurs restent à faire.
## M5 — bezels, shaders, scraper, RetroAchievements, netplay 🚧
Shaders ✅. Bezels ✅ (un par système, The Bezel Project): installation, désinstallation, aperçu et affichage RetroArch validés en jeu sur SNES et N64; restent à voir un bezel à ouverture non centrée et un écran 16:9. Reste: tatouages, scraper, RetroAchievements, netplay.
## M6 — PKGBUILD, session (Gamescope, Wayland/X11) 🚧
Écrits dans `packaging/arch/` (PKGBUILD `es-ne-git`, `es-ne-session`, `es-ne.desktop`, règle polkit `50-es-ne.rules`), pas encore testés: `makepkg` et la session de connexion restent à valider sur CachyOS.

## Chantiers ES hors jalons (voir `docs/AUDIT_ANALYSIS.md` §5)
- 🚧 patch 6: appels `batocera-*` restants dans `GuiMenu.cpp` (stockage, overscan, LED...): voir « Ce qui reste de Batocera » dans `docs/UPSTREAM.md`
- ✅ patch 7: arrêt / redémarrage via `systemctl`, redémarrage d'ES par `execv`
- ❌ patch 8: `batocera-keyboard` via le `PATH`
- ✅ patch 9 sans objet: ES lance déjà la commande de `es_systems.cfg`; le travail est côté `es-launcher` et dans la génération de `es_systems.cfg` (M2)
- ❌ patch 10: fonctions optionnelles (scraper, ports, LED...)

## Licence
Le projet est en GPL-3.0-or-later (voir `docs/LICENSING.md`): du code de batocera-configgen (GPL-3) peut être repris.
Le fork d'EmulationStation reste sous MIT.

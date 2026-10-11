# Roadmap
Légende: ✅ fait · 🚧 en cours · ❌ à faire. Un ✅ côté ES = code en place et vérifié à la compilation (syntaxe), pas encore testé dans ES lancé.

## M0 — ES compilé avec chemins patchés, `esctl` minimal, 1 système 🚧
- ✅ option CMake `-DESNE=ON` (variante sans `BATOCERA`)
- ✅ chemins XDG (`Paths.cpp`)
- ✅ `LinuxApiSystem`: traduction `batocera-*` → `esctl`, menus conditionnés, mises à jour désactivées
- ❌ build complet d'ES sur Arch/CachyOS et premier lancement
- ✅ `esctl` minimal: `has`, `version`, `resolution`, `audio`, `config lsoutputs` (testés sur sorties simulées; ❌ pas encore sur machine réelle)
- ❌ `esctl` suite: `timezone`, `systems`, `padsinfo`, `thebezelproject`, `info`, `swissknife`
- ✅ appels audio d'ES routés par la traduction `batocera-*` → `esctl` (sinon le menu audio échouait)
- 🚧 1 système de bout en bout (ES → `es-launcher` → RetroArch): lanceur écrit et testé avec un faux RetroArch; ❌ pas encore essayé avec un vrai jeu

## M1 — `es-launcher` + générateur RetroArch 🚧
- ✅ contrat de lancement lu (`FileData.cpp`): ES construit la ligne depuis la balise `<command>` d'`es_systems.cfg`, puis lit le code de sortie (200-205: messages fixes; 250/299: message dans `/tmp/launch_error.log`)
- ✅ CLI compatible avec la ligne d'ES (`-system -rom -emulator -core -gameinfoxml -systemname -p<N>index/guid/path/name/nbbuttons/nbhats/nbaxes`), options d'ES non interprétées conservées
- ✅ choix émulateur/core: arguments d'ES > `esne.conf` (en couches) > catalogue `systems.yml` (16 systèmes, surchargeable dans `~/.config/esne/systems.yml`)
- ✅ RetroArch: configuration complémentaire `--appendconfig` (le `retroarch.cfg` de l'utilisateur n'est jamais modifié): plein écran, dossiers de sauvegarde/BIOS, `smooth`, `ratio`, `rewind`, `autosave`, `integerscale`, `shaderset` (fichier de preset par nom)
- ✅ codes de sortie 200-205 et 299 vers ES, journal `<state>/logs/es-launcher.log`
- ❌ non validé avec un vrai RetroArch: table des ratios (`aspect_ratio_index`), noms des options
- ❌ manettes: transmises mais pas utilisées (l'autoconfiguration de RetroArch s'applique); pas de raccourci pour quitter un jeu à la manette
- ❌ netplay, états de sauvegarde (`-state_slot`), bezels, jeux compressés (zip/7z), `-monitor`
- ❌ pas de patch ES nécessaire pour lancer les jeux: il reste à générer `es_systems.cfg` (M2)

## M2 — config en couches + `features.yml` + génération `es_systems.cfg` / `es_features.cfg` 🚧
- ✅ résolution en couches (`<système>["rom"].clé` > `<système>.clé` > `global.clé`)
- ❌ `features.yml`, génération des fichiers d'ES

## M3 — manettes (es_input, SDL DB, multi-joueurs) ❌
## M4 — émulateurs standalone (Dolphin, PCSX2, PPSSPP, DuckStation, RPCS3, Cemu...) ❌
## M5 — bezels, shaders, scraper, RetroAchievements, netplay ❌
## M6 — PKGBUILD, session (Gamescope, Wayland/X11) ❌

## Chantiers ES hors jalons (voir `docs/AUDIT_ANALYSIS.md` §5)
- ❌ patch 6: appels `batocera-*` directs restants dans `GuiMenu.cpp` (stockage, overscan, LED...)
- ❌ patch 7: arrêt / redémarrage directs (`Platform.cpp`, `emulationstation.sh`), un seul mécanisme de fichiers drapeaux
- ❌ patch 8: `batocera-keyboard` via le `PATH`
- ✅ patch 9 sans objet: ES lance déjà la commande de `es_systems.cfg`; le travail est côté `es-launcher` et dans la génération de `es_systems.cfg` (M2)
- ❌ patch 10: fonctions optionnelles (scraper, ports, LED...)

## Licence
Le projet est en GPL-3.0-or-later (voir `docs/LICENSING.md`): du code de batocera-configgen (GPL-3) peut être repris.
Le fork d'EmulationStation reste sous MIT.

# Roadmap
Légende: ✅ fait · 🚧 en cours · ❌ à faire. Un ✅ côté ES = code en place et vérifié à la compilation (syntaxe), pas encore testé dans ES lancé.

## M0 — ES compilé avec chemins patchés, `esctl` minimal, 1 système 🚧
- ✅ option CMake `-DESNE=ON` (variante sans `BATOCERA`)
- ✅ chemins XDG (`Paths.cpp`)
- ✅ `LinuxApiSystem`: traduction `batocera-*` → `esctl`, menus conditionnés, mises à jour désactivées
- ❌ build complet d'ES sur Arch/CachyOS et premier lancement
- ❌ `esctl` minimal: `has`, `version`, `resolution`, `audio`
- ❌ 1 système de bout en bout (ES → `es-launcher` → RetroArch)

## M1 — `es-launcher` + générateur RetroArch complet 🚧
- ✅ CLI compatible avec l'appel d'ES, générateur RetroArch minimal (lance `retroarch -L core rom`)
- ❌ écriture de `retroarch.cfg`, ratio, shaders, rewind
- ❌ contrat de lancement avec ES (`FileData.cpp`, `/tmp/game.xml`, code retour): pas encore lu

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
- ❌ patch 9: lancement des jeux adapté à `es-launcher`
- ❌ patch 10: fonctions optionnelles (scraper, ports, LED...)

## Licence
Le projet est en GPL-3.0-or-later (voir `docs/LICENSING.md`): du code de batocera-configgen (GPL-3) peut être repris.
Le fork d'EmulationStation reste sous MIT.

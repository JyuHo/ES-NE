# ES-NE

Version standalone de [batocera-emulationstation](https://github.com/batocera-linux/batocera-emulationstation)
pour Arch Linux / CachyOS, avec les options de RetroBat, **sans aucune dépendance à Batocera**.

- Arborescence Linux classique (XDG), pas de `/userdata`
- Frontend: fork d'EmulationStation patché (variante de build `ESNE`), en sous-module
- Lanceur `es-launcher` (remplace `emulatorlauncher` / `batocera-configgen`)
- Outil système `esctl` (remplace les `batocera-*`): résolution, audio, fuseau horaire, BIOS...
- Même format de clés que `batocera.conf` (`global.ratio`, `snes.core`, `snes["jeu.zip"].shaderset`)
  pour rester compatible avec les menus d'ES
- Définitions déclaratives (YAML) des systèmes, émulateurs et features

## Statut
| Composant | État |
|---|---|
| Frontend ES (fork `emulationstation-esne`, branche `esne`) | ✅ compile et tourne sur CachyOS (KDE Wayland). Patchs: option `-DESNE=ON`, chemins (config XDG, données dans `~/esne`), `LinuxApiSystem`, arrêt/redémarrage système, redémarrage d'ES, menu QUIT simplifié, Zaparoo désactivé par défaut |
| `es-launcher` | ✅ lancement validé sur une vraie machine (SNES, N64, GameCube, Wii): RetroArch (manette `sdl2`, raccourcis, ratio, shaders, rewind...) et émulateurs autonomes; 172 tests |
| `es-genconfig` | ✅ génère `es_systems.cfg`, `es_features.cfg` et les jeux de shaders depuis le catalogue (25 systèmes) |
| `esctl` | ✅ `has`, `version`, `resolution`, `audio`, `config`, `info`, `timezone`, `padsinfo`, `thebezelproject`, `systems` (état des BIOS), `swissknife --emukill`, `preupdate-gamelists-hook`. Contrat dans `docs/ESCTL_CONTRACT.md` |
| Paquet Arch (`packaging/arch/PKGBUILD`), session `ES-NE`, règle polkit | 🚧 le paquet se construit (`makepkg -fs`); installation et session de connexion à valider. Compiler dans une copie hors du dépôt: `makepkg` réécrit `pkgver` |

Détails: `docs/ROADMAP.md` (jalons), `PARITY.md` (parité avec RetroBat), `docs/UPSTREAM.md` (patchs d'ES).

## Chemins
**Frontend ES** (`-DESNE=ON`):

| Rôle | Chemin par défaut | Surcharge |
|---|---|---|
| Ressources en lecture seule (thèmes, shaders, `es_systems.cfg`...) | `/usr/share/esne` | `ESNE_SHARE_DIR` |
| Config (`esne.conf`, `es_settings.cfg`) | `~/.config/esne` | `ESNE_CONFIG_DIR` ou `XDG_CONFIG_HOME` |
| Données (roms, bios, saves, screenshots...) | `~/esne` | `ESNE_DATA_DIR` |
| Logs | `~/.local/state/esne/logs` | `ESNE_STATE_DIR` ou `XDG_STATE_HOME` |

`emulationstation.ini` (hérité d'ES) peut encore surcharger chaque dossier.

**Lanceur Python** (`es-launcher`): config `~/.config/esne/esne.conf`, données `~/esne/`, cache `~/.cache/esne/`
(`ESNE_CONFIG_DIR`, `ESNE_DATA_DIR`, `ESNE_CACHE_DIR`).
`paths.py` connaît aussi `share` (`ESNE_SHARE_DIR`) et `state` (`ESNE_STATE_DIR`), comme le frontend.

## Dépendances d'exécution (Arch / CachyOS)
Pour les jeux libretro, `es-launcher` a besoin de:
```bash
sudo pacman -S --needed retroarch libretro-core-info libretro-snes9x \
    retroarch-assets-ozone retroarch-assets-xmb retroarch-assets-glui \
    libretro-shaders-slang libretro-overlays
```
Les `retroarch-assets-*` fournissent les icônes et polices du menu RetroArch (sans eux il s'affiche avec des ressources
manquantes). Aucun paquet autoconfig n'est nécessaire: `es-launcher` utilise le pilote joypad `sdl2`.

Raccourcis manette en jeu (réglables: `hotkey_enable`, `hotkey_exit`, `hotkey_menu`):
**Select + Start** quitte le jeu et revient à ES (aussi pour les émulateurs autonomes: `es-launcher` surveille la manette et ferme l'émulateur), **Select + R3** ouvre le menu RetroArch.
Options par système/jeu dans ES (ratio, shaders, lissage, rewind, pilote vidéo Vulkan/OpenGL...): voir `PARITY.md`.

## Bezels (décorations)
Un seul bezel par système, celui de The Bezel Project. Menu ES **Mises à jour → The Bezel Project**: ouvrir un système puis INSTALL (ou UPDATE / REMOVE). `esctl thebezelproject install snes` télécharge seulement l'image du système (`~/esne/decorations/thebezelproject/systems/snes.png`).
En jeu, `es-launcher` pose l'image en overlay RetroArch et cadre le jeu dans la zone transparente (le réglage de ratio d'ES est alors ignoré, comme en « auto »). Option **Decoration set** (global, système ou jeu): Auto (= The Bezel Project s'il est installé pour le système), Aucun, ou un jeu de décorations; le réglage du système prime sur le global.
La zone de jeu est détectée dans l'image (décodeur PNG intégré, résultat mis en cache; `python-pillow` est utilisé s'il est installé, ou un fichier `.png.info` si présent). L'image est toujours affichée en plein écran; si l'écran n'a pas son ratio (16:9 sur un écran 16:10), elle est étirée et le jeu garde les proportions de sa fenêtre. Au-delà de 25 % d'écart (21:9...), le bezel est ignoré sauf option STRETCH BEZELS sur Oui.

## Clés de scraping
Rien n'est compilé ni empaqueté. `es-genconfig` crée `~/.config/esne/keys.conf` (mode 600) avec un modèle commenté: décommente et remplis `SCREENSCRAPER_DEV_LOGIN`, `GAMESDB_APIKEY`, `CHEEVOS_DEV_LOGIN`..., puis redémarre ES. Un scraper dont la clé manque n'apparaît pas dans le menu. Ce fichier ne doit jamais être commité. Tes identifiants personnels (compte ScreenScraper, RetroAchievements) se saisissent dans les menus d'ES.

## Thème et jeu libre
Le paquet ajoute **ES-NE** au menu des applications (catégorie Jeux, icône ES), en plus de l'entrée de session de connexion.
Le paquet livre le thème **Carbon** (RetroPie) dans `/usr/share/esne/themes`: ES le choisit seul tant qu'aucun autre thème n'est sélectionné (menu Interface utilisateur → Thème). Tes propres thèmes vont dans `~/esne/themes`.
Le système **Ports** lance des scripts `.sh` (`~/esne/roms/ports/`). `es-genconfig` y crée `SuperTux.sh` si SuperTux est installé (dépendance du paquet) et n'écrase jamais un fichier existant; la liste est dans `src/esne/data/ports.yml` (complétable par `~/.config/esne/ports.yml`).

## Générer `es_systems.cfg`
```bash
es-genconfig                    # écrit ~/.config/esne/es_systems.cfg (tous les systèmes du catalogue) + dossiers de roms
es-genconfig --installed-only   # seulement les systèmes dont un core libretro est installé
es-genconfig --stdout           # affiche es_systems.cfg sans rien écrire
```
`es-genconfig` écrit aussi `es_features.cfg` (options par système/jeu: ratio, lissage, rewind, sauvegarde auto, pixel perfect,
shaders) et crée les jeux de shaders dans `~/esne/shaders/configs/` pour les presets libretro installés
(`libretro-shaders-slang`). Les systèmes viennent de `src/esne/data/systems.yml` (complété par `~/.config/esne/systems.yml`). Mets tes roms dans
`~/esne/roms/<système>/`; ES masque les systèmes vides.

## Systèmes et émulateurs
24 systèmes: consoles 8/16 bits à la GameCube, PSP, PS2/PS3, Wii/Wii U, Switch, Xbox, plus `steam` et `windows`.
- **libretro** (NES à PS1, N64, PSP, arcade...): cores choisis dans `systems.yml`.
- **Autonomes** (décrits dans `emulators.yml`, lancés par `generators/standalone.py`): Dolphin (GameCube, Wii), PCSX2 (PS2),
  RPCS3 (PS3), Cemu (Wii U), Eden ou Ryujinx (Switch), xemu (Xbox), Steam (fichiers `.steam` contenant l'appid),
  Wine ou umu-run (`windows`). Ils se lancent en plein écran sans interface; leurs réglages se font encore dans leur propre configuration.
  **PCSX2** (manette et réglages d'ES validés en jeu avec Final Fantasy XII, AppImage; après une mise à jour du paquet, relancer `es-genconfig` pour voir les nouvelles options, ce que fait déjà la session ES-NE): ES-NE réécrit les sections `[Pad1]`/`[Pad2]` de `~/.config/PCSX2/inis/PCSX2.ini` (manettes désignées par numéro SDL, pas de GUID) et applique API graphique, résolution, ratio, vsync et FXAA. Lancer PCSX2 une fois à la main avant (assistant, BIOS dans `~/esne/bios/ps2`).
  **RPCS3** (écrit, non testé): ES-NE écrit `input_configs/global/Default.yml` (gestionnaire SDL, une entrée par manette) et applique API graphique, résolution, ratio et vsync à `config.yml`. Lancer RPCS3 une fois à la main avant (firmware, configuration). Un dossier `Nom.ps3` est lancé par son `EBOOT.BIN`.
  **Eden** (validé en jeu, 2 manettes PS4, AppImage): configure la manette du joueur 1 dans Eden une fois; ES-NE recopie ce mappage vers les autres manettes du même modèle, avec le GUID que voit Eden (celui d'ES, CRC du nom à zéro) (`qt-config.ini`, option `AUTOCONFIGURE CONTROLLERS`). Réglages graphiques d'Eden non gérés.
  **Cemu** fait exception (validé en jeu: Mario Kart 8, 2 manettes PS4): ES-NE génère les profils « Wii U Pro Controller » (`controllerProfiles/controllerN.xml`) depuis les manettes d'ES et applique l'option `GRAPHICS API` (Vulkan/OpenGL) à `settings.xml`. Lancer Cemu une fois à la main avant (assistant de premier démarrage, clés et dossier MLC) et configurer une fois la manette dans Cemu: ES (SDL2) et Cemu (SDL3) ne calculent pas le même GUID, ES-NE reprend celui que Cemu a enregistré pour le même modèle. AppImage (`~/.local/bin/Cemu*.AppImage`), paquet ou Flatpak sont détectés; l'option `AUTOCONFIGURE CONTROLLERS` permet de garder son propre mapping.
Un émulateur absent donne l'erreur 204 avec le nom du paquet à installer. Xbox 360 n'est pas inclus (aucun émulateur Linux utilisable).

## Compiler le frontend
```bash
git clone --recurse-submodules https://github.com/JyuHo/ES-NE.git
cd ES-NE/third_party/emulationstation
cmake -B build -DESNE=ON -DGL=ON
cmake --build build -j"$(nproc)"
```
Dépendances de build: SDL2, SDL2_mixer, FreeImage, FreeType, cURL, RapidJSON, LibVLC, ALSA (voir `docs/UPSTREAM.md`).
Après un `git pull`, pense à `git submodule update --init`.

## `esctl`
Outil système qu'ES appelle à la place des `batocera-*` (voir `docs/ESCTL_CONTRACT.md`):
```bash
esctl commands            # commandes utilisables sur cette machine
esctl has audio           # code 0 si disponible
esctl resolution listModes
esctl audio list
esctl timezone get          # set peut demander une règle polkit
esctl padsinfo              # manettes et batteries, au format lu par ES
```
Sans installation: `PYTHONPATH=src python -m esne.esctl commands`.

## Dev (lanceur Python et esctl)
```bash
python -m venv .venv && . .venv/bin/activate
pip install pytest && pytest        # les tests trouvent src/ tout seuls
pip install -e '.[dev]'              # installe aussi es-launcher et esctl (compile evdev)
```

## Licence
GPL-3.0-or-later. Voir `LICENSE` et `docs/LICENSING.md`. Le fork d'ES est sous MIT.

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
| Frontend ES (fork `emulationstation-esne`, branche `esne`) | 🚧 6 patchs: option `-DESNE=ON`, chemins XDG, `LinuxApiSystem`, appels audio. **Pas encore compilé en entier ni lancé** |
| `es-launcher` | 🚧 CLI compatible ES, catalogue de systèmes, RetroArch (config complémentaire); testé avec un faux RetroArch, pas encore avec un vrai jeu |
| `esctl` | 🚧 `has`, `version`, `resolution`, `audio`, `config lsoutputs` écrits et testés (45 tests); **pas encore essayé sur une vraie machine**. Reste: `timezone`, `systems`, `padsinfo`, `thebezelproject`, `info`, `swissknife`. Contrat dans `docs/ESCTL_CONTRACT.md` |
| Paquets (`PKGBUILD`), session | ❌ |

Détails: `docs/ROADMAP.md` (jalons), `PARITY.md` (parité avec RetroBat), `docs/UPSTREAM.md` (patchs d'ES).

## Chemins
**Frontend ES** (`-DESNE=ON`):

| Rôle | Chemin par défaut | Surcharge |
|---|---|---|
| Ressources en lecture seule (thèmes, shaders, `es_systems.cfg`...) | `/usr/share/esne` | `ESNE_SHARE_DIR` |
| Config (`esne.conf`, `es_settings.cfg`) | `~/.config/esne` | `ESNE_CONFIG_DIR` ou `XDG_CONFIG_HOME` |
| Données (roms, bios, saves, screenshots...) | `~/.local/share/esne` | `ESNE_DATA_DIR` ou `XDG_DATA_HOME` |
| Logs | `~/.local/state/esne/logs` | `ESNE_STATE_DIR` ou `XDG_STATE_HOME` |

`emulationstation.ini` (hérité d'ES) peut encore surcharger chaque dossier.

**Lanceur Python** (`es-launcher`): config `~/.config/esne/esne.conf`, données `~/.local/share/esne/`, cache `~/.cache/esne/`
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
**Select + Start** quitte le jeu et revient à ES, **Select + R3** ouvre le menu RetroArch.

## Générer `es_systems.cfg`
```bash
es-genconfig                    # écrit ~/.config/esne/es_systems.cfg (tous les systèmes du catalogue) + dossiers de roms
es-genconfig --installed-only   # seulement les systèmes dont un core libretro est installé
es-genconfig --stdout           # affiche le fichier
```
Les systèmes viennent de `src/esne/data/systems.yml` (complété par `~/.config/esne/systems.yml`). Mets tes roms dans
`~/.local/share/esne/roms/<système>/`; ES masque les systèmes vides.

## Systèmes et émulateurs
24 systèmes: consoles 8/16 bits à la GameCube, PSP, PS2/PS3, Wii/Wii U, Switch, Xbox, plus `steam` et `windows`.
- **libretro** (NES à PS1, N64, PSP, arcade...): cores choisis dans `systems.yml`.
- **Autonomes** (décrits dans `emulators.yml`, lancés par `generators/standalone.py`): Dolphin (GameCube, Wii), PCSX2 (PS2),
  RPCS3 (PS3), Cemu (Wii U), Eden ou Ryujinx (Switch), xemu (Xbox), Steam (fichiers `.steam` contenant l'appid),
  Wine ou umu-run (`windows`). Ils se lancent en plein écran sans interface; leurs réglages se font encore dans leur propre configuration.
Un émulateur absent donne l'erreur 204 avec le nom du paquet à installer. Xbox 360 n'est pas inclus (aucun émulateur Linux utilisable).

## Compiler le frontend
```bash
git clone --recurse-submodules https://github.com/JyuHo/ES-NE.git
cd ES-NE/third_party/emulationstation
cmake -B build -DESNE=ON -DGL=ON
cmake --build build -j"$(nproc)"
```
`-DGL=ON` (OpenGL bureau) est à confirmer au premier build complet. Les dépendances (SDL2, SDL2_mixer, FreeImage,
FreeType, cURL, RapidJSON, LibVLC, ALSA...) ne sont pas encore validées sur Arch/CachyOS.

## `esctl`
Outil système qu'ES appelle à la place des `batocera-*` (voir `docs/ESCTL_CONTRACT.md`):
```bash
esctl commands            # commandes utilisables sur cette machine
esctl has audio           # code 0 si disponible
esctl resolution listModes
esctl audio list
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

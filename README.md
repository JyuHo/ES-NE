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
| Frontend ES (fork `emulationstation-esne`, branche `esne`) | 🚧 5 patchs poussés: option `-DESNE=ON`, chemins XDG, `LinuxApiSystem`. **Pas encore compilé en entier ni lancé** |
| `es-launcher` | 🚧 squelette: config en couches, CLI, générateur RetroArch minimal |
| `esctl` | ❌ non écrit. Contrat dans `docs/ESCTL_CONTRACT.md` |
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
Reste à aligner sur le frontend: les dossiers `share` et `state` ne sont pas encore connus de `paths.py`.

## Compiler le frontend
```bash
git clone --recurse-submodules https://github.com/JyuHo/ES-NE.git
cd ES-NE/third_party/emulationstation
cmake -B build -DESNE=ON -DGL=ON
cmake --build build -j"$(nproc)"
```
`-DGL=ON` (OpenGL bureau) est à confirmer au premier build complet. Les dépendances (SDL2, SDL2_mixer, FreeImage,
FreeType, cURL, RapidJSON, LibVLC, ALSA...) ne sont pas encore validées sur Arch/CachyOS.

## Dev (lanceur Python)
```bash
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]' && pytest
```

## Licence
GPL-3.0-or-later. Voir `LICENSE` et `docs/LICENSING.md`. Le fork d'ES est sous MIT.

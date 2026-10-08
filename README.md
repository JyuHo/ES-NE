# ES-NE

Version standalone de [batocera-emulationstation](https://github.com/batocera-linux/batocera-emulationstation)
pour Arch Linux / CachyOS, avec les options de RetroBat, **sans aucune dépendance à Batocera**.

- Arborescence Linux classique (XDG), pas de `/userdata`
- Nouveau lanceur `es-launcher` (remplace `emulatorlauncher` / `batocera-configgen`)
- Même format de clés que `batocera.conf` (`global.ratio`, `snes.core`, `snes["jeu.zip"].shaderset`)
  pour rester compatible avec les menus d'ES
- Définitions déclaratives (YAML) des systèmes, émulateurs et features

## Statut
M0/M1 en cours : squelette, config en couches, générateur RetroArch minimal. Voir `PARITY.md` et `docs/ROADMAP.md`.

## Chemins
| Rôle | Chemin |
|---|---|
| Config | `~/.config/esne/esne.conf` |
| Données (roms, bios, saves...) | `~/.local/share/esne/` |
| Cache | `~/.cache/esne/` |
Surcharge possible via `ESNE_CONFIG_DIR`, `ESNE_DATA_DIR`, `ESNE_CACHE_DIR`.

## Dev
```bash
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]' && pytest
```

## Licence
À définir (voir section Licence de `docs/ROADMAP.md`).

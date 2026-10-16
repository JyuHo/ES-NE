# Code et données tierces
| Fichier ES-NE | Source | Commit | Licence |
|---|---|---|---|
| `third_party/emulationstation` (sous-module) | [batocera-linux/batocera-emulationstation](https://github.com/batocera-linux/batocera-emulationstation), via le fork `JyuHo/emulationstation-esne` | base `8d2b39446`, branche `esne` | MIT (© 2014 Alec Lofquist) |
| `es-app/src/LinuxApiSystem.{h,cpp}` (dans le fork) | écrits pour ES-NE; règle d'affichage des menus décorations/shaders reprise de `Win32ApiSystem` (même dépôt) | `6e72066` | MIT (licence du fork) |
| `external/pugixml` (sous-module d'ES) | [zeux/pugixml](https://github.com/zeux/pugixml) | épinglé par le fork | MIT |
| Digger (jeu de démonstration du système ports, **téléchargé à la demande** par `es-genconfig --install-port digger`, jamais copié ni redistribué) | [catalogue PortMaster](https://github.com/PortsMaster/PortMaster-New), source du jeu: [sobomax/digger](https://github.com/sobomax/digger) | version du catalogue au moment du téléchargement | GPL-2.0 (le zip contient `LICENSE.GPL2.txt`) |
| `themes/es-ne/fonts/Rajdhani-*.ttf` (police du thème ES-NE) | [Rajdhani](https://fonts.google.com/specimen/Rajdhani), Indian Type Foundry | téléchargée depuis Google Fonts (octobre 2026) | SIL Open Font License 1.1 (`themes/es-ne/fonts/OFL.txt`) |
| `themes/es-ne/art/logo-src/*.svg` (logos de consoles du thème ES-NE) | [HVR88/Monochrome-Gaming-Logos](https://github.com/HVR88/Monochrome-Gaming-Logos) | HEAD au moment de la copie (octobre 2026) | pas de licence formelle; le README autorise l'usage libre avec mention et lien, et signale que beaucoup d'images sont des marques de leurs propriétaires (restrictions possibles en usage commercial). ES-NE est non commercial; voir `themes/es-ne/art/logo-src/README.md` |

Aucun émulateur n'est copié ni redistribué par ES-NE. Redream (Dreamcast, logiciel propriétaire gratuit, [redream.io](https://redream.io)) et Xenia Canary (Xbox 360, fork Linux natif [peerloomllc/xenia-canary](https://github.com/peerloomllc/xenia-canary)) sont installés par l'utilisateur; ES-NE ne fait que les lancer et écrire leurs réglages (`redream.cfg`; options de ligne de commande et `xconfig.settings` pour Xenia, octets relevés sur un fichier réel).

Aucun code de `batocera-configgen` ni de `batocera.linux` n'a été copié à ce jour. Si ça arrive, ajouter ici une ligne par fichier
(source, commit, licence exacte du fichier, voir `docs/LICENSING.md`).

## Batocera (GPL-3.0-or-later)
Les noms de sections, de clés et de valeurs de `PCSX2.ini` utilisés par `generators/pcsx2.py` (ainsi que la liste d'options graphiques) ont été relevés dans le générateur PCSX2 de Batocera (https://github.com/batocera-linux/batocera.linux, `python-src/batocera-launch-pcsx2`). Idem pour `generators/rpcs3.py` (`python-src/batocera-launch-rpcs3`: `config.yml`, `input_configs/global/Default.yml`). Le code est réécrit pour ES-NE; seules les informations de format sont reprises. Idem pour `generators/xemu.py` (clés de `xemu.toml`: `[sys.files]`, `[input.bindings]`; xemu n'écrit que les clés non défaut) : informations de format seulement.

Le lanceur Steam (`steamrun.py`, `steam.py`) et l'installation de cores (`cores.py`, `install_core.py`, aides `esne-install-core*`) sont écrits pour ES-NE, sans code tiers. Les paquets de cores AUR ne sont ni copiés ni redistribués: ils sont construits sur la machine de l'utilisateur à sa demande.

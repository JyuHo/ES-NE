# Code et données tierces
| Fichier ES-NE | Source | Commit | Licence |
|---|---|---|---|
| `third_party/emulationstation` (sous-module) | [batocera-linux/batocera-emulationstation](https://github.com/batocera-linux/batocera-emulationstation), via le fork `JyuHo/emulationstation-esne` | base `5b1764c9a`, branche `esne` | MIT (© 2014 Alec Lofquist) |
| `es-app/src/LinuxApiSystem.{h,cpp}` (dans le fork) | écrits pour ES-NE; règle d'affichage des menus décorations/shaders reprise de `Win32ApiSystem` (même dépôt) | `b935f4c` | MIT (licence du fork) |
| `external/pugixml` (sous-module d'ES) | [zeux/pugixml](https://github.com/zeux/pugixml) | épinglé par le fork | MIT |
| thème Carbon (`/usr/share/esne/themes/es-theme-carbon`) | [RetroPie/es-theme-carbon](https://github.com/RetroPie/es-theme-carbon), téléchargé par le `PKGBUILD` à la construction | branche par défaut | aucun fichier de licence dans le dépôt: **non redistribué dans ce dépôt** |
| Digger (jeu de démonstration du système ports, **téléchargé à la demande** par `es-genconfig --install-port digger`, jamais copié ni redistribué) | [catalogue PortMaster](https://github.com/PortsMaster/PortMaster-New), source du jeu: [sobomax/digger](https://github.com/sobomax/digger) | version du catalogue au moment du téléchargement | GPL-2.0 (le zip contient `LICENSE.GPL2.txt`) |

Aucun émulateur n'est copié ni redistribué par ES-NE. Redream (Dreamcast, logiciel propriétaire gratuit, [redream.io](https://redream.io)) et Xenia Canary (Xbox 360, fork Linux natif [peerloomllc/xenia-canary](https://github.com/peerloomllc/xenia-canary)) sont installés par l'utilisateur; ES-NE ne fait que les lancer et écrire leurs réglages (`redream.cfg`; options de ligne de commande et `xconfig.settings` pour Xenia, octets relevés sur un fichier réel).

Aucun code de `batocera-configgen` ni de `batocera.linux` n'a été copié à ce jour. Si ça arrive, ajouter ici une ligne par fichier
(source, commit, licence exacte du fichier, voir `docs/LICENSING.md`).

## Batocera (GPL-3.0-or-later)
Les noms de sections, de clés et de valeurs de `PCSX2.ini` utilisés par `generators/pcsx2.py` (ainsi que la liste d'options graphiques) ont été relevés dans le générateur PCSX2 de Batocera (https://github.com/batocera-linux/batocera.linux, `python-src/batocera-launch-pcsx2`). Idem pour `generators/rpcs3.py` (`python-src/batocera-launch-rpcs3`: `config.yml`, `input_configs/global/Default.yml`). Le code est réécrit pour ES-NE; seules les informations de format sont reprises. Idem pour `generators/xemu.py` (clés de `xemu.toml`: `[sys.files]`, `[input.bindings]`; xemu n'écrit que les clés non défaut) : informations de format seulement.

Le lanceur Steam (`steamrun.py`, `steam.py`) et l'installation de cores (`cores.py`, `install_core.py`, aides `esne-install-core*`) sont écrits pour ES-NE, sans code tiers. Les paquets de cores AUR ne sont ni copiés ni redistribués: ils sont construits sur la machine de l'utilisateur à sa demande.

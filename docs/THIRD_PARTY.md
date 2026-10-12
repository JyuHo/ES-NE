# Code et données tierces
| Fichier ES-NE | Source | Commit | Licence |
|---|---|---|---|
| `third_party/emulationstation` (sous-module) | [batocera-linux/batocera-emulationstation](https://github.com/batocera-linux/batocera-emulationstation), via le fork `JyuHo/emulationstation-esne` | base `5b1764c9a`, branche `esne` | MIT (© 2014 Alec Lofquist) |
| `es-app/src/LinuxApiSystem.{h,cpp}` (dans le fork) | écrits pour ES-NE; règle d'affichage des menus décorations/shaders reprise de `Win32ApiSystem` (même dépôt) | `b935f4c` | MIT (licence du fork) |
| `external/pugixml` (sous-module d'ES) | [zeux/pugixml](https://github.com/zeux/pugixml) | épinglé par le fork | MIT |
| thème Carbon (`/usr/share/esne/themes/es-theme-carbon`) | [RetroPie/es-theme-carbon](https://github.com/RetroPie/es-theme-carbon), téléchargé par le `PKGBUILD` à la construction | branche par défaut | aucun fichier de licence dans le dépôt: **non redistribué dans ce dépôt** |
| SuperTux (dépendance du paquet, jamais copié) | paquet `supertux` d'Arch | — | GPL-3.0-or-later |

Aucun code de `batocera-configgen` ni de `batocera.linux` n'a été copié à ce jour. Si ça arrive, ajouter ici une ligne par fichier
(source, commit, licence exacte du fichier, voir `docs/LICENSING.md`).

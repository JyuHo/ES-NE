# Licence et réutilisation de code

ES-NE est distribué sous **GPL-3.0-or-later**.

## Règles pour copier du code
1. Avant de reprendre un fichier de batocera.linux / batocera-configgen, vérifier son en-tête
   (GPL-3.0-only vs GPL-3.0-or-later). Un fichier "only" reste utilisable, mais il faut conserver sa mention.
2. Conserver les en-têtes de copyright et auteurs d'origine dans les fichiers repris.
3. Noter chaque emprunt dans `docs/THIRD_PARTY.md` (source, commit, fichier, licence).
4. Ne pas copier de code sous licence incompatible (GPL-2.0-only, propriétaire, "non commercial").
   Les données (BIOS, thèmes, shaders) ont chacune leur licence: à vérifier séparément.
5. EmulationStation (fork) est sous MIT: compatible, à garder avec sa mention.

## Fichiers ajoutés dans le fork d'EmulationStation
Le fork (`third_party/emulationstation`) est sous licence MIT. Les fichiers qu'on y ajoute (par exemple
`LinuxApiSystem.h` et `LinuxApiSystem.cpp`) portent `SPDX-License-Identifier: MIT`, pour rester cohérents avec le dépôt qui
les contient et permettre de proposer des changements à upstream. La MIT est compatible avec la GPL: la distribution d'ES-NE
dans son ensemble reste sous GPL-3.0-or-later.

## En-tête conseillé pour les nouveaux fichiers
Dans ce dépôt (Python, scripts, docs):

    # SPDX-License-Identifier: GPL-3.0-or-later

Dans le fork d'ES (C++): `// SPDX-License-Identifier: MIT`.

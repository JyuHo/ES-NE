# Suivi d'upstream : batocera-emulationstation

ES-NE embarque un fork d'EmulationStation comme sous-module git.

| Élément | Valeur |
|---|---|
| Upstream | https://github.com/batocera-linux/batocera-emulationstation |
| Fork ES-NE | https://github.com/JyuHo/emulationstation-esne |
| Chemin du sous-module | `third_party/emulationstation` |
| Branche de travail | `esne` |
| Licence | MIT (garder `LICENSE` et les mentions d'origine) |

## Base épinglée
À remplir lors de la création de la branche `esne` :

| Champ | Valeur |
|---|---|
| Branche upstream | `TODO` (ex: `master`) |
| Tag / commit de base | `TODO` |
| Date | `TODO` |
| Sous-modules d'ES | initialisés avec `--recursive` |

## Remotes du fork (dans `third_party/emulationstation`)
```bash
git remote add upstream https://github.com/batocera-linux/batocera-emulationstation.git
git fetch upstream
```

## Règles pour les patchs
1. Tous les changements vivent sur la branche `esne`, jamais sur la branche par défaut du fork.
2. Un commit = un changement ciblé (chemins, remplacement d'un appel `batocera-*`, option CMake...).
3. Préfixer les messages : `esne: paths: ...`, `esne: syscalls: ...`, `esne: build: ...`.
4. Ne pas reformater de code qu'on ne modifie pas (garde les rebases propres).
5. Un changement générique (bugfix) peut être proposé à upstream : le mettre dans une branche séparée.

## Mettre à jour depuis upstream
```bash
cd third_party/emulationstation
git fetch upstream
git checkout esne
git rebase upstream/<branche-ou-tag>      # résoudre les conflits commit par commit
git push --force-with-lease origin esne
cd ../..
git add third_party/emulationstation
git commit -m "Mise à jour d'ES: <nouveau commit upstream>"
```
Mettre ensuite à jour le tableau « Base épinglée » ci-dessus.

## Cloner ES-NE
```bash
git clone --recurse-submodules https://github.com/JyuHo/ES-NE.git
# ou, après un clone simple :
git submodule update --init --recursive
```

## Journal des patchs
| Commit | Catégorie | Description |
|---|---|---|
| | | |

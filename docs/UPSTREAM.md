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
| Champ | Valeur |
|---|---|
| Branche upstream | `master` |
| Commit de base | `5b1764c9a` (« Merge pull request #2239 from batocera-linux/fixfribidimultilines ») |
| Date d'épinglage | 2026-10-12 |
| Branche du fork | `esne` (8 commits au-dessus de la base) |
| Sous-modules d'ES | `external/pugixml` (initialisé avec `--recursive`) |

Le sous-module d'ES-NE doit pointer vers un commit **présent sur GitHub**. Après chaque `git am` / rebase local dans
`third_party/emulationstation`, pousser `esne` **avant** de commiter le nouveau pointeur dans ES-NE, sinon un
`git clone --recurse-submodules` échoue sur le sous-module.

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

## Variante de build `ESNE`
`-DESNE=ON` définit `ESNE` et `ESNE_SHARE_DIR` (défaut `/usr/share/esne`). Elle est exclusive avec `BATOCERA`, `RETROBAT`
et `WIN32` : `ESNE` n'active pas le code propre à l'OS Batocera. Détails dans `docs/AUDIT_ANALYSIS.md`.

## Journal des patchs
Hashes de la branche `esne` du fork.

| Commit | Catégorie | Description |
|---|---|---|
| `99b711a` | build | option CMake `-DESNE=ON`, `ESNE_SHARE_DIR`, exclusive avec BATOCERA/RETROBAT/WIN32 |
| `e142310` | paths | disposition XDG dans `Paths.cpp` (`ESNE_{CONFIG,DATA,STATE,SHARE}_DIR`) |
| `e28606c` | paths | ne plus lire `batocera.arch` ni réécrire `/recalbox` sous ESNE |
| `67167a7` | build | définir `X86`/`X86_64` depuis `CMAKE_SYSTEM_PROCESSOR` |
| `b935f4c` | syscalls | `LinuxApiSystem`: traduction `batocera-*` → `esctl`, menus conditionnés, mises à jour désactivées, Kodi et suspend directs |
| `3bdea9b` | syscalls | les 4 fonctions audio (`get`/`set` périphérique et profil) passent par `executeScript` / `executeEnumerationScript` au lieu de `popen`/`system` |
| `3dfc4be` | menus | crée `esne.conf` au premier lancement (sinon aucun réglage ne s'enregistre), entrée « QUIT EMULATIONSTATION » dans le menu Quitter, menu disposition clavier masqué (`batocera-keyboard`) |
| `f074529` | i18n | applique `system.language` au démarrage (Batocera l'exporte via ses scripts d'init) et cherche les `.mo` à côté de l'exécutable, quel que soit le dossier courant |

## Vérifications faites sur ces patchs
- Vérification de syntaxe (`g++ -fsyntax-only`) de `Paths.cpp`, `Platform.cpp`, `ThemeData.cpp`, `ApiSystem.cpp` et `LinuxApiSystem.cpp` en variantes `ESNE`, `BATOCERA` et par défaut.
- Test d'exécution des chemins (`Paths`) et de la logique de `LinuxApiSystem` (traduction, recherche dans le `PATH`, affichage conditionnel des menus avec un faux `esctl`).
- **Non fait**: build complet d'ES, lancement, test des menus dans l'interface.

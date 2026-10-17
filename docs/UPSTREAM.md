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
| Commit de base | `8d2b39446` (« update po », rebase du 2026-10-15; la base précédente était `5b1764c9a`) |
| Date d'épinglage | 2026-10-15 |
| Branche du fork | `esne` (38 commits au-dessus de la base) |
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
| `6921537` | build | option CMake `-DESNE=ON`, `ESNE_SHARE_DIR`, exclusive avec BATOCERA/RETROBAT/WIN32 |
| `765f90b` | paths | disposition XDG dans `Paths.cpp` (`ESNE_{CONFIG,DATA,STATE,SHARE}_DIR`) |
| `feca76e` | paths | ne plus lire `batocera.arch` ni réécrire `/recalbox` sous ESNE |
| `cac1569` | build | définir `X86`/`X86_64` depuis `CMAKE_SYSTEM_PROCESSOR` |
| `6e72066` | syscalls | `LinuxApiSystem`: traduction `batocera-*` → `esctl`, menus conditionnés, mises à jour désactivées, suspend direct; Kodi retiré (absent d'ES-NE, entrées masquées) |
| `9bc4a88` | syscalls | les 4 fonctions audio (`get`/`set` périphérique et profil) passent par `executeScript` / `executeEnumerationScript` au lieu de `popen`/`system` |
| `1e5845a` | menus | crée `esne.conf` au premier lancement (sinon aucun réglage ne s'enregistre), entrée « QUIT EMULATIONSTATION » dans le menu Quitter, menu disposition clavier masqué (`batocera-keyboard`) |
| `acd075d` | i18n | applique `system.language` au démarrage (Batocera l'exporte via ses scripts d'init) et cherche les `.mo` à côté de l'exécutable, quel que soit le dossier courant |
| `9152c03` | scrapers | les clés développeur (ScreenScraper, TheGamesDB...) viennent d'un `esne-keys.cmake` non versionné (modèle: `esne-keys.cmake.example`) |
| `5b3352e` | scrapers | modèle de clés entièrement commenté (les valeurs factices étaient compilées et faisaient apparaître ScreenScraper sans identifiants valides) |
| `fbe1a73` | lancement | crée `<state>/logs` au démarrage: ES redirige la sortie de l'émulateur dedans, et le shell abandonnait avec le code 1 sans lancer `es-launcher` si le dossier manquait |
| `eb881ba` | arrêt / redémarrage | `systemctl reboot` / `poweroff` à la place de `shutdown` et des fichiers `/tmp/*.please`; « redémarrer ES » se relance par `execv` (mêmes arguments) |
| `a89e170` | redémarrage requis | après un réglage qui demande un redémarrage (langue...), ES propose de se relancer tout de suite |
| `a53a4e1` | Zaparoo | pas de sondage de `127.0.0.1:7497` (ni d'erreur de connexion à chaque démarrage) sauf si `zaparoo.enabled=1` dans `esne.conf` |
| `84d8fca` | menu Quitter | retire « mettre en veille » et « extinction rapide » (l'extinction rapide ne fait qu'éviter la sauvegarde des métadonnées) |
| `af121ce` | décorations | un bezel par système: jeu de décorations « THE BEZEL PROJECT » (aperçu = image du système); pas de bezel par jeu |
| `21e0b24` | chemins | dossier de données par défaut `~/esne` (au lieu de `~/.local/share/esne`) |
| `619d295` | clés | clés de développeur lues à l'exécution dans `~/.config/esne/keys.conf` (`EsneKeys.h`); scrapers à clé et RetroAchievements proposés seulement si la clé est renseignée |
| `d3176ec` | scrapers | repli sur le premier scraper disponible si celui qui est configuré n'a pas de clé (évitait un SIGSEGV au scrape) |
| `980fde0`, `e43dce0` | lancement | code de sortie 205 (core manquant): lit `/tmp/esne-missing-core` (core, paquet, source), propose l'installation (`GuiLoading` puis `ApiSystem::installLibretroCore` → `esctl install-core`); variante AUR |
| `8de5495` | menus | disposition du clavier via `esctl keyboard get/list/set` (menu affiché si `esctl has keyboard`) |
| `17d6c20` | menus | Kodi retiré: `isScriptingSupported(KODI)` renvoie faux, entrées « KODI » masquées même si `kodi` est installé |
| `218a886` | ressources | écran de démarrage (`logo.png`), `splash.svg` et `window_icon_256.png` remplacés par ceux d'ES-NE; `splash_batocera.svg` supprimé (visuels Batocera et icône « ES » d'EmulationStation retirés) |
| `035e6d0`, `6d64e5e` | i18n | traductions françaises complètes (`.po` + `.pot`, 1282 chaînes) |
| `643df40` | i18n | 17 chaînes (redémarrage d'ES, installation d'un core, AUR, Wi-Fi, HDR, indexation, volume au stick droit, MSAA, limite d'images) traduites dans les 32 autres langues; seules les chaînes vides sont remplies; `eu_ES`: deux `%S` corrigés en `%s` |
| `af40479` | ES-NE | thème `es-ne` choisi par défaut (`ThemeSet`, sous `#if ESNE`), pour pouvoir retirer Carbon du paquet |
| `cfa9c58` | ES-NE | vue système: l'aide affiche le bouton select (menu d'accès rapide, déjà actif mais non indiqué) |
| `6e2d1fe` | ES-NE | menus `GuiSettings`: le bouton de validation (SELECT) est toujours dans l'aide (sous `#if ESNE`) |
| `5c94828` | ES-NE | vue système: l'aide « barre de navigation » utilise `BUTTON_BACK` (le bouton « b » littéral doublait l'icône de validation et la faisait disparaître) |
| `475da46` | ES-NE | `StoryboardAnimator`: une animation `repeat="forever"` seule est calée sur l'horloge globale (`SDL_GetTicks`), pour que le fond animé du thème reste continu d'une vue à l'autre (sous `#if ESNE`) |

## Ce qui reste de Batocera dans le frontend (état actuel)
- `updates.batocera.org`: sert seulement à la liste des thèmes téléchargeables (`themes.json`); surchargeable par `global.updates.url`.
  Les mises à jour du système (`UPGRADE`) et leur script GitHub ne sont jamais atteints: `LinuxApiSystem` désactive ce menu.
- Appels `batocera-*` directs de `GuiMenu.cpp`: plus aucun pour le clavier (remplacé par `esctl keyboard`). Les écrans de rotation et de splash sont
  dans la branche `BATOCERA`, jamais compilée en `ESNE`.
- Les autres commandes passent par `LinuxApiSystem::translateCommand` (`batocera-x` -> `esctl x`); les menus dont la commande `esctl` n'existe pas sont cachés.

## Vérifications faites sur ces patchs
- Vérification de syntaxe (`g++ -fsyntax-only`) de `Paths.cpp`, `Platform.cpp`, `ThemeData.cpp`, `ApiSystem.cpp` et `LinuxApiSystem.cpp` en variantes `ESNE`, `BATOCERA` et par défaut.
- Test d'exécution des chemins (`Paths`) et de la logique de `LinuxApiSystem` (traduction, recherche dans le `PATH`, affichage conditionnel des menus avec un faux `esctl`).
- Le build complet d'ES, son lancement et les menus ont ensuite été validés sur CachyOS (voir `README.md`, statut).

## Nettoyage des warnings (fork `esne`)

Compilation : 791 warnings -> 1. Changements notables : destructeurs virtuels, macro `LOG`
en expression, liste des scrapers initialisée à la demande (ordre d'initialisation statique),
`Paths::homePath` en statique local, `-Wno-sign-compare` (~230 warnings de style).
Bugs suspects laissés tels quels (comportement amont) : propriété thème « multiLine »
(TextComponent), `repeat = 1` (ThemeStoryboard), `mLastCursor = -9999` (ImageGridComponent).

## Rebase du 2026-10-15
Rebase de la branche `esne` sur le `master` de Batocera (`8d2b39446`), validé à l'usage sur CachyOS (menus, jeu, clavier, bezels): 8 conflits, tous mineurs (`#if ESNE` dans `GuiMenu.cpp`, menu du clavier, `.po`, splash). Le résultat compile en `-DESNE=ON` sans erreur ni warning. Nouveautés d'upstream reprises: HDR, réseaux Wi-Fi, affichage de droite à gauche, options masquées quand un réglage requis manque, corrections diverses; 8 chaînes françaises ajoutées. L'ancienne branche est gardée en local sous `esne-before-rebase` (hashes du journal ci-dessus mis à jour).

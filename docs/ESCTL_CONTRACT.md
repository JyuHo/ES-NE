# Contrat entre ES et `esctl`

`LinuxApiSystem` (frontend) ne connaît aucune commande système. Il applique deux règles, et `esctl`
(`src/esne/esctl/`, Python, bibliothèque standard uniquement) les honore.

## 1. Traduction des appels
Toute commande qui commence par `batocera-` (ou `/usr/bin/batocera-`) est exécutée via `esctl` :

| ES appelle | ES-NE exécute |
|---|---|
| `batocera-audio set 'X'` | `esctl audio set 'X'` |
| `batocera-resolution --screen "DP-1" listModes` | `esctl resolution --screen "DP-1" listModes` |
| `batocera-config lsoutputs` | `esctl config lsoutputs` |
| `batocera-es-swissknife --emukill` | `esctl swissknife --emukill` (le préfixe `es-` est retiré) |
| `batocera-es-thebezelproject list` | `esctl thebezelproject list` |

Les autres commandes (`uname -m`, `ping ...`) ne sont pas modifiées.

La traduction ne s'applique qu'aux appels qui passent par les méthodes virtuelles `executeScript` /
`executeEnumerationScript` d'`ApiSystem`. Les fonctions qui appellent `popen()` / `system()` directement ne sont
pas traduites: voir `docs/AUDIT_ANALYSIS.md` §1 pour la liste de celles qui restent.

## 2. Un menu `esctl` n'apparaît que si esctl le déclare utilisable
`esctl has <commande>` répond par le **code de sortie 0** si la commande existe **et** est utilisable sur cette machine
(par exemple `resolution` demande `xrandr` ou `wlr-randr`; `audio` demande `pactl`), autre chose sinon.
Si `esctl` est absent du `PATH`, tous ces menus sont masqués. Le frontend met le résultat en cache pour la durée du processus.
`esctl commands` liste les commandes utilisables (utile pour diagnostiquer).

Codes de sortie: `0` succès · `1` échec ou indisponible · `2` mauvais usage.

## 3. Commandes et formats
| Menu ES | `esctl has` | État | Détail |
|---|---|---|---|
| Version | `version` | ✅ | `esctl version`: une ligne (`<share>/esne.version`, sinon la version du package). `--extra`: nom de la distribution (`PRETTY_NAME`), ou rien |
| Résolution | `resolution` | ✅ | voir ci-dessous |
| Sortie audio | `audio` | ✅ | voir ci-dessous |
| (sorties vidéo) | — | ✅ | `esctl config lsoutputs`: noms des sorties connectées, une par ligne |
| BIOS | `systems` | ❌ | `systems [--filter <système>]`: lignes `> <système>` puis `<statut> <md5> <chemin>` (à relire dans `getBiosInformations`) |
| Manettes | `padsinfo` | ❌ | à relire dans `getPadsInfo` |
| Fuseau horaire | `timezone` | ❌ | `get`, `detect`, `set "<tz>"` |
| Bezels | `thebezelproject` | ❌ | `list`, `install <x>`, `remove <x>` |
| Hook gamelists | `preupdate-gamelists-hook` | ❌ | appelé avant la mise à jour des gamelists |

Appelés sans passer par `has` (donc à fournir dès qu'`esctl` est installé): `esctl info --full` ❌ (infos système) et
`esctl swissknife --emukill` ❌ (tuer l'émulateur).

### `esctl resolution [--screen SORTIE] <verbe>`
- `listModes`: une ligne par mode, **`ID:LIBELLÉ`**, du plus grand au plus petit. Le frontend découpe sur `:` : l'ID ne
  contient jamais `:`. Sans `--screen`: la sortie primaire, sinon la première connectée.
- `currentMode`: l'ID du mode actif.
- `setMode ID`: applique le mode (échoue si l'ID n'existe pas sur la sortie).
- ID: `LARGEURxHAUTEUR[i].FRÉQUENCE`, fréquence à 2 décimales (`1920x1080.60.00`, `1920x1080i.59.94`). Il est stocké
  dans `global.videomode` puis relu par le lanceur.
- Outils: `xrandr` (X11, ou XWayland en dernier recours) et `wlr-randr` (Wayland wlroots). Sous Wayland, `wlr-randr` est essayé en premier.
- **Limite**: KDE Plasma et GNOME sous Wayland ne sont pas pris en charge nativement (il faudrait `kscreen-doctor` et l'API de GNOME).
  `xrandr` via XWayland donne une liste de modes incomplète.

### `esctl audio <verbe>`
Format des listes: **`ID<TAB>LIBELLÉ`**, une seule tabulation par ligne (le frontend découpe sur la tabulation). L'ID `auto`
(« ne rien changer ») est toujours proposé en premier.
- `list`: les sorties (sinks `pactl`); l'ID est le nom stable du nœud (`alsa_output....`), pas son numéro.
- `get`: l'ID de la sortie par défaut. `set ID`: la définit (`auto` ne fait rien).
- `list-profiles`: profils de la carte de la sortie actuelle (profils indisponibles exclus). `get-profile`: le profil actif, ou `auto` sans carte.
  `set-profile ID`: l'applique à cette carte.
- Outil: `pactl >= 16` (`--format=json`), donc PulseAudio ou PipeWire avec `pipewire-pulse` (CachyOS).
- La carte d'une sortie est retrouvée par la propriété `alsa.card`, sinon par le nom (`alsa_output.X.profil` → `alsa_card.X`, `bluez_output.X.N` → `bluez_card.X`).
- Les flux déjà en lecture ne sont pas déplacés vers la nouvelle sortie.

## Vérification
- 45 tests Python (`pytest`) sur des sorties d'exemple de `xrandr`, `wlr-randr` et `pactl`, plus des sous-processus réels avec un faux `pactl`.
- Test C++ → `esctl` réel: le code de `LinuxApiSystem` affiche les menus résolution, audio et version, et masque les autres.
- **Non validé sur machine réelle**: les formats de `wlr-randr` et du JSON de `pactl` sont reconstitués de mémoire, pas capturés
  sur un système. À confirmer au premier essai sur CachyOS.

## Menus masqués sur ES-NE (gérés par la distribution)
Wi-Fi, Bluetooth, mises à jour, installation, formatage, overclock, store, services, sauvegarde, mode avion, backglass, NFC.

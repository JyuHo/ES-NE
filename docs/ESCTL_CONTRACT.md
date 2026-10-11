# Contrat entre ES et `esctl`

`LinuxApiSystem` (patch 5) ne connaît aucune commande système. Il applique deux règles.

## 1. Traduction des appels
Toute commande qui commence par `batocera-` (ou `/usr/bin/batocera-`) est exécutée via `esctl` :

| ES appelle | ES-NE exécute |
|---|---|
| `batocera-audio set 'X'` | `esctl audio set 'X'` |
| `batocera-resolution --screen "DP-1" listModes` | `esctl resolution --screen "DP-1" listModes` |
| `batocera-es-swissknife --emukill` | `esctl swissknife --emukill` (le préfixe `es-` est retiré) |
| `batocera-es-thebezelproject list` | `esctl thebezelproject list` |

Les autres commandes (`uname -m`, `ping ...`) ne sont pas modifiées.

## 2. Un menu `esctl` n'apparaît que si esctl le déclare
`esctl has <commande>` doit répondre par le **code de sortie 0** si la commande est implémentée, autre chose sinon.
Si `esctl` est absent du `PATH`, tous ces menus sont masqués. Le résultat est mis en cache pour la durée du processus.

| Menu ES | `esctl has ...` | Appels que fait ES (lus dans `ApiSystem.cpp`) |
|---|---|---|
| Résolution | `resolution` | `listModes`, `--screen <sortie> listModes` |
| BIOS | `systems` | `systems [--filter <système>]` (sortie: lignes `> <système>` puis `<statut> <md5> <chemin>`) |
| Manettes | `padsinfo` | (à relire dans `getPadsInfo`) |
| Fuseau horaire | `timezone` | `get`, `detect`, `set "<tz>"` |
| Sortie audio | `audio` | `list`, `get`, `set '<x>'`, `list-profiles`, `get-profile`, `set-profile '<x>'` |
| Bezels | `thebezelproject` | `list`, `install <x>`, `remove <x>` |
| Version | `version` | `version [--extra]`: première ligne = version |
| Hook gamelists | `preupdate-gamelists-hook` | appelé avant la mise à jour des gamelists |

Hors de ce tableau, `batocera-info --full` (infos système) et `batocera-es-swissknife --emukill` (tuer l'émulateur) ne passent pas par `has`: ils sont appelés directement, donc `esctl info --full` et `esctl swissknife --emukill` doivent exister dès que `esctl` est installé.

## Menus masqués sur ES-NE (gérés par la distribution)
Wi-Fi, Bluetooth, mises à jour, installation, formatage, overclock, store, services, sauvegarde, mode avion, backglass, NFC.

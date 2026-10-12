# SPDX-License-Identifier: GPL-3.0-or-later
"""Registre des sous-commandes d'esctl.

Chaque module expose:
  NAME         nom de la sous-commande (le frontend traduit batocera-<NAME> en esctl <NAME>)
  available()  True si la commande est utilisable sur cette machine (répond à ``esctl has <NAME>``)
  run(args)    exécute la commande, renvoie le code de sortie
"""
from . import (audio, config, info, padsinfo, preupdate_gamelists_hook, resolution, swissknife, systems, thebezelproject,
               timezone, version)

COMMANDS = {module.NAME: module for module in (audio, config, info, padsinfo, preupdate_gamelists_hook, resolution, swissknife, systems, thebezelproject,
                                           timezone, version)}

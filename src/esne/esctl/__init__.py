# SPDX-License-Identifier: GPL-3.0-or-later
"""esctl: outil système d'ES-NE.

Remplace les scripts ``batocera-*`` que le frontend appelle. Le frontend traduit
``batocera-xxx args`` en ``esctl xxx args`` et n'affiche un menu que si ``esctl has xxx``
réussit. Contrat complet: docs/ESCTL_CONTRACT.md.

Bibliothèque standard uniquement: esctl doit démarrer vite et sans dépendance.
"""

# Thème ES-NE pour l'écran Trofeo Vision 6,86" (1280×480)

Fond aux couleurs d'ES-NE avec deux cadres, **CPU** (cyan) et **GPU** (violet), qui affichent température, utilisation et
fréquence. Les valeurs vivantes viennent des capteurs de [trcc-linux](https://github.com/Lexonight1/thermalright-trcc-linux)
(`cpu:temp`, `cpu:usage`, `cpu:freq`, `gpu:primary:temp`, `gpu:primary:usage`, `gpu:primary:clock`).

Prérequis: trcc-linux installé et l'écran reconnu (`trcc report` doit montrer `0416:5302` et `resolution=1280x480`), Pillow
(`sudo pacman -S python-pillow`).

```fish
python contrib/trofeo-vision/esne_lcd_theme.py build     # dessine le fond dans ~/.trcc-user/esne-lcd/
# ferme trcc (zone de notification), puis:
python contrib/trofeo-vision/esne_lcd_theme.py apply     # sauvegarde ~/.trcc/trcc.json puis pose le thème
# relance trcc
python contrib/trofeo-vision/esne_lcd_theme.py restore   # revient aux réglages d'avant
```

Options: `--font "Nom de police"` (police installée, `DejaVu Sans` par défaut), `--anchor center` si trcc place les textes par
leur centre et non par leur coin haut-gauche.

Statut: dessiné d'après le rapport `trcc report` de la machine de développement, pas encore validé sur l'écran.

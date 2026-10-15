# Matrice de parité avec RetroBat
Légende: ❌ non fait · 🚧 en cours · ✅ fait · ⛔ masqué volontairement

## 1. Systèmes et émulateurs (lanceur `es-launcher`)
| Système | Émulateur | Lancement | Shaders | Ratio | Rewind | Bezels | Manettes |
|---|---|---|---|---|---|---|---|
| nes, snes, gb, gbc, gba, mastersystem, megadrive, gamegear, pcengine, atari2600, psx, nds, arcade | libretro | ✅ code + tests; snes validé en jeu | ✅ (preset slang, crt-royale validé) | ✅ | ✅ | ❌ | ✅ pilote `sdl2` |
| n64 | libretro | ✅ validé en jeu | ✅ | ✅ | ✅ | ❌ | ✅ |
| psp | libretro | 🚧 non testé (pas de roms) | ✅ | ✅ | ✅ | ❌ | ✅ |
| gc, wii | Dolphin | ✅ validé en jeu | ✅ réglages ES (API, résolution, AA, langues, barre capteur...) | ⛔ | ⛔ | ❌ | ✅ quitter: Select+Start |
| ps2, ps3, wiiu, switch, xbox | PCSX2, RPCS3, Cemu, Eden/Ryujinx, xemu | 🚧 arguments écrits de mémoire, non testés (Cemu ✅ validé: manettes + API graphique; Eden ✅ manettes validées; PCSX2 ✅ manette et réglages validés; RPCS3 ✅ manettes validées; xemu ✅ jeu lancé et manette détectée (`xemu.toml`: BIOS, manettes); réglages choisis dans ES (Eden: mode docké, résolution 1X à 4X, filtrage anisotrope, VSync, AA, filtre, format, langue, région; Cemu: langue, VSync, filtre, volume, FPS; xemu: résolution, format d'image) écrits à partir des clés relevées dans les fichiers réels, validés en jeu; Xenia: langue et région de la console, son; PCSX2: filtrage anisotrope, textures, CAS, dithering, patchs 16:9 et sans entrelacement, FPS, volume, son, RetroAchievements écrits, non essayés en jeu) | ⛔ | ⛔ | ⛔ | ❌ | ✅ |
| steam, windows | Steam, Wine/umu | 🚧 Steam: lancement et manette validés (`.steam` créés par es-genconfig, `esne-steam-run` attend la fin de la partie, ferme le client ouvert par ES-NE sauf KEEP STEAM OPEN: non testé); Select+Start ferme le jeu et ES revient (validé sur Cuphead), le client ouvert par ES-NE est refermé (validé); Wine/umu non testé | ⛔ | ⛔ | ⛔ | ❌ | ✅ |
| dreamcast | Redream (archive Linux, `~/.local/bin`) | ✅ lancement du jeu, plein écran, manette et réglages ES (région, langue, câble, standard TV, format, résolution, VSync) écrits dans `redream.cfg`, validés en jeu | | | | | |
| xbox 360 | Xenia Canary (AppImage du fork Linux natif) | 🚧 expérimental: détection de l'AppImage et lancement d'un `.iso`, plein écran (`--fullscreen=true`), manette validés en jeu; réglages vidéo choisis dans ES (résolution, VSync, AA, FSR/CAS, anisotrope, limite d'images) écrits en options de ligne de commande, validés en jeu; le reste reste dans la configuration de Xenia | | | | | |

Bezels: un bezel par système (pas de bezel par jeu); le réglage du système prime sur le global; quand un bezel est actif, le ratio d'ES est ignoré (équivalent de « auto »): le jeu est cadré dans la zone transparente du bezel. AUTO utilise The Bezel Project s'il est installé pour le système; « NONE » désactive; ratio de l'image différent de l'écran → image étirée sur l'écran, jeu aux proportions de sa fenêtre (jusqu'à 25 % d'écart, ou toujours avec STRETCH BEZELS). RetroArch 1.22 ajoute la position de la zone personnalisée à celle de la zone centrée: on envoie l'écart (0 pour un bezel centré). Tatouages/overlays de manettes non gérés. Zone de jeu détectée par le décodeur PNG intégré (Pillow s'il est installé) ou fichier `.png.info`. Les bords noirs d'une ROM PAL (N64) ne sont pas rognés: réglage du cœur (`mupen64plus-Overscan*`) laissé à l'utilisateur.

Limites: table `aspect_ratio_index` reprise de la source de RetroArch (4/3, 16/9 et custom confirmés; les autres à valider); ES « full » non géré; jeux compressés (zip) et états de sauvegarde validés en jeu; netplay et `-monitor` écrits mais non validés en jeu (RetroArch seulement, pas les émulateurs autonomes); RetroAchievements non géré; les réglages internes des émulateurs autonomes (plein écran, résolution) ne sont pas gérés.

## 2. Menus du frontend ES
Un ✅ = branché dans `LinuxApiSystem` et vérifié à la compilation; les menus validés dans ES lancé sont indiqués ci-dessous.
Les menus liés à `esctl` apparaissent seulement si `esctl has <commande>` réussit (voir `docs/ESCTL_CONTRACT.md`).

| Fonction ES | Batocera (script) | ES-NE | État |
|---|---|---|---|
| Résolution | `batocera-resolution` | `esctl resolution` (xrandr, wlr-randr, kscreen-doctor) | ✅ code + tests; format kscreen-doctor -j capturé sur KDE réel; ❌ GNOME Wayland; setMode non essayé sur machine |
| Sortie audio | `batocera-audio` | `esctl audio` (pactl) | ✅ code + tests; non essayé sur machine |
| Fuseau horaire | `batocera-timezone` | `esctl timezone` (`timedatectl`) | ✅ validé en session ES-NE (règle polkit) |
| BIOS / systèmes | `batocera-systems` | `esctl systems` | ✅ |
| Infos manettes | `batocera-padsinfo` | `esctl padsinfo` (evdev + batterie sysfs) | ✅ sortie réelle vérifiée (PS4) |
| The Bezel Project | `batocera-es-thebezelproject` | `esctl thebezelproject` (téléchargement GitHub, images seules) | ✅ installation, suppression et aperçu validés dans ES |
| Décorations (bezels) en jeu | `bezels.py` Batocera | `bezels.py` + overlay RetroArch, zone de jeu en `custom_viewport` | ✅ validé en jeu sur SNES, N64, PSX et GBA (écran 16:10), avec bezels par jeu téléchargés à la demande; 16:9 à valider |
| Version affichée | `batocera-version` | `esctl version` (`share/esne.version`, sinon version du package) | ✅ |
| Décorations / shaders | (dossiers) | menu visible si les dossiers existent (`es-genconfig` crée `decorations/`) | ✅ |
| Netplay | `7zr` | `7zz`, `7z`, `7za` ou `7zr` dans le `PATH` | ✅ |
| Veille, arrêt rapide | `pm-suspend` | retirés du menu QUIT | ⛔ |
| Manuel PDF | `pdftoppm`, `pdfinfo` | cherchés dans le `PATH` | ✅ |
| Thèmes (téléchargement) | — | inchangé | ✅ code d'ES |
| Raccourcis en jeu | `batocera-hotkeys` | `hotkey.py` + options RetroArch (Select+Start quitte, Select+R3 menu) | ✅ validé |
| Session de connexion ES-NE (Plasma Login Manager, gamescope) | — | `es-ne-session` (gamescope sans `-e`, journal `~/.local/state/esne/session.log`) | ✅ validé (BC-250) |
| Disposition du clavier (menu) | `batocera-keyboard` | `esctl keyboard` (`localectl`, règle polkit), appliquée à la prochaine session | ✅ validé (listes et changement, règle polkit) |
| Traductions | `.po` Batocera | français complet (1282 chaînes) | ✅ |
| Manette → clavier | `evmapy` | `esne-padkeys` (ports PortMaster) | ✅ validé |
| Installation d'un core manquant | — | dialogue d'ES, `esctl install-core` (pacman, paru/yay) | ✅ validé |
| Arrêt / redémarrage système | `batocera-shutdown` | `systemctl poweroff/reboot` (fork) | ✅ validé en session ES-NE (sans mot de passe) |
| Redémarrage d'ES | drapeaux `/tmp` | `execv` + invite après changement de langue/thème | ✅ validé |
| Options par système/jeu | `features.yml` | `es_features.cfg` généré (ratio, lissage, rewind, autosave, pixel perfect, shaders, pilote vidéo) | ✅ validé |
| Ports (jeux natifs), manette → clavier | scripts `.sh` + `gptokeyb` (PortMaster) | `es-genconfig --install-port` (catalogue PortMaster, sans PortMaster) + `esne-padkeys` (evdev → uinput, fichiers `.gptk`) | ✅ Digger validé: lancement et manette |
| Wi-Fi, Bluetooth | `batocera-wifi`, `batocera-bluetooth` | NetworkManager, BlueZ | ⛔ |
| Mises à jour, installation, formatage, overclock, sauvegarde | `batocera-upgrade`, `-install`, `-format`, `-overclock`, `-sync` | gestionnaire de paquets | ⛔ |
| Store, services, mode avion, backglass, NFC | `batocera-store`, `-services`, `-planemode`, `-backglass`, `-nfc` | — | ⛔ |

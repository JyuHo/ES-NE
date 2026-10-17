<p align="center">
  <img src="assets/es-ne-banner.png" alt="ES-NE" width="720">
</p>

<p align="center"><a href="README.md">🇫🇷 Français</a> &nbsp;·&nbsp; <b>🇬🇧 English</b> &nbsp;·&nbsp; <a href="README.de.md">🇩🇪 Deutsch</a></p>

# ES-NE

Standalone version of [batocera-emulationstation](https://github.com/batocera-linux/batocera-emulationstation)
for Arch Linux / CachyOS, with RetroBat's options, **with no dependency on Batocera**.

- Regular Linux layout (XDG), no `/userdata`
- Frontend: patched EmulationStation fork (`ESNE` build variant), as a submodule
- `es-launcher` launcher (replaces `emulatorlauncher` / `batocera-configgen`)
- `esctl` system tool (replaces the `batocera-*` tools): resolution, audio, time zone, BIOS...
- Same key format as `batocera.conf` (`global.ratio`, `snes.core`, `snes["game.zip"].shaderset`)
  to stay compatible with ES's menus
- Declarative (YAML) definitions of systems, emulators and features

## Status
| Component | State |
|---|---|
| ES frontend (`emulationstation-esne` fork, `esne` branch) | ✅ builds and runs on CachyOS (KDE Wayland). Fully translated French interface. Patches: `-DESNE=ON` option, paths (XDG config, data in `~/esne`), `LinuxApiSystem`, system shutdown/reboot, ES restart, simplified QUIT menu, Zaparoo disabled by default |
| `es-launcher` | ✅ launching validated on a real machine (SNES, N64, GameCube, Wii): RetroArch (`sdl2` pad, hotkeys, ratio, shaders, rewind...) and standalone emulators; 341 tests |
| `es-genconfig` | ✅ generates `es_systems.cfg`, `es_features.cfg` and shader sets from the catalog (27 systems) |
| `esctl` | ✅ `has`, `version`, `resolution`, `audio`, `config`, `info`, `timezone`, `keyboard`, `install-core`, `padsinfo`, `thebezelproject`, `systems` (BIOS status), `swissknife --emukill`, `preupdate-gamelists-hook`. Contract in `docs/ESCTL_CONTRACT.md` |
| Arch package (`packaging/arch/PKGBUILD`), `ES-NE` session, polkit rules | ✅ package installed and login session validated (Plasma Login Manager, gamescope, BC-250): `es-ne-session` runs `gamescope -f -- emulationstation` (without `-e`, which gave a black screen) and logs to `~/.local/state/esne/session.log`. Build in a copy outside the repository: `makepkg` rewrites `pkgver` |

Details: `docs/ROADMAP.md` (milestones), `PARITY.md` (parity with RetroBat), `docs/UPSTREAM.md` (ES patches).

## Paths
**ES frontend** (`-DESNE=ON`):

| Role | Default path | Override |
|---|---|---|
| Read-only resources (themes, shaders, `es_systems.cfg`...) | `/usr/share/esne` | `ESNE_SHARE_DIR` |
| Config (`esne.conf`, `es_settings.cfg`) | `~/.config/esne` | `ESNE_CONFIG_DIR` or `XDG_CONFIG_HOME` |
| Data (roms, bios, saves, screenshots...) | `~/esne` | `ESNE_DATA_DIR` |
| Logs | `~/.local/state/esne/logs` | `ESNE_STATE_DIR` or `XDG_STATE_HOME` |

`emulationstation.ini` (inherited from ES) can still override each folder.

**Python launcher** (`es-launcher`): config `~/.config/esne/esne.conf`, data `~/esne/`, cache `~/.cache/esne/`
(`ESNE_CONFIG_DIR`, `ESNE_DATA_DIR`, `ESNE_CACHE_DIR`).
`paths.py` also knows `share` (`ESNE_SHARE_DIR`) and `state` (`ESNE_STATE_DIR`), like the frontend.

## Runtime dependencies (Arch / CachyOS)
For libretro games, `es-launcher` needs:
```bash
sudo pacman -S --needed retroarch libretro-core-info libretro-snes9x \
    retroarch-assets-ozone retroarch-assets-xmb retroarch-assets-glui \
    libretro-shaders-slang libretro-overlays
```
The `retroarch-assets-*` packages provide the icons and fonts of the RetroArch menu (without them it is displayed with
missing resources). No autoconfig package is needed: `es-launcher` uses the `sdl2` joypad driver.

In-game pad shortcuts (configurable: `hotkey_enable`, `hotkey_exit`, `hotkey_menu`):
**Select + Start** quits the game and returns to ES (also for standalone emulators: `es-launcher` watches the pad and closes the emulator), **Select + R3** opens the RetroArch menu.
Per-system/per-game options in ES (ratio, shaders, smoothing, rewind, Vulkan/OpenGL video driver...): see `PARITY.md`.

## Known issues
- **`emulationstation: symbol lookup error: /usr/lib/libjxrglue.so: undefined symbol: WMPAlloc`** (October 2026): the `jxrlib` 1.4.4-3 package (Arch, October 12) ships a `libjxrglue.so` with no dependency on `libjpegxr.so`, which defines `WMPAlloc`; every program linked to `freeimage` 3.18.0-25, ES included, fails at startup. The defect is in the package, not in ES-NE. Tested workarounds: start with `LD_PRELOAD=/usr/lib/libjpegxr.so emulationstation`, or go back to `jxrlib` 1.4.4-1 (`sudo pacman -U /var/cache/pacman/pkg/jxrlib-1.4.4-1*.pkg.tar.zst`, then `IgnorePkg = jxrlib` in `/etc/pacman.conf` until a fix is out). Diagnosis: `readelf -d /usr/lib/libjxrglue.so | grep NEEDED` must not list only `libc.so.6`.

## Bezels (decorations)
Bezels from The Bezel Project. ES menu **Updates → The Bezel Project**: open a system then INSTALL (or UPDATE / REMOVE). `esctl thebezelproject install snes` downloads the system image (`~/esne/decorations/thebezelproject/systems/snes.png`): it is the fallback bezel and what enables bezels for the system.
**Per-game bezel**: when the launched game has its own bezel in the repository (`GameBezels/<system>/<ROM name>.png`, identical name or same title with the closest region), it replaces the system one. It is downloaded on first launch (a few hundred KB, 5 s at most; without network the system bezel is kept) then stored in `~/esne/decorations/thebezelproject/games/<system>/`. `esctl thebezelproject games snes` downloads them in advance for every ROM of the system. To keep only the system bezel: `bezel_games = 0` in the configuration (global, system or game).
In game, `es-launcher` sets the image as a RetroArch overlay and fits the game into the transparent area (ES's ratio setting is then ignored, as with "auto"). **Decoration set** option (global, system or game): Auto (= The Bezel Project if installed for the system), None, or a decoration set; the system setting takes precedence over the global one.
The game area is detected in the image (built-in PNG decoder, result cached; `python-pillow` is used if installed, or a `.png.info` file if present). The image is always displayed full screen; if the screen does not have its ratio (16:9 on a 16:10 screen), it is stretched and the game keeps the proportions of its window. Beyond a 25 % difference (21:9...), the bezel is ignored unless the STRETCH BEZELS option is set to Yes.

## libretro cores
One core per system, as an **optional** dependency of the package (`pacman -Qi es-ne-git`). `es-genconfig` picks by default, for each system, the highest-priority installed core (`src/esne/data/systems.yml`). If the launched core is missing, ES shows "the core is missing" and **offers to install it** (`esctl install-core <core>`, via pkexec and a polkit rule limited to the whitelist of official-repository cores, without a password from the active local session); AUR cores (whitelist) are built by `paru` or `yay` if installed (`--sudo pkexec`: dependencies included), otherwise cloned into `~/.cache/esne/aur`, built with makepkg as your user (PKGBUILD not reviewed, `git` and `base-devel` required, dependencies to be installed yourself) and installed by a second root helper; in both cases **your password is required** (polkit `auth_admin_keep`; without a polkit agent, for instance in a gamescope session, this step fails). Run `es-genconfig` again after installing a core to update the default core. Official repositories: `libretro-nestopia libretro-snes9x libretro-gambatte libretro-mgba libretro-genesis-plus-gx libretro-mupen64plus-next libretro-beetle-psx libretro-beetle-pce-fast libretro-melonds libretro-ppsspp libretro-mame`. AUR (preferred cores for NES, PSX, arcade, Atari 2600, GBA fallback): `libretro-fceumm libretro-pcsx-rearmed libretro-fbneo libretro-stella libretro-gpsp`.

## Save states, netplay, compressed games, screen
- **States**: ES offers its state menus (load a state, resume the autosave). ES chooses the slot (`-state_slot`), copies the state to resume as `<game>.state.auto` and launches the game with `-autosave 1`: `es-launcher` sets RetroArch's `state_slot`, automatic loading and automatic state index (`incrementalsavestates` option, yes by default). States are in `~/esne/saves/<system>/` (no per-core subfolder: `sort_savestates_enable=false`, otherwise ES does not see them). Validated in game (SNES).
- **Netplay**: deterministic cores (nestopia, fceumm, snes9x, bsnes, gambatte, mgba, gpsp, genesis_plus_gx, picodrive, mednafen_pce_fast, fbneo, mame, stella, pcsx_rearmed) are marked `netplay="true"` in `es_systems.cfg`. Enable it in ES (games menu → netplay settings) then host or join a game: `es-launcher` converts ES's options into `--host` / `--connect` / `--port` / `--mitm-session` / `--nick` and RetroArch's `netplay_*` settings (passwords, spectator, relay). Not validated in game.
- **Compressed games**: `.zip` and `.7z` are accepted. A core that reads archives (arcade) receives them as they are; for the others, the game is extracted to `~/.cache/esne/extract/<system>/` (only the last game is kept), renamed like the archive to keep the save names. `7z` / `7zz` is required for `.7z`. Validated in game (zip).
- **Screen** (`-monitor`): ES-NE passes the screen chosen in ES to RetroArch (`video_monitor_index`). Not validated (only one screen on the test machine).

## Scraping keys
By default, nothing is compiled in or packaged. `es-genconfig` creates `~/.config/esne/keys.conf` (mode 600) with a commented template: uncomment and fill in `SCREENSCRAPER_DEV_LOGIN`, `GAMESDB_APIKEY`, `CHEEVOS_DEV_LOGIN`..., then restart ES. A scraper whose key is missing does not appear in the menu. This file must never be committed. Your personal credentials (ScreenScraper account, RetroAchievements) are entered in ES's menus.

**Release package** (maintainer): `tools/build-release.sh /path/to/keys.conf` builds the Arch package, produced in `dist/release/` (ignored by git) and to be attached to the GitHub release; it installs with `sudo pacman -U`. The keys file is never committed. The user's `keys.conf` still takes precedence. Validated on CachyOS with release 1.0.0: the scrapers work without `keys.conf` or personal credentials.

## Theme and free-to-play

<table>
  <tr>
    <td><img src="docs/screenshots/theme-nuit-system.jpg" alt="Nuit: systems"></td>
    <td><img src="docs/screenshots/theme-nuit-gamelist.jpg" alt="Nuit: game list"></td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/theme-braise-system.jpg" alt="Braise: systems"></td>
    <td><img src="docs/screenshots/theme-braise-gamelist.jpg" alt="Braise: game list"></td>
  </tr>
</table>

The package adds **ES-NE** to the applications menu (Games category, ES icon), in addition to the login session entry.
The package ships the **ES-NE** theme (made for this project) in `/usr/share/esne/themes`: it is the default theme, covers all 27 systems, with two moods (Nuit, Braise) and three button icon sets (ES, Xbox, PlayStation; [Kenney](https://kenney.nl/assets/input-prompts) icons, CC0) selectable in User interface → Theme. The background is animated (and continuous from one system to the next); the clock, network and controller activity show at the top right (turn on "Show controller activity" in the controller settings). Console logos come from [Monochrome Gaming Logos](https://github.com/HVR88/Monochrome-Gaming-Logos) (non-commercial use; see `docs/THIRD_PARTY.md`). Your own themes go in `~/esne/themes`.
The **Ports** system runs `.sh` scripts (`~/esne/roms/ports/`). No game is shipped: `es-genconfig --install-port digger` downloads **Digger** (0.5 MB, GPL-2.0, x86_64 and aarch64) from the [PortMaster](https://github.com/PortsMaster/PortMaster-New) catalog and creates its launcher (`--list-ports` lists the available games). Only the game folder is taken, without PortMaster. Games that only accept a keyboard can be played with a pad thanks to `esne-padkeys`, the equivalent of `gptokeyb`: it reads the game's `.gptk` file (`a = enter`, `left_analog_up = up`, `mouse_movement_*`, `mouse_left`...), reads the pads (evdev) and emits a virtual keyboard/mouse (uinput). The package loads the `uinput` module and grants access to the session's `/dev/uinput` (udev rule). If uinput is unusable, the game still starts, without translation. Direct usage: `esne-padkeys game.gptk -- ./game` (`--grab` for exclusive access to the pads, at the cost of ES-NE's exit shortcut). `es-genconfig` never overwrites an existing launcher; the list is in `src/esne/data/ports.yml` (extendable via `~/.config/esne/ports.yml`, with `command:` forms for an installed program or `portmaster:`).

## Generating `es_systems.cfg`
```bash
es-genconfig                    # writes ~/.config/esne/es_systems.cfg (all systems of the catalog) + rom folders
es-genconfig --installed-only   # only systems for which a libretro core is installed
es-genconfig --stdout           # prints es_systems.cfg without writing anything
```
`es-genconfig` also writes `es_features.cfg` (per-system/per-game options: ratio, smoothing, rewind, auto-save, pixel perfect,
shaders) and creates the shader sets in `~/esne/shaders/configs/` for the installed libretro presets
(`libretro-shaders-slang`). Systems come from `src/esne/data/systems.yml` (extended by `~/.config/esne/systems.yml`). Put your roms in
`~/esne/roms/<system>/`; ES hides empty systems.

## Systems and emulators
27 systems: 8/16-bit consoles up to GameCube, Dreamcast, PSP, PS2/PS3, Wii/Wii U, Switch, Xbox, Xbox 360, plus `steam` and `windows`.
- **libretro** (NES to PS1, N64, PSP, arcade...): cores chosen in `systems.yml`.
- **Standalone** (described in `emulators.yml`, launched by `generators/standalone.py`): Dolphin (GameCube, Wii; ES settings in `Dolphin.ini`, `GFX.ini` and SYSCONF; SDL pads: GameCube with 2 players, Wii as Classic Controller or emulated Wiimote + Nunchuk, or real Wiimotes), PCSX2 (PS2),
  RPCS3 (PS3), Cemu (Wii U), Eden or Ryujinx (Switch), xemu (Xbox), Xenia Canary (Xbox 360), Redream (Dreamcast), RMG (Rosalie's Mupen GUI, N64), PPSSPP (PSP) DuckStation (PS1) and Snes9x (SNES) as alternatives to the libretro cores, Steam (launch and pad validated; `.steam` files containing the appid, created by `es-genconfig` for every installed game: Steam libraries and `libraryfolders.vdf` read, Proton and tools discarded; `esne-steam-run` waits for the end of the game, because Steam hands control back immediately, and the Select+Start shortcut closes the whole game tree (Proton included) and hands control back to ES; the Steam client opened by ES-NE is closed at the end of the game, KEEP STEAM OPEN option to keep it),
  Wine or umu-run (`windows`). They start full screen without an interface. The most useful graphics and console settings are chosen in ES (details per emulator below); for the rest, use the emulator's own configuration.
  **PCSX2** (pad and ES settings validated in game with Final Fantasy XII, AppImage; after a package update, run `es-genconfig` again to see the new options, which the ES-NE session already does): ES-NE rewrites the `[Pad1]`/`[Pad2]` sections of `~/.config/PCSX2/inis/PCSX2.ini` (pads designated by SDL number, no GUID) and applies graphics API, resolution, ratio, vsync and FXAA, as well as anisotropic filtering, texture filtering, CAS sharpness, dithering, 16:9 and no-interlacing patches, frame counter, volume, mute and RetroAchievements (written from a real `PCSX2.ini`; only RetroAchievements has not been tried in game). Launch PCSX2 once by hand beforehand (wizard, BIOS in `~/esne/bios/ps2`).
  **RPCS3** (pads validated in game): ES-NE writes `input_configs/global/Default.yml` (SDL handler, one entry per pad) and applies graphics API, resolution, ratio and vsync to `config.yml`. Launch RPCS3 once by hand beforehand (firmware, configuration). A `Name.ps3` folder is launched through its `EBOOT.BIN`.
  **Eden** (validated in game, 2 PS4 pads, AppImage): configure player 1's pad in Eden once; ES-NE copies that mapping to the other pads of the same model, with the GUID Eden sees (ES's one, name CRC set to zero) (`qt-config.ini`, `AUTOCONFIGURE CONTROLLERS` option). Settings chosen in ES and written to `qt-config.ini` when defined (a setting not chosen keeps Eden's value): docked or handheld mode, resolution (1X to 4X), anisotropic filtering (automatic, default, 2x to 16x), VSync mode, anti-aliasing, scaling filter, aspect ratio, console language and region (validated in game).
  **Cemu** is an exception (validated in game: Mario Kart 8, 2 PS4 pads): ES-NE generates the "Wii U Pro Controller" profiles (`controllerProfiles/controllerN.xml`) from ES's pads and applies to `settings.xml` the `GRAPHICS API` option (Vulkan/OpenGL) and the settings chosen in ES: console language, VSync, upscale filter, full-screen stretch, TV volume and frame counter (validated in game). Launch Cemu once by hand beforehand (first-run wizard, keys and MLC folder) and configure the pad once in Cemu: ES (SDL2) and Cemu (SDL3) do not compute the same GUID, ES-NE reuses the one Cemu recorded for the same model. AppImage (`~/.local/bin/Cemu*.AppImage`), package or Flatpak are detected; the `AUTOCONFIGURE CONTROLLERS` option lets you keep your own mapping.
**xemu (Xbox)**: put the system files in `~/esne/bios/xbox` (or `Xbox`) (512-byte MCPX boot ROM, 256-byte EEPROM, flash BIOS, `.qcow2` hard disk; they are recognized by size, not by name), launch xemu once by hand so it creates `xemu.toml`, then ES-NE fills in these files and the pads (full screen comes from the command line) (AUTOCONFIGURE CONTROLLERS option). The RENDER RESOLUTION (render scale 1X to 4X) and ASPECT RATIO (native, auto, 4:3, 16:9) options are written to `[display.quality]` and `[display.ui]` (validated in game). xemu is not in the official repositories: the **AppImage** is found in `~/.local/bin` or `~/Applications` (name `xemu*.AppImage`, made executable), otherwise AUR `xemu` or Flatpak `app.xemu.xemu`.

A missing emulator gives error 204 with the name of the package to install. **Xbox 360** (experimental; launching an `.iso`, full screen, pad and video settings validated in game): Xenia Canary has no official Linux binary; ES-NE detects the AppImage of the native Linux fork ([peerloomllc/xenia-canary](https://github.com/peerloomllc/xenia-canary/releases)) in `~/.local/bin` or `~/Applications` (name `xenia*.AppImage`). ES-NE launches the game (`.iso` or `.xex`) with `--fullscreen=true`; video settings (render resolution, VSync, anti-aliasing, FSR/CAS, anisotropic filtering, frame limit) chosen in ES, passed on the command line without touching Xenia's configuration (validated in game); console language and region (written to `xconfig.settings`, the binary file of the Xbox 360's internal settings, at bytes read from a real file: languages English, Japanese, German, French, Spanish, Italian, Korean, Russian, Traditional Chinese and the others following the console's order; regions France, Germany, Spain, Italy, United Kingdom, United States, Japan, Netherlands, Russia, Czechia), sound (mute, audio system), console video mode (`avpack`: HDMI, VGA, component, SCART, PAL-60) and video options, all validated in game; pads and the rest are set in Xenia's own configuration (`~/.local/share/Xenia/xenia-canary.config.toml`). Launch Xenia once by hand beforehand.

**DuckStation (PS1)** (validated in game; written from a real `settings.ini`): AppImage in `~/.local/bin` or `~/Applications` (`DuckStation*.AppImage`; `duckstation-qt` package or Flatpak also accepted), offered in ES in addition to the libretro cores. It starts with `-batch -fullscreen --`; ES-NE applies to `~/.local/share/duckstation/settings.ini` the graphics renderer, resolution, MSAA, texture filtering, PGXP, the widescreen hack, aspect ratio, VSync, frame counter, mute, the ask-to-save and auto-save on exit, and rewrites `Pad1`/`Pad2` (analog pad, `AUTOCONFIGURE CONTROLLERS` option; no multitap).

**Snes9x (SNES)** (validated in game: full screen, PS4 pad, Select+Start exit; written from a real `snes9x.conf` of version 1.63): AppImage in `~/.local/bin` or `~/Applications` (`Snes9x*.AppImage`; `snes9x-gtk` package or Flatpak also accepted), offered in ES in addition to the libretro cores. ES-NE forces full screen when a game opens and applies to `~/.config/snes9x/snes9x.conf` the display driver, aspect ratio, bilinear filter, VSync, high-resolution effect, scanlines, frame counter, mute, rewind, sprite-limit removal and CPU overclock. Pads: built-in profile for Sony pads (measured on a PS4 pad), written for every ES pad; for another model, configure player 1's pad once in Snes9x and ES-NE copies that mapping (`AUTOCONFIGURE CONTROLLERS` option); DIRECTIONS option: D-pad (default) or left stick.

**RMG (N64) and PPSSPP (PSP)** (validated in game; written from real configuration files): the AppImages go in `~/.local/bin` or `~/Applications` (names `RMG*.AppImage` and `PPSSPP*.AppImage`; package or Flatpak also accepted). They are offered in ES in addition to the libretro cores, which remain the default choice. Launch each once by hand to create its configuration. **RMG** starts with `-f -n -q` (full screen, no menus, it closes when the game ends); ES-NE rewrites the pad profiles of `~/.config/RMG/mupen64plus.cfg` (4 players; `AUTOCONFIGURE CONTROLLERS` option) and applies to `GLideN64.ini` the resolution, aspect ratio, MSAA, FXAA, anisotropic filtering, texture filtering, high-resolution textures, VSync and frame counter. **PPSSPP** starts with `--fullscreen --pause-menu-exit`, recognizes SDL pads by itself, and ES-NE applies to `ppsspp.ini` the graphics backend (Vulkan, OpenGL), resolution, anisotropic filtering, texture filtering, VSync, frame skipping, frame counter, mute and console language.

**Dreamcast**: Redream is not in the official repositories; put its Linux archive ([redream.io](https://redream.io)) in `~/.local/bin` (`redream` binary, direct path accepted), or in `~/Applications`. ES-NE launches the game (`.gdi`, `.cdi`, `.chd` or `.cue`); full screen comes from Redream's configuration (`redream.cfg`, created on its first launch, searched in the XDG data folder, the XDG config folder, `~/.redream` then next to the binary). Settings chosen in ES and written to `redream.cfg`: region, console language, TV standard (PAL, NTSC, PAL-M, PAL-N), cable (VGA, RGB, composite), aspect ratio, resolution (640x480 to 3840x2880), VSync, renderer (Vulkan, OpenGL), frame skipping and frame counter (validated in game).

## Building the frontend
```bash
git clone --recurse-submodules https://github.com/JyuHo/ES-NE.git
cd ES-NE/third_party/emulationstation
cmake -B build -DESNE=ON -DGL=ON
cmake --build build -j"$(nproc)"
```
Build dependencies: SDL2, SDL2_mixer, FreeImage, FreeType, cURL, RapidJSON, LibVLC, ALSA (see `docs/UPSTREAM.md`).
After a `git pull`, remember to run `git submodule update --init`.

## `esctl`
System tool that ES calls in place of the `batocera-*` tools (see `docs/ESCTL_CONTRACT.md`):
```bash
esctl commands            # commands usable on this machine
esctl has audio           # exit code 0 if available
esctl resolution listModes
esctl audio list
esctl timezone get          # set may require a polkit rule
esctl keyboard list-layouts # keyboard layouts (localectl); set <layout> [variant]
esctl install-core fceumm   # installs a libretro core (pacman, paru/yay for the AUR)
esctl padsinfo              # pads and batteries, in the format read by ES
```
Without installing: `PYTHONPATH=src python -m esne.esctl commands`.

## Dev (Python launcher and esctl)
```bash
python -m venv .venv && . .venv/bin/activate
pip install pytest && pytest        # tests find src/ on their own
pip install -e '.[dev]'              # also installs es-launcher and esctl (builds evdev)
```

## License
GPL-3.0-or-later. See `LICENSE` and `docs/LICENSING.md`. The ES fork is under MIT.

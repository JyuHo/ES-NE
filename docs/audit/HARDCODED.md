# Audit des dépendances Batocera

> Instantané de l'audit initial (avant les patchs). État actuel: voir `docs/AUDIT_ANALYSIS.md` et `docs/UPSTREAM.md` (par exemple `batocera-keyboard` est remplacé par `esctl keyboard`).

- Source: `third_party/emulationstation`
- Commit: `5b1764c9a`
- Généré: 2026-10-08

## 1. Chemins /userdata

Regex: `/userdata`

**12 occurrence(s)**

```
es-core/src/Paths.cpp:49: mRootPath = "/userdata";
es-core/src/Paths.cpp:51: mUserEmulationStationPath = "/userdata/system/configs/emulationstation";
es-core/src/Paths.cpp:53: mLogPath = "/userdata/system/logs";
es-core/src/Paths.cpp:54: mScreenShotsPath = "/userdata/screenshots";
es-core/src/Paths.cpp:55: mSaveStatesPath = "/userdata/saves";
es-core/src/Paths.cpp:57: mUserMusicPath = "/userdata/music";
es-core/src/Paths.cpp:59: mUserThemesPath = "/userdata/themes";
es-core/src/Paths.cpp:61: mUserKeyboardMappingsPath = "/userdata/system/configs/evmapy";
es-core/src/Paths.cpp:63: mUserDecorationsPath = "/userdata/decorations";
es-core/src/Paths.cpp:65: mUserShadersPath = "/userdata/shaders/configs";
es-core/src/Paths.cpp:68: mUserRetroachivementSounds = "/userdata/sounds/retroachievements";
es-core/src/Paths.cpp:70: mSystemConfFilePath = "/userdata/system/batocera.conf";
```

## 2. Chemins /usr/share/batocera, /recalbox

Regex: `/usr/share/batocera|/recalbox|/boot/`

**8 occurrence(s)**

```
es-app/src/ApiSystem.cpp:2702: auto res = executeEnumerationScript("cat /boot/boot/batocera.board");
es-core/src/Paths.cpp:56: mMusicPath = "/usr/share/batocera/music";
es-core/src/Paths.cpp:62: mDecorationsPath = "/usr/share/batocera/datainit/decorations";
es-core/src/Paths.cpp:64: mShadersPath = "/usr/share/batocera/shaders/configs";
es-core/src/Paths.cpp:71: mUserManualPath = "/usr/share/batocera/doc/notice.pdf";
es-core/src/Paths.cpp:72: mVersionInfoPath = "/usr/share/batocera/batocera.version";
es-core/src/ThemeData.cpp:1859: "/recalbox/share_init/system/.emulationstation/themes",
es-core/src/utils/Platform.cpp:685: std::string arch = Utils::FileSystem::readAllText("/usr/share/batocera/batocera.arch");
```

## 3. Chemins /etc/emulationstation, /usr/share/emulationstation

Regex: `/etc/emulationstation|/usr/share/emulationstation`

**5 occurrence(s)**

```
es-app/src/ApiSystem.cpp:1128: ,"/etc/emulationstation/themes" // Backward compatibility with Retropie
es-app/src/SystemData.cpp:1347: return "/etc/emulationstation/es_systems.cfg"; // Backward compatibility with Retropie
es-core/src/Paths.cpp:50: mEmulationStationPath = "/usr/share/emulationstation";
es-core/src/Paths.cpp:58: mThemesPath = "/usr/share/emulationstation/themes";
es-core/src/ThemeData.cpp:2370: ,"/etc/emulationstation/themes" // Backward compatibility with Retropie
```

## 4. Dossier ~/.emulationstation

Regex: `\.emulationstation`

**7 occurrence(s)**

```
es-app/src/main.cpp:526: //if ~/.emulationstation doesn't exist and cannot be created, bail
es-app/src/scrapers/Scraper.h:260: //About the same as "~/.emulationstation/downloaded_images/[system_name]/[game_name].[url's extension]".
es-core/src/Paths.cpp:31: mUserEmulationStationPath = Utils::FileSystem::getCanonicalPath(getHomePath() + "/.emulationstation");
es-core/src/Paths.cpp:80: mUserEmulationStationPath = Utils::FileSystem::getCanonicalPath(Utils::FileSystem::getHomePath() + "/.emulationstation");
es-core/src/Paths.cpp:266: // Is it a portable installation ? Check if ".emulationstation/es_systems.cfg" exists in the exe's path
es-core/src/Paths.cpp:269: std::string portableCfg = getExePath() + "/.emulationstation/es_systems.cfg";
es-core/src/ThemeData.cpp:1859: "/recalbox/share_init/system/.emulationstation/themes",
```

## 5. Appels batocera-*

Regex: `batocera-[a-z0-9_-]+`

**191 occurrence(s)**

```
es-app/src/ApiSystem.cpp:54:#define script_config "batocera-config"; // canupdate, overscan enable, overscan disable, storage 'X', storage current, storage list, forgetBT, getRootPassword, lsoutputs
es-app/src/ApiSystem.cpp:55:#define script_overclock "batocera-overclock"; // list, set X
es-app/src/ApiSystem.cpp:56:#define script_upgrade "batocera-upgrade";
es-app/src/ApiSystem.cpp:57:#define script_sync "batocera-sync"; // sync
es-app/src/ApiSystem.cpp:58:#define script_install "batocera-install"; // listDisks, listArchs, install X Y
es-app/src/ApiSystem.cpp:59:#define script_scraper "batocera-scraper";
es-app/src/ApiSystem.cpp:60:#define script_kodi "batocera-kodi";
es-app/src/ApiSystem.cpp:61:#define script_wifi "batocera-wifi"; // scanlist, list, enable X Y, disable
es-app/src/ApiSystem.cpp:62:#define script_bluetooth "batocera-bluetooth"; // trust, list, remove 
es-app/src/ApiSystem.cpp:63:#define script_resolution "batocera-resolution"; // listModes
es-app/src/ApiSystem.cpp:64:#define script_sync "batocera-sync"; // list
es-app/src/ApiSystem.cpp:65:#define script_info "batocera-info"; // --full
es-app/src/ApiSystem.cpp:66:#define script_systems "batocera-systems"; // --filter
es-app/src/ApiSystem.cpp:67:#define script_suport "batocera-support";
es-app/src/ApiSystem.cpp:68:#define script_gameforce "batocera-gameforce"; // buttonColorLed X, powerLed X
es-app/src/ApiSystem.cpp:69:#define script_audio "batocera-audio"; // list, list-profiles, get-profile, set-profile 'X', get, set 'X'
es-app/src/ApiSystem.cpp:70:#define script_bezelproject "batocera-es-thebezelproject"; // list, install X, remove X
es-app/src/ApiSystem.cpp:71:#define script_format "batocera-format"; // listDisks, listFstypes
es-app/src/ApiSystem.cpp:72:#define script_store "batocera-store"; // list, update, refresh, clean-all, install "X", remove "X"
es-app/src/ApiSystem.cpp:73:#define script_preupdategamelists "batocera-preupdate-gamelists-hook";
es-app/src/ApiSystem.cpp:74:#define script_timezones "batocera-timezone"; // get, detect, set "X"
es-app/src/ApiSystem.cpp:75:#define script_padsinfos "batocera-padsinfo";
es-app/src/ApiSystem.cpp:76:#define script_swissknife "batocera-es-swissknife"; // --emukill"
es-app/src/ApiSystem.cpp:164: std::string command = "batocera-version";
es-app/src/ApiSystem.cpp:222: return executeScript("batocera-config overscan " + std::string(enable ? "enable" : "disable"));
es-app/src/ApiSystem.cpp:230: return executeScript("batocera-overclock set " + mode);
es-app/src/ApiSystem.cpp:236: auto result = executeScript("batocera-mitigations status", nullptr);
es-app/src/ApiSystem.cpp:246: return executeScript(std::string("batocera-mitigations ") + (enabled ? "on" : "off"));
es-app/src/ApiSystem.cpp:255: std::string upgradeScriptPath = "batocera-upgrade";
es-app/src/ApiSystem.cpp:263: std::string downloadCommand = "curl --connect-timeout 10 -m 30 -L -f -s -o /tmp/batocera-upgrade "
es-app/src/ApiSystem.cpp:264: "https://github.com/batocera-linux/batocera.linux/raw/refs/heads/master/package/batocera/core/batocera-scripts/scripts/batocera-upgrade "
es-app/src/ApiSystem.cpp:265: "&& chmod +x /tmp/batocera-upgrade";
es-app/src/ApiSystem.cpp:268: if (downloadRes == 0 && Utils::FileSystem::exists("/tmp/batocera-upgrade"))
es-app/src/ApiSystem.cpp:270: LOG(LogInfo) << "Successfully fetched the latest batocera-upgrade script from GitHub.";
es-app/src/ApiSystem.cpp:271: upgradeScriptPath = "/tmp/batocera-upgrade";
es-app/src/ApiSystem.cpp:288: if (upgradeScriptPath == "/tmp/batocera-upgrade") {
es-app/src/ApiSystem.cpp:289: Utils::FileSystem::removeFile("/tmp/batocera-upgrade");
es-app/src/ApiSystem.cpp:295: FILE *flog = fopen(Utils::FileSystem::combine(Paths::getLogPath(), "batocera-upgrade.log").c_str(), "w");
es-app/src/ApiSystem.cpp:309: if (upgradeScriptPath == "/tmp/batocera-upgrade") {
es-app/src/ApiSystem.cpp:310: Utils::FileSystem::removeFile("/tmp/batocera-upgrade");
es-app/src/ApiSystem.cpp:326: std::string updatecommand = "batocera-sync sync " + device;
es-app/src/ApiSystem.cpp:333: FILE* flog = fopen(Utils::FileSystem::combine(Paths::getLogPath(), "batocera-sync.log").c_str(), "w");
es-app/src/ApiSystem.cpp:355: std::string updatecommand = "batocera-install install " + device + " " + architecture;
es-app/src/ApiSystem.cpp:362: FILE *flog = fopen(Utils::FileSystem::combine(Paths::getLogPath(), "batocera-install.log").c_str(), "w");
es-app/src/ApiSystem.cpp:385: FILE* pipe = popen("batocera-scraper", "r");
es-app/src/ApiSystem.cpp:391: FILE* flog = fopen(Utils::FileSystem::combine(Paths::getLogPath(), "batocera-scraper.log").c_str(), "w");
es-app/src/ApiSystem.cpp:429: FILE *pipe = popen("batocera-upgrade-torrent --is-file-ready-to-update", "r");
es-app/src/ApiSystem.cpp:447: std::vector<std::string> results = executeEnumerationScript("batocera-upgrade-torrent --status");
es-app/src/ApiSystem.cpp:458: std::string updatecommand = "batocera-upgrade-torrent --upgrade";
es-app/src/ApiSystem.cpp:465: FILE *flog = fopen(Utils::FileSystem::combine(Paths::getLogPath(), "batocera-upgrade-torrent.log").c_str(), "w");
es-app/src/ApiSystem.cpp:490: FILE *pipe = popen("batocera-upgrade --check-media-upgrade", "r");
es-app/src/ApiSystem.cpp:508: FILE *pipe = popen("batocera-architecture-compatibility", "r");
es-app/src/ApiSystem.cpp:534: FILE *pipe = popen("batocera-upgrade --check-upgrade", "r");
es-app/src/ApiSystem.cpp:586: system("batocera-controlcenter");
es-app/src/ApiSystem.cpp:595: std::string command = "batocera-kodi " + commandline;
es-app/src/ApiSystem.cpp:643: return executeScript("batocera-wifi enable \"" + ssid + "\" \"" + key + "\" \"" + country + "\"");
es-app/src/ApiSystem.cpp:648: return executeScript("batocera-wifi enable \"" + ssid + "\" \"" + key + "\"");
es-app/src/ApiSystem.cpp:654: return executeScript("batocera-wifi disable");
es-app/src/ApiSystem.cpp:670: return executeScript("batocera-bluetooth enable 2>&1 >/dev/null");
es-app/src/ApiSystem.cpp:675: return executeScript("batocera-bluetooth disable");
es-app/src/ApiSystem.cpp:680: executeScript("batocera-bluetooth live_devices", func);
es-app/src/ApiSystem.cpp:685: executeScript("batocera-bluetooth stop_live_devices");
es-app/src/ApiSystem.cpp:690: return executeScript("batocera-bluetooth trust " + deviceName);
es-app/src/ApiSystem.cpp:695: return executeScript("batocera-bluetooth connect " + deviceName);
es-app/src/ApiSystem.cpp:700: return executeScript("batocera-bluetooth disconnect " + deviceName);
es-app/src/ApiSystem.cpp:705: return executeScript("batocera-bluetooth remove " + deviceName);
es-app/src/ApiSystem.cpp:710: return executeScript("batocera-bluetooth trust input", func).second == 0;
es-app/src/ApiSystem.cpp:715: return executeEnumerationScript("batocera-bluetooth list");
es-app/src/ApiSystem.cpp:720: return executeEnumerationScript("batocera-config storage list");
es-app/src/ApiSystem.cpp:726: return executeEnumerationScript("batocera-resolution listModes");
es-app/src/ApiSystem.cpp:728: return executeEnumerationScript("batocera-resolution --screen \"" + output + "\" listModes");
es-app/src/ApiSystem.cpp:734: return executeEnumerationScript("batocera-wine-runners");
es-app/src/ApiSystem.cpp:739: return executeEnumerationScript("batocera-sync list");
es-app/src/ApiSystem.cpp:744: return executeEnumerationScript("batocera-install listDisks");
es-app/src/ApiSystem.cpp:749: return executeEnumerationScript("batocera-install listArchs");
es-app/src/ApiSystem.cpp:754: return executeEnumerationScript("batocera-overclock list");
es-app/src/ApiSystem.cpp:759: return executeEnumerationScript("batocera-info --full");
es-app/src/ApiSystem.cpp:768: std::string cmd = "batocera-systems";
es-app/src/ApiSystem.cpp:815: return executeScript("batocera-support");
es-app/src/ApiSystem.cpp:827: oss << "batocera-config storage current";
es-app/src/ApiSystem.cpp:844: return executeScript("batocera-config storage " + selected);
es-app/src/ApiSystem.cpp:849: return executeScript("batocera-gameforce buttonColorLed " + selected);
es-app/src/ApiSystem.cpp:854: return executeScript("batocera-gameforce powerLed " + selected);
es-app/src/ApiSystem.cpp:886: return executeScript("batocera-config forgetBT");
es-app/src/ApiSystem.cpp:894: oss << "batocera-config getRootPassword";
es-app/src/ApiSystem.cpp:912: return executeEnumerationScript("batocera-config lsoutputs");
es-app/src/ApiSystem.cpp:923: return executeEnumerationScript("batocera-audio list");
es-app/src/ApiSystem.cpp:935: oss << "batocera-audio get";
es-app/src/ApiSystem.cpp:958: oss << "batocera-audio set" << " '" << selected << "'";
es-app/src/ApiSystem.cpp:974: return executeEnumerationScript("batocera-audio list-profiles");
es-app/src/ApiSystem.cpp:986: oss << "batocera-audio get-profile";
es-app/src/ApiSystem.cpp:1009: oss << "batocera-audio set-profile" << " '" << selected << "'";
es-app/src/ApiSystem.cpp:1286: auto lines = executeEnumerationScript("batocera-es-thebezelproject list");
es-app/src/ApiSystem.cpp:1311: return executeScript("batocera-es-thebezelproject install " + bezelsystem, func);
es-app/src/ApiSystem.cpp:1316: return executeScript("batocera-es-thebezelproject remove " + bezelsystem, func);
es-app/src/ApiSystem.cpp:1663: executeScript("batocera-led-handheld block_color_changes");
es-app/src/ApiSystem.cpp:1669: executeScript("batocera-led-handheld block_color_changes");
es-app/src/ApiSystem.cpp:1690: executeScript("batocera-led-handheld block_color_changes"); // temporarily prevent changes from external daemon
es-app/src/ApiSystem.cpp:1699: executeScript("batocera-led-handheld block_color_changes");
es-app/src/ApiSystem.cpp:1762: executeScript("batocera-led-handheld set_color_force_dec " + 
es-app/src/ApiSystem.cpp:1902: executeScript("batocera-led-handheld set_brightness " + std::to_string(value));
es-app/src/ApiSystem.cpp:2008: executeScript("batocera-led-handheld unblock_color_changes");
es-app/src/ApiSystem.cpp:2011: executeScript("batocera-led-handheld rainbow");
es-app/src/ApiSystem.cpp:2013: executeScript("batocera-led-handheld chroma");
es-app/src/ApiSystem.cpp:2015: executeScript("batocera-led-handheld pulse");
es-app/src/ApiSystem.cpp:2069: return executeEnumerationScript(scan ? "batocera-wifi scanlist" : "batocera-wifi list");
es-app/src/ApiSystem.cpp:2146: executables.push_back("batocera-wifi");
es-app/src/ApiSystem.cpp:2149: executables.push_back("batocera-bluetooth");
es-app/src/ApiSystem.cpp:2152: executables.push_back("batocera-resolution");
es-app/src/ApiSystem.cpp:2155: executables.push_back("batocera-systems");
es-app/src/ApiSystem.cpp:2158: executables.push_back("batocera-format");
es-app/src/ApiSystem.cpp:2161: executables.push_back("batocera-overclock");
es-app/src/ApiSystem.cpp:2171: executables.push_back("batocera-store");
es-app/src/ApiSystem.cpp:2174: executables.push_back("batocera-es-thebezelproject");
es-app/src/ApiSystem.cpp:2177: executables.push_back("batocera-padsinfo");
es-app/src/ApiSystem.cpp:2183: executables.push_back("batocera-preupdate-gamelists-hook");
es-app/src/ApiSystem.cpp:2186: executables.push_back("batocera-timezone");
es-app/src/ApiSystem.cpp:2189: executables.push_back("batocera-audio");
es-app/src/ApiSystem.cpp:2192: executables.push_back("batocera-sync");
es-app/src/ApiSystem.cpp:2195: executables.push_back("batocera-install");
es-app/src/ApiSystem.cpp:2198: executables.push_back("batocera-support");
es-app/src/ApiSystem.cpp:2201: executables.push_back("batocera-upgrade");
es-app/src/ApiSystem.cpp:2204: executables.push_back("batocera-upgrade-torrent");
es-app/src/ApiSystem.cpp:2209: executables.push_back("batocera-version");
es-app/src/ApiSystem.cpp:2213: executables.push_back("batocera-planemode");
es-app/src/ApiSystem.cpp:2216: executables.push_back("batocera-services");
es-app/src/ApiSystem.cpp:2219: executables.push_back("batocera-backglass");
es-app/src/ApiSystem.cpp:2222: executables.push_back("batocera-nfc");
es-app/src/ApiSystem.cpp:2282: return executeEnumerationScript("batocera-format listDisks");
es-app/src/ApiSystem.cpp:2293: return executeEnumerationScript("batocera-format listFstypes");
es-app/src/ApiSystem.cpp:2298: return executeScript("batocera-format format " + disk + " " + format, func).second;
es-app/src/ApiSystem.cpp:2416: auto res = executeEnumerationScript("batocera-store list");
es-app/src/ApiSystem.cpp:2485: return executeScript("batocera-store install \"" + name + "\"", func);
es-app/src/ApiSystem.cpp:2490: return executeScript("batocera-store remove \"" + name + "\"", func);
es-app/src/ApiSystem.cpp:2495: executeScript("batocera-store refresh");
es-app/src/ApiSystem.cpp:2496: executeScript("batocera-store clean-all");
es-app/src/ApiSystem.cpp:2501: executeScript("batocera-preupdate-gamelists-hook");
es-app/src/ApiSystem.cpp:2506: executeScript("batocera-store update");
es-app/src/ApiSystem.cpp:2617: auto cmd = executeEnumerationScript("batocera-timezone get");
es-app/src/ApiSystem.cpp:2621: cmd = executeEnumerationScript("batocera-timezone detect");
es-app/src/ApiSystem.cpp:2631: return executeScript("batocera-timezone set \"" + tz + "\"");
es-app/src/ApiSystem.cpp:2640: auto res = executeEnumerationScript("batocera-padsinfo");
es-app/src/ApiSystem.cpp:2721: return executeScript("batocera-es-swissknife --emukill");
es-app/src/ApiSystem.cpp:2727: executeScript("/usr/bin/batocera-shutdown gui");
es-app/src/ApiSystem.cpp:2750: auto res = executeEnumerationScript("batocera-planemode status");
es-app/src/ApiSystem.cpp:2765: return executeScript("batocera-planemode " + std::string(enable ? "enable" : "disable"));
es-app/src/ApiSystem.cpp:2774: auto slines = executeEnumerationScript("batocera-services list");
es-app/src/ApiSystem.cpp:2795: auto res = executeEnumerationScript("batocera-joysticks-hotkeys");
es-app/src/ApiSystem.cpp:2838: return executeEnumerationScript("batocera-joysticks-hotkeys --values");
es-app/src/ApiSystem.cpp:2846: auto res = executeEnumerationScript("batocera-hotkeys --values");
es-app/src/ApiSystem.cpp:2889: executeScript("batocera-joysticks-hotkeys " + params);
es-app/src/ApiSystem.cpp:2897: auto res = executeEnumerationScript("batocera-hotkeys --detect");
es-app/src/ApiSystem.cpp:2941: auto res = executeEnumerationScript("batocera-hotkeys");
es-app/src/ApiSystem.cpp:3100: executeScript("batocera-hotkeys --set --config " + config + " --key " + key + " --action " + action);
es-app/src/ApiSystem.cpp:3105: executeScript("batocera-hotkeys --remove --config " + config + " --key " + key);
es-app/src/ApiSystem.cpp:3113: auto res = executeEnumerationScript("batocera-hotkeys --values");
es-app/src/ApiSystem.cpp:3210: auto res = executeEnumerationScript("batocera-hotkeys --detect --count 1 --nowait --evformat --device " + device_path);
es-app/src/ApiSystem.cpp:3248: auto slines = executeEnumerationScript("batocera-backglass list-themes");
es-app/src/ApiSystem.cpp:3259: executeScript("/usr/bin/batocera-backglass restart");
es-app/src/ApiSystem.cpp:3270: bool res = executeScript("batocera-services " + std::string(enable ? "enable" : "disable") + " " + serviceName);
es-app/src/ApiSystem.cpp:3272: res = executeScript("batocera-services " + std::string(enable ? "start" : "stop") + " " + serviceName);
es-app/src/ApiSystem.cpp:3279: return executeEnumerationScript("batocera-storage-manager list_ejectable");
es-app/src/ApiSystem.cpp:3284: std::string cmd = "batocera-storage-manager eject \"" + mountPath + "\"";
es-app/src/ApiSystem.cpp:3290: std::string cmd = "batocera-storage-manager merge \"" + mountPath + "\"";
es-app/src/ApiSystem.cpp:3296: std::string cmd = "batocera-storage-manager format \"" + device + "\" \"" + fsType + "\"";
es-app/src/ApiSystem.cpp:3302: std::string cmd = "batocera-storage-manager ignore \"" + deviceId + "\"";
es-app/src/ApiSystem.cpp:3307: return Utils::FileSystem::exists("/var/run/batocera-nfc.running");
es-app/src/ApiSystem.cpp:3311: std::string cmd = "batocera-nfc --write \"" + game + "\"";
es-app/src/Win32ApiSystem.cpp:29:#define VERSIONURL "https://github.com/fabricecaruso/batocera-emulationstation/releases/download/continuous-stable/version.info"
es-app/src/Win32ApiSystem.cpp:30:#define UPDATEURL "https://github.com/fabricecaruso/batocera-emulationstation/releases/download/continuous-stable/EmulationStation-Win32.zip"
es-app/src/Win32ApiSystem.cpp:32:#define LAUNCHERURL "https://github.com/fabricecaruso/batocera-ports/releases/download/continuous/batocera-ports.zip"
es-app/src/Win32ApiSystem.cpp:95: executables.push_back("batocera-wifi");
es-app/src/Win32ApiSystem.cpp:103: executables.push_back("batocera-bluetooth");
es-app/src/Win32ApiSystem.cpp:108: executables.push_back("batocera-resolution");
es-app/src/Win32ApiSystem.cpp:112: executables.push_back("batocera-systems");
es-app/src/Win32ApiSystem.cpp:125: executables.push_back("batocera-store");
es-app/src/Win32ApiSystem.cpp:140: executables.push_back("batocera-padsinfo");
es-app/src/Win32ApiSystem.cpp:147: executables.push_back("batocera-services");
es-app/src/Win32ApiSystem.cpp:165: std::string path = Paths::findEmulationStationFile("batocera-store.cfg");
es-app/src/Win32ApiSystem.cpp:847: if (downloadFile(url, zipFile, "batocera-ports", func))
es-app/src/Win32ApiSystem.cpp:850: func(std::string("Extracting batocera-ports"));
es-app/src/Win32ApiSystem.cpp:938: // This is a Batocera-Linux ('batocera-upgrade') function only (update from USB-key). 
es-app/src/Win32ApiSystem.cpp:1264: return executeScript("batocera-bluetooth forgetBT");
es-app/src/guis/GuiMenu.cpp:1507: auto layouts = getScriptOutput("/usr/bin/batocera-keyboard list-layouts");
es-app/src/guis/GuiMenu.cpp:1526: auto variants = getScriptOutput("/usr/bin/batocera-keyboard list-variants " + layoutCode);
es-app/src/guis/GuiMenu.cpp:1548: auto variants = getScriptOutput("/usr/bin/batocera-keyboard list-variants " + newLayout);
es-app/src/guis/GuiMenu.cpp:1568: std::string cmd = "/usr/bin/batocera-keyboard set \"" + selLayout + "\" \"" + selVariant + "\"";
resources/services/index.html:16:<!-- See REST Api list on https://github.com/batocera-linux/batocera-emulationstation/blob/master/es-app/src/services/HttpServerThread.cpp#L25
CMakeLists.txt:47: if (IS_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/../batocera-emulationstation-win32-dependencies)
CMakeLists.txt:48: set(CUSTOM_LIBDIR ${CMAKE_CURRENT_SOURCE_DIR}/../batocera-emulationstation-win32-dependencies)
CMakeLists.txt:57: GIT_REPOSITORY "https://github.com/batocera-linux/batocera-emulationstation-win32-dependencies.git"
```

## 6. Fichiers de config batocera.conf / settings

Regex: `batocera\.conf|batocera-settings|system\.conf`

**3 occurrence(s)**

```
es-app/src/ApiSystem.cpp:1995: // Check batocera.conf for "led.enabled" setting, default to "1" (true) if not found
es-core/src/Paths.cpp:41: mSystemConfFilePath = mUserEmulationStationPath + "/batocera.conf";
es-core/src/Paths.cpp:70: mSystemConfFilePath = "/userdata/system/batocera.conf";
```

## 7. Fichiers drapeaux /tmp (restart, shutdown...)

Regex: `/tmp/`

**32 occurrence(s)**

```
es-app/src/ApiSystem.cpp:263: std::string downloadCommand = "curl --connect-timeout 10 -m 30 -L -f -s -o /tmp/batocera-upgrade "
es-app/src/ApiSystem.cpp:265: "&& chmod +x /tmp/batocera-upgrade";
es-app/src/ApiSystem.cpp:268: if (downloadRes == 0 && Utils::FileSystem::exists("/tmp/batocera-upgrade"))
es-app/src/ApiSystem.cpp:271: upgradeScriptPath = "/tmp/batocera-upgrade";
es-app/src/ApiSystem.cpp:288: if (upgradeScriptPath == "/tmp/batocera-upgrade") {
es-app/src/ApiSystem.cpp:289: Utils::FileSystem::removeFile("/tmp/batocera-upgrade");
es-app/src/ApiSystem.cpp:309: if (upgradeScriptPath == "/tmp/batocera-upgrade") {
es-app/src/ApiSystem.cpp:310: Utils::FileSystem::removeFile("/tmp/batocera-upgrade");
es-app/src/ApiSystem.cpp:2260: Utils::FileSystem::removeFile("/tmp/emulationstation.ready");
es-app/src/ApiSystem.cpp:2264: FILE* fd = fopen("/tmp/emulationstation.ready", "w");
es-app/src/ApiSystem.cpp:2271: return Utils::FileSystem::exists("/tmp/emulationstation.ready");
es-app/src/FileData.cpp:578: std::string fileInfo = "/tmp/game.xml";
es-app/src/FileData.cpp:675: std::string messageFile = "/tmp/launch_error.log";
es-app/src/Win32ApiSystem.cpp:984: return Utils::FileSystem::exists(Paths::getUserEmulationStationPath() + "/tmp/emulationstation.ready");
es-app/src/guis/GuiKeyboardLayout.cpp:68: Utils::FileSystem::removeFile("/tmp/kblayout-1.svg");
es-app/src/guis/GuiKeyboardLayout.cpp:69: Utils::FileSystem::removeFile("/tmp/kblayout-2.svg");
es-app/src/guis/GuiKeyboardLayout.cpp:161: auto newPath = "/tmp/kblayout" + std::string(mImageToggle ? "-1" : "-2") + ".svg";
es-app/src/guis/GuiMenu.cpp:925: Utils::FileSystem::deleteDirectoryFiles(rootPath + "/tmp/");
es-core/src/Paths.cpp:87: mUserDecorationsPath = "/tmp/overlays/bezels";
es-core/src/components/VideoComponent.cpp:23: return Utils::FileSystem::getGenericPath(Paths::getUserEmulationStationPath() + "/tmp/");
es-core/src/components/VideoComponent.cpp:26: return "/tmp/";
es-core/src/components/WebImageComponent.cpp:132: std::string localFile = Paths::getUserEmulationStationPath() + "/tmp/" + uri.host + "/" + uri.path + queryCrc; 
es-core/src/resources/TextureData.cpp:316: std::string localFile = Utils::FileSystem::resolveRelativePath(val, Paths::getUserEmulationStationPath() + "/tmp/videothumbs/", true);
es-core/src/utils/Platform.cpp:262: touch("/tmp/restart.please");
es-core/src/utils/Platform.cpp:267: touch("/tmp/reboot.please");
es-core/src/utils/Platform.cpp:273: touch("/tmp/shutdown.please");
emulationstation.sh:5: rm -f /tmp/es-restart /tmp/es-sysrestart /tmp/es-shutdown
emulationstation.sh:8: [ -f /tmp/es-restart ] && continue
emulationstation.sh:9: if [ -f /tmp/es-sysrestart ]; then
emulationstation.sh:10: rm -f /tmp/es-sysrestart
emulationstation.sh:14: if [ -f /tmp/es-shutdown ]; then
emulationstation.sh:15: rm -f /tmp/es-shutdown
```

## 8. Exécutables en dur (/usr/bin, /bin, /sbin)

Regex: `"/(usr/)?(s?bin)/[a-zA-Z0-9_.-]+`

**13 occurrence(s)**

```
es-app/src/ApiSystem.cpp:2207: return (Utils::FileSystem::exists("/usr/sbin/pm-suspend") && Utils::FileSystem::exists("/usr/bin/pm-is-supported") && executeScript("/usr/bin/pm-is-supported --suspend"));
es-app/src/ApiSystem.cpp:2727: executeScript("/usr/bin/batocera-shutdown gui");
es-app/src/ApiSystem.cpp:2733: executeScript("/usr/bin/virtual-sindenlightgun-remap");
es-app/src/ApiSystem.cpp:2739: executeScript("/usr/bin/virtual-wii-mouse-bar-remap");
es-app/src/ApiSystem.cpp:2745: executeScript("/usr/bin/steamdeckgun-remap");
es-app/src/ApiSystem.cpp:3259: executeScript("/usr/bin/batocera-backglass restart");
es-app/src/guis/GuiMenu.cpp:1507: auto layouts = getScriptOutput("/usr/bin/batocera-keyboard list-layouts");
es-app/src/guis/GuiMenu.cpp:1526: auto variants = getScriptOutput("/usr/bin/batocera-keyboard list-variants " + layoutCode);
es-app/src/guis/GuiMenu.cpp:1548: auto variants = getScriptOutput("/usr/bin/batocera-keyboard list-variants " + newLayout);
es-app/src/guis/GuiMenu.cpp:1568: std::string cmd = "/usr/bin/batocera-keyboard set \"" + selLayout + "\" \"" + selVariant + "\"";
es-core/src/Paths.cpp:73: mKodiPath = "/usr/bin/kodi";
es-core/src/components/VideoPlayerComponent.cpp:243: execve("/usr/bin/omxplayer", (char**)argv, (char**)env); // .bin
es-core/src/utils/Platform.cpp:177: execl("/bin/sh", "sh", "-c", cmdOutput.c_str(), (char *) NULL);
```

## 9. sudo / reboot / poweroff / shutdown

Regex: `\bsudo\b|reboot|poweroff|shutdown`

**64 occurrence(s)**

```
es-app/src/ApiSystem.cpp:611: case 10: // reboot code
es-app/src/ApiSystem.cpp:615: case 11: // shutdown code
es-app/src/ApiSystem.cpp:2727: executeScript("/usr/bin/batocera-shutdown gui");
es-app/src/guis/GuiMenu.cpp:568: s->setVariable("exitreboot", true);
es-app/src/guis/GuiMenu.cpp:580: s->setVariable("exitreboot", true);
es-app/src/guis/GuiMenu.cpp:605: s->setVariable("exitreboot", true);
es-app/src/guis/GuiMenu.cpp:640: s->setVariable("exitreboot", true);
es-app/src/guis/GuiMenu.cpp:652: s->setVariable("exitreboot", true);
es-app/src/guis/GuiMenu.cpp:678: s->setVariable("exitreboot", true);
es-app/src/guis/GuiMenu.cpp:686: if (s->getVariable("exitreboot") && Settings::getInstance()->getBool("ExitOnRebootRequired"))
es-app/src/guis/GuiMenu.cpp:724: s->setVariable("reboot", true);
es-app/src/guis/GuiMenu.cpp:807: s->setVariable("reboot", true);
es-app/src/guis/GuiMenu.cpp:808: s->setVariable("exitreboot", true);
es-app/src/guis/GuiMenu.cpp:938: s->addSaveFunc([s, menuFontScale] { if (Settings::getInstance()->setString("MenuFontScale", menuFontScale->getSelected())) s->setVariable("reboot", true); });
es-app/src/guis/GuiMenu.cpp:944: s->addSaveFunc([s, fontScale] { if (Settings::getInstance()->setString("FontScale", fontScale->getSelected())) s->setVariable("reboot", true); });
es-app/src/guis/GuiMenu.cpp:949: s->addSaveFunc([s, fullScreenMenus] { if (Settings::getInstance()->setString("FullScreenMenu", fullScreenMenus->getSelected())) s->setVariable("reboot", true); });
es-app/src/guis/GuiMenu.cpp:954: s->addSaveFunc([s, isSmallScreen] { if (Settings::getInstance()->setString("ForceSmallScreen", isSmallScreen->getSelected())) s->setVariable("reboot", true); });
es-app/src/guis/GuiMenu.cpp:1173: if (s->getVariable("reboot"))
es-app/src/guis/GuiMenu.cpp:1488: s->setVariable("exitreboot", true);
es-app/src/guis/GuiMenu.cpp:1557: std::string kbHelpText = _("Select the physical keyboard layout. A reboot may be required for changes to take full effect.");
es-app/src/guis/GuiMenu.cpp:1574: s->setVariable("reboot", true);
es-app/src/guis/GuiMenu.cpp:1741: s->setVariable("exitreboot", true);
es-app/src/guis/GuiMenu.cpp:1897: s->setVariable("exitreboot", true);
es-app/src/guis/GuiMenu.cpp:1972: s->setVariable("reboot", true);
es-app/src/guis/GuiMenu.cpp:2096: s->setVariable("reboot", true);
es-app/src/guis/GuiMenu.cpp:2156: s->setVariable("reboot", true);
es-app/src/guis/GuiMenu.cpp:2233: s->setVariable("reboot", true); 
es-app/src/guis/GuiMenu.cpp:2243: s->setVariable("reboot", true);
es-app/src/guis/GuiMenu.cpp:2267: if (s->getVariable("exitreboot") && Settings::getInstance()->getBool("ExitOnRebootRequired"))
es-app/src/guis/GuiMenu.cpp:2273: if (s->getVariable("reboot") || s->getVariable("exitreboot"))
es-app/src/main.cpp:169: }else if(strcmp(argv[i], "--exit-on-reboot-required") == 0)
es-app/src/services/httplib.h:442: virtual void shutdown() = 0;
es-app/src/services/httplib.h:453: shutdown_(false) {
es-app/src/services/httplib.h:481: void shutdown() override {
es-app/src/services/httplib.h:484: shutdown_ = true;
es-app/src/services/httplib.h:522: return !jobs_.empty() || shutdown_;
es-app/src/services/httplib.h:532: return !jobs_.empty() || shutdown_;
es-app/src/services/httplib.h:538: if (shutdown_ && jobs_.empty())
es-app/src/services/httplib.h:582: bool shutdown_;
es-app/src/services/httplib.h:1941:inline int shutdown_socket(socket_t sock) {
es-app/src/services/httplib.h:1943: return shutdown(sock, SD_BOTH);
es-app/src/services/httplib.h:1945: return shutdown(sock, SHUT_RDWR);
es-app/src/services/httplib.h:3760: detail::shutdown_socket(sock);
es-app/src/services/httplib.h:4153: task_queue->shutdown();
es-app/src/services/httplib.h:5120: detail::shutdown_socket(sock);
es-app/src/services/httplib.h:5219: SSL_shutdown(ssl);
es-app/src/services/httplib.h:5257: SSL_shutdown(ssl); // shutdown only if not already closed by remote
es-core/src/InputConfig.cpp:422: // 01 is some kind of a system device index, but can change upon reboot & we sometimes have 00&00&0000B7234380ED7E, and the order changes !
es-core/src/InputManager.cpp:1344: // back on the device index to keep a deterministic order across reboots, otherwise std::sort
es-core/src/utils/Platform.cpp:198: return system("shutdown -s -t 0");
es-core/src/utils/Platform.cpp:200: return system("shutdown -P -h now");
es-core/src/utils/Platform.cpp:207: return system("shutdown -r -t 0");
es-core/src/utils/Platform.cpp:209: return system("shutdown -r now");
es-core/src/utils/Platform.cpp:223: Scripting::fireEvent("quit", "reboot");
es-core/src/utils/Platform.cpp:224: Scripting::fireEvent("reboot");
es-core/src/utils/Platform.cpp:229: Scripting::fireEvent("quit", "shutdown");
es-core/src/utils/Platform.cpp:230: Scripting::fireEvent("shutdown");
es-core/src/utils/Platform.cpp:267: touch("/tmp/reboot.please");
es-core/src/utils/Platform.cpp:273: touch("/tmp/shutdown.please");
emulationstation.sh:5: rm -f /tmp/es-restart /tmp/es-sysrestart /tmp/es-shutdown
emulationstation.sh:11: sudo reboot
emulationstation.sh:14: if [ -f /tmp/es-shutdown ]; then
emulationstation.sh:15: rm -f /tmp/es-shutdown
emulationstation.sh:16: sudo poweroff
```

## 10. Exécution de commandes (system, popen, exec)

Regex: `\b(system|popen|execl?p?|executeScript|executeEnumerationScript)\s*\(`

**157 occurrence(s)**

```
es-app/src/ApiSystem.cpp:168: auto res = executeEnumerationScript(command);
es-app/src/ApiSystem.cpp:222: return executeScript("batocera-config overscan " + std::string(enable ? "enable" : "disable"));
es-app/src/ApiSystem.cpp:230: return executeScript("batocera-overclock set " + mode);
es-app/src/ApiSystem.cpp:236: auto result = executeScript("batocera-mitigations status", nullptr);
es-app/src/ApiSystem.cpp:246: return executeScript(std::string("batocera-mitigations ") + (enabled ? "on" : "off"));
es-app/src/ApiSystem.cpp:267: int downloadRes = system(downloadCommand.c_str());
es-app/src/ApiSystem.cpp:284: FILE *pipe = popen(updatecommand.c_str(), "r");
es-app/src/ApiSystem.cpp:327: FILE* pipe = popen(updatecommand.c_str(), "r");
es-app/src/ApiSystem.cpp:356: FILE *pipe = popen(updatecommand.c_str(), "r");
es-app/src/ApiSystem.cpp:385: FILE* pipe = popen("batocera-scraper", "r");
es-app/src/ApiSystem.cpp:413: if (!executeScript("ping -c 1 -W 2 -t 255 8.8.8.8"))
es-app/src/ApiSystem.cpp:416: if (!executeScript("ping -c 1 -W 2 -t 255 1.1.1.1"))
es-app/src/ApiSystem.cpp:419: return executeScript("ping -c 1 -W 2 -t 255 9.9.9.9");
es-app/src/ApiSystem.cpp:429: FILE *pipe = popen("batocera-upgrade-torrent --is-file-ready-to-update", "r");
es-app/src/ApiSystem.cpp:447: std::vector<std::string> results = executeEnumerationScript("batocera-upgrade-torrent --status");
es-app/src/ApiSystem.cpp:460: FILE *pipe = popen(updatecommand.c_str(), "r");
es-app/src/ApiSystem.cpp:490: FILE *pipe = popen("batocera-upgrade --check-media-upgrade", "r");
es-app/src/ApiSystem.cpp:508: FILE *pipe = popen("batocera-architecture-compatibility", "r");
es-app/src/ApiSystem.cpp:534: FILE *pipe = popen("batocera-upgrade --check-upgrade", "r");
es-app/src/ApiSystem.cpp:586: system("batocera-controlcenter");
es-app/src/ApiSystem.cpp:599: int exitCode = system(command.c_str());
es-app/src/ApiSystem.cpp:631: int exitCode = system(command.c_str());
es-app/src/ApiSystem.cpp:643: return executeScript("batocera-wifi enable \"" + ssid + "\" \"" + key + "\" \"" + country + "\"");
es-app/src/ApiSystem.cpp:648: return executeScript("batocera-wifi enable \"" + ssid + "\" \"" + key + "\"");
es-app/src/ApiSystem.cpp:654: return executeScript("batocera-wifi disable");
es-app/src/ApiSystem.cpp:670: return executeScript("batocera-bluetooth enable 2>&1 >/dev/null");
es-app/src/ApiSystem.cpp:675: return executeScript("batocera-bluetooth disable");
es-app/src/ApiSystem.cpp:680: executeScript("batocera-bluetooth live_devices", func);
es-app/src/ApiSystem.cpp:685: executeScript("batocera-bluetooth stop_live_devices");
es-app/src/ApiSystem.cpp:690: return executeScript("batocera-bluetooth trust " + deviceName);
es-app/src/ApiSystem.cpp:695: return executeScript("batocera-bluetooth connect " + deviceName);
es-app/src/ApiSystem.cpp:700: return executeScript("batocera-bluetooth disconnect " + deviceName);
es-app/src/ApiSystem.cpp:705: return executeScript("batocera-bluetooth remove " + deviceName);
es-app/src/ApiSystem.cpp:710: return executeScript("batocera-bluetooth trust input", func).second == 0;
es-app/src/ApiSystem.cpp:715: return executeEnumerationScript("batocera-bluetooth list");
es-app/src/ApiSystem.cpp:720: return executeEnumerationScript("batocera-config storage list");
es-app/src/ApiSystem.cpp:726: return executeEnumerationScript("batocera-resolution listModes");
es-app/src/ApiSystem.cpp:728: return executeEnumerationScript("batocera-resolution --screen \"" + output + "\" listModes");
es-app/src/ApiSystem.cpp:734: return executeEnumerationScript("batocera-wine-runners");
es-app/src/ApiSystem.cpp:739: return executeEnumerationScript("batocera-sync list");
es-app/src/ApiSystem.cpp:744: return executeEnumerationScript("batocera-install listDisks");
es-app/src/ApiSystem.cpp:749: return executeEnumerationScript("batocera-install listArchs");
es-app/src/ApiSystem.cpp:754: return executeEnumerationScript("batocera-overclock list");
es-app/src/ApiSystem.cpp:759: return executeEnumerationScript("batocera-info --full");
es-app/src/ApiSystem.cpp:772: auto systems = executeEnumerationScript(cmd);
es-app/src/ApiSystem.cpp:815: return executeScript("batocera-support");
es-app/src/ApiSystem.cpp:828: FILE *pipe = popen(oss.str().c_str(), "r");
es-app/src/ApiSystem.cpp:844: return executeScript("batocera-config storage " + selected);
es-app/src/ApiSystem.cpp:849: return executeScript("batocera-gameforce buttonColorLed " + selected);
es-app/src/ApiSystem.cpp:854: return executeScript("batocera-gameforce powerLed " + selected);
es-app/src/ApiSystem.cpp:886: return executeScript("batocera-config forgetBT");
es-app/src/ApiSystem.cpp:895: FILE *pipe = popen(oss.str().c_str(), "r");
es-app/src/ApiSystem.cpp:912: return executeEnumerationScript("batocera-config lsoutputs");
es-app/src/ApiSystem.cpp:923: return executeEnumerationScript("batocera-audio list");
es-app/src/ApiSystem.cpp:936: FILE *pipe = popen(oss.str().c_str(), "r");
es-app/src/ApiSystem.cpp:959: int exitcode = system(oss.str().c_str());
es-app/src/ApiSystem.cpp:974: return executeEnumerationScript("batocera-audio list-profiles");
es-app/src/ApiSystem.cpp:987: FILE *pipe = popen(oss.str().c_str(), "r");
es-app/src/ApiSystem.cpp:1010: int exitcode = system(oss.str().c_str());
es-app/src/ApiSystem.cpp:1286: auto lines = executeEnumerationScript("batocera-es-thebezelproject list");
es-app/src/ApiSystem.cpp:1311: return executeScript("batocera-es-thebezelproject install " + bezelsystem, func);
es-app/src/ApiSystem.cpp:1316: return executeScript("batocera-es-thebezelproject remove " + bezelsystem, func);
es-app/src/ApiSystem.cpp:1355: auto ret = executeEnumerationScript(cmd);
es-app/src/ApiSystem.cpp:1406: auto lines = executeEnumerationScript(cmd);
es-app/src/ApiSystem.cpp:1487: bool ret = executeScript(cmd);
es-app/src/ApiSystem.cpp:1663: executeScript("batocera-led-handheld block_color_changes");
es-app/src/ApiSystem.cpp:1669: executeScript("batocera-led-handheld block_color_changes");
es-app/src/ApiSystem.cpp:1690: executeScript("batocera-led-handheld block_color_changes"); // temporarily prevent changes from external daemon
es-app/src/ApiSystem.cpp:1699: executeScript("batocera-led-handheld block_color_changes");
es-app/src/ApiSystem.cpp:1762: executeScript("batocera-led-handheld set_color_force_dec " + 
es-app/src/ApiSystem.cpp:1902: executeScript("batocera-led-handheld set_brightness " + std::to_string(value));
es-app/src/ApiSystem.cpp:2008: executeScript("batocera-led-handheld unblock_color_changes");
es-app/src/ApiSystem.cpp:2011: executeScript("batocera-led-handheld rainbow");
es-app/src/ApiSystem.cpp:2013: executeScript("batocera-led-handheld chroma");
es-app/src/ApiSystem.cpp:2015: executeScript("batocera-led-handheld pulse");
es-app/src/ApiSystem.cpp:2069: return executeEnumerationScript(scan ? "batocera-wifi scanlist" : "batocera-wifi list");
es-app/src/ApiSystem.cpp:2072:std::vector<std::string> ApiSystem::executeEnumerationScript(const std::string command)
es-app/src/ApiSystem.cpp:2078: FILE *pipe = popen(command.c_str(), "r");
es-app/src/ApiSystem.cpp:2094:std::pair<std::string, int> ApiSystem::executeScript(const std::string command, const std::function<void(const std::string)>& func)
es-app/src/ApiSystem.cpp:2098: FILE *pipe = popen(command.c_str(), "r");
es-app/src/ApiSystem.cpp:2118:bool ApiSystem::executeScript(const std::string command)
es-app/src/ApiSystem.cpp:2122: if (system(command.c_str()) == 0)
es-app/src/ApiSystem.cpp:2207: return (Utils::FileSystem::exists("/usr/sbin/pm-suspend") && Utils::FileSystem::exists("/usr/bin/pm-is-supported") && executeScript("/usr/bin/pm-is-supported --suspend"));
es-app/src/ApiSystem.cpp:2282: return executeEnumerationScript("batocera-format listDisks");
es-app/src/ApiSystem.cpp:2293: return executeEnumerationScript("batocera-format listFstypes");
es-app/src/ApiSystem.cpp:2298: return executeScript("batocera-format format " + disk + " " + format, func).second;
es-app/src/ApiSystem.cpp:2303: auto lines = executeEnumerationScript("pdfinfo \"" + fileName + "\"");
es-app/src/ApiSystem.cpp:2385: executeEnumerationScript("pdftoppm -r "+ squality + page +" \"" + fileName + "\" \""+ pdfFolder +"/" + prefix +"\"");
es-app/src/ApiSystem.cpp:2387: executeEnumerationScript("pdftoppm -jpeg -r "+ squality +" -cropbox" + page + " \"" + fileName + "\" \"" + pdfFolder + "/" + prefix + "\"");
es-app/src/ApiSystem.cpp:2416: auto res = executeEnumerationScript("batocera-store list");
es-app/src/ApiSystem.cpp:2485: return executeScript("batocera-store install \"" + name + "\"", func);
es-app/src/ApiSystem.cpp:2490: return executeScript("batocera-store remove \"" + name + "\"", func);
es-app/src/ApiSystem.cpp:2495: executeScript("batocera-store refresh");
es-app/src/ApiSystem.cpp:2496: executeScript("batocera-store clean-all");
es-app/src/ApiSystem.cpp:2501: executeScript("batocera-preupdate-gamelists-hook");
es-app/src/ApiSystem.cpp:2506: executeScript("batocera-store update");
es-app/src/ApiSystem.cpp:2617: auto cmd = executeEnumerationScript("batocera-timezone get");
es-app/src/ApiSystem.cpp:2621: cmd = executeEnumerationScript("batocera-timezone detect");
es-app/src/ApiSystem.cpp:2631: return executeScript("batocera-timezone set \"" + tz + "\"");
es-app/src/ApiSystem.cpp:2640: auto res = executeEnumerationScript("batocera-padsinfo");
es-app/src/ApiSystem.cpp:2693: auto res = executeEnumerationScript("uname -m");
es-app/src/ApiSystem.cpp:2702: auto res = executeEnumerationScript("cat /boot/boot/batocera.board");
es-app/src/ApiSystem.cpp:2721: return executeScript("batocera-es-swissknife --emukill");
es-app/src/ApiSystem.cpp:2727: executeScript("/usr/bin/batocera-shutdown gui");
es-app/src/ApiSystem.cpp:2733: executeScript("/usr/bin/virtual-sindenlightgun-remap");
es-app/src/ApiSystem.cpp:2739: executeScript("/usr/bin/virtual-wii-mouse-bar-remap");
es-app/src/ApiSystem.cpp:2745: executeScript("/usr/bin/steamdeckgun-remap");
es-app/src/ApiSystem.cpp:2750: auto res = executeEnumerationScript("batocera-planemode status");
es-app/src/ApiSystem.cpp:2765: return executeScript("batocera-planemode " + std::string(enable ? "enable" : "disable"));
es-app/src/ApiSystem.cpp:2774: auto slines = executeEnumerationScript("batocera-services list");
es-app/src/ApiSystem.cpp:2795: auto res = executeEnumerationScript("batocera-joysticks-hotkeys");
es-app/src/ApiSystem.cpp:2838: return executeEnumerationScript("batocera-joysticks-hotkeys --values");
es-app/src/ApiSystem.cpp:2846: auto res = executeEnumerationScript("batocera-hotkeys --values");
es-app/src/ApiSystem.cpp:2889: executeScript("batocera-joysticks-hotkeys " + params);
es-app/src/ApiSystem.cpp:2897: auto res = executeEnumerationScript("batocera-hotkeys --detect");
es-app/src/ApiSystem.cpp:2941: auto res = executeEnumerationScript("batocera-hotkeys");
es-app/src/ApiSystem.cpp:2997: auto res = executeEnumerationScript("keyboardToPads --search");
es-app/src/ApiSystem.cpp:3045: auto res = executeEnumerationScript("keyboardToPads --config \""+config+"\" --get-config");
es-app/src/ApiSystem.cpp:3100: executeScript("batocera-hotkeys --set --config " + config + " --key " + key + " --action " + action);
es-app/src/ApiSystem.cpp:3105: executeScript("batocera-hotkeys --remove --config " + config + " --key " + key);
es-app/src/ApiSystem.cpp:3113: auto res = executeEnumerationScript("batocera-hotkeys --values");
es-app/src/ApiSystem.cpp:3174: executeScript(cmd + cmd_dev);
es-app/src/ApiSystem.cpp:3198: executeScript(cmd + cmd_dev);
es-app/src/ApiSystem.cpp:3210: auto res = executeEnumerationScript("batocera-hotkeys --detect --count 1 --nowait --evformat --device " + device_path);
es-app/src/ApiSystem.cpp:3248: auto slines = executeEnumerationScript("batocera-backglass list-themes");
es-app/src/ApiSystem.cpp:3259: executeScript("/usr/bin/batocera-backglass restart");
es-app/src/ApiSystem.cpp:3270: bool res = executeScript("batocera-services " + std::string(enable ? "enable" : "disable") + " " + serviceName);
es-app/src/ApiSystem.cpp:3272: res = executeScript("batocera-services " + std::string(enable ? "start" : "stop") + " " + serviceName);
es-app/src/ApiSystem.cpp:3279: return executeEnumerationScript("batocera-storage-manager list_ejectable");
es-app/src/ApiSystem.cpp:3285: return executeScript(cmd);
es-app/src/ApiSystem.cpp:3291: return executeScript(cmd);
es-app/src/ApiSystem.cpp:3297: return executeScript(cmd);
es-app/src/ApiSystem.cpp:3303: return executeScript(cmd);
es-app/src/ApiSystem.cpp:3312: return executeScript(cmd);
es-app/src/ApiSystem.h:414: virtual bool executeScript(const std::string command); 
es-app/src/ApiSystem.h:415: virtual std::pair<std::string, int> executeScript(const std::string command, const std::function<void(const std::string)>& func);
es-app/src/ApiSystem.h:416: virtual std::vector<std::string> executeEnumerationScript(const std::string command);
es-app/src/Win32ApiSystem.cpp:314:bool Win32ApiSystem::executeScript(const std::string command)
es-app/src/Win32ApiSystem.cpp:340:std::pair<std::string, int> Win32ApiSystem::executeScript(const std::string command, const std::function<void(const std::string)>& func)
es-app/src/Win32ApiSystem.cpp:366:std::vector<std::string> Win32ApiSystem::executeEnumerationScript(const std::string command)
es-app/src/Win32ApiSystem.cpp:1264: return executeScript("batocera-bluetooth forgetBT");
es-app/src/Win32ApiSystem.h:55: bool executeScript(const std::string command) override;
es-app/src/Win32ApiSystem.h:56: std::pair<std::string, int> executeScript(const std::string command, const std::function<void(const std::string)>& func) override;
es-app/src/Win32ApiSystem.h:57: std::vector<std::string> executeEnumerationScript(const std::string command) override;
es-app/src/guis/GuiMenu.cpp:1384: std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(command.c_str(), "r"), pclose);
es-app/src/guis/GuiMenu.cpp:1569: if (system(cmd.c_str()) == 0) {
es-core/src/InputManager.cpp:38:// 1. Device index - this is the "lowest level" identifier, and is just the Nth joystick plugged in to the system (like /dev/js#).
es-core/src/Scripting.cpp:88: static void executeScript(const std::string& script, const std::string& eventName, const std::string& arg1, const std::string& arg2, const std::string& arg3, bool allowAsync = true)
es-core/src/Scripting.cpp:177: executeScript(script, "", arg1, arg2, arg3, isAsyncEvent(eventName));
es-core/src/Scripting.cpp:205: executeScript(script.path, eventName, arg1, arg2, arg3, isAsyncEvent(eventName));
es-core/src/utils/Platform.cpp:166: int n = system(cmdOutput.c_str());
es-core/src/utils/Platform.cpp:177: execl("/bin/sh", "sh", "-c", cmdOutput.c_str(), (char *) NULL);
es-core/src/utils/Platform.cpp:198: return system("shutdown -s -t 0");
es-core/src/utils/Platform.cpp:200: return system("shutdown -P -h now");
es-core/src/utils/Platform.cpp:207: return system("shutdown -r -t 0");
es-core/src/utils/Platform.cpp:209: return system("shutdown -r now");
es-core/src/utils/Platform.cpp:247: // system(("touch " + filename).c_str());
```

## 11. Services réseau (wifi, bluetooth, ssh, samba)

Regex: `wifi|bluetooth|\bssh\b|samba|nmcli|connman`

**62 occurrence(s)**

```
es-app/src/ApiSystem.cpp:61:#define script_wifi "batocera-wifi"; // scanlist, list, enable X Y, disable
es-app/src/ApiSystem.cpp:62:#define script_bluetooth "batocera-bluetooth"; // trust, list, remove 
es-app/src/ApiSystem.cpp:643: return executeScript("batocera-wifi enable \"" + ssid + "\" \"" + key + "\" \"" + country + "\"");
es-app/src/ApiSystem.cpp:648: return executeScript("batocera-wifi enable \"" + ssid + "\" \"" + key + "\"");
es-app/src/ApiSystem.cpp:654: return executeScript("batocera-wifi disable");
es-app/src/ApiSystem.cpp:670: return executeScript("batocera-bluetooth enable 2>&1 >/dev/null");
es-app/src/ApiSystem.cpp:675: return executeScript("batocera-bluetooth disable");
es-app/src/ApiSystem.cpp:680: executeScript("batocera-bluetooth live_devices", func);
es-app/src/ApiSystem.cpp:685: executeScript("batocera-bluetooth stop_live_devices");
es-app/src/ApiSystem.cpp:690: return executeScript("batocera-bluetooth trust " + deviceName);
es-app/src/ApiSystem.cpp:695: return executeScript("batocera-bluetooth connect " + deviceName);
es-app/src/ApiSystem.cpp:700: return executeScript("batocera-bluetooth disconnect " + deviceName);
es-app/src/ApiSystem.cpp:705: return executeScript("batocera-bluetooth remove " + deviceName);
es-app/src/ApiSystem.cpp:710: return executeScript("batocera-bluetooth trust input", func).second == 0;
es-app/src/ApiSystem.cpp:715: return executeEnumerationScript("batocera-bluetooth list");
es-app/src/ApiSystem.cpp:2069: return executeEnumerationScript(scan ? "batocera-wifi scanlist" : "batocera-wifi list");
es-app/src/ApiSystem.cpp:2146: executables.push_back("batocera-wifi");
es-app/src/ApiSystem.cpp:2149: executables.push_back("batocera-bluetooth");
es-app/src/Win32ApiSystem.cpp:95: executables.push_back("batocera-wifi");
es-app/src/Win32ApiSystem.cpp:103: executables.push_back("batocera-bluetooth");
es-app/src/Win32ApiSystem.cpp:1264: return executeScript("batocera-bluetooth forgetBT");
es-app/src/guis/GuiControllersSettings.cpp:23:#define gettext_controllers_and_bluetooth_settings _("CONTROLLER & BLUETOOTH SETTINGS")
es-app/src/guis/GuiControllersSettings.cpp:31:// Windows build does not have bluetooth support, so affect the label for Windows
es-app/src/guis/GuiControllersSettings.cpp:36:#define controllers_settings_label gettext_controllers_and_bluetooth_settings
es-app/src/guis/GuiControllersSettings.cpp:112: bool baseBtEnabled = SystemConf::getInstance()->getBool("controllers.bluetooth.enabled");
es-app/src/guis/GuiControllersSettings.cpp:121: SystemConf::getInstance()->setBool("controllers.bluetooth.enabled", btEnabled);
es-app/src/guis/GuiControllersSettings.cpp:137: if (btEnabled != SystemConf::getInstance()->getBool("controllers.bluetooth.enabled"))
es-app/src/guis/GuiControllersSettings.cpp:139: SystemConf::getInstance()->setBool("controllers.bluetooth.enabled", btEnabled);
es-app/src/guis/GuiMenu.cpp:1096: if(SystemConf::getInstance()->getBool("controllers.bluetooth.enabled"))
es-app/src/guis/GuiMenu.cpp:4396: bool baseWifiEnabled = SystemConf::getInstance()->getBool("wifi.enabled");
es-app/src/guis/GuiMenu.cpp:4427: auto enable_wifi = std::make_shared<SwitchComponent>(mWindow);
es-app/src/guis/GuiMenu.cpp:4428: enable_wifi->setState(baseWifiEnabled);
es-app/src/guis/GuiMenu.cpp:4429: s->addWithLabel(_("ENABLE WI-FI"), enable_wifi, selectWifiEnable);
es-app/src/guis/GuiMenu.cpp:4432: const std::string baseSSID = SystemConf::getInstance()->get("wifi.ssid");
es-app/src/guis/GuiMenu.cpp:4433: const std::string baseKEY = SystemConf::getInstance()->get("wifi.key");
es-app/src/guis/GuiMenu.cpp:4435: const std::string baseCountry = SystemConf::getInstance()->get("wifi.country");
es-app/src/guis/GuiMenu.cpp:4440: s->addInputTextConfigRow(_("WI-FI SSID"), "wifi.ssid", false, false, &openWifiSettings);
es-app/src/guis/GuiMenu.cpp:4441: s->addInputTextConfigRow(_("WI-FI KEY"), "wifi.key", true);
es-app/src/guis/GuiMenu.cpp:4457: s->addSaveFunc([country] { SystemConf::getInstance()->set("wifi.country", country->getSelected()); });
es-app/src/guis/GuiMenu.cpp:4465: enable_wifi, window]
es-app/src/guis/GuiMenu.cpp:4467: bool wifienabled = enable_wifi->getState();
es-app/src/guis/GuiMenu.cpp:4469: SystemConf::getInstance()->setBool("wifi.enabled", wifienabled);
es-app/src/guis/GuiMenu.cpp:4471: if (wifienabled)
es-app/src/guis/GuiMenu.cpp:4473: std::string newSSID = SystemConf::getInstance()->get("wifi.ssid");
es-app/src/guis/GuiMenu.cpp:4474: std::string newKey = SystemConf::getInstance()->get("wifi.key");
es-app/src/guis/GuiMenu.cpp:4476: std::string newCountry = SystemConf::getInstance()->get("wifi.country");
es-app/src/guis/GuiMenu.cpp:4500: enable_wifi->setOnChangedCallback([this, s, baseWifiEnabled, enable_wifi]()
es-app/src/guis/GuiMenu.cpp:4502: bool wifienabled = enable_wifi->getState();
es-app/src/guis/GuiMenu.cpp:4503: if (baseWifiEnabled != wifienabled)
es-app/src/guis/GuiMenu.cpp:4505: SystemConf::getInstance()->setBool("wifi.enabled", wifienabled);
es-app/src/guis/GuiMenu.cpp:4507: if (wifienabled)
es-app/src/guis/GuiMenu.cpp:4510: std::string country = SystemConf::getInstance()->get("wifi.country");
es-app/src/guis/GuiMenu.cpp:4511: ApiSystem::getInstance()->enableWifi(SystemConf::getInstance()->get("wifi.ssid"), SystemConf::getInstance()->get("wifi.key"), country);
es-app/src/guis/GuiMenu.cpp:4513: ApiSystem::getInstance()->enableWifi(SystemConf::getInstance()->get("wifi.ssid"), SystemConf::getInstance()->get("wifi.key"));
es-core/src/InputConfig.cpp:82: // have a bluetooth parent ?
es-core/src/InputConfig.cpp:83: udev_device* bt_parent = udev_device_get_parent_with_subsystem_devtype(ud, "bluetooth", NULL);
es-core/src/Settings.cpp:413: mBoolMap["wifi.enabled"] = false;
es-core/src/SystemConf.cpp:36: { "wifi.enabled", "0" },
resources/arcaderoms.xml:37934: <rom id="samba" name="Samba De Amigo (JPN) (Rev B)" />
resources/arcaderoms.xml:37935: <rom id="samba2k" name="Samba de Amigo ver. 2000" />
resources/arcaderoms.xml:37936: <rom id="sambaa" name="Samba De Amigo (Rev A)" />
resources/arcaderoms.xml:37937: <rom id="sambap" name="Samba De Amigo (prototype)" />
```

## 12. Mises à jour / OS (upgrade, overlay, mount)

Regex: `upgrade|overlay|mount|umount|fstab|filesystem`

**119 occurrence(s)**

```
es-app/src/ApiSystem.cpp:56:#define script_upgrade "batocera-upgrade";
es-app/src/ApiSystem.cpp:100:unsigned long ApiSystem::getFreeSpaceGB(std::string mountpoint) 
es-app/src/ApiSystem.cpp:108: if ((statvfs(mountpoint.c_str(), &fiData)) >= 0)
es-app/src/ApiSystem.cpp:125:std::string ApiSystem::getFreeSpaceInfo(const std::string mountpoint)
es-app/src/ApiSystem.cpp:133: if ((statvfs(mountpoint.c_str(), &fiData)) < 0)
es-app/src/ApiSystem.cpp:255: std::string upgradeScriptPath = "batocera-upgrade";
es-app/src/ApiSystem.cpp:257: // Fetch the latest script from GitHub if performing an online upgrade
es-app/src/ApiSystem.cpp:261: func(_("Checking for latest upgrade script..."));
es-app/src/ApiSystem.cpp:263: std::string downloadCommand = "curl --connect-timeout 10 -m 30 -L -f -s -o /tmp/batocera-upgrade "
es-app/src/ApiSystem.cpp:264: "https://github.com/batocera-linux/batocera.linux/raw/refs/heads/master/package/batocera/core/batocera-scripts/scripts/batocera-upgrade "
es-app/src/ApiSystem.cpp:265: "&& chmod +x /tmp/batocera-upgrade";
es-app/src/ApiSystem.cpp:268: if (downloadRes == 0 && Utils::FileSystem::exists("/tmp/batocera-upgrade"))
es-app/src/ApiSystem.cpp:270: LOG(LogInfo) << "Successfully fetched the latest batocera-upgrade script from GitHub.";
es-app/src/ApiSystem.cpp:271: upgradeScriptPath = "/tmp/batocera-upgrade";
es-app/src/ApiSystem.cpp:275: LOG(LogWarning) << "Failed to fetch latest upgrade script from GitHub, falling back to built-in version.";
es-app/src/ApiSystem.cpp:279: std::string updatecommand = upgradeScriptPath + " --upgrade";
es-app/src/ApiSystem.cpp:281: updatecommand = upgradeScriptPath + " --media-upgrade --media";
es-app/src/ApiSystem.cpp:288: if (upgradeScriptPath == "/tmp/batocera-upgrade") {
es-app/src/ApiSystem.cpp:289: Utils::FileSystem::removeFile("/tmp/batocera-upgrade");
es-app/src/ApiSystem.cpp:295: FILE *flog = fopen(Utils::FileSystem::combine(Paths::getLogPath(), "batocera-upgrade.log").c_str(), "w");
es-app/src/ApiSystem.cpp:309: if (upgradeScriptPath == "/tmp/batocera-upgrade") {
es-app/src/ApiSystem.cpp:310: Utils::FileSystem::removeFile("/tmp/batocera-upgrade");
es-app/src/ApiSystem.cpp:429: FILE *pipe = popen("batocera-upgrade-torrent --is-file-ready-to-update", "r");
es-app/src/ApiSystem.cpp:447: std::vector<std::string> results = executeEnumerationScript("batocera-upgrade-torrent --status");
es-app/src/ApiSystem.cpp:458: std::string updatecommand = "batocera-upgrade-torrent --upgrade";
es-app/src/ApiSystem.cpp:465: FILE *flog = fopen(Utils::FileSystem::combine(Paths::getLogPath(), "batocera-upgrade-torrent.log").c_str(), "w");
es-app/src/ApiSystem.cpp:490: FILE *pipe = popen("batocera-upgrade --check-media-upgrade", "r");
es-app/src/ApiSystem.cpp:497: LOG(LogInfo) << "Can media upgrade";
es-app/src/ApiSystem.cpp:501: LOG(LogInfo) << "Cannot media upgrade";
es-app/src/ApiSystem.cpp:534: FILE *pipe = popen("batocera-upgrade --check-upgrade", "r");
es-app/src/ApiSystem.cpp:2201: executables.push_back("batocera-upgrade");
es-app/src/ApiSystem.cpp:2204: executables.push_back("batocera-upgrade-torrent");
es-app/src/ApiSystem.cpp:3282:bool ApiSystem::ejectDrive(const std::string& mountPath)
es-app/src/ApiSystem.cpp:3284: std::string cmd = "batocera-storage-manager eject \"" + mountPath + "\"";
es-app/src/ApiSystem.cpp:3288:bool ApiSystem::mergeDrive(const std::string& mountPath)
es-app/src/ApiSystem.cpp:3290: std::string cmd = "batocera-storage-manager merge \"" + mountPath + "\"";
es-app/src/ApiSystem.h:184: virtual unsigned long getFreeSpaceGB(std::string mountpoint);
es-app/src/ApiSystem.h:188: std::string getFreeSpaceInfo(const std::string mountpoint);
es-app/src/ApiSystem.h:215: virtual bool canArchitectureUpdate(std::string& architecture); // allow to upgrade architectures
es-app/src/ApiSystem.h:230: // Gets a list of drives that are safe to unmount.
es-app/src/ApiSystem.h:234: // Executes the eject command for a given mount path.
es-app/src/ApiSystem.h:235: bool ejectDrive(const std::string& mountPath);
es-app/src/ApiSystem.h:237: // Merges the specific drive mount path into the ROMs pool
es-app/src/ApiSystem.h:238: bool mergeDrive(const std::string& mountPath);
es-app/src/ApiSystem.h:240: // Prepares the specific device with partition the given filesystem
es-app/src/SystemData.cpp:385: // Recurse list files in medias folder, just to let OS build filesystem cache 
es-app/src/SystemData.cpp:392: // List files in folder, just to get OS build filesystem cache 
es-app/src/Win32ApiSystem.cpp:398:unsigned long Win32ApiSystem::getFreeSpaceGB(std::string mountpoint)
es-app/src/Win32ApiSystem.cpp:528: if (subFolder.empty() && name.find("/overlay/GameBezels/") == std::string::npos)
es-app/src/Win32ApiSystem.cpp:938: // This is a Batocera-Linux ('batocera-upgrade') function only (update from USB-key). 
es-app/src/Win32ApiSystem.h:18: unsigned long getFreeSpaceGB(std::string mountpoint) override;
es-app/src/guis/GuiMenu.cpp:2168: s->addEntry(_("EJECT AN EXTRA DISK"), true, [this] { openUnmountDriveSettings(); });
es-app/src/guis/GuiMenu.cpp:3038: // tattoo and controller overlays
es-app/src/guis/GuiMenu.cpp:4970: // tattoo and controller overlays
es-app/src/guis/GuiMenu.cpp:5620:void GuiMenu::openUnmountDriveSettings()
es-app/src/guis/GuiMenu.cpp:5658: window->pushGui(new GuiMsgBox(window, "ARE YOU SURE YOU WANT TO EJECT THIS DRIVE?\n\nThis will unmount the drive and remove it from the boot configuration.",
es-app/src/guis/GuiMenu.h:70: void openUnmountDriveSettings();
es-app/src/services/httplib.h:616: const char *mount_point = nullptr);
es-app/src/services/httplib.h:617: bool set_mount_point(const char *mount_point, const char *dir);
es-app/src/services/httplib.h:618: bool remove_mount_point(const char *mount_point);
es-app/src/services/httplib.h:3672:inline bool Server::set_base_dir(const char *dir, const char *mount_point) {
es-app/src/services/httplib.h:3673: return set_mount_point(mount_point, dir);
es-app/src/services/httplib.h:3676:inline bool Server::set_mount_point(const char *mount_point, const char *dir) {
es-app/src/services/httplib.h:3678: std::string mnt = mount_point ? mount_point : "/";
es-app/src/services/httplib.h:3687:inline bool Server::remove_mount_point(const char *mount_point) {
es-app/src/services/httplib.h:3689: if (it->first == mount_point) {
es-app/src/services/httplib.h:4040: const auto &mount_point = kv.first;
es-app/src/services/httplib.h:4044: if (!req.path.find(mount_point)) {
es-app/src/services/httplib.h:4045: std::string sub_path = "/" + req.path.substr(mount_point.size());
es-core/src/Paths.cpp:87: mUserDecorationsPath = "/tmp/overlays/bezels";
es-core/src/Window.cpp:730: // FPS overlay
es-core/src/Window.cpp:1496: std::string mountPoint = parts[4];
es-core/src/Window.cpp:1503: _("MOUNT") + ": " + mountPoint + "\n\n" +
es-core/src/Window.cpp:1507: auto mergeLambda = [this, mountPoint, processNext] {
es-core/src/Window.cpp:1511: std::thread([this, mountPoint, processNext]() {
es-core/src/Window.cpp:1512: bool success = ApiSystem::getInstance()->mergeDrive(mountPoint);
es-core/src/components/GridTileComponent.cpp:183: // If the overlay zindex < image zindex, then keep dimensions
es-core/src/components/GridTileComponent.cpp:417: bool overlayDrawn = false;
es-core/src/components/GridTileComponent.cpp:421: overlayDrawn = true;
es-core/src/components/GridTileComponent.cpp:457: if (mImageOverlay != nullptr && mImageOverlay->hasImage() && mImageOverlay->isVisible() && !overlayDrawn)
es-core/src/components/GridTileComponent.cpp:912: // Apply theme to the <image name="gridtile.overlay"> element
es-core/src/components/GridTileComponent.cpp:913: elem = theme->getElement(view, "gridtile.overlay", "image");
es-core/src/components/GridTileComponent.cpp:917: mImageOverlay->applyTheme(theme, view, "gridtile.overlay", ThemeFlags::ALL);
es-core/src/components/GridTileComponent.cpp:924: elem = theme->getElement(view, "gridtile.overlay:selected", "image");
es-core/src/components/GridTileComponent.cpp:998: mVideoPlayingProperties.ImageOverlay.applyTheme(theme->getElement(view, "gridtile.overlay:videoplaying", "image"));
es-core/src/components/IList.h:294: // update the title overlay opacity
es-core/src/components/VideoVlcComponent.cpp:596:// If Vlc2 dlls have been upgraded with vlc3 dlls, libqt4_plugin.dll is not compatible, so check if libvlc is 3.x then delete obsolete libqt4_plugin.dll
es-core/src/resources/TextureData.h:54: // Get the amount of memory used by this texture.
es-core/src/resources/TextureResource.h:65: // The texture data manager manages loading and unloading of filesystem based textures
es-core/src/utils/FileSystemUtil.cpp:287: // Performs filesystem I/O with NO lock held — safe to call concurrently.
es-core/src/utils/StringUtil.cpp:310: size_t moveCursor(const std::string& _string, const size_t _cursor, const int _amount) 
es-core/src/utils/StringUtil.cpp:314: if(_amount > 0) 
es-core/src/utils/StringUtil.cpp:316: for(int i = 0; i < _amount; ++i) 
es-core/src/utils/StringUtil.cpp:319: else if(_amount < 0) 
es-core/src/utils/StringUtil.cpp:321: for(int i = _amount; i < 0; ++i) 
es-core/src/utils/StringUtil.h:19: size_t moveCursor (const std::string& _string, const size_t _cursor, const int _amount);
es-core/src/utils/zip_file.hpp:390: /* mz_deflateBound() returns a (very) conservative upper bound on the amount of data that could be generated by deflate(), assuming flush is set to only
es-core/src/utils/zip_file.hpp:399: /* mz_compressBound() returns a (very) conservative upper bound on the amount of data that could be generated by calling mz_compress(). */
es-core/src/utils/zip_file.hpp:6464: /* The file is stored or the caller has requested the compressed data, calc amount to return. */
es-core/src/utils/zip_file.hpp:6541: /* Calc amount to return. */
es-core/src/utils/zip_file.hpp:8650: /* dest is zip64, so upgrade the data descriptor */
resources/arcaderoms.xml:1204: <rom id="alienaru" name="Alien Arena (Stargate upgrade)" />
resources/arcaderoms.xml:2726: <rom id="bbc_overlay" device="true" />
resources/arcaderoms.xml:2924: <rom id="berl16l" name="Mephisto Berlin 68000 (London upgrade)" />
resources/arcaderoms.xml:2927: <rom id="berlinpl" name="Mephisto Berlin Professional 68020 (London upgrade)" />
resources/arcaderoms.xml:4378: <rom id="cc3" name="Chess Challenger (upgraded version, 3 levels)" />
resources/arcaderoms.xml:11154: <rom id="gen32l" name="Mephisto Genius 68030 (London upgrade)" />
resources/arcaderoms.xml:16347: <rom id="knightsh01" name="Knights of the Round (Anger upgrade)" />
resources/arcaderoms.xml:27230: <rom id="m5fmount" name="Full Mountie (Empire) (MPU5)" />
resources/arcaderoms.xml:29376: <rom id="mountmon" name="Mountain Money (0100294V, NSW/ACT)" />
resources/arcaderoms.xml:29377: <rom id="mountmona" name="Mountain Money (0100289V, NSW/ACT)" />
resources/arcaderoms.xml:29378: <rom id="mountmonce" name="Mountain Money - Cash Express (AHG1629, US)" />
resources/arcaderoms.xml:29379: <rom id="mountmonu" name="Mountain Money (BHG1465, US)" />
resources/arcaderoms.xml:29380: <rom id="mountmonua" name="Mountain Money (BHG1464, US)" />
resources/arcaderoms.xml:49622: <rom id="toutrund" name="Turbo Out Run (Out Run upgrade) (bootleg of FD1094 317-0118 set)" />
resources/arcaderoms.xml:49624: <rom id="toutrunj" name="Turbo Out Run (Japan, Out Run upgrade, FD1094 317-0117)" />
resources/arcaderoms.xml:49627: <rom id="toutrunjd" name="Turbo Out Run (Japan, Out Run upgrade) (bootleg of FD1094 317-0117 set)" />
resources/gamesdb.xml:6535: <game id="bigmountain2000">
CMakeLists.txt:24:option(ENABLE_FILEMANAGER "Set to ON to enable f1 shortcut for filesystem" OFF)
```

## 13. Webserver / API HTTP interne

Regex: `HttpServer|webserver|localhost|127\.0\.0\.1`

**63 occurrence(s)**

```
es-app/CMakeLists.txt:52: ${CMAKE_CURRENT_SOURCE_DIR}/src/services/HttpServerThread.h
es-app/CMakeLists.txt:162: ${CMAKE_CURRENT_SOURCE_DIR}/src/services/HttpServerThread.cpp 
es-app/src/ApiSystem.cpp:2715: return "127.0.0.1";
es-app/src/Win32ApiSystem.cpp:1234: return "127.0.0.1";
es-app/src/ZaparooSupport.cpp:39: HttpReq req("http://127.0.0.1:7497/health", &options);
es-app/src/ZaparooSupport.cpp:62: HttpReq req("http://127.0.0.1:7497/api/v0.1", &options);
es-app/src/main.cpp:4:#include "services/HttpServerThread.h"
es-app/src/main.cpp:639: HttpServerThread httpServer(&window);
es-app/src/services/HttpServerThread.cpp:1:#include "HttpServerThread.h"
es-app/src/services/HttpServerThread.cpp:66:HttpServerThread::HttpServerThread(Window* window) : mWindow(window)
es-app/src/services/HttpServerThread.cpp:68: LOG(LogDebug) << "HttpServerThread : Starting";
es-app/src/services/HttpServerThread.cpp:70: mHttpServer = nullptr;
es-app/src/services/HttpServerThread.cpp:75: mThread = new std::thread(&HttpServerThread::run, this);
es-app/src/services/HttpServerThread.cpp:78:HttpServerThread::~HttpServerThread()
es-app/src/services/HttpServerThread.cpp:80: LOG(LogDebug) << "HttpServerThread : Exit";
es-app/src/services/HttpServerThread.cpp:82: if (mHttpServer != nullptr)
es-app/src/services/HttpServerThread.cpp:84: mHttpServer->stop();
es-app/src/services/HttpServerThread.cpp:85: delete mHttpServer;
es-app/src/services/HttpServerThread.cpp:86: mHttpServer = nullptr;
es-app/src/services/HttpServerThread.cpp:115:std::string HttpServerThread::getMimeType(const std::string &path)
es-app/src/services/HttpServerThread.cpp:130: if (req.remote_addr != "127.0.0.1" && !Settings::getInstance()->getBool("PublicWebAccess"))
es-app/src/services/HttpServerThread.cpp:132: LOG(LogWarning) << "HttpServerThread : Access disabled for " + req.remote_addr;
es-app/src/services/HttpServerThread.cpp:142:void HttpServerThread::run()
es-app/src/services/HttpServerThread.cpp:144: mHttpServer = new httplib::Server();
es-app/src/services/HttpServerThread.cpp:146: mHttpServer->new_task_queue = [] {
es-app/src/services/HttpServerThread.cpp:150: mHttpServer->Get("/", [=](const httplib::Request & req, httplib::Response &res) 
es-app/src/services/HttpServerThread.cpp:158: mHttpServer->Get("/favicon.png", [](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:168: mHttpServer->Get("/index.html", [](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:220: mHttpServer->Get("/quit", [this](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:226: // http://127.0.0.1/quit?confirm=switchscreen
es-app/src/services/HttpServerThread.cpp:235: // http://127.0.0.1/quit?confirm=menu
es-app/src/services/HttpServerThread.cpp:245: mHttpServer->Get("/restart", [](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:253: mHttpServer->Get("/emukill", [](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:261: mHttpServer->Get("/caps", [](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:269: mHttpServer->Get("/systems", [](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:277: mHttpServer->Get("/runningGame", [](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:292: mHttpServer->Get("/isIdle", [](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:316: mHttpServer->Get(R"(/systems/(/?.*)/logo)", [](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:346: mHttpServer->Get(R"(/systems/(/?.*)/games)", [](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:363: mHttpServer->Get(R"(/systems/(/?.*)/games/(/?.*)/media/(/?.*))", [](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:400: mHttpServer->Post(R"(/systems/(/?.*)/games/(/?.*)/media/(/?.*))", [this](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:449: mHttpServer->Post(R"(/systems/(/?.*)/games/(/?.*))", [this](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:484: mHttpServer->Get(R"(/systems/(/?.*)/games/(/?.*))", [](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:507: mHttpServer->Get(R"(/systems/(/?.*))", [](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:526: mHttpServer->Get("/reloadgames", [this](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:538: mHttpServer->Post("/messagebox", [this](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:555: mHttpServer->Post("/notify", [this](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:570: mHttpServer->Post("/storage/event", [this](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:592: mHttpServer->Post("/launch", [this](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:626: mHttpServer->Post("/input", [this](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:653: mHttpServer->Post(R"(/addgames/(/?.*))", [this](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:732: mHttpServer->Post(R"(/removegames/(/?.*))", [this](const httplib::Request& req, httplib::Response& res)
es-app/src/services/HttpServerThread.cpp:807: mHttpServer->Get(R"(/resources/(/?.*))", [](const httplib::Request& req, httplib::Response& res) // (.*)
es-app/src/services/HttpServerThread.cpp:824: mHttpServer->Get(R"(/(/?.*))", [](const httplib::Request& req, httplib::Response& res) // (.*)
es-app/src/services/HttpServerThread.cpp:844: std::string ip = "127.0.0.1";
es-app/src/services/HttpServerThread.cpp:849: mHttpServer->listen(ip.c_str(), 1234);
es-app/src/services/HttpServerThread.h:11:class HttpServerThread
es-app/src/services/HttpServerThread.h:14: HttpServerThread(Window * window);
es-app/src/services/HttpServerThread.h:15: virtual ~HttpServerThread();
es-app/src/services/HttpServerThread.h:25: httplib::Server* mHttpServer;
es-core/src/utils/Platform.cpp:287: return "127.0.0.1";
es-core/src/utils/Platform.cpp:316: return std::string(szLocalIP); // "127.0.0.1"
resources/services/index.html:16:<!-- See REST Api list on https://github.com/batocera-linux/batocera-emulationstation/blob/master/es-app/src/services/HttpServerThread.cpp#L25
```

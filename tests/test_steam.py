# SPDX-License-Identifier: GPL-3.0-or-later
import signal

from esne import steam, steamrun

ACF = '"AppState"\n{{\n\t"appid"\t\t"{appid}"\n\t"name"\t\t"{name}"\n\t"StateFlags"\t\t"{flags}"\n}}\n'
VDF = '"libraryfolders"\n{\n\t"0"\n\t{\n\t\t"path"\t\t"%s"\n\t}\n}\n'


def library(root, games):
    apps = root / "steamapps"
    apps.mkdir(parents=True)
    for appid, name, flags in games:
        (apps / f"appmanifest_{appid}.acf").write_text(ACF.format(appid=appid, name=name, flags=flags))
    return apps


def test_installed_games_skip_tools_and_uninstalled(tmp_path):
    apps = library(tmp_path / "Steam", [("1245620", "ELDEN RING", 4), ("1493710", "Proton Experimental", 4),
                                        ("228980", "Steamworks Common Redistributables", 4), ("10", "Pas fini", 1026),
                                        ("620", "Portal 2", 6)])
    assert steam.installed_games([apps]) == [("1245620", "ELDEN RING"), ("620", "Portal 2")]


def test_libraries_follow_libraryfolders_vdf_without_duplicates(tmp_path):
    main = tmp_path / "Steam"
    library(main, [])
    second = tmp_path / "Jeux"
    library(second, [])
    (main / "steamapps" / "libraryfolders.vdf").write_text(VDF % second)
    found = steam.libraries([str(main), str(main)])
    assert found == [(main / "steamapps").resolve(), (second / "steamapps").resolve()]


def test_seed_creates_files_once_and_never_duplicates(tmp_path):
    roms = tmp_path / "roms"
    games = [("620", "Portal 2"), ("400", "Half-Life: Opposing/Force")]
    assert steam.seed(roms, games) == ["Portal 2.steam", "Half-Life- Opposing-Force.steam"]
    assert (roms / "steam" / "Portal 2.steam").read_text() == "620\n"
    (roms / "steam" / "Portal 2.steam").rename(roms / "steam" / "Mon portail.steam")  # renommé par l'utilisateur
    assert steam.seed(roms, games) == []


def fake_proc(tmp_path, entries):
    proc = tmp_path / "proc"
    proc.mkdir(exist_ok=True)
    for pid, words in entries.items():
        (proc / str(pid)).mkdir(exist_ok=True)
        (proc / str(pid) / "cmdline").write_bytes("\0".join(words).encode() + b"\0")
    (proc / "self").mkdir(exist_ok=True)
    return proc


def test_game_pids_match_the_reaper_of_that_game(tmp_path):
    proc = fake_proc(tmp_path, {10: ["reaper", "SteamLaunch", "AppId=620", "--", "game"], 11: ["reaper", "SteamLaunch", "AppId=42", "--"],
                                12: ["steam", "-silent"]})
    assert steamrun.game_pids("620", proc) == [10]


def test_run_waits_for_start_then_for_the_end(tmp_path):
    proc = fake_proc(tmp_path, {})
    started = []
    ticks = []

    def sleep(_):
        ticks.append(1)
        if len(ticks) == 2:  # le jeu apparaît après deux attentes
            fake_proc(tmp_path, {10: ["reaper", "SteamLaunch", "AppId=620"]})
        if len(ticks) == 5:  # puis disparaît
            (proc / "10" / "cmdline").unlink()
            (proc / "10").rmdir()

    code = steamrun.run("620", ["steam", "-silent"], proc, popen=lambda argv, **kw: started.append((argv, kw)), sleep=sleep)
    assert code == 0 and len(ticks) >= 5
    assert started[0][0] == ["steam", "-silent"] and started[0][1]["start_new_session"] is True


def test_run_times_out_when_the_game_never_starts(tmp_path):
    proc = fake_proc(tmp_path, {})
    now = iter(range(0, 10000, 100))
    code = steamrun.run("620", ["steam"], proc, popen=lambda *a, **k: None, sleep=lambda _: None, clock=lambda: next(now))
    assert code == 1


def test_sigterm_closes_the_game(tmp_path):
    proc = fake_proc(tmp_path, {10: ["reaper", "SteamLaunch", "AppId=620"]})
    killed = []

    def sleep(_):
        handler = signal.getsignal(signal.SIGTERM)
        handler(signal.SIGTERM, None)
        (proc / "10" / "cmdline").unlink()
        (proc / "10").rmdir()

    steamrun.run("620", ["steam"], proc, popen=lambda *a, **k: None, sleep=sleep, kill=lambda pid, sig: killed.append((pid, sig)))
    assert killed == [(10, signal.SIGTERM)]


def test_usage(capsys):
    assert steamrun.main(["620", "steam"]) == 2

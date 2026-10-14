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


def test_shutdown_command_keeps_the_program_but_drops_launch_arguments():
    assert steamrun.shutdown_command(["/usr/bin/steam", "-silent", "steam://rungameid/620"]) == ["/usr/bin/steam", "-shutdown"]
    assert steamrun.shutdown_command(["/usr/bin/flatpak", "run", "com.valvesoftware.Steam", "-silent", "steam://rungameid/1"]) == \
        ["/usr/bin/flatpak", "run", "com.valvesoftware.Steam", "-shutdown"]


def comm(tmp_path, pid, name):
    proc = fake_proc(tmp_path, {})
    (proc / str(pid)).mkdir(exist_ok=True)
    (proc / str(pid) / "comm").write_text(name + "\n")
    return proc


def test_steam_running_reads_comm(tmp_path):
    proc = fake_proc(tmp_path, {})
    assert steamrun.steam_running(proc) is False
    comm(tmp_path, 20, "steam")
    assert steamrun.steam_running(proc) is True


def test_close_shuts_down_steam_only_when_we_opened_it(tmp_path):
    for already_open in (False, True):
        base = tmp_path / str(already_open)
        base.mkdir()
        proc = fake_proc(base, {})
        if already_open:
            comm(base, 20, "steam")
        calls = []
        ticks = []

        def sleep(_):
            ticks.append(1)
            if len(ticks) == 1:
                fake_proc(base, {10: ["reaper", "SteamLaunch", "AppId=620"]})
            if len(ticks) == 2:
                (proc / "10" / "cmdline").unlink()
                (proc / "10").rmdir()
            if not already_open and calls[-1:] == [["/usr/bin/steam", "-shutdown"]] and (proc / "20").exists():
                (proc / "20" / "comm").unlink()
                (proc / "20").rmdir()

        def popen(argv, **kw):
            calls.append(argv)
            if len(calls) == 1 and not already_open:
                comm(base, 20, "steam")  # le client est ouvert par notre lancement

        steamrun.run("620", ["/usr/bin/steam", "-silent", "steam://rungameid/620"], proc, popen=popen, sleep=sleep, close=True)
        shut = [["/usr/bin/steam", "-shutdown"]] if not already_open else []
        assert calls[1:] == shut


def test_main_accepts_close_flag(monkeypatch):
    seen = {}
    monkeypatch.setattr(steamrun, "run", lambda appid, command, close=False: seen.update(appid=appid, command=command, close=close) or 0)
    assert steamrun.main(["--close", "620", "--", "steam", "-silent"]) == 0
    assert seen == {"appid": "620", "command": ["steam", "-silent"], "close": True}


def test_generator_adds_close_unless_kept_open(tmp_path, monkeypatch, esne_env):
    from esne.generators import standalone, steam as steam_generator
    from esne.generators.base import Context

    class Cfg:
        def __init__(self, **values):
            self.values = values

        def get(self, key, default=None):
            return self.values.get(key, default)

    monkeypatch.setattr(standalone.shutil, "which", lambda n: f"/usr/bin/{n}" if n == "steam" else None)
    rom = tmp_path / "Portal.steam"
    rom.write_text("620\n")
    def argv(**settings):
        return steam_generator.Steam().generate(Context(system="steam", rom=str(rom), config=Cfg(**settings), emulator="steam")).argv
    assert argv()[:3] == ["esne-steam-run", "--close", "620"]
    assert argv(steam_keep_open="1")[:2] == ["esne-steam-run", "620"]


def test_run_survives_a_gap_between_reapers(tmp_path):
    """Steam enchaîne plusieurs ``reaper``: un trou de quelques secondes ne signifie pas que le jeu est fini."""
    proc = fake_proc(tmp_path, {10: ["reaper", "SteamLaunch", "AppId=620"]})
    ticks = []

    def sleep(_):
        ticks.append(1)
        n = len(ticks)
        if n == 1:  # premier reaper disparaît
            (proc / "10" / "cmdline").unlink()
            (proc / "10").rmdir()
        if n == 6:  # le deuxième apparaît
            fake_proc(tmp_path, {11: ["reaper", "SteamLaunch", "AppId=620"]})
        if n == 9:  # fin de partie
            (proc / "11" / "cmdline").unlink()
            (proc / "11").rmdir()

    assert steamrun.run("620", ["steam"], proc, popen=lambda *a, **k: None, sleep=sleep) == 0
    assert len(ticks) > 9 + steamrun.GRACE_POLLS - 1


def stat(proc, pid, ppid):
    (proc / str(pid)).mkdir(exist_ok=True)
    (proc / str(pid) / "stat").write_text(f"{pid} (wine (x)) S {ppid} 1 1 0 -1\n")


def test_descendants_walks_the_whole_tree(tmp_path):
    proc = fake_proc(tmp_path, {})
    stat(proc, 10, 1)
    stat(proc, 20, 10)
    stat(proc, 30, 20)
    stat(proc, 40, 99)
    assert sorted(steamrun.descendants([10], proc)) == [20, 30]


def test_sigterm_also_closes_the_children_of_the_reaper_and_kills_survivors(tmp_path):
    proc = fake_proc(tmp_path, {10: ["reaper", "SteamLaunch", "AppId=620"]})
    stat(proc, 10, 1)
    stat(proc, 20, 10)
    sent = []

    def kill(pid, sig):
        sent.append((pid, sig))
        if pid == 10:  # le reaper meurt, pas le jeu
            (proc / "10" / "cmdline").unlink()
            (proc / "10" / "stat").unlink()
            (proc / "10").rmdir()

    def sleep(_):
        handler = signal.getsignal(signal.SIGTERM)
        if not sent:
            handler(signal.SIGTERM, None)

    steamrun.run("620", ["steam"], proc, popen=lambda *a, **k: None, sleep=sleep, kill=kill)
    assert (20, signal.SIGTERM) in sent and (10, signal.SIGTERM) in sent
    assert (20, signal.SIGKILL) in sent and (10, signal.SIGKILL) not in sent

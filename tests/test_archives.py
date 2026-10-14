import zipfile

from esne import archives


def write_info(path, extensions):
    path.write_text(f'display_name = "x"\nsupported_extensions = "{extensions}"\n')
    return path


def make_zip(path, files):
    with zipfile.ZipFile(path, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    return path


def test_supported_extensions(tmp_path):
    assert archives.supported_extensions(write_info(tmp_path / "a.info", "ZIP|7z|sfc")) == {"zip", "7z", "sfc"}
    assert archives.supported_extensions(tmp_path / "missing.info") is None


def test_pick_member_prefers_entry_files():
    names = ["track01.bin", "game.cue", "readme.txt"]
    assert archives.pick_member(names, {"bin", "cue"}) == "game.cue"
    assert archives.pick_member(names, {"nes"}) is None
    assert archives.pick_member(["dir/", "dir/a.nes"], {"nes"}) == "dir/a.nes"


def test_archive_given_as_is_when_core_reads_it_or_info_unknown(esne_env, tmp_path):
    z = make_zip(tmp_path / "g.zip", {"g.nes": "x"})
    assert archives.prepare(str(z), "nes", write_info(tmp_path / "i.info", "nes|zip")) == str(z)
    assert archives.prepare(str(z), "nes", None) == str(z)
    assert archives.prepare("/roms/g.nes", "nes", write_info(tmp_path / "i.info", "nes")) == "/roms/g.nes"


def test_zip_extracted_and_reused_then_only_last_game_kept(esne_env, tmp_path):
    info = write_info(tmp_path / "i.info", "nes")
    one = make_zip(tmp_path / "One.zip", {"inner name.nes": "1"})
    first = archives.prepare(str(one), "nes", info)
    assert first.endswith("/nes/One/One.nes")
    again = archives.prepare(str(one), "nes", info)
    assert again == first
    two = make_zip(tmp_path / "Two.zip", {"two.nes": "2"})
    second = archives.prepare(str(two), "nes", info)
    assert open(second).read() == "2"
    assert not __import__("pathlib").Path(first).exists()


def test_multi_file_content_keeps_member_names(esne_env, tmp_path):
    z = make_zip(tmp_path / "Disc.zip", {"Disc.cue": "FILE", "Disc.bin": "BIN"})
    cue = archives.prepare(str(z), "psx", write_info(tmp_path / "i.info", "cue|bin"))
    assert cue.endswith("/Disc/Disc.cue") and open(cue.replace(".cue", ".bin")).read() == "BIN"


def test_no_matching_member_or_bad_zip_falls_back(esne_env, tmp_path):
    info = write_info(tmp_path / "i.info", "nes")
    z = make_zip(tmp_path / "t.zip", {"a.txt": "x"})
    assert archives.prepare(str(z), "nes", info) == str(z)
    bad = tmp_path / "bad.zip"
    bad.write_text("not a zip")
    assert archives.prepare(str(bad), "nes", info) == str(bad)


def test_7z_uses_available_tool_and_warns_without(esne_env, tmp_path, monkeypatch):
    info = write_info(tmp_path / "i.info", "nes")
    sevenz = tmp_path / "G.7z"
    sevenz.write_bytes(b"7z")
    assert archives.prepare(str(sevenz), "nes", info, which=lambda tool: None) == str(sevenz)

    listing = "Path = g.nes\nFolder = -\nSize = 1\n\n"

    def run(cmd, **kwargs):
        class Result:
            stdout = listing
        if cmd[1] == "x":
            out = next(c for c in cmd if c.startswith("-o"))[2:]
            (tmp_path / "ignored").mkdir(exist_ok=True)
            import pathlib
            pathlib.Path(out, "g.nes").write_text("N")
        return Result()

    monkeypatch.setattr(archives.subprocess, "run", run)
    result = archives.prepare(str(sevenz), "nes", info, which=lambda tool: "/usr/bin/7z" if tool == "7z" else None)
    assert result.endswith("/G/G.nes") and open(result).read() == "N"

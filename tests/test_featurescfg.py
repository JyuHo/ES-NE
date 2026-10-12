# SPDX-License-Identifier: GPL-3.0-or-later
import xml.etree.ElementTree as ET

from esne import featurescfg, paths, systemscfg
from esne.generators import retroarch


def test_features_file_declares_libretro_options():
    emulator = ET.fromstring(featurescfg.render()).find("emulator")
    assert emulator.get("name") == "libretro"
    assert set(emulator.get("features").split(",")) == set(featurescfg.LIBRETRO_FEATURES)


def test_video_driver_option_declared_globally_and_for_libretro():
    root = ET.fromstring(featurescfg.render())
    for node in (root.find("globalFeatures"), root.find("emulator")):
        feature = node.find("feature")
        assert feature.get("value") == "video_driver"
        assert [c.get("value") for c in feature.findall("choice")] == ["vulkan", "glcore", "gl"]


def test_vulkan_available(tmp_path):
    assert not retroarch.vulkan_available((str(tmp_path),))
    (tmp_path / "radeon_icd.x86_64.json").write_text("{}")
    assert retroarch.vulkan_available((str(tmp_path),))


def make_shaders(tmp_path):
    (tmp_path / "crt").mkdir(parents=True)
    (tmp_path / "crt" / "crt-geom.slangp").write_text("")
    (tmp_path / "scanlines.glslp").write_text("")
    return [str(tmp_path)]


def test_find_shader_searches_subfolders(tmp_path):
    dirs = make_shaders(tmp_path)
    assert retroarch.find_shader("crt-geom", dirs) == tmp_path / "crt" / "crt-geom.slangp"
    assert retroarch.find_shader("scanlines", dirs) == tmp_path / "scanlines.glslp"
    assert retroarch.find_shader("absent", dirs) is None


def test_installed_sets_and_files(tmp_path):
    dirs = make_shaders(tmp_path / "libretro")
    names = featurescfg.installed_shader_sets(directories=dirs)
    assert names == ["crt-geom", "scanlines"]
    out = tmp_path / "cfg"
    files = featurescfg.write_shader_sets(out, names)
    assert (out / "crt-geom" / "rendering-defaults.yml") in files
    assert "shader: crt-geom" in files[0].read_text()


def test_genconfig_writes_features_and_shader_dirs(esne_env, monkeypatch, tmp_path):
    dirs = make_shaders(tmp_path / "libretro")
    monkeypatch.setattr(retroarch, "_shader_dirs", lambda: [__import__("pathlib").Path(d) for d in dirs])
    assert systemscfg.main([]) == 0
    assert (paths.config_dir() / "es_features.cfg").exists()
    assert (paths.data_dir() / "shaders" / "configs" / "crt-geom" / "rendering-defaults.yml").exists()

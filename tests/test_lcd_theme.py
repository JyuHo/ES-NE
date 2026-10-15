# SPDX-License-Identifier: GPL-3.0-or-later
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "contrib" / "trofeo-vision" / "esne_lcd_theme.py"
spec = importlib.util.spec_from_file_location("esne_lcd_theme", SCRIPT)
theme = importlib.util.module_from_spec(spec)
spec.loader.exec_module(theme)


def test_layout_covers_cpu_and_gpu_metrics():
    elements = theme.layout()
    assert [e["metric"] for e in elements] == [
        "cpu:temp", "cpu:usage", "cpu:freq", "gpu:primary:temp", "gpu:primary:usage", "gpu:primary:clock"]
    assert len({e["id"] for e in elements}) == 6
    assert all(0 <= e["x"] < theme.WIDTH and 0 <= e["y"] < theme.HEIGHT for e in elements)


def test_apply_keeps_the_rest_of_the_settings():
    data = {"app": {"language": "fr"}, "devices": {theme.DEVICE: {"brightness": 80, "mask_visible": True, "user_overlay_elements": []}}}
    out = theme.apply_settings(json.loads(json.dumps(data)), Path("/x/bg.png"), theme.layout())
    entry = out["devices"][theme.DEVICE]
    assert entry["brightness"] == 80 and out["app"] == {"language": "fr"}
    assert entry["background_path"] == "/x/bg.png" and entry["mask_visible"] is False and len(entry["user_overlay_elements"]) == 6
    with pytest.raises(KeyError):
        theme.apply_settings({"devices": {}}, Path("/x/bg.png"), [])


def test_background_has_the_screen_size():
    pytest.importorskip("PIL")
    assert theme.draw_background().size == (theme.WIDTH, theme.HEIGHT)

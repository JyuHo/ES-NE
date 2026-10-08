from esne.config import Config


def test_layers():
    c = Config({
        "global.ratio": "16/9",
        "snes.ratio": "4/3",
        'snes["mario.zip"].ratio': "core",
    })
    assert c.get("ratio") == "16/9"
    assert c.get("ratio", "snes") == "4/3"
    assert c.get("ratio", "snes", "mario.zip") == "core"
    assert c.get("ratio", "nes") == "16/9"
    assert c.get("missing", default="x") == "x"

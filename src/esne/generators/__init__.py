import importlib


def load_generator(name: str):
    mod = importlib.import_module(f"esne.generators.{name}")
    return mod.GENERATOR()

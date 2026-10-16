import sys, subprocess, time, os
from Xlib import X, display, XK
from Xlib.ext import xtest

ES, OUT, SYSTEMS = sys.argv[1], sys.argv[2], sys.argv[3:]
d = display.Display()


def key(name):
    code = d.keysym_to_keycode(XK.string_to_keysym(name))
    xtest.fake_input(d, X.KeyPress, code); d.sync(); time.sleep(0.05)
    xtest.fake_input(d, X.KeyRelease, code); d.sync()


def shot(name):
    subprocess.run(["import", "-window", "root", f"{OUT}/{name}.png"], check=False)


p = subprocess.Popen([ES, "--windowed", "--resolution", "1280", "800", "--no-splash", "--debug"], stdout=open(OUT + "/es.log", "w"), stderr=subprocess.STDOUT)
time.sleep(14)
# première utilisation : écran de config des touches possible → on tente Return pour passer
shot("00-start")
shot("search_pre")
key("y"); time.sleep(2); shot("extra-search"); key("Return"); time.sleep(1)
key("space"); time.sleep(2); shot("extra-quick"); key("Return"); time.sleep(1)
for n in range(len(SYSTEMS) + 2):
    shot(f"{n:02d}-system"); key("BackSpace"); time.sleep(2); shot(f"{n:02d}-gamelist")
    key("Return"); time.sleep(1); key("Right"); time.sleep(1.5)
p.terminate()

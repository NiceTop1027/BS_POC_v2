out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_introspect.log"


def log(s):
    open(out, "a", encoding="utf-8").write(str(s) + "\n")


log("BEGIN")
try:
    import sys

    log("sys.version=" + str(getattr(sys, "version", "?")))
    mods = sorted(sys.modules.keys())
    terms = ("asio", "MUI", "ui", "entity", "Entity", "avatar", "Avatar", "reload", "Launcher", "game", "combat")
    filtered = [m for m in mods if any(t in m for t in terms)]
    log("filtered_modules=" + repr(filtered[:300]))
    log("module_count=" + str(len(mods)))
except BaseException as e:
    log("sys dump failed " + repr(e))

for name in ("asiocore", "MUI", "MLauncher", "MReloadImporter", "MEngine"):
    try:
        mod = __import__(name)
        log("IMPORT " + name + " OK " + repr(mod))
        names = [x for x in dir(mod) if any(t in x for t in ("ent", "Ent", "Entity", "avatar", "Avatar", "player", "Player", "screen", "Screen", "Fake", "Board", "timer", "Timer"))]
        log("DIR " + name + " " + repr(names[:200]))
    except BaseException as e:
        log("IMPORT " + name + " FAIL " + repr(e))

try:
    gnames = [x for x in globals().keys() if any(t in x for t in ("asio", "MUI", "entity", "Entity", "game", "Game", "avatar", "Avatar"))]
    log("globals=" + repr(sorted(gnames)))
except BaseException as e:
    log("globals failed " + repr(e))

log("END")

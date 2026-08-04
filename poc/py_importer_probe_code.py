out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_importer_probe.log"


def log(s):
    open(out, "a", encoding="utf-8").write(str(s) + "\n")


def short(v, n=500):
    try:
        s = repr(v)
    except BaseException as e:
        s = "<repr failed %r>" % (e,)
    return s[:n] + ("..." if len(s) > n else "")


log("BEGIN")
for name in ("MImporter", "MReloadImporter", "MLauncher"):
    try:
        mod = __import__(name)
        log("MOD " + name + " " + short(mod))
        keys = sorted([k for k in dir(mod) if not k.startswith("__")])
        log("KEYS " + name + " " + short(keys, 2000))
        for k in keys:
            if any(t in k.lower() for t in ("open", "raw", "data", "file", "path", "package", "patch", "find", "loader")):
                try:
                    v = getattr(mod, k)
                    log("ATTR " + name + "." + k + " type=" + str(type(v)) + " val=" + short(v))
                except BaseException as e:
                    log("ATTR FAIL " + name + "." + k + " " + repr(e))
    except BaseException as e:
        log("MOD " + name + " FAIL " + repr(e))

try:
    import common.EntityManager as em

    loader = getattr(em, "__loader__", None)
    log("EntityManager loader type=" + str(type(loader)) + " val=" + short(loader))
    log("loader dir=" + short(sorted([x for x in dir(loader) if not x.startswith('__')]), 2000))
except BaseException as e:
    log("loader probe fail " + repr(e))
log("END")

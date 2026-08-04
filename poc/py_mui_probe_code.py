out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_mui_probe.log"


def log(s):
    open(out, "a", encoding="utf-8").write(str(s) + "\n")


def short(v, n=800):
    try:
        s = repr(v)
    except BaseException as e:
        s = "<repr failed %r>" % (e,)
    return s[:n] + ("..." if len(s) > n else "")


log("BEGIN")
try:
    import MUI

    for name in ("AddFakeBoardElement", "AddFakeBoardElement0", "AddFakeBoardElementWithBone", "RemoveFakeBoardElement", "CreateScreenText", "UpdateScreenText", "RemoveScreenText"):
        try:
            f = getattr(MUI, name)
            log(name + " repr=" + short(f))
            log(name + " doc=" + short(getattr(f, "__doc__", None), 1600))
            log(name + " textsig=" + short(getattr(f, "__text_signature__", None), 1600))
        except BaseException as e:
            log(name + " FAIL " + repr(e))
    for clsname in ("FakeBoardElementParam", "HarmTextParam"):
        cls = getattr(MUI, clsname)
        log(clsname + " doc=" + short(getattr(cls, "__doc__", None), 1600))
        try:
            obj = cls()
            log(clsname + " obj=" + short(obj) + " dir=" + short([n for n in dir(obj) if not n.startswith('__')], 2000))
            for attr in [n for n in dir(obj) if not n.startswith('__')]:
                try:
                    log(clsname + "." + attr + "=" + short(getattr(obj, attr)))
                except BaseException as e:
                    log(clsname + "." + attr + " FAIL " + repr(e))
        except BaseException as e:
            log(clsname + " init FAIL " + repr(e))
except BaseException as e:
    log("MUI block fail " + repr(e))
log("END")

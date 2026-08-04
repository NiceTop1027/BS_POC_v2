out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_entity_type_probe.log"


def log(s):
    open(out, "a", encoding="utf-8").write(str(s) + "\n")


def filt(names):
    terms = (
        "Name",
        "name",
        "Pos",
        "pos",
        "Position",
        "Bound",
        "bound",
        "Bone",
        "bone",
        "Outline",
        "outline",
        "Thermal",
        "Visible",
        "visible",
        "Team",
        "team",
        "Avatar",
        "avatar",
        "Player",
        "player",
        "Class",
        "class",
        "Prop",
        "prop",
    )
    return [n for n in names if any(t in n for t in terms)]


log("BEGIN")
try:
    import asiocore_64

    for objname, obj in (("entity_type", asiocore_64.entity), ("entity_obj", asiocore_64.entity())):
        try:
            names = sorted(dir(obj))
            log(objname + " filtered=" + repr(filt(names)[:500]))
            log(objname + " all_head=" + repr(names[:250]))
        except BaseException as e:
            log(objname + " dir fail " + repr(e))
except BaseException as e:
    log("asiocore block fail " + repr(e))
try:
    import MUI

    log("MUI FakeBoardElementParam dir=" + repr([n for n in dir(MUI.FakeBoardElementParam) if not n.startswith('__')][:250]))
    log("MUI HarmTextParam dir=" + repr([n for n in dir(MUI.HarmTextParam) if not n.startswith('__')][:250]))
except BaseException as e:
    log("MUI block fail " + repr(e))
log("END")

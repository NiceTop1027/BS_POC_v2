out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_manager_probe.log"


def log(s):
    open(out, "a", encoding="utf-8").write(str(s) + "\n")


def short(v, n=700):
    try:
        s = repr(v)
    except BaseException as e:
        s = "<repr failed %r>" % (e,)
    return s[:n] + ("..." if len(s) > n else "")


def dump_obj(label, obj):
    log("OBJ " + label + " type=" + str(type(obj)) + " val=" + short(obj))
    try:
        keys = sorted([k for k in dir(obj) if not k.startswith("__")])
        log("DIR " + label + " " + short(keys, 2500))
        terms = ("ent", "Ent", "entity", "Entity", "avatar", "Avatar", "player", "Player", "manager", "Manager", "map", "Map", "dict", "Dict", "all", "All", "local", "Local")
        for k in keys:
            if any(t in k for t in terms):
                try:
                    v = getattr(obj, k)
                    log("ATTR " + label + "." + k + " type=" + str(type(v)) + " val=" + short(v))
                except BaseException as e:
                    log("ATTR " + label + "." + k + " FAIL " + repr(e))
    except BaseException as e:
        log("DIR FAIL " + label + " " + repr(e))


log("BEGIN")
for modname, objnames in (
    ("common.EntityManager", ("EntityManager",)),
    ("common.Entity", ("Entity", "EntityManager")),
    ("common.EntityFactory", ("EntityFactory",)),
    ("client.ClientEntity", ("ClientEntity", "PlayerEntity", "AvatarEntity", "ClientAreaEntity")),
    ("gclient.gameplay.logic_base.entities.combat_avatar", ("CombatAvatar", "PlayerCombatAvatar")),
):
    try:
        mod = __import__(modname, fromlist=["*"])
        dump_obj(modname, mod)
        for objname in objnames:
            try:
                dump_obj(modname + "." + objname, getattr(mod, objname))
            except BaseException as e:
                log("GET " + modname + "." + objname + " FAIL " + repr(e))
    except BaseException as e:
        log("MOD " + modname + " FAIL " + repr(e))

try:
    import sys

    hits = []
    for mname, mod in list(sys.modules.items()):
        d = getattr(mod, "__dict__", {})
        for k, v in list(d.items()):
            if any(t in k for t in ("entity_manager", "EntityManager", "entities", "ENTITIES", "entity_map", "avatar_manager", "game_logic")):
                hits.append((mname, k, str(type(v)), short(v, 180)))
                if len(hits) >= 180:
                    raise StopIteration
except StopIteration:
    pass
except BaseException as e:
    log("module scan fail " + repr(e))
try:
    log("MODULE_SCAN " + short(hits, 8000))
except BaseException as e:
    log("module scan log fail " + repr(e))
log("END")

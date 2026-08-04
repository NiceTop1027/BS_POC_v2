out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_entity_probe.log"


def log(s):
    open(out, "a", encoding="utf-8").write(str(s) + "\n")


def short(v, n=260):
    try:
        s = repr(v)
    except BaseException as e:
        s = "<repr failed %r>" % (e,)
    if len(s) > n:
        s = s[:n] + "..."
    return s


def dump_module(name):
    try:
        mod = __import__(name, fromlist=["*"])
        log("MODULE " + name + " OK " + short(mod))
        keys = sorted([k for k in dir(mod) if not k.startswith("__")])
        log("KEYS " + name + " " + short(keys, 1200))
        terms = ("ent", "Ent", "entity", "Entity", "avatar", "Avatar", "player", "Player", "manager", "Manager", "local", "Local", "team", "Team", "aoi", "AOI")
        for k in keys:
            if any(t in k for t in terms):
                try:
                    v = getattr(mod, k)
                    log("ATTR " + name + "." + k + " type=" + str(type(v)) + " val=" + short(v))
                except BaseException as e:
                    log("ATTR " + name + "." + k + " FAIL " + repr(e))
    except BaseException as e:
        log("MODULE " + name + " FAIL " + repr(e))


log("BEGIN")
for modname in (
    "asiocore_64",
    "gclient.entitylist",
    "common.Entity",
    "common.EntityManager",
    "client.ClientEntity",
    "gclient.gameplay.logic_base.entities.combat_avatar",
    "gclient.gameplay.logic_base.entities.combat_team",
):
    dump_module(modname)

try:
    import asiocore_64

    for cname in (
        "entities",
        "entity",
        "get_entities",
        "get_entity",
        "GetEntity",
        "GetEntities",
        "GetEntityByID",
        "GetMainPlayer",
        "GetLocalPlayer",
        "get_main_player",
        "get_local_player",
    ):
        try:
            f = getattr(asiocore_64, cname)
        except BaseException:
            continue
        try:
            log("CALL asiocore_64." + cname + "() => " + short(f(), 800))
        except BaseException as e:
            log("CALL asiocore_64." + cname + "() FAIL " + repr(e))
except BaseException as e:
    log("asiocore_64 call block fail " + repr(e))

log("END")

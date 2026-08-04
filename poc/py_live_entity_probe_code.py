out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_live_entity_probe.log"


def log(s):
    open(out, "a", encoding="utf-8").write(str(s) + "\n")


def short(v, n=500):
    try:
        s = repr(v)
    except BaseException as e:
        s = "<repr failed %r>" % (e,)
    return s[:n] + ("..." if len(s) > n else "")


def wanted(name):
    terms = (
        "Name",
        "name",
        "Pos",
        "pos",
        "Position",
        "position",
        "World",
        "world",
        "Bound",
        "bound",
        "Bone",
        "bone",
        "Team",
        "team",
        "Toplogo",
        "toplogo",
        "Logo",
        "logo",
        "Outline",
        "outline",
        "Visible",
        "visible",
        "Mark",
        "mark",
        "Dead",
        "dead",
        "Health",
        "health",
        "Hp",
        "HP",
        "Avatar",
        "avatar",
        "Robot",
        "robot",
        "Player",
        "player",
        "Is",
    )
    return any(t in name for t in terms)


log("BEGIN")
try:
    from common.EntityManager import EntityManager

    ents = list(EntityManager._entities.items())
    log("entity_count=" + str(len(ents)))
    picked = []
    for key, ent in ents:
        r = repr(ent)
        if "Avatar" in r or "Robot" in r or "Player" in r or "Dummy" in r:
            picked.append((key, ent))
    picked = picked[:12]
    log("picked=" + short([(k, repr(e), type(e).__name__) for k, e in picked], 2000))
    for key, ent in picked:
        label = repr(ent)
        log("ENTITY " + key + " " + label + " class=" + str(ent.__class__))
        names = sorted([n for n in dir(ent) if not n.startswith("__")])
        log("DIR " + key + " " + short([n for n in names if wanted(n)], 4000))
        for n in names:
            if wanted(n):
                try:
                    v = getattr(ent, n)
                    if not callable(v):
                        log("ATTR " + key + "." + n + " type=" + str(type(v)) + " val=" + short(v))
                except BaseException as e:
                    log("ATTR " + key + "." + n + " FAIL " + repr(e))
        for n in (
            "GetName",
            "GetPosition",
            "GetWorldPosition",
            "GetEntityPosition",
            "GetWorldBound",
            "GetPrimitiveWorldBound",
            "GetTeamID",
            "GetTeamId",
            "GetTeam",
            "GetHp",
            "GetHP",
            "GetHealth",
            "IsDead",
            "IsAlive",
            "IsEnemy",
            "CanShowEnemyToplogo",
            "CanShowEnemyToplogoBar",
            "GetEntity",
            "GetRealEntity",
            "GetModel",
            "GetNode",
        ):
            try:
                f = getattr(ent, n)
            except BaseException:
                continue
            if callable(f):
                try:
                    log("CALL " + key + "." + n + "() => " + short(f()))
                except BaseException as e:
                    log("CALL " + key + "." + n + "() FAIL " + repr(e))
except BaseException as e:
    log("probe fail " + repr(e))
log("END")

import inspect
import time
import traceback

LOG = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_advanced_esp_probe.log"


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def pos_of(entity):
    for name in ("position", "pos", "last_position"):
        try:
            value = getattr(entity, name)
            if callable(value):
                value = value()
            if value is not None:
                return tuple(float(x) for x in value[:3])
        except Exception:
            pass
    return None


def simple(value):
    return isinstance(value, (int, float, str, bool, tuple, list, dict, type(None)))


def dump_stats_attrs(label, ent):
    tokens = (
        "hp", "health", "armor", "shield", "blood", "life", "maxhp", "curhp",
        "name", "team", "camp", "level", "dead", "kill", "damage", "attr",
    )
    names = [n for n in dir(ent) if any(t in n.lower() for t in tokens)]
    log(f"{label} ATTR_CANDIDATES count={len(names)} names={names[:220]!r}")
    for name in names[:220]:
        try:
            obj = getattr(ent, name)
            if callable(obj):
                try:
                    sig = inspect.signature(obj)
                except Exception as exc:
                    sig = f"sig_fail:{exc!r}"
                log(f"{label}.{name}: CALLABLE type={type(obj)!r} sig={sig!r}")
                if name.lower().startswith(("get", "is", "can", "has")):
                    try:
                        log(f"{label}.{name}() => {obj()!r}")
                    except Exception as exc:
                        log(f"{label}.{name}() FAIL {exc!r}")
            elif simple(obj):
                log(f"{label}.{name}: {type(obj)!r} {obj!r}")
            else:
                log(f"{label}.{name}: {type(obj)!r} {obj!r}")
        except Exception as exc:
            log(f"{label}.{name}: FAIL {exc!r}")


def try_set(obj, name, value):
    try:
        setattr(obj, name, value)
        return True
    except Exception as exc:
        log(f"set {name} FAIL {exc!r}")
        return False


def try_text(pos):
    import MUI

    log("MUI_NAMES " + repr([n for n in dir(MUI) if "Text" in n or "Harm" in n]))
    param = MUI.HarmTextParam()
    for attr, value in (
        ("harmText", "CTF ESP 12m HP100"),
        ("worldPos", pos),
        ("fontName", "Arial"),
        ("fontSize", 26.0),
        ("fovDistance", 9999.0),
        ("scale", 1.0),
        ("accScale", 1.0),
        ("localZ", 2),
        ("fontIndex", 0),
        ("type", 0),
    ):
        try_set(param, attr, value)
    for attr, value in (
        ("color", (0.0, 1.0, 0.0)),
        ("strokeColor", (0.0, 0.0, 0.0)),
        ("offset", (0.0, -28.0)),
    ):
        try_set(param, attr, value)

    funcs = [
        "CreateScreenText",
        "UpdateScreenText",
        "CreateHarmText",
        "CreateHarmText0",
        "CreateHarmText2",
        "CreateHarmText3",
        "UpdateHarmText",
        "CreateMessageText",
        "CreateMessageText2",
    ]
    arg_sets = [
        (param,),
        ("ctf_text_probe", param),
        (pos, "CTF ESP 12m HP100"),
        ("ctf_text_probe", pos, "CTF ESP 12m HP100"),
        ("ctf_text_probe", "CTF ESP 12m HP100", pos),
    ]
    for fname in funcs:
        fn = getattr(MUI, fname, None)
        if fn is None:
            log(f"{fname}: missing")
            continue
        for args in arg_sets:
            try:
                res = fn(*args)
                log(f"{fname}{args!r} => OK {res!r}")
            except Exception as exc:
                log(f"{fname}{args!r} => FAIL {exc!r}")


def main():
    log("BEGIN " + str(time.time()))
    try:
        import common.EntityManager as EM
        entities = getattr(EM.EntityManager, "_entities", {})
        players = [(str(k), e) for k, e in entities.items() if getattr(e, "IsPlayerCombatAvatar", False)]
        robots = [(str(k), e) for k, e in entities.items() if getattr(e, "IsRobotCombatAvatar", False)]
        log(f"counts total={len(entities)} players={len(players)} robots={len(robots)}")
        if players:
            log(f"PLAYER {players[0][0]} pos={pos_of(players[0][1])!r}")
            dump_stats_attrs("PLAYER", players[0][1])
        if robots:
            log(f"ROBOT {robots[0][0]} pos={pos_of(robots[0][1])!r}")
            dump_stats_attrs("ROBOT", robots[0][1])
            try_text(pos_of(robots[0][1]))
    except Exception:
        log("EXC\n" + traceback.format_exc())
    finally:
        log("END")


main()

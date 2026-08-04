out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\gacha_core_probe.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


def short(value, limit=4000):
    try:
        text = repr(value)
    except BaseException as error:
        text = "<repr failed %r>" % (error,)
    return text[:limit] + ("..." if len(text) > limit else "")


def report(label, value):
    code = getattr(value, "__code__", None)
    if code is None:
        return
    names = tuple(code.co_names)
    constants = [item for item in code.co_consts if isinstance(item, (str, int, float, tuple))]
    log("FUNC " + label +
        " names=" + short(names, 5000) +
        " vars=" + short(code.co_varnames, 3000) +
        " consts=" + short(constants, 6000))


module_names = (
    "gclient.gamesystem.entities.avatarmembers.cimp_gacha",
    "gclient.gamesystem.entities.avatarmembers.cimp_gacha_oneshot",
    "gclient.gamesystem.entities.avatarmembers.cimp_mall",
    "gclient.gamesystem.uihall.uimall.mall_box_window",
    "gclient.gamesystem.uihall.uimall.mall_box_weapon_v6_roll_window",
    "gclient.gamesystem.uihall.uimall.mall_box_weapon_v7_roll_window",
    "gclient.gamesystem.uihall.uigacha.flip_gacha_v6_window",
    "gclient.gamesystem.uihall.uigacha.flip_gacha_new_v5_window",
)


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    import sys
    import types

    for module_name in module_names:
        try:
            module = __import__(module_name, fromlist=["*"])
        except BaseException as error:
            log("IMPORT_FAIL " + module_name + " " + repr(error))
            continue
        log("MODULE " + module_name + " FILE=" + short(getattr(module, "__file__", None)))
        for name, value in sorted(module.__dict__.items()):
            if isinstance(value, types.FunctionType):
                report(module_name + "." + name, value)
            elif isinstance(value, type):
                relevant = []
                for method_name, method in sorted(value.__dict__.items()):
                    function = getattr(method, "__func__", method)
                    code = getattr(function, "__code__", None)
                    if code is None:
                        continue
                    joined = " ".join(code.co_names).lower()
                    if any(token in (method_name + " " + joined).lower() for token in (
                        "callserver", "gacha", "roll", "draw", "buy", "money", "reward", "cost",
                    )):
                        relevant.append((method_name, function))
                if relevant:
                    log("CLASS " + value.__name__ + " METHODS=" + short([method_name for method_name, _ in relevant], 5000))
                    for method_name, function in relevant:
                        report(module_name + "." + value.__name__ + "." + method_name, function)

    from common.EntityManager import EntityManager
    player = next(entity for _, entity in EntityManager._entities.items()
                  if type(entity).__name__ == "PlayerAvatar")
    for name in sorted(dir(player)):
        if any(token in name.lower() for token in ("gacha", "roll", "draw", "buy")):
            value = getattr(player, name)
            if callable(value):
                report("PLAYER." + name, value)
except BaseException as error:
    log("PROBE_FAIL " + repr(error))
log("END")

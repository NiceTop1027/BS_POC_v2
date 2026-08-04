out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\gold_probe.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


def short(value, limit=700):
    try:
        text = repr(value)
    except BaseException as error:
        text = "<repr failed %r>" % (error,)
    return text[:limit] + ("..." if len(text) > limit else "")


def is_money_name(name):
    lowered = name.lower()
    return any(token in lowered for token in (
        "gold", "money", "cash", "coin", "currency", "wallet", "balance",
        "yuanbao", "diamond", "credit", "token", "point",
    ))


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    import types
    import sys
    from common.EntityManager import EntityManager

    module_name = "gclient.gamesystem.entities.avatarmembers.cimp_money"
    money_module = __import__(module_name, fromlist=["*"])
    log("MODULE=" + short(money_module))
    log("MODULE_FILE=" + short(getattr(money_module, "__file__", None)))
    log("MODULE_DIR=" + short([name for name in dir(money_module) if is_money_name(name) or name.startswith("CImp")], 4000))

    for class_name in sorted(dir(money_module)):
        value = getattr(money_module, class_name)
        if not isinstance(value, type):
            continue
        relevant = [name for name in dir(value) if is_money_name(name) or name.startswith("on_set_")]
        if not relevant:
            continue
        log("CLASS " + class_name + " NAMES=" + short(relevant, 5000))
        for member_name in relevant:
            try:
                member = getattr(value, member_name)
                code = getattr(member, "__code__", None)
                if code:
                    constants = [item for item in code.co_consts if isinstance(item, (str, int, float, tuple))]
                    log("FUNC " + class_name + "." + member_name +
                        " names=" + short(code.co_names, 3000) +
                        " vars=" + short(code.co_varnames, 1500) +
                        " consts=" + short(constants, 3000))
            except BaseException as error:
                log("FUNC_FAIL " + class_name + "." + member_name + " " + repr(error))

    entities = list(getattr(EntityManager, "_entities", {}).items())
    players = [(key, entity) for key, entity in entities
               if type(entity).__name__ == "PlayerAvatar" or getattr(entity, "is_become_player", False)]
    log("PLAYERS=" + short([(key, type(entity).__name__, repr(entity)) for key, entity in players], 3000))
    for key, player in players[:3]:
        log("PLAYER " + str(key) + " TYPE=" + str(type(player)))
        log("MRO=" + short([cls.__module__ + "." + cls.__name__ for cls in type(player).__mro__], 5000))
        names = [name for name in dir(player) if is_money_name(name) or name.startswith("on_set_")]
        log("PLAYER_NAMES=" + short(names, 8000))
        for name in names:
            try:
                value = getattr(player, name)
                if callable(value):
                    code = getattr(value, "__code__", None)
                    if code:
                        log("PLAYER_FUNC " + name +
                            " names=" + short(code.co_names, 3000) +
                            " vars=" + short(code.co_varnames, 1500))
                else:
                    log("PLAYER_ATTR " + name + " type=" + str(type(value)) + " value=" + short(value, 3000))
            except BaseException as error:
                log("PLAYER_FIELD_FAIL " + name + " " + repr(error))

    log("LOADED_MONEY_MODULES=" + short(sorted(name for name in sys.modules if "money" in name.lower()), 4000))
except BaseException as error:
    log("PROBE_FAIL " + repr(error))
log("END")

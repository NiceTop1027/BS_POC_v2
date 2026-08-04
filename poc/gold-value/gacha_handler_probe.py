out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\gacha_handler_probe.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


def short(value, limit=2200):
    try:
        text = repr(value)
    except BaseException as error:
        text = "<repr failed %r>" % (error,)
    return text[:limit] + ("..." if len(text) > limit else "")


def relevant_name(name):
    lowered = name.lower()
    return any(token in lowered for token in (
        "gacha", "lottery", "draw", "roll", "mall", "shop", "money", "coin",
        "gold", "buy", "reward",
    ))


def report_function(label, function):
    code = getattr(function, "__code__", None)
    if code is None:
        return False
    names = tuple(code.co_names)
    text = " ".join(names).lower()
    if not (relevant_name(label) or any(token in text for token in (
            "callserver", "precheckenoughmoney", "gacha", "lottery", "draw", "roll", "buy"))):
        return False
    constants = [value for value in code.co_consts if isinstance(value, (str, int, float, tuple))]
    log("FUNC " + label + " names=" + short(names, 5000) +
        " vars=" + short(code.co_varnames, 2200) +
        " consts=" + short(constants, 5000))
    return True


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    import sys
    import types

    module_names = sorted(
        name for name in sys.modules
        if relevant_name(name) and getattr(sys.modules.get(name), "__dict__", None) is not None
    )
    log("MODULES=" + short(module_names, 12000))
    count = 0
    for module_name in module_names:
        module = sys.modules[module_name]
        for name, value in list(module.__dict__.items()):
            if isinstance(value, types.FunctionType):
                if report_function(module_name + "." + name, value):
                    count += 1
            elif isinstance(value, type):
                for method_name, method in list(value.__dict__.items()):
                    function = getattr(method, "__func__", method)
                    if isinstance(function, (types.FunctionType, types.MethodType)):
                        if report_function(module_name + "." + value.__name__ + "." + method_name, function):
                            count += 1
            if count >= 180:
                break
        if count >= 180:
            break
    log("MATCH_COUNT=" + str(count))
except BaseException as error:
    log("PROBE_FAIL " + repr(error))
log("END")

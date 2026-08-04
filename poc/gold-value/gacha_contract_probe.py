out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\gacha_contract_probe.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


def short(value, limit=6000):
    try:
        text = repr(value)
    except BaseException as error:
        text = "<repr failed %r>" % (error,)
    return text[:limit] + ("..." if len(text) > limit else "")


def function_chain(function):
    result = []
    seen = set()
    pending = [function]
    while pending:
        current = pending.pop(0)
        if id(current) in seen:
            continue
        seen.add(id(current))
        if callable(current) and getattr(current, "__code__", None) is not None:
            result.append(current)
            wrapped = getattr(current, "__wrapped__", None)
            if wrapped is not None:
                pending.append(wrapped)
            for cell in getattr(current, "__closure__", None) or ():
                try:
                    candidate = cell.cell_contents
                except ValueError:
                    continue
                if callable(candidate) and getattr(candidate, "__code__", None) is not None:
                    pending.append(candidate)
    return result


def report_function(label, function):
    import dis
    import inspect

    for index, current in enumerate(function_chain(function)):
        code = current.__code__
        try:
            signature = str(inspect.signature(current))
        except BaseException as error:
            signature = "<signature failed %r>" % (error,)
        log("FUNCTION " + label + " chain=" + str(index) +
            " name=" + str(getattr(current, "__name__", None)) +
            " signature=" + signature +
            " names=" + short(code.co_names, 5000) +
            " vars=" + short(code.co_varnames, 3000) +
            " defaults=" + short(getattr(current, "__defaults__", None), 1500))
        instructions = []
        for instruction in dis.Bytecode(current):
            instructions.append("%s %s" % (instruction.opname, instruction.argrepr))
        log("DIS " + label + " chain=" + str(index) + " " + short(instructions, 16000))


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    from common.EntityManager import EntityManager
    gacha_module = __import__("gclient.gamesystem.entities.avatarmembers.cimp_gacha", fromlist=["*"])
    player = next(entity for _, entity in EntityManager._entities.items()
                  if type(entity).__name__ == "PlayerAvatar")

    for name in ("BuyGacha", "AutoBuyGacha", "BuyCacheGacha", "BuyOneShot", "CheckCanBuyGacha", "OnGachaRoll", "OnGachaRollSkipAnim"):
        try:
            report_function("PLAYER." + name, getattr(player, name))
        except BaseException as error:
            log("FUNCTION_FAIL " + name + " " + repr(error))

    for name in ("GetOnlyGachaList", "GetGoldGachaID"):
        try:
            method = getattr(player, name)
            log("CALL " + name + "=" + short(method()))
        except BaseException as error:
            log("CALL_FAIL " + name + " " + repr(error))

    for field in ("gacha_mgr", "gacha", "gacha_oneshot", "gacha_token", "gacha_setting_id"):
        try:
            value = getattr(player, field)
            log("FIELD " + field + " type=" + str(type(value)) + " value=" + short(value, 8000))
            if hasattr(value, "items"):
                log("FIELD_ITEMS " + field + "=" + short(list(value.items())[:30], 12000))
        except BaseException as error:
            log("FIELD_FAIL " + field + " " + repr(error))

    setting_data = gacha_module.gacha_setting_data.data
    log("SETTING_KEYS=" + short(sorted(setting_data)[:80], 10000))
    for setting_id in sorted(setting_data)[:30]:
        proto = setting_data[setting_id]
        if isinstance(proto, dict):
            interesting = {key: proto.get(key) for key in proto if any(token in str(key).lower() for token in (
                "id", "money", "price", "cost", "roll", "type", "item", "server"))}
        else:
            interesting = proto
        log("SETTING " + str(setting_id) + "=" + short(interesting, 8000))
except BaseException as error:
    log("PROBE_FAIL " + repr(error))
log("END")

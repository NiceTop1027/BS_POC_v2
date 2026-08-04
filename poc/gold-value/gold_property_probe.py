out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\gold_property_probe.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


def short(value, limit=1200):
    try:
        text = repr(value)
    except BaseException as error:
        text = "<repr failed %r>" % (error,)
    return text[:limit] + ("..." if len(text) > limit else "")


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    from common.EntityManager import EntityManager
    money_module = __import__("gclient.gamesystem.entities.avatarmembers.cimp_money", fromlist=["*"])
    consts = money_module.consts

    entities = list(getattr(EntityManager, "_entities", {}).items())
    player = next(entity for _, entity in entities if type(entity).__name__ == "PlayerAvatar")
    fields = (
        "yuanbao", "free_yuanbao", "pay_yuanbao", "limit_yuanbao",
        "skin_metal_coin", "dmz_coin", "honor", "gold", "coins",
    )
    for field in fields:
        try:
            value = getattr(player, field)
            log("FIELD " + field + " type=" + str(type(value)) + " value=" + short(value))
        except BaseException as error:
            log("FIELD_FAIL " + field + " " + repr(error))

    for cls in type(player).__mro__:
        class_dict = getattr(cls, "__dict__", {})
        relevant = [field for field in fields if field in class_dict]
        if relevant:
            log("CLASS_DESCRIPTORS " + cls.__module__ + "." + cls.__name__ + " " + short({field: class_dict[field] for field in relevant}, 4000))
            for field in relevant:
                descriptor = class_dict[field]
                for accessor_name in ("fget", "fset"):
                    accessor = getattr(descriptor, accessor_name, None)
                    code = getattr(accessor, "__code__", None)
                    if code:
                        log("PROPERTY " + field + "." + accessor_name +
                            " names=" + short(code.co_names, 3000) +
                            " vars=" + short(code.co_varnames, 1500) +
                            " consts=" + short(code.co_consts, 3000))

    for name in ("EMoneyType_YUANBAO", "EMoneyType_PAY_YUANBAO", "EMoneyType_FREE_YUANBAO", "EMoneyType_LIMIT_YUANBAO", "EMoneyType_METAL", "EMoneyType_DMZ"):
        try:
            money_type = getattr(consts, name)
            log("CONST " + name + "=" + short(money_type) + " GET=" + short(player.GetMoneyByMoneyType(money_type)))
        except BaseException as error:
            log("CONST_FAIL " + name + " " + repr(error))

    log("GET_YUANBAO=" + short(player.GetYuanbao()))
    log("PLAYER_DICT=" + short(getattr(player, "__dict__", {}), 7000))
except BaseException as error:
    log("PROBE_FAIL " + repr(error))
log("END")

import dis

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\valor_id_mapping_probe.log"
terms = ("gacha_setting_proto", "real_gacha", "cur_key", "gacha_id")


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    module = __import__(
        "gclient.gamesystem.uihall.uimall.mall_box_weapon_v7_roll_window", fromlist=["*"])
    cls = module.MallBoxWeaponV7RollWindow
    for owner in cls.__mro__:
        for name, value in owner.__dict__.items():
            code = getattr(value, "__code__", None)
            if not code:
                continue
            names = tuple(code.co_names)
            strings = tuple(item for item in code.co_consts if isinstance(item, str))
            if not any(term in names or term in strings for term in terms):
                continue
            log("FUNCTION owner=%s name=%s names=%r consts=%r" % (
                owner.__name__, name, names, strings))
            if name in ("__init__", "Show", "LoadData", "Init", "Refresh", "SetData"):
                try:
                    log(dis.Bytecode(value).dis())
                except BaseException as error:
                    log("DIS_FAIL %r" % (error,))
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

import dis
import inspect

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\valor_route_detail_probe.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


def report(label, value):
    try:
        signature = inspect.signature(value)
    except BaseException as error:
        signature = "<signature failed %r>" % (error,)
    code = getattr(value, "__code__", None)
    log("FUNCTION %s signature=%s names=%r consts=%r" % (
        label, signature, tuple(code.co_names) if code else (),
        tuple(item for item in (code.co_consts if code else ()) if isinstance(item, str))))
    try:
        log(dis.Bytecode(value).dis())
    except BaseException as error:
        log("DIS_FAIL %r" % (error,))


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    from common.EntityManager import EntityManager
    gacha_module = __import__("gclient.gamesystem.entities.avatarmembers.cimp_gacha", fromlist=["*"])
    ui_module = __import__(
        "gclient.gamesystem.uihall.uimall.mall_box_weapon_v7_roll_window", fromlist=["*"])
    player = next(entity for _, entity in EntityManager._entities.items()
                  if type(entity).__name__ == "PlayerAvatar")

    for gacha_id in (1392, 1391):
        setting = gacha_module.gacha_setting_data.data.get(gacha_id)
        log("SETTING %s=%r" % (gacha_id, setting))
        log("ROLL %s=%r GACHA_STATE=%r" % (
            gacha_id, player.GetGachaRollCount(gacha_id),
            getattr(player, "gacha_mgr", {}).get(gacha_id)))
        log("CAN_BUY %s=%r" % (gacha_id, player.CheckCanBuyGacha(gacha_id, 1)
            if setting else None))

    cls = ui_module.MallBoxWeaponV7RollWindow
    buy_comp = cls.OnBuy.__globals__["MallGachaBuyComp"]
    log("BUY_COMP=%r MRO=%r" % (buy_comp, getattr(buy_comp, "__mro__", None)))
    for owner in getattr(buy_comp, "__mro__", (buy_comp,)):
        for method_name in ("OnBuy", "OnBuyConfirm", "_BuyGacha", "BuyConfirm"):
            if method_name in getattr(owner, "__dict__", {}):
                report("%s.%s" % (owner.__name__, method_name), owner.__dict__[method_name])
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

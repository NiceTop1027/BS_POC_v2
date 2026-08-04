import dis

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\gacha_currency_probe.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


def short(value, limit=5000):
    try:
        text = repr(value)
    except BaseException as error:
        text = "<repr failed %r>" % (error,)
    return text[:limit] + ("..." if len(text) > limit else "")


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    from common.EntityManager import EntityManager
    gacha_module = __import__("gclient.gamesystem.entities.avatarmembers.cimp_gacha", fromlist=["*"])

    player = next(entity for _, entity in EntityManager._entities.items()
                  if type(entity).__name__ == "PlayerAvatar")
    gacha_id = int(player.GetGoldGachaID())
    money_info = list(gacha_module._GetMoneyDictByGachaSettingData(
        gacha_module.gacha_setting_data.data[gacha_id], 1).values())[0]
    log("GACHA=%s MONEY_INFO=%s" % (gacha_id, short(money_info)))
    for item_id in (4000000020, 4100001820):
        try:
            count = player.GetItemCountByCostItemId(item_id)
        except BaseException as error:
            count = "<failed %r>" % (error,)
        log("ITEM id=%s count=%s" % (item_id, count))
    log("YUANBAO=%s CAN_BUY=%s" % (player.yuanbao, player.CheckCanBuyGacha(gacha_id, 1)))
    log("GET_ITEM_COUNT_DIS\n" + dis.Bytecode(player.GetItemCountByCostItemId).dis())
    warehouse = getattr(player, "warehouse", None)
    log("WAREHOUSE type=%s repr=%s" % (type(warehouse), short(warehouse)))
    log("WAREHOUSE_DICT=" + short(getattr(warehouse, "__dict__", None)))
    for module_name in (
        "gclient.data.lobby_item_data",
        "gclient.data.item_data",
        "gclient.data.item_base_data",
    ):
        try:
            module = __import__(module_name, fromlist=["*"])
            data = getattr(module, "data", None)
            log("DATA %s 4000000020=%s 4100001820=%s" % (
                module_name, short(data.get(4000000020) if data else None),
                short(data.get(4100001820) if data else None)))
        except BaseException as error:
            log("DATA_FAIL %s %r" % (module_name, error))
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

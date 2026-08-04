out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\gacha_preflight.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


def short(value, limit=6000):
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
    setting = gacha_module.gacha_setting_data.data[gacha_id]
    money_dict = gacha_module._GetMoneyDictByGachaSettingData(setting, 1)
    ticket = getattr(player, "server_random_ticket", None)
    gacha = getattr(player, "gacha_mgr", {}).get(gacha_id) if hasattr(getattr(player, "gacha_mgr", None), "get") else None

    interesting = {key: setting.get(key) for key in setting if any(token in str(key).lower() for token in (
        "id", "money", "price", "cost", "roll", "type", "item", "name", "real"))}
    log("GACHA_ID=" + str(gacha_id))
    log("SETTING=" + short(interesting))
    log("MONEY_DICT=" + short(money_dict))
    log("CHECK_CAN_BUY=" + repr(player.CheckCanBuyGacha(gacha_id, 1)))
    log("GOLD=" + str(int(player.yuanbao)))
    log("SERVER_RANDOM_TICKET_PRESENT=" + repr(bool(ticket)) + " LENGTH=" + str(len(ticket) if isinstance(ticket, str) else 0))
    log("GACHA_STATE=" + short(gacha))
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

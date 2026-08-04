import builtins
import time

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\gacha_result.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


def short(value, limit=4000):
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
    state = getattr(builtins, "_ctf_gold_gacha_state", None)
    gacha_id = int(state["gacha_id"]) if state else int(player.GetGoldGachaID())
    after_gold = int(player.yuanbao)
    after_roll_count = int(player.GetGachaRollCount(gacha_id))
    money_info = list(gacha_module._GetMoneyDictByGachaSettingData(
        gacha_module.gacha_setting_data.data[gacha_id], 1).values())[0]
    cost_item_id = money_info.get("cost_item_id")
    cost_item_count = (player.GetItemCountByCostItemId(cost_item_id)
                       if cost_item_id is not None else None)
    state_summary = ({key: state.get(key) for key in (
        "gacha_id", "requested_at", "before_gold", "before_roll_count", "callback_name")}
        if state else None)
    log("STATE=" + short(state_summary))
    log("AFTER gold=%s roll_count=%s checked_at=%s" % (after_gold, after_roll_count, time.time()))
    log("COST money_type=%s item_id=%s item_count=%s price=%s" % (
        money_info.get("money_type"), cost_item_id, cost_item_count, money_info.get("price")))
    if state:
        log("DELTA gold=%s rolls=%s" % (
            after_gold - int(state["before_gold"]),
            after_roll_count - int(state["before_roll_count"])))
except BaseException as error:
    log("FAIL " + repr(error))

log("END")

import builtins
import time
import traceback

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\gacha_purchase.log"


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

    player = next(entity for _, entity in EntityManager._entities.items()
                  if type(entity).__name__ == "PlayerAvatar")
    gacha_id = int(player.GetGoldGachaID())
    state = {
        "gacha_id": gacha_id,
        "requested_at": time.time(),
        "before_gold": int(player.yuanbao),
        "before_roll_count": int(player.GetGachaRollCount(gacha_id)),
        "callback": None,
    }

    # The game's UI sends the target method name, not a Python callable.
    state["callback_name"] = "OnGachaRoll"
    builtins._ctf_gold_gacha_state = state
    log("REQUEST gacha_id=%s before_gold=%s before_roll_count=%s" % (
        gacha_id, state["before_gold"], state["before_roll_count"]))
    player.BuyGacha(gacha_id, 1, "OnGachaRoll")
    log("REQUEST_DISPATCHED")
except BaseException as error:
    log("FAIL " + repr(error))
    log(traceback.format_exc())

log("END")

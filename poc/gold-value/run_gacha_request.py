import builtins
import json
import time

request_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\gacha_request.json"
out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\gacha_router.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    from common.EntityManager import EntityManager
    gacha_module = __import__("gclient.gamesystem.entities.avatarmembers.cimp_gacha", fromlist=["*"])

    with open(request_path, "r", encoding="utf-8") as handle:
        request = json.load(handle)
    gacha_id = int(request["gacha_id"])
    times = int(request.get("times", 1))

    player = next(entity for _, entity in EntityManager._entities.items()
                  if type(entity).__name__ == "PlayerAvatar")
    if gacha_id not in set(player.GetOnlyGachaList()):
        raise ValueError("gacha_id is not a currently visible standard gacha: %s" % gacha_id)
    setting = gacha_module.gacha_setting_data.data[gacha_id]
    allowed_times = tuple(setting.get("allow_roll_times", (1, 10)))
    if times not in allowed_times:
        raise ValueError("unsupported roll count %s; allowed=%s" % (times, allowed_times))
    if not player.CheckCanBuyGacha(gacha_id, times):
        raise RuntimeError("insufficient currency or unavailable gacha")

    callback_name = "OnGachaV6Roll" if setting.get("draw_type") == "Valor" else "OnGachaRoll"
    state = {
        "gacha_id": gacha_id,
        "times": times,
        "name": setting.get("name"),
        "draw_type": setting.get("draw_type"),
        "callback_name": callback_name,
        "before_gold": int(player.yuanbao),
        "before_roll_count": int(player.GetGachaRollCount(gacha_id)),
        "requested_at": time.time(),
    }
    builtins._ctf_gacha_router_state = state
    log("REQUEST=%r" % state)
    player.BuyGacha(gacha_id, times, callback_name)
    log("REQUEST_DISPATCHED")
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

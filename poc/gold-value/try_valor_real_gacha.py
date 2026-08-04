import builtins
import time

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\valor_real_gacha.log"
display_id = 1392
server_id = 1391
times = 1
callback_name = "OnGachaV6Roll"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    from common.EntityManager import EntityManager

    player = next(entity for _, entity in EntityManager._entities.items()
                  if type(entity).__name__ == "PlayerAvatar")
    state = {
        "display_id": display_id,
        "server_id": server_id,
        "times": times,
        "callback_name": callback_name,
        "before_gold": int(player.yuanbao),
        "before_display_roll": int(player.GetGachaRollCount(display_id)),
        "before_server_roll": int(player.GetGachaRollCount(server_id)),
        "requested_at": time.time(),
    }
    if not player.CheckCanBuyGacha(server_id, times):
        raise RuntimeError("server gacha ID did not pass normal precheck")
    builtins._ctf_valor_real_gacha_state = state
    log("REQUEST=%r" % state)
    player.BuyGacha(server_id, times, callback_name)
    log("REQUEST_DISPATCHED")
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

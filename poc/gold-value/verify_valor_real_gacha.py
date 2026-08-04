import builtins
import time

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\valor_real_gacha_result.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    from common.EntityManager import EntityManager

    state = getattr(builtins, "_ctf_valor_real_gacha_state", None)
    if not state:
        raise RuntimeError("no Valor real-gacha request state")
    player = next(entity for _, entity in EntityManager._entities.items()
                  if type(entity).__name__ == "PlayerAvatar")
    after_gold = int(player.yuanbao)
    after_display_roll = int(player.GetGachaRollCount(int(state["display_id"])))
    after_server_roll = int(player.GetGachaRollCount(int(state["server_id"])))
    log("STATE=%r" % state)
    log("AFTER gold=%s display_roll=%s server_roll=%s checked_at=%s" % (
        after_gold, after_display_roll, after_server_roll, time.time()))
    log("DELTA gold=%s display_roll=%s server_roll=%s" % (
        after_gold - int(state["before_gold"]),
        after_display_roll - int(state["before_display_roll"]),
        after_server_roll - int(state["before_server_roll"])))
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

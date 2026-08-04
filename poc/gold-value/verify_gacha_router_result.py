import builtins
import time

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\gacha_router_result.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    from common.EntityManager import EntityManager

    state = getattr(builtins, "_ctf_gacha_router_state", None)
    if not state:
        raise RuntimeError("no routed gacha request state")
    player = next(entity for _, entity in EntityManager._entities.items()
                  if type(entity).__name__ == "PlayerAvatar")
    after_gold = int(player.yuanbao)
    after_roll_count = int(player.GetGachaRollCount(int(state["gacha_id"])))
    log("STATE=%r" % state)
    log("AFTER gold=%s roll_count=%s checked_at=%s" % (
        after_gold, after_roll_count, time.time()))
    log("DELTA gold=%s rolls=%s" % (
        after_gold - int(state["before_gold"]),
        after_roll_count - int(state["before_roll_count"])))
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

import builtins
import time

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\valor_response_trace_result.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    from common.EntityManager import EntityManager

    player = next(entity for _, entity in EntityManager._entities.items()
                  if type(entity).__name__ == "PlayerAvatar")
    state = getattr(builtins, "_ctf_valor_response_trace", None)
    if not state:
        raise RuntimeError("trace state missing")
    for name, (had_value, old_value) in state["existing"].items():
        if had_value:
            setattr(player, name, old_value)
        else:
            delattr(player, name)
    after_gold = int(player.yuanbao)
    after_roll = int(player.GetGachaRollCount(int(state["gacha_id"])))
    log("STATE=%r" % {key: state[key] for key in (
        "gacha_id", "installed_at", "before_gold", "before_roll", "dispatch_count")})
    log("AFTER gold=%s roll=%s checked_at=%s" % (after_gold, after_roll, time.time()))
    log("DELTA gold=%s roll=%s" % (
        after_gold - int(state["before_gold"]), after_roll - int(state["before_roll"])))
    log("RESTORED")
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

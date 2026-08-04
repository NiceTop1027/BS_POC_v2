import builtins
import time

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\valor_response_trace.log"
gacha_id = 1392
times = 1


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    from common.EntityManager import EntityManager

    player = next(entity for _, entity in EntityManager._entities.items()
                  if type(entity).__name__ == "PlayerAvatar")
    names = ("_orded_dispatch_rpc", "OnGachaV6Roll", "OnGachaRoll", "OnGachaRollSkipAnim")
    raw_dict = getattr(player, "__dict__", {})
    state = {
        "installed_at": time.time(),
        "before_gold": int(player.yuanbao),
        "before_roll": int(player.GetGachaRollCount(gacha_id)),
        "gacha_id": gacha_id,
        "existing": {name: (name in raw_dict, raw_dict.get(name)) for name in names},
        "originals": {},
        "wrappers": {},
        "dispatch_count": 0,
    }

    for name in names:
        original = getattr(player, name)
        state["originals"][name] = original

        def wrapper(*args, __name=name, __original=original, **kwargs):
            if __name == "_orded_dispatch_rpc":
                state["dispatch_count"] += 1
                if state["dispatch_count"] <= 50:
                    log("RPC method=%r args=%r kwargs=%r" % (
                        args[0] if args else None, args[1:] if len(args) > 1 else (), kwargs))
            else:
                log("CALLBACK name=%s args=%r kwargs=%r" % (__name, args, kwargs))
            return __original(*args, **kwargs)

        state["wrappers"][name] = wrapper
        setattr(player, name, wrapper)

    builtins._ctf_valor_response_trace = state
    log("TRACE_INSTALLED gold=%s roll=%s" % (state["before_gold"], state["before_roll"]))
    player.BuyGacha(gacha_id, times, "OnGachaV6Roll")
    log("REQUEST_DISPATCHED")
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

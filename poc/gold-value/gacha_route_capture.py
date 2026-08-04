import time

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\gacha_route_capture.log"
gacha_id = 1392
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
    original = player.CallServer
    player_dict = getattr(player, "__dict__", {})
    had_override = "CallServer" in player_dict
    old_override = player_dict.get("CallServer")
    captured = []

    def capture(method_name, *args, **kwargs):
        captured.append((method_name, args, kwargs, time.time()))
        log("CAPTURE method=%r args=%r kwargs=%r" % (method_name, args, kwargs))
        return True

    try:
        player.CallServer = capture
        player.BuyGacha(gacha_id, times, callback_name)
    finally:
        if had_override:
            player.CallServer = old_override
        else:
            delattr(player, "CallServer")
    log("CAPTURED_COUNT=%s" % len(captured))
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

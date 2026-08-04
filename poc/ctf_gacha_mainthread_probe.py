"""One-shot main-thread diagnostic for the local CTF gacha instance.

The module is loaded through the game's supported Python entry hook.  It waits
for the logged-in PlayerAvatar, performs one normal Valor purchase request, and
records its callback and resulting account state.  It does not open a socket,
forge a ticket, alter an RPC payload, or loop purchases.
"""

from __future__ import annotations

import time
import traceback


LOG_PATH = (
    r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc"
    r"\gold-value\valor_mainthread_probe.log"
)
GACHA_ID = 1392
ROLL_TIMES = 1

_STATE = {"started": False, "requested": False, "callbacks": []}
_TIMER_REFS = []


def _log(message: str) -> None:
    with open(LOG_PATH, "a", encoding="utf-8") as handle:
        handle.write(f"{time.time():.3f} {message}\n")


def _player():
    from common.EntityManager import EntityManager

    return next(
        entity
        for _, entity in EntityManager._entities.items()
        if type(entity).__name__ == "PlayerAvatar"
    )


def _add_timer(delay, repeat, callback) -> None:
    import asiocore

    _TIMER_REFS.append(callback)
    errors = []
    for args in (
        (delay, repeat, False, callback),
        (delay, repeat, 0, callback),
        (delay, callback),
    ):
        try:
            asiocore.add_timer(*args)
            _log(f"timer scheduled args={args[:-1]!r}")
            return
        except Exception as error:
            errors.append(repr(error))
    raise RuntimeError(f"add_timer failed: {errors!r}")


def _restore_callback() -> None:
    state = _STATE
    player = state.get("player")
    if player is None or not state.get("callback_installed"):
        return
    try:
        if state["had_instance_callback"]:
            setattr(player, "OnGachaV6Roll", state["instance_callback"])
        else:
            delattr(player, "OnGachaV6Roll")
        _log("callback restored")
    except Exception as error:
        _log(f"callback restore failed: {error!r}")
    finally:
        state["callback_installed"] = False


def _verify(*_args) -> None:
    state = _STATE
    try:
        player = state["player"]
        after_gold = int(player.yuanbao)
        after_rolls = int(player.GetGachaRollCount(GACHA_ID))
        _log(
            "VERIFY gold=%s rolls=%s delta_gold=%s delta_rolls=%s callbacks=%r"
            % (
                after_gold,
                after_rolls,
                after_gold - state["before_gold"],
                after_rolls - state["before_rolls"],
                state["callbacks"],
            )
        )
    except Exception:
        _log("verify failed:\n" + traceback.format_exc())
    finally:
        _restore_callback()


def _request(*_args) -> None:
    state = _STATE
    if state["requested"]:
        return
    try:
        player = _player()
        if not getattr(player, "server_random_ticket", None):
            _log("waiting for server_random_ticket")
            return

        state["requested"] = True
        state["player"] = player
        instance_dict = getattr(player, "__dict__", {})
        state["had_instance_callback"] = "OnGachaV6Roll" in instance_dict
        state["instance_callback"] = instance_dict.get("OnGachaV6Roll")
        original = getattr(player, "OnGachaV6Roll")

        def traced_callback(*args, **kwargs):
            payload = (args, kwargs)
            state["callbacks"].append(payload)
            _log(f"OnGachaV6Roll args={args!r} kwargs={kwargs!r}")
            return original(*args, **kwargs)

        state["traced_callback"] = traced_callback
        setattr(player, "OnGachaV6Roll", traced_callback)
        state["callback_installed"] = True
        state["before_gold"] = int(player.yuanbao)
        state["before_rolls"] = int(player.GetGachaRollCount(GACHA_ID))
        can_buy = bool(player.CheckCanBuyGacha(GACHA_ID, ROLL_TIMES))
        _log(
            "REQUEST gacha=%s times=%s can_buy=%s gold=%s rolls=%s"
            % (
                GACHA_ID,
                ROLL_TIMES,
                can_buy,
                state["before_gold"],
                state["before_rolls"],
            )
        )
        if not can_buy:
            _restore_callback()
            return
        player.BuyGacha(GACHA_ID, ROLL_TIMES, "OnGachaV6Roll")
        _log("REQUEST_DISPATCHED")
        _add_timer(6.0, False, _verify)
    except Exception:
        _log("request failed:\n" + traceback.format_exc())
        _restore_callback()


def Entry(*args):  # noqa: N802 - game entry hook name
    if _STATE["started"]:
        return True
    _STATE["started"] = True
    open(LOG_PATH, "w", encoding="utf-8").write(f"ENTRY args={args!r}\n")
    try:
        _add_timer(1.0, True, _request)
    except Exception:
        _log("entry failed:\n" + traceback.format_exc())
    return True


def fini():  # noqa: N802 - game entry hook name
    _restore_callback()
    _log("fini")
    return True

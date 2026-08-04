import inspect
import time
import traceback

LOG = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_player_marker_signature.log"


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def describe(owner, name):
    try:
        obj = getattr(owner, name)
    except Exception as exc:
        log(f"{name}: getattr FAIL {exc!r}")
        return
    log(f"{name}: repr={obj!r} type={type(obj)!r}")
    try:
        log(f"{name}: sig={inspect.signature(obj)!r}")
    except Exception as exc:
        log(f"{name}: sig FAIL {exc!r}")
    code = getattr(obj, "__code__", None)
    if code is not None:
        log(
            f"{name}: file={code.co_filename!r} first={code.co_firstlineno} "
            f"argc={code.co_argcount} kwonly={code.co_kwonlyargcount} "
            f"vars={code.co_varnames[:code.co_argcount + code.co_kwonlyargcount]!r}"
        )
    defaults = getattr(obj, "__defaults__", None)
    kwdefaults = getattr(obj, "__kwdefaults__", None)
    if defaults is not None:
        log(f"{name}: defaults={defaults!r}")
    if kwdefaults is not None:
        log(f"{name}: kwdefaults={kwdefaults!r}")


def main():
    log("BEGIN " + str(time.time()))
    try:
        import common.EntityManager as EM
        entities = getattr(EM.EntityManager, "_entities", {})
        robots = [(k, e) for k, e in entities.items() if getattr(e, "IsRobotCombatAvatar", False)]
        players = [(k, e) for k, e in entities.items() if getattr(e, "IsPlayerCombatAvatar", False)]
        log(f"entities={len(entities)} robots={len(robots)} players={len(players)}")
        if not players:
            return
        pkey, player = players[0]
        log(f"player={pkey!r} {player!r} class={player.__class__!r}")
        names = [
            name
            for name in dir(player)
            if any(
                token in name.lower()
                for token in ("toplogo", "mark", "recon", "enemy", "damage", "screen", "field")
            )
        ]
        log(f"candidate_names={names!r}")
        for name in names:
            describe(player, name)
    except Exception:
        log("EXC\n" + traceback.format_exc())
    finally:
        log("END")


main()

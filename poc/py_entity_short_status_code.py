import time
import traceback

LOG = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_entity_short_status.log"


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def main():
    log("BEGIN " + str(time.time()))
    try:
        import common.EntityManager as EM

        entities = getattr(EM.EntityManager, "_entities", {})
        log(f"entity_count={len(entities)}")
        for key, ent in entities.items():
            flags = []
            for attr in ("IsAvatar", "IsCombatAvatar", "IsPlayerCombatAvatar", "IsRobotCombatAvatar", "IsCombatTeam", "IsShootingRange"):
                try:
                    if getattr(ent, attr, False):
                        flags.append(attr)
                except Exception:
                    pass
            pos = None
            for attr in ("position", "pos", "last_position"):
                try:
                    pos = getattr(ent, attr)
                    if callable(pos):
                        pos = pos()
                    if pos is not None:
                        break
                except Exception:
                    pos = None
            log(f"{key!r} {ent!r} class={ent.__class__.__name__} flags={flags!r} pos={pos!r}")
    except Exception:
        log("EXC\n" + traceback.format_exc())
    finally:
        log("END")


main()

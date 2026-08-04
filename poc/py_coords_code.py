import time
import traceback

LOG = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_coords.log"


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def pos_of(entity):
    for name in ("position", "pos", "last_position"):
        try:
            value = getattr(entity, name)
            if callable(value):
                value = value()
            if value is not None:
                return tuple(value)
        except Exception:
            pass
    return None


def main():
    log("BEGIN " + str(time.time()))
    try:
        import common.EntityManager as EM
        entities = getattr(EM.EntityManager, "_entities", {})
        rows = []
        for key, ent in entities.items():
            if getattr(ent, "IsPlayerCombatAvatar", False):
                rows.append(("PLAYER", key, ent.__class__.__name__, pos_of(ent), repr(ent)))
            elif getattr(ent, "IsRobotCombatAvatar", False):
                rows.append(("ROBOT", key, ent.__class__.__name__, pos_of(ent), repr(ent)))
        rows.sort(key=lambda row: (row[0] != "PLAYER", row[1]))
        log(f"COUNT total={len(entities)} selected={len(rows)}")
        for kind, key, cls, pos, rep in rows:
            log(f"{kind} key={key} class={cls} pos={pos!r} repr={rep}")
    except Exception:
        log("EXC\n" + traceback.format_exc())
    finally:
        log("END")


main()

import dis
import inspect
import time
import traceback

LOG = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_robot_toplogo_deep.log"


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def describe(cls, name):
    try:
        obj = getattr(cls, name)
    except Exception as exc:
        log(f"{name}: getattr FAIL {exc!r}")
        return
    log(f"{name}: repr={obj!r}")
    try:
        log(f"{name}: sig={inspect.signature(obj)!r}")
    except Exception as exc:
        log(f"{name}: sig FAIL {exc!r}")
    code = getattr(obj, "__code__", None)
    if code:
        log(
            f"{name}: file={code.co_filename!r} first={code.co_firstlineno} "
            f"vars={code.co_varnames!r} names={code.co_names!r} consts={code.co_consts!r}"
        )
        log(f"{name}: DIS_BEGIN")
        for inst in dis.Bytecode(obj):
            log(f"  {inst.offset:04x} {inst.opname:<30} {inst.argrepr}")
        log(f"{name}: DIS_END")


def main():
    log("BEGIN " + str(time.time()))
    try:
        import gclient.gameplay.logic_shootingrange.combat_avatar_shootingrange as mod

        cls = mod.RobotCombatAvatarShootingRange
        for name in (
            "TryInitToplogo",
            "IsShootingRangeToplogoReady",
            "CreateToplogo",
            "RemoveToplogo",
            "ShowEnemyToplogo",
            "ShowToplogo",
            "SetToplogoVisible",
            "RefreshToplogo",
        ):
            describe(cls, name)
    except Exception:
        log("EXC\n" + traceback.format_exc())
    finally:
        log("END")


main()

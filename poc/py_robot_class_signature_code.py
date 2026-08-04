import dis
import inspect
import time
import traceback

LOG = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_robot_class_signature.log"


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def describe(cls, name, dump_dis=False):
    try:
        obj = getattr(cls, name)
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
            f"vars={code.co_varnames[:code.co_argcount + code.co_kwonlyargcount]!r} "
            f"names={code.co_names!r} consts={code.co_consts!r}"
        )
        if dump_dis:
            log(f"{name}: DIS_BEGIN")
            try:
                for inst in dis.Bytecode(obj):
                    log(f"  {inst.offset:04x} {inst.opname:<30} {inst.argrepr}")
            except Exception as exc:
                log(f"{name}: dis FAIL {exc!r}")
            log(f"{name}: DIS_END")
    defaults = getattr(obj, "__defaults__", None)
    if defaults is not None:
        log(f"{name}: defaults={defaults!r}")


def main():
    log("BEGIN " + str(time.time()))
    try:
        import gclient.gameplay.logic_shootingrange.combat_avatar_shootingrange as mod

        for clsname in ("RobotCombatAvatarShootingRange", "PlayerCombatAvatarShootingRange"):
            cls = getattr(mod, clsname)
            log(f"CLASS {clsname} {cls!r} mro={[c.__name__ for c in cls.__mro__]}")
            for name in (
                "CreateToplogo",
                "EnsureShootingRangeToplogo",
                "EnemyTopLogoTimer",
                "AddToplogoVisibleTick",
                "AddTopLogoHiddenReason",
                "AddTopLogoWidgetHiddenReason",
                "HideEnemyTopLogo",
                "CanShowEnemyToplogo",
                "CanShowEnemyToplogoBar",
                "DrawReconDroneMarkFrame",
                "DestroyReconDroneMarkFrame",
            ):
                describe(cls, name, dump_dis=name in ("CreateToplogo", "EnsureShootingRangeToplogo", "EnemyTopLogoTimer"))
    except Exception:
        log("EXC\n" + traceback.format_exc())
    finally:
        log("END")


main()

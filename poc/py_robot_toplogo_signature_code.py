import dis
import inspect
import time
import traceback

LOG = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_robot_toplogo_signature.log"


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def describe(owner, name, dump_dis=False):
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
            f"vars={code.co_varnames[:code.co_argcount + code.co_kwonlyargcount]!r} "
            f"names={code.co_names!r} consts={code.co_consts!r}"
        )
        if dump_dis:
            try:
                log(f"{name}: DIS_BEGIN")
                for inst in dis.Bytecode(obj):
                    log(
                        f"  {inst.offset:04x} {inst.opname:<28} "
                        f"{inst.argrepr}"
                    )
                log(f"{name}: DIS_END")
            except Exception as exc:
                log(f"{name}: dis FAIL {exc!r}")
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
        robots = [
            (key, ent)
            for key, ent in entities.items()
            if getattr(ent, "IsRobotCombatAvatar", False)
        ]
        players = [
            (key, ent)
            for key, ent in entities.items()
            if getattr(ent, "IsPlayerCombatAvatar", False)
        ]
        log(f"entities={len(entities)} robots={len(robots)} players={len(players)}")
        if not robots:
            return
        key, robot = robots[0]
        log(f"robot={key!r} {robot!r} class={robot.__class__!r}")
        log(f"robot position={getattr(robot, 'position', None)!r}")
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
            "IsShootingRangeToplogoReady",
            "DrawReconDroneMarkFrame",
            "DestroyReconDroneMarkFrame",
        ):
            describe(robot, name, dump_dis=name in ("CreateToplogo", "EnsureShootingRangeToplogo", "EnemyTopLogoTimer"))
    except Exception:
        log("EXC\n" + traceback.format_exc())
    finally:
        log("END")


main()

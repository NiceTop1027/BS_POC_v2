import inspect
import time
import traceback

LOG = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_signature_probe.log"


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def describe_callable(owner, name):
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
            f"{name}: code file={code.co_filename!r} first={code.co_firstlineno} "
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
        mgr = EM.EntityManager
        entities = getattr(mgr, "_entities", {})
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
            log("no robots")
            return
        key, robot = robots[0]
        log(f"robot={key!r} {robot!r} class={robot.__class__!r}")
        for name in (
            "CanShowEnemyToplogo",
            "CanShowEnemyToplogoBar",
            "CreateEnemyToplogo",
            "CreateEnemyTopLogo",
            "CreateMarkToplogo",
            "CreateCommonMarkToplogo",
            "CreateCommonMarkToplogoSceneOnly",
            "CreateCommonMarkToplogoMapOnly",
            "CreateTeammateMarkToplogo",
            "CreateMarkWorldEffect",
            "DestroyMarkToplogo",
            "DestroyAllMarkToplogo",
            "HideEnemyTopLogo",
            "HideAllEnemyToplogo",
            "DrawEnemyReconMarkFrames",
            "DrawReconDroneMarkFrame",
            "CreateSceneCenterMark",
            "AddSceneCenterMark",
            "AddWorldField",
            "CreateWorldFieldFollow",
            "GetDamageTextOffPos",
            "GetTargetDamageTextWorldPosition",
            "GetMarkPosAndType",
            "GetCommonMarkInfo",
        ):
            describe_callable(robot, name)

        import MUI
        for name in (
            "CreateScreenText",
            "UpdateScreenText",
            "RemoveScreenText",
            "AddFakeBoardElement",
            "AddFakeBoardElement0",
            "AddFakeBoardElementWithBone",
            "RemoveFakeBoardElement",
            "GetScreenWidth",
            "GetScreenHeight",
            "GetScreenSize",
            "GetWindowClientInfo",
        ):
            describe_callable(MUI, name)
    except Exception:
        log("EXC\n" + traceback.format_exc())
    finally:
        log("END")


main()

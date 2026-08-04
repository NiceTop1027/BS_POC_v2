import inspect
import time
import traceback

LOG = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_enemy_toplogo_widget_probe.log"


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def short(value, limit=1800):
    text = repr(value)
    if len(text) > limit:
        return text[:limit] + "...<cut>"
    return text


def dump(label, obj, depth=0):
    if obj is None:
        log(f"{label}: None")
        return
    log(f"{label}: {short(obj)} type={type(obj)!r}")
    try:
        names = [name for name in dir(obj) if not name.startswith("__")]
        interesting = [
            name
            for name in names
            if any(token in name.lower() for token in ("text", "txt", "dist", "hp", "bar", "name", "level", "widget", "node", "toplogo", "visible", "scale", "opacity", "color", "seek", "child"))
        ]
        log(f"{label}: interesting={short(interesting, 5000)}")
    except Exception as exc:
        log(f"{label}: dir FAIL {exc!r}")
        interesting = []

    for name in interesting:
        try:
            value = getattr(obj, name)
        except Exception as exc:
            log(f"{label}.{name}: getattr FAIL {exc!r}")
            continue
        if callable(value):
            try:
                log(f"{label}.{name}: callable sig={inspect.signature(value)!r}")
            except Exception:
                log(f"{label}.{name}: callable {short(value, 500)}")
        else:
            log(f"{label}.{name}: {short(value, 900)} type={type(value)!r}")


def try_seek(label, obj):
    if obj is None:
        return
    candidates = [
        "txt_distance",
        "txt_dist",
        "txt_dis",
        "txtDistance",
        "Text_Distance",
        "text_distance",
        "distance",
        "dist",
        "txt_name",
        "txtName",
        "Text_Name",
        "txt_hp",
        "txtHP",
        "hp",
        "hp_bar",
        "bar_hp",
        "panel_top",
        "toplogo",
        "toplogo_widget",
        "txt_level",
        "txt_title",
    ]
    for method_name in ("rseek", "seek", "child", "childex", "rchild", "rchildex"):
        method = getattr(obj, method_name, None)
        if method is None:
            continue
        for name in candidates:
            try:
                found = method(name)
            except Exception:
                continue
            if found is not None:
                log(f"{label}.{method_name}({name!r}) -> {short(found)} type={type(found)!r}")
                dump(f"{label}.{method_name}.{name}", found)


def main():
    log("BEGIN " + str(time.time()))
    try:
        import common.EntityManager as EM
        entities = getattr(EM.EntityManager, "_entities", {})
        robots = [(str(k), e) for k, e in entities.items() if getattr(e, "IsRobotCombatAvatar", False)]
        log(f"robots={len(robots)}")
        if not robots:
            return
        key, robot = robots[0]
        log(f"robot={key} {robot!r}")
        for method_name in (
            "EnsureShootingRangeToplogo",
            "ShowEnemyToplogo",
            "RefreshToplogo",
            "RefreshToplogoTitles",
            "RefreshEnemyHpBar",
            "RefreshEnemyArmorBar",
            "DrawReconDroneMarkFrame",
            "SetToplogoVisible",
        ):
            try:
                method = getattr(robot, method_name)
                log(f"SOURCE {method_name} sig={inspect.signature(method)!r}")
                try:
                    log(inspect.getsource(method))
                except Exception as exc:
                    log(f"SOURCE {method_name} getsource FAIL {exc!r}")
            except Exception as exc:
                log(f"SOURCE {method_name} FAIL {exc!r}")

        for attr in ("toplogo_widget", "toplogo_border_widget", "toplogo", "recon_drone_frame_top_logo"):
            try:
                obj = getattr(robot, attr)
            except Exception as exc:
                log(f"robot.{attr}: FAIL {exc!r}")
                continue
            dump("robot." + attr, obj)
            try_seek("robot." + attr, obj)
    except Exception:
        log("EXC\n" + traceback.format_exc())
    finally:
        log("END")


main()

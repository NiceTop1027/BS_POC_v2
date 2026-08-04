import inspect
import time
import traceback

LOG = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_recon_frame_probe.log"


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def short(value, limit=1200):
    text = repr(value)
    if len(text) > limit:
        return text[:limit] + "...<cut>"
    return text


def call0(obj, name):
    try:
        method = getattr(obj, name, None)
        if method is None:
            return None
        return method()
    except Exception as exc:
        return f"ERR:{exc!r}"


def dump_state(label, obj):
    if obj is None:
        log(f"{label}: None")
        return
    log(f"{label}: {short(obj, 500)} type={type(obj)!r}")
    for attr in (
        "visible",
        "opacity",
        "scale",
        "scale_x",
        "scale_y",
        "width",
        "height",
        "pos",
        "x",
        "y",
        "z",
        "widget",
        "scene_node",
        "ui_node_top_logo",
        "toplogo_widget",
        "CSB_NAME",
    ):
        try:
            value = getattr(obj, attr)
        except Exception:
            continue
        log(f"{label}.{attr}={short(value, 700)} type={type(value)!r}")
    for method in (
        "GetWidth",
        "GetHeight",
        "GetContentSize",
        "GetRealContentSize",
        "GetWorldPosition",
        "GetPosition",
        "IsAncestorsVisible",
        "GetScale",
        "GetScaleX",
        "GetScaleY",
    ):
        value = call0(obj, method)
        if value is not None:
            log(f"{label}.{method}()={short(value, 700)}")


def dump_dir(label, obj):
    if obj is None:
        return
    try:
        names = [name for name in dir(obj) if not name.startswith("__")]
    except Exception as exc:
        log(f"{label}.dir FAIL {exc!r}")
        return
    interesting = [
        name
        for name in names
        if any(
            token in name.lower()
            for token in (
                "frame",
                "red",
                "box",
                "rect",
                "line",
                "img",
                "image",
                "panel",
                "node",
                "root",
                "scale",
                "size",
                "width",
                "height",
                "seek",
                "child",
                "visible",
                "opacity",
                "top",
                "logo",
            )
        )
    ]
    log(f"{label}.interesting={short(interesting, 5000)}")
    for name in interesting[:160]:
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
            log(f"{label}.{name}: {short(value, 700)} type={type(value)!r}")


def try_seek(label, obj):
    if obj is None:
        return
    candidates = [
        "root",
        "node",
        "toplogo",
        "top_logo",
        "ui_node_top_logo",
        "scene_node",
        "redframe",
        "red_frame",
        "node_red_frame",
        "img_red_frame",
        "img_redframe",
        "frame",
        "node_frame",
        "img_frame",
        "panel_frame",
        "box",
        "node_box",
        "img_box",
        "rect",
        "line",
        "line_top",
        "line_bottom",
        "line_left",
        "line_right",
        "Image",
        "image",
        "Panel",
        "panel",
        "node_ig_escape_hud_bottom_arms_range_redframe",
        "ig_escape_hud_bottom_arms_range_redframe",
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
                log(f"{label}.{method_name}({name!r}) -> {short(found, 500)} type={type(found)!r}")
                dump_state(f"{label}.{method_name}.{name}", found)


def main():
    log("BEGIN " + str(time.time()))
    try:
        import common.EntityManager as EM

        entities = getattr(EM.EntityManager, "_entities", {})
        robots = [(str(k), e) for k, e in entities.items() if getattr(e, "IsRobotCombatAvatar", False)]
        log(f"robots={len(robots)}")
        for key, robot in robots[:3]:
            log(f"ROBOT {key} {robot!r}")
            for method_name in ("EnsureShootingRangeToplogo", "ShowEnemyToplogo", "DrawReconDroneMarkFrame"):
                try:
                    result = getattr(robot, method_name)()
                    log(f"robot.{method_name}() -> {short(result, 500)}")
                except Exception as exc:
                    log(f"robot.{method_name} FAIL {exc!r}")
            frame = getattr(robot, "recon_drone_frame_top_logo", None)
            dump_state(f"robot[{key}].recon", frame)
            dump_dir(f"robot[{key}].recon", frame)
            try_seek(f"robot[{key}].recon", frame)
            for attr in ("ui_node_top_logo", "scene_node", "widget", "toplogo_widget"):
                child = getattr(frame, attr, None) if frame is not None else None
                dump_state(f"robot[{key}].recon.{attr}", child)
                dump_dir(f"robot[{key}].recon.{attr}", child)
                try_seek(f"robot[{key}].recon.{attr}", child)
    except Exception:
        log("EXC\n" + traceback.format_exc())
    finally:
        log("END")


main()

import time
import traceback

LOG = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_panel_frame_probe.log"


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def short(value, limit=900):
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


def call1(obj, name, arg):
    try:
        method = getattr(obj, name, None)
        if method is None:
            return None
        return method(arg)
    except Exception as exc:
        return f"ERR:{exc!r}"


def dump_obj(label, obj):
    if obj is None:
        log(f"{label}: None")
        return
    log(f"{label}: {short(obj, 500)} type={type(obj)!r}")
    for attr in ("visible", "opacity", "scale", "scale_x", "scale_y", "x", "y", "width", "height", "widget"):
        try:
            log(f"{label}.{attr}={short(getattr(obj, attr), 500)}")
        except Exception:
            pass
    for method in (
        "getName",
        "GetName",
        "GetWidth",
        "GetHeight",
        "getContentSize",
        "GetRealContentSize",
        "getPosition",
        "GetPosition",
        "getPositionX",
        "getPositionY",
        "getAnchorPoint",
        "GetWorldPosition",
        "getScale",
        "getScaleX",
        "getScaleY",
        "IsAncestorsVisible",
        "isVisible",
        "getChildrenCount",
    ):
        value = call0(obj, method)
        if value is not None:
            log(f"{label}.{method}()={short(value, 700)}")
    try:
        names = [name for name in dir(obj) if not name.startswith("__")]
        interesting = [
            name
            for name in names
            if any(token in name.lower() for token in ("child", "name", "size", "content", "pos", "scale", "width", "height", "visible", "anchor", "layout"))
        ]
        log(f"{label}.interesting={short(interesting, 5000)}")
    except Exception as exc:
        log(f"{label}.dir FAIL {exc!r}")


def children_of(obj):
    for method_name in ("getChildren", "GetChildren", "children"):
        try:
            method = getattr(obj, method_name, None)
            if method is None:
                continue
            result = method() if callable(method) else method
            if result is None:
                continue
            return list(result)
        except Exception as exc:
            log(f"children via {method_name} FAIL {exc!r}")
    return []


def dump_tree(label, obj, depth=0):
    if obj is None or depth > 3:
        return
    dump_obj(label, obj)
    raw = None
    try:
        raw = getattr(obj, "widget", None)
    except Exception:
        raw = None
    if raw is not None and raw is not obj:
        dump_obj(label + ".widget", raw)
        raw_children = children_of(raw)
        log(f"{label}.widget.children_count={len(raw_children)}")
        for idx, child in enumerate(raw_children[:30]):
            dump_tree(f"{label}.widget.child[{idx}]", child, depth + 1)

    direct_children = children_of(obj)
    log(f"{label}.children_count={len(direct_children)}")
    for idx, child in enumerate(direct_children[:30]):
        dump_tree(f"{label}.child[{idx}]", child, depth + 1)

    for method_name in ("seek", "child", "childex", "rseek", "rchild", "rchildex", "getChildByName", "GetChildByName"):
        method = getattr(obj, method_name, None)
        if method is None:
            continue
        for name in (
            "panel_frame",
            "img_frame",
            "red_frame",
            "img_red_frame",
            "frame",
            "left",
            "right",
            "top",
            "bottom",
            "line_left",
            "line_right",
            "line_top",
            "line_bottom",
            "img_left",
            "img_right",
            "img_top",
            "img_bottom",
            "Image_1",
            "Image_2",
            "Image_3",
            "Image_4",
        ):
            try:
                found = method(name)
            except Exception:
                continue
            if found is not None:
                log(f"{label}.{method_name}({name!r}) -> {short(found, 500)} type={type(found)!r}")
                dump_obj(f"{label}.{method_name}.{name}", found)


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
        for method_name in ("EnsureShootingRangeToplogo", "ShowEnemyToplogo", "DrawReconDroneMarkFrame"):
            try:
                method = getattr(robot, method_name)
                result = method(True) if method_name == "ShowEnemyToplogo" else method()
                log(f"{method_name} -> {short(result, 300)}")
            except Exception as exc:
                log(f"{method_name} FAIL {exc!r}")
        frame = getattr(robot, "recon_drone_frame_top_logo", None)
        node = getattr(frame, "ui_node_top_logo", None) if frame is not None else None
        panel = getattr(node, "panel_frame", None) if node is not None else None
        dump_tree(f"robot[{key}].panel_frame", panel)
    except Exception:
        log("EXC\n" + traceback.format_exc())
    finally:
        log("END")


main()

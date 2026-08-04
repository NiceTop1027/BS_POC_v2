import time
import traceback

LOG = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_internal_frame_children_probe.log"


def log(value):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(str(value) + "\n")


def call(obj, name, *args):
    try:
        fn = getattr(obj, name)
    except Exception:
        return None
    try:
        return fn(*args)
    except Exception as exc:
        return "ERR:" + repr(exc)


def short(value):
    try:
        return repr(value)[:800]
    except Exception:
        return "<repr>"


def dump(label, obj):
    if obj is None:
        log(label + " None")
        return
    log(label + " " + short(obj) + " type=" + repr(type(obj)))
    for method in (
        "getName", "GetName", "getChildrenCount", "getContentSize",
        "GetContentSize", "GetRealContentSize", "getPosition", "GetPosition",
        "getPositionX", "getPositionY", "getScale", "getScaleX", "getScaleY",
        "isVisible", "getAnchorPoint",
    ):
        value = call(obj, method)
        if value is not None:
            log(label + "." + method + "=" + short(value))
    try:
        names = [name for name in dir(obj) if not name.startswith("__")]
        log(label + ".interesting=" + repr([name for name in names if any(token in name.lower() for token in ("color", "opacity", "size", "scale", "pos", "visible", "child", "image", "texture"))])[:5000])
    except Exception as exc:
        log(label + ".dir=" + repr(exc))


def children(obj):
    for name in ("getChildren", "GetChildren", "children"):
        try:
            value = getattr(obj, name)
            value = value() if callable(value) else value
            if value is not None:
                return list(value)
        except Exception:
            pass
    return []


def main():
    log("BEGIN " + str(time.time()))
    try:
        import common.EntityManager as EM

        entities = getattr(EM.EntityManager, "_entities", {})
        robots = [ent for ent in entities.values() if getattr(ent, "IsRobotCombatAvatar", False)]
        if not robots:
            log("NO_ROBOTS")
            return
        robot = robots[0]
        for name in ("EnsureShootingRangeToplogo", "ShowEnemyToplogo", "DrawReconDroneMarkFrame"):
            try:
                result = getattr(robot, name)(True) if name == "ShowEnemyToplogo" else getattr(robot, name)()
                log(name + "=" + short(result))
            except Exception as exc:
                log(name + "=" + repr(exc))
        frame = getattr(robot, "recon_drone_frame_top_logo", None)
        node = getattr(frame, "ui_node_top_logo", None) if frame is not None else None
        raw = getattr(node, "widget", None) if node is not None else None
        dump("node", node)
        dump("node.widget", raw)
        for idx, child in enumerate(children(raw)):
            dump("node.widget.child[" + str(idx) + "]", child)
            for cidx, nested in enumerate(children(child)):
                dump("node.widget.child[" + str(idx) + "].child[" + str(cidx) + "]", nested)
    except Exception:
        log("EXC\n" + traceback.format_exc())
    finally:
        log("END")


main()

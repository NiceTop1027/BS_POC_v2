import inspect
import time
import traceback

_bounds_probe_log = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_avatar_bounds_probe.log"


def _bounds_probe_write(value):
    with open(_bounds_probe_log, "a", encoding="utf-8") as handle:
        handle.write(str(value) + "\n")


def _bounds_probe_short(value):
    try:
        return repr(value)[:1600]
    except Exception:
        return "<repr>"


def _bounds_probe_object(label, obj):
    if obj is None:
        _bounds_probe_write(label + " None")
        return
    _bounds_probe_write(label + " type=" + repr(type(obj)) + " repr=" + _bounds_probe_short(obj))
    try:
        names = [name for name in dir(obj) if not name.startswith("__")]
        wanted = [
            name for name in names
            if any(token in name.lower() for token in ("bound", "bone", "world", "model", "node", "height", "width", "position", "pos", "avatar"))
        ]
        _bounds_probe_write(label + " names=" + repr(wanted[:260]))
    except Exception as exc:
        _bounds_probe_write(label + " dir_fail=" + repr(exc))
        names = []
    for name in (
        "GetWorldBound", "GetPrimitiveWorldBound", "GetBoneWorldTransform",
        "GetBonePosition", "GetWorldPosition", "GetPosition", "GetModel",
        "GetNode", "GetAvatarModel", "GetRootNode", "GetSceneNode",
        "GetHeight", "GetWidth", "GetBoundingBox", "GetWorldBoundingBox",
    ):
        if name not in names:
            continue
        try:
            fn = getattr(obj, name)
            try:
                _bounds_probe_write(label + "." + name + " sig=" + repr(inspect.signature(fn)))
            except Exception:
                pass
            for args in ((), ("Head",), ("head",), ("Foot",), ("foot",)):
                try:
                    _bounds_probe_write(label + "." + name + repr(args) + " => " + _bounds_probe_short(fn(*args)))
                    break
                except Exception as exc:
                    if args == ():
                        _bounds_probe_write(label + "." + name + "() fail=" + repr(exc))
        except Exception as exc:
            _bounds_probe_write(label + "." + name + " getattr_fail=" + repr(exc))


def _bounds_probe_run():
    _bounds_probe_write("BEGIN " + str(time.time()))
    try:
        import common.EntityManager as _bounds_probe_em

        _bounds_probe_entities = getattr(_bounds_probe_em.EntityManager, "_entities", {})
        _bounds_probe_robots = [
            entity for entity in _bounds_probe_entities.values()
            if getattr(entity, "IsRobotCombatAvatar", False)
        ]
        if not _bounds_probe_robots:
            _bounds_probe_write("NO_ROBOTS")
            return
        _bounds_probe_robot = _bounds_probe_robots[0]
        _bounds_probe_object("robot", _bounds_probe_robot)
        for _bounds_probe_name in (
            "toplogo", "toplogo_widget", "recon_drone_frame_top_logo",
            "avatar", "model", "scene_node", "node", "entity",
        ):
            try:
                _bounds_probe_object("robot." + _bounds_probe_name, getattr(_bounds_probe_robot, _bounds_probe_name))
            except Exception:
                pass
    except Exception:
        _bounds_probe_write("EXC\n" + traceback.format_exc())
    finally:
        _bounds_probe_write("END")


_bounds_probe_run()

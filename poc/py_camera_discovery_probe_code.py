import sys
import time
import traceback

_camera_probe_log = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_camera_discovery_probe.log"


def _camera_probe_write(value):
    with open(_camera_probe_log, "a", encoding="utf-8") as handle:
        handle.write(str(value) + "\n")


def _camera_probe_short(value, limit=1200):
    try:
        return repr(value)[:limit]
    except Exception:
        return "<repr>"


def _camera_probe_dump(label, obj):
    if obj is None:
        _camera_probe_write(label + " None")
        return
    _camera_probe_write(label + " type=" + repr(type(obj)) + " repr=" + _camera_probe_short(obj))
    try:
        names = [name for name in dir(obj) if not name.startswith("__")]
        wanted = [
            name for name in names
            if any(token in name.lower() for token in ("camera", "project", "matrix", "screen", "world", "view", "fov", "convert"))
        ]
        _camera_probe_write(label + " names=" + repr(wanted[:260]))
    except Exception as exc:
        _camera_probe_write(label + " dir_fail=" + repr(exc))


def _camera_probe_children(label, obj, depth=0):
    if obj is None or depth > 2:
        return
    _camera_probe_dump(label, obj)
    try:
        children = list(obj.getChildren())
    except Exception:
        return
    _camera_probe_write(label + " child_count=" + str(len(children)))
    for index, child in enumerate(children[:60]):
        _camera_probe_children(label + ".child[" + str(index) + "]", child, depth + 1)


def _camera_probe_run():
    _camera_probe_write("BEGIN " + str(time.time()))
    try:
        _camera_names = sorted(
            name for name in sys.modules
            if any(token in name.lower() for token in ("camera", "render", "scene", "screen", "view", "world"))
        )
        _camera_probe_write("MODULES=" + repr(_camera_names[:1000]))

        import cc as _camera_cc

        _camera_director = _camera_cc.Director.getInstance()
        _camera_probe_children("scene", _camera_director.getRunningScene())
        _camera_probe_dump("glview", _camera_director.getOpenGLView())

        try:
            import common.EntityManager as _camera_em

            _camera_entities = getattr(_camera_em.EntityManager, "_entities", {})
            _camera_probe_write("entity_count=" + str(len(_camera_entities)))
            for _camera_key, _camera_entity in list(_camera_entities.items())[:40]:
                if not getattr(_camera_entity, "IsRobotCombatAvatar", False):
                    continue
                _camera_probe_dump("robot[" + str(_camera_key) + "].model", getattr(_camera_entity, "model", None))
                break
        except Exception as exc:
            _camera_probe_write("ENTITY_EXC=" + repr(exc))
    except Exception:
        _camera_probe_write("EXC\n" + traceback.format_exc())
    finally:
        _camera_probe_write("END")


_camera_probe_run()

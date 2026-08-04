import inspect
import sys
import time
import traceback

_mcamera_log_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_mcamera_probe.log"


def _mcamera_write(value):
    with open(_mcamera_log_path, "a", encoding="utf-8") as handle:
        handle.write(str(value) + "\n")


def _mcamera_short(value, limit=1600):
    try:
        return repr(value)[:limit]
    except Exception:
        return "<repr>"


def _mcamera_describe(label, obj):
    if obj is None:
        _mcamera_write(label + " None")
        return
    _mcamera_write(label + " type=" + repr(type(obj)) + " repr=" + _mcamera_short(obj))
    try:
        names = [name for name in dir(obj) if not name.startswith("__")]
    except Exception as exc:
        _mcamera_write(label + " dir_fail=" + repr(exc))
        return
    _mcamera_write(label + " names=" + repr(names[:1000]))
    for name in names[:600]:
        try:
            value = getattr(obj, name)
            if callable(value):
                try:
                    detail = "sig=" + repr(inspect.signature(value))
                except Exception:
                    detail = "callable=" + _mcamera_short(value)
                _mcamera_write(label + "." + name + " " + detail)
            elif any(token in name.lower() for token in ("camera", "view", "matrix", "world", "screen", "render", "project", "fov", "instance")):
                _mcamera_write(label + "." + name + "=" + _mcamera_short(value))
        except Exception as exc:
            _mcamera_write(label + "." + name + " fail=" + repr(exc))


def _mcamera_run():
    _mcamera_write("BEGIN " + str(time.time()))
    try:
        for _mcamera_name in ("MCamera", "MRender"):
            try:
                _mcamera_describe(_mcamera_name, __import__(_mcamera_name))
            except Exception as exc:
                _mcamera_write(_mcamera_name + " import_fail=" + repr(exc))

        for _mcamera_name in (
            "gclient.framework.camera",
            "gclient.framework.entities.camera",
            "gclient.framework.camera.types",
            "gclient.framework.camera.engine_placer",
        ):
            _mcamera_describe(_mcamera_name, sys.modules.get(_mcamera_name))

        _mcamera_candidates = []
        for _mcamera_module_name, _mcamera_module in list(sys.modules.items()):
            if _mcamera_module is None or "camera" not in _mcamera_module_name.lower():
                continue
            try:
                for _mcamera_attr in dir(_mcamera_module):
                    _mcamera_low = _mcamera_attr.lower()
                    if _mcamera_low in ("camera", "main_camera", "current_camera", "camera_mgr", "camera_manager"):
                        _mcamera_value = getattr(_mcamera_module, _mcamera_attr)
                        _mcamera_candidates.append((_mcamera_module_name, _mcamera_attr, _mcamera_short(_mcamera_value)))
            except Exception:
                pass
        _mcamera_write("CAMERA_GLOBALS=" + repr(_mcamera_candidates[:300]))
    except Exception:
        _mcamera_write("EXC\n" + traceback.format_exc())
    finally:
        _mcamera_write("END")


_mcamera_run()

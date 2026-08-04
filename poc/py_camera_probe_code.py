import dis as _ctf_cam_dis
import io as _ctf_cam_io
import time as _ctf_cam_time
import traceback as _ctf_cam_traceback
import types as _ctf_cam_types


_ctf_cam_log_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_camera_probe.log"


def _ctf_cam_write(value):
    with open(_ctf_cam_log_path, "a", encoding="utf-8") as _ctf_cam_handle:
        _ctf_cam_handle.write(str(value) + "\n")


def _ctf_cam_short(value, limit=3000):
    try:
        return repr(value)[:limit]
    except Exception:
        return "<repr failed>"


def _ctf_cam_object(label, value):
    _ctf_cam_write(label + " type=" + _ctf_cam_short(type(value)) + " repr=" + _ctf_cam_short(value))
    if value is None:
        return
    try:
        _ctf_cam_names = [
            _ctf_cam_name for _ctf_cam_name in dir(value)
            if not _ctf_cam_name.startswith("__")
        ]
        _ctf_cam_write(label + ".dir=" + _ctf_cam_short(_ctf_cam_names, 12000))
    except Exception:
        return
    for _ctf_cam_name in _ctf_cam_names[:200]:
        try:
            _ctf_cam_child = getattr(value, _ctf_cam_name)
        except Exception:
            continue
        if callable(_ctf_cam_child):
            continue
        _ctf_cam_write(label + "." + _ctf_cam_name + "=" + _ctf_cam_short(_ctf_cam_child))


def _ctf_cam_disassemble(label, candidate):
    _ctf_cam_code = candidate.__code__
    _ctf_cam_stream = _ctf_cam_io.StringIO()
    try:
        _ctf_cam_dis.dis(candidate, file=_ctf_cam_stream)
        _ctf_cam_write("DIS " + label + " names=" + _ctf_cam_short(_ctf_cam_code.co_names) + "\n" + _ctf_cam_stream.getvalue()[:7000])
    except Exception as exc:
        _ctf_cam_write("DIS " + label + " fail=" + repr(exc))


def _ctf_cam_run():
    _ctf_cam_write("BEGIN " + str(_ctf_cam_time.time()))
    try:
        import MCamera as _ctf_cam_native
        import common.EntityManager as _ctf_cam_em
        import gclient.framework.entities.camera as _ctf_cam_py
        _ctf_cam_object("MCamera", _ctf_cam_native)
        for _ctf_cam_name in ("CameraFrame", "CameraRuntimeInfo"):
            _ctf_cam_cls = getattr(_ctf_cam_native, _ctf_cam_name, None)
            _ctf_cam_object("MCamera." + _ctf_cam_name, _ctf_cam_cls)
            if _ctf_cam_cls is not None:
                for _ctf_cam_args in ((), (0,), (1,)):
                    try:
                        _ctf_cam_instance = _ctf_cam_cls(*_ctf_cam_args)
                        _ctf_cam_object("MCamera." + _ctf_cam_name + str(_ctf_cam_args), _ctf_cam_instance)
                        break
                    except Exception as _ctf_cam_exc:
                        _ctf_cam_write("MCamera." + _ctf_cam_name + str(_ctf_cam_args) + " fail=" + repr(_ctf_cam_exc))

        _ctf_cam_write("Camera class names=" + _ctf_cam_short([_ctf_cam_name for _ctf_cam_name in vars(_ctf_cam_py.Camera) if not _ctf_cam_name.startswith("__")], 12000))
        for _ctf_cam_name, _ctf_cam_value in vars(_ctf_cam_py.Camera).items():
            if isinstance(_ctf_cam_value, _ctf_cam_types.FunctionType) and any(_ctf_cam_token in _ctf_cam_name.lower() for _ctf_cam_token in ("camera", "screen", "world", "project", "update", "tick")):
                _ctf_cam_disassemble("Camera." + _ctf_cam_name, _ctf_cam_value)

        _ctf_cam_entities = getattr(_ctf_cam_em.EntityManager, "_entities", {})
        _ctf_cam_write("ENTITIES=" + _ctf_cam_short([(str(_ctf_cam_key), type(_ctf_cam_entity).__name__) for _ctf_cam_key, _ctf_cam_entity in _ctf_cam_entities.items()], 16000))
        _ctf_cam_players = [
            _ctf_cam_entity for _ctf_cam_entity in _ctf_cam_entities.values()
            if getattr(_ctf_cam_entity, "IsPlayerCombatAvatar", False)
        ]
        _ctf_cam_player = _ctf_cam_players[0] if _ctf_cam_players else None
        _ctf_cam_object("player", _ctf_cam_player)
        if _ctf_cam_player is not None:
            for _ctf_cam_method in ("GetCameraId", "_GetCameraData_FPS", "_GetCameraData_TPS", "_GetCameraData_AIM"):
                try:
                    _ctf_cam_object("player." + _ctf_cam_method + "()", getattr(_ctf_cam_player, _ctf_cam_method)())
                except Exception as _ctf_cam_exc:
                    _ctf_cam_write("player." + _ctf_cam_method + " fail=" + repr(_ctf_cam_exc))
            for _ctf_cam_attr in ("last_camera_frame", "camera_controller", "camera_date_getters", "model"):
                try:
                    _ctf_cam_object("player." + _ctf_cam_attr, getattr(_ctf_cam_player, _ctf_cam_attr))
                except Exception as _ctf_cam_exc:
                    _ctf_cam_write("player." + _ctf_cam_attr + " fail=" + repr(_ctf_cam_exc))

        for _ctf_cam_key, _ctf_cam_entity in _ctf_cam_entities.items():
            if "camera" in type(_ctf_cam_entity).__name__.lower():
                _ctf_cam_object("camera entity " + str(_ctf_cam_key), _ctf_cam_entity)
    except Exception:
        _ctf_cam_write("EXC\n" + _ctf_cam_traceback.format_exc())
    finally:
        _ctf_cam_write("END")


_ctf_cam_run()

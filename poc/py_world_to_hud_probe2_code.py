import dis as _ctf_w2h2_dis
import io as _ctf_w2h2_io
import sys as _ctf_w2h2_sys
import time as _ctf_w2h2_time
import traceback as _ctf_w2h2_traceback


_ctf_w2h2_log_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_world_to_hud_probe2.log"


def _ctf_w2h2_write(value):
    with open(_ctf_w2h2_log_path, "a", encoding="utf-8") as _ctf_w2h2_handle:
        _ctf_w2h2_handle.write(str(value) + "\n")


def _ctf_w2h2_short(value, limit=2000):
    try:
        return repr(value)[:limit]
    except Exception:
        return "<repr failed>"


def _ctf_w2h2_details(label, value):
    _ctf_w2h2_write(label + " type=" + _ctf_w2h2_short(type(value)) + " repr=" + _ctf_w2h2_short(value))
    if value is None:
        return
    for _ctf_w2h2_attr in ("x", "y", "z", "w", "engine_camera", "controller", "position"):
        try:
            _ctf_w2h2_write(label + "." + _ctf_w2h2_attr + "=" + _ctf_w2h2_short(getattr(value, _ctf_w2h2_attr)))
        except Exception:
            pass
    try:
        _ctf_w2h2_write(label + ".tuple=" + _ctf_w2h2_short(tuple(value)))
    except Exception:
        pass


def _ctf_w2h2_try(label, function, *args):
    try:
        _ctf_w2h2_result = function(*args)
        _ctf_w2h2_write(label + " => " + _ctf_w2h2_short(_ctf_w2h2_result))
        _ctf_w2h2_details(label + ".result", _ctf_w2h2_result)
        return _ctf_w2h2_result
    except Exception as _ctf_w2h2_exc:
        _ctf_w2h2_write(label + " fail=" + repr(_ctf_w2h2_exc))
        return None


def _ctf_w2h2_make_vector(vector_type, x, y, z):
    for _ctf_w2h2_args in ((x, y, z), (), ((x, y, z),)):
        try:
            _ctf_w2h2_vector = vector_type(*_ctf_w2h2_args)
            try:
                _ctf_w2h2_vector.x = x
                _ctf_w2h2_vector.y = y
                _ctf_w2h2_vector.z = z
            except Exception:
                pass
            return _ctf_w2h2_vector
        except Exception:
            pass
    return None


def _ctf_w2h2_scan_callers():
    _ctf_w2h2_hits = []
    for _ctf_w2h2_module_name, _ctf_w2h2_module in list(_ctf_w2h2_sys.modules.items()):
        if _ctf_w2h2_module is None or not (
            _ctf_w2h2_module_name.startswith("gclient")
            or _ctf_w2h2_module_name.startswith("common")
            or ".ui" in _ctf_w2h2_module_name
        ):
            continue
        try:
            _ctf_w2h2_items = list(vars(_ctf_w2h2_module).items())
        except Exception:
            continue
        for _ctf_w2h2_name, _ctf_w2h2_value in _ctf_w2h2_items:
            _ctf_w2h2_code = getattr(_ctf_w2h2_value, "__code__", None)
            if _ctf_w2h2_code is not None and "TransformFromWorldToHudWorld" in _ctf_w2h2_code.co_names:
                _ctf_w2h2_hits.append((_ctf_w2h2_module_name, _ctf_w2h2_name, _ctf_w2h2_value))
            if isinstance(_ctf_w2h2_value, type):
                for _ctf_w2h2_method_name, _ctf_w2h2_method in vars(_ctf_w2h2_value).items():
                    _ctf_w2h2_code = getattr(_ctf_w2h2_method, "__code__", None)
                    if _ctf_w2h2_code is not None and "TransformFromWorldToHudWorld" in _ctf_w2h2_code.co_names:
                        _ctf_w2h2_hits.append((_ctf_w2h2_module_name, _ctf_w2h2_value.__name__ + "." + _ctf_w2h2_method_name, _ctf_w2h2_method))
    _ctf_w2h2_write("caller_count=" + str(len(_ctf_w2h2_hits)))
    for _ctf_w2h2_module_name, _ctf_w2h2_name, _ctf_w2h2_value in _ctf_w2h2_hits[:50]:
        _ctf_w2h2_buf = _ctf_w2h2_io.StringIO()
        try:
            _ctf_w2h2_dis.dis(_ctf_w2h2_value, file=_ctf_w2h2_buf)
            _ctf_w2h2_body = _ctf_w2h2_buf.getvalue()[-8000:]
        except Exception as _ctf_w2h2_exc:
            _ctf_w2h2_body = repr(_ctf_w2h2_exc)
        _ctf_w2h2_write("CALLER " + _ctf_w2h2_module_name + "." + _ctf_w2h2_name + "\n" + _ctf_w2h2_body)


def _ctf_w2h2_run():
    _ctf_w2h2_write("BEGIN " + str(_ctf_w2h2_time.time()))
    try:
        import MRender as _ctf_w2h2_render
        import MType as _ctf_w2h2_type
        import common.EntityManager as _ctf_w2h2_em
        import gclient.framework.entities.camera as _ctf_w2h2_camera_module

        _ctf_w2h2_entities = getattr(_ctf_w2h2_em.EntityManager, "_entities", {})
        _ctf_w2h2_robot = next(
            (_ctf_w2h2_entity for _ctf_w2h2_entity in _ctf_w2h2_entities.values() if getattr(_ctf_w2h2_entity, "IsRobotCombatAvatar", False)),
            None,
        )
        _ctf_w2h2_point = None
        if _ctf_w2h2_robot is not None:
            _ctf_w2h2_point = getattr(_ctf_w2h2_robot.model.GetWorldBound(), "min")
        _ctf_w2h2_details("input", _ctf_w2h2_point)

        _ctf_w2h2_vector_type = getattr(_ctf_w2h2_type, "Vector3", None)
        _ctf_w2h2_output_vector = _ctf_w2h2_make_vector(_ctf_w2h2_vector_type, 0.0, 0.0, 0.0)
        _ctf_w2h2_details("output_vector", _ctf_w2h2_output_vector)

        _ctf_w2h2_genv = getattr(_ctf_w2h2_camera_module, "genv", None)
        _ctf_w2h2_details("camera_module.genv", _ctf_w2h2_genv)
        _ctf_w2h2_candidates = [
            ("None", None),
            ("zero", 0),
            ("one", 1),
            ("false", False),
            ("output_vector", _ctf_w2h2_output_vector),
        ]
        if _ctf_w2h2_genv is not None:
            _ctf_w2h2_env_names = [
                _ctf_w2h2_name for _ctf_w2h2_name in dir(_ctf_w2h2_genv)
                if any(_ctf_w2h2_token in _ctf_w2h2_name.lower() for _ctf_w2h2_token in ("camera", "hud", "world", "render"))
            ]
            _ctf_w2h2_write("genv.names=" + _ctf_w2h2_short(_ctf_w2h2_env_names, 10000))
            for _ctf_w2h2_name in _ctf_w2h2_env_names[:80]:
                try:
                    _ctf_w2h2_value = getattr(_ctf_w2h2_genv, _ctf_w2h2_name)
                    _ctf_w2h2_details("genv." + _ctf_w2h2_name, _ctf_w2h2_value)
                    _ctf_w2h2_candidates.append(("genv." + _ctf_w2h2_name, _ctf_w2h2_value))
                    for _ctf_w2h2_child_name in ("engine_camera", "controller"):
                        try:
                            _ctf_w2h2_child = getattr(_ctf_w2h2_value, _ctf_w2h2_child_name)
                            _ctf_w2h2_details("genv." + _ctf_w2h2_name + "." + _ctf_w2h2_child_name, _ctf_w2h2_child)
                            _ctf_w2h2_candidates.append(("genv." + _ctf_w2h2_name + "." + _ctf_w2h2_child_name, _ctf_w2h2_child))
                        except Exception:
                            pass
                except Exception:
                    pass

        for _ctf_w2h2_entity_key, _ctf_w2h2_entity in list(_ctf_w2h2_entities.items()):
            if "camera" in type(_ctf_w2h2_entity).__name__.lower() or "camera" in str(_ctf_w2h2_entity_key).lower():
                _ctf_w2h2_details("entity." + str(_ctf_w2h2_entity_key), _ctf_w2h2_entity)
                _ctf_w2h2_candidates.append(("entity." + str(_ctf_w2h2_entity_key), _ctf_w2h2_entity))

        if _ctf_w2h2_point is not None:
            for _ctf_w2h2_name, _ctf_w2h2_candidate in _ctf_w2h2_candidates:
                _ctf_w2h2_try(
                    "WorldToHud(" + _ctf_w2h2_name + ")",
                    _ctf_w2h2_render.TransformFromWorldToHudWorld,
                    _ctf_w2h2_point,
                    _ctf_w2h2_candidate,
                )
        _ctf_w2h2_scan_callers()
    except Exception:
        _ctf_w2h2_write("EXC\n" + _ctf_w2h2_traceback.format_exc())
    finally:
        _ctf_w2h2_write("END")


_ctf_w2h2_run()

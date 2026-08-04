import inspect as _ctf_w2h_inspect
import sys as _ctf_w2h_sys
import time as _ctf_w2h_time
import traceback as _ctf_w2h_traceback


_ctf_w2h_log_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_world_to_hud_probe.log"


def _ctf_w2h_write(value):
    with open(_ctf_w2h_log_path, "a", encoding="utf-8") as _ctf_w2h_handle:
        _ctf_w2h_handle.write(str(value) + "\n")


def _ctf_w2h_short(value, limit=2200):
    try:
        return repr(value)[:limit]
    except Exception:
        return "<repr failed>"


def _ctf_w2h_point_details(label, value):
    _ctf_w2h_write(label + " type=" + _ctf_w2h_short(type(value)) + " repr=" + _ctf_w2h_short(value))
    for _ctf_w2h_attr in ("x", "y", "z", "w"):
        try:
            _ctf_w2h_write(label + "." + _ctf_w2h_attr + "=" + _ctf_w2h_short(getattr(value, _ctf_w2h_attr)))
        except Exception:
            pass
    try:
        _ctf_w2h_write(label + " tuple=" + _ctf_w2h_short(tuple(value)))
    except Exception:
        pass


def _ctf_w2h_try(label, fn, *args):
    try:
        _ctf_w2h_result = fn(*args)
        _ctf_w2h_write(label + " => " + _ctf_w2h_short(_ctf_w2h_result))
        _ctf_w2h_point_details(label + ".result", _ctf_w2h_result)
        return _ctf_w2h_result
    except Exception as _ctf_w2h_exc:
        _ctf_w2h_write(label + " fail=" + repr(_ctf_w2h_exc))
        return None


def _ctf_w2h_source_window(source, needle, radius=12):
    _ctf_w2h_lines = source.splitlines()
    _ctf_w2h_hits = [index for index, line in enumerate(_ctf_w2h_lines) if needle.lower() in line.lower()]
    for _ctf_w2h_index in _ctf_w2h_hits[:20]:
        _ctf_w2h_start = max(0, _ctf_w2h_index - radius)
        _ctf_w2h_end = min(len(_ctf_w2h_lines), _ctf_w2h_index + radius + 1)
        _ctf_w2h_write(
            "SOURCE needle=" + needle + " lines=" + str(_ctf_w2h_start + 1) + "-" + str(_ctf_w2h_end)
            + "\n" + "\n".join(_ctf_w2h_lines[_ctf_w2h_start:_ctf_w2h_end])
        )


def _ctf_w2h_run():
    _ctf_w2h_write("BEGIN " + str(_ctf_w2h_time.time()))
    try:
        import MRender as _ctf_w2h_render
        import MUI as _ctf_w2h_mui
        import common.EntityManager as _ctf_w2h_em
        import gclient.framework.entities.camera as _ctf_w2h_camera_module

        _ctf_w2h_write("screen=" + _ctf_w2h_short((_ctf_w2h_mui.GetScreenWidth(), _ctf_w2h_mui.GetScreenHeight())))
        _ctf_w2h_render_names = [
            _ctf_w2h_name for _ctf_w2h_name in dir(_ctf_w2h_render)
            if any(_ctf_w2h_token in _ctf_w2h_name.lower() for _ctf_w2h_token in ("transform", "hud", "world", "camera", "view", "matrix", "project"))
        ]
        _ctf_w2h_write("MRender.names=" + _ctf_w2h_short(_ctf_w2h_render_names, 8000))
        for _ctf_w2h_name in _ctf_w2h_render_names:
            try:
                _ctf_w2h_value = getattr(_ctf_w2h_render, _ctf_w2h_name)
                if callable(_ctf_w2h_value):
                    try:
                        _ctf_w2h_sig = _ctf_w2h_inspect.signature(_ctf_w2h_value)
                    except Exception as _ctf_w2h_exc:
                        _ctf_w2h_sig = "<" + repr(_ctf_w2h_exc) + ">"
                    _ctf_w2h_write(
                        "MRender." + _ctf_w2h_name + " sig=" + _ctf_w2h_short(_ctf_w2h_sig)
                        + " doc=" + _ctf_w2h_short(getattr(_ctf_w2h_value, "__doc__", None))
                        + " textsig=" + _ctf_w2h_short(getattr(_ctf_w2h_value, "__text_signature__", None))
                    )
            except Exception as _ctf_w2h_exc:
                _ctf_w2h_write("MRender." + _ctf_w2h_name + " inspect_fail=" + repr(_ctf_w2h_exc))

        _ctf_w2h_entities = getattr(_ctf_w2h_em.EntityManager, "_entities", {})
        _ctf_w2h_robot = next(
            (_ctf_w2h_entity for _ctf_w2h_entity in _ctf_w2h_entities.values() if getattr(_ctf_w2h_entity, "IsRobotCombatAvatar", False)),
            None,
        )
        if _ctf_w2h_robot is not None:
            _ctf_w2h_model = getattr(_ctf_w2h_robot, "model", None)
            _ctf_w2h_bound = _ctf_w2h_model.GetWorldBound()
            _ctf_w2h_write("bound=" + _ctf_w2h_short(_ctf_w2h_bound))
            for _ctf_w2h_name in ("min", "max"):
                _ctf_w2h_point = getattr(_ctf_w2h_bound, _ctf_w2h_name)
                _ctf_w2h_point_details("bound." + _ctf_w2h_name, _ctf_w2h_point)
                _ctf_w2h_try("WorldToHud(" + _ctf_w2h_name + ")", _ctf_w2h_render.TransformFromWorldToHudWorld, _ctf_w2h_point)
                _ctf_w2h_try("HudToWorld(" + _ctf_w2h_name + ")", _ctf_w2h_render.TransformFromHudWorldToWorld, _ctf_w2h_point)

        _ctf_w2h_camera_class = _ctf_w2h_camera_module.Camera
        _ctf_w2h_write("Camera.dir=" + _ctf_w2h_short([_ctf_w2h_name for _ctf_w2h_name in dir(_ctf_w2h_camera_class) if not _ctf_w2h_name.startswith("__")], 10000))
        try:
            _ctf_w2h_source = _ctf_w2h_inspect.getsource(_ctf_w2h_camera_class)
            _ctf_w2h_write("Camera.source_length=" + str(len(_ctf_w2h_source)))
            for _ctf_w2h_needle in ("MRender", "Hud", "World", "camera", "matrix", "screen"):
                _ctf_w2h_source_window(_ctf_w2h_source, _ctf_w2h_needle)
        except Exception as _ctf_w2h_exc:
            _ctf_w2h_write("Camera.source_fail=" + repr(_ctf_w2h_exc))
            for _ctf_w2h_name in dir(_ctf_w2h_camera_class):
                if _ctf_w2h_name.startswith("__"):
                    continue
                try:
                    _ctf_w2h_method = getattr(_ctf_w2h_camera_class, _ctf_w2h_name)
                    _ctf_w2h_code = getattr(_ctf_w2h_method, "__code__", None)
                    if _ctf_w2h_code is not None:
                        _ctf_w2h_names = _ctf_w2h_code.co_names
                        if any(_ctf_w2h_token.lower() in " ".join(_ctf_w2h_names).lower() for _ctf_w2h_token in ("render", "world", "hud", "camera", "matrix", "screen")):
                            _ctf_w2h_write("Camera." + _ctf_w2h_name + ".names=" + _ctf_w2h_short(_ctf_w2h_names, 4000))
                except Exception:
                    pass
    except Exception:
        _ctf_w2h_write("EXC\n" + _ctf_w2h_traceback.format_exc())
    finally:
        _ctf_w2h_write("END")


_ctf_w2h_run()

import json as _ctf_proj_json
import time as _ctf_proj_time
import traceback as _ctf_proj_traceback


_ctf_proj_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\projection_probe.json"
_ctf_proj_log_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_projection_probe.log"


def _ctf_proj_xyz(value):
    try:
        return [float(value.x), float(value.y), float(value.z)]
    except Exception:
        try:
            return [float(value[i]) for i in range(3)]
        except Exception:
            return None


def _ctf_proj_write_log(value):
    with open(_ctf_proj_log_path, "a", encoding="utf-8") as _ctf_proj_handle:
        _ctf_proj_handle.write(str(value) + "\n")


def _ctf_proj_run():
    try:
        import MCamera as _ctf_proj_camera
        import MRender as _ctf_proj_render
        import MUI as _ctf_proj_ui
        import common.EntityManager as _ctf_proj_em

        _ctf_proj_entities = getattr(_ctf_proj_em.EntityManager, "_entities", {})
        _ctf_proj_players = [
            (_ctf_proj_key, _ctf_proj_entity) for _ctf_proj_key, _ctf_proj_entity in _ctf_proj_entities.items()
            if getattr(_ctf_proj_entity, "IsPlayerCombatAvatar", False)
        ]
        _ctf_proj_robots = [
            (_ctf_proj_key, _ctf_proj_entity) for _ctf_proj_key, _ctf_proj_entity in _ctf_proj_entities.items()
            if getattr(_ctf_proj_entity, "IsRobotCombatAvatar", False)
        ]
        _ctf_proj_frame = _ctf_proj_camera.CaptureFrame()
        _ctf_proj_screen = _ctf_proj_ui.GetScreenSize()
        _ctf_proj_rows = []
        for _ctf_proj_key, _ctf_proj_robot in _ctf_proj_robots:
            try:
                _ctf_proj_bound = _ctf_proj_robot.model.GetWorldBound()
                _ctf_proj_low = _ctf_proj_xyz(_ctf_proj_bound.min)
                _ctf_proj_high = _ctf_proj_xyz(_ctf_proj_bound.max)
                _ctf_proj_rows.append({
                    "key": str(_ctf_proj_key),
                    "position": _ctf_proj_xyz(getattr(_ctf_proj_robot, "position", None)),
                    "min": _ctf_proj_low,
                    "max": _ctf_proj_high,
                    "hud0_min": _ctf_proj_xyz(_ctf_proj_render.TransformFromWorldToHudWorld(_ctf_proj_bound.min, 0)),
                    "hud0_max": _ctf_proj_xyz(_ctf_proj_render.TransformFromWorldToHudWorld(_ctf_proj_bound.max, 0)),
                    "hud1_min": _ctf_proj_xyz(_ctf_proj_render.TransformFromWorldToHudWorld(_ctf_proj_bound.min, 1)),
                    "hud1_max": _ctf_proj_xyz(_ctf_proj_render.TransformFromWorldToHudWorld(_ctf_proj_bound.max, 1)),
                })
            except Exception as _ctf_proj_exc:
                _ctf_proj_rows.append({"key": str(_ctf_proj_key), "error": repr(_ctf_proj_exc)})
        _ctf_proj_payload = {
            "ts": _ctf_proj_time.time(),
            "screen": [int(_ctf_proj_screen.x), int(_ctf_proj_screen.y)],
            "camera": {
                "position": _ctf_proj_xyz(_ctf_proj_frame.Position),
                "yaw": float(_ctf_proj_frame.Yaw),
                "pitch": float(_ctf_proj_frame.Pitch),
                "roll": float(_ctf_proj_frame.Roll),
                "fov": float(_ctf_proj_frame.Fov),
            },
            "players": [{"key": str(_ctf_proj_key), "position": _ctf_proj_xyz(getattr(_ctf_proj_player, "position", None))} for _ctf_proj_key, _ctf_proj_player in _ctf_proj_players],
            "robots": _ctf_proj_rows,
        }
        with open(_ctf_proj_path, "w", encoding="utf-8") as _ctf_proj_handle:
            _ctf_proj_json.dump(_ctf_proj_payload, _ctf_proj_handle, ensure_ascii=True, indent=2)
        _ctf_proj_write_log("OK " + _ctf_proj_json.dumps(_ctf_proj_payload, ensure_ascii=True))
    except Exception:
        _ctf_proj_write_log("EXC\n" + _ctf_proj_traceback.format_exc())


_ctf_proj_run()

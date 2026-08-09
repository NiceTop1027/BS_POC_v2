"""State exporter for the local CTF ESP renderer.

The renderer is the native C++ process in cpp_overlay.  This module only reads
the isolated game's own entity and camera state, then writes an atomically
replaced text snapshot for the renderer to consume.
"""

import builtins as _ctf_native_builtins
import gc as _ctf_native_gc
import math as _ctf_native_math
import os as _ctf_native_os
import time as _ctf_native_time
import traceback as _ctf_native_traceback


_ctf_native_state_name = "_ctf_bloodstrike_native_esp_state"
_ctf_native_legacy_state_name = "_ctf_bloodstrike_live_esp_state"
_ctf_native_root = _ctf_native_os.path.dirname(_ctf_native_os.path.abspath(__file__))
_ctf_native_snapshot_path = _ctf_native_os.path.join(_ctf_native_root, "ctf_native_esp_state.txt")
_ctf_native_snapshot_temp_path = _ctf_native_snapshot_path + ".tmp"
_ctf_native_log_path = _ctf_native_os.path.join(_ctf_native_root, "ctf_native_esp.log")
_ctf_native_config_path = _ctf_native_os.path.join(_ctf_native_root, "ctf_native_esp_config.txt")
_ctf_native_aim_trigger_path = _ctf_native_os.path.join(_ctf_native_root, "ctf_native_aim_trigger.txt")
_ctf_native_default_max_distance = 800.0
_ctf_native_hard_max_distance = 800.0
_ctf_native_default_magic_hitbox_range = 3000.0
_ctf_native_hard_magic_hitbox_range = 3000.0
_ctf_native_default_hitbox_scale = 1.46
_ctf_native_max_hitbox_scale = 12.0
_ctf_native_aim_bones = (
    "biped Head",
    "biped Neck",
    "biped Spine2",
    "biped Spine1",
    "biped Spine",
    "biped Pelvis",
)
_ctf_native_vk_rbutton = 0x02
_ctf_native_user32 = None
# The host calls the timer close to 60 Hz.  A 1/60 throttle can reject callbacks
# that arrive a fraction early and halve the effective rate, so keep this below
# one host tick while leaving visibility checks independently cached.
_ctf_native_snapshot_interval = 1.0 / 240.0


def _ctf_native_log(message):
    try:
        with open(_ctf_native_log_path, "a", encoding="utf-8") as _ctf_native_handle:
            _ctf_native_handle.write("{:.3f} {}\n".format(_ctf_native_time.time(), message))
    except Exception:
        pass


def _ctf_native_call(obj, name, *args):
    try:
        return getattr(obj, name)(*args)
    except Exception:
        return None


def _ctf_native_vec3(value):
    if value is None:
        return None
    try:
        return (float(value.x), float(value.y), float(value.z))
    except Exception:
        pass
    try:
        return (float(value[0]), float(value[1]), float(value[2]))
    except Exception:
        return None


def _ctf_native_make_vec3_like(template, point):
    try:
        _ctf_native_value = template.clone()
        _ctf_native_value.x = float(point[0])
        _ctf_native_value.y = float(point[1])
        _ctf_native_value.z = float(point[2])
        return _ctf_native_value
    except Exception:
        pass
    try:
        import MType as _ctf_native_mtype
        _ctf_native_value = _ctf_native_mtype.Vector3()
        _ctf_native_value.x = float(point[0])
        _ctf_native_value.y = float(point[1])
        _ctf_native_value.z = float(point[2])
        return _ctf_native_value
    except Exception:
        return None


def _ctf_native_point_in_bounds(point, low, high, padding=0.45):
    if point is None or low is None or high is None:
        return True
    try:
        return (
            low[0] - padding <= point[0] <= high[0] + padding and
            low[1] - padding <= point[1] <= high[1] + padding and
            low[2] - padding <= point[2] <= high[2] + padding
        )
    except Exception:
        return False


def _ctf_native_ensure_aim_bones(state, key, model):
    _ctf_native_models = state.setdefault("aim_bone_models", {})
    _ctf_native_model_id = id(model)
    if _ctf_native_models.get(key) == _ctf_native_model_id:
        return
    for _ctf_native_bone in _ctf_native_aim_bones:
        _ctf_native_call(model, "CreateSpecifyBone", _ctf_native_bone)
    _ctf_native_models[key] = _ctf_native_model_id


def _ctf_native_upper_body_fallback_points(camera_pos, low, high):
    if low is None or high is None:
        return ()
    try:
        _ctf_native_height = float(high[1] - low[1])
        if not _ctf_native_math.isfinite(_ctf_native_height) or _ctf_native_height <= 0.25:
            return ()
        _ctf_native_x = (low[0] + high[0]) * 0.5
        _ctf_native_z = (low[2] + high[2]) * 0.5
        _ctf_native_top_margin = min(0.22, max(0.08, _ctf_native_height * 0.12))
        _ctf_native_candidates = (
            (_ctf_native_x, high[1] - _ctf_native_top_margin, _ctf_native_z),
            (_ctf_native_x, low[1] + _ctf_native_height * 0.72, _ctf_native_z),
            (_ctf_native_x, low[1] + _ctf_native_height * 0.58, _ctf_native_z),
        )
        _ctf_native_result = []
        for _ctf_native_point in _ctf_native_candidates:
            _ctf_native_vec = _ctf_native_make_vec3_like(camera_pos, _ctf_native_point)
            if _ctf_native_vec is not None:
                _ctf_native_result.append((_ctf_native_vec, _ctf_native_point))
        return tuple(_ctf_native_result)
    except Exception:
        return ()


def _ctf_native_position(entity):
    for _ctf_native_name in ("position", "pos", "last_position"):
        try:
            _ctf_native_value = getattr(entity, _ctf_native_name)
            if callable(_ctf_native_value):
                _ctf_native_value = _ctf_native_value()
            _ctf_native_result = _ctf_native_vec3(_ctf_native_value)
            if _ctf_native_result is not None:
                return _ctf_native_result
        except Exception:
            pass
    return None


def _ctf_native_metric(entity, names, default=0.0):
    for _ctf_native_name in names:
        try:
            _ctf_native_value = getattr(entity, _ctf_native_name)
            if callable(_ctf_native_value):
                _ctf_native_value = _ctf_native_value()
            return float(_ctf_native_value)
        except Exception:
            pass
    return float(default)


def _ctf_native_max_target_distance(state):
    """Refresh the overlay-controlled range without adding per-frame file I/O."""
    _ctf_native_now = _ctf_native_time.time()
    if _ctf_native_now < state.get("next_config_refresh", 0.0):
        return state.get("max_target_distance", _ctf_native_default_max_distance)

    state["next_config_refresh"] = _ctf_native_now + 0.5
    _ctf_native_value = _ctf_native_default_max_distance
    _ctf_native_native_aim = bool(state.get("native_aim_enabled", False))
    _ctf_native_aim_fov_px = float(state.get("aim_fov_px", 0.0))
    _ctf_native_visible_only = bool(state.get("visible_only", True))
    _ctf_native_hitbox_enabled = bool(state.get("hitbox_enabled", True))
    _ctf_native_hitbox_scale = float(state.get("hitbox_scale", _ctf_native_default_hitbox_scale))
    _ctf_native_magic_hitbox_range = float(
        state.get("magic_hitbox_range", _ctf_native_default_magic_hitbox_range)
    )
    try:
        with open(_ctf_native_config_path, "r", encoding="ascii") as _ctf_native_handle:
            for _ctf_native_line in _ctf_native_handle:
                _ctf_native_key, _ctf_native_separator, _ctf_native_raw = _ctf_native_line.partition("=")
                if not _ctf_native_separator:
                    continue
                _ctf_native_raw = _ctf_native_raw.strip()
                try:
                    if _ctf_native_key == "max_distance":
                        _ctf_native_candidate = float(_ctf_native_raw)
                        if _ctf_native_math.isfinite(_ctf_native_candidate):
                            _ctf_native_value = _ctf_native_candidate
                    elif _ctf_native_key == "native_aim":
                        _ctf_native_native_aim = _ctf_native_raw not in ("0", "false", "False")
                    elif _ctf_native_key == "aim_fov_px":
                        _ctf_native_candidate = float(_ctf_native_raw)
                        if _ctf_native_math.isfinite(_ctf_native_candidate):
                            _ctf_native_aim_fov_px = _ctf_native_candidate
                    elif _ctf_native_key == "visible_only":
                        _ctf_native_visible_only = _ctf_native_raw not in ("0", "false", "False")
                    elif _ctf_native_key == "hitbox":
                        _ctf_native_hitbox_enabled = _ctf_native_raw not in ("0", "false", "False")
                    elif _ctf_native_key == "hitbox_scale":
                        _ctf_native_candidate = float(_ctf_native_raw)
                        if _ctf_native_math.isfinite(_ctf_native_candidate):
                            _ctf_native_hitbox_scale = _ctf_native_candidate
                    elif _ctf_native_key in ("hitbox_range", "magic_hitbox_range"):
                        _ctf_native_candidate = float(_ctf_native_raw)
                        if _ctf_native_math.isfinite(_ctf_native_candidate):
                            _ctf_native_magic_hitbox_range = _ctf_native_candidate
                except Exception:
                    pass
    except Exception:
        pass

    state["max_target_distance"] = max(25.0, min(_ctf_native_hard_max_distance, _ctf_native_value))
    state["native_aim_enabled"] = _ctf_native_native_aim
    state["aim_fov_px"] = max(0.0, min(1000.0, _ctf_native_aim_fov_px))
    state["visible_only"] = _ctf_native_visible_only
    state["hitbox_enabled"] = _ctf_native_hitbox_enabled
    state["hitbox_scale"] = max(1.0, min(_ctf_native_max_hitbox_scale, _ctf_native_hitbox_scale))
    state["magic_hitbox_range"] = max(
        25.0,
        min(_ctf_native_hard_magic_hitbox_range, _ctf_native_magic_hitbox_range),
    )
    return state["max_target_distance"]


def _ctf_native_key_down(vk_code):
    global _ctf_native_user32
    try:
        if _ctf_native_user32 is None:
            import ctypes as _ctf_native_ctypes
            _ctf_native_user32 = _ctf_native_ctypes.windll.user32
        return bool(_ctf_native_user32.GetAsyncKeyState(vk_code) & 0x8000)
    except Exception:
        return False


def _ctf_native_rmb_down():
    return _ctf_native_key_down(_ctf_native_vk_rbutton)


def _ctf_native_external_aim_down(state):
    try:
        with open(_ctf_native_aim_trigger_path, "r", encoding="ascii") as _ctf_native_handle:
            _ctf_native_value = _ctf_native_handle.read(1)
        _ctf_native_down = _ctf_native_value == "1"
        state["native_aim_external_down"] = int(_ctf_native_down)
        return _ctf_native_down
    except Exception:
        state["native_aim_external_down"] = 0
        return False


def _ctf_native_wrap_angle_delta(source, target):
    _ctf_native_delta = (target - source + _ctf_native_math.pi) % (_ctf_native_math.pi * 2.0)
    return _ctf_native_delta - _ctf_native_math.pi


def _ctf_native_cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _ctf_native_dot(left, right):
    return left[0] * right[0] + left[1] * right[1] + left[2] * right[2]


def _ctf_native_project_point(frame, camera_pos, screen, point):
    try:
        _ctf_native_yaw = float(frame.Yaw)
        _ctf_native_pitch = float(frame.Pitch)
        _ctf_native_roll = float(frame.Roll)
        _ctf_native_fov = max(1.0, min(150.0, float(frame.Fov)))
        _ctf_native_width = float(screen.x)
        _ctf_native_height = float(screen.y)
    except Exception:
        return None
    if _ctf_native_width <= 1.0 or _ctf_native_height <= 1.0:
        return None

    _ctf_native_cos_pitch = _ctf_native_math.cos(_ctf_native_pitch)
    _ctf_native_forward = (
        -_ctf_native_math.sin(_ctf_native_yaw) * _ctf_native_cos_pitch,
        _ctf_native_math.sin(_ctf_native_pitch),
        -_ctf_native_math.cos(_ctf_native_yaw) * _ctf_native_cos_pitch,
    )
    _ctf_native_base_right = (
        _ctf_native_math.cos(_ctf_native_yaw),
        0.0,
        -_ctf_native_math.sin(_ctf_native_yaw),
    )
    _ctf_native_base_up = _ctf_native_cross(_ctf_native_base_right, _ctf_native_forward)
    _ctf_native_cos_roll = _ctf_native_math.cos(_ctf_native_roll)
    _ctf_native_sin_roll = _ctf_native_math.sin(_ctf_native_roll)
    _ctf_native_right = (
        _ctf_native_base_right[0] * _ctf_native_cos_roll + _ctf_native_base_up[0] * _ctf_native_sin_roll,
        _ctf_native_base_right[1] * _ctf_native_cos_roll + _ctf_native_base_up[1] * _ctf_native_sin_roll,
        _ctf_native_base_right[2] * _ctf_native_cos_roll + _ctf_native_base_up[2] * _ctf_native_sin_roll,
    )
    _ctf_native_up = (
        _ctf_native_base_up[0] * _ctf_native_cos_roll - _ctf_native_base_right[0] * _ctf_native_sin_roll,
        _ctf_native_base_up[1] * _ctf_native_cos_roll - _ctf_native_base_right[1] * _ctf_native_sin_roll,
        _ctf_native_base_up[2] * _ctf_native_cos_roll - _ctf_native_base_right[2] * _ctf_native_sin_roll,
    )
    _ctf_native_relative = (
        point[0] - camera_pos[0],
        point[1] - camera_pos[1],
        point[2] - camera_pos[2],
    )
    _ctf_native_depth = _ctf_native_dot(_ctf_native_relative, _ctf_native_forward)
    if _ctf_native_depth <= 0.08:
        return None

    _ctf_native_fov_radians = _ctf_native_fov * _ctf_native_math.pi / 180.0
    _ctf_native_focal_y = _ctf_native_height / (2.0 * _ctf_native_math.tan(_ctf_native_fov_radians * 0.5))
    _ctf_native_x = _ctf_native_width * 0.5 + _ctf_native_dot(_ctf_native_relative, _ctf_native_right) * _ctf_native_focal_y / _ctf_native_depth
    _ctf_native_y = _ctf_native_height * 0.5 - _ctf_native_dot(_ctf_native_relative, _ctf_native_up) * _ctf_native_focal_y / _ctf_native_depth
    if not (_ctf_native_math.isfinite(_ctf_native_x) and _ctf_native_math.isfinite(_ctf_native_y)):
        return None
    return _ctf_native_x, _ctf_native_y


def _ctf_native_head_angles(frame, camera_pos, head):
    _ctf_native_vector = (
        head[0] - camera_pos[0],
        head[1] - camera_pos[1],
        head[2] - camera_pos[2],
    )
    _ctf_native_horizontal = _ctf_native_math.hypot(_ctf_native_vector[0], _ctf_native_vector[2])
    if _ctf_native_horizontal <= 0.001:
        return None
    _ctf_native_yaw = _ctf_native_math.atan2(-_ctf_native_vector[0], -_ctf_native_vector[2])
    _ctf_native_pitch = _ctf_native_math.atan2(_ctf_native_vector[1], _ctf_native_horizontal)
    if not (_ctf_native_math.isfinite(_ctf_native_yaw) and _ctf_native_math.isfinite(_ctf_native_pitch)):
        return None
    return _ctf_native_yaw, max(-1.55, min(1.55, _ctf_native_pitch))


def _ctf_native_find_native_aim_target(state, frame, camera_pos, screen, rows):
    try:
        _ctf_native_width = float(screen.x)
        _ctf_native_height = float(screen.y)
    except Exception:
        return None
    _ctf_native_radius = float(state.get("aim_fov_px", 0.0))
    if _ctf_native_radius <= 1.0:
        _ctf_native_radius = max(78.0, _ctf_native_height * 0.20)
    _ctf_native_center_x = _ctf_native_width * 0.5
    _ctf_native_center_y = _ctf_native_height * 0.5
    _ctf_native_locked_key = state.get("native_aim_lock_key")
    _ctf_native_best = None

    for _ctf_native_row in rows:
        (
            _ctf_native_key,
            _ctf_native_pos,
            _ctf_native_low,
            _ctf_native_high,
            _ctf_native_hp,
            _ctf_native_maxhp,
            _ctf_native_armor,
            _ctf_native_maxarmor,
            _ctf_native_dead,
            _ctf_native_head,
            _ctf_native_is_visible,
            _ctf_native_is_robot,
            _ctf_native_relation,
        ) = _ctf_native_row
        if _ctf_native_dead or _ctf_native_head is None:
            continue
        if _ctf_native_relation != 2:
            continue
        if not _ctf_native_is_visible:
            continue
        _ctf_native_projected = _ctf_native_project_point(frame, camera_pos, screen, _ctf_native_head)
        if _ctf_native_projected is None:
            continue
        _ctf_native_dx = _ctf_native_projected[0] - _ctf_native_center_x
        _ctf_native_dy = _ctf_native_projected[1] - _ctf_native_center_y
        _ctf_native_distance = _ctf_native_math.hypot(_ctf_native_dx, _ctf_native_dy)
        _ctf_native_limit = _ctf_native_radius * (1.45 if _ctf_native_key == _ctf_native_locked_key else 1.0)
        if _ctf_native_distance > _ctf_native_limit:
            continue
        _ctf_native_angles = _ctf_native_head_angles(frame, camera_pos, _ctf_native_head)
        if _ctf_native_angles is None:
            continue
        _ctf_native_candidate = (_ctf_native_distance, _ctf_native_key, _ctf_native_head, _ctf_native_angles)
        if _ctf_native_key == _ctf_native_locked_key:
            return _ctf_native_candidate
        if _ctf_native_best is None or _ctf_native_distance < _ctf_native_best[0]:
            _ctf_native_best = _ctf_native_candidate
    return _ctf_native_best


def _ctf_native_apply_native_aim(state, camera, frame, camera_pos, screen, rows):
    if not state.get("native_aim_enabled", True):
        state["native_aim_lock_key"] = None
        return frame
    _ctf_native_trigger_down = _ctf_native_rmb_down() or _ctf_native_external_aim_down(state)
    state["native_aim_trigger_down"] = int(_ctf_native_trigger_down)
    if not _ctf_native_trigger_down:
        state["native_aim_lock_key"] = None
        return frame
    state["native_aim_trigger_seen"] = state.get("native_aim_trigger_seen", 0) + 1

    _ctf_native_target = _ctf_native_find_native_aim_target(
        state, frame, camera_pos, screen, rows
    )
    if _ctf_native_target is None:
        state["native_aim_lock_key"] = None
        state["native_aim_candidate_miss"] = state.get("native_aim_candidate_miss", 0) + 1
        return frame

    _ctf_native_yaw, _ctf_native_pitch = _ctf_native_target[3]
    try:
        _ctf_native_apply_frame = camera.CaptureFrame()
        _ctf_native_apply_frame.Yaw = _ctf_native_yaw
        _ctf_native_apply_frame.Pitch = _ctf_native_pitch
        try:
            _ctf_native_apply_frame.Roll = 0.0
        except Exception:
            pass
        for _ctf_native_attr, _ctf_native_value in (("InterpolateMode", 0), ("Time", 0.0)):
            try:
                setattr(_ctf_native_apply_frame, _ctf_native_attr, _ctf_native_value)
            except Exception:
                pass
        camera.ApplyFrame(_ctf_native_apply_frame)
        state["native_aim_lock_key"] = _ctf_native_target[1]
        state["native_aim_applied"] = state.get("native_aim_applied", 0) + 1
        return camera.CaptureFrame()
    except Exception as _ctf_native_exc:
        _ctf_native_error = repr(_ctf_native_exc)[:160]
        if state.get("native_aim_last_error") != _ctf_native_error:
            state["native_aim_last_error"] = _ctf_native_error
            _ctf_native_log("NATIVE_AIM_EXC {}".format(_ctf_native_error))
        return frame


def _ctf_native_probe_apply_frame(state):
    try:
        import MCamera as _ctf_native_camera
        _ctf_native_frame = _ctf_native_camera.CaptureFrame()
        _ctf_native_camera.ApplyFrame(_ctf_native_frame)
        state["native_apply_frame_ok"] = True
        state["native_apply_frame_error"] = ""
    except Exception as _ctf_native_exc:
        state["native_apply_frame_ok"] = False
        state["native_apply_frame_error"] = repr(_ctf_native_exc)[:160]


def _ctf_native_bounds(entity):
    for _ctf_native_source in (getattr(entity, "model", None), entity):
        if _ctf_native_source is None:
            continue
        for _ctf_native_name in ("GetWorldBound", "GetPrimWorldBound", "GetSkeletonDynamicWorldBound"):
            _ctf_native_bound = _ctf_native_call(_ctf_native_source, _ctf_native_name)
            if _ctf_native_bound is None:
                continue
            _ctf_native_low = _ctf_native_vec3(getattr(_ctf_native_bound, "min", None))
            _ctf_native_high = _ctf_native_vec3(getattr(_ctf_native_bound, "max", None))
            if _ctf_native_low is None or _ctf_native_high is None:
                continue
            if _ctf_native_high[1] > _ctf_native_low[1]:
                return _ctf_native_low, _ctf_native_high
    return None, None


class _CtfNativeSyntheticBoneResult(object):
    pass


class _CtfNativeSyntheticShootResult(object):
    pass


def _ctf_native_length(vector):
    try:
        return _ctf_native_math.sqrt(_ctf_native_dot(vector, vector))
    except Exception:
        return 0.0


def _ctf_native_normalized(vector):
    _ctf_native_len = _ctf_native_length(vector)
    if _ctf_native_len <= 0.000001:
        return None
    return (
        vector[0] / _ctf_native_len,
        vector[1] / _ctf_native_len,
        vector[2] / _ctf_native_len,
    )


def _ctf_native_screen_xy(shoot_screen_pos):
    try:
        return float(shoot_screen_pos[0]), float(shoot_screen_pos[1])
    except Exception:
        pass
    try:
        return float(shoot_screen_pos.x), float(shoot_screen_pos.y)
    except Exception:
        pass
    try:
        import MUI as _ctf_native_ui
        _ctf_native_screen = _ctf_native_ui.GetScreenSize()
        return float(_ctf_native_screen.x) * 0.5, float(_ctf_native_screen.y) * 0.5
    except Exception:
        return 0.0, 0.0


def _ctf_native_shoot_ray(caster, shoot_range, shoot_screen_pos, shoot_dir, start_pos):
    try:
        import MEngine as _ctf_native_engine
        import MType as _ctf_native_mtype

        _ctf_native_camera = _ctf_native_engine.GetGameplay().Player.Camera
        if shoot_dir is None:
            _ctf_native_x, _ctf_native_y = _ctf_native_screen_xy(shoot_screen_pos)
            shoot_dir = _ctf_native_camera.GetRayDirectionFromScreenPoint(
                int(_ctf_native_x), int(_ctf_native_y)
            )
        if start_pos is None:
            _ctf_native_origin = _ctf_native_camera.GetOrigin()
            try:
                _ctf_native_diff = _ctf_native_origin - _ctf_native_mtype.Vector3(*caster.position)
                _ctf_native_diff.y = 0
                start_pos = _ctf_native_origin + shoot_dir * (_ctf_native_diff.length * 0.8)
            except Exception:
                start_pos = _ctf_native_origin
        return start_pos, shoot_dir, float(shoot_range) + 0.5
    except Exception:
        return start_pos, shoot_dir, float(shoot_range or 0.0)


def _ctf_native_far_hitbox_padding(start, low, high, scale):
    try:
        _ctf_native_center = (
            (float(low[0]) + float(high[0])) * 0.5,
            (float(low[1]) + float(high[1])) * 0.5,
            (float(low[2]) + float(high[2])) * 0.5,
        )
        _ctf_native_distance_to_target = _ctf_native_distance(start, _ctf_native_center)
        if _ctf_native_distance_to_target is None or _ctf_native_distance_to_target <= 350.0:
            return 0.0
        _ctf_native_scale_factor = max(0.75, min(1.75, float(scale) / 3.4))
        return min(12.0, (_ctf_native_distance_to_target - 350.0) * 0.004 * _ctf_native_scale_factor)
    except Exception:
        return 0.0


def _ctf_native_expanded_bounds(low, high, scale, extra_padding=0.0):
    try:
        _ctf_native_scale = max(1.0, min(_ctf_native_max_hitbox_scale, float(scale)))
        _ctf_native_extra = max(0.0, min(12.0, float(extra_padding)))
        _ctf_native_min = (
            min(float(low[0]), float(high[0])),
            min(float(low[1]), float(high[1])),
            min(float(low[2]), float(high[2])),
        )
        _ctf_native_max = (
            max(float(low[0]), float(high[0])),
            max(float(low[1]), float(high[1])),
            max(float(low[2]), float(high[2])),
        )
        _ctf_native_center = (
            (_ctf_native_min[0] + _ctf_native_max[0]) * 0.5,
            (_ctf_native_min[1] + _ctf_native_max[1]) * 0.5,
            (_ctf_native_min[2] + _ctf_native_max[2]) * 0.5,
        )
        _ctf_native_half = (
            max(0.85, (_ctf_native_max[0] - _ctf_native_min[0]) * 0.5 * _ctf_native_scale + _ctf_native_extra),
            max(1.05, (_ctf_native_max[1] - _ctf_native_min[1]) * 0.5 * _ctf_native_scale + _ctf_native_extra),
            max(0.85, (_ctf_native_max[2] - _ctf_native_min[2]) * 0.5 * _ctf_native_scale + _ctf_native_extra),
        )
        return (
            (
                _ctf_native_center[0] - _ctf_native_half[0],
                _ctf_native_center[1] - _ctf_native_half[1],
                _ctf_native_center[2] - _ctf_native_half[2],
            ),
            (
                _ctf_native_center[0] + _ctf_native_half[0],
                _ctf_native_center[1] + _ctf_native_half[1],
                _ctf_native_center[2] + _ctf_native_half[2],
            ),
        )
    except Exception:
        return low, high


def _ctf_native_ray_aabb_hit(start, direction, low, high, max_distance):
    _ctf_native_tmin = 0.0
    _ctf_native_tmax = float(max_distance)
    for _ctf_native_index in range(3):
        _ctf_native_origin = start[_ctf_native_index]
        _ctf_native_dir = direction[_ctf_native_index]
        _ctf_native_low = low[_ctf_native_index]
        _ctf_native_high = high[_ctf_native_index]
        if abs(_ctf_native_dir) < 0.000001:
            if _ctf_native_origin < _ctf_native_low or _ctf_native_origin > _ctf_native_high:
                return None
            continue
        _ctf_native_a = (_ctf_native_low - _ctf_native_origin) / _ctf_native_dir
        _ctf_native_b = (_ctf_native_high - _ctf_native_origin) / _ctf_native_dir
        if _ctf_native_a > _ctf_native_b:
            _ctf_native_a, _ctf_native_b = _ctf_native_b, _ctf_native_a
        _ctf_native_tmin = max(_ctf_native_tmin, _ctf_native_a)
        _ctf_native_tmax = min(_ctf_native_tmax, _ctf_native_b)
        if _ctf_native_tmax < _ctf_native_tmin:
            return None
    if _ctf_native_tmax < 0.0 or _ctf_native_tmin > float(max_distance):
        return None
    _ctf_native_t = max(0.0, _ctf_native_tmin)
    return (
        _ctf_native_t,
        (
            start[0] + direction[0] * _ctf_native_t,
            start[1] + direction[1] * _ctf_native_t,
            start[2] + direction[2] * _ctf_native_t,
        ),
    )


def _ctf_native_ray_point_near_hit(start, direction, point, max_distance, radius):
    try:
        _ctf_native_to_point = (
            float(point[0]) - float(start[0]),
            float(point[1]) - float(start[1]),
            float(point[2]) - float(start[2]),
        )
        _ctf_native_t = _ctf_native_dot(_ctf_native_to_point, direction)
        if _ctf_native_t < 0.0 or _ctf_native_t > float(max_distance):
            return None
        _ctf_native_closest = (
            float(start[0]) + float(direction[0]) * _ctf_native_t,
            float(start[1]) + float(direction[1]) * _ctf_native_t,
            float(start[2]) + float(direction[2]) * _ctf_native_t,
        )
        _ctf_native_distance_to_ray = _ctf_native_distance(_ctf_native_closest, point)
        if _ctf_native_distance_to_ray is None or _ctf_native_distance_to_ray > float(radius):
            return None
        return _ctf_native_t, _ctf_native_closest, _ctf_native_distance_to_ray
    except Exception:
        return None


def _ctf_native_magic_near_points(target, low, high):
    _ctf_native_points = []
    try:
        _ctf_native_center = (
            (float(low[0]) + float(high[0])) * 0.5,
            (float(low[1]) + float(high[1])) * 0.5,
            (float(low[2]) + float(high[2])) * 0.5,
        )
        _ctf_native_height = max(0.1, float(high[1]) - float(low[1]))
        _ctf_native_points.extend((
            _ctf_native_center,
            (_ctf_native_center[0], float(low[1]) + _ctf_native_height * 0.72, _ctf_native_center[2]),
            (_ctf_native_center[0], float(low[1]) + _ctf_native_height * 0.88, _ctf_native_center[2]),
            (_ctf_native_center[0], float(low[1]) + _ctf_native_height * 0.34, _ctf_native_center[2]),
        ))
    except Exception:
        pass
    _ctf_native_model = getattr(target, "model", None)
    if _ctf_native_model is not None:
        _ctf_native_call(_ctf_native_model, "MakeSureBones")
        for _ctf_native_bone in _ctf_native_aim_bones:
            _ctf_native_point = _ctf_native_vec3(
                _ctf_native_call(_ctf_native_model, "GetBoneWorldPosition", _ctf_native_bone)
            )
            if _ctf_native_point is None:
                continue
            if not all(_ctf_native_math.isfinite(_ctf_native_value) for _ctf_native_value in _ctf_native_point):
                continue
            if _ctf_native_point_in_bounds(_ctf_native_point, low, high, padding=0.75):
                _ctf_native_points.append(_ctf_native_point)
    return _ctf_native_points


def _ctf_native_magic_near_radius(low, high, scale, extra_padding=0.0):
    try:
        _ctf_native_scale = max(1.0, min(_ctf_native_max_hitbox_scale, float(scale)))
        _ctf_native_extra = max(0.0, min(12.0, float(extra_padding)))
        _ctf_native_width = max(
            abs(float(high[0]) - float(low[0])),
            abs(float(high[2]) - float(low[2])),
        )
        return max(0.75, min(16.0, _ctf_native_width * 0.45 * _ctf_native_scale + 0.34 * _ctf_native_scale + _ctf_native_extra))
    except Exception:
        return max(0.75, min(16.0, float(scale) * 0.5))


def _ctf_native_magic_ray_hit(state, target, start, direction, low, high, expanded_low, expanded_high, max_distance, scale, extra_padding=0.0):
    _ctf_native_hit = _ctf_native_ray_aabb_hit(
        start,
        direction,
        expanded_low,
        expanded_high,
        max_distance,
    )
    if _ctf_native_hit is not None:
        return _ctf_native_hit[0], _ctf_native_hit[1], "box"

    _ctf_native_radius = _ctf_native_magic_near_radius(low, high, scale, extra_padding)
    _ctf_native_best = None
    for _ctf_native_point in _ctf_native_magic_near_points(target, low, high):
        _ctf_native_near = _ctf_native_ray_point_near_hit(
            start,
            direction,
            _ctf_native_point,
            max_distance,
            _ctf_native_radius,
        )
        if _ctf_native_near is None:
            continue
        if _ctf_native_best is None or _ctf_native_near[0] < _ctf_native_best[0]:
            _ctf_native_best = _ctf_native_near
    if _ctf_native_best is not None:
        state["magic_hitbox_near_hits"] = state.get("magic_hitbox_near_hits", 0) + 1
        return _ctf_native_best[0], _ctf_native_best[1], "near"
    return None


def _ctf_native_magic_hit_part(hit_point, low, high):
    try:
        _ctf_native_height = max(0.001, float(high[1]) - float(low[1]))
        _ctf_native_ratio = (float(hit_point[1]) - float(low[1])) / _ctf_native_height
        if _ctf_native_ratio > 0.82:
            return "Head"
        if _ctf_native_ratio > 0.38:
            return "UpperTop"
        return "Limbs_L_Thigh"
    except Exception:
        return "UpperTop"


def _ctf_native_magic_bone_candidates(part):
    if part == "Head":
        return (
            ("biped Head", "Head"),
            ("biped Neck", "UpperTop"),
            ("biped Spine2", "UpperTop"),
        )
    if part == "UpperTop":
        return (
            ("biped Spine2", "UpperTop"),
            ("biped Spine1", "UpperTop"),
            ("biped Neck", "UpperTop"),
            ("biped Spine", "UpperTop"),
        )
    return (
        ("biped L Thigh", "Limbs_L_Thigh"),
        ("biped R Thigh", "Limbs_R_Thigh"),
        ("biped L Calf", "Limbs_L_Calf"),
        ("biped R Calf", "Limbs_R_Calf"),
        ("biped Pelvis", "UpperTop"),
    )


def _ctf_native_clamped_bounds_point(point, low, high):
    try:
        return (
            min(max(float(point[0]), float(low[0])), float(high[0])),
            min(max(float(point[1]), float(low[1])), float(high[1])),
            min(max(float(point[2]), float(low[2])), float(high[2])),
        )
    except Exception:
        return point


def _ctf_native_magic_damage_point(target, hit_point, low, high):
    _ctf_native_part = _ctf_native_magic_hit_part(hit_point, low, high)
    _ctf_native_model = getattr(target, "model", None)
    if _ctf_native_model is not None:
        _ctf_native_ensure_aim_bones(
            getattr(_ctf_native_builtins, _ctf_native_state_name, {}),
            "magic_payload_{}".format(id(target)),
            _ctf_native_model,
        )
        _ctf_native_call(_ctf_native_model, "MakeSureBones")
        for _ctf_native_bone, _ctf_native_name in _ctf_native_magic_bone_candidates(_ctf_native_part):
            _ctf_native_pos = _ctf_native_vec3(
                _ctf_native_call(_ctf_native_model, "GetBoneWorldPosition", _ctf_native_bone)
            )
            if _ctf_native_pos is None:
                continue
            if not all(_ctf_native_math.isfinite(_ctf_native_value) for _ctf_native_value in _ctf_native_pos):
                continue
            if not _ctf_native_point_in_bounds(_ctf_native_pos, low, high, padding=0.35):
                continue
            return _ctf_native_pos, _ctf_native_name
    return _ctf_native_clamped_bounds_point(hit_point, low, high), _ctf_native_part


def _ctf_native_direction_object(start_obj, point):
    _ctf_native_start = _ctf_native_vec3(start_obj)
    if _ctf_native_start is None or point is None:
        return None
    _ctf_native_dir = _ctf_native_normalized((
        float(point[0]) - _ctf_native_start[0],
        float(point[1]) - _ctf_native_start[1],
        float(point[2]) - _ctf_native_start[2],
    ))
    if _ctf_native_dir is None:
        return None
    return _ctf_native_make_vec3_like(start_obj, _ctf_native_dir)


def _ctf_native_points_close(left, right, threshold=0.35):
    _ctf_native_left = _ctf_native_vec3(left)
    _ctf_native_right = _ctf_native_vec3(right)
    if _ctf_native_left is None or _ctf_native_right is None:
        return False
    return _ctf_native_distance(_ctf_native_left, _ctf_native_right) <= threshold


def _ctf_native_setattr(obj, name, value):
    try:
        setattr(obj, name, value)
        return True
    except Exception:
        return False


def _ctf_native_identity_tokens(entity):
    _ctf_native_tokens = set()
    if entity is None:
        return _ctf_native_tokens
    _ctf_native_tokens.add("id:{}".format(id(entity)))
    for _ctf_native_name in (
        "id", "guid", "key", "entity_id", "entityId", "player_id", "playerId",
        "player_guid", "combat_avatar_id", "avatar_id", "ownerid", "role_id",
    ):
        try:
            _ctf_native_value = getattr(entity, _ctf_native_name)
            if callable(_ctf_native_value):
                _ctf_native_value = _ctf_native_value()
            if isinstance(_ctf_native_value, (str, int, float)) and not isinstance(_ctf_native_value, bool):
                _ctf_native_tokens.add("{}:{}".format(_ctf_native_name, _ctf_native_value))
        except Exception:
            pass
    try:
        _ctf_native_name_value = _ctf_native_call(entity, "GetName")
        if isinstance(_ctf_native_name_value, str) and _ctf_native_name_value:
            _ctf_native_tokens.add("name:{}".format(_ctf_native_name_value))
    except Exception:
        pass
    return _ctf_native_tokens


def _ctf_native_targets_match(left, right):
    if left is right:
        return True
    if left is None or right is None:
        return False
    try:
        return bool(_ctf_native_identity_tokens(left) & _ctf_native_identity_tokens(right))
    except Exception:
        return False


def _ctf_native_collision_owner(hit):
    try:
        _ctf_native_body = getattr(hit, "Body", None)
        _ctf_native_parent = getattr(_ctf_native_body, "Parent", None)
        _ctf_native_owner = getattr(_ctf_native_parent, "owner", None)
        if _ctf_native_owner is not None:
            return _ctf_native_owner
    except Exception:
        pass
    return None


def _ctf_native_collision_matches_target(hit, target, skeleton):
    try:
        if getattr(hit, "actor", None) == skeleton:
            return True
    except Exception:
        pass
    return _ctf_native_targets_match(_ctf_native_collision_owner(hit), target)


def _ctf_native_magic_bone_result(state, key, target, start_obj, hit_pos_obj, hit_part, hit_normal_obj, material):
    _ctf_native_model = getattr(target, "model", None)
    _ctf_native_skeleton = _ctf_native_call(_ctf_native_model, "GetSkeleton")
    _ctf_native_space = _ctf_native_active_space(state)
    _ctf_native_candidates = []
    if _ctf_native_space is not None:
        _ctf_native_hits = _ctf_native_call(_ctf_native_space, "RaycastBoneWithPenetrate", start_obj, hit_pos_obj)
        if isinstance(_ctf_native_hits, (list, tuple)):
            _ctf_native_candidates.extend(_ctf_native_hits)
        else:
            _ctf_native_hit = _ctf_native_call(_ctf_native_space, "ClosestRaycastBone", start_obj, hit_pos_obj)
            if _ctf_native_hit is not None:
                _ctf_native_candidates.append(_ctf_native_hit)
    for _ctf_native_hit in _ctf_native_candidates:
        if not getattr(_ctf_native_hit, "IsHit", False):
            continue
        if not _ctf_native_collision_matches_target(_ctf_native_hit, target, _ctf_native_skeleton):
            continue
        _ctf_native_patch_bone_result(_ctf_native_hit, target, _ctf_native_skeleton, hit_pos_obj, hit_part, hit_normal_obj, material)
        state["magic_hitbox_real_bone_results"] = state.get("magic_hitbox_real_bone_results", 0) + 1
        return _ctf_native_hit
    _ctf_native_hit = _CtfNativeSyntheticBoneResult()
    _ctf_native_patch_bone_result(_ctf_native_hit, target, _ctf_native_skeleton, hit_pos_obj, hit_part, hit_normal_obj, material)
    return _ctf_native_hit


def _ctf_native_patch_bone_result(hit, target, skeleton, hit_pos_obj, hit_part, hit_normal_obj, material):
    _ctf_native_setattr(hit, "IsHit", True)
    if skeleton is not None and getattr(hit, "Body", None) is None:
        _ctf_native_setattr(hit, "Body", skeleton)
    if skeleton is not None:
        _ctf_native_setattr(hit, "actor", skeleton)
    _ctf_native_setattr(hit, "owner", target)
    _ctf_native_setattr(hit, "target", target)
    _ctf_native_setattr(hit, "name", hit_part)
    _ctf_native_setattr(hit, "hit_name", hit_part)
    _ctf_native_setattr(hit, "Pos", hit_pos_obj)
    _ctf_native_setattr(hit, "HitPos", hit_pos_obj)
    _ctf_native_setattr(hit, "Normal", hit_normal_obj)
    _ctf_native_setattr(hit, "MaterialTypeId", material)
    _ctf_native_setattr(hit, "materialTypeId", material)
    _ctf_native_setattr(hit, "can_penerate", False)
    _ctf_native_setattr(hit, "raycastDir", True)


def _ctf_native_material_id():
    try:
        from gclient import cconst as _ctf_native_cconst
        _ctf_native_ids = getattr(_ctf_native_cconst, "COMBAT_UNIT_MATERIAL_IDS", None)
        if _ctf_native_ids and 1001 in _ctf_native_ids:
            return 1001
        if _ctf_native_ids:
            return list(_ctf_native_ids)[0]
    except Exception:
        pass
    return 1001


def _ctf_native_collision_info():
    try:
        from gclient import cconst as _ctf_native_cconst
        return getattr(_ctf_native_cconst, "PHYSICS_CHARCTRL", 30)
    except Exception:
        return 30


def _ctf_native_install_damage_payload_patch(state, caster):
    try:
        _ctf_native_game_logic = getattr(caster, "game_logic", None)
        if _ctf_native_game_logic is None:
            return
        _ctf_native_cls = _ctf_native_game_logic.__class__
        _ctf_native_patch_revision = 2
        if getattr(_ctf_native_cls, "_ctf_native_damage_patch_revision", 0) == _ctf_native_patch_revision:
            state["magic_hitbox_damage_patch_installed"] = True
            return
        if not hasattr(_ctf_native_cls, "_ctf_native_original_DealWeaponDamageResult"):
            _ctf_native_cls._ctf_native_original_DealWeaponDamageResult = _ctf_native_cls.DealWeaponDamageResult

        def _ctf_native_wrapped_deal_weapon_damage_result(self, *args, **kwargs):
            _ctf_native_live_state = getattr(_ctf_native_builtins, _ctf_native_state_name, state)
            _ctf_native_payload = _ctf_native_live_state.get("magic_hitbox_last_payload")
            if _ctf_native_payload and _ctf_native_time.time() - _ctf_native_payload.get("time", 0.0) < 0.35:
                try:
                    _ctf_native_spell_result = args[1] if len(args) > 1 else None
                    _ctf_native_target = args[3] if len(args) > 3 else None
                    _ctf_native_hit_pos = kwargs.get("hit_pos")
                    if (
                        _ctf_native_targets_match(_ctf_native_target, _ctf_native_payload.get("target")) and
                        (
                            _ctf_native_hit_pos is None or
                            _ctf_native_points_close(_ctf_native_hit_pos, _ctf_native_payload.get("hit_pos_obj"), 0.85)
                        )
                    ):
                        _ctf_native_corrected_dir = _ctf_native_payload.get("shoot_dir_obj")
                        if _ctf_native_corrected_dir is not None:
                            kwargs["hit_pos"] = _ctf_native_payload.get("hit_pos_obj")
                            kwargs["hit_part"] = _ctf_native_payload.get("hit_part", kwargs.get("hit_part"))
                            kwargs["hit_dir"] = _ctf_native_corrected_dir
                            if "hit_back" in kwargs:
                                kwargs["hit_back"] = _ctf_native_payload.get("hit_back", kwargs.get("hit_back"))
                            if "hit_penetrate" in kwargs:
                                kwargs["hit_penetrate"] = False
                            if "penetrate_materials" in kwargs:
                                kwargs["penetrate_materials"] = [_ctf_native_payload.get("material", 1001)]
                            if "penetrate_power" in kwargs and not kwargs.get("penetrate_power"):
                                kwargs["penetrate_power"] = _ctf_native_payload.get("penetrate_power", 1000)
                            if _ctf_native_spell_result is not None:
                                try:
                                    _ctf_native_spell_result.verify_shoot_dir = _ctf_native_corrected_dir
                                except Exception:
                                    pass
                                try:
                                    _ctf_native_spell_result.verify_start_pos = _ctf_native_payload.get("start_pos_obj")
                                except Exception:
                                    pass
                                try:
                                    _ctf_native_spell_result.verify_camera_pos = _ctf_native_payload.get("start_pos_tuple")
                                except Exception:
                                    pass
                            _ctf_native_live_state["magic_hitbox_damage_dir_patches"] = (
                                _ctf_native_live_state.get("magic_hitbox_damage_dir_patches", 0) + 1
                            )
                except Exception:
                    _ctf_native_live_state["magic_hitbox_damage_patch_errors"] = (
                        _ctf_native_live_state.get("magic_hitbox_damage_patch_errors", 0) + 1
                    )
            return _ctf_native_cls._ctf_native_original_DealWeaponDamageResult(self, *args, **kwargs)

        _ctf_native_cls.DealWeaponDamageResult = _ctf_native_wrapped_deal_weapon_damage_result
        _ctf_native_cls._ctf_native_damage_patch_revision = _ctf_native_patch_revision
        state["magic_hitbox_damage_patch_installed"] = True
        _ctf_native_log("MAGIC_HITBOX_DAMAGE_PATCH installed {}".format(_ctf_native_cls))
    except Exception:
        state["magic_hitbox_damage_patch_installed"] = False
        _ctf_native_log("MAGIC_HITBOX_DAMAGE_PATCH_EXC\n" + _ctf_native_traceback.format_exc())


def _ctf_native_current_weapon(caster):
    for _ctf_native_args in ((False,), ()):
        try:
            _ctf_native_weapon = caster.GetCurWeaponCase(*_ctf_native_args)
            if _ctf_native_weapon is not None:
                return _ctf_native_weapon
        except Exception:
            pass
    return _ctf_native_call(caster, "GetCurHighPriorityWeapon")


def _ctf_native_weapon_attr(weapon, name, default):
    try:
        _ctf_native_value = getattr(weapon, name)
        if callable(_ctf_native_value):
            _ctf_native_value = _ctf_native_value()
        if _ctf_native_value is not None:
            return _ctf_native_value
    except Exception:
        pass
    return default


def _ctf_native_new_spell_context(caster, start_obj, shoot_dir_obj):
    _ctf_native_worker = None
    _ctf_native_spell_result = None
    try:
        import gclient.gameplay.logic_base.spell.spell_core.gun_spell as _ctf_native_gun_spell
        _ctf_native_worker = _ctf_native_gun_spell.SpellWorker(caster)
        _ctf_native_spell_result = _ctf_native_worker.NewSpellResult()
    except Exception:
        _ctf_native_spell_result = _CtfNativeSyntheticShootResult()
    try:
        _ctf_native_spell_result.cost_ammo = False
    except Exception:
        pass
    try:
        _ctf_native_spell_result.verify_start_pos = start_obj
    except Exception:
        pass
    try:
        _ctf_native_spell_result.verify_shoot_dir = shoot_dir_obj
    except Exception:
        pass
    try:
        import MEngine as _ctf_native_engine
        _ctf_native_transform = _ctf_native_engine.GetGameplay().Player.Camera.Transform
        _ctf_native_spell_result.verify_camera_pos = _ctf_native_transform.translation.tuple()
    except Exception:
        try:
            _ctf_native_spell_result.verify_camera_pos = start_obj.tuple()
        except Exception:
            pass
    return _ctf_native_worker, _ctf_native_spell_result


def _ctf_native_send_spell_result(worker, spell_result):
    try:
        if worker is not None and getattr(spell_result, "damage_result", None):
            worker.WrapperSendSpellResult(spell_result, True)
            return True
    except Exception:
        pass
    return False


def _ctf_native_direct_player_damage(state, caster, target):
    _ctf_native_payload = state.get("magic_hitbox_last_payload")
    if not _ctf_native_payload:
        return False
    _ctf_native_game_logic = None
    _ctf_native_spell_id = 0
    _ctf_native_spell_result = None
    _ctf_native_worker = None
    _ctf_native_weapon_id = 0
    _ctf_native_weapon_guid = ""
    try:
        _ctf_native_game_logic = getattr(caster, "game_logic", None)
        if _ctf_native_game_logic is None:
            return False
        _ctf_native_weapon = _ctf_native_current_weapon(caster)
        _ctf_native_weapon_id = _ctf_native_weapon_attr(_ctf_native_weapon, "weapon_id", 0)
        _ctf_native_weapon_guid = _ctf_native_weapon_attr(_ctf_native_weapon, "weapon_guid", "")
        _ctf_native_worker, _ctf_native_spell_result = _ctf_native_new_spell_context(
            caster,
            _ctf_native_payload.get("start_pos_obj"),
            _ctf_native_payload.get("shoot_dir_obj"),
        )
        if _ctf_native_weapon_guid:
            try:
                _ctf_native_spell_result.weapon_guid = _ctf_native_weapon_guid
            except Exception:
                pass
        _ctf_native_spell_id = getattr(_ctf_native_worker, "spell_id", 0)
        _ctf_native_kwargs = {
            "hit_part": _ctf_native_payload.get("hit_part", "UpperTop"),
            "hit_dir": _ctf_native_payload.get("shoot_dir_obj"),
            "hit_back": False,
            "hit_pos": _ctf_native_payload.get("hit_pos_obj"),
            "hit_penetrate": False,
            "penetrate_power": _ctf_native_payload.get("penetrate_power", 1000),
            "penetrate_materials": [_ctf_native_payload.get("material", 1001)],
            "is_ads": not bool(getattr(caster, "is_real_ads", False)),
            "weapon_guid": _ctf_native_weapon_guid,
        }
        state["magic_hitbox_direct_player_damage_attempts"] = (
            state.get("magic_hitbox_direct_player_damage_attempts", 0) + 1
        )
        _ctf_native_game_logic.DealWeaponDamageResult(
            _ctf_native_spell_id,
            _ctf_native_spell_result,
            caster,
            target,
            _ctf_native_weapon_id,
            True,
            **_ctf_native_kwargs
        )
        _ctf_native_sent = _ctf_native_send_spell_result(_ctf_native_worker, _ctf_native_spell_result)
        _ctf_native_damage_result = getattr(_ctf_native_spell_result, "damage_result", None)
        if _ctf_native_damage_result:
            state["magic_hitbox_direct_player_damage_success"] = (
                state.get("magic_hitbox_direct_player_damage_success", 0) + 1
            )
            state["magic_hitbox_direct_player_damage_sent"] = (
                state.get("magic_hitbox_direct_player_damage_sent", 0) + int(_ctf_native_sent)
            )
            return True
        state["magic_hitbox_direct_player_damage_empty"] = (
            state.get("magic_hitbox_direct_player_damage_empty", 0) + 1
        )
    except TypeError:
        try:
            _ctf_native_game_logic.DealWeaponDamageResult(
                _ctf_native_spell_id,
                _ctf_native_spell_result,
                caster,
                target,
                _ctf_native_weapon_id,
                True,
                hit_dir=_ctf_native_payload.get("shoot_dir_obj"),
                penetrate_power=_ctf_native_payload.get("penetrate_power", 1000),
                penetrate_materials=[_ctf_native_payload.get("material", 1001)],
                hit_pos=_ctf_native_payload.get("hit_pos_obj"),
                weapon_guid=_ctf_native_weapon_guid,
            )
            _ctf_native_sent = _ctf_native_send_spell_result(_ctf_native_worker, _ctf_native_spell_result)
            if getattr(_ctf_native_spell_result, "damage_result", None):
                state["magic_hitbox_direct_player_damage_success"] = (
                    state.get("magic_hitbox_direct_player_damage_success", 0) + 1
                )
                state["magic_hitbox_direct_player_damage_sent"] = (
                    state.get("magic_hitbox_direct_player_damage_sent", 0) + int(_ctf_native_sent)
                )
                return True
        except Exception:
            state["magic_hitbox_direct_player_damage_errors"] = (
                state.get("magic_hitbox_direct_player_damage_errors", 0) + 1
            )
            state["magic_hitbox_direct_player_damage_last_error"] = _ctf_native_traceback.format_exc()[-500:]
    except Exception:
        state["magic_hitbox_direct_player_damage_errors"] = (
            state.get("magic_hitbox_direct_player_damage_errors", 0) + 1
        )
        state["magic_hitbox_direct_player_damage_last_error"] = _ctf_native_traceback.format_exc()[-500:]
    return False


def _ctf_native_magic_candidates(state, caster):
    _ctf_native_players, _ctf_native_robots = _ctf_native_entities()
    _ctf_native_local_key, _ctf_native_local_player_obj = _ctf_native_local_player(
        state, _ctf_native_players
    )
    _ctf_native_local_ref = caster if caster is not None else _ctf_native_local_player_obj
    _ctf_native_candidates = [
        (_ctf_native_key, _ctf_native_entity, False)
        for _ctf_native_key, _ctf_native_entity in _ctf_native_players
        if _ctf_native_key != _ctf_native_local_key and _ctf_native_entity is not caster
    ] + [
        (_ctf_native_key, _ctf_native_entity, True)
        for _ctf_native_key, _ctf_native_entity in _ctf_native_robots
        if _ctf_native_entity is not caster
    ]
    _ctf_native_range = state.get(
        "magic_hitbox_range",
        _ctf_native_default_magic_hitbox_range,
    )
    _ctf_native_range_sq = _ctf_native_range * _ctf_native_range
    _ctf_native_caster_pos = _ctf_native_position(_ctf_native_local_ref)

    for _ctf_native_key, _ctf_native_target, _ctf_native_is_robot in _ctf_native_candidates:
        try:
            if _ctf_native_call(_ctf_native_target, "is_destroyed"):
                continue
            if bool(getattr(_ctf_native_target, "is_dead_state", False) or getattr(_ctf_native_target, "dead", False)):
                continue
            _ctf_native_model = getattr(_ctf_native_target, "model", None)
            if _ctf_native_model is not None and hasattr(_ctf_native_model, "isValid"):
                if not _ctf_native_model.isValid():
                    continue
            _ctf_native_relation = _ctf_native_team_relation(
                _ctf_native_local_ref,
                _ctf_native_key,
                _ctf_native_target,
                _ctf_native_is_robot,
            )
            if _ctf_native_relation != 2:
                continue
            if _ctf_native_caster_pos is not None:
                _ctf_native_pos = _ctf_native_position(_ctf_native_target)
                if _ctf_native_pos is not None:
                    _ctf_native_dx = _ctf_native_pos[0] - _ctf_native_caster_pos[0]
                    _ctf_native_dy = _ctf_native_pos[1] - _ctf_native_caster_pos[1]
                    _ctf_native_dz = _ctf_native_pos[2] - _ctf_native_caster_pos[2]
                    if (
                        _ctf_native_dx * _ctf_native_dx +
                        _ctf_native_dy * _ctf_native_dy +
                        _ctf_native_dz * _ctf_native_dz
                    ) > _ctf_native_range_sq:
                        continue
            yield _ctf_native_key, _ctf_native_target, _ctf_native_is_robot
        except Exception:
            continue


def _ctf_native_iter_shoot_results(value):
    if value is None or isinstance(value, dict):
        return
    if isinstance(value, (list, tuple)):
        for _ctf_native_item in value:
            for _ctf_native_result in _ctf_native_iter_shoot_results(_ctf_native_item):
                yield _ctf_native_result
        return
    yield value


def _ctf_native_authoritative_recast(
    state,
    caster,
    target,
    shoot_range,
    shoot_screen_pos,
    corrected_dir,
    start_pos,
):
    """Re-run the engine raycast toward a real bone and keep its native result."""
    try:
        from gclient.gameplay.logic_base.spell.spell_core import spell_core_main as _ctf_native_spell_core_main

        _ctf_native_original = getattr(
            _ctf_native_spell_core_main,
            "_ctf_native_original_GetShootResult",
            None,
        )
        if _ctf_native_original is None:
            return None
        _ctf_native_raw = _ctf_native_original(
            caster,
            shoot_range,
            shoot_screen_pos,
            corrected_dir,
            start_pos,
        )
        for _ctf_native_result in _ctf_native_iter_shoot_results(_ctf_native_raw):
            if not _ctf_native_result_hits_combat(_ctf_native_result):
                continue
            if not _ctf_native_targets_match(getattr(_ctf_native_result, "target", None), target):
                continue
            state["magic_hitbox_authoritative_recasts"] = (
                state.get("magic_hitbox_authoritative_recasts", 0) + 1
            )
            return _ctf_native_result
    except Exception:
        state["magic_hitbox_authoritative_recast_errors"] = (
            state.get("magic_hitbox_authoritative_recast_errors", 0) + 1
        )
        state["magic_hitbox_authoritative_recast_last_error"] = (
            _ctf_native_traceback.format_exc()[-500:]
        )
    return None


def _ctf_native_make_magic_result(
    state,
    caster,
    shoot_range,
    shoot_screen_pos,
    shoot_dir,
    start_pos,
    penetrate_count,
    penetrate_power,
):
    if not state.get("hitbox_enabled", True):
        return None

    _ctf_native_start_obj, _ctf_native_dir_obj, _ctf_native_effective_range = _ctf_native_shoot_ray(
        caster, shoot_range, shoot_screen_pos, shoot_dir, start_pos
    )
    _ctf_native_start = _ctf_native_vec3(_ctf_native_start_obj)
    _ctf_native_dir_tuple = _ctf_native_vec3(_ctf_native_dir_obj)
    _ctf_native_dir = _ctf_native_normalized(_ctf_native_dir_tuple)
    if _ctf_native_start is None or _ctf_native_dir is None:
        state["magic_hitbox_bad_ray"] = state.get("magic_hitbox_bad_ray", 0) + 1
        return None
    try:
        _ctf_native_effective_range = max(
            float(_ctf_native_effective_range),
            float(state.get("magic_hitbox_range", _ctf_native_default_magic_hitbox_range)) + 2.0,
            _ctf_native_default_magic_hitbox_range + 2.0,
        )
    except Exception:
        _ctf_native_effective_range = _ctf_native_default_magic_hitbox_range + 2.0

    _ctf_native_best = None
    _ctf_native_scale = state.get("hitbox_scale", _ctf_native_default_hitbox_scale)
    for _ctf_native_key, _ctf_native_target, _ctf_native_is_robot in _ctf_native_magic_candidates(state, caster):
        _ctf_native_low, _ctf_native_high = _ctf_native_bounds(_ctf_native_target)
        if _ctf_native_low is None or _ctf_native_high is None:
            continue
        if state.get("visible_only", True) and not _ctf_native_visible(
            state, _ctf_native_key, _ctf_native_target, _ctf_native_start_obj
        ):
            continue
        _ctf_native_extra_padding = _ctf_native_far_hitbox_padding(
            _ctf_native_start,
            _ctf_native_low,
            _ctf_native_high,
            _ctf_native_scale,
        )
        _ctf_native_expanded_low, _ctf_native_expanded_high = _ctf_native_expanded_bounds(
            _ctf_native_low, _ctf_native_high, _ctf_native_scale, _ctf_native_extra_padding
        )
        _ctf_native_hit = _ctf_native_magic_ray_hit(
            state,
            _ctf_native_target,
            _ctf_native_start,
            _ctf_native_dir,
            _ctf_native_low,
            _ctf_native_high,
            _ctf_native_expanded_low,
            _ctf_native_expanded_high,
            _ctf_native_effective_range,
            _ctf_native_scale,
            _ctf_native_extra_padding,
        )
        if _ctf_native_hit is None:
            continue
        if _ctf_native_best is None or _ctf_native_hit[0] < _ctf_native_best[0]:
            _ctf_native_best = (
                _ctf_native_hit[0],
                _ctf_native_hit[1],
                _ctf_native_target,
                _ctf_native_low,
                _ctf_native_high,
                _ctf_native_key,
                _ctf_native_is_robot,
                _ctf_native_hit[2],
            )

    if _ctf_native_best is None:
        state["magic_hitbox_misses"] = state.get("magic_hitbox_misses", 0) + 1
        return None

    _ctf_native_intersect_point = _ctf_native_best[1]
    _ctf_native_target = _ctf_native_best[2]
    _ctf_native_low = _ctf_native_best[3]
    _ctf_native_high = _ctf_native_best[4]
    _ctf_native_hit_point, _ctf_native_hit_part = _ctf_native_magic_damage_point(
        _ctf_native_target,
        _ctf_native_intersect_point,
        _ctf_native_low,
        _ctf_native_high,
    )
    _ctf_native_hit_pos_obj = _ctf_native_make_vec3_like(_ctf_native_start_obj, _ctf_native_hit_point)
    if _ctf_native_hit_pos_obj is None:
        return None
    _ctf_native_payload_dir_obj = _ctf_native_direction_object(_ctf_native_start_obj, _ctf_native_hit_point)
    _ctf_native_payload_dir = _ctf_native_vec3(_ctf_native_payload_dir_obj) or _ctf_native_dir
    _ctf_native_normal_obj = _ctf_native_make_vec3_like(
        _ctf_native_start_obj,
        (-_ctf_native_payload_dir[0], -_ctf_native_payload_dir[1], -_ctf_native_payload_dir[2]),
    )
    if _ctf_native_normal_obj is None:
        _ctf_native_normal_obj = _ctf_native_hit_pos_obj

    _ctf_native_material = _ctf_native_material_id()
    _ctf_native_bone_res = _ctf_native_magic_bone_result(
        state,
        _ctf_native_best[5],
        _ctf_native_target,
        _ctf_native_start_obj,
        _ctf_native_hit_pos_obj,
        _ctf_native_hit_part,
        _ctf_native_normal_obj,
        _ctf_native_material,
    )

    try:
        from gclient.gameplay.logic_base.spell.spell_core import spell_core_main as _ctf_native_spell_core_main
        _ctf_native_result = _ctf_native_spell_core_main.BuildShootEntityResult(
            _ctf_native_bone_res,
            caster,
            _ctf_native_start_obj,
            _ctf_native_payload_dir_obj or _ctf_native_dir_obj,
            penetrate_count,
            penetrate_power,
        )
    except Exception:
        try:
            from gclient.gameplay.logic_base.spell.spell_core import spell_core_main as _ctf_native_spell_core_main
            _ctf_native_result = _ctf_native_spell_core_main.ShootEntityResult()
        except Exception:
            _ctf_native_result = _CtfNativeSyntheticShootResult()

    # Prefer the game's own collision object when it can be recast toward the
    # selected bone, but keep the synthetic result as a fallback for both player
    # and robot targets. Long-range player targets often fail the native recast
    # because the original weapon range is shorter than the magic hitbox range.
    _ctf_native_recast = _ctf_native_authoritative_recast(
        state,
        caster,
        _ctf_native_target,
        _ctf_native_effective_range,
        shoot_screen_pos,
        _ctf_native_payload_dir_obj or _ctf_native_dir_obj,
        _ctf_native_start_obj,
    )
    if _ctf_native_recast is not None:
        _ctf_native_result = _ctf_native_recast
        if not _ctf_native_best[6]:
            state["magic_hitbox_player_recasts"] = (
                state.get("magic_hitbox_player_recasts", 0) + 1
            )
        _ctf_native_recast_bone = getattr(_ctf_native_result, "raycast_bone_res", None)
        if _ctf_native_recast_bone is not None:
            _ctf_native_bone_res = _ctf_native_recast_bone
            _ctf_native_hit_part = getattr(_ctf_native_recast_bone, "name", _ctf_native_hit_part)
        _ctf_native_recast_pos = getattr(_ctf_native_result, "physics_hit_pos", None)
        if _ctf_native_recast_pos is not None:
            _ctf_native_hit_pos_obj = _ctf_native_recast_pos
        _ctf_native_recast_normal = getattr(_ctf_native_result, "hit_normal", None)
        if _ctf_native_recast_normal is not None:
            _ctf_native_normal_obj = _ctf_native_recast_normal
        _ctf_native_recast_material = getattr(_ctf_native_result, "materialTypeId", None)
        if _ctf_native_recast_material is not None:
            _ctf_native_material = _ctf_native_recast_material
        _ctf_native_best = _ctf_native_best[:-1] + ("recast",)
    else:
        if not _ctf_native_best[6]:
            state["magic_hitbox_player_recast_misses"] = (
                state.get("magic_hitbox_player_recast_misses", 0) + 1
            )
            state["magic_hitbox_player_synthetic_fallbacks"] = (
                state.get("magic_hitbox_player_synthetic_fallbacks", 0) + 1
            )
        state["magic_hitbox_synthetic_fallbacks"] = (
            state.get("magic_hitbox_synthetic_fallbacks", 0) + 1
        )

    _ctf_native_result.start_pos = _ctf_native_start_obj
    _ctf_native_result.shoot_dir = _ctf_native_payload_dir_obj or _ctf_native_dir_obj
    _ctf_native_result.target = _ctf_native_target
    _ctf_native_result.target_name = _ctf_native_call(_ctf_native_target, "GetName") or ""
    _ctf_native_result.hit_normal = _ctf_native_normal_obj
    _ctf_native_result.is_hit = True
    _ctf_native_result.physics_hit_pos = _ctf_native_hit_pos_obj
    _ctf_native_result.materialTypeId = _ctf_native_material
    _ctf_native_result.raycast_bone_res = _ctf_native_bone_res
    _ctf_native_result.penetrate_count = penetrate_count
    _ctf_native_result.penetrate_power = penetrate_power
    _ctf_native_hit_distance = _ctf_native_distance(
        _ctf_native_start,
        _ctf_native_vec3(_ctf_native_hit_pos_obj) or _ctf_native_hit_point,
    )
    if _ctf_native_hit_distance is not None:
        for _ctf_native_distance_attr in ("Distance", "distance", "Dist", "dist"):
            _ctf_native_setattr(_ctf_native_result, _ctf_native_distance_attr, _ctf_native_hit_distance)
        _ctf_native_setattr(_ctf_native_result, "shoot_range", _ctf_native_effective_range)
    _ctf_native_result.has_penerate = False
    _ctf_native_result.collision_info = _ctf_native_collision_info()
    _ctf_native_result.magic_hitbox = True
    _ctf_native_result.verify_start_pos = _ctf_native_start_obj
    _ctf_native_result.verify_shoot_dir = _ctf_native_payload_dir_obj or _ctf_native_dir_obj

    _ctf_native_install_damage_payload_patch(state, caster)
    try:
        _ctf_native_start_tuple = _ctf_native_start_obj.tuple()
    except Exception:
        _ctf_native_start_tuple = _ctf_native_start
    state["magic_hitbox_last_payload"] = {
        "time": _ctf_native_time.time(),
        "target": _ctf_native_target,
        "hit_pos_obj": _ctf_native_hit_pos_obj,
        "hit_part": _ctf_native_hit_part,
        "material": _ctf_native_material,
        "start_pos_obj": _ctf_native_start_obj,
        "start_pos_tuple": _ctf_native_start_tuple,
        "shoot_dir_obj": _ctf_native_payload_dir_obj or _ctf_native_dir_obj,
        "hit_back": False,
        "penetrate_power": penetrate_power or 1000,
    }
    # Do not submit a second, detached player damage result here. The caller's
    # live SpellWorker consumes this result and invokes DealWeaponDamageResult
    # once with the correct spell id, weapon, ammo, and send context.
    state["magic_hitbox_hits"] = state.get("magic_hitbox_hits", 0) + 1
    state["magic_hitbox_last_target"] = _ctf_native_best[5]
    state["magic_hitbox_last_part"] = _ctf_native_bone_res.name
    state["magic_hitbox_last_kind"] = "bot" if _ctf_native_best[6] else "player"
    state["magic_hitbox_last_mode"] = _ctf_native_best[7]
    state["magic_hitbox_last_intersect"] = _ctf_native_intersect_point
    return _ctf_native_result


def _ctf_native_result_hits_combat(result):
    if result is None:
        return False
    try:
        _ctf_native_target = getattr(result, "target", None)
        if _ctf_native_target is not None and (
            _ctf_native_is_combat_avatar(_ctf_native_target) or
            _ctf_native_flag(_ctf_native_target, "IsSimpleCombatUnit")
        ):
            return True
    except Exception:
        pass
    try:
        _ctf_native_bone_res = getattr(result, "raycast_bone_res", None)
        if _ctf_native_bone_res is not None and getattr(result, "materialTypeId", None) in (1001, 1002):
            return True
    except Exception:
        pass
    return False


def _ctf_native_result_has_hit(result):
    if result is None:
        return False
    try:
        if isinstance(result, (list, tuple)):
            if len(result) >= 2 and isinstance(result[0], (list, tuple)):
                return any(_ctf_native_result_hits_combat(_ctf_native_item) for _ctf_native_item in result[0])
            return any(_ctf_native_result_hits_combat(_ctf_native_item) for _ctf_native_item in result)
    except Exception:
        pass
    return _ctf_native_result_hits_combat(result)


def _ctf_native_penetrate_result(original, penetrate_info):
    try:
        if isinstance(original, (list, tuple)) and len(original) >= 2 and isinstance(original[1], dict):
            return original[1]
    except Exception:
        pass
    if isinstance(penetrate_info, dict):
        return {
            "bullet_penerate_count": penetrate_info.get("bullet_penerate_count", 0),
            "bullet_penerate_power": penetrate_info.get("bullet_penerate_power", 0),
            "penetrate_end": True,
        }
    return {
        "bullet_penerate_count": 0,
        "bullet_penerate_power": 0,
        "penetrate_end": True,
    }


def _ctf_native_install_magic_hitbox_patch(state):
    try:
        from gclient.gameplay.logic_base.spell.spell_core import spell_core_main as _ctf_native_spell_core_main

        if not hasattr(_ctf_native_spell_core_main, "_ctf_native_original_GetShootResult"):
            _ctf_native_spell_core_main._ctf_native_original_GetShootResult = _ctf_native_spell_core_main.GetShootResult
        if not hasattr(_ctf_native_spell_core_main, "_ctf_native_original_GetShootResultWithPenetrate"):
            _ctf_native_spell_core_main._ctf_native_original_GetShootResultWithPenetrate = _ctf_native_spell_core_main.GetShootResultWithPenetrate

        def _ctf_native_wrapped_get_shoot_result(caster, shoot_range, shoot_screen_pos, shoot_dir=None, start_pos=None):
            _ctf_native_live_state = getattr(_ctf_native_builtins, _ctf_native_state_name, state)
            _ctf_native_original = _ctf_native_spell_core_main._ctf_native_original_GetShootResult
            _ctf_native_original_result = _ctf_native_original(
                caster, shoot_range, shoot_screen_pos, shoot_dir, start_pos
            )
            if _ctf_native_result_has_hit(_ctf_native_original_result):
                return _ctf_native_original_result
            _ctf_native_magic_result = _ctf_native_make_magic_result(
                _ctf_native_live_state,
                caster,
                shoot_range,
                shoot_screen_pos,
                shoot_dir,
                start_pos,
                0,
                0,
            )
            return _ctf_native_magic_result if _ctf_native_magic_result is not None else _ctf_native_original_result

        def _ctf_native_wrapped_get_shoot_result_with_penetrate(
            caster,
            shoot_range,
            shoot_screen_pos,
            shoot_dir=None,
            start_pos=None,
            penetrate_info=None,
            robot_hit=False,
            force_miss=False,
        ):
            _ctf_native_live_state = getattr(_ctf_native_builtins, _ctf_native_state_name, state)
            _ctf_native_original = _ctf_native_spell_core_main._ctf_native_original_GetShootResultWithPenetrate
            _ctf_native_original_result = _ctf_native_original(
                caster,
                shoot_range,
                shoot_screen_pos,
                shoot_dir,
                start_pos,
                penetrate_info,
                robot_hit,
                force_miss,
            )
            if _ctf_native_result_has_hit(_ctf_native_original_result):
                return _ctf_native_original_result

            _ctf_native_penetrate_count = 0
            _ctf_native_penetrate_power = 0
            if isinstance(penetrate_info, dict):
                _ctf_native_penetrate_count = penetrate_info.get("bullet_penerate_count", 0)
                _ctf_native_penetrate_power = penetrate_info.get("bullet_penerate_power", 0)
            _ctf_native_magic_result = _ctf_native_make_magic_result(
                _ctf_native_live_state,
                caster,
                shoot_range,
                shoot_screen_pos,
                shoot_dir,
                start_pos,
                _ctf_native_penetrate_count,
                _ctf_native_penetrate_power,
            )
            if _ctf_native_magic_result is None:
                return _ctf_native_original_result
            if penetrate_info:
                return (
                    [_ctf_native_magic_result],
                    _ctf_native_penetrate_result(_ctf_native_original_result, penetrate_info),
                )
            return _ctf_native_magic_result

        _ctf_native_spell_core_main.GetShootResult = _ctf_native_wrapped_get_shoot_result
        _ctf_native_spell_core_main.GetShootResultWithPenetrate = _ctf_native_wrapped_get_shoot_result_with_penetrate
        state["magic_hitbox_patch_installed"] = True
        _ctf_native_log("MAGIC_HITBOX_PATCH installed")
    except Exception:
        state["magic_hitbox_patch_installed"] = False
        _ctf_native_log("MAGIC_HITBOX_PATCH_EXC\n" + _ctf_native_traceback.format_exc())


def _ctf_native_head_position(state, key, entity, entity_pos):
    """Return the current model head/upper-body point for posture-safe aiming."""
    _ctf_native_model = getattr(entity, "model", None)
    if _ctf_native_model is None:
        return None

    _ctf_native_head_models = state.setdefault("head_models", {})
    _ctf_native_model_id = id(_ctf_native_model)
    if _ctf_native_head_models.get(key) != _ctf_native_model_id:
        _ctf_native_ensure_aim_bones(state, key, _ctf_native_model)
        _ctf_native_head_models[key] = _ctf_native_model_id

    # Refresh the skeleton immediately before reading the bone.  This keeps
    # the exported point tied to the same animation frame as CameraFrame.
    _ctf_native_call(_ctf_native_model, "MakeSureBones")

    _ctf_native_low, _ctf_native_high = _ctf_native_bounds(entity)
    for _ctf_native_bone in ("biped Head", "biped Neck", "biped Spine2"):
        _ctf_native_head = _ctf_native_vec3(
            _ctf_native_call(_ctf_native_model, "GetBoneWorldPosition", _ctf_native_bone)
        )
        if _ctf_native_head is None or not all(_ctf_native_math.isfinite(value) for value in _ctf_native_head):
            continue
        if not _ctf_native_point_in_bounds(_ctf_native_head, _ctf_native_low, _ctf_native_high):
            continue
        # The head can legitimately be below the entity origin while crouching
        # or sliding.  Only reject clearly detached stale bones.
        if entity_pos is not None:
            _ctf_native_offset = (
                _ctf_native_head[0] - entity_pos[0],
                _ctf_native_head[1] - entity_pos[1],
                _ctf_native_head[2] - entity_pos[2],
            )
            if _ctf_native_math.sqrt(_ctf_native_dot(_ctf_native_offset, _ctf_native_offset)) > 8.0:
                continue
        return _ctf_native_head
    return None


def _ctf_native_active_space(state):
    _ctf_native_space = state.get("physics_space")
    if _ctf_native_space is not None:
        return _ctf_native_space
    try:
        from gclient.framework.entities.space import Space as _ctf_native_space_class
        _ctf_native_spaces = [
            space for space in _ctf_native_gc.get_objects()
            if isinstance(space, _ctf_native_space_class)
        ]
        # The active scene is the non-disposed Space instance.  Disposed spaces
        # retain a '(D)' suffix while the shooting-range scene remains live.
        _ctf_native_space = next(
            (space for space in _ctf_native_spaces if "(D)" not in repr(space)),
            None,
        )
        if _ctf_native_space is not None:
            state["physics_space"] = _ctf_native_space
        return _ctf_native_space
    except Exception:
        return None


def _ctf_native_visibility_filter_values(state):
    _ctf_native_filters = state.get("visibility_filter_values")
    if _ctf_native_filters is not None:
        return _ctf_native_filters
    _ctf_native_filters = ()
    try:
        from gclient import cconst as _ctf_native_cconst
        _ctf_native_values = []
        for _ctf_native_name in (
            "PHYSICS_VISIBLE_OBSTACLE_QUERY",
            "PHYSICS_OBSTACLE_QUERY",
            "PHYSICS_SHOOT_VERIFY",
            "PHYSICS_CAMERA",
            "PHYSICS_BULLET",
            "PHYSICS_THROWN",
        ):
            _ctf_native_value = getattr(_ctf_native_cconst, _ctf_native_name, None)
            if isinstance(_ctf_native_value, int) and _ctf_native_value not in _ctf_native_values:
                _ctf_native_values.append(_ctf_native_value)
        _ctf_native_filters = tuple(_ctf_native_values)
    except Exception:
        _ctf_native_filters = ()
    state["visibility_filter_values"] = _ctf_native_filters
    return _ctf_native_filters


def _ctf_native_distance(a, b):
    if a is None or b is None:
        return None
    try:
        return _ctf_native_math.sqrt(
            (a[0] - b[0]) * (a[0] - b[0]) +
            (a[1] - b[1]) * (a[1] - b[1]) +
            (a[2] - b[2]) * (a[2] - b[2])
        )
    except Exception:
        return None


def _ctf_native_hit_position(hit):
    for _ctf_native_name in (
        "Pos",
        "HitPos",
        "HitPosition",
        "position",
        "point",
        "Point",
        "hit_pos",
        "hitPoint",
        "HitPoint",
    ):
        _ctf_native_pos = _ctf_native_vec3(getattr(hit, _ctf_native_name, None))
        if _ctf_native_pos is not None:
            return _ctf_native_pos
    return None


def _ctf_native_collision_distance(hit):
    for _ctf_native_name in ("Distance", "distance", "Dist", "dist"):
        try:
            _ctf_native_value = float(getattr(hit, _ctf_native_name))
            if _ctf_native_math.isfinite(_ctf_native_value) and _ctf_native_value >= 0.0:
                return _ctf_native_value
        except Exception:
            pass
    return None


def _ctf_native_environment_blocked(state, space, camera_pos, point):
    _ctf_native_camera = _ctf_native_vec3(camera_pos)
    _ctf_native_point = _ctf_native_vec3(point)
    _ctf_native_target_distance = _ctf_native_distance(_ctf_native_camera, _ctf_native_point)
    for _ctf_native_filter in _ctf_native_visibility_filter_values(state):
        _ctf_native_hit = _ctf_native_call(
            space, "ClosestRaycast", camera_pos, point, _ctf_native_filter, False
        )
        if _ctf_native_hit is not None and getattr(_ctf_native_hit, "IsHit", False):
            _ctf_native_hit_pos = _ctf_native_hit_position(_ctf_native_hit)
            _ctf_native_hit_distance = _ctf_native_distance(_ctf_native_camera, _ctf_native_hit_pos)
            if _ctf_native_hit_distance is None:
                _ctf_native_hit_distance = _ctf_native_collision_distance(_ctf_native_hit)
            if _ctf_native_hit_distance is not None:
                if _ctf_native_hit_distance <= 0.85:
                    state["visibility_near_hit_count"] = state.get("visibility_near_hit_count", 0) + 1
                    continue
                if (
                    _ctf_native_target_distance is not None and
                    _ctf_native_hit_distance >= _ctf_native_target_distance - 0.30
                ):
                    continue
            elif _ctf_native_hit_pos is None:
                state["visibility_unknown_hit_count"] = state.get("visibility_unknown_hit_count", 0) + 1
                continue
            state["visibility_env_block_count"] = state.get("visibility_env_block_count", 0) + 1
            state["visibility_env_last_filter"] = _ctf_native_filter
            return True
    return False


def _ctf_native_target_skeleton_hit(space, camera_pos, point, skeleton):
    _ctf_native_hits = _ctf_native_call(
        space, "RaycastBoneWithPenetrate", camera_pos, point
    )
    if isinstance(_ctf_native_hits, (list, tuple)):
        return bool(
            len(_ctf_native_hits) == 1 and
            getattr(_ctf_native_hits[0], "IsHit", False) and
            getattr(_ctf_native_hits[0], "actor", None) == skeleton
        )
    _ctf_native_hit = _ctf_native_call(
        space, "ClosestRaycastBone", camera_pos, point
    )
    return bool(
        _ctf_native_hit is not None and
        getattr(_ctf_native_hit, "IsHit", False) and
        getattr(_ctf_native_hit, "actor", None) == skeleton
    )


def _ctf_native_visible(state, key, entity, camera_pos):
    """Use the game physics scene so aim assist never selects a wall-blocked head."""
    _ctf_native_now = _ctf_native_time.time()
    _ctf_native_cache = state.setdefault("visibility_cache", {})
    _ctf_native_aim_points = state.setdefault("visibility_aim_points", {})
    _ctf_native_cached = _ctf_native_cache.get(key)
    if _ctf_native_cached is not None and _ctf_native_now - _ctf_native_cached[0] < (1.0 / 120.0):
        return _ctf_native_cached[1]
    _ctf_native_aim_points.pop(key, None)

    _ctf_native_model = getattr(entity, "model", None)
    _ctf_native_space = _ctf_native_active_space(state)
    if _ctf_native_model is None or _ctf_native_space is None:
        _ctf_native_cache[key] = (_ctf_native_now, False)
        return False
    _ctf_native_ensure_aim_bones(state, key, _ctf_native_model)
    _ctf_native_call(_ctf_native_model, "MakeSureBones")
    _ctf_native_skeleton = _ctf_native_call(_ctf_native_model, "GetSkeleton")
    _ctf_native_low, _ctf_native_high = _ctf_native_bounds(entity)
    _ctf_native_posture_fallback = None
    for _ctf_native_bone in _ctf_native_aim_bones:
        _ctf_native_point = _ctf_native_call(
            _ctf_native_model, "GetBoneWorldPosition", _ctf_native_bone
        )
        _ctf_native_point_tuple = _ctf_native_vec3(_ctf_native_point)
        if (
            _ctf_native_point_tuple is None or
            not all(_ctf_native_math.isfinite(value) for value in _ctf_native_point_tuple)
        ):
            continue
        if not _ctf_native_point_in_bounds(_ctf_native_point_tuple, _ctf_native_low, _ctf_native_high):
            continue
        if _ctf_native_environment_blocked(
            state, _ctf_native_space, camera_pos, _ctf_native_point
        ):
            continue
        if not _ctf_native_target_skeleton_hit(
            _ctf_native_space, camera_pos, _ctf_native_point, _ctf_native_skeleton
        ):
            if _ctf_native_posture_fallback is None and _ctf_native_bone != "biped Pelvis":
                _ctf_native_posture_fallback = _ctf_native_point_tuple
            state["visibility_skeleton_miss_count"] = state.get("visibility_skeleton_miss_count", 0) + 1
            continue
        _ctf_native_aim_points[key] = _ctf_native_point_tuple
        _ctf_native_cache[key] = (_ctf_native_now, True)
        return True
    if _ctf_native_posture_fallback is None:
        for _ctf_native_point, _ctf_native_point_tuple in _ctf_native_upper_body_fallback_points(
            camera_pos, _ctf_native_low, _ctf_native_high
        ):
            if _ctf_native_environment_blocked(
                state, _ctf_native_space, camera_pos, _ctf_native_point
            ):
                continue
            _ctf_native_posture_fallback = _ctf_native_point_tuple
            break
    if _ctf_native_posture_fallback is not None:
        state["visibility_posture_fallback_count"] = state.get("visibility_posture_fallback_count", 0) + 1
        _ctf_native_aim_points[key] = _ctf_native_posture_fallback
        _ctf_native_cache[key] = (_ctf_native_now, True)
        return True
    _ctf_native_cache[key] = (_ctf_native_now, False)
    return False


def _ctf_native_hide_widget(widget):
    if widget is None:
        return
    for _ctf_native_attr, _ctf_native_value in (("visible", False), ("opacity", 0), ("text", "")):
        try:
            setattr(widget, _ctf_native_attr, _ctf_native_value)
        except Exception:
            pass
    for _ctf_native_name, _ctf_native_args in (
        ("setVisible", (False,)),
        ("SetVisible", (False,)),
        ("SetHiddenReason", (True, 918273,)),
    ):
        _ctf_native_call(widget, _ctf_native_name, *_ctf_native_args)


def _ctf_native_suppress_legacy_widgets(robot):
    """Remove the prior fixed UI marker so only the projected C++ box remains."""
    _ctf_native_frame = getattr(robot, "recon_drone_frame_top_logo", None)
    if _ctf_native_frame is not None:
        for _ctf_native_attr in ("ui_node_top_logo", "scene_node", "panel_frame"):
            _ctf_native_hide_widget(getattr(_ctf_native_frame, _ctf_native_attr, None))
    _ctf_native_toplogo = getattr(robot, "toplogo", None)
    if _ctf_native_toplogo is not None:
        for _ctf_native_attr in (
            "toplogo_widget",
            "node_name_hp",
            "text_dis_friend",
            "text_name_enemy",
        ):
            _ctf_native_hide_widget(getattr(_ctf_native_toplogo, _ctf_native_attr, None))


def _ctf_native_stop_legacy_timer():
    _ctf_native_old = getattr(_ctf_native_builtins, _ctf_native_legacy_state_name, None)
    if not isinstance(_ctf_native_old, dict):
        return
    _ctf_native_owner = _ctf_native_old.get("timer_owner")
    _ctf_native_timer = _ctf_native_old.get("timer_id")
    if _ctf_native_owner is not None and _ctf_native_timer is not None:
        _ctf_native_call(_ctf_native_owner, "cancel_timer", _ctf_native_timer)
    _ctf_native_old["timer_id"] = None
    _ctf_native_old["timer_owner"] = None


def _ctf_native_entities():
    import common.EntityManager as _ctf_native_em

    _ctf_native_values = getattr(_ctf_native_em.EntityManager, "_entities", {}).items()
    _ctf_native_players = []
    _ctf_native_robots = []
    for _ctf_native_key, _ctf_native_entity in list(_ctf_native_values):
        try:
            _ctf_native_type_name = type(_ctf_native_entity).__name__.lower()
            _ctf_native_is_robot = _ctf_native_flag(_ctf_native_entity, "IsRobotCombatAvatar")
            _ctf_native_is_player = _ctf_native_flag(_ctf_native_entity, "IsPlayerCombatAvatar")
            if _ctf_native_is_robot:
                _ctf_native_robots.append((str(_ctf_native_key), _ctf_native_entity))
            elif _ctf_native_is_player:
                _ctf_native_players.append((str(_ctf_native_key), _ctf_native_entity))
            elif _ctf_native_is_combat_avatar(_ctf_native_entity):
                # Some real players are exposed as the base CombatAvatarMoba
                # class while their player flag is still false.  Robots keep
                # the robot class/flag and everything else is a player.
                if "robot" in _ctf_native_type_name:
                    _ctf_native_robots.append((str(_ctf_native_key), _ctf_native_entity))
                else:
                    _ctf_native_players.append((str(_ctf_native_key), _ctf_native_entity))
        except Exception:
            pass
    return _ctf_native_players, _ctf_native_robots


def _ctf_native_flag(entity, name):
    try:
        _ctf_native_value = getattr(entity, name)
        if callable(_ctf_native_value):
            _ctf_native_value = _ctf_native_value()
        return bool(_ctf_native_value)
    except Exception:
        return False


def _ctf_native_bool_probe(entity, names):
    """Return an explicit boolean only when the game exposes one."""
    for _ctf_native_name in names:
        try:
            _ctf_native_value = getattr(entity, _ctf_native_name)
            if callable(_ctf_native_value):
                _ctf_native_value = _ctf_native_value()
            if isinstance(_ctf_native_value, bool):
                return True, _ctf_native_value
        except Exception:
            pass
    return False, False


def _ctf_native_scalar_probe(entity, names):
    for _ctf_native_name in names:
        try:
            _ctf_native_value = getattr(entity, _ctf_native_name)
            if callable(_ctf_native_value):
                _ctf_native_value = _ctf_native_value()
            if isinstance(_ctf_native_value, bool):
                continue
            if isinstance(_ctf_native_value, (str, int, float)):
                return str(_ctf_native_value)
            for _ctf_native_child_name in (
                "id", "guid", "key", "team_id", "teamId", "teamID", "code"
            ):
                _ctf_native_child = getattr(_ctf_native_value, _ctf_native_child_name, None)
                if callable(_ctf_native_child):
                    _ctf_native_child = _ctf_native_child()
                if isinstance(_ctf_native_child, (str, int, float)) and not isinstance(_ctf_native_child, bool):
                    return str(_ctf_native_child)
        except Exception:
            pass
    return None


def _ctf_native_identity_candidates(key, entity):
    _ctf_native_candidates = [str(key)]
    for _ctf_native_name in (
        "id", "guid", "key", "entity_id", "player_id", "player_guid",
        "combat_avatar_id", "avatar_id"
    ):
        try:
            _ctf_native_value = getattr(entity, _ctf_native_name)
            if callable(_ctf_native_value):
                _ctf_native_value = _ctf_native_value()
            if isinstance(_ctf_native_value, (str, int, float)) and not isinstance(_ctf_native_value, bool):
                _ctf_native_text = str(_ctf_native_value)
                if _ctf_native_text and _ctf_native_text not in _ctf_native_candidates:
                    _ctf_native_candidates.append(_ctf_native_text)
        except Exception:
            pass
    return _ctf_native_candidates


def _ctf_native_team_relation(local_player, target_key, target, is_robot):
    """Use explicit team APIs first; do not infer a team from screen position."""
    _ctf_native_has_value, _ctf_native_value = _ctf_native_bool_probe(
        target, ("is_teammate", "is_team_mate", "IsTeammate", "IsTeamMate", "is_friend", "IsFriend")
    )
    if _ctf_native_has_value:
        return 1 if _ctf_native_value else 2

    _ctf_native_has_value, _ctf_native_value = _ctf_native_bool_probe(
        target, ("is_enemy", "IsEnemy", "enemy", "is_hostile", "IsHostile")
    )
    if _ctf_native_has_value:
        return 2 if _ctf_native_value else 1

    _ctf_native_local_team = _ctf_native_scalar_probe(
        local_player,
        ("team_id", "teamId", "teamID", "camp_id", "campId", "camp", "faction_id", "factionId", "faction"),
    )
    _ctf_native_target_team = _ctf_native_scalar_probe(
        target,
        ("team_id", "teamId", "teamID", "camp_id", "campId", "camp", "faction_id", "factionId", "faction"),
    )
    if _ctf_native_local_team is not None and _ctf_native_target_team is not None:
        return 1 if _ctf_native_local_team == _ctf_native_target_team else 2

    _ctf_native_target_ids = _ctf_native_identity_candidates(target_key, target)
    if local_player is not None:
        try:
            _ctf_native_teammates = getattr(local_player, "teammate_info")
            if isinstance(_ctf_native_teammates, dict):
                for _ctf_native_target_id in _ctf_native_target_ids:
                    if _ctf_native_target_id in _ctf_native_teammates:
                        return 1
            elif isinstance(_ctf_native_teammates, (set, list, tuple)):
                for _ctf_native_target_id in _ctf_native_target_ids:
                    if _ctf_native_target_id in _ctf_native_teammates:
                        return 1
        except Exception:
            pass

        _ctf_native_get_info = getattr(local_player, "GetTeammateInfo", None)
        if callable(_ctf_native_get_info):
            for _ctf_native_target_id in _ctf_native_target_ids:
                try:
                    _ctf_native_info = _ctf_native_get_info(_ctf_native_target_id)
                    if _ctf_native_info not in (None, False, {}, [], ()):
                        return 1
                except Exception:
                    pass

    _ctf_native_has_value, _ctf_native_value = _ctf_native_bool_probe(
        target, ("CanShowEnemyToplogo", "CanShowEnemyToplogoBar")
    )
    if _ctf_native_has_value and _ctf_native_value:
        return 2
    # Shooting-range robots have no team object, but are authoritative enemy
    # targets in this mode.  Keep the label useful while preserving unknown
    # for player entities whose team state is unavailable during transitions.
    if is_robot:
        return 2
    return 0


def _ctf_native_is_combat_avatar(entity):
    if _ctf_native_flag(entity, "IsCombatAvatar"):
        return True
    _ctf_native_type_name = type(entity).__name__.lower()
    return _ctf_native_type_name.endswith("combatavatarmoba")


def _ctf_native_timer_owner(players, robots):
    """Use a live game object as the timer owner, including in the lobby."""
    _ctf_native_candidates = [
        _ctf_native_entity
        for _ctf_native_key, _ctf_native_entity in players + robots
    ]
    try:
        import common.EntityManager as _ctf_native_em
        _ctf_native_candidates.extend(
            getattr(_ctf_native_em.EntityManager, "_entities", {}).values()
        )
    except Exception:
        pass

    _ctf_native_seen = set()
    for _ctf_native_candidate in _ctf_native_candidates:
        if id(_ctf_native_candidate) in _ctf_native_seen:
            continue
        _ctf_native_seen.add(id(_ctf_native_candidate))
        if callable(getattr(_ctf_native_candidate, "add_repeat_timer", None)):
            return _ctf_native_candidate
    return None


def _ctf_native_local_player(state, players):
    """Keep the controlled player out of the target stream across entity reorderings."""
    _ctf_native_local_key = state.get("local_key")
    for _ctf_native_key, _ctf_native_entity in players:
        if _ctf_native_key == _ctf_native_local_key:
            return _ctf_native_key, _ctf_native_entity

    try:
        import common.EntityManager as _ctf_native_em
        _ctf_native_all_entities = list(
            getattr(_ctf_native_em.EntityManager, "_entities", {}).values()
        )
    except Exception:
        _ctf_native_all_entities = []

    # GameLogicMoba keeps the authoritative reference to the controlled
    # combat avatar.  Prefer object identity over list order.
    for _ctf_native_manager in _ctf_native_all_entities:
        try:
            _ctf_native_candidate = getattr(_ctf_native_manager, "player")
            if callable(_ctf_native_candidate):
                _ctf_native_candidate = _ctf_native_candidate()
            for _ctf_native_key, _ctf_native_entity in players:
                if _ctf_native_entity is _ctf_native_candidate:
                    state["local_key"] = _ctf_native_key
                    return _ctf_native_key, _ctf_native_entity
        except Exception:
            pass

    # The hall profile name is a stable fallback when the game-logic reference
    # is temporarily unavailable during a scene transition.
    _ctf_native_profile_names = set()
    for _ctf_native_entity in _ctf_native_all_entities:
        if type(_ctf_native_entity).__name__ != "PlayerAvatar":
            continue
        try:
            _ctf_native_name = getattr(_ctf_native_entity, "name")
            if isinstance(_ctf_native_name, str) and _ctf_native_name:
                _ctf_native_profile_names.add(_ctf_native_name)
        except Exception:
            pass
    for _ctf_native_key, _ctf_native_entity in players:
        try:
            if getattr(_ctf_native_entity, "name") in _ctf_native_profile_names:
                state["local_key"] = _ctf_native_key
                return _ctf_native_key, _ctf_native_entity
        except Exception:
            pass

    for _ctf_native_key, _ctf_native_entity in players:
        for _ctf_native_name in ("is_main_player", "is_local_player", "is_self", "IsMainPlayer"):
            try:
                _ctf_native_value = getattr(_ctf_native_entity, _ctf_native_name)
                if callable(_ctf_native_value):
                    _ctf_native_value = _ctf_native_value()
                if _ctf_native_value:
                    state["local_key"] = _ctf_native_key
                    return _ctf_native_key, _ctf_native_entity
            except Exception:
                pass

    if len(players) == 1:
        _ctf_native_key, _ctf_native_entity = players[0]
        state["local_key"] = _ctf_native_key
        return _ctf_native_key, _ctf_native_entity
    # Never guess the local avatar from an unordered multi-player list.
    return None, None


def _ctf_native_active_weapon_ballistics(player):
    """Read equipped projectile data after weapon parts/modifiers are applied."""
    if player is None:
        return 0, 0.0, 0.0
    weapon = _ctf_native_call(player, "GetCurHighPriorityWeapon")
    if weapon is None:
        return 0, 0.0, 0.0

    try:
        item_id = int(getattr(weapon, "item_id", 0) or 0)
    except Exception:
        item_id = 0

    base_speed = 0.0
    base_gravity = 0.0
    try:
        proto = getattr(weapon, "weapon_proto", None)
        if proto is not None:
            if hasattr(proto, "get"):
                base_speed = float(proto.get("bullet_velocity", 0.0) or 0.0)
                base_gravity = float(proto.get("bullet_gravity", 0.0) or 0.0)
            else:
                base_speed = float(getattr(proto, "bullet_velocity", 0.0) or 0.0)
                base_gravity = float(getattr(proto, "bullet_gravity", 0.0) or 0.0)
    except Exception:
        pass

    # This resolves the currently equipped weapon case, including compatible mods.
    effective_speed = _ctf_native_call(
        player,
        "GetWeaponAttrValueWithCache",
        "bullet_velocity",
        base_speed,
        0.10,
    )
    try:
        speed = float(effective_speed)
    except Exception:
        speed = base_speed
    effective_gravity = _ctf_native_call(
        player,
        "GetWeaponAttrValueWithCache",
        "bullet_gravity",
        base_gravity,
        0.10,
    )
    try:
        gravity = abs(float(effective_gravity))
    except Exception:
        gravity = abs(base_gravity)
    # Reject multipliers and malformed values.  A confirmed gravity value is
    # in world acceleration units; zero means this weapon has no exported drop.
    if not _ctf_native_math.isfinite(gravity) or gravity < 0.10 or gravity > 30.0:
        gravity = 0.0
    return item_id, speed if speed > 0.0 else 0.0, gravity


def _ctf_native_write_snapshot(state):
    import MCamera as _ctf_native_camera
    import MUI as _ctf_native_ui

    _ctf_native_players, _ctf_native_robots = _ctf_native_entities()
    _ctf_native_local_key, _ctf_native_player = _ctf_native_local_player(state, _ctf_native_players)
    _ctf_native_player_pos = _ctf_native_position(_ctf_native_player) if _ctf_native_player is not None else (0.0, 0.0, 0.0)
    (
        _ctf_native_weapon_item_id,
        _ctf_native_projectile_speed,
        _ctf_native_projectile_gravity,
    ) = _ctf_native_active_weapon_ballistics(_ctf_native_player)
    _ctf_native_frame = _ctf_native_camera.CaptureFrame()
    _ctf_native_camera_pos = _ctf_native_vec3(_ctf_native_frame.Position) or (0.0, 0.0, 0.0)
    _ctf_native_screen = _ctf_native_ui.GetScreenSize()
    _ctf_native_rows = []

    _ctf_native_targets = [
        (_ctf_native_key, _ctf_native_entity, False)
        for _ctf_native_key, _ctf_native_entity in _ctf_native_players
        if _ctf_native_key != _ctf_native_local_key
    ] + [
        (_ctf_native_key, _ctf_native_entity, True)
        for _ctf_native_key, _ctf_native_entity in _ctf_native_robots
    ]
    state["last_player_targets"] = len(_ctf_native_targets) - len(_ctf_native_robots)
    state["last_robot_targets"] = len(_ctf_native_robots)
    _ctf_native_visible_count = 0
    _ctf_native_range = _ctf_native_max_target_distance(state)
    _ctf_native_range_sq = _ctf_native_range * _ctf_native_range
    _ctf_native_culled_targets = 0
    _ctf_native_detected_players = 0
    _ctf_native_detected_robots = 0

    for _ctf_native_key, _ctf_native_target, _ctf_native_is_robot in _ctf_native_targets:
        _ctf_native_pos = _ctf_native_position(_ctf_native_target)
        if _ctf_native_pos is None:
            continue
        if _ctf_native_player is not None:
            _ctf_native_dx = _ctf_native_pos[0] - _ctf_native_player_pos[0]
            _ctf_native_dy = _ctf_native_pos[1] - _ctf_native_player_pos[1]
            _ctf_native_dz = _ctf_native_pos[2] - _ctf_native_player_pos[2]
            if _ctf_native_dx * _ctf_native_dx + _ctf_native_dy * _ctf_native_dy + _ctf_native_dz * _ctf_native_dz > _ctf_native_range_sq:
                _ctf_native_culled_targets += 1
                continue
        _ctf_native_suppress_legacy_widgets(_ctf_native_target)
        _ctf_native_low, _ctf_native_high = _ctf_native_bounds(_ctf_native_target)
        if _ctf_native_low is None or _ctf_native_high is None:
            continue
        _ctf_native_head = _ctf_native_head_position(
            state, _ctf_native_key, _ctf_native_target, _ctf_native_pos
        )
        _ctf_native_relation = _ctf_native_team_relation(
            _ctf_native_player,
            _ctf_native_key,
            _ctf_native_target,
            _ctf_native_is_robot,
        )
        _ctf_native_is_visible = _ctf_native_visible(
            state, _ctf_native_key, _ctf_native_target, _ctf_native_frame.Position
        )
        if _ctf_native_is_visible:
            _ctf_native_head = state.get("visibility_aim_points", {}).get(
                _ctf_native_key, _ctf_native_head
            )
        _ctf_native_visible_count += int(_ctf_native_is_visible)
        _ctf_native_hp = _ctf_native_metric(_ctf_native_target, ("hp", "server_hp", "client_hp", "_hp"), 0.0)
        _ctf_native_maxhp = _ctf_native_metric(_ctf_native_target, ("cur_maxhp", "maxhp", "base_maxhp", "server_maxhp"), max(1.0, _ctf_native_hp))
        _ctf_native_armor = _ctf_native_metric(_ctf_native_target, ("client_armor", "armor", "_client_armor", "server_armor"), 0.0)
        _ctf_native_maxarmor = _ctf_native_metric(_ctf_native_target, ("base_maxarmor", "maxarmor", "server_maxarmor"), max(0.0, _ctf_native_armor))
        _ctf_native_dead = int(bool(getattr(_ctf_native_target, "is_dead_state", False) or getattr(_ctf_native_target, "dead", False)))
        _ctf_native_rows.append((
            _ctf_native_key,
            _ctf_native_pos,
            _ctf_native_low,
            _ctf_native_high,
            _ctf_native_hp,
            _ctf_native_maxhp,
            _ctf_native_armor,
            _ctf_native_maxarmor,
            _ctf_native_dead,
            _ctf_native_head,
            _ctf_native_is_visible,
            _ctf_native_is_robot,
            _ctf_native_relation,
        ))
        if _ctf_native_is_robot:
            _ctf_native_detected_robots += 1
        else:
            _ctf_native_detected_players += 1

    _ctf_native_header = (
        "ESP1 {:.6f} {} {} {:.6f} {:.6f} {:.6f} {:.9f} {:.9f} {:.9f} {:.6f} "
        "{:.6f} {:.6f} {:.6f} {}\n"
    ).format(
        _ctf_native_time.time(),
        int(_ctf_native_screen.x),
        int(_ctf_native_screen.y),
        _ctf_native_camera_pos[0],
        _ctf_native_camera_pos[1],
        _ctf_native_camera_pos[2],
        float(_ctf_native_frame.Yaw),
        float(_ctf_native_frame.Pitch),
        float(_ctf_native_frame.Roll),
        float(_ctf_native_frame.Fov),
        _ctf_native_player_pos[0],
        _ctf_native_player_pos[1],
        _ctf_native_player_pos[2],
        len(_ctf_native_rows),
    )
    _ctf_native_lines = [_ctf_native_header]
    for _ctf_native_row in _ctf_native_rows:
        (
            _ctf_native_key,
            _ctf_native_pos,
            _ctf_native_low,
            _ctf_native_high,
            _ctf_native_hp,
            _ctf_native_maxhp,
            _ctf_native_armor,
            _ctf_native_maxarmor,
            _ctf_native_dead,
            _ctf_native_head,
            _ctf_native_is_visible,
            _ctf_native_is_robot,
            _ctf_native_relation,
        ) = _ctf_native_row
        _ctf_native_has_head = int(_ctf_native_head is not None)
        _ctf_native_head = _ctf_native_head or (0.0, 0.0, 0.0)
        _ctf_native_lines.append(
            "T {} {:.6f} {:.6f} {:.6f} {:.6f} {:.6f} {:.6f} {:.6f} {:.6f} {:.6f} {:.3f} {:.3f} {:.3f} {:.3f} {} {} {:.6f} {:.6f} {:.6f} {} {} {}\n".format(
                _ctf_native_key,
                _ctf_native_pos[0], _ctf_native_pos[1], _ctf_native_pos[2],
                _ctf_native_low[0], _ctf_native_low[1], _ctf_native_low[2],
                _ctf_native_high[0], _ctf_native_high[1], _ctf_native_high[2],
                _ctf_native_hp, _ctf_native_maxhp,
                _ctf_native_armor, _ctf_native_maxarmor, _ctf_native_dead,
                _ctf_native_has_head,
                _ctf_native_head[0], _ctf_native_head[1], _ctf_native_head[2],
                int(_ctf_native_is_visible),
                int(_ctf_native_is_robot),
                _ctf_native_relation,
            )
        )
    _ctf_native_lines.append(
        "W {} {:.6f} {:.6f}\n".format(
            _ctf_native_weapon_item_id,
            _ctf_native_projectile_speed,
            _ctf_native_projectile_gravity,
        )
    )
    _ctf_native_lines.append(
        "C {} {} {}\n".format(
            _ctf_native_detected_players,
            _ctf_native_detected_robots,
            _ctf_native_culled_targets,
        )
    )
    _ctf_native_lines.append("S {}\n".format(int(bool(state.get("exporter_ready", False)))))

    _ctf_native_local_temp_path = "{}.{}.{}.{}.tmp".format(
        _ctf_native_snapshot_path,
        _ctf_native_os.getpid(),
        state.get("tick", 0),
        int(_ctf_native_time.time() * 1000000),
    )
    with open(_ctf_native_local_temp_path, "w", encoding="ascii") as _ctf_native_handle:
        _ctf_native_handle.writelines(_ctf_native_lines)
    for _ctf_native_attempt in range(4):
        try:
            _ctf_native_os.replace(_ctf_native_local_temp_path, _ctf_native_snapshot_path)
            state["last_count"] = len(_ctf_native_rows)
            state["weapon_item_id"] = _ctf_native_weapon_item_id
            state["projectile_speed"] = _ctf_native_projectile_speed
            state["projectile_gravity"] = _ctf_native_projectile_gravity
            state["visible_targets"] = _ctf_native_visible_count
            state["culled_targets"] = _ctf_native_culled_targets
            state["detected_players"] = _ctf_native_detected_players
            state["detected_robots"] = _ctf_native_detected_robots
            return
        except PermissionError:
            # Readers use shared handles; retry around short external reads.
            _ctf_native_time.sleep(0.0015 * (_ctf_native_attempt + 1))
    try:
        _ctf_native_os.remove(_ctf_native_local_temp_path)
    except Exception:
        pass
    state["dropped_snapshots"] = state.get("dropped_snapshots", 0) + 1


def _ctf_native_tick(*_ctf_native_args, **_ctf_native_kwargs):
    _ctf_native_state = getattr(_ctf_native_builtins, _ctf_native_state_name, None)
    if not isinstance(_ctf_native_state, dict):
        return
    _ctf_native_now = _ctf_native_time.time()
    if _ctf_native_now < _ctf_native_state.get("next_snapshot_time", 0.0):
        return
    _ctf_native_state["next_snapshot_time"] = _ctf_native_now + _ctf_native_snapshot_interval
    try:
        _ctf_native_state["tick"] += 1
        _ctf_native_write_snapshot(_ctf_native_state)
        if _ctf_native_state["tick"] == 1 or _ctf_native_state["tick"] % 240 == 0:
            _ctf_native_log(
                "snapshot tick={} targets={} players={} bots={} culled={} range={:.0f} hitbox_range={:.0f} native_aim={} hitbox={} hitbox_scale={:.2f} magic_hits={} magic_misses={} near_hits={} recasts={} player_recasts={} player_recast_misses={} player_synthetic={} synthetic={} recast_err={} damage_dir_patches={} direct_player_ok={} direct_player_err={} trigger={} external={} seen={} miss={} applied={} lock={} apply_frame_ok={} source_players={} source_robots={} weapon={} velocity={:.3f} posture_fallback={} skeleton_miss={}".format(
                    _ctf_native_state["tick"],
                    _ctf_native_state.get("last_count", 0),
                    _ctf_native_state.get("detected_players", 0),
                    _ctf_native_state.get("detected_robots", 0),
                    _ctf_native_state.get("culled_targets", 0),
                    _ctf_native_state.get("max_target_distance", _ctf_native_default_max_distance),
                    _ctf_native_state.get("magic_hitbox_range", _ctf_native_default_magic_hitbox_range),
                    int(bool(_ctf_native_state.get("native_aim_enabled", True))),
                    int(bool(_ctf_native_state.get("hitbox_enabled", True))),
                    _ctf_native_state.get("hitbox_scale", _ctf_native_default_hitbox_scale),
                    _ctf_native_state.get("magic_hitbox_hits", 0),
                    _ctf_native_state.get("magic_hitbox_misses", 0),
                    _ctf_native_state.get("magic_hitbox_near_hits", 0),
                    _ctf_native_state.get("magic_hitbox_authoritative_recasts", 0),
                    _ctf_native_state.get("magic_hitbox_player_recasts", 0),
                    _ctf_native_state.get("magic_hitbox_player_recast_misses", 0),
                    _ctf_native_state.get("magic_hitbox_player_synthetic_fallbacks", 0),
                    _ctf_native_state.get("magic_hitbox_synthetic_fallbacks", 0),
                    _ctf_native_state.get("magic_hitbox_authoritative_recast_errors", 0),
                    _ctf_native_state.get("magic_hitbox_damage_dir_patches", 0),
                    _ctf_native_state.get("magic_hitbox_direct_player_damage_success", 0),
                    _ctf_native_state.get("magic_hitbox_direct_player_damage_errors", 0),
                    _ctf_native_state.get("native_aim_trigger_down", 0),
                    _ctf_native_state.get("native_aim_external_down", 0),
                    _ctf_native_state.get("native_aim_trigger_seen", 0),
                    _ctf_native_state.get("native_aim_candidate_miss", 0),
                    _ctf_native_state.get("native_aim_applied", 0),
                    _ctf_native_state.get("native_aim_lock_key", None),
                    int(bool(_ctf_native_state.get("native_apply_frame_ok", False))),
                    _ctf_native_state.get("last_player_targets", 0),
                    _ctf_native_state.get("last_robot_targets", 0),
                    _ctf_native_state.get("weapon_item_id", 0),
                    _ctf_native_state.get("projectile_speed", 0.0),
                    _ctf_native_state.get("visibility_posture_fallback_count", 0),
                    _ctf_native_state.get("visibility_skeleton_miss_count", 0),
                )
            )
    except Exception:
        _ctf_native_log("TICK_EXC\n" + _ctf_native_traceback.format_exc())


def _ctf_native_install():
    _ctf_native_stop_legacy_timer()
    _ctf_native_old = getattr(_ctf_native_builtins, _ctf_native_state_name, None)
    if isinstance(_ctf_native_old, dict):
        _ctf_native_call(_ctf_native_old.get("timer_owner"), "cancel_timer", _ctf_native_old.get("timer_id"))

    _ctf_native_state = {
        "tick": 0,
        "timer_id": None,
        "timer_owner": None,
        "last_count": 0,
        "last_player_targets": 0,
        "last_robot_targets": 0,
        "weapon_item_id": 0,
        "projectile_speed": 0.0,
        "projectile_gravity": 0.0,
        "exporter_ready": False,
        "local_key": None,
        "head_models": {},
        "aim_bone_models": {},
        "physics_space": None,
        "visibility_cache": {},
        "visible_targets": 0,
        "visibility_posture_fallback_count": 0,
        "visibility_skeleton_miss_count": 0,
        "detected_players": 0,
        "detected_robots": 0,
        "max_target_distance": _ctf_native_default_max_distance,
        "magic_hitbox_range": _ctf_native_default_magic_hitbox_range,
        "native_aim_enabled": False,
        "native_aim_applied": 0,
        "native_aim_trigger_down": 0,
        "native_aim_external_down": 0,
        "native_aim_trigger_seen": 0,
        "native_aim_candidate_miss": 0,
        "native_aim_lock_key": None,
        "aim_fov_px": 0.0,
        "visible_only": True,
        "hitbox_enabled": True,
        "hitbox_scale": _ctf_native_default_hitbox_scale,
        "magic_hitbox_patch_installed": False,
        "magic_hitbox_damage_patch_installed": False,
        "magic_hitbox_hits": 0,
        "magic_hitbox_misses": 0,
        "magic_hitbox_authoritative_recasts": 0,
        "magic_hitbox_player_recasts": 0,
        "magic_hitbox_player_recast_rejects": 0,
        "magic_hitbox_player_recast_misses": 0,
        "magic_hitbox_player_synthetic_fallbacks": 0,
        "magic_hitbox_synthetic_fallbacks": 0,
        "magic_hitbox_authoritative_recast_errors": 0,
        "magic_hitbox_damage_dir_patches": 0,
        "native_apply_frame_ok": False,
        "native_apply_frame_error": "",
        "next_config_refresh": 0.0,
        "next_snapshot_time": 0.0,
        "culled_targets": 0,
    }
    setattr(_ctf_native_builtins, _ctf_native_state_name, _ctf_native_state)
    _ctf_native_max_target_distance(_ctf_native_state)
    _ctf_native_install_magic_hitbox_patch(_ctf_native_state)
    _ctf_native_tick()
    _ctf_native_players, _ctf_native_robots = _ctf_native_entities()
    _ctf_native_owner = _ctf_native_timer_owner(_ctf_native_players, _ctf_native_robots)
    if _ctf_native_owner is None or not hasattr(_ctf_native_owner, "add_repeat_timer"):
        _ctf_native_log("INSTALL_FAILED no timer owner")
        return
    _ctf_native_state["timer_owner"] = _ctf_native_owner
    _ctf_native_state["timer_id"] = _ctf_native_owner.add_repeat_timer(1.0 / 120.0, _ctf_native_tick)
    _ctf_native_state["exporter_ready"] = True
    _ctf_native_write_snapshot(_ctf_native_state)
    _ctf_native_log(
        "INSTALL_OK hz=120 timer_id={!r} apply_frame_ok={} apply_frame_error={!r}".format(
            _ctf_native_state["timer_id"],
            _ctf_native_state.get("native_apply_frame_ok", False),
            _ctf_native_state.get("native_apply_frame_error", ""),
        )
    )


try:
    _ctf_native_install()
except Exception:
    _ctf_native_log("INSTALL_EXC\n" + _ctf_native_traceback.format_exc())

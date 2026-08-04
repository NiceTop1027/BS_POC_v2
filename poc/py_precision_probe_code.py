"""Read-only timing, motion, and ballistics probe for the isolated CTF game."""

import builtins as _pp_builtins
import inspect as _pp_inspect
import math as _pp_math
import time as _pp_time
import traceback as _pp_traceback


_pp_log_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_precision_probe.log"
_pp_state_name = "_ctf_precision_probe_state"


def _pp_log(value):
    with open(_pp_log_path, "a", encoding="utf-8") as _pp_handle:
        _pp_handle.write(str(value) + "\n")


def _pp_short(value, limit=1800):
    try:
        text = repr(value)
    except Exception as error:
        text = "<repr error {!r}>".format(error)
    return text[:limit] + ("..." if len(text) > limit else "")


def _pp_vec(value):
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


def _pp_describe_motion(label, value):
    if value is None:
        _pp_log(label + "=None")
        return
    tokens = ("velocity", "speed", "motion", "move", "accel", "linear", "physics", "controller")
    try:
        names = [name for name in dir(value) if any(token in name.lower() for token in tokens)]
    except Exception as error:
        _pp_log(label + ".dir_error=" + repr(error))
        return
    _pp_log(label + ".type=" + repr(type(value)) + " names=" + _pp_short(names, 9000))
    for name in names:
        try:
            member = getattr(value, name)
            if callable(member):
                try:
                    signature = _pp_inspect.signature(member)
                except Exception:
                    signature = "?"
                _pp_log(label + "." + name + " callable sig=" + str(signature))
            else:
                _pp_log(label + "." + name + "=" + _pp_short(member))
        except Exception as error:
            _pp_log(label + "." + name + " error=" + repr(error))
    for name in ("GetVelocity", "GetLinearVelocity", "GetMoveVelocity", "GetMovementVelocity", "GetSpeed"):
        try:
            method = getattr(value, name)
            result = method()
            _pp_log(label + "." + name + "()=" + _pp_short(result) + " vec=" + _pp_short(_pp_vec(result)))
        except Exception:
            pass


def _pp_attr(obj, name, default=None):
    try:
        return getattr(obj, name)
    except Exception:
        return default


def _pp_probe_ballistics(player):
    weapon = None
    try:
        weapon = player.GetCurHighPriorityWeapon()
    except Exception:
        pass
    _pp_log("weapon=" + _pp_short(weapon))
    proto = _pp_attr(weapon, "weapon_proto")
    if proto is not None:
        try:
            items = sorted(proto.items())
        except Exception:
            items = []
        _pp_log("weapon_proto=" + _pp_short(items, 16000))

    case = None
    for name in ("GetCurWeaponCase", "GetCurHighPriorityWeaponCase"):
        try:
            case = getattr(player, name)()
            if case is not None:
                break
        except Exception:
            pass
    _pp_log("weapon_case=" + _pp_short(case))
    if case is not None:
        try:
            names = [name for name in dir(case) if any(token in name.lower() for token in (
                "bullet", "projectile", "gravity", "drag", "velocity", "speed", "range", "attr", "shoot"))]
            _pp_log("weapon_case.names=" + _pp_short(names, 12000))
        except Exception:
            pass

    candidates = (
        "bullet_velocity", "bullet_gravity", "projectile_gravity", "gravity",
        "bullet_drop", "bullet_drag", "projectile_drag", "air_drag",
        "bullet_acceleration", "projectile_acceleration", "bullet_lifetime",
        "projectile_lifetime", "max_projectile_time", "damage_range",
    )
    base = dict(items) if proto is not None and items else {}
    for name in candidates:
        values = []
        try:
            values.append(("cached", player.GetWeaponAttrValueWithCache(name, base.get(name), 0.0)))
        except Exception as error:
            values.append(("cached_error", repr(error)))
        if case is not None:
            for method_name in ("GetWeaponAttrValue", "GetAttrValue"):
                try:
                    values.append((method_name, getattr(case, method_name)(name, base.get(name))))
                except Exception:
                    pass
        _pp_log("ballistic_attr {}={}".format(name, _pp_short(values)))


def _pp_finish(state, reason):
    if state.get("finished"):
        return
    state["finished"] = True
    intervals = state.get("intervals", [])
    elapsed = _pp_time.perf_counter() - state["start"]
    ordered = sorted(intervals)
    def percentile(fraction):
        if not ordered:
            return 0.0
        return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * fraction))]
    _pp_log(
        "FRAME_RESULT reason={} callbacks={} elapsed={:.6f} hz={:.3f} "
        "dt_min={:.6f} dt_p50={:.6f} dt_p95={:.6f} dt_max={:.6f}".format(
            reason, state.get("count", 0), elapsed,
            state.get("count", 0) / elapsed if elapsed > 0.0 else 0.0,
            min(intervals) if intervals else 0.0,
            percentile(0.50), percentile(0.95), max(intervals) if intervals else 0.0,
        )
    )


def _pp_frame(*args, **kwargs):
    state = getattr(_pp_builtins, _pp_state_name, None)
    if not isinstance(state, dict) or state.get("finished"):
        return
    now = _pp_time.perf_counter()
    last = state.get("last")
    if last is not None:
        state["intervals"].append(now - last)
    state["last"] = now
    state["count"] += 1
    if now - state["start"] >= 2.0:
        _pp_finish(state, "sample_complete")
        return
    try:
        import asiocore_64 as asiocore
        asiocore.call_next_frame(_pp_frame)
    except Exception as error:
        _pp_log("call_next_frame_error=" + repr(error))
        _pp_finish(state, "schedule_error")


def _pp_run():
    _pp_log("BEGIN {:.6f}".format(_pp_time.time()))
    try:
        import common.EntityManager as entity_manager
        entities = list(getattr(entity_manager.EntityManager, "_entities", {}).items())
        players = [(str(key), entity) for key, entity in entities if getattr(entity, "IsPlayerCombatAvatar", False)]
        robots = [(str(key), entity) for key, entity in entities if getattr(entity, "IsRobotCombatAvatar", False)]
        _pp_log("players={} robots={}".format(len(players), len(robots)))
        if players:
            key, player = players[0]
            _pp_log("player_key=" + key)
            _pp_describe_motion("player", player)
            for child_name in ("model", "controller", "physics", "motor", "character_controller", "scene_node"):
                _pp_describe_motion("player." + child_name, _pp_attr(player, child_name))
            _pp_probe_ballistics(player)
        if robots:
            key, robot = robots[0]
            _pp_log("robot_key=" + key)
            _pp_describe_motion("robot", robot)
            for child_name in ("model", "controller", "physics", "motor", "character_controller", "scene_node", "camera_controller"):
                _pp_describe_motion("robot." + child_name, _pp_attr(robot, child_name))

        state = {
            "start": _pp_time.perf_counter(),
            "last": None,
            "count": 0,
            "intervals": [],
            "finished": False,
        }
        setattr(_pp_builtins, _pp_state_name, state)
        import asiocore_64 as asiocore
        asiocore.call_next_frame(_pp_frame)
        _pp_log("FRAME_SCHEDULED")
    except Exception:
        _pp_log("EXCEPTION\n" + _pp_traceback.format_exc())


_pp_run()

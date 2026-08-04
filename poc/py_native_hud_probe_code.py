"""Read the engine's 3D-UI follower position without leaving a visible marker."""

import builtins as _ctf_hud_builtins
import time as _ctf_hud_time
import traceback as _ctf_hud_traceback


_ctf_hud_log_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_native_hud_probe.log"
_ctf_hud_state_name = "_ctf_native_hud_probe_state"


def _ctf_hud_log(value):
    with open(_ctf_hud_log_path, "a", encoding="utf-8") as _ctf_hud_handle:
        _ctf_hud_handle.write(str(value) + "\n")


def _ctf_hud_value(value):
    try:
        return repr(value)
    except Exception:
        return "<repr failed>"


def _ctf_hud_vec(value):
    if value is None:
        return None
    try:
        return (float(value.x), float(value.y))
    except Exception:
        pass
    try:
        return (float(value.x), float(value.y), float(value.z))
    except Exception:
        return _ctf_hud_value(value)


def _ctf_hud_call(obj, name, *args):
    try:
        return getattr(obj, name)(*args)
    except Exception as _ctf_hud_exc:
        return "<" + name + " failed: " + repr(_ctf_hud_exc) + ">"


def _ctf_hud_finish(state):
    try:
        state["owner"].cancel_timer(state["timer"])
    except Exception:
        pass
    try:
        state["mui"].RemoveFakeBoardElement(state["key"])
    except Exception as _ctf_hud_exc:
        _ctf_hud_log("remove failed=" + repr(_ctf_hud_exc))
    try:
        state["node"].release()
    except Exception:
        pass
    _ctf_hud_log("END")
    setattr(_ctf_hud_builtins, _ctf_hud_state_name, None)


def _ctf_hud_tick(*_ctf_hud_args, **_ctf_hud_kwargs):
    state = getattr(_ctf_hud_builtins, _ctf_hud_state_name, None)
    if not isinstance(state, dict):
        return
    try:
        import MCamera as _ctf_hud_camera

        node = state["node"]
        frame = _ctf_hud_camera.CaptureFrame()
        _ctf_hud_log(
            "SAMPLE {} pos={} world={} parent={} visible={} camera=({}, {}, {}, {}, {})".format(
                state["samples"],
                _ctf_hud_vec(_ctf_hud_call(node, "getPosition")),
                _ctf_hud_vec(_ctf_hud_call(node, "convertToWorldSpaceAR", state["zero"])),
                _ctf_hud_value(_ctf_hud_call(node, "getParent")),
                _ctf_hud_value(_ctf_hud_call(node, "isVisible")),
                float(frame.Yaw), float(frame.Pitch), float(frame.Fov),
                _ctf_hud_vec(frame.Position),
                _ctf_hud_time.time(),
            )
        )
        state["samples"] += 1
        if state["samples"] >= 12:
            _ctf_hud_finish(state)
    except Exception:
        _ctf_hud_log("TICK EXC\n" + _ctf_hud_traceback.format_exc())
        _ctf_hud_finish(state)


def _ctf_hud_run():
    _ctf_hud_log("BEGIN " + str(_ctf_hud_time.time()))
    previous = getattr(_ctf_hud_builtins, _ctf_hud_state_name, None)
    if isinstance(previous, dict):
        _ctf_hud_finish(previous)
    try:
        import MType as _ctf_hud_type
        import MUI as _ctf_hud_mui
        import cc as _ctf_hud_cc
        import ccui as _ctf_hud_ccui
        import common.EntityManager as _ctf_hud_em

        entities = list(getattr(_ctf_hud_em.EntityManager, "_entities", {}).values())
        owner = next((entity for entity in entities if getattr(entity, "IsPlayerCombatAvatar", False)), None)
        target = next((entity for entity in entities if getattr(entity, "IsRobotCombatAvatar", False)), None)
        if owner is None or target is None:
            _ctf_hud_log("NO_ACTIVE_PLAYER_OR_TARGET")
            return
        engine_target = getattr(getattr(target, "model", None), "model", None)
        if engine_target is None:
            _ctf_hud_log("NO_ENGINE_TARGET")
            return

        screen = _ctf_hud_mui.GetScreenSize()
        director = _ctf_hud_cc.Director.getInstance()
        _ctf_hud_log("screen={} visible_size={} origin={}".format(
            _ctf_hud_vec(screen),
            _ctf_hud_vec(director.getVisibleSize()),
            _ctf_hud_vec(director.getVisibleOrigin()),
        ))

        node = _ctf_hud_ccui.Layout.create()
        # AddFakeBoardElement0 takes ownership of its parameter node.  Keep one
        # reference solely for this read-only coordinate sample.
        node.retain()
        node.setContentSize(_ctf_hud_cc.Size(1.0, 1.0))
        node.setAnchorPoint(_ctf_hud_cc.Vec2(0.5, 0.5))
        node.setVisible(False)
        key = "ctf_native_hud_probe"
        param = _ctf_hud_mui.FakeBoardElementParam()
        param.key = key
        param.node = node
        # Bind at the model head height, while leaving the helper node hidden.
        param.bias = _ctf_hud_type.Vector3(0.0, 1.60, 0.0)
        param.bone = ""
        param.biasType = 0
        param.fovDistance = 9999.0
        param.minScale = 1.0
        param.maxScale = 1.0
        param.normalFov = True
        result = _ctf_hud_mui.AddFakeBoardElement0(param, engine_target)
        _ctf_hud_log("attached={} engine_target={}".format(result, _ctf_hud_value(engine_target)))

        state = {
            "owner": owner,
            "mui": _ctf_hud_mui,
            "key": key,
            "node": node,
            "zero": _ctf_hud_cc.Vec2(0.0, 0.0),
            "samples": 0,
        }
        setattr(_ctf_hud_builtins, _ctf_hud_state_name, state)
        state["timer"] = owner.add_repeat_timer(0.05, _ctf_hud_tick)
    except Exception:
        _ctf_hud_log("EXC\n" + _ctf_hud_traceback.format_exc())


_ctf_hud_run()

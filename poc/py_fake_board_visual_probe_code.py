import builtins as _ctf_fbv_builtins
import inspect as _ctf_fbv_inspect
import math as _ctf_fbv_math
import time as _ctf_fbv_time
import traceback as _ctf_fbv_traceback


_ctf_fbv_log_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_fake_board_visual_probe.log"
_ctf_fbv_state_name = "_ctf_fake_board_visual_state"
_ctf_fbv_key = "ctf_fake_board_visual"


def _ctf_fbv_write(value):
    with open(_ctf_fbv_log_path, "a", encoding="utf-8") as _ctf_fbv_handle:
        _ctf_fbv_handle.write(str(value) + "\n")


def _ctf_fbv_short(value, limit=1800):
    try:
        return repr(value)[:limit]
    except Exception:
        return "<repr failed>"


def _ctf_fbv_make_node(cc_module, type_module):
    _ctf_fbv_draw = None
    for _ctf_fbv_creator in (lambda: cc_module.DrawNode.create(), lambda: cc_module.DrawNode()):
        try:
            _ctf_fbv_draw = _ctf_fbv_creator()
            if _ctf_fbv_draw is not None:
                break
        except Exception as _ctf_fbv_exc:
            _ctf_fbv_write("DrawNode create fail=" + repr(_ctf_fbv_exc))
    if _ctf_fbv_draw is None:
        raise RuntimeError("cannot create DrawNode")

    _ctf_fbv_write("DrawNode=" + _ctf_fbv_short(_ctf_fbv_draw))
    _ctf_fbv_write("DrawNode methods=" + _ctf_fbv_short([_ctf_fbv_name for _ctf_fbv_name in dir(_ctf_fbv_draw) if any(_ctf_fbv_token in _ctf_fbv_name.lower() for _ctf_fbv_token in ("draw", "line", "color", "width", "zorder"))], 5000))
    try:
        _ctf_fbv_director = cc_module.Director.getInstance()
        _ctf_fbv_vec2_type = type(_ctf_fbv_director.getVisibleOrigin())
        _ctf_fbv_write("cocos_vec2_type=" + _ctf_fbv_short(_ctf_fbv_vec2_type))
        _ctf_fbv_vec2 = lambda x, y: _ctf_fbv_vec2_type(float(x), float(y))
    except Exception as _ctf_fbv_exc:
        _ctf_fbv_write("cocos Vec2 discovery fail=" + repr(_ctf_fbv_exc))
        _ctf_fbv_vec2 = lambda x, y: type_module.Vector2(float(x), float(y))
    try:
        _ctf_fbv_write("drawLine sig=" + _ctf_fbv_short(_ctf_fbv_inspect.signature(_ctf_fbv_draw.drawLine)))
    except Exception as _ctf_fbv_exc:
        _ctf_fbv_write("drawLine sig fail=" + repr(_ctf_fbv_exc))
    _ctf_fbv_a = _ctf_fbv_vec2(-78.0, -160.0)
    _ctf_fbv_b = _ctf_fbv_vec2(78.0, 160.0)
    _ctf_fbv_color = cc_module.Color4B(13, 255, 184, 255)
    try:
        _ctf_fbv_draw.setLineWidth(2.0)
    except Exception as _ctf_fbv_exc:
        _ctf_fbv_write("setLineWidth fail=" + repr(_ctf_fbv_exc))
    for _ctf_fbv_label, _ctf_fbv_args in (
        ("drawRect", (_ctf_fbv_a, _ctf_fbv_b, _ctf_fbv_color)),
        ("drawRect4", (_ctf_fbv_a, _ctf_fbv_b, None, None, _ctf_fbv_color)),
    ):
        try:
            getattr(_ctf_fbv_draw, _ctf_fbv_label.rstrip("4"))(*_ctf_fbv_args)
            _ctf_fbv_write(_ctf_fbv_label + " OK")
            return _ctf_fbv_draw
        except Exception as _ctf_fbv_exc:
            _ctf_fbv_write(_ctf_fbv_label + " fail=" + repr(_ctf_fbv_exc))
    _ctf_fbv_lines = (
        (_ctf_fbv_vec2(-78.0, -160.0), _ctf_fbv_vec2(78.0, -160.0)),
        (_ctf_fbv_vec2(78.0, -160.0), _ctf_fbv_vec2(78.0, 160.0)),
        (_ctf_fbv_vec2(78.0, 160.0), _ctf_fbv_vec2(-78.0, 160.0)),
        (_ctf_fbv_vec2(-78.0, 160.0), _ctf_fbv_vec2(-78.0, -160.0)),
    )
    _ctf_fbv_line_args = (
        lambda p1, p2: (p1, p2, _ctf_fbv_color),
        lambda p1, p2: (p1, p2, _ctf_fbv_color, 2.0),
        lambda p1, p2: (p1, p2, 2.0, _ctf_fbv_color),
        lambda p1, p2: (p1, p2),
    )
    _ctf_fbv_last_error = None
    for _ctf_fbv_make_args in _ctf_fbv_line_args:
        try:
            for _ctf_fbv_p1, _ctf_fbv_p2 in _ctf_fbv_lines:
                _ctf_fbv_draw.drawLine(*_ctf_fbv_make_args(_ctf_fbv_p1, _ctf_fbv_p2))
            _ctf_fbv_write("drawLine rectangle OK argc=" + str(len(_ctf_fbv_make_args(*_ctf_fbv_lines[0]))))
            return _ctf_fbv_draw
        except Exception as _ctf_fbv_exc:
            _ctf_fbv_last_error = _ctf_fbv_exc
            _ctf_fbv_write("drawLine variant fail=" + repr(_ctf_fbv_exc))
    raise RuntimeError("DrawNode.drawLine failed: " + repr(_ctf_fbv_last_error))


def _ctf_fbv_run():
    _ctf_fbv_write("BEGIN " + str(_ctf_fbv_time.time()))
    try:
        import MType as _ctf_fbv_type
        import MUI as _ctf_fbv_mui
        import cc as _ctf_fbv_cc
        import common.EntityManager as _ctf_fbv_em

        try:
            _ctf_fbv_mui.RemoveFakeBoardElement(_ctf_fbv_key)
        except Exception:
            pass
        _ctf_fbv_entities = getattr(_ctf_fbv_em.EntityManager, "_entities", {})
        _ctf_fbv_players = [
            _ctf_fbv_entity for _ctf_fbv_entity in _ctf_fbv_entities.values()
            if getattr(_ctf_fbv_entity, "IsPlayerCombatAvatar", False)
        ]
        _ctf_fbv_player = _ctf_fbv_players[0] if _ctf_fbv_players else None
        _ctf_fbv_player_pos = getattr(_ctf_fbv_player, "position", None)
        _ctf_fbv_robots = [
            _ctf_fbv_entity for _ctf_fbv_entity in _ctf_fbv_entities.values()
            if getattr(_ctf_fbv_entity, "IsRobotCombatAvatar", False)
        ]
        def _ctf_fbv_distance(entity):
            try:
                return _ctf_fbv_math.sqrt(sum((float(entity.position[i]) - float(_ctf_fbv_player_pos[i])) ** 2 for i in range(3)))
            except Exception:
                return 999999.0
        _ctf_fbv_robots.sort(key=_ctf_fbv_distance)
        if not _ctf_fbv_robots:
            raise RuntimeError("no robot")
        _ctf_fbv_robot = _ctf_fbv_robots[0]
        _ctf_fbv_bound = _ctf_fbv_robot.model.GetWorldBound()
        _ctf_fbv_height = float(_ctf_fbv_bound.max.y - _ctf_fbv_bound.min.y)
        _ctf_fbv_node = _ctf_fbv_make_node(_ctf_fbv_cc, _ctf_fbv_type)
        _ctf_fbv_param = _ctf_fbv_mui.FakeBoardElementParam()
        _ctf_fbv_param.key = _ctf_fbv_key
        _ctf_fbv_param.node = _ctf_fbv_node
        _ctf_fbv_param.bias = _ctf_fbv_type.Vector3(0.0, _ctf_fbv_height * 0.5, 0.0)
        _ctf_fbv_param.bone = ""
        _ctf_fbv_param.biasType = 0
        _ctf_fbv_param.fovDistance = 25.0
        _ctf_fbv_param.minScale = 0.10
        _ctf_fbv_param.maxScale = 1.0
        _ctf_fbv_param.normalFov = True
        _ctf_fbv_result = _ctf_fbv_mui.AddFakeBoardElement0(_ctf_fbv_param, _ctf_fbv_robot.model.model)
        _ctf_fbv_builtins.__dict__[_ctf_fbv_state_name] = {
            "node": _ctf_fbv_node,
            "robot": _ctf_fbv_robot,
            "key": _ctf_fbv_key,
        }
        _ctf_fbv_write(
            "ADD_OK result=" + _ctf_fbv_short(_ctf_fbv_result)
            + " robot=" + _ctf_fbv_short(_ctf_fbv_robot)
            + " distance=" + str(_ctf_fbv_distance(_ctf_fbv_robot))
            + " height=" + str(_ctf_fbv_height)
        )
    except Exception:
        _ctf_fbv_write("EXC\n" + _ctf_fbv_traceback.format_exc())
    finally:
        _ctf_fbv_write("END")


_ctf_fbv_run()

import builtins as _ctf_fbv4_builtins
import math as _ctf_fbv4_math
import time as _ctf_fbv4_time
import traceback as _ctf_fbv4_traceback


_ctf_fbv4_log_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_fake_board_visual_probe4.log"
_ctf_fbv4_key = "ctf_fake_board_visual4"
_ctf_fbv4_state_name = "_ctf_fake_board_visual4_state"


def _ctf_fbv4_write(value):
    with open(_ctf_fbv4_log_path, "a", encoding="utf-8") as _ctf_fbv4_handle:
        _ctf_fbv4_handle.write(str(value) + "\n")


def _ctf_fbv4_short(value, limit=1500):
    try:
        return repr(value)[:limit]
    except Exception:
        return "<repr failed>"


def _ctf_fbv4_try(label, func, *args):
    try:
        value = func(*args)
        _ctf_fbv4_write(label + " OK " + _ctf_fbv4_short(value))
        return value
    except Exception as exc:
        _ctf_fbv4_write(label + " FAIL " + repr(exc))
        return None


def _ctf_fbv4_run():
    _ctf_fbv4_write("BEGIN " + str(_ctf_fbv4_time.time()))
    try:
        import MType as _ctf_fbv4_type
        import MUI as _ctf_fbv4_mui
        import cc as _ctf_fbv4_cc
        import ccui as _ctf_fbv4_ccui
        import common.EntityManager as _ctf_fbv4_em

        _ctf_fbv4_try("remove old", _ctf_fbv4_mui.RemoveFakeBoardElement, _ctf_fbv4_key)
        _ctf_fbv4_entities = getattr(_ctf_fbv4_em.EntityManager, "_entities", {})
        _ctf_fbv4_players = [
            _ctf_fbv4_entity for _ctf_fbv4_entity in _ctf_fbv4_entities.values()
            if getattr(_ctf_fbv4_entity, "IsPlayerCombatAvatar", False)
        ]
        _ctf_fbv4_player_pos = getattr(_ctf_fbv4_players[0], "position", None) if _ctf_fbv4_players else None
        _ctf_fbv4_robots = [
            _ctf_fbv4_entity for _ctf_fbv4_entity in _ctf_fbv4_entities.values()
            if getattr(_ctf_fbv4_entity, "IsRobotCombatAvatar", False)
        ]

        def _ctf_fbv4_dist(entity):
            try:
                return _ctf_fbv4_math.sqrt(sum((float(entity.position[i]) - float(_ctf_fbv4_player_pos[i])) ** 2 for i in range(3)))
            except Exception:
                return 999999.0

        _ctf_fbv4_robots.sort(key=_ctf_fbv4_dist)
        if not _ctf_fbv4_robots:
            raise RuntimeError("no robot")
        _ctf_fbv4_robot = _ctf_fbv4_robots[0]
        _ctf_fbv4_bound = _ctf_fbv4_robot.model.GetWorldBound()
        _ctf_fbv4_height = float(_ctf_fbv4_bound.max.y - _ctf_fbv4_bound.min.y)

        _ctf_fbv4_director = _ctf_fbv4_cc.Director.getInstance()
        _ctf_fbv4_size_type = type(_ctf_fbv4_director.getWinSize())
        _ctf_fbv4_vec2_type = type(_ctf_fbv4_director.getVisibleOrigin())
        _ctf_fbv4_size = _ctf_fbv4_size_type(420.0, 840.0)
        _ctf_fbv4_anchor = _ctf_fbv4_vec2_type(0.5, 0.5)
        _ctf_fbv4_layout = _ctf_fbv4_ccui.Layout.create()
        _ctf_fbv4_try("layout.content", _ctf_fbv4_layout.setContentSize, _ctf_fbv4_size)
        _ctf_fbv4_try("layout.anchor", _ctf_fbv4_layout.setAnchorPoint, _ctf_fbv4_anchor)
        _ctf_fbv4_try("layout.background type", _ctf_fbv4_layout.setBackGroundColorType, _ctf_fbv4_ccui.LAYOUT_BACKGROUNDCOLORTYPE_SOLID)
        _ctf_fbv4_try("layout.background color", _ctf_fbv4_layout.setBackGroundColor, _ctf_fbv4_cc.Color3B(255, 0, 255))
        _ctf_fbv4_try("layout.background alpha", _ctf_fbv4_layout.setBackGroundColorOpacity, 220)
        _ctf_fbv4_try("layout.visible", _ctf_fbv4_layout.setVisible, True)
        _ctf_fbv4_try("layout.scale", _ctf_fbv4_layout.setScale, 1.0)
        _ctf_fbv4_write("layout.size=" + _ctf_fbv4_short(_ctf_fbv4_layout.getContentSize()))

        _ctf_fbv4_param = _ctf_fbv4_mui.FakeBoardElementParam()
        _ctf_fbv4_param.key = _ctf_fbv4_key
        _ctf_fbv4_param.node = _ctf_fbv4_layout
        _ctf_fbv4_param.bias = _ctf_fbv4_type.Vector3(0.0, _ctf_fbv4_height * 0.5, 0.0)
        _ctf_fbv4_param.biasType = 0
        _ctf_fbv4_param.bone = ""
        _ctf_fbv4_param.fovDistance = 9999.0
        _ctf_fbv4_param.minScale = 0.10
        _ctf_fbv4_param.maxScale = 1.0
        _ctf_fbv4_param.normalFov = True
        _ctf_fbv4_result = _ctf_fbv4_mui.AddFakeBoardElement0(_ctf_fbv4_param, _ctf_fbv4_robot.model.model)
        _ctf_fbv4_builtins.__dict__[_ctf_fbv4_state_name] = {
            "node": _ctf_fbv4_layout,
            "robot": _ctf_fbv4_robot,
            "key": _ctf_fbv4_key,
        }
        _ctf_fbv4_write("ADD result=" + _ctf_fbv4_short(_ctf_fbv4_result) + " robot=" + _ctf_fbv4_short(_ctf_fbv4_robot) + " dist=" + str(_ctf_fbv4_dist(_ctf_fbv4_robot)) + " height=" + str(_ctf_fbv4_height))
    except Exception:
        _ctf_fbv4_write("EXC\n" + _ctf_fbv4_traceback.format_exc())
    finally:
        _ctf_fbv4_write("END")


_ctf_fbv4_run()

import time as _ctf_w2h3_time
import traceback as _ctf_w2h3_traceback


_ctf_w2h3_log_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_world_to_hud_probe3.log"


def _ctf_w2h3_write(value):
    with open(_ctf_w2h3_log_path, "a", encoding="utf-8") as _ctf_w2h3_handle:
        _ctf_w2h3_handle.write(str(value) + "\n")


def _ctf_w2h3_short(value, limit=1800):
    try:
        return repr(value)[:limit]
    except Exception:
        return "<repr failed>"


def _ctf_w2h3_xyz(value):
    try:
        return (float(value.x), float(value.y), float(value.z))
    except Exception:
        return None


def _ctf_w2h3_try(label, function, *args):
    try:
        _ctf_w2h3_value = function(*args)
        _ctf_w2h3_write(label + " => " + _ctf_w2h3_short(_ctf_w2h3_value) + " xyz=" + _ctf_w2h3_short(_ctf_w2h3_xyz(_ctf_w2h3_value)))
        return _ctf_w2h3_value
    except Exception as _ctf_w2h3_exc:
        _ctf_w2h3_write(label + " fail=" + repr(_ctf_w2h3_exc))
        return None


def _ctf_w2h3_children(label, node, depth=0):
    if node is None or depth > 2:
        return
    try:
        _ctf_w2h3_children_value = list(node.getChildren() or [])
    except Exception:
        return
    _ctf_w2h3_write(label + " children=" + str(len(_ctf_w2h3_children_value)))
    for _ctf_w2h3_index, _ctf_w2h3_child in enumerate(_ctf_w2h3_children_value[:40]):
        try:
            _ctf_w2h3_name = _ctf_w2h3_child.getName()
        except Exception:
            _ctf_w2h3_name = ""
        _ctf_w2h3_write(label + "/" + str(_ctf_w2h3_index) + " type=" + _ctf_w2h3_short(type(_ctf_w2h3_child)) + " name=" + _ctf_w2h3_short(_ctf_w2h3_name))
        _ctf_w2h3_children(label + "/" + str(_ctf_w2h3_index), _ctf_w2h3_child, depth + 1)


def _ctf_w2h3_make_layout(ccui_module):
    for _ctf_w2h3_class_name in ("Layout", "Widget", "ImageView"):
        _ctf_w2h3_class = getattr(ccui_module, _ctf_w2h3_class_name, None)
        if _ctf_w2h3_class is None:
            continue
        for _ctf_w2h3_method_name in ("create", "Create"):
            try:
                _ctf_w2h3_node = getattr(_ctf_w2h3_class, _ctf_w2h3_method_name)()
                if _ctf_w2h3_node is not None:
                    _ctf_w2h3_write("created " + _ctf_w2h3_class_name + " via " + _ctf_w2h3_method_name + " -> " + _ctf_w2h3_short(_ctf_w2h3_node))
                    return _ctf_w2h3_node
            except Exception as _ctf_w2h3_exc:
                _ctf_w2h3_write("create " + _ctf_w2h3_class_name + "." + _ctf_w2h3_method_name + " fail=" + repr(_ctf_w2h3_exc))
    return None


def _ctf_w2h3_run():
    _ctf_w2h3_write("BEGIN " + str(_ctf_w2h3_time.time()))
    try:
        import MRender as _ctf_w2h3_render
        import MType as _ctf_w2h3_type
        import MUI as _ctf_w2h3_mui
        import cc as _ctf_w2h3_cc
        import ccui as _ctf_w2h3_ccui
        import common.EntityManager as _ctf_w2h3_em

        _ctf_w2h3_write("cc.names=" + _ctf_w2h3_short([_ctf_w2h3_name for _ctf_w2h3_name in dir(_ctf_w2h3_cc) if any(_ctf_w2h3_token in _ctf_w2h3_name.lower() for _ctf_w2h3_token in ("draw", "layer", "node", "color", "sprite", "label"))], 8000))
        _ctf_w2h3_write("ccui.names=" + _ctf_w2h3_short([_ctf_w2h3_name for _ctf_w2h3_name in dir(_ctf_w2h3_ccui) if any(_ctf_w2h3_token in _ctf_w2h3_name.lower() for _ctf_w2h3_token in ("layout", "image", "widget", "button", "text", "panel"))], 8000))
        _ctf_w2h3_director = _ctf_w2h3_cc.Director.getInstance()
        _ctf_w2h3_scene = _ctf_w2h3_director.getRunningScene()
        _ctf_w2h3_children("scene", _ctf_w2h3_scene)

        _ctf_w2h3_entities = getattr(_ctf_w2h3_em.EntityManager, "_entities", {})
        _ctf_w2h3_players = [
            _ctf_w2h3_entity for _ctf_w2h3_entity in _ctf_w2h3_entities.values()
            if getattr(_ctf_w2h3_entity, "IsPlayerCombatAvatar", False)
        ]
        _ctf_w2h3_player = _ctf_w2h3_players[0] if _ctf_w2h3_players else None
        _ctf_w2h3_player_pos = getattr(_ctf_w2h3_player, "position", None)
        _ctf_w2h3_robots = [
            _ctf_w2h3_entity for _ctf_w2h3_entity in _ctf_w2h3_entities.values()
            if getattr(_ctf_w2h3_entity, "IsRobotCombatAvatar", False)
        ]
        def _ctf_w2h3_dist(entity):
            try:
                _ctf_w2h3_position = entity.position
                return sum((float(_ctf_w2h3_position[i]) - float(_ctf_w2h3_player_pos[i])) ** 2 for i in range(3))
            except Exception:
                return 999999.0
        _ctf_w2h3_robots.sort(key=_ctf_w2h3_dist)
        _ctf_w2h3_write("player_pos=" + _ctf_w2h3_short(_ctf_w2h3_player_pos) + " robots=" + str(len(_ctf_w2h3_robots)))
        for _ctf_w2h3_index, _ctf_w2h3_robot in enumerate(_ctf_w2h3_robots[:3]):
            _ctf_w2h3_bound = _ctf_w2h3_robot.model.GetWorldBound()
            _ctf_w2h3_write("robot[" + str(_ctf_w2h3_index) + "] pos=" + _ctf_w2h3_short(_ctf_w2h3_robot.position) + " bound=" + _ctf_w2h3_short(_ctf_w2h3_bound))
            for _ctf_w2h3_bound_name in ("min", "max"):
                _ctf_w2h3_point = getattr(_ctf_w2h3_bound, _ctf_w2h3_bound_name)
                for _ctf_w2h3_mode in (0, 1):
                    _ctf_w2h3_hud = _ctf_w2h3_try(
                        "robot[" + str(_ctf_w2h3_index) + "]." + _ctf_w2h3_bound_name + ".w2h(" + str(_ctf_w2h3_mode) + ")",
                        _ctf_w2h3_render.TransformFromWorldToHudWorld,
                        _ctf_w2h3_point,
                        _ctf_w2h3_mode,
                    )
                    if _ctf_w2h3_hud is not None:
                        _ctf_w2h3_try(
                            "robot[" + str(_ctf_w2h3_index) + "]." + _ctf_w2h3_bound_name + ".h2w(" + str(_ctf_w2h3_mode) + ")",
                            _ctf_w2h3_render.TransformFromHudWorldToWorld,
                            _ctf_w2h3_hud,
                            _ctf_w2h3_mode,
                        )

        if _ctf_w2h3_robots:
            _ctf_w2h3_node = _ctf_w2h3_make_layout(_ctf_w2h3_ccui)
            _ctf_w2h3_write("board_node=" + _ctf_w2h3_short(_ctf_w2h3_node))
            if _ctf_w2h3_node is not None:
                try:
                    _ctf_w2h3_node.setContentSize((8, 8))
                except Exception:
                    pass
                _ctf_w2h3_param = _ctf_w2h3_mui.FakeBoardElementParam()
                _ctf_w2h3_param.key = "ctf_w2h3_empty_board"
                _ctf_w2h3_param.node = _ctf_w2h3_node
                _ctf_w2h3_param.bias = _ctf_w2h3_type.Vector3(0.0, 0.0, 0.0)
                _ctf_w2h3_param.minScale = 1.0
                _ctf_w2h3_param.maxScale = 1.0
                _ctf_w2h3_param.fovDistance = 9999.0
                _ctf_w2h3_try("AddFakeBoardElement0", _ctf_w2h3_mui.AddFakeBoardElement0, _ctf_w2h3_robots[0], _ctf_w2h3_param)
                _ctf_w2h3_try("RemoveFakeBoardElement", _ctf_w2h3_mui.RemoveFakeBoardElement, "ctf_w2h3_empty_board")
    except Exception:
        _ctf_w2h3_write("EXC\n" + _ctf_w2h3_traceback.format_exc())
    finally:
        _ctf_w2h3_write("END")


_ctf_w2h3_run()

import time as _ctf_fb_time
import traceback as _ctf_fb_traceback


_ctf_fb_log_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_fake_board_probe.log"


def _ctf_fb_write(value):
    with open(_ctf_fb_log_path, "a", encoding="utf-8") as _ctf_fb_handle:
        _ctf_fb_handle.write(str(value) + "\n")


def _ctf_fb_short(value, limit=1600):
    try:
        return repr(value)[:limit]
    except Exception:
        return "<repr failed>"


def _ctf_fb_try(label, function, *args):
    try:
        _ctf_fb_result = function(*args)
        _ctf_fb_write(label + " => " + _ctf_fb_short(_ctf_fb_result))
        return True, _ctf_fb_result
    except Exception as _ctf_fb_exc:
        _ctf_fb_write(label + " fail=" + repr(_ctf_fb_exc))
        return False, None


def _ctf_fb_layout(ccui_module):
    _ctf_fb_layout_class = ccui_module.Layout
    _ctf_fb_node = _ctf_fb_layout_class.create()
    try:
        _ctf_fb_node.setContentSize((8.0, 8.0))
        _ctf_fb_node.setAnchorPoint((0.5, 0.5))
        _ctf_fb_node.setVisible(False)
    except Exception as _ctf_fb_exc:
        _ctf_fb_write("layout setup fail=" + repr(_ctf_fb_exc))
    return _ctf_fb_node


def _ctf_fb_param(mui_module, type_module, node, key):
    _ctf_fb_value = mui_module.FakeBoardElementParam()
    _ctf_fb_value.key = key
    _ctf_fb_value.node = node
    _ctf_fb_value.bias = type_module.Vector3(0.0, 0.0, 0.0)
    _ctf_fb_value.bone = "Root"
    _ctf_fb_value.biasType = 0
    _ctf_fb_value.fovDistance = 9999.0
    _ctf_fb_value.minScale = 1.0
    _ctf_fb_value.maxScale = 1.0
    _ctf_fb_value.normalFov = True
    return _ctf_fb_value


def _ctf_fb_run():
    _ctf_fb_write("BEGIN " + str(_ctf_fb_time.time()))
    try:
        import MType as _ctf_fb_type
        import MUI as _ctf_fb_mui
        import ccui as _ctf_fb_ccui
        import common.EntityManager as _ctf_fb_em

        _ctf_fb_robots = [
            _ctf_fb_entity for _ctf_fb_entity in getattr(_ctf_fb_em.EntityManager, "_entities", {}).values()
            if getattr(_ctf_fb_entity, "IsRobotCombatAvatar", False)
        ]
        if not _ctf_fb_robots:
            _ctf_fb_write("no robot")
            return
        _ctf_fb_robot = _ctf_fb_robots[0]
        _ctf_fb_write("robot=" + _ctf_fb_short(_ctf_fb_robot) + " position=" + _ctf_fb_short(getattr(_ctf_fb_robot, "position", None)))

        _ctf_fb_node = _ctf_fb_layout(_ctf_fb_ccui)
        _ctf_fb_write("node=" + _ctf_fb_short(_ctf_fb_node))
        _ctf_fb_variants = (
            ("AddFakeBoardElement0(param, robot)", _ctf_fb_mui.AddFakeBoardElement0, (_ctf_fb_param(_ctf_fb_mui, _ctf_fb_type, _ctf_fb_node, "ctf_fb_p0"), _ctf_fb_robot), "ctf_fb_p0"),
            ("AddFakeBoardElementWithBone(param, robot, Root)", _ctf_fb_mui.AddFakeBoardElementWithBone, (_ctf_fb_param(_ctf_fb_mui, _ctf_fb_type, _ctf_fb_node, "ctf_fb_p1"), _ctf_fb_robot, "Root"), "ctf_fb_p1"),
            ("AddFakeBoardElementWithBone(param, robot, Head)", _ctf_fb_mui.AddFakeBoardElementWithBone, (_ctf_fb_param(_ctf_fb_mui, _ctf_fb_type, _ctf_fb_node, "ctf_fb_p2"), _ctf_fb_robot, "Head"), "ctf_fb_p2"),
        )
        for _ctf_fb_label, _ctf_fb_function, _ctf_fb_args, _ctf_fb_key in _ctf_fb_variants:
            _ctf_fb_ok, _ctf_fb_result = _ctf_fb_try(_ctf_fb_label, _ctf_fb_function, *_ctf_fb_args)
            if _ctf_fb_ok:
                _ctf_fb_try("RemoveFakeBoardElement(" + _ctf_fb_key + ")", _ctf_fb_mui.RemoveFakeBoardElement, _ctf_fb_key)
                break
    except Exception:
        _ctf_fb_write("EXC\n" + _ctf_fb_traceback.format_exc())
    finally:
        _ctf_fb_write("END")


_ctf_fb_run()

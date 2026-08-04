import time as _ctf_fb2_time
import traceback as _ctf_fb2_traceback


_ctf_fb2_log_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_fake_board_probe2.log"


def _ctf_fb2_write(value):
    with open(_ctf_fb2_log_path, "a", encoding="utf-8") as _ctf_fb2_handle:
        _ctf_fb2_handle.write(str(value) + "\n")


def _ctf_fb2_short(value, limit=1800):
    try:
        return repr(value)[:limit]
    except Exception:
        return "<repr failed>"


def _ctf_fb2_try(label, function, *args):
    try:
        _ctf_fb2_result = function(*args)
        _ctf_fb2_write(label + " => " + _ctf_fb2_short(_ctf_fb2_result))
        return True, _ctf_fb2_result
    except Exception as _ctf_fb2_exc:
        _ctf_fb2_write(label + " fail=" + repr(_ctf_fb2_exc))
        return False, None


def _ctf_fb2_get(root, path):
    _ctf_fb2_value = root
    for _ctf_fb2_part in path.split("."):
        _ctf_fb2_value = getattr(_ctf_fb2_value, _ctf_fb2_part)
    return _ctf_fb2_value


def _ctf_fb2_new_param(mui_module, type_module, ccui_module, key):
    _ctf_fb2_node = ccui_module.Layout.create()
    _ctf_fb2_value = mui_module.FakeBoardElementParam()
    _ctf_fb2_value.key = key
    _ctf_fb2_value.node = _ctf_fb2_node
    _ctf_fb2_value.bias = type_module.Vector3(0.0, 0.94, 0.0)
    _ctf_fb2_value.bone = ""
    _ctf_fb2_value.biasType = 0
    _ctf_fb2_value.fovDistance = 25.0
    _ctf_fb2_value.minScale = 1.0
    _ctf_fb2_value.maxScale = 1.0
    _ctf_fb2_value.normalFov = True
    return _ctf_fb2_value


def _ctf_fb2_run():
    _ctf_fb2_write("BEGIN " + str(_ctf_fb2_time.time()))
    try:
        import MType as _ctf_fb2_type
        import MUI as _ctf_fb2_mui
        import ccui as _ctf_fb2_ccui
        import common.EntityManager as _ctf_fb2_em

        _ctf_fb2_robot = next(
            (_ctf_fb2_entity for _ctf_fb2_entity in getattr(_ctf_fb2_em.EntityManager, "_entities", {}).values()
             if getattr(_ctf_fb2_entity, "IsRobotCombatAvatar", False)),
            None,
        )
        if _ctf_fb2_robot is None:
            _ctf_fb2_write("no robot")
            return
        _ctf_fb2_paths = (
            "model",
            "model.model",
            "toplogo",
            "toplogo.scenenode_entity",
            "recon_drone_frame_top_logo.scene_node",
            "recon_drone_frame_top_logo.scene_node.scenenode_entity",
            "hand_model",
            "model.follower_model",
        )
        for _ctf_fb2_index, _ctf_fb2_path in enumerate(_ctf_fb2_paths):
            try:
                _ctf_fb2_candidate = _ctf_fb2_get(_ctf_fb2_robot, _ctf_fb2_path)
                _ctf_fb2_write("candidate " + _ctf_fb2_path + " type=" + _ctf_fb2_short(type(_ctf_fb2_candidate)) + " repr=" + _ctf_fb2_short(_ctf_fb2_candidate))
            except Exception as _ctf_fb2_exc:
                _ctf_fb2_write("candidate " + _ctf_fb2_path + " fail=" + repr(_ctf_fb2_exc))
                continue
            _ctf_fb2_key = "ctf_fb2_" + str(_ctf_fb2_index)
            _ctf_fb2_param = _ctf_fb2_new_param(_ctf_fb2_mui, _ctf_fb2_type, _ctf_fb2_ccui, _ctf_fb2_key)
            _ctf_fb2_ok, _ctf_fb2_result = _ctf_fb2_try(
                "AddFakeBoardElement0(" + _ctf_fb2_path + ")",
                _ctf_fb2_mui.AddFakeBoardElement0,
                _ctf_fb2_param,
                _ctf_fb2_candidate,
            )
            if _ctf_fb2_ok:
                _ctf_fb2_try("RemoveFakeBoardElement(" + _ctf_fb2_key + ")", _ctf_fb2_mui.RemoveFakeBoardElement, _ctf_fb2_key)
                break
    except Exception:
        _ctf_fb2_write("EXC\n" + _ctf_fb2_traceback.format_exc())
    finally:
        _ctf_fb2_write("END")


_ctf_fb2_run()

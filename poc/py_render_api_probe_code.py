import dis as _ctf_rap_dis
import io as _ctf_rap_io
import sys as _ctf_rap_sys
import time as _ctf_rap_time
import traceback as _ctf_rap_traceback


_ctf_rap_log_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_render_api_probe.log"


def _ctf_rap_write(value):
    with open(_ctf_rap_log_path, "a", encoding="utf-8") as _ctf_rap_handle:
        _ctf_rap_handle.write(str(value) + "\n")


def _ctf_rap_short(value, limit=3000):
    try:
        return repr(value)[:limit]
    except Exception:
        return "<repr failed>"


def _ctf_rap_code_hits():
    _ctf_rap_tokens = {
        "AddFakeBoardElement",
        "CreateScreenText",
        "TransformFromWorldToHudWorld",
        "TransformFromHudWorldToWorld",
        "WorldToScreen",
        "ScreenToWorld",
    }
    _ctf_rap_seen = set()
    _ctf_rap_hits = []
    for _ctf_rap_module_name, _ctf_rap_module in list(_ctf_rap_sys.modules.items()):
        if _ctf_rap_module is None:
            continue
        try:
            _ctf_rap_members = vars(_ctf_rap_module).items()
        except Exception:
            continue
        for _ctf_rap_member_name, _ctf_rap_value in list(_ctf_rap_members):
            _ctf_rap_values = [(_ctf_rap_member_name, _ctf_rap_value)]
            if isinstance(_ctf_rap_value, type):
                try:
                    _ctf_rap_values.extend((str(_ctf_rap_member_name) + "." + str(_ctf_rap_name), _ctf_rap_method) for _ctf_rap_name, _ctf_rap_method in vars(_ctf_rap_value).items())
                except Exception:
                    pass
            for _ctf_rap_name, _ctf_rap_candidate in _ctf_rap_values:
                _ctf_rap_code = getattr(_ctf_rap_candidate, "__code__", None)
                if _ctf_rap_code is None or id(_ctf_rap_code) in _ctf_rap_seen:
                    continue
                _ctf_rap_seen.add(id(_ctf_rap_code))
                _ctf_rap_names = set(getattr(_ctf_rap_code, "co_names", ()))
                _ctf_rap_found = sorted(_ctf_rap_names.intersection(_ctf_rap_tokens))
                if not _ctf_rap_found:
                    continue
                _ctf_rap_hits.append((_ctf_rap_module_name, str(_ctf_rap_name), _ctf_rap_found, _ctf_rap_candidate))
    _ctf_rap_write("CODE_HITS=" + str(len(_ctf_rap_hits)))
    for _ctf_rap_module_name, _ctf_rap_name, _ctf_rap_found, _ctf_rap_candidate in _ctf_rap_hits[:120]:
        _ctf_rap_stream = _ctf_rap_io.StringIO()
        try:
            _ctf_rap_dis.dis(_ctf_rap_candidate, file=_ctf_rap_stream)
            _ctf_rap_body = _ctf_rap_stream.getvalue()[:6000]
        except Exception as _ctf_rap_exc:
            _ctf_rap_body = repr(_ctf_rap_exc)
        _ctf_rap_write("HIT " + _ctf_rap_module_name + "." + _ctf_rap_name + " names=" + repr(_ctf_rap_found) + "\n" + _ctf_rap_body)


def _ctf_rap_run():
    _ctf_rap_write("BEGIN " + str(_ctf_rap_time.time()))
    try:
        import MRender as _ctf_rap_render
        import common.EntityManager as _ctf_rap_em
        _ctf_rap_write("MRender=" + _ctf_rap_short([_ctf_rap_name for _ctf_rap_name in dir(_ctf_rap_render) if not _ctf_rap_name.startswith("__")], 12000))
        _ctf_rap_entities = getattr(_ctf_rap_em.EntityManager, "_entities", {})
        _ctf_rap_players = [
            _ctf_rap_entity for _ctf_rap_entity in _ctf_rap_entities.values()
            if getattr(_ctf_rap_entity, "IsPlayerCombatAvatar", False)
        ]
        _ctf_rap_robots = [
            _ctf_rap_entity for _ctf_rap_entity in _ctf_rap_entities.values()
            if getattr(_ctf_rap_entity, "IsRobotCombatAvatar", False)
        ]
        for _ctf_rap_label, _ctf_rap_entity in (("player", _ctf_rap_players[0] if _ctf_rap_players else None), ("robot", _ctf_rap_robots[0] if _ctf_rap_robots else None)):
            if _ctf_rap_entity is None:
                continue
            _ctf_rap_names = [
                _ctf_rap_name for _ctf_rap_name in dir(_ctf_rap_entity)
                if any(_ctf_rap_token in _ctf_rap_name.lower() for _ctf_rap_token in ("camera", "scene", "model", "node", "render", "screen", "world", "view", "matrix"))
            ]
            _ctf_rap_write(_ctf_rap_label + ".type=" + _ctf_rap_short(type(_ctf_rap_entity)) + " names=" + _ctf_rap_short(_ctf_rap_names, 12000))
            for _ctf_rap_name in _ctf_rap_names[:160]:
                try:
                    _ctf_rap_value = getattr(_ctf_rap_entity, _ctf_rap_name)
                    if callable(_ctf_rap_value):
                        continue
                    _ctf_rap_write(_ctf_rap_label + "." + _ctf_rap_name + "=" + _ctf_rap_short(_ctf_rap_value))
                except Exception:
                    pass

        _ctf_rap_camera_modules = [
            (_ctf_rap_name, _ctf_rap_module) for _ctf_rap_name, _ctf_rap_module in list(_ctf_rap_sys.modules.items())
            if _ctf_rap_module is not None and "camera" in _ctf_rap_name.lower()
        ]
        _ctf_rap_write("CAMERA_MODULES=" + _ctf_rap_short([_ctf_rap_name for _ctf_rap_name, _ctf_rap_module in _ctf_rap_camera_modules], 12000))
        for _ctf_rap_module_name, _ctf_rap_module in _ctf_rap_camera_modules[:80]:
            try:
                _ctf_rap_module_names = [
                    _ctf_rap_name for _ctf_rap_name in vars(_ctf_rap_module)
                    if any(_ctf_rap_token in _ctf_rap_name.lower() for _ctf_rap_token in ("camera", "screen", "world", "project", "matrix", "render"))
                ]
                _ctf_rap_write("CAMERA " + _ctf_rap_module_name + " names=" + _ctf_rap_short(_ctf_rap_module_names, 8000))
            except Exception:
                pass
        _ctf_rap_code_hits()
    except Exception:
        _ctf_rap_write("EXC\n" + _ctf_rap_traceback.format_exc())
    finally:
        _ctf_rap_write("END")


_ctf_rap_run()

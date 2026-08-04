"""Read-only discovery of the local CTF engine raycast API."""

import inspect as _ctf_vp_inspect
import sys as _ctf_vp_sys
import gc as _ctf_vp_gc
import traceback as _ctf_vp_traceback


_ctf_vp_log_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_visibility_probe.log"


def _ctf_vp_log(message):
    with open(_ctf_vp_log_path, "a", encoding="utf-8") as _ctf_vp_handle:
        _ctf_vp_handle.write(str(message) + "\n")


try:
    _ctf_vp_module_names = [
        name for name in _ctf_vp_sys.modules
        if any(token in name.lower() for token in ("space", "physics", "ray", "scene", "world"))
    ]
    _ctf_vp_log("loaded_modules=" + repr(_ctf_vp_module_names[:240]))
    for _ctf_vp_loaded_name in _ctf_vp_module_names:
        _ctf_vp_loaded_module = _ctf_vp_sys.modules.get(_ctf_vp_loaded_name)
        if _ctf_vp_loaded_module is None:
            continue
        _ctf_vp_matches = [
            name for name in dir(_ctf_vp_loaded_module)
            if any(token in name.lower() for token in ("ray", "trace", "physics", "space"))
        ]
        if _ctf_vp_matches:
            _ctf_vp_log("loaded {} matches={}".format(_ctf_vp_loaded_name, _ctf_vp_matches[:120]))
    for _ctf_vp_module_name in ("Space", "Physics", "MPhysics", "MEngine"):
        try:
            _ctf_vp_module = __import__(_ctf_vp_module_name)
        except Exception as _ctf_vp_error:
            _ctf_vp_log("{} import ERROR={!r}".format(_ctf_vp_module_name, _ctf_vp_error))
            continue
        _ctf_vp_log("{} type={}".format(_ctf_vp_module_name, type(_ctf_vp_module)))
        for _ctf_vp_name in dir(_ctf_vp_module):
            if not any(_ctf_vp_token in _ctf_vp_name.lower() for _ctf_vp_token in ("ray", "trace", "physics", "space")):
                continue
            _ctf_vp_value = getattr(_ctf_vp_module, _ctf_vp_name)
            if not callable(_ctf_vp_value):
                continue
            try:
                _ctf_vp_signature = _ctf_vp_inspect.signature(_ctf_vp_value)
            except Exception as _ctf_vp_error:
                _ctf_vp_signature = "ERROR={!r}".format(_ctf_vp_error)
            _ctf_vp_log("{}.{} sig={} doc={!r} repr={!r}".format(
                _ctf_vp_module_name,
                _ctf_vp_name,
                _ctf_vp_signature,
                getattr(_ctf_vp_value, "__doc__", None),
                _ctf_vp_value,
            ))

    from gclient.framework.entities import space as _ctf_vp_space_module
    _ctf_vp_space_class = getattr(_ctf_vp_space_module, "Space", None)
    _ctf_vp_log("SpaceClass={}".format(_ctf_vp_space_class))
    for _ctf_vp_name in dir(_ctf_vp_space_class):
        if not any(token in _ctf_vp_name.lower() for token in ("ray", "trace", "physics", "space")):
            continue
        _ctf_vp_value = getattr(_ctf_vp_space_class, _ctf_vp_name)
        if not callable(_ctf_vp_value):
            continue
        try:
            _ctf_vp_signature = _ctf_vp_inspect.signature(_ctf_vp_value)
        except Exception as _ctf_vp_error:
            _ctf_vp_signature = "ERROR={!r}".format(_ctf_vp_error)
        _ctf_vp_log("SpaceClass.{} sig={} repr={!r}".format(
            _ctf_vp_name, _ctf_vp_signature, _ctf_vp_value
        ))
        try:
            _ctf_vp_code = _ctf_vp_value.__func__.__code__
            _ctf_vp_log("SpaceClass.{} vars={} names={} consts={}".format(
                _ctf_vp_name, _ctf_vp_code.co_varnames, _ctf_vp_code.co_names, _ctf_vp_code.co_consts
            ))
        except Exception:
            pass

    _ctf_vp_spaces = []
    for _ctf_vp_object in _ctf_vp_gc.get_objects():
        try:
            if isinstance(_ctf_vp_object, _ctf_vp_space_class):
                _ctf_vp_spaces.append(_ctf_vp_object)
        except Exception:
            pass
    _ctf_vp_log("space_instances={} {}".format(len(_ctf_vp_spaces), _ctf_vp_spaces[:4]))
    for _ctf_vp_space in _ctf_vp_spaces[:2]:
        _ctf_vp_log("space_instance attrs={}".format([
            name for name in dir(_ctf_vp_space)
            if any(token in name.lower() for token in ("ray", "trace", "physics", "space"))
        ]))

    import MCamera as _ctf_vp_camera
    import common.EntityManager as _ctf_vp_em
    _ctf_vp_frame = _ctf_vp_camera.CaptureFrame()
    _ctf_vp_camera_pos = _ctf_vp_frame.Position
    _ctf_vp_entities = getattr(_ctf_vp_em.EntityManager, "_entities", {})
    _ctf_vp_targets = [
        entity for entity in _ctf_vp_entities.values()
        if getattr(entity, "IsRobotCombatAvatar", False) or getattr(entity, "IsPlayerCombatAvatar", False)
    ]
    for _ctf_vp_entity in _ctf_vp_targets[:2]:
        _ctf_vp_model = getattr(_ctf_vp_entity, "model", None)
        if _ctf_vp_model is None:
            continue
        try:
            _ctf_vp_model.MakeSureBones()
            _ctf_vp_model.CreateSpecifyBone("biped Head")
            _ctf_vp_head = _ctf_vp_model.GetBoneWorldPosition("biped Head")
            _ctf_vp_skeleton = _ctf_vp_model.GetSkeleton()
        except Exception as _ctf_vp_error:
            _ctf_vp_log("ray target head ERROR={!r}".format(_ctf_vp_error))
            continue
        _ctf_vp_log("ray target={} camera={!r} head={!r} entity_space_attrs={}".format(
            _ctf_vp_entity,
            _ctf_vp_camera_pos,
            _ctf_vp_head,
            [(name, repr(getattr(_ctf_vp_entity, name))) for name in dir(_ctf_vp_entity) if "space" in name.lower()][:20],
        ))
        for _ctf_vp_space in _ctf_vp_spaces:
            try:
                _ctf_vp_hit = _ctf_vp_space.ClosestRaycastBone(_ctf_vp_camera_pos, _ctf_vp_head)
                _ctf_vp_hit_values = {}
                for _ctf_vp_field in ("IsHit", "actor", "name", "hitPos", "Pos", "Body", "MaterialTypeId"):
                    try:
                        _ctf_vp_hit_values[_ctf_vp_field] = repr(getattr(_ctf_vp_hit, _ctf_vp_field))
                    except Exception as _ctf_vp_field_error:
                        _ctf_vp_hit_values[_ctf_vp_field] = "ERROR={!r}".format(_ctf_vp_field_error)
                _ctf_vp_log("ray space={} hit_type={} hit={!r} hit_attrs={}".format(
                    _ctf_vp_space,
                    type(_ctf_vp_hit),
                    _ctf_vp_hit,
                    [name for name in dir(_ctf_vp_hit) if not name.startswith("__")][:60],
                ))
                _ctf_vp_log("ray values={}".format(_ctf_vp_hit_values))
                _ctf_vp_log("ray target_skeleton={!r} actor_matches={}".format(
                    _ctf_vp_skeleton,
                    getattr(_ctf_vp_hit, "actor", None) == _ctf_vp_skeleton,
                ))
            except Exception as _ctf_vp_error:
                _ctf_vp_log("ray space={} ERROR={!r}".format(_ctf_vp_space, _ctf_vp_error))
except Exception:
    _ctf_vp_log("EXCEPTION\n" + _ctf_vp_traceback.format_exc())

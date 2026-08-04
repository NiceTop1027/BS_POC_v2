"""Probe the initialized avatar pose for an exact head-bone position."""

import traceback as _ctf_hp_traceback


_ctf_hp_log_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_head_pose_probe.log"


def _ctf_hp_log(message):
    with open(_ctf_hp_log_path, "a", encoding="utf-8") as _ctf_hp_handle:
        _ctf_hp_handle.write(str(message) + "\n")


def _ctf_hp_vec(value):
    try:
        return float(value.x), float(value.y), float(value.z)
    except Exception:
        return None


def _ctf_hp_call(obj, name, *args):
    try:
        return getattr(obj, name)(*args)
    except Exception as error:
        return "ERROR={!r}".format(error)


try:
    import common.EntityManager as _ctf_hp_em

    _ctf_hp_entities = getattr(_ctf_hp_em.EntityManager, "_entities", {})
    _ctf_hp_targets = [
        (str(key), entity) for key, entity in _ctf_hp_entities.items()
        if getattr(entity, "IsRobotCombatAvatar", False) or getattr(entity, "IsPlayerCombatAvatar", False)
    ]
    _ctf_hp_log("targets=" + repr([key for key, _ in _ctf_hp_targets]))
    for _ctf_hp_key, _ctf_hp_entity in _ctf_hp_targets[:2]:
        _ctf_hp_model = getattr(_ctf_hp_entity, "model", None)
        if _ctf_hp_model is None:
            continue
        _ctf_hp_log("{} model={}".format(_ctf_hp_key, type(_ctf_hp_model)))
        for _ctf_hp_source_name, _ctf_hp_source in (("entity", _ctf_hp_entity), ("model", _ctf_hp_model)):
            _ctf_hp_log("{} {} head_attrs={}".format(
                _ctf_hp_key,
                _ctf_hp_source_name,
                [name for name in dir(_ctf_hp_source) if any(token in name.lower() for token in ("head", "sight", "collider", "hitbox"))],
            ))
        _ctf_hp_log("{} MakeSureBones={}".format(
            _ctf_hp_key, _ctf_hp_call(_ctf_hp_model, "MakeSureBones")
        ))
        _ctf_hp_skeleton = _ctf_hp_call(_ctf_hp_model, "GetSkeleton")
        _ctf_hp_log("{} skeleton={} type={}".format(
            _ctf_hp_key, _ctf_hp_skeleton, type(_ctf_hp_skeleton)
        ))
        _ctf_hp_pose = _ctf_hp_call(_ctf_hp_skeleton, "GetPoseBones")
        _ctf_hp_log("{} pose={} type={} attrs={}".format(
            _ctf_hp_key,
            _ctf_hp_pose,
            type(_ctf_hp_pose),
            [name for name in dir(_ctf_hp_pose) if "bone" in name.lower() or "pose" in name.lower() or "name" in name.lower()],
        ))
        for _ctf_hp_name in (
            "biped Neck", "biped Head", "Head", "head", "Bip001 Head", "Bip001_Head", "Bip001_HeadNub",
            "Bip001 Neck", "Neck", "neck", "mixamorig:Head",
        ):
            _ctf_hp_created = _ctf_hp_call(_ctf_hp_model, "CreateSpecifyBone", _ctf_hp_name)
            _ctf_hp_world = _ctf_hp_call(_ctf_hp_model, "GetBoneWorldPosition", _ctf_hp_name)
            _ctf_hp_model_pos = _ctf_hp_call(_ctf_hp_model, "GetBoneModelPosition", _ctf_hp_name)
            _ctf_hp_log("{} {} create={!r} world={} model={}".format(
                _ctf_hp_key,
                _ctf_hp_name,
                _ctf_hp_created,
                _ctf_hp_vec(_ctf_hp_world),
                _ctf_hp_vec(_ctf_hp_model_pos),
            ))
except Exception:
    _ctf_hp_log("EXCEPTION\n" + _ctf_hp_traceback.format_exc())

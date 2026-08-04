"""Read-only probe for the exact avatar head-bone world position."""

import inspect as _ctf_hb_inspect
import traceback as _ctf_hb_traceback


_ctf_hb_log_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_head_bone_probe.log"


def _ctf_hb_log(message):
    with open(_ctf_hb_log_path, "a", encoding="utf-8") as _ctf_hb_handle:
        _ctf_hb_handle.write(str(message) + "\n")


def _ctf_hb_vec(value):
    try:
        return float(value.x), float(value.y), float(value.z)
    except Exception:
        return None


try:
    import common.EntityManager as _ctf_hb_em

    _ctf_hb_entities = getattr(_ctf_hb_em.EntityManager, "_entities", {})
    _ctf_hb_targets = [
        (str(key), entity) for key, entity in _ctf_hb_entities.items()
        if getattr(entity, "IsRobotCombatAvatar", False) or getattr(entity, "IsPlayerCombatAvatar", False)
    ]
    _ctf_hb_log("targets=" + repr([key for key, _ in _ctf_hb_targets]))
    for _ctf_hb_key, _ctf_hb_entity in _ctf_hb_targets[:3]:
        _ctf_hb_model = getattr(_ctf_hb_entity, "model", None)
        _ctf_hb_bound = _ctf_hb_model.GetWorldBound() if _ctf_hb_model is not None else None
        _ctf_hb_log("{} bound={}..{}".format(
            _ctf_hb_key,
            _ctf_hb_vec(getattr(_ctf_hb_bound, "min", None)),
            _ctf_hb_vec(getattr(_ctf_hb_bound, "max", None)),
        ))
        for _ctf_hb_method_name in ("MakeSureBones", "CreateSpecifyBone"):
            _ctf_hb_method = getattr(_ctf_hb_model, _ctf_hb_method_name, None)
            try:
                _ctf_hb_log("{} {} sig={} repr={}".format(
                    _ctf_hb_key,
                    _ctf_hb_method_name,
                    _ctf_hb_inspect.signature(_ctf_hb_method),
                    _ctf_hb_method,
                ))
                _ctf_hb_code = _ctf_hb_method.__func__.__code__
                _ctf_hb_log("{} {} vars={} names={} consts={}".format(
                    _ctf_hb_key,
                    _ctf_hb_method_name,
                    _ctf_hb_code.co_varnames,
                    _ctf_hb_code.co_names,
                    _ctf_hb_code.co_consts,
                ))
            except Exception as _ctf_hb_error:
                _ctf_hb_log("{} {} signature ERROR={!r}".format(_ctf_hb_key, _ctf_hb_method_name, _ctf_hb_error))
        for _ctf_hb_bound_name in ("GetSkeletonDynamicWorldBound", "GetPrimWorldBound", "GetPrimWorldBoundWithAttachments"):
            try:
                _ctf_hb_value = getattr(_ctf_hb_model, _ctf_hb_bound_name)()
                _ctf_hb_log("{} {}={}..{}".format(
                    _ctf_hb_key,
                    _ctf_hb_bound_name,
                    _ctf_hb_vec(getattr(_ctf_hb_value, "min", None)),
                    _ctf_hb_vec(getattr(_ctf_hb_value, "max", None)),
                ))
            except Exception as _ctf_hb_error:
                _ctf_hb_log("{} {} ERROR={!r}".format(_ctf_hb_key, _ctf_hb_bound_name, _ctf_hb_error))
        for _ctf_hb_source_name, _ctf_hb_source in (
            ("model", _ctf_hb_model),
            ("model.model", getattr(_ctf_hb_model, "model", None)),
        ):
            if _ctf_hb_source is None:
                continue
            _ctf_hb_log("{} {} type={} bone_names={}".format(
                _ctf_hb_key,
                _ctf_hb_source_name,
                type(_ctf_hb_source),
                [name for name in dir(_ctf_hb_source) if "bone" in name.lower() or "joint" in name.lower()],
            ))
            for _ctf_hb_method_name in (
                "GetBoneWorldPosition",
                "GetBoneModelPosition",
                "GetBoneLocalPosition",
                "GetBoneWorldTransform",
                "GetBoneLocalTransform",
                "GetBoneTransform",
            ):
                _ctf_hb_method = getattr(_ctf_hb_source, _ctf_hb_method_name, None)
                if not callable(_ctf_hb_method):
                    continue
                try:
                    _ctf_hb_value = _ctf_hb_method("Head")
                    _ctf_hb_log("{} {}.{}('Head') -> {} raw={!r}".format(
                        _ctf_hb_key,
                        _ctf_hb_source_name,
                        _ctf_hb_method_name,
                        _ctf_hb_vec(_ctf_hb_value),
                        _ctf_hb_value,
                    ))
                except Exception as _ctf_hb_error:
                    _ctf_hb_log("{} {}.{} ERROR={!r}".format(
                        _ctf_hb_key,
                        _ctf_hb_source_name,
                        _ctf_hb_method_name,
                        _ctf_hb_error,
                    ))
except Exception:
    _ctf_hb_log("EXCEPTION\n" + _ctf_hb_traceback.format_exc())

"""Read-only ballistics metadata probe for the isolated CTF game process."""

import inspect as _ctf_wp_inspect
import sys as _ctf_wp_sys
import traceback as _ctf_wp_traceback


_ctf_wp_log_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_weapon_ballistics_probe.log"


def _ctf_wp_log(value):
    with open(_ctf_wp_log_path, "a", encoding="utf-8") as _ctf_wp_handle:
        _ctf_wp_handle.write(str(value) + "\n")


def _ctf_wp_short(value, limit=1800):
    try:
        text = repr(value)
    except Exception as error:
        text = "<repr error {!r}>".format(error)
    return text[:limit] + ("..." if len(text) > limit else "")


def _ctf_wp_describe(label, value):
    _ctf_wp_log(label + " type=" + str(type(value)) + " value=" + _ctf_wp_short(value))
    try:
        names = [name for name in dir(value) if any(token in name.lower() for token in (
            "speed", "velocity", "projectile", "bullet", "ballistic", "range", "weapon", "attr"))]
        _ctf_wp_log(label + ".names=" + _ctf_wp_short(names, 6000))
        for name in names:
            try:
                _ctf_wp_log(label + "." + name + "=" + _ctf_wp_short(getattr(value, name)))
            except Exception as error:
                _ctf_wp_log(label + "." + name + " ERROR=" + repr(error))
    except Exception as error:
        _ctf_wp_log(label + ".dir ERROR=" + repr(error))


try:
    _ctf_wp_log("BEGIN")
    import common.EntityManager as _ctf_wp_em

    _ctf_wp_entities = getattr(_ctf_wp_em.EntityManager, "_entities", {})
    _ctf_wp_players = [
        (str(key), entity) for key, entity in _ctf_wp_entities.items()
        if getattr(entity, "IsPlayerCombatAvatar", False)
    ]
    _ctf_wp_log("players=" + _ctf_wp_short([key for key, _ in _ctf_wp_players]))
    if not _ctf_wp_players:
        raise RuntimeError("no player avatar")

    _ctf_wp_key, _ctf_wp_player = _ctf_wp_players[0]
    _ctf_wp_weapon = _ctf_wp_player.GetCurHighPriorityWeapon()
    _ctf_wp_log("player=" + _ctf_wp_key)
    _ctf_wp_describe("weapon", _ctf_wp_weapon)
    _ctf_wp_describe("weapon_attr_cache", getattr(_ctf_wp_player, "weapon_attr_cache", None))

    for _ctf_wp_name in ("GetCurHighPriorityWeapon", "GetWeaponAttrValueWithCache"):
        _ctf_wp_method = getattr(_ctf_wp_player, _ctf_wp_name, None)
        _ctf_wp_log("method " + _ctf_wp_name + "=" + _ctf_wp_short(_ctf_wp_method))
        try:
            _ctf_wp_log("method " + _ctf_wp_name + ".signature=" + str(_ctf_wp_inspect.signature(_ctf_wp_method)))
        except Exception as error:
            _ctf_wp_log("method " + _ctf_wp_name + ".signature ERROR=" + repr(error))
        try:
            _ctf_wp_code = _ctf_wp_method.__func__.__code__
            _ctf_wp_log("method " + _ctf_wp_name + ".varnames=" + _ctf_wp_short(_ctf_wp_code.co_varnames, 4000))
            _ctf_wp_log("method " + _ctf_wp_name + ".names=" + _ctf_wp_short(_ctf_wp_code.co_names, 4000))
        except Exception as error:
            _ctf_wp_log("method " + _ctf_wp_name + ".code ERROR=" + repr(error))

    _ctf_wp_module_names = [
        name for name in sorted(_ctf_wp_sys.modules)
        if any(token in name.lower() for token in ("weapon", "bullet", "projectile", "ballistic", "gun"))
    ]
    _ctf_wp_log("modules=" + _ctf_wp_short(_ctf_wp_module_names, 12000))
    for _ctf_wp_module_name in _ctf_wp_module_names[:80]:
        _ctf_wp_module = _ctf_wp_sys.modules.get(_ctf_wp_module_name)
        _ctf_wp_names = [
            name for name in dir(_ctf_wp_module)
            if any(token in name.lower() for token in ("speed", "velocity", "projectile", "bullet", "ballistic", "weapon", "attr"))
        ]
        if _ctf_wp_names:
            _ctf_wp_log("module " + _ctf_wp_module_name + ".names=" + _ctf_wp_short(_ctf_wp_names, 3000))
    _ctf_wp_log("END")
except Exception:
    _ctf_wp_log("EXCEPTION\n" + _ctf_wp_traceback.format_exc())

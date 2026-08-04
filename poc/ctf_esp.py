"""CTF proof module for the isolated BloodStrike instance.

This module is intended to be loaded by BloodStrike.exe's embedded Python
runtime through the patch-source importer.  It demonstrates the ESP primitive
by using exported in-engine scripting APIs to outline entities and, where the
UI binding is available, attach lightweight board elements.

It does not open sockets, patch process memory, inject native code, or attempt
to bypass anti-cheat.  The only filesystem effect is an evidence log written
under the local CTF task directory.
"""

from __future__ import annotations

import sys
import time
import traceback


EVIDENCE_PATH = (
    r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc"
    r"\ctf_esp_evidence.log"
)

_STARTED = False
_DUMPED_API = False
_BOARD_IDS = set()


def _log(message: str) -> None:
    try:
        with open(EVIDENCE_PATH, "a", encoding="utf-8") as handle:
            handle.write(f"{time.time():.3f} {message}\n")
    except Exception:
        pass


def _safe_call(obj, name: str, *args):
    func = getattr(obj, name, None)
    if func is None:
        return None
    try:
        return func(*args)
    except Exception as exc:
        _log(f"{name} failed: {exc!r}")
        return None


def _safe_set(obj, name: str, value) -> bool:
    try:
        setattr(obj, name, value)
        return True
    except Exception as exc:
        _log(f"set {name} failed: {exc!r}")
        return False


def _entity_key(entity) -> str:
    for attr in ("guid", "id", "EntityID", "entity_id"):
        try:
            value = getattr(entity, attr)
            if callable(value):
                value = value()
            if value is not None:
                return str(value)
        except Exception:
            pass
    return str(id(entity))


def _iter_entities(asiocore):
    entities = asiocore.entities()
    if entities is None:
        return []
    if isinstance(entities, dict):
        return list(entities.values())
    try:
        return list(entities)
    except TypeError:
        return []


def _try_outline(entity) -> bool:
    changed = False
    before = _safe_call(entity, "GetIsOutlined")
    _safe_call(entity, "SetIsOutlined", True)
    after = _safe_call(entity, "GetIsOutlined")
    changed = changed or after is True or before is not None

    thermal_before = _safe_call(entity, "GetIsThermalVisible")
    _safe_call(entity, "SetIsThermalVisible", True)
    thermal_after = _safe_call(entity, "GetIsThermalVisible")
    changed = changed or thermal_after is True or thermal_before is not None

    # Some CTF builds expose debug render toggles directly on reflected objects.
    # These are the most literal "box" primitives when present.
    for method in ("ShowBoundingBox", "ShowBox", "ShowDebug", "SetShowBoundingBox"):
        result = _safe_call(entity, method, True)
        changed = changed or result is not None

    for prop in ("ShowBoundingBox", "ShowBox", "DebugDraw", "RenderDebug"):
        changed = _safe_set(entity, prop, True) or changed

    return changed


def _world_pos(entity):
    for name in ("GetWorldBound", "GetPrimitiveWorldBound"):
        box = _safe_call(entity, name)
        if box is None:
            continue
        for attr in ("center", "Center", "position", "Position"):
            try:
                value = getattr(box, attr)
                if callable(value):
                    value = value()
                if value is not None:
                    return value
            except Exception:
                pass
        try:
            return (
                (box.min.x + box.max.x) * 0.5,
                (box.min.y + box.max.y) * 0.5,
                (box.min.z + box.max.z) * 0.5,
            )
        except Exception:
            pass
    for name in ("GetPosition", "GetWorldPosition", "Position", "position"):
        try:
            value = getattr(entity, name)
            if callable(value):
                value = value()
            if value is not None:
                return value
        except Exception:
            pass
    return (0.0, 0.0, 0.0)


def _try_board(entity) -> bool:
    """Attach a board element when the MUI wrapper is present.

    Static wrapper metadata in BloodStrike.exe shows AddFakeBoardElement0 takes
    two Python arguments and validates FakeBoardElementParam.  Builds differ in
    exact accepted first-argument shape, so this intentionally tries only the
    two least invasive call forms and logs failures instead of crashing.
    """

    try:
        import MUI  # type: ignore
    except Exception:
        return False

    key = _entity_key(entity)
    if key in _BOARD_IDS:
        return False

    try:
        param = MUI.FakeBoardElementParam()
        try:
            harm = MUI.HarmTextParam()
            for attr, value in (
                ("harmText", "[CTF ESP BOX]"),
                ("fontName", "Arial"),
                ("worldPos", _world_pos(entity)),
                ("strokeColor", (0, 255, 0, 255)),
                ("fontSize", 18),
                ("fovDistance", 5000.0),
                ("accScale", 1.0),
                ("localZ", 9999.0),
                ("fontIndex", 0),
            ):
                _safe_set(harm, attr, value)
            _safe_set(param, "harmText", harm)
            _safe_set(param, "worldPos", _world_pos(entity))
            _safe_set(param, "strokeColor", (0, 255, 0, 255))
            _safe_set(param, "fontSize", 18)
            _safe_set(param, "fovDistance", 5000.0)
            _safe_set(param, "localZ", 9999.0)
        except Exception as exc:
            _log(f"HarmTextParam setup failed: {exc!r}")

        for attr, value in (
            ("biasType", 0),
            ("minScale", 1.0),
            ("maxScale", 1.8),
            ("normalFov", 90.0),
        ):
            _safe_set(param, attr, value)

        candidates = (
            ("AddFakeBoardElement0", ((entity, param), (key, param))),
            ("AddFakeBoardElementWithBone", ((key, entity, "Head", param), (entity, "Head", param))),
            ("AddFakeBoardElement", ((key, None, entity, _world_pos(entity), 1.0, 1.0, 1.0, 0, True),)),
        )
        for func_name, arg_sets in candidates:
            add = getattr(MUI, func_name, None)
            if add is None:
                continue
            for args in arg_sets:
                try:
                    add(*args)
                    _BOARD_IDS.add(key)
                    _log(f"{func_name} succeeded key={key}")
                    return True
                except Exception as exc:
                    _log(f"{func_name}{args!r} failed: {exc!r}")
        return False
    except Exception:
        _log("board exception:\n" + traceback.format_exc())
        return False


def _tick() -> None:
    global _DUMPED_API
    try:
        import asiocore  # type: ignore

        outlined = 0
        board_added = 0
        entities = _iter_entities(asiocore)
        if not _DUMPED_API:
            _DUMPED_API = True
            _log(f"asiocore api sample={dir(asiocore)[:80]!r}")
            try:
                import MUI  # type: ignore
                _log(f"MUI api sample={dir(MUI)[:120]!r}")
            except Exception as exc:
                _log(f"MUI import failed: {exc!r}")
            if entities:
                _log(f"entity api sample={dir(entities[0])[:160]!r}")

        for entity in entities:
            if entity is None:
                continue
            if _try_outline(entity):
                outlined += 1
            if _try_board(entity):
                board_added += 1

        _log(
            "tick "
            f"entities={len(entities)} outlined={outlined} "
            f"board_added={board_added} argv={sys.argv!r}"
        )
    except Exception:
        _log("tick exception:\n" + traceback.format_exc())


def _install_timer() -> None:
    import asiocore  # type: ignore

    timer = getattr(asiocore, "add_timer", None)
    if timer is None:
        _log("asiocore.add_timer missing; running one-shot tick")
        _tick()
        return

    for args in ((0.5, True, False, _tick), (0.5, True, 0, _tick), (0.5, _tick)):
        try:
            timer(*args)
            _log(f"timer installed args={args[:-1]!r}")
            return
        except Exception as exc:
            _log(f"add_timer args={args[:-1]!r} failed: {exc!r}")

    _log("timer install failed; running one-shot tick")
    _tick()


def Entry(*args):  # noqa: N802 - engine expects this exact name.
    global _STARTED
    if _STARTED:
        return True
    _STARTED = True
    _log(f"Entry called args={args!r}")
    try:
        _install_timer()
    except Exception:
        _log("Entry exception:\n" + traceback.format_exc())
    return True


def fini():  # noqa: N802 - engine looks up this exact name.
    _log("fini called")
    return True


_log("module imported")

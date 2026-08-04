"""Measure the active game camera update cadence without changing its output."""

import builtins as _ctf_cam_builtins
import gc as _ctf_cam_gc
import time as _ctf_cam_time
import traceback as _ctf_cam_traceback


_ctf_cam_log_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_camera_tick_probe.log"
_ctf_cam_state_name = "_ctf_camera_tick_probe_state"


def _ctf_cam_log(value):
    with open(_ctf_cam_log_path, "a", encoding="utf-8") as _ctf_cam_handle:
        _ctf_cam_handle.write(str(value) + "\n")


def _ctf_cam_finish(state, reason):
    if state.get("finished"):
        return
    state["finished"] = True
    for camera, original in state.get("hooks", []):
        try:
            camera._tickComponents = original
        except Exception as exc:
            _ctf_cam_log("restore failed=" + repr(exc))
    try:
        state["owner"].cancel_timer(state.get("finish_timer"))
    except Exception:
        pass
    elapsed = max(0.000001, _ctf_cam_time.perf_counter() - state["start"])
    _ctf_cam_log("RESULT reason={} callbacks={} elapsed={:.6f} hz={:.3f} intervals={}".format(
        reason,
        state["count"],
        elapsed,
        state["count"] / elapsed,
        [round(value, 5) for value in state["intervals"][:24]],
    ))
    _ctf_cam_log("PER_CAMERA=" + repr(state.get("counts", {})))
    setattr(_ctf_cam_builtins, _ctf_cam_state_name, None)


def _ctf_cam_check(*_ctf_cam_args, **_ctf_cam_kwargs):
    state = getattr(_ctf_cam_builtins, _ctf_cam_state_name, None)
    if not isinstance(state, dict):
        return
    if _ctf_cam_time.perf_counter() - state["start"] >= 1.5:
        _ctf_cam_finish(state, "sample_complete")


def _ctf_cam_make_wrapper(index, original):
    def _ctf_cam_wrap(*_ctf_cam_args, **_ctf_cam_kwargs):
        state = getattr(_ctf_cam_builtins, _ctf_cam_state_name, None)
        if not isinstance(state, dict) or state.get("finished"):
            return original(*_ctf_cam_args, **_ctf_cam_kwargs)
        now = _ctf_cam_time.perf_counter()
        last = state.get("last")
        if last is not None and len(state["intervals"]) < 30:
            state["intervals"].append(now - last)
        state["last"] = now
        state["count"] += 1
        state["counts"][index] = state["counts"].get(index, 0) + 1
        # This stays a transparent wrapper: the original bound update executes
        # with the exact arguments and return path that the game supplied.
        return original(*_ctf_cam_args, **_ctf_cam_kwargs)
    return _ctf_cam_wrap


def _ctf_cam_run():
    _ctf_cam_log("BEGIN " + str(_ctf_cam_time.time()))
    old = getattr(_ctf_cam_builtins, _ctf_cam_state_name, None)
    if isinstance(old, dict):
        _ctf_cam_finish(old, "replaced")
    try:
        import common.EntityManager as _ctf_cam_em
        from gclient.framework.entities.camera import Camera as _ctf_cam_class

        cameras = [
            obj for obj in _ctf_cam_gc.get_objects()
            if isinstance(obj, _ctf_cam_class) and "(D)" not in repr(obj)
        ]
        entities = list(getattr(_ctf_cam_em.EntityManager, "_entities", {}).values())
        owner = next((entity for entity in entities if getattr(entity, "IsPlayerCombatAvatar", False)), None)
        if not cameras or owner is None:
            summaries = []
            for index, candidate in enumerate(cameras):
                try:
                    summaries.append((
                        index,
                        repr(candidate),
                        repr(getattr(candidate, "position", None)),
                        repr(getattr(candidate, "engine_camera", None)),
                    ))
                except Exception as exc:
                    summaries.append((index, "<summary failed>", repr(exc)))
            _ctf_cam_log("NO_UNIQUE_CAMERA count={} owner={} candidates={}".format(
                len(cameras), owner is not None, summaries
            ))
            return
        camera = cameras[0]
        engine = getattr(camera, "engine_camera", None)
        engine_names = []
        if engine is not None:
            engine_names = [
                name for name in dir(engine)
                if any(token in name.lower() for token in ("camera", "frame", "runtime", "transform", "matrix", "fov", "view"))
            ]
        _ctf_cam_log("camera={} engine={} engine_names={}".format(
            repr(camera), repr(engine), engine_names[:120]
        ))
        state = {
            "owner": owner,
            "hooks": [],
            "start": _ctf_cam_time.perf_counter(),
            "last": None,
            "count": 0,
            "counts": {},
            "intervals": [],
            "finished": False,
        }
        setattr(_ctf_cam_builtins, _ctf_cam_state_name, state)
        for index, candidate in enumerate(cameras):
            original = candidate._tickComponents
            state["hooks"].append((candidate, original))
            candidate._tickComponents = _ctf_cam_make_wrapper(index, original)
        state["finish_timer"] = owner.add_repeat_timer(0.10, _ctf_cam_check)
        _ctf_cam_log("HOOKED candidates={}".format(len(cameras)))
    except Exception:
        _ctf_cam_log("EXC\n" + _ctf_cam_traceback.format_exc())


_ctf_cam_run()

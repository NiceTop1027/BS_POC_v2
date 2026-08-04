"""Read-only inspection of the isolated CTF engine camera interface."""

import gc
import inspect
import time
import traceback


_log_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_engine_camera_api_probe.log"


def _log(value):
    with open(_log_path, "a", encoding="utf-8") as handle:
        handle.write(str(value) + "\n")


def _short(value):
    try:
        return repr(value)[:2400]
    except Exception:
        return "<repr failed>"


def _call(label, obj, name):
    try:
        result = getattr(obj, name)()
        _log(label + "." + name + "()=" + _short(result))
    except Exception as exc:
        _log(label + "." + name + " FAIL=" + repr(exc))


def _run():
    _log("BEGIN " + str(time.time()))
    try:
        from gclient.framework.entities.camera import Camera

        cameras = [
            item for item in gc.get_objects()
            if isinstance(item, Camera) and "(D)" not in repr(item)
        ]
        _log("cameras=" + str(len(cameras)))
        engines = []
        for camera in cameras:
            engine = getattr(camera, "engine_camera", None)
            if engine is not None and all(engine is not seen for seen in engines):
                engines.append(engine)
        _log("unique_engines=" + str(len(engines)))
        for index, engine in enumerate(engines):
            names = [name for name in dir(engine) if not name.startswith("__")]
            _log("engine[{}]={}".format(index, _short(engine)))
            _log("engine[{}].names={}".format(index, _short(names)))
            for name in (
                "GetRuntimeInfo", "GetFrame", "CaptureFrame", "GetTransform",
                "GetCameraTransform", "GetPosition", "GetDirection", "GetFov",
                "GetScreenSize", "GetLastRenderTime",
                "Transform", "Position", "Direction", "Fov",
            ):
                if name in names:
                    _call("engine[{}]".format(index), engine, name)
                    try:
                        _log("engine[{}].{}={}".format(index, name, _short(getattr(engine, name))))
                    except Exception:
                        pass
            for name in ("FieldOfView", "TransformUpdate", "ViewMatrix", "BindEvent"):
                if name not in names:
                    continue
                try:
                    value = getattr(engine, name)
                    try:
                        signature = inspect.signature(value)
                    except Exception as exc:
                        signature = "<signature unavailable: {}>".format(repr(exc))
                    _log("engine[{}].{} value={} signature={}".format(
                        index, name, _short(value), signature
                    ))
                except Exception as exc:
                    _log("engine[{}].{} READ FAIL={}".format(index, name, repr(exc)))
        if engines:
            import common.EntityManager as entity_manager

            target = next(
                (entity for entity in getattr(entity_manager.EntityManager, "_entities", {}).values()
                 if getattr(entity, "IsRobotCombatAvatar", False)),
                None,
            )
            if target is not None:
                position = target.model.GetBoneWorldPosition("biped Head")
                _log("head=" + _short(position))
                try:
                    _log("screen_point({})={}".format(
                        _short(position), _short(engines[0].GetScreenPointFromWorldPoint(position))
                    ))
                except Exception as exc:
                    _log("screen_point FAIL=" + repr(exc))
    except Exception:
        _log("EXC\n" + traceback.format_exc())
    finally:
        _log("END")


_run()

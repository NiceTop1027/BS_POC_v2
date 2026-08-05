import gc
import os
import traceback

ROOT = os.path.dirname(__file__)
LOG = os.path.join(ROOT, "ctf_visibility_probe.log")


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


def call(obj, name, *args):
    try:
        return getattr(obj, name)(*args)
    except Exception as exc:
        return "EXC " + repr(exc)[:180]


def vec3(value):
    try:
        return (float(value.x), float(value.y), float(value.z))
    except Exception:
        return None


def hit_summary(value):
    parts = ["repr=" + repr(value)[:220]]
    for attr in (
        "IsHit",
        "actor",
        "entity",
        "body",
        "shape",
        "position",
        "point",
        "hit_pos",
        "distance",
        "normal",
    ):
        try:
            parts.append("{}={!r}".format(attr, getattr(value, attr)))
        except Exception:
            pass
    return " ".join(parts)


try:
    open(LOG, "w", encoding="utf-8").write("visibility probe start\n")
    import MCamera
    import common.EntityManager as EM
    from gclient.framework.entities.space import Space

    entities = list(getattr(EM.EntityManager, "_entities", {}).items())
    spaces = [entity for _, entity in entities if isinstance(entity, Space)]
    active_space = next((space for space in spaces if "(D)" not in repr(space)), None)
    log("spaces={} active={!r}".format(len(spaces), active_space))
    if active_space is not None:
        names = dir(active_space)
        interesting = [
            name for name in names
            if any(token in name.lower() for token in (
                "ray", "cast", "trace", "hit", "phys", "coll", "block", "line", "visible"
            ))
        ]
        log("space interesting={}".format(interesting))

    frame = MCamera.CaptureFrame()
    camera_pos = getattr(frame, "Position", None)
    log("camera={} yaw={} pitch={} fov={}".format(
        vec3(camera_pos), getattr(frame, "Yaw", None), getattr(frame, "Pitch", None), getattr(frame, "Fov", None)
    ))

    robots = []
    for key, entity in entities:
        try:
            is_robot = bool(getattr(entity, "IsRobotCombatAvatar")())
        except Exception:
            is_robot = "robot" in type(entity).__name__.lower()
        if is_robot:
            robots.append((str(key), entity))
    log("robots={}".format(len(robots)))

    ray_names = []
    if active_space is not None:
        for name in dir(active_space):
            lower = name.lower()
            if any(token in lower for token in ("ray", "cast", "trace", "line")):
                if callable(getattr(active_space, name, None)):
                    ray_names.append(name)
    log("ray names={}".format(ray_names))

    for key, entity in robots[:8]:
        model = getattr(entity, "model", None)
        head = None
        skeleton = None
        if model is not None:
            call(model, "MakeSureBones")
            head = call(model, "GetBoneWorldPosition", "biped Head")
            skeleton = call(model, "GetSkeleton")
        log("TARGET {} type={} pos={} head={} skeleton={!r}".format(
            key, type(entity).__name__, vec3(getattr(entity, "position", None)), vec3(head), skeleton
        ))
        for method in (
            "CanShowEnemyToplogo",
            "CanShowEnemyToplogoBar",
            "CanVisibleInLightAttackMode",
            "CanLimitFrameInvisible",
            "CheckUavEnemyPosValid",
            "CheckIsOutDoor",
            "IsCameraHitMe",
        ):
            if hasattr(entity, method):
                log("  {} -> {!r}".format(method, call(entity, method)))
        if active_space is None or head is None:
            continue
        for method in ray_names:
            result = call(active_space, method, camera_pos, head)
            log("  {}(camera,head) -> {}".format(method, hit_summary(result)))
        if skeleton is not None and "ClosestRaycastBone" in ray_names:
            result = call(active_space, "ClosestRaycastBone", camera_pos, head)
            log("  closest actor is skeleton -> {}".format(getattr(result, "actor", None) == skeleton))
except Exception:
    log("PROBE_EXC\n" + traceback.format_exc())

import os
import traceback

ROOT = os.path.dirname(__file__)
LOG = os.path.join(ROOT, "ctf_los_probe.log")


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


def call(obj, name, *args):
    try:
        return getattr(obj, name)(*args)
    except Exception as exc:
        return "EXC " + repr(exc)[:180]


def vec(value):
    try:
        return (float(value.x), float(value.y), float(value.z))
    except Exception:
        return None


def dist(a, b):
    if a is None or b is None:
        return None
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


def hit_pos(hit):
    for attr in ("Pos", "position", "point", "hit_pos"):
        pos = vec(getattr(hit, attr, None))
        if pos is not None:
            return pos
    return None


def hit_line(label, space, camera, point, filter_value):
    hit = call(space, "ClosestRaycast", camera, point, filter_value, False)
    is_hit = bool(hit is not None and not isinstance(hit, str) and getattr(hit, "IsHit", False))
    pos = hit_pos(hit) if is_hit else None
    body = getattr(hit, "Body", None) if is_hit else None
    body_filter = None
    if body is not None:
        body_filter = call(body, "GetCollisionFilterInfo")
    log("{} hit={} pos={} hit_d={} target_d={} body={} body_filter={!r} repr={}".format(
        label,
        is_hit,
        pos,
        dist(camera, pos),
        dist(camera, vec(point)),
        repr(body)[:120],
        body_filter,
        repr(hit)[:160],
    ))


try:
    open(LOG, "w", encoding="utf-8").write("los probe start\n")
    import MCamera
    import common.EntityManager as EM
    from gclient import cconst
    from gclient.framework.entities.space import Space

    entities = list(getattr(EM.EntityManager, "_entities", {}).items())
    spaces = [entity for _, entity in entities if isinstance(entity, Space)]
    space = next((item for item in spaces if "(D)" not in repr(item)), None)
    frame = MCamera.CaptureFrame()
    camera = getattr(frame, "Position", None)
    camera_tuple = vec(camera)
    log("camera={} yaw={} pitch={} fov={}".format(
        camera_tuple,
        getattr(frame, "Yaw", None),
        getattr(frame, "Pitch", None),
        getattr(frame, "Fov", None),
    ))
    filters = [
        ("VISIBLE", getattr(cconst, "PHYSICS_VISIBLE_OBSTACLE_QUERY", 5)),
        ("CAMERA", getattr(cconst, "PHYSICS_CAMERA", 11)),
        ("BULLET", getattr(cconst, "PHYSICS_BULLET", 23)),
    ]
    bones = [
        "biped Head",
        "biped Neck",
        "biped Spine2",
        "biped Spine1",
        "biped Spine",
        "biped Pelvis",
    ]
    targets = []
    for key, entity in entities:
        try:
            is_robot = bool(getattr(entity, "IsRobotCombatAvatar")())
        except Exception:
            is_robot = "robot" in type(entity).__name__.lower()
        try:
            is_player = bool(getattr(entity, "IsPlayerCombatAvatar")())
        except Exception:
            is_player = "combatavatar" in type(entity).__name__.lower() and not is_robot
        if is_robot or is_player:
            targets.append((str(key), entity, "robot" if is_robot else "player"))
    log("targets={}".format(len(targets)))
    for key, entity, kind in targets[:12]:
        model = getattr(entity, "model", None)
        if model is None:
            continue
        call(model, "MakeSureBones")
        skeleton = call(model, "GetSkeleton")
        log("TARGET {} kind={} type={} skeleton={}".format(
            key, kind, type(entity).__name__, repr(skeleton)[:140]
        ))
        for bone in bones:
            point = call(model, "GetBoneWorldPosition", bone)
            point_tuple = vec(point)
            if point_tuple is None:
                continue
            bone_hit = call(space, "RaycastBoneWithPenetrate", camera, point)
            bone_ok = isinstance(bone_hit, (list, tuple)) and len(bone_hit) == 1 and getattr(bone_hit[0], "actor", None) == skeleton
            log("  BONE {} point={} target_d={} bone_ok={} bone_hits={}".format(
                bone,
                point_tuple,
                dist(camera_tuple, point_tuple),
                bone_ok,
                repr(bone_hit)[:180],
            ))
            for name, value in filters:
                hit_line("    {} {}".format(name, bone), space, camera, point, value)
except Exception:
    log("PROBE_EXC\n" + traceback.format_exc())

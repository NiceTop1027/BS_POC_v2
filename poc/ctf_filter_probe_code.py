import dis
import gc
import importlib
import inspect
import os
import sys
import traceback

ROOT = os.path.dirname(__file__)
LOG = os.path.join(ROOT, "ctf_filter_probe.log")


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


def call(obj, name, *args):
    try:
        return getattr(obj, name)(*args)
    except Exception as exc:
        return "EXC " + repr(exc)[:220]


def safe_attrs(obj, limit=80):
    try:
        return sorted([name for name in dir(obj) if not name.startswith("__")])[:limit]
    except Exception as exc:
        return ["EXC " + repr(exc)]


def vec3(value):
    try:
        return (float(value.x), float(value.y), float(value.z))
    except Exception:
        return None


def hit_summary(value):
    if isinstance(value, (list, tuple)):
        return "list len={} [{}]".format(
            len(value), "; ".join(hit_summary(item) for item in value[:4])
        )
    parts = ["type={}".format(type(value).__name__), "repr=" + repr(value)[:180]]
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


def dump_callable(name, fn):
    log("{} object={!r}".format(name, fn))
    try:
        log("{} signature={}".format(name, inspect.signature(fn)))
    except Exception as exc:
        log("{} signature_exc={!r}".format(name, exc))
    try:
        code = getattr(fn, "__code__", None)
        if code is not None:
            log("{} names={}".format(name, code.co_names))
            log("{} consts={}".format(name, code.co_consts))
            for ins in dis.Bytecode(fn):
                log("  {:04d} {:24s} {}".format(ins.offset, ins.opname, ins.argrepr))
    except Exception as exc:
        log("{} dis_exc={!r}".format(name, exc))


def try_construct(cls, arg_sets):
    made = []
    for label, args in arg_sets:
        try:
            obj = cls(*args)
            made.append((label, obj))
            log("construct {} -> {!r} attrs={}".format(label, obj, safe_attrs(obj, 40)))
        except Exception as exc:
            log("construct {} EXC {!r}".format(label, exc))
    return made


try:
    open(LOG, "w", encoding="utf-8").write("filter probe start\n")

    import MCamera
    import common.EntityManager as EM
    from gclient.framework.entities.space import Space

    log("camera-like modules={}".format(
        sorted([name for name in sys.modules if "camera" in name.lower()])[:80]
    ))

    camera_modules = [("MCamera", MCamera)]
    for module_name in ("Camera", "gclient.gameplay.camera.Camera"):
        try:
            camera_modules.append((module_name, importlib.import_module(module_name)))
        except Exception as exc:
            log("import {} EXC {!r}".format(module_name, exc))
    try:
        camera_entity_module = importlib.import_module("gclient.framework.entities.camera")
        camera_modules.append(("gclient.framework.entities.camera.Camera", camera_entity_module.Camera))
    except Exception as exc:
        log("import gclient.framework.entities.camera.Camera EXC {!r}".format(exc))
    for module_name, module in sorted(sys.modules.items()):
        if module is None:
            continue
        lower = module_name.lower()
        if ("camera" in lower or "physics" in lower or "coll" in lower) and (
            hasattr(module, "CreateCollider") or hasattr(module, "CollisionFilterInfo")
        ):
            camera_modules.append((module_name, module))

    globals_from_camera = {}
    seen_modules = set()
    for module_name, module in camera_modules:
        if id(module) in seen_modules:
            continue
        seen_modules.add(id(module))
        dump_callable(module_name + ".CreateCollider", getattr(module, "CreateCollider", None))
        candidate_globals = getattr(getattr(module, "CreateCollider", None), "__globals__", {})
        log("{} globals filter-ish={}".format(
            module_name,
            sorted([name for name in candidate_globals if "Filter" in name or name == "cconst"])
        ))
        if candidate_globals.get("CollisionFilterInfo") is not None:
            globals_from_camera = candidate_globals
        if getattr(module, "CollisionFilterInfo", None) is not None and not globals_from_camera:
            globals_from_camera = getattr(module, "__dict__", {})
        if candidate_globals.get("cconst") is not None and not globals_from_camera:
            globals_from_camera = candidate_globals

    cconst = globals_from_camera.get("cconst", None)
    collision_cls = globals_from_camera.get("CollisionFilterInfo", None)
    overlap_cls = globals_from_camera.get("OverlapFilterInfo", None)
    log("selected cconst={!r} CollisionFilterInfo={!r} OverlapFilterInfo={!r}".format(
        cconst, collision_cls, overlap_cls
    ))
    if collision_cls is not None:
        dump_callable("CollisionFilterInfo", collision_cls)
    if overlap_cls is not None:
        dump_callable("OverlapFilterInfo", overlap_cls)

    physics_consts = []
    if cconst is not None:
        for name in sorted(dir(cconst)):
            if name.startswith("PHYSICS"):
                try:
                    physics_consts.append((name, getattr(cconst, name)))
                except Exception:
                    pass
        log("physics_consts={}".format(physics_consts))

    arg_sets = [("empty", ()), ("zero", (0,)), ("one", (1,)), ("minus1", (-1,))]
    for name, value in physics_consts:
        arg_sets.append((name, (value,)))
    for name, value in physics_consts[:8]:
        arg_sets.append((name + "_0", (value, 0)))

    filters = []
    if collision_cls is not None:
        filters.extend(try_construct(collision_cls, arg_sets))
    if not filters:
        filters.extend((name, value) for name, value in physics_consts)

    entities = list(getattr(EM.EntityManager, "_entities", {}).items())
    spaces = [entity for _, entity in entities if isinstance(entity, Space)]
    active_space = next((space for space in spaces if "(D)" not in repr(space)), None)
    log("active_space={!r}".format(active_space))
    if active_space is not None:
        for method in ("ClosestRaycast", "RawRaycast", "AllRaycast", "RaycastWithPenetrate"):
            dump_callable("Space." + method, getattr(active_space, method, None))

    frame = MCamera.CaptureFrame()
    camera_pos = getattr(frame, "Position", None)
    log("camera={}".format(vec3(camera_pos)))

    robots = []
    for key, entity in entities:
        try:
            is_robot = bool(getattr(entity, "IsRobotCombatAvatar")())
        except Exception:
            is_robot = "robot" in type(entity).__name__.lower()
        if is_robot:
            robots.append((str(key), entity))
    log("robots={}".format(len(robots)))

    targets = []
    for key, entity in robots[:6]:
        model = getattr(entity, "model", None)
        if model is None:
            continue
        call(model, "MakeSureBones")
        head = call(model, "GetBoneWorldPosition", "biped Head")
        skeleton = call(model, "GetSkeleton")
        targets.append((key, entity, head, skeleton))
        log("target {} head={} skeleton={!r}".format(key, vec3(head), skeleton))

    if active_space is not None:
        for label, filt in filters[:40]:
            log("FILTER_TEST {}".format(label))
            for key, entity, head, skeleton in targets[:6]:
                if camera_pos is None or head is None:
                    continue
                result = call(active_space, "ClosestRaycast", camera_pos, head, filt)
                log("  {} ClosestRaycast -> {}".format(key, hit_summary(result)))
                result = call(active_space, "RawRaycast", camera_pos, 9999.0, filt, True, head, None)
                log("  {} RawRaycast -> {}".format(key, hit_summary(result)))
                result = call(active_space, "AllRaycast", camera_pos, 9999.0, filt, head, None)
                log("  {} AllRaycast -> {}".format(key, hit_summary(result)))
                result = call(active_space, "RaycastWithPenetrate", camera_pos, 9999.0, filt, True, head, None)
                log("  {} RaycastWithPenetrate -> {}".format(key, hit_summary(result)))
                log("  {} closestbone -> {}".format(
                    key, hit_summary(call(active_space, "ClosestRaycastBone", camera_pos, head))
                ))
except Exception:
    log("PROBE_EXC\n" + traceback.format_exc())

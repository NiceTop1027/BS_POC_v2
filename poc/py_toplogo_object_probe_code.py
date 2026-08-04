import inspect
import time
import traceback

LOG = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_toplogo_object_probe.log"


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def short(value, limit=1400):
    text = repr(value)
    if len(text) > limit:
        return text[:limit] + "...<cut>"
    return text


def describe(label, obj):
    log(f"{label}: repr={short(obj)} type={type(obj)!r}")
    try:
        names = [name for name in dir(obj) if not name.startswith("__")]
        log(f"{label}: names={short(names, 4000)}")
    except Exception as exc:
        log(f"{label}: dir FAIL {exc!r}")
        names = []

    for name in names:
        lower = name.lower()
        if not any(token in lower for token in ("text", "name", "label", "title", "hp", "bar", "color", "scale", "offset", "visible", "pos", "icon", "mark", "toplogo", "box")):
            continue
        try:
            value = getattr(obj, name)
        except Exception as exc:
            log(f"{label}.{name}: getattr FAIL {exc!r}")
            continue
        log(f"{label}.{name}: {short(value)} type={type(value)!r}")
        if callable(value):
            try:
                log(f"{label}.{name}: sig={inspect.signature(value)!r}")
            except Exception as exc:
                log(f"{label}.{name}: sig FAIL {exc!r}")
            code = getattr(value, "__code__", None)
            if code is not None:
                log(
                    f"{label}.{name}: code file={code.co_filename!r} first={code.co_firstlineno} "
                    f"args={code.co_varnames[:code.co_argcount + code.co_kwonlyargcount]!r}"
                )


def pos_of(entity):
    for name in ("position", "pos", "last_position"):
        try:
            value = getattr(entity, name)
            if callable(value):
                value = value()
            if value is not None:
                return tuple(float(x) for x in value[:3])
        except Exception:
            pass
    return None


def main():
    log("BEGIN " + str(time.time()))
    try:
        import common.EntityManager as EM

        entities = getattr(EM.EntityManager, "_entities", {})
        players = [(str(k), e) for k, e in entities.items() if getattr(e, "IsPlayerCombatAvatar", False)]
        robots = [(str(k), e) for k, e in entities.items() if getattr(e, "IsRobotCombatAvatar", False)]
        log(f"entities={len(entities)} players={len(players)} robots={len(robots)}")
        if not players or not robots:
            return

        pkey, player = players[0]
        rkey, robot = robots[0]
        log(f"player={pkey} {player!r}")
        log(f"robot={rkey} {robot!r} pos={pos_of(robot)!r}")

        describe("player", player)
        describe("robot", robot)

        template = None
        try:
            values = list(getattr(player, "common_mark_info", {}).values())
            if values:
                template = dict(values[0])
        except Exception as exc:
            log(f"template copy FAIL {exc!r}")
        if not template:
            template = {
                "camera_hit_min_opacity": 70,
                "min_opacity": 1.0,
                "camera_hit": False,
                "camera_hit_max_opacity": 255,
                "offset": (0, 3.0, 0),
                "visible_distance": 9999.0,
                "camera_hit_max_dis": 9999,
                "icon": 733,
                "cls": "ToplogoGunRefit",
                "fov_distance": 9999.0,
                "id": 9801,
                "max_opacity": 1.0,
                "camera_hit_min_dis": 0,
                "scene_on": True,
            }

        template.update(
            {
                "pos": pos_of(robot),
                "offset": (0, 3.15, 0),
                "visible_distance": 9999.0,
                "fov_distance": 9999.0,
                "scene_on": True,
                "min_opacity": 1.0,
                "max_opacity": 1.0,
                "minScale": 1.0,
                "maxScale": 1.0,
                "id": 9801,
                "text": "CTF 12m HP125",
                "name": "CTF 12m HP125",
                "title": "CTF 12m HP125",
                "label": "CTF 12m HP125",
            }
        )
        log(f"template={short(template, 5000)}")
        mark_id = "ctf_probe_toplogo_object"
        try:
            getattr(player, "common_mark_info", {})[mark_id] = template
        except Exception as exc:
            log(f"common_mark_info set FAIL {exc!r}")
        try:
            obj = player.CreateCommonMarkToplogoSceneOnly(mark_id, template)
            log(f"CreateCommonMarkToplogoSceneOnly returned {short(obj)}")
            describe("toplogo", obj)
        except Exception:
            log("CreateCommonMarkToplogoSceneOnly EXC\n" + traceback.format_exc())
    except Exception:
        log("EXC\n" + traceback.format_exc())
    finally:
        log("END")


main()

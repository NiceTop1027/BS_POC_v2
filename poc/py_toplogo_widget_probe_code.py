import inspect
import time
import traceback

LOG = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_toplogo_widget_probe.log"


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def short(value, limit=2400):
    text = repr(value)
    if len(text) > limit:
        return text[:limit] + "...<cut>"
    return text


def dump_obj(label, obj):
    log(f"{label}: repr={short(obj)} type={type(obj)!r}")
    try:
        names = [name for name in dir(obj) if not name.startswith("__")]
        log(f"{label}: names={short(names, 8000)}")
    except Exception as exc:
        log(f"{label}: dir FAIL {exc!r}")
        return
    tokens = ("text", "string", "label", "color", "visible", "opacity", "scale", "font", "size", "pos", "set", "update")
    for name in names:
        if not any(token in name.lower() for token in tokens):
            continue
        try:
            value = getattr(obj, name)
        except Exception as exc:
            log(f"{label}.{name}: getattr FAIL {exc!r}")
            continue
        log(f"{label}.{name}: {short(value, 900)} type={type(value)!r}")
        if callable(value):
            try:
                log(f"{label}.{name}: sig={inspect.signature(value)!r}")
            except Exception as exc:
                log(f"{label}.{name}: sig FAIL {exc!r}")


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
        player = players[0][1]
        robot = robots[0][1]
        mark_id = "ctf_probe_toplogo_widget"
        info = {
            "camera_hit_min_opacity": 70,
            "min_opacity": 1.0,
            "camera_hit": False,
            "camera_hit_max_opacity": 255,
            "offset": (0, 3.15, 0),
            "visible_distance": 9999.0,
            "camera_hit_max_dis": 9999,
            "icon": 733,
            "cls": "ToplogoGunRefit",
            "fov_distance": 9999.0,
            "id": 9802,
            "max_opacity": 1.0,
            "camera_hit_min_dis": 0,
            "pos": pos_of(robot),
            "scene_on": True,
            "minScale": 1.0,
            "maxScale": 1.0,
        }
        getattr(player, "common_mark_info", {})[mark_id] = info
        obj = player.CreateCommonMarkToplogoSceneOnly(mark_id, info)
        log(f"toplogo={short(obj)}")
        for attr in ("txt_distance", "mark_toplogo_widget", "panel_mark", "img_mark", "img_black", "mark_vx_panel_2", "mark_vx_panel_2_0"):
            try:
                dump_obj("toplogo." + attr, getattr(obj, attr))
            except Exception as exc:
                log(f"toplogo.{attr}: FAIL {exc!r}")

        for method_name in ("InitMarkToplogoUI", "UpdateMarkToplogo", "_UpdateMarkToplogo", "AdjustWidgetByScale", "SetOpacity"):
            try:
                method = getattr(obj, method_name)
                log(f"SOURCE {method_name}:\n" + inspect.getsource(method))
            except Exception as exc:
                log(f"SOURCE {method_name} FAIL {exc!r}")
    except Exception:
        log("EXC\n" + traceback.format_exc())
    finally:
        log("END")


main()

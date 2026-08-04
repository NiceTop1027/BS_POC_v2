import time
import traceback

LOG = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_enemy_label_state_probe.log"


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def short(value, limit=900):
    text = repr(value)
    if len(text) > limit:
        return text[:limit] + "...<cut>"
    return text


def dump_widget(label, widget):
    if widget is None:
        log(f"{label}: None")
        return
    log(f"{label}: obj={short(widget)} type={type(widget)!r}")
    for attr in (
        "text",
        "_last_text",
        "visible",
        "opacity",
        "scale",
        "color",
        "text_color",
        "hidden_reason",
        "force_show_reason",
        "init_font_size",
        "auto_fit_parent_size",
    ):
        try:
            log(f"{label}.{attr}={short(getattr(widget, attr))}")
        except Exception as exc:
            log(f"{label}.{attr}=FAIL {exc!r}")
    for method_name in ("GetWidth", "GetHeight", "getContentSize", "GetWorldPosition", "GetRealContentSize", "IsAncestorsVisible"):
        try:
            method = getattr(widget, method_name)
            log(f"{label}.{method_name}()={short(method())}")
        except Exception as exc:
            log(f"{label}.{method_name}()=FAIL {exc!r}")


def main():
    log("BEGIN " + str(time.time()))
    try:
        import common.EntityManager as EM

        entities = getattr(EM.EntityManager, "_entities", {})
        robots = [(str(k), e) for k, e in entities.items() if getattr(e, "IsRobotCombatAvatar", False)]
        log(f"robots={len(robots)}")
        for key, robot in robots[:3]:
            top = getattr(robot, "toplogo", None)
            log(f"robot={key} top={short(top)}")
            if top is None:
                continue
            for attr in ("text_dis_friend", "text_name_enemy", "text_name_friend", "txt_blood_num", "node_name_hp", "panel_enemy_bars", "toplogo_widget"):
                dump_widget(f"{key}.{attr}", getattr(top, attr, None))
    except Exception:
        log("EXC\n" + traceback.format_exc())
    finally:
        log("END")


main()

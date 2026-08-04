import builtins
import math
import time
import traceback

LOG = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\ctf_live_esp.log"
STATE_NAME = "_ctf_bloodstrike_live_esp_state"


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(f"{time.time():.3f} {message}\n")


def call(obj, name, *args):
    try:
        fn = getattr(obj, name)
    except Exception as exc:
        return False, f"missing:{exc!r}", None
    try:
        result = fn(*args)
        return True, "ok", result
    except Exception as exc:
        return False, repr(exc), None


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


def metric(entity, names, default=None):
    for name in names:
        try:
            value = getattr(entity, name)
            if callable(value):
                value = value()
            if value is not None:
                return value
        except Exception:
            pass
    return default


def stats_of(entity):
    hp = metric(entity, ("hp", "server_hp", "client_hp", "_hp"), None)
    maxhp = metric(entity, ("cur_maxhp", "maxhp", "base_maxhp", "server_maxhp"), None)
    armor = metric(entity, ("client_armor", "armor", "_client_armor", "server_armor"), None)
    maxarmor = metric(entity, ("base_maxarmor", "maxarmor", "server_maxarmor"), None)
    dead = bool(metric(entity, ("is_dead_state", "dead", "is_dead"), False))
    return {
        "hp": as_float(hp),
        "maxhp": as_float(maxhp),
        "armor": as_float(armor),
        "maxarmor": as_float(maxarmor),
        "dead": dead,
    }


def as_float(value):
    try:
        return float(value)
    except Exception:
        return None


def distance_m(a, b):
    if a is None or b is None:
        return None
    try:
        return math.sqrt(
            (a[0] - b[0]) * (a[0] - b[0])
            + (a[1] - b[1]) * (a[1] - b[1])
            + (a[2] - b[2]) * (a[2] - b[2])
        )
    except Exception:
        return None


def tier_for(distance):
    if distance is None:
        return "UNK", (0.90, 0.90, 0.90), 1.0
    if distance < 12:
        return "NEAR", (1.0, 0.12, 0.08), 1.35
    if distance < 28:
        return "MID", (1.0, 0.85, 0.05), 1.15
    return "FAR", (0.10, 0.95, 0.25), 1.0


def esp_scale_for(distance):
    if distance is None:
        return 0.52
    try:
        return max(0.38, min(0.74, 0.78 - float(distance) * 0.0085))
    except Exception:
        return 0.52


def recon_frame_scale_for(distance):
    if distance is None:
        return 0.40
    try:
        d = max(0.0, float(distance))
    except Exception:
        return 0.40
    # The frame is attached to the world marker, so use one perspective
    # falloff. The previous linear tuning made the close range box collapse.
    return max(0.24, min(0.96, 5.30 / max(1.0, d + 0.30)))


def vec3_of(value):
    if value is None:
        return None
    try:
        return tuple(float(getattr(value, axis)) for axis in ("x", "y", "z"))
    except Exception:
        pass
    try:
        return tuple(float(value[index]) for index in range(3))
    except Exception:
        return None


def body_bounds_of(entity):
    sources = []
    model = metric(entity, ("model",), None)
    if model is not None:
        sources.append(model)
    sources.append(entity)
    for source in sources:
        for method_name in ("GetWorldBound", "GetPrimWorldBound", "GetSkeletonDynamicWorldBound"):
            ok, _msg, bound = call(source, method_name)
            if not ok or bound is None:
                continue
            low = metric(bound, ("min", "Min", "lower", "Lower"), None)
            high = metric(bound, ("max", "Max", "upper", "Upper"), None)
            low = vec3_of(low)
            high = vec3_of(high)
            if low is None or high is None:
                continue
            if high[1] <= low[1] or high[0] <= low[0]:
                continue
            return {
                "min": low,
                "max": high,
                "width": high[0] - low[0],
                "height": high[1] - low[1],
                "depth": high[2] - low[2],
            }
    return None


def recon_frame_size_for(distance, bounds=None):
    # The source CSB is 200x300. Keep a stable avatar aspect ratio and scale
    # it from the model's actual world height, not from distance tiers.
    reference_height = 1.888
    body_height = reference_height
    if bounds is not None:
        try:
            body_height = max(0.80, min(2.40, float(bounds["height"])))
        except Exception:
            body_height = reference_height
    height = 204.0 * max(0.78, min(1.20, body_height / reference_height))
    width = height * 0.31
    return max(48, int(round(width))), max(128, int(round(height)))


def label_font_for(distance):
    scale = esp_scale_for(distance)
    if scale >= 0.68:
        return 11
    if scale >= 0.52:
        return 10
    return 9


def fmt_num(value, width=0):
    if value is None:
        return "?"
    if abs(value - round(value)) < 0.05:
        return str(int(round(value))).rjust(width)
    return f"{value:.1f}".rjust(width)


def get_entities():
    import common.EntityManager as EM

    entities = getattr(EM.EntityManager, "_entities", {})
    players = []
    robots = []
    for key, ent in list(entities.items()):
        try:
            if getattr(ent, "IsPlayerCombatAvatar", False):
                players.append((str(key), ent))
            elif getattr(ent, "IsRobotCombatAvatar", False):
                robots.append((str(key), ent))
        except Exception:
            pass
    return entities, players, robots


def hide_widget(widget):
    if widget is None:
        return
    for name, value in (("visible", False), ("opacity", 0), ("scale", 0.1), ("text", ""), ("_last_text", "")):
        try:
            setattr(widget, name, value)
        except Exception:
            pass
    for name, args in (
        ("SetFontSize", (1,)),
        ("SetWidthHeight", (1, 1)),
        ("SetHiddenReason", (True, 991731)),
    ):
        call(widget, name, *args)


def show_widget(widget, width=None, height=None, scale=1.0):
    if widget is None:
        return
    for name, value in (("visible", True), ("opacity", 255), ("scale", scale), ("hidden_reason", 0)):
        try:
            setattr(widget, name, value)
        except Exception:
            pass
    for name, args in (
        ("SetHiddenReason", (False, 991731)),
        ("RemoveHiddenReason", (991731,)),
    ):
        call(widget, name, *args)
    if width is not None and height is not None:
        call(widget, "SetWidthHeight", width, height)


def force_widget_scale(widget, scale):
    if widget is None:
        return
    targets = [widget]
    try:
        raw = getattr(widget, "widget", None)
        if raw is not None and raw is not widget:
            targets.append(raw)
    except Exception:
        pass
    for target in targets:
        for name, value in (("scale", scale), ("scale_x", scale), ("scale_y", scale)):
            try:
                setattr(target, name, value)
            except Exception:
                pass
        for method_name, args in (
            ("SetScale", (scale,)),
            ("setScale", (scale,)),
            ("SetScaleX", (scale,)),
            ("SetScaleY", (scale,)),
            ("setScaleX", (scale,)),
            ("setScaleY", (scale,)),
        ):
            call(target, method_name, *args)


def raw_children(widget):
    try:
        raw = getattr(widget, "widget", widget)
    except Exception:
        raw = widget
    for name in ("getChildren", "GetChildren"):
        try:
            children = getattr(raw, name)()
            return list(children or [])
        except Exception:
            pass
    return []


def set_raw_position(node, x, y):
    targets = [node]
    try:
        raw = getattr(node, "widget", None)
        if raw is not None and raw is not node:
            targets.append(raw)
    except Exception:
        pass
    for target in targets:
        call(target, "setPosition", x, y)
        call(target, "SetPosition", x, y)
        call(target, "setPositionX", x)
        call(target, "setPositionY", y)
        call(target, "SetPositionX", x)
        call(target, "SetPositionY", y)


def fit_recon_panel_images(panel, width, height):
    for child in raw_children(panel):
        try:
            name = child.getName()
        except Exception:
            name = ""
        if name and not str(name).startswith("img_bg"):
            continue
        call(child, "setVisible", True)
        call(child, "setScale9Enabled", True)
        call(child, "setContentSize", (width, height))
        set_raw_position(child, width * 0.5, height * 0.5)
        call(child, "setScaleX", width / 200.0)
        call(child, "setScaleY", height / 300.0)


def tune_recon_frame(robot, distance):
    frame = getattr(robot, "recon_drone_frame_top_logo", None)
    if frame is None:
        return None
    node = getattr(frame, "ui_node_top_logo", None)
    if node is None:
        return None

    bounds = body_bounds_of(robot)
    scale = recon_frame_scale_for(distance)
    box_w, box_h = recon_frame_size_for(distance, bounds)
    try:
        node.MIN_SCALE = 0.18
        node.MAX_SCALE = 1.10
    except Exception:
        pass
    call(node, "CancelScaleTickTimer")
    show_widget(node, None, None, 1.0)
    force_widget_scale(node, 1.0)

    panels = []
    panel = getattr(node, "panel_frame", None)
    if panel is not None:
        panels.append(panel)
    for method_name in ("seek", "child", "childex"):
        try:
            found = getattr(node, method_name)("panel_frame")
        except Exception:
            continue
        if found is not None and found not in panels:
            panels.append(found)

    for panel in panels:
        show_widget(panel, box_w, box_h, scale)
        # The marker is anchored near the avatar's root. Move the box centre
        # upward by a fraction of its own height so it spans head to feet.
        set_raw_position(panel, 0.0, box_h * 0.17)
        fit_recon_panel_images(panel, box_w, box_h)
        force_widget_scale(panel, scale)

    return scale, box_w, box_h


def tune_enemy_toplogo(robot, distance, stats):
    top = metric(robot, ("toplogo",), None)
    if top is None:
        return
    show_widget(getattr(top, "toplogo_widget", None), None, None, 1.0)
    show_widget(getattr(top, "node_name_hp", None), 92, 24, 1.0)
    label = make_box_label(0, distance, stats)
    for attr in ("text_dis_friend", "text_name_enemy"):
        info_text = getattr(top, attr, None)
        if info_text is not None:
            set_text_widget(info_text, label, (0.92, 0.92, 0.90), label_font_for(distance))
    for attr in (
        "text_name_friend",
        "teammate_txt_num",
        "txt_blood_num",
        "node_blood_num",
        "node_title",
        "img_hero_achievement_level",
        "img_low_hp_emma",
    ):
        hide_widget(getattr(top, attr, None))
    for attr in ("enemy_hp_bar", "enemy_hp_bar_bg", "panel_enemy_bars", "img_enemy_hp_fade", "img_enemy_hp_fade_1", "img_enemy_hp_transition"):
        widget = getattr(top, attr, None)
        if widget is not None:
            try:
                widget.scale = max(0.38, min(0.72, esp_scale_for(distance)))
            except Exception:
                pass


def ensure_toplogo(state, key, robot, distance=None, stats=None):
    events = []
    pos = pos_of(robot)
    if stats is None:
        stats = stats_of(robot)

    ok, msg, before = call(robot, "IsShootingRangeToplogoReady")
    events.append(f"ready_before={before!r}" if ok else f"ready_before_fail={msg}")

    for name, args in (
        ("EnsureShootingRangeToplogo", ()),
        ("ShowEnemyToplogo", (True,)),
        ("SetToplogoVisible", (None, 0.01, 0.01)),
        ("AddToplogoVisibleTick", ()),
        ("EnemyTopLogoTimer", ()),
        ("RefreshToplogo", ()),
        ("RefreshEnemyHpBar", (stats["hp"],)),
        ("RefreshEnemyArmorBar", (stats["armor"],)),
    ):
        ok, msg, result = call(robot, name, *args)
        events.append(f"{name}={result!r}" if ok else f"{name}_fail={msg}")

    if key not in state["recon_once"]:
        ok, msg, result = call(robot, "DrawReconDroneMarkFrame")
        events.append(f"DrawReconDroneMarkFrame={result!r}" if ok else f"DrawReconDroneMarkFrame_fail={msg}")
        if ok:
            state["recon_once"].add(key)

    ok, msg, after = call(robot, "IsShootingRangeToplogoReady")
    events.append(f"ready_after={after!r}" if ok else f"ready_after_fail={msg}")
    tune_enemy_toplogo(robot, distance, stats)
    frame_info = tune_recon_frame(robot, distance)
    if frame_info is not None:
        frame_scale, frame_w, frame_h = frame_info
        events.append(f"frame={frame_w}x{frame_h}@{frame_scale:.3f}")

    last = state["last_robot_log"].get(key, 0)
    if key not in state["seen"] or state["tick"] - last >= 20:
        state["last_robot_log"][key] = state["tick"]
        state["seen"].add(key)
        log(f"ROBOT key={key} pos={pos!r} stats={stats!r} " + " ".join(events))


def clone_common_mark_template(player, idx, pos, distance):
    tier, _color, _scale = tier_for(distance)
    scale = esp_scale_for(distance)
    template = None
    try:
        values = list(getattr(player, "common_mark_info", {}).values())
        if values:
            template = dict(values[0])
    except Exception:
        template = None
    if not template:
        template = {
            "camera_hit_min_opacity": 70,
            "min_opacity": 1.0,
            "camera_hit": False,
            "camera_hit_max_opacity": 255,
            "offset": (0, 2.5, 0),
            "visible_distance": 9999.0,
            "camera_hit_max_dis": 9999,
            "icon": 733,
            "cls": "ToplogoGunRefit",
            "fov_distance": 9999.0,
            "id": 9000 + idx,
            "max_opacity": 1.0,
            "camera_hit_min_dis": 0,
            "scene_on": True,
        }
    template.update(
        {
            "pos": pos,
            "offset": (
                0,
                (2.45 if tier == "NEAR" else 2.25 if tier == "MID" else 2.05)
                + ((idx % 3) - 1) * 0.14,
                0,
            ),
            "visible_distance": 9999.0,
            "fov_distance": 9999.0,
            "scene_on": True,
            "min_opacity": 1.0,
            "max_opacity": 1.0,
            "minScale": scale,
            "maxScale": scale,
            "id": 9000 + idx,
        }
    )
    return template


def color255(color):
    return tuple(max(0, min(255, int(round(value * 255)))) for value in color) + (255,)


def make_box_label(idx, distance, stats):
    hp = fmt_num(stats["hp"])
    armor = fmt_num(stats["armor"])
    if distance is None:
        dist = "??m"
    elif distance < 10:
        dist = f"{distance:.1f}m"
    else:
        dist = f"{distance:.0f}m"
    dead = " DOWN" if stats["dead"] else ""
    if stats["armor"] and stats["armor"] > 0:
        return f"{hp}hp {armor}ar {dist}{dead}"
    return f"{hp}hp {dist}{dead}"


def set_text_widget(widget, text, color, font_size):
    rgba = color255(color)
    rgb = rgba[:3]
    for name, value in (("text", text), ("_last_text", text), ("visible", True), ("opacity", 255), ("scale", 1.0)):
        try:
            setattr(widget, name, value)
        except Exception:
            pass
    for name, args in (
        ("SetHiddenReason", (False, 991731)),
        ("SetFontSize", (font_size,)),
        ("SetForceOneLineForSingleWord", (True,)),
        ("SetAutoFitParentSize", (True, 1)),
        ("SetWidth", (82,)),
        ("SetTextColorByList", (rgba,)),
    ):
        call(widget, name, *args)
    try:
        widget.text_color = rgba
    except Exception:
        pass
    try:
        widget.color = rgb
    except Exception:
        pass


def tint_widget(widget, color, opacity=255):
    rgba = color255(color)
    rgb = rgba[:3]
    for name, args in (
        ("SetTextColorByList", (rgba,)),
        ("SetVertexColor", (True, rgba, rgba, rgba, rgba)),
    ):
        call(widget, name, *args)
    try:
        widget.color = rgb
    except Exception:
        pass
    try:
        widget.opacity = opacity
    except Exception:
        pass


def hide_marker_art(obj):
    for attr in ("img_mark", "img_black", "img_loading", "mark_vx_panel_2", "mark_vx_panel_2_0"):
        widget = getattr(obj, attr, None)
        if widget is None:
            continue
        for name, value in (("visible", False), ("opacity", 0), ("scale", 0.1)):
            try:
                setattr(widget, name, value)
            except Exception:
                pass
        call(widget, "SetWidthHeight", 1, 1)


def apply_mark_label(state, mark_id, idx, obj, distance, stats):
    tier, _color, _scale = tier_for(distance)
    scale = esp_scale_for(distance)
    color = (0.92, 0.92, 0.90)
    label = make_box_label(idx, distance, stats)
    hide_marker_art(obj)
    text = getattr(obj, "txt_distance", None)
    if text is not None:
        set_text_widget(text, label, color, label_font_for(distance))
    try:
        obj.AdjustWidgetByScale(scale)
    except Exception:
        pass
    old_label = state["mark_labels"].get(mark_id)
    old_tier = state["mark_tiers"].get(mark_id)
    if old_label is None or old_tier != tier or state["tick"] % 120 == 0:
        state["mark_labels"][mark_id] = label
        state["mark_tiers"][mark_id] = tier
        log(f"BOX_LABEL mark_id={mark_id} label={label!r} tier={tier} color={color!r}")


def ensure_common_mark(state, player, key, idx, pos, distance, stats):
    if not player or pos is None:
        return
    mark_id = "ctf_esp_" + key.replace("/", "_").replace("+", "_")
    info = clone_common_mark_template(player, idx, pos, distance)
    try:
        getattr(player, "common_mark_info", {})[mark_id] = info
    except Exception:
        pass

    obj = state["mark_objects"].get(mark_id)
    if obj is None:
        ok0, _msg0, existing = call(player, "GetCommonMarkToplogo", mark_id)
        if ok0 and existing is not None:
            obj = existing
        else:
            ok1, msg1, obj = call(player, "CreateCommonMarkToplogoSceneOnly", mark_id, info)
            if ok1 and obj is not None:
                state["mark_objects"][mark_id] = obj
                state["marks"].add(mark_id)
            log(
                f"MARK_CREATE key={key} mark_id={mark_id} pos={pos!r} "
                f"CreateCommonMarkToplogoSceneOnly={'ok' if ok1 else msg1} "
                f"res={obj!r}"
            )
            if obj is None:
                return
        state["mark_objects"][mark_id] = obj
        state["marks"].add(mark_id)

    try:
        obj.mark_info = info
    except Exception:
        pass
    try:
        obj.mark_toplogo_pos = (pos[0], pos[1] + info.get("offset", (0, 3.0, 0))[1], pos[2])
    except Exception:
        pass
    if state["tick"] - state["mark_refresh"].get(mark_id, 0) >= 4:
        state["mark_refresh"][mark_id] = state["tick"]
        call(obj, "UpdateMarkToplogo")
        call(obj, "_UpdateMarkToplogo")
    apply_mark_label(state, mark_id, idx, obj, distance, stats)
    if state["tick"] % 80 == 0:
        log(
            f"MARK_UPDATE key={key} mark_id={mark_id} pos={pos!r} "
            f"label={state['mark_labels'].get(mark_id)!r}"
        )


def set_vec3(vec, values):
    vec.x = float(values[0])
    vec.y = float(values[1])
    vec.z = float(values[2])


def set_vec2(vec, values):
    vec.x = float(values[0])
    vec.y = float(values[1])


def make_label(idx, distance, stats):
    tier, _color, _scale = tier_for(distance)
    hp = fmt_num(stats["hp"])
    maxhp = fmt_num(stats["maxhp"])
    armor = fmt_num(stats["armor"])
    dist = "??.?m" if distance is None else f"{distance:04.1f}m"
    dead = " DOWN" if stats["dead"] else ""
    return f"T{idx + 1} {tier} {dist} HP {hp}/{maxhp} AR {armor}{dead}"


def make_world_label(idx, distance, stats):
    tier, _color, _scale = tier_for(distance)
    tier_code = {"NEAR": "N", "MID": "M", "FAR": "F"}.get(tier, "?")
    hp = fmt_num(stats["hp"])
    armor = fmt_num(stats["armor"])
    dist = "??m" if distance is None else f"{distance:.1f}m"
    return f"T{idx + 1} {tier_code} {dist} H{hp} A{armor}"


def slot_for_distance(distance):
    tier, _color, _scale = tier_for(distance)
    if tier == "NEAR":
        return 0
    if tier == "MID":
        return 1
    if tier == "FAR":
        return 2
    return 3


def ensure_harm_text(state, key, idx, robot, player_pos):
    pos = pos_of(robot)
    if pos is None:
        return
    last = state["text_refresh"].get(key, 0)
    if state["tick"] - last < 4:
        return
    state["text_refresh"][key] = state["tick"]

    try:
        import MUI

        stats = stats_of(robot)
        distance = distance_m(player_pos, pos)
        tier, color, scale = tier_for(distance)
        label = make_world_label(idx, distance, stats)
        param = MUI.HarmTextParam()
        param.harmText = label
        param.fontName = "Arial"
        param.fontSize = 14.0 if tier != "NEAR" else 17.0
        param.fovDistance = 9999.0
        param.accScale = scale
        param.scale = scale
        param.localZ = 0
        param.fontIndex = 0
        param.type = 0
        set_vec3(param.worldPos, (pos[0], pos[1] + 2.45, pos[2]))
        set_vec3(param.color, color)
        set_vec3(param.strokeColor, (0.0, 0.0, 0.0))
        set_vec2(param.offset, (((idx % 3) - 1) * 34.0, -26.0 - (idx // 3) * 18.0))
        harm_id = MUI.CreateHarmText0(param)
        state["harm_ids"][key] = harm_id
        if key not in state["text_seen"] or state["tick"] % 40 == 0:
            state["text_seen"].add(key)
            log(f"TEXT key={key} id={harm_id!r} label={label!r} pos={pos!r} color={color!r}")
    except Exception:
        log(f"TEXT_FAIL key={key}\n" + traceback.format_exc())


def cleanup_probe_texts():
    import MUI

    for key in [
        "ctf_screen_probe",
        "ctf_hud_probe_1",
        "ctf_hud_probe_2",
        "ctf_hud_probe_3",
        "ctf_hud_probe_4",
        "ctf_hud_probe_5",
        "ctf_hud_probe_6",
        "ctf_hud_probe_7",
        "ctf_hud_probe_8",
        "ctf_hud_probe_9",
        "ctf_hud_probe_10",
        "ctf_hud_probe_11",
        "ctf_hud_probe_12",
        "ctf_hud_probe_13",
        "ctf_hud_probe_14",
        "ctf_hud_probe_15",
        "ctf_hud_probe_16",
        "ctf_esp_hud_header",
    ]:
        try:
            MUI.RemoveScreenText(key)
        except Exception:
            pass
    for idx in range(10):
        try:
            MUI.RemoveScreenText(f"ctf_esp_hud_row_{idx}")
        except Exception:
            pass


def cleanup_common_marks(old_state=None):
    try:
        _entities, players, _robots = get_entities()
    except Exception as exc:
        log(f"cleanup common marks get_entities failed: {exc!r}")
        return
    if not players:
        return

    player = players[0][1]
    mark_ids = set()
    if isinstance(old_state, dict):
        try:
            mark_ids.update(str(key) for key in old_state.get("marks", set()))
        except Exception:
            pass
        try:
            mark_ids.update(str(key) for key in old_state.get("mark_objects", {}).keys())
        except Exception:
            pass

    try:
        for key in list(getattr(player, "common_mark_info", {}).keys()):
            text = str(key)
            if text.startswith("ctf_esp_") or text.startswith("ctf_probe_toplogo_"):
                mark_ids.add(text)
    except Exception:
        pass

    for mark_id in sorted(mark_ids):
        for name in ("DestroyCommonMarkToplogoSceneOnly", "DestroyCommonMarkToplogo"):
            call(player, name, mark_id)
        try:
            getattr(player, "common_mark_info", {}).pop(mark_id, None)
        except Exception:
            pass

    if isinstance(old_state, dict):
        for obj in list(old_state.get("mark_objects", {}).values()):
            call(obj, "Destroy")

    if mark_ids:
        log(f"cleanup common marks removed={sorted(mark_ids)!r}")


def tick():
    state = getattr(builtins, STATE_NAME)
    state["tick"] += 1
    try:
        entities, players, robots = get_entities()
        player = players[0][1] if players else None
        player_pos = pos_of(player) if player else None

        if state["tick"] == 1 or len(robots) != state.get("last_robot_count") or state["tick"] % 40 == 0:
            player_rows = [(k, pos_of(e)) for k, e in players]
            robot_rows = [
                (k, pos_of(e), distance_m(player_pos, pos_of(e)), stats_of(e))
                for k, e in robots
            ]
            log(
                f"TICK n={state['tick']} total={len(entities)} "
                f"players={player_rows!r} robots={robot_rows!r}"
            )
            state["last_robot_count"] = len(robots)

        for idx, (key, robot) in enumerate(robots):
            pos = pos_of(robot)
            dist = distance_m(player_pos, pos)
            stats = stats_of(robot)
            ensure_toplogo(state, key, robot, dist, stats)
    except Exception:
        log("TICK_EXC\n" + traceback.format_exc())


def tick_any(*args, **kwargs):
    tick()


def timer_owner():
    entities, players, robots = get_entities()
    for _key, ent in players:
        if hasattr(ent, "add_repeat_timer"):
            return ent
    for _key, ent in entities.items():
        if hasattr(ent, "add_repeat_timer"):
            return ent
    return None


def install():
    old = getattr(builtins, STATE_NAME, None)
    if isinstance(old, dict):
        old_timer = old.get("timer_id")
        old_owner = old.get("timer_owner")
        if old_timer is not None and old_owner is not None:
            try:
                old_owner.cancel_timer(old_timer)
                log(f"old timer removed id={old_timer!r}")
            except Exception as exc:
                log(f"old timer remove failed id={old_timer!r} exc={exc!r}")

    state = {
        "started": time.time(),
        "tick": 0,
        "timer_id": None,
        "timer_owner": None,
        "seen": set(),
        "marks": set(),
        "mark_objects": {},
        "mark_labels": {},
        "mark_tiers": {},
        "recon_once": set(),
        "harm_ids": {},
        "text_seen": set(),
        "text_refresh": {},
        "mark_refresh": {},
        "last_robot_log": {},
        "last_robot_count": None,
    }
    setattr(builtins, STATE_NAME, state)

    try:
        cleanup_probe_texts()
    except Exception as exc:
        log(f"cleanup probe texts failed: {exc!r}")
    try:
        cleanup_common_marks(old)
    except Exception as exc:
        log(f"cleanup common marks failed: {exc!r}")
    tick()
    owner = timer_owner()
    if owner is None:
        log("INSTALL_FAILED no entity timer owner")
        return
    try:
        timer_id = owner.add_repeat_timer(0.25, tick_any)
        state["timer_id"] = timer_id
        state["timer_owner"] = owner
        log(f"INSTALL_OK owner={owner!r} timer_id={timer_id!r}")
    except Exception as exc:
        log(f"INSTALL_FAILED owner={owner!r} exc={exc!r}")


try:
    install()
except Exception:
    log("INSTALL_EXC\n" + traceback.format_exc())

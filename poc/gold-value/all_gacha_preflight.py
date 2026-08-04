import json

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\all_gacha_preflight.log"


def safe_call(func, *args):
    try:
        return func(*args)
    except BaseException as error:
        return "<failed %r>" % (error,)


def normalized(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(key): normalized(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [normalized(item) for item in value]
    return repr(value)


def cost_for(gacha_module, setting, times):
    try:
        costs = gacha_module._GetMoneyDictByGachaSettingData(setting, times)
        return normalized(costs)
    except BaseException as error:
        return "<failed %r>" % (error,)


def extract_ids(value):
    if isinstance(value, bool):
        return []
    if isinstance(value, int):
        return [value]
    if isinstance(value, dict):
        if "id" in value:
            try:
                return [int(value["id"])]
            except (TypeError, ValueError):
                return []
        result = []
        for item in value.values():
            if isinstance(item, (list, tuple, set, dict)):
                result.extend(extract_ids(item))
        return result
    if isinstance(value, (list, tuple, set)):
        result = []
        for item in value:
            result.extend(extract_ids(item))
        return result
    return []


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    from common.EntityManager import EntityManager
    gacha_module = __import__("gclient.gamesystem.entities.avatarmembers.cimp_gacha", fromlist=["*"])

    player = next(entity for _, entity in EntityManager._entities.items()
                  if type(entity).__name__ == "PlayerAvatar")
    getter_names = (
        "GetOnlyGachaList",
        "GetGachaShelfList",
        "GetGachaSettingShelfList",
        "GetActCacheGachaIds",
        "GetActNewPlayerGachaIds",
        "GetActRollNoCycleIds",
        "GetActGachaPreSaleIds",
    )
    groups = {}
    all_ids = set()
    for name in getter_names:
        value = safe_call(getattr(player, name))
        values = sorted(set(extract_ids(value)))
        groups[name] = {"ids": values, "raw": normalized(value)}
        all_ids.update(values)

    report = {
        "gold": int(player.yuanbao),
        "server_random_ticket_present": bool(getattr(player, "server_random_ticket", None)),
        "groups": groups,
        "gachas": [],
    }
    for gacha_id in sorted(all_ids):
        setting = gacha_module.gacha_setting_data.data.get(gacha_id)
        if not setting:
            report["gachas"].append({"id": gacha_id, "setting": None})
            continue
        selected = {key: setting.get(key) for key in (
            "id", "name", "draw_type", "cls_name", "act_gacha", "real_gacha",
            "is_minipool", "cache_one_shot", "first_cost_id", "first_cost_count",
            "cost_id", "cost_count", "ten_cost_id", "ten_cost_count", "level_id",
            "begin_time", "end_time", "max_roll_times", "is_linkage") if key in setting}
        report["gachas"].append({
            "id": gacha_id,
            "setting": normalized(selected),
            "roll_count": safe_call(player.GetGachaRollCount, gacha_id),
            "can_buy_one": safe_call(player.CheckCanBuyGacha, gacha_id, 1),
            "cost_one": cost_for(gacha_module, setting, 1),
            "cost_ten": cost_for(gacha_module, setting, 10),
        })
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n")
except BaseException as error:
    with open(out, "a", encoding="utf-8") as handle:
        handle.write("FAIL " + repr(error) + "\n")
open(out, "a", encoding="utf-8").write("END\n")

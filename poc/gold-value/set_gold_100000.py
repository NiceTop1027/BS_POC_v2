out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\set_gold_100000.log"
target_gold = 100000


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    from common.EntityManager import EntityManager
    money_module = __import__("gclient.gamesystem.entities.avatarmembers.cimp_money", fromlist=["*"])

    entities = list(getattr(EntityManager, "_entities", {}).items())
    player = next(entity for _, entity in entities if type(entity).__name__ == "PlayerAvatar")
    before = {
        "total": int(player.yuanbao),
        "free": int(player.free_yuanbao),
        "pay": int(player.pay_yuanbao),
        "limit": int(player.limit_yuanbao),
    }
    required_free = target_gold - before["pay"] - before["limit"]
    if required_free < 0:
        raise RuntimeError("Existing paid and limited Gold exceeds target: %r" % (before,))

    player.free_yuanbao = required_free

    after = {
        "total": int(player.yuanbao),
        "free": int(player.free_yuanbao),
        "pay": int(player.pay_yuanbao),
        "limit": int(player.limit_yuanbao),
    }
    money_type = money_module.consts.EMoneyType_YUANBAO
    money_lookup = int(player.GetMoneyByMoneyType(money_type))
    log("BEFORE=" + repr(before))
    log("AFTER=" + repr(after))
    log("GET_MONEY_BY_TYPE=" + str(money_lookup))
    if after["total"] != target_gold or money_lookup != target_gold:
        raise RuntimeError("Gold verification failed: after=%r lookup=%r" % (after, money_lookup))
    log("SUCCESS target_gold=" + str(target_gold))
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

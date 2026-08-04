out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\verify_gold.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    from common.EntityManager import EntityManager
    money_module = __import__("gclient.gamesystem.entities.avatarmembers.cimp_money", fromlist=["*"])

    player = next(entity for _, entity in EntityManager._entities.items()
                  if type(entity).__name__ == "PlayerAvatar")
    total = int(player.yuanbao)
    lookup = int(player.GetMoneyByMoneyType(money_module.consts.EMoneyType_YUANBAO))
    values = {
        "total": total,
        "free": int(player.free_yuanbao),
        "pay": int(player.pay_yuanbao),
        "limit": int(player.limit_yuanbao),
        "lookup": lookup,
    }
    log("VALUES=" + repr(values))
    if total != 100000 or lookup != 100000:
        raise RuntimeError("Expected 100000, got %r" % (values,))
    log("SUCCESS")
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

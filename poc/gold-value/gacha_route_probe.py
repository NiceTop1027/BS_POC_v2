import dis

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\gacha_route_probe.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


def report_method(cls, method_name):
    for owner in cls.__mro__:
        if method_name not in owner.__dict__:
            continue
        value = owner.__dict__[method_name]
        if not callable(value):
            return
        code = getattr(value, "__code__", None)
        names = tuple(code.co_names) if code else ()
        consts = tuple(item for item in (code.co_consts if code else ()) if isinstance(item, str))
        log("METHOD class=%s owner=%s name=%s names=%r consts=%r" % (
            cls.__name__, owner.__name__, method_name, names, consts))
        try:
            log(dis.Bytecode(value).dis())
        except BaseException as error:
            log("DIS_FAIL %r" % (error,))
        return


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    from common.EntityManager import EntityManager
    gacha_module = __import__("gclient.gamesystem.entities.avatarmembers.cimp_gacha", fromlist=["*"])
    player = next(entity for _, entity in EntityManager._entities.items()
                  if type(entity).__name__ == "PlayerAvatar")

    seen = set()
    for gacha_id in sorted(player.GetOnlyGachaList()):
        setting = gacha_module.gacha_setting_data.data[gacha_id]
        cls_name = setting.get("cls_name")
        if not cls_name:
            log("GACHA id=%s name=%r route=NO_UI_CLASS" % (gacha_id, setting.get("name")))
            continue
        module_part, class_part = cls_name.rsplit(".", 1)
        module_name = "gclient.gamesystem.uihall.uimall." + module_part
        key = (module_name, class_part)
        log("GACHA id=%s name=%r draw_type=%r class=%s" % (
            gacha_id, setting.get("name"), setting.get("draw_type"), cls_name))
        if key in seen:
            continue
        seen.add(key)
        try:
            module = __import__(module_name, fromlist=[class_part])
            cls = getattr(module, class_part)
            log("CLASS=%s MRO=%r" % (cls_name, tuple(owner.__name__ for owner in cls.__mro__)))
            for method_name in ("_BuyGacha", "OnBuyConfirm", "OnBuy", "BuyConfirm", "OnBuySingle", "OnBuyTen"):
                report_method(cls, method_name)
        except BaseException as error:
            log("CLASS_FAIL %s %r" % (cls_name, error))
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

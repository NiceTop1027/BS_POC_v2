import dis
import inspect

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\gacha_ui_contract_probe.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


def report(owner, name, value):
    try:
        code = value.__code__
        names = set(code.co_names)
    except BaseException:
        names = set()
    lowered = name.lower()
    interesting = (
        "buy" in lowered or "roll" in lowered or "confirm" in lowered or
        {"BuyGacha", "CallServer", "OnGachaRoll", "OnGachaRollSkipAnim", "GachaRoll"}.intersection(names)
    )
    if not interesting:
        return
    try:
        signature = inspect.signature(value)
    except BaseException as error:
        signature = "<signature failed %r>" % (error,)
    log("FUNCTION %s.%s signature=%s names=%r" % (owner.__name__, name, signature, tuple(sorted(names))))
    try:
        log("DIS %s.%s\n%s" % (owner.__name__, name, dis.Bytecode(value).dis()))
    except BaseException as error:
        log("DIS_FAIL %s.%s %r" % (owner.__name__, name, error))


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    module = __import__(
        "gclient.gamesystem.uihall.uimall.mall_box_attribute_new_window", fromlist=["*"])
    cls = module.MallBoxAttributeDragonNewWindow
    log("CLASS=%r MRO=%r" % (cls, cls.__mro__))
    for owner in cls.__mro__:
        for name, value in owner.__dict__.items():
            if callable(value):
                report(owner, name, value)
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

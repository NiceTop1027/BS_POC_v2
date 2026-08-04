import inspect
import sys

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\gacha_ticket_probe.log"
needle = "server_random_ticket"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


def check_callable(label, value):
    code = getattr(value, "__code__", None)
    if not code or needle not in code.co_names:
        return
    try:
        signature = inspect.signature(value)
    except BaseException as error:
        signature = "<signature failed %r>" % (error,)
    log("REFERENCE %s signature=%s names=%r" % (label, signature, code.co_names))


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    from common.EntityManager import EntityManager

    player = next(entity for _, entity in EntityManager._entities.items()
                  if type(entity).__name__ == "PlayerAvatar")
    log("CURRENT=%r" % getattr(player, needle, None))
    log("PLAYER_TICKET_NAMES=%r" % [name for name in dir(player) if "ticket" in name.lower()])
    for owner in type(player).__mro__:
        for name, value in owner.__dict__.items():
            if callable(value):
                check_callable("%s.%s" % (owner.__name__, name), value)

    for module_name, module in tuple(sys.modules.items()):
        if not module_name.startswith(("gclient.", "gshare.")) or module is None:
            continue
        for name, value in getattr(module, "__dict__", {}).items():
            if callable(value):
                check_callable("%s.%s" % (module_name, name), value)
            elif isinstance(value, type):
                for method_name, method in getattr(value, "__dict__", {}).items():
                    if callable(method):
                        check_callable("%s.%s.%s" % (module_name, name, method_name), method)
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

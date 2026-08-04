import dis
import inspect
import sys

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\rpc_wire_probe.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


def report(label, value):
    try:
        signature = inspect.signature(value)
    except BaseException as error:
        signature = "<signature failed %r>" % (error,)
    log("FUNCTION %s signature=%s repr=%r" % (label, signature, value))
    try:
        log("DIS %s\n%s" % (label, dis.Bytecode(value).dis()))
    except BaseException as error:
        log("DIS_FAIL %s %r" % (label, error))


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    from common.EntityManager import EntityManager

    player = next(entity for _, entity in EntityManager._entities.items()
                  if type(entity).__name__ == "PlayerAvatar")
    proxy_module = __import__("engine.client.AsioServerProxy", fromlist=["*"])
    for label, value in (
        ("Player.CallServerOld", getattr(player, "CallServerOld", None)),
        ("Player.CallServer", getattr(player, "CallServer", None)),
        ("AsioServerProxy.call_rpc", getattr(proxy_module, "call_rpc", None)),
    ):
        if value is not None:
            report(label, value)
    for module in (sys.modules.get(type(player).__module__), proxy_module):
        if module is None:
            continue
        loader = getattr(module, "__loader__", None)
        log("MODULE %s loader=%r file=%r" % (module.__name__, loader, getattr(module, "__file__", None)))
        if loader and hasattr(loader, "get_source"):
            try:
                source = loader.get_source(module.__name__)
                log("SOURCE %s\n%s" % (module.__name__, source))
            except BaseException as error:
                log("SOURCE_FAIL %s %r" % (module.__name__, error))
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

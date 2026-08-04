import inspect
import sys

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\mainthread_contract_probe.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


def describe(label, obj):
    for name in dir(obj):
        lowered = name.lower()
        if not any(token in lowered for token in ("tick", "update", "frame", "sched", "dispatch", "thread", "task", "callback")):
            continue
        try:
            value = getattr(obj, name)
        except BaseException:
            continue
        if not callable(value):
            continue
        try:
            signature = inspect.signature(value)
        except BaseException as error:
            signature = "<signature failed %r>" % (error,)
        log("%s.%s signature=%s repr=%r" % (label, name, signature, value))


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    from common.EntityManager import EntityManager
    player = next(entity for _, entity in EntityManager._entities.items()
                  if type(entity).__name__ == "PlayerAvatar")
    describe("PLAYER", player)
    for index, cls in enumerate(type(player).__mro__):
        describe("MRO[%s]=%s" % (index, cls.__name__), cls)

    for module_name in (
        "engine.client",
        "engine.client.AsioServerProxy",
        "common.EntityManager",
        "gclient.framework.entities.avatar",
        "gclient.framework.ui.commonnodes.ui_popup_reward_exit_window",
    ):
        module = sys.modules.get(module_name)
        if module is not None:
            describe("MODULE=" + module_name, module)
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

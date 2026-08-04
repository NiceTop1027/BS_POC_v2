import builtins
import threading
import time

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\tick_mainthread_probe.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    from common.EntityManager import EntityManager

    player = next(entity for _, entity in EntityManager._entities.items()
                  if type(entity).__name__ == "PlayerAvatar")
    cls = type(player)
    original_tick = cls.tick
    state = {
        "installed_at": time.time(),
        "injected_thread": threading.get_ident(),
        "tick_thread": None,
        "tick_at": None,
        "cls": cls,
        "original_tick": original_tick,
    }

    def tick_once(self, dtime):
        if self is player and state["tick_thread"] is None:
            state["tick_thread"] = threading.get_ident()
            state["tick_at"] = time.time()
            cls.tick = original_tick
            log("TICK thread=%s at=%s" % (state["tick_thread"], state["tick_at"]))
        return original_tick(self, dtime)

    state["hook"] = tick_once
    builtins._ctf_tick_mainthread_probe = state
    cls.tick = tick_once
    log("INSTALLED thread=%s" % state["injected_thread"])
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

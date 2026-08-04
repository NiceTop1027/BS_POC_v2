import builtins
import sys
import threading
import time

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\timer_mainthread_probe.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    state = {
        "scheduled_at": time.time(),
        "injected_thread": threading.get_ident(),
        "callback_thread": None,
        "callback_at": None,
    }

    def scheduled_probe():
        state["callback_thread"] = threading.get_ident()
        state["callback_at"] = time.time()
        log("CALLBACK thread=%s at=%s" % (state["callback_thread"], state["callback_at"]))

    state["func"] = scheduled_probe
    builtins._ctf_timer_mainthread_probe = state
    timer = sys.modules["Timer"]
    timer.add_callback(0.1, False, scheduled_probe)
    log("SCHEDULED thread=%s" % state["injected_thread"])
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

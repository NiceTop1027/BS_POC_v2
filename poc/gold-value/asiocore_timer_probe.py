import builtins
import threading
import time

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\asiocore_timer_probe.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    import asiocore

    state = {
        "scheduled_at": time.time(),
        "injected_thread": threading.get_ident(),
        "callback_thread": None,
        "callback_at": None,
    }

    def callback(*args):
        state["callback_thread"] = threading.get_ident()
        state["callback_at"] = time.time()
        log("CALLBACK thread=%s at=%s args=%r" % (
            state["callback_thread"], state["callback_at"], args))

    state["callback"] = callback
    builtins._ctf_asiocore_timer_probe = state
    installed = None
    for timer_args in ((0.25, False, False, callback), (0.25, False, 0, callback), (0.25, callback)):
        try:
            asiocore.add_timer(*timer_args)
            installed = timer_args[:-1]
            break
        except BaseException as error:
            log("ADD_TIMER_FAIL args=%r error=%r" % (timer_args[:-1], error))
    if installed is None:
        raise RuntimeError("could not schedule engine timer")
    log("SCHEDULED thread=%s args=%r" % (state["injected_thread"], installed))
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

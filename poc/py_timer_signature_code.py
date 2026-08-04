import inspect
import time
import traceback

LOG = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_timer_signature.log"


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def describe(obj, name):
    try:
        fn = getattr(obj, name)
    except Exception as exc:
        log(f"{name}: getattr FAIL {exc!r}")
        return
    log(f"{name}: repr={fn!r} type={type(fn)!r}")
    try:
        log(f"{name}: sig={inspect.signature(fn)!r}")
    except Exception as exc:
        log(f"{name}: sig FAIL {exc!r}")
    code = getattr(fn, "__code__", None)
    if code:
        log(
            f"{name}: file={code.co_filename!r} first={code.co_firstlineno} "
            f"argc={code.co_argcount} vars={code.co_varnames[:code.co_argcount]!r} "
            f"defaults={getattr(fn, '__defaults__', None)!r}"
        )


def main():
    log("BEGIN " + str(time.time()))
    try:
        import asiocore_64
        for name in ("add_timer", "del_timer", "call_next_frame"):
            describe(asiocore_64, name)

        import common.EntityManager as EM
        entities = getattr(EM.EntityManager, "_entities", {})
        for key, ent in entities.items():
            log(f"entity {key!r} {ent!r} class={ent.__class__!r}")
            for name in ("add_timer", "add_repeat_timer", "cancel_timer"):
                describe(ent, name)
            break
    except Exception:
        log("EXC\n" + traceback.format_exc())
    finally:
        log("END")


main()

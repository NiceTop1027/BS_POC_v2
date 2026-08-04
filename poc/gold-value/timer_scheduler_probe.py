import inspect
import sys

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\timer_scheduler_probe.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


def short(value, limit=5000):
    try:
        text = repr(value)
    except BaseException as error:
        text = "<repr failed %r>" % (error,)
    return text[:limit] + ("..." if len(text) > limit else "")


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    ui_module = __import__(
        "gclient.framework.ui.commonnodes.ui_popup_reward_exit_window", fromlist=["*"])
    timer = ui_module.UIWindow.add_timer.__globals__["Timer"]
    log("TIMER=" + short(timer))
    log("TYPE=" + short(type(timer)))
    log("MODULE=" + str(getattr(timer, "__module__", None)))
    for name in ("add_callback", "cancel_timer", "update", "add_repeat_callback"):
        value = getattr(timer, name, None)
        if value is None:
            continue
        try:
            signature = inspect.signature(value)
        except BaseException as error:
            signature = "<signature failed %r>" % (error,)
        log("METHOD %s signature=%s value=%s" % (name, signature, short(value)))
        try:
            log("SOURCE %s\n%s" % (name, inspect.getsource(value)))
        except BaseException as error:
            log("SOURCE_FAIL %s %r" % (name, error))
    log("UI_MODULE_FILE=" + str(getattr(ui_module, "__file__", None)))
    for module_name, module in sorted(sys.modules.items()):
        if module and any(token in module_name.lower() for token in ("timer", "scheduler", "task")):
            log("LOADED=" + module_name + " FILE=" + str(getattr(module, "__file__", None)))
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

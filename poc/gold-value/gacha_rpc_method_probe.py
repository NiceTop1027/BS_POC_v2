import dis
import inspect

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\gacha_rpc_method_probe.log"


def log(message):
    with open(out, "a", encoding="utf-8") as handle:
        handle.write(str(message) + "\n")


def report(label, value):
    log("%s type=%r repr=%r module=%r" % (
        label, type(value), value, getattr(type(value), "__module__", None)))
    try:
        log("%s signature=%s" % (label, inspect.signature(value)))
    except BaseException as error:
        log("%s signature_fail=%r" % (label, error))
    for candidate_name, candidate in (("value", value), ("class.__call__", getattr(type(value), "__call__", None))):
        if candidate is None:
            continue
        try:
            log("DIS %s.%s\n%s" % (label, candidate_name, dis.Bytecode(candidate).dis()))
        except BaseException as error:
            log("DIS_FAIL %s.%s %r" % (label, candidate_name, error))
    try:
        log("%s dict=%r" % (label, getattr(value, "__dict__", None)))
    except BaseException as error:
        log("%s dict_fail=%r" % (label, error))


open(out, "w", encoding="utf-8").write("BEGIN\n")
try:
    from common.EntityManager import EntityManager

    player = next(entity for _, entity in EntityManager._entities.items()
                  if type(entity).__name__ == "PlayerAvatar")
    server = player.server
    method = getattr(server, "GachaRoll")
    report("SERVER", server)
    report("GachaRoll", method)
    log("SERVER_DIR=" + repr([name for name in dir(server) if "gacha" in name.lower() or "callback" in name.lower()]))
except BaseException as error:
    log("FAIL " + repr(error))
log("END")

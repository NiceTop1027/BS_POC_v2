import builtins

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\tick_hook_restore.log"

with open(out, "w", encoding="utf-8") as handle:
    state = getattr(builtins, "_ctf_tick_mainthread_probe", None)
    if state and state.get("cls") and state.get("original_tick"):
        state["cls"].tick = state["original_tick"]
        handle.write("RESTORED\n")
    else:
        handle.write("NO_HOOK\n")

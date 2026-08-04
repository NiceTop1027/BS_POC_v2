import builtins

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\tick_mainthread_result.log"

with open(out, "w", encoding="utf-8") as handle:
    handle.write("STATE=" + repr(getattr(builtins, "_ctf_tick_mainthread_probe", None)) + "\n")

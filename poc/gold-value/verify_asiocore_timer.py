import builtins

out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\gold-value\asiocore_timer_result.log"

with open(out, "w", encoding="utf-8") as handle:
    handle.write("STATE=" + repr(getattr(builtins, "_ctf_asiocore_timer_probe", None)) + "\n")

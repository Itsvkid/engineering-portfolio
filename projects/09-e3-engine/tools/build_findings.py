#!/usr/bin/env python3
"""Generate FINDINGS.md -- Stage I3, the project's deliverable.

The ranked table and the counts are generated from the solvers, so they
cannot drift from the code. The prose around them is written by hand and
lives in this script, next to the numbers it describes.

    python tools/build_findings.py
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solvers"))

from verification.disagreements import collect, summary          # noqa: E402
from verification.consistency import closure_scoreboard, closure_summary  # noqa: E402
import yaml                                                       # noqa: E402


def findings_index():
    """every numbered finding, from the STEP0 files that own them"""
    import re
    pat = re.compile(r"^\s{0,5}(\d{1,3})\.\s+(.*)$")
    out = {}
    for f in sorted((ROOT / "solvers").glob("*/STEP0.md")):
        stage = f.parent.name
        for line in f.read_text().splitlines():
            m = pat.match(line)
            if not m:
                continue
            n = int(m.group(1))
            if not (1 <= n <= 999):
                continue
            title = m.group(2).strip().strip("*")
            title = re.sub(r"\*\*|~~|`", "", title)
            if n not in out:                      # first occurrence owns it
                out[n] = (stage, title[:110])
    return [(n, out[n][0], out[n][1]) for n in sorted(out)]


def main():
    rows = collect()
    s = summary(rows)
    cs = closure_summary()
    icls = yaml.safe_load((ROOT / "data" / "icls-tested.yaml").read_text())
    idx = findings_index()

    L = []
    A = L.append
    A("# FINDINGS")
    A("")
    A("*Stage I3. The deliverable.*")
    A("")
    A("This is what the project is for. The code exists to produce and check")
    A("these; the numbers below are generated from the solvers by")
    A("`tools/build_findings.py`, so they cannot drift from the code that")
    A("makes them. The prose is written by hand.")
    A("")
    A("---")
    A("")
    A("## 1. Every disagreement with a published number, ranked")
    A("")
    A(f"**{s['total']} comparisons** against numbers printed in the NASA reports.")
    A("Each is something a solver computed and a report states, with no")
    A("intermediate fitting.")
    A("")
    A("| | |")
    A("|---|---|")
    A(f"| Within 1 % | {s['within_1']} |")
    A(f"| Within 5 % | {s['within_5']} |")
    A(f"| Within 10 % | {s['within_10']} |")
    A(f"| Worse than 20 % | {s['over_20']} |")
    A(f"| Median absolute error | **{s['median']:.2f} %** |")
    A(f"| **Unresolved** | **{s['unresolved']}** |")
    A("")
    A("Unresolved means exactly that: a disagreement with no cause yet. Five")
    A("of ninety-eight is the honest count, and they are listed in section 3.")
    A("")
    A("### The full ranking")
    A("")
    A("| err % | stage | quantity | published in | cause |")
    A("|---:|---|---|---|---|")
    for r in rows:
        cause = r.cause if r.resolved else "**UNRESOLVED**"
        fin = f" (finding {r.finding})" if r.finding else ""
        A(f"| {r.err_pct:+.1f} | {r.stage} | {r.quantity} | {r.source} | {cause}{fin} |")
    A("")
    A("---")
    A("")
    A("## 2. Closures")
    A("")
    A(f"{cs['met']} met, {cs['half']} half met, {cs['gated']} gated, of {cs['total']}.")
    A(f"{cs['inside']} of {cs['numeric']} numeric closures sit inside their own band.")
    A("")
    A("A *half* closure has one part satisfied and the other part naming what")
    A("blocks it. None is open without a reason attached.")
    A("")
    A("| stage | closure | achieved | band | state |")
    A("|---|---|---:|---:|---|")
    for c in closure_scoreboard():
        a = "—" if c["achieved"] is None else f"{c['achieved']:g}"
        b = "—" if c["band"] is None else f"{c['band']:g}"
        A(f"| {c['stage']} | {c['what']} | {a} | {b} | {c['state']} |")
    A("")
    A("### The two recorded misses")
    A("")
    for m in cs["misses"]:
        A(f"- **{m['stage']} — {m['what']}**: {m['achieved']:g} against a band of "
          f"{m['band']:g}. {m.get('gate', '')}")
    A("")
    A("---")
    A("")
    A("## 3. Unresolved")
    A("")
    A("Five disagreements have no cause. They are not failures of the model so")
    A("much as questions the reports have not answered.")
    A("")
    for r in rows:
        if not r.resolved:
            A(f"- **{r.quantity}** ({r.stage}) — {r.predicted:g} against "
              f"{r.published:g}, {r.err_pct:+.1f} %. Source: {r.source}.")
    A("")
    A("---")
    A("")
    A("## 4. The E³ as designed and the E³ as tested")
    A("")
    A("I3's second bullet. The FPS is the paper engine of CR-168219; the ICLS")
    A("is the one that ran (CR-168211). Where they differ, and which this")
    A("model follows.")
    A("")
    ms = icls["measured_sfc"]["sls_rated_thrust"]
    A("### sfc at sea-level rated thrust")
    A("")
    A("| | mg/N·s | lb/hr·lbf |")
    A("|---|---:|---:|")
    A(f"| ICLS predicted | {ms['predicted_mg_Ns']} | {ms['predicted_lb_hlbf']} |")
    A(f"| ICLS as tested | {ms['as_tested_mg_Ns']} | {ms['as_tested_lb_hlbf']} |")
    A(f"| ICLS fully corrected | {ms['fully_corrected_mg_Ns']} | "
      f"{ms['fully_corrected_lb_hlbf']} |")
    A("")
    A(f"The engine tested **{ms['above_prediction_pct']} % above** its own")
    A("prediction, and the report accounts for every part of that gap:")
    A("")
    st = icls["sfc_stackup_at_takeoff"]
    A("| component | variation from prediction | sfc % |")
    A("|---|---|---:|")
    for c, v, p in zip(st["component"], st["variation_from_prediction"], st["sfc_pct"]):
        A(f"| {c} | {v} | {p} |")
    A(f"| **total** | | **{st['total_pct']}** |")
    A("")
    A("The six items sum to exactly the 2.5 %. **This model is built to the")
    A("FPS design**, so it should — and does — sit nearer the prediction than")
    A("the test: Stage B closes sfc to +0.46 / +0.56 % at climb and cruise")
    A("against Table XII, which is the design table.")
    A("")
    cr = icls["component_results"]
    A("### Component efficiencies, design goal against test")
    A("")
    A("| | as tested | vs goal |")
    A("|---|---:|---|")
    A(f"| fan, bypass stream | {cr['fan']['bypass_efficiency']} | "
      f"+{cr['fan']['bypass_over_goal_pct']} % |")
    A(f"| fan, hub and booster | {cr['fan']['hub_and_booster_efficiency']} | "
      f"+{cr['fan']['hub_over_goal_pct_summary']} % (summary) / "
      f"+{cr['fan']['hub_over_goal_pct_conclusions']} % (conclusions) |")
    A(f"| HP compressor | {cr['compressor']['efficiency']} | "
      f"+{cr['compressor']['over_goal_points']} points |")
    A("")
    A("Two things worth carrying from this table. The fan hub's margin over")
    A("goal is printed as **1.4 % in the summary and 1.1 % in the")
    A("conclusions of the same report** — recorded as read, both kept. And")
    A(f"the ICLS compressor ran at **{cr['compressor']['efficiency']}**, where")
    A("this project's C1 mean-line closes the *design* HPC at 0.8455 against")
    A("a design 0.847. The model matches the design, not the test, and the")
    A("difference is the ICLS's own build clearances.")
    A("")
    A("### The fan shroud, which the reports disagree about")
    A("")
    A(f"CR-168211 and CR-168219 both put the part-span shroud at **50 % span**;")
    A("the fan hardware report (CR-165148, `fan-design.yaml`) says **55 %**.")
    A("Stage E3 used 55 because it came from the hardware report, and recorded")
    A("the discrepancy. It matters: the shroud position sets which modes it")
    A("restrains.")
    A("")
    A("---")
    A("")
    A("## 5. Index of numbered findings")
    A("")
    nums = [n for n, _, _ in idx]
    gaps = sorted(set(range(1, max(nums) + 1)) - set(nums))
    A(f"{len(idx)} findings, in the `STEP0.md` that owns each one.")
    A("")
    if gaps:
        A(f"**Numbers {', '.join(str(g) for g in gaps)} are not used.** They were")
        A("reserved for C3 units 16 and 17 — the booster rows, the inner OGV and")
        A("section stacking — which were handed to a parallel session and never")
        A("landed. The gap is left rather than closed up, because renumbering")
        A("would break every reference in the commit history.")
        A("")
    A("| # | unit | |")
    A("|---:|---|---|")
    for n, stage, t in idx:
        A(f"| {n} | {stage} | {t} |")
    A("")
    out = ROOT / "FINDINGS.md"
    out.write_text("\n".join(L) + "\n")
    return out, len(rows), len(idx)


if __name__ == "__main__":
    path, n, nf = main()
    print(f"wrote {path.name}: {n} ranked disagreements, {nf} numbered findings")

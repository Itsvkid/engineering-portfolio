"""Stage K unit K2: does the FPS hardware have the growth margin GE claims?

Unit F1 tabulated seventeen stresses against a printed allowable and found
every one with margin -- but **four at or within 2 % of the limit**: the
three LPT blade retainers (1.022, 1.011, 1.000) and the HPT stage-1 disk
dovetail (1.000, which the report itself calls *on the limit exactly*).

The fan report separately claims the hardware was sized with growth in
mind (`hub_radii_oversized_for_growth: true`), and the HPT report says the
rotor structure was designed for the growth engine with *the growth case
limiting throughout*. Both claims are testable against F1's table, and
they can disagree.

**The speed ratio is published, not inferred.** The growth requirements
print a corrected fan tip speed for each of three ratings against the
FPS's own, so the LP spool's ratio comes out of the same column of the
same table. `booster_speed_increase_pct: 11` agrees with it to a tenth of
a percent.

**The assumption, stated once:** every stress here is taken as
centrifugally dominated and scaled as N squared. Where a part also carries
gas bending this over-states the scaling -- unit E8 measured gas bending
at roughly half the resultant at an LPT blade root -- so what this
produces is a **bound**, not a prediction, and `is_a_bound` says so.

Eleven of F1's seventeen rows are on the HP spool, whose growth speed is
**not published anywhere transcribed**. They are out of scope and named,
rather than scaled by the LP ratio and hoped over.

STEP0.md, unit K2."""
from __future__ import annotations

import yaml

from e3cycle.cycle import DATA

#: which spool each of F1's parts runs on. The fan and LPT are low-spool;
#: the HPC and HPT are high-spool.
SPOOL = {
    "fan blade dovetail corner": "lp",
    "fan disk post corner": "lp",
    "fan disk, max": "lp",
    "LPT blade retainer 1": "lp",
    "LPT blade retainer 2": "lp",
    "LPT blade retainer 3": "lp",
    "HPT stage-1 disk dovetail": "hp",
}

#: the claim under test, and which parts it is actually about
GROWTH_CLAIM = dict(
    key="hub_radii_oversized_for_growth",
    src="fan-design.yaml requirements.growth_notes, CR-165148",
    value=True,
    covers=["fan blade dovetail corner", "fan disk post corner", "fan disk, max"],
    does_not_cover=["LPT blade retainer 1", "LPT blade retainer 2",
                    "LPT blade retainer 3"],
    why=("the claim is about hub RADII being oversized. A blade retainer is "
         "not a hub radius, and nothing published says the retainers were "
         "sized for growth"))


def _fan():
    return yaml.safe_load((DATA / "fan-design.yaml").read_text())


def speed_ratios():
    """LP spool, from the two printed corrected tip speeds."""
    r = _fan()["requirements"]
    fps, gro = r["fps"]["corrected_tip_speed_m_s"], r["growth"]["corrected_tip_speed_m_s"]
    out = []
    for i, (a, b) in enumerate(zip(fps, gro), start=1):
        out.append(dict(rating=i, fps_m_s=a, growth_m_s=b,
                        speed_ratio=b / a, stress_ratio=(b / a) ** 2))
    return out


def speed_cross_check():
    """The tip-speed ratio against the separately printed booster speed
    increase. Two statements about the same spool, in different units."""
    pct = _fan()["requirements"]["growth_notes"]["booster_speed_increase_pct"]
    r1 = speed_ratios()[0]["speed_ratio"]
    return dict(from_tip_speeds_pct=(r1 - 1) * 100, printed_pct=pct,
                agree_within_pct=abs((r1 - 1) * 100 - pct))


def spool_of(part):
    if part in SPOOL:
        return SPOOL[part]
    return "hp" if part.startswith("HPC") else "unknown"


def in_scope():
    """F1's rows, split by whether this unit can honestly touch them."""
    from materials.allowables import stage_e_margins
    lp, hp = [], []
    for r in stage_e_margins():
        (lp if spool_of(r["part"]) == "lp" else hp).append(r)
    return dict(lp=lp, hp=hp,
                hp_excluded_because=("no growth HP-spool speed is published "
                                     "in anything transcribed"))


def regrown(rating=1):
    """Each LP part's margin at growth speed, on the N-squared bound."""
    sr = next(s for s in speed_ratios() if s["rating"] == rating)
    k = sr["stress_ratio"]
    out = []
    for r in in_scope()["lp"]:
        grown = r["stress_MPa"] * k
        out.append(dict(
            part=r["part"], allowable_MPa=r["allowable_MPa"], basis=r["basis"],
            fps_stress_MPa=r["stress_MPa"], fps_margin=r["margin"],
            growth_stress_MPa=grown,
            growth_margin=r["allowable_MPa"] / grown,
            survives=r["allowable_MPa"] / grown >= 1.0,
            covered_by_claim=r["part"] in GROWTH_CLAIM["covers"]))
    return dict(rating=rating, stress_ratio=k, rows=out)


def verdict(rating=1):
    """The claim, tested: do the parts it covers keep margin, and do the
    parts it does not?"""
    g = regrown(rating)
    covered = [r for r in g["rows"] if r["covered_by_claim"]]
    not_covered = [r for r in g["rows"] if not r["covered_by_claim"]]
    return dict(
        rating=rating, stress_ratio=g["stress_ratio"],
        claim=GROWTH_CLAIM["key"],
        covered_all_survive=all(r["survives"] for r in covered),
        covered_worst_margin=min(r["growth_margin"] for r in covered),
        not_covered_all_survive=all(r["survives"] for r in not_covered),
        not_covered_worst_margin=min(r["growth_margin"] for r in not_covered),
        claim_holds_where_it_applies=all(r["survives"] for r in covered),
        is_a_bound=True,
        bound_note=("N-squared assumes centrifugal dominance. Unit E8 measured "
                    "gas bending at about half the resultant at an LPT blade "
                    "root, so for a part carrying bending this over-states the "
                    "growth stress and the margin is pessimistic"),
        life_caveat=("an LCF allowable is a limit at a STATED cycle count -- "
                     "CR-165148 Fig 48 is 72,000 cycles. Margin above 1 on "
                     "stress does not mean that life is still met, because "
                     "LCF life falls far faster than stress rises"))


def summary():
    L = ["Stage K unit K2 -- growth margin on the FPS hardware", ""]
    cc = speed_cross_check()
    L.append(f"   LP spool speed, two published statements: "
             f"tip speeds give +{cc['from_tip_speeds_pct']:.2f} %, the note "
             f"prints +{cc['printed_pct']} % -- agree to "
             f"{cc['agree_within_pct']:.2f} points")
    L += ["", f"   {'rating':>7}{'FPS m/s':>10}{'growth':>9}{'speed':>8}{'stress':>9}"]
    for s in speed_ratios():
        L.append(f"   {s['rating']:>7}{s['fps_m_s']:>10.1f}{s['growth_m_s']:>9.1f}"
                 f"{s['speed_ratio']:>8.4f}{s['stress_ratio']:>9.4f}")
    sc = in_scope()
    L += ["", f"   in scope: {len(sc['lp'])} LP-spool parts. "
          f"Out of scope: {len(sc['hp'])} HP-spool parts --",
          f"      {sc['hp_excluded_because']}"]
    for rating in (1, 3):
        g = regrown(rating)
        L += ["", f"   at rating {rating}, stress x{g['stress_ratio']:.4f}:",
              f"      {'part':<30}{'FPS':>8}{'growth':>9}{'margin':>9}  claim?"]
        for r in g["rows"]:
            L.append(f"      {r['part']:<30}{r['fps_margin']:>8.3f}"
                     f"{r['growth_stress_MPa']:>9.1f}{r['growth_margin']:>9.3f}"
                     f"  {'covered' if r['covered_by_claim'] else 'NOT covered'}"
                     f"{'' if r['survives'] else '   FAILS'}")
    v = verdict(1)
    L += ["", f"   the claim '{v['claim']}':",
          f"      parts it covers      -- all survive: {v['covered_all_survive']}, "
          f"worst margin {v['covered_worst_margin']:.3f}",
          f"      parts it does NOT    -- all survive: {v['not_covered_all_survive']}, "
          f"worst margin {v['not_covered_worst_margin']:.3f}"]
    L.append(f"   this is a BOUND, not a prediction: {v['bound_note'][:66]}...")
    return "\n".join(L)


if __name__ == "__main__":
    print(summary())

"""C2 unit 11: the HPT's spanwise energy-extraction distribution.

CR-167955 sec 2.3 says the through-flow "gradients characterize the
forced-vortex flow distribution and small gradients in stage energy
extraction", and prints the distribution as Fig 5c and nothing else.
`tools/read_hpt_fig5.py` extracts it; this checks it.

Two vortex laws make a testable prediction about that curve:
  free vortex  (r*c_theta constant)  ->  dh uniform across the span
  solid body   (c_theta ~ r)         ->  dh ~ r^2, rising monotonically
STEP0.md, unit 11."""
from __future__ import annotations

import math

import yaml

from e3cycle.cycle import DATA, load_inputs, solve_rating

CM = 0.01


def load():
    fig5 = yaml.safe_load((DATA / "hpt-fig5.yaml").read_text())
    pub = yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())
    return fig5, pub


def _annulus(pub, stage):
    st = {x["location"]: x for x in pub["hpt"]["flowpath"]["stations"]}
    key = "stage1_blade_exit" if stage == 1 else "stage2_blade_exit"
    return st[key]["r_hub_cm"] * CM, st[key]["r_tip_cm"] * CM


def area_weighted(pct, vals, r_hub, r_tip):
    """weight by annulus area: dA = 2 pi r dr, and r = r_hub + x (r_tip - r_hub)"""
    num = den = 0.0
    for i in range(len(pct) - 1):
        xa, xb = pct[i] / 100, pct[i + 1] / 100
        ra, rb = r_hub + xa * (r_tip - r_hub), r_hub + xb * (r_tip - r_hub)
        da = math.pi * (rb ** 2 - ra ** 2)
        num += 0.5 * (vals[i] + vals[i + 1]) * da
        den += da
    return num / den


def analyse():
    fig5, pub = load()
    inp = load_inputs()
    res = solve_rating(next(r for r in inp.ratings if r.name == "max_climb"), inp)
    dh_final = res.stations["hpt_dh_per_kg"]
    # Fig 5 is the HPT report's own design through-flow, which predates the
    # final cycle rematch: its Table I max-climb column has T41 1557 K where
    # CR-168219 Table XVIII has 1517. dh/T is the same 355.5 either way, so
    # the design-point work is higher by exactly that temperature ratio.
    pre = pub["hpt"]["earlier_requirements"]["max_climb"]
    dh_total = pre["dh_over_T"] * pre["T41_K"]
    split = pub["hpt"]["stage_work_split_stage1"]
    out = []
    for n, cycle_dh in ((1, dh_total * split), (2, dh_total * (1 - split))):
        blk = fig5[f"stage{n}"]
        pct, vals = blk["pct_height"], [v * 1000 for v in blk["dh_kJ_kg"]]
        r_hub, r_tip = _annulus(pub, n)
        aw = area_weighted(pct, vals, r_hub, r_tip)
        peak = max(range(len(vals)), key=lambda i: vals[i])
        out.append(dict(stage=n, pct=pct, dh=vals, r_hub=r_hub, r_tip=r_tip,
                        area_weighted=aw, cycle_dh=cycle_dh, ratio=aw / cycle_dh,
                        hub_tip=r_hub / r_tip,
                        peak_pct=pct[peak], peak=vals[peak], lo=min(vals), hi=max(vals),
                        spread=(max(vals) - min(vals)) / aw,
                        ends_below_peak=(vals[peak] - 0.5 * (vals[0] + vals[-1])) / aw))
    # the implied work split, from Fig 5 alone
    aws = [o["area_weighted"] for o in out]
    return out, dict(dh_total=dh_total, dh_final_cycle=dh_final, split_printed=split,
                     split_from_fig5=aws[0] / (aws[0] + aws[1]),
                     total_from_fig5=sum(aws),
                     t41_design=pre["T41_K"])


def law_fit(o):
    """rms departure of Fig 5c from each vortex law, as a fraction of the
    area-weighted mean"""
    laws = vortex_law_shapes(o)
    out = {}
    for name, shape in laws.items():
        d = [(a - b) / o["area_weighted"] for a, b in zip(o["dh"], shape)]
        out[name] = math.sqrt(sum(x * x for x in d) / len(d))
    return out


def free_vortex_exit_angle_swing(r_hub, r_tip, alpha_tip_deg):
    """how much a *free* vortex would move the exit flow angle across this
    annulus -- the test Fig 5a cannot make on a short blade"""
    t = math.tan(math.radians(alpha_tip_deg))
    return math.degrees(math.atan(t * r_tip / r_hub)) - alpha_tip_deg


def vortex_law_shapes(o):
    """what a free vortex and a solid-body vortex would put on this plot,
    both scaled to the same area-weighted mean"""
    r = [o["r_hub"] + p / 100 * (o["r_tip"] - o["r_hub"]) for p in o["pct"]]
    free = [1.0] * len(r)
    solid = [(x / r[0]) ** 2 for x in r]
    out = {}
    for name, shape in (("free_vortex", free), ("solid_body", solid)):
        aw = area_weighted(o["pct"], shape, o["r_hub"], o["r_tip"])
        out[name] = [s / aw * o["area_weighted"] for s in shape]
    return out


if __name__ == "__main__":
    out, summ = analyse()
    for o in out:
        laws = vortex_law_shapes(o)
        print(f"\nstage {o['stage']}: annulus {o['r_hub'] * 100:.2f}-{o['r_tip'] * 100:.2f} cm "
              f"(hub/tip {o['r_hub'] / o['r_tip']:.3f})")
        print(f"{'height %':>9}{'Fig 5c':>10}{'free vortex':>13}{'solid body':>12}")
        for i, p in enumerate(o["pct"]):
            print(f"{p:>9}{o['dh'][i] / 1000:>10.1f}{laws['free_vortex'][i] / 1000:>13.1f}{laws['solid_body'][i] / 1000:>12.1f}")
        print(f"  area-weighted {o['area_weighted'] / 1000:.1f} kJ/kg vs the cycle's {o['cycle_dh'] / 1000:.1f} "
              f"({(o['ratio'] - 1) * 100:+.1f} %); peak {o['peak'] / 1000:.0f} at {o['peak_pct']} % height; "
              f"spread {o['spread'] * 100:.1f} % of the mean")
        f = law_fit(o)
        print(f"  rms departure from a free vortex {f['free_vortex'] * 100:.1f} %, from solid body {f['solid_body'] * 100:.1f} %")
        swing = free_vortex_exit_angle_swing(o["r_hub"], o["r_tip"], 70.0)
        print(f"  a free vortex would swing a 70 deg exit angle by only {swing:.1f} deg across this annulus")
    print(f"\nwork split from Fig 5c alone: {summ['split_from_fig5']:.3f} vs the printed {summ['split_printed']}")
    print(f"total from Fig 5c: {summ['total_from_fig5'] / 1000:.1f} kJ/kg vs the HPT report's own design point "
          f"{summ['dh_total'] / 1000:.1f} (T41 {summ['t41_design']} K, pre-rematch) "
          f"[{(summ['total_from_fig5'] / summ['dh_total'] - 1) * 100:+.1f} %]; "
          f"the final cycle is {summ['dh_final_cycle'] / 1000:.1f}")

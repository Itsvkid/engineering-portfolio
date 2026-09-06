"""Stage D4: active clearance control — the payoff, and the cruise value
by two independent routes.

The work plan's D4 closure: *the clearance transient has the published
shape and the cruise values land within 0.2 % of span.*

Two chapters of CR-167955 say what the cruise clearance is, in different
units and for different reasons, and neither refers to the other:

  * §2 Table III, the aerodynamic design, prints a **tip clearance as a
    percentage of span** for each stage: 1.0 % and 0.6 %.
  * §4, the clearance-control chapter, prints the **desired running
    clearance in centimetres**: 0.041 cm, and Table X's ACC payoff is
    computed on it.

With Fig 3's annulus heights, those are the same statement, and can be
checked against each other. STEP0.md, unit D4."""
from __future__ import annotations

from dataclasses import dataclass

import yaml

from e3cycle.cycle import DATA

CM = 0.01


def load():
    cl = yaml.safe_load((DATA / "hpt-clearance.yaml").read_text())
    pub = yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())
    return cl, pub


def blade_heights_cm():
    """from Fig 3's dimensioned annulus, at each rotor's exit plane"""
    _, pub = load()
    st = {x["location"]: x for x in pub["hpt"]["flowpath"]["stations"]}
    return {
        "stage1": st["stage1_blade_exit"]["r_tip_cm"] - st["stage1_blade_exit"]["r_hub_cm"],
        "stage2": st["stage2_blade_exit"]["r_tip_cm"] - st["stage2_blade_exit"]["r_hub_cm"],
    }


@dataclass
class PayoffRow:
    item: str
    d_eta_per_mm: float
    clearance_no_acc_cm: float
    clearance_reduction_cm: float
    d_eta_printed_pct: float

    @property
    def d_eta_recomputed_pct(self):
        return self.clearance_reduction_cm * 10.0 * self.d_eta_per_mm

    @property
    def clearance_with_acc_cm(self):
        return self.clearance_no_acc_cm - self.clearance_reduction_cm


def payoff_rows():
    cl, _ = load()
    p = cl["payoff"]
    return [PayoffRow(i, e, n, r, d) for i, e, n, r, d in
            zip(p["item"], p["d_eta_per_mm"], p["clearance_no_acc_cm"],
                p["clearance_reduction_cm"], p["d_eta_pct"])], p


def cruise_clearance_two_routes():
    """Table III's percent of span against §4's centimetres"""
    cl, pub = load()
    pct = pub["hpt"]["stage_aerodynamics"]["tip_clearance_pct"]
    h = blade_heights_cm()
    desired_cm = cl["acc_capability_vs_thrust"]["desired_cm"]
    out = []
    for i, stage in enumerate(("stage1", "stage2")):
        from_pct_cm = pct[i] / 100.0 * h[stage]
        out.append(dict(stage=stage, height_cm=h[stage], printed_pct_of_span=pct[i],
                        from_percent_cm=from_pct_cm, desired_cm=desired_cm,
                        difference_cm=from_pct_cm - desired_cm,
                        difference_pct_of_span=(from_pct_cm - desired_cm) / h[stage] * 100))
    return out


def transient():
    cl, _ = load()
    return cl["transients"], cl["design_clearances"]


if __name__ == "__main__":
    rows, p = payoff_rows()
    print("1. Does Table X's ACC payoff recompute?")
    print(f"{'item':<16}{'d_eta %/mm':>12}{'no ACC cm':>11}{'reduction':>11}{'with ACC':>10}"
          f"{'d_eta calc':>12}{'printed':>9}{'diff':>8}")
    for r in rows:
        print(f"{r.item:<16}{r.d_eta_per_mm:>12.3f}{r.clearance_no_acc_cm:>11.3f}"
              f"{r.clearance_reduction_cm:>11.3f}{r.clearance_with_acc_cm:>10.3f}"
              f"{r.d_eta_recomputed_pct:>12.3f}{r.d_eta_printed_pct:>9.3f}"
              f"{r.d_eta_recomputed_pct - r.d_eta_printed_pct:>8.3f}")
    tot = sum(r.d_eta_recomputed_pct for r in rows)
    print(f"{'total':<16}{'':>12}{'':>11}{'':>11}{'':>10}{tot:>12.3f}{p['d_eta_total_pct']:>9.3f}"
          f"{tot - p['d_eta_total_pct']:>8.3f}")
    print(f"\n   sfc: {p['d_sfc_from_eta_pct']} % from efficiency, +{p['d_sfc_fan_air_pct']} % for "
          f"{p['fan_air_pct_w25']} % W25 of fan air -> net {p['d_sfc_net_pct']} %"
          f"   (sum {p['d_sfc_from_eta_pct'] + p['d_sfc_fan_air_pct']:+.2f})")

    print("\n2. The cruise clearance, two chapters, two units")
    print(f"{'stage':<9}{'span cm':>9}{'Table III %':>13}{'-> cm':>9}{'sec 4 cm':>10}"
          f"{'diff cm':>9}{'diff % span':>13}")
    for r in cruise_clearance_two_routes():
        print(f"{r['stage']:<9}{r['height_cm']:>9.2f}{r['printed_pct_of_span']:>13.1f}"
              f"{r['from_percent_cm']:>9.4f}{r['desired_cm']:>10.3f}"
              f"{r['difference_cm']:>9.4f}{r['difference_pct_of_span']:>13.3f}")
    print("   work plan D4 band: 0.2 % of span")

    tr, dc = transient()
    print("\n3. The transient, as read from Figs 44-46")
    s1 = tr["stage1_tip"]
    print(f"   takeoff pinch {s1['takeoff_pinch']} cm, casing peak without ACC {s1['casing_peak_no_acc']} cm,")
    print(f"   max climb without ACC {s1['max_climb_clearance_no_acc']} cm, cruise WITH ACC "
          f"{s1['cruise_running_clearance_with_acc']} cm, reburst pinch with ACC {s1['reburst_pinch_with_acc']} cm")
    print(f"   design takeoff clearance {dc['takeoff_tip_clearance_both_stages_cm']} cm both stages")

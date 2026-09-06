"""Stage D2: the combustor's exit — is the profile the one D1's cooling
analysis used?

The work plan's D2 closure has two halves: *pressure drop 5.0 %
reproduced from the geometry, and the exit profile is what D1 used.*

The second half is checkable. CR-168301 Table IV gives the pattern factor
(0.25 max) and profile factor (0.125 max) and Fig 5 gives the radial
profile shape; CR-167955's heat-transfer design point gives the gas
temperatures the turbine was designed to. Those must be the same
statement, and the pattern factor is the bridge:

    PF = (T_max − T_avg) / (T_avg − T3)

The first half is NOT attempted: it needs the liner hole areas and
discharge coefficients, and Stage A transcribed the airflow *split* (Fig
8's 24 labels) but not the hole geometry. Said, not skipped quietly.
STEP0.md, unit D5."""
from __future__ import annotations

import yaml

from e3cycle.cycle import DATA


def load():
    comb = yaml.safe_load((DATA / "combustor-design.yaml").read_text())
    hpt = yaml.safe_load((DATA / "hpt-cooling.yaml").read_text())
    return comb, hpt


def airflow_split():
    """Fig 8's 24 labels, grouped"""
    comb, _ = load()
    a = comb["airflow_distribution"]
    groups = {
        "pilot dome": a["pilot_dome_pct"],
        "main dome": a["main_dome_pct"],
        "outer liner": sum(a["outer_liner_pct"]),
        "centerbody": sum(a["centerbody_pct"]),
        "inner liner": sum(a["inner_liner_pct"]),
    }
    n_labels = 2 + len(a["outer_liner_pct"]) + len(a["centerbody_pct"]) + len(a["inner_liner_pct"])
    return groups, sum(groups.values()), a["total_pct"], n_labels


def pattern_factor(t_max, t_avg, t3):
    return (t_max - t_avg) / (t_avg - t3)


def implied_combustor_exit_temperature():
    """CR-167955 prints T40 max peak (the hot streak the vane sees), T41
    design (the rotor inlet) and T3, and notes a pattern factor of 0.26.
    T41 is downstream of the nonchargeable coolant, so it is NOT the
    combustor exit average. Solving PF = 0.26 for T_avg gives what the
    combustor exit average must have been."""
    _, hpt = load()
    d = hpt["heat_transfer_design_point"]
    t3 = d["t3_C"][0]
    t_max = d["t40_max_peak_C"][0]
    t41 = d["t41_design_C"][0]
    pf_noted = 0.26            # hpt-cooling.yaml, heat_transfer_design_point note
    # PF = (t_max - t_avg)/(t_avg - t3)  ->  t_avg = (t_max + PF t3)/(1 + PF)
    t_avg = (t_max + pf_noted * t3) / (1 + pf_noted)
    return dict(t3_C=t3, t40_max_C=t_max, t41_design_C=t41, pf_noted=pf_noted,
                t4_implied_C=t_avg, drop_across_coolant_C=t_avg - t41,
                pf_if_t41_were_the_average=pattern_factor(t_max, t41, t3))


def radial_profile():
    comb, _ = load()
    return comb["aero_requirements"]["radial_profile"]


def profile_temperatures(t_avg_C=None, t3_C=None):
    """Fig 5's (T_local − T_avg)/ΔT_avg turned into temperatures"""
    imp = implied_combustor_exit_temperature()
    t_avg = t_avg_C if t_avg_C is not None else imp["t4_implied_C"]
    t3 = t3_C if t3_C is not None else imp["t3_C"]
    dt = t_avg - t3
    p = radial_profile()["design_profile"]
    return {k: t_avg + v * dt for k, v in p.items() if k != "peak_at_pct_height"}


if __name__ == "__main__":
    groups, total, printed, n = airflow_split()
    print("1. The airflow split (Fig 8)")
    for k, v in groups.items():
        print(f"   {k:<14}{v:>7.1f} % of Wc")
    print(f"   {'total':<14}{total:>7.1f}   printed {printed}   from {n} read labels")
    print(f"   domes together: {groups['pilot dome'] + groups['main dome']:.1f} %; "
          f"cooling and dilution: {total - groups['pilot dome'] - groups['main dome']:.1f} %")

    imp = implied_combustor_exit_temperature()
    print("\n2. The pattern factor, and what it says the combustor exit was")
    print(f"   T3 {imp['t3_C']} C, T40 max peak (hot streak) {imp['t40_max_C']} C, "
          f"T41 design (rotor inlet) {imp['t41_design_C']} C")
    print(f"   if T41 were the combustor exit average, PF = {imp['pf_if_t41_were_the_average']:.3f}"
          f"  -- against a 0.25 requirement and a noted 0.26")
    print(f"   solving PF = {imp['pf_noted']} instead gives a combustor exit average of "
          f"{imp['t4_implied_C']:.0f} C,")
    print(f"   which is {imp['drop_across_coolant_C']:.0f} C above T41 -- the nonchargeable coolant's worth")

    print("\n3. Fig 5's radial profile, as temperatures at that exit average")
    rp = radial_profile()
    for k, v in profile_temperatures().items():
        print(f"   {k:<12}{v:>8.0f} C   (profile factor {rp['design_profile'][k]:+.2f})")
    print(f"   peak sits at {rp['design_profile']['peak_at_pct_height']} % height; "
          f"the pattern-factor limit is drawn between {rp['pf_limit_span_pct'][0]} and "
          f"{rp['pf_limit_span_pct'][1]} % height")
    print(f"   note: {rp['note']}")

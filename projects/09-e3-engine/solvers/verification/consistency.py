"""Stage I1: cross-discipline consistency — as tests, not by inspection.

Stage I1's first bullet: *the same T41 in B, D and E; the same cooling
flows in B, D and D3; the same metal temperatures in D and E and F; the
same masses in F and G — **as tests, not by inspection**.*

Eight stages of solvers have grown up beside each other, each reading the
reports for itself. Nothing so far has forced them to agree. A quantity
that appears in three chapters of the E³ reports can enter this project
three times, and if one of those readings drifted — a unit, a rating, a
footnote missed — every stage downstream of it would still close against
its own band and nothing would say so.

This module is the thing that says so. Each function returns every
appearance of one shared quantity, with the stage that reads it, the file
it comes from, and the spread. The tests assert the spread.

There is a second kind of check here, and it is the more interesting one:
**quantities that arrive by genuinely different routes.** The LP spool
speed can be had from the fan's corrected tip speed and its tip diameter,
or from the LPT report's N/sqrt(T) parameter and the cycle's own T45. The
HP speed from HPC Table X's footnote, or from the HPT report's N/sqrt(T)
and T41. Those are four measurements of two numbers, out of four
documents, and none was derived from another.

STEP0.md, unit I1."""
from __future__ import annotations

import math
from dataclasses import dataclass

import yaml

from e3cycle import cycle as cyc
from e3cycle.cycle import DATA

C_TO_K = 273.15


def _y(name):
    return yaml.safe_load((DATA / name).read_text())


@dataclass
class Appearance:
    quantity: str
    stage: str
    source: str
    value: float
    units: str


def _spread(rows):
    v = [r.value for r in rows]
    return dict(n=len(rows), lo=min(v), hi=max(v), mean=sum(v) / len(v),
                spread_pct=(max(v) - min(v)) / (sum(v) / len(v)) * 100)


# ------------------------------------------------------------------- T41

def t41_across_stages():
    """T41 appears in the cycle (B, from Table XII), in the HPT report's own
    cycle-match line, in that report's *earlier requirements* table, and in
    the cooling design point (D).

    The earlier-requirements block is exactly what its name says and is
    **not** a disagreement -- it is the design before the final cycle, and
    the transcription labelled it so. It is reported here as chronology, not
    as a check. The check is against the HPT report's cycle-match value,
    which is the number that report actually designed to."""
    pub, cool = _y("e3-fps-published.yaml"), _y("hpt-cooling.yaml")
    inp = cyc.load_inputs()
    by_rating = {r.name: r for r in inp.ratings}
    er = pub["hpt"]["earlier_requirements"]
    hp = cool["heat_transfer_design_point"]

    checks = {}

    # the one place two documents describe the same instant of the same cycle
    checks["T41 max climb, the aero design point"] = [
        Appearance("T41", "B cycle", "Table XII, via Rating",
                   by_rating["max_climb"].t41_K, "K"),
        Appearance("T41", "A HPT report", "cycle match, inlet_temperature_T41_K",
                   pub["hpt"]["cycle_match"]["inlet_temperature_T41_K"], "K")]

    # takeoff: three appearances and three definitions of "takeoff"
    checks["T41 takeoff"] = [
        Appearance("T41", "B cycle", "Table XII takeoff, sea-level static",
                   by_rating["takeoff"].t41_K, "K"),
        Appearance("T41", "A HPT report", "SLTO +27 F requirement",
                   er["slto_plus_27F"]["T41_K"], "K"),
        Appearance("T41", "D cooling", "Table VIII, Mach 0.3 sea-level takeoff",
                   hp["t41_cycle_C"][0] + C_TO_K, "K")]

    out = {k: dict(rows=v, **_spread(v)) for k, v in checks.items()}
    out["chronology"] = dict(rows=[
        Appearance("T41 max climb", "earlier requirement", "HPT earlier_requirements",
                   er["max_climb"]["T41_K"], "K"),
        Appearance("T41 max climb", "final cycle", "Table XII",
                   by_rating["max_climb"].t41_K, "K"),
        Appearance("T41 max cruise", "earlier requirement", "HPT earlier_requirements",
                   er["max_cruise"]["T41_K"], "K"),
        Appearance("T41 max cruise", "final cycle", "Table XII",
                   by_rating["max_cruise"].t41_K, "K")],
        drop_max_climb_K=er["max_climb"]["T41_K"] - by_rating["max_climb"].t41_K,
        drop_max_cruise_K=er["max_cruise"]["T41_K"] - by_rating["max_cruise"].t41_K)
    return out


def t41_solved_is_the_rating_it_was_solved_to():
    """The cycle bisects the fuel-air ratio until T41 is Table XII's. That
    it still does is worth asserting: it is the hinge every downstream
    stage hangs on."""
    out = []
    for r in cyc.run_all():
        want = next(x for x in cyc.load_inputs().ratings if x.name == r.rating).t41_K
        out.append(dict(rating=r.rating, solved_K=r.stations["t41"], published_K=want,
                        err_pct=(r.stations["t41"] / want - 1) * 100))
    return out


def t41_margin_arithmetic():
    """D's own margin stack: direct adders sum, two-sigma events combine
    root-sum-square, and T41 design = cycle + margin."""
    m = _y("hpt-cooling.yaml")["t41_margin"]
    hp = _y("hpt-cooling.yaml")["heat_transfer_design_point"]
    d = m["direct_adders"]
    direct = sum(v for k, v in d.items() if k != "total")
    s = m["two_sigma_rss"]
    rss = math.sqrt(sum(v ** 2 for k, v in s.items() if k != "rss_total"))
    return dict(direct_sum=direct, direct_printed=d["total"],
                rss=rss, rss_printed=s["rss_total"],
                new_engine=d["total"] + s["rss_total"], new_printed=m["total_new_engine"],
                with_det=m["total_new_engine"] + m["deterioration"],
                with_det_printed=m["total_with_deterioration"],
                design_C=hp["t41_cycle_C"][0] + m["total_with_deterioration"],
                design_printed_C=hp["t41_design_C"][0])


# --------------------------------------------------------- cooling flows

def cooling_flows_across_stages():
    """The cycle's four bleed fractions (B) are the four final FPS streams
    (D3). The detailed design (D1) is a different, earlier accounting on
    the same basis, and the HPT report quotes a third number on a
    different denominator."""
    inp = cyc.load_inputs()
    cool = inp.cool
    c = _y("hpt-cooling.yaml")
    pub = _y("e3-fps-published.yaml")
    final = c["flows_final_fps_for_comparison"]

    pairs = [("cpd_nonchargeable", "cpd_nonchargeable_pct"),
             ("cpd_chargeable", "cpd_chargeable_pct"),
             ("stage_7_cooling_and_purge", "stage7_pct"),
             ("stage_5_cooling_and_purge", "stage5_pct")]
    streams = [dict(stream=a, cycle_pct=cool[a] * 100, published_pct=final[b],
                    err_pct=(cool[a] * 100 / final[b] - 1) * 100) for a, b in pairs]
    detailed = sum(i["pct"] for i in c["flows"]["items"])
    return dict(streams=streams,
                cycle_total_pct=sum(s["cycle_pct"] for s in streams),
                published_total_pct=final["total_pct"],
                detailed_total_pct=detailed,
                detailed_printed=c["heat_transfer_design_point"]["cooling_plus_leakage_pct_w25"][0],
                hpt_table_iii_pct_w2c=pub["hpt"]["stage_aerodynamics"]["cooling_and_leakage_pct_W2c"])


# ---------------------------------------------------- metal temperatures

def metal_temperatures_across_stages():
    """D reads the HPT blade and vane metal temperatures; E2 reads the HPT
    *rotor* metal temperatures from a different figure; F1 reads the HPC
    blade metal temperatures from Table X. Three sets, three figures, one
    engine — so the check is that they are ordered the way the gas path is,
    and that nothing reads a value its own source does not carry."""
    from materials.allowables import measured_blade_density
    from thermal.cooling import rows as cooled_rows
    h = _y("hpt-mechanical.yaml")["rotor_temperatures"]["locations_C"]

    cooled = [dict(row=r.name, t_gas_C=r.t_gas_C, t_metal_C=r.t_metal_C,
                   t_coolant_C=r.t_coolant_C) for r in cooled_rows()]
    rotor40 = {k: v[0] for k, v in h.items()}
    hpc = [dict(stage=r["stage"], metal_C=r["metal_C"]) for r in measured_blade_density()]
    return dict(
        d_cooled_rows=cooled,
        e_rotor_at_40s=rotor40,
        f_hpc_blades=hpc,
        hpc_max_C=max(r["metal_C"] for r in hpc),
        hpt_blade_metal_C=max(r["t_metal_C"] for r in cooled),
        hpt_shank_C=rotor40["stage1_blade_shank"],
        hpt_disc_bore_C=rotor40["stage1_disk_bore"])


# ---------------------------------------------------------------- masses

def masses_f_vs_g(rows=None):
    """F2 integrates the section areas; G1 lofts the same sections into a
    solid and OCC measures it. The conformal wrap is exactly
    volume-preserving, so the two must agree."""
    from geometry.blades import all_rows, volume_check
    rows = rows if rows is not None else all_rows()
    return volume_check(rows)


# ---------------------------------------------------------- spool speeds

def spool_speeds_four_routes(rating="max_climb"):
    """Four routes out of four documents, none derived from another.

      LP  1. the fan's corrected tip speed and its tip diameter (fan report)
          2. the LPT report's N/sqrt(T) and the cycle's T45
      HP  3. HPC Table X's footnote speed at the aero design point
          4. the HPT report's N/sqrt(T) and the cycle's T41
    """
    pub = _y("e3-fps-published.yaml")
    fan = _y("fan-design.yaml")
    r = next(x for x in cyc.run_all() if x.rating == rating)
    st = r.stations

    r_tip = fan["aero_parameters"]["tip_diameter_cm"][0] / 200
    u_corr = pub["fan"]["corrected_tip_speed_m_s"]
    theta = st["t0"] / 288.15
    lp_fan = u_corr / r_tip * math.sqrt(theta) * 60 / (2 * math.pi)

    k_lp = pub["lpt"]["cycle_match"]["speed_N_over_sqrtT_rad_s_sqrtK"]
    lp_lpt = k_lp * math.sqrt(st["t45"]) * 60 / (2 * math.pi)

    hp_table = pub["hpc"]["spool_speed_rpm"]["xnh_max_climb_aero_dp"]
    k_hp = pub["hpt"]["cycle_match"]["speed_N_over_sqrtT_rad_s_sqrtK"]
    hp_hpt = k_hp * math.sqrt(st["t41"]) * 60 / (2 * math.pi)

    return dict(
        rating=rating,
        lp=[Appearance("LP rpm", "A fan report", "corrected tip speed / tip radius", lp_fan, "rpm"),
            Appearance("LP rpm", "E4 via LPT report", "N/sqrt(T45)", lp_lpt, "rpm")],
        hp=[Appearance("HP rpm", "A HPC Table X", "XNH max-climb aero design point", hp_table, "rpm"),
            Appearance("HP rpm", "E4 via HPT report", "N/sqrt(T41)", hp_hpt, "rpm")],
        lp_spread_pct=abs(lp_fan / lp_lpt - 1) * 100,
        hp_spread_pct=abs(hp_hpt / hp_table - 1) * 100,
        ratio=hp_hpt / lp_lpt)


# ------------------------------------------------ every closure, re-checked

def closure_scoreboard():
    """Stage I1's third bullet: every "closes when" tolerance re-checked
    after Stage G's geometry. `data/closures.yaml` carries each stage's own
    closure sentence, its band and the number the solver produces now; a
    closure with a number must be inside its band or be a recorded miss."""
    c = _y("closures.yaml")["closures"]
    out = []
    for x in c:
        inside = None
        if x["state"] != "gated" and x["band"] is not None and x["achieved"] is not None:
            inside = x["achieved"] <= x["band"]
        out.append(dict(x, inside=inside))
    return out


def closure_summary():
    rows = closure_scoreboard()
    numeric = [r for r in rows if r["inside"] is not None]
    return dict(total=len(rows),
                met=sum(1 for r in rows if r["state"] == "met"),
                half=sum(1 for r in rows if r["state"] == "half"),
                gated=sum(1 for r in rows if r["state"] == "gated"),
                numeric=len(numeric),
                inside=sum(1 for r in numeric if r["inside"]),
                misses=[r for r in numeric if not r["inside"]])


if __name__ == "__main__":
    print("Stage I1: the same number, read by different stages\n")

    print("1. T41")
    t = t41_across_stages()
    for q, g in t.items():
        if q == "chronology":
            continue
        print(f"   {q}")
        for a in g["rows"]:
            print(f"      {a.stage:<14}{a.source:<44}{a.value:>9.1f} {a.units}")
        print(f"      spread {g['spread_pct']:.2f} %")
    ch = t["chronology"]
    print(f"   the design moved, and the reports say so:")
    for a in ch["rows"]:
        print(f"      {a.quantity:<16}{a.stage:<22}{a.value:>9.1f} K")
    print(f"      T41 fell {ch['drop_max_climb_K']:.0f} K at max climb and"
          f" {ch['drop_max_cruise_K']:.0f} K at max cruise between the HPT report's")
    print(f"      requirement and the final cycle -- chronology, not disagreement")
    print("\n   the cycle still solves to the rating it was given:")
    for r in t41_solved_is_the_rating_it_was_solved_to():
        print(f"      {r['rating']:<12}{r['solved_K']:>9.1f} vs {r['published_K']:>7.1f} K"
              f"   {r['err_pct']:+.4f} %")
    m = t41_margin_arithmetic()
    print(f"\n   D's own margin stack: direct {m['direct_sum']:.1f} vs {m['direct_printed']:.1f}, "
          f"RSS {m['rss']:.1f} vs {m['rss_printed']:.1f},")
    print(f"      new engine {m['new_engine']:.1f} vs {m['new_printed']:.1f}, "
          f"with deterioration {m['with_det']:.1f} vs {m['with_det_printed']:.1f} C")
    print(f"      T41 design {m['design_C']:.1f} vs {m['design_printed_C']:.1f} C")

    cf = cooling_flows_across_stages()
    print(f"\n2. Cooling flows: the cycle's bleeds against D3's final streams\n")
    print(f"   {'stream':<32}{'cycle %':>10}{'published %':>13}{'err %':>8}")
    for s in cf["streams"]:
        print(f"   {s['stream']:<32}{s['cycle_pct']:>10.2f}{s['published_pct']:>13.2f}"
              f"{s['err_pct']:>8.2f}")
    print(f"   {'total':<32}{cf['cycle_total_pct']:>10.2f}{cf['published_total_pct']:>13.2f}")
    print(f"\n   D1's detailed design sums to {cf['detailed_total_pct']:.2f} against a printed"
          f" {cf['detailed_printed']:.2f} % of W25")
    print(f"   HPT Table III quotes {cf['hpt_table_iii_pct_w2c']} % of W2c -- a different"
          f" denominator, not a disagreement")

    mt = metal_temperatures_across_stages()
    print(f"\n3. Metal temperatures, three figures in three stages\n")
    print(f"   F  hottest HPC blade          {mt['hpc_max_C']:>6.0f} C  (stage 10)")
    print(f"   D  hottest cooled HPT row     {mt['hpt_blade_metal_C']:>6.0f} C")
    print(f"   E  HPT stage-1 blade shank    {mt['hpt_shank_C']:>6.0f} C  at 40 s")
    print(f"   E  HPT stage-1 disc bore      {mt['hpt_disc_bore_C']:>6.0f} C  at 40 s")

    s = spool_speeds_four_routes()
    print(f"\n4. Spool speed, four routes out of four documents ({s['rating']})\n")
    for grp in ("lp", "hp"):
        for a in s[grp]:
            print(f"   {a.quantity:<9}{a.stage:<22}{a.source:<44}{a.value:>9,.0f}")
    print(f"\n   LP spread {s['lp_spread_pct']:.2f} %   HP spread {s['hp_spread_pct']:.2f} %"
          f"   HP:LP = {s['ratio']:.2f}")

    print(f"\n5. Masses: Stage F2's integral against Stage G1's solids")
    mg = masses_f_vs_g()
    print(f"   {len(mg)} rows, worst {max(abs(v['err_pct']) for v in mg):.2f} %,"
          f" all valid: {all(v['valid'] for v in mg)}")

    print(f"\n6. Every closure, re-checked\n")
    print(f"   {'stage':<7}{'closure':<52}{'achieved':>10}{'band':>8}{'state':>8}")
    for r in closure_scoreboard():
        a = "-" if r["achieved"] is None else f"{r['achieved']:.2f}"
        b = "-" if r["band"] is None else f"{r['band']:.2f}"
        mark = "" if r["inside"] in (None, True) else "  <- MISS"
        print(f"   {r['stage']:<7}{r['what'][:50]:<52}{a:>10}{b:>8}{r['state']:>8}{mark}")
    cs = closure_summary()
    print(f"\n   {cs['total']} closures: {cs['met']} met, {cs['half']} half, {cs['gated']} gated")
    print(f"   {cs['inside']} of {cs['numeric']} numeric closures are inside their band;"
          f" the miss is {cs['misses'][0]['stage']} ({cs['misses'][0]['what']})")

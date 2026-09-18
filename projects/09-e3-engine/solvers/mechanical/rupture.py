"""Unit E10 -- HPT blade rupture life, from CR-167955 Fig 84.

E1's second half. The gate said no creep data is sourced; Fig 84 p.142 is
creep data, on the stage-2 blade's pitch section, and it has been
transcribed in `hpt-mechanical.yaml` since 2026-09-05.

Everything here is a Larson-Miller parameter, LMP = T (C + log10 t), with T
in kelvin and t in hours. C is taken as 20 -- the standard value for a
nickel alloy -- and labelled an assumption everywhere it is used, because
no source on disk carries a Larson-Miller constant for Rene 150.

Nothing in this module fits a slope against stress. There is no stress: the
HPT's airfoil sections were never published.
"""
from __future__ import annotations

import math
import pathlib

import yaml

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"

C_LARSON_MILLER = 20.0      # ASSUMPTION: standard for Ni alloys. Not published.
KELVIN = 273.15


def _hpt():
    return yaml.safe_load((DATA / "hpt-mechanical.yaml").read_text())


def _cooling():
    return yaml.safe_load((DATA / "hpt-cooling.yaml").read_text())


def lmp(t_C, hours, c=C_LARSON_MILLER):
    return (t_C + KELVIN) * (c + math.log10(hours))


def hours_from_lmp(p, t_C, c=C_LARSON_MILLER):
    return 10.0 ** (p / (t_C + KELVIN) - c)


# --- band 1: two figures, one section ---------------------------------------

def fig84_points():
    return _hpt()["stage2_blade"]["rupture_life"]["pitch_section_map"]["points"]


def fig35_nodes_C():
    """ALL of Fig 35's nodes, surface and interior. BUCKET CREEP runs
    element by element over the whole section, so Fig 84's points are not
    confined to the surface -- and the coldest of them, at 867 C, is an
    interior node (finding 245)."""
    m = _cooling()["stage2_rotor"]["metal_temperatures"]
    return [p[0] for p in m["surface_nodes_c_f"] + m["interior_nodes_c_f"]]


def fig35_surface_nodes_C():
    return [p[0] for p in _cooling()["stage2_rotor"]["metal_temperatures"]["surface_nodes_c_f"]]


def band1_same_section():
    """Fig 84 (rupture map) and Fig 35 (metal map) are the stage-2 blade's
    pitch section at hot-day takeoff. Their temperature ranges must agree."""
    a = [p["C"] for p in fig84_points()]
    b = fig35_nodes_C()
    surf = fig35_surface_nodes_C()
    return dict(fig84=(min(a), max(a)), fig35=(min(b), max(b)),
                fig35_surface=(min(surf), max(surf)),
                dmin=abs(min(a) - min(b)), dmax=abs(max(a) - max(b)),
                dmin_surface_only=abs(min(a) - min(surf)))


# --- band 2: the mission mixes close on themselves --------------------------

def band2_mission_mix():
    h = _hpt()
    out = {}
    for stage, block in (("stage1", h["stage1_blade"]["rupture_life"]["mission_mix"]),
                         ("stage2", h["stage2_blade"]["rupture_life"]["mission_mix"])):
        eq = block["equivalent_hours_at_max_takeoff"]
        shares = block["pct_life_used"]
        hours = block["hours_at_point"]
        # the shares are shares OF the equivalent hours, so they must sum to
        # 100 and the implied rupture-life ratios follow from hours/share
        total = sum(shares)
        # life at condition i relative to takeoff: (h_i/h_TO) * (s_TO/s_i)
        ratios = [(hours[i] / hours[0]) * (shares[0] / shares[i]) for i in range(1, 3)]
        out[stage] = dict(share_sum=total, equivalent_hours=eq,
                          available=block["available_blade_life_at_max_takeoff_hours"],
                          margin=block["available_blade_life_at_max_takeoff_hours"] / eq,
                          life_ratio_climb=ratios[0], life_ratio_cruise=ratios[1])
    return out


# --- band 3: E1's closure ---------------------------------------------------

def stage2_limiting():
    """the boxed point on Fig 84 -- the one Table XXI is designed to"""
    return next(p for p in fig84_points() if p.get("where", "").endswith("(boxed)"))


def stage1_published():
    h = _hpt()
    mm = h["stage1_blade"]["rupture_life"]["mission_mix"]
    fig76 = h["stage1_blade"]["lcf"]["rupture_vs_span"]
    return dict(table_xx_available=mm["available_blade_life_at_max_takeoff_hours"],
                table_xx_required=mm["equivalent_hours_at_max_takeoff"],
                fig76_min=min(fig76["hours"]),
                fig76_min_span_pct=fig76["span_pct"][fig76["hours"].index(min(fig76["hours"]))],
                pitch_metal_C=_cooling()["stage1_blade"]["metal_temperatures"]["conditions"]["t_bulk_C"])


def band3_same_stress_transfer(c=C_LARSON_MILLER):
    """Calibrate on the stage-2 limiting point, evaluate at the stage-1 pitch
    metal temperature, ASSUMING the same stress. The assumption is the whole
    uncertainty and the result is reported as such."""
    s2 = stage2_limiting()
    s1 = stage1_published()
    p = lmp(s2["C"], s2["hours"], c)
    pred = hours_from_lmp(p, s1["pitch_metal_C"], c)
    return dict(lmp=p, predicted_hours=pred,
                published_table_xx=s1["table_xx_available"],
                published_fig76=s1["fig76_min"],
                factor_vs_table_xx=s1["table_xx_available"] / pred,
                factor_vs_fig76=s1["fig76_min"] / pred,
                stage1_metal_C=s1["pitch_metal_C"], stage2_metal_C=s2["C"])


def implied_stress_ratio(n_exponent=10.0):
    """What the miss costs in stress. Life ~ sigma^-n near the design point
    for a superalloy, n about 8-15; the stage-1 blade must be this much less
    stressed than the stage-2 blade for the published lives to be consistent
    at one master curve. `n_exponent` is a HANDBOOK RANGE, not a source."""
    b = band3_same_stress_transfer()
    return (b["published_table_xx"] / b["predicted_hours"]) ** (-1.0 / n_exponent)


# --- band 4: the eleven points are a stress map, not a creep curve ----------

def band4_constant_stress_residuals(c=C_LARSON_MILLER):
    """Fit one constant-stress master curve to all eleven points -- that is,
    one LMP -- and report each point's residual in log10(life)."""
    pts = fig84_points()
    ps = [lmp(p["C"], p["hours"], c) for p in pts]
    p_bar = sum(ps) / len(ps)
    rows = []
    for p, pp in zip(pts, ps):
        pred = hours_from_lmp(p_bar, p["C"], c)
        rows.append(dict(where=p["where"], C=p["C"], hours=p["hours"],
                         lmp=pp, predicted=pred,
                         dlog=math.log10(p["hours"] / pred)))
    rows.sort(key=lambda r: -r["dlog"])
    return p_bar, rows


# --- band 5: the standing rule ----------------------------------------------

def band5_fifty_degrees(c=C_LARSON_MILLER):
    """50 C of metal temperature is about 10x creep life. Checked on the
    calibrated curve at the stage-2 limiting point."""
    s2 = stage2_limiting()
    p = lmp(s2["C"], s2["hours"], c)
    hotter = hours_from_lmp(p, s2["C"] + 50.0, c)
    return s2["hours"] / hotter


def main():
    print("Unit E10 -- HPT blade rupture life, CR-167955 Fig 84")
    print(f"Larson-Miller constant C = {C_LARSON_MILLER} (ASSUMPTION: "
          "standard for Ni; no source on disk carries one for Rene 150)\n")

    b1 = band1_same_section()
    print(f"band 1  Fig 84 {b1['fig84'][0]}-{b1['fig84'][1]} C   "
          f"Fig 35 all nodes {b1['fig35'][0]}-{b1['fig35'][1]} C   "
          f"cold end {b1['dmin']:.0f} K, hot end {b1['dmax']:.0f} K")
    print(f"        (Fig 35 SURFACE nodes alone {b1['fig35_surface'][0]}-"
          f"{b1['fig35_surface'][1]} C: cold end {b1['dmin_surface_only']:.0f} K)")

    print("\nband 2  mission mixes")
    for stage, d in band2_mission_mix().items():
        print(f"  {stage}: shares sum {d['share_sum']:.1f} %, equivalent "
              f"{d['equivalent_hours']} h, available {d['available']} h, "
              f"margin {d['margin']:.3f}; implied life ratio climb "
              f"{d['life_ratio_climb']:.1f}x, cruise {d['life_ratio_cruise']:.1f}x")

    b3 = band3_same_stress_transfer()
    print(f"\nband 3  stage-2 limiting point {b3['stage2_metal_C']} C, "
          f"LMP {b3['lmp']:.0f}")
    print(f"        stage-1 pitch metal {b3['stage1_metal_C']} C -> "
          f"{b3['predicted_hours']:.0f} h at the same stress")
    print(f"        published: Table XX {b3['published_table_xx']} h "
          f"(factor {b3['factor_vs_table_xx']:.2f}), "
          f"Fig 76 {b3['published_fig76']} h "
          f"(factor {b3['factor_vs_fig76']:.2f})")
    for n in (8.0, 10.0, 15.0):
        print(f"        stress ratio sigma_1/sigma_2 implied at n={n:.0f}: "
              f"{implied_stress_ratio(n):.3f}")

    p_bar, rows = band4_constant_stress_residuals()
    print(f"\nband 4  one constant-stress LMP over all eleven points: {p_bar:.0f}")
    print(f"  {'location':<28}{'C':>6}{'hours':>7}{'pred':>8}{'dlog':>7}")
    for r in rows:
        print(f"  {r['where']:<28}{r['C']:>6}{r['hours']:>7}{r['predicted']:>8.0f}{r['dlog']:>+7.2f}")

    print(f"\nband 5  50 C of metal temperature is worth "
          f"{band5_fifty_degrees():.1f}x in life")


if __name__ == "__main__":
    main()

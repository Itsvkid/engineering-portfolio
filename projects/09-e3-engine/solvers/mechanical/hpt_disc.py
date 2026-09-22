"""Stage E unit E14: what two drawings of one rotor agree about, and what
that is worth to E2 and to D6 item 2.

`tools/read_hpt_fig50.py` calibrates CR-167955 Figure 50 p.87 on the four
published flowpath radii, measures five radii at depth on **both** Figure 50
and Figure 112, and measures the two live-disc rims.  This module never
opens a PDF: it reads that YAML and Figure 112's, and answers three
questions.

1.  **Are the two readings consistent?**  Not "do they agree to 5 %" alone
    -- that is band E3r and it is answered too -- but the sharper question:
    is the difference between them inside what each figure's own anchors say
    a radius at that depth is worth?  Four anchors spanning 6.9 cm carry a
    95 % interval that grows fast below them (E12 finding 267), and if the
    observed disagreement sits inside the combined interval then the two
    figures are consistent and simply imprecise, which is a different verdict
    from a mistake.

2.  **Does the measured geometry make E2's comparison honest?**  E2 has been
    gated since 2026-09-07 on the disc cross-sections, and E12 narrowed that
    to the bore radius.  The arithmetic here is the test of whether the bore
    was ever the binding constraint.

3.  **How far does D6 item 2 go?**  The HPT disc faces carry the same term as
    E11's compressor drum with the opposite sign.  The geometry is now
    measured; the question is what else it needs.

STEP0.md, unit E14.
"""
from __future__ import annotations

import math

import yaml

from e3cycle.cycle import DATA
from mechanical.disc import (NU, RHO_RENE95, MPA, hoop_stress_annular,
                             hoop_stress_solid, rim_load_hoop)

#: t(0.975) at 2 degrees of freedom -- four anchors, two fitted parameters
T975_DOF2 = 4.302653

#: Figure 64 prints its stage-1 disc stresses at "40 s into accel". Two
#: speeds in the same report can be that instant, and they are 4.9 % apart:
#: Fig 53's transient reads 13,300 rpm at max takeoff, and both stage-1
#: dovetail figures -- which the same section reports, and from which the
#: blade pull used here is taken -- are printed at 13,948 rpm on the growth
#: engine, which sec 3.2.7 says was limiting throughout for the rotor.
#: 13,948 is used as the primary because the blade pull entering the same
#: sum is printed at it; 13,300 is carried beside it, never averaged.
SPEEDS_FOR_FIG64_RPM = dict(growth_takeoff=13948, fig53_max_takeoff=13300)


def _y(name):
    return yaml.safe_load((DATA / name).read_text())


def fig50():
    return _y("hpt-fig50-calibration.yaml")


def fig112():
    return _y("hpt-rotor-calibration.yaml")


# ------------------------------------------------- what each figure is worth

def _anchor_frame(cal, feats):
    """the (Y, R) pairs a calibration was fitted on, de-rotated"""
    t = math.tan(math.radians(cal["rot_deg"]))
    xref = cal.get("xref")
    Y, R = [], []
    for s in ("stage1", "stage2"):
        for k in ("tip", "platform"):
            f = feats[s][k]
            Y.append(f["y_px"] - t * (f["x_px"] - xref))
            R.append(f["r_published_cm"])
    return Y, R


def interval_at(cal, feats, r_target, conf_t=T975_DOF2):
    """95 % interval on a radius read off one figure, from that figure's own
    four anchors. The lever is (r_target - mean anchor radius), so it grows
    linearly below the anchors and the anchors span only 6.9 cm."""
    Y, R = _anchor_frame(cal, feats)
    n = len(Y)
    ybar = sum(Y) / n
    syy = sum((y - ybar) ** 2 for y in Y)
    a, b = cal["a"], cal["b"]
    res = [R[i] - (a + b * Y[i]) for i in range(n)]
    s2 = sum(v * v for v in res) / (n - 2)
    y = (r_target - a) / b
    se = math.sqrt(s2 * (1 / n + (y - ybar) ** 2 / syy))
    return conf_t * se


def consistency_table():
    """Band E3r and band E4r, plus the question neither band asks: is the
    observed difference inside the two figures' combined 95 % interval?"""
    f50, f112 = fig50(), fig112()
    cal50, feat50 = f50["calibration"], f50["features"]
    cal112, feat112 = dict(f112["calibration"], xref=2750), f112["features"]
    rows = []
    for name, v in f50["cross_check"].items():
        if name == "summary":
            continue
        r50, r112 = v["fig50"]["r_cm"], v["fig112"]["r_cm"]
        i50 = interval_at(cal50, feat50, r50)
        i112 = interval_at(cal112, feat112, r112)
        comb = math.hypot(i50, i112)
        rows.append(dict(
            feature=name, r_fig50_cm=r50, r_fig112_cm=r112,
            difference_cm=r50 - r112,
            difference_pct=100 * (r50 - r112) / r112,
            interval_fig50_cm=i50, interval_fig112_cm=i112,
            combined_cm=comb,
            inside_combined=abs(r50 - r112) <= comb,
            within_5_pct=abs(100 * (r50 - r112) / r112) <= 5.0,
            within_half_cm=abs(r50 - r112) <= 0.5))
    return rows


def residual_is_the_rotation():
    """What a four-anchor calibration's rms actually measures.

    Both figures' four anchors sit at TWO axial stations, one per blade. A
    residual rotation d(theta) therefore shifts one pair of anchors relative
    to the other by tan(d_theta) * dx and nothing else, and a two-parameter
    line through four points in two equal groups splits a group offset as
    plus and minus a half. So

        rms  ==  0.5 * tan(d_theta) * dx / scale

    with d_theta the gap between the angle imposed and the angle the anchors
    would have chosen. If that holds, the anchor rms carries no information
    about line weight, scan quality or reading care -- only about how well
    the page rotation is known.
    """
    out = {}
    for tag, d in (("fig50", fig50()), ("fig112", fig112())):
        c, fr, ft = (d["calibration"], d["calibration_free_rotation"],
                     d["features"])
        xs = [ft[s][k]["x_px"] for s in ("stage1", "stage2")
              for k in ("tip", "platform")]
        dx = max(xs) - min(xs)
        dtheta = abs(fr["rot_deg"] - c["rot_deg"])
        reach = math.tan(math.radians(dtheta)) * dx / c["px_per_cm"]
        out[tag] = dict(x_span_px=dx, angle_gap_deg=dtheta,
                        radial_reach_cm=reach, rms_cm=c["rms_cm"],
                        rms_over_reach=c["rms_cm"] / reach,
                        line_width_cm=14 / c["px_per_cm"])
    out["note"] = ("the predicted ratio is 0.5 on any page. It is met on "
                   "both, which is why the smaller drawing fits better: it "
                   "is tilted less, not drawn more carefully.")
    return out


def implied_scale_difference():
    """A disagreement that grows as the radius falls is a SCALE difference,
    not an offset. Both figures are pinned to the same four published radii,
    so they agree near the anchors by construction; below them they diverge
    at a rate that is the difference between the two fitted scales.

    The point of computing it: the anchors span 6.9 cm, which is why neither
    figure's own fit can see a scale error of this size."""
    rows = consistency_table()
    f50, f112 = fig50(), fig112()
    Y, R = _anchor_frame(dict(f112["calibration"], xref=2750), f112["features"])
    r_bar = sum(R) / len(R)
    eps = [100 * row["difference_cm"] / (r_bar - row["r_fig112_cm"])
           for row in rows]
    # what each figure's own anchors say its scale is worth, 95 %
    out = {}
    for tag, cal, feats in (("fig50", f50["calibration"], f50["features"]),
                            ("fig112", dict(f112["calibration"], xref=2750),
                             f112["features"])):
        Yt, Rt = _anchor_frame(cal, feats)
        n = len(Yt)
        rbar = sum(Rt) / n
        srr = sum((v - rbar) ** 2 for v in Rt)
        res = [Rt[i] - (cal["a"] + cal["b"] * Yt[i]) for i in range(n)]
        s = math.sqrt(sum(v * v for v in res) / (n - 2))
        out[tag] = dict(anchor_span_cm=max(Rt) - min(Rt),
                        scale_se_pct=100 * s / math.sqrt(srr),
                        scale_95_pct=100 * T975_DOF2 * s / math.sqrt(srr))
    comb95 = math.hypot(out["fig50"]["scale_95_pct"],
                        out["fig112"]["scale_95_pct"])
    return dict(anchor_mean_radius_cm=r_bar,
                implied_scale_difference_pct=eps,
                implied_mean_pct=sum(eps) / len(eps),
                per_figure=out, combined_95_pct=comb95,
                detectable=abs(sum(eps) / len(eps)) > comb95,
                note="the mean implied scale difference against what the two "
                     "sets of anchors together could ever have detected")


def inner_surface_spacings():
    """Are the three surfaces at the bottom of the rotor the SAME three
    surfaces on both pages? Their radii disagree; their SPACINGS should not
    if they are the same parts, and that is a check the radii cannot make."""
    cc = fig50()["cross_check"]
    r50 = [cc[f"inner_surface_{i}"]["fig50"]["r_cm"] for i in (1, 2, 3)]
    r112 = [cc[f"inner_surface_{i}"]["fig112"]["r_cm"] for i in (1, 2, 3)]
    g50 = [r50[0] - r50[1], r50[1] - r50[2]]
    g112 = [r112[0] - r112[1], r112[1] - r112[2]]
    return dict(gaps_fig50_cm=g50, gaps_fig112_cm=g112,
                difference_cm=[g50[i] - g112[i] for i in range(2)],
                note="a wall thickness is a difference of two radii on the "
                     "same page, so the offset that dominates the radii "
                     "cancels out of it")


# ------------------------------------------------------------- E2's question

def measured_geometry():
    """everything E2 and D6 need that a figure can give, with its provenance"""
    f50 = fig50()
    lr = f50["live_disc_rim"]
    cc = f50["cross_check"]
    inner = sorted([cc[f"inner_surface_{i}"][p]["r_cm"]
                    for i in (1, 2, 3) for p in ("fig50", "fig112")])
    return dict(
        rim_stage1_cm=lr["stage1"]["r_cm"],
        rim_stage2_cm=lr["stage2"]["r_cm"],
        rim_src="measured on CR-167955 Fig 112, the dovetail seat",
        bore_region_low_cm=inner[0], bore_region_high_cm=inner[-1],
        bore_src="the three surfaces at the bottom of the rotor, as read on "
                 "BOTH figures -- the full spread of six readings, not one",
        rim_axial_width_cm=_y("hpt-mechanical.yaml")["stage1_blade"]
                             ["dovetail"]["axial_chord_cm"],
        rim_axial_width_src="the printed stage-1 dovetail axial chord, taken "
                            "as the rim axial width. A proxy: the disc post "
                            "is at least as long as the slot in it.")


def published_fig64_bore_MPa():
    """E2's target, read from the YAML and never written here"""
    m = _y("hpt-mechanical.yaml")
    pts = m["rotor_components"]["stage1_disk"]["stress_life_map"]["points"]
    (bore,) = [p for p in pts if p["where"] == "bore"]
    return float(bore["MPa"])


def bore_stress_bracket(rpm=None, a_cm=None, b_cm=None, t_cm=None):
    """The constant-thickness bracket at the MEASURED rim and bore.

    A real disc is thick at the bore and thin at the web, so it must sit
    below a constant-thickness annular disc of the same rim radius and above
    a solid one. Both ends carry the blade pull as a rim radial stress.
    """
    g = measured_geometry()
    rpm = rpm or SPEEDS_FOR_FIG64_RPM["growth_takeoff"]
    b = (b_cm if b_cm is not None else g["rim_stage1_cm"]) / 100
    a = (a_cm if a_cm is not None else
         0.5 * (g["bore_region_low_cm"] + g["bore_region_high_cm"])) / 100
    t = (t_cm if t_cm is not None else g["rim_axial_width_cm"]) / 100
    om = rpm * 2 * math.pi / 60

    m = _y("hpt-mechanical.yaml")
    pub = _y("e3-fps-published.yaml")
    n = pub["hpt"]["stage_aerodynamics"]["blade_count"][0]
    per = m["stage1_blade"]["dovetail"]["load_per_blade_kN"]
    rpm_pull = m["stage1_blade"]["dovetail"]["condition"]["rpm"]
    total_kN = n * per * (rpm / rpm_pull) ** 2
    S = total_kN * 1e3 / (2 * math.pi * b * t) / MPA

    rot_annular = hoop_stress_annular(a, a, b, RHO_RENE95, om) / MPA
    rot_solid = hoop_stress_solid(0.0, b, RHO_RENE95, om) / MPA
    upper = rot_annular + rim_load_hoop(S, a / b)
    lower = rot_solid + S               # a solid disc carries a rim traction
    published = published_fig64_bore_MPa()
    return dict(rpm=rpm, a_cm=a * 100, b_cm=b * 100, t_cm=t * 100,
                blade_pull_total_kN=total_kN, rim_radial_MPa=S,
                rotation_annular_MPa=rot_annular, rotation_solid_MPa=rot_solid,
                rim_term_annular_MPa=rim_load_hoop(S, a / b),
                upper_MPa=upper, lower_MPa=lower,
                published_fig64_bore_MPa=published,
                upper_over_published=upper / published,
                lower_over_published=lower / published,
                published_inside=lower <= published <= upper,
                bracket_ratio=upper / lower)


def sensitivity_ladder():
    """Which input moves E2's answer. The point of the unit: the bore radius
    has been the named gate since 2026-09-07 and is at the bottom of it."""
    g = measured_geometry()
    base = bore_stress_bracket()
    lo, hi = g["bore_region_low_cm"], g["bore_region_high_cm"]
    out = []

    def add(what, kw, span):
        v = bore_stress_bracket(**kw)
        out.append(dict(input=what, span=span,
                        upper_MPa=v["upper_MPa"],
                        change_pct=100 * (v["upper_MPa"] - base["upper_MPa"])
                        / base["upper_MPa"]))

    add("bore radius, low end", dict(a_cm=lo), f"{lo:.2f} cm")
    add("bore radius, high end", dict(a_cm=hi), f"{hi:.2f} cm")
    add("bore radius, 5 cm", dict(a_cm=5.0), "5 cm")
    add("bore radius, 14 cm", dict(a_cm=14.0), "14 cm")
    add("rim radius -1 %", dict(b_cm=g["rim_stage1_cm"] * 0.99), "-1 % of r")
    add("rim radius +1 %", dict(b_cm=g["rim_stage1_cm"] * 1.01), "+1 % of r")
    add("rim radius = the flowpath hub", dict(b_cm=32.455),
        "32.46 cm, what disc.py used before this unit")
    add("rim axial width 4.4 cm", dict(t_cm=4.4), "the drawn rim width")
    add("speed 13,300 rpm", dict(rpm=SPEEDS_FOR_FIG64_RPM["fig53_max_takeoff"]),
        "Fig 53's max takeoff")
    return dict(base=base, rows=out,
                profile_effect_pct=100 * (base["upper_MPa"] - base["lower_MPa"])
                / base["upper_MPa"])


# ------------------------------------------------------- D6 item 2's question

def disc_face_areas(a_cm=None):
    """the projected annulus each HPT disc face presents to its cavity"""
    g = measured_geometry()
    a = (a_cm if a_cm is not None else
         0.5 * (g["bore_region_low_cm"] + g["bore_region_high_cm"])) / 100
    b1, b2 = g["rim_stage1_cm"] / 100, g["rim_stage2_cm"] / 100
    A1 = math.pi * (b1 ** 2 - a ** 2)
    A2 = math.pi * (b2 ** 2 - a ** 2)
    return dict(bore_cm=a * 100, stage1_m2=A1, stage2_m2=A2,
                difference_m2=A1 - A2,
                difference_pct_of_stage1=100 * (A1 - A2) / A1)


def face_area_uncertainty():
    """One calibration, two verdicts: a disc face is a radial extent from
    bore to rim, so it takes its rim from the 1 %-of-r half of the
    calibration and its bore from the 9-13 % half. What that does to an
    AREA is not 13 %, because the area is a difference of squares and the
    bore is a quarter of the rim."""
    g = measured_geometry()
    lo = disc_face_areas(g["bore_region_low_cm"])
    hi = disc_face_areas(g["bore_region_high_cm"])
    mid = disc_face_areas()
    b_span_pct = 100 * (g["bore_region_high_cm"] - g["bore_region_low_cm"]) \
        / g["bore_region_low_cm"]
    return dict(
        bore_span_cm=(g["bore_region_low_cm"], g["bore_region_high_cm"]),
        bore_span_pct=b_span_pct,
        stage1_area_span_m2=(hi["stage1_m2"], lo["stage1_m2"]),
        stage1_area_span_pct=100 * (lo["stage1_m2"] - hi["stage1_m2"])
        / mid["stage1_m2"],
        rim_interval_pct=100 * interval_at(
            dict(fig112()["calibration"], xref=2750), fig112()["features"],
            g["rim_stage1_cm"]) / g["rim_stage1_cm"],
        note="the bore disagreement between the two figures is 20 % of the "
             "bore and under 6 % of the face area, because pi(b^2 - a^2) "
             "with a/b about 0.25 is 94 % rim")


def interstage_cavity_pressure_MPa():
    """The gas pressure the two middle disc faces sit next to, from published
    numbers only: the stage-1 vane gas total and the printed stage-1 pressure
    ratio. The cavity itself runs a per-cent above the gas -- that is what a
    backflow margin is -- and CR-168211 measured it."""
    c = _y("hpt-cooling.yaml")
    pub = _y("e3-fps-published.yaml")
    pt4 = c["stage1_nozzle"]["cavity_pressures"]["gas_at_vane"]["pt_MPa"] \
        if "gas_at_vane" in c["stage1_nozzle"].get("cavity_pressures", {}) \
        else None
    if pt4 is None:                       # the block is one level up
        pt4 = _find(c, "gas_at_vane")["pt_MPa"]
    pr1 = pub["hpt"]["stage_aerodynamics"]["pressure_ratio"][0]
    return dict(pt_stage1_vane_MPa=pt4, stage1_pressure_ratio=pr1,
                interstage_total_MPa=pt4 / pr1,
                src="hpt-cooling.yaml gas_at_vane pt_MPa (HPT report sec 3, "
                    "SLTO hot day) over Table III's printed stage-1 "
                    "pressure ratio")


def _find(o, key):
    if isinstance(o, dict):
        if key in o:
            return o[key]
        for v in o.values():
            r = _find(v, key)
            if r is not None:
                return r
    return None


def middle_faces():
    """What the two MEASURED cavity pressures do. CR-168211 Fig 210 p.348
    plots the interstage cavity pressure and the forward and aft wheelspace
    pressures against HPT corrected speed, and its text (p.343) says there
    was no discernible difference between the cavity and the forward
    wheelspace, with margins of 0.39-1 % dP.

    Those two wheelspaces are the cavity on the stage-1 disc's AFT face and
    the cavity on the stage-2 disc's FORWARD face. They push the rotor in
    opposite directions, so if they were equal AND the two faces were equal
    they would cancel. They are equal to 1 %. The faces are not equal.
    """
    A = disc_face_areas()
    p = interstage_cavity_pressure_MPa()["interstage_total_MPa"] * 1e6
    net = p * A["difference_m2"] / 1e3          # kN, positive forward
    dp_term = 0.01 * p * A["stage2_m2"] / 1e3
    # the net is a small difference of two large numbers, so it is quoted
    # against the ratio of the two cavity pressures rather than at one value
    sweep = [dict(p_aft_over_p_fwd=k,
                  net_kN=p * (A["stage1_m2"] - k * A["stage2_m2"]) / 1e3)
             for k in (0.95, 0.98, 1.00, 1.02, 1.05)]
    return dict(
        cavity_pressure_MPa=p / 1e6,
        stage1_aft_face_kN=p * A["stage1_m2"] / 1e3,
        stage2_forward_face_kN=-p * A["stage2_m2"] / 1e3,
        net_kN=net,
        one_percent_pressure_difference_kN=dp_term,
        ratio_sweep=sweep,
        sign="positive is forward, as unit D6",
        what_is_evidenced="CR-168211 p.343 says there was no discernible "
                          "difference between the interstage cavity and the "
                          "FORWARD wheelspace. It says nothing in words about "
                          "the aft wheelspace, which Figure 210 plots. So "
                          "k = 1 is an assumption for the aft face and the "
                          "sweep is what it is worth.",
        note="the two faces do not cancel: the stage-1 disc rim is 30.77 cm "
             "and the stage-2 rim 27.88, so the forward disc presents 23 % "
             "more area to the same pressure")


def what_is_not_published():
    """One quantity per entry, with the documents searched -- the form
    finding 269 forced. Two of the four HPT disc-face pressures ARE
    published, measured, and this unit's own step 0 predicted they were
    not."""
    searched = ["CR-167955 (HPT hardware)", "CR-168219 (FPS final design)",
                "CR-168211 (ICLS as tested)", "e3-hp-turbine-cooling-model",
                "e3-core-design-and-performance"]
    return dict(
        published_after_all=dict(
            quantity="the pressure in the cavity on the stage-1 disc aft "
                     "face and in the cavity on the stage-2 disc forward "
                     "face, against HPT corrected speed",
            where="CR-168211 Figure 210 p.348, 'High Pressure Turbine Stage 2 "
                  "Vane Cooling and Purge Pressures', with the text on p.343",
            note="unit E14's step 0 predicted this was unpublished. It is "
                 "not. A design report describes hardware; a test report "
                 "publishes what the hardware did."),
        still_not_found=[
            dict(quantity="the pressure in the cavity on the stage-1 disc "
                          "FORWARD face, between the disc and the impeller",
                 documents_searched=searched),
            dict(quantity="the pressure in the cavity on the stage-2 disc "
                          "AFT face, forward of the turbine aft seal",
                 documents_searched=searched),
            dict(quantity="the balance-piston area or radius",
                 documents_searched=searched,
                 note="finding 191, unchanged. Figs 95-96 give the seal as "
                      "hardware and never as a load."),
        ])


# ----------------------------------------------------------------- reporting

def main():
    f50 = fig50()
    c, r = f50["calibration"], f50["page_rotation"]
    print("UNIT E14 -- CR-167955 Figure 50 p.87 against Figure 112 p.180\n")
    print(f"E1  anchor fit           {c['rms_cm']:.4f} cm rms, "
          f"{c['max_cm']:.4f} max, band 0.25   "
          f"{'MET' if c['rms_cm'] <= 0.25 else 'FAILED'}")
    print(f"    scale                {c['px_per_cm']:.2f} px/cm, 1:"
          f"{c['drawing_scale_one_to']:.2f}, "
          f"{f50['scale_relative_to_figure_112']['ratio']:.3f} of Fig 112")
    print(f"E2r caption lines agree  {r['spread_deg']:.3f} deg, band 0.15    "
          f"{'MET' if r['spread_deg'] <= 0.15 else 'FAILED'}")
    n = f50["calibration_without_rotation"]
    print(f"    imposing it is worth {n['rms_cm'] / c['rms_cm']:.3f}x on the "
          f"rms -- on Figure 112 it was 4.9x")
    rr = residual_is_the_rotation()
    print("    and the anchor rms is half the rotation gap's radial reach, "
          "on both pages:")
    for tag in ("fig50", "fig112"):
        v = rr[tag]
        print(f"      {tag:6s} gap {v['angle_gap_deg']:.3f} deg -> reach "
              f"{v['radial_reach_cm']:.4f} cm, rms {v['rms_cm']:.4f}, "
              f"ratio {v['rms_over_reach']:.3f} (line width "
              f"{v['line_width_cm']:.3f} cm)")

    print("\nCROSS-CHECK")
    print(f"  {'feature':28s}{'fig50':>8s}{'fig112':>8s}{'diff':>8s}"
          f"{'%':>7s}{'+-95%':>8s}  verdict")
    for row in consistency_table():
        v = ("consistent" if row["inside_combined"] else "INCONSISTENT")
        print(f"  {row['feature']:28s}{row['r_fig50_cm']:8.3f}"
              f"{row['r_fig112_cm']:8.3f}{row['difference_cm']:+8.3f}"
              f"{row['difference_pct']:+7.2f}{row['combined_cm']:8.3f}  {v}"
              f"{'' if row['within_5_pct'] else '   (outside 5 %)'}")
    s = inner_surface_spacings()
    print(f"  wall thicknesses       fig50 {s['gaps_fig50_cm'][0]:.3f}/"
          f"{s['gaps_fig50_cm'][1]:.3f}  fig112 {s['gaps_fig112_cm'][0]:.3f}/"
          f"{s['gaps_fig112_cm'][1]:.3f} cm -- the same three surfaces")
    sd = implied_scale_difference()
    print(f"  implied scale difference {sd['implied_mean_pct']:+.2f} % against "
          f"a combined 95 % detectable of {sd['combined_95_pct']:.2f} % "
          f"-- {'detectable' if sd['detectable'] else 'NOT detectable'} by "
          f"either figure's own anchors")

    print("\nE2 -- the bracket at the MEASURED rim and bore")
    lad = sensitivity_ladder()
    b = lad["base"]
    print(f"  rim {b['b_cm']:.3f} cm, bore {b['a_cm']:.3f} cm, "
          f"rim width {b['t_cm']:.2f} cm, {b['rpm']} rpm")
    print(f"  blade pull {b['blade_pull_total_kN']:.0f} kN -> rim radial "
          f"{b['rim_radial_MPa']:.1f} MPa")
    print(f"  solid disc  {b['lower_MPa']:7.1f} MPa   "
          f"({b['lower_over_published']:.2f} x published)")
    print(f"  published   {b['published_fig64_bore_MPa']:7.1f} MPa   Fig 64, bore, 40 s")
    print(f"  bored disc  {b['upper_MPa']:7.1f} MPa   "
          f"({b['upper_over_published']:.2f} x published)")
    print(f"  bracket is {b['bracket_ratio']:.2f}:1 wide against a 10 % band -- "
          f"{'MET' if abs(b['upper_over_published'] - 1) <= 0.1 else 'FAILED'}")
    print("  what moves it:")
    for row in lad["rows"]:
        print(f"    {row['input']:38s}{row['span']:>34s}"
              f"{row['change_pct']:+8.2f} %")

    print("\nD6 item 2 -- the HPT disc faces")
    fa = face_area_uncertainty()
    A = disc_face_areas()
    print(f"  bore spread between the two figures "
          f"{fa['bore_span_cm'][0]:.2f}-{fa['bore_span_cm'][1]:.2f} cm "
          f"({fa['bore_span_pct']:.1f} % of the bore)")
    print(f"  stage-1 face area {A['stage1_m2']:.4f} m2, moves "
          f"{fa['stage1_area_span_pct']:.2f} % across that spread "
          f"-- band +-20 % "
          f"{'MET on geometry' if abs(fa['stage1_area_span_pct']) <= 20 else 'FAILED'}")
    mf = middle_faces()
    print(f"  at the published interstage {mf['cavity_pressure_MPa']:.3f} MPa: "
          f"stage-1 aft {mf['stage1_aft_face_kN']:+.0f} kN, stage-2 forward "
          f"{mf['stage2_forward_face_kN']:+.0f} kN, net {mf['net_kN']:+.0f} kN")
    print(f"  a 1 % difference between the two measured cavity pressures is "
          f"worth {mf['one_percent_pressure_difference_kN']:.1f} kN")
    print("  net against the aft/forward cavity pressure ratio:")
    for row in mf["ratio_sweep"]:
        print(f"    p_aft/p_fwd = {row['p_aft_over_p_fwd']:.2f}"
              f"{row['net_kN']:+9.0f} kN")
    npz = what_is_not_published()
    print(f"  PUBLISHED AFTER ALL: {npz['published_after_all']['where']}")
    for e in npz["still_not_found"]:
        print(f"  still not found: {e['quantity']}")


if __name__ == "__main__":
    main()

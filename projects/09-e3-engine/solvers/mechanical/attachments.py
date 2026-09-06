"""Stage E5: attachments and joints — dovetails, retainers and flange bolts.

The work plan's E5 closure: *every attachment has margin on all three
stresses and the weak-link order holds* — disc slot stronger than blade
root, blade root stronger than airfoil.

**One item is gated.** The first bullet asks for the HPC dovetails per HPC
report sec 3.2.3, and `hpc-mechanical.yaml` has no blade block and no
dovetail block at all: its meta records only Tables XV-XIX and Figs 55-62
as transcribed. Nothing to work with; written down, not worked around.

Everything else the E³ reports print in full, and the interesting part is
that the printed numbers can be made to check *each other*:

  * The **HPT stage-1 two-tang dovetail** prints one blade load, two neck
    widths, one axial chord and two combined stresses. Five numbers and
    one geometry, so the load split between the tangs is recoverable
    rather than assumed.
  * The **fan and booster dovetail crush stresses** are printed, and the
    loads that cause them follow from the blade masses E4 audited against
    Table VI. Bearing area is then an *output*.
  * **LPT Fig. 70** prints six stresses around the dovetail for two blade
    sections and two disc sections, *and* a stress-concentration factor
    for each. The factor can be checked against the stresses beside it.
  * The **LPT blade retainers** print a design force, two thicknesses and
    a maximum stress for three stages against one allowable — enough to
    recover which thickness carries the load and by what law.
  * The **casing flanges** print a bolt count, a bolt size and the
    criterion (*no axial separation at twice maximum operating pressure*),
    and the cycle prints the pressure.

STEP0.md, unit E5."""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass

import yaml

from e3cycle import cycle as cyc
from e3cycle.cycle import DATA

CM2 = 1e-4          # cm^2 -> m^2
KN_CM2_TO_MPA = 10.0


def _y(name):
    return yaml.safe_load((DATA / name).read_text())


# ------------------------------------------- the HPT two-tang dovetail

def hpt_dovetail_tangs():
    """Fig 81 prints the blade load, the axial chord, two neck widths and
    two combined-with-Kt stresses. The text says the upper tang is 'a
    deeper tang for the higher load' -- so how much higher? The two
    printed stresses are in almost exactly the ratio of the two printed
    neck widths, and that fixes the split."""
    dt = _y("hpt-mechanical.yaml")["stage1_blade"]["dovetail"]
    load, chord = dt["load_per_blade_kN"] * 1e3, dt["axial_chord_cm"] / 100
    tangs = dt["tangs"]
    w = [t["neck_width_cm"] / 100 for t in tangs]
    sig = [t["combined_stress_with_kt_MPa"] for t in tangs]
    area = [x * chord for x in w]

    # if the load split by AREA every tang would read the same stress; the
    # printed stresses differ, and by the ratio of the widths
    split_w2 = [x ** 2 / sum(v ** 2 for v in w) for x in w]
    nominal = [load * f / a / 1e6 for f, a in zip(split_w2, area)]
    equal_stress = load / sum(area) / 1e6
    return dict(load_kN=load / 1e3, chord_m=chord,
                names=[t["tang"] for t in tangs], widths_m=w, areas_m2=area,
                printed_MPa=sig, stress_ratio=sig[0] / sig[1],
                width_ratio=w[0] / w[1],
                ratio_of_ratios=(sig[0] / sig[1]) / (w[0] / w[1]),
                split_w2=split_w2, nominal_MPa=nominal,
                equal_stress_MPa=equal_stress,
                combined_factor=[s / n for s, n in zip(sig, nominal)])


# --------------------------------------------------- crush, two dovetails

@dataclass
class Crush:
    blade: str
    load_kN: float
    printed_kN_cm2: float
    flank_width_cm: float
    bearing_length_cm: float
    one_flank_cm2: float
    implied_area_cm2: float
    implied_flanks: float


def dovetail_crush():
    """The printed crush stress and the computed blade load together give
    the bearing AREA the report used. Compared with one printed flank, that
    is the number of flanks the figure is quoting over."""
    from mechanical.rotordynamics import blade_masses
    f = _y("fan-design.yaml")
    rpm = f["fan_rotor_mechanical"]["campbell"]["max_speed_rpm"]
    om2 = (rpm * 2 * math.pi / 60) ** 2
    specs = {
        "fan rotor": (f["fan_rotor_mechanical"]["dovetail_and_post"]["blade"],
                      "flank_width_cm", "axial_length_cm"),
        "booster rotor": (f["booster_blade_mechanical"]["dovetail"],
                          "flank_width_cm", "length_cm"),
    }
    out = []
    for b in blade_masses():
        d, wk, lk = specs[b["name"]]
        load = b["printed_kg"] * om2 * b["r_cg_m"]
        one = d[wk] * d[lk]
        implied = load / 1e3 / d["crush_stress_kN_cm2"]
        out.append(Crush(b["name"], load / 1e3, d["crush_stress_kN_cm2"],
                         d[wk], d[lk], one, implied, implied / one))
    return out


# ------------------------------------------- LPT Fig 70's own Kt values

def lpt_fig70_kt():
    """Fig 70 prints six stresses around the dovetail for each of four
    sections AND a Kt for each section. If positions 1 and 2 are the
    nominal and the concentrated reading of the same place, position 2 /
    position 1 must be that Kt."""
    d = _y("lpt-design.yaml")["dovetails"]["stage1_stress_distribution"]
    out = []
    for key, kt_key in (("blade_A_MPa", "blade_A"), ("blade_B_MPa", "blade_B"),
                        ("disk_C_MPa", "disk_C"), ("disk_D_MPa", "disk_D")):
        s = d[key]
        printed = d["kt"][kt_key]
        ratio = s[1] / s[0]
        out.append(dict(section=kt_key, pos1=s[0], pos2=s[1], ratio=ratio,
                        printed_kt=printed, err_pct=(ratio / printed - 1) * 100,
                        agrees=abs(ratio / printed - 1) < 0.01))
    return out


# ---------------------------------------------------- LPT blade retainers

def lpt_retainers():
    """Three stages, one allowable. The design force rises 75 % across
    them and the maximum stress rises 2 % -- so the thickness was chosen
    to hold the stress. Which thickness, and by what law?"""
    r = _y("lpt-design.yaml")["blade_retainers"]["stages_1_3"]
    allow = r["design_allowable_MPa"]
    rows = []
    for i, st in enumerate(r["stage"]):
        rows.append(dict(stage=st, force_N=r["design_force_N"][i],
                         t1_cm=r["t1_cm"][i], t2_cm=r["t2_cm"][i],
                         sigma_MPa=r["sigma_max_MPa"][i],
                         margin=allow / r["sigma_max_MPa"][i]))
    laws = {}
    for tk in ("t1_cm", "t2_cm"):
        for power, label in ((1, "F/t"), (2, "F/t^2")):
            pred = [rows[0]["sigma_MPa"] * (x["force_N"] / rows[0]["force_N"])
                    * (rows[0][tk] / x[tk]) ** power for x in rows]
            err = max(abs(p / x["sigma_MPa"] - 1) for p, x in zip(pred, rows))
            laws[f"{tk} {label}"] = dict(pred=pred, worst_pct=err * 100)
    return rows, allow, laws


# ------------------------------------------------- the weak-link ordering

def weak_link_order():
    """Every attachment against its own printed limit. The order the goals
    demanded -- disc post stronger than blade dovetail, blade dovetail
    stronger than airfoil -- shows up as the ordering of the margins."""
    f = _y("fan-design.yaml")
    dp = f["fan_rotor_mechanical"]["dovetail_and_post"]
    rows = [dict(part="fan blade dovetail corner",
                 stress=max(dp["blade"]["corner_stresses_kN_cm2"].values()),
                 limit=dp["blade"]["lcf_limit_kN_cm2"]),
            dict(part="fan disc post corner",
                 stress=max(dp["post"]["corner_stresses_kN_cm2"].values()),
                 limit=dp["post"]["lcf_limit_kN_cm2"]),
            dict(part="fan blade dovetail crush",
                 stress=dp["blade"]["crush_stress_kN_cm2"],
                 limit=dp["blade"]["lcf_limit_kN_cm2"])]
    for r in rows:
        r["margin"] = r["limit"] / r["stress"]

    bm = f["booster_blade_mechanical"]
    booster = dict(airfoil_peak=bm["root_stress"]["concave_peak_kN_cm2"],
                   dovetail_corner=max(bm["dovetail"]["corner_stresses_kN_cm2"]),
                   crush=bm["dovetail"]["crush_stress_kN_cm2"])
    booster["attachment_below_airfoil"] = booster["dovetail_corner"] < booster["airfoil_peak"]

    h = _y("hpt-mechanical.yaml")
    hpt = dict(blade_tang_max=max(t["combined_stress_with_kt_MPa"]
                                  for t in h["stage1_blade"]["dovetail"]["tangs"]),
               disc_slot=h["rotor_components"]["stage1_disk"]["dovetail_max"]["stress_MPa"],
               blade_lcf=h["stage1_blade"]["dovetail"]["lcf_cycles"],
               disc_lcf=h["rotor_components"]["stage1_disk"]["dovetail_max"]["lcf_cycles"],
               disc_required=h["design_lives"]["disks_shafts_seal_disk"][3],
               blade_required=h["design_lives"]["flowpath_components_and_blade_retainers"][3])
    return rows, booster, hpt


# ------------------------------------------------------ casing flange bolts

def casing_bolting():
    """Table XVII's criterion is *no axial flange separation at 2 x maximum
    operating pressure*. The bolt count and size are printed and the cycle
    gives the pressure; the flange radius is taken as the flowpath tip
    radius at that station and is the one stated assumption."""
    cb = _y("hpc-mechanical.yaml")["casing_bolting"]
    radii = {}
    with open(DATA / "hpc-flowpath.csv") as fh:
        for row in csv.DictReader(l for l in fh if not l.startswith("#")):
            radii[(row["row"], row["edge"])] = float(row["r_tip_cm"]) / 100
    r_front, r_aft = radii[("IGV", "LE")], radii[("S10", "TE")]

    takeoff = max(cyc.run_all(), key=lambda r: r.stations["p3"])
    p25, p3 = takeoff.stations["p25"], takeoff.stations["p3"]

    # tensile stress area of a 3/8-24 UNF bolt: 0.7854 (d - 0.9743/n)^2
    d_in, n_tpi = 0.375, 24
    a_t = 0.7854 * (d_in - 0.9743 / n_tpi) ** 2 * (0.0254 ** 2)

    out = []
    for name, casing, p, r in (("front", cb["front_casing"], p25, r_front),
                               ("front at p3", cb["front_casing"], p3, r_front),
                               ("aft", cb["aft_casing"], p3, r_aft),
                               ("manifold", cb["manifold_casing"], p3, r_aft)):
        force = 2 * p * math.pi * r ** 2
        out.append(dict(flange=name, bolts=casing["bolts"], pressure_MPa=p / 1e6,
                        radius_cm=r * 100, separating_MN=force / 1e6,
                        per_bolt_kN=force / casing["bolts"] / 1e3,
                        bolt_stress_MPa=force / casing["bolts"] / a_t / 1e6))
    return out, a_t, takeoff.rating


if __name__ == "__main__":
    t = hpt_dovetail_tangs()
    print("1. The HPT stage-1 two-tang dovetail: how the load splits\n")
    print(f"   blade load {t['load_kN']:.3f} kN over an axial chord of "
          f"{t['chord_m'] * 100:.2f} cm")
    print(f"   printed stresses  {t['printed_MPa'][0]:.0f} / {t['printed_MPa'][1]:.0f} MPa"
          f"   ratio {t['stress_ratio']:.4f}")
    print(f"   printed widths    {t['widths_m'][0] * 100:.3f} / {t['widths_m'][1] * 100:.3f} cm"
          f"   ratio {t['width_ratio']:.4f}")
    print(f"   -> the two ratios agree to {abs(1 - t['ratio_of_ratios']) * 100:.2f} %, so"
          f" sigma is proportional to w")
    print(f"   -> the load splits as w^2: {t['split_w2'][0] * 100:.1f} % upper,"
          f" {t['split_w2'][1] * 100:.1f} % lower")
    print(f"      (an equal-stress design would split by area and read"
          f" {t['equal_stress_MPa']:.0f} MPa on both)")
    print(f"   nominal neck tension {t['nominal_MPa'][0]:.0f} / {t['nominal_MPa'][1]:.0f} MPa,"
          f" so the printed combined stress is"
          f" {t['combined_factor'][0]:.1f}x / {t['combined_factor'][1]:.1f}x nominal")

    print(f"\n2. Dovetail crush: the load is known, so the bearing area is an output\n")
    print(f"   {'blade':<15}{'load kN':>9}{'printed':>10}{'one flank':>11}"
          f"{'implied':>10}{'flanks':>8}")
    for c in dovetail_crush():
        print(f"   {c.blade:<15}{c.load_kN:>9.1f}{c.printed_kN_cm2:>10.1f}"
              f"{c.one_flank_cm2:>11.2f}{c.implied_area_cm2:>10.2f}{c.implied_flanks:>8.2f}")

    print(f"\n3. LPT Fig 70's stress-concentration factors, against its own stresses\n")
    print(f"   {'section':<10}{'pos 1':>8}{'pos 2':>8}{'ratio':>8}{'printed Kt':>12}{'err %':>8}")
    for r in lpt_fig70_kt():
        print(f"   {r['section']:<10}{r['pos1']:>8.1f}{r['pos2']:>8.1f}{r['ratio']:>8.3f}"
              f"{r['printed_kt']:>12.2f}{r['err_pct']:>8.1f}")

    rows, allow, laws = lpt_retainers()
    print(f"\n4. LPT blade retainers: three stages, one allowable of {allow:.1f} MPa\n")
    print(f"   {'stage':>6}{'force N':>10}{'t1 cm':>8}{'t2 cm':>8}{'sigma':>9}{'margin':>9}")
    for r in rows:
        print(f"   {r['stage']:>6}{r['force_N']:>10}{r['t1_cm']:>8.3f}{r['t2_cm']:>8.3f}"
              f"{r['sigma_MPa']:>9.1f}{r['margin']:>9.3f}")
    print(f"\n   which thickness carries it, and by what law?")
    for k, v in sorted(laws.items(), key=lambda kv: kv[1]["worst_pct"]):
        print(f"      {k:<14} worst {v['worst_pct']:>6.1f} %")

    fan, booster, hpt = weak_link_order()
    print(f"\n5. Weak-link order\n")
    for r in fan:
        print(f"   {r['part']:<28}{r['stress']:>7.1f} of {r['limit']:>5.1f} kN/cm2"
              f"   margin {r['margin']:.2f}")
    print(f"   booster: airfoil peak {booster['airfoil_peak']:.1f} vs dovetail corner"
          f" {booster['dovetail_corner']:.1f} kN/cm2"
          f"  -> attachment below airfoil: {booster['attachment_below_airfoil']}")
    print(f"   HPT: blade tang {hpt['blade_tang_max']:.0f} MPa vs disc slot"
          f" {hpt['disc_slot']:.0f} MPa   (as printed; different alloys and instants)")
    print(f"        disc slot LCF {hpt['disc_lcf']:,} cycles against a required"
          f" {hpt['disc_required']:,}; blade dovetail {hpt['blade_lcf']} against"
          f" {hpt['blade_required']:,}")

    bolts, a_t, rating = casing_bolting()
    print(f"\n6. Casing flanges: no axial separation at 2 x maximum pressure"
          f" ({rating})\n")
    print(f"   3/8-24 UNF tensile stress area {a_t * 1e6:.1f} mm2\n")
    print(f"   {'flange':<14}{'bolts':>7}{'p MPa':>8}{'r cm':>8}"
          f"{'separating MN':>15}{'per bolt kN':>13}{'bolt MPa':>10}")
    for b in bolts:
        print(f"   {b['flange']:<14}{b['bolts']:>7}{b['pressure_MPa']:>8.2f}"
              f"{b['radius_cm']:>8.1f}{b['separating_MN']:>15.2f}"
              f"{b['per_bolt_kN']:>13.1f}{b['bolt_stress_MPa']:>10.0f}")

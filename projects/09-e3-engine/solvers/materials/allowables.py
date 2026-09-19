"""Stage F1: materials with allowables — and a measurement that corrects
Stage E.

The work plan's F1 closure: *every stress in Stage E is compared with an
allowable at its metal temperature, and the margin is tabulated.*

**Half of that is gated, and the gate is in the handbook rather than in
the E³ reports.** MIL-HDBK-5J gives room-temperature design allowables as
tables — those are now transcribed in
`data/methods/mil-hdbk-5j-allowables.yaml` — but gives *elevated*
temperature strength as **figures**, percentage of the room-temperature
value against temperature, which were not digitised. And its wrought
alloys do not include René 77, René 95, René 150 or AF115 at all. So a
margin at temperature can be quoted only where the E³ reports themselves
print an allowable, and elsewhere what can be quoted is the
room-temperature margin and **how much of the allowable the metal would
have to lose before the margin is gone** — which is a bound, not a fudge.

The other half of F1 is the first bullet: *alloy per component from the
reports*. HPC report Table X prints a material for every one of the ten
rotor stages. It also prints, in the same table, each stage's **airfoil
weight** and **root area** — and Table XXII prints the section shapes. Put
those three together and the **density of every blade is a measurement**,
not an input:

    rho = m_airfoil / (A_root * integral of A(r)/A_root dr)

That measurement is what this module does first, because it settles a
question Stage E got half wrong. STEP0.md, unit F1."""
from __future__ import annotations

import math

import yaml

from e3cycle.cycle import DATA
from mechanical.blade_stress import area_distribution, stress_speed_rpm

KSI = 6.894757e6            # Pa
MSI = 6.894757e9            # Pa per 10^3 ksi
LB_IN3 = 27679.9            # kg/m^3
KN_CM2 = 1.0e7              # Pa


def load():
    pub = yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())
    hdbk = yaml.safe_load((DATA / "methods" / "mil-hdbk-5j-allowables.yaml").read_text())
    return pub, hdbk


def alloys():
    """the handbook table in SI, converted here rather than read"""
    _, hdbk = load()
    out = {}
    for name, a in hdbk["alloys"].items():
        out[name] = dict(
            src=a["src"], used_for=a["used_for"],
            ftu_MPa=a["ftu_ksi"] * KSI / 1e6, fty_MPa=a["fty_ksi"] * KSI / 1e6,
            e_GPa=a["e_msi"] * MSI / 1e9, poisson=a["poisson"],
            density=a["density_lb_in3"] * LB_IN3)
    return out


# ------------------------------------------------- the density measurement

def measured_blade_density():
    """Table X prints the airfoil weight and the root area of every HPC
    rotor stage; Table XXII prints the section shapes. Density follows.
    Nothing about the material is assumed -- it comes out."""
    pub, _ = load()
    rs = pub["hpc"]["rotor_stages"]
    a = alloys()
    rho_ti = a["ti_8al_1mo_1v_forging"]["density"]
    rho_ni = a["inconel_718_bar_forging"]["density"]
    om2 = (stress_speed_rpm() * 2 * math.pi / 60) ** 2
    out = []
    for i, stage in enumerate(rs["stage"]):
        d = area_distribution(stage)
        i1 = sum(0.5 * (a0 + a1) * (r1 - r0) for (r0, a0), (r1, a1) in zip(d, d[1:]))
        i2 = sum(0.5 * (a0 * r0 + a1 * r1) * (r1 - r0) for (r0, a0), (r1, a1) in zip(d, d[1:]))
        a_root = rs["root_area_cm2"][i] * 1e-4
        m = rs["airfoil_weight_kg"][i]
        rho = m / (a_root * i1)
        # the heaviest a blade of this root section and span could possibly
        # be is a constant-area one -- if the printed weight exceeds that,
        # the printed material cannot be right
        span = d[-1][0] - d[0][0]
        out.append(dict(stage=stage, printed_material=rs["material"][i],
                        metal_C=rs["metal_temperature_C"][i],
                        span_m=span, a_root_m2=a_root, mass_kg=m,
                        rho=rho, over_ti=rho / rho_ti, over_ni=rho / rho_ni,
                        nearer="titanium" if abs(rho - rho_ti) < abs(rho - rho_ni) else "nickel",
                        max_titanium_kg=rho_ti * a_root * span,
                        mass_over_max_titanium=m / (rho_ti * a_root * span),
                        sigma_calc=rho * om2 * i2 / KN_CM2,
                        sigma_printed=rs["centrifugal_stress_kN_cm2"][i]))
    for r in out:
        r["sigma_err_pct"] = (r["sigma_calc"] / r["sigma_printed"] - 1) * 100
    return out


def material_crossover():
    """where the measured density changes, against where Table X says it does"""
    rows = measured_blade_density()
    measured = [r["stage"] for r in rows if r["nearer"] == "nickel"]
    printed = [r["stage"] for r in rows if "Inco" in r["printed_material"]]
    disputed = sorted(set(measured) ^ set(printed))
    return dict(measured_nickel_from=min(measured), printed_nickel_from=min(printed),
                disputed_stages=disputed,
                impossible=[r["stage"] for r in rows
                            if "Ti" in r["printed_material"]
                            and r["mass_over_max_titanium"] > 1.0])


# --------------------------------------------- the Ti -> Ni design check

def titanium_temperature_check(ti_limit_C=500):
    """F1's fourth bullet: the Ti-fire limit and the Ti -> Ni switch as a
    design check, not a fact. Titanium is not used much above ~500 C -- it
    burns. Where does the E3's HPC metal temperature cross that, and is it
    where the material changes?"""
    rows = measured_blade_density()
    t = [r["metal_C"] for r in rows]
    printed_switch = min(r["stage"] for r in rows if "Inco" in r["printed_material"])
    measured_switch = min(r["stage"] for r in rows if r["nearer"] == "nickel")
    return dict(limit_C=ti_limit_C, metal_C=t,
                last_ti_stage_printed=printed_switch - 1,
                t_last_ti_printed=t[printed_switch - 2],
                t_first_ni_printed=t[printed_switch - 1],
                t_at_measured_switch=t[measured_switch - 1],
                printed_switch=printed_switch, measured_switch=measured_switch,
                printed_switch_is_at_the_limit=t[printed_switch - 2] < ti_limit_C <= t[printed_switch + 1])


# ---------------------------------------------------- the margin table

def stage_e_margins():
    """Every Stage E stress that has an allowable, and what the allowable
    would have to fall to before the margin is gone."""
    pub, hdbk = load()
    a = alloys()
    rs = pub["hpc"]["rotor_stages"]
    f = yaml.safe_load((DATA / "fan-design.yaml").read_text())
    l = yaml.safe_load((DATA / "lpt-design.yaml").read_text())
    h = yaml.safe_load((DATA / "hpt-mechanical.yaml").read_text())

    rows = []
    for i, stage in enumerate(rs["stage"]):
        ti = "Ti" in rs["material"][i]
        alloy = a["ti_8al_1mo_1v_forging"] if ti else a["inconel_718_bar_forging"]
        rows.append(dict(part=f"HPC rotor {stage} root, max",
                         stress_MPa=rs["max_root_stress_kN_cm2"][i] * 10,
                         metal_C=rs["metal_temperature_C"][i],
                         allowable_MPa=alloy["fty_MPa"],
                         basis="MIL-HDBK-5J Fty at ROOM temperature"))

    dp = f["fan_rotor_mechanical"]["dovetail_and_post"]
    rows.append(dict(part="fan blade dovetail corner",
                     stress_MPa=max(dp["blade"]["corner_stresses_kN_cm2"].values()) * 10,
                     metal_C=None, allowable_MPa=dp["blade"]["lcf_limit_kN_cm2"] * 10,
                     basis="CR-165148 Fig 48, LCF limit at 72,000 cycles"))
    rows.append(dict(part="fan disk post corner",
                     stress_MPa=max(dp["post"]["corner_stresses_kN_cm2"].values()) * 10,
                     metal_C=None, allowable_MPa=dp["post"]["lcf_limit_kN_cm2"] * 10,
                     basis="CR-165148 Fig 48, LCF limit at 72,000 cycles"))
    rows.append(dict(part="fan disk, max",
                     stress_MPa=f["rotor_structure"]["fan_disk"]["max_stress_kN_cm2"] * 10,
                     metal_C=None,
                     allowable_MPa=f["rotor_structure"]["fan_disk"]["max_stress_kN_cm2"] * 10
                     / (f["rotor_structure"]["fan_disk"]["max_stress_pct_of_lcf_limit"] / 100),
                     basis="CR-165148 Fig 59: the report prints the stress as 58 % of the LCF limit"))

    r = l["blade_retainers"]["stages_1_3"]
    for i, st in enumerate(r["stage"]):
        rows.append(dict(part=f"LPT blade retainer {st}", stress_MPa=r["sigma_max_MPa"][i],
                         metal_C=649, allowable_MPa=r["design_allowable_MPa"],
                         basis="LPT Fig 68: 0.2 % yield at 649 C -- an allowable AT temperature"))

    dm = h["rotor_components"]["stage1_disk"]["dovetail_max"]
    rows.append(dict(part="HPT stage-1 disk dovetail", stress_MPa=dm["stress_MPa"],
                     metal_C=None, allowable_MPa=dm["stress_MPa"],
                     basis="HPT Fig 62: 'on the limit exactly' at 36,000 LCF cycles"))

    for row in rows:
        row["margin"] = row["allowable_MPa"] / row["stress_MPa"]
        row["knockdown_to_fail"] = 1 / row["margin"]
    return rows


def f1_restated():
    """F1's closure, restated 2026-09-19 to what the published record holds.

    The plan's wording was *every stress in Stage E is compared with an
    allowable AT ITS METAL TEMPERATURE*. That cannot be met for the ten
    HPC blade roots, and the reason is sharper than the original gate:

      * MIL-HDBK-5J prints elevated-temperature strength as FIGURES, not
        tables -- Figure 5.3.2.1.1 for Ti-8Al-1Mo-1V and Figure 6.3.5.1.1
        for Inconel 718; and
      * the titanium figure is for SHEET, single-annealed, where the
        room-temperature allowable F1 uses is Table 5.3.2.0(c), BAR and
        forging. Digitising the sheet curve and applying it to a blade
        root would be an unsourced transfer between product forms, which
        is worse than not having the number (finding 274); and
      * the handbook has no Rene 77, 95, 150 or AF115 at all, so the
        superalloy parts were never in its scope.

    The restated closure: *every Stage E stress is compared with an
    allowable, each comparison NAMES whether the allowable is one an E3
    report prints for that part at its own condition or a handbook
    room-temperature value, and every room-temperature comparison carries
    the fraction of the allowable the metal may lose before the margin is
    gone.*

    That claims strictly less than the plan did and is fully evaluable.
    """
    rows = stage_e_margins()
    at_T = [r for r in rows if "AT temperature" in r["basis"]
            or "LCF limit" in r["basis"] or "on the limit" in r["basis"]]
    at_RT = [r for r in rows if "ROOM temperature" in r["basis"]]
    return dict(
        rows=len(rows),
        e3_printed_allowable=len(at_T),
        handbook_room_temperature_with_bound=len(at_RT),
        every_row_has_a_basis=all(r["basis"] for r in rows),
        every_room_row_has_a_bound=all(
            0.0 < r["knockdown_to_fail"] < 1.0 for r in at_RT),
        worst_margin=min(r["margin"] for r in rows),
        every_margin_at_least_unity=min(r["margin"] for r in rows) >= 1.0,
        worst_room_temperature_bound=1 - max(
            r["knockdown_to_fail"] for r in at_RT),
        superalloys_absent_from_the_handbook=[
            "Rene 77", "Rene 95", "Rene 150", "AF115"],
        elevated_temperature_is_a_figure=dict(
            ti_8_1_1="MIL-HDBK-5J Figure 5.3.2.1.1 -- and it is SHEET, "
                     "single-annealed, not the bar/forging the RT allowable "
                     "comes from",
            inco_718="MIL-HDBK-5J Figure 6.3.5.1.1"))


if __name__ == "__main__":
    print("1. The density of every HPC blade, MEASURED from Table X's own")
    print("   airfoil weight and root area and Table XXII's section shapes\n")
    a = alloys()
    print(f"   handbook densities: Ti-8-1-1 {a['ti_8al_1mo_1v_forging']['density']:.0f},"
          f"  Inco 718 {a['inconel_718_bar_forging']['density']:.0f} kg/m3\n")
    print(f"   {'st':>3}{'Table X says':>14}{'T metal':>9}{'m g':>8}{'rho':>8}"
          f"{'/Ti':>6}{'/Ni':>6}{'nearer':>10}{'m/max Ti':>10}"
          f"{'sig calc':>10}{'sig pub':>9}{'err %':>8}")
    for r in measured_blade_density():
        print(f"   {r['stage']:>3}{r['printed_material']:>14}{r['metal_C']:>9}"
              f"{r['mass_kg'] * 1000:>8.2f}{r['rho']:>8.0f}{r['over_ti']:>6.2f}"
              f"{r['over_ni']:>6.2f}{r['nearer']:>10}{r['mass_over_max_titanium']:>10.2f}"
              f"{r['sigma_calc']:>10.2f}{r['sigma_printed']:>9.1f}{r['sigma_err_pct']:>8.1f}")

    c = material_crossover()
    print(f"\n   measured switch to nickel at stage {c['measured_nickel_from']};"
          f" Table X prints it at stage {c['printed_nickel_from']}")
    print(f"   disputed stages: {c['disputed_stages']}")
    print(f"   stages whose printed weight EXCEEDS the heaviest possible titanium"
          f" blade of their own root section and span: {c['impossible']}")

    t = titanium_temperature_check()
    print(f"\n2. The Ti -> Ni switch as a design check (F1's fourth bullet)\n")
    print(f"   metal temperature by stage, C: {t['metal_C']}")
    print(f"   Table X's switch is stage {t['printed_switch']}: the last titanium stage"
          f" runs at {t['t_last_ti_printed']} C and the first nickel one at"
          f" {t['t_first_ni_printed']} C")
    print(f"   titanium's practical limit is about {t['limit_C']} C -- it burns")
    print(f"   the measured switch, stage {t['measured_switch']}, sits at"
          f" {t['t_at_measured_switch']} C, with no thermal reason to leave titanium")

    print(f"\n3. Stage E stresses against an allowable\n")
    print(f"   {'part':<28}{'stress':>9}{'T C':>6}{'allowable':>11}{'margin':>8}"
          f"{'may lose':>10}  basis")
    for r in stage_e_margins():
        tc = f"{r['metal_C']}" if r["metal_C"] is not None else "-"
        print(f"   {r['part']:<28}{r['stress_MPa']:>9.0f}{tc:>6}{r['allowable_MPa']:>11.0f}"
              f"{r['margin']:>8.2f}{(1 - r['knockdown_to_fail']) * 100:>9.0f} %  {r['basis'][:44]}")

    f = f1_restated()
    print(f"\n4. F1's closure as restated 2026-09-19")
    print(f"   {f['rows']} stresses compared: {f['e3_printed_allowable']} against an "
          f"allowable an E3 report prints for that part,")
    print(f"   {f['handbook_room_temperature_with_bound']} against a handbook room-temperature "
          f"allowable with the loss the margin can absorb stated")
    print(f"   every row names its basis: {f['every_row_has_a_basis']}")
    print(f"   every room-temperature row carries a bound: {f['every_room_row_has_a_bound']}")
    print(f"   worst margin {f['worst_margin']:.2f}; every margin >= 1: "
          f"{f['every_margin_at_least_unity']}")
    print(f"   the tightest room-temperature row could lose "
          f"{f['worst_room_temperature_bound'] * 100:.0f} % of its allowable and still hold")

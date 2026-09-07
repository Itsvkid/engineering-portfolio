"""Stage F2: mass — what the reconstruction weighs, and what the reports
weigh.

The work plan's F2 closure: *basic engine mass within **10 %** of 3,473 kg,
and no module more than 20 % off.*

**That closure is gated, and by the same A3 gaps Stage E hit.** Building
3,473 kg from geometry needs the disc profiles (un-digitised — E2's
finding 81), the casings and frames (figure-status), and the 320 kg of
sumps, drives and seals that Table XXVI itself calls out and that E4
could not touch because no bearing geometry is printed. Adding those up
from nothing would be inventing an engine, not reconstructing one.

What *can* be done is worth more than a total anyway, and it is two
different things:

  1. **Check the reconstruction against printed masses.** HPC report
     Table X prints a root area, a tip area, an airfoil weight and a whole
     blade weight for every one of the ten rotor stages. The C3 blading
     work built those sections from camber, stagger and thickness. Until
     now it had been checked on *angles* and *throats*; this is the first
     time its **area** meets a published number, twenty times over.
  2. **Check the published masses against each other.** Four separate
     reports print a module weight that CR-168219's Table XXVI also
     prints. Nobody has ever had to make those agree.

STEP0.md, unit F2."""
from __future__ import annotations

import yaml

from blading.sections import all_sections, section
from e3cycle.cycle import DATA
from mechanical.beam import closed_airfoil, polygon_properties
from mechanical.blade_frequency import _xxii_thickness

CM2 = 1e4                # m^2 -> cm^2


def _y(n):
    return yaml.safe_load((DATA / n).read_text())


def _hpc_rotor_sections():
    rows = {}
    for s in all_sections():
        if s.kind == "rotor":
            rows.setdefault(s.stage, []).append(s)
    return {k: sorted(v, key=lambda s: s.radius_m) for k, v in rows.items()}


def _polygon(sc):
    b = section(sc.chord_m, sc.beta1, sc.beta2, sc.stagger, *_xxii_thickness(sc))
    return polygon_properties(closed_airfoil(b))


# ------------------------------------- the reconstruction against Table X

def hpc_airfoil_areas():
    """Twenty printed areas -- root and tip of ten rotors -- against the
    sections C3 unit 12 built from camber, stagger and thickness alone."""
    rs = _y("e3-fps-published.yaml")["hpc"]["rotor_stages"]
    out = []
    for stage, secs in sorted(_hpc_rotor_sections().items()):
        i = rs["stage"].index(stage)
        for where, sc, printed in (("root", secs[0], rs["root_area_cm2"][i]),
                                   ("tip", secs[-1], rs["tip_area_cm2"][i])):
            a = _polygon(sc)["area"] * CM2
            out.append(dict(stage=stage, where=where, built_cm2=a, printed_cm2=printed,
                            err_pct=(a / printed - 1) * 100))
    return out


def hpc_airfoil_masses():
    """Integrate the built sections along the span and weigh them. The
    density is the handbook value for the material the F1 measurement
    identified -- which is Table X's own printed material at eight stages
    of ten, and not at stages 5 and 6 (finding 104)."""
    from materials.allowables import alloys, measured_blade_density
    a = alloys()
    rho = {"titanium": a["ti_8al_1mo_1v_forging"]["density"],
           "nickel": a["inconel_718_bar_forging"]["density"]}
    measured = {r["stage"]: r for r in measured_blade_density()}
    rs = _y("e3-fps-published.yaml")["hpc"]["rotor_stages"]
    out = []
    for stage, secs in sorted(_hpc_rotor_sections().items()):
        i = rs["stage"].index(stage)
        xs = [s.radius_m for s in secs]
        areas = [_polygon(s)["area"] for s in secs]
        vol = sum(0.5 * (a0 + a1) * (x1 - x0)
                  for (x0, a0), (x1, a1) in zip(zip(xs, areas), zip(xs[1:], areas[1:])))
        m = rho[measured[stage]["nearer"]] * vol
        printed, whole = rs["airfoil_weight_kg"][i], rs["blade_weight_kg"][i]
        out.append(dict(stage=stage, material=measured[stage]["nearer"],
                        built_kg=m, printed_airfoil_kg=printed, whole_blade_kg=whole,
                        err_pct=(m / printed - 1) * 100,
                        airfoil_fraction=printed / whole,
                        count=rs["blade_count"][i]))
    return out


def attachment_fraction():
    """How much of a blade is not airfoil, across the whole engine. The
    HPC prints both numbers for all ten stages; the fan and booster print
    a whole-blade weight that E4 compared with an integrated airfoil; the
    LPT prints a blade-set weight per stage and has real coordinates on
    stage 1."""
    from mechanical.blade_frequency import lpt_stage1
    from mechanical.rotordynamics import blade_masses
    import numpy as np
    out = [dict(row=f"HPC rotor {r['stage']}", airfoil_kg=r["printed_airfoil_kg"],
                blade_kg=r["whole_blade_kg"], fraction=r["airfoil_fraction"],
                basis="both printed, Table X")
           for r in hpc_airfoil_masses()]
    for b in blade_masses():
        out.append(dict(row=b["name"], airfoil_kg=b["airfoil_kg"], blade_kg=b["printed_kg"],
                        fraction=b["fraction"], basis="airfoil integrated, blade printed"))
    m = lpt_stage1()
    lw = _y("lpt-design.yaml")["weights"]["rotor"]
    counts = _y("lpt-design.yaml")["rotor_blades"]["blade_count"]
    per_blade = lw["blades_per_stage_kg"][0] / counts[0]
    x, a = np.asarray(m.x), np.asarray(m.area)
    airfoil = m.rho * float(np.trapezoid(a, x))
    out.append(dict(row="LPT stage 1", airfoil_kg=airfoil, blade_kg=per_blade,
                    fraction=airfoil / per_blade,
                    basis="airfoil from transcribed coordinates, blade printed"))
    return out


# --------------------------------- the published masses against each other

def module_audit():
    """Four reports, four module weights, and CR-168219's Table XXVI
    printing all four again. None of them was derived from another."""
    t26 = _y("e3-fps-published.yaml")["weights"]
    fan = _y("fan-design.yaml")["fps_weight"]
    lpt = _y("lpt-design.yaml")["weights"]
    hpt = _y("hpt-mechanical.yaml")["fps_weight"]
    rows = [
        dict(module="fan + booster rotor", component_report=fan["total_kg"],
             table_xxvi=t26["fan_and_booster_module"]["rotor"],
             src="CR-165148 Table VI vs CR-168219 Table XXVI"),
        dict(module="HPT rotor", component_report=hpt["hpt_rotor_kg"],
             table_xxvi=t26["core_module"]["hpt_rotor"],
             src="CR-167955 Table XXIII vs Table XXVI"),
        dict(module="HPT stator", component_report=hpt["hpt_stator_kg"],
             table_xxvi=t26["core_module"]["hpt_stator"],
             src="CR-167955 Table XXIII vs Table XXVI"),
        dict(module="LPT rotor", component_report=lpt["rotor"]["total_kg"],
             table_xxvi=t26["lpt_module"]["rotor"],
             src="CR-168289 Table XXI vs Table XXVI"),
        dict(module="LPT stator", component_report=lpt["stator"]["total_kg"],
             table_xxvi=t26["lpt_module"]["stator"],
             src="CR-168289 Table XXI vs Table XXVI"),
    ]
    for r in rows:
        r["err_pct"] = (r["component_report"] / r["table_xxvi"] - 1) * 100
    return rows


def blading_roll_up():
    """What fraction of each rotor module is blades. Everything here is
    printed; the point is what is left over, because the remainder is
    exactly what the un-digitised disc profiles would have to supply."""
    t26 = _y("e3-fps-published.yaml")["weights"]
    rs = _y("e3-fps-published.yaml")["hpc"]["rotor_stages"]
    fan = _y("fan-design.yaml")["fps_weight"]["items_kg"]
    lpt = _y("lpt-design.yaml")["weights"]["rotor"]
    hpc_blades = sum(n * w for n, w in zip(rs["blade_count"], rs["blade_weight_kg"]))
    rows = [
        dict(module="HPC rotor", blades_kg=hpc_blades,
             module_kg=t26["core_module"]["compressor_rotor"]),
        dict(module="LPT rotor", blades_kg=sum(lpt["blades_per_stage_kg"]),
             module_kg=t26["lpt_module"]["rotor"]),
        dict(module="fan + booster rotor", blades_kg=fan["fan_blades"] + fan["booster_blades"],
             module_kg=t26["fan_and_booster_module"]["rotor"]),
    ]
    for r in rows:
        r["pct"] = r["blades_kg"] / r["module_kg"] * 100
        r["remainder_kg"] = r["module_kg"] - r["blades_kg"]
    return rows


def what_is_gated():
    t26 = _y("e3-fps-published.yaml")["weights"]
    return dict(basic_engine=t26["basic_engine_total"],
                sumps_drives_seals=t26["miscellaneous"]["sumps_drives_seals"],
                combustor_casing_diffuser=t26["core_module"]["combustor_casing_diffuser"],
                sumps_pct=t26["miscellaneous"]["sumps_drives_seals"]
                / t26["basic_engine_total"] * 100)


if __name__ == "__main__":
    areas = hpc_airfoil_areas()
    print("1. Twenty printed airfoil areas against the sections C3 built\n")
    print(f"   {'st':>3}{'root built':>12}{'root X':>9}{'err %':>8}"
          f"{'tip built':>12}{'tip X':>8}{'err %':>8}")
    for stage in sorted({a["stage"] for a in areas}):
        r = next(a for a in areas if a["stage"] == stage and a["where"] == "root")
        t = next(a for a in areas if a["stage"] == stage and a["where"] == "tip")
        print(f"   {stage:>3}{r['built_cm2']:>12.3f}{r['printed_cm2']:>9.3f}{r['err_pct']:>8.1f}"
              f"{t['built_cm2']:>12.3f}{t['printed_cm2']:>8.3f}{t['err_pct']:>8.1f}")
    e = [a["err_pct"] for a in areas]
    print(f"\n   twenty comparisons: mean {sum(e) / len(e):+.1f} %, "
          f"worst {min(e):+.1f} %, and {sum(1 for x in e if x < 0)} of 20 are negative")

    print(f"\n2. And what those sections weigh\n")
    print(f"   {'st':>3}{'material':>10}{'built g':>10}{'printed g':>11}{'err %':>8}"
          f"{'whole blade g':>15}{'airfoil %':>11}")
    for r in hpc_airfoil_masses():
        print(f"   {r['stage']:>3}{r['material']:>10}{r['built_kg'] * 1000:>10.2f}"
              f"{r['printed_airfoil_kg'] * 1000:>11.2f}{r['err_pct']:>8.1f}"
              f"{r['whole_blade_kg'] * 1000:>15.2f}{r['airfoil_fraction'] * 100:>11.0f}")

    print(f"\n3. How much of a blade is airfoil, across the engine\n")
    print(f"   {'row':<16}{'airfoil kg':>12}{'blade kg':>11}{'airfoil %':>11}  basis")
    for r in attachment_fraction():
        print(f"   {r['row']:<16}{r['airfoil_kg']:>12.4f}{r['blade_kg']:>11.4f}"
              f"{r['fraction'] * 100:>11.0f}  {r['basis']}")

    print(f"\n4. Five module weights, printed twice in two different reports\n")
    print(f"   {'module':<22}{'component report':>18}{'Table XXVI':>12}{'err %':>8}  source")
    for r in module_audit():
        print(f"   {r['module']:<22}{r['component_report']:>18.1f}{r['table_xxvi']:>12}"
              f"{r['err_pct']:>+8.1f}  {r['src']}")

    print(f"\n5. What fraction of a rotor module is blades\n")
    print(f"   {'module':<22}{'blades kg':>11}{'module kg':>11}{'blades %':>10}{'rest kg':>9}")
    for r in blading_roll_up():
        print(f"   {r['module']:<22}{r['blades_kg']:>11.1f}{r['module_kg']:>11}"
              f"{r['pct']:>10.0f}{r['remainder_kg']:>9.1f}")

    g = what_is_gated()
    print(f"\n6. Why F2's stated closure is gated")
    print(f"   basic engine {g['basic_engine']} kg. Sumps, drives and seals alone are"
          f" {g['sumps_drives_seals']} kg -- {g['sumps_pct']:.1f} % of it, and more than")
    print(f"   twice the combustor, casing and diffuser at"
          f" {g['combustor_casing_diffuser']} kg. No bearing or sump geometry is")
    print(f"   printed anywhere (E4's gate), and the disc profiles are un-digitised")
    print(f"   (E2's finding 81). A total built without them would be invention.")

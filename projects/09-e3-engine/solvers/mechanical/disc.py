"""Stage E2: the rotating disc — the bore doubling, the rim load, and what
the three published stress times say about which loads actually set the
bore.

The work plan's E2 closure has two halves: *HPT disc peak effective stress
within 10 % of Fig 64, and **the bore doubling for a small hole** is
demonstrated on the model.*

The second half is pure mechanics and is demonstrated here in closed form.
The first half is **not attempted, and that is stated rather than
skipped**: it needs the disc profile, and DATA-INDEX records the disc
cross-sections as "cross-sections only; digitise" — Stage A never
transcribed them, and Fig 64 itself is figure-status. What Stage A *did*
transcribe is Fig 55's effective stress at nineteen rotor locations at
three flight times, Fig 54's metal temperature at seventeen, Fig 53's
speed at each time, and the blade dovetail load. Those are enough to ask a
sharper question than the peak value: **which load sets the bore?**

Elastic solution for a rotating annular disc of constant thickness, inner
radius a, outer radius b, free at both surfaces (Timoshenko, *Theory of
Elasticity*, art. 32):

    sigma_theta(r) = (3+nu)/8 rho omega^2 [ b^2 + a^2 + a^2 b^2 / r^2
                                            - (1+3nu)/(3+nu) r^2 ]

At r = a this is (3+nu)/4 rho omega^2 [b^2 + (1-nu)/(3+nu) a^2], which as
a -> 0 tends to (3+nu)/4 rho omega^2 b^2 — exactly **twice** the centre
stress of a solid disc, (3+nu)/8 rho omega^2 b^2. A vanishingly small
hole does not weaken the disc by a vanishingly small amount; it doubles
the stress where it sits.

Adding the blade pull: a rim radial stress S at r = b, with the bore free,
is the Lame field sigma_theta = A + B/r^2, sigma_r = A - B/r^2 with
sigma_r(a) = 0 and sigma_r(b) = S, so at the bore sigma_theta doubles
again: 2 S b^2 / (b^2 - a^2).

STEP0.md, unit E2."""
from __future__ import annotations

import math
from dataclasses import dataclass

import yaml

from e3cycle.cycle import DATA

NU = 0.29                      # Poisson's ratio, wrought nickel superalloy
RHO_RENE95 = 8210.0            # kg/m^3, PM nickel -- handbook, not from the E3 reports
MPA = 1.0e6

# Rene 95 at 500 C, for the physical check on the fitted thermal constant.
# Handbook ranges, deliberately kept as ranges: alpha 13-15e-6 /K, E 190-205 GPa.
ALPHA_E_MPA_PER_K = (13.0e-6 * 190.0e3, 15.0e-6 * 205.0e3)   # 2.47 .. 3.08 MPa/K


def _hpt_mech():
    return yaml.safe_load((DATA / "hpt-mechanical.yaml").read_text())


def _published():
    return yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())


# ---------------------------------------------------------------- mechanics

def hoop_stress_annular(r, a, b, rho, omega, nu=NU):
    """tangential stress in a rotating annular disc of constant thickness"""
    return (3 + nu) / 8 * rho * omega ** 2 * (
        b ** 2 + a ** 2 + (a ** 2 * b ** 2) / r ** 2 - (1 + 3 * nu) / (3 + nu) * r ** 2)


def hoop_stress_solid(r, b, rho, omega, nu=NU):
    """tangential stress in a rotating SOLID disc"""
    return (3 + nu) / 8 * rho * omega ** 2 * (b ** 2 - (1 + 3 * nu) / (3 + nu) * r ** 2)


def bore_concentration(a_over_b, nu=NU):
    """bore stress of an annular disc over the centre stress of a solid one
    of the same outer radius -- the classic factor of 2 as the hole shrinks"""
    a = a_over_b
    bore = (3 + nu) / 4 * (1 + (1 - nu) / (3 + nu) * a ** 2)
    centre = (3 + nu) / 8
    return bore / centre


def rim_load_hoop(rim_stress_MPa, a_over_b):
    """bore hoop stress from a radial rim stress S -- the Lame field"""
    return 2 * rim_stress_MPa / (1 - a_over_b ** 2)


# ------------------------------------------------------------- the E3 disc

def rim_load():
    """the blade pull the stage-1 disc carries, entirely from published data"""
    hpt_m, pub = _hpt_mech(), _published()
    dt = hpt_m["stage1_blade"]["dovetail"]
    n = pub["hpt"]["stage_aerodynamics"]["blade_count"][0]
    total_kN = n * dt["load_per_blade_kN"]
    return dict(blades=n, load_per_blade_kN=dt["load_per_blade_kN"],
                total_kN=total_kN, tonnes=total_kN * 1e3 / 9.80665 / 1e3,
                rpm=dt["condition"]["rpm"])


def stage1_radii():
    """blade tip and hub radius at the dovetail's own speed, from Table III's
    tip speed and radius ratio -- nothing assumed"""
    pub, r = _published(), rim_load()
    sa = pub["hpt"]["stage_aerodynamics"]
    omega = r["rpm"] * 2 * math.pi / 60
    r_tip = sa["tip_speed_takeoff_m_s"][0] / omega
    return r_tip, sa["radius_ratio_Dh_Dt"][0] * r_tip, omega


def bounding_estimates(a_over_b=0.15):
    """what a CONSTANT-THICKNESS disc of the same outer radius would carry,
    solid and with a bore. The real disc must lie between: it is thick at
    the bore and thin at the rim, which is the whole purpose of a profile."""
    _, b_m, omega = stage1_radii()
    a = a_over_b * b_m
    return dict(b_m=b_m, omega=omega, a_over_b=a_over_b,
                solid_MPa=hoop_stress_solid(0.0, b_m, RHO_RENE95, omega) / MPA,
                annular_MPa=hoop_stress_annular(a, a, b_m, RHO_RENE95, omega) / MPA)


# --------------------------------------------- which load sets the bore?

def speeds():
    """Fig 53's rotor speed at each of Fig 55's three limiting times"""
    fig53 = _hpt_mech()["rotor_analysis_conditions"]["fig53_transient"]["rpm"]
    return [fig53["max_takeoff"], fig53["end_of_climb"], fig53["max_cruise"]]


def centrifugal_screen():
    """A stress that is purely centrifugal must scale as N^2 between the
    three times, because nothing else in it changes. Normalise each
    location on its 40 s value and see which locations obey."""
    es = _hpt_mech()["rotor_effective_stress"]
    n = speeds()
    scale = [(ni / n[0]) ** 2 for ni in n]
    rows = []
    for name, s in es["locations_MPa"].items():
        pred = [s[0] * f for f in scale]
        err = [(s[i] - pred[i]) / pred[i] * 100 for i in range(3)]
        rows.append(dict(location=name, published=s, predicted=pred, err_pct=err,
                         worst_pct=max(abs(e) for e in err)))
    return rows, n, scale


def two_term_stage2():
    """The stage-2 disc is the only one with BOTH a bore and a rim metal
    temperature transcribed. Fit sigma = c*(N/N40)^2 + k*(T_rim - T_bore)
    to its three published bore stresses. Two constants against three
    numbers, so it is overdetermined and can fail; and k has an
    independent physical meaning -- for a disc with a radial gradient the
    bore hoop stress is alpha*E*(T_mean - T_bore), so k must land at a
    fraction of alpha*E, which for Rene 95 is 2.5-3.1 MPa/K."""
    m = _hpt_mech()
    t = m["rotor_temperatures"]["locations_C"]
    sigma = m["rotor_effective_stress"]["locations_MPa"]["stage2_disk_bore"]
    n = speeds()
    x = [(ni / n[0]) ** 2 for ni in n]
    dt = [t["stage2_disk_rim_aft"][i] - t["stage2_disk_bore"][i] for i in range(3)]

    sxx = sum(v * v for v in x); sxy = sum(x[i] * dt[i] for i in range(3))
    syy = sum(v * v for v in dt); sxs = sum(x[i] * sigma[i] for i in range(3))
    sys_ = sum(dt[i] * sigma[i] for i in range(3))
    det = sxx * syy - sxy * sxy
    c = (sxs * syy - sys_ * sxy) / det
    k = (sxx * sys_ - sxy * sxs) / det
    fit = [c * x[i] + k * dt[i] for i in range(3)]

    # and the honest test: hold one time out, fit the other two exactly,
    # predict the third. Three ways round. If the split between centrifugal
    # and thermal is real, c and k should barely move.
    held = []
    for out in range(3):
        i, j = [m for m in range(3) if m != out]
        d = x[i] * dt[j] - x[j] * dt[i]
        ci = (sigma[i] * dt[j] - sigma[j] * dt[i]) / d
        ki = (x[i] * sigma[j] - x[j] * sigma[i]) / d
        pred = ci * x[out] + ki * dt[out]
        held.append(dict(held_out=out, c_MPa=ci, k_MPa_per_K=ki, predicted=pred,
                         published=sigma[out],
                         err_pct=(pred - sigma[out]) / sigma[out] * 100))

    return dict(c_MPa=c, k_MPa_per_K=k, x=x, delta_T=dt, published=sigma, fit=fit,
                err_pct=[(fit[i] - sigma[i]) / sigma[i] * 100 for i in range(3)],
                alpha_E_range=ALPHA_E_MPA_PER_K, leave_one_out=held)


def rim_load_contribution(rim_widths_cm=(2.0, 3.0, 5.0, 8.0), a_over_b=0.15):
    """How much of the bore stress is the blades pulling? The rim radial
    stress is S = F / (2 pi b t) and the bore hoop it produces is
    2 S b^2/(b^2 - a^2). The rim axial width t is NOT published -- the disc
    cross-sections were never transcribed -- so this is given as a table
    over plausible widths, not as one number."""
    r = rim_load()
    _, b_m, _ = stage1_radii()
    out = []
    for t_cm in rim_widths_cm:
        S = r["total_kN"] * 1e3 / (2 * math.pi * b_m * t_cm / 100) / MPA
        out.append(dict(rim_width_cm=t_cm, rim_radial_MPa=S,
                        bore_hoop_MPa=rim_load_hoop(S, a_over_b)))
    return out


@dataclass
class DiscBound:
    label: str
    stress_MPa: float


if __name__ == "__main__":
    print("1. The bore doubling for a small hole (E2's stated closure)\n")
    print(f"{'a/b':>8}{'bore / solid-centre stress':>30}")
    for ab in (0.30, 0.20, 0.10, 0.05, 0.02, 0.01, 0.001):
        print(f"{ab:>8.3f}{bore_concentration(ab):>30.4f}")
    print(f"   limit as a/b -> 0 : {bore_concentration(0.0):.4f}   (exactly 2)")

    r = rim_load()
    r_tip, b_m, omega = stage1_radii()
    print(f"\n2. The stage-1 disc's rim load")
    print(f"   {r['blades']} blades x {r['load_per_blade_kN']:.3f} kN = "
          f"{r['total_kN']:.0f} kN at {r['rpm']} rpm")
    print(f"   that is {r['tonnes']:.0f} tonnes of blade pull on one disc")
    print(f"   blade tip {r_tip * 100:.1f} cm, root {b_m * 100:.1f} cm "
          f"(Table III tip speed and Dh/Dt at that speed)")

    bd = bounding_estimates()
    es = _hpt_mech()["rotor_effective_stress"]
    print(f"\n3. Where the published bore stress sits, against a constant-thickness disc")
    print(f"   {'solid disc, centre':<40}{bd['solid_MPa']:>8.0f} MPa")
    print(f"   {'annular disc, bore at a/b = 0.15':<40}{bd['annular_MPa']:>8.0f} MPa")
    for key in ("stage1_disk_bore", "stage2_disk_bore"):
        v = es["locations_MPa"][key]
        print(f"   {'published ' + key + ' (Fig 55)':<40}"
              f"{'/'.join(str(x) for x in v):>8} MPa  at 40/875/1700 s")

    rows, n, scale = centrifugal_screen()
    print(f"\n4. Which locations are purely centrifugal?")
    print(f"   speeds {n[0]}/{n[1]}/{n[2]} rpm  ->  N^2 scale "
          f"{scale[0]:.3f}/{scale[1]:.3f}/{scale[2]:.3f} (Fig 53)")
    print(f"\n   {'location':<36}{'published':>18}{'N^2 pred':>18}{'worst %':>9}")
    for row in sorted(rows, key=lambda d: d["worst_pct"]):
        p = '/'.join(f"{v:.0f}" for v in row["published"])
        q = '/'.join(f"{v:.0f}" for v in row["predicted"])
        print(f"   {row['location']:<36}{p:>18}{q:>18}{row['worst_pct']:>9.1f}")

    tt = two_term_stage2()
    print(f"\n5. The stage-2 disc bore: centrifugal + thermal, two constants, three numbers")
    print(f"   T_rim - T_bore = {tt['delta_T'][0]:+.0f} / {tt['delta_T'][1]:+.0f} /"
          f" {tt['delta_T'][2]:+.0f} C   (Fig 54)")
    print(f"   published      = {'/'.join(f'{v:.0f}' for v in tt['published'])} MPa")
    print(f"   two-term fit   = {'/'.join(f'{v:.0f}' for v in tt['fit'])} MPa"
          f"   ({', '.join(f'{e:+.1f}%' for e in tt['err_pct'])})")
    print(f"   centrifugal at 40 s      c = {tt['c_MPa']:.0f} MPa")
    print(f"   thermal constant         k = {tt['k_MPa_per_K']:.2f} MPa/K")
    print(f"   alpha*E for Rene 95        = {tt['alpha_E_range'][0]:.2f} to "
          f"{tt['alpha_E_range'][1]:.2f} MPa/K  -> k/alpha*E = "
          f"{tt['k_MPa_per_K'] / tt['alpha_E_range'][1]:.2f} to "
          f"{tt['k_MPa_per_K'] / tt['alpha_E_range'][0]:.2f}")
    print(f"\n   hold one time out, fit the other two exactly, predict the third:")
    names = ["40 s", "875 s", "1700 s"]
    print(f"   {'held out':>10}{'c MPa':>10}{'k MPa/K':>10}{'predicted':>11}"
          f"{'published':>11}{'err %':>8}")
    for h in tt["leave_one_out"]:
        print(f"   {names[h['held_out']]:>10}{h['c_MPa']:>10.0f}{h['k_MPa_per_K']:>10.2f}"
              f"{h['predicted']:>11.0f}{h['published']:>11.0f}{h['err_pct']:>8.1f}")

    print(f"\n6. How much of the bore stress is the blades pulling?")
    print(f"   the rim axial width is not published; the table is over plausible widths")
    print(f"   {'rim width cm':>14}{'rim radial MPa':>17}{'bore hoop MPa':>16}")
    for row in rim_load_contribution():
        print(f"   {row['rim_width_cm']:>14.1f}{row['rim_radial_MPa']:>17.0f}"
              f"{row['bore_hoop_MPa']:>16.0f}")

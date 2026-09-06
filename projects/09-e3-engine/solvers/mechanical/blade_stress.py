"""Stage E1: centrifugal stress at every HPC blade root, from the section
geometry alone.

The work plan's E1 closure: *Table X centrifugal stresses reproduced
within 10 % all ten stages.*

A rotating blade's root stress is

    sigma_root = (rho omega^2 / A_root) * integral_root^tip A(r) r dr

Everything on the right except the density comes from what Stage A
transcribed. Table XXII gives the chord and the maximum thickness ratio at
twelve sections of every rotor, so the area distribution follows as
A(r) proportional to c(r)^2 (t/c)(r) — and only the RATIO A(r)/A_root
matters, so the airfoil shape constant cancels.

Speed: Table X's own footnote says the stress case is the deteriorated
engine at 13,948 rpm, not the 12,303 aero design point. That is a factor
of 1.29 in stress and is easy to get wrong. STEP0.md, unit E1."""
from __future__ import annotations

import math
from dataclasses import dataclass

import yaml

from e3cycle.cycle import DATA

CM = 0.01
KN_CM2 = 1.0e7          # 1 kN/cm^2 in Pa

# Densities, kg/m^3. The HPC rotor is "inertia-welded forward and aft
# sections" (CR-168219): GE practice puts titanium forward and a nickel
# alloy aft. Both are carried and the crossover is an OUTPUT, not an input.
RHO_TITANIUM = 4430.0
RHO_NICKEL = 8190.0


@dataclass
class StageStress:
    stage: int
    r_root_m: float
    r_tip_m: float
    area_integral: float          # integral A(r)/A_root * r dr, metres
    sigma_titanium_kN_cm2: float
    sigma_nickel_kN_cm2: float
    printed_kN_cm2: float
    taper_factor: float


def load():
    pub = yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())
    xxii = yaml.safe_load((DATA / "hpc-blade-sections.yaml").read_text())
    return pub, xxii


def stress_speed_rpm():
    """Table X's footnote: the stress case is the deteriorated engine"""
    pub, _ = load()
    return pub["hpc"]["spool_speed_rpm"]["nc_deteriorated_engine"]


def area_distribution(stage):
    """A(r)/A_root at the twelve printed sections, from chord and t/c"""
    _, xxii = load()
    cols = xxii["columns"]
    blk = next(b for b in xxii["rotors"] if b["stage"] == stage)
    rows = [dict(zip(cols, s)) for s in blk["sections"]]
    rows.sort(key=lambda r: r["sect_ht_cm"])           # root first
    root = rows[0]
    a_root = root["chord_cm"] ** 2 * root["tm_c"]
    return [(r["sect_ht_cm"] * CM, r["chord_cm"] ** 2 * r["tm_c"] / a_root) for r in rows]


def root_stress(stage, rho, rpm=None):
    rpm = rpm if rpm is not None else stress_speed_rpm()
    omega = rpm * 2 * math.pi / 60
    dist = area_distribution(stage)
    integral = 0.0
    for (r0, a0), (r1, a1) in zip(dist, dist[1:]):
        integral += 0.5 * (a0 * r0 + a1 * r1) * (r1 - r0)
    return rho * omega ** 2 * integral, integral, dist[0][0], dist[-1][0]


def all_stages():
    pub, _ = load()
    rs = pub["hpc"]["rotor_stages"]
    printed = rs["centrifugal_stress_kN_cm2"]
    out = []
    for i, stage in enumerate(rs["stage"]):
        s_ti, integral, r_root, r_tip = root_stress(stage, RHO_TITANIUM)
        s_ni, *_ = root_stress(stage, RHO_NICKEL)
        # a constant-area blade of the same span, for the taper factor
        omega = stress_speed_rpm() * 2 * math.pi / 60
        const = RHO_TITANIUM * omega ** 2 * (r_tip ** 2 - r_root ** 2) / 2
        out.append(StageStress(stage, r_root, r_tip, integral,
                               s_ti / KN_CM2, s_ni / KN_CM2, printed[i],
                               s_ti / const if const else 0.0))
    return out


if __name__ == "__main__":
    rpm = stress_speed_rpm()
    rows = all_stages()
    print(f"HPC blade root centrifugal stress at the Table X stress case: {rpm} rpm")
    print("(Table X's footnote: Nc deteriorated, the max-pressure/max-temperature case)")
    print(f"\n{'stage':>6}{'r_root':>9}{'r_tip':>8}{'taper':>8}{'Ti kN/cm2':>12}{'Ni kN/cm2':>12}"
          f"{'printed':>10}{'Ti diff %':>11}{'Ni diff %':>11}")
    for r in rows:
        dti = (r.sigma_titanium_kN_cm2 / r.printed_kN_cm2 - 1) * 100
        dni = (r.sigma_nickel_kN_cm2 / r.printed_kN_cm2 - 1) * 100
        print(f"{r.stage:>6}{r.r_root_m * 100:>9.2f}{r.r_tip_m * 100:>8.2f}{r.taper_factor:>8.3f}"
              f"{r.sigma_titanium_kN_cm2:>12.2f}{r.sigma_nickel_kN_cm2:>12.2f}"
              f"{r.printed_kN_cm2:>10.1f}{dti:>11.1f}{dni:>11.1f}")
    ti_ok = [r.stage for r in rows if abs(r.sigma_titanium_kN_cm2 / r.printed_kN_cm2 - 1) < 0.10]
    ni_ok = [r.stage for r in rows if abs(r.sigma_nickel_kN_cm2 / r.printed_kN_cm2 - 1) < 0.10]
    print(f"\nwithin 10 % on titanium: stages {ti_ok}")
    print(f"within 10 % on nickel:   stages {ni_ok}")

"""C1 unit 6: the fan and quarter-stage booster, mean-line.

The fan report prints a specific flow, a corrected tip speed and the
leading-edge Mach number at three radii. Those are three independent
things: the first two fix the velocity triangle, and the third is the
answer. STEP0.md, unit 6."""
from __future__ import annotations

import math
from dataclasses import dataclass

import yaml

from e3cycle import gas
from e3cycle.cycle import DATA

T_STD, P_STD = 288.15, 101325.0


def load():
    fan = yaml.safe_load((DATA / "fan-design.yaml").read_text())
    pub = yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())
    return fan, pub


def axial_mach_from_specific_flow(w_over_a, t0=T_STD, p0=P_STD):
    """the axial Mach number a corrected specific flow W sqrt(theta)/(delta A)
    implies, real gas, no swirl"""
    lo, hi = 0.05, 1.0
    for _ in range(90):
        m = 0.5 * (lo + hi)
        cp = gas.cp(t0 * 0.9)
        ts = t0
        for _ in range(20):
            cpv = gas.cp(ts)
            g = cpv / (cpv - gas.R_AIR)
            ts = t0 / (1 + 0.5 * (g - 1) * m * m)
        ps = p0 * math.exp(-(gas.phi(t0) - gas.phi(ts)) / gas.R_AIR)
        cpv = gas.cp(ts)
        g = cpv / (cpv - gas.R_AIR)
        v = m * math.sqrt(g * gas.R_AIR * ts)
        flux = ps / (gas.R_AIR * ts) * v
        lo, hi = (m, hi) if flux < w_over_a else (lo, m)
    return 0.5 * (lo + hi)


def _sound_and_static(mach, t0=T_STD):
    ts = t0
    for _ in range(30):
        cp = gas.cp(ts)
        g = cp / (cp - gas.R_AIR)
        ts = t0 / (1 + 0.5 * (g - 1) * mach * mach)
    cp = gas.cp(ts)
    g = cp / (cp - gas.R_AIR)
    return math.sqrt(g * gas.R_AIR * ts), ts


@dataclass
class Section:
    name: str
    radius_m: float
    u: float
    m_axial: float
    m_rel: float
    m_rel_printed: float | None


def fan_rotor_sections():
    """relative Mach at the fan rotor leading edge, at the three radii the
    report quotes, from the specific flow and the corrected tip speed"""
    fan, _ = load()
    s = fan["summary"]
    a = fan["aero_parameters"]
    r_tip = s["fan_tip_diameter_m"] / 2
    r_hub = r_tip * s["inlet_radius_ratio"]
    u_tip = s["corrected_tip_speed_m_s"]
    m_ax = axial_mach_from_specific_flow(s["specific_flow_kg_s_m2"])
    a_snd, ts = _sound_and_static(m_ax)
    airfoil = fan["fan_rotor_airfoil"]
    shroud_pct = airfoil["shroud"]["height_pct"] / 100
    out = []
    for name, r, printed in (("tip", r_tip, airfoil["tip_section"]["m_le"]),
                             ("shroud (55 % height)", r_hub + shroud_pct * (r_tip - r_hub), airfoil["shroud_section"]["m_le"]),
                             ("hub", r_hub, airfoil["hub_section"]["m_le"])):
        u = u_tip * r / r_tip
        out.append(Section(name, r, u, m_ax, math.hypot(m_ax, u / a_snd), printed))
    return out, dict(m_axial=m_ax, sound=a_snd, static_T=ts, r_tip=r_tip, r_hub=r_hub, u_tip=u_tip,
                     annulus_m2=math.pi * (r_tip ** 2 - r_hub ** 2),
                     specific_flow=s["specific_flow_kg_s_m2"], corrected_flow=a["airflow_kg_s"][0])


def row_efficiencies():
    """each CAFD row's adiabatic efficiency recomputed from its cumulative
    pressure and temperature ratios, real gas"""
    fan, _ = load()
    rows = fan["vector_diagram_rows"]["rows"]
    out = []
    for name, r in rows.items():
        pr, tr = r["pressure_ratio"], r["temperature_ratio"]
        t2 = T_STD * tr
        t2s = gas.t_from_phi(gas.phi(T_STD) + gas.R_AIR * math.log(pr), guess=t2)
        eta = (gas.h(t2s) - gas.h(T_STD)) / (gas.h(t2) - gas.h(T_STD))
        out.append(dict(row=name, pr=pr, tr=tr, eta=eta, eta_printed=r["adiabatic_efficiency"]))
    return out


def stage_coefficients():
    """loading and flow coefficient for the fan and the booster at pitch"""
    fan, _ = load()
    a = fan["aero_parameters"]
    v = fan["vector_diagram_rows"]
    _, g = fan_rotor_sections()
    out = []
    for i, name in enumerate(("fan stage 1", "booster stage")):
        r_tip = a["tip_diameter_cm"][i] / 200
        r_hub = r_tip * a["radius_ratio_inlet"][i]
        r_pitch = 0.5 * (r_tip + r_hub)
        u_tip = a["tip_speed_m_s"][i]
        u_pitch = u_tip * r_pitch / r_tip
        dh = gas.h(T_STD * a["temperature_ratio"][i]) - gas.h(T_STD)
        cx = g["m_axial"] * g["sound"]
        out.append(dict(row=name, r_pitch=r_pitch, u_tip=u_tip, u_pitch=u_pitch,
                        psi=dh / (u_pitch ** 2), phi=cx / u_pitch, dh=dh,
                        rpm_from_tip_speed=u_tip / r_tip * 60 / (2 * math.pi)))
    return out, v["corrected_speed_rpm"]


def island_split():
    fan, _ = load()
    f = fan["flowpath"]
    s = fan["summary"]
    total = f["corrected_flow_kg_s"]
    under = fan["vector_diagram_rows"]["rows"]["S1_island"]["inlet_corr_flow_kg_s"]
    back = fan["vector_diagram_rows"]["rows"]["S2OUT_island_exit"]["inlet_corr_flow_kg_s"]
    core = fan["vector_diagram_rows"]["rows"]["S2IN_inner_ogv"]["inlet_corr_flow_kg_s"]
    over = fan["vector_diagram_rows"]["rows"]["OGV_bypass"]["inlet_corr_flow_kg_s"]
    a = fan["aero_parameters"]["airflow_kg_s"][0]
    return dict(total_fig=total, total_table=a, under=under, back=back, core=core, over=over,
                split_pct=under / a * 100, split_printed=s["island_split_pct_of_total_flow"],
                return_pct=back / under * 100, return_printed=s["booster_flow_returning_to_bypass_pct"],
                closure=under - back - core, over_closure=a - under - over,
                bpr=(a - core) / core, bpr_printed=s["bypass_ratio"])


if __name__ == "__main__":
    secs, g = fan_rotor_sections()
    print(f"fan inlet: specific flow {g['specific_flow']} kg/s.m2 over a {g['annulus_m2']:.4f} m2 annulus"
          f" (r {g['r_hub'] * 100:.1f}-{g['r_tip'] * 100:.1f} cm) gives axial Mach {g['m_axial']:.3f},"
          f" static {g['static_T']:.1f} K, a {g['sound']:.1f} m/s")
    print(f"corrected tip speed {g['u_tip']} m/s\n")
    print(f"{'section':<22}{'r cm':>8}{'U m/s':>8}{'M_ax':>7}{'M_rel':>8}{'printed':>9}{'diff':>7}")
    for s in secs:
        print(f"{s.name:<22}{s.radius_m * 100:>8.1f}{s.u:>8.1f}{s.m_axial:>7.3f}{s.m_rel:>8.3f}"
              f"{s.m_rel_printed:>9.2f}{s.m_rel - s.m_rel_printed:>7.3f}")
    print(f"\n{'row':<20}{'PR':>8}{'TR':>8}{'eta':>8}{'printed':>9}{'diff':>8}")
    for r in row_efficiencies():
        print(f"{r['row']:<20}{r['pr']:>8.4f}{r['tr']:>8.4f}{r['eta']:>8.4f}{r['eta_printed']:>9.3f}{r['eta'] - r['eta_printed']:>8.4f}")
    coeffs, rpm = stage_coefficients()
    print(f"\n{'stage':<15}{'r_p cm':>9}{'U_tip':>8}{'U_p':>8}{'psi':>7}{'phi':>7}{'dh kJ/kg':>10}{'rpm from U_tip':>16}")
    for c in coeffs:
        print(f"{c['row']:<15}{c['r_pitch'] * 100:>9.2f}{c['u_tip']:>8.1f}{c['u_pitch']:>8.1f}{c['psi']:>7.3f}{c['phi']:>7.3f}"
              f"{c['dh'] / 1000:>10.1f}{c['rpm_from_tip_speed']:>16.1f}")
    print(f"printed corrected speed {rpm} rpm")
    i = island_split()
    print(f"\nisland: {i['under']:.2f} kg/s under ({i['split_pct']:.1f} %, printed {i['split_printed']}),"
          f" {i['back']:.2f} back to bypass ({i['return_pct']:.1f} %, printed {i['return_printed']}),"
          f" {i['core']:.2f} to core, {i['over']:.2f} over")
    print(f"closure: under - back - core = {i['closure']:+.3f} kg/s; total - under - over = {i['over_closure']:+.3f} kg/s")
    print(f"bypass ratio (total - core)/core = {i['bpr']:.3f}, printed {i['bpr_printed']}")

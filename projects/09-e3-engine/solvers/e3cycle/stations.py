"""B4: station properties and the annulus by continuity at the max-climb
design point, checked against every dimensioned annulus the reports give
and against the turbine cycle-match tables. STEP0.md, B4 section."""
from __future__ import annotations

import csv
import math
import pathlib
from dataclasses import dataclass

import yaml

from . import gas
from .cycle import DATA, load_inputs, solve_rating

BTU_PER_LB = 2326.0    # J/kg


def static_state(tt, pt, mach, far=0.0):
    """static T, p, density and velocity at a Mach number, real gas"""
    def resid(ts):
        cp = gas.cp(ts, far)
        g = cp / (cp - gas.R_AIR)
        return 2.0 * (gas.h(tt, far) - gas.h(ts, far)) - mach ** 2 * g * gas.R_AIR * ts
    lo, hi = 0.5 * tt, tt
    for _ in range(80):
        ts = 0.5 * (lo + hi)
        lo, hi = (ts, hi) if resid(ts) > 0 else (lo, ts)
    ts = 0.5 * (lo + hi)
    ps = pt * math.exp(-(gas.phi(tt, far) - gas.phi(ts, far)) / gas.R_AIR)
    cp = gas.cp(ts, far)
    v = mach * math.sqrt(cp / (cp - gas.R_AIR) * gas.R_AIR * ts)
    return ts, ps, ps / (gas.R_AIR * ts), v


def area_by_continuity(w, tt, pt, mach, far=0.0, swirl_deg=0.0):
    ts, ps, rho, v = static_state(tt, pt, mach, far)
    return w / (rho * v * math.cos(math.radians(swirl_deg)))


def annulus(r_hub_m, r_tip_m):
    return math.pi * (r_tip_m ** 2 - r_hub_m ** 2)


@dataclass
class Check:
    station: str
    component: str
    quantity: str
    computed: float
    published: float
    band: float
    src: str
    r_hub_cm: float | None = None
    r_tip_cm: float | None = None
    z_cm: float | None = None
    blockage: float = 1.0        # published area factor applied to the geometric annulus
    diagnostic: bool = False     # plotted hollow: a route not in STEP0's table

    @property
    def diff(self):
        return self.computed / self.published - 1

    @property
    def ok(self):
        return abs(self.diff) < self.band


def find_key(d, name):
    """the value of the first key called `name` anywhere in a nested mapping"""
    if isinstance(d, dict):
        if name in d:
            return d[name]
        for v in d.values():
            r = find_key(v, name)
            if r is not None:
                return r
    return None


def _csv_rows(path):
    with open(path) as f:
        return [r for r in csv.DictReader(l for l in f if not l.startswith("#"))]


def load_geometry():
    pub = yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())
    fan = yaml.safe_load((DATA / "fan-design.yaml").read_text())
    efp = yaml.safe_load((DATA / "engine-flowpath.yaml").read_text())
    hpcs = yaml.safe_load((DATA / "hpc-stagewise.yaml").read_text())
    vd = yaml.safe_load((DATA / "hpc-vector-diagrams.yaml").read_text())
    lpta = yaml.safe_load((DATA / "lpt-aero.yaml").read_text())
    hpc_fp = {(r["row"], r["edge"]): r for r in _csv_rows(DATA / "hpc-flowpath.csv")}
    lpt_fp = {(r["row"], r["edge"]): r for r in _csv_rows(DATA / "lpt-flowpath.csv")}
    igv = next(r for r in vd["rows"] if r["row"] == "igv")
    pitch = min(igv["exit"], key=lambda p: abs(p[1] - 50))
    alpha = pitch[vd["columns"]["stator_station"].index("alpha_deg")]
    return dict(pub=pub, fan=fan, efp=efp, hpcs=hpcs, lpta=lpta, hpc_fp=hpc_fp, lpt_fp=lpt_fp,
                r1_inlet_pitch_swirl_deg=alpha, blockage=find_key(hpcs, "blockage"), hpc_rows=[(r["row"], r["edge"]) for r in _csv_rows(DATA / "hpc-flowpath.csv")],
                lpt_rows=[(r["row"], r["edge"]) for r in _csv_rows(DATA / "lpt-flowpath.csv")])


def run(rating_name="max_climb"):
    inp = load_inputs()
    rating = next(r for r in inp.ratings if r.name == rating_name)
    res = solve_rating(rating, inp)
    s = res.stations
    g = load_geometry()
    pub, fan, efp, hpcs, lpta = g["pub"], g["fan"], g["efp"], g["hpcs"], g["lpta"]
    cool = inp.cool
    checks = []

    # ---- fan face: specific flow on the corrected flow
    fr = efp["fan_and_booster"]["fan_rotor"]
    a_fan = annulus(fr["r_hub_cm"] / 100, fr["r_tip_cm"] / 100)
    checks.append(Check("2", "fan", "specific flow kg/s.m2", res.w2_corrected_kg_s / a_fan, fan["summary"]["specific_flow_kg_s_m2"], 0.01, "CR-165148 p.1; r from CR-165148 Table IV"))
    fan_face_mach = None
    for m in (x / 1000 for x in range(300, 900)):
        if area_by_continuity(res.w2_kg_s, s["t0"], s["p0"], m) <= a_fan:
            fan_face_mach = m
            break

    # ---- HPC rotor-1 inlet and OGV exit
    r1 = g["hpc_fp"][("R1", "LE")]
    a = annulus(float(r1["r_hub_cm"]) / 100, float(r1["r_tip_cm"]) / 100)
    m_mer = find_key(hpcs, "rotor1_inlet_meridional_mach")
    swirl = g["r1_inlet_pitch_swirl_deg"]
    m_abs = m_mer / math.cos(math.radians(swirl))
    checks.append(Check("25", "hpc", "R1 LE annulus m2", area_by_continuity(res.w_core_kg_s, s["t25"], s["p25"], m_abs, 0.0, swirl), a, 0.03,
                        "Table XXI R1 LE; Fig 12 meridional Mach 0.602", float(r1["r_hub_cm"]), float(r1["r_tip_cm"]), float(r1["z_hub_cm"])))
    a_c = checks[-1].computed
    checks.append(Check("25", "hpc", "R1 LE annulus x blockage 0.97", a_c, a * g["blockage"]["inlet"], 0.03, "Table XXI R1 LE; Fig 12; blockage p.19",
                        float(r1["r_hub_cm"]), float(r1["r_tip_cm"]), float(r1["z_hub_cm"]) + 2.0, g["blockage"]["inlet"]))
    specific_flow_route = inp.core_corrected_kg_s / find_key(hpcs, "rotor1_specific_flow_kg_s_m2")
    ogv = g["hpc_fp"][("S10", "TE")]
    a = annulus(float(ogv["r_hub_cm"]) / 100, float(ogv["r_tip_cm"]) / 100)
    m3 = find_key(hpcs, "exit_meridional_mach")["at_23_to_1_operating_line"]
    swirl3 = find_key(hpcs, "stator_exit_swirl_deg")["pitch"][-1]
    w3 = res.w_core_kg_s * (1 - cool["stage_5_cooling_and_purge"] - cool["stage_7_cooling_and_purge"])
    checks.append(Check("3", "hpc", "OGV TE annulus m2", area_by_continuity(w3, s["t3"], s["p3"], m3 / math.cos(math.radians(swirl3)), 0.0, swirl3), a, 0.04,
                        "Table XXI S10 TE; exit meridional Mach 0.30", float(ogv["r_hub_cm"]), float(ogv["r_tip_cm"]), float(ogv["z_hub_cm"])))

    checks.append(Check("3", "hpc", "OGV TE annulus x blockage 0.90", checks[-1].computed, a * g["blockage"]["exit"], 0.04, "Table XXI S10 TE; Mach 0.30; blockage p.19",
                        float(ogv["r_hub_cm"]), float(ogv["r_tip_cm"]), float(ogv["z_hub_cm"]) + 2.0, g["blockage"]["exit"]))

    # ---- HPT: Table XVIII two routes, then the two stage exits
    hpt = pub["hpt"]
    cm = hpt["cycle_match"]
    w41, t41, p41 = s["w41"], s["t41"], s["p4"]
    f41 = res.w_fuel_kg_s / (w41 - res.w_fuel_kg_s)
    checks.append(Check("41", "hpt", "W41 sqrtT/P g.sqrtK/(s.Pa)", w41 * math.sqrt(t41) / p41 * 1000, cm["corrected_flow_g_sqrtK_s_Pa"], 0.02, "Table XVIII"))
    dh_hpt = gas.h(t41, f41) - gas.h(s["t45"], f41)     # per kg of W41, before the coolant rejoins
    # the solver mixed the chargeable streams into t45; recover the pre-mix exit from the work
    hpc_power = res.stations.get("hpc_power")
    checks.append(Check("41", "hpt", "dh/T41 J/(kg.K)", s["hpt_dh_per_kg"] / t41, cm["energy_dh_over_T_J_kgK"], 0.02, "Table XVIII"))
    sa = hpt["stage_aerodynamics"]
    split = hpt["stage_work_split_stage1"]
    h_41 = gas.h(t41, f41)
    h_1x = h_41 - split * s["hpt_dh_per_kg"]
    t_1x = gas.t_from_h(h_1x, f41, guess=t41 - 200)
    # pressure after stage 1 at the overall efficiency
    h_1x_s = h_41 - split * s["hpt_dh_per_kg"] / inp.comp["hpt_efficiency"]
    t_1x_s = gas.t_from_h(h_1x_s, f41, guess=t_1x - 30)
    p_1x = p41 * math.exp(-(gas.phi(t41, f41) - gas.phi(t_1x_s, f41)) / gas.R_AIR)
    st = {x["location"]: x for x in hpt["flowpath"]["stations"]}
    e1, e2 = st["stage1_blade_exit"], st["stage2_blade_exit"]
    checks.append(Check("4x", "hpt", "stage-1 exit annulus m2",
                        area_by_continuity(w41, t_1x, p_1x, sa["exit_mach"][0], f41, sa["exit_swirl_deg"][0]),
                        annulus(e1["r_hub_cm"] / 100, e1["r_tip_cm"] / 100), 0.04, "HPT Fig 3; Table III exit Mach 0.34, swirl 16 deg", e1["r_hub_cm"], e1["r_tip_cm"], e1["x_cm"]))
    w45, t45, p45 = s["w45"], s["t45"], s["p45"]
    f45 = res.w_fuel_kg_s / (w45 - res.w_fuel_kg_s)
    checks.append(Check("45", "hpt", "stage-2 exit annulus m2",
                        area_by_continuity(w45, t45, p45, sa["exit_mach"][1], f45, sa["exit_swirl_deg"][1]),
                        annulus(e2["r_hub_cm"] / 100, e2["r_tip_cm"] / 100), 0.03, "HPT Fig 3; Table III exit Mach 0.42", e2["r_hub_cm"], e2["r_tip_cm"], e2["x_cm"]))

    # ---- LPT: Table XXI two routes, vane-1 LE, five stage exits
    lcm = pub["lpt"]["cycle_match"]
    checks.append(Check("49", "lpt", "T49 K", t45, lcm["inlet_temperature_T49_K"], 0.015, "Table XXI"))
    checks.append(Check("49", "lpt", "W49 sqrtT/P g.sqrtK/(s.Pa)", w45 * math.sqrt(t45) / p45 * 1000, lcm["corrected_flow_g_sqrtK_s_Pa"], 0.02, "Table XXI"))
    checks.append(Check("49", "lpt", "dh/T49 J/(kg.K)", s["lpt_dh_per_kg"] / t45, lcm["energy_dh_over_T_J_kgK"], 0.03, "Table XXI"))
    td = find_key(lpta, "transition_duct_axisymmetric_analysis")
    s1 = g["lpt_fp"][("S1", "LE")]
    m_le = 0.5 * (td["outer_wall_mach"]["at_vane_le"] + td["inner_wall_mach"]["at_vane_le"])
    checks.append(Check("49", "lpt", "vane-1 LE annulus m2", area_by_continuity(w45, t45, p45, m_le, f45),
                        annulus(float(s1["r_hub_cm"]) / 100, float(s1["r_tip_cm"]) / 100), 0.04, "sections S1 LE; Fig 7 Mach 0.40", float(s1["r_hub_cm"]), float(s1["r_tip_cm"]), float(s1["z_hub_cm"])))
    vdg = find_key(lpta, "vector_diagrams")
    h_t, p_t = gas.h(t45, f45), p45
    table_ii_dh = 0.0
    for n in range(1, 6):
        stg = vdg[f"stage{n}"]
        dh = stg["energy_extraction"] * BTU_PER_LB
        table_ii_dh += dh
        h_t -= dh
        p_t /= stg["pressure_ratio"]
        w = s["w5"] if n == 5 else w45
        far = res.w_fuel_kg_s / (w - res.w_fuel_kg_s)
        t_t = gas.t_from_h(h_t, far, guess=t45 - 60 * n)
        fluxes = []
        for m in stg["stage_exit_axial_mach"]:
            ts, ps, rho, v = static_state(t_t, p_t, m, far)
            fluxes.append(rho * v)
        a_c = w / (sum(fluxes) / 3)
        row = g["lpt_fp"][(f"R{n}", "TE")]
        a_pub = annulus(float(row["r_hub_cm"]) / 100, float(row["r_tip_cm"]) / 100)
        checks.append(Check(f"R{n}", "lpt", f"stage-{n} exit annulus m2", a_c, a_pub, 0.05,
                            "sections R%d TE; Table II axial Mach h/p/t mean" % n, float(row["r_hub_cm"]), float(row["r_tip_cm"]), float(row["z_hub_cm"])))
        checks.append(Check(f"R{n}", "lpt", f"stage-{n} exit annulus, pitch Mach only", w / fluxes[1], a_pub, 0.05, "diagnostic: Table II pitch axial Mach alone",
                            float(row["r_hub_cm"]), float(row["r_tip_cm"]), float(row["z_hub_cm"]) + 1.5, 1.0, True))
    # the vane-1 leading-edge Mach the sections' annulus and the cycle's flow imply
    a_le = annulus(float(s1["r_hub_cm"]) / 100, float(s1["r_tip_cm"]) / 100)
    m_le_implied = next(m / 1000 for m in range(150, 700) if area_by_continuity(w45, t45, p45, m / 1000, f45) <= a_le)
    extra = dict(fan_face_mach=fan_face_mach, fan_annulus_m2=a_fan, hpc_r1_specific_flow_route_m2=specific_flow_route,
                 table_ii_dh_sum_J_kg=table_ii_dh, lpt_dh_per_kg=s["lpt_dh_per_kg"], hpt_dh_per_kg=s["hpt_dh_per_kg"],
                 t_1x=t_1x, p_1x=p_1x, hpt_stage1_pr=p41 / p_1x, hpt_stage2_pr=p_1x / p45, lpt_vane1_le_mach_implied=m_le_implied,
                 igv_exit_pitch_swirl_deg=g["r1_inlet_pitch_swirl_deg"])
    return res, checks, extra, g


def station_table(res):
    """T, p at every cycle station of the max-climb solve"""
    s = res.stations
    order = [("0", "t0", "p0"), ("13", "t13", "p13"), ("23", "t23", "p23"), ("25", "t25", "p25"), ("3", "t3", "p3"), ("4", "t4", "p4"),
             ("41", "t41", "p4"), ("45", "t45", "p45"), ("5", "t5", "p5"), ("6", "t6", "p6")]
    return [(name, s[t], s[p]) for name, t, p in order]


def plot(res, checks, extra, g, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    outdir = pathlib.Path(outdir)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    panels = {"hpc": (axes[0], "HPC — Table XXI streamlines 1 and 12 (z from rotor-1 LE hub)"),
              "hpt": (axes[1], "HPT — Fig 3 (x from vane-1 inlet)"),
              "lpt": (axes[2], "LPT — from the airfoil sections (z from HPT exit)")}
    # published hub/tip lines
    for comp, fp, rows in (("hpc", g["hpc_fp"], g["hpc_rows"]), ("lpt", g["lpt_fp"], g["lpt_rows"])):
        ax = panels[comp][0]
        z = [float(fp[k]["z_hub_cm"]) for k in rows]
        ax.plot(z, [float(fp[k]["r_hub_cm"]) for k in rows], "k-", lw=1.2, label="hub, published")
        ax.plot([float(fp[k]["z_tip_cm"]) for k in rows], [float(fp[k]["r_tip_cm"]) for k in rows], "k-", lw=1.2, label="tip, published")
    ax = panels["hpt"][0]
    st = g["pub"]["hpt"]["flowpath"]["stations"]
    ax.plot([x["x_cm"] for x in st], [x["r_hub_cm"] for x in st], "k-", lw=1.2, label="hub, published")
    ax.plot([x["x_cm"] for x in st], [x["r_tip_cm"] for x in st], "k-", lw=1.2, label="tip, published")
    for c in checks:
        if c.r_hub_cm is None or c.component not in panels:
            continue
        ax = panels[c.component][0]
        # the tip radius the computed area implies over the published hub, the
        # published blockage divided out so it sits on the geometric wall
        r_tip_c = math.sqrt(c.computed / c.blockage / math.pi + (c.r_hub_cm / 100) ** 2) * 100
        a_geo = c.published / c.blockage
        r_lo = math.sqrt(a_geo * (1 - c.band) / math.pi + (c.r_hub_cm / 100) ** 2) * 100
        r_hi = math.sqrt(a_geo * (1 + c.band) / math.pi + (c.r_hub_cm / 100) ** 2) * 100
        ax.fill_between([c.z_cm - 0.6, c.z_cm + 0.6], [r_lo, r_lo], [r_hi, r_hi], color="tab:green", alpha=0.25, lw=0)
        color = "tab:green" if c.ok else "tab:red"
        if c.diagnostic:
            ax.plot(c.z_cm, r_tip_c, "o", mfc="none", mec=color, mew=1.6, ms=7)
        elif c.blockage != 1.0:
            ax.plot(c.z_cm, r_tip_c, "D", color=color, ms=6)
        else:
            ax.plot(c.z_cm, r_tip_c, "o", color=color, ms=6)
    for comp, (ax, title) in panels.items():
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("axial, cm")
        ax.set_ylabel("radius, cm")
        ax.grid(alpha=0.3)
    axes[0].plot([], [], "o", color="tab:green", label="tip by continuity, in band")
    axes[0].plot([], [], "o", color="tab:red", label="tip by continuity, out of band")
    axes[0].plot([], [], "D", color="tab:green", label="with the published blockage (0.97 / 0.90)")
    axes[0].plot([], [], "o", mfc="none", mec="tab:red", mew=1.6, label="diagnostic: pitch Mach alone")
    axes[0].fill_between([], [], [], color="tab:green", alpha=0.25, label="pass band on the published annulus")
    axes[0].legend(fontsize=7, loc="lower left")
    fig.suptitle("E3 annulus at max climb: continuity at each report's design Mach against the published walls", fontsize=10)
    fig.tight_layout()
    fig.savefig(outdir / "annulus.png", dpi=130)
    plt.close(fig)
    # T-s diagram
    fig, ax = plt.subplots(figsize=(6.5, 5))
    s = res.stations
    pts = station_table(res)
    far_at = {"4": res.far_combustor, "41": res.w_fuel_kg_s / (s["w41"] - res.w_fuel_kg_s), "45": res.w_fuel_kg_s / (s["w45"] - res.w_fuel_kg_s),
              "5": res.w_fuel_kg_s / (s["w5"] - res.w_fuel_kg_s), "6": res.w_fuel_kg_s / (s["w6"] - res.w_fuel_kg_s)}
    ent = [(n, gas.phi(t, far_at.get(n, 0.0)) - gas.R_AIR * math.log(p / s["p0"]), t) for n, t, p in pts]
    core = [e for e in ent if e[0] != "13"]
    ax.plot([e[1] for e in core], [e[2] for e in core], "o-", color="tab:blue", label="core stream, solved")
    ax.plot([ent[1][1]], [ent[1][2]], "s", color="tab:orange", label="bypass 13, solved")
    offsets = {"0": (-10, -10), "13": (6, -4), "23": (-14, 4), "25": (6, 6)}
    for n, sv, t in ent:
        ax.annotate(n, (sv, t), textcoords="offset points", xytext=offsets.get(n, (4, 4)), fontsize=8)
    t41_pub = g["pub"]["cycle_definition"]["max_climb"]["hpt_rotor_inlet_temperature_K"]
    t49_pub = g["pub"]["lpt"]["cycle_match"]["inlet_temperature_T49_K"]
    s41 = next(e[1] for e in ent if e[0] == "41"); s45 = next(e[1] for e in ent if e[0] == "45")
    ax.plot([s41, s45], [t41_pub, t49_pub], "x", color="k", ms=9, mew=2, label="published: T41 Table XII, T49 Table XXI")
    ax.set_xlabel("entropy relative to station 0, J/(kg·K)")
    ax.set_ylabel("total temperature, K")
    ax.set_title("E3 max climb, 10.67 km M0.8 ISA+10 — T–s of the solved cycle", fontsize=10)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(outdir / "ts-diagram.png", dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    res, checks, extra, g = run()
    print("station  T_t K   p_t kPa")
    for n, t, p in station_table(res):
        print(f"{n:>7}{t:>8.1f}{p / 1000:>10.1f}")
    print(f"\nfan-face Mach by continuity {extra['fan_face_mach']:.3f}; fan annulus {extra['fan_annulus_m2']:.3f} m2")
    print(f"HPC R1 inlet area by the specific-flow route {extra['hpc_r1_specific_flow_route_m2']:.4f} m2")
    print(f"HPT stage PRs at the 56.5 % split: {extra['hpt_stage1_pr']:.2f} / {extra['hpt_stage2_pr']:.2f} (Table III 2.25 / 2.11); interstage T {extra['t_1x']:.0f} K")
    print(f"LPT dh: solver {extra['lpt_dh_per_kg'] / 1000:.1f} kJ/kg; Table II stage sum {extra['table_ii_dh_sum_J_kg'] / 1000:.1f}")
    print(f"LPT vane-1 LE Mach implied by the sections' annulus and the cycle's flow: {extra['lpt_vane1_le_mach_implied']:.3f} (Fig 7 walls read 0.40); IGV exit swirl at pitch {extra['igv_exit_pitch_swirl_deg']} deg\n")
    print(f"{'st':<4}{'comp':<5}{'quantity':<32}{'computed':>11}{'published':>11}{'diff %':>8}{'band %':>7}  verdict  source")
    for c in checks:
        print(f"{c.station:<4}{c.component:<5}{c.quantity:<32}{c.computed:>11.4f}{c.published:>11.4f}{c.diff * 100:>8.2f}{c.band * 100:>7.1f}  {'pass' if c.ok else 'MISS':<7}  {c.src}")
    plot(res, checks, extra, g, pathlib.Path(__file__).parent / "figures")
    print("\nfigures written")

"""C1 unit 1: LPT mean-line at the pitch streamline, stage by stage, from
the max-climb cycle state. STEP0.md, unit 1."""
from __future__ import annotations

import math
import pathlib
from dataclasses import dataclass

import yaml

from e3cycle import gas
from e3cycle.cycle import DATA, load_inputs, solve_rating
from e3cycle.stations import _csv_rows, find_key

BTU_PER_LB = 2326.0
IN = 0.0254


@dataclass
class StageResult:
    n: int
    dh: float
    r2: float
    r3: float
    u2: float
    u3: float
    cx2: float
    cx3: float
    alpha2: float
    beta2: float
    beta3: float
    alpha3: float
    m2: float
    m2rel: float
    m3rel: float
    m3: float
    mx3: float
    reaction: float
    phi: float
    psi: float
    t01: float
    p01: float
    t03: float
    p03: float
    stage_pr: float
    reaction_static: float = 0.0
    u2r: float = 0.0
    reaction_p: float = 0.0
    ps2: float = 0.0
    ps3: float = 0.0


def load():
    aero = yaml.safe_load((DATA / "lpt-aero.yaml").read_text())
    design = yaml.safe_load((DATA / "lpt-design.yaml").read_text())
    fp = {(r["row"], r["edge"]): r for r in _csv_rows(DATA / "lpt-flowpath.csv")}
    rpm = find_key(design, "case_41_flowpath_and_clearance")["fan_physical_speed_rpm"][0]
    blockage = aero["derived"]["throughflow_blockage"]["value"]
    return dict(table_ii=find_key(aero, "vector_diagrams"), fp=fp, rpm=rpm, blockage=blockage)


def _pitch_and_area(fp, row, edge, blockage):
    r = fp[(row, edge)]
    r_p = float(r["r50_in"]) * IN
    a = math.pi * ((float(r["r_tip_cm"]) / 100) ** 2 - (float(r["r_hub_cm"]) / 100) ** 2) * blockage
    return r_p, a


def _cx_by_continuity(w, t0, p0, a, far, tan_alpha, guess=150.0):
    """axial velocity such that rho c_x A = w at total state (t0, p0) with
    swirl tan_alpha = c_theta / c_x; real gas"""
    h0 = gas.h(t0, far)

    def flow(cx):
        c2 = cx * cx * (1 + tan_alpha ** 2)
        ts = gas.t_from_h(h0 - 0.5 * c2, far, guess=t0 - c2 / 2400)
        ps = p0 * math.exp(-(gas.phi(t0, far) - gas.phi(ts, far)) / gas.R_AIR)
        return ps / (gas.R_AIR * ts) * cx * a, ts, ps

    lo, hi = 10.0, 400.0
    for _ in range(80):
        cx = 0.5 * (lo + hi)
        lo, hi = (cx, hi) if flow(cx)[0] < w else (lo, cx)
    cx = 0.5 * (lo + hi)
    _, ts, ps = flow(cx)
    return cx, ts, ps


def _a(ts, far):
    cp = gas.cp(ts, far)
    return math.sqrt(cp / (cp - gas.R_AIR) * gas.R_AIR * ts)


def run():
    inp = load_inputs()
    rating = next(r for r in inp.ratings if r.name == "max_climb")
    res = solve_rating(rating, inp)
    s = res.stations
    g = load()
    omega = g["rpm"] * 2 * math.pi / 60
    w = s["w45"]
    far = res.w_fuel_kg_s / (w - res.w_fuel_kg_s)
    t01, p01 = s["t45"], s["p45"]
    alpha1 = 0.0
    # static state at the vane-1 inlet for the stage-1 reaction
    r1, a1 = _pitch_and_area(g["fp"], "S1", "LE", g["blockage"])
    cx1, ts1, ps1 = _cx_by_continuity(w, t01, p01, a1, far, math.tan(alpha1))
    h1 = gas.h(ts1, far)
    out = []
    for n in range(1, 6):
        tb = g["table_ii"][f"stage{n}"]
        dh = tb["energy_extraction"] * BTU_PER_LB
        alpha2 = math.radians(tb["stator_exit_angle_deg"][1])
        r2, a2 = _pitch_and_area(g["fp"], f"S{n}", "TE", g["blockage"])   # station 2: the stator trailing edge
        r2r, _ = _pitch_and_area(g["fp"], f"R{n}", "LE", g["blockage"])   # the rotor-inlet pitch radius, for U in the loading
        r3, a3 = _pitch_and_area(g["fp"], f"R{n}", "TE", g["blockage"])
        u2, u3, u2r = omega * r2, omega * r3, omega * r2r
        # stator exit / rotor inlet (lossless stator: p02 = p01)
        cx2, ts2, ps2 = _cx_by_continuity(w, t01, p01, a2, far, math.tan(alpha2))
        ct2 = cx2 * math.tan(alpha2)
        c2 = math.hypot(cx2, ct2)
        w2 = math.hypot(cx2, ct2 - u2)
        beta2 = math.atan2(ct2 - u2, cx2)
        a_2 = _a(ts2, far)
        # rotor exit from Euler; exit total pressure from Table II's stage PR
        h03 = gas.h(t01, far) - dh
        t03 = gas.t_from_h(h03, far, guess=t01 - 60)
        p03 = p01 / tb["pressure_ratio"]
        ct3 = (u2 * ct2 - dh) / u3
        cx3, ts3, ps3 = _cx_by_continuity(w, t03, p03, a3, far, ct3 / 150.0)
        # the swirl ratio depends on cx3 itself: iterate
        for _ in range(30):
            cx3, ts3, ps3 = _cx_by_continuity(w, t03, p03, a3, far, ct3 / cx3)
        c3 = math.hypot(cx3, ct3)
        w3 = math.hypot(cx3, ct3 - u3)
        alpha3 = math.atan2(ct3, cx3)
        beta3 = math.atan2(ct3 - u3, cx3)
        a_3 = _a(ts3, far)
        h2, h3 = gas.h(ts2, far), gas.h(ts3, far)
        reaction = (h2 - h3) / dh                 # rotor static enthalpy drop over the stage total drop
        reaction_static = (h2 - h3) / (h1 - h3)   # over the stage static drop
        reaction_p = (ps2 - ps3) / (ps1 - ps3)     # static pressure based
        out.append(StageResult(n, dh, r2, r3, u2, u3, cx2, cx3, math.degrees(alpha2), abs(math.degrees(beta2)), abs(math.degrees(beta3)),
                               abs(math.degrees(alpha3)), c2 / a_2, w2 / a_2, w3 / a_3, c3 / a_3, cx3 / a_3, reaction, cx2 / u2,
                               dh / (2 * u2r * u2r), t01, p01, t03, p03, tb["pressure_ratio"], reaction_static, u2r, reaction_p, ps2, ps3))
        # next stage inlet
        t01, p01, alpha1, h1, ps1 = t03, p03, alpha3, h3, ps3
    return res, g, out


COMPARE = [  # (attribute, Table II key, band)
    ("beta2", "rotor_rel_inlet_angle_deg", 2.5),
    ("beta3", "rotor_rel_exit_angle_deg", 2.5),
    ("alpha3", "stage_exit_swirl_deg", 2.5),
    ("m2", "stator_exit_mach", 0.03),
    ("m2rel", "rotor_rel_inlet_mach", 0.03),
    ("m3rel", "rotor_rel_exit_mach", 0.03),
    ("mx3", "stage_exit_axial_mach", 0.03),
    ("reaction", "reaction", 0.04),
    ("phi", "flow_coefficient_vz_over_u", 0.06),
    ("psi", "loading_dh_over_2u2", 0.06),
]


def published(tb, key):
    v = tb[key]
    return v[1] if isinstance(v, list) else v


def comparison(g, out):
    rows = []
    for st in out:
        tb = g["table_ii"][f"stage{st.n}"]
        for attr, key, band in COMPARE:
            rows.append((st.n, attr, getattr(st, attr), published(tb, key), band))
    return rows


def plot(g, out, res, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    stages = [st.n for st in out]
    groups = [(axes[0], "angles from axial, deg", [("beta2", "β₂ rotor rel. inlet"), ("beta3", "β₃ rotor rel. exit"), ("alpha3", "α₃ stage exit swirl")]),
              (axes[1], "Mach", [("m2", "M₂ stator exit"), ("m2rel", "M₂rel"), ("m3rel", "M₃rel"), ("mx3", "M_x3 exit axial")]),
              (axes[2], "coefficients", [("reaction", "reaction"), ("phi", "φ = c_x/U"), ("psi", "ψ = Δh/2U²")])]
    for ax, ylabel, items in groups:
        for i, (attr, label) in enumerate(items):
            color = f"C{i}"
            comp = [getattr(st, attr) for st in out]
            key = next(k for a, k, _ in COMPARE if a == attr)
            band = next(b for a, _, b in COMPARE if a == attr)
            pub = [published(g["table_ii"][f"stage{n}"], key) for n in stages]
            ax.fill_between(stages, [p - band for p in pub], [p + band for p in pub], color=color, alpha=0.15, lw=0)
            ax.plot(stages, comp, "-o", color=color, label=f"{label}, computed")
            ax.plot(stages, pub, "x", color=color, ms=9, mew=2, label=f"{label}, Table II")
        ax.set_xlabel("stage")
        ax.set_ylabel(ylabel)
        ax.set_xticks(stages)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7)
    fig.suptitle("E3 LPT mean-line at pitch, max climb 3,539 rpm: computed from Δh and α₂ against Table II (bands shaded)", fontsize=10)
    fig.tight_layout()
    fig.savefig(pathlib.Path(outdir) / "lpt-vector-diagrams.png", dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    res, g, out = run()
    print(f"LPT inlet {out[0].t01:.1f} K {out[0].p01 / 1000:.1f} kPa, {res.stations['w45']:.2f} kg/s, {g['rpm']} rpm, blockage {g['blockage']}")
    print(f"{'st':<3}{'r2 cm':>7}{'U2':>7}{'cx2':>7}{'cx3':>7}{'β2':>7}{'β3':>7}{'α3':>7}{'M2':>7}{'M2r':>7}{'M3r':>7}{'Mx3':>7}{'R':>7}{'Rstat':>7}{'Rp':>7}{'φ':>7}{'ψ':>7}{'T03':>8}{'p03':>8}")
    for st in out:
        print(f"{st.n:<3}{st.r2 * 100:>7.2f}{st.u2:>7.1f}{st.cx2:>7.1f}{st.cx3:>7.1f}{st.beta2:>7.1f}{st.beta3:>7.1f}{st.alpha3:>7.1f}{st.m2:>7.3f}{st.m2rel:>7.3f}{st.m3rel:>7.3f}{st.mx3:>7.3f}{st.reaction:>7.3f}{st.reaction_static:>7.3f}{st.reaction_p:>7.3f}{st.phi:>7.3f}{st.psi:>7.3f}{st.t03:>8.1f}{st.p03 / 1000:>8.1f}")
    print(f"\n{'st':<3}{'quantity':<12}{'computed':>10}{'Table II':>10}{'diff':>8}{'band':>6}  verdict")
    miss = 0
    for n, attr, c, p, band in comparison(g, out):
        ok = abs(c - p) < band
        miss += not ok
        print(f"{n:<3}{attr:<12}{c:>10.3f}{p:>10.3f}{c - p:>8.3f}{band:>6}  {'pass' if ok else 'MISS'}")
    pr = 1.0
    for st in out:
        pr *= st.stage_pr
    print(f"\nTable II stage PR product {pr:.3f} vs cycle LPT PR {res.lpt_pr:.3f} ({(pr / res.lpt_pr - 1) * 100:+.1f} %); misses {miss} of {len(comparison(g, out))}")
    plot(g, out, res, pathlib.Path(__file__).parent / "figures")
MD_END=1

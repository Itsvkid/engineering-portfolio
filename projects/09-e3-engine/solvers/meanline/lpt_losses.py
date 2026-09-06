"""C1 unit 2, application: the E3 LPT with Ainley-Mathieson row losses.
Same stage walk as lpt.py, but every row's total-pressure loss comes
from its geometry (sections, counts, flowpath, clearance goal) and the
mean-line angles, and the stage exit pressure follows from the losses
instead of Table II's pressure ratio."""
from __future__ import annotations

import math
import pathlib
from dataclasses import dataclass

import yaml

from e3cycle import gas
from e3cycle.cycle import DATA, load_inputs, solve_rating
from e3cycle.stations import _csv_rows, find_key
from meanline import losses as L
from meanline.lpt import BTU_PER_LB, IN, _a, _cx_by_continuity, run as run_kinematics
from meanline.sections import section_geometry

CM = 0.01


@dataclass
class Row:
    name: str
    s_c: float
    t_c: float
    te_s: float
    alpha1: float
    alpha2: float
    k_h: float
    an1: float
    an2: float
    id_od: float
    yp: float
    ysk: float
    yt: float
    re_chord: float
    i_s: float
    c_h: float = 0.0
    ysk_dc: float = 0.0
    yt_dc: float = 0.0


@dataclass
class Stage:
    n: int
    dh: float
    t01: float
    p01: float
    t03: float
    p03: float
    p03_table_ii: float
    eta_tt: float
    rows: list
    p03_dc: float = 0.0
    eta_tt_dc: float = 0.0


def load_geometry():
    aero = yaml.safe_load((DATA / "lpt-aero.yaml").read_text())
    design = yaml.safe_load((DATA / "lpt-design.yaml").read_text())
    fp = {(r["row"], r["edge"]): r for r in _csv_rows(DATA / "lpt-flowpath.csv")}
    return dict(aero=aero, design=design, fp=fp,
                rpm=find_key(design, "case_41_flowpath_and_clearance")["fan_physical_speed_rpm"][0],
                blockage=aero["derived"]["throughflow_blockage"]["value"],
                clearance_m=find_key(design, "goal_gap_cm") * CM,
                te_blockage=_table_iii(aero))


def _table_iii(aero):
    """the Table III block: the mapping that carries te_blockage"""
    def walk(d):
        if isinstance(d, dict):
            if "te_blockage" in d:
                return d
            for v in d.values():
                r = walk(v)
                if r:
                    return r
    t = walk(aero)
    return dict(zip(t["rows"], t["te_blockage"]))


def _row_geom(fp, row, edge):
    r = fp[(row, edge)]
    r_p = float(r["r50_in"]) * IN
    hub, tip = float(r["r_hub_cm"]) * CM, float(r["r_tip_cm"]) * CM
    return r_p, math.pi * (tip ** 2 - hub ** 2), hub / tip, tip - hub


def _viscosity(t):
    """Sutherland, air"""
    return 1.716e-5 * (t / 273.15) ** 1.5 * (273.15 + 110.4) / (t + 110.4)


def run(counts_vanes=(72, 102, 96, 114, 120), counts_rotors=(120, 122, 122, 156, 110)):
    """Row angles and Mach numbers from unit 1 (lpt.py) are the inputs;
    each row's loss coefficient sets its exit total pressure; the stage
    and turbine efficiencies follow. Two secondary-loss routes: R&M 2974
    as printed, and the Dunham-Came aspect-ratio form (assumption)."""
    res, gk, kin = run_kinematics()
    s = res.stations
    g = load_geometry()
    w = s["w45"]
    far = res.w_fuel_kg_s / (w - res.w_fuel_kg_s)
    stages = []
    h_in = gas.h(s["t45"], far)
    p01 = p01_dc = s["p45"]
    p01_table = s["p45"]
    alpha1 = 0.0
    for st in kin:
        n = st.n
        tb = find_key(g["aero"], "vector_diagrams")[f"stage{n}"]
        # ---- geometry
        _, an_s_le, _, _ = _row_geom(g["fp"], f"S{n}", "LE")
        r2, an_s_te, id_od2, h2 = _row_geom(g["fp"], f"S{n}", "TE")
        _, an_r_le, _, _ = _row_geom(g["fp"], f"R{n}", "LE")
        r3, an_r_te, id_od3, h3 = _row_geom(g["fp"], f"R{n}", "TE")
        secS, secR = section_geometry(f"S{n}"), section_geometry(f"R{n}")
        cS, cR = secS["chord_in"] * IN, secR["chord_in"] * IN
        pitchS, pitchR = 2 * math.pi * r2 / counts_vanes[n - 1], 2 * math.pi * r3 / counts_rotors[n - 1]
        # ---- row losses at the unit-1 angles (zero incidence: beta1 = alpha1)
        lossS = L.row_total_loss(alpha1, alpha1, st.alpha2, pitchS / cS, secS["t_over_c"], secS["te_in"] * IN / pitchS,
                                 an_s_le, an_s_te, id_od2, g["clearance_m"] / h2, shrouded=True, c_h=cS / h2)
        lossR = L.row_total_loss(st.beta2, st.beta2, st.beta3, pitchR / cR, secR["t_over_c"], secR["te_in"] * IN / pitchR,
                                 an_r_le, an_r_te, id_od3, g["clearance_m"] / h3, shrouded=True, c_h=cR / h3)
        # ---- static states from unit 1's Mach numbers (real gas), stator
        def stage_pressures(p01, yt_s, yt_r):
            # stator exit: total from the loss on the exit dynamic head at M2
            ts2, ps2_ratio = _static_ratio(st.t01, st.m2, far)
            p02 = p01 / (1 + yt_s * (1 - ps2_ratio))
            ps2 = p02 * ps2_ratio
            # rotor: relative frame
            h02rel = gas.h(ts2, far) + 0.5 * (st.m2rel * _a(ts2, far)) ** 2
            t02rel = gas.t_from_h(h02rel, far, guess=ts2 + 20)
            p02rel = ps2 * math.exp((gas.phi(t02rel, far) - gas.phi(ts2, far)) / gas.R_AIR)
            h03rel = h02rel - 0.5 * (st.u2 ** 2 - st.u3 ** 2)
            t03rel = gas.t_from_h(h03rel, far, guess=t02rel)
            p03rel_i = p02rel * math.exp((gas.phi(t03rel, far) - gas.phi(t02rel, far)) / gas.R_AIR)
            ts3, ps3rel_ratio = _static_ratio(t03rel, st.m3rel, far)
            p03rel = p03rel_i / (1 + yt_r * (1 - ps3rel_ratio))
            ps3 = p03rel * ps3rel_ratio
            p03 = ps3 * math.exp((gas.phi(st.t03, far) - gas.phi(ts3, far)) / gas.R_AIR)
            return p02, p03, ts2, ts3, ps2, ps3

        p02, p03, ts2, ts3, ps2, ps3 = stage_pressures(p01, lossS["yt"], lossR["yt"])
        _, p03_dc, _, _, _, _ = stage_pressures(p01_dc, lossS["yt_dc"], lossR["yt_dc"])
        t03s = gas.t_from_phi(gas.phi(st.t01, far) - gas.R_AIR * math.log(p01 / p03), far, guess=st.t03)
        t03s_dc = gas.t_from_phi(gas.phi(st.t01, far) - gas.R_AIR * math.log(p01_dc / p03_dc), far, guess=st.t03)
        eta = st.dh / (gas.h(st.t01, far) - gas.h(t03s, far))
        eta_dc = st.dh / (gas.h(st.t01, far) - gas.h(t03s_dc, far))
        mu2, mu3 = _viscosity(ts2), _viscosity(ts3)
        rowS = Row(f"S{n}", pitchS / cS, secS["t_over_c"], secS["te_in"] * IN / pitchS, alpha1, st.alpha2, g["clearance_m"] / h2, an_s_le, an_s_te, id_od2,
                   lossS["yp"], lossS["ysk"], lossS["yt"], ps2 / (gas.R_AIR * ts2) * st.m2 * _a(ts2, far) * cS / mu2, lossS["i_s"], cS / h2, lossS["ysk_dc"], lossS["yt_dc"])
        rowR = Row(f"R{n}", pitchR / cR, secR["t_over_c"], secR["te_in"] * IN / pitchR, st.beta2, st.beta3, g["clearance_m"] / h3, an_r_le, an_r_te, id_od3,
                   lossR["yp"], lossR["ysk"], lossR["yt"], ps3 / (gas.R_AIR * ts3) * st.m3rel * _a(ts3, far) * cR / mu3, lossR["i_s"], cR / h3, lossR["ysk_dc"], lossR["yt_dc"])
        p01_table /= tb["pressure_ratio"]
        stages.append(Stage(n, st.dh, st.t01, p01, st.t03, p03, p01_table, eta, [rowS, rowR], p03_dc, eta_dc))
        p01, p01_dc, alpha1 = p03, p03_dc, st.alpha3
    dh_tot = sum(x.dh for x in stages)

    def overall(p_exit):
        t05s = gas.t_from_phi(gas.phi(s["t45"], far) - gas.R_AIR * math.log(s["p45"] / p_exit), far, guess=stages[-1].t03)
        return dh_tot / (h_in - gas.h(t05s, far))

    return res, g, stages, dict(eta_tt=overall(p01), eta_tt_dc=overall(p01_dc), pr=s["p45"] / p01, pr_dc=s["p45"] / p01_dc,
                                pr_table_ii=s["p45"] / p01_table, pr_cycle=res.lpt_pr)


def _static_ratio(t0, mach, far):
    """static temperature and p/p0 at a Mach number, real gas"""
    from e3cycle.stations import static_state
    ts, ps, _, _ = static_state(t0, 1.0, mach, far)
    return ts, ps


def plot(stages, summ, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.8))
    rows = [r for st in stages for r in st.rows]
    x = list(range(len(rows)))
    ax1.bar([i - 0.2 for i in x], [r.yp for r in rows], 0.4, color="tab:blue", label="profile Y_p (Fig 4, eq 5)")
    ax1.bar([i - 0.2 for i in x], [r.ysk for r in rows], 0.4, bottom=[r.yp for r in rows], color="tab:orange", label="secondary + clearance, R&M 2974 Fig 8")
    ax1.bar([i + 0.2 for i in x], [r.yp for r in rows], 0.4, color="tab:blue", alpha=0.5)
    ax1.bar([i + 0.2 for i in x], [r.ysk_dc for r in rows], 0.4, bottom=[r.yp for r in rows], color="tab:green", alpha=0.7, label="secondary + clearance, Dunham-Came c/h form (assumption)")
    ax1.set_xticks(x)
    ax1.set_xticklabels([r.name for r in rows])
    ax1.set_ylabel("loss coefficient Y = ΔP₀ / (P₀ − p) at row exit")
    ax1.set_title("E3 LPT row losses at max climb, zero incidence", fontsize=10)
    ax1.legend(fontsize=7)
    ax1.grid(alpha=0.3, axis="y")
    n = [st.n for st in stages]
    ax2.plot(n, [st.eta_tt for st in stages], "o-", color="tab:orange", label="stage η_tt, R&M 2974 as printed")
    ax2.plot(n, [st.eta_tt_dc for st in stages], "s-", color="tab:green", label="stage η_tt, with Dunham-Came")
    ax2.axhline(summ["eta_tt"], color="tab:orange", ls="--", label=f"five-stage η_tt {summ['eta_tt']:.3f}")
    ax2.axhline(summ["eta_tt_dc"], color="tab:green", ls="--", label=f"five-stage η_tt {summ['eta_tt_dc']:.3f}")
    ax2.axhspan(0.897, 0.937, color="k", alpha=0.08, label="published 0.917 ± 2 points (the method's own accuracy)")
    ax2.plot([3], [0.917], "kx", ms=10, mew=2, label="LPT report Table I: 0.917 at max climb")
    ax2.set_xlabel("stage")
    ax2.set_ylabel("total-to-total efficiency")
    ax2.set_xticks(n)
    ax2.set_ylim(0.7, 0.96)
    ax2.grid(alpha=0.3)
    ax2.legend(fontsize=7, loc="lower right")
    ax2.set_title("Stage and turbine efficiency against the published value", fontsize=10)
    fig.tight_layout()
    fig.savefig(pathlib.Path(outdir) / "lpt-losses.png", dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    res, g, stages, summ = run()
    plot(stages, summ, pathlib.Path(__file__).parent / "figures")
    print(f"{'row':<4}{'s/c':>6}{'t/c':>6}{'te/s':>7}{'h/c':>6}{'a1':>6}{'a2':>6}{'k/h':>7}{'i_s':>6}{'Yp':>7}{'Ys+k':>7}{'Yt':>7}{'Ys+k DC':>8}{'Yt DC':>7}{'Re':>8}")
    for st in stages:
        for r in st.rows:
            print(f"{r.name:<4}{r.s_c:>6.3f}{r.t_c:>6.3f}{r.te_s:>7.3f}{1 / r.c_h:>6.2f}{r.alpha1:>6.1f}{r.alpha2:>6.1f}{r.k_h:>7.4f}{r.i_s:>6.1f}{r.yp:>7.4f}{r.ysk:>7.4f}{r.yt:>7.4f}{r.ysk_dc:>8.4f}{r.yt_dc:>7.4f}{r.re_chord:>8.0f}")
        print(f"     stage {st.n}: dh {st.dh / 1000:.1f} kJ/kg  T {st.t01:.0f}->{st.t03:.0f} K  p {st.p01 / 1000:.1f}->{st.p03 / 1000:.1f} kPa (DC {st.p03_dc / 1000:.1f}; Table II chain {st.p03_table_ii / 1000:.1f})  eta_tt {st.eta_tt:.4f} (DC {st.eta_tt_dc:.4f})")
    print(f"\nLPT eta_tt: R&M 2974 as printed {summ['eta_tt']:.4f}; with the Dunham-Came aspect-ratio term {summ['eta_tt_dc']:.4f}; LPT report Table I 0.917, status at max climb 0.915, rig 0.920")
    print(f"LPT PR: {summ['pr']:.3f} (DC {summ['pr_dc']:.3f}); Table II chain {summ['pr_table_ii']:.3f}; cycle {summ['pr_cycle']:.3f}")

"""C1 unit 3: the E3 HPT mean-line at pitch, two cooled stages, with the
loss model validated in units 2 and 2b. STEP0.md, unit 3.

The sharp target is not the single efficiency but HPT report Table V,
which prices the aspect-ratio and tip-clearance debits separately against
a tight-clearance uncooled baseline."""
from __future__ import annotations

import math
import pathlib
from dataclasses import dataclass, field

import yaml

from e3cycle import gas
from e3cycle.cycle import DATA, load_inputs, solve_rating
from e3cycle.stations import static_state
from meanline import losses as L

CM = 0.01


@dataclass
class HptStage:
    n: int
    dh: float
    u: float
    r_pitch: float
    psi: float
    reaction: float
    alpha2: float
    beta2: float
    beta3: float
    alpha3: float
    m2: float
    m2rel: float
    m3rel: float
    m3: float
    turning: float
    t01: float
    p01: float
    t03: float
    p03: float
    eta_tt: float
    rows: list = field(default_factory=list)
    reaction_kin: float = 0.0
    reaction_h: float = 0.0
    reaction_p: float = 0.0
    psi_model: float = 0.0


@dataclass
class HptRow:
    name: str
    s_c: float
    te_s: float
    s_h: float
    k_h: float
    stagger_deg: float
    alpha1: float
    alpha2: float
    yp: float
    ys: float
    yk: float
    yt: float


def load():
    pub = yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())
    hpt = pub["hpt"]
    st = {x["location"]: x for x in hpt["flowpath"]["stations"]}
    return dict(pub=pub, hpt=hpt, st=st,
                rpm=pub["speeds"]["hp_rpm"] if "speeds" in pub else 12303.0)


def _pitch(station, st):
    x = st[station]
    return 0.5 * (x["r_hub_cm"] + x["r_tip_cm"]) * CM, (x["r_tip_cm"] - x["r_hub_cm"]) * CM, math.pi * ((x["r_tip_cm"] * CM) ** 2 - (x["r_hub_cm"] * CM) ** 2)


def solve(clearance_scale=1.0, uncooled=False, aspect_ratio_scale=1.0, swirl_sign=-1.0):
    """the two stages at pitch. `clearance_scale` 0 gives the tight-clearance
    baseline of Table V; `aspect_ratio_scale` scales the end-wall area term."""
    inp = load_inputs()
    rating = next(r for r in inp.ratings if r.name == "max_climb")
    res = solve_rating(rating, inp)
    s = res.stations
    g = load()
    hpt, st = g["hpt"], g["st"]
    ta = hpt["stage_aerodynamics"]
    bg = hpt["blading_geometry"]
    omega = g["rpm"] * 2 * math.pi / 60
    split = hpt["stage_work_split_stage1"]
    w41, t01, p01 = s["w41"], s["t41"], s["p4"]
    far = res.w_fuel_kg_s / (w41 - res.w_fuel_kg_s)
    dh_total = s["hpt_dh_per_kg"]
    inlet = ("stage1_vane_inlet", "stage1_blade_exit")
    exits = ("stage1_blade_exit", "stage2_blade_exit")
    vane_exits = ("stage1_vane_exit", "stage2_vane_exit")
    stages = []
    h_in = gas.h(t01, far)
    alpha1 = 0.0
    for k in (0, 1):
        n = k + 1
        dh = dh_total * (split if k == 0 else 1 - split)
        r2, h2, a2g = _pitch(vane_exits[k], st)
        r3, h3, a3g = _pitch(exits[k], st)
        u2, u3 = omega * r2, omega * r3
        psi = ta["loading_dh_over_2U2"][k]
        reaction = ta["reaction"][k]
        alpha3 = ta["exit_swirl_deg"][k] * swirl_sign
        # velocity triangles at pitch from loading, reaction and exit swirl.
        # Euler: dh = U (c_t2 + c_t3) with c_t3 the exit swirl against rotation
        # for stage 1 (16 deg swirl into stage 2, same sense as c_t2)... the
        # report's exit swirl is in the direction of rotation, so c_t3 = +.
        ct3 = 0.0
        for _ in range(60):
            ct2 = (dh + u3 * ct3) / u2 if k == 0 else dh / u2 + ct3 * u3 / u2
            cx = ct2 / math.tan(math.radians(90 - 0)) if False else None
            # axial velocity from the stage-exit axial Mach implied by
            # continuity is handled below; first close on c_t3 from swirl
            cx3 = None
            break
        # solve axial velocity by continuity at the vane exit and rotor exit
        def state(t0, p0, area, ct, guess=200.0):
            """axial velocity by continuity on the SUBSONIC branch. Mass flux
            rises with c_x only up to the choking point and falls after it, so
            the bracket is capped at the peak, found by a scan."""
            def flux(cxi):
                c2 = cxi * cxi + ct * ct
                ts = gas.t_from_h(gas.h(t0, far) - 0.5 * c2, far, guess=t0 - c2 / 2400)
                ps = p0 * math.exp(-(gas.phi(t0, far) - gas.phi(ts, far)) / gas.R_AIR)
                return ps / (gas.R_AIR * ts) * cxi * area, ts, ps

            peak_cx, peak_w = 20.0, flux(20.0)[0]
            cxi = 20.0
            while cxi < 900.0:
                cxi += 5.0
                f = flux(cxi)[0]
                if f > peak_w:
                    peak_w, peak_cx = f, cxi
                else:
                    break
            if peak_w < w41:
                raise RuntimeError(f"row cannot pass {w41:.2f} kg/s: max {peak_w:.2f} at c_x {peak_cx:.0f} m/s")
            lo, hi = 5.0, peak_cx
            for _ in range(90):
                cxi = 0.5 * (lo + hi)
                lo, hi = (cxi, hi) if flux(cxi)[0] < w41 else (lo, cxi)
            cxi = 0.5 * (lo + hi)
            _, ts, ps = flux(cxi)
            return cxi, ts, ps

        # Euler with the printed exit swirl: dh = u2 ct2 - u3 ct3 (ct3 opposite)
        # take ct3 from the exit swirl angle and the exit axial velocity
        cx3, ts3, ps3 = state(gas.t_from_h(h_in - sum(x.dh for x in stages) - dh, far, guess=t01 - 200), p01 * 0.5, a3g, 0.0)
        for _ in range(40):
            ct3 = cx3 * math.tan(math.radians(alpha3))
            ct2 = (dh + u3 * ct3) / u2
            cx2, ts2, ps2 = state(t01, p01, a2g, ct2)
            t03 = gas.t_from_h(gas.h(t01, far) - dh, far, guess=t01 - 200)
            p03 = p01 / ta["pressure_ratio"][k]
            cx3n, ts3, ps3 = state(t03, p03, a3g, ct3)
            if abs(cx3n - cx3) < 1e-6:
                cx3 = cx3n
                break
            cx3 = cx3n
        c2 = math.hypot(cx2, ct2)
        w2 = math.hypot(cx2, ct2 - u2)
        w3 = math.hypot(cx3, ct3 - u3)
        beta2 = math.degrees(math.atan2(ct2 - u2, cx2))
        beta3 = math.degrees(math.atan2(ct3 - u3, cx3))
        alpha2 = math.degrees(math.atan2(ct2, cx2))

        def a_of(ts):
            cp = gas.cp(ts, far)
            return math.sqrt(cp / (cp - gas.R_AIR) * gas.R_AIR * ts)

        m2, m2rel = c2 / a_of(ts2), w2 / a_of(ts2)
        m3rel, m3 = w3 / a_of(ts3), math.hypot(cx3, ct3) / a_of(ts3)
        turning = abs(beta2) + abs(beta3)
        # degree of reaction, three definitions
        reaction_kin = 1.0 - (ct2 + ct3) / (2 * u2)
        # ---- losses: vane then blade
        rows = []
        for j, (label, a_in, a_out, sol, teb, ar, r_row, h_row, count, k_h) in enumerate((
                (f"V{n}", alpha1, abs(alpha2), bg["solidity_AW_over_t"][k], bg["te_blockage_pct"][k] / 100, bg["aspect_ratio_h_d0"][k], r2, h2, bg["count"][k], 0.0),
                (f"B{n}", abs(beta2), abs(beta3), bg["solidity_AW_over_t"][2 + k], bg["te_blockage_pct"][2 + k] / 100, bg["aspect_ratio_h_d0"][2 + k], r3, h3, bg["count"][2 + k],
                 ta["tip_clearance_pct"][k] / 100 * clearance_scale))):
            pitch = 2 * math.pi * r_row / count
            # solidity is axial width over pitch; stagger from the turning
            stagger = 0.5 * (a_in + a_out)
            chord = sol * pitch / math.cos(math.radians(stagger))
            s_c = pitch / chord
            te_s = teb * math.cos(math.radians(a_out))     # Table IV's blockage is t_e/(s cos a2)
            sp = L.sp290_row_total_loss(a_in, a_in, a_out, s_c, 0.20, te_s,
                                        pitch / h_row * aspect_ratio_scale, stagger, k_h, shrouded=False)
            rows.append(HptRow(label, s_c, te_s, pitch / h_row, k_h, stagger, a_in, a_out, sp["yp"], sp["ys"], sp["yk"], sp["yt"]))
        # pressures from the losses
        yv, yb = rows[0].yt, rows[1].yt
        _, r2s, _, _ = static_state(t01, 1.0, m2, far)
        p02 = p01 / (1 + yv * (1 - r2s))
        ps2 = p02 * r2s
        h02rel = gas.h(ts2, far) + 0.5 * w2 * w2
        t02rel = gas.t_from_h(h02rel, far, guess=ts2 + 30)
        p02rel = ps2 * math.exp((gas.phi(t02rel, far) - gas.phi(ts2, far)) / gas.R_AIR)
        h03rel = h02rel - 0.5 * (u2 * u2 - u3 * u3)
        t03rel = gas.t_from_h(h03rel, far, guess=t02rel)
        p03rel_i = p02rel * math.exp((gas.phi(t03rel, far) - gas.phi(t02rel, far)) / gas.R_AIR)
        _, r3s, _, _ = static_state(t03rel, 1.0, m3rel, far)
        p03rel = p03rel_i / (1 + yb * (1 - r3s))
        ps3b = p03rel * r3s
        p03_loss = ps3b * math.exp((gas.phi(t03, far) - gas.phi(ts3, far)) / gas.R_AIR)
        t03s = gas.t_from_phi(gas.phi(t01, far) - gas.R_AIR * math.log(p01 / p03_loss), far, guess=t03)
        eta = dh / (gas.h(t01, far) - gas.h(t03s, far))
        reaction_h = (gas.h(ts2, far) - gas.h(ts3, far)) / dh
        reaction_p = (ps2 - ps3) / (p01 - ps3)
        st_obj = HptStage(n, dh, u2, r2, psi, reaction, abs(alpha2), abs(beta2), abs(beta3), abs(alpha3),
                          m2, m2rel, m3rel, m3, turning, t01, p01, t03, p03_loss, eta, rows)
        st_obj.reaction_kin = reaction_kin
        st_obj.reaction_h = reaction_h
        st_obj.reaction_p = reaction_p
        st_obj.psi_model = dh / (2 * u2 * u2)
        stages.append(st_obj)
        t01, p01, alpha1 = t03, p03_loss, abs(alpha3)
    t05s = gas.t_from_phi(gas.phi(s["t41"], far) - gas.R_AIR * math.log(s["p4"] / p01), far, guess=t01)
    eta_tt = dh_total / (h_in - gas.h(t05s, far))
    re_mean = None
    return res, g, stages, dict(eta_tt=eta_tt, pr=s["p4"] / p01, pr_cycle=res.hpt_pr, dh_total=dh_total)


def table_v_decomposition():
    """HPT report Table V prices the tip-clearance and aspect-ratio debits
    separately against a stated tight-clearance baseline. Only the first is
    directly comparable: Table V's aspect-ratio line is a difference from an
    unstated baseline turbine, not the whole end-wall loss (finding 3)."""
    _, _, _, tight = solve(clearance_scale=0.0)
    _, _, _, actual = solve()
    _, _, _, no_endwall = solve(clearance_scale=0.0, aspect_ratio_scale=0.0)
    return dict(tip_clearance_points=(tight["eta_tt"] - actual["eta_tt"]) * 100,
                end_wall_points=(no_endwall["eta_tt"] - tight["eta_tt"]) * 100,
                tight=tight["eta_tt"], actual=actual["eta_tt"], no_endwall=no_endwall["eta_tt"])


if __name__ == "__main__":
    res, g, stages, summ = solve()
    pub = g["hpt"]
    ta = pub["stage_aerodynamics"]
    tb = pub["preliminary_trade"]["two_stage"]
    print(f"{'st':<3}{'U':>7}{'r_p cm':>8}{'psi':>7}{'pub':>6}{'R':>7}{'pub':>6}{'a2':>7}{'b2':>7}{'b3':>7}{'a3':>6}{'turn':>7}{'pub':>5}{'M2':>7}{'pub':>6}{'M3r':>7}{'pub':>6}{'M3':>7}{'pub':>6}{'eta':>8}")
    for i, st in enumerate(stages):
        pt = tb[f"stage{i + 1}"]
        print(f"{st.n:<3}{st.u:>7.1f}{st.r_pitch * 100:>8.2f}{st.psi_model:>7.3f}{ta['loading_dh_over_2U2'][i]:>6.2f}{st.reaction_kin:>7.3f}{ta['reaction'][i]:>6.2f}"
              f"{st.alpha2:>7.1f}{st.beta2:>7.1f}{st.beta3:>7.1f}{st.alpha3:>6.1f}{st.turning:>7.1f}{pt['turning_deg']:>5}"
              f"{st.m2:>7.3f}{pt['vane_exit_M']:>6}{st.m3rel:>7.3f}{pt['blade_exit_M']:>6}{st.m3:>7.3f}{ta['exit_mach'][i]:>6}{st.eta_tt:>8.4f}")
    print(f"\n{'row':<5}{'s/c':>7}{'te/s':>7}{'s/h':>7}{'k/h':>7}{'stag':>7}{'a1':>7}{'a2':>7}{'Yp':>8}{'Ys':>8}{'Yk':>8}{'Yt':>8}")
    for st in stages:
        for r in st.rows:
            print(f"{r.name:<5}{r.s_c:>7.3f}{r.te_s:>7.3f}{r.s_h:>7.3f}{r.k_h:>7.4f}{r.stagger_deg:>7.1f}{r.alpha1:>7.1f}{r.alpha2:>7.1f}{r.yp:>8.4f}{r.ys:>8.4f}{r.yk:>8.4f}{r.yt:>8.4f}")
    d = table_v_decomposition()
    ev = pub["efficiency_estimate"]
    print(f"\nHPT eta_tt {summ['eta_tt']:.4f}; PR {summ['pr']:.3f} vs cycle {summ['pr_cycle']:.3f}")
    print(f"Table V decomposition (points of efficiency):")
    print(f"  tip clearance  model {d['tip_clearance_points']:+.2f}  Table V {ev['corrections_pct']['tip_clearance']:+.2f}")
    print(f"  whole end wall model {d['end_wall_points']:+.2f}  (Table V's aspect-ratio line {ev['corrections_pct']['aspect_ratio']:+.2f} is a delta from an unstated baseline turbine, not the whole end-wall loss)")
    print(f"  tight-clearance, no end wall {d['no_endwall']:.4f}; tight clearance {d['tight']:.4f}; as designed {d['actual']:.4f}")
    print(f"published: Table V net {ev['net_efficiency_pct']}, base {ev['base_aerodynamic_tight_clearance_pct']}; rig {pub['efficiency_chronology']['warm_air_turbine_rig_pct']}; Table XI {pub['efficiency_chronology']['fps_table_xi_pct']}")

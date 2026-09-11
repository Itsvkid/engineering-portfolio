"""Stage L: ME TF0.01 -- a higher-bypass derivative of the E3, on a fixed core.

NOT the E3, and not Stage K's growth engine. Stage K is GE's own machine
pushed harder -- higher T41, T3 and speed -- and every number in it is read
from the reports. This is a DERIVATIVE: the same core at the same turbine
temperature with a bigger fan, and nothing in the reports describes it.
Every number this module produces is derived or assumed. See STEP0.md.

The physical closure is the mixer. A mixed-flow engine runs only if the
core reaches the mixing plane near the bypass total pressure, so at every
bypass ratio the fan pressure ratio is SOLVED to hold the E3's own p5/p13
rather than chosen. Take that constraint away and the LP turbine can be
asked for any expansion at all.

Run:  cd solvers && python -m derivative.tf001
"""
from __future__ import annotations

import csv
import dataclasses
import math
import pathlib
from dataclasses import dataclass

from e3cycle import cycle, gas

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

# ── design rules, fixed in step 0 and not adjusted afterwards ─────────────
M_REL_CEILING = 1.45        # band 4: the most this fan family is asked for
MAX_EXTRA_LPT_STAGES = 1    # "sensible" = at most one stage more than the E3
FPR_BRACKET = (1.05, 1.90)  # band 2: a physical fan pressure ratio

# ── published constants, each with its source ────────────────────────────
SPEC_FLOW = 208.9      # kg/s.m2 corrected, CR-165148 Table IV p.47
RADIUS_RATIO = 0.342   # CR-168219 sec 5.1.1 p.41
N_E3_RPM = 3539.0      # LP physical speed at max climb, CR-165148 Table III p.46
DH_LPT_TABLE_II = 353.8e3   # J/kg: the five printed energy extractions, LPT Table II p.16
RHO_TI = 4430.0        # kg/m3, Ti-6Al-4V (fan blade material, CR-165148 Table V)


def _lpt_pitch_radii():
    """The five LPT rotor pitch radii, in metres, from data/lpt-flowpath.csv,
    which unit A3 derived from the transcribed airfoil coordinates. Each
    rotor's LE and TE are averaged."""
    rows = {}
    with open(DATA / "lpt-flowpath.csv") as f:
        for rec in csv.DictReader(l for l in f if not l.startswith("#")):
            if rec["row"].startswith("R"):
                rows.setdefault(rec["row"], []).append(float(rec["r50_in"]) * 0.0254)
    return {k: sum(v) / len(v) for k, v in sorted(rows.items())}


LPT_R_PITCH = _lpt_pitch_radii()
LPT_RMEAN_SQ = sum(r ** 2 for r in LPT_R_PITCH.values()) / len(LPT_R_PITCH)


def e3_mean_stage_loading():
    """The loading limit, MEASURED on the E3 rather than chosen: Table II's
    five printed energy extractions over five stages at the mean of the five
    pitch speeds. Band 3 requires that feeding this number back through
    stages_needed() returns the E3's own five stages."""
    u_sq = (N_E3_RPM * 2 * math.pi / 60) ** 2 * LPT_RMEAN_SQ
    return DH_LPT_TABLE_II / 5 / (2 * u_sq)


LOADING_LIMIT = e3_mean_stage_loading()


def stages_needed(dh_lpt, rpm, loading=None):
    """LPT stages to absorb dh_lpt at this shaft speed, at the E3's own mean
    stage loading and the E3's own pitch radius. Not rounded -- the caller
    decides, and the fractional value is what band 3 checks."""
    u_sq = (rpm * 2 * math.pi / 60) ** 2 * LPT_RMEAN_SQ
    return dh_lpt / (2 * (loading or LOADING_LIMIT) * u_sq)


def rpm_for_stages(dh_lpt, n, loading=None):
    """The inverse: the shaft speed n stages need. This is the LPT's demand,
    and it is the half of the conflict the fan does not get a say in."""
    return math.sqrt(dh_lpt / (n * 2 * (loading or LOADING_LIMIT) * LPT_RMEAN_SQ)) * 60 / (2 * math.pi)


# ── the fan face: a specific flow and a tip speed are a velocity triangle ──
def _axial_mach(spec_flow=SPEC_FLOW):
    """The axial Mach a corrected specific flow implies, real gas, no swirl.
    Same routine unit 6 used to reproduce the printed 1.41 to 0.005."""
    lo, hi = 0.05, 1.0
    for _ in range(90):
        m = 0.5 * (lo + hi)
        ts = 288.15
        for _ in range(20):
            cp = gas.cp(ts)
            ts = 288.15 / (1 + 0.5 * (cp / (cp - gas.R_AIR) - 1) * m * m)
        cp = gas.cp(ts)
        g = cp / (cp - gas.R_AIR)
        ps = 101325.0 * math.exp(-(gas.phi(288.15) - gas.phi(ts)) / gas.R_AIR)
        flux = ps / (gas.R_AIR * ts) * m * math.sqrt(g * gas.R_AIR * ts)
        lo, hi = (m, hi) if flux < spec_flow else (lo, m)
    m = 0.5 * (lo + hi)
    ts = 288.15
    for _ in range(30):
        cp = gas.cp(ts)
        ts = 288.15 / (1 + 0.5 * (cp / (cp - gas.R_AIR) - 1) * m * m)
    cp = gas.cp(ts)
    return m, math.sqrt(cp / (cp - gas.R_AIR) * gas.R_AIR * ts)


M_AXIAL, A_SOUND = _axial_mach()


def tip_relative_mach(u_tip_corrected):
    """M_rel at the fan tip from the CORRECTED tip speed and the corrected
    sound speed. Reproduces the published 1.41 at the E3's 411.5 m/s."""
    return math.hypot(M_AXIAL, u_tip_corrected / A_SOUND)


def fan_radius(w2_corrected, spec_flow=SPEC_FLOW, rr=RADIUS_RATIO):
    return math.sqrt(w2_corrected / spec_flow / (math.pi * (1 - rr ** 2)))


def blade_root_stress(annulus_m2, rpm, rho=RHO_TI):
    """Untapered root centrifugal stress, sigma = 1.745e-3 rho A N^2 [Pa].
    A real tapered fan blade is 0.55-0.7 of this; the ratio is what matters
    here, not the level."""
    return 1.745e-3 * rho * annulus_m2 * rpm ** 2


# ── the cycle excursion ───────────────────────────────────────────────────
@dataclass
class Point:
    bpr: float
    hub_mode: str
    fpr_bypass: float
    fpr_hub: float
    opr: float
    sfc: float
    dsfc_pct: float
    thrust_N: float
    w2_kg_s: float
    w2_corrected_kg_s: float
    w_core_kg_s: float
    fan_diameter_m: float
    fan_annulus_m2: float
    lpt_dh_J_kg: float
    lpt_pr: float
    t5_K: float
    p5_over_p13: float
    fpr_at_bracket_end: bool


class Excursion:
    """The fixed-core bypass-ratio sweep. Construction runs the E3 baseline
    once; every swept point is solved against it."""

    def __init__(self):
        self.inp = cycle.load_inputs()
        self.base_rating = next(r for r in self.inp.ratings if r.name == "max_climb")
        self.base = cycle.solve_rating(self.base_rating, self.inp)
        self.w25_corrected = self._w25c(self.base)
        self.transition_loss = self.base.transition_loss
        self.mixer_target = self.base.p5_over_p13
        self.hub_scale = self.base_rating.fpr_hub / self.base_rating.fpr_bypass

    @staticmethod
    def _w25c(res):
        s = res.stations
        return res.w_core_kg_s * math.sqrt(s["t25"] / 288.15) / (s["p25"] / 101325.0)

    def _solve(self, bpr, fpr_bypass, hub_mode):
        """One point at a given fan pressure ratio, with the physical core
        flow iterated so that CORRECTED W25 matches the baseline."""
        fpr_hub = fpr_bypass * self.hub_scale if hub_mode == "scaled" else self.base_rating.fpr_hub
        opr = fpr_hub * (1 - self.transition_loss) * self.base_rating.hpc_pr
        r = dataclasses.replace(self.base_rating, bpr=bpr, fpr_bypass=fpr_bypass,
                                fpr_hub=fpr_hub, opr=opr)
        w2 = self.base.w2_kg_s * (1 + bpr) / (1 + self.base_rating.bpr)
        for _ in range(80):
            res = cycle.solve(r, self.inp, w2=w2)
            f = self.w25_corrected / self._w25c(res)
            w2 *= f
            if abs(f - 1) < 1e-12:
                break
        else:
            raise RuntimeError(f"core flow did not converge at BPR {bpr}")
        return cycle.solve(r, self.inp, w2=w2)

    def match_mixer(self, bpr, hub_mode="held"):
        """Solve the fan pressure ratio that puts the core and bypass streams
        at the E3's own p5/p13. Returns (fpr, result, hit_bracket_end)."""
        lo, hi = FPR_BRACKET
        for _ in range(80):
            m = 0.5 * (lo + hi)
            if self._solve(bpr, m, hub_mode).p5_over_p13 > self.mixer_target:
                lo = m
            else:
                hi = m
        fpr = 0.5 * (lo + hi)
        at_end = (fpr - FPR_BRACKET[0] < 1e-3) or (FPR_BRACKET[1] - fpr < 1e-3)
        return fpr, self._solve(bpr, fpr, hub_mode), at_end

    def point(self, bpr, hub_mode="held"):
        fpr, res, at_end = self.match_mixer(bpr, hub_mode)
        s = res.stations
        w2c = res.w2_corrected_kg_s
        rt = fan_radius(w2c)
        return Point(
            bpr=bpr, hub_mode=hub_mode, fpr_bypass=fpr,
            fpr_hub=fpr * self.hub_scale if hub_mode == "scaled" else self.base_rating.fpr_hub,
            opr=(fpr * self.hub_scale if hub_mode == "scaled" else self.base_rating.fpr_hub)
                * (1 - self.transition_loss) * self.base_rating.hpc_pr,
            sfc=res.sfc_kg_N_h,
            dsfc_pct=100 * (res.sfc_kg_N_h / self.base.sfc_kg_N_h - 1),
            thrust_N=res.fn_N, w2_kg_s=res.w2_kg_s, w2_corrected_kg_s=w2c,
            w_core_kg_s=res.w_core_kg_s, fan_diameter_m=2 * rt,
            fan_annulus_m2=w2c / SPEC_FLOW,
            lpt_dh_J_kg=s["lpt_dh_per_kg"], lpt_pr=res.lpt_pr, t5_K=s["t5"],
            p5_over_p13=res.p5_over_p13, fpr_at_bracket_end=at_end)

    def sweep(self, bprs=(6.7, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0), hub_mode="held"):
        return [self.point(b, hub_mode) for b in bprs]

    # ── the result worth having: the fan and the LPT want different speeds ─
    def shaft_speed_conflict(self, p, n_stages_target=5):
        """At one swept point, the LP shaft speed the LPT wants and the speed
        the FAN wants, and the ratio between them -- which is the gearbox
        ratio if you decide to stop compromising."""
        theta = self.base.stations["t0"] / 288.15
        rt = p.fan_diameter_m / 2
        n_lpt = rpm_for_stages(p.lpt_dh_J_kg, n_stages_target)
        # The fan's own preference: hold the E3's tip loading psi = dh / U_tip^2.
        # FRAME DISCIPLINE (unit 15's error 2, one discipline over): psi is
        # frame-invariant only if dh and U are in the SAME frame. The published
        # 411.5 m/s is a CORRECTED tip speed and the cycle's dh is PHYSICAL, so
        # mixing them reads psi low by exactly theta -- 0.274 against 0.306.
        sb = self.base.stations
        u_tip_e3_physical = 411.5 * math.sqrt(theta)
        psi_e3 = (gas.h(sb["t13"]) - gas.h(sb["t0"])) / u_tip_e3_physical ** 2
        dh_fan = gas.h(self._solve(p.bpr, p.fpr_bypass, p.hub_mode).stations["t13"]) - gas.h(sb["t0"])
        u_fan_physical = math.sqrt(dh_fan / psi_e3)
        u_fan_corr = u_fan_physical / math.sqrt(theta)
        n_fan = u_fan_physical / rt * 60 / (2 * math.pi)
        return dict(bpr=p.bpr, n_lpt_rpm=n_lpt, n_fan_rpm=n_fan,
                    gear_ratio=n_lpt / n_fan, stages=n_stages_target,
                    fan_u_tip_corrected=u_fan_corr, fan_m_rel=tip_relative_mach(u_fan_corr),
                    fan_psi=psi_e3)

    def architecture(self, p, n_stages):
        """What an n-stage direct-drive LPT costs the fan at this bypass ratio.
        The shaft speed is set by the TURBINE; the fan has to live with it."""
        theta = self.base.stations["t0"] / 288.15
        rt = p.fan_diameter_m / 2
        rpm = rpm_for_stages(p.lpt_dh_J_kg, n_stages)
        u_tip_corr = rpm * 2 * math.pi / 60 * rt / math.sqrt(theta)
        return dict(bpr=p.bpr, stages=n_stages, rpm=rpm,
                    u_tip_corrected=u_tip_corr, m_rel_tip=tip_relative_mach(u_tip_corr),
                    root_stress_Pa=blade_root_stress(p.fan_annulus_m2, rpm),
                    within_ceiling=tip_relative_mach(u_tip_corr) <= M_REL_CEILING)

    def largest_direct_drive_bpr(self, hub_mode="held", ceiling=M_REL_CEILING,
                                 max_extra_stages=MAX_EXTRA_LPT_STAGES, hi=10.0):
        """'Sensible' is defined before it is computed (step 0 band 4): the fan
        tip relative Mach must stay at or under `ceiling`, and the LPT may have
        at most `max_extra_stages` more than the E3's five. Bisect on BPR."""
        n_max = 5 + max_extra_stages
        lo = 6.7
        if not self.architecture(self.point(lo, hub_mode), n_max)["within_ceiling"]:
            return None
        if self.architecture(self.point(hi, hub_mode), n_max)["within_ceiling"]:
            return hi
        for _ in range(30):
            mid = 0.5 * (lo + hi)
            if self.architecture(self.point(mid, hub_mode), n_max)["within_ceiling"]:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)

    def booster_check(self, p):
        """Does the quarter stage survive a lower fan hub pressure ratio?

        The fan hub and the bypass are the same rotor, so if the bypass
        pressure ratio falls the hub's falls with it -- and holding the core
        supercharged then falls to the booster. Loading is taken at the pitch
        radius, which is where the work is done."""
        # Table IV's 261.1 m/s booster tip speed is CORRECTED, so the enthalpy
        # rises it is compared against must be corrected too -- which means
        # evaluating them at the standard-day inlet, not the max-climb fan face.
        # Same frame rule as shaft_speed_conflict.
        t2 = 288.15
        # E3 as built: fan hub region PR 1.46 (CR-165148 Fig 2), booster 1.129 (Table IV)
        t_hub_e3, _ = gas.compress(t2, 101325.0, 1.46, 0.910)
        dh_boost_e3 = gas.h(gas.compress(t_hub_e3, 101325.0, 1.129, 0.904)[0]) - gas.h(t_hub_e3)
        rr_pitch = (1 + 0.782) / 2       # booster inlet radius ratio, Table IV
        u_pitch_e3 = 261.1 * rr_pitch    # booster tip speed 261.1 m/s, Table IV
        psi_e3 = dh_boost_e3 / u_pitch_e3 ** 2

        # the derivative: the fan hub does less work in the same ratio as the bypass
        dh_hub_e3 = gas.h(t_hub_e3) - gas.h(t2)
        scale = ((gas.h(gas.compress(t2, 101325.0, p.fpr_bypass, 0.910)[0]) - gas.h(t2))
                 / (gas.h(gas.compress(t2, 101325.0, self.base_rating.fpr_bypass, 0.910)[0]) - gas.h(t2)))
        dh_hub = dh_hub_e3 * scale
        t_hub = gas.t_from_h(gas.h(t2) + dh_hub, guess=t2 + dh_hub / 1005)
        pr_hub = math.exp((gas.phi(gas.t_from_h(gas.h(t2) + 0.910 * dh_hub, guess=t2)) - gas.phi(t2)) / gas.R_AIR)
        pr_needed = self.base_rating.fpr_hub / pr_hub
        dh_needed = gas.h(gas.compress(t_hub, 101325.0, pr_needed, 0.90)[0]) - gas.h(t_hub)
        return dict(bpr=p.bpr, e3_pitch_loading=psi_e3, booster_pr_needed=pr_needed,
                    booster_dh_J_kg=dh_needed, fan_hub_pr=pr_hub,
                    loading_if_one_stage=None, stages_at_psi_040=None)

    def booster_loading(self, p, n_stages_lpt):
        """The booster's pitch loading in the derivative, at the shaft speed the
        LPT forces and a booster tip diameter scaled with the fan."""
        b = self.booster_check(p)
        theta = self.base.stations["t0"] / 288.15   # -> corrected tip speed, to match Table IV
        rpm = rpm_for_stages(p.lpt_dh_J_kg, n_stages_lpt)
        d_tip = 1.338 * p.fan_diameter_m / (2 * fan_radius(self.base.w2_corrected_kg_s))
        u_tip = rpm / math.sqrt(theta) * 2 * math.pi / 60 * d_tip / 2
        u_pitch = u_tip * (1 + 0.782) / 2
        b["booster_tip_diameter_m"] = d_tip
        b["loading_if_one_stage"] = b["booster_dh_J_kg"] / u_pitch ** 2
        b["stages_at_psi_040"] = b["booster_dh_J_kg"] / (0.40 * u_pitch ** 2)
        return b

    def fan_efficiency_sensitivity(self, bpr=10.0, delta=-0.01, hub_mode="held"):
        """What a point of fan efficiency is worth in sfc -- the price of the
        step-0 assumption that the E3's fan efficiencies survive a different
        pressure ratio and a different tip Mach."""
        ref = self.point(bpr, hub_mode)
        saved = self.inp
        try:
            self.inp = dataclasses.replace(saved, comp={
                **saved.comp,
                "fan_bypass_efficiency": saved.comp["fan_bypass_efficiency"] + delta,
                "fan_hub_efficiency": saved.comp["fan_hub_efficiency"] + delta})
            got = self.point(bpr, hub_mode)
        finally:
            self.inp = saved
        return dict(bpr=bpr, delta_eta=delta, sfc_ref=ref.sfc, sfc_perturbed=got.sfc,
                    dsfc_pct=100 * (got.sfc / ref.sfc - 1),
                    pct_sfc_per_point=100 * (got.sfc / ref.sfc - 1) / (abs(delta) * 100))

    def core_invariants(self, p):
        res = self._solve(p.bpr, p.fpr_bypass, p.hub_mode)
        s = res.stations
        return dict(w25_corrected=self._w25c(res), t25=s["t25"], p25=s["p25"],
                    t3=s["t3"], t41=s["t41"], w_fuel=res.w_fuel_kg_s,
                    w_core=res.w_core_kg_s)


def main():
    ex = Excursion()
    b = ex.base
    print("ME TF0.01 -- a higher-bypass derivative of the E3 on a FIXED CORE.")
    print("DERIVED, not E3 data. Max climb only; no off-design re-match. See STEP0.md.\n")
    print(f"loading limit measured on the E3: dh/2U^2 = {LOADING_LIMIT:.3f} "
          f"over 5 stages at pitch radius {math.sqrt(LPT_RMEAN_SQ):.4f} m")
    print(f"E3 baseline: sfc {b.sfc_kg_N_h:.5f} kg/N.h, mixer p5/p13 {ex.mixer_target:.4f}, "
          f"axial Mach {M_AXIAL:.4f}\n")

    print(f"{'BPR':>5} {'FPR':>6} {'OPR':>6} {'Dfan m':>7} {'sfc':>8} {'dsfc%':>7} "
          f"{'Fn kN':>7} {'LPT kJ/kg':>9} {'lptPR':>6} {'stages@3539':>11} {'p5/p13':>7}")
    pts = ex.sweep()
    for p in pts:
        n = stages_needed(p.lpt_dh_J_kg, N_E3_RPM)
        print(f"{p.bpr:5.1f} {p.fpr_bypass:6.3f} {p.opr:6.2f} {p.fan_diameter_m:7.3f} "
              f"{p.sfc:8.5f} {p.dsfc_pct:+7.2f} {p.thrust_N/1e3:7.2f} {p.lpt_dh_J_kg/1e3:9.1f} "
              f"{p.lpt_pr:6.3f} {n:11.2f} {p.p5_over_p13:7.4f}")

    print(f"\nThe fan/LPT shaft-speed conflict (the result worth having):")
    for p in (pts[0], pts[-1]):
        c = ex.shaft_speed_conflict(p)
        print(f"  BPR {p.bpr:4.1f}: LPT wants {c['n_lpt_rpm']:.0f} rpm for 5 stages, "
              f"fan wants {c['n_fan_rpm']:.0f} rpm at its own loading -> ratio {c['gear_ratio']:.3f}")

    print(f"\nDirect-drive architectures at BPR 10 (shaft speed set by the turbine):")
    p10 = pts[-1]
    for n in (5, 6, 7, 8):
        a = ex.architecture(p10, n)
        print(f"  {n} LPT stages: {a['rpm']:6.0f} rpm, fan U_tip {a['u_tip_corrected']:6.1f} m/s, "
              f"M_rel {a['m_rel_tip']:5.2f} {'OK ' if a['within_ceiling'] else 'OVER'} "
              f"(ceiling {M_REL_CEILING}), root sigma {a['root_stress_Pa']/1e6:.0f} MPa")

    best = ex.largest_direct_drive_bpr()
    print(f"\nLargest sensible direct-drive BPR (M_rel <= {M_REL_CEILING}, "
          f"<= {5+MAX_EXTRA_LPT_STAGES} LPT stages): {best:.2f}" if best else "\nno sensible point")

    bc = ex.booster_loading(p10, 7)
    print(f"\nThe quarter-stage booster at BPR {p10.bpr}:")
    print(f"  fan hub PR falls to {bc['fan_hub_pr']:.3f}, so the booster must make "
          f"{bc['booster_pr_needed']:.3f} to hold 1.70")
    print(f"  pitch loading {bc['e3_pitch_loading']:.3f} (E3) -> {bc['loading_if_one_stage']:.3f}; "
          f"{bc['stages_at_psi_040']:.2f} stages at psi 0.40")

    s = ex.fan_efficiency_sensitivity()
    print(f"\nThe price of the held-efficiency assumption: 1 point of fan efficiency "
          f"= {s['pct_sfc_per_point']:.2f} % of sfc")


if __name__ == "__main__":
    main()

"""The E3 mixed-flow cycle, station by station: real gas, the Table XI
secondary-air streams, the mixer and the C-D nozzle. Inputs only from
the data files. STEP0.md carries the validation cases and assumptions.

Station numbering (SAE ARP 755): 0 free stream, 2 fan face, 13 bypass
after the fan, 25 HPC inlet, 3 HPC exit, 4 combustor exit, 41 HPT rotor
inlet (after the nonchargeable coolant), 45 HPT exit, 5 LPT exit,
6 mixing plane, 8 nozzle throat, 9 nozzle exit."""
from __future__ import annotations

import math
import pathlib
from dataclasses import dataclass, field

import yaml

from . import gas

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
LHV = 43.124e6      # J/kg fuel (18,540 Btu/lb), STEP0 assumption
# CR-168219 sec 4.4 p.33: each rating is solved on its flat-rating day, the
# day Table XII's T41 is quoted at (+10 C climb and cruise, +15 C takeoff).
# Table XII's sfc column is standard day; see STEP0.md, finding 2.
RATING_CONDITIONS = {"max_climb": (10668.0, 0.80, 10.0), "max_cruise": (10668.0, 0.80, 10.0), "takeoff": (0.0, 0.0, 15.0)}


def isa(altitude_m, delta_t=0.0):
    """ISA troposphere with a day-temperature offset (pressure is standard)."""
    t_std = 288.15 - 0.0065 * altitude_m
    return t_std + delta_t, 101325.0 * (t_std / 288.15) ** 5.2559


@dataclass(frozen=True)
class Rating:
    name: str
    altitude_m: float
    mach: float
    delta_t: float
    bpr: float
    fpr_bypass: float
    fpr_hub: float
    hpc_pr: float
    opr: float
    t41_K: float
    sfc_published: float
    fn_published_N: float | None = None


@dataclass(frozen=True)
class Inputs:
    comp: dict
    cool: dict
    ratings: list
    fan_corrected_kg_s: float
    core_corrected_kg_s: float
    bleed_port_fraction: dict   # stage -> port total pressure / HPC exit total pressure


def load_inputs() -> Inputs:
    pub = yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())
    vd = yaml.safe_load((DATA / "hpc-vector-diagrams.yaml").read_text())

    def stator_exit_pt(stage):
        for r in vd["rows"]:
            if r["row"] == "stator" and r.get("stage") == stage:
                mid = min(r["exit"], key=lambda p: abs(p[1] - 50))
                return mid[4]
        raise KeyError(stage)

    pt_ogv = stator_exit_pt(10)
    bpf = {5: stator_exit_pt(5) / pt_ogv, 7: stator_exit_pt(7) / pt_ogv}
    cyc = pub["cycle_definition"]
    ratings = []
    for name, (alt, mach, dt) in RATING_CONDITIONS.items():
        c = cyc[name]
        ratings.append(Rating(name, alt, mach, dt, c["bypass_ratio"], c["fan_bypass_pressure_ratio"],
                              c["fan_hub_pressure_ratio"], c["compressor_pressure_ratio"], c["overall_pressure_ratio"],
                              c["hpt_rotor_inlet_temperature_K"], c["sfc_kg_per_N_hr"],
                              pub["thrust"]["final_takeoff_N"] if name == "takeoff" else None))
    return Inputs(pub["component_performance"], pub["cooling_flows"], ratings,
                  pub["fan_flow"]["cycle_match_point"]["corrected_flow_kg_s"], pub["size"]["core_inlet_corrected_flow_kg_s"], bpf)


@dataclass
class Result:
    rating: str
    sfc_kg_N_h: float
    sfc_published: float
    fn_N: float
    fg_N: float
    w2_kg_s: float
    w2_corrected_kg_s: float
    w_core_kg_s: float
    w_fuel_kg_s: float
    far_combustor: float
    transition_loss: float
    p5_over_p13: float
    hpt_pr: float
    lpt_pr: float
    ideal_mixing_gain_pct: float
    stations: dict = field(default_factory=dict)


def solve(rating: Rating, inp: Inputs, *, mixed=True, mixer_eff=None, extra_loss=0.0, eta_mech=1.0, w2=None):
    """One rating point. `extra_loss` is an additional fractional total-
    pressure loss on both streams ahead of the mixing plane (negative
    removes the mixer's own loss for a separate-flow comparison)."""
    comp, cool = inp.comp, inp.cool
    tamb, pamb = isa(rating.altitude_m, rating.delta_t)
    v0 = rating.mach * math.sqrt(1.4 * gas.R_AIR * tamb)
    t0 = gas.t_from_h(gas.h(tamb) + 0.5 * v0 ** 2, guess=tamb + 0.5 * v0 ** 2 / 1005)
    p0 = pamb * math.exp((gas.phi(t0) - gas.phi(tamb)) / gas.R_AIR)
    t2, p2 = t0, p0                       # 100 percent ram recovery
    delta, theta = p2 / 101325.0, t2 / 288.15
    if w2 is None:
        w2 = inp.fan_corrected_kg_s * delta / math.sqrt(theta)
    w_core = w2 / (1.0 + rating.bpr)
    w_byp = w2 - w_core

    # fan: two streams, each with its own pressure ratio and efficiency
    t13, p13 = gas.compress(t2, p2, rating.fpr_bypass, comp["fan_bypass_efficiency"])
    t23, p23 = gas.compress(t2, p2, rating.fpr_hub, comp["fan_hub_efficiency"])
    # booster-to-HPC transition duct: the loss the printed OPR implies
    p25 = p2 * rating.opr / rating.hpc_pr
    t25 = t23
    transition_loss = 1.0 - p25 / p23

    # HPC with the two mid-compressor bleed ports
    t3, p3 = gas.compress(t25, p25, rating.hpc_pr, comp["compressor_efficiency"])
    b_nc, b_c = cool["cpd_nonchargeable"], cool["cpd_chargeable"]
    b7, b5 = cool["stage_7_cooling_and_purge"], cool["stage_5_cooling_and_purge"]
    t_port = {s: gas.compress(t25, p25, inp.bleed_port_fraction[s] * rating.hpc_pr, comp["compressor_efficiency"])[0] for s in (5, 7)}
    hpc_power = w_core * ((1 - b5 - b7) * (gas.h(t3) - gas.h(t25))
                          + b5 * (gas.h(t_port[5]) - gas.h(t25)) + b7 * (gas.h(t_port[7]) - gas.h(t25)))

    # combustor: solve the fuel-air ratio so that the nonchargeable coolant
    # (at T3) mixed back in ahead of the rotor gives Table XII's T41
    w_comb = w_core * (1 - b_nc - b_c - b7 - b5)
    w_nc = w_core * b_nc
    p4 = p3 * (1.0 - comp["combustor_pressure_drop"])

    def t41_of(f):
        h4 = (gas.h(t3) + f * comp["combustor_efficiency"] * LHV) / (1 + f)
        t4 = gas.t_from_h(h4, f, guess=1600)
        f41 = w_comb * f / (w_comb + w_nc)
        h41 = (w_comb * (1 + f) * gas.h(t4, f) + w_nc * gas.h(t3)) / (w_comb * (1 + f) + w_nc)
        return gas.t_from_h(h41, f41, guess=t4 - 40), t4, f41

    lo, hi = 0.005, 0.05
    while hi - lo > 1e-10:
        f = 0.5 * (lo + hi)
        t41, t4, f41 = t41_of(f)
        lo, hi = (lo, f) if t41 > rating.t41_K else (f, hi)
    w_fuel = w_comb * f
    w41 = w_comb * (1 + f) + w_nc

    # HPT drives the HPC; chargeable and stage-7 streams rejoin at its exit
    t45, p45 = gas.expand_for_work(t41, p4, hpc_power / (w41 * eta_mech), comp["hpt_efficiency"], f41)
    w45 = w41 + w_core * (b_c + b7)
    f45 = w_fuel / (w45 - w_fuel)
    t45 = gas.t_from_h((w41 * gas.h(t45, f41) + w_core * b_c * gas.h(t3) + w_core * b7 * gas.h(t_port[7])) / w45, f45, guess=t45)

    # LPT drives the fan (both streams, the booster inside the hub ratio)
    fan_power = w_byp * (gas.h(t13) - gas.h(t2)) + w_core * (gas.h(t23) - gas.h(t2))
    t5, p5 = gas.expand_for_work(t45, p45, fan_power / (w45 * eta_mech), comp["lpt_efficiency"], f45)
    w5 = w45 + w_core * b5
    f5 = w_fuel / (w5 - w_fuel)
    t5 = gas.t_from_h((w45 * gas.h(t5, f45) + w_core * b5 * gas.h(t_port[5])) / w5, f5, guess=t5)

    # ducts to the mixing plane (Table XI: both losses are 'duct mixer')
    p6_core = p5 * (1.0 - comp["core_duct_pressure_drop"] - extra_loss)
    p6_byp = p13 * (1.0 - comp["fan_duct_pressure_drop"] - extra_loss)
    p_loss = 1.0 - comp["nozzle_duct_pressure_loss"]
    cv = comp["nozzle_coefficient"]

    def jet(tt, pt, far, w):
        """full expansion to ambient through the C-D nozzle"""
        ts = gas.expand_to_pressure(tt, pt * p_loss, pamb, far)
        return w * cv * math.sqrt(max(2.0 * (gas.h(tt, far) - gas.h(ts, far)), 0.0))

    fg_sep = jet(t5, p6_core, f5, w5) + jet(t13, p6_byp, 0.0, w_byp)
    w6 = w5 + w_byp
    f6 = w_fuel / (w6 - w_fuel)
    t6 = gas.t_from_h((w5 * gas.h(t5, f5) + w_byp * gas.h(t13)) / w6, f6, guess=0.5 * (t5 + t13))
    p6 = (w5 * p6_core + w_byp * p6_byp) / w6          # mass-weighted: ideal mixing
    fg_mix = jet(t6, p6, f6, w6)
    eff = comp["mixer_effectiveness"] if mixer_eff is None else mixer_eff
    fg = fg_sep + eff * (fg_mix - fg_sep) if mixed else fg_sep
    fn = fg - w2 * v0
    return Result(rating.name, w_fuel / fn * 3600.0, rating.sfc_published, fn, fg, w2, w2 * math.sqrt(theta) / delta,
                  w_core, w_fuel, f, transition_loss, p6_core / p6_byp, p4 / p45, p45 / p5,
                  (fg_mix - fg_sep) / fg_sep * 100,
                  dict(t0=t0, p0=p0, t13=t13, p13=p13, t23=t23, p23=p23, t25=t25, p25=p25, t3=t3, p3=p3, t4=t4, p4=p4,
                       t41=t41, t45=t45, p45=p45, t5=t5, p5=p5, t6=t6, p6=p6, w41=w41, w45=w45, w5=w5, w6=w6,
                       hpt_dh_per_kg=hpc_power / (w41 * eta_mech), lpt_dh_per_kg=fan_power / (w45 * eta_mech)))


def solve_rating(rating: Rating, inp: Inputs, **kw):
    """The rating as published: takeoff sized to its printed thrust, the
    others at the fan's corrected match-point flow."""
    r = solve(rating, inp, **kw)
    if rating.fn_published_N is not None:
        r = solve(rating, inp, w2=r.w2_kg_s * rating.fn_published_N / r.fn_N, **kw)
    return r


def run_all(inp: Inputs | None = None):
    inp = inp or load_inputs()
    return [solve_rating(r, inp) for r in inp.ratings]

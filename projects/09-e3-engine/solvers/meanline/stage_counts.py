"""C1 unit 7: derive the stage count of every component from the cycle,
the shaft speeds and a loading limit, then compare with the E3's actual
1 / quarter / 10 / 2 / 5. STEP0.md, unit 7.

The limits are stated in STEP0 before the run and come from the agent's
section 4 (Smith chart / Dixon & Hall ranges), not from the E3."""
from __future__ import annotations

import math
from dataclasses import dataclass

import yaml

from e3cycle import gas
from e3cycle.cycle import DATA, load_inputs, solve_rating
from e3cycle.stations import _csv_rows, find_key

IN, CM = 0.0254, 0.01

# Loading limits, stated before the run. Compressors: psi = dh/U^2 at the
# pitch line. Turbines: the conventional psi = dh/(2 U^2).
LIMITS = dict(fan=0.45, booster=0.45, hpc=0.45, hpt=0.85, lpt=1.75)
LIMIT_SRC = ("compressors psi = dh/U^2 <= 0.45 (Dixon & Hall ch.5, the agent's section 4: 0.3-0.45); "
             "HP turbine psi = dh/2U^2 <= 0.85 and LP <= 1.75 (agent's section 4: turbines 1-2.5, HP lower)")


@dataclass
class Component:
    name: str
    dh: float
    u_pitch: float
    limit: float
    convention: str
    actual: float

    @property
    def per_stage_max(self):
        return self.limit * self.u_pitch ** 2 * (2 if self.convention == "turbine" else 1)

    @property
    def stages_needed(self):
        return self.dh / self.per_stage_max

    @property
    def stages_rounded(self):
        return math.ceil(self.stages_needed - 1e-9)

    @property
    def psi_actual(self):
        d = self.dh / self.actual / self.u_pitch ** 2
        return d / 2 if self.convention == "turbine" else d


def build():
    inp = load_inputs()
    rating = next(r for r in inp.ratings if r.name == "max_climb")
    res = solve_rating(rating, inp)
    s = res.stations
    far = res.w_fuel_kg_s / (s["w41"] - res.w_fuel_kg_s)
    fan = yaml.safe_load((DATA / "fan-design.yaml").read_text())
    pub = yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())
    design = yaml.safe_load((DATA / "lpt-design.yaml").read_text())
    hpc_fp = {(r["row"], r["edge"]): r for r in _csv_rows(DATA / "hpc-flowpath.csv")}
    lpt_fp = {(r["row"], r["edge"]): r for r in _csv_rows(DATA / "lpt-flowpath.csv")}

    n_lp = find_key(design, "case_41_flowpath_and_clearance")["fan_physical_speed_rpm"][0]
    n_hp = 12303.0
    w_lp, w_hp = n_lp * 2 * math.pi / 60, n_hp * 2 * math.pi / 60

    a = fan["aero_parameters"]
    # fan: pitch radius at inlet, work from the bypass temperature ratio
    r_tip_f = a["tip_diameter_cm"][0] / 200
    r_p_f = 0.5 * r_tip_f * (1 + a["radius_ratio_inlet"][0])
    dh_fan = gas.h(288.15 * a["temperature_ratio"][0]) - gas.h(288.15)
    r_tip_b = a["tip_diameter_cm"][1] / 200
    r_p_b = 0.5 * r_tip_b * (1 + a["radius_ratio_inlet"][1])
    dh_boost = gas.h(288.15 * a["temperature_ratio"][1]) - gas.h(288.15)

    # HPC: pitch radius averaged over the machine, work from the cycle
    r_in = 0.5 * (float(hpc_fp[("R1", "LE")]["r_hub_cm"]) + float(hpc_fp[("R1", "LE")]["r_tip_cm"])) * CM
    r_out = 0.5 * (float(hpc_fp[("S10", "TE")]["r_hub_cm"]) + float(hpc_fp[("S10", "TE")]["r_tip_cm"])) * CM
    r_p_c = 0.5 * (r_in + r_out)
    dh_hpc = gas.h(s["t3"]) - gas.h(s["t25"])

    # HPT: pitch radius from Fig 3, work from the cycle
    st = {x["location"]: x for x in pub["hpt"]["flowpath"]["stations"]}
    r_p_hpt = 0.25 * sum(st[k][f"r_{w}_cm"] for k in ("stage1_vane_inlet", "stage2_blade_exit") for w in ("hub", "tip")) * CM
    dh_hpt = s["hpt_dh_per_kg"]

    # LPT: pitch radius averaged over the five stages, work from the cycle
    rs = [float(lpt_fp[(f"R{n}", e)]["r50_in"]) * IN for n in range(1, 6) for e in ("LE", "TE")]
    r_p_lpt = sum(rs) / len(rs)
    dh_lpt = s["lpt_dh_per_kg"]

    return [
        Component("fan", dh_fan, w_lp * r_p_f, LIMITS["fan"], "compressor", 1),
        Component("booster", dh_boost, w_lp * r_p_b, LIMITS["booster"], "compressor", 1),
        Component("HPC", dh_hpc, w_hp * r_p_c, LIMITS["hpc"], "compressor", 10),
        Component("HPT", dh_hpt, w_hp * r_p_hpt, LIMITS["hpt"], "turbine", 2),
        Component("LPT", dh_lpt, w_lp * r_p_lpt, LIMITS["lpt"], "turbine", 5),
    ], dict(n_lp=n_lp, n_hp=n_hp)


if __name__ == "__main__":
    comps, sp = build()
    print(f"LP {sp['n_lp']:.0f} rpm, HP {sp['n_hp']:.0f} rpm")
    print(f"limits: {LIMIT_SRC}\n")
    print(f"{'component':<11}{'dh kJ/kg':>10}{'U_p m/s':>9}{'limit':>7}{'dh/stage':>10}{'needed':>8}{'->':>4}{'actual':>8}{'psi actual':>12}")
    for c in comps:
        print(f"{c.name:<11}{c.dh / 1000:>10.1f}{c.u_pitch:>9.1f}{c.limit:>7.2f}{c.per_stage_max / 1000:>10.1f}"
              f"{c.stages_needed:>8.2f}{c.stages_rounded:>4}{c.actual:>8}{c.psi_actual:>12.3f}")
    print("\nE3 as built: 1 fan, 1/4 booster, 10 HPC, 2 HPT, 5 LPT")

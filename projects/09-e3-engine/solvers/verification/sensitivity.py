"""Stage I2: which assumptions move the answers, one at a time.

I2's bullet: *which assumptions move the sfc, the metal temperature and the
disc stress most -- one-at-a-time, tabulated.*

Every number this project produces rests on inputs of three kinds: values
printed in the reports, values measured from them, and a small number of
handbook constants that are nobody's measurement. The third kind is the one
worth worrying about, and the only way to know how much to worry is to move
each one and watch.

The perturbation is **+1 % of the value**, not a fixed absolute step, so the
results are elasticities: d(ln output)/d(ln input). An elasticity of 1 means
a 1 % error in that input is a 1 % error in the answer. Anything above 1 is
an input the project is more sensitive to than it is to its own accuracy.

Three outputs, one per bullet:

  * **sfc** at max cruise, the cycle's headline number (Stage B)
  * **metal temperature** of the HPT stage-1 blade (Stage D)
  * **disc bore stress**, constant-thickness model (Stage E2)

STEP0.md, unit I2."""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass

STEP = 0.01          # +1 % of the value


@dataclass
class Sensitivity:
    output: str
    parameter: str
    kind: str                 # published | measured | handbook
    base: float
    perturbed: float
    base_output: float
    new_output: float

    @property
    def elasticity(self):
        d_in = (self.perturbed - self.base) / self.base
        if d_in == 0 or self.base_output == 0:
            return 0.0
        return ((self.new_output - self.base_output) / self.base_output) / d_in


# ------------------------------------------------------------------- sfc

SFC_PARAMS = {
    "fan_bypass_efficiency": "published",
    "fan_hub_efficiency": "published",
    "compressor_efficiency": "published",
    "hpt_efficiency": "published",
    "lpt_efficiency": "published",
    "combustor_efficiency": "published",
    "combustor_pressure_drop": "published",
    "fan_duct_pressure_drop": "published",
    "core_duct_pressure_drop": "published",
    "mixer_effectiveness": "published",
    "nozzle_coefficient": "published",
}
SFC_COOL = {
    "cpd_nonchargeable": "published",
    "cpd_chargeable": "published",
    "stage_7_cooling_and_purge": "published",
    "stage_5_cooling_and_purge": "published",
}


def _sfc(inp, rating="max_cruise"):
    from e3cycle import cycle as cyc
    r = cyc.solve_rating(next(x for x in inp.ratings if x.name == rating), inp)
    return r.sfc_kg_N_h


def sfc_sensitivities(rating="max_cruise"):
    from e3cycle.cycle import load_inputs
    base_inp = load_inputs()
    base = _sfc(base_inp, rating)
    out = []
    for key, kind in SFC_PARAMS.items():
        inp = copy.deepcopy(base_inp)
        v = inp.comp[key]
        inp.comp[key] = v * (1 + STEP)
        out.append(Sensitivity(f"sfc {rating}", key, kind, v, v * (1 + STEP),
                               base, _sfc(inp, rating)))
    for key, kind in SFC_COOL.items():
        inp = copy.deepcopy(base_inp)
        v = inp.cool[key]
        inp.cool[key] = v * (1 + STEP)
        out.append(Sensitivity(f"sfc {rating}", key, kind, v, v * (1 + STEP),
                               base, _sfc(inp, rating)))
    return sorted(out, key=lambda s: -abs(s.elasticity))


# ------------------------------------------------------- metal temperature

def metal_temperature_sensitivities():
    """The stage-1 blade's chordwise metal temperature comes from a wall
    balance T_m = (h_g T_aw + H_c T_c) / (h_g + H_c). Four inputs move it:
    the gas-side coefficient the report prints at each chordwise station,
    the internal conductance unit D2 fitted from the published metal
    temperatures, and the gas and coolant temperatures."""
    from thermal.cooling import (blade_conditions, fit_internal_conductance,
                                 stage1_blade_stations)

    stations = stage1_blade_stations()
    t_g0, t_c0, _ = blade_conditions()
    hc0 = fit_internal_conductance(stations)["H_c"]

    def predict(hg=1.0, hc=1.0, tg=1.0, tc=1.0):
        vals = [((s.h_gas * hg) * (t_g0 * tg) + (hc0 * hc) * (t_c0 * tc))
                / (s.h_gas * hg + hc0 * hc) for s in stations]
        return sum(vals) / len(vals)

    base = predict()
    out = []
    for name, kind, kw in (
            ("gas-side coefficient h_g (Fig 23)", "published", dict(hg=1 + STEP)),
            ("internal conductance H_c (fitted, unit D2)", "measured", dict(hc=1 + STEP)),
            ("gas temperature", "published", dict(tg=1 + STEP)),
            ("coolant temperature", "published", dict(tc=1 + STEP))):
        out.append(Sensitivity("HPT stage-1 blade metal temperature", name, kind,
                               1.0, 1 + STEP, base, predict(**kw)))
    return sorted(out, key=lambda s: -abs(s.elasticity))


# ------------------------------------------------------------ disc stress

def disc_stress_sensitivities():
    """The constant-thickness bore stress of unit E2:
    sigma = (3+nu)/4 rho omega^2 [b^2 + (1-nu)/(3+nu) a^2]."""
    from mechanical.disc import NU, RHO_RENE95, hoop_stress_annular, stage1_radii

    _, b, omega = stage1_radii()
    a = 0.15 * b

    def sigma(rho=RHO_RENE95, om=omega, nu=NU, bb=b):
        return hoop_stress_annular(0.15 * bb, 0.15 * bb, bb, rho, om, nu)

    base = sigma()
    out = [
        Sensitivity("HPT disc bore stress", "density (Rene 95, handbook)", "handbook",
                    RHO_RENE95, RHO_RENE95 * (1 + STEP), base,
                    sigma(rho=RHO_RENE95 * (1 + STEP))),
        Sensitivity("HPT disc bore stress", "rotor speed", "published",
                    omega, omega * (1 + STEP), base, sigma(om=omega * (1 + STEP))),
        Sensitivity("HPT disc bore stress", "rim radius", "measured",
                    b, b * (1 + STEP), base, sigma(bb=b * (1 + STEP))),
        Sensitivity("HPT disc bore stress", "Poisson's ratio (handbook)", "handbook",
                    NU, NU * (1 + STEP), base, sigma(nu=NU * (1 + STEP))),
    ]
    return sorted(out, key=lambda s: -abs(s.elasticity))


def all_sensitivities():
    return (sfc_sensitivities() + metal_temperature_sensitivities()
            + disc_stress_sensitivities())


def handbook_exposure():
    """How much of each answer rests on a constant nobody measured."""
    out = {}
    for s in all_sensitivities():
        d = out.setdefault(s.output, dict(handbook=0.0, published=0.0, measured=0.0))
        d[s.kind] += abs(s.elasticity)
    for k, d in out.items():
        tot = sum(d.values())
        d["handbook_share_pct"] = 100 * d["handbook"] / tot if tot else 0.0
    return out


if __name__ == "__main__":
    print("Stage I2: which assumptions move the answers\n")
    print("   elasticity = d(ln output)/d(ln input); 1.0 means a 1 % input error")
    print("   is a 1 % error in the answer\n")
    for title, rows in (("sfc at max cruise", sfc_sensitivities()),
                        ("HPT stage-1 blade metal temperature",
                         metal_temperature_sensitivities()),
                        ("HPT disc bore stress", disc_stress_sensitivities())):
        print(f"   {title}")
        print(f"      {'elasticity':>11}  {'kind':<10} parameter")
        for s in rows:
            if abs(s.elasticity) < 1e-6:
                continue
            print(f"      {s.elasticity:>+11.3f}  {s.kind:<10} {s.parameter}")
        print()
    print("   how much of each answer rests on a handbook constant:")
    for out, d in handbook_exposure().items():
        print(f"      {out:<42}{d['handbook_share_pct']:>6.1f} %")

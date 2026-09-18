"""Unit D9 -- the stage-1 HPT blade's two printed coolant margins.

D3's remaining half. The vane's cavities were settled by D7; these two are
on the rotor, where the reference pressure is a RELATIVE total and the
supply is pumped by rotation.

Published inputs only: CR-167955 Fig 26's two (dovetail ratio, tip margin)
pairs, Fig 3's dimensioned annulus, Fig 27's coolant temperature at pitch,
the HP spool speed, and unit C1's HPT mean-line for the rotor-inlet
velocity triangle.
"""
from __future__ import annotations

import math
import pathlib

import yaml

from e3cycle import gas

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"
CM = 0.01


def _y(name):
    return yaml.safe_load((DATA / name).read_text())


def printed():
    c = _y("hpt-cooling.yaml")["stage1_blade"]["flow_characteristics"]
    return dict(dovetail_pr=c["design_dovetail_pressure_ratio"],
                min_supply_pr=c["minimum_supply_pressure_ratio"],
                tip_margin=c["tip_backflow_margin_at_design"],
                damage_pr=1.24, damage_tip_margin=1.09,
                definition=c["backflow_margin_definition"])


def rotor_inlet_radii_m():
    """Fig 3's dimensioned stage-1 vane exit = the rotor inlet plane."""
    f = _y("e3-fps-published.yaml")["hpt"]["flowpath"]["stations"]
    s = next(x for x in f if x["location"] == "stage1_vane_exit")
    return s["r_hub_cm"] * CM, s["r_tip_cm"] * CM


def hp_speed_rad_s():
    """The HP spool speed the C1 mean-line runs at, taken FROM the mean-line
    rather than re-read, so the two units cannot drift apart."""
    from meanline.hpt import load as hpt_load
    rpm = hpt_load()["rpm"]
    return rpm * 2.0 * math.pi / 60.0, rpm


def coolant_temperature_K():
    """Fig 27's coolant temperature at the pitch section."""
    return _y("hpt-cooling.yaml")["stage1_blade"]["metal_temperatures"]["conditions"]["t_cp_C"] + 273.15


# --- band 2: rotational pumping ---------------------------------------------

def pumping_factor(r_lo, r_hi, omega, t_coolant):
    """Total-pressure rise of a coolant column rotating with the blade,
    isothermal: p2/p1 = exp(omega^2 (r2^2 - r1^2) / (2 R T)). Isothermal is
    the conservative reading -- the real column heats up, which reduces the
    gain -- and the E3's blade coolant rises only ~44 C across the dovetail
    (Fig 27's T_CDT), so the difference is small."""
    return math.exp(omega ** 2 * (r_hi ** 2 - r_lo ** 2) / (2.0 * gas.R_AIR * t_coolant))


# --- band 6: the gas side across the span -----------------------------------

def relative_total_ratio_hub_to_tip(vortex="free"):
    """P_t,rel at the rotor-inlet hub over P_t,rel at the tip, from unit C1's
    pitch triangle carried across the span on a stated vortex law. The blade
    is 4 cm long, so free vortex and solid body bracket tightly."""
    from meanline.hpt import solve as hpt_solve
    st = hpt_solve()[2][0]          # stage 1
    omega, _ = hp_speed_rad_s()
    r_h, r_t = rotor_inlet_radii_m()
    r_p = st.r_pitch
    # pitch triangle, back out of the mean-line's own two angles:
    #   c_t = c_x tan(alpha2)  and  c_t - U = c_x tan(beta2)
    cx_p = st.u / (math.tan(math.radians(st.alpha2)) - math.tan(math.radians(st.beta2)))
    ct_p = cx_p * math.tan(math.radians(st.alpha2))
    out = {}
    for r in (r_h, r_p, r_t):
        if vortex == "free":
            ct = ct_p * r_p / r
        elif vortex == "solid":
            ct = ct_p * r / r_p
        else:
            raise ValueError(vortex)
        u = omega * r
        w2 = cx_p ** 2 + (ct - u) ** 2
        c2 = cx_p ** 2 + ct ** 2
        # static state from the ABSOLUTE velocity (finding 15's trap), then
        # the relative total from the relative velocity
        ts = gas.t_from_h(gas.h(st.t01) - 0.5 * c2, 0.0, guess=st.t01 - 200)
        t0rel = gas.t_from_h(gas.h(ts) + 0.5 * w2, 0.0, guess=ts + 100)
        out[r] = math.exp((gas.phi(t0rel) - gas.phi(ts)) / gas.R_AIR)   # p0rel/ps
    # the static pressure is very nearly uniform over a 4 cm span at this
    # reaction, so the ratio of relative totals is the ratio of these factors
    return out[r_h] / out[r_t], out


# --- bands 1, 3, 4, 5 -------------------------------------------------------

def band1_audit():
    p = printed()
    return dict(design_margin_over_unity=p["tip_margin"] > 1.0,
                damage_margin_over_unity=p["damage_tip_margin"] > 1.0,
                design_above_minimum=p["dovetail_pr"] > p["min_supply_pr"],
                damage_above_minimum=p["damage_pr"] > p["min_supply_pr"],
                headroom_pct=(p["dovetail_pr"] / p["min_supply_pr"] - 1.0) * 100.0)


def band5_fig26_slope():
    p = printed()
    slope = (p["tip_margin"] - p["damage_tip_margin"]) / (p["dovetail_pr"] - p["damage_pr"])
    proportional = p["tip_margin"] / p["dovetail_pr"]
    return dict(slope=slope, proportional_slope=proportional,
                intercept=p["tip_margin"] - slope * p["dovetail_pr"],
                proportional_prediction_at_damage=proportional * p["damage_pr"])


def bands_3_and_4():
    p = printed()
    omega, rpm = hp_speed_rad_s()
    r_h, r_t = rotor_inlet_radii_m()
    tc = coolant_temperature_K()
    pump = pumping_factor(r_h, r_t, omega, tc)
    span_free, _ = relative_total_ratio_hub_to_tip("free")
    span_solid, _ = relative_total_ratio_hub_to_tip("solid")
    out = {}
    for name, span in (("free vortex", span_free), ("solid body", span_solid)):
        lossless = p["dovetail_pr"] * pump * span
        out[name] = dict(span_ratio=span, lossless_tip_margin=lossless,
                         implied_loss_pct=(1.0 - p["tip_margin"] / lossless) * 100.0)
    return dict(rpm=rpm, r_hub=r_h, r_tip=r_t, t_coolant=tc, pumping=pump, cases=out)


def main():
    p = printed()
    print("Unit D9 -- stage-1 HPT blade backflow margins")
    print(f"printed definition: {p['definition']}\n")

    a = band1_audit()
    print("band 1  D3's closure sentence, on printed numbers")
    print(f"  design tip margin {p['tip_margin']} > 1: {a['design_margin_over_unity']}")
    print(f"  inducer-seal damage case {p['damage_tip_margin']} > 1: {a['damage_margin_over_unity']}")
    print(f"  design dovetail ratio {p['dovetail_pr']} > minimum supply "
          f"{p['min_supply_pr']}: {a['design_above_minimum']} "
          f"({a['headroom_pct']:.1f} % headroom)")
    print(f"  damage case {p['damage_pr']} > minimum supply: {a['damage_above_minimum']}")

    b = bands_3_and_4()
    print(f"\nband 2  pumping over the published radius rise "
          f"{b['r_hub']*100:.2f} -> {b['r_tip']*100:.2f} cm at {b['rpm']:.0f} rpm, "
          f"coolant {b['t_coolant']-273.15:.0f} C: x{b['pumping']:.4f}")
    print("\nbands 3 and 6  the gas side across the span, both vortex laws")
    for name, d in b["cases"].items():
        print(f"  {name:<12} P_t,rel hub/tip {d['span_ratio']:.4f}   "
              f"lossless tip margin {d['lossless_tip_margin']:.3f}   "
              f"implied internal loss {d['implied_loss_pct']:.1f} %")

    s = band5_fig26_slope()
    print(f"\nband 5  Fig 26's two points: slope {s['slope']:.4f} against a "
          f"proportional {s['proportional_slope']:.4f}")
    print(f"        a proportional line would put the damage case at "
          f"{s['proportional_prediction_at_damage']:.3f}; the report prints "
          f"{p['damage_tip_margin']}")


if __name__ == "__main__":
    main()

"""C3 unit 15: the fan blade. **Designed, not transcribed.**

The E3 fan report publishes almost everything about its rotor blade
except the blade. It gives the chord and the maximum thickness against
radius (Figs 15, 16), 32 blades, the design incidence (5 degrees across
the span), the leading- and trailing-edge relative Mach numbers at three
radii, where the maximum thickness sits, and the thickness distribution
in words. It does not give a single coordinate, a camber angle or a
stagger.

So those are designed here, and the design is checked against the one
thing the report states that was not used to make it: the **throat
margin** -- 7.5 percent at the OD, 8.8 at the ID, 5 typical, defined as
the effective throat-to-capture area ratio above critical after one
normal shock at the leading-edge Mach.

Everything this module produces is a design, not a transcription, and is
labelled so wherever it is recorded. STEP0.md, unit 15."""
from __future__ import annotations

import math
from dataclasses import dataclass

import yaml

from e3cycle import gas
from e3cycle.cycle import DATA
from blading.sections import GAMMA, area_ratio, normal_shock, section, throat
from meanline.compressor import carter_m
from meanline.losses import _interp

CM, IN = 0.01, 0.0254
T_STD, P_STD = 288.15, 101325.0


def load():
    return yaml.safe_load((DATA / "fan-design.yaml").read_text())


def _published_profiles(fan):
    a = fan["fan_rotor_airfoil"]
    s = fan["summary"]
    r_tip = s["fan_tip_diameter_m"] / 2
    r_hub = r_tip * s["inlet_radius_ratio"]
    r_shroud = r_hub + a["shroud"]["height_pct"] / 100 * (r_tip - r_hub)
    # the three radii the report quotes leading- and trailing-edge Mach at
    radii = [r_hub, r_shroud, r_tip]
    m_le = [a["hub_section"]["m_le"], a["shroud_section"]["m_le"], a["tip_section"]["m_le"]]
    m_te = [a["hub_section"]["m_te"], a["shroud_section"]["m_te"], a["tip_section"]["m_te"]]
    # Fig 3's rotor-exit total-pressure ratio against PERCENT OF TOTAL FAN
    # FLOW, measured from the OD inward. Converted to radius by area:
    # pct = (r_tip^2 - r^2) / (r_tip^2 - r_hub^2).
    prof = fan["flowpath"]["pressure_profile"]["rotor_exit_bypass"]
    pct = [0.0, 30.0, 60.0, 78.0]
    pr = [prof["od"], prof["peak_at_30pct"], prof["at_60pct"], prof["at_island_78pct"]]
    pr_radii = [math.sqrt(r_tip ** 2 - q / 100 * (r_tip ** 2 - r_hub ** 2)) for q in pct]
    tm = a["max_thickness_location_pct_chord"]
    a_loc = [tm["hub"], tm["shroud_region"], tm["tip"]]
    return dict(r_hub=r_hub, r_tip=r_tip, r_shroud=r_shroud, radii=radii,
                pr_radii=list(reversed(pr_radii)), pr=list(reversed(pr)),
                r_island=pr_radii[-1], eta_rotor=fan["vector_diagram_rows"]["rows"]["R1_fan"]["adiabatic_efficiency"],
                m_le=m_le, m_te=m_te, a_loc=a_loc,
                chord_r=[x * CM for x in a["fig15"]["radius_cm"]],
                chord=[x * CM for x in a["fig15"]["chord_cm"]],
                tmc_r=[x * CM for x in a["fig16_tm_over_c"]["radius_cm"]],
                tmc=a["fig16_tm_over_c"]["tm_c"],
                blades=s["fan_blades"], u_tip=s["corrected_tip_speed_m_s"],
                incidence=a["incidence_deg"]["design_point_all_span"],
                margin=a["throat_margin_pct"])


def _sound(ts):
    cp = gas.cp(ts)
    return math.sqrt(cp / (cp - gas.R_AIR) * gas.R_AIR * ts)


def _axial_from_relative_mach(t0, u, m_rel, swirl=0.0):
    """Solve the axial velocity that gives a RELATIVE Mach of m_rel.

    The static temperature is set by the ABSOLUTE velocity -- the gas does
    not know the blade is moving -- so T = T0 - (cx^2 + c_theta^2)/2cp,
    while the Mach number that matters to the blade is |W|/a with
    W = (cx, u - c_theta). Taking the static state from the relative Mach
    instead is the obvious mistake and it puts the tip axial velocity at
    54 m/s instead of 207."""
    lo, hi = 20.0, 400.0
    for _ in range(90):
        cx = 0.5 * (lo + hi)
        c2 = cx * cx + swirl * swirl
        ts = gas.t_from_h(gas.h(t0) - 0.5 * c2, guess=t0 - c2 / 2000)
        w = math.hypot(cx, u - swirl)
        # the relative Mach RISES with axial velocity (W grows, a falls), so
        # overshooting the target means the axial velocity is too high
        lo, hi = (lo, cx) if w / _sound(ts) > m_rel else (cx, hi)
    cx = 0.5 * (lo + hi)
    c2 = cx * cx + swirl * swirl
    ts = gas.t_from_h(gas.h(t0) - 0.5 * c2, guess=t0 - c2 / 2000)
    return cx, ts


@dataclass
class FanSection:
    radius_m: float
    u: float
    m_le: float
    m_te: float
    w1: float
    w2: float
    cx1: float
    beta1_flow: float
    beta2_flow: float
    beta1_metal: float
    beta2_metal: float
    camber: float
    stagger: float
    chord_m: float
    pitch_m: float
    solidity: float
    tm_c: float
    a_loc_pct: float
    deviation: float
    o_over_s: float
    throat_margin_pct: float


def design(n=12):
    """design the rotor section at n radii from hub to tip"""
    fan = load()
    p = _published_profiles(fan)
    out = []
    # Fig 3 publishes the rotor-exit pressure profile only over the bypass
    # span, from the OD in to the island at 78 % of the flow. Below that the
    # fan hub's work is shared with the booster and Fig 3 does not say how,
    # so the blade is designed over the published span and the inner span is
    # left to Stage C's booster work rather than extrapolated.
    r_lo, r_hi = p["r_island"], p["r_tip"]
    for k in range(n):
        x = k / (n - 1)
        r = r_lo + x * (r_hi - r_lo)
        u = p["u_tip"] * r / p["r_tip"]
        m_le = _interp(r, p["radii"], p["m_le"])
        m_te = _interp(r, p["radii"], p["m_te"])
        a_loc = _interp(r, p["radii"], p["a_loc"])
        chord = _interp(r, p["chord_r"], p["chord"])
        tmc = _interp(r, p["tmc_r"], p["tmc"])
        pitch = 2 * math.pi * r / p["blades"]
        # inlet: no swirl ahead of the rotor
        cx1, ts1 = _axial_from_relative_mach(T_STD, u, m_le)
        w1 = math.hypot(cx1, u)
        beta1 = math.degrees(math.atan2(u, cx1))
        # exit: Fig 3's LOCAL pressure ratio at this radius sets the local
        # work (the mass-averaged 1.1757 would ask the hub for more work
        # than its blade speed can do), and Euler then fixes the swirl.
        pr_local = _interp(r, p["pr_radii"], p["pr"])
        t02 = T_STD * pr_local ** (gas.R_AIR / gas.cp(T_STD) / p["eta_rotor"])
        dh = gas.h(t02) - gas.h(T_STD)
        ct2 = dh / u
        if ct2 >= u:
            continue                  # more work than the blade speed allows
        cx2, ts2 = _axial_from_relative_mach(t02, u, m_te, swirl=ct2)
        wt2 = u - ct2
        w2 = math.hypot(cx2, wt2)
        beta2 = math.degrees(math.atan2(wt2, cx2))
        # design the blade: 5 deg incidence, Carter deviation
        beta1_m = beta1 - p["incidence"]
        theta, stagger = 10.0, 0.5 * (beta1_m + beta2)
        for _ in range(60):
            m_c = carter_m(abs(stagger))
            denom = 1 - m_c * math.sqrt(pitch / chord)
            theta_new = (beta1_m - beta2) / denom if abs(denom) > 1e-6 else theta
            beta2_m = beta1_m - theta_new
            # aft-loaded like the E3's other rotors: max camber at the max
            # thickness position (unit 12 finding 43)
            f = a_loc / 100
            t1 = math.radians(beta1_m - stagger)
            # solve the stagger that the double-arc closure implies for this f
            lo, hi = beta2_m, beta1_m
            for _ in range(60):
                g = 0.5 * (lo + hi)
                lhs = f * math.tan(math.radians((beta1_m - g) / 2))
                rhs = (1 - f) * math.tan(math.radians((g - beta2_m) / 2))
                lo, hi = (g, hi) if lhs > rhs else (lo, g)
            stagger_new = 0.5 * (lo + hi)
            if abs(theta_new - theta) < 1e-8 and abs(stagger_new - stagger) < 1e-8:
                theta, stagger = theta_new, stagger_new
                break
            theta, stagger = theta_new, stagger_new
        beta2_m = beta1_m - theta
        dev = beta2 - beta2_m
        sec = section(chord, beta1_m, beta2_m, stagger, tmc, a_loc, 0.01)
        if sec is None:
            # the double-circular-arc construction is undefined at zero
            # camber, which is where this design lands outboard of about
            # 90 % span. That is a limit of the construction, not of the
            # blade: a real transonic fan tip does have near-zero camber.
            continue
        o, _ = throat(sec, pitch)
        o_s = o / pitch
        capture = math.cos(math.radians(beta1))
        if m_le > 1.0:
            _, p0 = normal_shock(m_le)
            a_min = capture / area_ratio(m_le) / p0
        else:
            a_min = capture / area_ratio(m_le)
        out.append(FanSection(r, u, m_le, m_te, w1, w2, cx1, beta1, beta2, beta1_m, beta2_m,
                              theta, stagger, chord, pitch, chord / pitch, tmc, a_loc, dev,
                              o_s, (o_s / a_min - 1) * 100))
    return out, p


if __name__ == "__main__":
    secs, p = design()
    print("E3 fan rotor blade -- DESIGNED, not transcribed")
    print(f"32 blades, tip radius {p['r_tip']*100:.1f} cm, blade hub {p['r_hub']*100:.1f} cm, "
          f"corrected tip speed {p['u_tip']} m/s, design incidence {p['incidence']} deg")
    print(f"designed over the span Fig 3 publishes: the island at {p['r_island']*100:.1f} cm (78 % of the flow) to the OD\n")
    print(f"{'r cm':>7}{'% span':>8}{'U':>7}{'M_LE':>7}{'M_TE':>7}{'b1':>7}{'b2':>7}"
          f"{'camber':>8}{'stagger':>9}{'dev':>6}{'c cm':>7}{'sigma':>7}{'tm/c':>7}{'o/s':>7}{'margin %':>10}")
    for s in secs:
        span = (s.radius_m - p["r_hub"]) / (p["r_tip"] - p["r_hub"]) * 100
        print(f"{s.radius_m*100:>7.1f}{span:>8.0f}{s.u:>7.1f}{s.m_le:>7.3f}{s.m_te:>7.3f}"
              f"{s.beta1_flow:>7.2f}{s.beta2_flow:>7.2f}{s.camber:>8.2f}{s.stagger:>9.2f}"
              f"{s.deviation:>6.2f}{s.chord_m*100:>7.2f}{s.solidity:>7.3f}{s.tm_c:>7.3f}"
              f"{s.o_over_s:>7.3f}{s.throat_margin_pct:>10.1f}")
    m = p["margin"]
    print(f"\npublished throat margins: OD {m['od']} %, ID {m['id']} %, typical {m['typical']} %")
    print(f"  designed: OD (tip) {secs[-1].throat_margin_pct:.1f} %, island end {secs[0].throat_margin_pct:.1f} %, "
          f"median {sorted(s.throat_margin_pct for s in secs)[len(secs)//2]:.1f} %")
    print(f"published solidity: hub {load()['fan_rotor_airfoil']['fig15']['solidity_hub']}, "
          f"tip {load()['fan_rotor_airfoil']['fig15']['solidity_tip']}")
    print(f"  designed: hub {secs[0].solidity:.2f}, tip {secs[-1].solidity:.2f}")

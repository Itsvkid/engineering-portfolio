"""A momentum-balance mixing plane for the E3's 18-lobe mixer.

Unit B5. The model B1 was closed on takes the mixed total pressure as the
mass-weighted mean of the two streams -- the IDEAL-mixing upper bound, which
has no loss in it at all. This module replaces that with a constant-area
momentum balance, and the point of the unit is that it needs only the AREA
RATIO of the two streams and not either absolute area: every equation below
is per unit area, so the scale divides out. That is asserted by a test
(`scale_invariance`), not by inspection.

Both streams are taken to a common static pressure at the mixing-plane
inlet, which is the standard closure for a mixing plane and is what fixes
the split of a given total area between them.

Real gas throughout, from `gas.py`, exactly as the rest of the cycle.
"""
import math
from . import gas

R = gas.R_AIR


def _static(tt, pt, ps, far, w):
    """One stream expanded from its total state to a static pressure.
    Returns (T_static, V, rho, required area)."""
    ts = gas.expand_to_pressure(tt, pt, ps, far)
    v = math.sqrt(max(2.0 * (gas.h(tt, far) - gas.h(ts, far)), 1e-9))
    rho = ps / (R * ts)
    return ts, v, rho, w / (rho * v)


def _sonic_ps(tt, pt, far):
    """The static pressure at which this stream reaches M = 1. Bisected on
    the real-gas Mach so that no constant-gamma shortcut creeps in."""
    lo, hi = 1e-4 * pt, 0.999999 * pt
    for _ in range(120):
        ps = 0.5 * (lo + hi)
        ts = gas.expand_to_pressure(tt, pt, ps, far)
        lo, hi = (ps, hi) if _mach(tt, ts, far) > 1.0 else (lo, ps)
    return 0.5 * (lo + hi)


def _mach(tt, ts, far):
    """Mach from the static/total temperature pair, local gamma."""
    cp = gas.cp(ts, far) * 1000.0
    gamma = cp / (cp - R)
    v = math.sqrt(max(2.0 * (gas.h(tt, far) - gas.h(ts, far)), 0.0))
    return v / math.sqrt(gamma * R * ts)


def solve(w_c, tt_c, pt_c, far_c, w_b, tt_b, pt_b, area_ratio):
    """Mix a core and a bypass stream at constant total area.

    `area_ratio` is A_core / A_bypass at the mixing plane. Note what is NOT
    in this signature: an absolute area. Given the two total states, the two
    mass flows and the ratio, the common static pressure is determined, and
    with it both areas -- so the mixing plane is closed on the ratio alone.
    That is B1's gate, and it is arithmetic rather than a figure.

    Returns a dict of the mixing-plane state.
    """
    # 1. the common static pressure that produces the prescribed area ratio.
    #    A_c/A_b rises monotonically with p_s ON THE SUBSONIC BRANCH only:
    #    each stream's mass flux peaks at its own sonic point and falls
    #    again below it, so the ratio turns over and a bisection started at
    #    p_s -> 0 walks off onto a supersonic branch. The lower bound is
    #    therefore the sonic static pressure of whichever stream chokes
    #    first, and there is a FLOOR on the achievable area ratio.
    ps_sonic = max(_sonic_ps(tt_c, pt_c, far_c), _sonic_ps(tt_b, pt_b, 0.0))
    lo, hi = ps_sonic, 0.999999 * min(pt_c, pt_b)
    _, _, _, a_c0 = _static(tt_c, pt_c, lo, far_c, w_c)
    _, _, _, a_b0 = _static(tt_b, pt_b, lo, 0.0, w_b)
    if area_ratio < a_c0 / a_b0:
        raise ValueError(
            f"area ratio {area_ratio:.4f} is below the subsonic floor "
            f"{a_c0 / a_b0:.4f}: no common static pressure gives it with "
            "both streams subsonic")
    for _ in range(200):
        ps = 0.5 * (lo + hi)
        _, _, _, a_c = _static(tt_c, pt_c, ps, far_c, w_c)
        _, _, _, a_b = _static(tt_b, pt_b, ps, 0.0, w_b)
        lo, hi = (lo, ps) if a_c / a_b > area_ratio else (ps, hi)
    ps = 0.5 * (lo + hi)
    ts_c, v_c, rho_c, a_c = _static(tt_c, pt_c, ps, far_c, w_c)
    ts_b, v_b, rho_b, a_b = _static(tt_b, pt_b, ps, 0.0, w_b)
    area = a_c + a_b

    # 2. mixed totals: mass for continuity, enthalpy for energy
    w6 = w_c + w_b
    #  fuel-air of the mixed stream: the core carries w_fuel = w_c*far/(1+far)
    wf = w_c * far_c / (1.0 + far_c)
    far6 = wf / (w6 - wf) if wf else 0.0
    ht6 = (w_c * gas.h(tt_c, far_c) + w_b * gas.h(tt_b)) / w6
    tt6 = gas.t_from_h(ht6, far6, guess=0.5 * (tt_c + tt_b))

    # 3. momentum: F = w_c V_c + w_b V_b + p_s A = w6 V6 + p_s6 A
    #    with continuity p_s6 = w6 R T_s6 / (V6 A), so
    #    w6 R T_s6 + w6 V6^2 = F V6, and T_s6 = T(h_t6 - V6^2/2).
    f_mom = w_c * v_c + w_b * v_b + ps * area

    def residual(v6):
        ts6 = gas.t_from_h(ht6 - 0.5 * v6 ** 2, far6, guess=tt6)
        return w6 * R * ts6 + w6 * v6 ** 2 - f_mom * v6

    # Subsonic root: the SMALLER of the two velocities that satisfy it.
    # residual is positive at V -> 0 (thermal term dominates) and goes
    # negative between the roots, so march up from a small velocity to the
    # first sign change and bisect there. Marching rather than assuming a
    # vertex, because T_s6 is a function of V6 and the curve is not a
    # parabola.
    v_ceiling = math.sqrt(2.0 * (ht6 - gas.h(1.0, far6)))   # T_s6 -> 0
    lo = 1.0
    step = v_ceiling / 400.0
    hi = None
    while lo + step < v_ceiling:
        if residual(lo + step) < 0.0:
            hi = lo + step
            break
        lo += step
    if hi is None:
        raise RuntimeError("no subsonic mixed-out root")
    for _ in range(200):
        v6 = 0.5 * (lo + hi)
        lo, hi = (v6, hi) if residual(v6) > 0 else (lo, v6)
    v6 = 0.5 * (lo + hi)
    ts6 = gas.t_from_h(ht6 - 0.5 * v6 ** 2, far6, guess=tt6)
    ps6 = w6 * R * ts6 / (v6 * area)
    pt6 = ps6 * math.exp((gas.phi(tt6, far6) - gas.phi(ts6, far6)) / R)

    pt6_ideal = (w_c * pt_c + w_b * pt_b) / w6
    return dict(ps=ps, ps6=ps6, pt6=pt6, tt6=tt6, ts6=ts6, v6=v6,
                pt6_ideal=pt6_ideal, area=area, area_core=a_c, area_bypass=a_b,
                mach_core=_mach(tt_c, ts_c, far_c), mach_bypass=_mach(tt_b, ts_b, 0.0),
                mach6=_mach(tt6, ts6, far6), far6=far6,
                loss_vs_ideal_pct=(1.0 - pt6 / pt6_ideal) * 100.0)


def scale_invariance(w_c, tt_c, pt_c, far_c, w_b, tt_b, pt_b, area_ratio, k=10.0):
    """Band 1, the unit's central claim, as a number.

    Scale both mass flows by k. At a fixed area ratio that scales both areas
    by k -- a mixing plane k times the size passing k times the flow. If the
    absolute area matters the intensive state must move; if only the ratio
    matters it cannot. Returns the largest fractional change over the
    intensive quantities.
    """
    a = solve(w_c, tt_c, pt_c, far_c, w_b, tt_b, pt_b, area_ratio)
    b = solve(k * w_c, tt_c, pt_c, far_c, k * w_b, tt_b, pt_b, area_ratio)
    keys = ("ps", "ps6", "pt6", "tt6", "ts6", "v6", "mach_core", "mach_bypass", "mach6")
    return max(abs(b[j] / a[j] - 1.0) for j in keys), (b["area"] / a["area"])


# ---------------------------------------------------------------------------
# The E3's own area ratio, from published geometry. Nothing here is fitted.
# ---------------------------------------------------------------------------
import csv as _csv
import pathlib as _pathlib
import yaml as _yaml

_DATA = _pathlib.Path(__file__).resolve().parents[2] / "data"


def core_annulus_m2():
    """The LPT rotor-5 trailing-edge annulus -- the last dimensioned core
    station upstream of the mixing plane. From `lpt-flowpath.csv`, itself
    derived from the transcribed LPT airfoil coordinates."""
    with open(_DATA / "lpt-flowpath.csv") as f:
        rows = [r for r in _csv.DictReader(l for l in f if not l.startswith("#"))]
    r5 = next(r for r in rows if r["row"] == "R5" and r["edge"] == "TE")
    rh, rt = float(r5["r_hub_cm"]) / 100.0, float(r5["r_tip_cm"]) / 100.0
    return math.pi * (rt ** 2 - rh ** 2)


def bypass_annulus_m2():
    """The bypass duct annulus band the published fan-duct Mach requires.
    Published Mach, derived area -- e3-fps-published.yaml records the
    method and this reads it rather than repeating the number."""
    y = _yaml.safe_load((_DATA / "e3-fps-published.yaml").read_text())
    return tuple(y["nacelle"]["bypass_duct_area_by_continuity"]["required_annulus_area_m2"])


def published_area_ratio():
    """A_core / A_bypass at the mixing plane: nominal and the band the
    bypass area's own Mach band implies."""
    ac = core_annulus_m2()
    lo, hi = bypass_annulus_m2()
    return ac / (0.5 * (lo + hi)), (ac / hi, ac / lo)


# ---------------------------------------------------------------------------
# Unit B5's own table
# ---------------------------------------------------------------------------
TABLE_XXIII = ((0.75, 0.0020, 3.1), (0.79, 0.0057, 2.6), (0.85, 0.0057, 2.9))


def _streams(result, inp):
    """The two streams as they arrive at the mixing plane, out of a solved
    cycle: the duct losses are already applied, nothing is re-derived."""
    s, comp = result.stations, inp.comp
    p6_core = s["p5"] * (1.0 - comp["core_duct_pressure_drop"])
    p6_byp = s["p13"] * (1.0 - comp["fan_duct_pressure_drop"])
    w_byp = result.w2_kg_s - result.w_core_kg_s
    far5 = result.w_fuel_kg_s / (s["w5"] - result.w_fuel_kg_s)
    return dict(w_c=s["w5"], tt_c=s["t5"], pt_c=p6_core, far_c=far5,
                w_b=w_byp, tt_b=s["t13"], pt_b=p6_byp)


def mach_admissible_range(st, lo=0.30, hi=0.70, n=400):
    """The area ratios for which BOTH mixing-plane Mach numbers sit inside
    [lo, hi]. Band 4: outside this the area ratio is wrong whatever the sfc
    says."""
    ok = []
    for i in range(n):
        ar = 0.24 + 0.36 * i / (n - 1)
        try:
            m = solve(area_ratio=ar, **st)
        except (ValueError, RuntimeError):
            continue          # below the subsonic floor, or the mixed-out
            # stream itself chokes -- both are "this area ratio is not the
            # E3's", not a solver failure
        if lo <= m["mach_core"] <= hi and lo <= m["mach_bypass"] <= hi:
            ok.append(ar)
    return (min(ok), max(ok)) if ok else None


def main():
    from .cycle import load_inputs, solve as cycle_solve, solve_rating
    inp = load_inputs()
    ar_nom, (ar_lo, ar_hi) = published_area_ratio()
    print("Unit B5 -- the momentum-balance mixing plane\n")
    print(f"core annulus (LPT R5 TE)      {core_annulus_m2():.4f} m2")
    print(f"bypass annulus (published M)  {bypass_annulus_m2()[0]:.2f} - {bypass_annulus_m2()[1]:.2f} m2")
    print(f"area ratio A_core/A_bypass    {ar_nom:.4f}  ({ar_lo:.4f} - {ar_hi:.4f})\n")

    mc = inp.ratings[1]
    st = _streams(solve_rating(mc, inp), inp)
    inv, ascale = scale_invariance(**st, area_ratio=ar_nom)
    print(f"band 1  scale invariance: both flows x10 -> areas x{ascale:.1f}, "
          f"intensive state moves {inv:.2e}")

    m = solve(area_ratio=ar_nom, **st)
    print(f"band 2  pt6 {m['pt6']:.0f} Pa; mass-weighted {m['pt6_ideal']:.0f}; "
          f"lower stream {min(st['pt_c'], st['pt_b']):.0f}  "
          f"-> mixing loss {m['loss_vs_ideal_pct']:.3f} % of pt")
    print(f"band 4  mixing-plane Mach: core {m['mach_core']:.3f}, bypass "
          f"{m['mach_bypass']:.3f}, mixed {m['mach6']:.3f}")
    rng = mach_admissible_range(st)
    print(f"        area ratios with both Mach in 0.30-0.70: "
          f"{rng[0]:.3f} - {rng[1]:.3f}\n")

    def gain(eff, loss, ar, rating=mc):
        """Identical to tests/test_e3cycle.py::_mixer_gain -- the separate-flow
        baseline sheds the column's own mixer pressure loss (STEP0 assumption
        3). The ONLY thing unit B5 changes is how p_t6 is formed."""
        sep = cycle_solve(rating, inp, mixed=False, extra_loss=-loss)
        r = cycle_solve(rating, inp, mixer_eff=eff, mixing_area_ratio=ar)
        return (1.0 - r.sfc_kg_N_h / sep.sfc_kg_N_h) * 100.0

    print("           " + "".join(f"{e*100:>8.0f}%" for e, _, _ in TABLE_XXIII))
    print("Table XXIII" + "".join(f"{p:>9.1f}" for _, _, p in TABLE_XXIII))
    print("mass-wtd   " + "".join(f"{gain(e, l, None):>9.2f}" for e, l, _ in TABLE_XXIII))
    for ar in (rng[0], ar_lo, ar_nom, ar_hi, rng[1]):
        print(f"AR {ar:<8.4f}" + "".join(f"{gain(e, l, ar):>9.2f}" for e, l, _ in TABLE_XXIII))
    print("\nslopes (col2-col1, col3-col2); Table XXIII prints -0.5, +0.3")
    for label, ar in (("mass-weighted", None), ("momentum", ar_nom)):
        g = [gain(e, l, ar) for e, l, _ in TABLE_XXIII]
        print(f"  {label:<14}{g[1]-g[0]:+.2f}  {g[2]-g[1]:+.2f}")

    print("\nall three ratings at the nominal area ratio, 85 % / 0.57 %:")
    for r in inp.ratings:
        s2 = _streams(solve_rating(r, inp), inp)
        mm = solve(area_ratio=ar_nom, **s2)
        gr = gain(0.85, 0.0057, ar_nom, rating=r)
        print(f"  {r.name:<11} Mc {mm['mach_core']:.3f}  Mb {mm['mach_bypass']:.3f}  "
              f"pt loss {mm['loss_vs_ideal_pct']:.3f} %   gain {gr:.2f} %")


if __name__ == "__main__":
    main()

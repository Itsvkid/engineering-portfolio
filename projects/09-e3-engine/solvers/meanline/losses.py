"""Ainley-Mathieson turbine loss model (ARC R&M 2974), every correlation
read from data/methods/ainley-mathieson-rm2974.yaml. Angles in degrees,
magnitudes; a turbine row turns the flow from alpha1 (inlet, positive when
against the outlet swirl) to alpha2 (outlet). Loss coefficient
Y = (P01 - P02) / (P02 - p2)."""
from __future__ import annotations

import math
import pathlib

import yaml

METHODS = pathlib.Path(__file__).resolve().parents[2] / "data" / "methods"
AM = yaml.safe_load((METHODS / "ainley-mathieson-rm2974.yaml").read_text())
SP290 = yaml.safe_load((METHODS / "sp290-boundary-layer-losses.yaml").read_text())


def _interp(x, xs, ys):
    """linear interpolation, linear extrapolation at the ends"""
    if x <= xs[0]:
        i = 0
    elif x >= xs[-1]:
        i = len(xs) - 2
    else:
        i = next(k for k in range(len(xs) - 1) if xs[k] <= x <= xs[k + 1])
    t = (x - xs[i]) / (xs[i + 1] - xs[i])
    return ys[i] + t * (ys[i + 1] - ys[i])


def _interp_family(x, key, xs, curves):
    """interpolate a family of curves keyed by a parameter (outlet angle)"""
    keys = sorted(curves)
    vals = [_interp(x, xs, curves[k]) for k in keys]
    return _interp(key, keys, vals)


def yp_nozzle(alpha2, s_c):
    f = AM["fig4a_nozzle_profile_loss"]
    return _interp_family(s_c, alpha2, f["s_over_c"], f["curves"])


def yp_impulse(alpha2, s_c):
    f = AM["fig4b_impulse_profile_loss"]
    return _interp_family(s_c, alpha2, f["s_over_c"], f["curves"])


def yp_zero_incidence(beta1, alpha2, s_c, t_c):
    """equation (5): profile loss at zero incidence for a blade of inlet
    angle beta1 (magnitude, same sense as an impulse blade's) and outlet
    angle alpha2"""
    e5 = AM["equation_5"]
    r = abs(beta1 / alpha2)
    y0, yi = yp_nozzle(alpha2, s_c), yp_impulse(alpha2, s_c)
    tc = min(max(t_c, e5["thickness_clip"][0]), e5["thickness_clip"][1])
    return (y0 + r * r * (yi - y0)) * (tc / e5["thickness_reference"]) ** r


def alpha2_star(acos_o_s):
    f = AM["fig5_outlet_angle"]
    return _interp(acos_o_s, f["acos_o_over_s_deg"], f["alpha2_star_deg"])


def outlet_angle_low_mach(o_s, s_e):
    """equation (1): alpha2 = alpha2*(cos^-1 o/s) - 4 s/e in the report's
    signs (outlet angles negative), so the magnitude grows by 4 s/e:
    worked example 62.4 -> 63.5 at s/e 0.279"""
    return alpha2_star(math.degrees(math.acos(o_s))) + 4.0 * s_e


def outlet_angle_with_clearance(alpha2_zero, beta1, k_h, shrouded=False):
    """equation (4)"""
    X = AM["equation_4"]["X"]["simple_shroud" if shrouded else "radial_tip_clearance"]
    a, b = math.radians(alpha2_zero), math.radians(beta1)
    f = X * k_h * math.cos(b) / math.cos(a)
    return math.degrees(math.atan((1 - f) * math.tan(a) - f * math.tan(b)))


def stalling_incidence(beta1, alpha2, s_c):
    """sec 5.2 procedure with Fig 7: i_s for the actual s/c"""
    mid = AM["fig7_mid_outlet_angle_ratio"]
    ratio = _interp(s_c, mid["s_over_c"], mid["alpha2_over_alpha2_at_075"])
    alpha2_075 = alpha2 / ratio
    fb = AM["fig7b_stalling_incidence"]
    x = -beta1 / alpha2_075           # the report's sign: negative for an accelerating row
    is_075 = _interp_family(x, alpha2_075, fb["beta1_over_alpha2"], fb["curves"])
    fa = AM["fig7a_stall_shift"]
    if s_c <= 0.85:
        shift = _interp(s_c, fa["s_over_c"], fa["delta_is_deg_common"])
    else:
        shift = _interp_family(s_c, alpha2, fa["branches_s_over_c"], fa["branches"])
    return is_075 + shift


def yp_at_incidence(yp0, i, i_s):
    f = AM["fig6_incidence"]
    return yp0 * _interp(i / i_s, f["i_over_is"], f["yp_ratio"])


def lift_terms(alpha1, alpha2):
    """C_L/(s/c) and cos^2 a2 / cos^3 a_m of equation (6); alpha1 positive
    against the outlet swirl (the row turns the flow through alpha1 + alpha2)"""
    a1, a2 = math.radians(alpha1), math.radians(alpha2)
    am = math.atan(0.5 * (math.tan(a1) - math.tan(a2)))
    cl_sc = 2.0 * (math.tan(a1) + math.tan(a2)) * math.cos(am)
    return cl_sc, math.cos(a2) ** 2 / math.cos(am) ** 3


def secondary_lambda(beta1, alpha2, an1, an2, id_od):
    """Fig 8's lambda from the zero-incidence areas (the worked example
    evaluates it once, at the blade inlet angle)"""
    f = AM["fig8_secondary_lambda"]
    b1, a2 = math.radians(beta1), math.radians(alpha2)
    x = (an2 * math.cos(a2) / (an1 * math.cos(b1))) ** 2 / (1 + id_od)
    return _interp(x, f["x"], f["lambda"]), x


def secondary_and_clearance(alpha1, alpha2, an1, an2, id_od, k_h, shrouded=False, beta1=None):
    """equation (6). Returns Y_s + Y_k and the factors used."""
    f = AM["fig8_secondary_lambda"]
    cl_sc, geo = lift_terms(alpha1, alpha2)
    lam, x = secondary_lambda(beta1 if beta1 is not None else alpha1, alpha2, an1, an2, id_od)
    B = f["B"]["shroud_seal" if shrouded else "radial_tip_clearance"]
    return (lam + B * k_h) * cl_sc ** 2 * geo, dict(cl_sc=cl_sc, geo=geo, x=x, lam=lam)


def te_factor(te_s):
    f = AM["fig9_trailing_edge"]
    return _interp(te_s, f["te_over_s"], f["factor"])


def dunham_came_secondary_and_clearance(alpha1, alpha2, c_h, k_c, shrouded=False):
    """the 1970 aspect-ratio form (data file: dunham_came_1970, an
    assumption until the paper is on disk)"""
    dc = AM["dunham_came_1970"]["constants"]
    cl_sc, geo = lift_terms(alpha1, alpha2)
    a1, a2 = math.radians(alpha1), math.radians(alpha2)
    ys = dc["secondary"] * c_h * (math.cos(a2) / math.cos(a1)) * cl_sc ** 2 * geo
    B = dc["B_shrouded"] if shrouded else dc["B_unshrouded"]
    yk = B * c_h * k_c ** dc["clearance_exponent"] * cl_sc ** 2 * geo
    return ys + yk, dict(ys=ys, yk=yk)


def row_total_loss(beta1, alpha1, alpha2_loss, s_c, t_c, te_s, an1, an2, id_od, k_h, shrouded=False, c_h=None):
    """total loss coefficient of a row at inlet flow angle alpha1 (blade
    inlet angle beta1), all angles magnitudes. alpha2_loss is the
    zero-clearance outlet angle used for the loss (sec 5.2)."""
    yp0 = yp_zero_incidence(beta1, alpha2_loss, s_c, t_c)
    i_s = stalling_incidence(beta1, alpha2_loss, s_c)
    i = alpha1 - beta1
    yp = yp_at_incidence(yp0, i, i_s)
    r = max(-1.5, min(1.0, i / i_s)) if i_s else 0.0
    ysk, fac = secondary_and_clearance(beta1 + r * i_s, alpha2_loss, an1, an2, id_od, k_h, shrouded, beta1=beta1)
    yt = (yp + ysk) * te_factor(te_s)
    out = dict(yp0=yp0, i_s=i_s, i=i, yp=yp, ysk=ysk, yt=yt, **fac)
    if c_h is not None:
        ysk_dc, _ = dunham_came_secondary_and_clearance(beta1 + r * i_s, alpha2_loss, c_h, k_h / c_h, shrouded)
        out["ysk_dc"] = ysk_dc
        out["yt_dc"] = (yp + ysk_dc) * te_factor(te_s)
    return out


# ---------------------------------------------------------------------------
# The report's stage calculation (sec 6), constant gas properties, for the
# worked example of Appendix II. SI inside; the inputs are the report's.
# ---------------------------------------------------------------------------
PSI = 6894.757
LB = 0.45359237
IN2 = 0.0254 ** 2
FT = 0.3048


def _flow_function(m, gamma, R):
    """W sqrt(T0) / (A P0) for an isentropic expansion to Mach m"""
    return math.sqrt(gamma / R) * m * (1 + 0.5 * (gamma - 1) * m * m) ** (-(gamma + 1) / (2 * (gamma - 1)))


def _row_exit(w, t0, p_in, area_of_mach, y_t, gamma, R):
    """outlet Mach and total pressure of a row: loss Y = (P_in - P_out)/(P_out - p_out),
    continuity W sqrt(T0)/(A P_out) = Q(M); bisection on M. Returns None if choked."""
    def resid(m):
        p_ratio = (1 + 0.5 * (gamma - 1) * m * m) ** (-gamma / (gamma - 1))
        p_out = p_in / (1 + y_t * (1 - p_ratio))
        return w * math.sqrt(t0) / (area_of_mach(m) * p_out) - _flow_function(m, gamma, R), p_out
    lo, hi = 0.02, 1.0
    if resid(hi)[0] > 0:
        return None
    for _ in range(80):
        m = 0.5 * (lo + hi)
        lo, hi = (m, hi) if resid(m)[0] > 0 else (lo, m)
    m = 0.5 * (lo + hi)
    return m, resid(m)[1]


def worked_example_stage(w_param):
    """the Appendix II turbine at inlet flow W sqrt(T)/P (lb sqrtK / s psi):
    returns P3/P1, isentropic efficiency, and the station values, or None
    if the flow cannot pass."""
    ex = AM["worked_example"]
    g = ex["gas"]
    gamma, cp, R = g["gamma"], g["cp_J_kgK"], g["R_J_kgK"]
    t_in = ex["inlet"]["T_K"]
    p_in = ex["inlet"]["P_psia"] * PSI
    u = ex["inlet"]["U_ft_s"] * FT
    an = ex["annulus"]["area_sq_in"] * IN2
    w = w_param * ex["inlet"]["P_psia"] / math.sqrt(t_in) * LB
    st, ro = ex["stator"], ex["rotor"]

    def stator_angle(m):
        a_lo, a_hi = abs(st["results"]["alpha2_low_mach_deg"]), abs(st["results"]["alpha2_mach1_deg"])
        return a_lo if m <= 0.5 else a_lo + (a_hi - a_lo) * (m - 0.5) / 0.5

    def rotor_angle(m):
        a_lo, a_hi = abs(ro["results"]["alpha2_with_clearance_deg"]), abs(ro["results"]["alpha2_mach1_deg"])
        return a_lo if m <= 0.5 else a_lo + (a_hi - a_lo) * (m - 0.5) / 0.5

    tab = ro["results"]["incidence_table"]
    extra = ex["fig14_rotor_total_loss_read"]
    pts = sorted(set(zip(tab["i_deg"], tab["Yt_corrected"])) | {(i, y) for i, y in zip(extra["i_deg"], extra["Yt"]) if i not in tab["i_deg"]})
    i_pts, y_pts = [p[0] for p in pts], [p[1] for p in pts]

    def rotor_loss(i):
        return _interp(i, i_pts, y_pts)

    out = _row_exit(w, t_in, p_in, lambda m: an * math.cos(math.radians(stator_angle(m))), st["results"]["Yt"], gamma, R)
    if out is None:
        return None
    m0, p0 = out
    a0 = math.radians(stator_angle(m0))
    t0s = t_in / (1 + 0.5 * (gamma - 1) * m0 * m0)
    v0 = m0 * math.sqrt(gamma * R * t0s)
    va, vw0 = v0 * math.cos(a0), v0 * math.sin(a0)
    vw1 = vw0 - u                       # relative whirl at rotor inlet
    v1 = math.hypot(va, vw1)
    alpha1 = math.degrees(math.atan2(vw1, va))
    t1rel = t0s + v1 * v1 / (2 * cp)
    p_static0 = p0 * (t0s / t_in) ** (gamma / (gamma - 1))
    p1rel = p_static0 * (t1rel / t0s) ** (gamma / (gamma - 1))
    i = alpha1 - ro["beta1_deg"]
    yt = rotor_loss(i)
    out = _row_exit(w, t1rel, p1rel, lambda m: an * math.cos(math.radians(rotor_angle(m))), yt, gamma, R)
    if out is None:
        return None
    m2, p2rel = out
    a2 = math.radians(rotor_angle(m2))
    t2s = t1rel / (1 + 0.5 * (gamma - 1) * m2 * m2)
    v2rel = m2 * math.sqrt(gamma * R * t2s)
    va2, vw2rel = v2rel * math.cos(a2), -v2rel * math.sin(a2)   # turned against rotation
    vw2 = vw2rel + u
    v2 = math.hypot(va2, vw2)
    t02 = t2s + v2 * v2 / (2 * cp)
    p_static2 = p2rel * (t2s / t1rel) ** (gamma / (gamma - 1))
    p02 = p_static2 * (t02 / t2s) ** (gamma / (gamma - 1))
    pr = p02 / p_in
    dt = t_in - t02
    dt_is = t_in * (1 - pr ** ((gamma - 1) / gamma))
    return dict(pr=pr, eta=dt / dt_is, m0=m0, m2=m2, i=i, yt=yt, alpha1=alpha1, dt=dt,
                euler_dt=u * (vw0 - vw2) / cp)


def worked_example_choking_flow():
    lo, hi = 8.0, 12.0
    for _ in range(60):
        m = 0.5 * (lo + hi)
        lo, hi = (m, hi) if worked_example_stage(m) is not None else (lo, m)
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------------------
# SP-290 chapter 7: the end-wall loss as an area ratio, and the Reynolds rule
# ---------------------------------------------------------------------------

def end_wall_multiplier(s_h, stagger_deg):
    """equation (7-47): the factor by which the end walls raise a blade's
    own momentum loss, 1 + (s/h) cos(stagger)"""
    return 1.0 + s_h * math.cos(math.radians(stagger_deg))


def reynolds_corrected_efficiency(eta, re_mean):
    """R&M 2974 sec 8 equation (20): (1 - eta) proportional to Re^-1/5,
    the data taken at Re 2e5"""
    r = SP290["reynolds_number"]
    return 1.0 - (1.0 - eta) * (re_mean / r["rm2974_reference_reynolds"]) ** -r["exponent"]


def sp290_row_total_loss(beta1, alpha1, alpha2_loss, s_c, t_c, te_s, s_h, stagger_deg, k_h, shrouded=False):
    """profile loss and incidence from R&M 2974, the end-wall loss from
    SP-290's area ratio, the clearance term from R&M 2974's B (k/h) on the
    same lift group. A hybrid, labelled as one."""
    yp0 = yp_zero_incidence(beta1, alpha2_loss, s_c, t_c)
    i_s = stalling_incidence(beta1, alpha2_loss, s_c)
    i = alpha1 - beta1
    yp = yp_at_incidence(yp0, i, i_s)
    ys = yp * (end_wall_multiplier(s_h, stagger_deg) - 1.0)
    r = max(-1.5, min(1.0, i / i_s)) if i_s else 0.0
    cl_sc, geo = lift_terms(beta1 + r * i_s, alpha2_loss)
    B = AM["fig8_secondary_lambda"]["B"]["shroud_seal" if shrouded else "radial_tip_clearance"]
    yk = B * k_h * cl_sc ** 2 * geo
    return dict(yp=yp, ys=ys, yk=yk, ysk=ys + yk, yt=(yp + ys + yk) * te_factor(te_s), i_s=i_s, i=i)

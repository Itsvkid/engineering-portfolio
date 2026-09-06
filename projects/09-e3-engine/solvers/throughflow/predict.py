"""C2 unit 9: predict the spanwise distribution, don't audit it.

A through-flow designer specifies three things at a station: the vortex
law r*c_theta(r), the spanwise work distribution, and the spanwise loss
distribution. Radial equilibrium then *determines* the axial velocity
profile, and continuity sets its level. The Mach number and the flow
angle are outputs.

This solver takes those three inputs from Table XXI, integrates

    d(c_z^2 / 2)/dr = [dh0/dr - T ds/dr] - (c_theta / r) d(r c_theta)/dr

outward from the hub, sets the level by the mass flow the printed
distribution itself carries, and compares the resulting c_z, alpha and
Mach with the printed columns. STEP0.md, unit 9."""
from __future__ import annotations

import math

from e3cycle import gas
from throughflow.radial_equilibrium import _ddr, _key, load, station_points


def _sound(ts):
    cp = gas.cp(ts)
    return math.sqrt(cp / (cp - gas.R_AIR) * gas.R_AIR * ts)


def predict_station(points, curvature=None):
    """points sorted by radius. Returns the predicted c_z, alpha and Mach
    at each, with the level set by the printed distribution's own mass flow."""
    r = [p.r for p in points]
    t0 = [p.t0 for p in points]
    p0 = [p.p0 for p in points]
    rct = [p.r * p.ctheta for p in points]

    def mass_flow(cz_list, ts_list):
        w = 0.0
        for i in range(len(points) - 1):
            for a, b in ((i, i + 1),):
                ra, rb = r[a], r[b]
                rho_a = p0[a] * math.exp(-(gas.phi(t0[a]) - gas.phi(ts_list[a])) / gas.R_AIR) / (gas.R_AIR * ts_list[a])
                rho_b = p0[b] * math.exp(-(gas.phi(t0[b]) - gas.phi(ts_list[b])) / gas.R_AIR) / (gas.R_AIR * ts_list[b])
                w += math.pi * (rb ** 2 - ra ** 2) * 0.5 * (rho_a * cz_list[a] + rho_b * cz_list[b])
        return w

    # the mass flow the printed distribution carries
    ts_pr = [p.ts for p in points]
    cz_pr = [p.cz for p in points]
    w_target = mass_flow(cz_pr, ts_pr)

    # integrate the radial-equilibrium right-hand side outward from the hub
    ts = list(ts_pr)
    cz = list(cz_pr)
    for _ in range(60):
        rhs = []
        for i, p in enumerate(points):
            cp = gas.cp(t0[i])
            lhs = cp * (1 - ts[i] / t0[i]) * _ddr(t0, r, i) + ts[i] * gas.R_AIR / p0[i] * _ddr(p0, r, i)
            vortex = p.ctheta / p.r * _ddr(rct, r, i)
            term = lhs - vortex
            if curvature is not None and p.sl in curvature:
                term += curvature[p.sl]
            rhs.append(term)
        # c_z^2 / 2 by trapezoidal integration from the innermost point
        half = [0.0]
        for i in range(len(points) - 1):
            half.append(half[-1] + 0.5 * (rhs[i] + rhs[i + 1]) * (r[i + 1] - r[i]))
        # level from continuity against the printed mass flow
        lo, hi = 10.0, 400.0
        for _ in range(60):
            c0 = 0.5 * (lo + hi)
            trial = [math.sqrt(max(c0 * c0 + 2 * h, 1.0)) for h in half]
            tt = []
            for i, p in enumerate(points):
                c2 = trial[i] ** 2 + p.ctheta ** 2
                tt.append(gas.t_from_h(gas.h(t0[i]) - 0.5 * c2, guess=t0[i] - c2 / 2000))
            lo, hi = (c0, hi) if mass_flow(trial, tt) < w_target else (lo, c0)
        c0 = 0.5 * (lo + hi)
        cz_new = [math.sqrt(max(c0 * c0 + 2 * h, 1.0)) for h in half]
        ts_new = []
        for i, p in enumerate(points):
            c2 = cz_new[i] ** 2 + p.ctheta ** 2
            ts_new.append(gas.t_from_h(gas.h(t0[i]) - 0.5 * c2, guess=t0[i] - c2 / 2000))
        if max(abs(a - b) for a, b in zip(cz_new, cz)) < 1e-6:
            cz, ts = cz_new, ts_new
            break
        cz, ts = cz_new, ts_new
    out = []
    for i, p in enumerate(points):
        c = math.hypot(cz[i], p.ctheta)
        out.append(dict(sl=p.sl, pct_imm=p.pct_imm, r=p.r,
                        cz=cz[i], cz_printed=p.cz,
                        alpha=math.degrees(math.atan2(p.ctheta, cz[i])),
                        alpha_printed=math.degrees(math.atan2(p.ctheta, p.cz)),
                        mach=c / _sound(ts[i]),
                        mach_printed=math.hypot(p.cz, p.ctheta) / _sound(p.ts)))
    return out


def predict_all(with_curvature=False):
    """Default: the *simple* form. Unit 9 finding 34 -- the curvature term
    improves the local residual (unit 8) but degrades the integrated
    prediction, because integrating a correction noisier than the term it
    corrects accumulates its error across the span."""
    from throughflow.radial_equilibrium import curvature_terms, gas_path_stations
    xxi = load()
    curv = curvature_terms(xxi) if with_curvature else {}
    out = []
    for label, pts in gas_path_stations(xxi):
        pts = sorted(pts, key=lambda p: p.r)
        res = predict_station(pts, curv.get(label))
        out.append((label, res))
    return out


def errors(res):
    d_cz = [x["cz"] - x["cz_printed"] for x in res]
    d_a = [x["alpha"] - x["alpha_printed"] for x in res]
    d_m = [x["mach"] - x["mach_printed"] for x in res]
    return dict(cz_rms=math.sqrt(sum(x * x for x in d_cz) / len(d_cz)),
                alpha_rms=math.sqrt(sum(x * x for x in d_a) / len(d_a)),
                alpha_max=max(abs(x) for x in d_a),
                mach_rms=math.sqrt(sum(x * x for x in d_m) / len(d_m)),
                mach_max=max(abs(x) for x in d_m))


if __name__ == "__main__":
    all_res = predict_all()
    target = next(r for label, r in all_res if label == "S10 ex")
    print("C2's closure test: stator-10 exit, predicted from the vortex law, the work and the loss")
    print(f"{'sl':>3}{'imm %':>7}{'c_z':>8}{'printed':>9}{'alpha':>8}{'printed':>9}{'diff':>7}{'Mach':>7}{'printed':>9}{'diff':>7}")
    for x in target:
        print(f"{x['sl']:>3}{x['pct_imm']:>7.1f}{x['cz']:>8.1f}{x['cz_printed']:>9.1f}"
              f"{x['alpha']:>8.2f}{x['alpha_printed']:>9.2f}{x['alpha'] - x['alpha_printed']:>7.2f}"
              f"{x['mach']:>7.3f}{x['mach_printed']:>9.3f}{x['mach'] - x['mach_printed']:>7.3f}")
    e = errors(target)
    print(f"\nstator-10 exit: swirl rms {e['alpha_rms']:.2f} deg (max {e['alpha_max']:.2f}), "
          f"Mach rms {e['mach_rms']:.3f} (max {e['mach_max']:.3f}); C2 asks for 2 deg and 0.02")
    print(f"\n{'station':<10}{'alpha rms':>11}{'alpha max':>11}{'Mach rms':>10}{'Mach max':>10}{'c_z rms':>9}")
    worst_a = worst_m = 0.0
    for label, res in all_res:
        e = errors(res)
        worst_a, worst_m = max(worst_a, e["alpha_rms"]), max(worst_m, e["mach_rms"])
        print(f"{label:<10}{e['alpha_rms']:>11.2f}{e['alpha_max']:>11.2f}{e['mach_rms']:>10.3f}{e['mach_max']:>10.3f}{e['cz_rms']:>9.1f}")
    print(f"\nworst station: swirl rms {worst_a:.2f} deg, Mach rms {worst_m:.3f} over {len(all_res)} stations")

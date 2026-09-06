"""C2 unit 10: what vortex law does the E3 LPT actually use?

The LPT report calls its design "controlled vortex" (sec 2.6) and never
says what that means numerically. Table II prints the stator exit angle
and Mach at hub, pitch and tip for all five stages, and the flowpath
gives the three radii. Fitting c_theta proportional to r^n across the
span turns the adjective into a number: free vortex is n = -1, solid-body
(forced) is n = +1. STEP0.md, unit 10."""
from __future__ import annotations

import math

import yaml

from e3cycle import gas
from e3cycle.cycle import DATA
from e3cycle.stations import _csv_rows, find_key

IN, CM = 0.0254, 0.01


def load():
    aero = yaml.safe_load((DATA / "lpt-aero.yaml").read_text())
    fp = {(r["row"], r["edge"]): r for r in _csv_rows(DATA / "lpt-flowpath.csv")}
    return find_key(aero, "vector_diagrams"), fp


def _velocities(t0, mach, far=0.0):
    ts = t0
    for _ in range(40):
        cp = gas.cp(ts, far)
        g = cp / (cp - gas.R_AIR)
        ts = t0 / (1 + 0.5 * (g - 1) * mach * mach)
    cp = gas.cp(ts, far)
    g = cp / (cp - gas.R_AIR)
    return mach * math.sqrt(g * gas.R_AIR * ts), ts


def stage_vortex(t_inlet=1058.9):
    """c_theta at hub, pitch and tip of every stator exit, and the exponent
    n in c_theta ~ r^n that fits them"""
    tb, fp = load()
    out = []
    t0 = t_inlet
    for n in range(1, 6):
        s = tb[f"stage{n}"]
        row = fp[(f"S{n}", "TE")]
        radii = [float(row["r_hub_cm"]) * CM, float(row["r50_in"]) * IN, float(row["r_tip_cm"]) * CM]
        ct, cz = [], []
        for m, alpha, r in zip(s["stator_exit_mach"], s["stator_exit_angle_deg"], radii):
            c, _ = _velocities(t0, m)
            ct.append(c * math.sin(math.radians(alpha)))
            cz.append(c * math.cos(math.radians(alpha)))
        # least-squares exponent of ln(c_theta) against ln(r)
        lr = [math.log(r) for r in radii]
        lc = [math.log(x) for x in ct]
        mean_r, mean_c = sum(lr) / 3, sum(lc) / 3
        num = sum((a - mean_r) * (b - mean_c) for a, b in zip(lr, lc))
        den = sum((a - mean_r) ** 2 for a in lr)
        exponent = num / den
        # how well a free vortex would fit: r*c_theta constant?
        rct = [r * c for r, c in zip(radii, ct)]
        out.append(dict(stage=n, radii=radii, ctheta=ct, cz=cz, exponent=exponent,
                        rct=rct, rct_spread=(max(rct) - min(rct)) / (sum(rct) / 3),
                        ct_spread=(max(ct) - min(ct)) / (sum(ct) / 3), t0=t0,
                        angles=s["stator_exit_angle_deg"], machs=s["stator_exit_mach"]))
        # next stage inlet total temperature
        t0 = gas.t_from_h(gas.h(t0) - s["energy_extraction"] * 2326.0, guess=t0 - 60)
    return out


def hpc_vortex():
    """the same exponent for every HPC stator exit, from Table XXI's 12
    streamlines -- a compressor's vortex law beside the turbine's"""
    from throughflow.radial_equilibrium import load as load_xxi, station_points
    xxi = load_xxi()
    out = []
    for row in xxi["rows"]:
        if row["row"] != "stator":
            continue
        pts = sorted(station_points(xxi, row, "exit"), key=lambda p: p.r)
        pts = [p for p in pts if p.ctheta > 1.0]
        if len(pts) < 4:
            continue
        # a row designed to leave the flow axial has no vortex law to fit:
        # the exponent of a near-zero swirl is meaningless
        swirl = sum(abs(math.degrees(math.atan2(q.ctheta, q.cz))) for q in pts) / len(pts)
        lr = [math.log(p.r) for p in pts]
        lc = [math.log(p.ctheta) for p in pts]
        mr, mc = sum(lr) / len(lr), sum(lc) / len(lc)
        num = sum((a - mr) * (b - mc) for a, b in zip(lr, lc))
        den = sum((a - mr) ** 2 for a in lr)
        rct = [p.r * p.ctheta for p in pts]
        out.append(dict(stage=row["stage"], n=len(pts), exponent=num / den, mean_swirl=swirl,
                        degenerate=swirl < 8.0,
                        rct_spread=(max(rct) - min(rct)) / (sum(rct) / len(rct))))
    return out


if __name__ == "__main__":
    rows = stage_vortex()
    print("E3 LPT stator exits: what vortex law?  (free vortex n = -1, solid body n = +1)")
    print(f"{'st':>3}{'r hub':>8}{'r pitch':>9}{'r tip':>8}{'ct hub':>9}{'ct pitch':>10}{'ct tip':>9}"
          f"{'n':>8}{'r.ct spread':>13}{'ct spread':>11}")
    for r in rows:
        print(f"{r['stage']:>3}{r['radii'][0] * 100:>8.1f}{r['radii'][1] * 100:>9.1f}{r['radii'][2] * 100:>8.1f}"
              f"{r['ctheta'][0]:>9.1f}{r['ctheta'][1]:>10.1f}{r['ctheta'][2]:>9.1f}"
              f"{r['exponent']:>8.3f}{r['rct_spread'] * 100:>12.1f}%{r['ct_spread'] * 100:>10.1f}%")
    ex = [r["exponent"] for r in rows]
    print(f"\nexponent n: {min(ex):+.3f} to {max(ex):+.3f}, mean {sum(ex) / len(ex):+.3f}")
    print("free vortex would be -1.000 on every stage")
    print(f"\nHPC stator exits, the same fit over 12 streamlines:")
    print(f"{'stage':>6}{'pts':>5}{'swirl':>8}{'n':>9}{'r.ct spread':>13}")
    hv = hpc_vortex()
    for h in hv:
        note = "  (near-axial: no vortex law to fit)" if h["degenerate"] else ""
        print(f"{h['stage']:>6}{h['n']:>5}{h['mean_swirl']:>8.1f}{h['exponent']:>9.3f}{h['rct_spread'] * 100:>12.1f}%{note}")
    good = [h["exponent"] for h in hv if not h["degenerate"]]
    print(f"\nHPC exponent over the nine swirling stators: {min(good):+.3f} to {max(good):+.3f} -- no single law")

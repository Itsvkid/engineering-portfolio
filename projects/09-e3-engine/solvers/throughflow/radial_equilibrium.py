"""C2 unit 8: does the E3's printed through-flow satisfy radial
equilibrium, and what is left over when it does not?

Simple radial equilibrium, in the absolute frame, for steady axisymmetric
flow with no radial velocity and no streamline curvature (SP-36 ch. VIII,
eq. 8-6 in that form):

    dh0/dr - T ds/dr = c_z dc_z/dr + (c_theta / r) d(r c_theta)/dr

Table XXI prints, at 12 streamlines of every station, everything both
sides need. What is left over is the term simple radial equilibrium
throws away -- the streamline curvature and slope that the E3's own CAFD
through-flow kept. STEP0.md, unit 8."""
from __future__ import annotations

import math
from dataclasses import dataclass

import yaml

from e3cycle import gas
from e3cycle.cycle import DATA

T_INLET, P_INLET = 288.15, 101325.0


@dataclass
class StationPoint:
    sl: int
    pct_imm: float
    r: float
    z: float
    t0: float
    p0: float
    ts: float
    cz: float
    ctheta: float
    phi_deg: float


def load():
    return yaml.safe_load((DATA / "hpc-vector-diagrams.yaml").read_text())


def _key(row):
    return "IGV" if row["row"] == "igv" else f"{'R' if row['row'] == 'rotor' else 'S'}{row['stage']}"


def station_points(xxi, row, which):
    """the 12 streamline points of one station, in the absolute frame"""
    kind = "rotor_station" if row["row"] == "rotor" else "stator_station"
    cols = xxi["columns"][kind]
    igv_ref = dict(zip(xxi["columns"]["stator_station"], xxi["rows"][0]["inlet"][0]))
    out = []
    for raw in row[which]:
        d = dict(zip(cols, raw))
        t0 = T_INLET * d["tt_ratio"] / igv_ref["tt_ratio"]
        p0 = P_INLET * d["pt_ratio"] / igv_ref["pt_ratio"]
        cz = d["cz_m_s"]
        if row["row"] == "rotor":
            ctheta = d["u_m_s"] - cz * math.tan(math.radians(d["beta_deg"]))
        else:
            ctheta = cz * math.tan(math.radians(d["alpha_deg"]))
        c2 = cz * cz + ctheta * ctheta
        ts = gas.t_from_h(gas.h(t0) - 0.5 * c2, guess=t0 - c2 / 2000)
        out.append(StationPoint(d["sl"], d["pct_imm"], d["radius_cm"] / 100, d["z_cm"] / 100,
                                t0, p0, ts, cz, ctheta, d["phi_deg"]))
    return sorted(out, key=lambda p: p.r)


def _ddr(vals, radii, i):
    """central difference, one-sided at the ends"""
    if i == 0:
        return (vals[1] - vals[0]) / (radii[1] - radii[0])
    if i == len(vals) - 1:
        return (vals[-1] - vals[-2]) / (radii[-1] - radii[-2])
    return (vals[i + 1] - vals[i - 1]) / (radii[i + 1] - radii[i - 1])


def residual(points):
    """left- and right-hand sides of simple radial equilibrium at every
    streamline, and the residual normalised by the largest single term.

    The left-hand side is written analytically rather than as a difference
    of two separately differenced quantities. dh0/dr and T ds/dr are each
    an order of magnitude larger than their difference (a 10:1
    cancellation on this machine), so differencing enthalpy and entropy
    separately and subtracting amplifies the finite-difference error by
    that factor. Substituting h0 = h(T0) and s = phi(T0) - R ln p0:

        dh0/dr - T ds/dr = cp(T0) (1 - T/T0) dT0/dr + (T R / p0) dp0/dr

    which differences T0 and p0 once each and does the cancellation in
    closed form."""
    r = [p.r for p in points]
    t0 = [p.t0 for p in points]
    p0 = [p.p0 for p in points]
    cz = [p.cz for p in points]
    rct = [p.r * p.ctheta for p in points]
    out = []
    for i, p in enumerate(points):
        dt0, dp0 = _ddr(t0, r, i), _ddr(p0, r, i)
        cp = gas.cp(p.t0)
        lhs = cp * (1 - p.ts / p.t0) * dt0 + p.ts * gas.R_AIR / p.p0 * dp0
        cz_term = p.cz * _ddr(cz, r, i)
        vortex = p.ctheta / p.r * _ddr(rct, r, i)
        rhs = cz_term + vortex
        scale = max(abs(cz_term), abs(vortex), abs(lhs), 1.0)
        out.append(dict(sl=p.sl, pct_imm=p.pct_imm, r=p.r, lhs=lhs, rhs=rhs,
                        residual=lhs - rhs, normalised=(lhs - rhs) / scale,
                        thermal=cp * (1 - p.ts / p.t0) * dt0, pressure=p.ts * gas.R_AIR / p.p0 * dp0,
                        cz_term=cz_term, vortex=vortex, phi_deg=p.phi_deg))
    return out


def all_stations(interior_only=True):
    xxi = load()
    out = []
    for row in xxi["rows"]:
        for which in ("inlet", "exit"):
            pts = station_points(xxi, row, which)
            res = residual(pts)
            if interior_only:
                res = res[1:-1]
            out.append(dict(row=_key(row), which=which, points=pts, residual=res,
                            z=sum(p.z for p in pts) / len(pts)))
    return out


def summary():
    st = all_stations()
    rows = []
    for s in st:
        n = [abs(x["normalised"]) for x in s["residual"]]
        rows.append(dict(row=s["row"], which=s["which"], z=s["z"], mean=sum(n) / len(n), worst=max(n),
                         scale=max(max(abs(x["lhs"]), abs(x["rhs"])) for x in s["residual"])))
    return rows


if __name__ == "__main__":
    rows = summary()
    print("simple radial equilibrium, station by station (12 streamlines, interior 10 differenced)")
    print(f"{'station':<10}{'z cm':>8}{'|resid| mean':>14}{'worst':>9}{'term scale kJ/kg/m':>20}")
    for r in rows:
        print(f"{r['row'] + ' ' + r['which'][:2]:<10}{r['z'] * 100:>8.1f}{r['mean']:>14.3f}{r['worst']:>9.3f}{r['scale'] / 1000:>20.0f}")
    allr = [x for s in all_stations() for x in s["residual"]]
    n = [abs(x["normalised"]) for x in allr]
    print(f"\n{len(allr)} interior points over {len(rows)} stations: mean |residual| {sum(n) / len(n):.3f} of the larger term, worst {max(n):.3f}")


# ---------------------------------------------------------------------------
# What simple radial equilibrium throws away: the streamline curvature term.
# Table XXI prints the streamline slope phi at every station, so the
# curvature d(phi)/dm follows from consecutive stations along a streamline
# and the discarded term can be evaluated instead of assumed small.
# ---------------------------------------------------------------------------

def slope_check(xxi):
    """the printed streamline slope against atan(dr/dz) from the printed
    coordinates -- the column's own sign convention, settled by geometry"""
    st = gas_path_stations(xxi)
    out = []
    for i in range(1, len(st) - 1):
        label, pts = st[i]
        prev, nxt = st[i - 1][1], st[i + 1][1]
        for k, p in enumerate(pts):
            a, b = prev[k], nxt[k]
            if abs(b.z - a.z) < 1e-6:
                continue
            geo = math.degrees(math.atan2(b.r - a.r, b.z - a.z))
            out.append(dict(row=label, sl=p.sl, printed=p.phi_deg, geometric=geo))
    return out


def gas_path_stations(xxi):
    """every station in gas-path order, as (label, points) with the points
    sorted by streamline number so a streamline can be followed"""
    out = []
    for row in xxi["rows"]:
        for which in ("inlet", "exit"):
            pts = sorted(station_points(xxi, row, which), key=lambda p: p.sl)
            out.append((f"{_key(row)} {which[:2]}", pts))
    return sorted(out, key=lambda t: sum(p.z for p in t[1]) / len(t[1]))


def curvature_terms(xxi):
    """the term simple radial equilibrium discards, -c_m^2 cos(phi) dphi/dm,
    at every interior station, per streamline.

    Sign: a meridional streamline concave outward (phi increasing along m)
    accelerates its fluid outward, which needs dp/dr < 0, so the term
    enters the right-hand side negative. Table XXI's phi column is
    confirmed against atan(dr/dz) from its own coordinates (0.23 deg mean),
    so the sign is the equation's, not the column's."""
    stations = gas_path_stations(xxi)
    out = {}
    for i in range(1, len(stations) - 1):
        label, pts = stations[i]
        prev, nxt = stations[i - 1][1], stations[i + 1][1]
        terms = {}
        for k, p in enumerate(pts):
            a, b = prev[k], nxt[k]
            dm = math.hypot(b.z - a.z, b.r - a.r)
            if dm < 1e-6:
                continue
            dphi = math.radians(b.phi_deg - a.phi_deg)
            cm = p.cz / math.cos(math.radians(p.phi_deg))
            terms[p.sl] = -cm * cm * math.cos(math.radians(p.phi_deg)) * dphi / dm
        out[label] = terms
    return out


def balance_with_curvature():
    """the residual of simple radial equilibrium, and the same residual
    after the curvature term is added to the right-hand side"""
    xxi = load()
    curv = curvature_terms(xxi)
    rows = []
    for label, pts in gas_path_stations(xxi):
        if label not in curv:
            continue
        res = residual(sorted(pts, key=lambda p: p.r))
        c = curv[label]
        simple, full, scales = [], [], []
        for x in res[1:-1]:
            if x["sl"] not in c:
                continue
            scale = max(abs(x["cz_term"]), abs(x["vortex"]), abs(x["lhs"]), 1.0)
            simple.append(abs(x["residual"]) / scale)
            full.append(abs(x["residual"] - c[x["sl"]]) / scale)
            scales.append(scale)
        if simple:
            rows.append(dict(row=label, simple=sum(simple) / len(simple), full=sum(full) / len(full),
                             n=len(simple), scale=max(scales)))
    return rows


def main_curvature():
    rows = balance_with_curvature()
    print("simple radial equilibrium, and the same with the streamline-curvature term restored")
    print(f"{'station':<10}{'n':>4}{'|resid| simple':>16}{'with curvature':>16}{'change':>9}")
    for r in rows:
        print(f"{r['row']:<10}{r['n']:>4}{r['simple']:>16.3f}{r['full']:>16.3f}{(r['full'] - r['simple']):>9.3f}")
    s = sum(r["simple"] * r["n"] for r in rows) / sum(r["n"] for r in rows)
    f = sum(r["full"] * r["n"] for r in rows) / sum(r["n"] for r in rows)
    better = sum(1 for r in rows if r["full"] < r["simple"])
    print(f"\n{sum(r['n'] for r in rows)} points over {len(rows)} stations")
    print(f"  simple radial equilibrium      mean |residual| {s:.3f} of the largest term")
    print(f"  with the curvature term        mean |residual| {f:.3f}   ({(1 - f / s) * 100:+.0f} %)")
    print(f"  stations improved: {better} of {len(rows)}")


if __name__ == "__main__" and "--curvature" in __import__("sys").argv:
    main_curvature()

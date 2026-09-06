"""C3 unit 13: the LPT's real airfoil coordinates, its throats and its
Zweifel numbers.

Stage A transcribed all 30 LPT sections as (Z, R, R-theta) triples. Two
published relations can be tested directly against them:

  1. the throat. R&M 2974 Fig 5 relates a turbine's outlet gas angle to
     cos^-1(o/s); Table II prints the outlet angles. The coordinates give
     o/s. Neither was used to get the other.
  2. Zweifel. Table III prints a Zweifel number for all ten rows;
     psi_Z = 2 (s/b_x) cos^2(a2) (tan a1 + tan a2) can be evaluated from
     the coordinates' axial width and the Table II angles.

STEP0.md, unit 13."""
from __future__ import annotations

import math
from dataclasses import dataclass

import yaml

from e3cycle.cycle import DATA
from e3cycle.stations import find_key
from meanline.losses import _interp, AM
from meanline.sections import load_section, section_geometry

IN = 0.0254
ROWS = ["S1", "R1", "S2", "R2", "S3", "R3", "S4", "R4", "S5", "R5"]
SPANS = {10: "hub", 50: "pitch", 90: "tip"}


def load():
    aero = yaml.safe_load((DATA / "lpt-aero.yaml").read_text())
    design = yaml.safe_load((DATA / "lpt-design.yaml").read_text())
    counts_v = find_key(aero, "vane_counts") or [72, 102, 96, 114, 120]
    counts_b = find_key(design, "blade_count") or [120, 122, 122, 156, 110]
    return aero, design, counts_v, counts_b


def _table_iii(aero):
    def walk(d):
        if isinstance(d, dict):
            if "zweifel_coefficient" in d:
                return d
            for v in d.values():
                r = walk(v)
                if r:
                    return r
    return walk(aero)


def blade_count(row, counts_v, counts_b):
    n = int(row[1])
    return counts_v[n - 1] if row[0] == "S" else counts_b[n - 1]


def suction_curvature_radius(row, span, from_frac, to_frac=1.0):
    """e, the mean radius of curvature of the convex surface between the
    throat and the trailing edge (R&M 2974 Fig 3's definition), by fitting
    a circle to that arc of the transcribed coordinates"""
    pts = load_section(row, span)["suction"]
    lo, hi = int(from_frac * (len(pts) - 1)), int(to_frac * (len(pts) - 1))
    arc = [(z * IN, t * IN) for z, t in pts[lo:hi + 1]]
    if len(arc) < 5:
        return None
    # algebraic circle fit: x^2 + y^2 + Dx + Ey + F = 0
    n = len(arc)
    sx = sum(x for x, _ in arc); sy = sum(y for _, y in arc)
    sxx = sum(x * x for x, _ in arc); syy = sum(y * y for _, y in arc)
    sxy = sum(x * y for x, y in arc)
    sxxx = sum(x ** 3 for x, _ in arc); syyy = sum(y ** 3 for _, y in arc)
    sxyy = sum(x * y * y for x, y in arc); sxxy = sum(x * x * y for x, y in arc)
    a11, a12, a13 = sxx, sxy, sx
    a21, a22, a23 = sxy, syy, sy
    a31, a32, a33 = sx, sy, float(n)
    b1 = -(sxxx + sxyy); b2 = -(sxxy + syyy); b3 = -(sxx + syy)
    det = (a11 * (a22 * a33 - a23 * a32) - a12 * (a21 * a33 - a23 * a31)
           + a13 * (a21 * a32 - a22 * a31))
    if abs(det) < 1e-20:
        return None
    D = (b1 * (a22 * a33 - a23 * a32) - a12 * (b2 * a33 - a23 * b3)
         + a13 * (b2 * a32 - a22 * b3)) / det
    E = (a11 * (b2 * a33 - a23 * b3) - b1 * (a21 * a33 - a23 * a31)
         + a13 * (a21 * b3 - b2 * a31)) / det
    F = (a11 * (a22 * b3 - b2 * a32) - a12 * (a21 * b3 - b2 * a31)
         + b1 * (a21 * a32 - a22 * a31)) / det
    r2 = 0.25 * (D * D + E * E) - F
    return math.sqrt(r2) if r2 > 0 else None


def throat_from_coordinates(row, span, pitch_m):
    """the shortest distance from one blade's surface to the next, one pitch
    away in r-theta. A turbine passage accelerates, so its throat is near
    the trailing edge; the whole surface is searched anyway."""
    pts = load_section(row, span)
    suc = [(z * IN, t * IN) for z, t in pts["suction"]]
    # the neighbouring blade sits one pitch away; the sections are stored with
    # r-theta increasing either way depending on the row, so try both and keep
    # whichever gives a real passage -- and keep the throat position from the
    # SAME neighbour, or the curvature arc that follows will be measured in
    # the wrong place (it was, on every stator, until this was fixed)
    best, at = float("inf"), None
    for sign in (+1, -1):
        nxt = [(z * IN, t * IN + sign * pitch_m) for z, t in pts["pressure"]]
        for i, (pz, pt) in enumerate(suc):
            for qz, qt in nxt:
                d = (pz - qz) ** 2 + (pt - qt) ** 2
                if d < best:
                    best, at = d, i / (len(suc) - 1)
    return math.sqrt(best), at


@dataclass
class LptRow:
    row: str
    span: int
    radius_m: float
    count: int
    pitch_m: float
    o_over_s: float
    acos_o_s_deg: float
    alpha2_rule: float
    alpha2_printed: float
    axial_width_m: float
    s_over_e: float
    alpha2_full_rule: float
    chord_m: float
    stagger_deg: float
    zweifel: float
    zweifel_printed: float


def analyse():
    aero, design, cv, cb = load()
    t2 = find_key(aero, "vector_diagrams")
    t3 = _table_iii(aero)
    zw = dict(zip(t3["rows"], t3["zweifel_coefficient"]))
    out = []
    for row in ROWS:
        n = int(row[1])
        stage = t2[f"stage{n}"]
        count = blade_count(row, cv, cb)
        for span, where in SPANS.items():
            idx = {"hub": 0, "pitch": 1, "tip": 2}[where]
            pts = load_section(row, span)
            radius = sum(r for _, r in [(0, 0)]) if False else None
            rs = []
            with open(DATA / "lpt-airfoils" / f"{row}_{span}.csv") as f:
                for line in f:
                    if line.startswith("#") or line.startswith("surface"):
                        continue
                    rs.append(float(line.split(",")[2]))
            radius = sum(rs) / len(rs) * IN
            pitch = 2 * math.pi * radius / count
            o, at = throat_from_coordinates(row, span, pitch)
            g = section_geometry(row, span)
            # the exit angle the row is being asked to produce
            if row[0] == "S":
                a2 = stage["stator_exit_angle_deg"][idx]
                a1 = 0.0 if n == 1 else abs(t2[f"stage{n-1}"]["stage_exit_swirl_deg"][idx])
            else:
                a2 = stage["rotor_rel_exit_angle_deg"][idx]
                a1 = stage["rotor_rel_inlet_angle_deg"][idx]
            acos = math.degrees(math.acos(min(o / pitch, 1.0)))
            f5 = AM["fig5_outlet_angle"]
            rule = _interp(acos, f5["acos_o_over_s_deg"], f5["alpha2_star_deg"])
            # equation (1): alpha2 = alpha2* - 4 (s/e), which in the report's
            # sign convention increases the magnitude of the outlet angle
            e = suction_curvature_radius(row, span, at if at else 0.5)
            s_e = pitch / e if e else 0.0
            full = rule + 4.0 * s_e
            bx = g["axial_chord_in"] * IN
            zwv = 2 * (pitch / bx) * math.cos(math.radians(a2)) ** 2 * (
                math.tan(math.radians(a1)) + math.tan(math.radians(a2)))
            out.append(LptRow(row=row, span=span, radius_m=radius, count=count, pitch_m=pitch,
                              o_over_s=o / pitch, acos_o_s_deg=acos, alpha2_rule=rule,
                              alpha2_printed=a2, axial_width_m=bx, s_over_e=s_e,
                              alpha2_full_rule=full, chord_m=g["chord_in"] * IN,
                              stagger_deg=g["stagger_deg"], zweifel=zwv, zweifel_printed=zw[row]))
    return out


if __name__ == "__main__":
    import statistics
    res = analyse()
    print(f"{'row':<5}{'span':>5}{'r cm':>7}{'N':>5}{'pitch cm':>10}{'o/s':>7}"
          f"{'acos o/s':>10}{'a2 rule':>9}{'a2 Tbl II':>11}{'diff':>7}")
    for r in res:
        print(f"{r.row:<5}{r.span:>5}{r.radius_m*100:>7.2f}{r.count:>5}{r.pitch_m*100:>10.3f}"
              f"{r.o_over_s:>7.3f}{r.acos_o_s_deg:>10.2f}{r.alpha2_rule:>9.2f}"
              f"{r.alpha2_printed:>11.2f}{r.alpha2_rule - r.alpha2_printed:>7.2f}")
    d = [r.alpha2_rule - r.alpha2_printed for r in res]
    print(f"\noutlet angle, Fig 5 alone (alpha2*)      vs Table II: mean {statistics.mean(d):+.2f} deg, "
          f"rms {math.sqrt(sum(x*x for x in d)/len(d)):.2f}, worst {max(abs(x) for x in d):.2f}")
    d2 = [r.alpha2_full_rule - r.alpha2_printed for r in res]
    print(f"outlet angle, equation (1) with -4(s/e) vs Table II: mean {statistics.mean(d2):+.2f} deg, "
          f"rms {math.sqrt(sum(x*x for x in d2)/len(d2)):.2f}, worst {max(abs(x) for x in d2):.2f}")
    se = [r.s_over_e for r in res]
    print(f"s/e from the coordinates: {min(se):.3f}-{max(se):.3f} (R&M worked example: 0.279 vane, 0.355 rotor)")
    print(f"\n{'row':<5}{'span':>5}{'s/bx':>8}{'Zweifel':>10}{'Table III':>11}{'diff':>8}")
    for r in res:
        print(f"{r.row:<5}{r.span:>5}{r.pitch_m/r.axial_width_m:>8.3f}{r.zweifel:>10.3f}"
              f"{r.zweifel_printed:>11.3f}{r.zweifel - r.zweifel_printed:>8.3f}")
    dz = [r.zweifel - r.zweifel_printed for r in res if r.span == 50]
    print(f"\nZweifel at pitch vs Table III: mean {statistics.mean(dz):+.3f}, "
          f"rms {math.sqrt(sum(x*x for x in dz)/len(dz)):.3f}")

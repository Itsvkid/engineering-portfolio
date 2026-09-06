"""Row geometry from the LPT airfoil sections (data/lpt-airfoils): chord,
maximum thickness, trailing-edge thickness and stagger at a span."""
from __future__ import annotations

import csv
import math
import pathlib

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"


def load_section(row, span):
    pts = {"suction": [], "pressure": []}
    with open(DATA / "lpt-airfoils" / f"{row}_{span}.csv") as f:
        for r in csv.DictReader(l for l in f if not l.startswith("#")):
            pts[r["surface"]].append((float(r["z_in"]), float(r["rtheta_in"])))
    return pts


def section_geometry(row, span=50):
    """chord (LE to TE), maximum thickness normal to the chord line,
    trailing-edge thickness (the gap between the two surfaces' last
    points) and stagger from axial, all from the (z, r theta) section"""
    p = load_section(row, span)
    s, q = p["suction"], p["pressure"]
    le = s[0]
    te = ((s[-1][0] + q[-1][0]) / 2, (s[-1][1] + q[-1][1]) / 2)
    chord = math.dist(le, te)
    ux, uy = (te[0] - le[0]) / chord, (te[1] - le[1]) / chord
    nx, ny = -uy, ux

    def along_normal(pts):
        return [((x - le[0]) * ux + (y - le[1]) * uy, (x - le[0]) * nx + (y - le[1]) * ny) for x, y in pts]

    sa, qa = along_normal(s), along_normal(q)

    def at(pts, x):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if min(x0, x1) <= x <= max(x0, x1) and x1 != x0:
                return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
        return None

    t_max = 0.0
    for k in range(1, 200):
        x = chord * k / 200
        ys, yq = at(sa, x), at(qa, x)
        if ys is not None and yq is not None:
            t_max = max(t_max, abs(ys - yq))
    te_thickness = math.dist(s[-1], q[-1])
    stagger = math.degrees(math.atan2(abs(te[1] - le[1]), te[0] - le[0]))
    return dict(chord_in=chord, t_over_c=t_max / chord, te_in=te_thickness, stagger_deg=stagger, axial_chord_in=te[0] - le[0])


if __name__ == "__main__":
    for row in ["S1", "R1", "S2", "R2", "S3", "R3", "S4", "R4", "S5", "R5"]:
        g = section_geometry(row)
        print(f"{row}: chord {g['chord_in']:.3f} in, axial {g['axial_chord_in']:.3f}, t/c {g['t_over_c']:.3f}, te {g['te_in']:.4f} in, stagger {g['stagger_deg']:.1f} deg")

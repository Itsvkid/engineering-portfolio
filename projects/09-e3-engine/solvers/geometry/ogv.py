"""Stage G unit G2: the inner OGV, swept and leaned.

Stage C3 asks for *booster rows and inner OGV with the published sweep 60°
/ lean 0-20°*. The sweep and lean are published for the **inner OGV only**
-- `fan-design.yaml`'s `booster_rotor_airfoil` carries neither, and nothing
else in the fan report gives the booster one. G1 already builds the booster
on a radial stacking line and that is correct rather than a shortcut. This
module is the OGV.

Table VII p.92 gives the row completely -- 64 vanes, 11.61 cm long, chord
9.25 cm at the root to 5.44 at the tip, stagger 18.40 to 21.53 degrees,
camber 55.38 to 62.38, tm/c 0.053 to 0.062. Section II.D gives the shape of
the stacking axis:

    curved in space, swept aft 60 degrees from radial, leaned
    circumferentially from 0 at the OD to 20 degrees at the ID with the
    pressure side facing the axis

and the sentence that decides how the sections are placed:

    sections: on planes perpendicular to the swept and leaned axis

That last line is why this vane needs its own module. Every other row in
this project is built by `wrapped_wire`, which lays a planar section onto a
**cylinder** at a fixed radius -- the right construction for a radially
stacked blade and the wrong one here. These sections sit on planes normal
to a curve, and the curve leaves the meridional plane.

STEP0.md, unit G2."""
from __future__ import annotations

import functools
import math

import cadquery as cq
import yaml

from e3cycle.cycle import DATA

CM = 0.01
DEG = math.pi / 180.0

#: from section II.D, the one number the sentence gives
SWEEP_DEG = 60.0
#: the two ends the sentence gives; linear between them is the reading
LEAN_ID_DEG = 20.0
LEAN_OD_DEG = 0.0

#: Does Table VII's 11.61 cm measure radially, or ALONG the swept axis?
#: The plain reading of "length" is radial, and STEP0 named it before the
#: run, so it is the default. `swept_span_reading()` reports the other, and
#: finding 182 gives the two independent reasons it is the likelier one.
LENGTH_IS_ALONG_AXIS = False


def radial_span_m():
    """The vane's radial span, on whichever reading is selected."""
    L = table_vii()["length_cm"] * CM
    return L * math.cos(SWEEP_DEG * DEG) if LENGTH_IS_ALONG_AXIS else L


def table_vii(stator="inner_ogv"):
    rows = yaml.safe_load((DATA / "fan-design.yaml").read_text())[
        "fan_stator"]["geometry"]["rows"]
    return next(r for r in rows if r["stator"] == stator)


def placement():
    """The one number no report prints, read from `data/` and not from
    here -- unit J1 finding 159's rule applied to a second assumption."""
    p = yaml.safe_load((DATA / "fan-design.yaml").read_text())[
        "inner_ogv_placement"]
    assert p["status"] == "assumed"
    return p


def lean_deg(f):
    """Lean angle at span fraction f, 0 at the ID and 1 at the OD."""
    return LEAN_ID_DEG + (LEAN_OD_DEG - LEAN_ID_DEG) * f


def stacking_axis(n=41):
    """The curve the sections sit on, as points and unit tangents.

    Built by integrating the two published angles outward from the hub:

      dz/dr = tan(sweep)      -- aft, constant 60 degrees from radial
      dy/dr = -tan(lean(r))   -- circumferential, 20 degrees at the ID
                                 falling to 0 at the OD

    `y` is arc length round the axis, so the point at radius r sits at
    angle theta = y / r. The sign puts the pressure side towards the axis,
    which is what the report says the lean is for."""
    pl = placement()
    r0 = pl["hub_radius_m"]
    span = radial_span_m()
    pts, z, y = [], 0.0, 0.0
    dr = span / (n - 1)
    for i in range(n):
        f = i / (n - 1)
        r = r0 + f * span
        if i:
            fm = (i - 0.5) / (n - 1)
            z += dr * math.tan(SWEEP_DEG * DEG)
            y += -dr * math.tan(lean_deg(fm) * DEG)
        th = y / r
        pts.append(dict(f=f, r=r, z=z, y=y, theta=th,
                        point=(z, r * math.sin(th), r * math.cos(th))))
    # unit tangents by central difference on the 3D points
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]["point"]
        b = pts[min(i + 1, n - 1)]["point"]
        t = [b[k] - a[k] for k in range(3)]
        m = math.sqrt(sum(v * v for v in t))
        p["tangent"] = tuple(v / m for v in t)
    return pts


def _section_2d(f, n=180):
    """The Table VII section at span fraction f, in its own plane.

    Circular-arc camber with a quarter-sine thickness, the construction
    C3 unit 12 uses for every other row in this module, so the shape rule
    is shared and only the placement is new."""
    t = table_vii()
    chord = (t["chord_root_cm"] + f * (t["chord_tip_cm"] - t["chord_root_cm"])) * CM
    camber = (t["camber_root_deg"] + f * (t["camber_tip_deg"] - t["camber_root_deg"]))
    stagger = (t["stagger_root_deg"] + f * (t["stagger_tip_deg"] - t["stagger_root_deg"]))
    tmc = t["tm_c_root"] + f * (t["tm_c_tip"] - t["tm_c_root"])

    half = camber * DEG / 2.0
    # circular arc through (0,0) and (chord,0) with total turning `camber`
    radius = chord / (2 * math.sin(half)) if half > 1e-9 else 1e9
    upper, lower = [], []
    for i in range(n + 1):
        u = i / n
        ang = -half + 2 * half * u
        xc = radius * (math.sin(ang) + math.sin(half))
        yc = radius * (math.cos(ang) - math.cos(half))
        th = tmc * chord * math.sin(math.pi * u)          # quarter-sine, closed
        # camber-line slope for the surface normal
        dx, dy = math.cos(ang), -math.sin(ang)
        nx, ny = -dy, dx
        upper.append((xc + nx * th / 2, yc + ny * th / 2))
        lower.append((xc - nx * th / 2, yc - ny * th / 2))
    pts = upper + lower[::-1][1:-1]
    c, s = math.cos(stagger * DEG), math.sin(stagger * DEG)
    return [(x * c - y * s, x * s + y * c) for x, y in pts]


def _plane_at(p):
    """A cadquery Plane whose normal is the local tangent -- which is what
    'sections on planes perpendicular to the axis' means."""
    origin = cq.Vector(*p["point"])
    normal = cq.Vector(*p["tangent"])
    # x of the section plane points aft-ish, made orthogonal to the normal
    ref = cq.Vector(1, 0, 0)
    if abs(ref.dot(normal)) > 0.95:
        ref = cq.Vector(0, 1, 0)
    xdir = (ref - normal.multiply(ref.dot(normal))).normalized()
    return cq.Plane(origin=origin, xDir=xdir, normal=normal)


def sections(n_span=9):
    """The wires the vane is lofted through, each on its own normal plane."""
    axis = stacking_axis()
    out = []
    for i in range(n_span):
        f = i / (n_span - 1)
        p = min(axis, key=lambda q: abs(q["f"] - f))
        plane = _plane_at(p)
        pts2d = _section_2d(f)
        w = cq.Workplane(plane).polyline(pts2d).close().wire().val()
        out.append(dict(f=f, wire=w, plane=plane, axis_point=p))
    return out


def solid(n_span=9):
    from geometry.blades import loft_capped
    return loft_capped([s["wire"] for s in sections(n_span)])


def trapezoid_volume(n=201):
    """The integral the CAD is checked against: section area along the
    stacking axis, trapezoidal. Area comes from the same 2-D section the
    loft uses, so this checks the CAD and not the aerofoil."""
    axis = stacking_axis(n)
    total = 0.0
    prev_a = prev_s = None
    for p in axis:
        pts = _section_2d(p["f"])
        a = abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1]
                    - pts[(i + 1) % len(pts)][0] * pts[i][1]
                    for i in range(len(pts)))) / 2
        # arc length along the axis
        s = p["r"]
        if prev_a is not None:
            dz = p["z"] - prev_z
            dy = p["y"] - prev_y
            dr = p["r"] - prev_r
            ds = math.sqrt(dz * dz + dy * dy + dr * dr)
            total += 0.5 * (a + prev_a) * ds
        prev_a, prev_s = a, s
        prev_z, prev_y, prev_r = p["z"], p["y"], p["r"]
    return total


def aspect_ratios():
    """Table VII prints an aspect ratio per row. Does it reproduce from the
    same table's own length and chords? On stage 1 yes, to 0.2 %. On the
    other two rows no. Reported, because it is a property of the table."""
    out = []
    for row in yaml.safe_load((DATA / "fan-design.yaml").read_text())[
            "fan_stator"]["geometry"]["rows"]:
        cm_ = (row["chord_root_cm"] + row["chord_tip_cm"]) / 2
        implied = row["length_cm"] / cm_
        out.append(dict(row=row["stator"], length_cm=row["length_cm"],
                        chord_mean_cm=cm_, implied=implied,
                        printed=row["aspect_ratio"],
                        err_pct=(implied / row["aspect_ratio"] - 1) * 100))
    return out


def swept_span_reading():
    """The other reading of Table VII's 'length', and what it would mean.

    If 11.61 cm is measured ALONG a 60-degree swept axis rather than
    radially, the radial span is 11.61 cos 60 = 5.81 cm and the aspect
    ratio on the mean chord is 0.79 -- against the 0.83 the fan report's
    Appendix A prints for this row. Suggestive and not adopted: the same
    reading does nothing for the bypass row, which is 49 % out and is not
    described as swept."""
    t = table_vii()
    cm_ = (t["chord_root_cm"] + t["chord_tip_cm"]) / 2
    radial = t["length_cm"] * math.cos(SWEEP_DEG * DEG)
    return dict(printed_length_cm=t["length_cm"], radial_if_swept_cm=radial,
                ar_on_radial=radial / cm_, appendix_a_ar=0.83,
                adopted=False,
                why_not=("the plain reading of 'length' is the radial span, "
                         "and this reading explains nothing about the bypass "
                         "row's 49 % gap"))


def summary():
    t, pl = table_vii(), placement()
    ax = stacking_axis()
    s = solid()
    trap = trapezoid_volume()
    L = ["Stage G unit G2 -- the inner OGV, swept and leaned", ""]
    L.append(f"   Table VII: {t['vanes']} vanes, {t['length_cm']} cm long, "
             f"chord {t['chord_root_cm']}->{t['chord_tip_cm']} cm")
    L.append(f"   stacking axis: swept {SWEEP_DEG:.0f} deg aft, leaned "
             f"{LEAN_ID_DEG:.0f} deg at the ID to {LEAN_OD_DEG:.0f} at the OD")
    L.append(f"   hub radius {pl['hub_radius_m']*100:.1f} cm (ASSUMED, "
             f"range {pl['range_m'][0]*100:.0f}-{pl['range_m'][1]*100:.0f})")
    L.append(f"   axis runs {ax[-1]['z']*100:6.2f} cm aft and "
             f"{ax[-1]['y']*100:6.2f} cm round over the span")
    L += ["", f"   CAD volume      {s.Volume()*1e6:9.2f} cm3",
          f"   trapezoid       {trap*1e6:9.2f} cm3",
          f"   difference      {(s.Volume()/trap - 1)*100:9.2f} %",
          f"   valid solid     {s.isValid()}"]
    L += ["", "   Table VII's aspect ratio against its own length and chords:"]
    for r in aspect_ratios():
        L.append(f"      {r['row']:<12} implied {r['implied']:6.3f}  "
                 f"printed {r['printed']:6.3f}  {r['err_pct']:+7.1f} %")
    sw = swept_span_reading()
    L += ["", f"   the other reading of 'length': radial span would be "
          f"{sw['radial_if_swept_cm']:.2f} cm,",
          f"   aspect ratio {sw['ar_on_radial']:.3f} against Appendix A's "
          f"{sw['appendix_a_ar']}. Not adopted."]
    return "\n".join(L)


if __name__ == "__main__":
    print(summary())


# ---------------------------------------------------------------------------
# Unit G2b -- the curved-axis reference integral
# ---------------------------------------------------------------------------

def _polygon_area_centroid(pts):
    """Signed area and centroid of a closed polygon, in its own plane."""
    a = 0.0
    cx = cy = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        a += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    a *= 0.5
    if abs(a) < 1e-18:
        return 0.0, (0.0, 0.0)
    return abs(a), (cx / (6.0 * a), cy / (6.0 * a))


@functools.lru_cache(maxsize=8)
def _pappus_cached(n, lean, sweep, along):
    return _pappus_volume_uncached(n)


def pappus_volume(n=201, axis=None, section=None):
    """Memoised on the module state the result depends on, because building
    201 cadquery Planes is the slow part and the test suite asks for this
    several times."""
    if axis is None and section is None:
        return _pappus_cached(n, LEAN_ID_DEG, SWEEP_DEG, LENGTH_IS_ALONG_AXIS)
    return _pappus_volume_uncached(n, axis, section)


def _pappus_volume_uncached(n=201, axis=None, section=None):
    """The reference volume for a section swept along a CURVED axis.

    V = integral of A(s) * (1 - c_bar . dT/ds) ds, which is Pappus's second
    theorem in differential form: a point offset by d from the axis sweeps
    an arc ds(1 - kappa d.N), so the section's own centroid offset is the
    only first-order term. Where the axis is straight dT/ds vanishes and
    this is `trapezoid_volume` exactly -- so no straight-stacked row in this
    project moves.

    `axis` and `section` are injectable so the exact torus case below can
    validate the machinery without going near the OGV.
    """
    axis = axis if axis is not None else stacking_axis(n)
    section = section if section is not None else _section_2d
    n = len(axis)

    # arc length and unit tangent at every station, then dT/ds by central
    # difference on arc length
    s = [0.0]
    for i in range(1, n):
        a, b = axis[i - 1]["point"], axis[i]["point"]
        s.append(s[-1] + math.sqrt(sum((b[k] - a[k]) ** 2 for k in range(3))))
    tang = [p["tangent"] for p in axis]
    dtds = []
    for i in range(n):
        lo, hi = max(i - 1, 0), min(i + 1, n - 1)
        ds = s[hi] - s[lo]
        dtds.append(tuple((tang[hi][k] - tang[lo][k]) / ds if ds else 0.0
                          for k in range(3)))

    total = 0.0
    prev = None
    for i, p in enumerate(axis):
        pts = section(p["f"])
        a, (cx, cy) = _polygon_area_centroid(pts)
        plane = _plane_at(p)
        c3 = [plane.xDir.toTuple()[k] * cx + plane.yDir.toTuple()[k] * cy
              for k in range(3)]
        factor = 1.0 - sum(c3[k] * dtds[i][k] for k in range(3))
        w = a * factor
        if prev is not None:
            total += 0.5 * (w + prev) * (s[i] - s[i - 1])
        prev = w
    return total


@functools.lru_cache(maxsize=8)
def torus_validation(R=1.0, a=0.1, e=0.04, n=721):
    """Band 1: the exact case, before the OGV.

    A circular section of radius `a` swept round a circle of radius `R`,
    with the stacking axis offset from the section centroid by `e` towards
    the centre. Pappus gives 2*pi*(R - e)*pi*a^2 exactly, and the plain
    trapezoidal integral gives 2*pi*R*pi*a^2 -- so the case has a known
    right answer AND a known wrong one.

    Returns (pappus, exact, trapezoid).
    """
    axis = []
    for i in range(n):
        f = i / (n - 1)
        th = 2.0 * math.pi * f
        # the axis circle sits at radius R + e, so its centroid circle -- the
        # axis point displaced by -e towards the centre -- is at radius R
        ra = R + e
        axis.append(dict(f=f, point=(ra * math.cos(th), ra * math.sin(th), 0.0)))
    for i, p in enumerate(axis):
        lo, hi = axis[max(i - 1, 0)]["point"], axis[min(i + 1, n - 1)]["point"]
        t = [hi[k] - lo[k] for k in range(3)]
        m = math.sqrt(sum(v * v for v in t))
        p["tangent"] = tuple(v / m for v in t)

    def circ(f, m=360):
        """a circle of radius `a` whose centre is offset by -e along the
        plane axis that points radially outward"""
        p = min(axis, key=lambda q: abs(q["f"] - f))
        pl = _plane_at(p)
        out = []
        for j in range(m):
            ang = 2.0 * math.pi * j / m
            out.append((a * math.cos(ang), a * math.sin(ang)))
        # find which plane direction is radial, and offset along it
        radial = (math.cos(2 * math.pi * f), math.sin(2 * math.pi * f), 0.0)
        ex = sum(pl.xDir.toTuple()[k] * radial[k] for k in range(3))
        ey = sum(pl.yDir.toTuple()[k] * radial[k] for k in range(3))
        return [(x - e * ex, y - e * ey) for x, y in out]

    exact = 2.0 * math.pi * R * math.pi * a * a
    return pappus_volume(axis=axis, section=circ), exact, \
        2.0 * math.pi * (R + e) * math.pi * a * a


def straight_axis_check(n=201):
    """Band 2: with no lean the axis is straight and the two integrals must
    be the same number."""
    global LEAN_ID_DEG
    keep = LEAN_ID_DEG
    try:
        LEAN_ID_DEG = 0.0
        return pappus_volume(n), trapezoid_volume(n)
    finally:
        LEAN_ID_DEG = keep

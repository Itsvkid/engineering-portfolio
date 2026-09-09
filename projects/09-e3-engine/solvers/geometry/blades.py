"""Stage G1: solid blade geometry, generated from the validated sections.

Stage G's first bullet: *blade rows from C3 sections — PF-06 extended to
arbitrary section stacks; every row, every count.*

PF-06 places its sections **planar**, stacked along the radius, and applies
the tangential offset "as a straight tangential distance rather than
conformally wrapped around the annulus — valid because chord is small next
to radius, **and stated here because it stops being valid if that ratio
isn't small**". On the E³ that ratio is *not* small: the HPC stage-1 rotor
has a 10.1 cm chord at a 19.1 cm root radius, so **chord/radius = 0.49**.
PF-06's own stated condition fails, so this module does the conformal wrap
instead:

    (x_axial, y_tangential) at radius r  ->  (x, r sin(y/r), r cos(y/r))

which puts every section on its own cylinder about the engine axis. That
is the extension Stage G asked for.

The wrap costs one piece of machinery. A wrapped section wire is **not
planar**, and OpenCASCADE's ThruSections cannot cap a non-planar wire: it
returns a shell with the two end faces missing, and the volume of an open
shell is meaningless — see finding 113, where a *flat rectangle* wrapped
through 1.5° reports exactly two-thirds of its true volume. So the loft is
built as a shell, the ends are capped with n-sided surfaces, and the result
is sewn into a solid and checked. Capped, it is exact.

Volume is the check that matters, because it is the one quantity the
analysis and the CAD must share: for arc-length tangential coordinates the
wrap is volume-preserving exactly, so a generated solid must reproduce
Stage F2's trapezoidal integral of the same sections. STEP0.md, unit G1."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import cadquery as cq
import yaml
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid, BRepBuilderAPI_Sewing
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections

from blading.sections import all_sections, section
from e3cycle.cycle import DATA
from mechanical.beam import closed_airfoil, polygon_properties
from mechanical.blade_frequency import _xxii_thickness
from meanline.sections import load_section

CM, IN = 0.01, 0.0254
SEW_TOL = 1.0e-6
POINTS_PER_SECTION = 80


MIN_SEGMENT = 1.0e-6            # m; shorter than this and OCC cannot make an edge


def _arc_resample(chain, n):
    """n points equally spaced along a polyline by arc length"""
    d = [0.0]
    for a, b in zip(chain, chain[1:]):
        d.append(d[-1] + math.dist(a, b))
    total = d[-1]
    out, j = [], 0
    for i in range(n):
        t = total * i / (n - 1)
        while j < len(d) - 2 and d[j + 1] < t:
            j += 1
        span = d[j + 1] - d[j]
        f = 0.0 if span <= 0 else (t - d[j]) / span
        out.append((chain[j][0] + f * (chain[j + 1][0] - chain[j][0]),
                    chain[j][1] + f * (chain[j + 1][1] - chain[j][1])))
    return out


def _decimate(pts, n=POINTS_PER_SECTION):
    """Resample the section to exactly n points, split at the trailing edge
    so that leading and trailing edges correspond between sections.

    Two things force this. The LPT appendix prints some coordinates twice
    -- R1_10 repeats the point at 5.552902, 13.819397, 0.146528 -- and a
    repeated point is a zero-length edge, which OCC refuses. And stride
    decimation gave LPT stator 5 ninety-three edges on two sections and
    ninety-two on the third, which is what ThruSections cannot loft
    (finding 114). Both go away if every section carries the same number
    of arc-length-spaced points. The transcription is untouched; the
    thinning happens here, at the geometry."""
    if math.dist(pts[0], pts[-1]) < MIN_SEGMENT:
        pts = pts[:-1]
    # the trailing edge is the point furthest from the leading edge
    te = max(range(1, len(pts)), key=lambda i: math.dist(pts[0], pts[i]))
    half = max(4, n // 2)
    a = _arc_resample(list(pts[:te + 1]), half)
    b = _arc_resample(list(pts[te:]) + [pts[0]], half)
    out = a + b[1:-1]
    dedup = []
    for q in out:
        if not dedup or math.dist(dedup[-1], q) > MIN_SEGMENT:
            dedup.append(q)
    return dedup


def wrapped_wire(radius, pts):
    """one section, conformally wrapped onto the cylinder of that radius"""
    p3 = [(x, radius * math.sin(y / radius), radius * math.cos(y / radius))
          for x, y in _decimate(pts)]
    return cq.Workplane().polyline(p3).close().wire().val()


CAP_TOLERANCES = (1.0e-4, 3.0e-4, 1.0e-3, 3.0e-3)


def _cap(wire, tolerances=CAP_TOLERANCES):
    """A face closing one end wire, at the tightest tolerance that works.

    `makeNSidedSurface` is the only tool here for a non-planar wire -- the
    end sections lie on cylinders, so `makeFromWires` refuses them -- and it
    is fragile. It fails on perfectly valid closed wires with nothing but
    "BRep_API: command not done", and whether it fails depends on where the
    points happen to land rather than on how many there are: changing a
    section's resampling, same edge count and same minimum segment, was
    enough to turn a working cap into a failing one.

    Its default tol3d of 1e-4 m is what fails. Loosening it one step to
    3e-4 or 1e-3 succeeds, so the tolerances are tried in order and the
    first that works is used. This is an END face -- the hub and tip ends of
    the blade, buried in the hub wall or up against the casing -- not a flow
    surface, and the volume check downstream will catch a cap that is
    actually wrong."""
    last = None
    for tol in tolerances:
        try:
            return cq.Face.makeNSidedSurface(wire.Edges(), [], tol3d=tol)
        except Exception as e:
            last = e
    raise RuntimeError(
        f"cannot cap a {len(wire.Edges())}-edge end wire at any tolerance "
        f"in {tolerances}: {last}")


def loft_capped(wires):
    """ThruSections leaves non-planar ends open; cap them and sew"""
    lo = BRepOffsetAPI_ThruSections(False, True)      # shell, ruled
    for w in wires:
        lo.AddWire(w.wrapped)
    lo.Build()
    if not lo.IsDone():
        raise RuntimeError("blade loft failed")
    sew = BRepBuilderAPI_Sewing(SEW_TOL)
    sew.Add(lo.Shape())
    for w in (wires[0], wires[-1]):
        sew.Add(_cap(w).wrapped)
    sew.Perform()
    shells = cq.Shape.cast(sew.SewedShape()).Shells()
    if not shells or not shells[0].wrapped.Closed():
        raise RuntimeError("sewn blade shell is not closed")
    solid = cq.Shape.cast(BRepBuilderAPI_MakeSolid(shells[0].wrapped).Solid())
    if solid.Volume() < 0:
        # the sewn shell came out inward-facing; flip it so the STEP file
        # has material on the right side of its faces
        solid = cq.Shape.cast(solid.wrapped.Reversed())
    return solid


@dataclass
class Row:
    name: str
    spool: str                    # lp | hp | static
    count: int
    radii: list = field(default_factory=list)
    sections: list = field(default_factory=list)   # planar (x, y) point lists
    areas: list = field(default_factory=list)

    @property
    def chord_over_radius(self):
        xs = [max(x for x, _ in s) - min(x for x, _ in s) for s in self.sections]
        return max(c / r for c, r in zip(xs, self.radii))

    def trapezoid_volume(self):
        return sum(0.5 * (a0 + a1) * (r1 - r0)
                   for (r0, a0), (r1, a1) in zip(zip(self.radii, self.areas),
                                                 zip(self.radii[1:], self.areas[1:])))

    def solid(self):
        """The lofted blade. Memoised on the instance: unit J3 asks every row
        for its solid five or six times over (volume fidelity, the envelope,
        containment, the glTF, the preview) and the loft is the expensive
        part. `rotate` and `translate` return copies, so a shared base is
        safe -- but OCC caches its TRIANGULATION on the shape, so anything
        tessellating at a chosen tolerance must clear it first. See
        `publication.render.tessellate`."""
        if getattr(self, "_solid", None) is None:
            self._solid = loft_capped([wrapped_wire(r, s)
                                       for r, s in zip(self.radii, self.sections)])
        return self._solid

    def pitch_rad(self):
        return 2 * math.pi / self.count


def _row_from_points(name, spool, count, pairs):
    r = Row(name, spool, count)
    for radius, pts in pairs:
        r.radii.append(radius)
        r.sections.append(pts)
        r.areas.append(polygon_properties(pts)["area"])
    return r


# ---------------------------------------------------------------- the rows

def hpc_rows():
    """all ten rotors and ten stators, from Table XXII's sections"""
    groups = {}
    for s in all_sections():
        groups.setdefault((s.kind, s.stage), []).append(s)
    out = []
    for (kind, stage), secs in sorted(groups.items()):
        secs = sorted(secs, key=lambda s: s.radius_m)
        pairs = []
        for sc in secs:
            b = section(sc.chord_m, sc.beta1, sc.beta2, sc.stagger, *_xxii_thickness(sc))
            pairs.append((sc.radius_m, closed_airfoil(b)))
        out.append(_row_from_points(f"hpc-{kind}-{stage}",
                                    "hp" if kind == "rotor" else "static",
                                    secs[0].count, pairs))
    return out


def lpt_rows():
    """all ten rows from the transcribed appendix coordinates -- no
    reconstruction at all, the only rows in the engine like that"""
    aero = yaml.safe_load((DATA / "lpt-aero.yaml").read_text())
    design = yaml.safe_load((DATA / "lpt-design.yaml").read_text())
    vanes = design.get("vane_counts") or aero.get("vane_counts") or {}
    counts_v = (vanes.get("vane_count") if isinstance(vanes, dict) else None) or [72, 102, 96, 114, 120]
    counts_b = design["rotor_blades"]["blade_count"]
    out = []
    for n in range(1, 6):
        for kind in ("S", "R"):
            row = f"{kind}{n}"
            pairs = []
            for span in (10, 50, 90):
                pts = load_section(row, span)
                radii = []
                with open(DATA / "lpt-airfoils" / f"{row}_{span}.csv") as f:
                    for line in f:
                        if line.startswith(("#", "surface")):
                            continue
                        radii.append(float(line.split(",")[2]))
                r = sum(radii) / len(radii) * IN
                pairs.append((r, [(z * IN, t * IN) for z, t in closed_airfoil(pts)]))
            count = counts_v[n - 1] if kind == "S" else counts_b[n - 1]
            out.append(_row_from_points(f"lpt-{'stator' if kind == 'S' else 'rotor'}-{n}",
                                        "static" if kind == "S" else "lp", count, pairs))
    return out


def fan_rows():
    """the fan rotor and the booster rotor, from the sections unit E3 built
    out of Fig 41's and Fig 52's chord, camber, stagger and thickness"""
    from mechanical.blade_frequency import _built_sections, _fan
    f = _fan()
    counts = f["aero_parameters"]["number_of_blades"]
    out = []

    g = f["fan_rotor_mechanical"]["blade_geometry"]
    a = f["fan_rotor_airfoil"]
    fig15 = a["fig15"]
    hub, length = fig15["r_sa_id_in"] * IN, fig15["blade_height_in"] * IN
    loc = a["max_thickness_location_pct_chord"]
    ats = [loc["hub"] + (loc["tip"] - loc["hub"]) * h / 100 for h in g["height_pct"]]
    polys = _built_sections([c * IN / CM for c in g["chord_in"]], g["camber_deg"],
                            g["stagger_deg"], g["tm_c_pct"], g["tle_c_pct"], ats)
    out.append(_row_from_points("fan-rotor", "lp", counts[0],
                                [(hub + h / 100 * length, p)
                                 for h, p in zip(g["height_pct"], polys)]))

    g = f["booster_blade_mechanical"]["geometry"]
    ap = f["aero_parameters"]
    tip = ap["tip_diameter_cm"][1] / 200
    hub = tip * ap["radius_ratio_inlet"][1]
    polys = _built_sections([c * IN / CM for c in g["chord_in"]], g["camber_deg"],
                            g["stagger_deg"], g["tm_c_pct"], g["te_c_pct"],
                            [50.0] * len(g["height_pct"]))
    out.append(_row_from_points("booster-rotor", "lp", counts[1],
                                [(hub + h / 100 * (tip - hub), p)
                                 for h, p in zip(g["height_pct"], polys)]))
    return out


def all_rows():
    return fan_rows() + hpc_rows() + lpt_rows()


# ------------------------------------------------------------- the checks

def volume_check(rows=None):
    """the generated solid against Stage F2's integral of the same sections.
    The wrap is volume-preserving in arc-length coordinates, exactly, so
    this is a check on the CAD and not on the aerodynamics."""
    out = []
    for row in rows if rows is not None else all_rows():
        s = row.solid()
        trap = row.trapezoid_volume()
        out.append(dict(row=row.name, spool=row.spool, count=row.count,
                        sections=len(row.radii), chord_over_radius=row.chord_over_radius,
                        cad_m3=s.Volume(), trapezoid_m3=trap,
                        err_pct=(s.Volume() / trap - 1) * 100,
                        valid=BRepCheck_Analyzer(s.wrapped).IsValid()))
    return out


def interference_check(rows=None):
    """A row is the same blade repeated round the annulus. Take the solid,
    take a copy rotated by one pitch, and intersect: a row whose blades
    touch would show a volume here. Zero is the only acceptable answer."""
    out = []
    for row in rows if rows is not None else all_rows():
        s = row.solid()
        nxt = s.rotate((0, 0, 0), (1, 0, 0), math.degrees(row.pitch_rad()))
        common = s.intersect(nxt)
        vol = 0.0 if common is None or not common.Solids() else common.Volume()
        out.append(dict(row=row.name, count=row.count,
                        pitch_deg=math.degrees(row.pitch_rad()),
                        overlap_m3=vol, blade_m3=s.Volume(),
                        overlap_pct=vol / s.Volume() * 100))
    return out


def export(rows=None, out_dir=None):
    """one STEP per row plus one compound per spool"""
    from pathlib import Path
    out_dir = Path(out_dir or (DATA.parent / "exports"))
    out_dir.mkdir(parents=True, exist_ok=True)
    by_spool = {}
    written = []
    for row in rows if rows is not None else all_rows():
        s = row.solid()
        p = out_dir / f"{row.name}.step"
        cq.exporters.export(cq.Workplane(obj=s), str(p))
        written.append(p)
        by_spool.setdefault(row.spool, []).append(s)
    for spool, solids in by_spool.items():
        comp = cq.Compound.makeCompound(solids)
        p = out_dir / f"spool-{spool}.step"
        cq.exporters.export(cq.Workplane(obj=comp), str(p))
        written.append(p)
    return written


if __name__ == "__main__":
    rows = all_rows()
    print(f"Stage G1: {len(rows)} blade rows generated from the validated sections\n")
    print(f"   {'row':<18}{'spool':>8}{'n':>5}{'sect':>6}{'c/r':>7}"
          f"{'CAD m3':>12}{'F2 m3':>12}{'err %':>8}{'valid':>7}")
    tot_err = []
    for v in volume_check(rows):
        tot_err.append(v["err_pct"])
        print(f"   {v['row']:<18}{v['spool']:>8}{v['count']:>5}{v['sections']:>6}"
              f"{v['chord_over_radius']:>7.2f}{v['cad_m3']:>12.4e}{v['trapezoid_m3']:>12.4e}"
              f"{v['err_pct']:>8.2f}{str(v['valid']):>7}")
    print(f"\n   {len(tot_err)} rows: worst volume error {max(abs(e) for e in tot_err):.2f} %")

    print(f"\n   blade-to-blade interference, one pitch apart:")
    bad = [i for i in interference_check(rows) if i["overlap_m3"] > 0]
    print(f"      {len(rows) - len(bad)} of {len(rows)} rows clear; overlapping: "
          f"{[b['row'] for b in bad] or 'none'}")

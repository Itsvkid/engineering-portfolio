"""Build the CFD surface geometry from the CST curve fitted to NASA TM
110300's real external ordinates (fit_reference_geometry.py) and export it
as STL for the OpenFOAM case's snappyHexMesh to read.

Needs pyOCC for the cowl/afterbody shell — run inside the pyocc_env conda
environment used by the rest of this project:

    cd projects/07-nacelle
    conda run -n pyocc_env python -m openfoam.generate_stl

Three surfaces, not one solid — this is the actual model, not a
simplification of convenience:

* `cowl-and-afterbody.stl` — the external cowl surface plus a cylindrical
  afterbody extension and a flat aft cap. NASA TM 110300 states the real
  test article this way explicitly: "a considerable portion of the model
  aft of the cowl was cylindrical in shape equal in diameter to the cowl
  maximum diameter" (p. 8) — this project's Cp comparison target
  (reference_data.FOREBODY_CP_TOP) includes afterbody stations out to
  X/L=139%, so the geometry needs to extend that far to have anything
  meaningful to compare against there. The slope discontinuity where the
  cowl meets the cylindrical section is not a modelling error — it is what
  the real article has.
* `highlight-inlet.stl` — a flat disc at the highlight, the internal
  capture-plane simplification: not a claim about the real internal duct
  shape, a boundary condition location. See openfoam/README.md, "What this
  case does and does not model," for why representing captured mass flow
  this way (a prescribed velocity at the highlight) is enough to get the
  EXTERNAL cowl pressure distribution right without modelling the real
  internal duct at all, and why NacelleSolid/CompleteNacelle's fully
  closed geometry doesn't fit this case's needs.

Neither the open cowl+afterbody shell nor the disc is built through
NacelleSolid or CompleteNacelle: both existing classes close the profile
into a solid with no flow-through opening, and modifying them to add one
would touch already-validated, in-use geometry (NacelleSolid backs the
site's CAD gallery) for a need specific to this CFD case. This module
builds the open shell directly with the same pyOCC primitives nacelle.py
uses (BRepPrimAPI_MakeRevol on a WIRE rather than a closed FACE gives a
shell, not a solid — tested directly in pyocc_env before being written
here, not assumed to work).
"""

from __future__ import annotations

import math
from pathlib import Path

# pyOCC-free — CSTCurve and NacelleProfile have no OpenCASCADE dependency
# (see their own module docstrings), so everything down to main() works
# without pyocc_env.
from src.profile import NacelleProfile

from .fit_reference_geometry import fit_target_curve, length_m

# How far past the cowl's own length the cylindrical afterbody runs, as a
# multiple of the cowl length L. 1.55 gives an aft station beyond
# reference_data.FOREBODY_CP_TOP's furthest point (X/L=139%), with margin
# rather than landing exactly on the last comparison station.
AFTERBODY_LENGTH_FACTOR = 1.55
AFTERBODY_POINTS = 20


def build_external_profile() -> NacelleProfile:
    curve = fit_target_curve()
    return NacelleProfile(length=length_m(), curve=curve)


def write_disc_stl(path, x: float, radius: float, n: int = 64) -> Path:
    """A flat triangulated disc, centred on the axis at station x, radius
    `radius`. Used for the highlight-inlet capture-plane patch. Plain
    Python, no pyOCC — a disc is simple enough not to need the kernel, and
    this way it stays generatable even without pyocc_env.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    center = (x, 0.0, 0.0)
    rim = [
        (x, radius * math.cos(2 * math.pi * i / n), radius * math.sin(2 * math.pi * i / n))
        for i in range(n)
    ]

    lines = ["solid highlightInlet"]
    for i in range(n):
        a, b = rim[i], rim[(i + 1) % n]
        # +x-facing normal (winding center, b, a), matching nacelle.py's
        # own (x, 0, r) meridian-point convention (x axial, +x downstream)
        # — an inlet facing into the freestream.
        lines.append("  facet normal 1 0 0")
        lines.append("    outer loop")
        for v in (center, b, a):
            lines.append(f"      vertex {v[0]:.8f} {v[1]:.8f} {v[2]:.8f}")
        lines.append("    endloop")
        lines.append("  endfacet")
    lines.append("endsolid highlightInlet")

    path.write_text("\n".join(lines) + "\n")
    return path


def _open_shell_points(profile: NacelleProfile) -> list[tuple[float, float]]:
    """Cowl meridian points plus a cylindrical afterbody run — see the
    module docstring for why the afterbody exists and why the slope
    discontinuity where it meets the cowl is not an error."""
    points = list(profile.meridian_points())
    l, r1 = profile.length, profile.trailing_radius
    afterbody_end = AFTERBODY_LENGTH_FACTOR * l
    for i in range(1, AFTERBODY_POINTS + 1):
        x = l + i * (afterbody_end - l) / AFTERBODY_POINTS
        points.append((x, r1))
    return points


def build_open_shell(profile: NacelleProfile):
    """The cowl-plus-afterbody surface, open at the highlight: a B-spline
    through every meridian point (cowl + cylindrical afterbody) plus a
    flat aft cap, revolved as a WIRE (not a closed FACE, unlike
    NacelleSolid.build()) — BRepPrimAPI_MakeRevol on a wire produces a
    shell open wherever the wire itself is open, which is exactly the
    highlight end here since no highlight-cap edge is added to close it.
    Requires pyOCC.
    """
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire
    from OCC.Core.BRepCheck import BRepCheck_Analyzer
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeRevol
    from OCC.Core.GeomAPI import GeomAPI_PointsToBSpline
    from OCC.Core.TColgp import TColgp_Array1OfPnt
    from OCC.Core.gp import gp_Ax1, gp_Dir, gp_Pnt

    points = _open_shell_points(profile)
    array = TColgp_Array1OfPnt(1, len(points))
    for i, (x, r) in enumerate(points, start=1):
        array.SetValue(i, gp_Pnt(x, 0.0, r))
    meridian_curve = GeomAPI_PointsToBSpline(array).Curve()
    meridian_edge = BRepBuilderAPI_MakeEdge(meridian_curve).Edge()

    afterbody_end, r1 = points[-1]
    trailing_cap = BRepBuilderAPI_MakeEdge(
        gp_Pnt(afterbody_end, 0.0, r1), gp_Pnt(afterbody_end, 0.0, 0.0)
    ).Edge()

    wire = BRepBuilderAPI_MakeWire()
    wire.Add(meridian_edge)
    wire.Add(trailing_cap)

    axis = gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0))
    revol = BRepPrimAPI_MakeRevol(wire.Wire(), axis, 2 * math.pi)
    if not revol.IsDone():
        raise RuntimeError("revolution failed to build")

    shape = revol.Shape()
    if not BRepCheck_Analyzer(shape).IsValid():
        raise RuntimeError(
            "revolved cowl+afterbody shell is not valid — check the "
            "meridian point list for self-intersection"
        )
    return shape


def main() -> None:
    from src.export import to_stl

    external = build_external_profile()
    print(f"{'cowl length':<28}{external.length:.4f} m")
    print(f"{'highlight radius':<28}{external.highlight_radius:.5f} m")
    print(f"{'trailing / afterbody radius':<28}{external.trailing_radius:.5f} m")
    afterbody_end = AFTERBODY_LENGTH_FACTOR * external.length
    print(f"{'afterbody end station':<28}{afterbody_end:.4f} m "
          f"(X/L = {AFTERBODY_LENGTH_FACTOR * 100:.0f}%)")

    shell = build_open_shell(external)

    from OCC.Core.BRepGProp import brepgprop
    from OCC.Core.GProp import GProp_GProps

    props = GProp_GProps()
    brepgprop.SurfaceProperties(shell, props)
    print(f"{'shell surface area':<28}{props.Mass():.6f} m^2")

    triSurface = Path(__file__).parent / "case" / "constant" / "triSurface"
    shell_path = to_stl(shell, triSurface / "cowl-and-afterbody.stl")
    print(f"\nwrote {shell_path}")

    inlet_path = write_disc_stl(triSurface / "highlight-inlet.stl",
                                 x=0.0, radius=external.highlight_radius)
    print(f"wrote {inlet_path}")
    print(f"{'highlight-inlet disc radius':<28}{external.highlight_radius:.5f} m  "
          f"(the flowRateInletVelocity patch — see case/0/U)")


if __name__ == "__main__":
    main()

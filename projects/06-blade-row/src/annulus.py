"""The annulus: hub and casing flowpath surfaces, and the full ring of
n_blades patterned about the engine axis.

This is the piece a single blade (blade.py) cannot show on its own — a blade
row is only "engine hardware" once it is a ring inside a flowpath, not one
part in isolation. Also requires pyOCC, same as blade.py.

`hub_solid`/`casing_shell` below build a single cylinder — still the right
answer for one row on its own, where "the annulus" means only the flowpath
directly under that row's own blades, and still what
`exports/blade_row.step` and the site's CAD viewer use, unchanged. A real
multi-row *stage* annulus narrows hub-to-casing along the axial direction to
keep annulus area matched to the gas's falling specific volume as it's
compressed — `converging_hub_solid`/`converging_casing_shell` further down
build that as three axial segments (cylinder under the rotor, a cone through
the gap, cylinder under the stator) rather than one smoothly-varying
surface, so each row's blade roots still sit on a true cylinder exactly
matching that row's own `BladeRow.hub_radius`/`tip_radius` — see
`stage.converging_stage_assembly`, where the two rows' differing radii come
from.
"""

from __future__ import annotations

import math

from OCC.Core.BRep import BRep_Builder
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCone, BRepPrimAPI_MakeCylinder
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.gp import gp_Ax1, gp_Ax2, gp_Dir, gp_Pnt, gp_Trsf
from OCC.Core.TopoDS import TopoDS_Compound

from .blade import BladeRow

CASING_WALL_FRACTION = 0.03  # casing outer radius = tip_radius * (1 + this)
AXIAL_MARGIN_FRACTION = 0.15  # hub/casing extend this far past the blade


def _rotated_copy(shape, angle_rad: float):
    trsf = gp_Trsf()
    trsf.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0)), angle_rad)
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


def blade_ring(row: BladeRow):
    """All n_blades copies of the blade, patterned about the engine axis
    (+x). The k=0 copy is the blade blade.py builds directly; every other
    copy is a rotation of it, not an independent loft — so the ring is
    exactly n_blades-fold symmetric by construction, not by coincidence."""
    single = row.build()
    compound = TopoDS_Compound()
    builder = BRep_Builder()
    builder.MakeCompound(compound)
    for k in range(row.n_blades):
        angle = 2 * math.pi * k / row.n_blades
        piece = single if k == 0 else _rotated_copy(single, angle)
        builder.Add(compound, piece)
    return compound


def axial_extent(row: BladeRow) -> tuple[float, float]:
    """Axial range the blade actually occupies, measured off the built solid
    rather than estimated — stagger shifts where the leading and trailing
    edges land, so a guess from chord alone would be wrong at high stagger.
    """
    box = Bnd_Box()
    brepbndlib.AddOptimal(row.build(), box)
    xmin, _, _, xmax, _, _ = box.Get()
    return xmin, xmax


def _flowpath_cylinder(row: BladeRow, radius: float,
                        axial_range: tuple[float, float] | None = None):
    """axial_range overrides the single-row extent with an explicit (xmin,
    xmax) — how stage.py gets one hub/casing spanning a rotor *and* a
    downstream stator instead of duplicating flowpath surfaces per row."""
    xmin, xmax = axial_range if axial_range is not None else axial_extent(row)
    span = xmax - xmin
    margin = AXIAL_MARGIN_FRACTION * span
    origin = gp_Pnt(xmin - margin, 0, 0)
    axis = gp_Ax2(origin, gp_Dir(1, 0, 0))
    length = span + 2 * margin
    return BRepPrimAPI_MakeCylinder(axis, radius, length).Shape()


def hub_solid(row: BladeRow, axial_range: tuple[float, float] | None = None):
    """Solid hub drum at r_hub — the blade roots sit on its surface."""
    return _flowpath_cylinder(row, row.hub_radius, axial_range)


def casing_shell(row: BladeRow, wall_fraction: float = CASING_WALL_FRACTION,
                  axial_range: tuple[float, float] | None = None):
    """Hollow casing tube whose inner surface is r_tip.

    Built as an outer cylinder minus an inner one, not a single solid
    cylinder at r_tip — a solid disc that large would engulf the blade ring
    it's meant to sit outside, not bound it.
    """
    outer = _flowpath_cylinder(row, row.tip_radius * (1 + wall_fraction), axial_range)
    inner = _flowpath_cylinder(row, row.tip_radius, axial_range)
    result = BRepAlgoAPI_Cut(outer, inner).Shape()
    return result


def full_assembly(row: BladeRow):
    """Hub, blade ring and casing as one compound — what build.py exports."""
    compound = TopoDS_Compound()
    builder = BRep_Builder()
    builder.MakeCompound(compound)
    for shape in (hub_solid(row), blade_ring(row), casing_shell(row)):
        builder.Add(compound, shape)
    return compound


def _flowpath_cone_segment(radius_in: float, radius_out: float, x0: float, x1: float):
    """A straight conical transition between two flowpath radii over the
    axial range [x0, x1] — the converging-annulus analogue of
    `_flowpath_cylinder`'s constant-radius segment.

    Falls back to a cylinder when the two radii are equal: a first version
    assumed OCC would just build a degenerate (zero half-angle) cone
    without complaint, on the reasoning that a cone with r1 == r2 *is*
    geometrically a cylinder — wrong. `BRepPrimAPI_MakeCone` raises
    `Standard_DomainError: cone with two identic radii` instead of doing
    that collapse itself, caught by a test that builds exactly that case
    rather than only ever passing it two different radii.
    """
    axis = gp_Ax2(gp_Pnt(x0, 0, 0), gp_Dir(1, 0, 0))
    if radius_in == radius_out:
        return BRepPrimAPI_MakeCylinder(axis, radius_in, x1 - x0).Shape()
    return BRepPrimAPI_MakeCone(axis, radius_in, radius_out, x1 - x0).Shape()


def _three_segment_pieces(radius_rotor: float, radius_stator: float,
                           rotor_x0: float, rotor_x1: float,
                           stator_x0: float, stator_x1: float):
    """Cylinder at `radius_rotor` under the rotor, a cone transitioning to
    `radius_stator` through the gap, cylinder at `radius_stator` under the
    stator — not one smoothly-varying surface swept through both rows,
    which would leave each row's own (still individually cylindrical)
    blade roots sitting proud of or sunk into a hub/casing surface that
    had already started moving under them.

    Returns the three solids *separately*, not pre-compounded — a first
    version compounded them here and let `converging_casing_shell` cut one
    three-solid compound from another. That built without error and even
    reported a numerically-plausible volume (outer minus inner, to six
    figures), but `BRepCheck_Analyzer` flagged the result invalid: cutting
    a compound of solids that touch each other at coincident seam faces
    (where each cylinder meets its cone) is not the same operation as
    cutting three genuinely separate solids, and a volume number alone
    didn't catch that the topology was wrong. `converging_casing_shell`
    below cuts each segment individually instead, matching the single-
    solid cut `casing_shell` already uses, then compounds the three
    already-hollow results — `converging_hub_solid` doesn't need a cut at
    all, so it compounds these three pieces directly.
    """
    rotor_axis = gp_Ax2(gp_Pnt(rotor_x0, 0, 0), gp_Dir(1, 0, 0))
    rotor_seg = BRepPrimAPI_MakeCylinder(rotor_axis, radius_rotor, rotor_x1 - rotor_x0).Shape()
    cone_seg = _flowpath_cone_segment(radius_rotor, radius_stator, rotor_x1, stator_x0)
    stator_axis = gp_Ax2(gp_Pnt(stator_x0, 0, 0), gp_Dir(1, 0, 0))
    stator_seg = BRepPrimAPI_MakeCylinder(stator_axis, radius_stator, stator_x1 - stator_x0).Shape()
    return rotor_seg, cone_seg, stator_seg


def _compound(*shapes):
    compound = TopoDS_Compound()
    builder = BRep_Builder()
    builder.MakeCompound(compound)
    for shape in shapes:
        builder.Add(compound, shape)
    return compound


def converging_hub_solid(hub_radius_rotor: float, hub_radius_stator: float,
                          rotor_x0: float, rotor_x1: float,
                          stator_x0: float, stator_x1: float):
    """Three-segment hub drum for a converging annulus — see
    `_three_segment_pieces`. The rotor and stator blade roots sit on the
    first and third segments respectively, both true cylinders at exactly
    that row's own `BladeRow.hub_radius`, the same guarantee the single
    shared cylinder in `hub_solid` gives a constant-annulus stage, just
    applied per row instead of to one shared surface."""
    return _compound(*_three_segment_pieces(
        hub_radius_rotor, hub_radius_stator, rotor_x0, rotor_x1, stator_x0, stator_x1
    ))


def converging_casing_shell(tip_radius_rotor: float, tip_radius_stator: float,
                             rotor_x0: float, rotor_x1: float,
                             stator_x0: float, stator_x1: float,
                             wall_fraction: float = CASING_WALL_FRACTION):
    """Three-segment casing shell for a converging annulus: each of the
    three outer (wall-thickness-scaled) segments cut by its own matching
    inner segment — three individual single-solid cuts, not one compound-
    from-compound cut (see `_three_segment_pieces` for why) — then
    compounded into one hollow shell, same reasoning as `casing_shell`'s
    single-cylinder version: a solid disc that large would engulf the
    blade rings it's meant to sit outside, not bound them.
    """
    outer_pieces = _three_segment_pieces(
        tip_radius_rotor * (1 + wall_fraction), tip_radius_stator * (1 + wall_fraction),
        rotor_x0, rotor_x1, stator_x0, stator_x1,
    )
    inner_pieces = _three_segment_pieces(
        tip_radius_rotor, tip_radius_stator, rotor_x0, rotor_x1, stator_x0, stator_x1
    )
    hollow_segments = [
        BRepAlgoAPI_Cut(outer, inner).Shape()
        for outer, inner in zip(outer_pieces, inner_pieces)
    ]
    return _compound(*hollow_segments)

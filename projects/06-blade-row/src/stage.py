"""A rotor-stator stage: the stator ring translated downstream of the
rotor ring, sharing one hub and casing.

A rotor alone adds swirl to do work on the flow; nothing downstream can use
that swirl as kinetic energy, so a real stage always follows the rotor with
a stationary row that removes it (see StatorDesignPoint in
velocity_triangles.py). This module is where the two rows, each built
independently by blade.py/annulus.py, become one piece of hardware. Also
requires pyOCC, same as blade.py and annulus.py.
"""

from __future__ import annotations

from OCC.Core.BRep import BRep_Builder
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.gp import gp_Trsf, gp_Vec
from OCC.Core.TopoDS import TopoDS_Compound

from .annulus import (
    AXIAL_MARGIN_FRACTION,
    axial_extent,
    blade_ring,
    casing_shell,
    converging_casing_shell,
    converging_hub_solid,
    hub_solid,
)
from .blade import BladeRow
from .meridional import annulus_area

AXIAL_GAP_FRACTION = 0.5  # rotor-stator gap, x the rotor's mean chord


def _translated(shape, dx: float):
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(dx, 0, 0))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


def stator_offset(rotor: BladeRow, stator: BladeRow,
                   gap_fraction: float = AXIAL_GAP_FRACTION) -> float:
    """Axial translation that puts the stator's leading edge gap_fraction
    of the rotor's mean chord downstream of the rotor's trailing edge.

    Both rows are built independently starting near x=0 (see blade.py), so
    without this they'd sit on top of each other rather than in sequence.
    """
    rotor_xmin, rotor_xmax = axial_extent(rotor)
    stator_xmin, _ = axial_extent(stator)
    gap = gap_fraction * rotor.chord_at(rotor.mean_radius)
    return (rotor_xmax - stator_xmin) + gap


def stage_assembly(rotor: BladeRow, stator: BladeRow,
                    gap_fraction: float = AXIAL_GAP_FRACTION):
    """Hub, rotor ring, stator ring and casing, as one compound.

    rotor and stator must share hub_radius/tip_radius — they sit in one
    annulus, and building each against its own would let that drift apart
    silently instead of failing loudly here.
    """
    if (rotor.hub_radius, rotor.tip_radius) != (stator.hub_radius, stator.tip_radius):
        raise ValueError(
            "rotor and stator must share the same annulus (hub_radius, "
            "tip_radius) — they sit in one flowpath, not two"
        )

    dx = stator_offset(rotor, stator, gap_fraction)
    rotor_ring = blade_ring(rotor)
    stator_ring = _translated(blade_ring(stator), dx)

    rotor_xmin, rotor_xmax = axial_extent(rotor)
    stator_xmin, stator_xmax = axial_extent(stator)
    combined = (min(rotor_xmin, stator_xmin + dx),
                max(rotor_xmax, stator_xmax + dx))

    compound = TopoDS_Compound()
    builder = BRep_Builder()
    builder.MakeCompound(compound)
    for shape in (
        hub_solid(rotor, axial_range=combined),
        rotor_ring,
        stator_ring,
        casing_shell(rotor, axial_range=combined),
    ):
        builder.Add(compound, shape)
    return compound


def converging_stage_assembly(rotor: BladeRow, stator: BladeRow,
                               gap_fraction: float = AXIAL_GAP_FRACTION):
    """Like `stage_assembly`, but for a rotor and stator that sit in
    genuinely different annuli — the converging-annulus case
    `stage_assembly`'s equal-radius requirement exists specifically to rule
    out. `stator` is expected to already carry the converged radii (see
    `meridional.converging_annulus_exit`, which build.py uses to construct
    it) — this function's job is the geometry, not deciding how much the
    annulus should narrow.

    Hub and casing are three axial segments each (cylinder under the rotor,
    a cone through the gap, cylinder under the stator — see
    `annulus.converging_hub_solid`/`converging_casing_shell`), not one
    smoothly-varying surface swept through both rows: that would leave each
    row's own (still individually cylindrical) blade roots sitting proud of
    or sunk into a hub/casing surface that had already started moving under
    them before that row's own trailing edge.
    """
    if annulus_area(stator.hub_radius, stator.tip_radius) >= annulus_area(
        rotor.hub_radius, rotor.tip_radius
    ):
        raise ValueError(
            "stator annulus area is not smaller than the rotor's — this "
            "function builds a converging annulus specifically; use "
            "stage_assembly for a constant one"
        )

    dx = stator_offset(rotor, stator, gap_fraction)
    rotor_ring = blade_ring(rotor)
    stator_ring = _translated(blade_ring(stator), dx)

    rotor_xmin, rotor_xmax = axial_extent(rotor)
    stator_xmin, stator_xmax = axial_extent(stator)
    stator_xmin_t, stator_xmax_t = stator_xmin + dx, stator_xmax + dx

    margin = AXIAL_MARGIN_FRACTION * (rotor_xmax - rotor_xmin)
    seg_args = (
        rotor_xmin - margin, rotor_xmax, stator_xmin_t, stator_xmax_t + margin,
    )
    hub = converging_hub_solid(rotor.hub_radius, stator.hub_radius, *seg_args)
    casing = converging_casing_shell(rotor.tip_radius, stator.tip_radius, *seg_args)

    compound = TopoDS_Compound()
    builder = BRep_Builder()
    builder.MakeCompound(compound)
    for shape in (hub, rotor_ring, stator_ring, casing):
        builder.Add(compound, shape)
    return compound

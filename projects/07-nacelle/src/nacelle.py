"""An axisymmetric nacelle solid, revolved from a CST meridian profile on
the OpenCASCADE kernel through pythonocc-core.

The meridian curve sits in the XZ half-plane (y=0, x=axial, z=radial) closed
into a loop by the two end radii and a segment lying on the axis itself,
then that closed profile is revolved a full turn about the axial (+x) axis —
the standard "lathe" construction for a body of revolution. Requires pyOCC.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakeWire,
)
from OCC.Core.BRepCheck import BRepCheck_Analyzer
from OCC.Core.BRepGProp import brepgprop
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeRevol
from OCC.Core.GeomAPI import GeomAPI_PointsToBSpline
from OCC.Core.GProp import GProp_GProps
from OCC.Core.TColgp import TColgp_Array1OfPnt
from OCC.Core.gp import gp_Ax1, gp_Dir, gp_Pnt

from .profile import NacelleProfile, internal_clearance_ok, material_surface_area, material_volume


@dataclass(frozen=True)
class NacelleSolid:
    profile: NacelleProfile

    def _closed_wire(self):
        """Meridian spline, closed back to itself via the two end radii and
        the axis segment between them — the loop BRepPrimAPI_MakeRevol
        needs to produce a solid rather than an open shell."""
        points = self.profile.meridian_points()
        array = TColgp_Array1OfPnt(1, len(points))
        for i, (x, r) in enumerate(points, start=1):
            array.SetValue(i, gp_Pnt(x, 0.0, r))
        meridian_curve = GeomAPI_PointsToBSpline(array).Curve()
        meridian_edge = BRepBuilderAPI_MakeEdge(meridian_curve).Edge()

        length = self.profile.length
        r0, r1 = self.profile.highlight_radius, self.profile.trailing_radius
        trailing_cap = BRepBuilderAPI_MakeEdge(
            gp_Pnt(length, 0.0, r1), gp_Pnt(length, 0.0, 0.0)
        ).Edge()
        axis_segment = BRepBuilderAPI_MakeEdge(
            gp_Pnt(length, 0.0, 0.0), gp_Pnt(0.0, 0.0, 0.0)
        ).Edge()
        highlight_cap = BRepBuilderAPI_MakeEdge(
            gp_Pnt(0.0, 0.0, 0.0), gp_Pnt(0.0, 0.0, r0)
        ).Edge()

        wire = BRepBuilderAPI_MakeWire()
        for edge in (meridian_edge, trailing_cap, axis_segment, highlight_cap):
            wire.Add(edge)
        return wire.Wire()

    def build(self):
        """Revolve the closed meridian profile a full turn about the axial
        axis into a solid."""
        face = BRepBuilderAPI_MakeFace(self._closed_wire()).Face()
        axis = gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0))
        revol = BRepPrimAPI_MakeRevol(face, axis, 2 * math.pi)
        if not revol.IsDone():
            raise RuntimeError("revolution failed to build")

        shape = revol.Shape()
        if not BRepCheck_Analyzer(shape).IsValid():
            raise RuntimeError(
                "revolved nacelle is not valid — check the meridian curve "
                "for self-intersection or a radius going negative"
            )
        return shape

    def measured_volume(self) -> float:
        props = GProp_GProps()
        brepgprop.VolumeProperties(self.build(), props)
        return props.Mass()

    def measured_surface_area(self) -> float:
        props = GProp_GProps()
        brepgprop.SurfaceProperties(self.build(), props)
        return props.Mass()


@dataclass(frozen=True)
class CompleteNacelle:
    """External cowl plus internal inlet duct as one hollow solid — the
    "internal duct / inlet surface" this project's Outstanding list named.
    `NacelleSolid` above revolves a profile closed straight back through
    the axis, producing a solid lump; this instead closes the loop between
    two *independent* profiles (never touching the axis), so the revolved
    result is a proper annular shell — material between the two surfaces,
    empty space inside the internal one, which is where a real nacelle's
    air actually flows. `NacelleSolid` is left exactly as it was rather
    than folded into this: it is already validated and in use (`build.py`,
    the site's CAD gallery), and "external cowl only" is a legitimate,
    already-documented v1 scope, not a bug this class needs to fix.

    `internal` represents the duct wall from the highlight inward: its own
    r0 is the *inner* lip radius (less than the external r0 by the lip's
    wall thickness) and its own r1 is the duct's radius at the same
    trailing-edge station the external cowl ends at — this project does not
    model a separately-positioned fan face, so the duct is only defined
    over the same length as the cowl it sits inside.
    """

    external: NacelleProfile
    internal: NacelleProfile

    def __post_init__(self) -> None:
        if not internal_clearance_ok(self.external, self.internal):
            raise ValueError(
                "internal profile is not strictly inside the external "
                "profile at every station along the shared length — this "
                "combination would self-intersect when revolved rather "
                "than bound a valid hollow shell"
            )

    def _closed_wire(self):
        def spline_edge(points):
            array = TColgp_Array1OfPnt(1, len(points))
            for i, (x, r) in enumerate(points, start=1):
                array.SetValue(i, gp_Pnt(x, 0.0, r))
            curve = GeomAPI_PointsToBSpline(array).Curve()
            return BRepBuilderAPI_MakeEdge(curve).Edge()

        # External: highlight -> trailing edge. Internal: same points
        # reversed, trailing edge -> highlight, so the two splines plus the
        # two caps below trace one continuous loop rather than two open arcs.
        external_edge = spline_edge(self.external.meridian_points())
        internal_edge = spline_edge(list(reversed(self.internal.meridian_points())))

        length = self.external.length
        r0_ext, r1_ext = self.external.highlight_radius, self.external.trailing_radius
        r0_int, r1_int = self.internal.highlight_radius, self.internal.trailing_radius

        # Trailing-edge cap: the ring of material where the fan cowl's
        # outer skin meets the duct wall at the back of this section.
        trailing_cap = BRepBuilderAPI_MakeEdge(
            gp_Pnt(length, 0.0, r1_ext), gp_Pnt(length, 0.0, r1_int)
        ).Edge()
        # Lip cap: the ring of material at the highlight itself — a real
        # lip's rounded cross-section is not modelled (that is its own
        # blend-surface problem, not a straight line), so this is the same
        # simplification the trailing cap already makes, just at the front.
        lip_cap = BRepBuilderAPI_MakeEdge(
            gp_Pnt(0.0, 0.0, r0_int), gp_Pnt(0.0, 0.0, r0_ext)
        ).Edge()

        wire = BRepBuilderAPI_MakeWire()
        for edge in (external_edge, trailing_cap, internal_edge, lip_cap):
            wire.Add(edge)
        return wire.Wire()

    def build(self):
        """Revolve the closed external/internal loop a full turn. Because
        the loop never touches the axis (unlike NacelleSolid's), this
        produces an annular (tube-like) solid rather than a filled one —
        the standard result of revolving a profile offset from its axis,
        the same principle a torus is built on."""
        face = BRepBuilderAPI_MakeFace(self._closed_wire()).Face()
        axis = gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0))
        revol = BRepPrimAPI_MakeRevol(face, axis, 2 * math.pi)
        if not revol.IsDone():
            raise RuntimeError("revolution failed to build")

        shape = revol.Shape()
        if not BRepCheck_Analyzer(shape).IsValid():
            raise RuntimeError(
                "revolved hollow nacelle is not valid — check the two "
                "meridian curves for self-intersection"
            )
        return shape

    def measured_volume(self) -> float:
        props = GProp_GProps()
        brepgprop.VolumeProperties(self.build(), props)
        return props.Mass()

    def measured_surface_area(self) -> float:
        props = GProp_GProps()
        brepgprop.SurfaceProperties(self.build(), props)
        return props.Mass()

    def predicted_material_volume(self) -> float:
        return material_volume(self.external, self.internal)

    def predicted_total_surface_area(self) -> float:
        return material_surface_area(self.external, self.internal)

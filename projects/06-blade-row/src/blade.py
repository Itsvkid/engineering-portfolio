"""A single rotor blade, lofted through radial sections on the OpenCASCADE
kernel through pythonocc-core.

Requires pyOCC — everything this module imports from OCC.Core means it only
runs inside the pyocc_env conda environment, unlike velocity_triangles.py and
blade_section.py, which decide the numbers this module places.

Axes: +x axial (flow direction), +y radial (blade speed direction), +z
tangential (direction of rotation). A blade sits from y = r_hub to y = r_tip
with its chord staggered in the x-z plane at each radius — the same
"radial = span" substitution the module docstring in build.py explains.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeWire,
)
from OCC.Core.BRepCheck import BRepCheck_Analyzer
from OCC.Core.BRepGProp import brepgprop
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_ThruSections
from OCC.Core.GeomAPI import GeomAPI_PointsToBSpline
from OCC.Core.GProp import GProp_GProps
from OCC.Core.TColgp import TColgp_Array1OfPnt
from OCC.Core.gp import gp_Pnt

from .blade_section import CircularArcSection
from .velocity_triangles import RotorDesignPoint


@dataclass(frozen=True)
class BladeRow:
    """One rotor blade row, radially twisted by free-vortex velocity
    triangles and stacked from hub to casing.

    hub_radius, tip_radius   annulus limits the blade spans, m.
    n_blades                 blade count Z — used for solidity and, in
                              annulus.py, to pattern the full ring.
    root_chord, tip_chord    chord at hub and casing, m. Linear taper
                              between, same convention as the wing project.
    thickness                t/c, constant across the span.
    design                   the RotorDesignPoint whose free-vortex law sets
                              stagger and camber at each station.
    n_stations                radial loft stations, hub to tip inclusive.
    n_points                  points per surface per section.
    """

    hub_radius: float
    tip_radius: float
    n_blades: int
    root_chord: float
    tip_chord: float
    thickness: float
    design: RotorDesignPoint
    n_stations: int = 5
    n_points: int = 120

    def __post_init__(self) -> None:
        if self.hub_radius <= 0 or self.tip_radius <= self.hub_radius:
            raise ValueError("need 0 < hub_radius < tip_radius")
        if self.n_blades < 1:
            raise ValueError("n_blades must be at least 1")
        if self.n_stations < 2:
            raise ValueError("need at least 2 radial stations to loft")

    @property
    def span(self) -> float:
        """Blade height, tip minus hub — the radial analogue of the wing's
        span, and the quantity chord_at() below normalises against."""
        return self.tip_radius - self.hub_radius

    @property
    def mean_radius(self) -> float:
        return 0.5 * (self.hub_radius + self.tip_radius)

    def chord_at(self, r: float) -> float:
        """Chord at radius r, linearly tapered hub to tip."""
        eta = (r - self.hub_radius) / self.span
        return self.root_chord + (self.tip_chord - self.root_chord) * eta

    def solidity_at(self, r: float) -> float:
        """sigma(r) = chord * Z / (2*pi*r) — chord as a fraction of blade
        spacing. Typical axial-compressor rotors sit around 0.8-1.5; this is
        what the reference design in build.py is checked against."""
        return self.chord_at(r) * self.n_blades / (2 * math.pi * r)

    def radial_stations(self) -> list[float]:
        step = self.span / (self.n_stations - 1)
        return [self.hub_radius + i * step for i in range(self.n_stations)]

    def _section_wire(self, r: float):
        """Closed blade-section wire at radius r, staggered and placed.

        Mirrors the wing project's Wing._section_wire: scale to local chord,
        rotate about the quarter-chord point (here by the free-vortex
        stagger angle rather than a fixed sweep), then place at (axial,
        radial, tangential). The thickness/camber offset is applied as a
        straight tangential distance rather than conformally wrapped around
        the annulus — valid because chord is small next to radius, and
        stated here because it stops being valid if that ratio isn't small.
        """
        chord = self.chord_at(r)
        stagger = self.design.stagger_angle(r)
        section = CircularArcSection(
            camber_angle_deg=math.degrees(self.design.camber_angle(r)),
            thickness=self.thickness,
            n_points=self.n_points,
        )
        upper, lower = section.surfaces()

        def place(points):
            out = []
            for xc, zc in points:
                x = (xc - 0.25) * chord
                z = zc * chord
                # Stagger rotates the chord line toward the tangential
                # direction, same sense as the velocity triangles: positive
                # stagger leans the blade the way rotation drags the flow.
                x_axial = x * math.cos(stagger) - z * math.sin(stagger)
                z_tan = x * math.sin(stagger) + z * math.cos(stagger)
                out.append(gp_Pnt(0.25 * chord + x_axial, r, z_tan))
            return out

        edges = []
        for points in (place(upper), place(lower)):
            array = TColgp_Array1OfPnt(1, len(points))
            for i, p in enumerate(points, start=1):
                array.SetValue(i, p)
            curve = GeomAPI_PointsToBSpline(array).Curve()
            edges.append(BRepBuilderAPI_MakeEdge(curve).Edge())

        wire = BRepBuilderAPI_MakeWire()
        for edge in edges:
            wire.Add(edge)
        return wire.Wire()

    def build(self):
        """Loft the radial sections into a single blade solid."""
        loft = BRepOffsetAPI_ThruSections(True, True)  # solid, ruled
        for r in self.radial_stations():
            loft.AddWire(self._section_wire(r))
        loft.Build()
        if not loft.IsDone():
            raise RuntimeError("blade loft failed to build")

        shape = loft.Shape()
        if not BRepCheck_Analyzer(shape).IsValid():
            raise RuntimeError(
                "lofted blade is not valid — a self-intersecting solid here "
                "usually means stagger swept too far between two stations; "
                "add more n_stations before trusting this design"
            )
        return shape

    def measured_volume(self) -> float:
        props = GProp_GProps()
        brepgprop.VolumeProperties(self.build(), props)
        return props.Mass()

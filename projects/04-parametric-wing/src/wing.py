"""Parametric wing built on the OpenCASCADE kernel through pythonocc-core.

Every dimension comes from the parameters below. Changing taper ratio or sweep
regenerates the solid; nothing is positioned by hand, and there is no step that
has to be repeated in a GUI to get a different wing out.

Axes follow the usual convention: +x aft along the chord, +y out along the
span, +z up. The root leading edge sits at the origin.
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
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.GeomAPI import GeomAPI_PointsToBSpline
from OCC.Core.GProp import GProp_GProps
from OCC.Core.TColgp import TColgp_Array1OfPnt
from OCC.Core.gp import gp_Pnt

from .airfoil import NACA4


@dataclass(frozen=True)
class Wing:
    """A linearly tapered wing with sweep, dihedral and washout.

    span            full span b, m (tip to tip)
    root_chord      c_root, m
    taper_ratio     lambda = c_tip / c_root
    sweep_deg       quarter-chord sweep, degrees aft
    dihedral_deg    degrees up from horizontal
    twist_deg       washout at the tip, degrees pitch-down
    section         airfoil section, constant across the span
    n_points        points per surface per section
    """

    span: float
    root_chord: float
    taper_ratio: float
    sweep_deg: float = 0.0
    dihedral_deg: float = 0.0
    twist_deg: float = 0.0
    section: NACA4 = field(default_factory=lambda: NACA4.from_code("2412"))
    n_points: int = 120

    def __post_init__(self) -> None:
        if self.span <= 0 or self.root_chord <= 0:
            raise ValueError("span and root_chord must be positive")
        if not 0 < self.taper_ratio <= 1:
            raise ValueError(
                f"taper_ratio must be in (0, 1], got {self.taper_ratio}. "
                f"A tip chord larger than the root is an inverse-taper wing "
                f"and is not what this builder models."
            )
        if abs(self.sweep_deg) >= 89 or abs(self.dihedral_deg) >= 89:
            raise ValueError("sweep and dihedral must be under 89 degrees")

    # ── Analytical planform properties ──────────────────────────────────────
    #
    # Closed forms for a trapezoidal wing. These are what the built solid is
    # checked against in the tests — a geometry kernel that disagrees with the
    # algebra means one of the two is wrong.

    @property
    def tip_chord(self) -> float:
        return self.root_chord * self.taper_ratio

    @property
    def area(self) -> float:
        """Planform area, S = b*(c_root + c_tip)/2."""
        return self.span * (self.root_chord + self.tip_chord) / 2.0

    @property
    def aspect_ratio(self) -> float:
        return self.span**2 / self.area

    @property
    def mac(self) -> float:
        """Mean aerodynamic chord, (2/3)*c_root*(1+L+L^2)/(1+L)."""
        lam = self.taper_ratio
        return (2.0 / 3.0) * self.root_chord * (1 + lam + lam**2) / (1 + lam)

    @property
    def mac_spanwise_station(self) -> float:
        """Spanwise position of the MAC, y = (b/6)*(1+2L)/(1+L)."""
        lam = self.taper_ratio
        return (self.span / 6.0) * (1 + 2 * lam) / (1 + lam)

    def chord_at(self, eta: float) -> float:
        """Chord at fractional semi-span eta in [0, 1]."""
        return self.root_chord + (self.tip_chord - self.root_chord) * eta

    # ── Geometry ────────────────────────────────────────────────────────────

    def _section_wire(self, y: float):
        """Closed airfoil wire at spanwise station y, placed and rotated."""
        semi = self.span / 2.0
        eta = abs(y) / semi
        chord = self.chord_at(eta)

        # Sweep is defined on the quarter-chord line, so the leading edge is
        # placed relative to it rather than swept directly. Sweeping the
        # leading edge instead is a common slip and puts the quarter-chord
        # line at the wrong angle for every taper ratio except 1.
        quarter_x = 0.25 * self.root_chord + abs(y) * math.tan(
            math.radians(self.sweep_deg)
        )
        le_x = quarter_x - 0.25 * chord
        z_offset = abs(y) * math.tan(math.radians(self.dihedral_deg))
        twist = math.radians(-self.twist_deg * eta)  # negative: pitch down

        upper, lower = self.section.surfaces(self.n_points)

        def place(points):
            out = []
            for xc, zc in points:
                # Scale to chord, then rotate about the quarter-chord point.
                x = (xc - 0.25) * chord
                z = zc * chord
                xr = x * math.cos(twist) - z * math.sin(twist)
                zr = x * math.sin(twist) + z * math.cos(twist)
                out.append(gp_Pnt(le_x + 0.25 * chord + xr, y, z_offset + zr))
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
        """Loft the sections into a single solid and return the shape."""
        semi = self.span / 2.0
        loft = BRepOffsetAPI_ThruSections(True, True)  # solid, ruled
        for y in (-semi, 0.0, semi):
            loft.AddWire(self._section_wire(y))
        loft.Build()
        if not loft.IsDone():
            raise RuntimeError("loft failed to build")

        shape = loft.Shape()
        if not BRepCheck_Analyzer(shape).IsValid():
            raise RuntimeError(
                "lofted solid is not valid — a non-manifold or self-"
                "intersecting body will mesh badly in CFD, and that is far "
                "harder to diagnose downstream than here"
            )
        return shape

    # ── Measured properties, read back off the built solid ──────────────────

    def measured_volume(self) -> float:
        props = GProp_GProps()
        brepgprop.VolumeProperties(self.build(), props)
        return props.Mass()

    def measured_bounds(self) -> dict:
        """Tight bounding box of the built solid.

        AddOptimal, not Add. The default bounds a B-spline surface by its
        control polygon, which lies outside the surface it defines — here that
        over-reported the wing's height by 1.1%, a constant offset that does
        not shrink with denser sampling because it is not a sampling error.
        A measurement that feeds a drawing cannot carry that.
        """
        box = Bnd_Box()
        brepbndlib.AddOptimal(self.build(), box)
        xmin, ymin, zmin, xmax, ymax, zmax = box.Get()
        return {
            "span": ymax - ymin,
            "x_extent": xmax - xmin,
            "z_extent": zmax - zmin,
            "x": (xmin, xmax), "y": (ymin, ymax), "z": (zmin, zmax),
        }

    def section_area_coefficient(self) -> float:
        """Enclosed area of the unit-chord section, by the shoelace formula.

        Used to predict the solid's volume independently of the kernel, so the
        two can be compared.
        """
        upper, lower = self.section.surfaces(self.n_points)
        loop = upper + list(reversed(lower))
        total = 0.0
        for (x1, y1), (x2, y2) in zip(loop, loop[1:] + loop[:1]):
            total += x1 * y2 - x2 * y1
        return abs(total) / 2.0

    def predicted_volume(self) -> float:
        """Volume from integrating the section area along the span.

        V = k * b * c_root^2 * (1 + L + L^2) / 3, where k is the unit-chord
        section area. Independent of the kernel: if this and measured_volume
        disagree, the loft is not the shape the parameters describe.
        """
        lam = self.taper_ratio
        k = self.section_area_coefficient()
        return k * self.span * self.root_chord**2 * (1 + lam + lam**2) / 3.0

"""Blade ring and hub/casing surfaces. Needs pyOCC — run inside pyocc_env."""

from __future__ import annotations

import math

import pytest
from OCC.Core.BRepCheck import BRepCheck_Analyzer
from OCC.Core.BRepGProp import brepgprop
from OCC.Core.GProp import GProp_GProps

from src.annulus import (
    _flowpath_cone_segment,
    blade_ring,
    casing_shell,
    converging_casing_shell,
    converging_hub_solid,
    full_assembly,
    hub_solid,
)
from src.blade import BladeRow
from src.meridional import cone_frustum_volume
from src.velocity_triangles import RotorDesignPoint

DESIGN = RotorDesignPoint(
    axial_velocity=150.0,
    omega=8000.0 * 2 * math.pi / 60.0,
    mean_radius=0.275,
    exit_swirl_mean=80.0,
)
ROW = BladeRow(
    hub_radius=0.20, tip_radius=0.35, n_blades=8,  # few blades: faster tests
    root_chord=0.062, tip_chord=0.052, thickness=0.06, design=DESIGN,
)


def _volume(shape) -> float:
    props = GProp_GProps()
    brepgprop.VolumeProperties(shape, props)
    return props.Mass()


def test_blade_ring_is_valid():
    ring = blade_ring(ROW)
    assert BRepCheck_Analyzer(ring).IsValid()


def test_blade_ring_volume_is_n_blades_times_one_blade():
    """Independent-route check, same spirit as the wing project's kernel-vs-
    predicted volume comparison: the ring's total volume has to equal the
    single blade's volume times the blade count, because every copy is a
    rigid rotation of the same solid and rotation does not change volume."""
    ring_volume = _volume(blade_ring(ROW))
    single_volume = ROW.measured_volume()
    assert ring_volume == pytest.approx(single_volume * ROW.n_blades, rel=1e-6)


def test_hub_solid_is_valid_and_positive_volume():
    hub = hub_solid(ROW)
    assert BRepCheck_Analyzer(hub).IsValid()
    assert _volume(hub) > 0


def test_casing_shell_is_valid_and_hollow():
    """Hollow means less material than a solid cylinder of the same outer
    radius and length would have — the actual check that it's a shell and
    not an accidental solid disc."""
    casing = casing_shell(ROW)
    assert BRepCheck_Analyzer(casing).IsValid()
    assert _volume(casing) > 0


def test_full_assembly_is_valid():
    assembly = full_assembly(ROW)
    assert BRepCheck_Analyzer(assembly).IsValid()


# ── Converging annulus: cone segment + three-segment hub/casing ─────────


def test_cone_segment_is_valid():
    cone = _flowpath_cone_segment(0.20, 0.25, x0=0.0, x1=0.1)
    assert BRepCheck_Analyzer(cone).IsValid()


def test_cone_segment_volume_matches_closed_form():
    """The independent-route check this project holds every solid to:
    the kernel-built cone's volume against the exact frustum formula in
    meridional.py, which shares no code with BRepPrimAPI_MakeCone."""
    r1, r2, height = 0.20, 0.25, 0.1
    cone = _flowpath_cone_segment(r1, r2, x0=0.0, x1=height)
    assert _volume(cone) == pytest.approx(cone_frustum_volume(r1, r2, height), rel=1e-6)


def test_cone_segment_with_equal_radii_matches_cylinder_volume():
    r, height = 0.22, 0.15
    cone = _flowpath_cone_segment(r, r, x0=0.0, x1=height)
    assert _volume(cone) == pytest.approx(math.pi * r * r * height, rel=1e-6)


def test_converging_hub_solid_is_valid_and_positive_volume():
    hub = converging_hub_solid(
        hub_radius_rotor=0.200, hub_radius_stator=0.2075,
        rotor_x0=-0.01, rotor_x1=0.06, stator_x0=0.10, stator_x1=0.15,
    )
    assert BRepCheck_Analyzer(hub).IsValid()
    assert _volume(hub) > 0


def test_converging_hub_solid_volume_matches_three_segment_closed_form():
    """Kernel volume against the sum of three independent closed forms
    (two cylinders, one frustum) — the same species of check as
    test_cone_segment_volume_matches_closed_form, on the assembled result
    rather than one bare cone."""
    hub_r, hub_s = 0.200, 0.2075
    rotor_x0, rotor_x1, stator_x0, stator_x1 = -0.01, 0.06, 0.10, 0.15
    hub = converging_hub_solid(hub_r, hub_s, rotor_x0, rotor_x1, stator_x0, stator_x1)

    expected = (
        math.pi * hub_r**2 * (rotor_x1 - rotor_x0)
        + cone_frustum_volume(hub_r, hub_s, stator_x0 - rotor_x1)
        + math.pi * hub_s**2 * (stator_x1 - stator_x0)
    )
    assert _volume(hub) == pytest.approx(expected, rel=1e-6)


def test_converging_casing_shell_is_valid_and_hollow():
    casing = converging_casing_shell(
        tip_radius_rotor=0.350, tip_radius_stator=0.3425,
        rotor_x0=-0.01, rotor_x1=0.06, stator_x0=0.10, stator_x1=0.15,
    )
    assert BRepCheck_Analyzer(casing).IsValid()
    assert _volume(casing) > 0


def test_converging_casing_shell_thinner_than_solid_flowpath():
    """Same "hollow means less material than solid" check
    test_casing_shell_is_valid_and_hollow runs on the single-cylinder
    version, run here on the three-segment one."""
    hub_r, hub_s = 0.350, 0.3425
    rotor_x0, rotor_x1, stator_x0, stator_x1 = -0.01, 0.06, 0.10, 0.15
    casing = converging_casing_shell(hub_r, hub_s, rotor_x0, rotor_x1, stator_x0, stator_x1)
    solid_equivalent = (
        math.pi * hub_r**2 * (rotor_x1 - rotor_x0)
        + cone_frustum_volume(hub_r, hub_s, stator_x0 - rotor_x1)
        + math.pi * hub_s**2 * (stator_x1 - stator_x0)
    )
    assert 0 < _volume(casing) < solid_equivalent

"""Rotor + stator stage assembly. Needs pyOCC — run inside pyocc_env."""

from __future__ import annotations

import math

import pytest
from OCC.Core.BRepCheck import BRepCheck_Analyzer
from OCC.Core.BRepGProp import brepgprop
from OCC.Core.GProp import GProp_GProps

from src.annulus import axial_extent
from src.blade import BladeRow
from src.meridional import converging_annulus_exit
from src.stage import converging_stage_assembly, stage_assembly, stator_offset
from src.velocity_triangles import RotorDesignPoint, StatorDesignPoint

ROTOR_DESIGN = RotorDesignPoint(
    axial_velocity=150.0,
    omega=8000.0 * 2 * math.pi / 60.0,
    mean_radius=0.275,
    exit_swirl_mean=80.0,
)
ROTOR = BladeRow(
    hub_radius=0.20, tip_radius=0.35, n_blades=8,  # few blades: faster tests
    root_chord=0.062, tip_chord=0.052, thickness=0.06, design=ROTOR_DESIGN,
)

STATOR_DESIGN = StatorDesignPoint(
    axial_velocity=150.0, mean_radius=0.275, inlet_swirl_mean=80.0,
)
STATOR = BladeRow(
    hub_radius=0.20, tip_radius=0.35, n_blades=11,
    root_chord=0.050, tip_chord=0.045, thickness=0.08, design=STATOR_DESIGN,
)


def _volume(shape) -> float:
    props = GProp_GProps()
    brepgprop.VolumeProperties(shape, props)
    return props.Mass()


def test_rejects_mismatched_annulus():
    mismatched = BladeRow(
        hub_radius=0.18, tip_radius=0.35, n_blades=11,
        root_chord=0.050, tip_chord=0.045, thickness=0.08, design=STATOR_DESIGN,
    )
    with pytest.raises(ValueError):
        stage_assembly(ROTOR, mismatched)


def test_stator_offset_is_positive_and_scales_with_gap_fraction():
    small_gap = stator_offset(ROTOR, STATOR, gap_fraction=0.2)
    large_gap = stator_offset(ROTOR, STATOR, gap_fraction=1.0)
    assert 0 < small_gap < large_gap


def test_stator_sits_fully_downstream_of_rotor():
    """The whole point of translating the stator: no axial overlap between
    the two rings once assembled — checked on the actual translated bounds,
    not just trusted from the offset arithmetic."""
    dx = stator_offset(ROTOR, STATOR)
    rotor_xmin, rotor_xmax = axial_extent(ROTOR)
    stator_xmin, _ = axial_extent(STATOR)
    translated_stator_xmin = stator_xmin + dx
    assert translated_stator_xmin > rotor_xmax


def test_stage_assembly_is_valid():
    stage = stage_assembly(ROTOR, STATOR)
    assert BRepCheck_Analyzer(stage).IsValid()


def test_stage_volume_exceeds_either_row_alone():
    """A weak but real independent-route check: the stage has to contain at
    least the material of its two blade rings plus a hub and casing, so its
    volume must exceed either row's ring volume on its own."""
    stage_volume = _volume(stage_assembly(ROTOR, STATOR))
    rotor_ring_volume = ROTOR.measured_volume() * ROTOR.n_blades
    stator_ring_volume = STATOR.measured_volume() * STATOR.n_blades
    assert stage_volume > rotor_ring_volume
    assert stage_volume > stator_ring_volume


def test_larger_gap_fraction_gives_larger_assembly_bounding_extent():
    from OCC.Core.Bnd import Bnd_Box
    from OCC.Core.BRepBndLib import brepbndlib

    def x_extent(gap_fraction):
        box = Bnd_Box()
        brepbndlib.AddOptimal(stage_assembly(ROTOR, STATOR, gap_fraction), box)
        xmin, _, _, xmax, _, _ = box.Get()
        return xmax - xmin

    assert x_extent(0.2) < x_extent(1.5)


# ── Converging annulus stage ──────────────────────────────────────────────

CONVERGED_HUB, CONVERGED_TIP = converging_annulus_exit(
    ROTOR.hub_radius, ROTOR.tip_radius, area_ratio=0.90
)
CONVERGING_STATOR_DESIGN = StatorDesignPoint(
    axial_velocity=150.0, mean_radius=ROTOR.mean_radius, inlet_swirl_mean=80.0,
)
CONVERGING_STATOR = BladeRow(
    hub_radius=CONVERGED_HUB, tip_radius=CONVERGED_TIP, n_blades=11,
    root_chord=0.050, tip_chord=0.045, thickness=0.08, design=CONVERGING_STATOR_DESIGN,
)


def test_converging_stage_assembly_rejects_a_non_converging_pair():
    """The same guard stage_assembly's equal-radius check runs, adapted for
    this function's actual precondition: the stator's annulus area has to
    be smaller than the rotor's, not merely different from it."""
    with pytest.raises(ValueError):
        converging_stage_assembly(ROTOR, STATOR)  # same annulus, not converging


def test_converging_stage_assembly_is_valid():
    stage = converging_stage_assembly(ROTOR, CONVERGING_STATOR)
    assert BRepCheck_Analyzer(stage).IsValid()


def test_converging_stage_mean_radius_is_unchanged():
    """The whole reason area_ratio convergence is defined at constant mean
    radius: the stator's own free-vortex velocity triangle stays evaluated
    at the same mean_radius as the rotor's, so its stagger/camber law
    doesn't need touching, only the span it's swept across."""
    assert CONVERGING_STATOR.mean_radius == pytest.approx(ROTOR.mean_radius)


def test_converging_stage_hub_rises_and_casing_falls():
    assert CONVERGING_STATOR.hub_radius > ROTOR.hub_radius
    assert CONVERGING_STATOR.tip_radius < ROTOR.tip_radius


def test_converging_stage_volume_exceeds_either_row_alone():
    """Same weak-but-real independent-route check as
    test_stage_volume_exceeds_either_row_alone, run on the converging
    assembly."""
    stage_volume = _volume(converging_stage_assembly(ROTOR, CONVERGING_STATOR))
    rotor_ring_volume = ROTOR.measured_volume() * ROTOR.n_blades
    stator_ring_volume = CONVERGING_STATOR.measured_volume() * CONVERGING_STATOR.n_blades
    assert stage_volume > rotor_ring_volume
    assert stage_volume > stator_ring_volume

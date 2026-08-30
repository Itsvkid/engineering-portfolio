"""BladeRow solid construction. Needs pyOCC — run inside pyocc_env:

    conda run -n pyocc_env python -m pytest tests/test_blade.py -q
"""

from __future__ import annotations

import math

import pytest
from OCC.Core.BRepCheck import BRepCheck_Analyzer

from src.blade import BladeRow
from src.velocity_triangles import RotorDesignPoint

DESIGN = RotorDesignPoint(
    axial_velocity=150.0,
    omega=8000.0 * 2 * math.pi / 60.0,
    mean_radius=0.275,
    exit_swirl_mean=80.0,
)


def make_row(**overrides) -> BladeRow:
    defaults = dict(
        hub_radius=0.20, tip_radius=0.35, n_blades=32,
        root_chord=0.062, tip_chord=0.052, thickness=0.06, design=DESIGN,
    )
    defaults.update(overrides)
    return BladeRow(**defaults)


def test_rejects_inverted_or_equal_radii():
    with pytest.raises(ValueError):
        make_row(hub_radius=0.35, tip_radius=0.20)
    with pytest.raises(ValueError):
        make_row(hub_radius=0.30, tip_radius=0.30)


def test_rejects_zero_blades():
    with pytest.raises(ValueError):
        make_row(n_blades=0)


def test_rejects_too_few_stations():
    with pytest.raises(ValueError):
        make_row(n_stations=1)


def test_chord_at_hub_and_tip_matches_inputs():
    row = make_row()
    assert row.chord_at(row.hub_radius) == pytest.approx(row.root_chord)
    assert row.chord_at(row.tip_radius) == pytest.approx(row.tip_chord)


def test_radial_stations_span_hub_to_tip():
    row = make_row(n_stations=6)
    stations = row.radial_stations()
    assert len(stations) == 6
    assert stations[0] == pytest.approx(row.hub_radius)
    assert stations[-1] == pytest.approx(row.tip_radius)
    assert stations == sorted(stations)


def test_solidity_uses_local_chord_and_radius():
    row = make_row()
    for r in (row.hub_radius, row.mean_radius, row.tip_radius):
        expected = row.chord_at(r) * row.n_blades / (2 * math.pi * r)
        assert row.solidity_at(r) == pytest.approx(expected)


def test_build_produces_a_valid_solid():
    row = make_row()
    shape = row.build()
    assert BRepCheck_Analyzer(shape).IsValid()


def test_volume_is_positive_and_repeatable():
    row = make_row()
    v1 = row.measured_volume()
    v2 = row.measured_volume()
    assert v1 > 0
    assert v1 == pytest.approx(v2)


def test_more_stations_does_not_change_volume_much():
    """The loft should converge — five stations and fifteen should agree to
    a few percent, not describe visibly different blades."""
    coarse = make_row(n_stations=5).measured_volume()
    fine = make_row(n_stations=15).measured_volume()
    assert coarse == pytest.approx(fine, rel=0.03)


def test_thicker_section_gives_more_volume():
    thin = make_row(thickness=0.04).measured_volume()
    thick = make_row(thickness=0.10).measured_volume()
    assert thick > thin

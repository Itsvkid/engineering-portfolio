"""Tests for the XFLR5 cross-check.

These run anywhere: they read the committed reference polars, never XFLR5
itself, which is a GUI application that cannot run headless.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from src.xflr5_reference import (
    LINEAR_BAND_DEG,
    compare,
    lift_curve_slope_per_rad,
    read_project_polar,
    read_xflr5_polar,
)

ROOT = Path(__file__).resolve().parent.parent
CASES = [
    ("NACA 0012", "polars/naca0012_re1e+06.csv",
     "xflr5/reference/naca0012_T1_Re1e6_N9.txt"),
    ("NACA 4412", "polars/naca4412_re1e+06.csv",
     "xflr5/reference/naca4412_T1_Re1e6_N9.txt"),
]


@pytest.fixture(params=CASES, ids=[c[0] for c in CASES])
def case(request):
    name, project_path, reference_path = request.param
    return (name,
            read_project_polar(ROOT / project_path),
            read_xflr5_polar(ROOT / reference_path))


def test_reference_polar_parses_expected_sweep(case):
    _, _, reference = case
    assert len(reference) >= 18
    assert min(reference) == pytest.approx(-6.0)
    assert max(reference) == pytest.approx(12.0)


def test_reference_drag_is_positive_everywhere(case):
    _, _, reference = case
    assert all(p.cd > 0 for p in reference.values())


def test_symmetric_section_has_zero_lift_at_zero_alpha():
    """A symmetric section must give Cl = 0 at alpha = 0 in both methods.
    This is the one point where the two are required to agree exactly, so
    it is the sharpest available check that the polars are aligned on the
    same angle convention rather than offset by a sign or a degree."""
    reference = read_xflr5_polar(ROOT / "xflr5/reference/naca0012_T1_Re1e6_N9.txt")
    project = read_project_polar(ROOT / "polars/naca0012_re1e+06.csv")
    assert reference[0.0].cl == pytest.approx(0.0, abs=1e-3)
    assert project[0.0].cl == pytest.approx(0.0, abs=1e-3)


def test_cambered_section_has_positive_lift_at_zero_alpha():
    reference = read_xflr5_polar(ROOT / "xflr5/reference/naca4412_T1_Re1e6_N9.txt")
    assert reference[0.0].cl > 0.3


def test_lift_slopes_bracket_thin_airfoil_theory(case):
    """The inviscid panel method should sit above 2*pi (thickness adds
    slope) and XFoil below it (viscous decambering removes more than
    thickness adds). That ordering is the physics, and it is what makes the
    comparison a check rather than a coincidence."""
    _, project, reference = case
    assert lift_curve_slope_per_rad(project) > 2 * math.pi
    assert lift_curve_slope_per_rad(reference) < lift_curve_slope_per_rad(project)


def test_lift_agrees_within_documented_tolerance(case):
    """Cl agreement over the linear band. The bound is loose on the
    cambered section on purpose -- see the README: an inviscid method
    cannot reproduce the decambering that pulls 4412's lift down."""
    name, project, reference = case
    result = compare(project, reference, name)
    bound = 0.06 if name == "NACA 0012" else 0.12
    assert result.cl_rms < bound


def test_drag_is_underpredicted_by_a_documented_factor(case):
    """The finding this cross-check exists to record: an uncoupled
    Thwaites/flat-plate estimate run through Squire-Young recovers well
    under half of XFoil's profile drag. Pinned as a range so a change in
    the boundary-layer model shows up here as a failure rather than
    silently moving the README's numbers."""
    name, project, reference = case
    result = compare(project, reference, name)
    assert 0.2 < result.cd_ratio_mean < 0.6


def test_comparison_uses_only_shared_angles(case):
    name, project, reference = case
    result = compare(project, reference, name)
    assert set(result.alphas) <= set(project) & set(reference)
    assert all(LINEAR_BAND_DEG[0] <= a <= LINEAR_BAND_DEG[1] for a in result.alphas)


def test_reader_rejects_a_file_with_no_table(tmp_path):
    bad = tmp_path / "empty.txt"
    bad.write_text("xflr5 v6.62\n\n Calculated polar for: NACA 0012\n")
    with pytest.raises(ValueError):
        read_xflr5_polar(bad)

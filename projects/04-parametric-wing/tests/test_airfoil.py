"""NACA 4-digit sections against their published definition."""

import pytest

from src.airfoil import NACA4


@pytest.mark.parametrize("code, thickness", [
    ("0012", 0.12), ("2412", 0.12), ("4415", 0.15), ("0024", 0.24),
])
def test_max_thickness_matches_the_code(code, thickness):
    """The last two digits are the thickness, and it peaks near 30% chord."""
    x, t = NACA4.from_code(code).max_thickness_station()
    assert t == pytest.approx(thickness, rel=1e-3)
    assert 0.29 < x < 0.31


def test_digits_are_parsed_into_the_right_parameters():
    a = NACA4.from_code("2412")
    assert a.max_camber == pytest.approx(0.02)
    assert a.camber_position == pytest.approx(0.40)
    assert a.thickness == pytest.approx(0.12)


def test_symmetric_section_has_no_camber_anywhere():
    a = NACA4.from_code("0012")
    assert a.is_symmetric
    upper, lower = a.surfaces()
    for (xu, zu), (xl, zl) in zip(upper, lower):
        assert xu == pytest.approx(xl, abs=1e-12)
        assert zu == pytest.approx(-zl, abs=1e-12)


def test_trailing_edge_closes():
    """An open trailing edge leaves a gap that will not loft into a solid."""
    upper, lower = NACA4.from_code("2412", closed_trailing_edge=True).surfaces()
    assert upper[-1][0] == pytest.approx(1.0, abs=1e-9)
    assert upper[-1] == pytest.approx(lower[-1], abs=1e-12)


def test_open_trailing_edge_really_is_open():
    """The distinction has to be real, or the flag is decoration."""
    a = NACA4.from_code("2412", closed_trailing_edge=False)
    assert a.half_thickness(1.0) > 1e-4


def test_leading_edge_sits_at_the_origin():
    upper, lower = NACA4.from_code("4415").surfaces()
    assert upper[0] == pytest.approx((0.0, 0.0), abs=1e-12)
    assert lower[0] == pytest.approx((0.0, 0.0), abs=1e-12)


def test_cosine_spacing_clusters_points_at_the_leading_edge():
    """Uniform spacing facets the nose, which is where the eye goes first."""
    upper, _ = NACA4.from_code("0012").surfaces(n=100)
    first_gap = upper[1][0] - upper[0][0]
    mid = len(upper) // 2
    middle_gap = upper[mid + 1][0] - upper[mid][0]
    assert first_gap < middle_gap / 5


def test_rejects_malformed_codes():
    for bad in ("241", "24123", "24a2", ""):
        with pytest.raises(ValueError, match="four digits"):
            NACA4.from_code(bad)


def test_rejects_camber_with_no_position():
    """NACA 2012 is undefined — camber cannot peak at the leading edge."""
    with pytest.raises(ValueError, match="camber position 0"):
        NACA4.from_code("2012")


def test_rejects_too_few_points():
    with pytest.raises(ValueError, match="too coarse"):
        NACA4.from_code("0012").surfaces(n=5)

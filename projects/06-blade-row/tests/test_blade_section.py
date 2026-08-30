"""Circular-arc blade sections. No pyOCC import — runs anywhere."""

from __future__ import annotations

import math

import pytest

from src.blade_section import CircularArcSection


def test_rejects_nonpositive_thickness():
    with pytest.raises(ValueError):
        CircularArcSection(camber_angle_deg=20.0, thickness=0.0)


def test_symmetric_section_has_zero_camber_everywhere():
    sec = CircularArcSection(camber_angle_deg=0.0, thickness=0.08)
    assert sec.is_symmetric
    for x in (0.0, 0.1, 0.5, 0.9, 1.0):
        yc, dyc = sec.camber(x)
        assert yc == pytest.approx(0.0, abs=1e-12)
        assert dyc == pytest.approx(0.0, abs=1e-12)


def test_camberline_passes_through_chord_endpoints():
    sec = CircularArcSection(camber_angle_deg=20.0, thickness=0.08)
    yc_le, _ = sec.camber(0.0)
    yc_te, _ = sec.camber(1.0)
    assert yc_le == pytest.approx(0.0, abs=1e-9)
    assert yc_te == pytest.approx(0.0, abs=1e-9)


def test_camberline_peaks_at_midchord():
    """A circular arc symmetric about x=0.5 must have its highest point
    there — checked against every other station, not assumed."""
    sec = CircularArcSection(camber_angle_deg=25.0, thickness=0.08)
    yc_mid, _ = sec.camber(0.5)
    for x in (0.05, 0.2, 0.35, 0.65, 0.8, 0.95):
        yc, _ = sec.camber(x)
        assert yc < yc_mid


def test_camberline_symmetric_about_midchord():
    sec = CircularArcSection(camber_angle_deg=18.0, thickness=0.08)
    for x in (0.1, 0.25, 0.4):
        yc_left, _ = sec.camber(x)
        yc_right, _ = sec.camber(1.0 - x)
        assert yc_left == pytest.approx(yc_right, abs=1e-9)


def test_camberline_endpoint_slopes_are_half_the_camber_angle():
    """By construction (see the module docstring's circle geometry), the
    tangent at each end sits at +/- camber_angle/2 from the chord — the
    total turn from LE to TE is therefore exactly camber_angle_deg."""
    sec = CircularArcSection(camber_angle_deg=20.0, thickness=0.08)
    _, dyc_le = sec.camber(1e-9)
    _, dyc_te = sec.camber(1 - 1e-9)
    half = math.radians(20.0) / 2.0
    assert math.atan(dyc_le) == pytest.approx(half, abs=1e-4)
    assert math.atan(dyc_te) == pytest.approx(-half, abs=1e-4)


def test_more_camber_gives_taller_camberline():
    thin = CircularArcSection(camber_angle_deg=8.0, thickness=0.08)
    fat = CircularArcSection(camber_angle_deg=24.0, thickness=0.08)
    yc_thin, _ = thin.camber(0.5)
    yc_fat, _ = fat.camber(0.5)
    assert yc_fat > yc_thin


def test_surfaces_start_at_leading_edge_and_end_at_trailing_edge():
    sec = CircularArcSection(camber_angle_deg=15.0, thickness=0.08)
    upper, lower = sec.surfaces(80)
    assert upper[0][0] == pytest.approx(0.0, abs=1e-9)
    assert lower[0][0] == pytest.approx(0.0, abs=1e-9)
    assert upper[-1][0] == pytest.approx(1.0, abs=1e-9)
    assert lower[-1][0] == pytest.approx(1.0, abs=1e-9)


def test_surfaces_rejects_too_coarse_a_resolution():
    sec = CircularArcSection(camber_angle_deg=15.0, thickness=0.08)
    with pytest.raises(ValueError):
        sec.surfaces(10)


def test_upper_surface_stays_above_lower_surface():
    sec = CircularArcSection(camber_angle_deg=20.0, thickness=0.1)
    upper, lower = sec.surfaces(100)
    # Compare at matching indices; cosine spacing is symmetric so the x
    # stations of upper[i] and lower[i] coincide.
    for (xu, zu), (xl, zl) in zip(upper, lower):
        if 0.02 < xu < 0.98:  # skip the near-singular LE/TE region
            assert zu > zl

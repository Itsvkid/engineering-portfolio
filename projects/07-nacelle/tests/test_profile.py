"""NacelleProfile: closed-form limiting cases and integration checks.
No pyOCC import — runs anywhere."""

from __future__ import annotations

import math

import pytest

from src.cst import CSTCurve
from src.profile import (
    NacelleProfile,
    internal_clearance_ok,
    material_surface_area,
    material_volume,
)


def test_rejects_nonpositive_length():
    curve = CSTCurve(r0=1.0, r1=0.5, weights=(0.1,))
    with pytest.raises(ValueError):
        NacelleProfile(length=0.0, curve=curve)


def test_rejects_too_coarse_sampling():
    curve = CSTCurve(r0=1.0, r1=0.5, weights=(0.1,))
    with pytest.raises(ValueError):
        NacelleProfile(length=2.0, curve=curve, n_points=5)


def test_radius_at_ends_matches_curve_endpoints():
    curve = CSTCurve(r0=0.9, r1=0.5, weights=(0.2, 0.3))
    profile = NacelleProfile(length=3.0, curve=curve)
    assert profile.radius_at(0.0) == pytest.approx(0.9)
    assert profile.radius_at(3.0) == pytest.approx(0.5)


def test_cylinder_limiting_case_volume_matches_closed_form():
    """r0 = r1 = R and zero weights collapses the profile to a perfect
    cylinder — V = pi*R^2*L is exact, so the Simpson integration has to
    reproduce it to machine-ish precision, not just approximately."""
    R, L = 0.9, 3.2
    curve = CSTCurve(r0=R, r1=R, weights=(0.0, 0.0, 0.0))
    profile = NacelleProfile(length=L, curve=curve)
    assert profile.predicted_volume() == pytest.approx(math.pi * R**2 * L, rel=1e-9)


def test_cylinder_limiting_case_lateral_area_matches_closed_form():
    R, L = 0.9, 3.2
    curve = CSTCurve(r0=R, r1=R, weights=(0.0, 0.0, 0.0))
    profile = NacelleProfile(length=L, curve=curve)
    assert profile.predicted_lateral_area() == pytest.approx(2 * math.pi * R * L, rel=1e-6)


def test_cylinder_limiting_case_total_surface_matches_closed_form():
    R, L = 0.9, 3.2
    curve = CSTCurve(r0=R, r1=R, weights=(0.0, 0.0, 0.0))
    profile = NacelleProfile(length=L, curve=curve)
    expected = 2 * math.pi * R * L + 2 * math.pi * R**2
    assert profile.predicted_total_surface_area() == pytest.approx(expected, rel=1e-6)


def test_max_radius_exceeds_both_ends_for_a_bulging_profile():
    curve = CSTCurve(r0=0.85, r1=0.70, weights=(0.6, 0.6, 0.6))
    profile = NacelleProfile(length=3.0, curve=curve)
    _, r_max = profile.max_radius()
    assert r_max > profile.highlight_radius
    assert r_max > profile.trailing_radius


def test_max_radius_station_lies_within_the_length():
    curve = CSTCurve(r0=0.85, r1=0.70, weights=(0.6, 0.6, 0.6))
    profile = NacelleProfile(length=3.0, curve=curve)
    x_max, _ = profile.max_radius()
    assert 0.0 <= x_max <= 3.0


def test_meridian_points_span_the_full_length():
    curve = CSTCurve(r0=0.85, r1=0.70, weights=(0.4,))
    profile = NacelleProfile(length=4.0, curve=curve, n_points=50)
    points = profile.meridian_points()
    assert len(points) == 50
    assert points[0][0] == pytest.approx(0.0)
    assert points[-1][0] == pytest.approx(4.0)


def test_predicted_volume_grows_with_more_bulge():
    small_bulge = NacelleProfile(
        length=3.0, curve=CSTCurve(r0=0.8, r1=0.6, weights=(0.2, 0.2, 0.2))
    )
    big_bulge = NacelleProfile(
        length=3.0, curve=CSTCurve(r0=0.8, r1=0.6, weights=(1.0, 1.0, 1.0))
    )
    assert big_bulge.predicted_volume() > small_bulge.predicted_volume()


# ── Internal duct / hollow shell ─────────────────────────────────────────
# The math side of the "internal duct / inlet surface" outstanding item —
# see nacelle.py's CompleteNacelle for the pyOCC-dependent solid these
# check against.


def test_internal_clearance_ok_for_a_duct_well_inside_the_cowl():
    external = NacelleProfile(length=3.0, curve=CSTCurve(r0=0.85, r1=0.60, weights=(0.6, 0.9, 0.5)))
    internal = NacelleProfile(length=3.0, curve=CSTCurve(r0=0.75, r1=0.50, weights=(0.55, 0.65, 0.45)))
    assert internal_clearance_ok(external, internal)


def test_internal_clearance_catches_a_mid_span_crossing_not_just_the_ends():
    # Both endpoints of the internal curve sit inside the external cylinder
    # (0.5 < 0.7 and 0.4 < 0.7), but equal CST weights make the bump term a
    # constant 2.0 everywhere (the Bernstein partition-of-unity property
    # cst.py itself relies on), pushing the mid-span radius to ~1.45 — well
    # past the external radius of 0.7. A check that only compared the two
    # endpoints would call this valid; it isn't.
    external = NacelleProfile(length=3.0, curve=CSTCurve(r0=0.7, r1=0.7, weights=(0.0,)))
    internal = NacelleProfile(length=3.0, curve=CSTCurve(r0=0.5, r1=0.4, weights=(2.0, 2.0, 2.0)))
    assert internal.radius_at(1.5) > external.radius_at(1.5)  # confirms the crossing exists
    assert not internal_clearance_ok(external, internal)


def test_internal_clearance_rejects_mismatched_lengths():
    external = NacelleProfile(length=3.0, curve=CSTCurve(r0=0.85, r1=0.60, weights=(0.6,)))
    internal = NacelleProfile(length=2.5, curve=CSTCurve(r0=0.75, r1=0.50, weights=(0.5,)))
    with pytest.raises(ValueError):
        internal_clearance_ok(external, internal)


def test_material_volume_matches_closed_form_for_concentric_cylinders():
    """Two concentric cylinders is the hollow-shell equivalent of the plain
    cylinder limiting case above: an annulus of constant cross-section
    pi*(R_ext^2 - R_int^2), swept over length L — exact, no numerical
    integration error to allow for beyond what Simpson already carries."""
    R_ext, R_int, L = 0.9, 0.6, 3.2
    external = NacelleProfile(length=L, curve=CSTCurve(r0=R_ext, r1=R_ext, weights=(0.0,)))
    internal = NacelleProfile(length=L, curve=CSTCurve(r0=R_int, r1=R_int, weights=(0.0,)))
    expected = math.pi * (R_ext**2 - R_int**2) * L
    assert material_volume(external, internal) == pytest.approx(expected, rel=1e-9)


def test_material_surface_area_matches_closed_form_for_concentric_cylinders():
    R_ext, R_int, L = 0.9, 0.6, 3.2
    external = NacelleProfile(length=L, curve=CSTCurve(r0=R_ext, r1=R_ext, weights=(0.0,)))
    internal = NacelleProfile(length=L, curve=CSTCurve(r0=R_int, r1=R_int, weights=(0.0,)))
    expected = 2 * math.pi * L * (R_ext + R_int) + 2 * math.pi * (R_ext**2 - R_int**2)
    assert material_surface_area(external, internal) == pytest.approx(expected, rel=1e-6)


def test_material_volume_is_positive_for_a_realistic_duct():
    external = NacelleProfile(length=3.0, curve=CSTCurve(r0=0.85, r1=0.60, weights=(0.6, 0.9, 0.5)))
    internal = NacelleProfile(length=3.0, curve=CSTCurve(r0=0.75, r1=0.50, weights=(0.55, 0.65, 0.45)))
    assert material_volume(external, internal) > 0

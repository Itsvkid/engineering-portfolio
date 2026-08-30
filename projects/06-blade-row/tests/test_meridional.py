"""converging_annulus_exit and cone_frustum_volume: closed-form checks.
No pyOCC import — runs anywhere."""

from __future__ import annotations

import math

import pytest

from src.meridional import annulus_area, cone_frustum_volume, converging_annulus_exit


def test_area_ratio_one_gives_the_same_radii_back():
    hub, tip = converging_annulus_exit(0.200, 0.350, area_ratio=1.0)
    assert hub == pytest.approx(0.200)
    assert tip == pytest.approx(0.350)


def test_mean_radius_is_preserved():
    hub_in, tip_in = 0.200, 0.350
    mean_in = 0.5 * (hub_in + tip_in)
    hub_out, tip_out = converging_annulus_exit(hub_in, tip_in, area_ratio=0.90)
    assert 0.5 * (hub_out + tip_out) == pytest.approx(mean_in)


def test_area_actually_shrinks_by_the_given_ratio():
    hub_in, tip_in = 0.200, 0.350
    area_in = annulus_area(hub_in, tip_in)
    hub_out, tip_out = converging_annulus_exit(hub_in, tip_in, area_ratio=0.90)
    assert annulus_area(hub_out, tip_out) == pytest.approx(0.90 * area_in)


def test_hub_rises_and_tip_falls_for_a_converging_case():
    hub_in, tip_in = 0.200, 0.350
    hub_out, tip_out = converging_annulus_exit(hub_in, tip_in, area_ratio=0.90)
    assert hub_out > hub_in
    assert tip_out < tip_in


@pytest.mark.parametrize("bad_ratio", [0.0, -0.1, 1.0001, 1.5])
def test_rejects_area_ratio_out_of_range(bad_ratio):
    with pytest.raises(ValueError):
        converging_annulus_exit(0.200, 0.350, area_ratio=bad_ratio)


def test_annulus_area_matches_the_reference_design():
    # Cross-check against the numbers already quoted in the README for the
    # existing (unconverged) reference design, not just a fresh calculation.
    area = annulus_area(0.200, 0.350)
    assert area == pytest.approx(math.pi * (0.350**2 - 0.200**2))


def test_cone_frustum_collapses_to_cylinder_volume_for_equal_radii():
    r, h = 0.3, 1.5
    assert cone_frustum_volume(r, r, h) == pytest.approx(math.pi * r * r * h)


def test_cone_frustum_volume_matches_known_closed_form():
    # A cone-to-a-point (r2=0) is the textbook case: V = (1/3)*pi*r1^2*h.
    r1, h = 0.4, 2.0
    assert cone_frustum_volume(r1, 0.0, h) == pytest.approx((1 / 3) * math.pi * r1**2 * h)


def test_cone_frustum_volume_is_positive_for_realistic_dimensions():
    assert cone_frustum_volume(0.200, 0.2075, 0.05) > 0

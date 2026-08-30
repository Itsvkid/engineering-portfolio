import numpy as np
import pytest

from src.polar import sweep


def test_symmetric_airfoil_polar_is_antisymmetric():
    pts_pos = sweep("0012", [4.0], reynolds=1e6)[0]
    pts_neg = sweep("0012", [-4.0], reynolds=1e6)[0]
    assert pts_pos.cl == pytest.approx(-pts_neg.cl, abs=1e-6)
    # Drag is even in alpha for a symmetric section — same magnitude either
    # side of zero lift, not just "positive both times".
    assert pts_pos.cd == pytest.approx(pts_neg.cd, rel=1e-6)


def test_cambered_lifts_more_than_symmetric_at_the_same_alpha():
    a0012 = sweep("0012", [4.0], reynolds=1e6)[0]
    a4412 = sweep("4412", [4.0], reynolds=1e6)[0]
    assert a4412.cl > a0012.cl


def test_zero_alpha_drag_is_a_reasonable_low_speed_airfoil_value():
    # A sanity band, not a precision claim (see the README for the
    # documented gap between this and a real validated polar) — but it
    # should land somewhere a real subsonic airfoil's Cd,min actually
    # sits, not off by an order of magnitude.
    pt = sweep("0012", [0.0], reynolds=1e6)[0]
    assert 0.002 < pt.cd < 0.02


def test_higher_reynolds_number_reduces_drag():
    # Thinner boundary layers at higher Re — the qualitative trend every
    # viscous drag estimate should get right regardless of its precision.
    low_re = sweep("0012", [2.0], reynolds=2e5)[0]
    high_re = sweep("0012", [2.0], reynolds=5e6)[0]
    assert high_re.cd < low_re.cd

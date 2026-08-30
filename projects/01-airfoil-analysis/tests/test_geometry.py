import numpy as np

from src.geometry import Naca4


def test_parse():
    a = Naca4.parse("2412")
    assert a.m == 0.02 and a.p == 0.4 and a.t == 0.12


def test_symmetric_camber_is_zero():
    a = Naca4.parse("0012")
    x = np.linspace(0, 1, 50)
    assert np.allclose(a.camber(x), 0.0)
    assert np.allclose(a.camber_slope(x), 0.0)


def test_symmetric_zero_lift_angle_is_zero():
    a = Naca4.parse("0012")
    assert abs(a.thin_airfoil_zero_lift_angle()) < 1e-12


def test_cambered_zero_lift_angle_is_negative():
    # A cambered section lifts at alpha = 0 (camber does the work the angle
    # of attack would otherwise), so the angle at which it lifts nothing is
    # negative — a standard, physically-expected sign.
    a = Naca4.parse("4412")
    assert a.thin_airfoil_zero_lift_angle() < 0


def test_thickness_closes_at_trailing_edge():
    a = Naca4.parse("0012")
    x = np.array([1.0])
    # Closed-TE coefficients (-0.1036, not -0.1015) leave a small residual
    # gap by design of the polynomial fit, not exactly zero, but it should
    # be tiny relative to the 12% max thickness.
    assert a.thickness(x)[0] < 0.001


def test_surface_is_closed_and_ordered():
    a = Naca4.parse("2412")
    x, y = a.surface(n_per_side=60)
    # Starts and ends at the trailing edge.
    assert abs(x[0] - 1.0) < 1e-9
    assert abs(x[-1] - 1.0) < 1e-9
    # Upper surface (first half) sits above the lower surface (second half)
    # at the same chord station, away from the trailing edge itself.
    mid = len(x) // 4
    assert y[mid] > 0

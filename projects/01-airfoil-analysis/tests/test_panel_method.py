import numpy as np
import pytest

from src.geometry import Naca4
from src.panel_method import PanelGeometry, _influence_matrices, solve


def _panels(code="0012", n_per_side=120):
    a = Naca4.parse(code)
    x, y = a.surface(n_per_side)
    return a, PanelGeometry.from_surface(x, y)


def test_self_induced_velocity_matches_closed_form():
    # The textbook result this whole method rests on: a constant panel's
    # self-induced normal velocity (source) or tangential velocity
    # (vortex) is exactly half its own strength. Confirmed here directly
    # against _influence_matrices' diagonal, independent of the solve.
    _, geo = _panels("0012", n_per_side=40)
    Us, Vs, Uv, Vv = _influence_matrices(geo)
    normal = geo.normal
    tangent = geo.tangent
    self_normal_source = np.diag(Us) * normal[:, 0] + np.diag(Vs) * normal[:, 1]
    self_tangent_vortex = np.diag(Uv) * tangent[:, 0] + np.diag(Vv) * tangent[:, 1]
    assert np.allclose(self_normal_source, 0.5, atol=1e-9)
    assert np.allclose(self_tangent_vortex, 0.5, atol=1e-9)


def test_symmetric_airfoil_zero_lift_at_zero_alpha():
    _, geo = _panels("0012")
    sol = solve(geo, alpha_rad=0.0)
    assert abs(sol.cl) < 1e-8
    assert abs(sol.cl_surface) < 1e-3


def test_kutta_joukowski_matches_surface_pressure_integration():
    # Two independent routes to Cl — circulation (Kutta-Joukowski) and
    # integrating Cp around the surface — should agree if the solve is
    # actually self-consistent, the same species of cross-check project 08
    # runs on its own energy balance.
    _, geo = _panels("2412")
    for alpha_deg in [-4, 0, 4, 8]:
        sol = solve(geo, alpha_rad=np.radians(alpha_deg))
        assert sol.cl == pytest.approx(sol.cl_surface, abs=0.01)


def test_lift_curve_slope_matches_joukowski_thickness_correction():
    # A first pass compared straight to 2*pi/rad and failed at ~10% high —
    # not a bug: NACA 0012 is 12% thick, and it's a well-documented result
    # (the Joukowski-transform thickness correction) that finite thickness
    # *raises* the lift-curve slope above the zero-thickness limit, roughly
    # 2*pi*(1 + 0.77*t/c). For t/c = 0.12 that predicts ~6.86/rad, close to
    # what the panel method actually gives — the discrepancy against bare
    # thin-airfoil theory was real physics, not an error, and the test was
    # checking the wrong reference value.
    a, geo = _panels("0012")
    alphas = np.radians([-2, 0, 2])
    cls = [solve(geo, ar).cl for ar in alphas]
    slope = np.polyfit(alphas, cls, 1)[0]
    thickness_corrected = a.thin_airfoil_lift_slope() * (1 + 0.77 * a.t)
    assert slope == pytest.approx(thickness_corrected, rel=0.03)


def test_cambered_lift_curve_intercept_matches_thin_airfoil_theory():
    a, geo = _panels("4412")
    alphas_deg = np.array([-6, -4, -2, 0, 2])
    cls = [solve(geo, np.radians(d)).cl for d in alphas_deg]
    slope, intercept = np.polyfit(np.radians(alphas_deg), cls, 1)
    zero_lift_alpha = -intercept / slope
    assert zero_lift_alpha == pytest.approx(
        a.thin_airfoil_zero_lift_angle(), abs=np.radians(1.0)
    )


def test_more_panels_converges():
    # Refinement sanity check: Cl at a fixed alpha shouldn't be wandering
    # around as panel count increases — it should be settling.
    a = Naca4.parse("2412")
    cls = []
    for n in (40, 80, 160):
        x, y = a.surface(n)
        geo = PanelGeometry.from_surface(x, y)
        cls.append(solve(geo, alpha_rad=np.radians(4)).cl)
    assert abs(cls[2] - cls[1]) < abs(cls[1] - cls[0])

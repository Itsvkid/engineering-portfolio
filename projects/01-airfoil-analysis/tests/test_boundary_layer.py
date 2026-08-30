import numpy as np
import pytest

from src.boundary_layer import (
    _grow_turbulent_theta,
    _squire_young,
    _thwaites_theta,
    develop,
    michel_transition_index,
    thwaites_l,
)


def test_thwaites_matches_blasius_flat_plate():
    # Zero pressure gradient (constant U) is the one case with a known
    # exact answer to check an approximate method against: Blasius gives
    # Cf = 0.664/sqrt(Re_x). Thwaites is a curve-fit approximation, not an
    # exact solution, and is well known to sit a percent or two low on
    # this exact case — the tolerance here reflects that documented
    # property of the method, not slack for a bug.
    nu = 1.5e-5
    u_inf = 20.0
    x = np.linspace(1e-4, 1.0, 4000)
    u_edge = np.full_like(x, u_inf)
    theta = _thwaites_theta(x, u_edge, nu)

    # Masked before dividing, not after: theta[0] is exactly 0 by
    # construction (the stagnation-point start condition), which would
    # otherwise divide by zero for one element before the mask below ever
    # gets a chance to exclude it.
    mask = x > 0.1
    re_x = u_inf * x[mask] / nu
    lam = np.zeros(mask.sum())  # dU/dx = 0 identically for a flat plate
    cf_thwaites = 2 * thwaites_l(lam) / (u_inf * theta[mask] / nu)
    cf_blasius = 0.664 / np.sqrt(re_x)

    # White's power-law l(lambda) sits ~1% *above* Blasius here (a first
    # pass assumed "Thwaites runs low", based on the different quadratic
    # fit tried first, and expected the wrong direction) — still a tight
    # match either way.
    ratio = cf_thwaites / cf_blasius
    assert np.all((ratio > 0.98) & (ratio < 1.02))


def test_thwaites_theta_grows_like_sqrt_x_on_flat_plate():
    # x starts at exactly 0 here, not just near it: a flat plate has no
    # leading-edge singularity to dodge the way an airfoil's stagnation
    # point does, and starting at 1e-4 instead (a first-pass copy-paste
    # from the airfoil case) left theta=0 pinned at x=1e-4 while the
    # closed-form comparison assumed the integral truly started at 0 —
    # a small, systematic near-origin offset, not a real disagreement
    # (the two arrays already agreed to ~5e-5 relative by x=1).
    nu = 1.5e-5
    u_inf = 20.0
    x = np.linspace(0.0, 1.0, 2000)
    theta = _thwaites_theta(x, np.full_like(x, u_inf), nu)
    predicted = np.sqrt(0.45 * nu * x / u_inf)
    assert np.allclose(theta, predicted, rtol=1e-4, atol=1e-7)


def test_adverse_gradient_reduces_l_toward_separation():
    # l(lambda) is clipped to exactly 0 for the whole lambda <= -0.09
    # region (flow has separated; there's no attached-flow shear for the
    # power law to describe there), not just at a single crossing point —
    # a first-pass search for "wherever |l| is smallest" over a range
    # including that flat region found its very first point (lambda=-0.2)
    # instead of the -0.09 boundary. Bracketing the known boundary
    # directly is the right check, not a search over a region that isn't
    # single-valued.
    assert thwaites_l(np.array([-0.09]))[0] == pytest.approx(0.0, abs=1e-9)
    assert thwaites_l(np.array([-0.08]))[0] > 0
    assert thwaites_l(np.array([-0.2]))[0] == 0.0


def test_michel_transition_on_flat_plate_is_reynolds_dependent():
    # Higher freestream speed (higher Re) should trigger transition
    # earlier (smaller x) — the qualitative behaviour the criterion exists
    # to capture, checked without pinning an exact station. A first pass
    # used 5 and 40 m/s over a 1 m plate: at 25 m/s (partway between them)
    # transition landed at Re_theta within 0.1% of the critical value right
    # at x = 1.0, the domain's own last point — whether that registers as
    # "transitioned" was down to floating-point rounding, not physics.
    # 60/150 m/s clears that edge case with real margin.
    nu = 1.5e-5
    x = np.linspace(1e-4, 1.0, 4000)

    def transition_x(u_inf):
        u_edge = np.full_like(x, u_inf)
        theta = _thwaites_theta(x, u_edge, nu)
        idx = michel_transition_index(x, u_edge, theta, nu)
        return x[idx] if idx is not None else None

    x_slow = transition_x(60.0)
    x_fast = transition_x(150.0)
    assert x_slow is not None and x_fast is not None
    assert x_fast < x_slow


def test_squire_young_zero_momentum_thickness_gives_zero_drag():
    assert _squire_young(0.0, 1.4, 1.0, 1.0) == 0.0


def test_turbulent_growth_is_monotonic():
    x = np.linspace(0, 0.5, 50)
    u = np.full_like(x, 15.0)
    theta = _grow_turbulent_theta(x, u, theta0=0.001, nu=1.5e-5)
    assert np.all(np.diff(theta) > 0)


def test_develop_end_to_end_on_flat_plate_transitions_and_reports_reasonable_cd():
    nu = 1.5e-5
    x = np.linspace(1e-4, 1.0, 3000)
    u_edge = np.full_like(x, 60.0)  # see the transition test above for why
    result = develop(x, u_edge, nu, u_ref=60.0)
    assert result.transitioned_at is not None
    assert result.separated_at is None
    # A flat plate at this Reynolds number (~1.7e6) should land in the
    # ballpark of a real turbulent-transitioning flat plate's Cf, not
    # orders of magnitude off — a sanity band, not a precision claim.
    assert 0.001 < result.cd_side < 0.02

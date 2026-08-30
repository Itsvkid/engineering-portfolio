"""CST weight fitting. No pyOCC import — runs anywhere (needs numpy)."""

from __future__ import annotations

import pytest

from src.cst import CSTCurve
from src.fit import fit_residual, fit_weights


def test_fit_recovers_a_known_curve():
    """Sample points from a CST curve with known weights, fit against them,
    and confirm the fitted curve reproduces the original to near machine
    precision — this is the "does the benchmarking pipeline actually work"
    check, using a target whose right answer is known rather than trusting
    the fit blind."""
    truth = CSTCurve(r0=0.85, r1=0.55, weights=(0.9, 1.4, -0.3, 0.7), n1=0.5, n2=0.5)
    target = [(i / 40, truth(i / 40)) for i in range(41)]

    fitted_weights = fit_weights(target, r0=0.85, r1=0.55, order=3)
    fitted = CSTCurve(r0=0.85, r1=0.55, weights=fitted_weights)

    assert fit_residual(target, fitted) < 1e-9


def test_fit_residual_is_zero_for_a_perfect_match():
    curve = CSTCurve(r0=0.9, r1=0.6, weights=(0.5, 0.5))
    target = [(psi, curve(psi)) for psi in (0.0, 0.25, 0.5, 0.75, 1.0)]
    assert fit_residual(target, curve) == pytest.approx(0.0, abs=1e-12)


def test_fit_residual_is_positive_for_a_mismatched_curve():
    curve_a = CSTCurve(r0=0.9, r1=0.6, weights=(0.5, 0.5))
    curve_b = CSTCurve(r0=0.9, r1=0.6, weights=(2.0, -1.0))
    target = [(psi, curve_a(psi)) for psi in (0.1, 0.3, 0.5, 0.7, 0.9)]
    assert fit_residual(target, curve_b) > 0.01


def test_higher_order_fit_does_not_get_worse():
    """More degrees of freedom should never make a least-squares fit worse
    — a basic sanity check on the fitting machinery, not a claim about
    every possible target."""
    truth = CSTCurve(r0=0.85, r1=0.55, weights=(0.9, 1.4, -0.3, 0.7))
    target = [(i / 40, truth(i / 40)) for i in range(41)]

    low_order = CSTCurve(r0=0.85, r1=0.55,
                          weights=fit_weights(target, r0=0.85, r1=0.55, order=1))
    high_order = CSTCurve(r0=0.85, r1=0.55,
                           weights=fit_weights(target, r0=0.85, r1=0.55, order=5))

    assert fit_residual(target, high_order) <= fit_residual(target, low_order) + 1e-9


def test_rejects_negative_order():
    with pytest.raises(ValueError):
        fit_weights([(0.0, 1.0), (1.0, 0.5)], r0=1.0, r1=0.5, order=-1)

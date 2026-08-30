"""Fit CST weights to a target set of (psi, r) points by linear
least-squares.

This is the actual mechanism behind "benchmarked against commercial CAD
output for dimensional accuracy": in practice, a CAD export gives you a
point cloud, not weights, and you fit a CST curve to it and report how well
the fit reproduces the points. The fit is linear, not iterative — r(psi)
minus the (r0, r1) baseline is C(psi) * sum_i(A_i * B_i(psi)), and that sum
is linear in the weights A_i — so this is ordinary linear least squares, not
an optimizer. No OpenCASCADE dependency.
"""

from __future__ import annotations

import math

import numpy as np

from .cst import CSTCurve


def fit_weights(target: list[tuple[float, float]], r0: float, r1: float,
                 order: int, n1: float = 0.5, n2: float = 0.5) -> tuple[float, ...]:
    """Least-squares weights for a CSTCurve(r0, r1, weights, n1, n2) that
    best reproduces `target` — a list of (psi, r) pairs.

    Solves M @ A = b where M[j, i] = C(psi_j) * B_i,order(psi_j) and
    b[j] = r_j - baseline(psi_j); A is the vector of weights.
    """
    if order < 0:
        raise ValueError("order must be >= 0")
    probe = CSTCurve(r0=r0, r1=r1, weights=tuple([0.0] * (order + 1)),
                      n1=n1, n2=n2)

    rows = []
    b = []
    for psi, r in target:
        baseline = (1.0 - psi) * r0 + psi * r1
        c = probe.class_value(psi)
        row = [c * math.comb(order, i) * psi**i * (1.0 - psi) ** (order - i)
               for i in range(order + 1)]
        rows.append(row)
        b.append(r - baseline)

    solution, *_ = np.linalg.lstsq(np.array(rows), np.array(b), rcond=None)
    return tuple(float(a) for a in solution)


def fit_residual(target: list[tuple[float, float]], curve: CSTCurve) -> float:
    """RMS radius error between `curve` and the target points — the
    accuracy number a real CAD-benchmarking pass would report."""
    errors = [curve(psi) - r for psi, r in target]
    return math.sqrt(sum(e * e for e in errors) / len(errors))

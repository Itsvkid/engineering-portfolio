"""Fit a CST curve to the real NACA 1-85-100 (CR 1.009) external ordinates
from NASA TM 110300 (see reference_data.py) — the actual geometry the
OpenFOAM case's surface is built from, not project 07's own arbitrary
reference design.

This is real dimensional benchmarking against a published point cloud, the
same mechanism src/fit.py's docstring describes for a CATIA export, just
using a NACA report's ordinate table as the external point cloud instead
— pure Python, no OpenCASCADE, no OpenFOAM, runs anywhere pytest does.

Run:
    cd projects/07-nacelle
    python -m openfoam.fit_reference_geometry
"""

from __future__ import annotations

import math
from pathlib import Path

from src.cst import CSTCurve
from src.fit import fit_residual, fit_weights

from .reference_data import EXTERNAL_ORDINATES_PERCENT, L_INCHES, RMAX_INCHES

INCH_TO_M = 0.0254

# Order high enough that residual is dominated by how well a CST curve CAN
# represent this shape, not by too few degrees of freedom — chosen the same
# way project 07's own reference design's fit-recovery demo picks an order,
# not tuned per curve to force a good-looking number.
CST_ORDER = 8


def target_points_m() -> list[tuple[float, float]]:
    """The real external ordinates, converted from percent/inches to
    (psi, r) in metres — psi = X/L in [0, 1], r = physical radius."""
    l_m = L_INCHES * INCH_TO_M
    rmax_m = RMAX_INCHES * INCH_TO_M
    points = []
    for x_l_pct, r_rmax_pct in EXTERNAL_ORDINATES_PERCENT:
        psi = x_l_pct / 100.0
        r = (r_rmax_pct / 100.0) * rmax_m
        points.append((psi, r))
    return points


def fit_target_curve(order: int = CST_ORDER) -> CSTCurve:
    """The CST curve fitted to the real NACA 1-85-100 (CR 1.009) external
    ordinates. r0 and r1 are read directly off the target data's own
    endpoints (psi=0 and psi=1), not assumed — the curve's endpoints are
    then exact by construction (CSTCurve's class function vanishes at
    psi=0 and psi=1), matching the target data's own endpoints exactly
    regardless of fit quality in between.
    """
    points = target_points_m()
    r0 = points[0][1]
    r1 = points[-1][1]
    weights = fit_weights(points, r0=r0, r1=r1, order=order)
    return CSTCurve(r0=r0, r1=r1, weights=weights)


def length_m() -> float:
    return L_INCHES * INCH_TO_M


def main() -> None:
    points = target_points_m()
    curve = fit_target_curve()
    residual = fit_residual(points, curve)
    l_m = length_m()

    print(f"{'target points':<24}{len(points)}")
    print(f"{'CST order':<24}{CST_ORDER}")
    print(f"{'cowl length L':<24}{l_m:.4f} m ({L_INCHES:.2f} in)")
    print(f"{'r0 (highlight)':<24}{curve.r0:.5f} m")
    print(f"{'r1 (max radius)':<24}{curve.r1:.5f} m")
    print(f"{'RMS fit residual':<24}{residual * 1000:.4f} mm "
          f"({residual / curve.r1 * 100:.3f}% of max radius)")

    max_err = max(abs(curve(psi) - r) for psi, r in points)
    print(f"{'max fit residual':<24}{max_err * 1000:.4f} mm")

    figures_dir = Path(__file__).parent / "figures"
    figures_dir.mkdir(exist_ok=True)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        psis = [p for p, _ in points]
        rs = [r * 1000 for _, r in points]
        fine = [i / 400 for i in range(1, 400)]
        fit_rs = [curve(p) * 1000 for p in fine]

        fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
        ax.plot(fine, fit_rs, color="#2874a6", linewidth=1.8, label="CST fit", zorder=2)
        ax.plot(psis, rs, "o", color="#c0392b", markersize=5,
                label="NASA TM 110300, Table II", zorder=3)
        ax.set_xlabel("psi = x/L")
        ax.set_ylabel("radius, mm")
        ax.set_title("CST fit to NACA 1-85-100 (CR 1.009) external ordinates")
        ax.legend(frameon=False)
        ax.grid(alpha=0.3)
        fig.tight_layout()
        path = figures_dir / "cst-fit-to-naca-1-85-100.png"
        fig.savefig(path)
        plt.close(fig)
        print(f"\nwrote {path}")
    except ImportError:
        print("\n(matplotlib not available — skipped the comparison figure)")


if __name__ == "__main__":
    main()

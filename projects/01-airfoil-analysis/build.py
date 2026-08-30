"""Solve NACA 0012 (symmetric) vs NACA 4412 (cambered) across an alpha
sweep, print a summary, and write figures + a polar CSV.

Run:
    python build.py
"""

import csv
from pathlib import Path

import numpy as np

from src.plotting import (
    cl_alpha_figure,
    cp_distribution_figure,
    drag_polar_figure,
    efficiency_figure,
    xflr5_validation_figure,
)
from src.polar import sweep
from src.xflr5_reference import compare, read_project_polar, read_xflr5_polar

REYNOLDS = 1.0e6  # representative light-aircraft / UAV cruise Reynolds number
ALPHAS_DEG = np.arange(-6, 13, 1.0)


def main() -> None:
    polars = {code: sweep(code, ALPHAS_DEG, reynolds=REYNOLDS) for code in ("0012", "4412")}

    print(f"Re = {REYNOLDS:.1e}\n")
    for code, pts in polars.items():
        print(f"NACA {code}")
        print(f"{'alpha':>7}{'Cl':>9}{'Cd':>10}{'L/D':>9}  separation")
        for p in pts:
            ld = p.cl / p.cd if p.cd else float("nan")
            sep = "upper" if p.upper_separated else ""
            sep += "+lower" if p.lower_separated else ""
            print(f"{p.alpha_deg:7.1f}{p.cl:9.3f}{p.cd:10.5f}{ld:9.1f}  {sep}")
        print()

    Path("polars").mkdir(exist_ok=True)
    for code, pts in polars.items():
        with open(f"polars/naca{code}_re{REYNOLDS:.0e}.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["alpha_deg", "cl", "cd", "upper_separated", "lower_separated"])
            for p in pts:
                writer.writerow([p.alpha_deg, p.cl, p.cd, p.upper_separated, p.lower_separated])

    print("wrote", cl_alpha_figure(ALPHAS_DEG, polars, "figures/cl-alpha.png"))
    print("wrote", drag_polar_figure(polars, "figures/drag-polar.png"))
    print("wrote", efficiency_figure(ALPHAS_DEG, polars, "figures/efficiency.png"))
    print("wrote", cp_distribution_figure(6.0, "figures/cp-distribution.png"))

    # Cross-check against XFLR5, from the committed reference polars under
    # xflr5/reference/ -- no XFLR5 install needed here. Regenerate those with
    # `python xflr5/run_analysis.py` (needs a macOS GUI session).
    project = {code: read_project_polar(f"polars/naca{code}_re{REYNOLDS:.0e}.csv")
               for code in polars}
    reference = {code: read_xflr5_polar(f"xflr5/reference/naca{code}_T1_Re1e6_N9.txt")
                 for code in polars}

    print("\nCross-check against XFLR5 v6.62 (XFoil), Re = 1e6, NCrit = 9")
    for code in sorted(project):
        print(" ", compare(project[code], reference[code], f"NACA {code}").summary())

    for theme in ("light", "dark"):
        suffix = "-dark" if theme == "dark" else ""
        print("wrote", xflr5_validation_figure(
            project, reference, f"figures/xflr5-validation{suffix}.png", theme))


if __name__ == "__main__":
    main()

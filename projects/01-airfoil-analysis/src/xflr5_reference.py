"""Reading XFLR5's polar output, and comparing it against this project's own.

Everything this project validated against before was closed-form or
internal: a panel's self-induced velocity, two internal routes to the same
Cl, the Blasius flat-plate solution. All four are checks that the code
implements the mathematics it claims to. None of them is an *independent
solver* disagreeing.

XFLR5 (v6.62) is that independent solver. It wraps Mark Drela's XFoil —
a coupled inviscid/boundary-layer method with a real e^N transition model —
so it is not a second opinion from the same family of assumptions. Where
this project's panel method is inviscid with a bolt-on boundary-layer drag
estimate, XFoil solves the two together. The places the two disagree are
therefore informative rather than embarrassing: they locate exactly which
physics the simpler method leaves out.

This module has no dependency on XFLR5 itself. It reads polar files that
were produced earlier and committed under `xflr5/reference/`, so the
comparison reruns anywhere, including in CI on a machine with no GUI.
See `xflr5/README.md` for how those files are regenerated.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# The angle-of-attack band over which the two methods are compared
# quantitatively. Above roughly 8 degrees XFoil's coupled boundary layer
# starts shedding lift that an inviscid panel method has no mechanism to
# lose, so a headline "RMS difference" taken across the full sweep would be
# reporting the onset of stall rather than the accuracy of the solver.
LINEAR_BAND_DEG = (-4.0, 8.0)


@dataclass(frozen=True)
class PolarPoint:
    alpha_deg: float
    cl: float
    cd: float


def read_xflr5_polar(path) -> dict[float, PolarPoint]:
    """Parse an XFLR5 'XFoil polar format' text export, keyed by alpha.

    The file carries a header block of provenance (version, foil name,
    Reynolds, Mach, NCrit) and then a comma-separated table introduced by a
    line beginning 'alpha,'. Anything before that line is metadata; the
    table itself has more columns than are used here (Cm, transition
    locations, Cpmin), and trailing columns vary between versions, so only
    the first three are read by position.
    """
    points: dict[float, PolarPoint] = {}
    in_table = False
    for line in Path(path).read_text().splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("alpha,"):
            in_table = True
            continue
        if not in_table or not stripped:
            continue
        fields = [f.strip() for f in stripped.split(",")]
        if len(fields) < 3:
            continue
        try:
            alpha, cl, cd = float(fields[0]), float(fields[1]), float(fields[2])
        except ValueError:
            # A non-converged operating point is written as blanks or dashes
            # rather than omitted; skipping it is correct, and is why the two
            # polars are matched on alpha rather than zipped by index.
            continue
        points[round(alpha, 6)] = PolarPoint(alpha, cl, cd)
    if not points:
        raise ValueError(f"no polar table found in {path}")
    return points


def read_project_polar(path) -> dict[float, PolarPoint]:
    """Parse this project's own polar CSV, keyed by alpha the same way."""
    points: dict[float, PolarPoint] = {}
    with Path(path).open() as handle:
        for row in csv.DictReader(handle):
            alpha = float(row["alpha_deg"])
            points[round(alpha, 6)] = PolarPoint(alpha, float(row["cl"]),
                                                 float(row["cd"]))
    if not points:
        raise ValueError(f"no rows in {path}")
    return points


def lift_curve_slope_per_rad(points: dict[float, PolarPoint],
                            band=LINEAR_BAND_DEG) -> float:
    """Least-squares dCl/dalpha in per-radian, over the linear band.

    Thin-airfoil theory puts this at 2*pi for any thin section. A real
    section with thickness sits slightly above it inviscidly, and viscous
    decambering pulls it back below — so the slope is a compact way to see
    which of those two effects a method does and does not contain.
    """
    alphas = sorted(a for a in points if band[0] <= a <= band[1])
    if len(alphas) < 3:
        raise ValueError("need at least three points in the linear band")
    slope_per_deg = np.polyfit(alphas, [points[a].cl for a in alphas], 1)[0]
    return float(np.degrees(slope_per_deg))


@dataclass(frozen=True)
class Comparison:
    """One airfoil's worth of agreement between the two methods."""

    name: str
    alphas: list[float]
    cl_rms: float
    cl_mean_abs: float
    cl_max_abs: float
    cd_ratio_mean: float
    cd_ratio_min: float
    cd_ratio_max: float
    slope_project: float
    slope_reference: float

    def summary(self) -> str:
        return (
            f"{self.name}: {len(self.alphas)} matched alphas over "
            f"{LINEAR_BAND_DEG[0]:.0f}..{LINEAR_BAND_DEG[1]:.0f} deg | "
            f"Cl RMS {self.cl_rms:.4f}, max |diff| {self.cl_max_abs:.4f} | "
            f"Cd ratio {self.cd_ratio_mean:.2f}x | "
            f"slope {self.slope_project:.2f} vs {self.slope_reference:.2f} /rad"
        )


def compare(project: dict[float, PolarPoint], reference: dict[float, PolarPoint],
            name: str, band=LINEAR_BAND_DEG) -> Comparison:
    """Agreement statistics over the linear band, on alphas both solved.

    Cl is compared as a difference and Cd as a *ratio*, deliberately. A drag
    coefficient of 0.005 against 0.012 is a difference of 0.007, which reads
    as negligible and is not: it is a factor of 2.4, and the factor is the
    thing worth reporting.
    """
    shared = sorted(a for a in (set(project) & set(reference))
                    if band[0] <= a <= band[1])
    if not shared:
        raise ValueError("no overlapping angles of attack in the linear band")

    cl_diff = np.array([project[a].cl - reference[a].cl for a in shared])
    cd_ratio = np.array([project[a].cd / reference[a].cd for a in shared])

    return Comparison(
        name=name,
        alphas=shared,
        cl_rms=float(np.sqrt(np.mean(cl_diff ** 2))),
        cl_mean_abs=float(np.mean(np.abs(cl_diff))),
        cl_max_abs=float(np.max(np.abs(cl_diff))),
        cd_ratio_mean=float(np.mean(cd_ratio)),
        cd_ratio_min=float(np.min(cd_ratio)),
        cd_ratio_max=float(np.max(cd_ratio)),
        slope_project=lift_curve_slope_per_rad(project, band),
        slope_reference=lift_curve_slope_per_rad(reference, band),
    )

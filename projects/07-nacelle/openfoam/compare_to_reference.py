"""Compare a solved case's cowl surface pressure against NASA TM 110300's
real Table V(a) data (reference_data.FOREBODY_CP_TOP) — the actual point
of this whole exercise, and the one piece of this deliverable that cannot
be run or verified without an actual OpenFOAM solve (see ../README.md).

Reads case/postProcessing/cowlSurfaceSample/<time>/cowlPatch_p.raw, written
by controlDict's cowlSurfaceSample function object — OpenFOAM's `raw`
surface format: a `#`-prefixed header line, then one "x y z p" row per
boundary face centre. This script picks out the top-meridian trace itself
(faces near y=0, z>0) rather than relying on any special sampling geometry
in the OpenFOAM dictionaries — see controlDict's comment for why.

Run once a solve exists:
    cd projects/07-nacelle
    python -m openfoam.compare_to_reference
"""

from __future__ import annotations

import math
from pathlib import Path

from .reference_data import ANGLE_OF_ATTACK_DEG, FOREBODY_CP_TOP, L_INCHES, MACH, MASS_FLOW_RATIO
from .freestream_conditions import freestream_state
from .reference_data import REYNOLDS_PER_FOOT_RANGE

INCH_TO_M = 0.0254

# Axial bin width for grouping face centres into stations, in the STL's own
# metres. Chosen against the real mesh once a solve existed to check
# against: cowlAndAfterbody has only ~1252 faces on the full body of
# revolution (~27 around the circumference), so a tight y~0 "top meridian"
# band (originally 1cm, written blind before any solve existed) missed
# almost every axial station -- caught by running this and finding 1
# matched point out of 1252 faces.
AXIAL_BIN_M = 0.005


def parse_raw_surface(path) -> list[tuple[float, float, float, float]]:
    """Rows of (x, y, z, p) from an OpenFOAM raw surface sample file."""
    rows = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        x, y, z, p = (float(v) for v in line.split())
        rows.append((x, y, z, p))
    return rows


def axial_pressure_trace(rows: list[tuple[float, float, float, float]]
                          ) -> list[tuple[float, float]]:
    """(x, p) pairs, sorted by x, one per axial bin.

    This case is an isolated axisymmetric body at alpha=0 deg (reference_data.
    ANGLE_OF_ATTACK_DEG), so Cp should be circumferentially uniform by
    symmetry -- there is no distinguished "top" meridian in the solved flow
    itself, only in NASA TM 110300's own reporting convention (which picks
    one meridian on a real physical model, where circumferential uniformity
    is an experimental result, not a given). Averaging p over ALL
    circumferential faces at each axial station uses that symmetry directly:
    it is more robust to this mesh's coarse ~27-faces-around resolution than
    hunting for faces that happen to sit near y=0, and it reduces face-to-face
    discretisation noise by averaging rather than sampling a single face.
    A true nonzero-alpha case would need the original meridian-only approach.
    """
    from collections import defaultdict

    bins: dict[int, list[float]] = defaultdict(list)
    for x, y, z, p in rows:
        bins[round(x / AXIAL_BIN_M)].append(p)

    trace = [
        (bin_index * AXIAL_BIN_M, sum(ps) / len(ps))
        for bin_index, ps in bins.items()
    ]
    return sorted(trace)


def to_cp(pressures: list[tuple[float, float]], p_inf: float, rho_inf: float,
          v_inf: float) -> list[tuple[float, float]]:
    """(x, Cp) from (x, p) — Cp = (p - p_inf) / (0.5 * rho_inf * v_inf^2)."""
    q_inf = 0.5 * rho_inf * v_inf ** 2
    return [(x, (p - p_inf) / q_inf) for x, p in pressures]


def interpolate(trace: list[tuple[float, float]], x: float) -> float | None:
    """Linear interpolation of a sorted (x, value) trace at `x`; None if x
    falls outside the trace's range rather than extrapolating silently."""
    if x < trace[0][0] or x > trace[-1][0]:
        return None
    for (x0, v0), (x1, v1) in zip(trace, trace[1:]):
        if x0 <= x <= x1:
            if x1 == x0:
                return v0
            t = (x - x0) / (x1 - x0)
            return v0 + t * (v1 - v0)
    return None


def compare(cp_trace_m: list[tuple[float, float]]) -> dict:
    """cp_trace_m: (x in metres from the highlight, Cp) from a solve.
    Interpolates the solved trace onto reference_data.FOREBODY_CP_TOP's own
    X/L stations (converted to metres) and reports the error at each —
    the same "interpolate the model onto the reference's stations, not the
    other way round" convention project 05 and project 08 both use.
    """
    l_m = L_INCHES * INCH_TO_M
    results = []
    for x_l_pct, cp_ref in FOREBODY_CP_TOP:
        x_m = (x_l_pct / 100.0) * l_m
        cp_model = interpolate(cp_trace_m, x_m)
        results.append({
            "x_l_pct": x_l_pct,
            "cp_reference": cp_ref,
            "cp_model": cp_model,
            "error": None if cp_model is None else cp_model - cp_ref,
        })
    return {"stations": results}


def main() -> None:
    here = Path(__file__).parent
    pattern = here / "case" / "postProcessing" / "cowlSurfaceSample"
    if not pattern.exists():
        raise SystemExit(
            f"No postProcessing output at {pattern} -- run the case first "
            "(see case/Allrun) before comparing."
        )

    time_dirs = sorted(pattern.iterdir(), key=lambda p: float(p.name))
    latest = time_dirs[-1]
    # OpenFOAM's raw surface writer names files "<field>_<surfaceName>.raw"
    # (field first) -- e.g. "p_cowlPatch.raw" -- not "<surfaceName>_<field>"
    # as first guessed here before any solve existed to check against.
    raw_files = list(latest.glob("p_*.raw"))
    if not raw_files:
        raise SystemExit(f"No p_*.raw file found under {latest}")

    rows = parse_raw_surface(raw_files[0])
    trace_p = axial_pressure_trace(rows)

    state = freestream_state(MACH, sum(REYNOLDS_PER_FOOT_RANGE) / 2.0)
    trace_cp = to_cp(trace_p, state["pressure_pa"], state["density_kg_m3"],
                      state["velocity_m_s"])

    result = compare(trace_cp)

    print(f"Comparing against NASA TM 110300, Table V(a): M={MACH}, "
          f"mfr={MASS_FLOW_RATIO}, alpha={ANGLE_OF_ATTACK_DEG} deg\n")
    print(f"{'X/L, %':>8}{'Cp (NASA)':>12}{'Cp (model)':>12}{'error':>10}")
    errors = []
    for row in result["stations"]:
        cp_model = row["cp_model"]
        error = row["error"]
        if cp_model is None:
            print(f"{row['x_l_pct']:>8.2f}{row['cp_reference']:>12.4f}"
                  f"{'--':>12}{'--':>10}")
        else:
            print(f"{row['x_l_pct']:>8.2f}{row['cp_reference']:>12.4f}"
                  f"{cp_model:>12.4f}{error:>10.4f}")
            errors.append(error)

    if errors:
        rms = math.sqrt(sum(e * e for e in errors) / len(errors))
        print(f"\nRMS Cp error over {len(errors)} matched stations: {rms:.4f}")


if __name__ == "__main__":
    main()

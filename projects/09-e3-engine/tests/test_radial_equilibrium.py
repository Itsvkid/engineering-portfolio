"""C2 unit 8: radial equilibrium against the printed through-flow
(solvers/throughflow/STEP0.md unit 8)."""
import math
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from throughflow.radial_equilibrium import (  # noqa: E402
    balance_with_curvature, curvature_terms, gas_path_stations, load, residual, slope_check,
    station_points,
)

XXI = load()
SLOPES = slope_check(XXI)
BALANCE = balance_with_curvature()


def test_printed_slope_is_the_geometric_slope():
    """finding 31: the phi column reproduces atan(dr/dz) from the table's
    own coordinates"""
    d = [abs(x["printed"] - x["geometric"]) for x in SLOPES]
    assert len(d) == 480      # 40 interior stations x 12 streamlines
    assert statistics.mean(d) < 1.0
    assert statistics.mean(d) < 0.5


def test_slope_sign_convention_is_the_ordinary_one():
    same = statistics.mean(abs(x["printed"] - x["geometric"]) for x in SLOPES)
    flipped = statistics.mean(abs(x["printed"] + x["geometric"]) for x in SLOPES)
    assert same < flipped / 5


def _weighted(key):
    return sum(r[key] * r["n"] for r in BALANCE) / sum(r["n"] for r in BALANCE)


def test_simple_radial_equilibrium_balances():
    assert _weighted("simple") < 0.30


def test_curvature_term_improves_the_balance():
    """finding 30: the discarded term is a third of what simple radial
    equilibrium leaves over"""
    simple, full = _weighted("simple"), _weighted("full")
    assert full < simple
    assert (simple - full) / simple > 0.20
    better = sum(1 for r in BALANCE if r["full"] < r["simple"])
    assert better > len(BALANCE) / 2
    assert better >= 30


def test_the_left_hand_side_is_a_cancellation():
    """finding 32: dh0/dr and T ds/dr differ by an order of magnitude from
    their difference, which is why the analytic form is used"""
    from e3cycle import gas
    row = next(r for r in XXI["rows"] if r["row"] == "stator" and r.get("stage") == 5)
    pts = sorted(station_points(XXI, row, "inlet"), key=lambda p: p.r)
    r = [p.r for p in pts]
    h0 = [gas.h(p.t0) for p in pts]
    s = [gas.phi(p.t0) - gas.R_AIR * math.log(p.p0) for p in pts]
    res = residual(pts)
    ratios = []
    for i in range(1, len(pts) - 1):
        dh0 = (h0[i + 1] - h0[i - 1]) / (r[i + 1] - r[i - 1])
        tds = pts[i].ts * (s[i + 1] - s[i - 1]) / (r[i + 1] - r[i - 1])
        if abs(res[i]["lhs"]) > 1:
            ratios.append(abs(dh0) / abs(res[i]["lhs"]))
            ratios.append(abs(tds) / abs(res[i]["lhs"]))
    assert max(ratios) > 5
    assert statistics.median(ratios) > 2


def test_curvature_terms_cover_every_interior_station():
    curv = curvature_terms(XXI)
    stations = gas_path_stations(XXI)
    assert len(curv) == len(stations) - 2
    assert all(len(v) == 12 for v in curv.values())

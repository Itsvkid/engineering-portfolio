"""C1 unit 4b: the HPC loss roll-up by two routes, both from Table XXI
(solvers/meanline/STEP0.md unit 4b)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from meanline.compressor import (  # noqa: E402
    _sl, efficiency_from_printed_ratios, load, pressure_chain_from_losses, rollup,
)

R = rollup()
XXI = load()[0]
CUM = {s["sl"]: s.get("cum_eff") for s in _sl(XXI, XXI["rows"][-1])}


def test_route1_reproduces_the_printed_cumulative_efficiency():
    """real-gas efficiency from the printed pressure and temperature ratios
    against Table XXI's own cum_eff column, streamline by streamline"""
    d = [abs(x["eta"] - CUM[x["sl"]]) for x in R["per_sl"] if CUM.get(x["sl"])]
    assert len(d) == 12
    assert max(d) < 0.010, max(d)
    assert sum(d) / len(d) < 0.005


def test_area_weighted_efficiency_meets_the_design_intent():
    assert abs(R["eta_area_weighted"] - R["design_intent"]) < 0.010


def test_area_weighted_pressure_ratio():
    assert abs(R["pr_area_weighted"] / R["design_pr"] - 1) < 0.02


def test_route2_pressure_chain_from_losses_alone():
    """21 rows of printed loss coefficients compounded through a real-gas
    chain rebuild the printed pressure ratio (finding 14)"""
    d = [x["pr_model"] / x["pr_printed"] - 1 for x in R["chain"]]
    assert len(d) == 12
    assert abs(sum(d) / len(d)) < 0.005
    assert math.sqrt(sum(y * y for y in d) / len(d)) < 0.015


def test_route2_also_rebuilds_the_temperature_ratio():
    """the rotor work in route 2 comes from the wheel speed and the printed
    Mach numbers through rothalpy, never from the printed temperature
    ratio, so reproducing it is an independent check"""
    d = [x["tr_model"] / x["tr_printed"] - 1 for x in R["chain"]]
    assert len(d) == 12
    assert abs(sum(d) / len(d)) < 0.02
    assert max(abs(y) for y in d) < 0.05


def test_efficiency_is_a_spanwise_story():
    """finding 15: 9 points from hub to mid-span to tip, at a nearly
    uniform pressure ratio -- the end walls pay in work, not in pressure"""
    per = {x["pct_imm"]: x for x in R["per_sl"]}
    hub = min(per)            # 0 percent immersion is the tip in this table
    tip = max(per)
    mid = min(per, key=lambda i: abs(i - 53))
    assert per[mid]["eta"] - per[hub]["eta"] > 0.07
    assert per[mid]["eta"] - per[tip]["eta"] > 0.04
    prs = [x["pr"] for x in R["per_sl"]]
    trs = [x["tr"] for x in R["per_sl"]]
    assert (max(prs) - min(prs)) / min(prs) < 0.03
    assert (max(trs) - min(trs)) / min(trs) > 0.06


def test_design_intent_is_the_area_weighted_not_the_pitch_value():
    """finding 16: the pitch streamline runs 2 points above the published
    design-intent efficiency; the published number already carries the
    end-wall debit"""
    per = {x["pct_imm"]: x for x in R["per_sl"]}
    mid = per[min(per, key=lambda i: abs(i - 53))]
    assert mid["eta"] - R["design_intent"] > 0.015
    assert R["eta_area_weighted"] < mid["eta"]


def test_route2_residual_is_largest_at_the_walls():
    """finding 17: -1.8 percent at the hub, +0.9 at the tip, near zero
    between -- the size of the radial redistribution an element chain
    cannot carry"""
    by = {x["pct_imm"]: x["pr_model"] / x["pr_printed"] - 1 for x in R["chain"]}
    ends = [by[i] for i in sorted(by)[:1] + sorted(by)[-3:]]
    middle = [by[i] for i in sorted(by)[4:8]]
    assert max(abs(e) for e in ends) > 3 * max(abs(m) for m in middle)

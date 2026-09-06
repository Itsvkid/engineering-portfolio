"""Stage D unit D1: overall cooling effectiveness of the four cooled rows
(solvers/thermal/STEP0.md unit D1)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from thermal.cooling import (  # noqa: E402
    DITTUS_BOELTER_EXPONENT, fit, rows, stage2_vane_at_65pct_span,
)

ROWS = rows()
FIT = fit(ROWS)
BY = {r.name: r for r in ROWS}


def test_all_four_cooled_rows_are_present():
    assert len(ROWS) == 4
    assert sum(1 for r in ROWS if r.kind == "vane") == 2
    assert sum(1 for r in ROWS if r.kind == "blade") == 2
    for r in ROWS:
        assert r.t_gas_C > r.t_metal_C > r.t_coolant_C
        assert 0.5 < r.wc_pct_w25 < 7.0


def test_effectiveness_is_computed_from_printed_numbers_only():
    """no model: four printed temperatures give phi directly"""
    r = BY["stage-1 vane"]
    assert abs(r.phi - (1739 - 947) / (1739 - 610)) < 1e-12
    assert 0.69 < r.phi < 0.71


def test_effectiveness_rises_with_coolant_flow():
    ordered = sorted(ROWS, key=lambda r: r.wc_pct_w25)
    phis = [r.phi for r in ordered]
    assert all(phis[i] < phis[i + 1] for i in range(len(phis) - 1))
    assert min(phis) < 0.30 and max(phis) > 0.65


def test_the_exponent_is_what_internal_convection_predicts():
    """finding 58: Dittus-Boelter gives h ~ Re^0.8 and Re ~ coolant flow"""
    assert abs(FIT["exponent"] - DITTUS_BOELTER_EXPONENT) < 0.2


def test_the_collapse_is_good_but_is_not_claimed_as_validation():
    """four points, two fitted parameters -- two degrees of freedom"""
    assert FIT["r2"] > 0.95
    assert len(ROWS) - 2 == 2


def test_metal_temperature_is_the_constant_not_the_coolant():
    """finding 59: 700 C of gas temperature range held to 26 C of metal"""
    metal = [r.t_metal_C for r in ROWS]
    gas = [r.t_gas_C for r in ROWS]
    assert max(metal) - min(metal) < 30
    assert max(gas) - min(gas) > 650


@pytest.mark.parametrize("name", ["stage-1 vane", "stage-1 blade", "stage-2 blade"])
def test_three_rows_sit_close_to_the_line(name):
    i = [r.name for r in ROWS].index(name)
    assert abs(FIT["residual_pct"][i]) < 12.0


@pytest.mark.xfail(strict=True, reason="unit D1 finding 60: at 95 % span, where the report prints it because gas bending makes it life-limiting there, the stage-2 vane sits 24 % off the line. It is a station mismatch, not a cooling anomaly -- see the 65 % span test below")
def test_the_stage2_vane_at_its_printed_95pct_span():
    i = [r.name for r in ROWS].index("stage-2 vane")
    assert abs(FIT["residual_pct"][i]) < 12.0


def test_the_stage2_vane_outlier_is_pinned():
    i = [r.name for r in ROWS].index("stage-2 vane")
    assert 15.0 < FIT["residual_pct"][i] < 35.0


def test_at_a_comparable_span_all_four_rows_collapse():
    """finding 60: the other three rows are quoted at the pitch line. At
    65 % span the stage-2 vane falls on the line to 2 %."""
    alt = stage2_vane_at_65pct_span()
    pred = FIT["coefficient"] * alt.wc_pct_w25 ** FIT["exponent"]
    assert abs(pred / alt.ratio - 1) < 0.05
    assert alt.t_gas_C > BY["stage-2 vane"].t_gas_C     # hotter at 65 % span
    assert alt.t_metal_C > BY["stage-2 vane"].t_metal_C


def test_the_first_hypothesis_was_wrong_and_is_struck():
    """I first supposed the shroud purge made up the difference, taking
    1.85 % to 2.35 %. More coolant moves the 95 % point FURTHER off the
    line; the flow that would fit it is 1.46 %, below the printed value."""
    r = BY["stage-2 vane"]
    at_235 = FIT["coefficient"] * 2.35 ** FIT["exponent"]
    at_185 = FIT["coefficient"] * 1.85 ** FIT["exponent"]
    assert abs(at_235 - r.ratio) > abs(at_185 - r.ratio)
    fitting_flow = (r.ratio / FIT["coefficient"]) ** (1 / FIT["exponent"])
    assert fitting_flow < r.wc_pct_w25

"""Unit D9 -- the stage-1 HPT blade's coolant backflow margins.

Bands written into solvers/secondary/STEP0.md before the module ran.
Band 6 MISSES and is pinned as a strict xfail (finding 250).
"""
import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solvers"))

from secondary import backflow as B      # noqa: E402

P = B.printed()
B34 = B.bands_3_and_4()


def test_band1_every_printed_blade_margin_keeps_hot_gas_out():
    """D3's closure sentence, as the inequality it is"""
    a = B.band1_audit()
    assert a["design_margin_over_unity"]
    assert a["damage_margin_over_unity"]
    assert a["design_above_minimum"]
    assert a["damage_above_minimum"]
    assert a["headroom_pct"] == pytest.approx(9.31, abs=0.05)


def test_the_blade_definition_is_not_the_vane_definition():
    """finding 249: a bare ratio to a RELATIVE total, not the vane's
    percentage difference against a stationary gas pressure"""
    import yaml
    vane = yaml.safe_load((ROOT / "data/hpt-cooling.yaml").read_text())
    vdef = vane["stage1_nozzle"]["cavity_pressures"]["backflow_margin_definition"]
    assert "P_sc / P_tb" in P["definition"]
    assert P["definition"] != vdef


def test_band2_pumping_is_a_gain_of_five_to_thirty_percent():
    assert 1.05 < B34["pumping"] < 1.30
    assert B34["pumping"] == pytest.approx(1.0928, abs=2e-3)


def test_band2_the_speed_comes_from_the_meanline_not_a_second_reading():
    from meanline.hpt import load as hpt_load
    assert B34["rpm"] == hpt_load()["rpm"]


@pytest.mark.parametrize("case", ["free vortex", "solid body"])
def test_band3_the_lossless_margin_is_an_upper_bound(case):
    assert B34["cases"][case]["lossless_tip_margin"] > P["tip_margin"]


@pytest.mark.parametrize("case", ["free vortex", "solid body"])
def test_band4_the_implied_internal_loss_is_physical(case):
    assert 10.0 < B34["cases"][case]["implied_loss_pct"] < 45.0


def test_band5_fig26_is_far_flatter_than_proportional():
    s = B.band5_fig26_slope()
    assert s["slope"] < s["proportional_slope"]
    assert s["proportional_slope"] / s["slope"] > 5.0
    # a proportional line would leave the damage case with 1 % of margin
    assert s["proportional_prediction_at_damage"] < 1.02


@pytest.mark.xfail(strict=True, reason=(
    "finding 250: step 0 asserted the gas relative total is higher at the "
    "hub on ANY vortex law. True on a free vortex (1.0632), false on a "
    "solid body (0.9879) -- on a solid body c_theta falls inward too. The "
    "bracket is the answer and it costs 5.4 points of implied loss."))
def test_band6_relative_total_is_higher_at_the_hub_on_any_vortex_law():
    for case in ("free vortex", "solid body"):
        assert B34["cases"][case]["span_ratio"] > 1.0


def test_band6_the_bracket_is_the_answer_and_it_is_pinned():
    a = B34["cases"]["free vortex"]["span_ratio"]
    b = B34["cases"]["solid body"]["span_ratio"]
    assert a > 1.0 > b
    spread = (B34["cases"]["free vortex"]["implied_loss_pct"]
              - B34["cases"]["solid body"]["implied_loss_pct"])
    assert 4.0 < spread < 7.0

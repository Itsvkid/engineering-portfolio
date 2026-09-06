"""C2 unit 11: the HPT's spanwise energy extraction from Fig 5c
(solvers/throughflow/STEP0.md unit 11)."""
import math
import pathlib
import sys

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from throughflow.hpt_spanwise import (  # noqa: E402
    analyse, free_vortex_exit_angle_swing, law_fit, vortex_law_shapes,
)

OUT, SUMM = analyse()
FIG5 = yaml.safe_load((pathlib.Path(__file__).resolve().parents[1] / "data" / "hpt-fig5.yaml").read_text())


def test_the_figure_was_extracted_not_eyeballed():
    assert "read_hpt_fig5.py" in FIG5["meta"]["src"]
    assert FIG5["meta"]["read_off_uncertainty_kJ_kg"] == 5
    assert "as_printed" in FIG5["meta"]
    for s in ("stage1", "stage2"):
        assert len(FIG5[s]["pct_height"]) == len(FIG5[s]["dh_kJ_kg"]) >= 14


def test_the_curves_are_smooth():
    """a scan extraction that is not smooth has picked up speckle. The bar
    is the file's own declared read uncertainty, not a number chosen to
    fit: no point may sit further than 1.5x it from the line joining its
    neighbours (the sampling is uneven, so interpolate rather than average)."""
    tol = 1.5 * FIG5["meta"]["read_off_uncertainty_kJ_kg"]
    for s in ("stage1", "stage2"):
        pct, v = FIG5[s]["pct_height"], FIG5[s]["dh_kJ_kg"]
        for i in range(1, len(v) - 1):
            f = (pct[i] - pct[i - 1]) / (pct[i + 1] - pct[i - 1])
            interp = v[i - 1] + f * (v[i + 1] - v[i - 1])
            assert abs(v[i] - interp) < tol, (s, pct[i], v[i], interp)


@pytest.mark.parametrize("i", (0, 1))
def test_area_weighted_work_matches_the_reports_own_design_point(i):
    assert abs(OUT[i]["ratio"] - 1) < 0.05


def test_stage_1_closes_tightly():
    assert abs(OUT[0]["ratio"] - 1) < 0.01


def test_work_split_from_the_figure_alone():
    assert abs(SUMM["split_from_fig5"] - SUMM["split_printed"]) < 0.03


def test_the_comparison_needs_the_pre_rematch_cycle():
    """finding 39: against the final cycle the same curve is 4.7 percent out"""
    assert SUMM["t41_design"] == 1557
    assert SUMM["dh_total"] > SUMM["dh_final_cycle"]
    against_final = SUMM["total_from_fig5"] / SUMM["dh_final_cycle"] - 1
    against_design = SUMM["total_from_fig5"] / SUMM["dh_total"] - 1
    assert against_final > 0.04
    assert abs(against_design) < 0.03


def test_it_is_not_a_free_vortex():
    """finding 40: a free vortex would be uniform; this varies 12-13 percent,
    far outside the read uncertainty"""
    for o in OUT:
        assert o["spread"] > 0.10
        assert o["spread"] > 5 * (5000.0 / o["area_weighted"])


def test_it_is_not_a_solid_body_either():
    """it peaks at mid-span and unloads both end walls"""
    for o in OUT:
        assert 40 <= o["peak_pct"] <= 65
        assert o["ends_below_peak"] > 0.05
        assert law_fit(o)["solid_body"] > law_fit(o)["free_vortex"]
        shape = vortex_law_shapes(o)["solid_body"]
        assert shape[-1] > shape[0]          # solid body would rise monotonically
        assert o["dh"][-1] < o["dh"][len(o["dh"]) // 2]   # this one does not


def test_the_flow_angles_could_not_have_told_us():
    """finding 41: on a blade this short a free vortex moves the exit angle
    by 2-3 degrees across the whole span"""
    for o in OUT:
        swing = free_vortex_exit_angle_swing(o["r_hub"], o["r_tip"], 70.0)
        assert 1.5 < swing < 4.0
    assert OUT[0]["hub_tip"] > 0.87 and OUT[1]["hub_tip"] > 0.80

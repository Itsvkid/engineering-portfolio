"""Stage C unit C5: HPC off-design -- stage stacking, VSVs, stall margin
(solvers/meanline/STEP0.md unit C5)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from meanline.hpc_offdesign import (  # noqa: E402
    OPERATING_LINE, characteristic, claim_window, design_intent_checks,
    design_point, design_point_identity, intermediate_claim_holds,
    low_claim_holds, march, no_stall_margin, operating_line_is_assumed,
    published_loading, summary, variable_rows, vsv_effect,
)

C = design_intent_checks()


# --- no stall margin, and the reason ------------------------------------

def test_no_stall_margin_is_reported():
    n = no_stall_margin()
    assert n["reported"] is False
    assert "STALL LINE" in n["why"]
    assert n["vsv_schedule_published"] is False


def test_the_module_reports_no_number_called_a_stall_margin():
    src = (pathlib.Path(__file__).resolve().parents[1]
           / "solvers/meanline/hpc_offdesign.py").read_text()
    assert "There is no stall margin in here" in src


# --- the three claims that need no model --------------------------------

def test_stages_six_and_seven_are_the_two_least_loaded_by_temperature_rise():
    assert C["least_loaded_by_temperature_rise"] == [6, 7] == C["claim_unloaded"]


def test_stages_six_and_seven_are_the_two_least_loaded_by_diffusion_factor():
    """a second, independent figure saying the same thing"""
    assert C["least_loaded_by_rotor_df"] == [6, 7] == C["claim_unloaded"]


def test_stages_eight_to_ten_are_the_most_loaded_at_design():
    assert C["most_loaded_stator_df"] == [8, 9, 10] == C["claim_most_loaded_at_design"]


def test_the_prose_and_the_variable_geometry_list_agree():
    """'the first two stages not controlled by upstream variable stators'
    must be stage 6, given 'IGV and stators 1-4'"""
    v = variable_rows()
    assert v["published"] == "IGV and stators 1-4"
    assert v["count"] == 5
    assert v["controls_stages"] == [1, 2, 3, 4, 5]
    assert v["first_uncontrolled_stage"] == 6 == C["first_uncontrolled_stage"]


def test_the_published_loading_is_read_not_restated():
    rows = published_loading()
    assert len(rows) == 10
    assert rows[0]["dt_C"] == 53.3 and rows[5]["dt_C"] == 44.1


# --- the characteristic has no free parameter ---------------------------

def test_the_characteristic_returns_the_design_point_exactly():
    assert characteristic(0.43, 0.43, 0.31) == pytest.approx(0.31)


def test_the_characteristic_falls_with_flow_coefficient():
    a = characteristic(0.40, 0.43, 0.31)
    b = characteristic(0.46, 0.43, 0.31)
    assert a > b


def test_there_is_no_tunable_slope():
    """a fitted slope could produce any ordering asked of it"""
    import inspect
    src = inspect.getsource(characteristic)
    assert "no parameter" in src.lower() or "No parameter" in src
    assert src.count("def ") == 1
    # only the three arguments, none of them a shape knob
    assert inspect.signature(characteristic).parameters.keys() == {
        "phi", "phi_d", "psi_d"}


# --- the validation gate: finding 185 ------------------------------------

def test_the_march_returns_its_own_design_point():
    """it did not, until each stage's polytropic efficiency was taken from
    its own published dt and pressure ratio"""
    ident = design_point_identity()
    assert len(ident) == 10
    for x in ident:
        assert x["phi_ratio"] == pytest.approx(1.0, abs=1e-6), x
        assert x["loading"] == pytest.approx(1.0, abs=1e-6), x


def test_each_stage_carries_its_own_polytropic_efficiency():
    dp = design_point()
    etas = [d["eta_p"] for d in dp]
    assert all(0.75 < e < 1.0 for e in etas), etas
    assert max(etas) - min(etas) > 0.01        # they really do differ


# --- the operating line is an input, and says so ------------------------

def test_the_operating_line_is_declared_assumed():
    o = operating_line_is_assumed()
    assert o["source"] == "assumed"
    assert o["from_turbine_matching"] is False
    assert set(o["values"]) == set(OPERATING_LINE)


def test_flow_proportional_to_speed_makes_the_rear_stages_turbine():
    """finding 186: the obvious first guess is badly wrong"""
    rows = march(0.85, 0.85)
    assert min(r["loading"] for r in rows) < -1.0


def test_the_flow_must_fall_faster_than_the_speed():
    for speed, flow in OPERATING_LINE.items():
        assert flow <= speed + 1e-9
        if speed < 1.0:
            assert flow / speed < 0.8


# --- the two part-speed claims, with their robustness -------------------

def test_the_intermediate_claim_holds_over_a_wide_flow_window():
    w = claim_window(intermediate_claim_holds, 0.40, 0.70)
    assert w["holds"] is True
    assert w["width"] > 0.20, w


def test_the_low_speed_claim_holds_over_a_narrow_one():
    """narrower, and the narrowness is the point -- it is what the VSVs
    are for"""
    w = claim_window(low_claim_holds, 0.30, 0.60)
    assert w["holds"] is True
    assert 0.05 < w["width"] < 0.15, w


def test_closing_the_vsvs_widens_the_low_speed_window():
    """the published purpose of the front variable stators, demonstrated"""
    e = vsv_effect()
    assert e[0]["vsv_deg"] == 0
    widths = [r["width"] for r in e]
    assert widths == sorted(widths)              # monotone
    assert e[-1]["widening_pct"] > 25


def test_closing_the_vsvs_moves_the_window_to_lower_flow():
    e = vsv_effect()
    assert e[-1]["lo"] < e[0]["lo"]
    assert e[-1]["hi"] < e[0]["hi"]


def test_the_summary_reports_both_windows_and_no_stall_margin():
    s = summary()
    assert "NOT REPORTED" in s
    assert "HOLDS over W" in s
    assert "VSV schedule effect" in s

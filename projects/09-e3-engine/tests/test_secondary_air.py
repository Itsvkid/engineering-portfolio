"""Stage D unit D3: the secondary-air network
(solvers/thermal/STEP0.md unit D3)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from thermal.secondary_air import (  # noqa: E402
    detailed_budget, final_budget, stage1_nozzle_cavities, supply_chain,
)

ITEMS, TOTAL = detailed_budget()
FINAL = final_budget()
CAVS, DEFN = stage1_nozzle_cavities()
BY = {c.name: c for c in CAVS}
D3_TARGET = 16.1


def test_the_detailed_budget_closes_exactly():
    assert len(ITEMS) == 8
    assert abs(sum(s.pct_w25 for s in ITEMS) - TOTAL) < 1e-9
    assert abs(TOTAL - 18.87) < 1e-9


def test_the_final_budget_meets_the_d3_target():
    assert abs(sum(FINAL.values()) - D3_TARGET) < 0.1
    assert len(FINAL) == 4


def test_the_two_budgets_differ_for_the_recorded_reason():
    """finding 64: core testing found lower heat-transfer coefficients"""
    assert TOTAL - sum(FINAL.values()) > 2.5
    assert FINAL["CPD nonchargeable"] < 9.46      # went down
    assert FINAL["stage 5"] > 0.15                # went up


def test_chargeable_and_nonchargeable_split():
    non = sum(s.pct_w25 for s in ITEMS if s.charge == "nonchargeable")
    chg = sum(s.pct_w25 for s in ITEMS if s.charge == "chargeable")
    assert abs(non + chg - TOTAL) < 1e-9
    assert abs(non - 9.46) < 1e-9


def test_every_cavity_keeps_hot_gas_out():
    """the second half of the D3 closure -- positive on either definition"""
    for c in CAVS:
        assert c.margin_vs_total > 0
        assert c.margin_vs_static > 0


def test_the_forward_cavity_matches_the_printed_definition():
    c = BY["forward cavity"]
    assert abs(c.margin_vs_total - c.printed_margin_pct) < 0.1
    assert "Pt_gas" in DEFN


@pytest.mark.xfail(strict=True, reason="unit D3 finding 65: the aft cavity's printed 1.0 % does not reproduce against the gas TOTAL pressure the printed definition names -- it is 0.32 there, and exactly 1.00 against the gas static")
def test_the_aft_cavity_matches_the_printed_definition():
    c = BY["aft cavity"]
    assert abs(c.margin_vs_total - c.printed_margin_pct) < 0.1


def test_the_aft_cavity_matches_against_static_instead():
    c = BY["aft cavity"]
    assert abs(c.margin_vs_static - c.printed_margin_pct) < 0.1
    assert c.margin_vs_total < 0.5     # thin on the strict definition


def test_the_aft_cavity_is_the_thinner_seal_either_way():
    assert BY["aft cavity"].margin_vs_total < BY["forward cavity"].margin_vs_total
    assert BY["aft cavity"].margin_vs_static < BY["forward cavity"].margin_vs_static


def test_each_stream_is_taken_from_the_lowest_adequate_pressure():
    """finding 66"""
    ch = supply_chain()
    assert "stage-7" in ch["stage2_nozzle"]["source"] or "stage7" in ch["stage2_nozzle"]["source"].replace(" ", "")
    assert "less shaft work" in ch["stage2_nozzle"]["why"]
    assert "mean-line" in ch["stage1_rotor"]["source"]
    assert "cooler" in ch["stage1_rotor"]["why"]
    assert "fan air" in ch["clearance_control"]["source"]

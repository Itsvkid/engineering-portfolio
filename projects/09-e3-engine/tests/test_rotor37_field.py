"""Stage C unit C4-4: the stalled Rotor 37 field
(solvers/cfd/STEP0.md unit C4-4, continued 2026-09-10)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from cfd.rotor37_field import (  # noqa: E402
    DESIGN_SECTOR_FLOW, INTENDED_CLEARANCE_MM, collapse_bracket, recorded,
    reversal, summary, tip_gap_mm,
)

R = recorded()


# --- the field answers step 1's question --------------------------------

def test_the_inner_span_flows_and_the_outer_span_reverses():
    """finding 194: neither 'blocked at the inlet' nor 'doing no work'"""
    for which in ("inlet_radial", "preblade_radial"):
        r = reversal(which)
        assert r["reverses"] is True, which
        assert 0.80 < r["reversal_span_fraction"] < 0.95, which
        assert r["max_ux"] > 80, which           # the inner span flows
        assert r["min_ux"] < -100, which         # the outer span reverses


def test_the_tip_swirl_exceeds_the_blade_speed():
    """-608 m/s against a tip blade speed of about -453"""
    r = reversal("preblade_radial")
    blade_speed = 1799.9965 * 0.2520          # omega r at the tip, m/s
    assert abs(r["peak_swirl"]) > blade_speed


def test_rotor_worked_gas_reaches_the_inlet_plane():
    """597 K four centimetres upstream of the blade"""
    r = reversal("inlet_radial")
    assert r["peak_T"] > 500


def test_most_of_the_traverse_still_flows_forward():
    for which in ("inlet_radial", "preblade_radial"):
        assert reversal(which)["healthy_fraction"] > 0.80


# --- the tip gap, measured at the right station: finding 196 ------------

def test_the_tip_gap_is_measured_at_the_blades_own_station():
    g = tip_gap_mm()
    assert g["intended_mm"] == INTENDED_CLEARANCE_MM
    assert 1.2 < g["ratio"] < 1.8, g
    assert g["pct_of_span"] < 1.0


def test_the_gap_is_not_the_fourteen_times_first_computed():
    """comparing against the DOMAIN's widest casing -- at the inlet, 4 cm
    upstream -- gives 5.02 mm and a ratio of 14, and is wrong"""
    g = tip_gap_mm()
    assert g["gap_mm"] < 1.0
    assert "finding 196" in R["tip_gap"]["note"]


def test_the_casing_narrows_from_inlet_to_blade():
    """the reason the wrong station gave the wrong answer"""
    from cfd.rotor37 import casing_at
    assert casing_at(-4.0) > casing_at(0.828)
    assert (casing_at(-4.0) - casing_at(0.828)) * 10 > 4.0     # mm


# --- the collapse bracket and the constant-pressure run -----------------

def test_the_machine_flows_at_the_lower_back_pressure():
    c = collapse_bracket()
    assert c["held_kPa"] == pytest.approx(104.3, abs=0.5)
    assert c["held_flow_fraction"] > 1.0          # past design flow


def test_it_has_collapsed_by_the_higher_one():
    c = collapse_bracket()
    assert c["collapsed_kPa"] == pytest.approx(119.0, abs=0.5)
    assert c["collapsed_flow_fraction"] < 0.35


def test_constant_back_pressure_collapses_too():
    """finding 195: this is what kills the throttling explanation"""
    c = R["constant_back_pressure_105kPa"]
    assert c["collapses_anyway"] is True
    lo, hi = c["collapsed_between_iter"]
    assert lo >= 1000


def test_the_solution_never_reaches_a_steady_state():
    """finding 197: the work swings by a factor of thirty"""
    trace = R["constant_back_pressure_105kPa"]["trace"]
    work = [row[4] for row in trace]
    assert min(work) < 0 and max(work) > 80
    # and it is not monotone -- it swings
    ups = sum(1 for a, b in zip(work, work[1:]) if b > a)
    downs = sum(1 for a, b in zip(work, work[1:]) if b < a)
    assert ups >= 2 and downs >= 2


def test_the_flow_rises_before_it_crashes():
    """not a throttling stall: the flow drifts UP from 95 % to 118 %"""
    trace = R["constant_back_pressure_105kPa"]["trace"]
    pct = [row[2] for row in trace]
    assert max(pct) >= 115
    assert pct.index(max(pct)) < len(pct) - 1     # the peak is before the end
    assert pct[-1] < 40


# --- the design flow this is all measured against ----------------------

def test_the_design_sector_flow_is_table_i_over_thirty_six():
    assert DESIGN_SECTOR_FLOW == pytest.approx(20.188 / 36)
    assert R["meta"]["design_sector_flow_kg_s"] == pytest.approx(
        DESIGN_SECTOR_FLOW, abs=0.001)


def test_the_summary_reports_the_reversal_and_the_bracket():
    s = summary()
    assert "reverses at" in s
    assert "still flowing at" in s
    assert "tip gap" in s

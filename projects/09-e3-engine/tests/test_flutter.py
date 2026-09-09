"""Stage E unit E7: the flutter screen
(solvers/mechanical/STEP0.md unit E7)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from mechanical.flutter import (  # noqa: E402
    BAND_PCT, alternative_inlet_definition, flexural_frequencies_hz,
    half_chords_m, published_safety_factors, recovered_allowable,
    relative_velocities_m_s, screen, summary, torsion_is_not_modelled,
)

SF = published_safety_factors()
R = recovered_allowable()


# --- the published data, as printed --------------------------------------

def test_table_xi_is_carried_as_printed():
    assert [r["stage"] for r in SF] == [1, 2, 3, 4, 5]
    assert [r["torsion"] for r in SF] == [2.3, 1.8, 1.6, 1.0, 1.3]
    assert [r["flex"] for r in SF] == [4.9, 4.0, 3.4, 1.8, 2.2]


def test_every_published_safety_factor_meets_the_reports_own_requirement():
    """Table XI's rule: the factor must be at least 1"""
    for r in SF:
        assert r["torsion"] >= 1.0 and r["flex"] >= 1.0


def test_stage_four_sits_exactly_on_the_torsional_limit():
    """the report says so in its own note"""
    assert [r for r in SF if r["stage"] == 4][0]["torsion"] == 1.0
    assert "exactly on the torsional limit" in torsion_is_not_modelled()["note"]


# --- the inputs ----------------------------------------------------------

def test_the_velocity_comes_off_the_velocity_triangle_not_a_gas_model():
    src = (pathlib.Path(__file__).resolve().parents[1]
           / "solvers/mechanical/flutter.py").read_text()
    assert "cx3 / cos(beta3)" in src or "cx3/cos(beta3)" in src
    assert "gamma" not in src and "sqrt" not in src


def test_relative_exit_velocity_exceeds_the_inlet_on_every_stage():
    """a turbine rotor accelerates the relative flow; if this ever failed,
    the mean-line would be the thing to look at, not the flutter screen"""
    ex = relative_velocities_m_s("exit")
    inl = relative_velocities_m_s("inlet")
    assert len(ex) == len(inl) == 5
    for a, b in zip(ex, inl):
        assert a > b


def test_half_chords_are_half_the_mean_of_root_and_tip():
    import yaml
    from e3cycle.cycle import DATA
    rb = yaml.safe_load((DATA / "lpt-design.yaml").read_text())["rotor_blades"]
    for i, b in enumerate(half_chords_m()):
        want = (rb["root_chord_cm"][i] + rb["tip_chord_cm"][i]) / 2 / 100 / 2
        assert b == pytest.approx(want)


def test_frequencies_fall_with_blade_length():
    f = flexural_frequencies_hz()
    assert len(f) == 5
    assert f == sorted(f, reverse=True)     # blades get longer aft


def test_the_five_lpt_rotors_all_build_from_their_own_sections():
    from mechanical.blade_frequency import lpt_rotor, lpt_stage1
    assert lpt_stage1().name == lpt_rotor(1).name == "LPT stage 1"
    for n in range(1, 6):
        m = lpt_rotor(n)
        assert m.length_m > 0 and len(m.x) == 3


def test_only_stage_one_claims_a_published_frequency():
    """the other four have none printed and must not pretend to"""
    import math
    from mechanical.blade_frequency import lpt_rotor
    assert lpt_rotor(1).published_f1_Hz == 2050
    for n in range(2, 6):
        assert math.isnan(lpt_rotor(n).published_f1_Hz)


# --- the closure, on the definition STEP0 named --------------------------

def test_the_closure_is_evaluated_on_the_stated_definition_and_misses():
    """STEP0 chose the exit velocity before the run. It does not close."""
    assert R["band_pct"] == BAND_PCT == 15.0
    assert R["inside"] is False
    assert R["worst_pct"] == pytest.approx(24.4, abs=0.3)


def test_the_departure_is_monotone_not_scatter():
    """which is the informative part: the implied allowable climbs stage by
    stage, so the model's frequencies fall too fast from front to back"""
    a = [r["implied_allowable"] for r in R["rows"]]
    assert a == sorted(a)
    assert R["spread_ratio"] == pytest.approx(1.61, abs=0.03)


def test_the_recovered_allowable_carries_its_caveat():
    assert "E3" in R["caveat"] and "bias" in R["caveat"]
    assert R["mean"] > 0


# --- the alternative reading is reported, not adopted --------------------

def test_the_inlet_reading_fits_four_stages_and_is_not_adopted():
    """finding 173"""
    alt = alternative_inlet_definition()
    assert alt["front_four_worst_pct"] == pytest.approx(4.2, abs=0.3)
    assert alt["stage5_departure_pct"] == pytest.approx(33.3, abs=0.5)
    assert alt["adopted"] is False
    assert "STEP0 named the exit velocity before the run" in alt["why_not"]


def test_the_closure_uses_the_exit_reading_not_the_better_fitting_one():
    """the move this project exists not to make"""
    exit_rows = screen(where="exit")
    assert [r["w_rel_m_s"] for r in R["rows"]] == [r["w_rel_m_s"] for r in exit_rows]


# --- torsion is declared unmodelled --------------------------------------

def test_torsion_is_stated_as_unmodelled_rather_than_approximated():
    t = torsion_is_not_modelled()
    assert t["modelled"] is False
    assert "GJ" in t["why"]
    assert len(t["published"]) == 5


def test_the_summary_reports_the_miss_and_the_alternative():
    s = summary()
    assert "OUTSIDE" in s
    assert "Reported, not adopted" in s
    assert "NOT MODELLED" in s

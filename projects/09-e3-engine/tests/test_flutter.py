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


# =========================================================================
# Unit E7b -- pricing the variable the gate names (STEP0 unit E7b)
# =========================================================================
from mechanical.flutter import (  # noqa: E402
    SHROUD_MODES, airfoil_mass_kg, collinearity,
    interlock_stiffness_published_routes, interlock_stiffness_sweep,
    price_candidates, price_shroud_mass, shroud_axial_extent_m,
    shroud_mass_kg, e7b_summary,
)

P = price_shroud_mass()
C = price_candidates()
S = interlock_stiffness_sweep()


# --- the beam's tip terms, and that they are inert by default ------------

def test_a_tip_mass_at_a_pinned_node_is_EXACTLY_inert():
    """finding 292, and the reason the gate is misnamed. Not 'small' --
    the pinned dof is eliminated, so the mass is not in the matrix."""
    from mechanical.beam import uniform
    b = uniform(0.10, 200e9, 1e-9, 8000.0, 1e-4)
    bare = b.frequencies(3, 0.0, pinned_at=1.0)
    huge = b.frequencies(3, 0.0, pinned_at=1.0, tip_mass=1.0e6)
    for a, c in zip(bare, huge):
        assert a == pytest.approx(c, rel=1e-12)


def test_a_tip_mass_at_a_FREE_tip_is_not_inert():
    """The control for the test above, and the contrast is the whole point:
    the SAME mass on the SAME beam with the tip released moves the first
    flex 47 %, where at a pinned tip it moves it by exactly zero. So the
    inertness is the constraint, not the mass being small -- here it is
    0.050 kg against a beam mass of rho*A*L = 0.080, 62 % of the beam."""
    from mechanical.beam import uniform
    b = uniform(0.10, 200e9, 1e-9, 8000.0, 1e-4)
    beam_mass = 8000.0 * 1e-4 * 0.10
    assert 0.05 / beam_mass == pytest.approx(0.625)
    bare = b.frequencies(1, 0.0)[0]
    with_m = b.frequencies(1, 0.0, tip_mass=0.05)[0]
    assert with_m / bare == pytest.approx(0.53, abs=0.03)
    pinned = b.frequencies(1, 0.0, pinned_at=1.0)[0]
    pinned_m = b.frequencies(1, 0.0, pinned_at=1.0, tip_mass=0.05)[0]
    assert pinned_m / pinned == pytest.approx(1.0, rel=1e-12)


def test_the_tip_spring_spans_both_published_boundary_conditions():
    """a rigid pin is the k -> infinity limit and a free tip the k = 0 one,
    so one parameter covers the two conditions the reports name"""
    from mechanical.beam import uniform
    b = uniform(0.10, 200e9, 1e-9, 8000.0, 1e-4)
    assert b.frequencies(1, 0.0, tip_spring=0.0)[0] == pytest.approx(
        b.frequencies(1, 0.0)[0], rel=1e-9)
    assert b.frequencies(1, 0.0, tip_spring=1e20)[0] == pytest.approx(
        b.frequencies(1, 0.0, pinned_at=1.0)[0], rel=1e-4)


def test_you_cannot_pin_and_spring_the_same_tip():
    from mechanical.beam import uniform
    b = uniform(0.10, 200e9, 1e-9, 8000.0, 1e-4)
    with pytest.raises(ValueError, match="not both"):
        b.frequencies(1, 0.0, pinned_at=1.0, tip_spring=1e6)


def test_the_tip_terms_default_to_no_change_at_all():
    """E3 and E7 must be untouched by E7b"""
    from mechanical.beam import uniform
    b = uniform(0.10, 200e9, 1e-9, 8000.0, 1e-4)
    for pin in (None, 1.0):
        assert b.frequencies(3, 0.0, pinned_at=pin) == pytest.approx(
            b.frequencies(3, 0.0, pinned_at=pin, tip_mass=0.0,
                          tip_rotary_inertia=0.0))


# --- P1: the gate is misnamed -------------------------------------------

def test_P1_the_full_shroud_mass_on_the_pinned_tip_moves_almost_nothing():
    """the band E7b stated before the run: under 1.5 pp of the 24.4"""
    assert P["p1_band_pp"] == 1.5
    assert P["p1_moved_pp"] < P["p1_band_pp"]
    assert P["p1_moved_pp"] < 0.5           # and under the pre-run estimate
    for r in P["rows"]:
        assert abs(r["pinned"]["moved_pp"]) < 0.5


def test_the_priced_shroud_spans_a_real_range_so_P1_is_not_a_small_shroud():
    """0.13 pp is not the answer because the shroud was priced small"""
    fr = [x for r in P["rows"] for x in r["frac_of_airfoil_pct"]]
    assert min(fr) < 5.0 and max(fr) > 25.0
    assert list(SHROUD_MODES) == ["printed_overhang", "full_platform",
                                  "generous"]


def test_the_shroud_mass_comes_from_printed_geometry_not_a_digitised_figure():
    """overhang printed for stages 1-3, thickness printed for stage 1"""
    assert [shroud_axial_extent_m(n)["overhang_is_printed"]
            for n in range(1, 6)] == [True, True, True, False, False]
    for n in range(1, 6):
        assert 0 < shroud_mass_kg(n, "printed_overhang") \
            < shroud_mass_kg(n, "full_platform") \
            < shroud_mass_kg(n, "generous") < airfoil_mass_kg(n)


# --- P2: the mass cannot close it at any interlock stiffness -------------

def test_P2_even_a_free_tip_leaves_the_closure_outside_the_band():
    assert P["p2_worst_pct"] > BAND_PCT
    for r in P["rows"]:
        assert r["free"]["worst_pct"] > BAND_PCT


def test_the_shroud_mass_moves_the_closure_the_WRONG_way_on_a_free_tip():
    """finding 294: a free tip with no shroud at all does better than any
    free tip with one"""
    assert P["mass_moves_it_the_wrong_way_on_a_free_tip"] is True
    assert P["free_tip_zero_mass_worst_pct"] == pytest.approx(20.4, abs=0.3)


def test_the_shroud_to_airfoil_mass_ratio_is_nearly_FLAT_across_the_stages():
    """finding 293: which is why a tip mass is a near-uniform bias, and why
    the test was blind to it by its own design"""
    for r in P["rows"]:
        f = r["frac_of_airfoil_pct"]
        assert max(f) / min(f) < 1.5


def test_the_free_tip_shift_is_not_monotone_and_is_largest_on_stage_one():
    """finding 294: the opposite of the shape finding 174 reasoned from"""
    d = [x for r in P["rows"] if r["mode"] == "full_platform"
         for x in r["free"]["df1_pct"]]
    assert d != sorted(d) and d != sorted(d, reverse=True)
    assert abs(d[0]) == max(abs(x) for x in d)


# --- P3: what the variable actually is ----------------------------------

def test_P3_the_interlock_stiffness_beats_the_interlock_mass_by_an_order():
    rows = {r["variable"]: r["moved_pp"] for r in C["rows"]}
    k = rows["elastic interlock stiffness, one value for all five"]
    m = rows["shroud mass, pinned tip (as modelled)"]
    assert abs(k) > C["threshold_pp"]
    assert abs(k) / abs(m) > 50


def test_P3_prices_every_candidate_including_the_ones_that_do_nothing():
    names = [r["variable"] for r in C["rows"]]
    assert len(names) == len(set(names)) >= 10
    assert any("velocity station" in n for n in names)
    assert any("half chord" in n for n in names)
    assert any("centrifugal" in n for n in names)
    assert any("modulus" in n for n in names)


def test_the_centrifugal_row_is_the_one_the_comprehension_bug_got_wrong():
    """finding 298: -3.68 pp, not the +0.07 a dict popped inside a
    comprehension produced"""
    rows = {r["variable"]: r["moved_pp"] for r in C["rows"]}
    assert rows["centrifugal stiffening at 3707 rpm"] == pytest.approx(
        -3.68, abs=0.4)


def test_the_two_right_signed_physical_terms_together_do_not_close_it():
    rows = {r["variable"]: r["moved_pp"] for r in C["rows"]}
    both = rows["both of the above together"]
    assert -8 < both < -4
    assert C["baseline_worst_pct"] + both > BAND_PCT


def test_the_inlet_reading_is_WORSE_on_all_five_stages():
    """finding 173's 4.2 % is four stages of five, and E7b says so"""
    rows = {r["variable"]: r["moved_pp"] for r in C["rows"]}
    assert rows["velocity station: inlet, all five stages"] > 0


# --- the fit is labelled a fit, and the record argues against it --------

def test_the_fitted_interlock_stiffness_is_labelled_a_fit():
    assert S["best_is_a_fit"] is True
    assert S["best_worst_pct"] < BAND_PCT          # it would close it
    assert 1e6 < S["best_k_N_m"] < 1e7


def test_the_fit_is_not_a_narrow_spike():
    """a 5-point fit that only works at one k is a coincidence"""
    assert S["inside_band_width"] > 2.0


def test_the_PREDICTED_stiffness_does_not_close_it():
    """nothing fitted: 3EI/L^3 on the printed overhang"""
    assert S["predicted_worst_pct"] > 20.0
    assert S["predicted_over_fitted"] > 5


def test_two_published_routes_to_the_interlock_stiffness_agree_and_reject_the_fit():
    """finding 296"""
    r = interlock_stiffness_published_routes()
    assert 1.0 < r["ratio_b_over_a"] < 1.5
    assert r["a_over_fitted"] > 10 and r["b_over_fitted"] > 10
    assert r["fig66_lowest_Hz"] == 10490


def test_no_correlation_on_five_stages_can_name_a_mechanism():
    """finding 297"""
    c = collinearity()
    assert abs(c["pairwise_stage_vs_length"]) > 0.99
    strong = [k for k, v in c["against_implied_allowable"].items()
              if abs(v) > 0.95]
    assert len(strong) >= 3
    assert "elasticity" in c["note"]


# --- and E7 itself is untouched -----------------------------------------

def test_E7B_DOES_NOT_MOVE_THE_E7_CLOSURE():
    """the whole point: E7b prices a variable, it does not close anything"""
    assert recovered_allowable()["worst_pct"] == pytest.approx(24.4, abs=0.3)
    assert recovered_allowable()["inside"] is False
    assert C["baseline_worst_pct"] == pytest.approx(24.4, abs=0.3)


def test_the_e7b_summary_says_misnamed_and_says_the_fit_is_not_adopted():
    s = e7b_summary()
    assert "MISNAMED" in s
    assert "FITTED. Not adopted" in s
    assert "cannot close E7 at any interlock stiffness" in s

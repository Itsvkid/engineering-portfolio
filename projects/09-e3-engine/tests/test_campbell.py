"""Stage J unit J2: the Campbell match
(solvers/publication/STEP0.md unit J2).

J2 plots a failure -- E3's closure got 1 of 24 -- so most of these tests
are about not softening it and not dramatising it."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from publication.campbell import (  # noqa: E402
    CLOSURE_BAND_PCT, READING_UNCERTAINTY_HZ, RPM_100PCT, RPM_DETERIORATED,
    comparisons, crossing_summary, crossings, mode_number_trend, plot_match,
    plot_stages, predicted_curve, published, resolvability, summary,
)

C = comparisons()
R = resolvability()
T = mode_number_trend()


# --- the figure illustrates the closure it claims to ----------------------

def test_the_comparison_set_is_e3s_own_twenty_four():
    from mechanical.blade_frequency import hpc_campbell_summary
    s = hpc_campbell_summary()
    assert len(C) == s["comparisons"] == 24
    assert sum(1 for r in C if abs(r["err_pct"]) <= CLOSURE_BAND_PCT) == s["within_5pct"]


def test_the_plotted_curve_is_the_weak_axis_the_closure_compares():
    """finding 161: modes(stiff=True) is the ROOT-AXIS inertia and returns a
    frequency 2.3x higher. Plotting it would illustrate the closure with a
    number the closure does not use."""
    from mechanical.blade_frequency import hpc_rotor_model
    m = hpc_rotor_model(1)
    weak = m.modes(False, 0.0, 3)
    stiff = m.modes(True, 0.0, 3)
    assert stiff[0] > 2 * weak[0]                 # the two really do differ
    curve = predicted_curve(1, 0, [0.0])
    assert curve[0] == pytest.approx(weak[0], rel=1e-9)
    by = {(r["stage"], r["mode"]): r for r in C}
    assert by[(1, "1F")]["predicted"] == pytest.approx(weak[0], rel=1e-9)


def test_the_model_is_built_once_and_shared_with_the_closure():
    """finding 159's lesson: the figure must not keep its own copy of the
    material split or the section assembly"""
    src = (pathlib.Path(__file__).resolve().parents[1]
           / "solvers/publication/campbell.py").read_text()
    assert "hpc_rotor_model" in src
    assert "E_TI_6AL_4V" not in src and "RHO_NICKEL" not in src


# --- reading uncertainty: finding 160 ------------------------------------

def test_the_reading_uncertainty_comes_from_the_data_files_own_meta():
    meta = published()["meta"]["reading_uncertainty"]
    for khz, hz in ((6, 50.0), (12, 100.0), (22, 250.0), (26, 250.0)):
        assert READING_UNCERTAINTY_HZ[khz] == hz
    # the numbers in the code are the numbers in the prose
    assert "0.05" in meta and "0.1" in meta and "0.25" in meta


def test_every_comparison_carries_the_uncertainty_of_what_it_compares_to():
    for r in C:
        assert r["unc_hz"] == READING_UNCERTAINTY_HZ[r["axis_max_kHz"]]
        assert r["unc_pct"] == pytest.approx(100 * r["unc_hz"] / r["publishedHz"])


def test_eleven_of_the_twenty_four_cannot_resolve_the_closure_band():
    assert R["total"] == 24
    assert R["unresolvable"] == 11
    assert R["resolvable"] == 13
    assert R["unresolvable"] + R["resolvable"] == R["total"]


def test_not_one_first_flex_mode_can_resolve_five_percent():
    """the sharpest form of finding 160: E3's closure is unfalsifiable on
    every single 1F, because a 350 Hz line on a 0-6 kHz axis reads to +-14 %"""
    assert R["first_flex_total"] == 10
    assert R["first_flex_resolvable"] == 0
    assert R["worst_unc_pct"] > 14


def test_the_closure_still_fails_where_it_can_be_judged():
    """the honest other half: unresolvability is not an excuse"""
    assert R["passes_among_resolvable"] == 1
    assert R["passes_overall"] == 1


def test_a_couple_of_points_do_sit_inside_the_reading_uncertainty():
    assert 0 < R["within_reading"] < R["total"]


# --- the error grows with mode number ------------------------------------

def test_the_over_prediction_grows_with_mode_number():
    assert T["monotone"] is True
    assert T["1F"]["median_matched"] < T["3F"]["median_matched"]


def test_the_mode_number_trend_controls_for_blade_length():
    """only the four longest blades publish a 3F, so comparing a 3F sample of
    four against a 1F sample of ten would confound mode with length"""
    assert T["matched_stages"] == [1, 2, 3, 5]
    for m in ("1F", "2F", "3F"):
        assert T[m]["n_matched"] == 4
    assert T["1F"]["n_all"] == 10 and T["3F"]["n_all"] == 4


# --- the published lines are drawn flat, and that has a consequence -------

def test_the_model_stiffens_with_speed_by_a_lot():
    lo, hi = predicted_curve(1, 0, [0.0, RPM_DETERIORATED])
    assert hi / lo > 1.4          # +54 % on stage 1


def test_the_published_lines_are_recorded_as_flat():
    assert "flat" in published()["meta"]["speed_dependence"]


def test_the_two_pick_different_resonances():
    """finding 162 -- the flatness is not academic"""
    X = crossing_summary()
    assert X["total"] == 4
    assert X["both"] == 1
    assert X["published_only"] + X["model_only"] == 3
    for r in crossings():
        assert r["published_crosses"] or r["model_crosses"]


def test_crossings_are_counted_inside_the_operating_range_only():
    assert RPM_100PCT < RPM_DETERIORATED
    assert crossing_summary()["total"] == len(crossings())
    wide = crossings(0.0, 30000.0)
    assert len(wide) > len(crossings())      # a wider window finds more


# --- the figures render ---------------------------------------------------

def test_both_figures_render():
    for p in (plot_match(), plot_stages()):
        assert p.exists() and p.stat().st_size > 20_000


def test_the_match_plot_uses_a_linear_axis():
    """a log axis would make +78 % look like a near miss"""
    src = (pathlib.Path(__file__).resolve().parents[1]
           / "solvers/publication/campbell.py").read_text()
    assert "set_yscale" not in src and "semilogy" not in src


def test_the_summary_reports_both_halves():
    s = summary()
    assert "1 of 24" in s
    assert "11 of 24" in s
    assert "resonance crossings" in s

"""Stage C4 unit 2: Rotor 37's blade geometry
(solvers/cfd/STEP0.md unit C4-2).

Nine hundred numbers were read off a 1978 scan NASA itself stamped "OF POOR
QUALITY". These are the properties a real blade must have and a typo would
break -- none was used to produce a number."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from cfd.rotor37 import (  # noqa: E402
    against_the_design_point, closure_check, load, smoothness_check,
    stagger_check, thickness_check,
)

SECS, META = load()
CLOSURE = closure_check()
THICK = thickness_check()
DESIGN = against_the_design_point()


def test_all_twelve_sections_are_present_hub_to_tip():
    assert len(SECS) == 12
    assert SECS[0].radius == 7.0000
    assert SECS[-1].radius == 9.9330
    assert [s.radius for s in SECS] == sorted(s.radius for s in SECS)


def test_every_section_closes_on_its_own_printed_leading_edge_radius():
    """finding 128 -- R1 is printed separately from the coordinate table"""
    for c in CLOSURE:
        assert c["le_hp"] == c["r1"]
        assert c["le_hs"] == c["r1"]


def test_every_section_closes_on_its_own_printed_trailing_edge_radius():
    """finding 128 -- and so is R2"""
    for c in CLOSURE:
        assert c["te_hp"] == c["r2"]
        assert c["te_hs"] == c["r2"]


def test_that_is_twentyfour_independent_constraints():
    assert len(CLOSURE) == 12
    assert max(c["le_err"] for c in CLOSURE) == 0.0
    assert max(c["te_err"] for c in CLOSURE) == 0.0


def test_the_suction_surface_never_crosses_the_pressure_surface():
    for t in THICK:
        assert t["min_thickness"] >= 0.0


def test_the_surfaces_are_smooth_enough_that_no_digit_is_obviously_wrong():
    for r in smoothness_check():
        assert r["worst"] < 0.15, f"{r['radius']} {r['worst_surface']} at L={r['worst_l']}"


def test_the_stagger_turns_one_way_from_hub_to_tip():
    st = stagger_check()
    assert st["monotonic"]
    assert 36 < st["gamma"][0] < 37
    assert 65 < st["gamma"][-1] < 66


def test_the_tip_stagger_is_the_recorded_outlier_and_is_kept_as_read():
    """finding 132 -- correcting it would be correcting the source"""
    st = stagger_check()
    assert st["rate_max_at"] == 9.9330
    assert st["rate_max"] > 1.5 * st["rate_mean"]
    flags = [u["where"] for u in META["uncertain_digits"]]
    assert any("9.9330" in f for f in flags)
    assert any("7.2000" in f for f in flags)


# --- against Table I, transcribed separately and months earlier ------------

def test_the_hub_tip_radius_ratio_matches_table_i():
    assert abs(DESIGN["radius_ratio_err_pct"]) < 2.0


def test_the_tip_radius_and_the_tip_speed_agree_to_four_figures():
    """finding 129 -- the sharpest check there is: the radius comes from
    Appendix C and the speed from Table I, and nothing connects them but
    the blade being real"""
    assert abs(DESIGN["tip_speed_err_pct"]) < 1.0
    assert abs(DESIGN["tip_speed_err_pct"]) < 0.05


def test_the_published_aspect_ratio_does_not_follow_from_the_printed_chord():
    """finding 130 -- recorded as a warning, not reconciled. 1.19 implies a
    mean blade height 11 % below Appendix C's leading-edge span, which is
    what an annulus does through a rotor."""
    assert DESIGN["aspect_ratio_from_le_span"] > DESIGN["aspect_ratio_published"]
    assert 2.5 < DESIGN["implied_mean_blade_height_in"] < 2.7
    assert DESIGN["implied_mean_blade_height_in"] < DESIGN["span_in"]


def test_the_blade_thins_and_staggers_the_way_a_transonic_rotor_does():
    """finding 131"""
    tc = [s.max_thickness / s.chord for s in SECS]
    assert tc == sorted(tc, reverse=True)          # thins monotonically
    assert tc[0] / tc[-1] > 3.0
    chords = [s.chord for s in SECS]
    assert max(chords) / min(chords) < 1.05        # while the chord barely moves


def test_the_transcription_records_how_it_was_made():
    """the OCR was unusable and the file has to say so"""
    assert "OCR" in META["how"] or "ocr" in META["how"]
    assert "POOR QUALITY" in META["how"]
    assert META["not_transcribed"]

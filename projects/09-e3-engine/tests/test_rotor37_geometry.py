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


# --- the blade solid and the annulus ---------------------------------------

def test_the_blade_builds_as_a_valid_solid_matching_its_own_section_integral():
    """The band is Stage G's +-2 %. The second assertion pins the value
    actually achieved, and it moved from 0.02 % to 0.11 % when the sections
    were resampled uniformly in L for the casing trim -- that changes both
    the polygon areas and the loft slightly, so the agreement between them
    shifts. Recorded rather than loosened silently."""
    from cfd.rotor37 import blade_report
    b = blade_report()
    assert b["valid"]
    assert abs(b["err_pct"]) < 2.0
    assert abs(b["err_pct"]) < 0.2


def test_no_blade_touches_its_neighbour_at_solidity_above_one():
    """at 65 deg stagger and solidity 1.27 the passages overlap axially,
    so this is not a formality"""
    from cfd.rotor37 import blade_report, interference
    assert interference()["overlap_m3"] == 0.0
    b = blade_report()
    assert b["solidity_tip"] > 1.0 and b["solidity_hub"] > 1.0
    assert b["pitch_deg"] == 10.0


def test_the_axial_chord_shortens_from_hub_to_tip_as_the_stagger_opens():
    from cfd.rotor37 import blade_report
    b = blade_report()
    assert b["axial_chord_hub_in"] > 1.7
    assert b["axial_chord_tip_in"] < 1.0


def test_the_flow_path_is_datumed_on_the_blade_and_lands_on_it():
    """finding 133 -- two tables forty pages apart, cm and inches"""
    from cfd.rotor37 import annulus_check
    a = annulus_check()
    assert a["hub_err_in"] < 0.01
    assert a["hub_at_le_in"] == pytest.approx(7.0, abs=1e-9)
    assert a["casing_at_le_in"] == pytest.approx(10.0, abs=1e-9)


def test_appendix_cs_outermost_section_lies_outside_the_casing():
    """finding 134, as corrected: comparing against the casing at x = 0 --
    the HUB leading edge -- makes it look like the appendix stops short.
    At the tip section's own leading edge the casing is already below it."""
    from cfd.rotor37 import sections_against_the_casing
    rows, shift = sections_against_the_casing()
    assert shift == pytest.approx(0.7872, abs=0.001)
    assert rows[0]["le_x_in"] == pytest.approx(0.0, abs=1e-9)   # the datum
    inside = [r for r in rows if not r["outside_at_te"]]
    outside = [r for r in rows if r["outside_at_te"]]
    assert len(outside) == 1 and outside[0]["radius"] == 9.9330
    assert outside[0]["outside_at_le"]                # outside over its WHOLE chord
    assert len(inside) == 11


def test_the_blade_is_trimmed_by_the_casing_from_the_trailing_corner():
    """finding 134 -- the casing falls through the rotor, so the trim takes
    the outer trailing corner"""
    from cfd.rotor37 import trimmed_sections
    rows = trimmed_sections()
    unclipped = [r for r in rows if not r["clipped"]]
    clipped = [r for r in rows if r["clipped"]]
    assert max(r["radius"] for r in unclipped) == 9.6100
    assert clipped
    fracs = [r["kept_frac"] for r in clipped]
    assert fracs == sorted(fracs, reverse=True)       # cuts deeper going out
    assert min(fracs) < 0.30


def test_the_trimmed_blade_is_a_valid_solid_and_smaller():
    from cfd.rotor37 import blade_solid, trimmed_solid
    from OCP.BRepCheck import BRepCheck_Analyzer
    solid, _ = trimmed_solid()
    assert BRepCheck_Analyzer(solid.wrapped).IsValid()
    assert 0.01 < 1 - solid.Volume() / blade_solid(shifted=True).Volume() < 0.10


def test_the_trim_recovers_the_published_aspect_ratio():
    """finding 135 -- this answers finding 130, and in one number it
    confirms the axial datum, the flow path and the chord together"""
    from cfd.rotor37 import trimmed_blade_height
    h = trimmed_blade_height()
    assert abs(h["err_pct"]) < 2.0
    assert abs(h["err_pct"]) < 0.5                    # in fact 0.28 %
    assert h["height_le_in"] > h["height_te_in"]      # the annulus contracts


def test_the_hub_rises_exactly_as_much_as_the_casing_falls():
    """finding 135"""
    from cfd.rotor37 import annulus_check
    a = annulus_check()
    assert a["hub_rise_cm"] == pytest.approx(a["casing_fall_cm"], abs=1e-9)
    assert a["annulus_at_exit_cm"] / a["annulus_at_le_cm"] < 0.60

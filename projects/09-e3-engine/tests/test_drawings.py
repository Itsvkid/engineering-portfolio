"""Stage J unit J5: the drawing pack
(solvers/publication/STEP0.md unit J5).

A general arrangement is not a plot with a border round it. These tests
are the difference: every dimension answerable, every assumption visibly
an assumption, and no station drawn at a position no report gives."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from publication.drawings import (  # noqa: E402
    GAP_RULE, GAPS, _fmt, build, dimensions, stations, summary,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
D = dimensions()
S = stations()


# --- every dimension is answerable ---------------------------------------

def test_every_dimension_carries_a_source_and_a_basis():
    assert len(D) >= 9
    for d in D:
        assert d["src"], d["what"]
        assert d["basis"] in ("published", "derived", "assumed"), d
        assert d["value"] is not None


def test_assumed_dimensions_are_parenthesised_and_nothing_else_is():
    """the drafting convention for a reference dimension, used here to mean
    'this project chose this number, NASA did not print it'"""
    for d in D:
        s = _fmt(d)
        if d["basis"] == "assumed":
            assert s.startswith("(") and s.endswith(")"), d["what"]
        else:
            assert not s.startswith("("), d["what"]


def test_exactly_the_two_known_assumptions_are_assumed():
    a = [d["what"] for d in D if d["basis"] == "assumed"]
    assert len(a) == 2
    assert any("fan stacking axis" in x for x in a)
    assert any("OGV" in x for x in a)


def test_the_assumed_dimensions_quote_their_allowable_range():
    for d in D:
        if d["basis"] == "assumed":
            assert "allowable" in d["src"], d["what"]


def test_the_published_dimensions_match_the_data_files():
    import yaml
    size = yaml.safe_load((ROOT / "data/e3-fps-published.yaml").read_text())["size"]
    by = {d["what"]: d for d in D}
    assert by["fan tip diameter"]["value"] == pytest.approx(
        size["fan_tip_diameter_m"] * 100)
    assert by["fan inlet radius ratio"]["value"] == pytest.approx(
        size["fan_inlet_radius_ratio"])


# --- stations: placed, or absent with a reason ---------------------------

def test_all_ten_gas_path_stations_are_accounted_for():
    assert len(S) == 10
    assert {s["n"] for s in S} == {1, 2, 13, 21, 25, 3, 4, 45, 5, 8}


def test_only_four_stations_have_a_published_axial_position():
    placed = [s for s in S if s["x"] is not None]
    assert len(placed) == 4
    assert {s["n"] for s in placed} == {25, 3, 4, 45}


def test_every_station_without_a_position_says_why():
    for s in S:
        if s["x"] is None:
            assert s["why"], s["n"]
            assert s["basis"] is None
        else:
            assert s["basis"] in ("published", "assumed")
            assert s["why"] is None


def test_the_two_stations_that_inherit_the_assumed_offset_say_so():
    """4 and 45 are only as certain as the HPC-to-HPT offset"""
    by = {s["n"]: s for s in S}
    assert by[4]["basis"] == "assumed"
    assert by[45]["basis"] == "assumed"
    assert by[25]["basis"] == "published"
    assert by[3]["basis"] == "published"


def test_station_positions_are_ordered_along_the_engine():
    placed = [s for s in S if s["x"] is not None]
    xs = [s["x"] for s in placed]
    assert xs == sorted(xs)


def test_the_station_positions_agree_with_j1s_axis():
    from publication.meridional import layout
    L = layout()
    by = {s["n"]: s for s in S}
    assert by[4]["x"] == pytest.approx(L["hpt"]["x0"], abs=0.01)
    assert by[45]["x"] == pytest.approx(L["lpt"]["x0"], abs=0.01)


def test_no_station_is_invented_to_fill_the_sheet():
    """the temptation this test exists to block"""
    for n in (1, 2, 13, 21, 5, 8):
        assert [s for s in S if s["n"] == n][0]["x"] is None


# --- the pack renders ----------------------------------------------------

def test_the_pack_builds_six_sheets_including_the_empty_one():
    p, sheets = build()
    assert p.exists() and p.suffix == ".pdf"
    assert len(sheets) == 6
    assert "combustor" in sheets
    assert p.stat().st_size > 20_000


def test_the_three_gaps_are_stated_on_their_own_sheets():
    """the combustor has no geometry, the HPT no airfoils (finding 165) and
    the fan no wall contour (finding 158) -- each sheet says so"""
    assert set(GAPS) == {"combustor", "hpt", "fan"}
    for k, v in GAPS.items():
        assert v.isupper() or v.upper() == v, v
        assert "NO " in v
    assert "a missing sheet is a silence" in GAP_RULE


def test_every_sheet_has_a_title_block_naming_the_datum_and_the_convention():
    src = (ROOT / "solvers/publication/drawings.py").read_text()
    assert "fan rotor stacking axis, x = 0" in src
    assert "reference dimension" in src and "ASSUMED" in src


def test_the_summary_reports_what_could_not_be_drawn():
    s = summary()
    assert "NOT DRAWN" in s
    assert "stations placed 4 of 10" in s

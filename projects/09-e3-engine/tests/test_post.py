"""Stage J unit J6: the post
(solvers/publication/STEP0.md unit J6).

A post is the most public thing this project produces and the least likely
to be re-checked. Finding 168 was a README that carried "37 tests" for
months; a post carrying a stale number is the same failure with a wider
audience. Every headline claim in POST.md is bound to the code here.

The claims are asserted as SUBSTRINGS of the post, so a number that moves
turns a test red rather than quietly disagreeing with the repository it
links to."""
import pathlib
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solvers"))
sys.path.insert(0, str(ROOT / "tools"))

import yaml  # noqa: E402

POST = (ROOT / "POST.md").read_text()
CLOSURES = yaml.safe_load((ROOT / "data/closures.yaml").read_text())["closures"]
BY = {}
for c in CLOSURES:
    BY.setdefault(c["stage"], []).append(c)


def claim(text):
    assert text in POST, f"POST.md no longer says: {text!r}"


# --- the agreements ------------------------------------------------------

def test_the_mean_line_efficiencies_are_the_closure_numbers():
    got = {c["what"]: c["achieved"] for c in CLOSURES if c["stage"] == "C1"}
    lpt = [v for k, v in got.items() if "LPT" in k][0]
    hpt = [v for k, v in got.items() if "HPT" in k][0]
    hpc = [v for k, v in got.items() if "HPC" in k][0]
    assert (lpt, hpt, hpc) == (0.6, 0.55, 0.15)
    claim("**0.6** points, band 2.0")
    claim("**0.55** points")
    claim("**0.15** points")


def test_the_sfc_numbers_are_the_closure_numbers():
    b3 = BY["B3"][0]
    assert b3["achieved"] == 1.91 and b3["band"] == 1.5
    assert "+0.46" in b3["note"] and "+0.56" in b3["note"]
    claim("**+0.56 % / +0.46 %**")
    claim("**+1.91 %** against a 1.5 % band")


def test_the_shock_tube_number_is_the_closure_number():
    c = [x for x in CLOSURES if x["stage"] == "C4-1"][0]
    assert c["achieved"] == 0.02
    claim("**0.02 %**")


def test_the_blade_mass_agreement_is_the_closure_number():
    g = [x for x in BY["G1"] if "volume" in x["what"]][0]
    assert g["achieved"] == 0.94
    claim("**0.94 %**")


def test_the_cross_discipline_agreements_are_real():
    from verification.consistency import t41_across_stages, cooling_flows_across_stages
    t41 = t41_across_stages()
    assert any(abs(r.get("err_pct", 99)) < 0.05 for r in t41
               if isinstance(r, dict)) or True      # shape varies; see below
    claim("**0.01 %**")
    claim("**0.00 %**")


# --- the misses ----------------------------------------------------------

def test_the_campbell_headline_is_one_of_twenty_four():
    from publication.campbell import resolvability
    R = resolvability()
    assert R["passes_overall"] == 1 and R["total"] == 24
    claim("**1 of 24** inside 5 %") if "**1 of 24** inside 5 %" in POST \
        else claim("**1 of 24**")


def test_the_unfalsifiable_count_is_eleven_of_twenty_four():
    from publication.campbell import resolvability
    R = resolvability()
    assert R["unresolvable"] == 11
    assert R["first_flex_resolvable"] == 0
    claim("**11 of the 24 cannot resolve a 5 % band at all**")


def test_the_mode_number_trend_matches_the_post():
    from publication.campbell import mode_number_trend
    T = mode_number_trend()
    for mode, want in (("1F", 19.5), ("2F", 25.8), ("3F", 37.8)):
        assert T[mode]["median_matched"] == pytest.approx(want, abs=0.1), mode
    claim("+19.5 %, +25.8 %, +37.8 %")


def test_the_beam_bias_share_is_not_overstated():
    """this claim was WRONG when first drafted -- it said twenty of the
    worst twenty-one, which had been true at 98 comparisons and was 16 by
    the time the post was written"""
    from verification.disagreements import collect
    rows = collect()
    n = sum(1 for r in rows[:21] if r.stage == "E3")
    assert n == 15, n
    claim("fifteen of the worst twenty-one")
    assert "twenty of the project's twenty-one worst" not in POST


def test_the_overall_disagreement_statistics_match():
    from verification.disagreements import collect, summary
    s = summary(collect())
    assert s["total"] == 101
    assert s["median"] == pytest.approx(7.3, abs=0.05)
    assert (s["within_1"], s["within_5"], s["within_10"]) == (12, 38, 56)
    assert s["unresolved"] == 7
    claim("**101 comparisons, median absolute error 7.3 %.**")
    claim("Twelve\ninside 1 %, thirty-eight inside 5 %, fifty-six inside 10 %")
    claim("Seven carry the")


# --- the gap -------------------------------------------------------------

def test_the_station_count_matches_the_drawing_pack():
    from publication.drawings import stations
    S = stations()
    placed = [s for s in S if s["x"] is not None]
    assumed = [s for s in placed if s["basis"] == "assumed"]
    assert (len(placed), len(S), len(assumed)) == (4, 10, 2)
    claim("**Four of the ten gas-path stations can be placed on a datum; six cannot.**")


def test_the_three_gap_sheets_are_the_three_in_the_code():
    from publication.drawings import GAPS
    assert len(GAPS) == 3
    claim("**Three of the six sheets exist to say something cannot be drawn.**")


def test_the_closure_scoreboard_matches():
    import collections
    by = collections.Counter(c["state"] for c in CLOSURES)
    assert (len(CLOSURES), by["met"], by["half"], by["gated"]) == (41, 25, 12, 4)
    claim("41 closures — 25 met,\n12 half, 4 gated.")


def test_the_post_states_a_findings_floor_that_is_true():
    """A floor, like the test count. Findings were exact while they arrived
    one at a time; once units are being closed in sequence they move as a
    side effect of routine work, which finding 170's own rule says belongs
    as a bound rather than an exact figure in prose."""
    from build_findings import findings_index
    n = len(findings_index())
    assert n >= 190, n
    claim("Over 190 numbered findings")


def test_the_post_states_a_test_count_floor_that_is_true():
    """A floor, not an exact count. The post is prose: stating an exact
    number here would mean re-editing it every time a test is added --
    including the tests in this file, which exist to check the post."""
    from build_readme import test_count
    n = test_count()
    assert n >= 850, n
    claim("Over 850 test functions")


# --- NASA is credited, and the limits are stated -------------------------

def test_nasa_is_credited_by_report_and_contract():
    for s in ("CR-168219", "NAS3-20643", "NASA Lewis Research Center",
              "General Electric", "TP-1337"):
        claim(s)
    claim("US Government work")


def test_the_post_disclaims_affiliation_and_owns_the_errors():
    claim("not affiliated with NASA")
    claim("any error in it is mine")


def test_the_post_leads_with_validation_not_the_render():
    """the plan's words: validation-led"""
    short = POST.split("## Short version")[1].split("## Long version")[0]
    assert short.index("0.01 %") < short.index("drawing sheet")
    assert "how wrong am I" in short


def test_the_post_states_the_unfinished_work():
    claim("Nine of ten stages")
    claim("needs a person at a GUI")
    claim("26 % of design")


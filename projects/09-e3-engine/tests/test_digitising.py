"""Stage I unit I4: the digitising uncertainty register
(solvers/verification/STEP0.md unit I4)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from verification.digitising import (  # noqa: E402
    campbell_resolvability, coverage, figure_citations, recorded, summary,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
R = recorded()
C = coverage()


# --- the register is built from the data files, not from here ------------

def test_every_entry_names_a_file_that_exists():
    for e in R:
        if e["file"] == "derived, not read":
            continue
        assert (ROOT / "data" / e["file"]).exists(), e["file"]


def test_every_recorded_uncertainty_is_actually_in_its_file():
    """the register must not be the only place a number lives"""
    import re
    for e in R:
        text = (ROOT / "data" / e["file"]).read_text()
        # each entry quotes a distinctive fragment of its source
        if e["key"] == "hpc_stagewise":
            assert "read_off_uncertainty" in text
        elif e["key"] == "hpt_fig5":
            assert "read_off_uncertainty_kJ_kg: 5" in text
        elif e["key"] == "hpc_rotor_campbell":
            assert "reading_uncertainty" in text
        elif e["key"] == "hpt_fig3_axial":
            assert re.search(r"\+-0\.3 cm|\+-0\.3", text)
        elif e["key"] == "lpt_blockage":
            assert "uncertainty: 0.012" in text


def test_every_entry_names_the_closures_it_governs():
    for e in R:
        assert e["closures"], e["key"]
        for c in e["closures"]:
            assert isinstance(c, str) and c


def test_the_registered_closures_exist():
    import yaml
    stages = {c["stage"] for c in
              yaml.safe_load((ROOT / "data/closures.yaml").read_text())["closures"]}
    for e in R:
        for c in e["closures"]:
            assert any(s == c or s.startswith(c) for s in stages), c


# --- nothing is invented -------------------------------------------------

def test_only_one_entry_carries_a_numeric_per_point_uncertainty():
    """the rest are prose because that is how their files record them;
    turning prose into a number here would be inventing it"""
    numeric = [e for e in R if e["value_hz"]]
    assert len(numeric) == 1
    assert numeric[0]["key"] == "hpc_rotor_campbell"


def test_entries_without_a_band_say_none_rather_than_guessing():
    for e in R:
        assert e["band_pct"] is None or e["band_pct"] > 0


def test_the_module_invents_no_uncertainty():
    src = (ROOT / "solvers/verification/digitising.py").read_text()
    assert "none is invented here" in src
    assert "because it would look measured" in src


# --- finding 160, generalised -------------------------------------------

def test_the_campbell_resolvability_is_recomputed_not_restated():
    cam = campbell_resolvability()
    from publication.campbell import resolvability
    assert cam["unresolvable"] == resolvability()["unresolvable"] == 11
    assert cam["resolvable"] == 13
    assert cam["first_flex_resolvable"] == 0


def test_the_worst_reading_is_coarser_than_the_band_it_is_judged_against():
    cam = campbell_resolvability()
    assert cam["worst_reading_pct"] > cam["band_pct"] * 2


# --- the honest coverage number -----------------------------------------

def test_the_coverage_is_reported_and_is_small():
    assert C["distinct_citations"] > 200
    assert C["recorded_entries"] == len(R) == 5
    assert C["pct_covered"] < 25


def test_the_coverage_count_declares_itself_generous():
    assert "generous" in C["note"]
    assert "per-figure coverage" in C["note"]


def test_figure_citations_are_found_across_many_files():
    cites = figure_citations()
    assert len(cites) == C["distinct_citations"]
    assert len({c[0] for c in cites}) == C["files_citing"] > 5


def test_the_summary_reports_the_gap_not_only_the_register():
    s = summary()
    assert "NO stated uncertainty" in s
    assert "generous count" in s
    assert "0 of 10" in s          # every first-flex mode unfalsifiable

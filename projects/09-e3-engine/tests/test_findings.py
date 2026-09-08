"""Stage I unit I3: FINDINGS.md, the deliverable
(solvers/verification/STEP0.md unit I3).

The document is generated, so these test the generator's inputs rather
than its prose: that every disagreement is harvested, that `unresolved`
means something, and that the file on disk is not stale."""
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solvers"))
from verification.disagreements import collect, summary  # noqa: E402

ROWS = collect()
S = summary(ROWS)


def test_every_disagreement_carries_a_source_and_both_numbers():
    assert len(ROWS) > 90
    for r in ROWS:
        assert r.source, r.quantity
        assert r.published != 0 or r.predicted == 0
        assert r.stage
        assert r.cause


def test_the_ranking_is_actually_ranked():
    errs = [abs(r.err_pct) for r in ROWS]
    assert errs == sorted(errs, reverse=True)


def test_unresolved_is_used_and_is_a_small_minority():
    """I3 asks for 'a cause or unresolved'. Zero unresolved would mean the
    causes were being invented; a large fraction would mean the project had
    not done its work."""
    assert 1 <= S["unresolved"] <= 15
    assert S["unresolved"] / S["total"] < 0.2
    unres = [r for r in ROWS if not r.resolved]
    assert {r.stage for r in unres} >= {"C4", "E2", "E3", "E5"}


def test_the_median_disagreement_is_single_digit_percent():
    """the project's overall standard of agreement, in one number"""
    assert S["median"] < 10.0


def test_more_than_half_the_comparisons_land_within_ten_percent():
    assert S["within_10"] / S["total"] > 0.5


def test_the_worst_disagreements_are_the_ones_the_findings_name():
    """the top of the ranking should be E3's beam-model bias and the
    open questions, not something unaccounted for"""
    top = ROWS[:10]
    assert all(r.stage in ("E3", "E5", "E2", "C4") for r in top), \
        [(r.stage, r.quantity) for r in top]


def test_findings_md_exists_and_is_current():
    """regenerating must not change it -- a stale deliverable is worse than
    no deliverable"""
    path = ROOT / "FINDINGS.md"
    assert path.exists()
    before = path.read_text()
    subprocess.run([sys.executable, "tools/build_findings.py"], cwd=ROOT,
                   capture_output=True, check=True)
    assert path.read_text() == before, "FINDINGS.md is stale; run tools/build_findings.py"


def test_findings_md_has_the_sections_i3_asked_for():
    t = (ROOT / "FINDINGS.md").read_text()
    assert "ranked" in t
    assert "Unresolved" in t
    assert "as designed and the E" in t          # the FPS vs ICLS section
    assert "Index of numbered findings" in t
    assert "55, 56, 57 are not used" in t        # the gap, recorded not hidden

"""Stage J: the README is generated where it carries numbers
(solvers/publication/STEP0.md, unit J4).

The README claimed "37 tests" and "build.py arrives with Stage C" long
after there were nine stages and nine hundred tests. A hand-maintained
count is a claim nobody re-checks, which is the one thing this project
says it does not do. These tests hold the generated block to the code."""
import pathlib
import re
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "solvers"))

import yaml  # noqa: E402
from build_readme import BEGIN, END, block, closures  # noqa: E402

README = (ROOT / "README.md").read_text()
GENERATED = re.search(re.escape(BEGIN) + r"(.*?)" + re.escape(END), README,
                      re.S).group(0)


def test_the_readme_has_a_generated_block():
    assert BEGIN in README and END in README
    assert README.index(BEGIN) < README.index(END)


def test_the_generated_block_is_current():
    """regenerating must not change it -- a stale README is the failure this
    whole arrangement exists to stop"""
    assert GENERATED.strip() == block().strip(), \
        "run: python tools/build_readme.py"


def test_every_closure_appears_in_the_readme():
    c, _ = closures()
    for x in c:
        assert f"**{x['stage']}**" in GENERATED, x["stage"]


def test_the_gated_closures_are_marked_gated_and_not_buried():
    c, by = closures()
    gated = [x for x in c if x["state"] == "gated"]
    assert len(gated) == by["gated"] > 0
    for x in gated:
        assert "**gated**" in GENERATED
    # and each one says why, in Outstanding
    for x in gated:
        assert x["stage"] in GENERATED.split("### Outstanding")[1]


def test_no_closure_is_open_without_a_reason():
    c, _ = closures()
    out = GENERATED.split("### Outstanding")[1]
    for x in c:
        if x["state"] != "met":
            assert (x.get("gate") or x.get("note")), f"{x['stage']} has no reason"
            assert f"**{x['stage']}**" in out


def test_every_figure_on_disk_is_listed():
    figs = sorted((ROOT / "solvers/publication/figures").glob("*.png"))
    assert len(figs) >= 4
    for f in figs:
        assert f.name in GENERATED


def test_the_status_line_counts_agree_with_the_data():
    c, by = closures()
    assert f"**{len(c)} closures**" in GENERATED
    assert f"{by['met']} met, {by['half']} half, {by['gated']} gated" in GENERATED


def test_the_hand_written_half_carries_no_stale_test_count():
    """the specific rot that happened: a number in the prose"""
    prose = README.replace(GENERATED, "")
    # sibling projects' own counts live in the "What it builds on" table and
    # are about those projects; only this project's count is the hazard
    prose = "\n".join(ln for ln in prose.splitlines() if "../0" not in ln)
    assert "37 tests" not in prose
    assert "904 tests" not in prose
    assert not re.search(r"\b\d{2,4} tests\b", prose), \
        "a test count in this project's prose will go stale; " \
        "put it in the generated block"


def test_the_readme_points_at_the_deliverable_and_the_method():
    for link in ("FINDINGS.md", "WORK-PLAN.md", "METHOD.md", "RESUME.md",
                 "REFERENCES.md"):
        assert link in README


def test_the_ci_workflow_runs_the_whole_suite():
    """not a hand-picked list of files, which goes stale the same way"""
    ci = (ROOT.parents[1] / ".github/workflows/e3-engine-ci.yml")
    if not ci.exists():
        pytest.skip("workflow not in this checkout")
    t = ci.read_text()
    runs = [ln.strip() for ln in t.splitlines() if ln.strip().startswith("- run:")]
    pytest_runs = [r for r in runs if "-m pytest" in r]   # not pip install
    assert pytest_runs == ["- run: python -m pytest -q"], pytest_runs
    y = yaml.safe_load(t)
    assert "projects/09-e3-engine" in str(y)


def test_the_two_cadquery_tests_declare_their_own_dependency():
    """so the CI never needs to know which files they are"""
    for name in ("test_geometry.py", "test_render.py"):
        t = (ROOT / "tests" / name).read_text()
        assert 'importorskip("cadquery")' in t


def test_build_readme_refuses_a_readme_without_markers(tmp_path):
    import build_readme
    p = tmp_path / "README.md"
    p.write_text("no markers here")
    old = build_readme.ROOT
    try:
        build_readme.ROOT = tmp_path
        with pytest.raises(SystemExit):
            build_readme.main()
    finally:
        build_readme.ROOT = old

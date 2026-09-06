"""C1 unit 6: the fan and quarter-stage mean-line
(solvers/meanline/STEP0.md unit 6)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from meanline.fan import (  # noqa: E402
    fan_rotor_sections, island_split, row_efficiencies, stage_coefficients,
)

SECS, G = fan_rotor_sections()
BY = {s.name: s for s in SECS}
ROWS = row_efficiencies()
COEFFS, RPM_PRINTED = stage_coefficients()
ISLAND = island_split()


def test_tip_relative_mach_from_specific_flow_and_tip_speed():
    """finding 21: two printed numbers that never mention Mach give the
    printed leading-edge relative Mach to 0.005"""
    t = BY["tip"]
    assert abs(t.m_rel - t.m_rel_printed) < 0.05
    assert abs(t.m_rel - t.m_rel_printed) < 0.01
    assert 0.62 < G["m_axial"] < 0.64


@pytest.mark.parametrize("name", ["shroud (55 % height)", "hub"])
def test_inner_sections_with_a_uniform_axial_mach(name):
    """inside the +-0.08 stated for a uniform-axial assumption, but only
    just, and the errors are opposite in sign -- see finding 22"""
    s = BY[name]
    assert abs(s.m_rel - s.m_rel_printed) < 0.08
    assert abs(s.m_rel - s.m_rel_printed) > 0.05


def test_inner_section_errors_are_opposite_in_sign_and_pinned():
    """the sign is the finding: low at the shroud, high at the hub"""
    shroud = BY["shroud (55 % height)"]
    hub = BY["hub"]
    assert shroud.m_rel - shroud.m_rel_printed < -0.05
    assert hub.m_rel - hub.m_rel_printed > 0.05
    assert abs(shroud.m_rel - shroud.m_rel_printed) < 0.10
    assert abs(hub.m_rel - hub.m_rel_printed) < 0.10


def test_row_efficiencies_recompute():
    for r in ROWS:
        band = 0.011 if r["row"] == "S2IN_inner_ogv" else 0.005
        assert abs(r["eta"] - r["eta_printed"]) < band, r


def test_only_the_inner_ogv_misses():
    """finding 25"""
    misses = [r for r in ROWS if abs(r["eta"] - r["eta_printed"]) > 0.005]
    assert [r["row"] for r in misses] == ["S2IN_inner_ogv"]


def test_one_shaft_two_rows():
    """finding 23: both tip speeds imply the printed corrected speed"""
    for c in COEFFS:
        assert abs(c["rpm_from_tip_speed"] / RPM_PRINTED - 1) < 0.002
    assert abs(COEFFS[0]["rpm_from_tip_speed"] - COEFFS[1]["rpm_from_tip_speed"]) < 2.0


def test_island_split_closes():
    assert abs(ISLAND["closure"]) < 0.1
    assert abs(ISLAND["over_closure"]) < 0.1
    assert abs(ISLAND["split_pct"] - ISLAND["split_printed"]) < 0.1
    assert abs(ISLAND["return_pct"] - ISLAND["return_printed"]) < 1.0
    assert abs(ISLAND["bpr"] - ISLAND["bpr_printed"]) < 0.02


def test_the_booster_is_a_quarter_stage_in_loading_too():
    """finding 24"""
    fan, booster = COEFFS
    assert 0.6 < fan["psi"] < 0.75
    assert 0.2 < booster["psi"] < 0.30
    assert booster["psi"] < 0.45 * fan["psi"]
    assert 0.7 < fan["phi"] < 0.8 and 0.85 < booster["phi"] < 0.95

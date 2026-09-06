"""C3 unit 15: the fan blade, DESIGNED not transcribed
(solvers/blading/STEP0.md unit 15). The published throat margin is the
check; everything else about the blade is a design."""
import math
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from blading.fan_blade import design, load  # noqa: E402

SECS, P = design()
FAN = load()
PUB = FAN["fan_rotor_airfoil"]


def test_it_is_designed_over_the_span_the_report_publishes():
    """Fig 3 stops at the island; below it the work is shared with the
    booster and is not extrapolated"""
    assert len(SECS) >= 9
    assert SECS[0].radius_m > P["r_island"] - 1e-6
    assert SECS[0].radius_m < 0.62 and SECS[-1].radius_m > 0.95
    assert P["r_island"] > P["r_hub"]


def test_throat_margin_against_the_published_value():
    """finding 53: the one published number not used to make the design"""
    m = [s.throat_margin_pct for s in SECS]
    pub = PUB["throat_margin_pct"]
    assert all(0 < x for x in m)
    assert max(m) < pub["id"] + 10.0
    assert statistics.median(m) > pub["typical"]


def test_the_design_is_conservative_not_marginal():
    assert all(s.throat_margin_pct > 5.0 for s in SECS)


def test_tip_solidity_matches_the_published_value():
    assert abs(SECS[-1].solidity - PUB["fig15"]["solidity_tip"]) < 0.1


def test_camber_falls_monotonically_toward_the_transonic_tip():
    """finding 52 -- and 54: it reaches about 1 degree"""
    c = [s.camber for s in SECS]
    assert all(c[i] > c[i + 1] for i in range(len(c) - 1))
    assert c[0] > 25 and c[-1] < 3


def test_turning_and_deviation_are_monotonic_and_sensible():
    b2 = [s.beta2_flow for s in SECS]
    dev = [s.deviation for s in SECS]
    assert all(b2[i] < b2[i + 1] for i in range(len(b2) - 1))
    assert all(dev[i] > dev[i + 1] for i in range(len(dev) - 1))
    assert 0 < min(dev) and max(dev) < 10


def test_the_velocity_triangles_are_physical():
    """the errors of unit 15: work above the blade speed, and a static
    state taken from the relative Mach"""
    for s in SECS:
        assert 100 < s.cx1 < 300, s.cx1          # a 2.1 m fan ingests ~200 m/s
        assert 40 < s.beta1_flow < 70
        assert s.beta2_flow < s.beta1_flow        # a compressor diffuses
        assert s.w2 < s.w1


def test_relative_mach_rises_outward_and_is_transonic_at_the_tip():
    m = [s.m_le for s in SECS]
    assert all(m[i] < m[i + 1] for i in range(len(m) - 1))
    assert m[-1] > 1.3


def test_incidence_is_the_published_five_degrees():
    for s in SECS:
        assert abs((s.beta1_flow - s.beta1_metal) - PUB["incidence_deg"]["design_point_all_span"]) < 1e-6

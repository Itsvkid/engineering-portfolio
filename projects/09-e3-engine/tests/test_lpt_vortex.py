"""C2 unit 10: the vortex law of the LPT and the HPC
(solvers/throughflow/STEP0.md unit 10)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from throughflow.lpt_vortex import hpc_vortex, stage_vortex  # noqa: E402

LPT = stage_vortex()
HPC = hpc_vortex()
FREE_VORTEX = -1.0


def test_the_lpt_is_not_a_free_vortex():
    """finding 36: the report's 'controlled vortex' is n about -0.5"""
    ex = [r["exponent"] for r in LPT]
    assert len(ex) == 5
    assert all(-1.0 < n < 0.0 for n in ex)
    assert all(n > FREE_VORTEX + 0.25 for n in ex)
    assert -0.6 < sum(ex) / len(ex) < -0.4


def test_angular_momentum_is_not_constant_across_the_span():
    for r in LPT:
        assert r["rct_spread"] > 0.10


def test_the_law_drifts_toward_free_vortex_rearward():
    """finding 37: scheduled with radius ratio, not a constant"""
    ex = [r["exponent"] for r in LPT]
    assert ex[4] < ex[0] - 0.25
    ratios = [r["radii"][0] / r["radii"][2] for r in LPT]
    assert ratios[4] < ratios[0]


def test_the_compressor_has_no_single_vortex_law():
    """finding 38: exponents from +0.54 to -0.76 with no order"""
    good = [h for h in HPC if not h["degenerate"]]
    assert len(good) == 9
    ex = [h["exponent"] for h in good]
    assert max(ex) > 0.3 and min(ex) < -0.6
    assert max(ex) - min(ex) > 1.0
    # and the spread is larger than the turbine's
    lpt_ex = [r["exponent"] for r in LPT]
    assert (max(ex) - min(ex)) > 2 * (max(lpt_ex) - min(lpt_ex))


def test_stator_1_is_a_forced_vortex():
    s1 = next(h for h in HPC if h["stage"] == 1)
    assert s1["exponent"] > 0.3


def test_the_ogv_is_excluded_as_degenerate():
    ogv = next(h for h in HPC if h["stage"] == 10)
    assert ogv["degenerate"]
    assert ogv["mean_swirl"] < 8.0

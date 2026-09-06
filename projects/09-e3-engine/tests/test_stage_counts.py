"""C1 unit 7: stage counts derived from the cycle, the shaft speeds and
generic loading limits (solvers/meanline/STEP0.md unit 7)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from meanline.stage_counts import LIMITS, build  # noqa: E402

COMPS, SPEEDS = build()
BY = {c.name: c for c in COMPS}


def test_the_limits_are_generic_not_fitted():
    """they are the agent's section 4 ranges, and none is an E3 value"""
    assert LIMITS["fan"] == LIMITS["booster"] == LIMITS["hpc"] == 0.45
    assert LIMITS["hpt"] == 0.85 and LIMITS["lpt"] == 1.75


@pytest.mark.parametrize("name, expected", [("HPC", 10), ("HPT", 2), ("booster", 1)])
def test_stage_count_falls_out_of_the_cycle(name, expected):
    assert BY[name].stages_rounded == expected


def test_actual_loadings_sit_inside_the_limits_used():
    assert BY["HPC"].psi_actual < LIMITS["hpc"]
    assert BY["HPT"].psi_actual < LIMITS["hpt"]
    assert BY["LPT"].psi_actual < LIMITS["lpt"]


def test_a_single_stage_hpt_is_rejected_as_ge_rejected_it():
    """finding 27: one stage would need psi 1.38 against a 0.85 limit;
    the HPT report's Table II evaluated and rejected exactly that option"""
    c = BY["HPT"]
    psi_one_stage = c.dh / (2 * c.u_pitch ** 2)
    assert psi_one_stage > 1.3
    assert psi_one_stage > 1.5 * LIMITS["hpt"]


@pytest.mark.xfail(strict=True, reason="unit 7 finding 28: a subsonic-compressor loading limit does not govern a transonic fan -- the E3 does in one stage what psi <= 0.45 says needs two, at psi 0.74, because tip Mach and blade stress bound it instead")
def test_fan_stage_count():
    assert BY["fan"].stages_rounded == 1


def test_fan_miss_is_pinned_and_is_the_transonic_signature():
    c = BY["fan"]
    assert c.stages_rounded == 2
    assert 0.70 < c.psi_actual < 0.80
    assert c.psi_actual > 1.5 * LIMITS["fan"]


@pytest.mark.xfail(strict=True, reason="unit 7 finding 29: loading alone asks for four LPT stages; the E3 uses five because stage count there is set by efficiency, not feasibility")
def test_lpt_stage_count():
    assert BY["LPT"].stages_rounded == 5


def test_lpt_has_one_stage_more_than_loading_requires():
    c = BY["LPT"]
    assert c.stages_rounded == 4
    assert c.psi_actual < 1.4
    # four stages would still be inside the limit
    assert c.dh / (4 * 2 * c.u_pitch ** 2) < LIMITS["lpt"]


def test_speeds_are_the_published_ones():
    assert abs(SPEEDS["n_lp"] - 3539) < 1 and abs(SPEEDS["n_hp"] - 12303) < 1

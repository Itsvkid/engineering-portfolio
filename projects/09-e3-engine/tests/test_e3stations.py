"""B4: station properties and the annulus against STEP0.md's B4 bands.
Bands written first; misses are strict xfails with their size pinned."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from e3cycle.stations import run  # noqa: E402

RES, CHECKS, EXTRA, GEO = run()
BY = {(c.station, c.quantity): c for c in CHECKS}


def check(station, quantity):
    return BY[(station, quantity)]


@pytest.mark.parametrize("station, quantity", [
    ("2", "specific flow kg/s.m2"),
    ("25", "R1 LE annulus x blockage 0.97"),
    ("3", "OGV TE annulus x blockage 0.90"),
    ("41", "W41 sqrtT/P g.sqrtK/(s.Pa)"),
    ("41", "dh/T41 J/(kg.K)"),
    ("4x", "stage-1 exit annulus m2"),
    ("45", "stage-2 exit annulus m2"),
    ("49", "T49 K"),
    ("49", "W49 sqrtT/P g.sqrtK/(s.Pa)"),
    ("49", "dh/T49 J/(kg.K)"),
])
def test_within_band(station, quantity):
    c = check(station, quantity)
    assert abs(c.diff) < c.band, f"{quantity}: {c.computed:.4f} vs {c.published:.4f} ({c.diff * 100:+.2f} %)"


@pytest.mark.xfail(strict=True, reason="B4 finding 1: the geometric annulus reads short by Table XXI's blockage (0.97 inlet, 0.90 exit); the blockage-corrected rows pass")
@pytest.mark.parametrize("station, quantity", [("25", "R1 LE annulus m2"), ("3", "OGV TE annulus m2")])
def test_hpc_geometric_annulus(station, quantity):
    c = check(station, quantity)
    assert abs(c.diff) < c.band


def test_hpc_blockage_is_the_whole_miss():
    """the exit misses by 10.2 percent geometric and 0.2 with the 0.90"""
    assert -0.12 < check("3", "OGV TE annulus m2").diff < -0.08
    assert -0.07 < check("25", "R1 LE annulus m2").diff < -0.04


@pytest.mark.xfail(strict=True, reason="B4 finding 2: Fig 7's wall Mach 0.40 at the vane-1 LE needs 18 percent less annulus than the sections give; continuity puts the LE Mach at 0.32")
def test_lpt_vane1_le_annulus():
    c = check("49", "vane-1 LE annulus m2")
    assert abs(c.diff) < c.band


def test_lpt_vane1_le_mach_pinned():
    assert -0.21 < check("49", "vane-1 LE annulus m2").diff < -0.16
    assert 0.30 < EXTRA["lpt_vane1_le_mach_implied"] < 0.33


@pytest.mark.xfail(strict=True, reason="B4 finding 3: an equal-weighted hub/pitch/tip axial Mach overstates the LPT flow by 6-17 percent; the pitch value carries the flow")
@pytest.mark.parametrize("n", [1, 2, 3, 4, 5])
def test_lpt_stage_exit_three_point_mean(n):
    c = check(f"R{n}", f"stage-{n} exit annulus m2")
    assert abs(c.diff) < c.band


def test_lpt_stage_exits_at_pitch_show_a_uniform_blockage():
    """3.4-5.5 percent under the sections' annulus on every stage: the
    through-flow blockage the LPT report applies (sec 2.6) and does not print"""
    diffs = [check(f"R{n}", f"stage-{n} exit annulus, pitch Mach only").diff for n in range(1, 6)]
    assert all(-0.06 < d < -0.03 for d in diffs), diffs
    assert max(diffs) - min(diffs) < 0.025


def test_turbine_two_routes_agree_to_one_percent():
    for st, q in (("41", "W41 sqrtT/P g.sqrtK/(s.Pa)"), ("41", "dh/T41 J/(kg.K)"), ("49", "T49 K"), ("49", "W49 sqrtT/P g.sqrtK/(s.Pa)")):
        assert abs(check(st, q).diff) < 0.01


def test_lpt_work_matches_table_ii_stage_sum():
    assert abs(EXTRA["lpt_dh_per_kg"] / EXTRA["table_ii_dh_sum_J_kg"] - 1) < 0.01


def test_station_table_monotonic():
    s = RES.stations
    assert s["t0"] < s["t25"] < s["t3"] < s["t41"] < s["t4"]
    assert s["t4"] > s["t41"] > s["t45"] > s["t5"] > s["t6"] > s["t13"]
    assert s["p0"] < s["p25"] < s["p3"] and s["p4"] > s["p45"] > s["p5"]
    assert 0.60 < EXTRA["fan_face_mach"] < 0.66


def test_figures_exist():
    d = pathlib.Path(__file__).resolve().parents[1] / "solvers" / "e3cycle" / "figures"
    assert (d / "annulus.png").exists() and (d / "ts-diagram.png").exists()

"""Stage E unit E2: the rotating disc
(solvers/mechanical/STEP0.md unit E2)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from mechanical.disc import (  # noqa: E402
    NU, RHO_RENE95, bore_concentration, bounding_estimates, centrifugal_screen,
    hoop_stress_annular, hoop_stress_solid, rim_load, rim_load_contribution,
    rim_load_hoop, speeds, stage1_radii, two_term_stage2,
)

ROWS, N, SCALE = centrifugal_screen()
BY = {r["location"]: r for r in ROWS}
TT = two_term_stage2()


# --- the closed-form mechanics, against the textbook -----------------------

def test_the_bore_doubling_is_exactly_two_in_the_limit():
    """E2's stated closure half: a vanishing hole doubles the stress."""
    assert abs(bore_concentration(0.0) - 2.0) < 1e-12
    assert abs(bore_concentration(0.01) - 2.0) < 0.005      # the +-0.5 % band


def test_the_concentration_rises_monotonically_with_hole_size():
    ratios = [bore_concentration(x) for x in (0.0, 0.05, 0.1, 0.2, 0.3, 0.5)]
    assert ratios == sorted(ratios)


def test_the_annular_solution_reduces_to_the_solid_one_as_the_hole_shrinks():
    """away from the hole the two fields must agree"""
    b, omega, r = 0.31, 1460.0, 0.20
    a = 1e-6 * b
    annular = hoop_stress_annular(r, a, b, RHO_RENE95, omega)
    solid = hoop_stress_solid(r, b, RHO_RENE95, omega)
    assert abs(annular / solid - 1) < 1e-6


def test_the_solid_disc_centre_is_the_textbook_coefficient():
    b, omega = 0.31, 1460.0
    expect = (3 + NU) / 8 * RHO_RENE95 * omega ** 2 * b ** 2
    assert abs(hoop_stress_solid(0.0, b, RHO_RENE95, omega) - expect) < 1e-6


def test_a_rim_pull_also_doubles_at_a_small_bore():
    """the Lame field: sigma_theta(a) -> 2 S as a/b -> 0"""
    assert abs(rim_load_hoop(100.0, 1e-6) - 200.0) < 1e-3
    assert rim_load_hoop(100.0, 0.15) > 200.0


# --- the E3 disc, from published numbers only ------------------------------

def test_the_rim_load_is_the_published_dovetail_load_times_the_blade_count():
    r = rim_load()
    assert r["blades"] == 76
    assert abs(r["load_per_blade_kN"] - 77.395) < 1e-9
    assert abs(r["total_kN"] - 76 * 77.395) < 1e-9
    assert r["rpm"] == 13948
    assert abs(r["tonnes"] - 600) < 2          # 5882 kN is 600 tonnes-force


def test_the_stage1_radii_come_out_of_table_iii_not_an_assumption():
    r_tip, r_hub, omega = stage1_radii()
    assert abs(omega - 13948 * 2 * math.pi / 60) < 1e-6
    assert 0.34 < r_tip < 0.36
    assert abs(r_hub / r_tip - 0.88) < 1e-9


def test_the_published_bore_stress_lies_inside_the_constant_thickness_bracket():
    bd = bounding_estimates()
    for published in (779, 903, 889, 910, 807):
        assert bd["solid_MPa"] < published < bd["annular_MPa"]


def test_the_blade_pull_at_the_bore_is_the_same_order_as_the_gap_it_must_fill():
    """finding 80: for any plausible rim width the blade pull puts
    77-309 MPa at the bore, on top of the disc's own 691"""
    rows = rim_load_contribution()
    assert 70 < min(r["bore_hoop_MPa"] for r in rows) < 100
    assert 290 < max(r["bore_hoop_MPa"] for r in rows) < 330


# --- which load sets the bore? --------------------------------------------

def test_the_three_speeds_are_figure_53s_own():
    assert speeds() == [13300, 12800, 12600]
    assert SCALE[0] == 1.0
    assert 0.89 < SCALE[2] < 0.91


def test_not_one_of_nineteen_locations_scales_as_speed_squared():
    """finding 78 -- the model is rejected at every single location, and
    the closest of them, the stage-1 disc bore forward face, misses the
    stated 5 % band at 5.1 %"""
    assert len(ROWS) == 19
    assert [r["location"] for r in ROWS if r["worst_pct"] <= 5.0] == []
    closest = min(ROWS, key=lambda r: r["worst_pct"])
    assert closest["location"] == "stage1_disk_bore_forward"
    assert 5.0 < closest["worst_pct"] < 5.5


def test_the_bores_peak_at_875_s_and_the_gas_washed_parts_at_40_s():
    """finding 78 -- two different limiting instants in one rotor"""
    for bore in ("stage1_disk_bore", "stage2_disk_bore", "inducer_disk_bore"):
        s = BY[bore]["published"]
        assert s[1] == max(s)
    for washed in ("stage1_blade_retainer", "stage1_forward_shank_seal",
                   "impeller_to_stage1_forward_arm"):
        s = BY[washed]["published"]
        assert s[0] == max(s)


def test_the_two_term_fit_lands_inside_ten_percent():
    assert max(abs(e) for e in TT["err_pct"]) < 10.0


def test_the_thermal_constant_is_a_physical_fraction_of_alpha_E():
    lo, hi = TT["alpha_E_range"]
    assert 0 < TT["k_MPa_per_K"] < lo
    assert 0.2 < TT["k_MPa_per_K"] / hi < 0.5


def test_the_leave_one_out_shows_the_split_is_not_determined():
    """finding 79 -- 875 s and 1700 s are nearly the same thermal state,
    so the pair carries almost no information about k"""
    ks = [h["k_MPa_per_K"] for h in TT["leave_one_out"]]
    assert max(ks) - min(ks) > 20          # k swings from +1.56 to -27.6
    worst = max(abs(h["err_pct"]) for h in TT["leave_one_out"])
    assert worst > 100                      # the 40 s hold-out is 196 % out
    assert abs(TT["delta_T"][1] - TT["delta_T"][2]) < 5   # the near-singularity


def test_the_gated_half_is_absent_rather_than_guessed():
    """E2's Fig 64 peak needs the disc profile, which was never transcribed;
    nothing in this module returns a peak effective stress"""
    import mechanical.disc as d
    assert not [n for n in dir(d) if "peak" in n.lower()]

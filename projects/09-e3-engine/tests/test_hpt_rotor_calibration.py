"""Stage E unit E12: what CR-167955's stage-1 disc can and cannot be
calibrated to.

The bands are solvers/mechanical/STEP0.md, unit E12. They were written
before the run and are not edited here. Band C5 is a recorded FAILURE and
is xfailed with its cause, not widened; C2 is recorded as not evaluable as
written and its substitute is tested in its own right; C4 is not a miss but
a quantity the drawing does not contain.

These tests never open the PDF. `tools/read_hpt_fig112.py` writes the pixel
coordinates it read into `data/hpt-rotor-calibration.yaml`, so every refit
below runs off the YAML.
"""
import math
import pathlib

import numpy as np
import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
CAL = yaml.safe_load((ROOT / "data" / "hpt-rotor-calibration.yaml").read_text())
XREF = 2750


def _anchors():
    t = math.tan(math.radians(CAL["calibration"]["rot_deg"]))
    Y, R = [], []
    for s in ("stage1", "stage2"):
        for k in ("tip", "platform"):
            f = CAL["features"][s][k]
            Y.append(f["y_px"] - t * (f["x_px"] - XREF))
            R.append(f["r_published_cm"])
    return np.array(Y), np.array(R)


# ------------------------------------------------ the anchors are published

def test_the_four_anchors_are_the_published_flowpath_and_nothing_else():
    """Every radius the calibration is fitted on must be a number in
    e3-fps-published.yaml hpt.flowpath, not a value read off this drawing."""
    pub = yaml.safe_load((ROOT / "data" / "e3-fps-published.yaml").read_text())
    fp = {r["location"]: r for r in pub["hpt"]["flowpath"]["stations"]}
    want = {
        ("stage1", "tip"): (fp["stage1_vane_exit"]["r_tip_cm"],
                            fp["stage1_blade_exit"]["r_tip_cm"]),
        ("stage1", "platform"): (fp["stage1_vane_exit"]["r_hub_cm"],
                                 fp["stage1_blade_exit"]["r_hub_cm"]),
        ("stage2", "tip"): (fp["stage2_vane_exit"]["r_tip_cm"],
                            fp["stage2_blade_exit"]["r_tip_cm"]),
        ("stage2", "platform"): (fp["stage2_vane_exit"]["r_hub_cm"],
                                 fp["stage2_blade_exit"]["r_hub_cm"]),
    }
    for (s, k), (lo, hi) in want.items():
        used = CAL["features"][s][k]["r_published_cm"]
        assert used == pytest.approx((lo + hi) / 2, abs=1e-9), (s, k, used)


# ------------------------------------------------------------ band C1, met

def test_c1_the_calibration_fits_its_own_anchors_to_the_band():
    assert CAL["calibration"]["rms_cm"] <= 0.15
    assert CAL["calibration"]["max_cm"] <= 0.15


def test_the_fit_reproduces_from_the_stored_pixels():
    """the YAML's coefficients must come out of the YAML's own pixels"""
    Y, R = _anchors()
    coef = np.polyfit(Y, R, 1)
    assert coef[1] == pytest.approx(CAL["calibration"]["a"], abs=1e-6)
    assert coef[0] == pytest.approx(CAL["calibration"]["b"], abs=1e-9)


# ------------------------------------- finding 265: the rotation is external

def test_the_rotation_is_measured_on_the_caption_not_fitted_to_the_anchors():
    r = CAL["page_rotation"]
    assert r["spread_deg"] <= 0.10, "the two caption lines must agree"
    assert r["deg"] == pytest.approx(
        (r["baseline"]["deg"] + r["cap_height"]["deg"]) / 2, abs=1e-9)
    # and it is NOT the angle the anchors would pick for themselves
    assert abs(CAL["calibration_free_rotation"]["rot_deg"] - r["deg"]) > 0.2


def test_imposing_the_caption_rotation_is_worth_a_factor_of_four():
    with_rot = CAL["calibration"]["rms_cm"]
    without = CAL["calibration_without_rotation"]["rms_cm"]
    assert without / with_rot >= 4.0
    # and it costs the scale almost nothing
    assert abs(CAL["calibration_without_rotation"]["px_per_cm"]
               / CAL["calibration"]["px_per_cm"] - 1) < 0.02


# ---------------- band C2: not evaluable as written; the substitute instead

def test_c2_as_written_is_degenerate_and_is_recorded_as_such():
    """Two families of two points against two parameters. A held-out-family
    test has nothing left to predict, which is why finding 266 substitutes
    the per-blade scale."""
    n_per_family = 2
    n_params = 2
    assert n_per_family <= n_params


def test_each_blade_gives_the_scale_on_its_own_and_they_agree():
    s = CAL["scale_per_blade"]
    assert s["spread_pct"] <= 2.0
    # the two blades' spans differ by more than half, so this is not a
    # comparison of two near-identical measurements
    r = s["stage2"]["span_cm"] / s["stage1"]["span_cm"]
    assert r > 1.5


def test_the_drawn_platform_slope_has_the_published_sign_on_both_blades():
    """**This is what E12's third check actually established**, and it
    survives finding 290 intact: the drawn platform falls outward-to-inward
    in the published sense on both blades, and by the published order of
    magnitude, which is what identifies the line as the flowpath hub and not
    the angel wing half a centimetre below it. Four of four blades across
    Figures 112 and 50 agree in sign and order. What finding 290 corrects is
    the arithmetic of one comparison, not the identification."""
    for k, v in CAL["platform_slope_check"].items():
        assert v["drop_over_window_cm"] > 0, k
        assert v["published_drop_over_window_cm"] > 0, k
        ratio = v["drop_over_window_cm"] / v["published_drop_over_window_cm"]
        assert 0.3 < ratio < 3.0, (k, ratio)


def test_the_slope_comparison_is_pro_rated_to_the_drawn_window():
    """finding 290: the published hub fall is quoted across the WHOLE blade
    and the drawn window is shorter, so comparing the two directly compares
    unlike windows. The YAML carries both; only the pro-rated one is
    comparable, and it is the one the two tests below use."""
    for k, v in CAL["platform_slope_check"].items():
        assert v["window_cm"] < v["blade_axial_cm"], k
        assert v["published_drop_over_window_cm"] == pytest.approx(
            v["published_drop_cm"] * v["window_cm"] / v["blade_axial_cm"],
            abs=5e-4), k
        # and it is NOT the same number, which is why this matters
        assert abs(v["published_drop_over_window_cm"]
                   - v["published_drop_cm"]) > 0.03, k


def test_the_pro_rated_platform_slope_matches_on_the_stage_2_blade():
    """finding 290: three parts in ten thousand -- and E12 recorded this
    blade as a 0.034 cm miss, because it compared a 2.94 cm window against a
    4.5 cm blade's fall."""
    v = CAL["platform_slope_check"]["stage2"]
    assert abs(v["drop_over_window_cm"]
               - v["published_drop_over_window_cm"]) <= 0.05


@pytest.mark.xfail(strict=True, reason="finding 290: recorded failure, not "
                   "widened. Pro-rated to its own 3.75 cm window of a 5.0 cm "
                   "blade, the drawn stage-1 platform falls 0.2838 cm against "
                   "a published 0.1875 -- +0.096 cm, nearly 3x E12's own "
                   "0.05 cm band. E12 read it as a 0.034 cm pass by comparing "
                   "the window's drop against the whole blade's fall. The "
                   "identification stands (see the sign test above); the "
                   "arithmetic of this one check does not.")
def test_the_pro_rated_platform_slope_matches_on_the_stage_1_blade():
    v = CAL["platform_slope_check"]["stage1"]
    assert abs(v["drop_over_window_cm"]
               - v["published_drop_over_window_cm"]) <= 0.05


# ------------------------------- band C4: not measurable, and the evidence

def test_c4_the_published_stud_is_not_drawn_so_it_cannot_check_the_scale():
    b = CAL["independent_scale_check"]
    assert b["measurable"] is False
    assert b["median_dark_run_in_gap_px"] < 0.25 * b["expected_shank_px_if_drawn"]


# ----------------------------------------- band C5: the recorded FAILURE

def _interval(r_target, conf_t=4.302):      # t(0.975, dof=2)
    Y, R = _anchors()
    n = len(Y)
    coef = np.polyfit(Y, R, 1)
    res = R - np.polyval(coef, Y)
    s2 = (res @ res) / (n - 2)
    y = (r_target - coef[1]) / coef[0]
    se = math.sqrt(s2 * (1 / n + (y - Y.mean()) ** 2 / ((Y - Y.mean()) ** 2).sum()))
    return conf_t * se


def test_the_calibration_is_worth_one_percent_at_the_disc_rim():
    """finding 267: where the rim is, the figure is good enough for E2's
    dominant term -- bore hoop stress goes as the RIM radius squared"""
    assert _interval(30.0) <= 0.35


@pytest.mark.xfail(strict=True, reason="finding 267: recorded failure, not "
                   "widened. Four anchors spanning 6.9 cm cannot carry a "
                   "bore 18 cm below them; the 95 % interval is 1.18 cm "
                   "analytic and 0.81 jackknife against a 0.5 cm band.")
def test_c5_the_bore_radius_interval_meets_the_band():
    assert _interval(13.0) <= 0.5


def test_the_extrapolation_penalty_is_monotone_and_large():
    a, b, c = _interval(31.17), _interval(22.0), _interval(13.0)
    assert a < b < c
    assert c / a > 4


# ------------------- finding 264: the dovetail chain is singular, not weak

def test_the_dovetail_chain_determinant_is_a_difference_of_equals():
    """CR-167955 Fig 81 prints the two tang neck widths. Solving the two
    pitch equations for a radius divides by
        (measured post-width step) - (pitch growth over the tang separation)
    and the printed neck-width difference is the same size as that growth,
    so the system is singular to within a line width."""
    n_blades = 76
    dw = 0.952 - 0.820                       # cm, printed
    for tang_sep_cm in (1.0, 1.5, 2.0):
        growth = 2 * math.pi * tang_sep_cm / n_blades
        assert 0.4 < growth / dw < 1.6, tang_sep_cm
    # a half-millimetre reading error moves the derived scale by >25 %
    err = 0.05
    assert abs(dw / (dw - err) - 1) > 0.25
    assert abs(dw / (dw + err) - 1) > 0.25


# ------------------------------------------- finding 263: what Fig 63 is not

def test_the_calibration_records_that_figure_63_carries_no_anchor():
    why = CAL["meta"]["why_not_figure_63"]
    assert "no flowpath" in why and "dovetail seat" in why

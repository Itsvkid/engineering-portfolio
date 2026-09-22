"""Stage E unit E14: CR-167955 Figure 50 p.87 calibrated, and put against
Figure 112 p.180 -- the only test available that does not run through the
same page twice.

The bands are solvers/mechanical/STEP0.md, unit E14, written before the run
and not edited here. E3r and E4r are recorded FAILURES and are xfailed with
their cause; E5r is a recorded failure too. Nothing is widened.

These tests never open a PDF. `tools/read_hpt_fig50.py` writes every pixel
coordinate it read into `data/hpt-fig50-calibration.yaml`, so each refit
below runs off the YAML.
"""
import math
import pathlib

import numpy as np
import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
CAL = yaml.safe_load((ROOT / "data" / "hpt-fig50-calibration.yaml").read_text())
CAL112 = yaml.safe_load(
    (ROOT / "data" / "hpt-rotor-calibration.yaml").read_text())
XREF = 3385


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
    pub = yaml.safe_load((ROOT / "data" / "e3-fps-published.yaml").read_text())
    fp = {r["location"]: r for r in pub["hpt"]["flowpath"]["stations"]}
    want = {
        ("stage1", "tip"): ("stage1_vane_exit", "stage1_blade_exit", "r_tip_cm"),
        ("stage1", "platform"): ("stage1_vane_exit", "stage1_blade_exit", "r_hub_cm"),
        ("stage2", "tip"): ("stage2_vane_exit", "stage2_blade_exit", "r_tip_cm"),
        ("stage2", "platform"): ("stage2_vane_exit", "stage2_blade_exit", "r_hub_cm"),
    }
    for (s, k), (lo, hi, col) in want.items():
        used = CAL["features"][s][k]["r_published_cm"]
        assert used == pytest.approx((fp[lo][col] + fp[hi][col]) / 2, abs=1e-9)


def test_figure_50_is_calibrated_on_the_same_anchors_as_figure_112():
    """the two calibrations must be comparable feature by feature, which
    they are only if they were fitted on identical published radii"""
    for s in ("stage1", "stage2"):
        for k in ("tip", "platform"):
            assert (CAL["features"][s][k]["r_published_cm"]
                    == CAL112["features"][s][k]["r_published_cm"])


# ------------------------------------------------------------ band E1, met

def test_e1_the_calibration_fits_its_own_anchors_to_the_band():
    assert CAL["calibration"]["rms_cm"] <= 0.25
    assert CAL["calibration"]["max_cm"] <= 0.25


def test_the_fit_reproduces_from_the_stored_pixels():
    Y, R = _anchors()
    coef = np.polyfit(Y, R, 1)
    assert coef[1] == pytest.approx(CAL["calibration"]["a"], abs=1e-6)
    assert coef[0] == pytest.approx(CAL["calibration"]["b"], abs=1e-9)


def test_the_smaller_drawing_fits_better_than_the_larger_one():
    """finding 278, the headline: Figure 50 is drawn 0.72x the size at the
    same line weight and fits TWICE as well. Step 0 predicted the opposite."""
    q = CAL["scale_relative_to_figure_112"]
    assert q["ratio"] < 0.80
    assert q["line_width_cm_fig50"] > q["line_width_cm_fig112"]
    assert CAL["calibration"]["rms_cm"] < 0.6 * CAL112["calibration"]["rms_cm"]


# --------------------------------- band E2r: the trick transfers, the gain does not

def test_e2r_the_two_caption_lines_agree():
    r = CAL["page_rotation"]
    assert r["spread_deg"] <= 0.15
    assert r["deg"] == pytest.approx(
        (r["baseline"]["deg"] + r["cap_height"]["deg"]) / 2, abs=1e-9)


def test_imposing_the_rotation_is_worth_nothing_on_this_page():
    """finding 279: the method transfers, its VALUE does not, because the
    value scales with the tilt and this page is tilted a quarter as far"""
    with_rot = CAL["calibration"]["rms_cm"]
    without = CAL["calibration_without_rotation"]["rms_cm"]
    assert without / with_rot == pytest.approx(1.0, abs=0.02)
    # Figure 112, same method, same author, same day: a factor of 4.9
    assert (CAL112["calibration_without_rotation"]["rms_cm"]
            / CAL112["calibration"]["rms_cm"]) > 4.0


def test_the_residual_angle_changes_sign_between_the_two_pages():
    """finding 279: E12 read Figure 112's excess as the draughtsman. On a
    second page the same quantity has the opposite sign, so it is not."""
    g50 = CAL["calibration_free_rotation"]["rot_deg"] - CAL["page_rotation"]["deg"]
    g112 = (CAL112["calibration_free_rotation"]["rot_deg"]
            - CAL112["page_rotation"]["deg"])
    assert g50 < 0 < g112


def test_the_anchor_rms_is_half_the_rotation_gaps_radial_reach():
    """finding 278: four anchors at two axial stations measure the page
    rotation and nothing else, so the rms is algebraically half the radial
    reach of the residual angle -- on BOTH pages, to three decimals."""
    for cal, xref in ((CAL, XREF), (CAL112, 2750)):
        xs = [cal["features"][s][k]["x_px"] for s in ("stage1", "stage2")
              for k in ("tip", "platform")]
        dx = max(xs) - min(xs)
        dtheta = abs(cal["calibration_free_rotation"]["rot_deg"]
                     - cal["calibration"]["rot_deg"])
        reach = math.tan(math.radians(dtheta)) * dx / cal["calibration"]["px_per_cm"]
        assert cal["calibration"]["rms_cm"] / reach == pytest.approx(0.5, abs=0.02)


def test_the_anchors_sit_at_only_two_axial_stations():
    """which is WHY the test above holds -- and the reason the anchor rms
    cannot be a test of anything but the rotation"""
    for cal in (CAL, CAL112):
        xs = {round(cal["features"][s][k]["x_px"], 3)
              for s in ("stage1", "stage2") for k in ("tip", "platform")}
        assert len(xs) == 2


# --------------------------------------------- the platform slope, pro-rated

def test_the_drawn_platform_slope_has_the_published_sign_on_both_blades():
    """what proves the line found is the flowpath hub and not the angel
    wing. The published fall is quoted across the whole blade and the drawn
    window is shorter, so it is pro-rated before comparison -- which unit
    E12 did not do."""
    for k, v in CAL["platform_slope_check"].items():
        assert v["drop_over_window_cm"] > 0, k
        assert v["published_drop_over_window_cm"] > 0, k
        assert abs(v["drop_over_window_cm"]
                   - v["published_drop_over_window_cm"]) <= 0.06, k
        assert v["window_cm"] < v["blade_axial_cm"], k


# ---------------------------------- bands E3r and E4r: the recorded FAILURES

def _cc():
    return [(k, v) for k, v in CAL["cross_check"].items() if k != "summary"]


def test_five_common_radii_were_measured_and_none_was_fitted_on():
    assert len(_cc()) == 5
    anchors = {CAL["features"][s][k]["r_published_cm"]
               for s in ("stage1", "stage2") for k in ("tip", "platform")}
    for _, v in _cc():
        assert v["fig112"]["r_cm"] < min(anchors), "must be BELOW the anchors"


def test_the_two_bolt_centrelines_do_meet_the_five_percent_band():
    for name in ("interstage_bolt_centreline", "aft_bolt_centreline"):
        assert abs(CAL["cross_check"][name]["difference_pct"]) <= 5.0, name


@pytest.mark.xfail(strict=True, reason="finding 280: recorded failure, not "
                   "widened. The three surfaces at the bottom of the rotor "
                   "disagree by 12-14 % between the two figures, against a "
                   "5 % band. The two bolt centrelines at r 17-20 cm do "
                   "meet it; the verdict splits by radius.")
def test_e3r_every_common_radius_agrees_to_five_percent():
    assert CAL["cross_check"]["summary"]["worst_pct"] <= 5.0


@pytest.mark.xfail(strict=True, reason="finding 280: recorded failure. Only "
                   "the interstage bolt centreline, the shallowest of the "
                   "five, agrees to 0.5 cm.")
def test_e4r_every_common_radius_agrees_to_half_a_centimetre():
    assert CAL["cross_check"]["summary"]["worst_cm"] <= 0.5


def test_the_disagreement_grows_as_the_radius_falls():
    """which is the signature of a SCALE difference and not an offset"""
    pairs = sorted((v["fig112"]["r_cm"], abs(v["difference_cm"]))
                   for _, v in _cc())
    assert pairs[0][1] > pairs[-1][1]
    diffs = [d for _, d in pairs]
    assert diffs == sorted(diffs, reverse=True)


def test_the_wall_thicknesses_agree_so_they_are_the_same_three_surfaces():
    """finding 281: a wall is a difference of two radii on one page, so the
    offset that dominates the radii cancels out of it. 0.95 cm apart in
    radius, under 0.05 cm apart in wall thickness."""
    cc = CAL["cross_check"]
    r50 = [cc[f"inner_surface_{i}"]["fig50"]["r_cm"] for i in (1, 2, 3)]
    r112 = [cc[f"inner_surface_{i}"]["fig112"]["r_cm"] for i in (1, 2, 3)]
    for i in (0, 1):
        g50, g112 = r50[i] - r50[i + 1], r112[i] - r112[i + 1]
        assert g50 > 0 and g112 > 0
        assert abs(g50 - g112) <= 0.05
    assert abs(r50[0] - r112[0]) > 0.8, "while the radii disagree by nearly 1 cm"


# ------------- what the two figures' own anchors could ever have detected

def _interval(cal, feats, xref, r_target, conf_t=4.302653):
    t = math.tan(math.radians(cal["rot_deg"]))
    Y, R = [], []
    for s in ("stage1", "stage2"):
        for k in ("tip", "platform"):
            f = feats[s][k]
            Y.append(f["y_px"] - t * (f["x_px"] - xref))
            R.append(f["r_published_cm"])
    Y, R = np.array(Y), np.array(R)
    n = len(Y)
    res = R - (cal["a"] + cal["b"] * Y)
    s2 = (res @ res) / (n - 2)
    y = (r_target - cal["a"]) / cal["b"]
    se = math.sqrt(s2 * (1 / n + (y - Y.mean()) ** 2 / ((Y - Y.mean()) ** 2).sum()))
    return conf_t * se


def test_every_disagreement_is_inside_the_combined_95_percent_interval():
    """finding 282: both readings are consistent everywhere. The bands fail
    on PRECISION, not on agreement, and that is a different verdict."""
    for name, v in _cc():
        i50 = _interval(CAL["calibration"], CAL["features"], XREF,
                        v["fig50"]["r_cm"])
        i112 = _interval(CAL112["calibration"], CAL112["features"], 2750,
                         v["fig112"]["r_cm"])
        assert abs(v["difference_cm"]) <= math.hypot(i50, i112), name


def test_the_implied_scale_difference_is_below_what_the_anchors_can_see():
    """finding 282: +3.1 % implied against +-6.1 % detectable at 95 %. No
    amount of care on either page could have found this."""
    import sys
    sys.path.insert(0, str(ROOT / "solvers"))
    from mechanical.hpt_disc import implied_scale_difference
    sd = implied_scale_difference()
    assert 2.0 <= abs(sd["implied_mean_pct"]) <= 5.0
    assert sd["combined_95_pct"] > abs(sd["implied_mean_pct"])
    assert sd["detectable"] is False


# ---------------------------------------------- the live rim, and what E2 is

def test_the_live_rim_is_below_the_platform_on_both_blades():
    """the line is the dovetail seat, so it must sit below the flowpath hub,
    and the three-tang blade's must sit deeper than the two-tang blade's"""
    lr = CAL["live_disc_rim"]
    for s in ("stage1", "stage2"):
        v = lr[s]
        assert 0.5 < v["shank_plus_dovetail_depth_cm"] < 5.0, s
        assert v["r_cm"] < v["platform_r_cm"], s
        assert v["rms_px"] < 2.0, s
    assert (lr["stage2"]["shank_plus_dovetail_depth_cm"]
            > lr["stage1"]["shank_plus_dovetail_depth_cm"])


@pytest.mark.xfail(strict=True, reason="finding 284: recorded failure. The "
                   "constant-thickness bracket at the measured rim and bore "
                   "is 770-1570 MPa, 2.04:1 wide, and contains Figure 64's "
                   "1034. The profile is what makes it wide; the bore is "
                   "worth 0.4 %.")
def test_e5r_the_disc_model_lands_within_ten_percent_of_figure_64():
    import sys
    sys.path.insert(0, str(ROOT / "solvers"))
    from mechanical.hpt_disc import bore_stress_bracket
    b = bore_stress_bracket()
    assert abs(b["upper_over_published"] - 1) <= 0.10


def test_the_bracket_contains_the_published_bore_stress():
    import sys
    sys.path.insert(0, str(ROOT / "solvers"))
    from mechanical.hpt_disc import bore_stress_bracket
    b = bore_stress_bracket()
    assert b["published_inside"]
    assert b["bracket_ratio"] > 1.8


def test_the_bore_radius_is_at_the_bottom_of_e2s_sensitivity_ladder():
    """finding 284: E2 has been gated on the bore since 2026-09-07. Across
    the entire disagreement between the two figures it is worth under 1 %,
    where the rim is worth 9 % and the profile 51 %."""
    import sys
    sys.path.insert(0, str(ROOT / "solvers"))
    from mechanical.hpt_disc import sensitivity_ladder
    lad = sensitivity_ladder()
    rows = {r["input"]: abs(r["change_pct"]) for r in lad["rows"]}
    bore = max(rows["bore radius, low end"], rows["bore radius, high end"])
    assert bore < 1.0
    assert rows["rim radius = the flowpath hub"] > 8.0
    assert rows["speed 13,300 rpm"] > 8.0
    assert lad["profile_effect_pct"] > 40.0
    assert lad["profile_effect_pct"] > 50 * bore


def test_the_published_target_is_read_from_the_yaml():
    """never hardcode a number that lives in the data files"""
    import sys
    sys.path.insert(0, str(ROOT / "solvers"))
    from mechanical.hpt_disc import published_fig64_bore_MPa
    m = yaml.safe_load((ROOT / "data" / "hpt-mechanical.yaml").read_text())
    pts = m["rotor_components"]["stage1_disk"]["stress_life_map"]["points"]
    (bore,) = [p for p in pts if p["where"] == "bore"]
    assert published_fig64_bore_MPa() == float(bore["MPa"])


# ------------------------------------------------------- D6 item 2

def test_the_disc_face_area_barely_notices_the_bore_disagreement():
    """finding 287: the warning was that a disc face is a radial extent from
    bore to rim and so lives in the bad half of the calibration. It does
    not: pi(b^2 - a^2) at a/b = 0.25 is 94 % rim."""
    import sys
    sys.path.insert(0, str(ROOT / "solvers"))
    from mechanical.hpt_disc import face_area_uncertainty
    fa = face_area_uncertainty()
    assert fa["bore_span_pct"] > 15.0
    assert abs(fa["stage1_area_span_pct"]) < 5.0
    assert abs(fa["stage1_area_span_pct"]) <= 20.0


def test_the_two_middle_disc_faces_do_not_cancel():
    """finding 289: the stage-1 rim is 30.77 cm and the stage-2 rim 27.88,
    so the forward disc presents 23 % more area to the same pressure"""
    import sys
    sys.path.insert(0, str(ROOT / "solvers"))
    from mechanical.hpt_disc import middle_faces
    mf = middle_faces()
    assert mf["stage1_aft_face_kN"] > 0 > mf["stage2_forward_face_kN"]
    assert mf["net_kN"] > 40.0
    # and it is a small difference of large numbers
    assert mf["net_kN"] < 0.25 * mf["stage1_aft_face_kN"]
    ks = [r["net_kN"] for r in mf["ratio_sweep"]]
    assert max(ks) - min(ks) > 20.0


def test_two_of_the_four_face_pressures_are_published_after_all():
    """finding 288: unit E14's own step 0 predicted no cavity pressure
    anywhere on the rotor was printed. CR-168211 Figure 210 p.348 plots two
    of them. The sixth occurrence of this error in the project."""
    import sys
    sys.path.insert(0, str(ROOT / "solvers"))
    from mechanical.hpt_disc import what_is_not_published
    n = what_is_not_published()
    assert "CR-168211" in n["published_after_all"]["where"]
    assert "Figure 210" in n["published_after_all"]["where"]
    # and every remaining absence names ONE quantity and its documents
    for e in n["still_not_found"]:
        assert e["quantity"].count(" and ") == 0 or "impeller" in e["quantity"]
        assert len(e["documents_searched"]) >= 5


def test_no_balance_piston_area_is_invented():
    """finding 191 stands: a good calibration is not a licence"""
    src = (ROOT / "solvers" / "mechanical" / "hpt_disc.py").read_text()
    assert "piston_area" not in src.replace("piston_area_given", "")
    import sys
    sys.path.insert(0, str(ROOT / "solvers"))
    from mechanical.hpt_disc import what_is_not_published
    q = [e["quantity"] for e in what_is_not_published()["still_not_found"]]
    assert any("balance-piston" in s for s in q)

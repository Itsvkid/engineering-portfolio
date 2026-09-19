"""Stage E unit E11: HPC Figure 30, calibrated on the annulus it is drawn
against, and the bore radius unit D6 was gated on.

The bands are solvers/mechanical/STEP0.md, unit E11. They were written
before the run and are not edited here; band 4 is a recorded miss and is
xfailed with its cause, not widened.

These tests never open the PDF. `tools/read_hpc_fig30.py` writes the pixel
coordinates it read into `data/hpc-disc-profile.yaml`, so every refit below
runs off the YAML."""
import math
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solvers"))

from mechanical import disc_profile as dp  # noqa: E402

P = dp.profile()


# ------------------------------------------------------ the transcription

def test_every_rotor_has_a_tip_and_a_root_and_the_bores_are_nine_not_ten():
    assert [t["stage"] for t in P["blade_tips"]] == list(range(1, 11))
    assert [t["stage"] for t in P["blade_roots"]] == list(range(1, 11))
    # stage 1 runs into the stub shaft and has no bore foot -- finding 262
    assert [b["stage"] for b in P["disc_bores"]] == list(range(2, 11))


def test_the_calibration_reproduces_the_published_radii_it_was_fitted_on():
    for row in P["blade_tips"] + P["blade_roots"]:
        assert abs(row["residual_cm"]) <= 0.10, row


def test_the_bores_are_below_every_hub_and_above_zero():
    hubs = {t["stage"]: t["published_cm"] for t in P["blade_roots"]}
    for b in P["disc_bores"]:
        assert 0 < b["r_calibrated_cm"] < hubs[b["stage"]]


def test_the_two_reading_routes_agree():
    """the fitted calibration against a depth below the PUBLISHED hub of the
    same stage, which uses the scale and not the intercept"""
    for b in P["disc_bores"]:
        assert abs(b["two_routes_differ_cm"]) <= 0.10, b


def test_the_bore_steps_once_and_it_steps_at_the_bolt_joint():
    """finding 261: two disc families, and the break is where the figure
    draws the one bolt joint"""
    r = {b["stage"]: b["r_calibrated_cm"] for b in P["disc_bores"]}
    fwd = [r[s] for s in (2, 3, 4)]
    aft = [r[s] for s in range(5, 11)]
    assert min(fwd) - max(aft) > 1.0          # a real step, not scatter
    assert max(fwd) - min(fwd) < 0.10         # each family is flat
    assert max(aft) - min(aft) < 0.10
    # the joint sits between rotor 4's trailing edge and rotor 5's
    assert 38.0 < P["bolt_joint"]["z_cm"] < 45.0


def test_the_cdp_seal_disc_is_the_deepest_bore_in_the_rotor():
    deepest = min(b["r_calibrated_cm"] for b in P["disc_bores"])
    assert P["cdp_seal_disc"]["r_bore_cm"] < deepest


# --------------------------------------------------------------- the bands

def test_band_1_held_out_five_stages_of_ten():
    h = dp.holdout(P)
    assert h["worst_rms_cm"] <= 0.12, h
    assert h["worst_max_cm"] <= 0.25, h


def test_band_2_the_rotation_is_stable_across_disjoint_halves():
    assert dp.holdout(P)["rotation_spread_deg"] <= 0.15


def test_band_3_one_scale_not_two():
    iso = dp.isotropy(P)
    assert abs(iso["isotropy_pct"]) <= 3.0


def test_the_apparent_anisotropy_is_the_rotation_finding_257():
    iso = dp.isotropy(P)
    # a tip-only calibration fits its own ten points beautifully ...
    assert iso["tip_only_shear_free"]["rms_cm"] < 0.05
    # ... and disagrees with the axial scale by the best part of ten percent
    assert abs(iso["apparent_anisotropy_pct"]) > 5.0
    # a shear-free fit forced onto all twenty costs a factor of three in rms
    assert iso["shear_free_costs_rms_x"] > 2.5
    # and the rotation buys it all back
    assert abs(iso["isotropy_pct"]) < 0.25 * abs(iso["apparent_anisotropy_pct"])


@pytest.mark.xfail(strict=True, reason=(
    "finding 258: recorded miss. The bore sits 10 cm below the calibration's "
    "lowest anchor, 64 % beyond its fitted span, and the four estimators give "
    "95 % widths of 0.27 / 0.38 / 0.40 / 0.61 cm against a band of 0.25. The "
    "band is not widened; the widest estimator is carried into D6, where it "
    "is worth 1.9 % of the answer (finding 259)."))
def test_band_4_the_bore_uncertainty():
    assert dp.bootstrap_bore(10, p=P)["width_cm"] <= 0.25


def test_band_4_every_estimator_agrees_that_it_misses():
    """a miss that one estimator disputed would be an estimator problem"""
    est = dp.bore_band(10, P)["estimators_width95_cm"]
    assert len(est) == 4
    assert all(v > 0.25 for v in est.values()), est


def test_band_5_per_disc_against_the_telescoped_form():
    v = dp.d6_verdict(P)
    for tag in ("lo", "mid", "hi"):
        assert 0.80 <= v[tag]["per_over_telescoped"] <= 1.10, v[tag]


def test_band_6_the_disc_face_term_still_dominates_and_still_pushes_forward():
    v = dp.d6_verdict(P)
    for tag in ("lo", "mid", "hi"):
        assert v[tag]["per_disc_N"] > 0
        assert 5.0 <= v[tag]["times_annulus"] <= 7.0, v[tag]
    assert v["annulus_hpc_N"] < 0          # unit D6 finding 192, unchanged


# ---------------------------------------------------------- what it means

def test_the_bore_band_is_worth_almost_nothing_to_d6():
    """finding 259: the gate was two wide because the bore was unknown over a
    safe range, not because it is uncertain"""
    v = dp.d6_verdict(P)
    assert v["swing_from_bore_pct"] < 5.0


def test_the_drum_makes_its_thrust_at_the_back():
    w = dp.where_the_thrust_is_made(P)
    assert w["rear_three_pct"] > 50
    assert w["forward_family_pct"] < 20
    assert math.isclose(w["total_N"], sum(r["forward_N"]
                                          for r in dp.disc_face_per_disc(P)))


def test_d6_is_still_gated_and_names_what_on():
    m = dp.still_missing()
    assert m["hpc_drum_disc_face"].startswith("CLOSED")
    for k in ("hpc_stage1_forward_face", "hpt_rotor_disc_faces",
              "balance_piston", "bearing_capacity"):
        assert len(m[k]) > 40
    assert "no longer the bore" in m["consequence"]


def test_the_closure_entry_says_the_gate_has_moved():
    import yaml
    c = yaml.safe_load((ROOT / "data" / "closures.yaml").read_text())
    d6 = next(x for x in c["closures"] if x["stage"] == "D6")
    assert d6["state"] == "gated"
    # the old gate must no longer be claimed
    assert "GATED on the HPC disc BORE RADIUS" not in d6["gate"]
    assert "balance piston" in d6["gate"].lower()


def test_the_data_file_is_generated_and_says_so():
    txt = (ROOT / "data" / "hpc-disc-profile.yaml").read_text()
    assert "tools/read_hpc_fig30.py" in txt
    assert P["meta"]["nothing_dimensioned_on_the_page"] is True

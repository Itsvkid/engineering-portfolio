"""Stage E unit E3: blade natural frequency
(solvers/mechanical/STEP0.md unit E3)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from mechanical.beam import (  # noqa: E402
    CLAMPED_CLAMPED, CLAMPED_FREE, CLAMPED_PINNED, exact, polygon_properties, uniform,
)
import mechanical.blade_frequency as BF  # noqa: E402
from mechanical.blade_frequency import (  # noqa: E402
    blades, fan_shroud_bracket, hpc_rotor_predictions, hpc_vane_check, southwell_table,
)

L, E, I, RHO, A = 0.5, 200e9, 1e-8, 8000.0, 1e-4
BEAM = uniform(L, E, I, RHO, A)
BY = {b.name: b for b in blades()}
SW = {r["name"]: r for r in southwell_table()}


# --- the beam, against closed form: METHOD.md's "a cantilever beam first" --

@pytest.mark.parametrize("bl,kw", [
    (CLAMPED_FREE, {}),
    (CLAMPED_PINNED, {"pinned_at": 1.0}),
    (CLAMPED_CLAMPED, {"tip_clamped": True}),
])
def test_the_beam_reproduces_the_closed_form_eigenvalues(bl, kw):
    got = BEAM.frequencies(3, **kw)
    for g, b in zip(got, bl):
        assert abs(g / exact(b, L, E, I, RHO, A) - 1) < 0.005      # the +-0.5 % band


def test_the_geometric_stiffness_gives_the_standard_southwell_coefficient():
    """1.19 for a uniform cantilever at zero hub radius -- this validates
    the centrifugal term without reference to any blade"""
    s, _, _ = BEAM.southwell(0.15 * BEAM.frequencies(1)[0] * 2 * math.pi)
    assert abs(s / 1.19 - 1) < 0.05


def test_the_southwell_coefficient_grows_linearly_with_hub_radius():
    """S = 1.193 + 1.571 (R/L): a stubby blade on a big drum stiffens far
    more than the textbook case"""
    ss = []
    for rl in (0.0, 0.5, 1.0, 2.0):
        b = uniform(L, E, I, RHO, A, hub_radius=rl * L)
        ss.append(b.southwell(0.15 * b.frequencies(1)[0] * 2 * math.pi)[0])
    slopes = [(ss[i + 1] - ss[i]) / (0.5 if i == 0 else (0.5 if i == 1 else 1.0))
              for i in range(3)]
    for sl in slopes:
        assert abs(sl - math.pi / 2) < 0.01


# --- section properties, exactly ------------------------------------------

def test_polygon_properties_are_exact_on_a_rectangle():
    b, h = 3.0, 1.0
    p = polygon_properties([(0, 0), (b, 0), (b, h), (0, h)])
    assert abs(p["area"] - b * h) < 1e-12
    assert abs(p["ixx"] - b * h ** 3 / 12) < 1e-12
    assert abs(p["iyy"] - h * b ** 3 / 12) < 1e-12
    assert abs(p["ixy"]) < 1e-12
    assert abs(p["i_min"] - b * h ** 3 / 12) < 1e-12


def test_polygon_properties_are_exact_on_an_ellipse():
    a, b, n = 2.0, 0.5, 4000
    pts = [(a * math.cos(2 * math.pi * k / n), b * math.sin(2 * math.pi * k / n))
           for k in range(n)]
    p = polygon_properties(pts)
    assert abs(p["area"] / (math.pi * a * b) - 1) < 1e-5
    assert abs(p["ixx"] / (math.pi * a * b ** 3 / 4) - 1) < 1e-5
    assert abs(p["iyy"] / (math.pi * b * a ** 3 / 4) - 1) < 1e-5


def test_the_polygon_winding_direction_does_not_matter():
    pts = [(0, 0), (3, 0), (3, 1), (0, 1)]
    a = polygon_properties(pts)
    b = polygon_properties(list(reversed(pts)))
    for k in ("area", "ixx", "iyy", "i_min"):
        assert abs(a[k] - b[k]) < 1e-12


# --- the E3 blades ---------------------------------------------------------

def test_each_blade_gets_the_tip_condition_its_own_report_names():
    """finding 83"""
    assert BY["LPT stage 1"].pinned_at == 1.0          # Fig 62: "pinned-tip"
    assert BY["booster rotor"].pinned_at is None       # unshrouded
    assert BY["fan rotor"].pinned_at is None           # part-span shroud, not a tip


def test_the_unshrouded_booster_blade_is_a_beam_to_under_one_percent():
    """finding 82 as RESTATED 2026-09-18 on Appendix D's printed sections.

    The read-off geometry gave 243 Hz against a published 250, -2.7 %, and
    250 sat strictly inside the weak-axis/root-axis twist bracket. On the
    printed sections the beam gives 250.68, +0.27 %, and the published
    value now sits 0.68 Hz BELOW the bracket's soft end.

    That is the bracket collapsing onto the answer, not a miss. The bracket
    is 46 % wide and the agreement is 0.27 %, so "inside the bracket" was
    never what carried this result -- the number was. This test therefore
    asserts the number, and asserts only the half of the bracket claim that
    still means something: the published value is below the root-axis end,
    so the blade is not behaving as though forced to bend about one axis."""
    b = BY["booster rotor"]
    soft, stiff = b.bracket(0.0, 1)
    err = soft[0] / b.published_f1_Hz - 1
    assert abs(err) < 0.15                      # the band stated in step 0
    assert abs(err) < 0.01                      # and in fact 0.27 %
    assert b.published_f1_Hz < stiff[0]         # still below the stiff end
    # and the soft end is now ABOVE the published value, which is the part
    # of finding 82's old form that was withdrawn. Asserted so that a
    # future change moving it back is visible rather than silent.
    assert soft[0] > b.published_f1_Hz


def test_the_fan_brackets_now_overlap_so_the_boundary_condition_is_not_resolved():
    """finding 83 as RESTATED 2026-09-18, and finding 228.

    The old form asserted that the published 80 Hz sits inside the free
    bracket AND below the shroud-pinned floor, which was the evidence that
    the lowest in-phase mode barely feels the part-span shroud. Finding
    226's span correction took the fan blade from 62.14 cm to 69.34 cm --
    the read-off spanned Fig 15's stacking-axis box, Appendix B spans the
    annulus -- and a longer blade is softer, so BOTH brackets fell: free
    43-89 to 36.1-102.7, pinned 84-587 to 73.1-652.5.

    They now overlap, and the published value lies in the overlap. The
    comparison cannot distinguish the two boundary conditions any more.
    That is asserted here as the current truth, with the diagnosis, rather
    than left as a failure whose reason decays -- and it is written as a
    CONVERSE so that recovering the discrimination breaks this test and
    forces finding 83 to be restated again."""
    fb = fan_shroud_bracket()
    assert abs(fb["shroud_span"] - 0.55) < 1e-9
    # what survives: the published mode is still inside the free bracket
    assert fb["free"][0] < fb["published"] < fb["free"][1]
    # what is withdrawn: it is inside the shrouded bracket too
    assert fb["pinned"][0] < fb["published"] < fb["pinned"][1]
    # and the brackets themselves overlap, which is WHY the test cannot
    # discriminate. This is the diagnosis, and it is the thing to fix.
    assert fb["pinned"][0] < fb["free"][1], (
        "the brackets no longer overlap -- the boundary condition is "
        "resolvable again and finding 83 needs restating")


def test_the_fan_part_span_shrouds_mass_is_not_the_missing_physics():
    """finding 228 -- the restraint is worth about 90x the mass.

    E7's flutter miss was attributed to a beam pinning a tip shroud without
    its mass. That diagnosis is right for the LPT and does not transfer to
    the fan, and the fan's own printed shroud dimensions settle it rather
    than leaving it an opinion."""
    f = BF._fan()
    sh_a = f["fan_rotor_airfoil"]["shroud"]
    sh_m = f["fan_rotor_mechanical"]["shroud"]
    base, _ = BF.fan_rotor()
    span = sh_m["span_pct"] / 100
    pitch = 2 * math.pi * (base.hub_radius_m + span * base.length_m) / 32
    mass = pitch * (sh_m["length_cm"] / 100) * (sh_a["thickness_cm"] / 100) * base.rho
    assert 0.25 < mass < 0.40                      # 287-365 g, elliptical to rectangular

    f0 = base.modes(False, 0.0, 1)[0]
    m2, _ = BF.fan_rotor()
    i = min(range(len(m2.x)), key=lambda j: abs(m2.x[j] - span * m2.length_m))
    h = ((m2.x[i] - m2.x[i - 1]) + (m2.x[i + 1] - m2.x[i])) / 2
    m2.area = list(m2.area)
    m2.area[i] += mass / (m2.rho * h)
    with_mass = m2.modes(False, 0.0, 1)[0]

    base.pinned_at = span
    restrained = base.modes(False, 0.0, 1)[0]
    base.pinned_at = None

    d_mass = abs(with_mass / f0 - 1)
    d_restraint = abs(restrained / f0 - 1)
    assert d_mass < 0.02, d_mass                   # about 1 %
    assert d_restraint > 0.9, d_restraint          # about 100 %
    assert d_restraint / d_mass > 50


def test_the_pinned_tip_lpt_blade_misses_and_the_miss_is_recorded():
    """finding 84 -- +45 %, and no modulus was chosen to hide it"""
    b = BY["LPT stage 1"]
    soft = b.modes(False, 0.0, 1)[0]
    err = soft / b.published_f1_Hz - 1
    assert err > 0.15                                    # outside the stated band
    assert 0.40 < err < 0.50
    needed_E = b.e_pa * (b.published_f1_Hz / soft) ** 2
    assert 0.45 < needed_E / b.e_pa < 0.50               # a 53 % modulus loss


def test_the_centrifugal_stiffening_is_under_predicted_on_both_free_blades():
    """finding 85 -- both miss the +-25 % band, and both the same way"""
    for name in ("booster rotor", "fan rotor"):
        r = SW[name]
        assert r["s_model"] < r["s_published"]
        assert 0.25 < abs(r["err_pct"]) / 100 < 0.45


def test_a_pinned_tip_blades_frequency_falls_with_speed():
    """finding 86 -- no tension model can give a negative Southwell
    coefficient; the published LPT curve has one"""
    r = SW["LPT stage 1"]
    assert r["s_published"] < 0
    assert r["fN_pub"] < r["f0_pub"]
    assert r["s_model"] > 0


# --- the HPC: one comparison possible, ten gated ---------------------------

def test_both_published_hpc_vanes_sit_inside_the_bracket():
    """finding 87"""
    rows = hpc_vane_check()
    assert len(rows) == 2
    for r in rows:
        assert r["inside"]
        assert r["cantilever"][1] < r["published"] < r["built_in"][1]


def test_the_two_hpc_vanes_agree_on_the_same_restraint_fraction():
    """finding 87 -- a real inner band, the same design on both stages"""
    fracs = [r["published"] / r["built_in"][0] for r in hpc_vane_check()]
    assert all(0.55 < f < 0.80 for f in fracs)
    assert abs(fracs[0] - fracs[1]) < 0.10


def test_the_ten_hpc_rotors_are_predicted_and_carry_e1s_material_split():
    """finding 88 -- recorded so the gate is a comparison, not a rebuild"""
    rows = hpc_rotor_predictions()
    assert len(rows) == 10
    assert [r["material"] for r in rows] == ["Ti-6Al-4V"] * 4 + ["nickel"] * 6
    f1 = [r["modes"][0] for r in rows]
    assert 350 < f1[0] < 500
    assert 3500 < f1[-1] < 4500
    assert f1[-1] > f1[0]                       # blades get shorter and stiffer aft
    for r in rows:                              # three modes, ordered
        assert r["modes"] == sorted(r["modes"])


def test_e3s_stated_closure_is_gated_not_claimed():
    """the ten HPC rotor Campbell diagrams were never transcribed"""
    import yaml
    data = pathlib.Path(__file__).resolve().parents[1] / "data"
    status = yaml.safe_load((data / "hpc-mechanical.yaml").read_text())["meta"]["status"]
    assert "figure-status" in status and "33-54" in status
    for r in hpc_rotor_predictions():
        assert "published" not in r             # nothing to compare against


# --- E3's closure, no longer gated -----------------------------------------

def test_all_ten_campbell_diagrams_are_transcribed():
    """the gate that stood since Stage A"""
    import yaml
    data = pathlib.Path(__file__).resolve().parents[1] / "data"
    d = yaml.safe_load((data / "hpc-rotor-campbell.yaml").read_text())
    assert len(d["stages"]) == 10
    assert [s["figure"] for s in d["stages"]] == list(range(33, 43))
    for s in d["stages"]:
        assert s["modes"]["first_flex"] > 0
        assert s["modes"]["first_torsion"] > s["modes"]["first_flex"]
    assert "reading_uncertainty" in d["meta"]


def test_the_first_flex_frequency_rises_monotonically_with_stage():
    """short stiff rear blades ring higher; a transcription slip would break it"""
    import yaml
    data = pathlib.Path(__file__).resolve().parents[1] / "data"
    d = yaml.safe_load((data / "hpc-rotor-campbell.yaml").read_text())
    f = [s["modes"]["first_flex"] for s in d["stages"]]
    assert f == sorted(f)
    assert f[-1] / f[0] > 8


def test_e3s_closure_is_evaluated_and_fails():
    """finding 143 -- 1 of 24 inside a 5 % band. The band was written
    before the model existed and the predictions before the diagrams were
    read; neither was moved."""
    from mechanical.blade_frequency import hpc_campbell_summary
    s = hpc_campbell_summary()
    assert s["comparisons"] == 24
    assert s["within_5pct"] <= 2
    assert s["mean"] > 15.0


def test_the_bias_is_a_bias_not_scatter():
    """finding 143 -- first flex over-predicted on nine stages of ten"""
    from mechanical.blade_frequency import hpc_campbell_comparison
    first = [m["err_pct"] for r in hpc_campbell_comparison()
             for m in r["modes"] if m["mode"] == "1F"]
    assert len(first) == 10
    assert sum(1 for e in first if e > 0) >= 9
    assert 10 < sum(first) / len(first) < 25


def test_the_error_grows_with_mode_number():
    """finding 144 -- a soft root removes more from a high mode than a low
    one; a material or area error would scale every mode alike"""
    from mechanical.blade_frequency import hpc_campbell_comparison
    rows = hpc_campbell_comparison()
    by = {n: [m["err_pct"] for r in rows for m in r["modes"]
              if m["mode"] == n and m["err_pct"] is not None] for n in ("1F", "2F", "3F")}
    mean = {k: sum(v) / len(v) for k, v in by.items()}
    assert mean["1F"] < mean["2F"] < mean["3F"]

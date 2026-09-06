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


def test_the_unshrouded_booster_blade_is_a_beam_to_three_percent():
    """finding 82 -- the result that licenses the other three"""
    b = BY["booster rotor"]
    soft, stiff = b.bracket(0.0, 1)
    assert abs(soft[0] / b.published_f1_Hz - 1) < 0.15      # the stated +-15 %
    assert abs(soft[0] / b.published_f1_Hz - 1) < 0.05      # and in fact 2.7 %
    assert soft[0] < b.published_f1_Hz < stiff[0]           # inside the twist bracket


def test_the_fan_blade_sits_inside_the_free_bracket_not_the_shrouded_one():
    """finding 83 -- the lowest in-phase mode barely feels the part-span shroud"""
    fb = fan_shroud_bracket()
    assert fb["free"][0] < fb["published"] < fb["free"][1]
    assert fb["published"] < fb["pinned"][0]
    assert abs(fb["shroud_span"] - 0.55) < 1e-9


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

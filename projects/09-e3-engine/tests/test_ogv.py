"""Stage G unit G2: the swept and leaned inner OGV
(solvers/geometry/STEP0.md unit G2)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
pytest.importorskip("cadquery")

import geometry.ogv as ogv  # noqa: E402
from geometry.ogv import (  # noqa: E402
    LEAN_ID_DEG, LEAN_OD_DEG, SWEEP_DEG, aspect_ratios, lean_deg, placement,
    radial_span_m, sections, solid, stacking_axis, swept_span_reading,
    table_vii, trapezoid_volume,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
T = table_vii()
AXIS = stacking_axis()


# --- the published row ---------------------------------------------------

def test_table_vii_gives_the_row_completely():
    for k in ("vanes", "length_cm", "chord_root_cm", "chord_tip_cm",
              "tm_c_root", "tm_c_tip", "stagger_root_deg", "stagger_tip_deg",
              "camber_root_deg", "camber_tip_deg"):
        assert T[k] is not None, k
    assert T["vanes"] == 64


def test_the_booster_has_no_published_sweep_or_lean():
    """finding 180: the plan line conflated two rows"""
    import yaml
    d = yaml.safe_load((ROOT / "data/fan-design.yaml").read_text())
    b = d["booster_rotor_airfoil"]
    blob = str(b).lower()
    assert "sweep" not in blob and "lean" not in blob
    # and the OGV does have them
    assert "swept aft 60" in d["inner_ogv_airfoil"]["blade_axis"]


# --- the stacking axis ---------------------------------------------------

def test_the_sweep_and_lean_are_the_published_angles():
    assert SWEEP_DEG == 60.0
    assert (LEAN_ID_DEG, LEAN_OD_DEG) == (20.0, 0.0)


def test_lean_falls_from_the_id_to_zero_at_the_od():
    assert lean_deg(0.0) == pytest.approx(20.0)
    assert lean_deg(1.0) == pytest.approx(0.0)
    assert lean_deg(0.5) == pytest.approx(10.0)


def test_the_axis_sweeps_aft_by_the_published_angle():
    """dz/dr = tan(60 deg) over the span"""
    dz = AXIS[-1]["z"] - AXIS[0]["z"]
    dr = AXIS[-1]["r"] - AXIS[0]["r"]
    assert dz / dr == pytest.approx(math.tan(math.radians(60.0)), rel=1e-6)


def test_the_axis_leans_one_way_and_flattens_at_the_od():
    """pressure side towards the axis, and lean drops to zero at the OD"""
    ys = [p["y"] for p in AXIS]
    assert all(b <= a for a, b in zip(ys, ys[1:]))     # monotone, one sign
    assert ys[-1] < 0
    last = AXIS[-1]["y"] - AXIS[-2]["y"]
    first = AXIS[1]["y"] - AXIS[0]["y"]
    assert abs(last) < abs(first) / 5                  # flattens


def test_the_axis_leaves_the_meridional_plane():
    """which is what makes this row need its own module"""
    assert abs(AXIS[-1]["y"]) > 0.01


# --- sections normal to the axis: construction, not tolerance -----------

def test_every_section_plane_is_normal_to_the_local_tangent():
    for s in sections():
        n = s["plane"].zDir
        t = s["axis_point"]["tangent"]
        dot = abs(n.x * t[0] + n.y * t[1] + n.z * t[2])
        assert dot == pytest.approx(1.0, abs=1e-9), s["f"]


def test_the_sections_are_not_on_cylinders():
    """the distinction from every other row in the project: `wrapped_wire`
    lays a section onto a cylinder, which is right for a radial stack and
    wrong for this one"""
    import geometry.ogv as m
    src = (ROOT / "solvers/geometry/ogv.py").read_text()
    body = src.split("STEP0.md, unit G2.")[1]
    assert "wrapped_wire" not in body      # the cylindrical construction
    # and the planes really are built from the tangent, not from a radius
    import inspect
    assert "tangent" in inspect.getsource(m._plane_at)
    assert "normal=normal" in inspect.getsource(m._plane_at)


# --- the solid ------------------------------------------------------------

def test_the_vane_is_a_valid_solid():
    assert solid(13).isValid()


def test_sixty_four_vanes_do_not_touch():
    s = solid(13)
    nxt = s.rotate((0, 0, 0), (1, 0, 0), 360.0 / T["vanes"])
    common = s.intersect(nxt)
    vol = 0.0 if common is None or not common.Solids() else common.Volume()
    assert vol == 0.0


def test_the_volume_misses_the_band_by_a_whisker():
    """closure as stated: -2.09 % against +-2 %"""
    err = (solid(13).Volume() / trapezoid_volume() - 1) * 100
    assert err == pytest.approx(-2.09, abs=0.15)
    assert abs(err) > 2.0          # it really is a miss


def test_the_miss_is_the_reference_and_not_the_cad():
    """finding 181: straighten the axis and the same pair agree to 0.015 %"""
    lean = ogv.LEAN_ID_DEG
    try:
        ogv.LEAN_ID_DEG = 0.0            # constant sweep -> straight axis
        err = (ogv.solid(13).Volume() / ogv.trapezoid_volume() - 1) * 100
        assert abs(err) < 0.1, err
    finally:
        ogv.LEAN_ID_DEG = lean


def test_the_curvature_error_grows_when_the_sweep_is_removed():
    """the Pappus term is largest when the axis curves most"""
    sw = ogv.SWEEP_DEG
    try:
        ogv.SWEEP_DEG = 0.0
        err = (ogv.solid(13).Volume() / ogv.trapezoid_volume() - 1) * 100
        assert err < -5.0, err
    finally:
        ogv.SWEEP_DEG = sw


# --- what the geometry says about the published numbers ------------------

def test_table_vii_reproduces_its_own_aspect_ratio_on_one_row_of_three():
    a = {r["row"]: r for r in aspect_ratios()}
    assert abs(a["stage_1"]["err_pct"]) < 0.5
    assert abs(a["inner_ogv"]["err_pct"]) > 10
    assert abs(a["bypass"]["err_pct"]) > 40


def test_the_other_reading_of_length_is_reported_not_adopted():
    """finding 182"""
    sw = swept_span_reading()
    assert sw["adopted"] is False
    assert sw["ar_on_radial"] == pytest.approx(0.79, abs=0.02)
    assert sw["appendix_a_ar"] == 0.83
    assert ogv.LENGTH_IS_ALONG_AXIS is False
    assert radial_span_m() == pytest.approx(T["length_cm"] / 100)


def test_the_vane_overhangs_the_assumed_hub_on_either_reading():
    """finding 183: it must be endwall-trimmed, as Rotor 37's blade was"""
    hub = placement()["hub_radius_m"]
    s = solid(13)
    rs = [math.hypot(v.Y, v.Z) for v in s.Vertices()]
    assert min(rs) < hub - 0.03


# --- the placement assumption lives in data/ ----------------------------

def test_the_hub_radius_is_an_assumption_recorded_in_data():
    """finding 159's rule, applied to a second assumption"""
    p = placement()
    assert p["status"] == "assumed"
    assert p["range_m"][0] < p["hub_radius_m"] < p["range_m"][1]
    assert "flowpath.js" in p["src"]
    src = (ROOT / "solvers/geometry/ogv.py").read_text()
    assert "0.49" not in src           # no second copy here

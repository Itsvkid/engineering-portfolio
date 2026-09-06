"""C3 unit 12: HPC sections reconstructed from Table XXII, and their
throats (solvers/blading/STEP0.md unit 12)."""
import math
import pathlib
import statistics
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from blading.sections import (  # noqa: E402
    area_ratio, implied_max_camber, load, normal_shock, rotor_throat_margins, section, throat,
)

XXII, XXI = load()
COLS = XXII["columns"]
MARGINS = rotor_throat_margins(step=2)


def _rows(kind):
    key = {"rotor": "rotors", "stator": "stators"}[kind]
    return [dict(zip(COLS, raw)) for blk in XXII[key] for raw in blk["sections"]]


def test_isentropic_and_shock_relations():
    assert abs(area_ratio(1.0) - 1.0) < 1e-9
    assert area_ratio(0.5) > 1.3 and area_ratio(1.5) > 1.1
    m2, p0 = normal_shock(1.5)
    assert 0.69 < m2 < 0.71 and 0.92 < p0 < 0.94
    assert normal_shock(1.0)[1] > 0.9999


def test_a_section_reproduces_its_printed_angles_by_construction():
    """the camber line is built to hit beta1*, beta2* and the stagger"""
    r = _rows("rotor")[40]
    sec = section(r["chord_cm"] / 100, r["beta1"], r["beta2"], r["stagger"],
                  r["tm_c"], r["pct_c_tm"], r["tte_c"])
    cam = sec["camber"]
    lead = math.degrees(math.atan2(cam[2][1] - cam[0][1], cam[2][0] - cam[0][0]))
    trail = math.degrees(math.atan2(cam[-1][1] - cam[-3][1], cam[-1][0] - cam[-3][0]))
    chordline = math.degrees(math.atan2(cam[-1][1] - cam[0][1], cam[-1][0] - cam[0][0]))
    assert abs(chordline - r["stagger"]) < 0.5
    assert abs(lead - r["beta1"]) < 1.5
    assert abs(trail - r["beta2"]) < 1.5


def test_throat_margin_of_the_transonic_rotors():
    """finding 42: the report states 6 percent for rotors 1-4"""
    tr = [r["margin"] * 100 for r in MARGINS if r["transonic"]]
    assert abs(statistics.median(tr) - 6.0) < 4.0


def test_the_margin_falls_monotonically_toward_the_front():
    by_stage = {}
    for r in MARGINS:
        by_stage.setdefault(r["stage"], []).append(r["margin"] * 100)
    med = [statistics.median(by_stage[s]) for s in sorted(by_stage)]
    assert med[0] < 5 and med[-1] > 20
    # broadly increasing rearward: no stage more than 2 points below its predecessor
    assert all(med[i + 1] > med[i] - 2.0 for i in range(len(med) - 1))


def test_the_constraint_binds_only_where_the_flow_is_transonic():
    sup = [r["margin"] * 100 for r in MARGINS if r["m_rel"] > 1.0]
    sub = [r["margin"] * 100 for r in MARGINS if r["m_rel"] < 0.8]
    assert statistics.median(sup) < 5.0
    assert statistics.median(sub) > 3 * statistics.median(sup)


def test_stators_are_circular_arc_and_rotors_are_not():
    """finding 43"""
    for kind, lo, hi in (("stator", 44, 54), ("rotor", 52, 60)):
        f = [implied_max_camber(r["beta1"], r["beta2"], r["stagger"]) for r in _rows(kind)]
        f = [x * 100 for x in f if x is not None]
        assert lo < statistics.median(f) < hi, (kind, statistics.median(f))
    ds = [r["stagger"] - 0.5 * (r["beta1"] + r["beta2"]) for r in _rows("stator")]
    dr = [r["stagger"] - 0.5 * (r["beta1"] + r["beta2"]) for r in _rows("rotor")]
    assert statistics.mean(ds) < 0 < statistics.mean(dr)


def test_the_inference_is_ill_conditioned_at_low_camber():
    """finding 44: sensitivity is 1/camber, so report but do not trust the
    low-camber transonic tips"""
    rows = _rows("rotor")
    low = [r for r in rows if r["camber"] < 10]
    f = [implied_max_camber(r["beta1"], r["beta2"], r["stagger"]) * 100 for r in low]
    assert max(f) > 80
    # a half-degree of stagger moves it by about 100/(2*camber) percent
    r = min(low, key=lambda x: x["camber"])
    a = implied_max_camber(r["beta1"], r["beta2"], r["stagger"])
    b = implied_max_camber(r["beta1"], r["beta2"], r["stagger"] + 0.5)
    assert abs(b - a) * 100 > 3.0


@pytest.mark.xfail(strict=True, reason="unit 12 finding 45: the IGV is an accelerating vane with an axial inlet; the double-circular-arc model built for the diffusing rows returns a max camber at 98-100 % of chord, which is not a blade")
def test_igv_fits_the_same_camber_family():
    f = [implied_max_camber(*[dict(zip(COLS, raw))[k] for k in ("beta1", "beta2", "stagger")])
         for raw in XXII["igv"]["sections"]]
    assert all(0.3 < x < 0.7 for x in f if x is not None)


def test_igv_departure_is_pinned():
    f = [implied_max_camber(*[dict(zip(COLS, raw))[k] for k in ("beta1", "beta2", "stagger")])
         for raw in XXII["igv"]["sections"]]
    assert all(x > 0.95 for x in f if x is not None)

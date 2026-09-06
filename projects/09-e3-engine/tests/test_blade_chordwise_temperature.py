"""Stage D unit D2: the stage-1 blade's chordwise metal temperature
(solvers/thermal/STEP0.md unit D2). The band is the work plan's own D1
closure: +-25 K at three chordwise points with the published cooling flow."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from thermal.cooling import (  # noqa: E402
    LE_FILM_HOLES, blade_conditions, film_effectiveness_needed,
    fit_internal_conductance, predict_chordwise, stage1_blade_stations,
)

STATIONS = stage1_blade_stations()
FIT = fit_internal_conductance()
PRED, H_C = predict_chordwise()
BY = {p["name"]: p for p in PRED}
BAND_K = 25.0


def test_the_external_coefficient_comes_from_the_figure():
    """Fig 23: a stagnation peak near 9500 falling to 4600 on the suction side"""
    h = {s.name: s.h_gas for s in STATIONS}
    assert abs(h["leading edge"] - 9500) < 100
    assert 4500 < h["suction surface"] < 5100
    assert h["leading edge"] > h["midchord"] > h["suction surface"]


def test_only_one_parameter_is_fitted():
    assert 1000 < FIT["H_c"] < 20000          # physical
    assert FIT["spread_pct"] < 30             # a single value describes all three


@pytest.mark.parametrize("name", ["suction surface", "midchord"])
def test_the_unfilmed_stations_land_inside_the_band(name):
    """finding 61"""
    assert abs(BY[name]["error_K"]) < BAND_K
    assert abs(BY[name]["error_K"]) < 10


@pytest.mark.xfail(strict=True, reason="unit D2 finding 62: the leading edge misses by 31 K because the model has no film cooling, and the leading edge is where the blade's showerhead is -- three rows of ten holes at 0.49 % W25")
def test_the_leading_edge_lands_inside_the_band():
    assert abs(BY["leading edge"]["error_K"]) < BAND_K


def test_the_leading_edge_miss_is_pinned_and_is_positive():
    """positive: the no-film model predicts the metal HOTTER than published,
    which is the direction film cooling would fix"""
    assert 20 < BY["leading edge"]["error_K"] < 45


def test_the_implied_film_effectiveness_is_where_the_film_holes_are():
    """finding 62: 0.064 at the leading edge, essentially zero elsewhere"""
    eta = {s.name: film_effectiveness_needed(s) for s in STATIONS}
    assert 0.03 < eta["leading edge"] < 0.12
    assert abs(eta["suction surface"]) < 0.03
    assert abs(eta["midchord"]) < 0.03
    assert eta["leading edge"] > 3 * max(abs(eta["suction surface"]), abs(eta["midchord"]))
    assert LE_FILM_HOLES["rows"] == 3 and LE_FILM_HOLES["pct_w25"] == 0.49


def test_the_internal_conductance_is_the_right_order():
    """finding 63: comparable with the external coefficient, which is why
    the local effectiveness sits near 0.4-0.5"""
    t_g, t_c, _ = blade_conditions()
    for s in STATIONS:
        ratio = FIT["H_c"] / s.h_gas
        assert 0.4 < ratio < 1.5
    phi_le = (t_g - BY["leading edge"]["published_C"]) / (t_g - t_c)
    assert 0.38 < phi_le < 0.45


def test_the_published_cooling_flow_is_used_not_a_tuned_one():
    from thermal.cooling import load
    assert load()["stage1_blade"]["metal_temperatures"]["conditions"]["w_coolant_pct_w25"] == 3.3

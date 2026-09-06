"""Stage B cycle solver against STEP0.md: gas validation, the three Table
XII ratings, the mixer, and the two-route checks. Bands were written in
STEP0.md before the first run and are not widened here; a miss is an
xfail with its finding."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from e3cycle import gas  # noqa: E402
from e3cycle.cycle import isa, load_inputs, run_all, solve  # noqa: E402

INP = load_inputs()
RESULTS = {r.rating: r for r in run_all(INP)}
SFC_BAND = 0.015


@pytest.mark.parametrize("t, far, ref, band", [(288.15, 0.0, 1.005, 0.005), (1500.0, 0.0, 1.216, 0.005), (1500.0, 0.02, 1.285, 0.01), (800.0, 0.0, 1.099, 0.005)])
def test_gas_cp(t, far, ref, band):
    assert abs(gas.cp(t, far) / 1000 / ref - 1) < band


def test_gas_consistency():
    assert gas.h(gas.T_REF) == 0.0 and gas.phi(gas.T_REF) == 0.0
    for t in (300.0, 900.0, 1700.0):
        assert abs(gas.t_from_h(gas.h(t, 0.02), 0.02) - t) < 1e-3
        assert abs(gas.t_from_phi(gas.phi(t), 0.0) - t) < 1e-3
    # eta = 1 compression is isentropic: phi2 - phi1 = R ln pr
    t2, p2 = gas.compress(300.0, 1e5, 20.0, 1.0)
    assert abs((gas.phi(t2) - gas.phi(300.0)) - gas.R_AIR * math.log(20.0)) < 1e-3
    # numerical derivative of h is cp
    assert abs((gas.h(1000.5) - gas.h(999.5)) - gas.cp(1000.0)) < 0.05


def test_isa_35000_ft():
    t, p = isa(10668.0)
    assert abs(t - 218.8) < 0.1 and abs(p / 23842 - 1) < 0.002


@pytest.mark.parametrize("rating", ["max_climb", "max_cruise"])
def test_sfc_within_band(rating):
    r = RESULTS[rating]
    assert abs(r.sfc_kg_N_h / r.sfc_published - 1) < SFC_BAND


@pytest.mark.xfail(strict=True, reason="STEP0 finding 2: takeoff is +1.9 percent -- Table XII's sfc is standard day, its T41 the +15 C flat-rating day; the constant-thrust day shift needs the maps (Stage C)")
def test_sfc_takeoff_within_band():
    r = RESULTS["takeoff"]
    assert abs(r.sfc_kg_N_h / r.sfc_published - 1) < SFC_BAND


def test_sfc_miss_is_pinned():
    """the size of the takeoff miss is recorded, so a change is noticed"""
    r = RESULTS["takeoff"]
    assert 0.015 < r.sfc_kg_N_h / r.sfc_published - 1 < 0.025


def _mixer_gain(eff, loss):
    """sfc gain of a mixer of effectiveness `eff` and pressure loss `loss`
    over the separate-flow engine without that loss (STEP0 assumption 6)"""
    mc = next(r for r in INP.ratings if r.name == "max_cruise")
    sep = solve(mc, INP, mixed=False, extra_loss=-loss)
    return (1 - solve(mc, INP, mixer_eff=eff).sfc_kg_N_h / sep.sfc_kg_N_h) * 100


TABLE_XXIII = [(0.75, 0.0020, 3.1), (0.79, 0.0057, 2.6), (0.85, 0.0057, 2.9)]


@pytest.mark.xfail(strict=True, reason="STEP0 finding 3: ideal (mass-weighted total pressure) mixing puts the level 0.7 point above Table XXIII; the momentum-balance mixer needs the mixing-plane geometry (Stage H)")
def test_mixer_gain_level_table_xxiii():
    assert abs(_mixer_gain(0.85, 0.0057) - 2.9) < 0.5


def test_mixer_gain_level_is_pinned():
    assert 3.3 < _mixer_gain(0.85, 0.0057) < 3.9


def test_mixer_gain_slopes_table_xxiii():
    """the three Table XXIII columns differ in effectiveness and loss; the
    model reproduces the differences between them to 0.3 point"""
    g = [_mixer_gain(e, l) for e, l, _ in TABLE_XXIII]
    t = [x for _, _, x in TABLE_XXIII]
    assert abs((g[1] - g[0]) - (t[1] - t[0])) < 0.3
    assert abs((g[2] - g[1]) - (t[2] - t[1])) < 0.3
    assert 0.83 < INP.comp["mixer_effectiveness"] < 0.85


def test_core_flow_two_routes():
    """W2/(1+BPR) at the match point against the published core corrected flow"""
    r = RESULTS["max_climb"]
    s = r.stations
    w25c = r.w_core_kg_s * math.sqrt(s["t25"] / 288.15) / (s["p25"] / 101325.0)
    assert abs(w25c / INP.core_corrected_kg_s - 1) < 0.015


def test_opr_two_routes_and_transition_loss():
    """fan hub PR x HPC PR overshoots the printed OPR; the implied transition-
    duct loss is of the order of Table XI's duct losses (STEP0 finding 1)"""
    for r in INP.ratings:
        overshoot = r.fpr_hub * r.hpc_pr / r.opr - 1
        assert 0.01 < overshoot < 0.03
        assert 0.01 < RESULTS[r.name].transition_loss < 0.03
    assert abs(RESULTS["max_climb"].transition_loss - 0.0222) < 0.001


def test_mixing_plane_pressures_match():
    """on the flat-rating day the core reaches the mixing plane a little
    below the bypass pressure at all three ratings (STEP0 finding 2)"""
    for r in RESULTS.values():
        assert 0.90 < r.p5_over_p13 < 1.0


def test_takeoff_sized_to_published_thrust():
    r = RESULTS["takeoff"]
    assert abs(r.fn_N - 173500) < 1
    assert 0.85 < r.w2_corrected_kg_s / INP.fan_corrected_kg_s < 0.95


def test_station_temperatures_plausible():
    for r in RESULTS.values():
        s = r.stations
        assert s["t2"] if "t2" in s else True
        assert 700 < s["t3"] < 900 and s["t4"] > s["t41"] > s["t45"] > s["t5"] > s["t6"] > s["t13"]
        assert 4.5 < r.hpt_pr < 5.2 and 3.5 < r.lpt_pr < 4.8

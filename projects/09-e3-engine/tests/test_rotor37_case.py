"""C4 step 0: the Rotor 37 validation case, and the known answer, written
down before a solver exists (data/methods/rotor37-validation-case.yaml).

No CFD is run here. These tests check that the transcribed case is
internally consistent -- that the printed efficiencies follow from the
printed pressure and temperature ratios -- so that when a solver is
installed the target is known to be sound."""
import math
import pathlib
import sys

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from e3cycle import gas  # noqa: E402

CASE = yaml.safe_load((pathlib.Path(__file__).resolve().parents[1] / "data" / "methods"
                       / "rotor37-validation-case.yaml").read_text())
DESIGN = CASE["design_point"]
MEAS = CASE["measured_100pct_speed"]
T_IN = 288.15


def adiabatic_efficiency(pr, tr, t1=T_IN):
    """real gas, from a total-pressure and total-temperature ratio"""
    t2 = t1 * tr
    t2s = gas.t_from_phi(gas.phi(t1) + gas.R_AIR * math.log(pr), guess=t2)
    return (gas.h(t2s) - gas.h(t1)) / (gas.h(t2) - gas.h(t1))


def test_the_design_point_is_self_consistent():
    eta = adiabatic_efficiency(DESIGN["rotor_total_pressure_ratio"],
                               DESIGN["rotor_total_temperature_ratio"])
    assert abs(eta - DESIGN["rotor_adiabatic_efficiency"]) < 0.01


def test_design_tip_speed_follows_from_the_rpm_and_the_annulus():
    """20.188 kg/s over 200.549 kg/s/m2 is the annulus; with hub/tip 0.70
    that fixes the tip radius, and the rpm then fixes the tip speed"""
    area = DESIGN["mass_flow_kg_s"] / DESIGN["flow_per_unit_annulus_area_kg_s_m2"]
    rr = DESIGN["hub_tip_radius_ratio"]
    r_tip = math.sqrt(area / (math.pi * (1 - rr ** 2)))
    u = r_tip * DESIGN["rpm"] * 2 * math.pi / 60
    assert abs(u / DESIGN["tip_speed_m_s"] - 1) < 0.02


@pytest.mark.parametrize("i", (0, 1, 2))
def test_the_clean_measured_efficiencies_recompute(i):
    eta = adiabatic_efficiency(MEAS["rotor_total_pressure_ratio"][i],
                               MEAS["rotor_total_temperature_ratio"][i])
    assert abs(eta - MEAS["rotor_adiabatic_efficiency"][i]) < 0.02


@pytest.mark.parametrize("i", (3, 4))
def test_the_corrupted_efficiencies_are_null_and_recomputable(i):
    """the scan prints 0.667 and 0.952, neither possible beside its own
    ratios; they are recorded as null rather than transcribed"""
    assert MEAS["rotor_adiabatic_efficiency"][i] is None
    eta = adiabatic_efficiency(MEAS["rotor_total_pressure_ratio"][i],
                               MEAS["rotor_total_temperature_ratio"][i])
    assert 0.83 < eta < 0.89, eta


def test_the_speed_line_behaves_like_a_compressor():
    pr = MEAS["rotor_total_pressure_ratio"]
    w = MEAS["airflow_at_orifice_kg_s"]
    assert all(pr[i] < pr[i + 1] for i in range(len(pr) - 1))     # toward stall
    assert all(w[i] > w[i + 1] for i in range(len(w) - 1))        # flow falls
    assert max(w) == MEAS["choking_flow_kg_s"]


def test_the_peak_efficiency_point_is_where_the_literature_puts_it():
    etas = [adiabatic_efficiency(p, t) for p, t in
            zip(MEAS["rotor_total_pressure_ratio"], MEAS["rotor_total_temperature_ratio"])]
    peak = max(range(len(etas)), key=lambda i: etas[i])
    assert MEAS["reading"][peak] == 4182
    assert abs(MEAS["airflow_at_orifice_kg_s"][peak] / MEAS["choking_flow_kg_s"] - 0.991) < 0.005


def test_the_published_cfd_reference_has_no_grid_independence():
    """it is a comparison, not a converged result, and cannot be used to
    skip METHOD.md step 6"""
    ref = CASE["published_cfd_reference"]
    assert "NONE" in ref["grid_independence"]
    assert "Only one grid resolution" in ref["grid_independence"]
    assert ref["grid_cells"] == 1.8e6


def test_the_pass_bands_come_from_the_experimental_scatter():
    b = CASE["pass_bands"]
    clean = [e for e in MEAS["rotor_adiabatic_efficiency"] if e is not None]
    assert b["adiabatic_efficiency_points"] / 100 < max(clean) - min(clean)
    assert b["grid_convergence_index_pct"] == 3.0

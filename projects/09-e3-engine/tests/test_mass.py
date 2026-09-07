"""Stage F unit F2: mass (solvers/materials/STEP0.md unit F2)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from materials.mass import (  # noqa: E402
    attachment_fraction, blading_roll_up, hpc_airfoil_areas, hpc_airfoil_masses,
    module_audit, what_is_gated,
)

AREAS = hpc_airfoil_areas()
MASSES = hpc_airfoil_masses()
FRAC = {r["row"]: r for r in attachment_fraction()}
MOD = {r["module"]: r for r in module_audit()}
ROLL = {r["module"]: r for r in blading_roll_up()}


# --- the reconstruction against twenty printed areas -----------------------

def test_all_twenty_areas_land_inside_the_band():
    assert len(AREAS) == 20
    assert max(abs(a["err_pct"]) for a in AREAS) < 20.0


def test_the_area_error_is_one_sided_which_makes_it_a_model_not_noise():
    """finding 109 -- a section that ends in a point is lighter than one
    that ends in a circle"""
    errs = [a["err_pct"] for a in AREAS]
    assert all(e < 0 for e in errs)
    assert -10 < sum(errs) / len(errs) < -5


def test_the_masses_inherit_the_area_bias():
    """finding 109"""
    assert len(MASSES) == 10
    assert all(r["err_pct"] < 0 for r in MASSES)
    assert max(abs(r["err_pct"]) for r in MASSES) < 20.0
    mean_area = sum(a["err_pct"] for a in AREAS) / len(AREAS)
    mean_mass = sum(r["err_pct"] for r in MASSES) / len(MASSES)
    assert abs(mean_mass - mean_area) < 5.0


def test_the_masses_use_the_material_f1_measured_not_the_one_table_x_prints():
    """stages 5 and 6 are the disputed ones -- finding 104"""
    by = {r["stage"]: r for r in MASSES}
    assert [by[s]["material"] for s in (1, 2, 3, 4)] == ["titanium"] * 4
    assert [by[s]["material"] for s in (5, 6)] == ["nickel", "nickel"]


# --- how much of a blade is airfoil ---------------------------------------

def test_the_airfoil_is_always_a_fraction_of_the_blade():
    for r in FRAC.values():
        assert 0.0 < r["fraction"] < 1.0


def test_the_smaller_the_blade_the_less_of_it_is_blade():
    """finding 110 -- a dovetail does not shrink with the airfoil"""
    assert FRAC["fan rotor"]["fraction"] > FRAC["HPC rotor 1"]["fraction"]
    assert FRAC["HPC rotor 1"]["fraction"] > FRAC["HPC rotor 7"]["fraction"]
    assert FRAC["HPC rotor 7"]["fraction"] < 0.25
    assert FRAC["fan rotor"]["fraction"] > 0.60
    front = [FRAC[f"HPC rotor {s}"]["fraction"] for s in (1, 2, 3, 4)]
    rear = [FRAC[f"HPC rotor {s}"]["fraction"] for s in (7, 8, 9)]
    assert min(front) > max(rear)


def test_the_lpt_stage1_airfoil_comes_from_its_transcribed_coordinates():
    r = FRAC["LPT stage 1"]
    assert "coordinates" in r["basis"]
    assert 0.30 < r["fraction"] < 0.55


# --- the published masses against each other -------------------------------

def test_five_module_weights_agree_across_two_documents_each():
    """finding 111"""
    assert len(MOD) == 5
    assert max(abs(r["err_pct"]) for r in MOD.values()) < 5.0
    assert abs(MOD["HPT stator"]["err_pct"]) < 1e-9        # exact
    assert abs(MOD["HPT rotor"]["err_pct"]) < 1.0


def test_the_worst_module_is_the_one_whose_component_table_includes_a_shaft():
    worst = max(MOD.values(), key=lambda r: abs(r["err_pct"]))
    assert worst["module"] == "fan + booster rotor"
    assert 3.0 < worst["err_pct"] < 3.5


# --- what is left, and why the closure is gated ----------------------------

def test_blades_are_half_the_fan_and_lpt_rotors_and_a_fifth_of_the_hpc():
    assert 45 < ROLL["LPT rotor"]["pct"] < 60
    assert 45 < ROLL["fan + booster rotor"]["pct"] < 60
    assert 18 < ROLL["HPC rotor"]["pct"] < 27
    assert ROLL["HPC rotor"]["remainder_kg"] > 150         # disc and joint


def test_the_bearing_system_is_a_tenth_of_the_engine_and_is_not_printed():
    """finding 112 -- Table XXVI's own note, quantified"""
    g = what_is_gated()
    assert g["basic_engine"] == 3473
    assert g["sumps_drives_seals"] == 320
    assert 9.0 < g["sumps_pct"] < 9.5
    assert g["sumps_drives_seals"] > 2 * g["combustor_casing_diffuser"]


def test_no_basic_engine_total_is_produced():
    """the closure is gated, and the module must not quietly supply one"""
    import materials.mass as m
    assert not [n for n in dir(m) if "total" in n.lower() and not n.startswith("_")]

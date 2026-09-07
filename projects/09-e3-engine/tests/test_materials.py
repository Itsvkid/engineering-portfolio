"""Stage F unit F1: materials with allowables, and the correction it
forces on Stage E (solvers/materials/STEP0.md unit F1)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from materials.allowables import (  # noqa: E402
    alloys, material_crossover, measured_blade_density, stage_e_margins,
    titanium_temperature_check,
)

A = alloys()
RHO = measured_blade_density()
BY = {r["stage"]: r for r in RHO}
X = material_crossover()
T = titanium_temperature_check()
MARGINS = stage_e_margins()


# --- the handbook transcription -------------------------------------------

def test_the_three_alloys_convert_to_the_expected_si_values():
    assert A["ti_6al_4v_die_forging"]["density"] == pytest.approx(4428.8, abs=0.5)
    assert A["ti_8al_1mo_1v_forging"]["density"] == pytest.approx(4373.4, abs=0.5)
    assert A["inconel_718_bar_forging"]["density"] == pytest.approx(8220.9, abs=0.5)
    assert A["inconel_718_bar_forging"]["e_GPa"] == pytest.approx(202.7, abs=0.2)
    assert A["ti_8al_1mo_1v_forging"]["fty_MPa"] == pytest.approx(827, abs=1)


def test_no_substitute_is_nominated_for_the_cast_and_pm_alloys():
    """naming one would put an unsourced allowable in under a handbook's
    authority; the E3's own printed allowables are used instead"""
    import yaml
    data = pathlib.Path(__file__).resolve().parents[1] / "data"
    h = yaml.safe_load((data / "methods" / "mil-hdbk-5j-allowables.yaml").read_text())
    assert h["substitutions"]["src"] == "assumption"
    for alloy in ("Rene 77", "Rene 95", "Rene 150", "AF115"):
        assert alloy in h["substitutions"]["note"]
    assert not any("Rene" in k or "AF115" in k for k in h["alloys"])


# --- the density measurement -----------------------------------------------

def test_every_blade_density_lands_on_one_of_the_two_handbook_values():
    """finding 104 -- the measurement is decisive because the candidates
    are a factor of two apart"""
    assert len(RHO) == 10
    for r in RHO:
        near = min(abs(r["over_ti"] - 1), abs(r["over_ni"] - 1))
        assert near < 0.15


def test_the_measured_crossover_is_at_stage_five():
    assert X["measured_nickel_from"] == 5
    assert all(BY[s]["nearer"] == "titanium" for s in (1, 2, 3, 4))
    assert all(BY[s]["nearer"] == "nickel" for s in range(5, 11))


def test_the_stress_column_recomputes_from_the_measured_density():
    """a different combination of the same table, and it closes"""
    assert max(abs(r["sigma_err_pct"]) for r in RHO) < 15.0


def test_table_x_contradicts_itself_at_stages_five_and_six():
    """finding 104 -- two columns against one"""
    assert X["printed_nickel_from"] == 7
    assert X["disputed_stages"] == [5, 6]
    for s in (5, 6):
        assert "Ti" in BY[s]["printed_material"]
        assert BY[s]["nearer"] == "nickel"


def test_the_disputed_blades_are_heavier_than_titanium_can_possibly_be():
    """finding 104 -- a constant-area blade is the heaviest one there is"""
    assert X["impossible"] == [5, 6]
    for s in (5, 6):
        assert BY[s]["mass_over_max_titanium"] > 1.4
    for s in (1, 2, 3, 4):
        assert BY[s]["mass_over_max_titanium"] < 1.0


# --- the Ti -> Ni switch as a design check ---------------------------------

def test_the_printed_switch_is_where_the_metal_reaches_the_titanium_limit():
    """finding 106 -- 423 C then 480 C, against a ~500 C limit"""
    assert T["printed_switch"] == 7
    assert T["t_last_ti_printed"] == 423
    assert T["t_first_ni_printed"] == 480
    assert T["t_last_ti_printed"] < T["limit_C"]


def test_the_measured_switch_has_no_thermal_reason_behind_it():
    """finding 106 -- which is why this is flagged, not resolved"""
    assert T["measured_switch"] == 5
    assert T["t_at_measured_switch"] < 400
    assert T["t_at_measured_switch"] < T["t_last_ti_printed"]


def test_the_metal_temperature_rises_monotonically_through_the_compressor():
    assert T["metal_C"] == sorted(T["metal_C"])


# --- the margin table -------------------------------------------------------

def test_every_stress_with_a_printed_allowable_has_margin():
    """F1's closure, on the parts where an allowable exists"""
    assert all(r["margin"] >= 1.0 - 1e-9 for r in MARGINS)


def test_the_parts_sitting_exactly_on_their_allowable_are_the_printed_ones():
    """finding 107"""
    on_limit = [r["part"] for r in MARGINS if r["margin"] < 1.005]
    assert "HPT stage-1 disk dovetail" in on_limit
    assert "LPT blade retainer 3" in on_limit
    assert not any("HPC rotor" in p for p in on_limit)


def test_the_hpc_blades_would_have_to_lose_more_than_half_their_yield():
    """finding 108 -- the conclusion survives the elevated-temperature gate
    even though the number behind it does not"""
    hpc = [r for r in MARGINS if r["part"].startswith("HPC rotor")]
    assert len(hpc) == 10
    assert min(r["margin"] for r in hpc) > 2.2
    assert max(r["knockdown_to_fail"] for r in hpc) < 0.45


def test_no_allowable_at_temperature_is_invented():
    """MIL-HDBK-5J's elevated-temperature data is figure-status; every row
    that quotes a temperature must be citing an E3 report, not the handbook"""
    for r in MARGINS:
        if "MIL-HDBK" in r["basis"]:
            assert "ROOM temperature" in r["basis"]

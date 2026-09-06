"""C1 unit 5: the HPC stage by stage from Table XXI against the report's
Figs 11, 14, 17 and 18 (solvers/meanline/STEP0.md unit 5)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from meanline.compressor import overall_temperature_rise, stagewise_from_table_xxi  # noqa: E402

ST, SW = stagewise_from_table_xxi()
G = SW["stagewise"]
OVERALL = overall_temperature_rise()
FIG14_TOTAL = G["temperature_rise_C"]["total"]


@pytest.mark.parametrize("n", range(10))
def test_diffusion_factor_matches_fig18(n):
    assert abs(ST[n]["df_rotor"] - G["diffusion_factor_pitch"]["rotors"][n]) < 0.01
    assert abs(ST[n]["df_stator"] - G["diffusion_factor_pitch"]["stators"][n]) < 0.01


@pytest.mark.parametrize("n", range(10))
def test_loss_coefficient_matches_fig17(n):
    assert abs(ST[n]["loss_rotor"] - G["loss_coefficient_pitch"]["rotors"][n]) < 0.005
    assert abs(ST[n]["loss_stator"] - G["loss_coefficient_pitch"]["stators"][n]) < 0.005


@pytest.mark.parametrize("n", range(10))
def test_solidity_matches_fig11(n):
    assert abs(ST[n]["solidity_rotor"] - G["pitch_solidity"]["rotors"][n]) < 0.03


def test_two_transcriptions_agree_closely():
    """finding 18: a 756-line table and four small plots, transcribed
    separately in Stage A, land on each other"""
    df = max(max(abs(ST[n]["df_rotor"] - G["diffusion_factor_pitch"]["rotors"][n]),
                 abs(ST[n]["df_stator"] - G["diffusion_factor_pitch"]["stators"][n])) for n in range(10))
    loss = max(max(abs(ST[n]["loss_rotor"] - G["loss_coefficient_pitch"]["rotors"][n]),
                   abs(ST[n]["loss_stator"] - G["loss_coefficient_pitch"]["stators"][n])) for n in range(10))
    assert df < 0.005 and loss < 0.001


def test_fig14_is_the_span_average_not_the_pitch_value():
    """finding 19: the pitch line understates the work by 3.3 percent;
    area-weighted across the span it closes to 0.2"""
    assert abs(OVERALL["area_weighted_K"] / FIG14_TOTAL - 1) < 0.01
    assert -0.045 < OVERALL["pitch_K"] / FIG14_TOTAL - 1 < -0.025
    assert OVERALL["area_weighted_K"] > OVERALL["pitch_K"]


@pytest.mark.parametrize("n", range(10))
def test_stagewise_temperature_rise_is_uniformly_low_at_pitch(n):
    """every stage low, none high -- a bias, not scatter"""
    d = ST[n]["dt"] - G["temperature_rise_C"]["per_stage"][n]
    assert -3.0 < d < -1.0


def test_stage_6_is_the_deliberately_unloaded_one():
    """the report says stages 6 and 7 are unloaded on purpose"""
    dts = [s["dt"] for s in ST]
    assert dts[5] == min(dts)
    assert dts[5] < dts[4] - 4 and dts[5] < dts[7] - 3


def test_de_haller_is_below_the_classic_limit_on_most_rows():
    """finding 20: a 23:1 ten-stage compressor is not the machine de
    Haller's criterion was written for; the report plots DF instead"""
    rotors = [s["de_haller_rotor"] for s in ST]
    stators = [s["de_haller_stator"] for s in ST]
    assert sum(1 for x in rotors if x < 0.72) >= 6
    assert min(stators) < 0.65
    assert 0.65 < min(rotors) < 0.70
    # and the design criterion it was built to is met
    for n in range(10):
        assert ST[n]["df_rotor"] < 0.62 and ST[n]["df_stator"] < 0.62


def test_stage_pressure_ratios_fall_rearward():
    prs = [s["pr_stage"] for s in ST]
    assert prs[0] > 1.6 and prs[-1] < 1.28
    assert all(prs[i] > prs[i + 1] for i in range(4))

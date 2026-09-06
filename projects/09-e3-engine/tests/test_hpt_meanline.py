"""C1 unit 3: the E3 HPT mean-line against Tables III, IV and V
(solvers/meanline/STEP0.md unit 3). Bands stated there; the two misses
are strict xfails with their size pinned."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from meanline.hpt import solve, table_v_decomposition  # noqa: E402

RES, G, STAGES, SUMM = solve()
HPT = G["hpt"]
TA = HPT["stage_aerodynamics"]
TB = HPT["preliminary_trade"]["two_stage"]
EV = HPT["efficiency_estimate"]
DECOMP = table_v_decomposition()


def test_table_v_sums_to_its_printed_net():
    total = EV["base_aerodynamic_tight_clearance_pct"] + sum(EV["corrections_pct"].values())
    assert abs(total - EV["net_efficiency_pct"]) < 1e-9


@pytest.mark.parametrize("k", (0, 1))
def test_stage_loading(k):
    assert abs(STAGES[k].psi_model - TA["loading_dh_over_2U2"][k]) < 0.06


def test_stage1_reaction():
    assert abs(STAGES[0].reaction_kin - TA["reaction"][0]) < 0.08


def test_stage2_reaction_sits_on_the_band_edge():
    """0.407 against a printed 0.33: inside the +-0.08 band by 0.003.
    Recorded, not celebrated -- see unit 3 finding 10."""
    d = STAGES[1].reaction_kin - TA["reaction"][1]
    assert abs(d) < 0.08
    assert 0.07 < d < 0.08


@pytest.mark.parametrize("k", (0, 1))
def test_stage_exit_mach(k):
    assert abs(STAGES[k].m3 - TA["exit_mach"][k]) < 0.05


@pytest.mark.parametrize("k", (0, 1))
def test_vane_and_blade_exit_mach(k):
    pt = TB[f"stage{k + 1}"]
    assert abs(STAGES[k].m2 - pt["vane_exit_M"]) < 0.08
    assert abs(STAGES[k].m3rel - pt["blade_exit_M"]) < 0.08


def test_stage1_turning():
    assert abs(STAGES[0].turning - TB["stage1"]["turning_deg"]) < 8


@pytest.mark.xfail(strict=True, reason="unit 3 finding 10: 85 deg against the preliminary study's 99")
def test_stage2_turning():
    assert abs(STAGES[1].turning - TB["stage2"]["turning_deg"]) < 8


def test_efficiency_against_all_three_published_values():
    for target in (EV["net_efficiency_pct"] / 100,
                   HPT["efficiency_chronology"]["warm_air_turbine_rig_pct"] / 100,
                   HPT["efficiency_chronology"]["fps_table_xi_pct"] / 100):
        assert abs(SUMM["eta_tt"] - target) < 0.02


def test_pressure_ratio_matches_the_cycle():
    assert abs(SUMM["pr"] / SUMM["pr_cycle"] - 1) < 0.03


@pytest.mark.xfail(strict=True, reason="unit 3 finding 9: R&M 2974's B (k/h) clearance term prices the E3 HPT clearances at 0.95 point against Table V's stated 1.50; the later (k/c)^0.78 forms raise it")
def test_tip_clearance_debit_matches_table_v():
    assert abs(DECOMP["tip_clearance_points"] - abs(EV["corrections_pct"]["tip_clearance"])) < 0.5


def test_tip_clearance_debit_pinned():
    assert 0.8 < DECOMP["tip_clearance_points"] < 1.2
    assert DECOMP["tight"] > DECOMP["actual"]
    assert DECOMP["no_endwall"] > DECOMP["tight"]


def test_swirl_sign_is_settled_by_the_reaction():
    """with the swirl in the direction of rotation the stage-1 reaction
    collapses to 0.09 and the vane goes supersonic (finding 7)"""
    _, _, wrong, _ = solve(swirl_sign=+1.0)
    assert wrong[0].reaction_kin < 0.15
    assert wrong[0].m2 > 1.05
    assert abs(STAGES[0].reaction_kin - TA["reaction"][0]) < abs(wrong[0].reaction_kin - TA["reaction"][0])


def test_row_losses_are_plausible():
    for st in STAGES:
        for r in st.rows:
            assert 0.03 < r.yp < 0.12 and r.yt < 0.25
            assert (r.yk > 0) == r.name.startswith("B")

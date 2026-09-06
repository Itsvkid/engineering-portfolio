"""C1 unit 2, application: the E3 LPT with Ainley-Mathieson losses
(solvers/meanline/STEP0.md unit 2). The band, +-2 points on the
five-stage efficiency, was stated first; the miss is a strict xfail with
its size pinned, by both secondary-loss routes."""
import math
import pathlib
import sys

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from meanline.lpt_losses import routes_with_band, run  # noqa: E402
from meanline.sections import section_geometry  # noqa: E402

RES, G, STAGES, SUMM = run()
RB = routes_with_band()
ROWS = {r.name: r for st in STAGES for r in st.rows}
PUBLISHED = 0.917


@pytest.mark.xfail(strict=True, reason="unit 2 finding 2: R&M 2974 as printed gives 0.837 for a 0.917 turbine -- no aspect-ratio term, 1951 profile-loss level")
def test_lpt_efficiency_rm2974():
    assert abs(SUMM["eta_tt"] - PUBLISHED) < 0.02


@pytest.mark.xfail(strict=True, reason="unit 2 finding 2: the Dunham-Came c/h term recovers 3 points, to 0.869; the profile-loss level remains 1951's")
def test_lpt_efficiency_dunham_came():
    assert abs(SUMM["eta_tt_dc"] - PUBLISHED) < 0.02


def test_lpt_efficiency_sp290_route_closes():
    """unit 2b: profile loss from R&M 2974, end-wall loss from SP-290's
    area ratio (eq 7-47), Reynolds correction from R&M 2974 sec 8 --
    inside the +-2 points the method claims for itself"""
    assert abs(RB["sp290"]["eta_re"] - PUBLISHED) < 0.02
    assert abs(RB["sp290"]["eta"] - PUBLISHED) < 0.02


def test_reynolds_correction_helps_not_hurts():
    """the mean of first vane and last rotor is above the charts' 2e5"""
    assert 2.2e5 < RB["re_mean"] < 2.8e5
    for k in ("rm2974", "dunham_came", "sp290"):
        assert 0.003 < RB[k]["eta_re"] - RB[k]["eta"] < 0.008


def test_the_three_routes_are_ordered_and_bracket_the_answer():
    assert RB["rm2974"]["eta"] < RB["dunham_came"]["eta"] < RB["sp290"]["eta"]
    assert RB["rm2974"]["eta"] < PUBLISHED
    assert abs(RB["sp290"]["eta"] - PUBLISHED) < abs(RB["dunham_came"]["eta"] - PUBLISHED) < abs(RB["rm2974"]["eta"] - PUBLISHED)


def test_stated_loss_band_is_the_reports_own():
    """R&M 2974 sec 9 prints +-15 percent on its loss rules; on this
    turbine that is 1.2-1.9 points of five-stage efficiency"""
    for k in ("rm2974", "dunham_came", "sp290"):
        assert 1.0 < RB[k]["band_points"] < 2.2


def test_end_wall_multiplier_tracks_aspect_ratio():
    """SP-290 eq 7-47 on the tall rear rows is a tenth of what Fig 8 implies"""
    from meanline.losses import end_wall_multiplier
    r4, s1 = ROWS["R4"], ROWS["S1"]
    m_r4 = end_wall_multiplier(r4.s_c * r4.c_h, r4.stagger_deg)
    m_s1 = end_wall_multiplier(s1.s_c * s1.c_h, s1.stagger_deg)
    assert 1.05 < m_r4 < 1.15 and 1.2 < m_s1 < 1.35
    assert (r4.ysk / r4.yp) > 3 * (m_r4 - 1)


def test_lpt_efficiency_pinned():
    assert 0.825 < SUMM["eta_tt"] < 0.85
    assert 0.855 < SUMM["eta_tt_dc"] < 0.88
    assert 0.895 < SUMM["eta_tt_sp"] < 0.92
    assert SUMM["eta_tt_sp"] > SUMM["eta_tt_dc"] > SUMM["eta_tt"]


def test_rear_stages_lose_less():
    """the tall rear rows (h/c 5-8) carry less secondary loss and higher
    stage efficiency; the aspect-ratio route widens the gap"""
    etas = [st.eta_tt for st in STAGES]
    assert etas[4] > etas[3] > etas[1]
    assert STAGES[4].eta_tt_dc - STAGES[4].eta_tt > STAGES[0].eta_tt_dc - STAGES[0].eta_tt


def test_row_geometry_against_fig52_and_table_iii():
    design = yaml.safe_load((pathlib.Path(__file__).resolve().parents[1] / "data" / "lpt-design.yaml").read_text())

    def find(d, k):
        if isinstance(d, dict):
            if k in d:
                return d[k]
            for v in d.values():
                r = find(v, k)
                if r is not None:
                    return r
    root, tip = find(design, "root_chord_in"), find(design, "tip_chord_in")
    for n in range(1, 6):
        c = section_geometry(f"R{n}")["chord_in"]
        lo, hi = min(root[n - 1], tip[n - 1]), max(root[n - 1], tip[n - 1])
        if n == 4:
            assert c < lo          # the 'flask' rotor: mid-span chord under both ends
        else:
            assert lo * 0.97 < c < hi * 1.03, (n, c)
    for name, r in ROWS.items():
        blockage = r.te_s / math.cos(math.radians(r.alpha2))
        assert abs(blockage / G["te_blockage"][name] - 1) < 0.25, (name, blockage)


def test_loss_coefficients_are_in_range():
    for r in ROWS.values():
        assert 0.02 < r.yp < 0.12 and 0.03 < r.ysk < 0.15 and r.yt < 0.25
        assert 0.4 < r.s_c < 0.8 and 0.05 < r.t_c < 0.27
        assert 5e4 < r.re_chord < 5e5


def test_pressure_chain_bracketed_by_the_cycle():
    """losses beyond the cycle's 0.925 push the required expansion above
    the cycle's 4.55; Table II's chain (pre-rematch) sits below it"""
    assert SUMM["pr_table_ii"] < SUMM["pr_cycle"] < SUMM["pr_sp"] < SUMM["pr_dc"] < SUMM["pr"]
    assert abs(SUMM["pr_sp"] / SUMM["pr_cycle"] - 1) < 0.05


def test_figure_exists():
    assert (pathlib.Path(__file__).resolve().parents[1] / "solvers" / "meanline" / "figures" / "lpt-losses.png").exists()

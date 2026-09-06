"""C1 unit 1: LPT mean-line kinematics against Table II (solvers/meanline/STEP0.md).
Bands written first; every miss is a strict xfail so a change is noticed."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from meanline.lpt import COMPARE, comparison, run  # noqa: E402

RES, G, OUT = run()
ROWS = {(n, attr): (c, p, band) for n, attr, c, p, band in comparison(G, OUT)}

# the systematic misses of 2026-09-06, each with its finding in STEP0
MISSES = {
    (1, "beta2"), (2, "beta2"), (3, "beta2"), (4, "beta2"), (5, "beta2"),          # finding 4
    (1, "reaction"), (2, "reaction"), (3, "reaction"), (4, "reaction"), (5, "reaction"),  # finding 2
    (2, "phi"), (3, "phi"), (4, "phi"), (5, "phi"),                                 # findings 2, 3
    (1, "m2"), (2, "m2"), (3, "m2"), (2, "m2rel"), (3, "m2rel"),                    # finding 3
    (2, "beta3"), (5, "beta3"), (5, "psi"),
}


def _params():
    for n in range(1, 6):
        for attr, _, _ in COMPARE:
            marks = [pytest.mark.xfail(strict=True, reason="STEP0 unit 1 findings")] if (n, attr) in MISSES else []
            yield pytest.param(n, attr, marks=marks, id=f"stage{n}-{attr}")


@pytest.mark.parametrize("n, attr", list(_params()))
def test_table_ii_pitch(n, attr):
    c, p, band = ROWS[(n, attr)]
    assert abs(c - p) < band, f"stage {n} {attr}: {c:.3f} vs Table II {p:.3f}"


def test_pass_count_is_pinned():
    passes = sum(abs(c - p) < band for c, p, band in ROWS.values())
    assert passes == 50 - len(MISSES)


def test_loading_on_four_of_five_stages():
    for n in range(1, 5):
        c, p, band = ROWS[(n, "psi")]
        assert abs(c - p) < 0.04


def test_table_ii_pressure_ratios_are_the_pre_rematch_cycle():
    """product 4.21 against the final cycle's 4.55 (STEP0 finding 3)"""
    pr = 1.0
    for st in OUT:
        pr *= st.stage_pr
    assert 4.15 < pr < 4.27 and abs(pr / RES.lpt_pr - 1) > 0.05


def test_station_2_is_the_stator_trailing_edge():
    """the annulus grows ~8 percent between a stator TE and the next rotor
    LE; Table II's stator-exit column is at the TE (finding 1)"""
    from meanline.lpt import _pitch_and_area
    _, a_te = _pitch_and_area(G["fp"], "S1", "TE", 1.0)
    _, a_le = _pitch_and_area(G["fp"], "R1", "LE", 1.0)
    assert 1.05 < a_le / a_te < 1.10
    assert abs(OUT[0].phi - 1.25) < 0.02


def test_table_ii_columns_disagree_with_their_own_angles():
    """phi and reaction from Table II's pitch angles differ from its printed
    phi and reaction columns (finding 2); pinned so it stays visible"""
    import math
    t = G["table_ii"]["stage1"]
    a2, b2, b3 = [math.radians(t[k][1]) for k in ("stator_exit_angle_deg", "rotor_rel_inlet_angle_deg", "rotor_rel_exit_angle_deg")]
    phi = 1 / (math.tan(a2) - math.tan(b2))
    r = phi / 2 * (math.tan(b3) - math.tan(b2))
    assert abs(phi - 1.43) < 0.02 and abs(r - 0.52) < 0.02
    assert t["flow_coefficient_vz_over_u"] == 1.25 and t["reaction"][1] == 0.305


def test_figure_exists():
    assert (pathlib.Path(__file__).resolve().parents[1] / "solvers" / "meanline" / "figures" / "lpt-vector-diagrams.png").exists()

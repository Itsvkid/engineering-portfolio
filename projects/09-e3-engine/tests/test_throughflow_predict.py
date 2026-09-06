"""C2 unit 9: predict the spanwise distribution from radial equilibrium
(solvers/throughflow/STEP0.md unit 9). The band is the work plan's own
C2 closure criterion: 2 degrees of swirl and 0.02 of Mach at the
stator-10 exit."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from throughflow.predict import errors, predict_all  # noqa: E402

ALL = predict_all()
BY = dict(ALL)
S10 = errors(BY["S10 ex"])


def _mean(labels, key):
    rows = [errors(BY[l]) for l in labels]
    return sum(r[key] for r in rows) / len(rows)


FRONT = [l for l in BY if l.split()[0] in ("IGV", "R1", "S1", "R2", "S2")]
REAR = [l for l in BY if l.split()[0] in ("R6", "S6", "R7", "S7", "R8", "S8", "R9", "S9", "R10", "S10")]


def test_c2_closure_criterion_at_the_stator_10_exit():
    """the work plan's own criterion, written before Stage A"""
    assert S10["alpha_max"] < 2.0
    assert S10["mach_max"] < 0.02


def test_the_criterion_is_met_with_orders_to_spare():
    assert S10["alpha_rms"] < 0.1
    assert S10["mach_rms"] < 0.005


def test_every_station_is_predicted_not_just_the_criterion_one():
    assert len(ALL) == 42
    for label, res in ALL:
        assert len(res) == 12


def test_the_rear_of_the_machine_predicts_far_better_than_the_front():
    """finding 35"""
    assert _mean(REAR, "alpha_rms") < 0.4
    assert _mean(REAR, "mach_rms") < 0.006
    assert _mean(FRONT, "alpha_rms") > 3 * _mean(REAR, "alpha_rms")
    assert _mean(FRONT, "mach_rms") > 5 * _mean(REAR, "mach_rms")


def test_the_worst_station_is_a_transonic_front_row():
    worst = max(ALL, key=lambda t: errors(t[1])["alpha_rms"])
    assert worst[0].split()[0] in ("IGV", "R1", "S1")


def test_curvature_term_degrades_the_integrated_prediction():
    """finding 34: it improved the local residual in unit 8 and makes the
    integration worse here -- integrating a noisy correction accumulates"""
    curved = dict(predict_all(with_curvature=True))
    for labels in (FRONT, REAR):
        simple = sum(errors(BY[l])["alpha_rms"] for l in labels) / len(labels)
        with_c = sum(errors(curved[l])["alpha_rms"] for l in labels) / len(labels)
        assert with_c > simple

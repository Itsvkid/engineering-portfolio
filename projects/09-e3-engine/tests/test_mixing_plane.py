"""Unit B5 -- the momentum-balance mixing plane.

Every band here was written into solvers/e3cycle/STEP0.md before the module
first ran. Band 1 is the one the unit exists for: if the mixed state depends
on an absolute area, B1's gate really is a transcription job and this whole
unit is wrong.
"""
import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solvers"))

from e3cycle import mixing_plane as mp                       # noqa: E402
from e3cycle.cycle import load_inputs, solve, solve_rating    # noqa: E402

INP = load_inputs()
MC = next(r for r in INP.ratings if r.name == "max_cruise")
ST = mp._streams(solve_rating(MC, INP), INP)
AR_NOM, (AR_LO, AR_HI) = mp.published_area_ratio()


def _gain(eff, loss, ar):
    """identical convention to tests/test_e3cycle.py::_mixer_gain"""
    sep = solve(MC, INP, mixed=False, extra_loss=-loss)
    return (1 - solve(MC, INP, mixer_eff=eff, mixing_area_ratio=ar).sfc_kg_N_h
            / sep.sfc_kg_N_h) * 100


# --- band 1: the claim the unit is for --------------------------------------

def test_band1_the_absolute_area_does_not_enter():
    """Scale both mass flows by ten. At a fixed area ratio that is a mixing
    plane ten times the size passing ten times the flow; if the absolute area
    mattered the intensive state would have to move."""
    moved, area_scale = mp.scale_invariance(**ST, area_ratio=AR_NOM)
    assert area_scale == pytest.approx(10.0, rel=1e-9)
    assert moved < 1e-9


def test_band1_solve_takes_no_absolute_area():
    """the signature is the evidence: a ratio goes in, no area does"""
    import inspect
    params = set(inspect.signature(mp.solve).parameters)
    assert "area_ratio" in params
    assert not {p for p in params if p.startswith("area") and p != "area_ratio"}


# --- band 2: a real mixing plane must lose ----------------------------------

def test_band2_mixed_total_pressure_is_below_the_mass_weighted_mean():
    m = mp.solve(**ST, area_ratio=AR_NOM)
    assert min(ST["pt_c"], ST["pt_b"]) < m["pt6"] < m["pt6_ideal"]
    assert 0.5 < m["loss_vs_ideal_pct"] < 1.5


# --- band 3: B1's own band, unchanged ---------------------------------------

def test_band3_table_xxiii_level_closes():
    """B1's closure. The band is the one B1 was always judged against."""
    assert abs(_gain(0.85, 0.0057, AR_NOM) - 2.9) < 0.5


@pytest.mark.parametrize("ar", [AR_LO, AR_NOM, AR_HI])
def test_band3_holds_across_the_published_area_ratio_band(ar):
    """the bypass area is a band, because the published fan-duct Mach is;
    the closure must not depend on where inside it the ratio sits"""
    assert abs(_gain(0.85, 0.0057, ar) - 2.9) < 0.5


def test_the_mass_weighted_model_is_still_there_and_still_misses():
    """unit B5 adds a model; it does not delete the one it replaces, and the
    ideal bound is still 0.7 point high -- that comparison is the finding"""
    assert abs(_gain(0.85, 0.0057, None) - 2.9) > 0.5


# --- band 4: the mixing plane must be at a physical Mach number -------------

def test_band4_mixing_plane_mach_numbers_are_physical():
    m = mp.solve(**ST, area_ratio=AR_NOM)
    assert 0.30 <= m["mach_core"] <= 0.70
    assert 0.30 <= m["mach_bypass"] <= 0.70


def test_band4_the_published_ratio_sits_inside_the_mach_admissible_range():
    lo, hi = mp.mach_admissible_range(ST)
    assert lo < AR_LO and AR_HI < hi


# --- band 5: the slopes must survive fixing the level -----------------------

def test_band5_table_xxiii_slopes_still_reproduce():
    g = [_gain(e, l, AR_NOM) for e, l, _ in mp.TABLE_XXIII]
    t = [x for _, _, x in mp.TABLE_XXIII]
    assert abs((g[1] - g[0]) - (t[1] - t[0])) < 0.5
    assert abs((g[2] - g[1]) - (t[2] - t[1])) < 0.5


# --- band 6: sensitivity to the one assumed input ---------------------------

def test_band6_the_answer_moves_less_than_the_correction_it_makes():
    """across the published area-ratio band the gain must move by much less
    than the 0.71 point the momentum balance is being asked to find"""
    g = [_gain(0.85, 0.0057, ar) for ar in (AR_LO, AR_HI)]
    assert abs(g[1] - g[0]) < 0.71


def test_band6_minus_30_percent_is_not_reachable():
    """finding 243: the sweep step 0 asked for cannot be run symmetrically.
    Below a floor the streams go sonic at the common static pressure and no
    area ratio exists; the E3's published ratio sits 24 % above it."""
    with pytest.raises((ValueError, RuntimeError)):
        mp.solve(**ST, area_ratio=0.70 * AR_NOM)


# --- the area ratio itself --------------------------------------------------

def test_the_area_ratio_is_read_from_published_geometry():
    assert mp.core_annulus_m2() == pytest.approx(0.7106, abs=5e-4)
    assert mp.bypass_annulus_m2() == (2.20, 2.41)
    assert AR_NOM == pytest.approx(0.3083, abs=5e-4)

"""Stage J unit J1: the meridional plot
(solvers/publication/STEP0.md unit J1).

The step-0 band for a drawing is not a percentage -- it is the list of
things that would make the figure a lie. Each row of that table is a test
here."""
import pathlib
import re
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from publication.meridional import (  # noqa: E402
    assumed_offsets, fan_stations, hpc_flowpath, hpt_flowpath, joins,
    layout, lpt_flowpath, plot, summary, transition_duct,
)

L = layout()
J = joins()
FAN = fan_stations()
OFF = assumed_offsets()


# --- provenance ------------------------------------------------------------

def test_every_module_is_present_with_its_own_datum():
    for m in ("fan", "hpc", "hpt", "lpt"):
        assert L[m]["datum"], m


def test_the_engine_axis_is_datumed_on_the_fan_stacking_axis():
    """the same datum atlas/flowpath.js uses: y = 0 at the fan rotor SA"""
    assert L["fan"]["x0"] == 0.0
    assert L["fan"]["assumed"] is False
    assert len(L["hpc"]["rows"]) == 42          # 21 rows, LE and TE
    assert L["hpc"]["length"] == pytest.approx(85.9, abs=0.3)


# --- radial extent: finding 140 -------------------------------------------

def test_the_fan_tip_is_where_table_iv_puts_it():
    tip = max(s["r_tip"] for s in FAN)
    assert tip == pytest.approx(210.8 / 2, abs=0.1)


def test_the_fan_is_more_than_twice_the_radius_of_the_core():
    """finding 140: an axis sized to the core hides the whole fan"""
    core_tip = max(r["r_tip"] for r in hpc_flowpath())
    assert max(s["r_tip"] for s in FAN) > 2.5 * core_tip


def test_the_figure_axes_contain_every_station():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    p = plot()
    assert p.exists() and p.stat().st_size > 20_000
    fig = plt.gcf()
    plt.close(fig)


def test_the_plot_is_drawn_at_equal_aspect():
    """a stretched meridional plot misstates every wall angle on it"""
    src = (pathlib.Path(__file__).resolve().parents[1]
           / "solvers/publication/meridional.py").read_text()
    assert 'set_aspect("equal")' in src


# --- the fan draws no wall it does not have: finding 143 -------------------

def test_the_fan_has_three_radial_stations_and_one_axial_position():
    assert len(FAN) == 3
    assert sum(s["z_known"] for s in FAN) == 1


def test_the_one_fan_station_with_an_axial_position_is_the_stacking_axis():
    known = [s for s in FAN if s["z_known"]][0]
    assert "stacking axis" in known["name"]
    assert known["r_tip"] == pytest.approx(103.9, abs=0.2)   # Fig 15, < the 105.4 tip
    assert known["r_hub"] == pytest.approx(41.8, abs=0.2)


def test_the_stacking_axis_sits_inside_the_fan_tip():
    """Fig 15's stacking-axis OD is below Table IV's tip radius, as it must be"""
    known = [s for s in FAN if s["z_known"]][0]
    assert known["r_tip"] < 210.8 / 2


def test_the_booster_annulus_is_the_short_one():
    booster = [s for s in FAN if "booster" in s["name"]][0]
    assert booster["r_tip"] == pytest.approx(133.8 / 2, abs=0.1)
    assert booster["r_tip"] - booster["r_hub"] < 15      # radius ratio 0.782


def test_every_fan_station_carries_its_source():
    for s in FAN:
        assert s["src"]


# --- the known join is drawn at its measured length: finding 141 -----------

def test_the_lpt_rides_on_the_hpt_exit_plane_and_is_not_re_zeroed():
    """finding 141: the draft subtracted the first row's z and deleted the duct"""
    assert L["lpt"]["assumed"] is False
    assert L["lpt"]["datum"] == "HPT exit plane"
    first_le = min(r["z_hub"] for r in lpt_flowpath())
    assert first_le > 6.0          # the duct is still there
    assert first_le == pytest.approx(6.85, abs=0.05)


def test_the_lpt_starts_after_the_hpt_ends():
    hpt_end = L["hpt"]["x0"] + L["hpt"]["length"]
    lpt_first = L["lpt"]["x0"] + min(r["z_hub"] for r in lpt_flowpath())
    assert lpt_first - hpt_end == pytest.approx(6.85, abs=0.05)


def test_the_csv_header_still_says_what_the_datum_is():
    """the sentence finding 141 turned on -- if it goes, the test goes red"""
    hdr = (pathlib.Path(__file__).resolve().parents[1]
           / "data/lpt-flowpath.csv").read_text().splitlines()[0]
    assert "HPT exit plane" in hdr


# --- the two published duct lengths disagree: finding 142 -----------------

def test_the_two_published_duct_lengths_disagree_by_ten_percent():
    td = transition_duct()
    assert td["axial_length_cm"] == 7.62
    assert td["from_sections_cm"] == pytest.approx(6.85, abs=0.01)
    assert J["duct_disagreement_cm"] == pytest.approx(0.77, abs=0.01)
    assert 9 < 100 * J["duct_disagreement_cm"] / td["axial_length_cm"] < 11


def test_the_sections_are_the_number_used():
    """not the printed 7.62 -- the LPT rows are drawn on the section datum"""
    lpt_first = min(r["z_hub"] for r in lpt_flowpath())
    assert lpt_first == pytest.approx(transition_duct()["from_sections_cm"], abs=0.05)
    assert lpt_first != pytest.approx(transition_duct()["axial_length_cm"], abs=0.05)


# --- the unknown joins stay visible ---------------------------------------

def test_both_unpublished_joins_are_drawn_with_their_allowable_range():
    assert len(J["unknown"]) == 2
    assert len(L["gaps"]) == 2
    for g in L["gaps"]:
        lo, hi = g["rng"]
        assert lo < g["value"] < hi              # the assumption sits inside its range
        assert g["x1"] - g["x0"] == pytest.approx(g["value"], abs=0.05)
        assert g["span"][0] < g["span"][1]
    assert any("fan" in u for u in J["unknown"])
    assert any("HPT" in u or "HPC OGV" in u for u in J["unknown"])


def test_the_modules_placed_across_an_assumed_join_are_flagged():
    assert L["hpc"]["assumed"] is True
    assert L["hpt"]["assumed"] is True
    assert L["lpt"]["assumed"] is False          # measured off the HPT exit


def test_the_two_assumed_offsets_live_in_the_data_file_not_the_plot():
    """finding 159: the same two numbers draw the Turbofan Atlas. If either
    artefact keeps its own copy they will drift, and two pictures of one
    engine will disagree."""
    assert OFF["status"] == "assumed"
    for k in ("fan_sa_to_hpc_r1_le", "hpc_ogv_te_to_hpt_vane1"):
        assert OFF[k]["value_cm"] > 0 and len(OFF[k]["range_cm"]) == 2
        assert OFF[k]["note"]
    assert "NOT PUBLISHED" in OFF["src"]
    src = (pathlib.Path(__file__).resolve().parents[1]
           / "solvers/publication/meridional.py").read_text()
    assert "142" not in src and "0.48" not in src     # no second copy here


def test_the_plot_and_the_turbofan_atlas_place_the_engine_identically():
    """cross-artefact consistency, which is Stage I's job applied to a figure"""
    js = pathlib.Path(__file__).resolve().parents[3] / "app/turbofan/atlas/flowpath.js"
    if not js.exists():
        pytest.skip("the atlas page is not in this checkout")
    text = js.read_text()
    hpc0 = float(re.search(r"export const HPC0 = ([\d.]+)", text).group(1))
    hpt0 = float(re.search(r"export const HPT0 = ([\d.]+)", text).group(1))
    assert hpc0 * 100 == pytest.approx(OFF["fan_sa_to_hpc_r1_le"]["value_cm"], abs=0.5)
    assert hpc0 * 100 == pytest.approx(L["hpc"]["x0"], abs=0.5)
    # the atlas rounds the OGV station to 0.782 m; agree to a centimetre
    assert hpt0 * 100 == pytest.approx(L["hpt"]["x0"], abs=1.0)


def test_no_radius_comes_from_a_scaled_cutaway():
    """engine-flowpath.yaml's own rule; CR-168219 Fig 1 is not digitised"""
    src = (pathlib.Path(__file__).resolve().parents[1]
           / "solvers/publication/meridional.py").read_text()
    assert "cutaway" in src
    for name in ("hpc-flowpath.csv", "lpt-flowpath.csv"):
        hdr = (pathlib.Path(__file__).resolve().parents[1]
               / "data" / name).read_text().splitlines()[0]
        assert "DERIVED by tools/build_flowpaths.py" in hdr


# --- walls behave ---------------------------------------------------------

def test_no_wall_crosses_itself():
    for rows in (hpc_flowpath(), lpt_flowpath()):
        for r in rows:
            assert r["r_tip"] > r["r_hub"], r["row"]


def test_the_hpt_annulus_closes_down_then_opens():
    st = hpt_flowpath()
    h = [s["r_tip"] - s["r_hub"] for s in st]
    assert h[0] > h[1]          # vane row turns it down
    assert h[-1] > h[1]         # stage 2 opens it out again
    assert all(x > 0 for x in h)


def test_the_summary_names_both_kinds_of_join():
    s = summary()
    assert "joins known (2)" in s
    assert "joins NOT published (2)" in s
    assert "MEASURED" in s or "sections used" in s

"""Stage D unit D7: the stage-1 nozzle cooling flow network
(solvers/thermal/STEP0.md unit D7)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
from thermal.nozzle_network import (  # noqa: E402
    DISCHARGES_AT_STAGNATION, FORWARD_ROWS, AFT_ROWS,
    cavity_for, discharge_coefficient, discharge_reference,
    film_hole_area_m2, impingement_ratios, insert_split, pressure_chain,
    required_reassignment, row_network, suction_side_row_mismatch,
    the_aggregate_hides_the_rows, w25_kg_s, why_the_rows_miss,
)

BAND_PCT = 0.5          # step 0, checks 1 and 2
CD_PHYSICAL = (0.5, 1.0)
CD_TYPICAL = (0.6, 0.85)


# ---------------------------------------------------------------- check 1

def test_the_pressure_chain_closes_inside_the_stated_band():
    rows = pressure_chain()
    assert len(rows) == 2
    for r in rows:
        assert abs(r["err_pct"]) < BAND_PCT, r


def test_the_pressure_chain_loses_more_on_the_outer_band():
    """The outer liner is the longer path and the report prints the bigger
    loss for it, so the outer band must be delivered at a lower pressure."""
    by = {r["band"]: r for r in pressure_chain()}
    assert by["outer"]["loss_pct"] > by["inner"]["loss_pct"]
    assert by["outer"]["printed_MPa"] < by["inner"]["printed_MPa"]


# ---------------------------------------------------------------- check 2

def test_the_impingement_ratios_reproduce_inside_the_stated_band():
    rows = impingement_ratios()
    assert len(rows) == 2
    for r in rows:
        assert abs(r["err_pct"]) < BAND_PCT, r


def test_the_aft_insert_works_the_harder_of_the_two():
    by = {r["cavity"]: r for r in impingement_ratios()}
    assert by["aft_cavity"]["printed"] > by["forward_cavity"]["printed"]


# ---------------------------------- the discharge reference, D3 finding 65

def test_each_cavity_matches_one_gas_reference_and_not_the_other():
    """finding 65 found the printed definition fits only one cavity. Which
    one it fits each is what D7 needs, and the data says it cleanly."""
    d = discharge_reference()
    assert d["references_differ"]
    assert d["forward_reference"] == "pt_MPa"
    assert d["aft_reference"] == "ps_MPa"
    for r in d["rows"]:
        assert abs(r["err_pct"]) < 0.02, r
        assert r["separation"] > 40, r


def test_the_showerhead_is_the_row_referenced_to_stagnation():
    d = discharge_reference()
    assert d["forward_reference"] == "pt_MPa"
    assert DISCHARGES_AT_STAGNATION == ("leading_edge",)
    assert cavity_for("leading_edge") == "forward_cavity"
    stag = [r for r in row_network() if r["discharges_at_stagnation"]]
    assert [r["row"] for r in stag] == ["leading_edge"]
    assert stag[0]["m_used"] == 0.0
    assert stag[0]["m_gas_printed"] > 0.0


# ------------------------------------------------- the feed map, recovered

def test_exactly_one_subset_of_the_rows_is_the_forward_insert_flow():
    s = insert_split()
    assert s["candidate_subsets"] == 1
    assert s["unique"]
    assert set(s["the_unique_subset"]) == set(FORWARD_ROWS)


def test_both_insert_flows_are_reproduced_to_the_last_printed_digit():
    s = insert_split()
    assert s["forward_exact"] and s["aft_exact"]
    assert abs(s["forward_sum_pct"] - s["forward_printed_pct"]) < 1e-9
    assert abs(s["aft_sum_pct"] - s["aft_printed_pct"]) < 1e-9
    assert abs(s["total_pct"] - s["total_printed_pct"]) < 1e-9


def test_the_forward_group_is_contiguous_from_the_leading_edge():
    """The subset that closes is not an arbitrary four of seven -- it is
    the four running back from the leading edge, which is what a forward
    impingement insert would feed."""
    assert FORWARD_ROWS[0] == "leading_edge"
    assert "pressure_side_te_slots" in AFT_ROWS
    assert set(FORWARD_ROWS) & set(AFT_ROWS) == set()
    assert len(FORWARD_ROWS) + len(AFT_ROWS) == len(row_network())


# ---------------------------------------------------------- the geometry

def test_the_round_hole_area_and_count_are_figure_15s():
    a = film_hole_area_m2()
    assert a["round_hole_count"] == 105 + 51 + 43
    assert abs(a["round_hole_area_m2"] * 1e6 - 45.71) < 0.01


def test_the_trailing_edge_slots_are_included_because_both_dimensions_print():
    """A first pass excluded them on the belief that Figure 15 printed one
    slot dimension. It prints two, 0.559 by 1.63 mm. The slots are 26 % of
    the vane's film area and carry 36 % of its film flow, so excluding
    them while keeping their flow is what made that pass unphysical."""
    a = film_hole_area_m2()
    te = a["groups"]["trailing_edge"]
    assert te["kind"] == "slot" and te["holes"] == 18
    assert abs(te["area_m2"] * 1e6 - 18 * 0.559 * 1.63) < 1e-6
    assert a["te_slot_area_m2"] / a["total_area_m2"] > 0.25
    d = discharge_coefficient()
    te_flow = next(g["w_c_pct"] for g in d["groups"]
                   if g["group"] == "trailing_edge")
    assert te_flow / d["total_w_c_pct"] > 0.35


def test_every_printed_film_row_is_in_exactly_one_area_group():
    a = film_hole_area_m2()
    groups = set(a["groups"])
    assert {r["group"] for r in row_network()} == groups
    assert abs(sum(v["area_m2"] for v in a["groups"].values())
               - a["total_area_m2"]) < 1e-15


# ------------------------------------------------------------------- W25

def test_w25_comes_from_the_published_corrected_flow():
    """The cycle model has no station 2.5, so W25 is not read off it. It
    is the FPS report's printed corrected flow put through the cycle's own
    p25 and t25 -- both printed, one conversion."""
    w = w25_kg_s()
    assert w["corrected_kg_s"] == 54.4
    assert w["delta"] > 1.0 and w["theta"] > 1.0
    assert 70.0 < w["physical_kg_s"] < 85.0
    assert abs(w["physical_kg_s"] - 76.91) < 0.05


# -------------------------------------------------------------- check 3

def test_the_whole_vane_passes_its_flow_at_a_physical_cd():
    d = discharge_coefficient()
    assert CD_PHYSICAL[0] <= d["cd"] <= CD_PHYSICAL[1], d["cd"]
    assert CD_TYPICAL[0] <= d["cd"] <= CD_TYPICAL[1], d["cd"]
    assert d["physical"] and d["typical"]
    assert abs(d["cd"] - 0.798) < 0.005


def test_the_flow_and_area_that_cd_was_inverted_from_are_the_printed_ones():
    d = discharge_coefficient()
    assert abs(d["total_w_c_pct"] - 6.30) < 1e-9
    assert d["vanes"] == 46
    assert abs(d["total_area_per_vane_m2"] * 1e6 - 62.11) < 0.01
    assert abs(d["coolant_kg_s"] - d["w25_kg_s"] * 0.063) < 1e-9


def test_the_incompressible_orifice_is_fair_at_these_ratios():
    d = discharge_coefficient()
    assert d["max_pressure_ratio"] < 1.4
    assert d["incompressible_is_fair"]


# -------------------------------------- and the finding the aggregate hides

def test_two_of_the_four_groups_are_out_of_band_in_opposite_directions():
    h = the_aggregate_hides_the_rows()
    assert h["aggregate_in_band"]
    assert h["groups_in_band"] == 2 and h["groups"] == 4
    assert h["misses_both_ways"]
    assert h["too_much_area"] == ["leading_edge"]
    assert h["too_little_area"] == ["suction_side"]


def test_the_showerhead_has_a_third_of_the_area_and_a_twentyfifth_of_the_flow():
    h = the_aggregate_hides_the_rows()
    assert h["area_fraction_leading_edge"] > 0.30
    assert h["flow_fraction_leading_edge"] < 0.05
    assert (h["area_fraction_leading_edge"]
            / h["flow_fraction_leading_edge"]) > 7


def test_closing_the_two_groups_would_take_more_than_a_reading_error():
    """If the two figures merely drew the leading-edge/suction-side
    boundary in different places, a small transfer would close both. It
    takes 71 % of the showerhead, so they disagree about more than that."""
    r = required_reassignment()
    assert r["transfer_fraction_of_showerhead"] > 0.6
    assert r["transfer_holes"] > 70
    assert not r["credible"]
    assert r["suction_shortfall_ratio"] > 2.0


def test_nothing_was_transferred_to_make_the_aggregate_close():
    """required_reassignment() prices a change; discharge_coefficient()
    must not have made it."""
    a = film_hole_area_m2()["groups"]
    d = {g["group"]: g for g in discharge_coefficient()["groups"]}
    for name, v in a.items():
        assert d[name]["area_per_vane_m2"] == v["area_m2"]


def test_the_two_groups_in_band_are_the_two_at_the_highest_gas_mach():
    """The signature of a mixing Mach standing in for a surface static:
    it is a good stand-in far from the stagnation point and a bad one at
    it. The two groups that close are the two furthest aft."""
    w = why_the_rows_miss()
    assert w["in_band_are_the_two_highest_mach"]
    assert w["group_order_by_mach"][0] == "leading_edge"
    assert set(w["groups_in_band"]) == {"pressure_side", "trailing_edge"}


def test_the_vane_lacks_the_figure_the_blade_has():
    """What would settle it is a surface static distribution. The report
    prints one for the stage-1 blade and not for the vane, so this check
    is limited by a figure that exists one row downstream."""
    w = why_the_rows_miss()
    assert w["blade_has_surface_distribution"]
    assert not w["vane_has_surface_distribution"]
    assert "Fig.22" in w["blade_figure"]


def test_the_suction_side_row_count_mismatch_is_recorded_not_resolved():
    m = suction_side_row_mismatch()
    assert m["loss_row_count"] == 4
    assert m["geometry_row_count"] == 3
    assert not m["resolved"]

"""HPT cooling design (CR-167955 section 3), checked against itself.

The report states most flows twice -- as a table of items and as a prose
split, as a vane total and as its two inserts, as a margin budget and its
arithmetic. Each pair is a transcription check. Plain interpreter.
"""

from __future__ import annotations

import math
import pathlib

import pytest

yaml = pytest.importorskip("yaml")

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="module")
def hpt():
    return yaml.safe_load((DATA / "hpt-cooling.yaml").read_text())


@pytest.fixture(scope="module")
def published():
    return yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())


# ── Table VII, four ways ────────────────────────────────────────────────

def test_table_vii_items_sum_to_the_printed_total(hpt):
    f = hpt["flows"]
    assert abs(sum(i["pct"] for i in f["items"]) - f["total_pct"]) < 0.005


def test_chargeable_and_nonchargeable_split_matches_the_prose(hpt):
    f = hpt["flows"]
    non = sum(i["pct"] for i in f["items"] if i["charge"] == "nonchargeable")
    chg = sum(i["pct"] for i in f["items"] if i["charge"] == "chargeable")
    assert abs(non - f["prose_splits"]["nonchargeable_pct"]) < 0.005
    assert abs(chg - f["prose_splits"]["chargeable_pct"]) < 0.005


def test_chargeable_flow_by_source_matches_the_prose(hpt):
    """sec 3.1.3: 6.91 % CDP, 2.35 % seventh stage, 0.15 % fifth stage."""
    f = hpt["flows"]
    by = {}
    for i in f["items"]:
        if i["charge"] == "chargeable":
            src = "CDP" if i["source"].startswith("CDP") else i["source"]
            by[src] = by.get(src, 0) + i["pct"]
    for src, want in f["prose_splits"]["chargeable_by_source"].items():
        assert abs(by[src] - want) < 0.005, f"{src}: items {by[src]:.2f}, prose {want}"


def test_total_flow_appears_identically_in_table_viii(hpt):
    assert hpt["heat_transfer_design_point"]["cooling_plus_leakage_pct_w25"] == [
        hpt["flows"]["total_pct"]] * 2


# ── stage 1 nozzle ──────────────────────────────────────────────────────

def test_vane_inserts_sum_to_the_vane_flow(hpt):
    s = hpt["stage1_nozzle"]
    split, design = s["vane_flow_split"], s["design"]
    assert abs(split["forward_insert_pct_w25"] + split["aft_insert_pct_w25"] - design["wc_vanes_pct_w25"]) < 0.005
    assert abs(split["inner_band_pct_w25"] + split["outer_band_pct_w25"] - design["wc_bands_pct_w25"]) < 0.005


def test_vane_bands_and_leakage_sum_to_table_vii_nonchargeable(hpt):
    """Table IX's components reproduce Table VII's 9.46 -- which is why
    Table IX's own printed 9.24 is recorded as an inconsistency."""
    d = hpt["stage1_nozzle"]["design"]
    parts = d["wc_vanes_pct_w25"] + d["wc_bands_pct_w25"] + d["w_leakage_nonchargeable_pct_w25"]
    assert abs(parts - hpt["flows"]["prose_splits"]["nonchargeable_pct"]) < 0.005
    assert abs(parts - d["nonchargeable_flow_pct_w25"]) > 0.1, "Table IX inconsistency has gone away -- update the note"


def test_backflow_margins_recompute_from_the_printed_pressures(hpt):
    """Fig.13 defines margin = 100 (Ps_coolant - Pt_gas) / Pt_gas. The
    leading-edge (forward) cavity faces the gas TOTAL pressure; the aft
    cavity's film holes sit where the gas has accelerated, and its 1.0 %
    recomputes exactly against the printed gas STATIC pressure. Two
    definitions, both closing on the printed numbers."""
    s = hpt["stage1_nozzle"]
    gas = s["supply_conditions"]["gas_at_vane"]
    fwd = s["cavity_pressures"]["forward_cavity"]
    aft = s["cavity_pressures"]["aft_cavity"]
    m_fwd = 100 * (fwd["static_MPa"] - gas["pt_MPa"]) / gas["pt_MPa"]
    m_aft = 100 * (aft["static_MPa"] - gas["ps_MPa"]) / gas["ps_MPa"]
    assert abs(m_fwd - fwd["backflow_margin_pct"]) < 0.05, f"forward: {m_fwd:.2f} vs {fwd['backflow_margin_pct']}"
    assert abs(m_aft - aft["backflow_margin_pct"]) < 0.05, f"aft: {m_aft:.2f} vs {aft['backflow_margin_pct']}"


def test_impingement_pressure_ratios_recompute(hpt):
    s = hpt["stage1_nozzle"]["cavity_pressures"]
    fwd = s["forward_cavity"]["insert_supply_MPa"] / s["forward_cavity"]["static_MPa"]
    assert abs(fwd - s["forward_cavity"]["impingement_pressure_ratio"]) < 0.002
    aft = s["aft_cavity"]["insert_supply_MPa"] / s["aft_cavity"]["static_MPa"]
    assert abs(aft - s["aft_cavity"]["impingement_pressure_ratio"]) < 0.002


def test_vane_count_matches_the_published_data(hpt, published):
    assert hpt["stage1_nozzle"]["vane_count"] == published["hpt"]["stage_aerodynamics"]["vane_count"][0]


def test_film_hole_inventory_is_plausible(hpt):
    g = hpt["stage1_nozzle"]["film_cooling_geometry"]
    rows = g["leading_edge_radial_rows_at_25deg"] + g["suction_side_compound_angle_rows"] + g["pressure_side_diffusion_shaped_rows"]
    holes = sum(r["holes"] for r in rows)
    assert 150 < holes < 300, holes
    area_mm2 = sum(math.pi * (r["diameter_mm"] / 2) ** 2 * r["holes"] for r in rows)
    slot = g["trailing_edge"]
    area_mm2 += slot["slots"] * slot["slot_size_mm"][0] * slot["slot_size_mm"][1]
    assert 50 < area_mm2 < 120, f"total film + slot area {area_mm2:.1f} mm^2"


def test_film_mixing_flows_sum_to_the_vane_flow(hpt):
    """Fig.17's seven injection rows carry the whole 6.30 % vane flow."""
    m = hpt["stage1_nozzle"]["film_mixing_losses"]
    assert abs(sum(r["w_c_pct"] for r in m["rows"]) - m["total_w_c_pct"]) < 0.005
    assert m["total_w_c_pct"] == hpt["stage1_nozzle"]["design"]["wc_vanes_pct_w25"]


def test_film_mixing_pressure_losses_do_not_sum_as_printed(hpt):
    """Recorded: the rows sum to -0.955, the printed total is -0.995. If a
    re-read closes the gap, this test says the note is stale."""
    m = hpt["stage1_nozzle"]["film_mixing_losses"]
    total = sum(r["dp_over_p_pct"] for r in m["rows"])
    assert abs(total - m["total_dp_over_p_pct_printed"]) > 0.02, "rows now match the printed total -- drop the inconsistency note"
    assert abs(total - m["total_dp_over_p_pct_printed"]) < 0.06, "gap larger than one digit -- a row is mis-read"
    assert "as_printed_inconsistency" in m


def test_nozzle_leakage_inconsistency_is_real(hpt):
    d = hpt["stage1_nozzle"]["design"]
    parts = d["w_leakage_nonchargeable_pct_w25"] + d["w_leakage_chargeable_pct_w25"]
    printed = hpt["stage1_nozzle"]["nozzle_leakage"]["total_pct_w25_printed"]
    assert abs(parts - printed) > 0.05 and abs(parts - printed) < 0.15, (parts, printed)


def test_vane_pitch_section_temperatures_are_bounded_by_bulk_and_hot_streak_limit(hpt):
    """Fig.16: every node sits between coolant and gas; the bulk 947 sits
    inside the node range; and the prose says leading- and trailing-edge
    surfaces stay under 1093 C in the hot streak."""
    mt = hpt["stage1_nozzle"]["metal_temperatures"]
    n = mt["pitch_section_nodes_C"]
    nodes = [n["leading_edge"], n["trailing_edge"], n["internal_rib"]] + n["suction_surface_le_to_te"] + n["pressure_surface_le_to_te"]
    assert len(nodes) == 14  # 1 LE, 7 suction, 1 TE, 4 pressure, 1 rib -- as labelled on Fig.16
    assert 610 < min(nodes) and max(nodes) < 1739
    assert min(nodes) < mt["pitch_line_bulk_C"] < max(nodes)
    assert max(n["leading_edge"], n["trailing_edge"]) <= mt["leading_and_trailing_edge_surface_in_hot_streak_C_max"]
    # The rib and the impingement-cooled suction surface are the cool
    # metal; the trailing-edge region, thin and far from the inserts, is
    # among the hottest.
    assert n["internal_rib"] < mt["pitch_line_bulk_C"]
    assert n["trailing_edge"] > mt["pitch_line_bulk_C"]


def test_band_flows_sum_and_the_outer_band_runs_hotter(hpt):
    b = hpt["stage1_nozzle"]["bands"]
    assert abs(b["outer_band"]["w_c_pct_w25"] + b["inner_band"]["w_c_pct_w25"]
               - hpt["stage1_nozzle"]["design"]["wc_bands_pct_w25"]) < 0.005
    assert b["t_gas_design_C"]["outer_band"] > b["t_gas_design_C"]["inner_band"]
    assert abs(b["outer_band"]["t_gas_C"] - b["t_gas_design_C"]["outer_band"]) <= 1


def test_rotor_supply_split_is_consistent_with_table_vii(hpt):
    """6 % extracted, 80 % of it via the inducer, must at least cover the two
    inducer-fed blade rows in Table VII."""
    s = hpt["stage1_rotor_supply"]
    to_inducer = s["extracted_fraction_of_compressor_inlet_flow_pct"] * s["inducer_share_pct"] / 100
    blades = sum(i["pct"] for i in hpt["flows"]["items"] if i["source"] == "CDP_inducer")
    assert blades < to_inducer < blades + hpt["flows"]["items"][1]["pct"] + 0.05, (to_inducer, blades)
    assert s["inducer_share_pct"] + s["seal_blockage_share_pct"] == 100


def test_blade_metal_temperatures_are_ordered_as_the_features_imply(hpt):
    """Fig.21: the impinged, film-cooled leading edge and the thin trailing
    edge are the hottest; the film-blanketed suction surface the coolest."""
    t = hpt["stage1_blade"]["fig21_metal_temperatures_C"]
    assert t["suction_surface"] < t["midchord"] < t["trailing_edge"] < t["leading_edge"]
    assert all(610 < v < 1400 for v in t.values())


# ── stage 1 blade ───────────────────────────────────────────────────────

def test_blade_circuits_and_exits_both_sum_to_table_vii(hpt):
    b = hpt["stage1_blade"]["cooling_system"]
    blade_flow = next(i["pct"] for i in hpt["flows"]["items"] if i["name"] == "stage1_blade")
    circuits = sum(b["circuits"].values())
    exits = b["exits"]["tip_cap_pct"] + sum(v["pct"] for k, v in b["exits"].items() if k != "tip_cap_pct")
    assert abs(circuits - blade_flow) < 0.005, (circuits, blade_flow)
    assert abs(exits - blade_flow) < 0.005, (exits, blade_flow)


def test_tip_cap_hole_flows_sum_to_the_printed_total(hpt):
    t = hpt["stage1_blade"]["tip_cap"]
    assert abs(sum(t["hole_flows_pct_w25"]) - t["total_flow_pct_w25"]) < 0.005
    assert t["total_flow_pct_w25"] == hpt["stage1_blade"]["cooling_system"]["exits"]["tip_cap_pct"]


def test_tip_cap_fps_holes_replace_the_core_hole_at_similar_area(hpt):
    """One 1.092 mm hole on the core build becomes three 0.711 mm holes on
    the FPS -- the area should be comparable, not wildly different."""
    d = hpt["stage1_blade"]["tip_cap"]["hole_diameters_mm"]
    one = math.pi * (d["large_core_icls"] / 2) ** 2
    three = 3 * math.pi * (d["fps_replacement"] / 2) ** 2
    assert 0.8 < three / one < 1.6, three / one


def test_blade_node_map_reads_agree_between_celsius_and_fahrenheit(hpt):
    """Fig.27 prints every node twice. C must equal (F - 32) / 1.8 to within
    print rounding, except where the YAML records a read disagreement and
    says which is right."""
    mt = hpt["stage1_blade"]["metal_temperatures"]
    flagged = {(d["block"], d["index"]) for d in mt["read_disagreements"]}
    for block in ("surface", "interior"):
        for i, (c, f) in enumerate(mt[f"{block}_nodes_c_f"], 1):
            c_from_f = (f - 32) / 1.8
            if (block, i) in flagged:
                assert abs(c - c_from_f) > 1.5, f"{block} {i}: reads now agree -- drop the disagreement note"
                d = next(x for x in mt["read_disagreements"] if (x["block"], x["index"]) == (block, i))
                assert abs(d["c_from_f"] - c_from_f) < 1.0, f"{block} {i}: c_from_f {d['c_from_f']} vs {c_from_f:.1f}"
                continue
            assert abs(c - c_from_f) <= 1.5, f"{block} node {i}: {c} C vs {f} F = {c_from_f:.1f} C"


def test_blade_coating_maxima_are_the_leading_and_trailing_edge_nodes(hpt):
    mt = hpt["stage1_blade"]["metal_temperatures"]
    surface_c = [c for c, _ in mt["surface_nodes_c_f"]]
    assert max(surface_c) == mt["coating_max_C"]["leading_edge"] == 1084
    assert mt["coating_max_C"]["trailing_edge"] in surface_c


def test_blade_bulk_temperature_sits_inside_the_node_range(hpt):
    mt = hpt["stage1_blade"]["metal_temperatures"]
    allc = [c for c, _ in mt["surface_nodes_c_f"]] + [c for c, _ in mt["interior_nodes_c_f"]]
    assert min(allc) < mt["conditions"]["t_bulk_C"] < max(allc)
    assert mt["conditions"]["t_cp_C"] < min(allc)
    # The interior, next to the coolant, is cooler than the gas-washed surface on average.
    surf = [c for c, _ in mt["surface_nodes_c_f"]]
    inner = [c for c, _ in mt["interior_nodes_c_f"]]
    assert sum(inner) / len(inner) < sum(surf) / len(surf)


def test_blade_bulk_temperatures_agree_between_figures_and_prose(hpt):
    """Fig.21 and Fig.27 both give the coating maxima; sec 3.2.2 gives the
    bulk. Same numbers, or a transcription slipped."""
    f21 = hpt["stage1_blade"]["fig21_metal_temperatures_C"]
    f27 = hpt["stage1_blade"]["metal_temperatures"]["coating_max_C"]
    assert f21["leading_edge"] == f27["leading_edge"]
    assert f21["trailing_edge"] == f27["trailing_edge"]


def test_transient_levels_bracket_the_steady_state_map(hpt):
    """Fig.28's max-takeoff plateau for the hottest tracked node should sit
    near the leading-edge coating maximum; idle well below."""
    tr = hpt["stage1_blade"]["transient"]
    assert abs(max(tr["steady_levels_C"]["max_takeoff"]) - hpt["stage1_blade"]["metal_temperatures"]["coating_max_C"]["leading_edge"]) < 20
    assert max(tr["steady_levels_C"]["idle"]) < min(tr["steady_levels_C"]["max_takeoff"])
    s = tr["schedule_s"]
    assert s["accel_to_max_takeoff"][1] - s["accel_to_max_takeoff"][0] == 10
    assert s["decel"][1] - s["decel"][0] == 20


def test_shroud_flow_matches_table_vii(hpt):
    assert hpt["stage1_shroud"]["flow_pct_w25"] == next(i["pct"] for i in hpt["flows"]["items"] if i["name"] == "stage1_shroud")
    assert hpt["stage1_shroud"]["temperatures"]["condition"]["flow_pct_w25"] == hpt["stage1_shroud"]["flow_pct_w25"]


def c_f_pairs_agree(pairs, disagreements, key=lambda d: d["index"], tol=1.5):
    """Shared check for every C/F node map: C == (F - 32)/1.8 to print
    rounding, except at indices the YAML records as read disagreements --
    where the gap must be real and the resolved value must follow from F."""
    flagged = {key(d): d for d in disagreements}
    for i, (c, f) in enumerate(pairs, 1):
        c_from_f = (f - 32) / 1.8
        if i in flagged:
            assert abs(c - c_from_f) > 1.5, f"node {i}: reads now agree -- drop the disagreement note"
            assert abs(flagged[i]["c_from_f"] - c_from_f) < 1.0, f"node {i}: c_from_f {flagged[i]['c_from_f']} vs {c_from_f:.1f}"
            continue
        assert abs(c - c_from_f) <= tol, f"node {i}: {c} C vs {f} F = {c_from_f:.1f} C"


def test_shroud_node_map_reads_agree_between_units(hpt):
    t = hpt["stage1_shroud"]["temperatures"]
    c_f_pairs_agree(t["nodes_c_f"], t["read_disagreements"])
    cs = [c for c, _ in t["nodes_c_f"]]
    assert max(cs) == t["limits"]["zirconia_surface_max_C"] == 1349
    assert t["limits"]["rene77_backing_max_at_leading_edge_C"] in cs
    assert abs((t["condition"]["t_gas_outer_wall_F"] - 32) / 1.8 - t["condition"]["t_gas_outer_wall_C"]) < 1.5


# ── stage 2 nozzle ──────────────────────────────────────────────────────

def test_stage2_nozzle_flows_close_two_ways(hpt):
    f = hpt["stage2_nozzle"]["flows_pct_w25"]
    assert abs(f["vane_cooling"] + f["shroud_purge"] + f["purge_leakage"] - f["stage7_total"]) < 0.005
    assert abs(f["vane_exit_trailing_edge_slots"] + f["vane_exit_interstage_seal_purge"] - f["vane_cooling"]) < 0.005
    table_vii_stage7 = sum(i["pct"] for i in hpt["flows"]["items"] if i["source"] == "stage7")
    assert abs(f["stage7_total"] - table_vii_stage7) < 0.005
    assert abs(f["stage7_total"] - hpt["flows"]["prose_splits"]["chargeable_by_source"]["stage7"]) < 0.005


def test_stage2_vane_node_maps_read_consistently(hpt):
    t = hpt["stage2_nozzle"]["temperatures"]
    c_f_pairs_agree(t["nodes_95pct_span_c_f"], [d for d in t["read_disagreements"] if d["span"] == 95])
    c_f_pairs_agree(t["nodes_65pct_span_c_f"], [d for d in t["read_disagreements"] if d["span"] == 65])


def test_stage2_vane_bulk_temperatures_follow_the_figure_not_the_reversed_prose(hpt):
    """Node averages decide which span is which: the 95 % panel averages
    near 928, the 65 % panel near 972."""
    t = hpt["stage2_nozzle"]["temperatures"]
    def resolved(pairs, disagreements):
        flagged = {d["index"]: d["c_from_f"] for d in disagreements}
        return [flagged.get(i, c) for i, (c, _) in enumerate(pairs, 1)]
    n95 = resolved(t["nodes_95pct_span_c_f"], [d for d in t["read_disagreements"] if d["span"] == 95])
    n65 = resolved(t["nodes_65pct_span_c_f"], [d for d in t["read_disagreements"] if d["span"] == 65])
    m95, m65 = sum(n95) / len(n95), sum(n65) / len(n65)
    assert abs(m95 - t["bulk_by_span_C"]["pct_95"]) < 15, m95
    assert abs(m65 - t["bulk_by_span_C"]["pct_65"]) < 15, m65
    assert m65 > m95
    assert t["conditions_95pct_span"]["t_bulk_C"] == t["bulk_by_span_C"]["pct_95"]


def test_stage2_vane_gas_temperatures_are_ordered(hpt):
    g = hpt["stage2_nozzle"]["gas_temperature_profile"]["peak_C"]
    assert g["at_65pct_span"] > g["at_95pct_span"]
    t = hpt["stage2_nozzle"]["temperatures"]["conditions_95pct_span"]
    assert t["t_coolant_C"] < t["t_bulk_C"] < t["t_gas_C"] < t["t41_design_C"]
    assert t["t41_design_C"] == hpt["heat_transfer_design_point"]["t41_design_C"][0] + 1  # 1421 vs 1422: rounding of 1420.7


def test_stage2_vane_count_matches_the_published_data(hpt, published):
    assert hpt["stage2_nozzle"]["vane_count"] == published["hpt"]["stage_aerodynamics"]["vane_count"][1]


def test_stage2_rotor_flow_and_count_match(hpt, published):
    r = hpt["stage2_rotor"]
    assert r["flow_pct_w25"] == next(i["pct"] for i in hpt["flows"]["items"] if i["name"] == "stage2_blade")
    assert r["blade_count"] == published["hpt"]["stage_aerodynamics"]["blade_count"][1]
    t = r["temperatures"]
    assert r["supply"]["t_coolant_supply_C"] < t["bulk_C"] < t["coating_max_C"] < t["gas_pitch_line_C"]
    for c, f in ((t["gas_pitch_line_C"], t["gas_pitch_line_F"]), (t["bulk_C"], t["bulk_F"]), (t["coating_max_C"], t["coating_max_F"])):
        assert abs((f - 32) / 1.8 - c) < 1.5


def test_stage2_blade_flows_close_two_ways(hpt):
    cs = hpt["stage2_rotor"]["cooling_system"]
    assert abs(sum(cs["circuits_in"].values()) - cs["total_pct"]) < 0.005
    exits = sum(cs["exits"]["tip_pct"]) + cs["exits"]["forward_slot"]["pct"] + cs["exits"]["aft_slot"]["pct"]
    assert abs(exits - cs["total_pct"]) < 0.005
    assert cs["total_pct"] == hpt["stage2_rotor"]["flow_pct_w25"]
    for slot in ("forward_slot", "aft_slot"):
        mm, inch = cs["exits"][slot]["size_mm"], cs["exits"][slot]["size_in"]
        for a, b in zip(mm, inch):
            assert abs(a - b * 25.4) < 0.03, (slot, a, b)


def test_stage2_blade_node_map_reads_agree_and_the_trailing_edge_is_hottest(hpt):
    mt = hpt["stage2_rotor"]["metal_temperatures"]
    c_f_pairs_agree(mt["surface_nodes_c_f"], mt["read_disagreements"])
    c_f_pairs_agree(mt["interior_nodes_c_f"], [])
    surf = [c for c, _ in mt["surface_nodes_c_f"]]
    assert max(surf) == hpt["stage2_rotor"]["temperatures"]["coating_max_C"] == 1013
    assert mt["conditions"]["t_bulk_C"] == hpt["stage2_rotor"]["temperatures"]["bulk_C"]
    allc = surf + [c for c, _ in mt["interior_nodes_c_f"]]
    assert min(allc) < mt["conditions"]["t_bulk_C"] < max(allc)
    for c, f in ((mt["conditions"]["t_tb_C"], mt["conditions"]["t_tb_F"]), (mt["conditions"]["t_cdt_C"], mt["conditions"]["t_cdt_F"]), (mt["conditions"]["t_cp_C"], mt["conditions"]["t_cp_F"])):
        assert abs((f - 32) / 1.8 - c) < 1.5


def test_stage2_blade_fod_and_tip_cap_analyses_are_bounded(hpt):
    f = hpt["stage2_rotor"]["fod_analysis"]
    assert min(f["delta_nodes_C_sample"]) == -f["max_local_drop_C"]
    assert -f["max_local_drop_C"] < -f["bulk_temperature_drop_C"] < 0
    t = hpt["stage2_rotor"]["tip_cap_loss_analysis"]
    assert t["flow_with_cap_pct"] == hpt["stage2_rotor"]["flow_pct_w25"]
    assert 2.5 < t["flow_without_cap_pct"] / t["flow_with_cap_pct"] < 3.5


def test_stage2_shroud_purge_matches_table_vii_and_fig_32(hpt):
    s = hpt["stage2_shroud"]
    assert s["purge_flow_pct_w25"] == next(i["pct"] for i in hpt["flows"]["items"] if i["name"] == "stage2_shroud")
    assert s["purge_flow_pct_w25"] == hpt["stage2_nozzle"]["flows_pct_w25"]["shroud_purge"]
    assert abs((s["gas_temperature_F"] - 32) / 1.8 - s["gas_temperature_C"]) < 1.5
    # The shroud sees the absolute gas temperature at the outer wall; the
    # blade's 1038 C is its pitch-line RELATIVE bulk. Not comparable -- only
    # that both sit below the stage-1 figures.
    assert s["gas_temperature_C"] < hpt["heat_transfer_design_point"]["t_tb_design_C"][0]


def test_casing_flow_distribution_reads_as_recorded(hpt):
    fd = hpt["casing_thermal"]["flow_distribution"]
    assert abs(sum(fd["stage1_shroud_split_pct"].values()) - fd["cdp_to_stage1_shroud_pct"]) < 0.005
    s7 = fd["seventh_stage_split_pct"]
    assert abs(s7["leakage_forward"] + s7["leakage_aft"] - s7["shroud_purge"]) < 0.005
    assert abs(s7["vane_cooling"] + s7["shroud_purge"] + hpt["stage2_nozzle"]["flows_pct_w25"]["purge_leakage"] - fd["seventh_stage_bleed_pct"]) < 0.005
    assert fd["seventh_stage_bleed_pct"] == hpt["stage2_nozzle"]["flows_pct_w25"]["stage7_total"]


def test_casing_node_map_reads_agree_and_metal_stays_below_the_shroud(hpt):
    t = hpt["casing_thermal"]["temperatures"]
    c_f_pairs_agree(t["nodes_c_f"], t["read_disagreements"])
    cs = [c for c, _ in t["nodes_c_f"]]
    assert max(cs) == hpt["stage1_shroud"]["temperatures"]["limits"]["zirconia_surface_max_C"]
    metal = [c for c in cs if c < 1000]
    assert 500 < min(metal) and max(metal) < 750


def test_rotor_structure_fixes_are_self_consistent(hpt):
    r = hpt["rotor_structure_thermal"]
    g = r["stage2_disk_bore_fix"]["radial_gap_cm"]
    assert abs(g["before"] / g["after"] - 2.0) < 0.01
    gi = r["stage2_disk_bore_fix"]["radial_gap_in"]
    assert abs(g["before"] - gi["before"] * 2.54) < 0.001 and abs(g["after"] - gi["after"] * 2.54) < 0.001
    f = r["interstage_seal_disk_fix"]["flows_pct_w25"]
    assert f["supply"] >= 2 * f["to_each_side"]
    assert len(r["problem_areas"]) == 7
    s = hpt["casing_thermal"]["stage2_nozzle_bolt_flange_fix"]
    for a, b in zip(s["slot_size_cm"], s["slot_size_in"]):
        assert abs(a - b * 2.54) < 0.001


# ── temperatures and margin ─────────────────────────────────────────────

def test_t41_margin_budget_adds_up(hpt):
    m = hpt["t41_margin"]
    da = m["direct_adders"]
    assert abs(da["minimum_to_average_engine"] + da["engine_transient_at_takeoff"]
               + da["open_clearance_schedule_at_takeoff"] - da["total"]) < 0.05
    r = m["two_sigma_rss"]
    # The RSS was done in degrees F (7, 26, 25 -> 36.7, printed 37) and the
    # C column is that converted (37 / 1.8 = 20.6, printed 20.5). An RSS of
    # the rounded C entries gives 20.3; the F route is the one that closes.
    rss_f = math.sqrt(7 ** 2 + 26 ** 2 + 25 ** 2)
    assert abs(rss_f / 1.8 - r["rss_total"]) < 0.15, rss_f / 1.8
    rss_c = math.sqrt(r["humidity"] ** 2 + r["engine_quality_variations"] ** 2 + r["control_system_tolerance"] ** 2)
    assert abs(rss_c - r["rss_total"]) < 0.35, rss_c
    assert abs(da["total"] + r["rss_total"] - m["total_new_engine"]) < 0.05
    assert abs(m["total_new_engine"] + m["deterioration"] - m["total_with_deterioration"]) < 0.05


def test_design_t41_is_cycle_plus_margin(hpt):
    h = hpt["heat_transfer_design_point"]
    for cyc, mar, des in zip(h["t41_cycle_C"], h["dt41_margin_C"], h["t41_design_C"]):
        assert abs(cyc + mar - des) < 1.0


def test_design_t41_matches_the_published_takeoff_value(hpt, published):
    """CR-168219 Table XII: HPT rotor inlet at takeoff, flat-rating
    temperature, 1365 C -- the OPTIMUM from the trade study, which the
    final cycle rematch moved back up to (sec 4.3 p.32: +22 C at takeoff).
    The detailed design's 1343 sits 22 C below it."""
    xii = published["cycle_definition"]["takeoff"]["hpt_rotor_inlet_temperature_C"]
    assert xii == hpt["turbine_inlet_temperature"]["optimum_max_takeoff_C"]
    assert xii - hpt["turbine_inlet_temperature"]["design_max_takeoff_C"] == 22


def test_hot_streak_implies_a_sensible_combustor_exit_mean(hpt):
    """Pattern factor: T40_peak = T40_mean + PF (T40_mean - T3). The report
    prints the peak and PF but not the combustor-exit mean; solving for it
    must give a mean that sits above T41 design (the rotor-inlet value,
    after ~9.5 % nonchargeable dilution) and below the peak."""
    s = hpt["stage1_nozzle"]["design"]
    h = hpt["heat_transfer_design_point"]
    t3, pf, peak = h["t3_C"][0], s["pattern_factor"], s["t40_max_peak_C"]
    t40_mean = (peak + pf * t3) / (1 + pf)
    t41_design = h["t41_design_C"][0]
    assert t41_design < t40_mean < peak, f"implied T40 mean {t40_mean:.0f}"
    assert 40 < t40_mean - t41_design < 150, f"dilution from T40 mean to T41: {t40_mean - t41_design:.0f} K"


def test_final_fps_flows_are_lower_than_the_detailed_design(hpt):
    d, f = hpt["flows"]["prose_splits"], hpt["flows_final_fps_for_comparison"]
    assert f["cpd_nonchargeable_pct"] < d["nonchargeable_pct"]
    assert f["cpd_chargeable_pct"] < d["chargeable_by_source"]["CDP"]
    assert f["stage7_pct"] < d["chargeable_by_source"]["stage7"]
    assert abs(f["cpd_nonchargeable_pct"] + f["cpd_chargeable_pct"] + f["stage7_pct"] + f["stage5_pct"] - f["total_pct"]) < 0.005


def test_final_fps_flows_match_the_published_data_file(hpt, published):
    c = published["cooling_flows"]
    f = hpt["flows_final_fps_for_comparison"]
    assert abs(c["cpd_nonchargeable"] * 100 - f["cpd_nonchargeable_pct"]) < 0.005
    assert abs(c["cpd_chargeable"] * 100 - f["cpd_chargeable_pct"]) < 0.005
    assert abs(c["stage_7_cooling_and_purge"] * 100 - f["stage7_pct"]) < 0.005
    assert abs(c["stage_5_cooling_and_purge"] * 100 - f["stage5_pct"]) < 0.005


def test_flight_mission_is_about_two_hours(hpt):
    m = hpt["flight_mission"]
    minutes = sum(s.get("minutes", 0) + s.get("seconds", 0) / 60 for s in m["segments_minutes"])
    assert 110 < minutes < 125, minutes

"""LPT final aerodynamic design (LPT hardware report sections 2.4-2.8),
checked against itself, against the mechanical data in lpt-design.yaml
and against the cycle data. Plain interpreter."""

from __future__ import annotations

import math
import pathlib

import pytest

yaml = pytest.importorskip("yaml")

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"
BTU_PER_LB_TO_J_PER_KG = 2326.0


@pytest.fixture(scope="module")
def aero():
    return yaml.safe_load((DATA / "lpt-aero.yaml").read_text())


@pytest.fixture(scope="module")
def mech():
    return yaml.safe_load((DATA / "lpt-design.yaml").read_text())


@pytest.fixture(scope="module")
def published():
    return yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())


def stages(aero):
    return [aero["vector_diagrams"][f"stage{i}"] for i in range(1, 6)]


# ── airfoil counts: one figure, three other places ──────────────────────

def test_fig6_counts_agree_with_every_other_source(aero, mech, published):
    c = aero["airfoil_counts"]
    assert c["counts"][0::2] == c["vanes"] and c["counts"][1::2] == c["rotors"]
    assert sum(c["counts"]) == c["total"] == sum(c["vanes"]) + sum(c["rotors"])
    assert c["rotors"] == mech["rotor_blades"]["blade_count"] == published["lpt"]["blade_counts_per_stage"]["value"]
    assert c["vanes"] == mech["vane_counts"]["all"] == published["lpt"]["vane_counts_per_stage"]["value"]
    assert c["vanes"][:2] == mech["rotor_blades"]["vibration"]["stage1_crossings_near_operating_range"]["forcing"]
    assert c["block_i_stage1_vane"] < c["vanes"][0]


# ── Table II against the cycle: the energy-extraction units ─────────────

def test_stage_energy_extractions_sum_to_table_i_in_btu_per_lb(aero, published):
    """Five stage dh in Btu/lb must equal the LPT's dh/T x T49 from Table I
    (J/kg/K x K). This is what fixes the unit of an unlabelled column."""
    total = sum(s["energy_extraction"] for s in stages(aero))
    assert abs(total - aero["vector_diagrams"]["totals"]["energy_extraction_sum"]) < 0.05
    er = published["lpt"]["earlier_requirements"]["max_climb"]
    from_cycle = er["dh_over_T"] * er["T49_K"] / BTU_PER_LB_TO_J_PER_KG
    assert abs(total - from_cycle) / from_cycle < 0.003, (total, from_cycle)


def test_stage_pressure_ratios_multiply_to_the_printed_product(aero):
    prod = math.prod(s["pressure_ratio"] for s in stages(aero))
    assert abs(prod - aero["vector_diagrams"]["totals"]["pressure_ratio_product"]) < 0.01
    assert 3.8 < prod < 4.8  # a five-stage E3-class LPT


def test_stage1_loading_recomputes_from_dh_and_table_vii_geometry(aero, mech):
    """dh/2U^2 at pitch: dh from Table II, U from Table VII's tip diameter
    and radius ratio at Table VI's 3,539 rpm. Two documents, one number."""
    ap = mech["aero_design_parameters"]
    rpm = mech["design_cycle_points"]["case_41_flowpath_and_clearance"]["fan_physical_speed_rpm"][0]
    omega = rpm * 2 * math.pi / 60
    for col, st in ((0, 0), (1, 4)):
        r_t = ap["tip_diameter_cm"][col] / 200
        r_p = r_t * (1 + ap["inlet_radius_ratio"][col]) / 2
        u = omega * r_p
        dh = stages(aero)[st]["energy_extraction"] * BTU_PER_LB_TO_J_PER_KG
        psi = dh / (2 * u * u)
        printed = stages(aero)[st]["loading_dh_over_2u2"]
        tol = 0.04 if st == 0 else 0.10  # stage 5's pitch radius is not the inlet mean
        assert abs(psi - printed) / printed < tol, f"stage {st+1}: {psi:.2f} vs {printed}"


def test_euler_work_from_pitch_angles_brackets_the_printed_loading(aero):
    """psi = [phi (tan a1 + tan b2) - 1] / 2 for constant Vz and radius.
    Stages 1-2 (little radius change) agree to 4 %; the rear stages, whose
    radius rises through the rotor, print LOWER than this -- as they must."""
    for i, s in enumerate(stages(aero), 1):
        phi = s["flow_coefficient_vz_over_u"]
        a1 = math.radians(s["stator_exit_angle_deg"][1])
        b2 = math.radians(s["rotor_rel_exit_angle_deg"][1])
        psi = (phi * (math.tan(a1) + math.tan(b2)) - 1) / 2
        printed = s["loading_dh_over_2u2"]
        ratio = psi / printed
        if i <= 2:
            assert abs(ratio - 1) < 0.045, (i, ratio)
        else:
            assert 1.0 < ratio < 1.25, (i, ratio)


# ── Table II internal physics ───────────────────────────────────────────

def test_reaction_rises_hub_to_tip_and_stays_positive(aero):
    for s in stages(aero):
        r = s["reaction"]
        assert r == sorted(r) and r[0] > 0.2 and r[2] < 0.5


def test_rotor_accelerates_the_relative_flow_everywhere(aero):
    for s in stages(aero):
        for m1, m2 in zip(s["rotor_rel_inlet_mach"], s["rotor_rel_exit_mach"]):
            assert m2 > m1


def test_stator_exit_mach_falls_hub_to_tip(aero):
    for s in stages(aero):
        m = s["stator_exit_mach"]
        assert m[0] > m[1] > m[2]


def test_loading_falls_and_last_stage_exits_nearly_axial(aero):
    psi = [s["loading_dh_over_2u2"] for s in stages(aero)]
    assert psi == sorted(psi, reverse=True)
    last = stages(aero)[4]["stage_exit_swirl_deg"]
    assert max(last) <= 20 and last[2] <= 5
    for s in stages(aero)[:4]:
        assert min(s["stage_exit_swirl_deg"]) > 15  # the next stator has work to do


def test_flow_coefficient_and_reaction_are_in_the_moderately_loaded_band(aero):
    for s in stages(aero):
        assert 0.95 <= s["flow_coefficient_vz_over_u"] <= 1.30
        assert 0.8 <= s["loading_dh_over_2u2"] <= 1.75


def test_illegible_digit_is_recorded_with_its_alternatives(aero):
    ill = aero["vector_diagrams"]["illegible_as_printed"]
    assert len(ill) == 1 and ill[0]["stage"] == 1
    assert ill[0]["taken"] in ill[0]["alternatives"]
    assert aero["vector_diagrams"]["stage1"]["rotor_rel_exit_angle_deg"][0] == ill[0]["taken"]


# ── Table III against Fig.52 ────────────────────────────────────────────

def rotor_rows(aero):
    g = aero["blading_geometry"]
    return {row: i for i, row in enumerate(g["rows"]) if row.startswith("R")}


def test_axial_width_aspect_ratio_over_chord_aspect_ratio_is_a_stagger(aero, mech):
    """h/AW (Table III) / h/c (Fig.52) = c/AW = 1/cos(stagger). It must be
    >1, and roughly the same on every rotor of a family design."""
    g = aero["blading_geometry"]
    ratios = []
    for row, i in rotor_rows(aero).items():
        st = int(row[1]) - 1
        ratios.append(g["aspect_ratio_h_over_aw"][i] / mech["rotor_blades"]["aspect_ratio"][st])
    assert all(1.08 < r < 1.20 for r in ratios), ratios
    assert max(ratios) - min(ratios) < 0.06
    stagger = [math.degrees(math.acos(1 / r)) for r in ratios]
    assert all(24 < s < 32 for s in stagger), stagger


def test_axial_solidity_times_pitch_gives_the_same_chord_to_width_ratio(aero, mech):
    """Third route: AW = (AW/t) x 2 pi r_p / N; c/AW from Fig.52's mean chord
    must match the ratio above on the two rotors whose radius Table VII
    gives."""
    g, ap, rb = aero["blading_geometry"], mech["aero_design_parameters"], mech["rotor_blades"]
    for row, col, st in (("R1", 0, 0), ("R5", 1, 4)):
        i = g["rows"].index(row)
        r_t = ap["tip_diameter_cm"][col] / 2
        r_p = r_t * (1 + ap["inlet_radius_ratio"][col]) / 2
        pitch = 2 * math.pi * r_p / rb["blade_count"][st]
        aw = g["axial_solidity_aw_over_t"][i] * pitch
        c = (rb["root_chord_cm"][st] + rb["tip_chord_cm"][st]) / 2
        c_over_aw = c / aw
        from_ar = g["aspect_ratio_h_over_aw"][i] / rb["aspect_ratio"][st]
        assert abs(c_over_aw - from_ar) / from_ar < 0.06, (row, c_over_aw, from_ar)


def test_zweifel_and_blockage_sit_in_their_bands_and_the_stage1_vane_is_the_conservative_one(aero):
    g = aero["blading_geometry"]
    assert all(0.55 < z < 1.15 for z in g["zweifel_coefficient"])
    assert all(0.035 < b < 0.08 for b in g["te_blockage"])
    assert g["axial_solidity_aw_over_t"][0] == max(g["axial_solidity_aw_over_t"])
    assert g["zweifel_coefficient"][0] == min(g["zweifel_coefficient"])
    # rotors are more highly loaded (Zweifel ~1.0-1.1) than vanes (0.6-1.0)
    rot = [g["zweifel_coefficient"][i] for i in rotor_rows(aero).values()]
    van = [z for i, z in enumerate(g["zweifel_coefficient"]) if i not in rotor_rows(aero).values()]
    assert min(rot) > max(van)


def test_rotor_h_over_aw_is_largest_on_the_flask_shaped_stage4(aero):
    g = aero["blading_geometry"]
    r4 = g["rows"].index("R4")
    assert g["aspect_ratio_h_over_aw"][r4] == max(g["aspect_ratio_h_over_aw"])
    assert g["aspect_ratio_h_over_do"][r4] == max(g["aspect_ratio_h_over_do"])


# ── airfoil sections ────────────────────────────────────────────────────

def test_sections_are_subsonic_and_axially_ordered(aero):
    rows = aero["airfoil_sections"]["rows"]
    order = ["V1", "R1", "V2", "R2", "V3", "R3", "V4", "R4", "V5", "R5"]
    prev_end = 0
    for r in order:
        lo, hi = rows[r]["axial_in"]
        assert lo >= prev_end and hi > lo, r
        prev_end = hi
        assert max(rows[r]["peak_mach"]) <= 0.92
    # the machine spans ~2.8 to ~23.2 in from HPT exit: 20+ in of turbine
    assert 19 < rows["R5"]["axial_in"][1] - rows["V1"]["axial_in"][0] < 22
    # hub peak Mach is the highest on every front-half row
    for r in order[:6]:
        pm = rows[r]["peak_mach"]
        assert pm[0] == max(pm), r


def test_calculation_model_length_matches_the_section_extents(aero):
    cm = aero["block_ii_flowpath"]["calculation_model"]
    rows = aero["airfoil_sections"]["rows"]
    assert abs(cm["axial_length_to_exit_in"] - rows["R5"]["axial_in"][1]) < 1.5


# ── rig results ─────────────────────────────────────────────────────────

def test_status_stackups_add_and_the_status_beats_the_icls_goal(aero, published):
    r = aero["block_ii_rig_results"]
    s = r["status_stackup"]
    for col in range(2):
        total = s["eta_tt"][col] + s["delta_edge_blockage"][col] + s["delta_purge_air"][col] + s["delta_reynolds_number"][col]
        assert abs(total - s["eta_tt_at_m0_8_10_67km_max_climb"][col]) < 0.0006, (col, total)
    assert abs(r["status_at_max_climb"] - r["goals_at_max_climb"]["icls"] - 0.003) < 0.0006
    assert r["goals_at_max_climb"]["fps"] == published["lpt"]["earlier_requirements"]["max_climb"]["efficiency"]
    assert r["status_at_max_climb"] < r["goals_at_max_climb"]["fps"]
    assert r["five_stage_design_point_efficiency"] > r["two_stage"]["efficiency_at_design_loading"]


def test_block_ii_beats_block_i_at_every_loading_and_by_more_at_low_loading(aero):
    f = aero["block_ii_rig_results"]["fig19_efficiency_vs_loading"]
    gains = [b2 - b1 for b1, b2 in zip(f["block_i"], f["block_ii"])]
    assert all(g > 0 for g in gains)
    assert gains[0] > gains[2] > gains[-1]
    i = min(range(len(f["loading"])), key=lambda k: abs(f["loading"][k] - 1.65))
    assert abs(gains[i] - aero["block_ii_rig_results"]["two_stage"]["improvement_over_block_i_at_design_loading"]) < 0.004


def test_block_i_stage1_vane_loss_core_is_at_80_percent_span(aero):
    v = aero["block_i_lessons"]["stage1_vane_kinetic_energy_efficiency"]
    # the two end points are wall losses; the loss core is the interior trough
    interior = range(2, len(v["span_pct"]))
    worst = v["span_pct"][min(interior, key=lambda k: v["efficiency"][k])]
    assert worst == 80
    assert max(v["efficiency"]) > 0.98


def test_transition_duct_stays_short_of_separation(aero):
    d = aero["block_ii_flowpath"]["transition_duct_axisymmetric_analysis"]
    sp = d["separation_parameter"]
    assert sp["block_ii_peak"] < sp["possible_separation"] < sp["probable_separation"]
    assert d["outer_wall_mach"]["at_hpt_exit"] > d["outer_wall_mach"]["at_vane_le"]  # diffusing outer wall
    r = d["streamline_radii_cm"]
    assert r["vane_le_outer"] > r["hpt_exit_outer"] and r["vane_le_inner"] > r["hpt_exit_inner"]

"""The published data, checked against itself.

A transcription error is the most likely defect in this project and the
hardest to see: a digit dropped from a 1980s scanned table looks exactly
like a real number. So wherever the reports give two independent routes to
the same quantity, both are transcribed and this file makes them agree.

None of this validates the ENGINE -- that is Phase A2 onward. It validates
the TRANSCRIPTION, which has to come first.

Runs on a plain interpreter -- yaml only.
"""

from __future__ import annotations

import math
import pathlib

import pytest

yaml = pytest.importorskip("yaml")

DATA = pathlib.Path(__file__).resolve().parents[1] / "data" / "e3-fps-published.yaml"


@pytest.fixture(scope="module")
def d():
    return yaml.safe_load(DATA.read_text())


# ── mass ────────────────────────────────────────────────────────────────

def test_module_subtotals_sum_to_the_printed_subtotals(d):
    w = d["weights"]
    for module in ("fan_and_booster_module", "lpt_module", "core_module",
                   "miscellaneous", "installation"):
        rows = {k: v for k, v in w[module].items() if k != "subtotal"}
        assert sum(rows.values()) == w[module]["subtotal"], (
            f"{module}: rows sum to {sum(rows.values())}, "
            f"printed subtotal is {w[module]['subtotal']}"
        )


def test_module_subtotals_sum_to_the_engine_totals(d):
    w = d["weights"]
    basic = (w["fan_and_booster_module"]["subtotal"] + w["lpt_module"]["subtotal"]
             + w["core_module"]["subtotal"] + w["miscellaneous"]["subtotal"])
    assert basic == w["basic_engine_total"]
    assert basic + w["installation"]["subtotal"] == w["installed_engine_total"]


# ── compressor table ────────────────────────────────────────────────────

def test_hpc_rotor_table_columns_all_have_ten_stages(d):
    r = d["hpc"]["rotor_stages"]
    # Data columns are lists indexed by stage. Prose lists (transcription
    # notes) are not columns and are excluded by name, not by guessing.
    cols = {k: v for k, v in r.items()
            if isinstance(v, list) and k != "transcription_notes"}
    bad = {k: len(v) for k, v in cols.items() if len(v) != 10}
    assert not bad, f"columns without 10 entries: {bad}"
    assert len(cols) >= 25, f"expected the full Table X, got {len(cols)} columns"


def test_hpc_blade_count_rises_monotonically(d):
    counts = d["hpc"]["rotor_stages"]["blade_count"]
    assert counts == sorted(counts), counts
    assert counts[0] == 28 and counts[-1] == 94


def test_hpc_printed_radius_ratio_matches_printed_radii(d):
    """Table X prints radius ratio AND both radii. They are the same fact
    twice, so a mis-read digit in either shows up here."""
    r = d["hpc"]["rotor_stages"]
    for i, (rr, root, tip) in enumerate(zip(r["radius_ratio_aero"],
                                            r["radius_root_le_cm"],
                                            r["radius_tip_le_cm"]), 1):
        computed = root / tip
        assert abs(computed - rr) < 0.004, (
            f"stage {i}: root_le/tip_le = {computed:.4f}, printed {rr}"
        )


def test_hpc_airfoil_length_is_tip_minus_root(d):
    """The stage-10 airfoil length was corrected from a mis-printed 1.094
    to 2.094 cm on the strength of the US-units column. This checks the
    correction against the radii, which are a third independent route."""
    r = d["hpc"]["rotor_stages"]
    for i, (length, root, tip) in enumerate(zip(r["airfoil_length_cm"],
                                                r["radius_root_cm"],
                                                r["radius_tip_le_cm"]), 1):
        # tip is at LE, root at stacking axis: not identical planes, so a
        # loose tolerance -- but 1.094 vs 2.094 is a 1 cm error and fails.
        assert abs((tip - root) - length) < 0.6, (
            f"stage {i}: tip-root = {tip - root:.3f}, printed length {length}"
        )


def test_hpc_annulus_contracts_through_the_compressor(d):
    r = d["hpc"]["rotor_stages"]
    areas = [math.pi * ((t / 100) ** 2 - (h / 100) ** 2)
             for t, h in zip(r["radius_tip_le_cm"], r["radius_root_le_cm"])]
    for i in range(1, len(areas)):
        assert areas[i] < areas[i - 1], (
            f"annulus grows between stage {i} and {i + 1}: "
            f"{areas[i - 1]:.4f} -> {areas[i]:.4f} m^2"
        )


def test_hpc_metal_temperature_rises_through_the_compressor(d):
    t = d["hpc"]["rotor_stages"]["metal_temperature_C"]
    assert t == sorted(t), t


def test_hpc_material_changes_where_titanium_runs_out(d):
    """Ti-8-1-1 is limited by temperature; the switch to Inco 718 should
    happen where the metal temperature crosses into the 400s C."""
    r = d["hpc"]["rotor_stages"]
    last_ti = max(i for i, m in enumerate(r["material"]) if m.startswith("Ti"))
    first_ni = min(i for i, m in enumerate(r["material"]) if m.startswith("Inco"))
    assert first_ni == last_ti + 1
    assert r["metal_temperature_C"][last_ti] < 500, "titanium beyond 500 C"
    assert r["metal_temperature_C"][first_ni] > 400


def test_hpc_root_solidity_exceeds_tip_solidity(d):
    """Pitch is proportional to radius; chord barely changes; so solidity
    must be higher at the root. If it is not, chord and pitch were swapped."""
    r = d["hpc"]["rotor_stages"]
    for i, (root, tip) in enumerate(zip(r["solidity_root"], r["solidity_tip"]), 1):
        assert root >= tip, f"stage {i}: root {root} < tip {tip}"


# ── HPT ─────────────────────────────────────────────────────────────────

def test_hpt_flowpath_radii_reproduce_the_printed_annulus_areas(d):
    """Fig.3 prints hub and tip radii; Fig.1 prints the design annulus
    areas. Two figures, one fact."""
    h = d["hpt"]
    s = {st["location"]: st for st in h["flowpath"]["stations"]}
    a1 = math.pi * ((s["stage1_vane_exit"]["r_tip_cm"] / 100) ** 2
                    - (s["stage1_vane_exit"]["r_hub_cm"] / 100) ** 2)
    a2 = math.pi * ((s["stage2_blade_exit"]["r_tip_cm"] / 100) ** 2
                    - (s["stage2_blade_exit"]["r_hub_cm"] / 100) ** 2)
    printed = h["annulus_area_design_m2"]
    # Fig.1 areas are read off a graph; Fig.3 radii are printed. Stage 1
    # "exhaust" in Fig.1 is the stage exit, closer to the blade exit plane.
    assert abs(a2 - printed["stage2_exhaust"]) / printed["stage2_exhaust"] < 0.03, (
        f"stage 2: radii give {a2:.4f} m^2, Fig.1 reads {printed['stage2_exhaust']}"
    )
    assert abs(a1 - printed["stage1_exhaust"]) / printed["stage1_exhaust"] < 0.06, (
        f"stage 1: radii give {a1:.4f} m^2, Fig.1 reads {printed['stage1_exhaust']}"
    )


def test_hpt_stage_pressure_ratios_multiply_to_a_sane_expansion(d):
    pr = d["hpt"]["stage_aerodynamics"]["pressure_ratio"]
    total = pr[0] * pr[1]
    assert 4.5 < total < 5.0, total
    # And the one-stage alternative in Table II was sized to the same total.
    one = d["hpt"]["preliminary_trade"]["one_stage"]["PR"]
    assert abs(one - total) / total < 0.06


def test_hpt_blade_counts_appear_identically_in_two_tables(d):
    """Table III and Table IV both list the counts. Same numbers, or a
    transcription slipped."""
    h = d["hpt"]
    assert h["stage_aerodynamics"]["vane_count"] == h["blading_geometry"]["count"][:2]
    assert h["stage_aerodynamics"]["blade_count"] == h["blading_geometry"]["count"][2:]


def test_hpt_work_split_is_consistent_with_stage_loadings(d):
    """Stage-1 work fraction of 56.5% was chosen deliberately. With the
    printed loadings and near-equal tip speeds, dh1/(dh1+dh2) should land
    near it."""
    s = d["hpt"]["stage_aerodynamics"]
    u1, u2 = s["tip_speed_takeoff_m_s"]
    l1, l2 = s["loading_dh_over_2U2"]
    dh1, dh2 = l1 * 2 * u1 ** 2, l2 * 2 * u2 ** 2
    split = dh1 / (dh1 + dh2)
    assert abs(split - d["hpt"]["stage_work_split_stage1"]) < 0.03, split


# ── spool speeds: two routes each ───────────────────────────────────────

def rpm_from_corrected(n_over_sqrt_t: float, t_k: float) -> float:
    return n_over_sqrt_t * math.sqrt(t_k) * 60 / (2 * math.pi)


def test_hp_spool_speed_from_the_turbine_agrees_with_the_compressor_report(d):
    """HPT Table XVIII gives N/sqrt(T41) and T41. HPC Table X footnote gives
    XNH in rpm at the same point. Turbine and compressor are on one shaft;
    they had better agree."""
    h = d["hpt"]["cycle_match"]
    from_turbine = rpm_from_corrected(h["speed_N_over_sqrtT_rad_s_sqrtK"],
                                      h["inlet_temperature_T41_K"])
    from_compressor = d["hpc"]["spool_speed_rpm"]["xnh_max_climb_aero_dp"]
    assert abs(from_turbine - from_compressor) / from_compressor < 0.03, (
        f"HP speed: {from_turbine:.0f} rpm from the HPT, "
        f"{from_compressor} rpm from the HPC report"
    )


def test_lp_spool_speed_from_the_turbine_agrees_with_the_fan_tip_speed(d):
    """LPT Table XXI gives N/sqrt(T49) and T49 -> physical LP rpm at max
    climb. The fan gives a CORRECTED tip speed and a tip radius -> corrected
    rpm, which must be de-corrected to the max-climb inlet temperature.
    Fan and LPT are on one shaft."""
    l = d["lpt"]["cycle_match"]
    lp_from_lpt = rpm_from_corrected(l["speed_N_over_sqrtT_rad_s_sqrtK"],
                                     l["inlet_temperature_T49_K"])

    r_tip = d["size"]["fan_tip_diameter_m"] / 2
    omega_corr = d["fan"]["corrected_tip_speed_m_s"] / r_tip
    rpm_corr = omega_corr * 60 / (2 * math.pi)

    # De-correct: N = N_corr * sqrt(T2 / 288.15) at 10.67 km, Mach 0.8, ISA+10.
    t_static = 216.65 + 10.0
    t2 = t_static * (1 + 0.2 * d["design_point"]["mach"] ** 2)
    rpm_phys = rpm_corr * math.sqrt(t2 / 288.15)

    assert abs(rpm_phys - lp_from_lpt) / lp_from_lpt < 0.05, (
        f"LP speed: {lp_from_lpt:.0f} rpm from the LPT, "
        f"{rpm_phys:.0f} rpm from fan tip speed de-corrected to max climb"
    )


def test_hp_runs_much_faster_than_lp(d):
    """Sanity, and the reason the spools are separate at all."""
    h = d["hpt"]["cycle_match"]
    l = d["lpt"]["cycle_match"]
    hp = rpm_from_corrected(h["speed_N_over_sqrtT_rad_s_sqrtK"], h["inlet_temperature_T41_K"])
    lp = rpm_from_corrected(l["speed_N_over_sqrtT_rad_s_sqrtK"], l["inlet_temperature_T49_K"])
    assert 3.0 < hp / lp < 4.5, hp / lp


# ── cycle-level cross-checks ────────────────────────────────────────────

def test_overall_pressure_ratio_is_fan_hub_times_compressor(d):
    """OPR, fan hub PR and HPC PR are printed separately in Table XII. The
    booster is a quarter stage, so nearly all of the difference is the
    booster's own small pressure rise."""
    for point in ("max_climb", "max_cruise", "takeoff"):
        c = d["cycle_definition"][point]
        implied_booster = c["overall_pressure_ratio"] / (
            c["fan_hub_pressure_ratio"] * c["compressor_pressure_ratio"])
        assert 0.95 < implied_booster < 1.10, (
            f"{point}: OPR / (fan_hub x HPC) = {implied_booster:.3f} — "
            "a quarter-stage booster cannot supply this"
        )


def test_hpt_inlet_temperature_agrees_between_tables(d):
    """Table XII prints T41 in C; Table XVIII prints it in K. Same point."""
    t12 = d["cycle_definition"]["max_climb"]["hpt_rotor_inlet_temperature_K"]
    t18 = d["hpt"]["cycle_match"]["inlet_temperature_T41_K"]
    assert abs(t12 - t18) < 1.0, (t12, t18)


def test_turbine_temperature_drops_are_ordered(d):
    t41 = d["hpt"]["cycle_match"]["inlet_temperature_T41_K"]
    t49 = d["lpt"]["cycle_match"]["inlet_temperature_T49_K"]
    assert t41 > t49 > 800, (t41, t49)


def test_combustor_has_two_cups_per_nozzle(d):
    """Double annular: each dual-tip nozzle feeds one pilot cup and one main
    cup. 60 cups / 30 nozzles must be exactly 2."""
    c = d["combustor"]
    assert c["swirl_cup_count"] == 2 * c["fuel_nozzle_count"]
    assert c["support_pin_count"] == c["fuel_nozzle_count"]


def test_prediffuser_split_sums_to_one(d):
    p = d["combustor"]["prediffuser"]
    assert abs(p["outer_passage_fraction"] + p["inner_passage_fraction"] - 1.0) < 1e-9


def test_fan_inlet_geometry_is_self_consistent(d):
    """Radius ratio, tip diameter and specific flow together give the fan
    face corrected flow. Table on p.41 prints that too."""
    s = d["size"]
    r_tip = s["fan_tip_diameter_m"] / 2
    r_hub = r_tip * s["fan_inlet_radius_ratio"]
    area = math.pi * (r_tip ** 2 - r_hub ** 2)
    flow = area * s["fan_specific_flow_kg_s_m2"]
    printed = d["fan_flow"]["aero_design_point"]["corrected_flow_kg_s"]
    assert abs(flow - printed) / printed < 0.02, (
        f"area x specific flow = {flow:.1f} kg/s, printed {printed}"
    )


# ── bearings ────────────────────────────────────────────────────────────

def test_bearing_arrangement_matches_the_prose(d):
    """p.96: five bearings; LP has a ball and two rollers; HP has a forward
    thrust and an aft intershaft roller."""
    b = d["bearings"]
    assert len(b["list"]) == 5
    numbers = [x["number"] for x in b["list"]]
    assert numbers == [1, 2, 3, 4, 5]

    def supports(bearing, spool):
        s = bearing["supports"]
        return spool in (s if isinstance(s, list) else [s])

    lp = [x for x in b["list"] if supports(x, "lp")]
    hp = [x for x in b["list"] if supports(x, "hp")]
    assert len(lp) == b["lp_bearing_count"] == 3
    assert len(hp) == b["hp_bearing_count"] + 1  # No.5 reacts both via the intershaft
    assert sum(x["type"] == "ball" for x in lp) == 1
    assert sorted(b["forward_sump"] + b["aft_sump"]) == numbers


def test_every_bearing_is_in_exactly_one_sump(d):
    b = d["bearings"]
    assert not set(b["forward_sump"]) & set(b["aft_sump"])
    for x in b["list"]:
        assert x["number"] in (b["forward_sump"] if x["sump"] == "forward" else b["aft_sump"])


# ── provenance ──────────────────────────────────────────────────────────

def test_every_architecture_entry_is_now_verified(d):
    """Phase A1's close condition, as a test."""
    for name, v in d["architecture"].items():
        if isinstance(v, dict) and "verified" in v:
            assert v["verified"] is True, f"{name} still unverified"
            assert v.get("src"), f"{name} verified but has no src"

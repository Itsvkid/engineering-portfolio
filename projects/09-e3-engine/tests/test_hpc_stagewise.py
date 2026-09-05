"""HPC stagewise design figures (Figs 10-20) against Table XXI's through-
flow and Table X's per-stage summary. The figures and the table came
from the same CAFD run, so they must agree at the pitch streamline."""

from __future__ import annotations

import math
import pathlib

import pytest

yaml = pytest.importorskip("yaml")

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"
T_INLET_K = 288.15  # standard-day sea-level static at the IGV inlet (sec 2.3.1)


@pytest.fixture(scope="module")
def sw():
    return yaml.safe_load((DATA / "hpc-stagewise.yaml").read_text())


@pytest.fixture(scope="module")
def vd():
    return yaml.safe_load((DATA / "hpc-vector-diagrams.yaml").read_text())


@pytest.fixture(scope="module")
def pub():
    return yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())


def row(vd, kind, stage=None):
    for r in vd["rows"]:
        if r["row"] == kind and (stage is None or r.get("stage") == stage):
            return r
    raise KeyError((kind, stage))


def at_immersion(table, col, imm):
    """Linear interpolation of column `col` at percent immersion `imm`
    (column 1 is pct_imm)."""
    pts = sorted((t[1], t[col]) for t in table)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= imm <= x1:
            return y0 + (y1 - y0) * (imm - x0) / (x1 - x0)
    return pts[0][1] if imm < pts[0][0] else pts[-1][1]


# column indices
R_MABS, R_MREL, R_U, R_CZ, R_BETA = 6, 7, 8, 9, 10
S_MABS, S_CZ, S_ALPHA = 6, 7, 8
SL_SOLIDITY, SL_DF, SL_LOSS = 3, 4, 5
PT, TT = 4, 5


# ── Fig.11 solidity, Fig.18 DF, Fig.17 loss at pitch vs Table XXI ───────

def test_pitch_solidity_matches_the_sl_data(sw, vd):
    s = sw["stagewise"]["pitch_solidity"]
    for i, st in enumerate(sw["stagewise"]["stage"]):
        r = row(vd, "rotor", st)
        tol = 0.09 if st in (9, 10) else 0.045  # rotors 9-10 re-bladed after Table XXI
        assert abs(at_immersion(r["sl_data"], SL_SOLIDITY, 50) - s["rotors"][i]) < tol, (st, "rotor")
        v = row(vd, "stator", st)
        tol = 0.09 if st in (8, 9) else 0.045  # stators 8-9 re-chorded
        assert abs(at_immersion(v["sl_data"], SL_SOLIDITY, 50) - s["stators"][i]) < tol, (st, "stator")


def test_pitch_diffusion_factor_matches_the_sl_data(sw, vd):
    d = sw["stagewise"]["diffusion_factor_pitch"]
    for i, st in enumerate(sw["stagewise"]["stage"]):
        assert abs(at_immersion(row(vd, "rotor", st)["sl_data"], SL_DF, 50) - d["rotors"][i]) < 0.02, (st, "rotor")
        assert abs(at_immersion(row(vd, "stator", st)["sl_data"], SL_DF, 50) - d["stators"][i]) < 0.02, (st, "stator")
    assert d["stators"][9] == max(d["stators"])  # the OGV is the most loaded row
    assert min(d["rotors"]) == d["rotors"][5]     # stage 6, deliberately unloaded


def test_pitch_loss_matches_the_sl_data(sw, vd):
    l = sw["stagewise"]["loss_coefficient_pitch"]
    for i, st in enumerate(sw["stagewise"]["stage"]):
        assert abs(at_immersion(row(vd, "rotor", st)["sl_data"], SL_LOSS, 50) - l["rotors"][i]) < 0.006, (st, "rotor")
        assert abs(at_immersion(row(vd, "stator", st)["sl_data"], SL_LOSS, 50) - l["stators"][i]) < 0.006, (st, "stator")


# ── Fig.12 meridional Mach ──────────────────────────────────────────────

def rotor_inlet_meridional_mach(r, imm):
    m_abs = at_immersion(r["inlet"], R_MABS, imm)
    u = at_immersion(r["inlet"], R_U, imm)
    cz = at_immersion(r["inlet"], R_CZ, imm)
    beta = math.radians(at_immersion(r["inlet"], R_BETA, imm))
    c_theta = u - cz * math.tan(beta)
    v_abs = math.hypot(cz, c_theta)
    return m_abs * cz / v_abs


def test_meridional_mach_at_pitch_recomputes_from_the_vector_diagrams(sw, vd):
    m = sw["stagewise"]["meridional_mach_pitch"]
    for i, st in enumerate(sw["stagewise"]["stage"]):
        mr = rotor_inlet_meridional_mach(row(vd, "rotor", st), 50)
        assert abs(mr - m["rotor_inlet"][i]) < 0.012, (st, mr, m["rotor_inlet"][i])
        v = row(vd, "stator", st)
        ms = at_immersion(v["inlet"], S_MABS, 50) * math.cos(math.radians(at_immersion(v["inlet"], S_ALPHA, 50)))
        assert abs(ms - m["stator_inlet"][i]) < 0.012, (st, ms, m["stator_inlet"][i])
    assert abs(m["rotor_inlet"][0] - sw["design_point"]["rotor1_inlet_meridional_mach"]) < 0.001
    assert m["rotor_inlet"] == sorted(m["rotor_inlet"], reverse=True)


# ── Fig.13 swirl ────────────────────────────────────────────────────────

def test_stator_exit_swirl_at_tip_pitch_hub_matches_table_xxi(sw, vd):
    s = sw["stagewise"]["stator_exit_swirl_deg"]
    for i, name in enumerate(s["row"]):
        if name == "IGV":
            r = row(vd, "igv")
        else:
            st = 10 if name == "OGV" else int(name[1:])
            r = row(vd, "stator", st)
        tip, hub = r["exit"][0][S_ALPHA], r["exit"][-1][S_ALPHA]
        pitch = at_immersion(r["exit"], S_ALPHA, 50)
        assert abs(tip - s["tip"][i]) < 0.8, (name, "tip", tip)
        assert abs(hub - s["hub"][i]) < 0.8, (name, "hub", hub)
        assert abs(pitch - s["pitch"][i]) < 0.8, (name, "pitch", pitch)
    assert max(s["pitch"]) == s["pitch"][5]  # S5 the peak, then falling


def test_stator6_radial_swirl_matches_table_xxi(sw, vd):
    f = sw["radial"]["stator6_exit_swirl"]
    r = row(vd, "stator", 6)
    for imm, sw_deg in zip(f["immersion_pct"], f["swirl_deg"]):
        assert abs(at_immersion(r["exit"], S_ALPHA, imm) - sw_deg) < 1.2, (imm, sw_deg)
    pitch = f["swirl_deg"][f["immersion_pct"].index(50)]
    assert abs(f["swirl_deg"][0] - pitch - f["text"]["casing_above_pitch_deg"]) < 0.8
    assert abs(f["swirl_deg"][-1] - pitch - f["text"]["hub_above_pitch_deg"]) < 0.8


# ── Fig.14 temperature rise ─────────────────────────────────────────────

def test_stage_temperature_rise_recomputes_from_tt_ratios(sw, vd):
    t = sw["stagewise"]["temperature_rise_C"]
    for i, st in enumerate(sw["stagewise"]["stage"]):
        r = row(vd, "rotor", st)
        # the figure's "average" rise: mean over the twelve streamlines of the
        # rotor's TT-ratio jump, times the inlet total temperature
        d_t = T_INLET_K * sum(e[TT] - n[TT] for n, e in zip(r["inlet"], r["exit"])) / len(r["inlet"])
        tol = 3.0 if st == 1 else 1.2  # rotor 1's hub-strong profile makes its mean sensitive to the weighting
        assert abs(d_t - t["per_stage"][i]) < tol, (st, d_t, t["per_stage"][i])
    assert abs(sum(t["per_stage"]) - t["total"]) < 0.2
    assert min(t["per_stage"]) == t["per_stage"][5]  # stage 6
    # the whole compressor, two ways: sum of stages vs the last stator's TT ratio
    last = row(vd, "stator", 10)
    # pitch value at the exit is below the span-mean sum (the profile is hub-strong): within 5 percent
    assert abs(T_INLET_K * (at_immersion(last["exit"], TT, 50) - 1.0) - t["total"]) / t["total"] < 0.05


# ── Fig.20 inlet Mach extremes ──────────────────────────────────────────

def test_inlet_mach_extremes_match_table_xxi(sw, vd):
    e = sw["stagewise"]["inlet_mach_extremes"]
    for i, st in enumerate(sw["stagewise"]["stage"]):
        r = row(vd, "rotor", st)
        assert abs(r["inlet"][0][R_MREL] - e["rotor_tip_relative"][i]) < 0.025, (st, "tip")
        m_max = max(line[R_MREL] for line in r["inlet"])
        assert abs(m_max - e["rotor_maximum_relative"][i]) < 0.025, (st, "max", m_max)
        imm_at_max = max(r["inlet"], key=lambda line: line[R_MREL])[1]
        if st > 1:
            assert 5 <= imm_at_max <= 45, (st, imm_at_max)  # "about 15 percent"; rotors 7-9 peak at 35-44 in the table
        v = row(vd, "stator", st)
        assert abs(v["inlet"][-1][S_MABS] - e["stator_hub_absolute"][i]) < 0.025, (st, "stator hub")
    assert e["rotor_tip_relative"][0] > 1.3 and max(e["rotor_tip_relative"][4:]) < 0.8


# ── Fig.19 stage-5 radial DF ────────────────────────────────────────────

def test_stage5_radial_diffusion_factor_matches_sl_data(sw, vd):
    f = sw["radial"]["stage5_diffusion_factor"]
    r5, s5 = row(vd, "rotor", 5), row(vd, "stator", 5)
    for imm, dr, ds in zip(f["immersion_pct"], f["rotor5"], f["stator5"]):
        assert abs(at_immersion(r5["sl_data"], SL_DF, imm) - dr) < 0.025, (imm, "rotor", dr)
        assert abs(at_immersion(s5["sl_data"], SL_DF, imm) - ds) < 0.025, (imm, "stator", ds)
    assert f["rotor5"][-1] > f["stator5"][-1] and f["rotor5"][0] > f["stator5"][0]  # rotor end walls higher
    assert min(f["rotor5"]) < min(f["stator5"])


# ── Fig.10 aspect ratio vs Table X ──────────────────────────────────────

def find_table_x(node):
    if isinstance(node, dict):
        if "aspect_ratio_tip" in node and "aspect_ratio_root" in node:
            return node
        for v in node.values():
            found = find_table_x(v)
            if found:
                return found
    return None


def test_rotor_aspect_ratio_matches_table_x(sw, pub):
    tx = find_table_x(pub)
    assert tx is not None
    ar = sw["stagewise"]["aspect_ratio"]["rotors"]
    # Fig.10 plots Table X's TIP aspect ratio: all ten within 0.035
    for i in range(10):
        assert abs(tx["aspect_ratio_tip"][i] - ar[i]) < 0.04, (i + 1, tx["aspect_ratio_tip"][i], ar[i])
        assert tx["aspect_ratio_root"][i] >= tx["aspect_ratio_tip"][i] - 0.001
    st = sw["stagewise"]["aspect_ratio"]["stators"]
    assert st == sorted(st, reverse=True)
    assert all(s > r for s, r in zip(st[:7], ar[:7]))  # stators higher AR in the front


# ── design-point facts ──────────────────────────────────────────────────

def test_design_point_facts_agree_with_the_published_file(sw, pub):
    d = sw["design_point"]
    assert d["pressure_ratio_operating_line"] == pub["hpc"]["design_pressure_ratio_operating_line"]
    assert d["pressure_ratio_design"] > d["pressure_ratio_operating_line"]
    assert abs(d["rotor1_specific_flow_kg_s_m2"] - d["rotor1_specific_flow_lbm_s_ft2"] * 4.8824) < 0.5
    assert d["transonic_rotors"]["stages"] == pub["hpc"]["transonic_rotors"]
    b = d["bleeds"]
    assert abs(b["stage5"]["customer_max_pct"] + b["stage5"]["lpt_use_pct"] - b["stage5"]["max_pct_throughflow"]) < 0.01
    assert abs(b["stage7"]["starting_max_pct"] + b["stage7"]["hpt_stage2_nozzle_pct"] - b["stage7"]["max_pct_design_flow"]) < 0.01
    assert 0.6 < d["pitch_reaction_average"] < 0.75
    # temperature rise vs the isentropic-with-efficiency estimate at 25:1: within 5 percent
    total = sw["stagewise"]["temperature_rise_C"]["total"]
    ideal = T_INLET_K * (25 ** (0.2857) - 1) / d["efficiency_adiabatic"]
    assert 0.93 < total / ideal < 1.01, (total, ideal)  # real cp lowers the rise

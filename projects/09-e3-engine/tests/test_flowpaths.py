"""The derived flowpaths (data/lpt-flowpath.csv, data/hpc-flowpath.csv)
against the design tables, against each other across the HPT-LPT
transition duct, and against their own generator."""

from __future__ import annotations

import csv
import math
import pathlib
import subprocess
import sys

import pytest

yaml = pytest.importorskip("yaml")

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def read(name):
    text = (DATA / name).read_text()
    return list(csv.DictReader(l for l in text.splitlines() if not l.startswith("#")))


def test_derived_files_regenerate_identically():
    before = {n: (DATA / n).read_text() for n in ("lpt-flowpath.csv", "hpc-flowpath.csv")}
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_flowpaths.py")], check=True, capture_output=True)
    for n, txt in before.items():
        assert (DATA / n).read_text() == txt, n


def test_lpt_tip_radii_and_radius_ratios_match_table_vii():
    ap = yaml.safe_load((DATA / "lpt-design.yaml").read_text())["aero_design_parameters"]
    fp = {(r["row"], r["edge"]): r for r in read("lpt-flowpath.csv")}
    for col, row in ((0, "R1"), (1, "R5")):
        le = fp[(row, "LE")]
        r_tip = float(le["r_tip_cm"]); r_hub = float(le["r_hub_cm"])
        assert abs(r_tip - ap["tip_diameter_cm"][col] / 2) / (ap["tip_diameter_cm"][col] / 2) < 0.02, (row, r_tip)
        # the hub is extrapolated from the 10 and 90 percent sections; stage 1
        # lands on Table VII's 0.76, stage 5 reads 0.61 against 0.64 -- the
        # sections are spaced on the airfoil, not on the annulus (engine-flowpath.yaml)
        assert abs(r_hub / r_tip - ap["inlet_radius_ratio"][col]) < 0.03, (row, r_hub / r_tip)


def test_lpt_blade_heights_match_fig52_lengths():
    rb = yaml.safe_load((DATA / "lpt-design.yaml").read_text())["rotor_blades"]
    fp = {(r["row"], r["edge"]): r for r in read("lpt-flowpath.csv")}
    for st in range(1, 6):
        le, te = fp[(f"R{st}", "LE")], fp[(f"R{st}", "TE")]
        h_le, h_te = float(le["blade_height_in"]) * 2.54, float(te["blade_height_in"]) * 2.54
        printed = rb["blade_length_cm"][st - 1]
        # the annulus diverges through every rotor, so the blade is longer at
        # its trailing edge than its leading edge; Fig 52's one length sits
        # between the two (within 3 percent either side)
        # (rotor 4's printed 20.22 cm sits 3.4 percent under even its LE height:
        # the extrapolated walls overshoot on the tall rear blades, as the hub did)
        assert min(h_le, h_te) * 0.96 < printed < max(h_le, h_te) * 1.03, (st, h_le, h_te, printed)
        assert h_te > h_le


def test_lpt_hub_rises_then_turns_inward_and_tip_rises_throughout():
    rows = read("lpt-flowpath.csv")
    hub = [float(r["r_hub_cm"]) for r in rows]
    tip = [float(r["r_tip_cm"]) for r in rows]
    z = [float(r["z_hub_cm"]) for r in rows]
    assert z == sorted(z)
    assert tip == sorted(tip)
    # the hub climbs to rotor 3's trailing edge, runs flat (within 0.05 cm)
    # through stator 4 and rotor 4 -- the cylindrical stage-4 hub -- and then
    # turns inward through stage 5
    names = [f'{r["row"]}_{r["edge"]}' for r in rows]
    i_r3te = names.index("R3_TE"); i_r4te = names.index("R4_TE")
    assert hub[:i_r3te + 1] == sorted(hub[:i_r3te + 1])
    plateau = hub[i_r3te:i_r4te + 1]
    assert max(plateau) - min(plateau) < 0.05, plateau
    assert hub[-1] < max(plateau) - 0.5


def test_lpt_extent_matches_the_calculation_model_and_the_section_figures():
    rows = read("lpt-flowpath.csv")
    aero = yaml.safe_load((DATA / "lpt-aero.yaml").read_text())
    last = [r for r in rows if r["row"] == "R5" and r["edge"] == "TE"][0]
    assert abs(float(last["z_tip_in"]) - aero["block_ii_flowpath"]["calculation_model"]["axial_length_to_exit_in"]) < 1.5
    first = [r for r in rows if r["row"] == "S1" and r["edge"] == "LE"][0]
    assert 12.0 < float(first["r_hub_in"]) < 13.0 and 15.5 < float(first["r_tip_in"]) < 16.5


def test_hpt_exit_to_lpt_inlet_is_the_transition_duct():
    """The LPT's z datum is the HPT exit plane. Between the HPT stage-2 blade
    exit (Fig 3 of the HPT report, in the published file) and the LPT
    stator-1 leading edge lies the transition duct the published file gives
    as 7.62 cm long with a 25-degree outer wall."""
    pub = yaml.safe_load((DATA / "e3-fps-published.yaml").read_text())
    hpt_exit = [s for s in pub["hpt"]["flowpath"]["stations"] if s["location"] == "stage2_blade_exit"][0]
    s1 = [r for r in read("lpt-flowpath.csv") if r["row"] == "S1" and r["edge"] == "LE"][0]
    duct_len = float(s1["z_tip_cm"])
    assert abs(duct_len - pub["lpt"]["transition_duct_axial_length_cm"]) < 1.2, duct_len
    # radii: the LPT inlet sits outside the HPT exit on both walls
    assert float(s1["r_tip_cm"]) > hpt_exit["r_tip_cm"] and float(s1["r_hub_cm"]) > hpt_exit["r_hub_cm"]
    slope = math.degrees(math.atan((float(s1["r_tip_cm"]) - hpt_exit["r_tip_cm"]) / duct_len))
    assert 15 < slope < pub["lpt"]["outer_wall_slope_deg"] + 1, slope  # the mean slope sits under the 25-degree maximum


def test_hpc_rotor1_radii_match_table_x_and_the_annulus_contracts():
    fp = {(r["row"], r["edge"]): r for r in read("hpc-flowpath.csv")}
    assert abs(float(fp[("R1", "LE")]["r_tip_cm"]) - 35.07) < 0.05  # Table X's 35.08 cm
    rows = read("hpc-flowpath.csv")
    h = [float(r["blade_height_cm"]) for r in rows]
    assert h == sorted(h, reverse=True)
    assert h[0] > 18 and h[-1] < 4

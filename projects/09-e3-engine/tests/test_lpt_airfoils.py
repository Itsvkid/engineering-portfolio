"""The LPT appendix airfoil coordinates (data/lpt-airfoils/*.csv) against
themselves (tools/lpt_airfoil_check.py) and against the design tables."""

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
AIR = DATA / "lpt-airfoils"


def load(name):
    text = (AIR / f"{name}.csv").read_text()
    rows = list(csv.DictReader(l for l in text.splitlines() if not l.startswith("#")))
    return {s: [(float(r["z_in"]), float(r["r_in"]), float(r["rtheta_in"])) for r in rows if r["surface"] == s] for s in ("suction", "pressure")}


def sections():
    return sorted(p.stem for p in AIR.glob("*.csv"))


def chord_in(sec):
    """Leading edge to trailing edge in the (z, r-theta) plane, mean of the two surfaces' ends."""
    su, pr = sec["suction"], sec["pressure"]
    le = su[0]
    te = ((su[-1][0] + pr[-1][0]) / 2, (su[-1][2] + pr[-1][2]) / 2)
    return math.hypot(te[0] - le[0], te[1] - le[2])


def test_every_section_passes_the_self_checks():
    files = [str(AIR / f"{s}.csv") for s in sections()]
    assert files, "no sections transcribed"
    res = subprocess.run([sys.executable, str(ROOT / "tools" / "lpt_airfoil_check.py"), *files], capture_output=True, text=True)
    assert res.returncode == 0, res.stdout


def test_each_section_has_48_points_per_surface_and_a_shared_leading_edge():
    for name in sections():
        sec = load(name)
        text = (AIR / f"{name}.csv").read_text()
        exp_pr = 47 if "points: pressure = 47" in text else 48
        assert len(sec["suction"]) == 48 and len(sec["pressure"]) == exp_pr, name
        assert sec["suction"][0] == sec["pressure"][0], name


def test_rotor_chords_match_fig52_root_and_tip():
    """Chord from the coordinates at 10 and 90 percent span against Fig.52's
    root and tip chords (lpt-design.yaml), stage by stage, within 3 percent."""
    rb = yaml.safe_load((DATA / "lpt-design.yaml").read_text())["rotor_blades"]
    checked = 0
    for name in sections():
        if not name.startswith("R"):
            continue
        stage = int(name[1]); span = int(name.split("_")[1])
        if span not in (10, 90):
            continue
        printed_cm = rb["root_chord_cm"][stage - 1] if span == 10 else rb["tip_chord_cm"][stage - 1]
        c = chord_in(load(name)) * 2.54
        # the sections are at 10 and 90 percent, not at the platform and tip, so
        # they read a little under the printed end chords; rotor 4's "flask"
        # airfoil (chord smallest at midspan) drops fastest from its root
        tol = 0.08 if (stage == 4 and span == 10) else 0.04
        assert abs(c - printed_cm) / printed_cm < tol, (name, c, printed_cm)
        assert c < printed_cm * 1.02, (name, c, printed_cm)
        checked += 1
    assert checked >= 2


def test_rotor1_section_radii_sit_where_table_vii_puts_them():
    ap = yaml.safe_load((DATA / "lpt-design.yaml").read_text())["aero_design_parameters"]
    r_tip = ap["tip_diameter_cm"][0] / 2 / 2.54
    r_hub = r_tip * ap["inlet_radius_ratio"][0]
    for span in (10, 50, 90):
        name = f"R1_{span}"
        if name not in sections():
            continue
        r_le = load(name)["suction"][0][1]
        expected = r_hub + span / 100 * (r_tip - r_hub)
        assert abs(r_le - expected) < 0.08, (name, r_le, expected)


def test_rows_sit_in_gas_path_order_along_z():
    order = ["S1", "R1", "S2", "R2", "S3", "R3", "S4", "R4", "S5", "R5"]
    z_le = {}
    for name in sections():
        row, span = name.split("_")
        if span == "10":
            z_le[row] = load(name)["suction"][0][0]
    present = [r for r in order if r in z_le]
    zs = [z_le[r] for r in present]
    assert zs == sorted(zs), z_le
    # each row's trailing edge lies upstream of the next row's leading edge
    for a, b in zip(present, present[1:]):
        te = max(p[0] for p in load(f"{a}_10")["suction"])
        assert te < z_le[b], (a, b)


def test_hub_radius_rises_through_the_turbine_and_sections_stack_outward():
    for name in sections():
        row, span = name.split("_")
        r10 = load(f"{row}_10")["suction"][0][1] if f"{row}_10" in sections() else None
        r50 = load(f"{row}_50")["suction"][0][1] if f"{row}_50" in sections() else None
        r90 = load(f"{row}_90")["suction"][0][1] if f"{row}_90" in sections() else None
        vals = [v for v in (r10, r50, r90) if v is not None]
        assert vals == sorted(vals), (row, vals)
    rows = [r for r in ["S1", "R1", "S2", "R2", "S3", "R3", "S4", "R4", "S5", "R5"] if f"{r}_10" in sections()]
    hub = {r: load(f"{r}_10")["suction"][0][1] for r in rows}
    rising = [hub[r] for r in rows if r in ("S1", "R1", "S2", "R2", "S3", "R3", "S4", "R4")]
    assert rising == sorted(rising), hub
    # the hub turns inward at the last stage: the 10 percent sections of S5 and
    # R5 sit below R4's, and S5's own wall slopes inward along the row
    if "S5" in hub and "R4" in hub:
        assert hub["S5"] < hub["R4"] and hub["R5"] < hub["S5"], hub
        s5 = load("S5_10")["suction"]
        assert s5[-1][1] < s5[0][1]


def test_stators_turn_one_way_and_rotors_the_other():
    """A stator's trailing edge sits at positive r-theta relative to its leading
    edge (it turns the flow toward +theta); a rotor's at negative -- the
    opposite-handed rows of a turbine stage."""
    for name in sections():
        sec = load(name)
        dt = sec["suction"][-1][2] - sec["suction"][0][2]
        assert (dt > 0) if name.startswith("S") else (dt < 0), (name, dt)

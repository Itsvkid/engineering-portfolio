#!/usr/bin/env python3
"""Derive the LPT and HPC flowpaths from the transcribed tables.

LPT: from data/lpt-airfoils/*.csv. Each row has sections at 10, 50 and 90
percent span; the hub (0 %) and tip (100 %) radii at the leading and
trailing edges are extrapolated linearly from the 10 and 90 percent
sections (span = (r90 - r10) / 0.8). Written to data/lpt-flowpath.csv with
z from the HPT exit plane, inches and centimetres.

HPC: from data/hpc-vector-diagrams.yaml (Table XXI). Streamline 1 is the
tip, streamline 12 the hub, at each row's inlet and exit. Written to
data/hpc-flowpath.csv in the HPC report's own z datum, centimetres.

Both are DERIVED files: regenerate them with this script, never edit."""
import csv, pathlib, sys
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
AIR = ROOT / "data" / "lpt-airfoils"
ORDER = ["S1", "R1", "S2", "R2", "S3", "R3", "S4", "R4", "S5", "R5"]


def load(name):
    text = (AIR / f"{name}.csv").read_text()
    rows = list(csv.DictReader(l for l in text.splitlines() if not l.startswith("#")))
    return {s: [(float(r["z_in"]), float(r["r_in"]), float(r["rtheta_in"])) for r in rows if r["surface"] == s] for s in ("suction", "pressure")}


def le_te(sec):
    su, pr = sec["suction"], sec["pressure"]
    le = (su[0][0], su[0][1])
    te = ((su[-1][0] + pr[-1][0]) / 2, (su[-1][1] + pr[-1][1]) / 2)
    return le, te


def lpt():
    out = [["row", "edge", "z_hub_in", "r_hub_in", "z_tip_in", "r_tip_in", "z_hub_cm", "r_hub_cm", "z_tip_cm", "r_tip_cm", "blade_height_in", "r10_in", "r50_in", "r90_in"]]
    for row in ORDER:
        s10, s50, s90 = (load(f"{row}_{p}") for p in (10, 50, 90))
        for edge, idx in (("LE", 0), ("TE", 1)):
            p10, p50, p90 = le_te(s10)[idx], le_te(s50)[idx], le_te(s90)[idx]
            dz = (p90[0] - p10[0]) / 0.8
            dr = (p90[1] - p10[1]) / 0.8
            hub = (p10[0] - 0.125 * dz, p10[1] - 0.125 * dr)
            tip = (p90[0] + 0.125 * dz, p90[1] + 0.125 * dr)
            out.append([row, edge, f"{hub[0]:.4f}", f"{hub[1]:.4f}", f"{tip[0]:.4f}", f"{tip[1]:.4f}",
                        f"{hub[0]*2.54:.3f}", f"{hub[1]*2.54:.3f}", f"{tip[0]*2.54:.3f}", f"{tip[1]*2.54:.3f}",
                        f"{tip[1]-hub[1]:.4f}", f"{p10[1]:.4f}", f"{p50[1]:.4f}", f"{p90[1]:.4f}"])
    with (ROOT / "data" / "lpt-flowpath.csv").open("w", newline="") as f:
        f.write("# DERIVED by tools/build_flowpaths.py from data/lpt-airfoils/*.csv -- hub and tip extrapolated linearly from the 10 and 90 percent sections; z from the HPT exit plane\n")
        csv.writer(f).writerows(out)


def hpc():
    vd = yaml.safe_load((ROOT / "data" / "hpc-vector-diagrams.yaml").read_text())
    out = [["row", "edge", "z_hub_cm", "r_hub_cm", "z_tip_cm", "r_tip_cm", "blade_height_cm"]]
    rows = []
    for r in vd["rows"]:
        name = "IGV" if r["row"] == "igv" else ("R" if r["row"] == "rotor" else "S") + str(r["stage"])
        key = -1 if name == "IGV" else (2 * r["stage"] - (1 if r["row"] == "rotor" else 0))
        rows.append((key, name, r))
    for _, name, r in sorted(rows):
        for edge, station in (("LE", "inlet"), ("TE", "exit")):
            tip, hub = r[station][0], r[station][-1]
            out.append([name, edge, f"{hub[3]:.3f}", f"{hub[2]:.3f}", f"{tip[3]:.3f}", f"{tip[2]:.3f}", f"{tip[2]-hub[2]:.3f}"])
    with (ROOT / "data" / "hpc-flowpath.csv").open("w", newline="") as f:
        f.write("# DERIVED by tools/build_flowpaths.py from data/hpc-vector-diagrams.yaml (Table XXI streamlines 1 and 12) -- z in the HPC report's datum\n")
        csv.writer(f).writerows(out)


if __name__ == "__main__":
    lpt(); hpc()
    print("wrote data/lpt-flowpath.csv and data/hpc-flowpath.csv")

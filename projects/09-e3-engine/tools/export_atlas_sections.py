#!/usr/bin/env python3
"""Export the transcribed E3 blade sections for the Turbofan Atlas page.

Reads data/hpc-blade-sections.yaml (HPC Table XXII: 12 sections per row,
21 rows), data/lpt-airfoils/*.csv (LPT appendix: 30 sections, 3 spans
per row, real surface coordinates), and data/fan-design.yaml (CR-165148
Appendices B and D: the fan rotor's 23 plane sections and the booster
rotor's 14), and writes one ES module,
app/turbofan/atlas/data/e3-sections.js, that the page lofts its blades
from. Run from the repository root after any of those sources change.
"""
import csv, glob, json, math, os, re, sys
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, "projects", "09-e3-engine", "data")
OUT = os.path.join(ROOT, "app", "turbofan", "atlas", "data", "e3-sections.js")

# ── HPC ────────────────────────────────────────────────────────────────────
y = yaml.safe_load(open(os.path.join(DATA, "hpc-blade-sections.yaml")))
hpc = {}
def rows(block, key):
    for item in block:
        secs = item["sections"]
        out = []
        for sec in reversed(secs):  # printed tip first; hub first here
            r_cm, chord_cm = sec[0], sec[2]
            if key == "IGV":
                stagger, cl0, tm = sec[4], sec[5], sec[6]
                camber = round(25.0 * cl0, 2)  # CL0 -> turning, schematic; the IGV prints no camber
            else:
                camber, stagger, tm = sec[4], sec[5], sec[8]
            out.append([round(r_cm / 100, 5), round(chord_cm / 100, 5), camber, stagger, tm])
        yield item.get("stage"), out
for stage, secs in rows(y["rotors"], "R"):
    hpc[f"R{stage}"] = secs
for stage, secs in rows(y["stators"], "S"):
    hpc[f"S{stage}"] = secs
hpc["IGV"] = next(rows([y["igv"]], "IGV"))[1]

# ── LPT ────────────────────────────────────────────────────────────────────
def resample(points, n):
    """Resample a polyline to n points spaced by arc length, cosine-clustered at the ends."""
    d = [0.0]
    for a, b in zip(points, points[1:]):
        d.append(d[-1] + math.dist(a, b))
    total = d[-1]
    out = []
    for i in range(n):
        s = i / (n - 1)
        t = (1 - math.cos(math.pi * s)) / 2 * total
        k = max(1, min(len(d) - 1, next((j for j in range(1, len(d)) if d[j] >= t), len(d) - 1)))
        f = 0 if d[k] == d[k - 1] else (t - d[k - 1]) / (d[k] - d[k - 1])
        out.append([points[k - 1][c] + f * (points[k][c] - points[k - 1][c]) for c in range(3)])
    return out

N = 14
lpt = {}
for path in sorted(glob.glob(os.path.join(DATA, "lpt-airfoils", "*.csv"))):
    name = os.path.basename(path)[:-4]
    row, span = name.split("_")
    suction, pressure = [], []
    with open(path) as f:
        for rec in csv.DictReader(l for l in f if not l.startswith("#")):
            # [r, z, rtheta] in metres; z from the HPT exit plane (the LPT datum)
            p = [float(rec["r_in"]) * 0.0254, float(rec["z_in"]) * 0.0254, float(rec["rtheta_in"]) * 0.0254]
            (suction if rec["surface"] == "suction" else pressure).append(p)
    s = resample(suction, N)
    q = resample(pressure, N)
    poly = s + list(reversed(q[1:-1]))  # closed loop: suction LE->TE, pressure TE->LE
    lpt.setdefault(row, {})[int(span)] = [[round(v, 5) for v in p] for p in poly]

def extrap(a, b, f):
    return [[round(a[i][c] + (b[i][c] - a[i][c]) * f, 5) for c in range(3)] for i in range(len(a))]
lpt_rows = {}
for row, spans in lpt.items():
    s10, s50, s90 = spans[10], spans[50], spans[90]
    # Hub and tip by straight-line extrapolation through 10 % and 50 % (and 50 % and 90 %),
    # the same rule data/lpt-flowpath.csv uses for the walls.
    lpt_rows[row] = [extrap(s10, s50, -0.25), s10, s50, s90, extrap(s50, s90, 1.25)]

# ── Fan and booster (CR-165148 Appendices B and D) ─────────────────────────
# Both appendices print exactly the five columns the atlas loft wants, in the
# same order the HPC block emits, so they need no conversion beyond cm -> m.
#
# Three things the page must not do to these rows, each of which the source
# would punish:
#   * do not drop the end stations. Appendix B's first and last are the
#     flowpath hub and tip -- R_ID + (-5.690) = 36.067 cm against a published
#     inlet hub of 36.047, and R_ID + 63.653 = 105.410 against Fig 2's 105.4.
#     They look like overhang and are not.
#   * use radius_cm, not the percent column. The 0-100 % rows are linear in
#     height at 0.62328 cm/%, but the two end rows deliberately are not:
#     extrapolating the percent misplaces them by 0.8 and 2.3 mm.
#   * do not smooth. The booster's tm/c rises 0.0488 -> 0.0490 at the tip,
#     the only non-monotonic column in either appendix, and a spline through
#     it would quietly remove a printed feature.
fan_yaml = yaml.safe_load(open(os.path.join(DATA, "fan-design.yaml")))

def plane_sections(block, key):
    a = fan_yaml[block][key]
    return [[round(a["radius_cm"][i] / 100, 5), round(a["chord_cm"][i] / 100, 5),
             a["camber_deg"][i], a["stagger_deg"][i], a["tm_over_c"][i]]
            for i in range(a["stations"])]          # printed hub first already

fan = plane_sections("fan_rotor_airfoil", "appendix_b")
booster = plane_sections("booster_rotor_airfoil", "appendix_d")

with open(OUT, "w") as f:
    f.write("// GENERATED by projects/09-e3-engine/tools/export_atlas_sections.py — do not edit.\n")
    f.write("// HPC: Table XXII of the E³ HPC detail design report (NTRS 19850002690), 12 sections\n")
    f.write("// per row hub first as [r_m, chord_m, camber_deg, stagger_deg, tmax/chord]; the IGV's\n")
    f.write("// camber is 25×CL0 (schematic — the table prints CL0, not camber).\n")
    f.write("// LPT: the thirty transcribed airfoil sections of the E³ LPT report appendix, each\n")
    f.write("// resampled to %d points per surface as [r_m, z_m from the HPT exit plane, rtheta_m];\n" % N)
    f.write("// hub and tip extrapolated from the 10/50/90 % sections as the flowpath is.\n")
    f.write("// FAN / BOOSTER: CR-165148 Appendix B p.134 (23 plane sections) and Appendix D\n")
    f.write("// p.136 (14), hub first as [r_m, chord_m, camber_deg, stagger_deg, tmax/chord].\n")
    f.write("// These replaced seven and five points read off Figs 41 and 52, which carried a\n")
    f.write("// mean stagger error of +3.14 deg on the fan and -1.61 deg on the booster.\n")
    f.write("export const HPC_SECTIONS = " + json.dumps(hpc, separators=(",", ":")) + ";\n")
    f.write("export const LPT_SECTIONS = " + json.dumps(lpt_rows, separators=(",", ":")) + ";\n")
    f.write("export const FAN_SECTIONS = " + json.dumps(fan, separators=(",", ":")) + ";\n")
    f.write("export const BOOSTER_SECTIONS = " + json.dumps(booster, separators=(",", ":")) + ";\n")
print("wrote", OUT, os.path.getsize(OUT), "bytes;", len(hpc), "HPC rows,", len(lpt_rows), "LPT rows,",
      len(fan), "fan sections,", len(booster), "booster sections")

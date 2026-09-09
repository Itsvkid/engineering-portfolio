"""Stage I unit I4: the digitising uncertainty register.

Stage A3's last line asks for a digitising uncertainty per figure. Unit J2
showed why, and showed it the expensive way: Stage E3's closure wants blade
frequencies within 5 % of the published Campbell diagrams, and those
diagrams can be read to about half a minor division -- **±14 % on a 350 Hz
line drawn against a 0-6 kHz axis**. Eleven of twenty-four comparisons
cannot resolve a 5 % band at all. The closure was never falsifiable on
those points and nothing said so until someone plotted it (finding 160).

That question -- *can this comparison resolve its own band?* -- should not
wait for a figure. This asks it of every closure at once.

**What it does not do** is invent an uncertainty for each of the 125 figure
citations in `data/`. That needs the figures measured. A plausible number per figure would be worse than a missing one,
because it would look measured. The register is built from what the data files **actually
record**, and the ones with nothing recorded are counted and named.

STEP0.md, unit I4."""
from __future__ import annotations

import pathlib
import re

import yaml

from e3cycle.cycle import DATA


def recorded():
    """Every reading uncertainty the data files state, as they state it.

    Each entry names the file that owns it, the figures it covers, and the
    closures that lean on it. Nothing here is computed; the `value` fields
    are quoted from the source file."""
    return [
        dict(key="hpc_rotor_campbell",
             file="hpc-rotor-campbell.yaml", figures="HPC Figs 33-42",
             quantity="blade natural frequency",
             value_hz={6: 50.0, 12: 100.0, 22: 250.0, 26: 250.0},
             basis="half a minor division of the stage's own frequency axis",
             closures=["E3"], band_pct=5.0),
        dict(key="hpc_stagewise",
             file="hpc-stagewise.yaml", figures="HPC Figs 11, 14, 17, 18",
             quantity="diffusion factor, loss coefficient, swirl, temperature rise",
             value_hz=None,
             basis="+-0.01 on ratios, +-0.005 on Mach and loss, "
                   "+-0.3 deg on swirl, +-0.2 C on temperature rise",
             closures=["C1"], band_pct=None),
        dict(key="hpt_fig5",
             file="hpt-fig5.yaml", figures="CR-167955 Fig 5c",
             quantity="stage energy extraction",
             value_hz=None, basis="+-5 kJ/kg, from a pixel-level extraction "
                                  "with the method recorded in the file",
             closures=["C1"], band_pct=None),
        dict(key="hpt_fig3_axial",
             file="e3-fps-published.yaml", figures="HPT Fig 3",
             quantity="axial position of a dimensioned radius",
             value_hz=None,
             basis="+-0.3 cm; the radii are printed, their axial positions "
                   "are read off the drawing's own scale",
             closures=["J1", "J5"], band_pct=None),
        dict(key="lpt_blockage",
             file="lpt-aero.yaml", figures="derived, not read",
             quantity="through-flow blockage",
             value_hz=None, basis="+-0.012 on 0.955, from the spread of five "
                                  "rotor trailing edges",
             closures=["B4"], band_pct=None),
    ]


def campbell_resolvability():
    """Finding 160, recomputed here rather than restated: the one register
    entry whose uncertainty is numeric per point, so the verdict can be
    counted instead of described."""
    from publication.campbell import resolvability
    r = resolvability()
    return dict(closure="E3", band_pct=5.0, total=r["total"],
                resolvable=r["resolvable"], unresolvable=r["unresolvable"],
                first_flex_resolvable=r["first_flex_resolvable"],
                first_flex_total=r["first_flex_total"],
                worst_reading_pct=r["worst_unc_pct"])


def figure_citations():
    """Every distinct figure the data files cite. The denominator."""
    pat = re.compile(r"Fig\.?\s?(\d+[a-c]?)")
    seen = set()
    for f in sorted(pathlib.Path(DATA).glob("*.yaml")):
        for m in pat.finditer(f.read_text()):
            seen.add((f.name, m.group(1)))
    return sorted(seen)


def coverage():
    """How far Stage A3's last line has actually got."""
    cites = figure_citations()
    files_with = {r["file"] for r in recorded()}
    covered = [c for c in cites if c[0] in files_with]
    return dict(
        distinct_citations=len(cites),
        files_citing=len({c[0] for c in cites}),
        recorded_entries=len(recorded()),
        citations_in_files_with_a_recorded_uncertainty=len(covered),
        pct_covered=100.0 * len(covered) / len(cites) if cites else 0.0,
        note=("a citation counts as covered when its FILE records a reading "
              "uncertainty, which is generous -- one uncertainty rarely "
              "governs every figure in a file. The true per-figure coverage "
              "is lower, and measuring it is the rest of A3's last line."))


def summary():
    c, cam = coverage(), campbell_resolvability()
    L = ["Stage I unit I4 -- the digitising uncertainty register", ""]
    L.append(f"   {'entry':<22}{'figures':<26}{'closures':<12}basis")
    for r in recorded():
        L.append(f"   {r['key']:<22}{r['figures']:<26}"
                 f"{','.join(r['closures']):<12}{r['basis'][:52]}")
    L += ["", "   the one entry with a per-point numeric uncertainty:",
          f"      closure E3, band {cam['band_pct']:.0f} %: "
          f"{cam['resolvable']} of {cam['total']} comparisons can resolve it",
          f"      first flex: {cam['first_flex_resolvable']} of "
          f"{cam['first_flex_total']}  (worst reading "
          f"+-{cam['worst_reading_pct']:.0f} %)"]
    L += ["", "   coverage of Stage A3's last line:",
          f"      {c['distinct_citations']} distinct figure citations across "
          f"{c['files_citing']} data files",
          f"      {c['recorded_entries']} recorded reading uncertainties",
          f"      {c['citations_in_files_with_a_recorded_uncertainty']} "
          f"citations sit in a file that records one "
          f"({c['pct_covered']:.0f} %, and that is the generous count)"]
    L.append("      the rest have NO stated uncertainty, and none is invented here")
    return "\n".join(L)


if __name__ == "__main__":
    print(summary())

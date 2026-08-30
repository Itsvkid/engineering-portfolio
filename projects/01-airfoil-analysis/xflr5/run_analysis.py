#!/usr/bin/env python3
"""Regenerate the committed XFLR5 reference polars.

Run this only when the reference needs rebuilding -- a new XFLR5 version, a
different Reynolds number, a changed sweep. The comparison itself does not
need it: `src/xflr5_reference.py` reads the committed output under
`reference/`, so `build.py` and the tests run on any machine.

    python xflr5/run_analysis.py

**This needs a logged-in macOS GUI session.** XFLR5 ships only Qt's `cocoa`
platform plugin -- there is no `offscreen` -- so it cannot run over SSH, in
CI, or with the screen locked, even in `--script` mode. That is the reason
the polars are committed rather than regenerated on demand.

The foil coordinates are written from this project's own `Naca4.surface()`
rather than from XFLR5's built-in NACA generator. That matters more than it
looks: comparing two solvers is only meaningful if they are given the same
body, and the two generators differ in trailing-edge closure (this project
uses the -0.1036 closed-TE coefficient) and in point distribution. Feeding
XFLR5 our own coordinates removes geometry as a source of disagreement, so
what is left is solver physics.

Script format: `xflscript` v1.0. The authoritative example is
`xflr5v6/xflscript/resources/foil_script.xml` in the XFLR5 source tree,
which is commented field by field. Note that XFLR5 responds to a script it
cannot parse by calling abort() rather than exiting -- a malformed file
shows up as a SIGABRT crash report, not an error message.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.geometry import Naca4  # noqa: E402

XFLR5 = Path("/Applications/xflr5.app/Contents/MacOS/xflr5")
REFERENCE_DIR = Path(__file__).resolve().parent / "reference"

FOILS = ("0012", "4412")
REYNOLDS = 1.0e6
MACH = 0.0
NCRIT = 9.0
ALPHA_MIN, ALPHA_MAX, ALPHA_STEP = -6.0, 12.0, 1.0
PANELS_PER_SIDE = 100
MAX_XFOIL_ITERATIONS = 150

SCRIPT_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE flow5>
<xflscript version="1.0">
    <Metadata>
        <make_project_file>false</make_project_file>
        <polar_text_output_format>CSV</polar_text_output_format>
        <Directories>
            <output_dir>{work}/out</output_dir>
            <foil_files_dir>{work}/foils</foil_files_dir>
            <foil_analysis_xml_dir>{work}/analyses</foil_analysis_xml_dir>
            <foil_polars_dir>{work}/polars</foil_polars_dir>
            <xfoil_polars_dir>{work}/xfoil</xfoil_polars_dir>
        </Directories>
        <MultiThreading>
            <Allow_Multithreading>true</Allow_Multithreading>
            <Thread_Priority>Normal</Thread_Priority>
            <Max_threads>4</Max_threads>
        </MultiThreading>
    </Metadata>
    <Foil_Analysis>
        <Foil_Files>
{foil_entries}
        </Foil_Files>
        <Analysis_Files>
            <Process_All_Files>false</Process_All_Files>
        </Analysis_Files>
        <Batch_Analysis_Data>
            <Polar_Type>1</Polar_Type>
            <Forced_Top_Transition>1.0</Forced_Top_Transition>
            <Forced_Bottom_Transition>1.0</Forced_Bottom_Transition>
            <Batch_Range>
                <Reynolds>{reynolds:g}</Reynolds>
                <Mach>{mach:g}</Mach>
                <NCrit>{ncrit:g}</NCrit>
            </Batch_Range>
        </Batch_Analysis_Data>
        <OpPoint_Range>
            <Alpha>{amin}, {amax}, {astep}</Alpha>
            <Spec_Alpha>true</Spec_Alpha>
            <From_Zero>true</From_Zero>
        </OpPoint_Range>
        <Output>
            <make_polars_bin_file>false</make_polars_bin_file>
            <make_polars_text_file>true</make_polars_text_file>
            <make_oppoints>false</make_oppoints>
        </Output>
        <Options>
            <Max_XFoil_Iterations>{iterations}</Max_XFoil_Iterations>
            <Repanel_Foils>false</Repanel_Foils>
        </Options>
    </Foil_Analysis>
</xflscript>
"""


def write_foil(code: str, directory: Path) -> Path:
    """Write one NACA section as a Selig-format .dat, from this project's
    own geometry. `surface()` already returns points from the trailing edge
    over the upper surface and back along the lower, which is the ordering
    .dat files use."""
    foil = Naca4.parse(code)
    x, y = foil.surface(n_per_side=PANELS_PER_SIDE)
    path = directory / f"NACA{code}.dat"
    with path.open("w") as handle:
        handle.write(f"NACA {code}\n")
        for xi, yi in zip(x, y):
            handle.write(f"{xi:12.7f} {yi:12.7f}\n")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xflr5", type=Path, default=XFLR5,
                        help="path to the xflr5 executable")
    args = parser.parse_args()

    if not args.xflr5.exists():
        print(f"XFLR5 not found at {args.xflr5}", file=sys.stderr)
        print("Install it from https://sourceforge.net/projects/xflr5/files/",
              file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="xflr5_") as tmp:
        work = Path(tmp)
        for name in ("foils", "analyses", "out", "polars", "xfoil"):
            (work / name).mkdir()

        for code in FOILS:
            write_foil(code, work / "foils")

        entries = "\n".join(
            f"            <Foil_File_Name>NACA{code}.dat</Foil_File_Name>"
            for code in FOILS)
        script = work / "foil_script.xml"
        script.write_text(SCRIPT_TEMPLATE.format(
            work=work, foil_entries=entries, reynolds=REYNOLDS, mach=MACH,
            ncrit=NCRIT, amin=ALPHA_MIN, amax=ALPHA_MAX, astep=ALPHA_STEP,
            iterations=MAX_XFOIL_ITERATIONS))

        result = subprocess.run(
            [str(args.xflr5), "--script", str(script), "-p"],
            capture_output=True, text=True, cwd=work)
        print(result.stdout)
        if "Finished script successfully" not in result.stdout:
            print("XFLR5 did not report success", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            return 1

        REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
        copied = 0
        for code in FOILS:
            produced = list((work / "xfoil").glob(f"NACA {code}_*.txt"))
            if not produced:
                print(f"no polar produced for NACA {code}", file=sys.stderr)
                return 1
            target = REFERENCE_DIR / f"naca{code}_T1_Re1e6_N9.txt"
            shutil.copy(produced[0], target)
            print(f"  wrote {target.relative_to(PROJECT_ROOT)}")
            copied += 1

    print(f"\n{copied} reference polars regenerated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

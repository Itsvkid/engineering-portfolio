#!/usr/bin/env python3
"""Regenerate the README's status block -- Stage J, the publication stage.

The README carried "37 tests" and "build.py arrives with Stage C" months
after there were 928 tests and nine stages of it. That is the failure mode
this script exists to close: a hand-maintained count is a claim nobody
re-checks, and this project's whole argument is that claims get checked.

The prose stays hand-written. Only the block between the two markers is
generated, and `tests/test_readme.py` fails if it has drifted -- the same
arrangement `tools/build_findings.py` has with `FINDINGS.md`.

    python tools/build_readme.py
"""
from __future__ import annotations

import collections
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solvers"))

import yaml  # noqa: E402

BEGIN = "<!-- BEGIN GENERATED: tools/build_readme.py -->"
END = "<!-- END GENERATED -->"

#: Stage letter -> what it delivers. The plan's own names.
STAGES = [
    ("A", "sources and transcription", "data/*.yaml, every value with a src:"),
    ("B", "cycle", "three Table XII ratings, the mixer, the station table"),
    ("C", "aero", "mean-line, through-flow, blading, CFD validation"),
    ("D", "thermal", "cooling, secondary air, clearance, combustor"),
    ("E", "mechanical", "blade and disc stress, frequencies, rotordynamics, attachments"),
    ("F", "materials and mass", "allowables, the module roll-up"),
    ("G", "geometry", "32 blade rows lofted to STEP"),
    ("H", "assembly", "hand CAD -- needs a human at the GUI"),
    ("I", "verification", "cross-discipline consistency, sensitivity, FINDINGS.md"),
    ("J", "publication", "meridional plot, Campbell match, glTF"),
]


def test_count():
    """Test FUNCTIONS, counted statically.

    Not `pytest --collect-only`: several test modules do real work at import
    -- Stage J2 builds beam models, J3 lofts and tessellates 32 rows -- so
    collection costs two minutes, and running pytest from inside pytest to
    print a number in a README is a poor trade. `@pytest.mark.parametrize`
    expands these into rather more cases at run time; this counts the
    functions, and says so."""
    import re as _re
    return sum(len(_re.findall(r"^def test_", p.read_text(), _re.M))
               for p in sorted((ROOT / "tests").glob("test_*.py")))


def findings_count():
    sys.path.insert(0, str(ROOT / "tools"))
    from build_findings import findings_index
    return len(findings_index())


def closures():
    c = yaml.safe_load((ROOT / "data" / "closures.yaml").read_text())["closures"]
    return c, collections.Counter(x["state"] for x in c)


def figures():
    out = []
    for p in sorted((ROOT / "solvers" / "publication" / "figures").glob("*.png")):
        out.append(p.relative_to(ROOT))
    return out


def block():
    c, by = closures()
    n_tests, n_find = test_count(), findings_count()
    open_ones = [x for x in c if x["state"] != "met"]

    L = [BEGIN, ""]
    L.append(f"**Status:** nine of ten stages built. "
             f"**{n_tests} test functions**, "
             f"**{n_find} numbered findings**, **{len(c)} closures** — "
             f"{by['met']} met, {by['half']} half, {by['gated']} gated. "
             "Stage H needs a human at a CAD GUI; Stage J is in progress.")
    L += ["", "| Stage | | State |", "|---|---|---|"]
    for letter, name, what in STAGES:
        rel = [x for x in c if x["stage"].rstrip("0123456789-") == letter
               or x["stage"] == letter]
        if letter == "A":
            state = "transcribed; four figure gaps remain"
        elif letter == "H":
            state = "**not started** — needs a human at the GUI"
        elif not rel:
            state = "built"
        else:
            g = sum(1 for x in rel if x["state"] == "gated")
            h = sum(1 for x in rel if x["state"] == "half")
            m = sum(1 for x in rel if x["state"] == "met")
            bits = ([f"{m} met"] if m else []) + ([f"{h} half"] if h else []) + \
                   ([f"**{g} gated**"] if g else [])
            state = ", ".join(bits)
        L.append(f"| **{letter}** | {name} — {what} | {state} |")

    L += ["", "### Validation", "",
          "Every solver states its tolerance in a `STEP0.md` **before** the "
          "run, and the tolerance is never edited afterwards. "
          "`data/closures.yaml` holds all of them with today's number, so "
          "the scoreboard below is read from the code rather than "
          "remembered.", "",
          "| Closure | Achieved vs band | |", "|---|---|---|"]
    for x in c:
        if x["band"] is None or x["achieved"] is None:
            got = "—"
        else:
            got = f"{x['achieved']} vs {x['band']}"
            if x["units"]:
                got += f" {x['units']}"
        mark = {"met": "met", "half": "half", "gated": "**gated**"}[x["state"]]
        L.append(f"| **{x['stage']}** — {x['what']} | {got} | {mark} |")

    L += ["", "### Figures", ""]
    for f in figures():
        L.append(f"- [`{f.name}`]({f})")

    L += ["", "### Outstanding", "",
          f"{len(open_ones)} closures are not met. None is open without a "
          "reason attached:", ""]
    for x in open_ones:
        why = (x.get("gate") or x.get("note") or "").strip().replace("\n", " ")
        why = re.sub(r"\s+", " ", why)[:190]
        L.append(f"- **{x['stage']}** ({x['state']}) — {x['what']}. {why}")
    L += ["",
          "The four gaps that are **transcription, not modelling**: the HPT "
          "disc profile has no absolute radial scale (blocks E2's peak stress "
          "and burst margin, and F2's disc masses); the HPC §3.2.3 dovetails "
          "(E5); the casing, liner and dome flowpaths (G); and the combustor "
          "liner hole areas (D2). None is a hard problem — they are figures "
          "nobody has digitised.", "", END]
    return "\n".join(L)


def main():
    p = ROOT / "README.md"
    s = p.read_text()
    if not (BEGIN in s and END in s):
        raise SystemExit("README.md has no generated block; add the markers first")
    new = block()
    s = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), lambda _: new,
               s, flags=re.S)
    p.write_text(s)
    print(f"wrote README.md: generated block, {len(new.splitlines())} lines")


if __name__ == "__main__":
    main()

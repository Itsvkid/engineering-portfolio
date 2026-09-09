"""Stage J unit J5: the drawing pack -- a GA with stations, one sheet per module.

A general arrangement is not a plot with a border round it. What makes it a
drawing is that **every dimension on it is answerable**: it comes from a
table or a dimensioned figure, or it is marked as not.

Two drafting conventions carry that here:

* A dimension in **parentheses** is a reference dimension -- on these
  sheets, one this project assumed rather than read. They are also listed
  in the title block, so a reader who takes a number off the sheet finds
  out immediately whether NASA printed it.
* A station with no published axial position is **absent**, not guessed.
  Four of the nine gas-path stations are missing for that reason, and the
  GA says which and why rather than spacing them out to look complete.

STEP0.md unit J5."""
from __future__ import annotations

from pathlib import Path

import yaml

from e3cycle.cycle import DATA

FIGDIR = Path(__file__).resolve().parent / "figures"
SHEET = (16.5, 11.7)          # A3 landscape, inches

#: What each sheet must say about what it cannot draw. Held as data rather
#: than buried in the plotting calls, so the tests assert on the statement
#: itself instead of grepping for a string that a line break can split.
GAPS = {
    "combustor": "NO DIMENSIONED GEOMETRY PUBLISHED",
    "hpt": "NO AIRFOIL IS DRAWN",
    "fan": "NO WALL CONTOUR IS DRAWN",
}
GAP_RULE = ("An empty sheet with the reason is a result; "
            "a missing sheet is a silence.")
TITLE_H = 0.155               # fraction of the sheet the title block takes


def _y(n):
    return yaml.safe_load((DATA / n).read_text())


# ------------------------------------------------------------- stations

def stations():
    """The nine gas-path stations, each with an axial position **or a
    reason it has none**.

    Positions are derived from unit J1's engine axis, so a station is only
    as certain as the module it belongs to. Four have no position at all:
    the inlet and fan face are upstream of the fan stacking axis by an
    amount no report gives, the bypass duct is a stream and not a plane in
    this projection, and the nozzle throat is aft of a mixer whose geometry
    was never dimensioned."""
    from publication.meridional import hpc_flowpath, layout
    L = layout()
    hpc = hpc_flowpath()
    igv = min(r["z_hub"] for r in hpc)
    ogv = max(max(r["z_hub"], r["z_tip"]) for r in hpc)
    out = [
        dict(n=1, name="inlet", x=None, basis=None,
             why="freestream; no plane in this projection"),
        dict(n=2, name="fan face", x=None, basis=None,
             why="upstream of the fan stacking axis by an unpublished amount"),
        dict(n=13, name="bypass duct", x=None, basis=None,
             why="a stream, not a plane; the bypass duct wall is not dimensioned"),
        dict(n=21, name="booster exit", x=None, basis=None,
             why="the booster's own axial station was never published"),
        dict(n=25, name="HPC inlet", x=L["hpc"]["x0"] + igv, basis="published",
             why=None),
        dict(n=3, name="compressor discharge", x=L["hpc"]["x0"] + ogv,
             basis="published", why=None),
        dict(n=4, name="HPT rotor inlet", x=L["hpt"]["x0"], basis="assumed",
             why=None),
        dict(n=45, name="HPT exit / LPT inlet", x=L["lpt"]["x0"],
             basis="assumed", why=None),
        dict(n=5, name="LPT exit", x=None, basis=None,
             why="the mixer plane; the 18-lobe mixer was never dimensioned"),
        dict(n=8, name="nozzle throat", x=None, basis=None,
             why="aft of the mixer; no published axial geometry"),
    ]
    return out


def dimensions():
    """Every callout the pack draws, with where it came from.

    `basis` is 'published' when a report prints the number, 'derived' when
    it falls out of published geometry, and 'assumed' when this project
    chose it. Only 'assumed' is parenthesised on the sheet."""
    from publication.meridional import assumed_offsets, hpc_flowpath, layout
    L, off = layout(), assumed_offsets()
    hpc = hpc_flowpath()
    lpt = L["lpt"]["rows"]
    size = _y("e3-fps-published.yaml")["size"]
    out = [
        dict(what="fan tip diameter", value=size["fan_tip_diameter_m"] * 100,
             units="cm", basis="published", src="CR-168219 sec 4.3 p.32"),
        dict(what="fan inlet radius ratio", value=size["fan_inlet_radius_ratio"],
             units="", basis="published", src="CR-168219 sec 5.1.1 p.41"),
        dict(what="HPC length, IGV LE to OGV TE", value=L["hpc"]["length"],
             units="cm", basis="derived", src="HPC flowpath, Table XXI"),
        dict(what="HPC inlet tip radius",
             value=max(r["r_tip"] for r in hpc if r["edge"] == "LE"),
             units="cm", basis="published", src="Table XXI streamline 12"),
        dict(what="HPT axial length", value=L["hpt"]["length"], units="cm",
             basis="published", src="HPT report Fig 3, dimensioned"),
        dict(what="LPT exit tip radius", value=max(r["r_tip"] for r in lpt),
             units="cm", basis="published", src="LPT appendix sections"),
        dict(what="transition duct, HPT exit to LPT vane 1",
             value=min(r["z_hub"] for r in lpt), units="cm", basis="derived",
             src="LPT sections, z from the HPT exit plane"),
        dict(what="fan stacking axis to HPC rotor 1",
             value=off["fan_sa_to_hpc_r1_le"]["value_cm"], units="cm",
             basis="assumed", src="bearing spans, CR-168219; allowable 110-150"),
        dict(what="HPC OGV exit to HPT vane 1",
             value=off["hpc_ogv_te_to_hpt_vane1"]["value_cm"], units="cm",
             basis="assumed", src="diffuser + combustor; allowable 45-55"),
    ]
    return out


def _fmt(d):
    """A reference (assumed) dimension is parenthesised, as on any drawing."""
    v = f"{d['value']:.1f} {d['units']}".strip() if d["units"] else \
        f"{d['value']:.3f}"
    return f"({v})" if d["basis"] == "assumed" else v


# --------------------------------------------------------------- sheets

def _title_block(fig, ax, title, sheet_no, of, notes):
    """Every sheet carries its own provenance: a drawing leaves the
    repository and must still say where its numbers came from."""
    ax.set_axis_off()
    ax.add_patch(__import__("matplotlib").patches.Rectangle(
        (0, 0), 1, 1, transform=ax.transAxes, fill=False, ec="0.2", lw=1.2))
    ax.plot([0.62, 0.62], [0, 1], transform=ax.transAxes, color="0.2", lw=1.0)
    ax.text(0.012, 0.80, title, transform=ax.transAxes, fontsize=12,
            weight="bold", va="top")
    ax.text(0.012, 0.55, "NASA/GE Energy Efficient Engine — Flight Propulsion "
            "System.  Reconstructed from public-domain NASA reports.",
            transform=ax.transAxes, fontsize=7.5, va="top")
    import textwrap
    ax.text(0.012, 0.38, "\n".join(textwrap.wrap(notes, 118)),
            transform=ax.transAxes, fontsize=6.8, va="top", linespacing=1.5,
            color="0.25")
    ax.text(0.632, 0.80, "PF-09  E³ RECONSTRUCTION", transform=ax.transAxes,
            fontsize=8.5, weight="bold", va="top")
    ax.text(0.632, 0.58, "DATUM   fan rotor stacking axis, x = 0\n"
            "UNITS   centimetres\n"
            "PROJ    meridional half-section\n"
            "( )     reference dimension — ASSUMED, not published",
            transform=ax.transAxes, fontsize=7, va="top", linespacing=1.5)
    ax.text(0.985, 0.80, f"SHEET {sheet_no} OF {of}", transform=ax.transAxes,
            fontsize=8.5, ha="right", va="top")
    ax.text(0.985, 0.12, "generated by solvers/publication/drawings.py",
            transform=ax.transAxes, fontsize=6.5, ha="right", color="0.45")


def _dim(ax, x0, x1, y, label, assumed=False):
    col = "#8a4f0a" if assumed else "0.25"
    ax.annotate("", xy=(x1, y), xytext=(x0, y),
                arrowprops=dict(arrowstyle="<->", color=col, lw=0.9))
    for x in (x0, x1):
        ax.plot([x, x], [y - 1.6, y + 1.6], color=col, lw=0.7)
    ax.text((x0 + x1) / 2, y + 1.0, label, ha="center", va="bottom",
            fontsize=7.4, color=col)


def _walls(ax, L):
    hx = L["hpc"]["x0"]
    for kz, kr in (("z_hub", "r_hub"), ("z_tip", "r_tip")):
        ax.plot([r[kz] + hx for r in L["hpc"]["rows"]],
                [r[kr] for r in L["hpc"]["rows"]], color="0.1", lw=1.3)
    px = L["lpt"]["x0"]
    for kz, kr in (("z_hub", "r_hub"), ("z_tip", "r_tip")):
        ax.plot([r[kz] + px for r in L["lpt"]["rows"]],
                [r[kr] for r in L["lpt"]["rows"]], color="0.1", lw=1.3)
    t = L["hpt"]
    for k in ("r_hub", "r_tip"):
        ax.plot([s["z"] + t["x0"] for s in t["stations"]],
                [s[k] for s in t["stations"]], color="0.1", lw=1.3)


def sheet_ga(fig):
    """Sheet 1 -- the general arrangement, with the stations that have a
    published position and a note naming the four that do not."""
    from publication.meridional import layout
    L = layout()
    ax = fig.add_axes([0.045, 0.30, 0.925, 0.63])
    _walls(ax, L)

    st = stations()
    placed = [s for s in st if s["x"] is not None]
    missing = [s for s in st if s["x"] is None]
    for s in placed:
        assumed = s["basis"] == "assumed"
        col = "#8a4f0a" if assumed else "#1f4e79"
        ax.plot([s["x"], s["x"]], [0, 68], color=col, lw=0.8,
                ls=(0, (6, 3)), zorder=1)
        lab = f"({s['n']})" if assumed else str(s["n"])
        ax.text(s["x"], 70, lab, ha="center", va="bottom", fontsize=9,
                weight="bold", color=col)
        ax.text(s["x"], 62, s["name"], ha="center", va="top", fontsize=6.2,
                color=col, rotation=90)

    d = {x["what"]: x for x in dimensions()}
    hx, px = L["hpc"]["x0"], L["lpt"]["x0"]
    _dim(ax, 0, hx, 88, f"fan stacking axis to HPC rotor 1  "
         f"{_fmt(d['fan stacking axis to HPC rotor 1'])}", assumed=True)
    _dim(ax, hx, hx + L["hpc"]["length"], 78,
         f"HPC  {_fmt(d['HPC length, IGV LE to OGV TE'])}")
    _dim(ax, L["hpt"]["x0"], L["hpt"]["x0"] + L["hpt"]["length"], 78,
         f"HPT  {_fmt(d['HPT axial length'])}")

    ax.plot([-8, 355], [0, 0], color="0.35", lw=0.8, ls=(0, (12, 4, 2, 4)))
    ax.text(-8, 1.5, "℄", fontsize=11, color="0.35")
    ax.set_xlim(-14, 356)
    ax.set_ylim(-4, 96)
    ax.set_aspect("equal")
    ax.set_xlabel("axial position from the fan rotor stacking axis, cm",
                  fontsize=8)
    ax.set_ylabel("radius, cm", fontsize=8)
    ax.tick_params(labelsize=7.5)
    ax.grid(alpha=0.16, lw=0.4)
    ax.set_axisbelow(True)

    notes = ("STATIONS DRAWN: " +
             ", ".join(str(s["n"]) for s in placed) +
             ".   NOT DRAWN, no published axial position: " +
             "; ".join(f"{s['n']} ({s['why']})" for s in missing[:2]) + " …")
    return notes, len(missing)


def sheet_module(fig, name, rows, extra=None):
    """One detail sheet: the module's own walls on its own datum."""
    ax = fig.add_axes([0.06, 0.30, 0.90, 0.62])
    if rows:
        z0 = min(min(r["z_hub"], r["z_tip"]) for r in rows)
        for kz, kr in (("z_hub", "r_hub"), ("z_tip", "r_tip")):
            ax.plot([r[kz] - z0 for r in rows], [r[kr] for r in rows],
                    color="0.1", lw=1.4)
        for r in rows:
            if r["edge"] == "LE":
                ax.plot([r["z_hub"] - z0, r["z_tip"] - z0],
                        [r["r_hub"], r["r_tip"]], color="0.55", lw=0.7)
        ax.set_aspect("equal")
    if extra:
        extra(ax)
    ax.set_xlabel("axial position on this module's own datum, cm", fontsize=8)
    ax.set_ylabel("radius, cm", fontsize=8)
    ax.tick_params(labelsize=7.5)
    ax.grid(alpha=0.16, lw=0.4)
    ax.set_axisbelow(True)
    return ax


def build(path=None):
    """The pack, as a multi-page PDF."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from publication.meridional import fan_stations, hpc_flowpath, layout, \
        lpt_flowpath

    L = layout()
    path = Path(path or (FIGDIR / "e3-drawing-pack.pdf"))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheets = []

    with PdfPages(path) as pdf:
        pages = 6

        # --- 1: GA
        fig = plt.figure(figsize=SHEET)
        notes, n_missing = sheet_ga(fig)
        tb = fig.add_axes([0.045, 0.045, 0.925, TITLE_H])
        _title_block(fig, tb, "GENERAL ARRANGEMENT — meridional half-section",
                     1, pages, notes)
        pdf.savefig(fig); plt.close(fig); sheets.append("GA")

        # --- 2: fan and booster
        fig = plt.figure(figsize=SHEET)

        def fan_extra(ax):
            st = fan_stations()
            for i, s in enumerate(st):
                # the stacking axis at its published z; the other two spread
                # either side of it, dashed, because their z is unknown
                x = s["z"] if s["z_known"] else (-14.0 if i == 0 else 30.0)
                ax.plot([x, x], [s["r_hub"], s["r_tip"]], color="#8c3b2f",
                        lw=2.8, ls="-" if s["z_known"] else (0, (4, 2.5)))
                for r in (s["r_hub"], s["r_tip"]):
                    ax.plot([x], [r], marker="_", ms=13, color="#8c3b2f")
                ax.text(x, s["r_tip"] + 3 + 8 * (i % 2), s["name"],
                        ha="center", va="bottom", fontsize=7.4,
                        color="#8c3b2f", linespacing=1.2)
                ax.text(x, s["r_hub"] - 3,
                        f"r {s['r_hub']:.1f}–{s['r_tip']:.1f}",
                        ha="center", va="top", fontsize=6.4, color="0.4")
            ax.set_xlim(-26, 46)
            ax.set_ylim(0, 124)
            ax.set_aspect("equal")
        sheet_module(fig, "fan", None, fan_extra)
        tb = fig.add_axes([0.045, 0.045, 0.925, TITLE_H])
        _title_block(fig, tb, "FAN AND BOOSTER — radial stations", 2, pages,
                     GAPS["fan"] + ". The fan module has three "
                     "dimensioned radial stations and one axial position "
                     "(Fig 15 stacking axis, solid). No hub or casing line "
                     "was published against an axial coordinate, so none is "
                     "drawn. Dashed bars are radii only, placed indicatively.")
        pdf.savefig(fig); plt.close(fig); sheets.append("fan and booster")

        # --- 3: HPC
        fig = plt.figure(figsize=SHEET)
        ax = sheet_module(fig, "hpc", hpc_flowpath())
        d = {x["what"]: x for x in dimensions()}
        _dim(ax, 0, L["hpc"]["length"], 40,
             f"{_fmt(d['HPC length, IGV LE to OGV TE'])}")
        tb = fig.add_axes([0.045, 0.045, 0.925, TITLE_H])
        _title_block(fig, tb, "HIGH-PRESSURE COMPRESSOR — 10 stages, 21 rows",
                     3, pages,
                     "Hub and tip from Table XXI streamlines 1 and 12, 42 "
                     "stations. Row lines mark leading edges. Pressure ratio "
                     "23.0 (CR-168219 Table XIV); the HPC report's abstract "
                     "quotes 22.6 and both are recorded.")
        pdf.savefig(fig); plt.close(fig); sheets.append("HPC")

        # --- 4: combustor -- the sheet that says there is no sheet
        fig = plt.figure(figsize=SHEET)
        ax = fig.add_axes([0.06, 0.30, 0.90, 0.62])
        ax.set_axis_off()
        ax.text(0.5, 0.62, GAPS["combustor"],
                ha="center", fontsize=17, weight="bold", color="#8c2f39",
                transform=ax.transAxes)
        ax.text(0.5, 0.47,
                "The double-annular combustor appears in Figures 1, 22 and 79 "
                "as undimensioned drawings.\nLiner axial coordinates, dome "
                "height and the liner hole areas are not printed anywhere in "
                "the reports read.\n\nWhat IS published: double-annular, 60 "
                "cups, 30 fuel nozzles (CR-168219 sec 5.3 p.57),\nand the "
                "exit temperature profile that Stage D's cooling design is "
                "built on.\n\nThis sheet is deliberately empty. An empty "
                "sheet with the reason is a result;\na missing sheet is a "
                "silence.",
                ha="center", va="top", fontsize=9.5, linespacing=1.7,
                transform=ax.transAxes, color="0.2")
        tb = fig.add_axes([0.045, 0.045, 0.925, TITLE_H])
        _title_block(fig, tb, "COMBUSTOR — double annular", 4, pages,
                     "A3 backlog item. It also gates unit D2 (liner hole "
                     "areas) and is half the reason the HPC-to-HPT axial "
                     "offset must be assumed rather than built up.")
        pdf.savefig(fig); plt.close(fig); sheets.append("combustor")

        # --- 5: HPT
        fig = plt.figure(figsize=SHEET)
        ax = fig.add_axes([0.06, 0.30, 0.90, 0.62])
        t = L["hpt"]
        for k in ("r_hub", "r_tip"):
            ax.plot([s["z"] for s in t["stations"]],
                    [s[k] for s in t["stations"]], color="0.1", lw=1.4)
        for s in t["stations"]:
            ax.plot([s["z"], s["z"]], [s["r_hub"], s["r_tip"]], color="0.75",
                    lw=0.7)
            ax.text(s["z"], s["r_tip"] + 0.5, s["row"].replace("_", " "),
                    rotation=90, fontsize=6.2, ha="center", va="bottom",
                    color="0.35")
        _dim(ax, 0, t["length"], 27, _fmt(
            {x["what"]: x for x in dimensions()}["HPT axial length"]))
        ax.set_xlim(-2, 23)
        ax.set_ylim(24, 46)
        ax.set_aspect("equal")
        ax.set_xlabel("axial position, HPT Fig 3 datum, cm", fontsize=8)
        ax.set_ylabel("radius, cm", fontsize=8)
        ax.tick_params(labelsize=7.5)
        ax.grid(alpha=0.16, lw=0.4)
        tb = fig.add_axes([0.045, 0.045, 0.925, TITLE_H])
        _title_block(fig, tb, "HIGH-PRESSURE TURBINE — 2 stages", 5, pages,
                     "Five dimensioned stations from HPT report Fig 3. "
                     + GAPS["hpt"] +
                     ": the HPT blade and vane coordinates "
                     "were never published — the reports give throat "
                     "dimensions and aspect ratio only. Radii are printed; "
                     "their axial positions are read off the drawing's own "
                     "scale, ±0.3 cm.")
        pdf.savefig(fig); plt.close(fig); sheets.append("HPT")

        # --- 6: LPT
        fig = plt.figure(figsize=SHEET)
        ax = sheet_module(fig, "lpt", lpt_flowpath())
        tb = fig.add_axes([0.045, 0.045, 0.925, TITLE_H])
        _title_block(fig, tb, "LOW-PRESSURE TURBINE — 5 stages, 10 rows",
                     6, pages,
                     "Walls and rows from the thirty printed section "
                     "coordinates. This module's z runs from the HPT exit "
                     "plane, which is the one inter-module offset the "
                     "reports do give — the transition duct at the left is "
                     "measured, not assumed.")
        pdf.savefig(fig); plt.close(fig); sheets.append("LPT")

    return path, sheets


def summary():
    st = stations()
    placed = [s for s in st if s["x"] is not None]
    d = dimensions()
    assumed = [x for x in d if x["basis"] == "assumed"]
    L = ["Stage J unit J5 -- the drawing pack", ""]
    L.append(f"   6 sheets: GA, fan and booster, HPC, combustor, HPT, LPT")
    L.append(f"   stations placed {len(placed)} of {len(st)}; "
             f"{len(st) - len(placed)} have no published axial position "
             "and are not drawn")
    for s in st:
        mark = f"x = {s['x']:7.2f} cm  {s['basis']}" if s["x"] is not None \
            else f"NOT DRAWN -- {s['why']}"
        L.append(f"      station {s['n']:<3} {s['name']:<22} {mark}")
    L += ["", f"   {len(d)} dimensions, of which {len(assumed)} are ASSUMED "
          "and parenthesised on the sheet:"]
    for x in d:
        L.append(f"      {_fmt(x):>12}  {x['what']:<42} {x['basis']:<10} "
                 f"{x['src']}")
    return "\n".join(L)


if __name__ == "__main__":
    print(summary())
    p, sheets = build()
    root = Path(__file__).resolve().parents[2]
    print(f"\n   wrote {p.relative_to(root)}  "
          f"{p.stat().st_size / 1e3:.0f} kB, {len(sheets)} sheets")

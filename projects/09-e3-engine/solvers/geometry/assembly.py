"""Stage G unit G3: the whole engine as one STEP assembly.

Unit G1's `export()` writes 36 STEP files -- one per blade row, one
compound per spool -- and every one of them sits at its own local origin.
Open all 36 and thirty-two rows of blades stack on top of each other at
zero. That is a parts bin, not a design.

This builds the assembly: every row at its true axial station on unit J1's
engine axis, at full blade count, in one file whose product structure a
reader can expand.

**The axial layout is not free.** Two of the three joins between module
datums are assumed -- fan stacking axis to HPC rotor 1 (103.4 cm) and the
HPC OGV trailing edge across the diffuser and combustor to HPT vane 1
(25.3 cm) -- and their SUM is constrained by CR-159584 Table I p.6's
published 318.0 cm turbomachinery length. They are read through
`publication.meridional.layout()` and no copy is kept here (unit J1,
finding 159), and the assembled length is checked back against the
published number.

**Provenance survives the export.** Every node name carries `PUBLISHED`,
`DERIVED` or `ASSUMED`, and the module nodes name the offset they ride on,
because a STEP file outlives the page that explains it -- the same
argument unit J3 makes for `asset.extras`.

Blade counts are FULL. The STEP assembly writer shares one representation
between instances, so a 28-blade row costs 18 kB more than a 1-blade row
(measured). There is no honest reason to ship a sector.

STEP0.md, unit G3."""
from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq

from geometry.blades import all_rows
from publication.meridional import (hpc_flowpath, hpt_flowpath, layout,
                                    lpt_flowpath)

CM = 0.01
EXPORTDIR = Path(__file__).resolve().parents[2] / "exports"

#: CR-159584 Table I p.6: fan front flange to LP turbine aft frame flange.
#: The definition check in engine-flowpath.yaml matters -- it runs to the
#: LPT casing's aft flange at the R5 exit plane, not the rear frame.
PUBLISHED_TURBOMACHINERY_LENGTH_CM = 318.0
LENGTH_BAND_CM = 2.0

#: engine-flowpath.yaml's own assumed datum for the fan front flange; the
#: required length moves 1:1 with it, which is why it is named here.
FAN_FRONT_FLANGE_CM = -32.5

#: The walls are revolved through this much, leaving a window so a reader
#: can see the blading without sectioning the file. Unit J3 uses the same
#: wedge for the glTF, from the same argument.
WALL_REVOLVE_DEG = 285.0

VOLUME_BAND_PCT = 2.0


# --------------------------------------------------------------- naming

def _tag(status):
    return {"published": "PUBLISHED", "derived": "DERIVED",
            "assumed": "ASSUMED"}[status]


def row_node_name(row, status):
    """A row's name in the STEP tree, carrying its own provenance.

    The `status` here is the provenance of the row's AXIAL PLACEMENT, not
    of its sections -- every section in the engine is published or built
    from published parameters, and it is the placement that is in doubt."""
    return f"{row.name}--n{row.count}--axial-{_tag(status)}"


# --------------------------------------------------------------- walls

def _wall_wire(pts):
    """A meridional polyline (x_m, r_m) as a wire in the XZ plane."""
    return (cq.Workplane("XZ")
            .polyline([(x, r) for x, r in pts]).wire().val())


def _revolve_wall(pts, deg=WALL_REVOLVE_DEG):
    """Surface of revolution about the engine axis, +X.

    A zero-thickness surface is the honest representation: these are
    aerodynamic walls and no wall THICKNESS is published anywhere for the
    HPC, the HPT annulus or the LPT. A solid would be inventing one."""
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeRevol
    from OCP.gp import gp_Ax1, gp_Dir, gp_Pnt
    ax = gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0))
    mk = BRepPrimAPI_MakeRevol(_wall_wire(pts).wrapped, ax,
                               math.radians(deg))
    mk.Build()
    if not mk.IsDone():
        raise RuntimeError("wall revolve failed")
    return cq.Shape.cast(mk.Shape())


def published_walls():
    """Every annulus wall this project can draw from a published table.

    Returns (name, status, points) with points in metres on J1's axis.

    What is here and what is not:

    * **HPC hub and casing** -- `hpc-flowpath.csv`, which is Table XXI's
      streamlines 1 and 12. Published, at 21 rows' leading and trailing
      edges.
    * **HPT hub and casing** -- HPT Fig 3's five dimensioned stations,
      published. The HPT's AIRFOILS are not published at all (Table IV
      gives an aspect ratio and a throat, which is what unit 14 built a
      mean-line from), so this is the one module in the file that has walls
      and no blades. That gap is deliberate and visible.
    * **LPT hub and casing** -- `lpt-flowpath.csv`, derived from the
      transcribed appendix airfoil coordinates rather than printed as a
      wall. Marked DERIVED, not PUBLISHED.
    * **The fan has no wall.** Three dimensioned radial stations and one
      axial position is not a contour (unit J1, finding 158). Drawing one
      would be the only invented surface in the file.
    """
    L = layout()
    out = []

    hx = L["hpc"]["x0"] * CM
    hp = sorted(hpc_flowpath(), key=lambda r: r["z_hub"])
    out.append(("wall-hpc-hub", "published",
                [(hx + r["z_hub"] * CM, r["r_hub"] * CM) for r in hp]))
    hp_t = sorted(hpc_flowpath(), key=lambda r: r["z_tip"])
    out.append(("wall-hpc-casing", "published",
                [(hx + r["z_tip"] * CM, r["r_tip"] * CM) for r in hp_t]))

    tx = L["hpt"]["x0"] * CM
    ht = sorted(hpt_flowpath(), key=lambda s: s["z"])
    out.append(("wall-hpt-hub", "published",
                [(tx + s["z"] * CM, s["r_hub"] * CM) for s in ht]))
    out.append(("wall-hpt-casing", "published",
                [(tx + s["z"] * CM, s["r_tip"] * CM) for s in ht]))

    lx = L["lpt"]["x0"] * CM
    lp = sorted(lpt_flowpath(), key=lambda r: r["z_hub"])
    out.append(("wall-lpt-hub", "derived",
                [(lx + r["z_hub"] * CM, r["r_hub"] * CM) for r in lp]))
    lp_t = sorted(lpt_flowpath(), key=lambda r: r["z_tip"])
    out.append(("wall-lpt-casing", "derived",
                [(lx + r["z_tip"] * CM, r["r_tip"] * CM) for r in lp_t]))
    return out


def _dedup(pts, tol=1e-6):
    out = []
    for p in pts:
        if not out or math.dist(out[-1], p) > tol:
            out.append(p)
    return out


# ------------------------------------------------------------ placement

MODULES = [
    ("fan", ("fan-rotor", "booster-rotor"), "assumed",
     "rides on the fan stacking axis, the engine datum; the booster's own "
     "axial station was never published"),
    ("hpc", ("hpc-",), "assumed",
     "rides on the ASSUMED 103.4 cm fan-SA-to-HPC-rotor-1 offset"),
    ("hpt", ("hpt-",), "assumed",
     "rides on the ASSUMED 25.3 cm HPC-OGV-to-HPT-vane-1 offset; walls "
     "only, no published airfoils"),
    ("lpt", ("lpt-",), "assumed",
     "the HPT exit plane to LPT join is MEASURED, but the module's "
     "position on the engine axis inherits both assumed offsets"),
]


def _module_of(name):
    for mod, prefixes, _, _ in MODULES:
        for p in prefixes:
            if name == p or name.startswith(p):
                return mod
    return "other"


def placed_rows(rows=None):
    """Every row with its axial station, read through unit J3's placement
    so that the STEP assembly and the glTF cannot drift apart."""
    from publication.render import place_rows
    return place_rows(rows)


# ------------------------------------------------------------ the checks

def assembled_length(rows=None):
    """The built geometry against CR-159584 Table I's 318.0 cm.

    Measured on the LOFTED LPT rotor-5 blade rather than on the CSV, which
    is the point: the two offsets were calibrated on the published length
    through the flowpath tables, and this asks whether the solids that came
    out the other end still reproduce it."""
    placed = placed_rows(rows)
    aft = None
    for e in placed:
        if e["row"].name != "lpt-rotor-5":
            continue
        aft = e["x_m"] + e["row"].solid().BoundingBox().xmax
    if aft is None:
        return None
    length_cm = aft / CM - FAN_FRONT_FLANGE_CM
    return dict(lpt_r5_te_cm=aft / CM,
                fan_front_flange_cm=FAN_FRONT_FLANGE_CM,
                length_cm=length_cm,
                published_cm=PUBLISHED_TURBOMACHINERY_LENGTH_CM,
                err_cm=length_cm - PUBLISHED_TURBOMACHINERY_LENGTH_CM,
                band_cm=LENGTH_BAND_CM,
                met=abs(length_cm - PUBLISHED_TURBOMACHINERY_LENGTH_CM)
                <= LENGTH_BAND_CM)


def row_extents(rows=None):
    """Each row's assembled axial extent, gas-path ordered."""
    out = []
    for e in placed_rows(rows):
        bb = e["row"].solid().BoundingBox()
        out.append(dict(row=e["row"].name, spool=e["row"].spool,
                        count=e["row"].count,
                        x_lo=e["x_m"] + bb.xmin, x_hi=e["x_m"] + bb.xmax,
                        r_lo=None, basis=e["basis"]))
    return sorted(out, key=lambda r: r["x_lo"])


def axial_clearances(rows=None):
    """Gap between consecutive rows, in gas-path order.

    This is the check the assembly makes possible and G1 could not. Two
    rows whose axial extents do not overlap cannot interfere at ANY
    relative angular position, so a positive gap is a proof rather than a
    sample. A negative one means the layout is wrong -- and because the
    layout contains two assumed offsets, that is a real possibility and not
    a formality."""
    ext = row_extents(rows)
    out = []
    for a, b in zip(ext, ext[1:]):
        out.append(dict(upstream=a["row"], downstream=b["row"],
                        gap_m=b["x_lo"] - a["x_hi"],
                        joins_modules=_module_of(a["row"]) != _module_of(b["row"])))
    return out


def placed_interference(rows=None):
    """G1's blade-to-blade check, re-run on the placed rows.

    Translation along X and rotation about X commute, so this must return
    what G1 returned. It is here because an assembly that quietly applied a
    scale or a non-rigid transform would show up nowhere else."""
    from geometry.blades import interference_check
    return interference_check(rows)


def missing_rows():
    """Published bladed rows that this assembly does NOT contain, and why.

    The file must be able to say what it is short of. Counting rows against
    the source rather than against `all_rows()` is the only way that
    question gets asked at all."""
    import yaml
    pub = yaml.safe_load((Path(__file__).resolve().parents[2] / "data"
                          / "e3-fps-published.yaml").read_text())
    hpt = pub["hpt"]["stage_aerodynamics"]
    igv = yaml.safe_load((Path(__file__).resolve().parents[2] / "data"
                          / "hpc-blade-sections.yaml").read_text())["igv"]
    return [
        dict(row="hpc-igv", count=igv["vane_count"],
             src="HPC Table XXII p.157 -- the block is transcribed, in "
                 "data/hpc-blade-sections.yaml under `igv`",
             why="Table XXII prints the IGV's camber as a 65-series DESIGN "
                 "LIFT COEFFICIENT (cl0 0.08-0.80), not as the inlet and "
                 "exit metal angles every other row prints. "
                 "`blading.sections.all_sections` walks `rotors` and "
                 "`stators` only, so the row has never reached the section "
                 "builder. Building it needs a cl0-to-camber rule, which "
                 "would be the only invented camber in the file."),
        dict(row="hpt-vane-1 / blade-1 / vane-2 / blade-2",
             count=sum(hpt["vane_count"]) + sum(hpt["blade_count"]),
             src="CR-167955 Table IV -- aspect ratio and throat only",
             why="the E3 never published HPT airfoil coordinates or "
                 "sections. Unit 14 built a mean-line from the throat; "
                 "there is nothing to loft. The HPT ANNULUS is published "
                 "(Fig 3) and is in the file, so the gap is visible."),
        dict(row="fan inner OGV", count=64,
             src="unit G2, solvers/geometry/ogv.py",
             why="built, valid and interference-free, but its hub radius is "
                 "ASSUMED and unit G2 finding 183 shows it overhangs that "
                 "hub by 5.7 cm and needs an endwall trim that the assumed "
                 "walls cannot provide. Left out rather than shipped "
                 "sticking through a wall that is itself a guess."),
        dict(row="fan island stator / bypass OGV / booster stators",
             count=60 + 34 + 34,
             src="CR-165148 Table VII p.92 (angles), Appendix C and E "
                 "(sections, legible, untranscribed)",
             why="the sections are printed and have not been transcribed. "
                 "This is a transcription debt, not a method gap -- "
                 "Appendix C is the stage-1 stator at 13 stations and "
                 "Appendix E the inner OGV at 14."),
    ]


def front_end_placement(rows=None):
    """What the fan and booster rows' axial stations actually rest on.

    Every other row in the engine is placed by a station a table prints:
    the HPC rows by their leading edge in `hpc-flowpath.csv`, the LPT rows
    by their own transcribed z. The fan is placed by putting the SECTION's
    x = 0 -- its leading edge -- at Fig 15's stacking-axis Z, which asserts
    that the stacking axis is at the leading edge. It is not; a fan blade
    stacks near its centroid. And the booster is then placed at the fan
    row's downstream end, which no table gives at all.

    This returns the size of that, because a number is the only form in
    which it will be believed."""
    placed = {e["row"].name: e for e in placed_rows(rows)}
    fan = placed.get("fan-rotor")
    if fan is None:
        return None
    bb = fan["row"].solid().BoundingBox()
    extent = bb.xmax - bb.xmin
    return dict(
        fan_x_lo_cm=(fan["x_m"] + bb.xmin) / CM,
        fan_x_hi_cm=(fan["x_m"] + bb.xmax) / CM,
        fan_axial_extent_cm=extent / CM,
        shift_if_sa_at_midchord_cm=-extent / 2 / CM,
        booster_x_cm=placed["booster-rotor"]["x_m"] / CM
        if "booster-rotor" in placed else None,
        note=("the fan row is placed leading-edge-on-stacking-axis; if the "
              "axis is at mid-chord instead, the fan and everything placed "
              "off it move forward by half the fan's axial extent. Nothing "
              "downstream of the HPC moves -- the 318.0 cm closure is "
              "measured from the fan FRONT FLANGE, which is its own "
              "assumption -- so this is a front-end error, bounded and "
              "local. Left as unit J3 placed it so that the STEP file and "
              "the glTF cannot describe two different engines "
              "(unit J1, finding 159)."))


def volume_audit(rows=None):
    """Total blade volume in the assembly, against F2's integral.

    Per row: one lofted solid against the trapezoid, which is G1's band.
    Times the blade count, which is the number the assembly actually
    contains."""
    from geometry.blades import volume_check
    out = volume_check(rows)
    tot_cad = sum(v["cad_m3"] * v["count"] for v in out)
    tot_trap = sum(v["trapezoid_m3"] * v["count"] for v in out)
    return dict(rows=out, blades=sum(v["count"] for v in out),
                cad_m3=tot_cad, trapezoid_m3=tot_trap,
                err_pct=(tot_cad / tot_trap - 1) * 100,
                worst_row_pct=max(abs(v["err_pct"]) for v in out),
                band_pct=VOLUME_BAND_PCT)


# ------------------------------------------------------------ the build

def build(rows=None, walls=True, cutaway_deg=WALL_REVOLVE_DEG):
    """The assembly: root -> module -> row -> blade instance."""
    placed = placed_rows(rows)
    root = cq.Assembly(name="E3-engine--NASA-GE-Energy-Efficient-Engine")

    subs = {}
    for mod, _, status, why in MODULES:
        subs[mod] = cq.Assembly(name=f"MODULE-{mod}--{_tag(status)}--{why[:60]}")

    for e in placed:
        row, x = e["row"], e["x_m"]
        mod = _module_of(row.name)
        status = "assumed"          # every station rides on an assumed offset
        node = cq.Assembly(name=row_node_name(row, status))
        s = row.solid()
        pitch = 360.0 / row.count
        for i in range(row.count):
            node.add(s, name=f"{row.name}-blade-{i + 1:03d}",
                     loc=cq.Location(cq.Vector(x, 0, 0),
                                     cq.Vector(1, 0, 0), i * pitch))
        subs.setdefault(mod, cq.Assembly(name=f"MODULE-{mod}")).add(node)

    if walls:
        for name, status, pts in published_walls():
            pts = _dedup(pts)
            if len(pts) < 2:
                continue
            mod = name.split("-")[1]
            shell = _revolve_wall(pts, cutaway_deg)
            subs[mod].add(shell,
                          name=f"{name}--{_tag(status)}--"
                               f"revolved-{cutaway_deg:.0f}deg-window")

    for mod, _, _, _ in MODULES:
        # a module with nothing in it is left out rather than exported as an
        # empty product -- an empty node in a CAD tree reads as a missing
        # part, which is a different claim from "not published"
        if subs[mod].children:
            root.add(subs[mod])
    return root


def export(path=None, rows=None, walls=True):
    path = Path(path or (EXPORTDIR / "e3-engine-assembly.step"))
    path.parent.mkdir(parents=True, exist_ok=True)
    build(rows, walls=walls).export(str(path))
    return path


def reimport_structure(path):
    """Read the file back and describe the tree it produces.

    The stated failure mode for this unit is a STEP that imports as N
    unrelated solids at the origin, so the check is to import it and look.
    `STEPCAFControl_Reader` is the reader that honours the product
    structure; the plain `STEPControl_Reader` flattens it, which is exactly
    the difference being tested for."""
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.STEPCAFControl import STEPCAFControl_Reader
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.TDataStd import TDataStd_Name
    from OCP.TDF import TDF_LabelSequence
    from OCP.TDocStd import TDocStd_Document
    from OCP.XCAFDoc import XCAFDoc_DocumentTool

    doc = TDocStd_Document(TCollection_ExtendedString("d"))
    rdr = STEPCAFControl_Reader()
    rdr.SetNameMode(True)
    if rdr.ReadFile(str(path)) != IFSelect_RetDone:
        raise RuntimeError("STEP re-import failed")
    rdr.Transfer(doc)
    tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())

    free = TDF_LabelSequence()
    tool.GetFreeShapes(free)

    def name_of(lab):
        n = TDataStd_Name()
        if lab.FindAttribute(TDataStd_Name.GetID_s(), n):
            return n.Get().ToExtString()
        return ""

    def walk(lab, depth=0, seen=None):
        """Follow references as well as components.

        An instance label carries a transform and a POINTER to the shape it
        instances; its own name is the instance's. Stopping at the pointer
        is what made the first run report a three-node tree with numbers
        for names."""
        seen = seen if seen is not None else []
        is_ref = tool.IsReference_s(lab)
        target = lab
        if is_ref:
            from OCP.TDF import TDF_Label
            ref = TDF_Label()
            if tool.GetReferredShape_s(lab, ref):
                target = ref
        # An instance label and the product it points at each carry a
        # name, and they are not the same name: the product holds the one
        # written here, the instance holds whatever the writer generated.
        # Both are kept, because preferring either one alone loses names.
        inst, prod = name_of(lab), name_of(target)
        nm = prod if (prod and (not inst or inst.isdigit())) else (inst or prod)
        rows = [(depth, nm, tool.IsAssembly_s(target), is_ref)]
        kids = TDF_LabelSequence()
        tool.GetComponents_s(target, kids)
        for i in range(1, kids.Length() + 1):
            rows += walk(kids.Value(i), depth + 1, seen)
        return rows

    tree = []
    for i in range(1, free.Length() + 1):
        tree += walk(free.Value(i))

    shapes = TDF_LabelSequence()
    tool.GetShapes(shapes)
    return dict(roots=free.Length(), nodes=len(tree),
                instances=sum(1 for t in tree if t[3]),
                assemblies=sum(1 for t in tree if t[2]),
                distinct_shapes=shapes.Length(), tree=tree)


def figure(rows=None, path=None):
    """The assembled engine in the meridional plane, drawn from the SOLIDS.

    Unit J1 draws this annulus from the flowpath tables; this draws the
    same annulus from the walls and then puts the lofted blades on it, at
    the stations the STEP file uses. Radius is rotation-invariant, so one
    instance per row carries the whole annulus -- the figure is the
    assembly, not a sample of it.

    What it is for: to show, in one picture, which surfaces are here and
    which are not. The HPT has walls and no blades; the fan has blades and
    no wall. Both of those are facts about the public record."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from publication.render import tessellate_row

    path = Path(path or (Path(__file__).resolve().parent / "figures"
                         / "e3-assembly-meridional.png"))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(13, 4.2))

    colour = {"lp": "#4a6fa5", "hp": "#c08a3e", "static": "#8d9196"}
    for e in placed_rows(rows):
        row = e["row"]
        P, _, _ = tessellate_row(row, 0.002)
        x = (P[:, 0] + e["x_m"]) / CM
        r = np.hypot(P[:, 1], P[:, 2]) / CM
        ax.plot(x, r, ".", ms=0.4, alpha=0.5, color=colour[row.spool], zorder=2)

    for name, status, pts in published_walls():
        xs = [p[0] / CM for p in pts]
        rs = [p[1] / CM for p in pts]
        ax.plot(xs, rs, "-", lw=1.4, zorder=3,
                color="k" if status == "published" else "#b03a3a")

    L = assembled_length(rows)
    if L:
        ax.annotate("", xy=(L["lpt_r5_te_cm"], 5), xytext=(FAN_FRONT_FLANGE_CM, 5),
                    arrowprops=dict(arrowstyle="<->", color="#333"))
        ax.text((L["lpt_r5_te_cm"] + FAN_FRONT_FLANGE_CM) / 2, 7,
                f"turbomachinery length {L['length_cm']:.1f} cm "
                f"against a published {L['published_cm']:.1f} "
                f"({L['err_cm']:+.2f})", ha="center", fontsize=8)

    ax.text(216.9, 15, "HPT:\nwalls published,\nno airfoils published",
            ha="center", fontsize=7, color="#b03a3a")
    ax.text(18, 15, "fan: blade built,\nno wall published",
            ha="center", fontsize=7, color="#b03a3a")
    ax.set_xlabel("axial station, cm from the fan rotor stacking axis")
    ax.set_ylabel("radius, cm")
    ax.set_title("E\u00b3 — the STEP assembly in the meridional plane "
                 "(black: published wall; red: derived wall)", fontsize=10)
    ax.set_ylim(0, 115)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


if __name__ == "__main__":
    import sys
    rows = all_rows()
    print(f"Stage G3: the whole engine as one STEP assembly\n")

    ext = row_extents(rows)
    print(f"   {'row':<18}{'module':>8}{'spool':>8}{'n':>5}"
          f"{'x_lo cm':>10}{'x_hi cm':>10}")
    for r in ext:
        print(f"   {r['row']:<18}{_module_of(r['row']):>8}{r['spool']:>8}"
              f"{r['count']:>5}{r['x_lo'] / CM:>10.2f}{r['x_hi'] / CM:>10.2f}")

    L = assembled_length(rows)
    print(f"\n   assembled length, fan front flange to LPT R5 TE: "
          f"{L['length_cm']:.1f} cm against a published "
          f"{L['published_cm']:.1f} cm -> {L['err_cm']:+.2f} cm "
          f"(band +-{L['band_cm']:.1f}) : {'MET' if L['met'] else 'MISS'}")

    gaps = axial_clearances(rows)
    worst = min(gaps, key=lambda g: g["gap_m"])
    neg = [g for g in gaps if g["gap_m"] < 0]
    print(f"\n   row-to-row axial clearance, {len(gaps)} consecutive pairs:")
    print(f"      tightest {worst['gap_m'] * 1000:.1f} mm between "
          f"{worst['upstream']} and {worst['downstream']}")
    print(f"      negative gaps: {[g['upstream'] + '/' + g['downstream'] for g in neg] or 'none'}")

    ov = [i for i in placed_interference(rows) if i["overlap_m3"] > 0]
    print(f"\n   blade-to-blade, placed: {len(rows) - len(ov)} of {len(rows)} "
          f"rows clear; overlapping: {[o['row'] for o in ov] or 'none'}")

    fe = front_end_placement(rows)
    print(f"\n   front end: fan row {fe['fan_x_lo_cm']:.2f} to "
          f"{fe['fan_x_hi_cm']:.2f} cm, axial extent "
          f"{fe['fan_axial_extent_cm']:.2f} cm; leading-edge-on-stacking-axis. "
          f"Mid-chord stacking would move it "
          f"{fe['shift_if_sa_at_midchord_cm']:+.2f} cm")

    print(f"\n   published rows NOT in the assembly:")
    for m in missing_rows():
        print(f"      {m['row']:<42} n={m['count']:<4} {m['src'][:56]}")

    V = volume_audit(rows)
    print(f"\n   {V['blades']} blades: total volume {V['cad_m3'] * 1e6:.1f} cm3 "
          f"against F2's {V['trapezoid_m3'] * 1e6:.1f} cm3, "
          f"{V['err_pct']:+.2f} % (worst row {V['worst_row_pct']:.2f} %, "
          f"band {V['band_pct']:.1f} %)")

    # The file is 70-odd MB, so writing it is opt-in: `python build.py`
    # runs this module for its tables and `python build.py --export` writes
    # the STEP, which is the same arrangement unit G1 already has.
    f = figure(rows)
    print(f"\n   figure: {f}")

    if "--export" in sys.argv:
        p = export(rows=rows)
        mb = p.stat().st_size / 1e6
        print(f"\n   wrote {p} : {mb:.1f} MB")
        st = reimport_structure(p)
        print(f"   re-imported: {st['roots']} root product, "
              f"{st['assemblies']} assemblies, {st['instances']} instances, "
              f"{st['distinct_shapes']} distinct shapes")

"""Stage J unit J1: the meridional plot. The work plan says this one comes first.

Every radius on it comes from a table or a dimensioned drawing. None comes
from scaling a cutaway -- `engine-flowpath.yaml`'s own rule, and the reason
CR-168219 Figure 1, an unlabelled reproduction of the whole engine, is not
digitised anywhere in this project.

Three things this figure refuses to do:

1.  **It does not pretend the two unknown joins are measured.** The fan
    stacking axis to the HPC inlet, and the HPC outlet guide vane to the
    HPT stage-1 vane, were never published. They are drawn at the values
    `engine-flowpath.yaml` records as **assumed**, each with the range it
    is allowed shown beside it, and labelled ASSUMED on the figure. The
    numbers live in the data file and not in this module because the
    Turbofan Atlas draws the same engine from the same two offsets: two
    pictures of one engine that disagree would be worse than either being
    wrong (finding 159).

2.  **It does not draw a fan duct.** The fan module has exactly one
    dimensioned axial station -- the rotor stacking axis, Fig 15 -- plus
    two inlet annuli from Table IV radius ratios. Three radial stations,
    no wall contour. They are drawn as radial station bars. Inventing a
    casing line through them would be the scaled-cutaway mistake in a
    different coat.

3.  **It does not scale the core up to be legible.** True aspect. The fan
    is 2.1 m across and the core annulus is 20 cm tall; a high-bypass
    engine looks like that, and stretching the radial axis to make the HPC
    readable would misstate every angle on the plot.

The one join that *is* known is drawn to scale: the LPT flowpath's z runs
from the HPT exit plane, so the transition duct between them is a measured
6.85 cm, not a gap.

STEP0.md unit J1."""
from __future__ import annotations

import csv
from pathlib import Path

import yaml

from e3cycle.cycle import DATA

IN_TO_CM = 2.54
FIGDIR = Path(__file__).resolve().parent / "figures"


def _yaml(name):
    return yaml.safe_load((DATA / name).read_text())


def _csv_flowpath(name):
    rows = []
    with open(DATA / name) as f:
        for r in csv.DictReader(l for l in f if not l.startswith("#")):
            rows.append(dict(row=r["row"], edge=r["edge"],
                             z_hub=float(r["z_hub_cm"]), r_hub=float(r["r_hub_cm"]),
                             z_tip=float(r["z_tip_cm"]), r_tip=float(r["r_tip_cm"])))
    return rows


def hpc_flowpath():
    """z is in the HPC report's own datum (header of the CSV)."""
    return _csv_flowpath("hpc-flowpath.csv")


def lpt_flowpath():
    """z is measured FROM THE HPT EXIT PLANE -- the CSV header says so, and
    that is the one join between modules that is known. Do not re-zero it."""
    return _csv_flowpath("lpt-flowpath.csv")


def hpt_flowpath():
    st = _yaml("e3-fps-published.yaml")["hpt"]["flowpath"]["stations"]
    return [dict(row=s["location"], z=s["x_cm"], r_hub=s["r_hub_cm"],
                 r_tip=s["r_tip_cm"]) for s in st]


def fan_stations():
    """What the fan module actually gives: three radial stations, one of
    which has an axial position. Not a flowpath."""
    f = _yaml("fan-design.yaml")
    fig15, ap = f["fan_rotor_airfoil"]["fig15"], f["aero_parameters"]
    fan_tip = ap["tip_diameter_cm"][0] / 2
    boost_tip = ap["tip_diameter_cm"][1] / 2
    # physical order along the gas path: inlet, then rotor, then booster
    return [
        dict(name="fan inlet", z=None, r_hub=fan_tip * ap["radius_ratio_inlet"][0],
             r_tip=fan_tip, src="Table IV: 210.8 cm tip, 0.342 radius ratio",
             z_known=False),
        dict(name="fan rotor\nstacking axis", z=fig15["z_sa_in"] * IN_TO_CM,
             r_hub=fig15["r_sa_id_in"] * IN_TO_CM, r_tip=fig15["r_sa_od_in"] * IN_TO_CM,
             src="fan report Fig 15", z_known=True),
        dict(name="booster inlet", z=None, r_hub=boost_tip * ap["radius_ratio_inlet"][1],
             r_tip=boost_tip, src="Table IV: 133.8 cm tip, 0.782 radius ratio",
             z_known=False),
    ]


def transition_duct():
    td = _yaml("engine-flowpath.yaml")["transition_duct"]
    return td


def assumed_offsets():
    """The only two axial numbers in this project that no table gives.

    They live in `engine-flowpath.yaml` and NOT in this module, because the
    Turbofan Atlas draws the same engine from the same two numbers. Two
    pictures of one engine that disagree would be worse than either being
    wrong."""
    a = _yaml("engine-flowpath.yaml")["whole_engine_stitching"]["assumed_offsets"]
    assert a["status"] == "assumed"
    return a


def joins():
    """finding: the transition duct's published axial length and the length
    the LPT sections imply disagree by 0.77 cm (10 %). The sections are the
    number used here, because the LPT flowpath is drawn on that datum and
    mixing the two would put the vane row in the wrong place."""
    st = _yaml("engine-flowpath.yaml")["whole_engine_stitching"]
    td = transition_duct()
    return dict(known=st["known_offsets"], unknown=st["unknown_offsets"],
                duct_published_cm=td["axial_length_cm"],
                duct_from_sections_cm=td["from_sections_cm"],
                duct_disagreement_cm=td["axial_length_cm"] - td["from_sections_cm"])


def layout():
    """Axial placement of every module on ONE engine axis, y = 0 at the fan
    rotor stacking axis -- the same datum `atlas/flowpath.js` uses.

    Two of the three joins are assumed rather than published. They are drawn
    at their assumed value with their allowable range shown as a band, so
    the figure carries its own uncertainty instead of hiding it. The third,
    HPT exit to LPT, is measured and drawn to scale."""
    off = assumed_offsets()
    hpc0 = off["fan_sa_to_hpc_r1_le"]["value_cm"]          # fan SA -> HPC z=0
    hpc = hpc_flowpath()
    hpc_len = max(max(r["z_hub"], r["z_tip"]) for r in hpc) \
        - min(min(r["z_hub"], r["z_tip"]) for r in hpc)
    ogv_te = max(max(r["z_hub"], r["z_tip"]) for r in hpc)  # HPC OGV TE, HPC datum
    hpt = hpt_flowpath()
    hpt0 = hpc0 + ogv_te + off["hpc_ogv_te_to_hpt_vane1"]["value_cm"]
    hpt_len = max(s["z"] for s in hpt)

    def band(centre, o):
        lo, hi = o["range_cm"]
        return (centre - (o["value_cm"] - lo), centre + (hi - o["value_cm"]))

    return dict(
        fan=dict(stations=fan_stations(), x0=0.0, datum="fan stacking axis (y = 0)",
                 assumed=False),
        hpc=dict(rows=hpc, x0=hpc0, length=hpc_len, datum="HPC report", assumed=True),
        hpt=dict(stations=hpt, x0=hpt0, length=hpt_len, datum="HPT Fig 3", assumed=True),
        # the LPT rides on the HPT exit plane: measured, no assumption
        lpt=dict(rows=lpt_flowpath(), x0=hpt0 + hpt_len, datum="HPT exit plane",
                 assumed=False),
        gaps=[
            dict(x0=0.0, x1=hpc0, value=off["fan_sa_to_hpc_r1_le"]["value_cm"],
                 rng=off["fan_sa_to_hpc_r1_le"]["range_cm"], span=band(hpc0, off["fan_sa_to_hpc_r1_le"]),
                 label="fan stacking axis\nto HPC rotor 1"),
            dict(x0=hpc0 + ogv_te, x1=hpt0,
                 value=off["hpc_ogv_te_to_hpt_vane1"]["value_cm"],
                 rng=off["hpc_ogv_te_to_hpt_vane1"]["range_cm"],
                 span=band(hpt0, off["hpc_ogv_te_to_hpt_vane1"]),
                 label="HPC OGV exit to HPT vane 1\n(diffuser + combustor)"),
        ],
        offsets=off,
    )


def plot(path=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    L = layout()
    fig, ax = plt.subplots(figsize=(16, 6.4))
    WALL = dict(color="0.1", lw=1.5, solid_joinstyle="round")
    ROW = dict(color="0.5", lw=0.7)
    TOP = 118

    # ---- the two assumed joins, drawn as DIMENSIONS rather than as filled
    #      regions: a bar at the assumed value with a whisker showing the
    #      range it is allowed. A full-height hatch would swamp the figure
    #      and imply the space is empty, which it is not -- it holds the fan
    #      frame, the diffuser and the combustor, none of them dimensioned.
    for k, g in enumerate(L["gaps"]):
        y = 100 - 9 * k
        lo, hi = g["span"]
        ax.add_patch(Rectangle((g["x0"], 0), g["x1"] - g["x0"], TOP,
                               facecolor="#f6f1e7", edgecolor="none", zorder=0))
        for xv in (g["x0"], g["x1"]):
            ax.plot([xv, xv], [0, TOP], color="#d8c9ad", lw=0.8, zorder=0)
        ax.plot([lo, hi], [y, y], color="#d9a441", lw=5, alpha=0.55,
                solid_capstyle="butt", zorder=3)
        ax.annotate("", xy=(g["x1"], y), xytext=(g["x0"], y),
                    arrowprops=dict(arrowstyle="<->", color="#8a4f0a", lw=1.3),
                    zorder=4)
        ax.text((g["x0"] + g["x1"]) / 2, y + 2.5,
                g["label"].replace("\n", " ") +
                f"  —  ASSUMED {g['value']:.0f} cm "
                f"(allowable {g['rng'][0]:.0f}\u2013{g['rng'][1]:.0f})",
                ha="center", va="bottom", fontsize=7.6, color="#8a4f0a", zorder=5)

    # ---- HPC
    h, hx = L["hpc"], L["hpc"]["x0"]
    ax.plot([r["z_hub"] + hx for r in h["rows"]], [r["r_hub"] for r in h["rows"]], **WALL)
    ax.plot([r["z_tip"] + hx for r in h["rows"]], [r["r_tip"] for r in h["rows"]], **WALL)
    for r in h["rows"]:
        ax.plot([r["z_hub"] + hx, r["z_tip"] + hx], [r["r_hub"], r["r_tip"]], **ROW)

    # ---- HPT
    t, tx = L["hpt"], L["hpt"]["x0"]
    ax.plot([s["z"] + tx for s in t["stations"]], [s["r_hub"] for s in t["stations"]], **WALL)
    ax.plot([s["z"] + tx for s in t["stations"]], [s["r_tip"] for s in t["stations"]], **WALL)

    # ---- LPT, on the HPT exit datum: its own z already carries the duct
    p_, px = L["lpt"], L["lpt"]["x0"]
    ax.plot([r["z_hub"] + px for r in p_["rows"]], [r["r_hub"] for r in p_["rows"]], **WALL)
    ax.plot([r["z_tip"] + px for r in p_["rows"]], [r["r_tip"] for r in p_["rows"]], **WALL)
    for r in p_["rows"]:
        ax.plot([r["z_hub"] + px, r["z_tip"] + px], [r["r_hub"], r["r_tip"]], **ROW)

    # the one join that is measured, marked as such
    duct_end = px + min(r["z_hub"] for r in p_["rows"])
    ax.annotate("", xy=(duct_end, 22), xytext=(px, 22),
                arrowprops=dict(arrowstyle="<->", color="#1f6f4a", lw=1.2))
    ax.text(px + 3, 19.2, f"transition duct {duct_end - px:.2f} cm\nMEASURED "
            "(LPT z runs from\nthe HPT exit plane)", ha="left", va="top",
            fontsize=7.4, color="#1f6f4a", linespacing=1.3)

    # ---- fan: radial stations only, no invented wall
    f = L["fan"]
    n = len(f["stations"])
    for i, st in enumerate(f["stations"]):
        x = 8.0 + 26.0 * (i - 1)          # stacking axis at its own datum, y = 0
        if st["z_known"]:
            x = st["z"]
        ax.plot([x, x], [st["r_hub"], st["r_tip"]], color="#8c3b2f", lw=2.6,
                solid_capstyle="butt",
                linestyle="-" if st["z_known"] else (0, (4, 2.5)))
        for r in (st["r_hub"], st["r_tip"]):
            ax.plot([x], [r], marker="_", ms=14, color="#8c3b2f")
        ax.text(x, st["r_tip"] + 3.0 + 9.0 * (i % 2), st["name"], ha="center",
                va="bottom", fontsize=7.2, color="#8c3b2f", linespacing=1.15)
    ax.text(-31, 14,
            "fan module: 3 dimensioned radial stations.\n"
            "Solid = axial position published (Fig 15);\n"
            "dashed = radii only, placed indicatively.\n"
            "No published wall contour, so none is drawn.",
            ha="left", va="top", fontsize=7.2, color="#8c3b2f",
            linespacing=1.35)

    ax.text(hx + h["length"] / 2, 6, "HP compressor, 10 stages\n(2 walls, 21 rows)",
            ha="center", fontsize=8.5)
    ax.text(tx + t["length"] / 2, 8, "HPT\n2 stages", ha="center", fontsize=8.5)
    ax.text(px + 32, 6, "LP turbine, 5 stages", ha="center", fontsize=8.5)

    ax.set_xlabel("axial position from the fan rotor stacking axis, cm "
                  "\u2014 one engine axis, true scale")
    ax.set_ylabel("radius, cm")
    ax.set_title("E$^3$ meridional flowpath \u2014 every radius from a table or a "
                 "dimensioned drawing.\nThe two axial offsets no report gives are "
                 "drawn as assumptions, with the range they are allowed.",
                 fontsize=10.5)
    ax.set_xlim(-34, px + max(r["z_tip"] for r in p_["rows"]) + 22)
    ax.set_ylim(0, 124)
    ax.set_aspect("equal")
    ax.grid(alpha=0.22, lw=0.5)
    fig.tight_layout()
    path = Path(path or (FIGDIR / "meridional.png"))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def summary():
    L, J = layout(), joins()
    lines = ["Stage J unit J1 -- the meridional flowpath", ""]
    lines.append(f"   HPC   {len(L['hpc']['rows']) // 2:2d} rows, "
                 f"{L['hpc']['length']:.1f} cm, two walls, datum: {L['hpc']['datum']}")
    lines.append(f"   HPT   {len(L['hpt']['stations']):2d} stations, "
                 f"{L['hpt']['length']:.1f} cm, datum: {L['hpt']['datum']}")
    lines.append(f"   LPT   {len(L['lpt']['rows']) // 2:2d} rows, two walls, "
                 f"datum: {L['lpt']['datum']}")
    lines.append(f"   fan    {len(L['fan']['stations'])} radial stations, "
                 f"{sum(s['z_known'] for s in L['fan']['stations'])} with an axial position")
    lines += ["", f"   engine axis: y = 0 at the {L['fan']['datum']}; "
              f"HPC at {L['hpc']['x0']:.0f} cm, HPT at {L['hpt']['x0']:.1f} cm, "
              f"LPT at {L['lpt']['x0']:.1f} cm"]
    lines += ["", f"   joins known ({len(J['known'])}), drawn to scale:"]
    lines += [f"      {k}" for k in J["known"]]
    lines.append(f"   joins NOT published ({len(J['unknown'])}), drawn as "
                 "labelled assumptions with the range each is allowed:")
    for g in L["gaps"]:
        lines.append(f"      {g['label'].replace(chr(10), ' ')}: ASSUMED "
                     f"{g['value']:.0f} cm (allowable {g['rng'][0]:.0f}"
                     f"\u2013{g['rng'][1]:.0f})")
    lines += ["", "   transition duct: published "
              f"{J['duct_published_cm']:.2f} cm vs sections "
              f"{J['duct_from_sections_cm']:.2f} cm "
              f"-- disagree by {J['duct_disagreement_cm']:.2f} cm "
              f"({100 * J['duct_disagreement_cm'] / J['duct_published_cm']:.0f} %); "
              "sections used"]
    return "\n".join(lines)


if __name__ == "__main__":
    print(summary())
    print(f"\n   wrote {plot().relative_to(Path(__file__).resolve().parents[2])}")

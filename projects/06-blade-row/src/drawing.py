"""Dimensioned general arrangement drawing, in the style of project 04's
`drawing.py` — A4 landscape, millimetres, arrowhead dimension lines, a
title block. Not a shared import: each project in this portfolio stays
self-contained (see e.g. project 08's atmosphere.py), so this reimplements
the same visual language rather than importing project 04's module across
a project boundary.

No OpenCASCADE dependency — everything drawn here comes from
velocity_triangles.py and blade_section.py directly, matching
plotting.py's own "no pyOCC" convention, not from the built solid. The
meridional view's blade envelope is therefore the analytic axial chord
projection (chord * cos(stagger) at hub and tip), not the exact
built-solid extent annulus.axial_extent measures (which needs pyOCC and
accounts for thickness too) — a legitimate GA-level simplification, the
same kind project 04's own front view already makes.

A blade twists with radius, and no single 2D view shows that the way a
wing's planform shows washout — so unlike project 04's drawing, this one
carries a blade-angle SCHEDULE table (hub/mean/tip stagger, camber,
chord, solidity) in the title-block area, the standard way real
turbomachinery drawings handle a spanwise-varying blade angle a section
view alone can't.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Arc, Polygon, Rectangle  # noqa: E402

from .blade import BladeRow  # noqa: E402
from .blade_section import CircularArcSection  # noqa: E402

SHEET_W, SHEET_H = 297.0, 210.0
MARGIN = 10.0
TITLE_W, TITLE_H = 108.0, 46.0

INK = "#111111"
DIM_COLOR = "#333333"
THIN, MEDIUM, THICK = 0.5, 0.9, 1.4

HEAD_L, HEAD_W = 2.2, 0.7


def _sheet():
    fig, ax = plt.subplots(figsize=(SHEET_W / 25.4, SHEET_H / 25.4), dpi=200)
    fig.subplots_adjust(0, 0, 1, 1)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, SHEET_W)
    ax.set_ylim(0, SHEET_H)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.add_patch(Rectangle((MARGIN, MARGIN), SHEET_W - 2 * MARGIN,
                           SHEET_H - 2 * MARGIN, fill=False, edgecolor=INK,
                           lw=THICK))
    return fig, ax


def _head(ax, tip, ux, uy):
    bx, by = tip[0] - ux * HEAD_L, tip[1] - uy * HEAD_L
    px, py = -uy * HEAD_W / 2.0, ux * HEAD_W / 2.0
    ax.add_patch(Polygon([tip, (bx + px, by + py), (bx - px, by - py)],
                         closed=True, facecolor=DIM_COLOR, edgecolor="none",
                         zorder=6))


def _dim_linear(ax, p1, p2, dim_pos, text, vertical=False, text_side=1):
    gap, over = 1.0, 1.8
    if vertical:
        x = dim_pos
        for p in (p1, p2):
            d = 1.0 if x > p[0] else -1.0
            ax.plot([p[0] + d * gap, x + d * over], [p[1], p[1]],
                    color=DIM_COLOR, lw=THIN, zorder=4)
        lo, hi = sorted((p1[1], p2[1]))
        ax.plot([x, x], [lo, hi], color=DIM_COLOR, lw=THIN, zorder=4)
        _head(ax, (x, lo), 0.0, -1.0)
        _head(ax, (x, hi), 0.0, 1.0)
        ax.text(x + text_side * 1.5, (lo + hi) / 2.0, text, rotation=90,
                ha="center", va="center", fontsize=6.2, color=INK, zorder=7)
    else:
        y = dim_pos
        for p in (p1, p2):
            d = 1.0 if y > p[1] else -1.0
            ax.plot([p[0], p[0]], [p[1] + d * gap, y + d * over],
                    color=DIM_COLOR, lw=THIN, zorder=4)
        lo, hi = sorted((p1[0], p2[0]))
        ax.plot([lo, hi], [y, y], color=DIM_COLOR, lw=THIN, zorder=4)
        _head(ax, (lo, y), -1.0, 0.0)
        _head(ax, (hi, y), 1.0, 0.0)
        ax.text((lo + hi) / 2.0, y + text_side * 1.5, text, ha="center",
                va="bottom" if text_side > 0 else "top", fontsize=6.2,
                color=INK, zorder=7)


def _dim_angle(ax, vertex, start_deg, end_deg, radius, text, label_offset=5.0):
    ax.add_patch(Arc(vertex, 2 * radius, 2 * radius, angle=0,
                     theta1=min(start_deg, end_deg),
                     theta2=max(start_deg, end_deg),
                     color=DIM_COLOR, lw=THIN, zorder=4))
    mid = math.radians((start_deg + end_deg) / 2.0)
    ax.text(vertex[0] + (radius + label_offset) * math.cos(mid),
            vertex[1] + (radius + label_offset) * math.sin(mid), text,
            ha="center", va="center", fontsize=6.2, color=INK, zorder=7)


def _centreline(ax, x, y0, y1):
    ax.plot([x, x], [y0, y1], color=DIM_COLOR, lw=THIN,
            linestyle=(0, (7, 2, 1.5, 2)), zorder=3)


def general_arrangement(row: BladeRow, path=None, scale_denominator: int = 5,
                        drawn_by: str = "V. Venkateshkumar",
                        date: str | None = None, drawing_no: str = "BR-001",
                        row_name: str = "ROTOR"):
    s = 1.0 / scale_denominator
    hub_r, tip_r = row.hub_radius * 1000.0, row.tip_radius * 1000.0
    root_c, tip_c = row.root_chord * 1000.0, row.tip_chord * 1000.0
    stagger_hub = row.design.stagger_angle(row.hub_radius)
    stagger_tip = row.design.stagger_angle(row.tip_radius)

    fig, ax = _sheet()
    cx = SHEET_W / 2.0
    merid_x0 = 60.0   # sheet x of the leading edge, meridional view
    merid_y_hub = 128.0
    merid_y_tip = merid_y_hub + row.span * 1000.0 * s

    # ── Meridional view ─────────────────────────────────────────────────
    #
    # Hub and casing as straight lines (this project's constant-annulus
    # reference stage — see README for the converging-annulus variant this
    # view does not attempt to show), blade envelope as the analytic axial
    # chord projection at hub and tip (chord * cos(stagger)) — see the
    # module docstring for why this is a simplification, not the exact
    # built-solid extent. Hub/tip radii are called out as text (R200 style)
    # rather than dimensioned all the way to the axis: at this scale the
    # centreline sits far below the sheet, and a real drawing would break
    # that empty shaft length rather than draw it to scale — a callout is
    # the simpler way to the same information.
    axial_span = max(root_c * math.cos(stagger_hub), tip_c * math.cos(stagger_tip))
    merid_x1 = merid_x0 + axial_span * s

    ax.plot([merid_x0 - 15, merid_x1 + 15], [merid_y_hub, merid_y_hub],
            color=INK, lw=MEDIUM, zorder=5)
    ax.plot([merid_x0 - 15, merid_x1 + 15], [merid_y_tip, merid_y_tip],
            color=INK, lw=MEDIUM, zorder=5)

    hub_chord_x1 = merid_x0 + root_c * math.cos(stagger_hub) * s
    tip_chord_x1 = merid_x0 + tip_c * math.cos(stagger_tip) * s
    ax.plot([merid_x0, hub_chord_x1], [merid_y_hub, merid_y_hub],
            color=INK, lw=THICK, zorder=6)
    ax.plot([merid_x0, tip_chord_x1], [merid_y_tip, merid_y_tip],
            color=INK, lw=THICK, zorder=6)
    ax.plot([merid_x0, merid_x0], [merid_y_hub, merid_y_tip], color=INK,
            lw=MEDIUM, zorder=5, linestyle=(0, (4, 2)))
    ax.plot([hub_chord_x1, tip_chord_x1], [merid_y_hub, merid_y_tip],
            color=INK, lw=MEDIUM, zorder=5, linestyle=(0, (4, 2)))

    # Radius, not diameter — matching the schedule table and title block,
    # which both quote r rather than 2r; mixing the two on one sheet is
    # the kind of thing a real drafter would flag.
    ax.text(merid_x0 - 18, merid_y_hub, f"HUB R{hub_r:.0f}", fontsize=5.8,
            color=INK, ha="right", va="center", zorder=7)
    ax.text(merid_x0 - 18, merid_y_tip, f"TIP R{tip_r:.0f}", fontsize=5.8,
            color=INK, ha="right", va="center", zorder=7)

    _dim_linear(ax, (merid_x0, merid_y_hub - 10), (hub_chord_x1, merid_y_hub - 10),
                merid_y_hub - 16, f"{root_c:.0f}", text_side=-1)
    _dim_linear(ax, (merid_x0, merid_y_tip + 10), (tip_chord_x1, merid_y_tip + 10),
                merid_y_tip + 15, f"{tip_c:.0f}")

    ax.text(MARGIN + 6, merid_y_tip + 30, "MERIDIONAL VIEW", fontsize=8,
            fontweight="bold", color=INK)
    ax.text(MARGIN + 6, merid_y_tip + 25,
            f"{row.n_blades} BLADES  ·  AXIAL CHORD PROJECTION SHOWN, "
            "NOT BUILT-SOLID EXTENT", fontsize=5.4, color=DIM_COLOR)

    # ── Root section detail (cascade view) ──────────────────────────────
    detail_scale = 2
    ds = 1.0 / detail_scale
    dx, dy = 40.0, 55.0
    section = CircularArcSection(
        camber_angle_deg=math.degrees(row.design.camber_angle(row.hub_radius)),
        thickness=row.thickness,
    )
    upper, lower = section.surfaces()
    loop = upper + list(reversed(lower))

    def transformed(xc, zc):
        x = (xc - 0.25) * root_c
        z = zc * root_c
        xr = x * math.cos(stagger_hub) - z * math.sin(stagger_hub)
        zr = x * math.sin(stagger_hub) + z * math.cos(stagger_hub)
        return dx + xr * ds, dy + zr * ds

    pts = [transformed(xc, zc) for xc, zc in loop]
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=INK, lw=MEDIUM,
            zorder=5)

    chord_x0, chord_y0 = transformed(0.25, 0.0)
    chord_x1, chord_y1 = dx, dy
    ax.plot([chord_x0, dx + 0.75 * root_c * math.cos(stagger_hub) * ds],
            [chord_y0, dy + 0.75 * root_c * math.sin(stagger_hub) * ds],
            color=DIM_COLOR, lw=THIN, linestyle=(0, (7, 2, 1.5, 2)), zorder=3)
    ax.plot([dx - 10, dx + 25], [dy, dy], color=DIM_COLOR, lw=THIN,
            linestyle=(0, (4, 3)), zorder=3)
    _dim_angle(ax, (dx, dy), 0.0, -math.degrees(stagger_hub), 14.0,
               f"{math.degrees(stagger_hub):.1f}°  γ")

    le_x, le_y = transformed(0.0, 0.0)
    te_x, te_y = transformed(1.0, 0.0)
    _dim_linear(ax, (le_x, le_y), (te_x, te_y), dy - 16.0, f"{root_c:.0f}",
                text_side=-1)

    ax.text(dx - 10, dy + 20.0,
            f"SECTION AT HUB (r={hub_r:.0f})   SCALE 1:{detail_scale}",
            fontsize=6.2, fontweight="bold", color=INK)

    # ── Blade-angle schedule ────────────────────────────────────────────
    #
    # No single 2D view shows spanwise twist — a schedule table is the
    # standard way a real turbomachinery drawing carries it.
    table_x, table_y = 190.0, 150.0
    ax.text(table_x, table_y + 6, "BLADE ANGLE SCHEDULE", fontsize=7,
            fontweight="bold", color=INK)
    headers = f"{'STATION':<8}{'r,mm':>8}{'STAGGER':>10}{'CAMBER':>9}{'SOLIDITY':>10}"
    ax.text(table_x, table_y, headers, fontsize=5.6, family="monospace",
            color=INK)
    rows = [
        ("HUB", row.hub_radius), ("MEAN", row.mean_radius), ("TIP", row.tip_radius),
    ]
    for i, (label, r) in enumerate(rows):
        line = (f"{label:<8}{r*1000:>8.0f}"
                f"{math.degrees(row.design.stagger_angle(r)):>9.1f}°"
                f"{math.degrees(row.design.camber_angle(r)):>8.1f}°"
                f"{row.solidity_at(r):>10.3f}")
        ax.text(table_x, table_y - 5.0 * (i + 1), line, fontsize=5.6,
                family="monospace", color=INK)

    # ── Title block ──────────────────────────────────────────────────────
    tx, ty = SHEET_W - MARGIN - TITLE_W, MARGIN
    ax.add_patch(Rectangle((tx, ty), TITLE_W, TITLE_H, facecolor="white",
                           edgecolor=INK, lw=MEDIUM, zorder=8))
    for frac in (0.26, 0.55):
        ax.plot([tx, tx + TITLE_W], [ty + TITLE_H * frac, ty + TITLE_H * frac],
                color=INK, lw=THIN, zorder=9)
    ax.plot([tx + TITLE_W * 0.52] * 2, [ty + TITLE_H * 0.26, ty + TITLE_H * 0.55],
            color=INK, lw=THIN, zorder=9)

    ax.text(tx + 3, ty + TITLE_H - 6.5, "AXIAL COMPRESSOR BLADE ROW",
            fontsize=8.5, fontweight="bold", color=INK, zorder=10)
    ax.text(tx + 3, ty + TITLE_H - 11.5, f"GENERAL ARRANGEMENT — {row_name}",
            fontsize=6.2, color=INK, zorder=10)

    left = [f"BLADES   {row.n_blades}", f"SPAN     {row.span*1000:.0f} mm",
            f"THICK    t/c {row.thickness:.2f}"]
    right = [f"HUB/TIP  {hub_r:.0f}/{tip_r:.0f}", f"SCALE    1:{scale_denominator}",
             f"MEAN R   {row.mean_radius*1000:.0f} mm"]
    for i, line in enumerate(left):
        ax.text(tx + 3, ty + TITLE_H * 0.48 - i * 4.0, line, fontsize=5.6,
                color=INK, family="monospace", zorder=10)
    for i, line in enumerate(right):
        ax.text(tx + TITLE_W * 0.545, ty + TITLE_H * 0.48 - i * 4.0, line,
                fontsize=5.6, color=INK, family="monospace", zorder=10)

    footer = f"DRAWN {drawn_by}    DWG {drawing_no}    UNITS mm"
    if date:
        footer += f"    {date}"
    ax.text(tx + 3, ty + 3.5, footer, fontsize=5.2, color=INK,
            family="monospace", zorder=10)

    ax.text(MARGIN + 5, SHEET_H - MARGIN - 6,
            "THIRD ANGLE PROJECTION   ·   ALL DIMENSIONS IN MILLIMETRES",
            fontsize=5.8, color=DIM_COLOR)

    if path is not None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, facecolor="white", dpi=200)
    return fig

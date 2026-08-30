"""Dimensioned general arrangement drawing.

Generated from the same `Wing` object that builds the solid, so the drawing
cannot document a different wing from the one exported — the usual failure of a
drawing produced once by hand and then left behind by the model.

Deterministic: no timestamp unless one is passed, so regenerating an unchanged
design produces an identical file rather than a noisy diff.

A4 landscape, millimetres, plan above front view.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Arc, Polygon, Rectangle  # noqa: E402

from .wing import Wing  # noqa: E402

SHEET_W, SHEET_H = 297.0, 210.0
MARGIN = 10.0
TITLE_W, TITLE_H = 108.0, 40.0

INK = "#111111"
DIM_COLOR = "#333333"
THIN, MEDIUM, THICK = 0.5, 0.9, 1.4

# Arrowheads are polygons in sheet coordinates. Matplotlib sizes its own arrow
# heads in points scaled by the font size, which on an A4 sheet at 200 dpi drew
# heads about 10 mm long — bigger than most features they pointed at.
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
    """Dimension between two points, its line placed at absolute `dim_pos`.

    Absolute rather than an offset from the feature: on a drawing a dimension
    goes where there is room, not a fixed distance from geometry that may sit
    anywhere on the sheet.
    """
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


def section_label(wing: Wing) -> str:
    """The NACA designation, rebuilt from the section's parameters."""
    return (f"NACA {int(wing.section.max_camber*100)}"
            f"{int(wing.section.camber_position*10)}"
            f"{int(wing.section.thickness*100):02d}")


def general_arrangement(wing: Wing, path=None, scale_denominator: int = 50,
                        drawn_by: str = "V. Venkateshkumar",
                        date: str | None = None, drawing_no: str = "PW-001"):
    s = 1.0 / scale_denominator
    semi = (wing.span / 2.0) * 1000.0
    root_c, tip_c = wing.root_chord * 1000.0, wing.tip_chord * 1000.0
    sweep = math.tan(math.radians(wing.sweep_deg))
    dihedral = math.tan(math.radians(wing.dihedral_deg))

    fig, ax = _sheet()
    cx = SHEET_W / 2.0
    plan_y = 184.0          # sheet y of the root leading edge
    front_y = 86.0          # sheet y of the front-view baseline

    def plan(y_model):
        frac = abs(y_model) / semi
        chord = root_c + (tip_c - root_c) * frac
        quarter = 0.25 * root_c + abs(y_model) * sweep
        return ((cx + y_model * s, plan_y - (quarter - 0.25 * chord) * s),
                (cx + y_model * s, plan_y - (quarter + 0.75 * chord) * s))

    # ── Plan view ───────────────────────────────────────────────────────────
    stations = [(-1 + 2 * i / 120) * semi for i in range(121)]
    le = [plan(y)[0] for y in stations]
    te = [plan(y)[1] for y in stations]
    for pts in (le, te):
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=INK,
                lw=MEDIUM, zorder=5)
    for sign in (-1, 1):
        a, b = plan(sign * semi)
        ax.plot([a[0], b[0]], [a[1], b[1]], color=INK, lw=MEDIUM, zorder=5)

    qc = [(cx + y * s, plan_y - (0.25 * root_c + abs(y) * sweep) * s)
          for y in stations]
    ax.plot([p[0] for p in qc], [p[1] for p in qc], color=DIM_COLOR, lw=THIN,
            linestyle=(0, (6, 2)), zorder=4)

    root_le, root_te = plan(0.0)
    tip_le, tip_te = plan(semi)
    left_le, _ = plan(-semi)
    _centreline(ax, cx, root_te[1] - 6, root_le[1] + 6)

    y_mac = wing.mac_spanwise_station * 1000.0
    mac_le, mac_te = plan(y_mac)
    ax.plot([mac_le[0], mac_te[0]], [mac_le[1], mac_te[1]], color=INK,
            lw=THICK, zorder=6)
    ax.text(mac_te[0] + 2.0, mac_te[1] - 1.0,
            f"MAC {wing.mac*1000:.0f}\nat y {y_mac:.0f}", fontsize=5.8,
            color=INK, va="top", ha="left", zorder=7)

    _dim_linear(ax, left_le, tip_le, 112.0, f"{wing.span*1000:.0f}",
                text_side=-1)
    _dim_linear(ax, root_le, root_te, cx - 7.0, f"{root_c:.0f}", vertical=True,
                text_side=-1)
    _dim_linear(ax, tip_le, tip_te, tip_le[0] + 9.0, f"{tip_c:.0f}",
                vertical=True)

    qc_root = (cx, plan_y - 0.25 * root_c * s)
    ax.plot([qc_root[0], qc_root[0] + 30], [qc_root[1], qc_root[1]],
            color=DIM_COLOR, lw=THIN, linestyle=(0, (4, 3)), zorder=3)
    _dim_angle(ax, qc_root, -wing.sweep_deg, 0.0, 24.0,
               f"{wing.sweep_deg:.0f}°  Λ c/4")

    ax.text(MARGIN + 6, plan_y - 14, "PLAN", fontsize=8, fontweight="bold",
            color=INK)

    # ── Front view ──────────────────────────────────────────────────────────
    tip_rise = semi * dihedral
    for sign in (-1, 1):
        ax.plot([cx, cx + sign * semi * s], [front_y, front_y + tip_rise * s],
                color=INK, lw=MEDIUM, zorder=5)
    ax.plot([cx - semi * s - 6, cx + semi * s + 6], [front_y, front_y],
            color=DIM_COLOR, lw=THIN, linestyle=(0, (6, 2)), zorder=3)
    _centreline(ax, cx, front_y - 8, front_y + tip_rise * s + 8)
    _dim_angle(ax, (cx, front_y), 0.0, wing.dihedral_deg, 30.0,
               f"{wing.dihedral_deg:.0f}°  Γ")
    _dim_linear(ax, (cx + semi * s, front_y),
                (cx + semi * s, front_y + tip_rise * s),
                cx + semi * s + 9.0, f"{tip_rise:.0f}", vertical=True)
    ax.text(MARGIN + 6, front_y + 10, "FRONT", fontsize=8, fontweight="bold",
            color=INK)

    # ── Root section detail ─────────────────────────────────────────────────
    #
    # The sheet has an empty quadrant and the wing is 51:1 span to thickness,
    # so neither view above shows the aerofoil at all. At 1:20 it is legible,
    # and a detail at its own scale is normal practice for exactly this reason.
    detail_scale = 20
    ds = 1.0 / detail_scale
    dx, dy = 38.0, 44.0
    upper, lower = wing.section.surfaces()
    loop = upper + list(reversed(lower))
    ax.plot([dx + xc * root_c * ds for xc, _ in loop],
            [dy + zc * root_c * ds for _, zc in loop],
            color=INK, lw=MEDIUM, zorder=5)
    ax.plot([dx, dx + root_c * ds], [dy, dy], color=DIM_COLOR, lw=THIN,
            linestyle=(0, (7, 2, 1.5, 2)), zorder=3)

    x_t, t_c = wing.section.max_thickness_station()
    z_hi = max(z for x, z in upper if abs(x - x_t) < 0.02)
    z_lo = min(z for x, z in lower if abs(x - x_t) < 0.02)
    _dim_linear(ax, (dx + x_t * root_c * ds, dy + z_hi * root_c * ds),
                (dx + x_t * root_c * ds, dy + z_lo * root_c * ds),
                dx + root_c * ds + 8.0, f"{t_c * root_c:.0f}", vertical=True)
    _dim_linear(ax, (dx, dy), (dx + root_c * ds, dy), dy - 11.0,
                f"{root_c:.0f}", text_side=-1)

    ax.text(dx, dy + 14.0,
            f"SECTION AT ROOT   {section_label(wing)}   SCALE 1:{detail_scale}",
            fontsize=6.2, fontweight="bold", color=INK)

    # ── Title block ─────────────────────────────────────────────────────────
    tx, ty = SHEET_W - MARGIN - TITLE_W, MARGIN
    ax.add_patch(Rectangle((tx, ty), TITLE_W, TITLE_H, facecolor="white",
                           edgecolor=INK, lw=MEDIUM, zorder=8))
    for frac in (0.30, 0.62):
        ax.plot([tx, tx + TITLE_W], [ty + TITLE_H * frac, ty + TITLE_H * frac],
                color=INK, lw=THIN, zorder=9)
    ax.plot([tx + TITLE_W * 0.52] * 2, [ty + TITLE_H * 0.30, ty + TITLE_H * 0.62],
            color=INK, lw=THIN, zorder=9)

    ax.text(tx + 3, ty + TITLE_H - 6.5, "PARAMETRIC WING", fontsize=9,
            fontweight="bold", color=INK, zorder=10)
    ax.text(tx + 3, ty + TITLE_H - 11.5, "GENERAL ARRANGEMENT", fontsize=6.2,
            color=INK, zorder=10)

    left = [f"SECTION  {section_label(wing)}", f"AREA     {wing.area:.3f} m2",
            f"ASPECT   {wing.aspect_ratio:.3f}"]
    right = [f"TAPER    {wing.taper_ratio:.2f}",
             f"WASHOUT  {wing.twist_deg:.0f} deg tip",
             f"SCALE    1:{scale_denominator}"]
    for i, line in enumerate(left):
        ax.text(tx + 3, ty + TITLE_H * 0.55 - i * 4.0, line, fontsize=5.6,
                color=INK, family="monospace", zorder=10)
    for i, line in enumerate(right):
        ax.text(tx + TITLE_W * 0.545, ty + TITLE_H * 0.55 - i * 4.0, line,
                fontsize=5.6, color=INK, family="monospace", zorder=10)

    footer = f"DRAWN {drawn_by}    DWG {drawing_no}    UNITS mm"
    if date:
        footer += f"    {date}"
    ax.text(tx + 3, ty + 3.5, footer, fontsize=5.4, color=INK,
            family="monospace", zorder=10)

    ax.text(MARGIN + 5, SHEET_H - MARGIN - 6,
            "THIRD ANGLE PROJECTION   ·   ALL DIMENSIONS IN MILLIMETRES",
            fontsize=5.8, color=DIM_COLOR)

    if path is not None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, facecolor="white", dpi=200)
    return fig

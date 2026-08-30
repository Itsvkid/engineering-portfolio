"""Figures. Matplotlib only — no pyOCC dependency, since everything plotted
here comes from velocity_triangles.py and blade_section.py directly rather
than from the built solid.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .blade import BladeRow

# Site tokens (see the portfolio's app/globals.css :root / [data-theme="light"]
# blocks) so a figure sits flush on the page it's dropped into rather than
# carrying its own unrelated palette.
THEMES = {
    "light": {"surface": "#f2eee6", "ink": "#221e18", "ink_muted": "#6e6558",
              "grid": "#d9d0c0", "hub": "#b23d0e", "tip": "#4f473c"},
    "dark": {"surface": "#1b1815", "ink": "#f1ece4", "ink_muted": "#8c8377",
             "grid": "#39332b", "hub": "#ff6d3b", "tip": "#b8afa2"},
}


def velocity_triangle_figure(row: BladeRow, path) -> Path:
    """Stagger and camber angle against radius — the spanwise twist a
    free-vortex design demands, which is the whole reason this project is
    not just the wing generator with a different loft axis."""
    radii = [row.hub_radius + i * row.span / 200 for i in range(201)]
    stagger = [math.degrees(row.design.stagger_angle(r)) for r in radii]
    camber = [math.degrees(row.design.camber_angle(r)) for r in radii]

    fig, ax1 = plt.subplots(figsize=(6.4, 4.4), dpi=150)
    ax1.plot(radii, stagger, color="#c0392b", label="Stagger angle")
    ax1.set_xlabel("Radius, m")
    ax1.set_ylabel("Stagger angle, deg", color="#c0392b")
    ax1.tick_params(axis="y", labelcolor="#c0392b")

    ax2 = ax1.twinx()
    ax2.plot(radii, camber, color="#2874a6", label="Camber angle")
    ax2.set_ylabel("Camber angle, deg", color="#2874a6")
    ax2.tick_params(axis="y", labelcolor="#2874a6")

    ax1.axvline(row.mean_radius, color="#888888", linestyle="--", linewidth=1)
    ax1.set_title("Free-vortex spanwise twist")
    fig.tight_layout()

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path


def deviation_comparison_figure(row: BladeRow, corrected_row: BladeRow, path,
                                 theme: str = "light") -> Path:
    """Blade camber angle against radius, tangent-mean rule (row.design)
    against Carter's-rule-corrected (corrected_row.design) — the gap
    between the two curves *is* the deviation angle, drawn rather than
    left as a single number. row and corrected_row must share the same
    span (same hub/tip radius) — this plots two designs over one blade
    geometry, not two blades.
    """
    t = THEMES[theme]
    radii = [row.hub_radius + i * row.span / 200 for i in range(201)]
    base_camber = [math.degrees(row.design.camber_angle(r)) for r in radii]
    corrected_camber = [math.degrees(corrected_row.design.camber_angle(r)) for r in radii]

    fig, ax = plt.subplots(figsize=(6.4, 4.4), dpi=150)
    fig.patch.set_facecolor(t["surface"])
    ax.set_facecolor(t["surface"])

    ax.plot(radii, base_camber, "--", color=t["tip"], linewidth=1.8,
            label="Tangent-mean rule (no deviation)", zorder=2)
    ax.plot(radii, corrected_camber, color=t["hub"], linewidth=2.2,
            label="Carter's-rule-corrected", zorder=3)
    ax.fill_between(radii, base_camber, corrected_camber, color=t["hub"],
                    alpha=0.12, zorder=1)

    ax.set_xlabel("Radius, m", color=t["ink_muted"])
    ax.set_ylabel("Blade camber angle, deg", color=t["ink"])
    ax.tick_params(colors=t["ink_muted"])
    for spine in ax.spines.values():
        spine.set_color(t["grid"])
    ax.grid(True, color=t["grid"], linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    legend = ax.legend(frameon=False, loc="lower right")
    for text in legend.get_texts():
        text.set_color(t["ink"])
    ax.set_title("Deviation: how much more camber a real cascade needs",
                  color=t["ink"], loc="left", fontweight="600", pad=14)
    fig.tight_layout()

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=t["surface"], bbox_inches="tight")
    plt.close(fig)
    return path


def meridional_flowpath_figure(
    rotor_hub, rotor_tip, stator_hub, stator_tip,
    rotor_x0, rotor_x1, stator_x0, stator_x1,
    path, theme: str = "light",
) -> Path:
    """Hub and casing radius against axial station for a converging-annulus
    stage — flat under each row, sloped through the gap between them, the
    same three-segment shape `annulus.converging_hub_solid`/
    `converging_casing_shell` actually build. Pure numbers in, no pyOCC:
    the axial extents are measured off the built solids elsewhere
    (`annulus.axial_extent`) and passed in rather than recomputed here.
    """
    t = THEMES[theme]
    xs = [rotor_x0, rotor_x1, stator_x0, stator_x1]
    hub = [rotor_hub, rotor_hub, stator_hub, stator_hub]
    tip = [rotor_tip, rotor_tip, stator_tip, stator_tip]

    fig, ax = plt.subplots(figsize=(8.0, 4.0), dpi=220)
    fig.patch.set_facecolor(t["surface"])
    ax.set_facecolor(t["surface"])

    ax.plot(xs, tip, color=t["hub"], linewidth=2.2, zorder=3, label="Casing")
    ax.plot(xs, hub, color=t["tip"], linewidth=2.2, zorder=3, label="Hub")
    ax.fill_between(xs, hub, tip, color=t["hub"], alpha=0.10, zorder=1)
    ax.axvspan(rotor_x0, rotor_x1, color=t["grid"], alpha=0.5, zorder=0)
    ax.axvspan(stator_x0, stator_x1, color=t["grid"], alpha=0.5, zorder=0)

    ax.set_xlabel("Axial station, m", color=t["ink_muted"])
    ax.set_ylabel("Radius, m", color=t["ink_muted"])
    ax.tick_params(colors=t["ink_muted"])
    for spine in ax.spines.values():
        spine.set_color(t["grid"])
    ax.grid(True, color=t["grid"], linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    legend = ax.legend(frameon=False, loc="lower left")
    for text in legend.get_texts():
        text.set_color(t["ink"])
    ax.set_title("Converging annulus — rotor and stator shaded",
                  color=t["ink"], loc="left", fontweight="600", pad=14)
    fig.tight_layout()

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=t["surface"], bbox_inches="tight")
    plt.close(fig)
    return path


def section_comparison_figure(row: BladeRow, path, theme: str = "light") -> Path:
    """Hub and tip sections overlaid at true relative chord — the same
    "why draw this" logic as the wing project's root/tip sections figure:
    without it, the difference in camber and stagger between hub and tip is
    a pair of numbers, not a shape a reviewer can see.

    theme picks the site's dark or light tokens (THEMES above) so this can be
    dropped straight into public/products/ as the CAD-gallery pair, the same
    dark/light convention project 04's figures use.
    """
    from .blade_section import CircularArcSection

    t = THEMES[theme]
    fig, ax = plt.subplots(figsize=(8.0, 4.5), dpi=260)
    fig.patch.set_facecolor(t["surface"])
    ax.set_facecolor(t["surface"])

    for r, color, label in (
        (row.hub_radius, t["hub"], "Hub"),
        (row.tip_radius, t["tip"], "Tip"),
    ):
        chord = row.chord_at(r)
        stagger = row.design.stagger_angle(r)
        section = CircularArcSection(
            camber_angle_deg=math.degrees(row.design.camber_angle(r)),
            thickness=row.thickness,
        )
        upper, lower = section.surfaces()
        for surf in (upper, lower):
            xs, zs = [], []
            for xc, zc in surf:
                x = (xc - 0.25) * chord
                z = zc * chord
                xr = x * math.cos(stagger) - z * math.sin(stagger)
                zr = x * math.sin(stagger) + z * math.cos(stagger)
                xs.append(xr)
                zs.append(zr)
            ax.plot(xs, zs, color=color, linewidth=2.2, zorder=3,
                     label=label if surf is upper else None)
            ax.fill(xs, zs, color=color, alpha=0.14, zorder=1)

    ax.set_xlabel("Axial, m", color=t["ink_muted"])
    ax.set_ylabel("Tangential, m", color=t["ink_muted"])
    ax.set_aspect("equal")
    ax.tick_params(colors=t["ink_muted"])
    for spine in ax.spines.values():
        spine.set_color(t["grid"])
    ax.grid(True, color=t["grid"], linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, labelcolor=t["ink"])
    ax.set_title("Hub vs. tip section, true relative scale and stagger",
                 color=t["ink"], loc="left", fontweight="600")
    fig.tight_layout()

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=t["surface"], bbox_inches="tight")
    plt.close(fig)
    return path

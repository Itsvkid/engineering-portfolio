"""Figures. Matplotlib only — no pyOCC dependency."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def station_ladder_figure(cycle, path, dark: bool = False) -> Path:
    """Stagnation temperature through the core gas path, intake to core
    nozzle exit — compression as a staircase up, combustion as a spike,
    expansion as a staircase down. The single most legible way to show
    what a cycle actually does to the working fluid, station by station,
    rather than leaving it as a table of numbers.

    `dark=True` renders on the portfolio site's dark scheme (bg1/fg0/fg1/
    accent from app/globals.css) so the figure ships a matching pair with
    the default light render, per the site's theme-aware figure convention.
    """
    s = cycle.stations
    names = ["fan\nface", "fan\nexit", "booster\nexit", "HPC\nexit",
             "combustor\nexit", "HPT\nexit", "LPT\nexit", "core nozzle\nexit"]
    temps = [s.fan_face.t, s.fan_exit.t, s.booster_exit.t, s.hpc_exit.t,
             s.combustor_exit.t, s.hpt_exit.t, s.lpt_exit.t, s.core_nozzle.t]
    x = list(range(len(names)))

    if dark:
        bg, fg0, fg1, line_color = "#101316", "#EDEEF0", "#A8AFB8", "#23282E"
        trace, compress, expand = "#FF6D3B", "#5FA8D3", "#4FBE84"
    else:
        bg, fg0, fg1, line_color = "#FFFFFF", "#17191C", "#4A5057", "#E3E3DF"
        trace, compress, expand = "#c0392b", "#2874a6", "#1b9e5a"

    fig, ax = plt.subplots(figsize=(8.5, 4.2), dpi=150)
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.plot(x, temps, "o-", color=trace, linewidth=2.2, markersize=7, zorder=3)
    ax.fill_between(x, temps, min(temps) - 50, color=trace, alpha=0.12 if dark else 0.08, zorder=1)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=9, color=fg1)
    ax.tick_params(axis="y", colors=fg1)
    ax.set_ylabel("Stagnation temperature, K", color=fg1)
    ax.set_title("Core gas path — station temperature", color=fg0)
    for spine in ax.spines.values():
        spine.set_color(line_color)
    ax.axvspan(0.5, 3.5, color=compress, alpha=0.1 if dark else 0.06, zorder=0)
    ax.annotate("compression", xy=(2, min(temps)), xytext=(0, -28),
                textcoords="offset points", ha="center", color=compress, fontsize=9)
    ax.axvspan(4.5, 6.5, color=expand, alpha=0.1 if dark else 0.06, zorder=0)
    ax.annotate("expansion", xy=(5.5, min(temps)), xytext=(0, -28),
                textcoords="offset points", ha="center", color=expand, fontsize=9)
    fig.tight_layout()

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=bg)
    plt.close(fig)
    return path


def throttle_sweep_figure(throttles, thrusts_kn, tsfcs, path, dark: bool = False) -> Path:
    """Net thrust and TSFC against throttle — the two curves
    off_design.py's simplified single-parameter throttle model produces,
    both falling out of the same pressure-ratio/TET scaling rather than
    being independently fitted. Precomputed sequences in, not a
    TurbofanDesignPoint or cycle here, so this stays free of any
    dependency on off_design.py or cycle.py — pure plotting, matching
    station_ladder_figure's own separation.
    """
    if dark:
        bg, fg0, fg1, line_color = "#101316", "#EDEEF0", "#A8AFB8", "#23282E"
        thrust_color, tsfc_color = "#5FA8D3", "#FF6D3B"
    else:
        bg, fg0, fg1, line_color = "#FFFFFF", "#17191C", "#4A5057", "#E3E3DF"
        thrust_color, tsfc_color = "#2874a6", "#c0392b"

    fig, ax1 = plt.subplots(figsize=(7.0, 4.4), dpi=150)
    fig.patch.set_facecolor(bg)
    ax1.set_facecolor(bg)

    ax1.plot(throttles, thrusts_kn, "o-", color=thrust_color, linewidth=2.2,
              markersize=6, zorder=3, label="Net thrust")
    ax1.set_xlabel("Throttle", color=fg1)
    ax1.set_ylabel("Net thrust, kN", color=thrust_color)
    ax1.tick_params(axis="y", colors=thrust_color)
    ax1.tick_params(axis="x", colors=fg1)

    ax2 = ax1.twinx()
    ax2.plot(throttles, tsfcs, "o-", color=tsfc_color, linewidth=2.2,
              markersize=6, zorder=3, label="TSFC")
    ax2.set_ylabel("TSFC, g/(kN·s)", color=tsfc_color)
    ax2.tick_params(axis="y", colors=tsfc_color)

    ax1.set_title("Part-throttle sweep — simplified single-parameter model", color=fg0)
    for spine in ax1.spines.values():
        spine.set_color(line_color)
    for spine in ax2.spines.values():
        spine.set_color(line_color)
    fig.tight_layout()

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=bg)
    plt.close(fig)
    return path

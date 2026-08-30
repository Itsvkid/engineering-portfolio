"""The general arrangement drawing. Needs pyOCC — run inside pyocc_env: it
imports BladeRow from blade.py, which imports OCC.Core at module level even
though general_arrangement() itself never calls BladeRow.build() or touches
pyOCC directly.

No test can say a drawing reads well — that needs eyes on the sheet. These
check it is produced, that it is deterministic, and that the values it
quotes come from the blade row rather than from constants typed into the
drawing code.
"""

import math

import matplotlib.pyplot as plt

from src.blade import BladeRow
from src.drawing import general_arrangement
from src.velocity_triangles import RotorDesignPoint

DESIGN = RotorDesignPoint(
    axial_velocity=150.0, omega=800.0, mean_radius=0.275, exit_swirl_mean=80.0
)
ROW = BladeRow(
    hub_radius=0.20, tip_radius=0.35, n_blades=32,
    root_chord=0.062, tip_chord=0.052, thickness=0.06, design=DESIGN,
)


def test_produces_a_sheet(tmp_path):
    path = tmp_path / "ga.png"
    plt.close(general_arrangement(ROW, path))
    assert path.exists() and path.stat().st_size > 30_000


def test_is_deterministic(tmp_path):
    """Regenerating an unchanged design must produce an identical file — a
    timestamp in the sheet would make every rebuild a diff."""
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    plt.close(general_arrangement(ROW, a))
    plt.close(general_arrangement(ROW, b))
    assert a.read_bytes() == b.read_bytes()


def test_a_date_changes_the_sheet(tmp_path):
    """The determinism above must come from omitting the date, not
    ignoring it."""
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    plt.close(general_arrangement(ROW, a))
    plt.close(general_arrangement(ROW, b, date="2026-08-22"))
    assert a.read_bytes() != b.read_bytes()


def test_a_different_row_gives_a_different_sheet(tmp_path):
    """Guards against a drawing that ignores its input."""
    other = BladeRow(hub_radius=0.20, tip_radius=0.40, n_blades=32,
                     root_chord=0.062, tip_chord=0.052, thickness=0.06,
                     design=DESIGN)
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    plt.close(general_arrangement(ROW, a))
    plt.close(general_arrangement(other, b))
    assert a.read_bytes() != b.read_bytes()


def test_scale_is_honoured(tmp_path):
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    plt.close(general_arrangement(ROW, a, scale_denominator=5))
    plt.close(general_arrangement(ROW, b, scale_denominator=10))
    assert a.read_bytes() != b.read_bytes()


def test_deviation_corrected_design_also_draws():
    """A DeviationCorrectedDesign duck-types stagger_angle/camber_angle,
    so a BladeRow built from one has to work here too, without any change
    to drawing.py — the same duck-typing guarantee blade.py's own
    docstring already relies on for a StatorDesignPoint."""
    from src.deviation import DeviationCorrectedDesign

    corrected_design = DeviationCorrectedDesign(
        base=DESIGN, space_chord_ratio=lambda r: 1.0 / ROW.solidity_at(r)
    )
    corrected_row = BladeRow(hub_radius=0.20, tip_radius=0.35, n_blades=32,
                             root_chord=0.062, tip_chord=0.052, thickness=0.06,
                             design=corrected_design)
    fig = general_arrangement(corrected_row)
    plt.close(fig)

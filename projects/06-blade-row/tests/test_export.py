"""STEP and glTF export. Needs pyOCC — run inside pyocc_env."""

from __future__ import annotations

import math

from src.blade import BladeRow
from src.export import to_glb, to_step
from src.velocity_triangles import RotorDesignPoint

DESIGN = RotorDesignPoint(
    axial_velocity=150.0,
    omega=8000.0 * 2 * math.pi / 60.0,
    mean_radius=0.275,
    exit_swirl_mean=80.0,
)
ROW = BladeRow(
    hub_radius=0.20, tip_radius=0.35, n_blades=4,
    root_chord=0.062, tip_chord=0.052, thickness=0.06, design=DESIGN,
)


def test_step_export_writes_a_nonempty_file(tmp_path):
    shape = ROW.build()
    out = to_step(shape, tmp_path / "blade.step")
    assert out.exists()
    assert out.stat().st_size > 0


def test_glb_export_writes_a_nonempty_file(tmp_path):
    shape = ROW.build()
    out = to_glb(shape, tmp_path / "blade.glb")
    assert out.exists()
    assert out.stat().st_size > 0


def test_step_export_rejects_unknown_unit(tmp_path):
    import pytest

    shape = ROW.build()
    with pytest.raises(ValueError):
        to_step(shape, tmp_path / "blade.step", unit="FURLONGS")

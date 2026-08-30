"""STEP and glTF export. Needs pyOCC — run inside pyocc_env."""

from __future__ import annotations

from src.cst import CSTCurve
from src.export import to_glb, to_step, to_stl
from src.nacelle import NacelleSolid
from src.profile import NacelleProfile

SOLID = NacelleSolid(NacelleProfile(
    length=3.0, curve=CSTCurve(r0=0.85, r1=0.60, weights=(0.6, 0.9, 0.5))
))


def test_step_export_writes_a_nonempty_file(tmp_path):
    shape = SOLID.build()
    out = to_step(shape, tmp_path / "nacelle.step")
    assert out.exists()
    assert out.stat().st_size > 0


def test_glb_export_writes_a_nonempty_file(tmp_path):
    shape = SOLID.build()
    out = to_glb(shape, tmp_path / "nacelle.glb")
    assert out.exists()
    assert out.stat().st_size > 0


def test_step_export_rejects_unknown_unit(tmp_path):
    import pytest

    shape = SOLID.build()
    with pytest.raises(ValueError):
        to_step(shape, tmp_path / "nacelle.step", unit="FURLONGS")


def test_stl_export_writes_a_nonempty_file(tmp_path):
    shape = SOLID.build()
    out = to_stl(shape, tmp_path / "nacelle.stl")
    assert out.exists()
    assert out.stat().st_size > 0


def test_stl_export_binary_header_reports_a_plausible_triangle_count(tmp_path):
    """Binary STL's header is 80 bytes of free text followed by a 4-byte
    little-endian triangle count — checked directly against the file
    rather than just trusting a nonzero size, since a corrupt or
    ASCII-when-binary-expected file would still pass the size check."""
    import struct

    shape = SOLID.build()
    out = to_stl(shape, tmp_path / "nacelle.stl", ascii_mode=False)
    with open(out, "rb") as f:
        f.read(80)
        count = struct.unpack("<I", f.read(4))[0]
    assert count > 0
    expected_size = 80 + 4 + count * 50
    assert out.stat().st_size == expected_size

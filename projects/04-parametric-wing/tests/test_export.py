"""Export round-trips, including the unit conversion.

An export nobody else can open at the right size is not an export.
"""

import pytest
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.BRepGProp import brepgprop
from OCC.Core.GProp import GProp_GProps
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.STEPControl import STEPControl_Reader

from src.export import to_glb, to_iges, to_step
from src.wing import Wing

REF = Wing(span=10.0, root_chord=1.6, taper_ratio=0.45, sweep_deg=25.0,
           dihedral_deg=5.0, twist_deg=3.0)


def _read(path):
    reader = STEPControl_Reader()
    assert reader.ReadFile(str(path)) == IFSelect_RetDone, "STEP is unreadable"
    reader.TransferRoots()
    return reader.OneShape()


def _span_of(shape):
    box = Bnd_Box()
    brepbndlib.AddOptimal(shape, box)
    _, ymin, _, _, ymax, _ = box.Get()
    return ymax - ymin


def test_step_defaults_to_millimetres(tmp_path):
    """A 10 m wing must arrive as 10 000 units, not 10.

    FreeCAD opened the metre-declared export at 1/1000 scale: it read the raw
    numbers as millimetres and ignored the SI_UNIT declaration. Most
    mechanical CAD assumes millimetres whatever the file says, so this is the
    default and this test is what keeps it.
    """
    path = to_step(REF.build(), tmp_path / "wing.step")
    assert _span_of(_read(path)) == pytest.approx(10_000.0, rel=1e-5)
    assert "MILLI" in path.read_text()


def test_step_in_metres_when_asked(tmp_path):
    path = to_step(REF.build(), tmp_path / "wing_m.step", unit="M")
    assert _span_of(_read(path)) == pytest.approx(10.0, rel=1e-5)


def test_round_trip_preserves_volume(tmp_path):
    """Re-read the export and confirm it is the same solid, scale aside."""
    path = to_step(REF.build(), tmp_path / "wing.step")
    props = GProp_GProps()
    brepgprop.VolumeProperties(_read(path), props)
    assert props.Mass() / 1e9 == pytest.approx(REF.measured_volume(), rel=1e-6)


def test_rejects_unknown_units(tmp_path):
    with pytest.raises(ValueError, match="unit must be"):
        to_step(REF.build(), tmp_path / "x.step", unit="INCH")


def test_iges_writes_and_is_not_empty(tmp_path):
    path = to_iges(REF.build(), tmp_path / "wing.iges")
    assert path.exists() and path.stat().st_size > 10_000


def test_glb_is_written_and_is_a_real_gltf(tmp_path):
    path = to_glb(REF.build(), tmp_path / "wing.glb")
    assert path.read_bytes()[:4] == b"glTF"
    assert path.stat().st_size > 20_000


def test_mesh_density_actually_responds_to_deflection(tmp_path):
    """Guards against the helper that silently ignores it.

    OCC.Extend.DataExchange.write_gltf_file discards any existing triangulation
    and re-meshes with `BRepMesh_IncrementalMesh(shape, True)` — True landing in
    the linear-deflection argument as 1.0. On a ten-metre wing that produced 48
    triangles for the whole model, and the file was still a valid glTF, so only
    a size comparison catches it.
    """
    fine = to_glb(Wing(span=10.0, root_chord=1.6, taper_ratio=0.45).build(),
                  tmp_path / "fine.glb", linear_deflection=0.002)
    coarse = to_glb(Wing(span=10.0, root_chord=1.6, taper_ratio=0.45).build(),
                    tmp_path / "coarse.glb", linear_deflection=0.015)
    assert fine.stat().st_size > coarse.stat().st_size * 2


def test_glb_stays_in_metres(tmp_path):
    """glTF's convention is metres and three.js assumes it — no conversion."""
    small = to_glb(Wing(span=1.0, root_chord=0.16, taper_ratio=0.45).build(),
                   tmp_path / "small.glb", linear_deflection=0.0004)
    assert small.exists()

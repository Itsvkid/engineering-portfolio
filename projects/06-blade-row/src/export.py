"""STEP and glTF export.

Same conventions as the parametric-wing project's export.py: STEP in
millimetres because most mechanical CAD assumes mm regardless of what the
file declares, glTF in metres because that is glTF's own convention and what
three.js expects. Duplicated rather than imported — this project stays
self-contained, the same choice the wing and OpenFOAM projects each made.
"""

from __future__ import annotations

from pathlib import Path

from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.Interface import Interface_Static
from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Writer
from OCC.Core.gp import gp_Trsf

M_TO_MM = 1000.0


def _scaled(shape, factor: float):
    trsf = gp_Trsf()
    trsf.SetScaleFactor(factor)
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


def to_step(shape, path, unit: str = "MM") -> Path:
    """Write `shape` as STEP AP214, converting from metres to `unit`."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if unit == "MM":
        shape = _scaled(shape, M_TO_MM)
    elif unit != "M":
        raise ValueError(f"unit must be 'MM' or 'M', got {unit!r}")

    writer = STEPControl_Writer()
    Interface_Static.SetCVal("write.step.unit", unit)
    Interface_Static.SetCVal("write.step.schema", "AP214")
    writer.Transfer(shape, STEPControl_AsIs)

    if writer.Write(str(path)) != IFSelect_RetDone:
        raise RuntimeError(f"STEP export failed for {path}")
    return path


def to_glb(shape, path, linear_deflection: float = 0.0005,
           angular_deflection: float = 0.35) -> Path:
    """Tessellate and write a binary glTF for the web, kept in metres.

    linear_deflection is much finer than the wing project's default (0.004)
    because a blade row is a few centimetres of chord, not metres of span —
    the same absolute deflection would be a much coarser fraction of this
    part and would facet visibly.
    """
    from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
    from OCC.Core.Message import Message_ProgressRange
    from OCC.Core.RWGltf import RWGltf_CafWriter
    from OCC.Core.TColStd import TColStd_IndexedDataMapOfStringString
    from OCC.Core.TDocStd import TDocStd_Document
    from OCC.Core.XCAFDoc import XCAFDoc_DocumentTool

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    mesher = BRepMesh_IncrementalMesh(shape, linear_deflection, False,
                                      angular_deflection, True)
    mesher.Perform()

    doc = TDocStd_Document("pythonocc-doc-gltf-export")
    XCAFDoc_DocumentTool.ShapeTool(doc.Main()).AddShape(shape)

    writer = RWGltf_CafWriter(str(path), True)
    if writer.Perform(doc, TColStd_IndexedDataMapOfStringString(),
                      Message_ProgressRange()) != IFSelect_RetDone:
        raise RuntimeError(f"glTF export failed for {path}")
    return path

"""STEP and glTF export — same conventions as projects 04 and 06: STEP in
millimetres (most mechanical CAD assumes mm regardless of what the file
declares), glTF in metres (its own convention, and what three.js expects).
Duplicated rather than imported — this project stays self-contained.
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


def to_stl(shape, path, linear_deflection: float = 0.0005,
           angular_deflection: float = 0.2, ascii_mode: bool = False) -> Path:
    """STL for an external mesher (openfoam/'s snappyHexMesh, in this
    project's case) — metres, matching the shape's native units (unlike
    to_step, STL carries no unit declaration at all, so the caller has to
    already know what a mesher downstream will assume; snappyHexMesh
    assumes metres, and this project's shapes are already built in
    metres, so no scaling here). Finer default deflection than to_glb's —
    a viewer tolerates a coarser mesh than a CFD surface mesh should
    start from.
    """
    from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
    from OCC.Core.StlAPI import StlAPI_Writer

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    mesher = BRepMesh_IncrementalMesh(shape, linear_deflection, False,
                                      angular_deflection, True)
    mesher.Perform()

    writer = StlAPI_Writer()
    writer.SetASCIIMode(ascii_mode)
    if not writer.Write(shape, str(path)):
        raise RuntimeError(f"STL export failed for {path}")
    return path


def to_glb(shape, path, linear_deflection: float = 0.003,
           angular_deflection: float = 0.35) -> Path:
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

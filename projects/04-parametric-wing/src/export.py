"""STEP and IGES export.

STEP (AP214) is the format to hand anyone else — it carries units and solid
topology, and every CAD system and the Autodesk viewer read it. IGES is here
because some older tools still ask for it; it is surface-based and loses the
solid, so prefer STEP wherever there is a choice.
"""

from __future__ import annotations

from pathlib import Path

from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.IGESControl import IGESControl_Writer
from OCC.Core.Interface import Interface_Static
from OCC.Core.STEPControl import STEPControl_AsIs, STEPControl_Writer
from OCC.Core.gp import gp_Trsf

# The wing is modelled in metres, which is the natural unit for an aircraft.
# Mechanical CAD exchange is millimetres, and most tools assume it regardless
# of what the file declares — so exports convert by default.
M_TO_MM = 1000.0


def _scaled(shape, factor: float):
    trsf = gp_Trsf()
    trsf.SetScaleFactor(factor)
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


def to_step(shape, path, unit: str = "MM") -> Path:
    """Write `shape` as STEP AP214, converting from metres to `unit`.

    Defaults to millimetres, and that default was earned. Writing metres and
    declaring METRE is correct by the standard, and FreeCAD still opened the
    result at 1/1000 scale: it read the raw numbers as millimetres and ignored
    the declaration. Most mechanical CAD assumes millimetres whatever the file
    says, so the interoperable choice is to meet that assumption rather than to
    be right and unreadable.

    Pass unit="M" to write metres, if the receiving tool is known to honour the
    declared unit.
    """
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


def to_iges(shape, path) -> Path:
    """Write `shape` as IGES in millimetres, for the same reason as STEP."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    shape = _scaled(shape, M_TO_MM)
    writer = IGESControl_Writer("MM", 0)
    writer.AddShape(shape)
    writer.ComputeModel()
    if not writer.Write(str(path)):
        raise RuntimeError(f"IGES export failed for {path}")
    return path


def to_glb(shape, path, linear_deflection: float = 0.004,
           angular_deflection: float = 0.35) -> Path:
    """Tessellate and write a binary glTF for the web.

    Kept in metres, unlike the STEP and IGES exports: glTF's convention is
    metres and three.js assumes it, so converting here would be the mistake
    that converting there avoids.

    Drives RWGltf_CafWriter directly rather than using
    OCC.Extend.DataExchange.write_gltf_file, which cannot be given a mesh
    density: it calls breptools.Clean to discard any existing triangulation and
    then re-meshes with `BRepMesh_IncrementalMesh(shape, True)`, where True
    lands in the linear-deflection argument as 1.0. A one-metre deflection on a
    ten-metre wing produced 48 triangles for the whole model.

    The deflections here control triangle count directly. A browser canvas
    cannot resolve more detail than a few thousand triangles across a
    silhouette this slender, so raise `linear_deflection` until the outline
    stops changing and stop — a finer mesh only costs the visitor bytes.
    """
    from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
    from OCC.Core.IFSelect import IFSelect_RetDone
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

    # Constructed from a plain str. Passing TCollection_ExtendedString throws
    # Standard_NullObject from the C++ layer, which aborts the interpreter
    # without a Python traceback.
    doc = TDocStd_Document("pythonocc-doc-gltf-export")
    XCAFDoc_DocumentTool.ShapeTool(doc.Main()).AddShape(shape)

    writer = RWGltf_CafWriter(str(path), True)
    if writer.Perform(doc, TColStd_IndexedDataMapOfStringString(),
                      Message_ProgressRange()) != IFSelect_RetDone:
        raise RuntimeError(f"glTF export failed for {path}")
    return path

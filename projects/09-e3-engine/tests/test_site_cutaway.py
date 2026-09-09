"""Stage J unit J7: the rotating cutaway on the site
(solvers/publication/STEP0.md unit J7).

The page turns the two spools at their own speeds. It does not decide
which rows belong to which spool, and it does not carry the speeds -- both
come out of the glTF, written by the exporter from the same data that
drives the mass roll-up. These tests hold that contract from both ends:
the Python that writes the file, and the three.js that reads it."""
import json
import pathlib
import shutil
import struct
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = ROOT.parents[1]
sys.path.insert(0, str(ROOT / "solvers"))
pytest.importorskip("cadquery")

from publication.render import (  # noqa: E402
    RPM_HP, RPM_LP, WEB_BAND_PCT, WEB_TOL_M, _kinematics, build_gltf,
    web_fidelity,
)

WEB_GLB = SITE / "public/models/e3-blading.glb"


def _read(path):
    raw = path.read_bytes()
    off, chunks = 12, {}
    while off < len(raw):
        ln, ty = struct.unpack("<II", raw[off:off + 8])
        off += 8
        chunks[ty] = raw[off:off + ln]
        off += ln
    return json.loads(chunks[0x4E4F534A])


# --- the web variant is its own artefact with its own band ---------------

def test_the_web_variant_holds_its_own_stated_band():
    """2 mm and 2 %, against the archival file's 0.6 mm and 1 %. Two
    artefacts, two declared bands -- not one tolerance quietly loosened."""
    f = web_fidelity()
    assert f["inside"] is True
    assert f["worst_pct"] <= WEB_BAND_PCT
    assert f["rows"] == 32


def test_the_web_variant_is_coarser_than_the_archival_one():
    from publication.render import TESS_TOL_M, volume_fidelity
    assert WEB_TOL_M > TESS_TOL_M
    fine = max(abs(r["err_pct"]) for r in volume_fidelity())
    assert fine < web_fidelity()["worst_pct"]     # coarser really is coarser
    assert web_fidelity()["triangles"] < sum(r["triangles"]
                                             for r in volume_fidelity())


def test_the_web_file_is_on_the_site_and_small_enough_to_serve():
    if not WEB_GLB.exists():
        pytest.skip("site checkout not present")
    mb = WEB_GLB.stat().st_size / 1e6
    assert 0.5 < mb < 4.0, mb


# --- the file carries the architecture, so the page need not guess -------

def test_every_row_node_declares_its_spool():
    g, _, stats = build_gltf()
    rows = [n for n in g["nodes"] if "extras" in n]
    assert len(rows) == 32 == len(stats)
    for n in rows:
        assert n["extras"]["spool"] in ("lp", "hp", "static")
        assert n["extras"]["blades"] > 0


def test_the_spool_split_is_the_engine_architecture():
    g, _, _ = build_gltf()
    from collections import Counter
    by = Counter(n["extras"]["spool"] for n in g["nodes"] if "extras" in n)
    # fan, booster and the five LPT rotors ride the low spool
    assert by["lp"] == 7
    # the ten HPC rotors ride the high spool
    assert by["hp"] == 10
    # every stator and vane is static
    assert by["static"] == 15
    assert sum(by.values()) == 32


def test_the_kinematics_travel_on_the_scene_not_only_the_asset():
    """three.js copies node and scene extras into userData, but not the
    asset block -- a viewer reading only the object graph would otherwise
    never see the speeds"""
    g, _, _ = build_gltf()
    assert "kinematics" in g["scenes"][0]["extras"]
    assert "kinematics" in g["asset"]["extras"]
    assert g["scenes"][0]["extras"]["kinematics"] == g["asset"]["extras"]["kinematics"]


def test_the_speeds_are_unit_i1s_reconciled_numbers():
    k = _kinematics()
    assert k["rpm_lp"] == RPM_LP and k["rpm_hp"] == RPM_HP
    assert k["ratio"] == pytest.approx(3.583, abs=0.002)
    # unit I1 reconciled the ratio from four documents
    from verification.consistency import spool_speeds_four_routes
    assert k["ratio"] == pytest.approx(spool_speeds_four_routes()["ratio"],
                                       rel=0.01)


def test_co_rotation_is_declared_a_decision_not_a_fact():
    """the reports read do not state the relative rotation direction"""
    k = _kinematics()
    assert k["co_rotating"] is True
    assert "MODELLING" in k["note"] and "not a published fact" in k["note"]
    assert "does not run" in k["note"]


# --- the page reads it, rather than pattern-matching on names ------------

def test_the_component_takes_the_spool_from_the_file():
    src = (SITE / "app/components/EngineCutaway.js")
    if not src.exists():
        pytest.skip("site checkout not present")
    t = src.read_text()
    assert "userData?.spool" in t
    assert "userData?.kinematics" in t
    # no name-based guessing
    assert "hpc-rotor" not in t and "startsWith" not in t


def test_the_component_does_not_recentre_off_the_rotation_axis():
    """the 75 deg cutaway makes the geometry deliberately non-axisymmetric,
    so centring on the bounding box in y or z would make the spools wobble"""
    src = (SITE / "app/components/EngineCutaway.js")
    if not src.exists():
        pytest.skip("site checkout not present")
    t = src.read_text()
    assert "Centre in X ONLY" in t
    assert "centre.y" not in t and "centre.z" not in t


def test_three_js_really_does_surface_the_extras():
    """the assumption the whole component rests on, checked against the
    actual loader rather than the specification"""
    if not WEB_GLB.exists() or shutil.which("node") is None:
        pytest.skip("node or the site checkout is not present")
    script = """
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import fs from 'fs';
const buf = fs.readFileSync(process.argv[1]);
const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
new GLTFLoader().parse(ab, '', (gltf) => {
  const s = gltf.scene;
  const by = {};
  for (const c of s.children) by[c.userData?.spool ?? 'MISSING'] =
    (by[c.userData?.spool ?? 'MISSING'] || 0) + 1;
  console.log(JSON.stringify({
    ratio: s.userData?.kinematics?.ratio,
    children: s.children.length,
    by,
  }));
});
"""
    p = subprocess.run(["node", "--input-type=module", "-e", script,
                        str(WEB_GLB)], cwd=SITE, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr[-800:]
    got = json.loads(p.stdout.strip().splitlines()[-1])
    assert got["children"] == 32
    assert got["by"] == {"lp": 7, "hp": 10, "static": 15}
    assert got["ratio"] == pytest.approx(3.583, abs=0.002)


def test_the_model_is_measured_before_its_rows_are_re_parented():
    """the silent failure: adding a child to another group REMOVES it from
    root, so a Box3 taken after the split is taken from an empty object.
    three.js then reports an inverted box, a centre of (0, 0, 0) and an
    infinite bounding sphere -- so the X-centring quietly did nothing, and
    a camera fitted to that sphere goes to infinity and renders a blank
    canvas. Nothing about it looks wrong in the source; only the order is."""
    src = (SITE / "app/components/EngineCutaway.js")
    if not src.exists():
        pytest.skip("site checkout not present")
    t = src.read_text()
    measured = t.index("new Box3().setFromObject(root)")
    split = t.index("made.static).add(child)")
    assert measured < split, \
        "the bounding box must be taken while root still holds the rows"


def test_the_camera_is_fitted_to_the_canvas_rather_than_fixed():
    """a fixed camera distance is right for exactly one canvas size. The
    other models in this viewer use drei's <Bounds fit observe>; a turning
    model cannot, because Bounds would re-fit every frame, so the same job
    is done once per resize against a rotation-invariant sphere."""
    src = (SITE / "app/components/EngineCutaway.js")
    if not src.exists():
        pytest.skip("site checkout not present")
    t = src.read_text()
    assert "FitToView" in t
    assert "size.width / size.height" in t      # it reads the aspect
    assert "Math.sin(Math.min(vHalf, hHalf))" in t   # fits the tighter one


def test_the_site_registers_the_model_with_the_spool_flag():
    data = (SITE / "app/data.js")
    if not data.exists():
        pytest.skip("site checkout not present")
    t = data.read_text()
    assert "/models/e3-blading.glb" in t
    assert "spools: true" in t
    # the claim on the page must not overstate the rotation direction
    assert "it does not run" in t


def test_only_the_engine_model_spins_its_spools():
    data = (SITE / "app/data.js")
    if not data.exists():
        pytest.skip("site checkout not present")
    assert data.read_text().count("spools: true") == 1

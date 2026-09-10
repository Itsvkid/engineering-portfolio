"""Stage J unit J3: the render
(solvers/publication/STEP0.md unit J3)."""
import json
import pathlib
import struct
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "solvers"))
# the lofted rows come from Stage G1, which needs the geometry kernel. CI
# runs on a plain runner where cadquery has no wheel, so this file skips
# itself there rather than being named in a list that goes stale --
# test_geometry.py does the same.
pytest.importorskip("cadquery")

from publication.render import (  # noqa: E402
    CUTAWAY_FROM_DEG, CUTAWAY_TO_DEG, SPOOL_COLOUR, axial_stations,
    blade_angles, blade_envelope, build_gltf, cap_overshoot, containment,
    mesh_volume,
    place_rows, plot_blading, summary, tessellate, volume_fidelity, write_glb,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Built once, on first use -- NOT at import. Assembling the glTF lofts and
# tessellates 32 rows and takes about three minutes, and at module level
# that cost lands on `pytest --collect-only`, which tools/build_readme.py
# shells out to for its test count. Collection should be cheap.
_BUILT = None


def built():
    global _BUILT
    if _BUILT is None:
        _BUILT = build_gltf()
    return _BUILT


@pytest.fixture(scope="module")
def gltf():
    return built()[0]


@pytest.fixture(scope="module")
def blob():
    return built()[1]


@pytest.fixture(scope="module")
def stats():
    return built()[2]


# --- the mesh is the solid: the step-0 band -------------------------------

def test_every_row_tessellates_inside_one_percent_by_volume():
    v = volume_fidelity()
    assert len(v) == 32
    worst = max(abs(r["err_pct"]) for r in v)
    assert worst <= 1.0, [(r["row"], r["err_pct"]) for r in v
                          if abs(r["err_pct"]) > 1.0]


def test_mesh_volume_is_the_divergence_theorem_and_is_checked_on_a_cube():
    """a volume routine that is never checked against a known answer is a
    number generator"""
    P = np.array([[0, 0, 0], [2, 0, 0], [2, 2, 0], [0, 2, 0],
                  [0, 0, 2], [2, 0, 2], [2, 2, 2], [0, 2, 2]], dtype=np.float32)
    T = np.array([[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
                  [0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5],
                  [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]], dtype=np.uint32)
    assert mesh_volume(P, T) == pytest.approx(8.0, rel=1e-6)


def test_normals_are_unit_length():
    from geometry.blades import all_rows
    _, _, N = tessellate(all_rows()[0].solid())
    assert np.allclose(np.linalg.norm(N, axis=1), 1.0, atol=1e-5)


# --- every row, every blade ----------------------------------------------

def test_all_thirty_two_rows_and_all_blades_are_accounted_for(stats):
    assert len(stats) == 32
    assert sum(s["count"] for s in stats) == 2890
    from geometry.blades import all_rows
    by = {r.name: r.count for r in all_rows()}
    for s in stats:
        assert s["count"] == by[s["row"]]


def test_one_mesh_per_row_and_one_node_per_drawn_blade(gltf, stats):
    """the whole reason the file is deliverable"""
    assert len(gltf["meshes"]) == 32
    drawn = sum(s["drawn"] for s in stats)
    assert len(gltf["nodes"]) == drawn + 32          # blades plus row nodes
    assert len(gltf["scenes"][0]["nodes"]) == 32


def test_instancing_actually_saves_the_file(gltf, stats):
    """32 meshes for 2275 drawn blades -- without instancing this is 70x"""
    drawn = sum(s["drawn"] for s in stats)
    assert drawn > 2000
    assert len(gltf["meshes"]) * 50 < drawn


# --- the cutaway removes blades, never clips them -------------------------

def test_the_cutaway_omits_whole_blades():
    from geometry.blades import all_rows
    for row in all_rows():
        kept = blade_angles(row, cutaway=True)
        full = blade_angles(row, cutaway=False)
        assert len(full) == row.count
        assert set(kept) <= set(full)                # no new angles invented
        for a in kept:
            assert not (CUTAWAY_FROM_DEG <= a < CUTAWAY_TO_DEG)


def test_the_cutaway_removes_roughly_its_own_wedge(stats):
    frac = (CUTAWAY_TO_DEG - CUTAWAY_FROM_DEG) / 360.0
    drawn = sum(s["drawn"] for s in stats)
    assert drawn / 2890 == pytest.approx(1 - frac, abs=0.02)


def test_no_geometry_is_clipped_anywhere_in_the_writer():
    src = (ROOT / "solvers/publication/render.py").read_text()
    assert "never clipped" in src
    for word in ("cut(", "split(", "intersect("):
        assert word not in src


# --- placement is J1's, not a second copy ---------------------------------

def test_placement_reads_j1s_layout_and_keeps_no_copy_of_the_offsets():
    src = (ROOT / "solvers/publication/render.py").read_text()
    assert "from publication.meridional import" in src
    assert "142" not in src and "1.42" not in src


def test_the_hpc_sits_at_j1s_assumed_offset():
    from publication.meridional import layout
    st = axial_stations()
    assert st["hpc-rotor-1"] * 100 == pytest.approx(layout()["hpc"]["x0"], abs=0.05)


def test_the_lpt_rows_ride_on_their_own_coordinates():
    from publication.meridional import layout
    st = axial_stations()
    lx = layout()["lpt"]["x0"] / 100
    for n in range(1, 6):
        assert st[f"lpt-rotor-{n}"] == pytest.approx(lx, abs=1e-9)


def test_the_booster_station_is_declared_assumed():
    b = [e for e in place_rows() if e["row"].name == "booster-rotor"][0]
    assert "ASSUMED" in b["basis"]


# --- the render is the same engine as J1's flowpath -----------------------

def test_every_hpc_row_sits_inside_the_published_annulus():
    """the check no other unit could make: G1's solids against J1's walls"""
    c = containment()
    assert len(c) == 20
    for r in c:
        assert r["below_hub_mm"] < 1.0, r
        assert r["above_casing_mm"] < 1.0, r


def test_the_blades_touch_the_walls_because_no_clearance_is_modelled():
    """finding 164 -- the agreement is sub-mm and so is the running
    clearance, so a viewer must not read tip clearance off this render"""
    c = containment()
    assert max(abs(r["above_casing_mm"]) for r in c) < 1.0
    assert all(r["r_hi"] <= r["tip_m"] + 1e-3 for r in c)


def test_the_engine_spans_what_j1_says_it_spans():
    """285.6 cm, not the 346.9 this asserted until 2026-09-10.

    The difference is 61.3 cm and it is not a coincidence: it is exactly the
    excess the two assumed stitching offsets were carrying before CR-159584
    Table I's published 318.0 cm turbomachinery length constrained their
    sum. Correcting them shortened the core by precisely the amount the
    closure had predicted, which is the strongest confirmation available
    that the right thing moved -- an arbitrary error would not have landed
    on its own predicted size.

    The forward end does not move, because the fan is the datum."""
    env = blade_envelope()
    assert min(e["x_lo"] for e in env) * 100 == pytest.approx(8.19, abs=0.2)
    assert max(e["x_hi"] for e in env) * 100 == pytest.approx(285.6, abs=1.0)
    # 104.2, not the 103.9 of the fan tip section: the tip cap stands
    # 3 mm proud of its own boundary wire -- finding 163, tested below
    assert max(e["r_hi"] for e in env) * 100 == pytest.approx(104.2, abs=0.1)


def test_the_tip_caps_bulge_past_their_own_sections():
    """finding 163: makeNSidedSurface interpolates across the boundary wire
    and overshoots it, worst on the largest cap"""
    o = {r["row"]: r for r in cap_overshoot()}
    assert o["fan-rotor"]["overshoot_mm"] == pytest.approx(3.0, abs=0.3)
    assert all(r["overshoot_mm"] < 0.7 for k, r in o.items() if k != "fan-rotor")
    # the LPT caps are exact
    assert all(r["overshoot_mm"] < 0.1 for k, r in o.items() if k.startswith("lpt-"))
    # and it is always outward, never inward
    assert all(r["overshoot_mm"] >= -0.01 for r in o.values())


def test_the_overshoot_stays_inside_the_volume_band():
    """it is a real 3 mm and it is still a 0.3 % blade"""
    o = {r["row"]: r for r in cap_overshoot()}
    fan = o["fan-rotor"]
    assert fan["overshoot_mm"] / (fan["section_tip_m"] * 1000) * 100 < 0.3


def test_there_are_no_hpt_rows_and_that_is_a_source_gap(stats):
    """finding 165"""
    assert not any(s["row"].startswith("hpt-") for s in stats)


# --- the container ---------------------------------------------------------

def test_the_glb_is_structurally_valid():
    p, _ = write_glb()
    raw = p.read_bytes()
    magic, ver, total = struct.unpack("<III", raw[:12])
    assert magic == 0x46546C67 and ver == 2
    assert total == len(raw)
    off, chunks = 12, {}
    while off < len(raw):
        ln, ty = struct.unpack("<II", raw[off:off + 8])
        off += 8
        chunks[ty] = raw[off:off + ln]
        off += ln
        assert ln % 4 == 0                       # every chunk 4-byte aligned
    g = json.loads(chunks[0x4E4F534A])
    assert g["asset"]["version"] == "2.0"
    assert g["buffers"][0]["byteLength"] == len(chunks[0x004E4942])


def test_the_file_is_small_enough_to_be_a_deliverable():
    p, _ = write_glb()
    assert p.stat().st_size / 1e6 < 12.0


def test_every_accessor_is_consistent_with_its_buffer_view(gltf, blob):
    # 5123 is UNSIGNED_SHORT, two bytes. It appeared when the writer began
    # narrowing indices per row, and this map knew only the four-byte types,
    # so the test raised KeyError instead of failing an assertion -- a test
    # that cannot express the file's own vocabulary does not check it.
    SIZE = {5126: 4, 5125: 4, 5123: 2}
    COMP = {"VEC3": 3, "SCALAR": 1}
    for a in gltf["accessors"]:
        bv = gltf["bufferViews"][a["bufferView"]]
        need = a["count"] * COMP[a["type"]] * SIZE[a["componentType"]]
        assert need <= bv["byteLength"]
        assert bv["byteOffset"] + bv["byteLength"] <= len(blob)


def test_indices_narrow_to_uint16_exactly_when_the_row_allows_it(gltf):
    """the narrowing is lossless or it is corruption: uint16 addresses
    65,536 vertices, so a row may use it only if it has fewer than that.

    Unit J7 covers the spools and the web variant; this stays here because
    it is about the container, and it rides the fixture already built."""
    for mesh in gltf["meshes"]:
        prim = mesh["primitives"][0]
        idx = gltf["accessors"][prim["indices"]]
        verts = gltf["accessors"][prim["attributes"]["POSITION"]]["count"]
        assert idx["componentType"] == (5123 if verts < 65536 else 5125), (
            mesh["name"], verts, idx["componentType"])
    # Every row qualifies, which is why the saving is worth having. The
    # bound is the uint16 ceiling, not a number measured once: the first
    # draft asserted "under 6,000", which was the largest row at the WEB
    # tolerance and not at this one -- the archival file's largest is
    # 10,886. Same conclusion, wrong evidence.
    biggest = max(gltf["accessors"][m["primitives"][0]["attributes"]
                                    ["POSITION"]]["count"]
                  for m in gltf["meshes"])
    assert biggest < 65536, biggest
    assert biggest == 10886, biggest        # pinned: archival tolerance


def test_materials_carry_one_colour_per_spool(gltf):
    assert len(gltf["materials"]) == 3
    assert {m["name"] for m in gltf["materials"]} == set(SPOOL_COLOUR)


def test_the_assumption_travels_inside_the_file(gltf):
    """a 3D file outlives the page that explains it"""
    ex = gltf["asset"]["extras"]
    for k in ("fan_sa_to_hpc_r1_le", "hpc_ogv_te_to_hpt_vane1"):
        assert ex["assumed_offsets"][k]["value_cm"] > 0
        assert len(ex["assumed_offsets"][k]["allowable_cm"]) == 2
    assert "NOT published" in ex["assumed_offsets_note"]
    assert "cutaway" in ex and "axis" in ex


def test_the_preview_figure_renders():
    p = plot_blading()
    assert p.exists() and p.stat().st_size > 20_000


def test_the_summary_names_the_instancing_saving():
    s = summary()
    assert "2890 blades" in s
    assert "instanced" in s

"""Stage J unit J3: the render -- 32 blade rows as one glTF object.

Stage G1 lofted 32 rows from the validated sections; nothing in this
project has shown them as a single object, and J1's meridional plot draws
the annulus with no blade in it.

**Why this writes its own GLB.** One row of 53 blades comes out of
`cadquery`'s assembly exporter at 27.6 MB, and the cost is the lofted
surface's own face structure rather than the deflection tolerance --
coarsening 0.5 mm to 8 mm saves 14 %. All 2,890 blades that way is about
1.4 GB. glTF lets many nodes reference one mesh, so the file here carries
**32 meshes and 2,890 nodes**: each row is tessellated once and then
instanced round its annulus by a transform. `cadquery` writes a mesh per
solid and cannot do that, and neither `trimesh` nor `pygltflib` is
installed, so the container is written here. It is a JSON chunk and a
binary chunk; that is the whole format.

**Placement comes from unit J1.** The LPT rows already carry their axial
stations -- their CSV's z runs from the HPT exit plane -- while the fan,
booster and HPC rows each sit at their own local zero. Putting them on one
axis needs the two offsets that are *assumed and not published*, so this
module reads them through `publication.meridional.layout()` and keeps no
copy of its own (unit J1, finding 159). Those offsets and their allowable
ranges are written into the glTF's `asset.extras`, because a 3D file
outlives the page that explains it.

STEP0.md unit J3."""
from __future__ import annotations

import base64
import json
import math
import struct
from pathlib import Path

import numpy as np

CM_ = 0.01

FIGDIR = Path(__file__).resolve().parent / "figures"
EXPORTDIR = Path(__file__).resolve().parents[2] / "exports"

#: deflection for the OCC tessellation, metres. Fine enough that the mesh
#: volume holds inside the 1 % step-0 band; see `volume_fidelity`.
TESS_TOL_M = 0.0006
TESS_ANGLE_RAD = 0.25

#: The web variant is a DIFFERENT artefact with its own, looser band. 2 mm
#: halves the triangle count to about 65,000 and costs 1.35 % on the worst
#: row's volume, against 0.37 % for the archival file. Both bands are
#: declared; neither is the other's tolerance quietly relaxed.
WEB_TOL_M = 0.002
WEB_BAND_PCT = 2.0

#: Spool speeds at max climb, from unit I1's four-route reconciliation.
#: The site cutaway turns the two spools at this ratio.
RPM_LP = 3528.9
RPM_HP = 12645.0

#: The cutaway. Blades whose angular station falls inside this wedge are
#: LEFT OUT ENTIRELY -- never clipped. A clipped blade draws a shape the
#: engine does not have.
CUTAWAY_FROM_DEG = 0.0
CUTAWAY_TO_DEG = 75.0

SPOOL_COLOUR = {
    "lp": (0.42, 0.55, 0.72, 1.0),        # low-pressure spool
    "hp": (0.78, 0.55, 0.24, 1.0),        # high-pressure spool
    "static": (0.62, 0.64, 0.66, 1.0),    # vanes and stators
}


# --------------------------------------------------------------- geometry

def tessellate(solid, tol=TESS_TOL_M, angle=TESS_ANGLE_RAD):
    """Triangles for one blade, with area-weighted vertex normals.

    `Shape.tessellate` caches its triangulation on the shape, which is why
    a second export at a different tolerance silently returns the first
    mesh. Callers that vary the tolerance must hand in a fresh shape."""
    from OCP.BRepTools import BRepTools
    # Row.solid() is memoised, and OCC caches a triangulation on the shape,
    # so a second call at a different tolerance would silently return the
    # first mesh. Clear it and mean the tolerance that was asked for.
    BRepTools.Clean_s(solid.wrapped)
    verts, tris = solid.tessellate(tol, angle)
    P = np.array([[v.x, v.y, v.z] for v in verts], dtype=np.float32)
    T = np.array(tris, dtype=np.uint32)
    # area-weighted normals: the cross product's magnitude is twice the
    # triangle area, so accumulating it unnormalised weights by area
    n = np.zeros_like(P)
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    fn = np.cross(b - a, c - a)
    for k in range(3):
        np.add.at(n, T[:, k], fn)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    n = np.divide(n, ln, out=np.zeros_like(n), where=ln > 0)
    return P, T, n.astype(np.float32)


_MESH_CACHE = {}


def tessellate_row(row, tol=TESS_TOL_M, angle=TESS_ANGLE_RAD):
    """`tessellate` for a Row, memoised on (row, tolerance).

    Unit J3 asks each row for its mesh from five places -- volume fidelity,
    the envelope, containment, the glTF and the preview figure -- and a
    tessellation of these lofts costs about five seconds. Keyed on the
    tolerance as well as the row, so asking for a different tolerance still
    means it."""
    key = (row.name, tol, angle)
    if key not in _MESH_CACHE:
        _MESH_CACHE[key] = tessellate(row.solid(), tol, angle)
    return _MESH_CACHE[key]


def mesh_volume(P, T):
    """Signed volume by the divergence theorem -- one sixth of the sum of
    the scalar triple products of each triangle's vertices."""
    a, b, c = P[T[:, 0]].astype(np.float64), P[T[:, 1]].astype(np.float64), \
        P[T[:, 2]].astype(np.float64)
    return abs(float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum()) / 6.0)


def volume_fidelity(rows=None, tol=TESS_TOL_M):
    """The step-0 band: is the mesh still the part? Compared against the
    exact `Solid.Volume()`, which G1 in turn checks against F2's integral."""
    from geometry.blades import all_rows
    out = []
    for row in rows if rows is not None else all_rows():
        s = row.solid()
        P, T, _ = tessellate_row(row, tol)
        exact, mesh = s.Volume(), mesh_volume(P, T)
        out.append(dict(row=row.name, exact_m3=exact, mesh_m3=mesh,
                        err_pct=(mesh / exact - 1) * 100,
                        triangles=len(T), vertices=len(P)))
    return out


# ------------------------------------------------------------- placement

def axial_stations():
    """Where each row sits on J1's engine axis, in metres.

    Read through `publication.meridional.layout()` so that the two assumed
    offsets have exactly one home (unit J1 finding 159)."""
    from publication.meridional import layout, hpc_flowpath
    L = layout()
    CM = 0.01
    out = {}

    # fan and booster: the stacking axis is the datum, y = 0
    fan = {s["name"]: s for s in L["fan"]["stations"]}
    sa = [s for s in L["fan"]["stations"] if s["z_known"]][0]
    out["fan-rotor"] = sa["z"] * CM
    # the booster sits downstream of the fan; its own axial station was
    # never published, so it is placed at the fan station plus the fan
    # blade's own axial extent. Recorded as assumed, not measured.
    out["booster-rotor"] = None          # filled by `place_rows`

    # HPC: each row's leading edge from the flowpath CSV, on J1's axis
    hx = L["hpc"]["x0"] * CM
    for r in hpc_flowpath():
        if r["edge"] != "LE":
            continue
        name = ("hpc-rotor-" if r["row"].startswith("R") else
                "hpc-stator-" if r["row"].startswith("S") else None)
        if name is None:
            continue
        out[f"{name}{r['row'][1:]}"] = hx + r["z_hub"] * CM

    # LPT: the rows already carry their z from the HPT exit plane
    lx = L["lpt"]["x0"] * CM
    for n in range(1, 6):
        out[f"lpt-stator-{n}"] = lx
        out[f"lpt-rotor-{n}"] = lx
    return out


def place_rows(rows=None):
    """Every row with its axial offset and whether that offset is measured,
    assumed, or the row's own coordinates."""
    from geometry.blades import all_rows
    rows = rows if rows is not None else all_rows()
    st = axial_stations()
    by = {r.name: r for r in rows}
    fan = by.get("fan-rotor")
    out = []
    for row in rows:
        x = st.get(row.name)
        basis = "flowpath table"
        if row.name == "booster-rotor":
            # downstream of the fan by the fan blade's own axial extent
            x = st["fan-rotor"] + (fan.solid().BoundingBox().xlen if fan else 0.0)
            basis = "ASSUMED: fan station + fan axial extent; never published"
        elif row.name == "fan-rotor":
            basis = "fan report Fig 15 stacking axis (the engine datum)"
        elif row.name.startswith("lpt-"):
            basis = "the row's own z, measured from the HPT exit plane"
        elif row.name.startswith("hpc-"):
            basis = "HPC flowpath LE, on J1's axis across an ASSUMED offset"
        out.append(dict(row=row, x_m=x, basis=basis))
    return out


def blade_angles(row, cutaway=True):
    """The angular station of every blade that is DRAWN. Blades inside the
    cutaway wedge are omitted whole; none is ever clipped."""
    pitch = 360.0 / row.count
    out = []
    for i in range(row.count):
        a = (i * pitch) % 360.0
        if cutaway and CUTAWAY_FROM_DEG <= a < CUTAWAY_TO_DEG:
            continue
        out.append(a)
    return out


def blade_envelope(rows=None, tol=TESS_TOL_M):
    """Each row's meridional footprint in WORLD coordinates: the axial span
    and the radial span the lofted blade actually occupies once placed.

    This is the check that the render is the same engine as J1's flowpath.
    A blade that pokes through the casing or below the hub would be visible
    here and nowhere else -- G1 checks each row against its own sections,
    J1 draws the walls, and nothing until now has put the two together."""
    out = []
    for entry in place_rows(rows):
        row = entry["row"]
        P, _, _ = tessellate_row(row, tol)
        r = np.hypot(P[:, 1], P[:, 2])
        out.append(dict(row=row.name, spool=row.spool,
                        x_lo=float(P[:, 0].min()) + entry["x_m"],
                        x_hi=float(P[:, 0].max()) + entry["x_m"],
                        r_lo=float(r.min()), r_hi=float(r.max())))
    return out


def cap_overshoot(rows=None, tol=TESS_TOL_M):
    """How far each row's mesh reaches beyond its own tip section.

    G1 caps the lofted blade with `makeNSidedSurface`, which interpolates
    across the boundary wire and may bulge past it. The bulge scales with
    the cap: the fan, whose tip section is a 28 cm chord on a 104 cm
    radius, stands 3 mm proud, while every LPT row is exact. It is inside
    the 1 % volume band and it is still real geometry -- the render's
    outermost radius is not the aerodynamic tip radius (finding 163)."""
    out = []
    for e in place_rows(rows):
        row = e["row"]
        P, _, _ = tessellate_row(row, tol)
        r = np.hypot(P[:, 1], P[:, 2])
        out.append(dict(row=row.name,
                        section_tip_m=max(row.radii), mesh_tip_m=float(r.max()),
                        section_hub_m=min(row.radii), mesh_hub_m=float(r.min()),
                        overshoot_mm=(float(r.max()) - max(row.radii)) * 1000))
    return out


def containment(rows=None):
    """Do the HPC blades stay inside the HPC annulus J1 draws?

    Compared against the flowpath walls at each row's own axial station,
    interpolated from the same CSV J1 uses. The hub and casing are the
    aerodynamic walls, so a rotor tip should sit just below the casing
    (running clearance) and a stator hub just above the hub line."""
    from publication.meridional import hpc_flowpath, layout
    L = layout()
    hx, CM = L["hpc"]["x0"] * CM_, 0.01
    pts = sorted(((r["z_hub"] * CM + hx, r["r_hub"] * CM, r["r_tip"] * CM)
                  for r in hpc_flowpath()), key=lambda t: t[0])
    zs = [p[0] for p in pts]

    def wall(x):
        import bisect
        i = min(max(bisect.bisect_left(zs, x), 1), len(zs) - 1)
        (z0, h0, t0), (z1, h1, t1) = pts[i - 1], pts[i]
        f = 0.0 if z1 == z0 else (x - z0) / (z1 - z0)
        return h0 + f * (h1 - h0), t0 + f * (t1 - t0)

    out = []
    for e in blade_envelope(rows):
        if not e["row"].startswith("hpc-"):
            continue
        xm = (e["x_lo"] + e["x_hi"]) / 2
        hub, tip = wall(xm)
        out.append(dict(row=e["row"], r_lo=e["r_lo"], r_hi=e["r_hi"],
                        hub_m=hub, tip_m=tip,
                        below_hub_mm=(hub - e["r_lo"]) * 1000,
                        above_casing_mm=(e["r_hi"] - tip) * 1000))
    return out


# ------------------------------------------------------------ the GLB

def _pad(b, n=4, fill=b"\x00"):
    return b + fill * ((n - len(b) % n) % n)


def _kinematics():
    """How the two spools turn, for any viewer that animates the file."""
    return dict(
        rpm_lp=RPM_LP, rpm_hp=RPM_HP, ratio=round(RPM_HP / RPM_LP, 4),
        co_rotating=True,
        note=("Each row node carries extras.spool: lp, hp or static. "
              "Co-rotation at this ratio is a MODELLING DECISION recorded "
              "2026-09-03, not a published fact about the engine -- the "
              "reports read do not state the relative rotation direction. "
              "It turns; it does not run."))


def build_gltf(rows=None, cutaway=True, tol=TESS_TOL_M):
    """One mesh per row, one node per blade. Returns (json dict, bin blob)."""
    placed = place_rows(rows)
    blob = bytearray()
    buffer_views, accessors, meshes, nodes, materials = [], [], [], [], []
    mat_index = {}
    for spool, rgba in SPOOL_COLOUR.items():
        mat_index[spool] = len(materials)
        materials.append(dict(
            name=spool, pbrMetallicRoughness=dict(
                baseColorFactor=list(rgba), metallicFactor=0.65,
                roughnessFactor=0.42), doubleSided=False))

    def add_view(data, target):
        off = len(blob)
        blob.extend(data)
        blob.extend(b"\x00" * ((4 - len(blob) % 4) % 4))
        buffer_views.append(dict(buffer=0, byteOffset=off,
                                 byteLength=len(data), target=target))
        return len(buffer_views) - 1

    stats = []
    for entry in placed:
        row = entry["row"]
        P, T, N = tessellate_row(row, tol)
        v_view = add_view(P.tobytes(), 34962)
        n_view = add_view(N.tobytes(), 34962)
        # uint16 where the row's vertex count allows it -- lossless, and it
        # halves the index data. Every row qualifies at both tolerances this
        # project uses: the largest is 10,886 vertices at the archival
        # 0.6 mm and 5,846 at the web variant's 2 mm, against a uint16
        # ceiling of 65,536. The uint32 branch stays for a denser
        # tessellation than either.
        small = len(P) < 65536
        idx = T.astype(np.uint16 if small else np.uint32).ravel()
        i_view = add_view(idx.tobytes(), 34963)
        pos = len(accessors)
        accessors.append(dict(bufferView=v_view, componentType=5126,
                              count=len(P), type="VEC3",
                              min=P.min(axis=0).tolist(),
                              max=P.max(axis=0).tolist()))
        accessors.append(dict(bufferView=n_view, componentType=5126,
                              count=len(N), type="VEC3"))
        accessors.append(dict(bufferView=i_view,
                              componentType=5123 if small else 5125,
                              count=int(T.size), type="SCALAR"))
        meshes.append(dict(name=row.name, primitives=[dict(
            attributes=dict(POSITION=pos, NORMAL=pos + 1),
            indices=pos + 2, material=mat_index[row.spool], mode=4)]))
        mesh_i = len(meshes) - 1

        angles = blade_angles(row, cutaway)
        children = []
        for a in angles:
            # rotation about the engine axis, +X; glTF wants a quaternion
            h = math.radians(a) / 2.0
            children.append(len(nodes))
            nodes.append(dict(mesh=mesh_i, rotation=[math.sin(h), 0.0, 0.0,
                                                     math.cos(h)]))
        nodes.append(dict(name=row.name, children=children,
                          translation=[entry["x_m"], 0.0, 0.0],
                          extras=dict(spool=row.spool, blades=row.count,
                                      drawn=len(angles))))
        stats.append(dict(row=row.name, spool=row.spool, count=row.count,
                          drawn=len(angles), triangles=len(T),
                          x_m=entry["x_m"], basis=entry["basis"]))

    roots = [i for i, n in enumerate(nodes) if "children" in n]
    from publication.meridional import assumed_offsets
    off = assumed_offsets()
    gltf = dict(
        asset=dict(
            version="2.0",
            generator="PF-09 E3 reconstruction, solvers/publication/render.py",
            extras=dict(
                source="NASA/GE Energy Efficient Engine, public-domain reports",
                geometry="Stage G1: 32 rows lofted from the validated sections",
                cutaway=(f"{CUTAWAY_FROM_DEG:.0f}-{CUTAWAY_TO_DEG:.0f} deg "
                         "removed; blades omitted whole, never clipped"),
                axis="engine axis is +X; y = 0 at the fan rotor stacking axis",
                assumed_offsets={
                    k: dict(value_cm=off[k]["value_cm"],
                            allowable_cm=off[k]["range_cm"])
                    for k in ("fan_sa_to_hpc_r1_le", "hpc_ogv_te_to_hpt_vane1")},
                kinematics=_kinematics(),
                assumed_offsets_note=(
                    "These two axial offsets are NOT published. Every artefact "
                    "in this project reads them from "
                    "data/engine-flowpath.yaml; see unit J1 finding 159."))),
        scene=0,
        # kinematics is repeated on the SCENE as well as in asset.extras:
        # three.js's GLTFLoader copies node and scene extras into userData
        # but not the asset block, so a viewer that reads only the runtime
        # object graph would otherwise never see it.
        scenes=[dict(nodes=roots, extras=dict(kinematics=_kinematics()))],
        nodes=nodes, meshes=meshes,
        accessors=accessors, bufferViews=buffer_views, materials=materials,
        buffers=[dict(byteLength=len(blob))])
    return gltf, bytes(blob), stats


def write_glb(path=None, rows=None, cutaway=True, tol=TESS_TOL_M):
    gltf, blob, stats = build_gltf(rows, cutaway, tol)
    js = _pad(json.dumps(gltf, separators=(",", ":")).encode("utf-8"), 4, b" ")
    bn = _pad(blob, 4)
    body = (struct.pack("<II", len(js), 0x4E4F534A) + js
            + struct.pack("<II", len(bn), 0x004E4942) + bn)
    glb = struct.pack("<III", 0x46546C67, 2, 12 + len(body)) + body
    path = Path(path or (EXPORTDIR / "e3-blading.glb"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(glb)
    return path, stats


def plot_blading(path=None, tol=TESS_TOL_M):
    """J1's meridional annulus with the actual lofted blades in it.

    Not decoration: this is the only view in the project where G1's solids,
    J1's walls and J3's placement are drawn on one axis, and a row in the
    wrong place is obvious here and invisible everywhere else."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from publication.meridional import hpc_flowpath, layout, lpt_flowpath

    L = layout()
    fig, ax = plt.subplots(figsize=(16, 5.6))

    # the walls, from J1
    hx = L["hpc"]["x0"]
    h = L["hpc"]["rows"]
    for key_z, key_r in (("z_hub", "r_hub"), ("z_tip", "r_tip")):
        ax.plot([r[key_z] + hx for r in h], [r[key_r] for r in h],
                color="0.15", lw=1.4, zorder=4)
    px = L["lpt"]["x0"]
    lp = L["lpt"]["rows"]
    for key_z, key_r in (("z_hub", "r_hub"), ("z_tip", "r_tip")):
        ax.plot([r[key_z] + px for r in lp], [r[key_r] for r in lp],
                color="0.15", lw=1.4, zorder=4)
    t = L["hpt"]
    for k in ("r_hub", "r_tip"):
        ax.plot([st["z"] + t["x0"] for st in t["stations"]],
                [st[k] for st in t["stations"]], color="0.15", lw=1.4, zorder=4)

    COL = {"lp": "#4a6db8", "hp": "#c78a3c", "static": "#8d9296"}
    for e in blade_envelope(tol=tol):
        x0, x1 = e["x_lo"] * 100, e["x_hi"] * 100
        r0, r1 = e["r_lo"] * 100, e["r_hi"] * 100
        ax.fill([x0, x1, x1, x0], [r0, r0, r1, r1], color=COL[e["spool"]],
                alpha=0.72, lw=0.6, edgecolor="0.25", zorder=3)

    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=COL[k], alpha=0.72, edgecolor="0.25",
                             label=v) for k, v in
                       (("lp", "LP spool"), ("hp", "HP spool"),
                        ("static", "stators and vanes"))],
              loc="upper right", fontsize=8.5, framealpha=0.95)
    ax.set_xlabel("axial position from the fan rotor stacking axis, cm")
    ax.set_ylabel("radius, cm")
    # the two places with no blading, and why -- both are source gaps
    ax.annotate("", xy=(L["hpc"]["x0"], 74), xytext=(34, 74),
                arrowprops=dict(arrowstyle="<->", color="#8a4f0a", lw=1.0))
    ax.text((34 + L["hpc"]["x0"]) / 2, 76,
            "fan frame and inlet duct — no blading here, and the\n"
            f"{L['hpc']['x0']:.0f} cm is ASSUMED, not published (finding 159)",
            ha="center", fontsize=7.6, color="#8a4f0a", linespacing=1.3)
    ax.text(t["x0"] + t["length"] / 2, 44,
            "HPT: walls but no blades.\nThe airfoil coordinates were\n"
            "never published — only throat\nand aspect ratio (finding 165)",
            ha="center", va="bottom", fontsize=7.6, color="#8c2f39",
            linespacing=1.3)
    ax.text((L["hpc"]["x0"] + 78 + t["x0"]) / 2, 14,
            "diffuser + combustor:\nundimensioned in Figs 1, 22, 79",
            ha="center", fontsize=7.6, color="0.4", linespacing=1.3)
    ax.set_title("E$^3$ blading — Stage G1's 32 lofted rows placed on unit J1's "
                 "engine axis.\nEvery HPC row lands on the published annulus "
                 "wall to within 0.8 mm. Where there is no blading, no report "
                 "gave the geometry.", fontsize=10.5)
    ax.set_ylim(0, 112)
    ax.set_aspect("equal")
    ax.grid(alpha=0.22, lw=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()
    path = Path(path or (FIGDIR / "blading-meridional.png"))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def write_web_glb(path=None, tol=WEB_TOL_M):
    """The site variant: coarser, smaller, and held to its own stated band.

    The archival file is tessellated to 1 % of each row's volume. This one
    is 2 mm and 2 %, which halves the triangles for a page that has to
    download it. Writing it as a separate artefact with a separate band is
    the point -- the alternative is quietly loosening the archival
    tolerance and shipping one file that meets neither claim."""
    return write_glb(path, cutaway=True, tol=tol)


def web_fidelity(tol=WEB_TOL_M):
    """Does the site variant hold ITS band?"""
    v = volume_fidelity(tol=tol)
    return dict(rows=len(v), worst_pct=max(abs(r["err_pct"]) for r in v),
                band_pct=WEB_BAND_PCT, triangles=sum(r["triangles"] for r in v),
                inside=all(abs(r["err_pct"]) <= WEB_BAND_PCT for r in v))


def summary():
    _, _blob, stats = build_gltf()
    drawn = sum(s["drawn"] for s in stats)
    total = sum(s["count"] for s in stats)
    tri = sum(s["triangles"] for s in stats)
    L = ["Stage J unit J3 -- the render", ""]
    L.append(f"   {len(stats)} rows, {total} blades, {drawn} drawn after the "
             f"{CUTAWAY_TO_DEG - CUTAWAY_FROM_DEG:.0f}-degree cutaway")
    L.append(f"   {len(stats)} meshes instanced by {drawn} nodes -- "
             f"{tri:,} triangles stored, {tri * drawn // max(len(stats),1):,} drawn")
    L += ["", f"   {'row':<18}{'spool':>8}{'n':>5}{'drawn':>7}{'tris':>9}{'x cm':>9}"]
    for s in stats:
        L.append(f"   {s['row']:<18}{s['spool']:>8}{s['count']:>5}{s['drawn']:>7}"
                 f"{s['triangles']:>9}{s['x_m'] * 100:>9.2f}")
    return "\n".join(L)


if __name__ == "__main__":
    print(summary())
    root = Path(__file__).resolve().parents[2]
    p, stats = write_glb()
    print(f"\n   wrote {p.relative_to(root)}  {p.stat().st_size / 1e6:.1f} MB")
    print(f"   wrote {plot_blading().relative_to(root)}")

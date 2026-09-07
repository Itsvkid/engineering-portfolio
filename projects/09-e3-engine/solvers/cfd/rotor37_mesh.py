"""Stage C4 unit 3: the Rotor 37 mesh.

One blade passage of thirty-six, so a 10-degree sector with cyclic sides.

The background mesh is **body-fitted to the annulus**: the hub and casing
are surfaces of revolution and their radii are printed against axial
distance (TP-1337 fig 1(a)), so a blockMesh whose radial extent follows
them at every axial station needs no snapping on those walls at all. That
leaves snappyHexMesh with one job -- the blade -- instead of three, which
matters because the blade sits in a passage whose walls it nearly touches:
the running tip clearance is 0.356 mm against a 74 mm span.

Everything here is generated from the transcribed geometry. Nothing is
drawn by hand. STEP0.md, unit C4-3."""
from __future__ import annotations

import math
from pathlib import Path

from cfd.rotor37 import (IN, blade_tip_radius, casing_at, hub_at, trimmed_solid)

BLADES = 36
SECTOR_DEG = 360.0 / BLADES
CM = 0.01

# domain: upstream of the blade to well downstream, inside the flow path's
# own tabulated range (-22.86 to +15.40 cm)
X_IN_CM = -4.0
X_OUT_CM = 10.64          # a printed flow-path station

# The MRF zone's axial extent, in cm. The hub is split on it: inside, the
# hub turns with the rotor; outside, it is a stationary duct wall. These
# must match system/topoSetDict's box.
MRF_X0_CM = -1.2
MRF_X1_CM = 5.6


def _rot(y, z, deg):
    a = math.radians(deg)
    return y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)


def stations(n=24):
    """axial stations, clustered where the blade is"""
    x0, x1 = X_IN_CM, X_OUT_CM
    blade_lo, blade_hi = 0.0, 4.39      # the blade's own axial extent, cm
    xs = set()
    for i in range(9):
        xs.add(x0 + (blade_lo - x0) * (i / 8) ** 1.4)
    for i in range(n // 2 + 1):
        xs.add(blade_lo + (blade_hi - blade_lo) * i / (n // 2))
    for i in range(1, 11):
        xs.add(blade_hi + (x1 - blade_hi) * (i / 10) ** 0.8)
    return sorted(xs)


def block_mesh_dict(n_theta=40, n_radial=60, path=None):
    """A body-fitted 10-degree annular sector: at every axial station the
    radial extent runs from the printed hub to the printed casing."""
    xs = stations()
    half = SECTOR_DEG / 2
    verts, idx = [], {}

    def add(x_cm, r_cm, deg):
        key = (round(x_cm, 6), round(r_cm, 6), round(deg, 6))
        if key not in idx:
            y, z = _rot(0.0, r_cm * CM, deg)
            idx[key] = len(verts)
            verts.append((x_cm * CM, y, z))
        return idx[key]

    blocks, arcs, faces_in, faces_out, faces_cas, faces_p, faces_m = \
        [], [], [], [], [], [], []
    # The hub is split. Only the part inside the MRF zone turns with the
    # rotor; upstream and downstream it is a stationary duct wall. Spinning
    # the whole 14.6 cm hub at 1800 rad/s while the MRF zone covers only the
    # 6.8 cm around the blade pumps swirl into the inlet duct with nothing
    # to balance it, and the solution converges to a stalled rotor doing no
    # work at all -- low residual, wrong answer.
    faces_hub_rot, faces_hub_static = [], []
    seen_arcs = set()
    for i, x in enumerate(xs):
        rh, rc = hub_at(x), casing_at(x)
        for deg in (-half, half):
            add(x, rh, deg)
            add(x, rc, deg)

    for i in range(len(xs) - 1):
        xa, xb = xs[i], xs[i + 1]
        ha, ca = hub_at(xa), casing_at(xa)
        hb, cb = hub_at(xb), casing_at(xb)
        # -half first. _rot puts +half at NEGATIVE y (it returns
        # y = -r sin(deg)), so this is the right-handed ordering:
        # (x_axial cross y_radial) . z_theta > 0. Checked numerically, not
        # argued -- the sign convention in _rot is easy to get backwards.
        v = [add(xa, ha, -half), add(xb, hb, -half), add(xb, cb, -half), add(xa, ca, -half),
             add(xa, ha, half), add(xb, hb, half), add(xb, cb, half), add(xa, ca, half)]
        nx = max(2, int(round((xb - xa) / 0.18)))
        blocks.append((v, nx))
        for (r0, x0v, r1, x1v, lst) in ((ha, xa, hb, xb, "hub"), (ca, xa, cb, xb, "cas")):
            pass
        # arcs: the circumferential edges are arcs of the true radius
        # Circumferential edges are arcs of the true radius. Adjacent
        # blocks SHARE these edges, so each must be emitted once: blockMesh
        # rejects the whole topology if an edge is defined twice, and it
        # says only "patch -> block consistency" when it does.
        for (xx, rr, va, vb) in ((xa, ha, v[0], v[4]), (xa, ca, v[3], v[7]),
                                 (xb, hb, v[1], v[5]), (xb, cb, v[2], v[6])):
            key = (min(va, vb), max(va, vb))
            if key in seen_arcs:
                continue
            seen_arcs.add(key)
            y, z = _rot(0.0, rr * CM, 0.0)      # the arc midpoint, at theta = 0
            arcs.append((va, vb, (xx * CM, y, z)))
        xm_block = 0.5 * (xa + xb)
        if MRF_X0_CM <= xm_block <= MRF_X1_CM:
            faces_hub_rot.append((v[0], v[1], v[5], v[4]))
        else:
            faces_hub_static.append((v[0], v[1], v[5], v[4]))
        faces_cas.append((v[3], v[7], v[6], v[2]))
        faces_m.append((v[0], v[3], v[2], v[1]))     # -half plane, local z-min
        faces_p.append((v[4], v[5], v[6], v[7]))     # +half plane, local z-max
    v0 = blocks[0][0]
    faces_in.append((v0[0], v0[4], v0[7], v0[3]))    # local x-min
    vN = blocks[-1][0]
    faces_out.append((vN[1], vN[2], vN[6], vN[5]))   # local x-max

    def fl(fs):
        return "\n".join("            (%d %d %d %d)" % f for f in fs)

    out = ["FoamFile{version 2.0; format ascii; class dictionary; object blockMeshDict;}",
           "", "scale 1;", "", "vertices", "("]
    out += ["    (%.9g %.9g %.9g)" % v for v in verts]
    out += [");", "", "blocks", "("]
    for v, nx in blocks:
        out.append("    hex (%d %d %d %d %d %d %d %d) (%d %d %d) simpleGrading (1 1 1)"
                   % (*v, nx, n_radial, n_theta))
    out += [");", "", "edges", "("]
    for va, vb, mid in arcs:
        out.append("    arc %d %d (%.9g %.9g %.9g)" % (va, vb, *mid))
    out += [");", "", "boundary", "("]
    for name, typ, fs in (("inlet", "patch", faces_in), ("outlet", "patch", faces_out),
                          ("hub_rotating", "wall", faces_hub_rot),
                          ("hub_static", "wall", faces_hub_static),
                          ("casing", "wall", faces_cas)):
        out += ["    %s" % name, "    {", "        type %s;" % typ,
                "        faces", "        (", fl(fs), "        );", "    }"]
    for name, nb, fs in (("periodic_m", "periodic_p", faces_m),
                         ("periodic_p", "periodic_m", faces_p)):
        # `cyclic`, not `cyclicAMI`. The two sector faces are generated
        # with identical divisions at identical radii, so they match
        # exactly after rotation and need no interpolation. An AMI here
        # leaves uncovered faces (weight 0) wherever snappy refines the two
        # sides differently, and an uncovered face returns T = 0, which the
        # thermophysical model then divides by -- a floating-point
        # exception during construction, before a single iteration.
        out += ["    %s" % name, "    {", "        type cyclic;",
                "        neighbourPatch %s;" % nb,
                "        transform rotational;",
                "        rotationAxis (1 0 0);", "        rotationCentre (0 0 0);",
                "        faces", "        (", fl(fs), "        );", "    }"]
    out += [");", "", "mergePatchPairs ();", ""]
    text = "\n".join(out)
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text)
    return text, dict(vertices=len(verts), blocks=len(blocks),
                      hub_rotating_blocks=len(faces_hub_rot),
                      hub_static_blocks=len(faces_hub_static),
                      cells=sum(nx for _, nx in blocks) * n_radial * n_theta,
                      x_in_cm=X_IN_CM, x_out_cm=X_OUT_CM, sector_deg=SECTOR_DEG)


def write_blade_stl(path=None, tol=1.0e-5):
    import cadquery as cq
    path = Path(path or (Path(__file__).resolve().parents[2] / "cfd" / "rotor37"
                         / "constant" / "triSurface" / "blade.stl"))
    path.parent.mkdir(parents=True, exist_ok=True)
    solid, _ = trimmed_solid()
    cq.exporters.export(cq.Workplane(obj=solid), str(path),
                        tolerance=tol, angularTolerance=0.1)
    return path, solid


# The three grid levels the GCI 3 % band needs. They are declared here
# rather than chosen later, so the refinement ratio is fixed before any of
# them is run: n_theta and n_radial go up by 1.5 each step, which is the
# r >= 1.3 that Roache's GCI wants.
GRIDS = {
    "coarse": dict(n_theta=26, n_radial=40, snappy=(1, 2)),
    "medium": dict(n_theta=40, n_radial=60, snappy=(2, 3)),
    "fine":   dict(n_theta=60, n_radial=90, snappy=(2, 4)),
}


def write_grid(level="medium", base=None):
    """blockMeshDict and snappyHexMeshDict for one of the three levels"""
    g = GRIDS[level]
    base = Path(base or (Path(__file__).resolve().parents[2] / "cfd" / "rotor37"))
    text, info = block_mesh_dict(n_theta=g["n_theta"], n_radial=g["n_radial"],
                                 path=base / "system" / "blockMeshDict")
    snap = (base / "system" / "snappyHexMeshDict")
    if snap.exists():
        t = snap.read_text()
        import re
        t = re.sub(r"level \(\d+ \d+\)", "level (%d %d)" % g["snappy"], t)
        snap.write_text(t)
    info["level"] = level
    info["snappy_levels"] = g["snappy"]
    return info


if __name__ == "__main__":
    import sys
    level = sys.argv[1] if len(sys.argv) > 1 else "medium"
    base = Path(__file__).resolve().parents[2] / "cfd" / "rotor37"
    info = write_grid(level, base)
    text = None
    print(f"Stage C4 unit 3: the Rotor 37 sector mesh, level '{info['level']}'\n")
    for k, v in info.items():
        print(f"   {k:<16}{v}")
    p, solid = write_blade_stl()
    print(f"\n   blade STL      {p.name}, {p.stat().st_size / 1e6:.1f} MB")
    print(f"   blade volume   {solid.Volume():.6e} m3")
    print(f"   tip clearance  {blade_tip_radius()['clearance_mm']:.3f} mm")

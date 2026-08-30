# Environment setup

macOS 26.6.1 · Apple Silicon (arm64) · **8 GB RAM · 8 cores**

## What the hardware means

The RAM is the binding constraint, and it shapes the project plan more than
anything else:

- **2D CFD is fine.** Project 05's airfoil case will run comfortably.
- **3D CFD locally is not.** A meshed 3D wing with inflation layers will thrash
  swap long before it converges. This is exactly why project 02 uses SimScale —
  the cloud run is not a shortcut, it is the right tool at this memory budget.
- **Keep an eye on disk.** ~26 GB free. OpenFOAM's image is 4–5 GB, so it is
  deliberately not installed yet (see below).

## Installed and verified

| Tool | Version | Used for |
|---|---|---|
| Homebrew | 6.0.12 | package management |
| Python (system) | 3.13.9 | project 03 |
| conda (Anaconda) | 25.7.0 | environment management, `/opt/anaconda3` |
| **pythonocc-core** | 7.9.0 (OCCT 7.9.0) | parametric geometry in code |
| FreeCAD | latest cask | project 04 |
| ParaView | brew | post-processing for 02 and 05 |
| gmsh | brew | meshing |
| OpenRocket | 24.12 | rocketry, learning |
| Docker | 29.1.3 | OpenFOAM host |
| colima | 0.10.3 | Docker VM on macOS (currently stopped) |
| Java | OpenJDK 11 | not needed by OpenRocket — it bundles its own JRE |
| PyCharm | 2026.1 | IDE |

Both `numpy` and `matplotlib` exist in the system Python *and* in `pyocc_env`.
That is intentional, not duplication — see below.

## Which Python to use

**Project 03 → system Python 3.13.9.** numpy 2.1.3, scipy 1.15.3,
matplotlib 3.10.0, pandas 2.2.3, pytest 8.3.4 are already present. Nothing to
install.

**Anything touching pyOCC → `conda activate pyocc_env`.** Python 3.10.15 with
pythonocc-core 7.9.0, numpy 2.2.6, scipy 1.15.2, matplotlib 3.10.9,
pytest 9.1.1.

The version split is deliberate: pythonocc-core is built against a specific
Python via conda-forge, and it has **no pip wheel** — it cannot be installed
into the system Python at all. Do not try to unify them.

Verify the geometry kernel at any time:

```bash
conda run -n pyocc_env python -c "
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepGProp import brepgprop
box = BRepPrimAPI_MakeBox(10.,20.,30.).Shape()
p = GProp_GProps(); brepgprop.VolumeProperties(box, p)
assert abs(p.Mass() - 6000.0) < 1e-6
print('pythonocc OK')"
```

A duplicate `pyocc-env` was removed to reclaim space. If PyCharm shows a broken
interpreter, re-point the project at `/opt/anaconda3/envs/pyocc_env/bin/python`.

## Tooling notes

**XFLR5** — installed, `/Applications/xflr5.app`, **v6.62** (released
2026-03-24). Still not in Homebrew: the build came from the project's
SourceForge, which is where <https://www.xflr5.tech> points, not from the
website directly.

```bash
curl -L -o xflr5_v6.62.dmg \
  "https://sourceforge.net/projects/xflr5/files/6.62/xflr5_v6.62.dmg/download"
hdiutil attach xflr5_v6.62.dmg -readonly -nobrowse -mountpoint /tmp/xflr5mnt
cp -R /tmp/xflr5mnt/xflr5.app /Applications/ && hdiutil detach /tmp/xflr5mnt
```

Two things this file used to say that are no longer true. The macOS build is
**arm64-native**, not Intel — no Rosetta. And it is **signed and notarized**
("Developer ID Application: Andre Deperrois", `spctl` returns
`source=Notarized Developer ID`), so the quarantine workaround this note used
to give is unnecessary — it opens by double-click like any other app. Verify
before trusting that, since it is a claim about a downloaded binary:

```bash
spctl -a -vv -t exec /Applications/xflr5.app
```

**What it is for, now that project 01 does not need it.** Project 01 was built
as a from-scratch panel method rather than driven through this GUI (see its
README for why), so nothing depends on XFLR5. It is useful as an *independent
numerical reference*: project 01 currently validates against closed-form
results and a second internal route to Cl, and XFLR5 gives a third, external
check on the same NACA 0012 / 4412 polars — which is exactly the standard this
repo sets in `README.md` ("a result without a reference is a picture"). It is
also the sane way to sanity-check an unfamiliar section before committing
solver time to it.

**OpenFOAM** — installed. `opencfd/openfoam-default:latest`, v2512, arm64
native under colima (`colima start --cpu 4 --memory 4 --disk 20`). Run cases
through `projects/05-openfoam-airfoil/foam.sh`, which works around the image's
login shell overriding docker's working directory.

> **Stop colima when you are not running a case: `colima stop`.**
>
> The VM reserves its memory whether or not anything is using it, and on
> 2026-08-27 it was found running with **6 GiB of this machine's 8 GB** and
> four CPUs allocated, with zero containers — which is most of the reason
> the machine had accumulated 1.27 million pageouts. Stopping it took system
> free memory from 38% to 47% instantly. `colima start` brings it back in
> about twenty seconds with the image still cached, so there is nothing to
> lose by stopping it between sessions.
>
> Note it was also running with more memory than the documented command
> asks for (6 GiB against `--memory 4`) — colima persists whatever it was
> last configured with, so check `colima list` rather than trusting the
> flags in this file.

Original note, kept for the reasoning: it was deferred on purpose. It is last in the build order
and costs 4–5 GB, which is better spent free while working on 03 and 04. When
you reach it:

```bash
colima start --cpu 4 --memory 4 --disk 20   # sized for 8 GB RAM
docker pull opencfd/openfoam-default
```

Check the image is arm64-native before committing to it — an amd64 image runs
under emulation on Apple Silicon and is several times slower, which matters
when a case takes hours.

Stop the VM when you are done to get the RAM back: `colima stop`.

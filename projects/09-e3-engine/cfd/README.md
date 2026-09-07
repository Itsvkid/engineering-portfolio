# Stage C4 — CFD

Everything here is reproducible from a clean clone. Nothing depends on a
particular machine, account or session.

## What is committed, and what is not

**Committed** — the inputs:

| Path | What |
|---|---|
| `rotor37/system/` | `controlDict`, `fvSchemes`, `fvSolution`, `snappyHexMeshDict`, `topoSetDict` |
| `rotor37/constant/thermophysicalProperties` | air, perfect gas, Sutherland |
| `rotor37/constant/turbulenceProperties` | k-omega SST |
| `rotor37/constant/MRFProperties` | the rotating frame, 1799.9965 rad/s |
| `rotor37/0.orig/` | the boundary and initial conditions |
| `run_shocktube.sh` | the C4-1 validation case |

**Not committed** — everything generated, because it is large and
reproducible: `constant/polyMesh/`, `constant/triSurface/blade.stl`,
`system/blockMeshDict`, `log.*`, and the time directories.

## Reproducing it

Needs a Docker daemon. On the machine this was built on that is **colima**,
not Docker Desktop:

```bash
colima start
docker pull opencfd/openfoam-default:2406      # native arm64
```

Then:

```bash
# 1. the solver, validated against an exact answer first (unit C4-1)
./cfd/run_shocktube.sh
(cd solvers && python -m cfd.shocktube)        # star pressure to 0.02 %

# 2. the blade and the mesh (units C4-2, C4-3)
(cd solvers && python -m cfd.rotor37)          # geometry checks
(cd solvers && python -m cfd.rotor37_mesh)     # writes blockMeshDict + blade.stl
cd cfd/rotor37
docker run --rm -v "$PWD":/work opencfd/openfoam-default:2406 bash -lc '
  cd /work && blockMesh && snappyHexMesh -overwrite && checkMesh && topoSet'

# 3. the solve (unit C4-4, in progress)
docker run --rm -v "$PWD":/work opencfd/openfoam-default:2406 bash -lc '
  cd /work && rm -rf 0 && cp -r 0.orig 0 && rhoSimpleFoam'
```

**colima mounts `$HOME` only.** A case directory outside `$HOME` is
invisible to the container — which is why these live in the repo and not
in a temp directory.

## Toolchain gotchas, all found the hard way

| Symptom | Cause |
|---|---|
| `blockMesh: patch -> block consistency` | an **edge defined twice**. Adjacent blocks share circumferential edges; emit each arc once. The message names the wrong thing entirely |
| `blockMesh: block ... is inside-out` | left-handed hex. Check numerically: this sector's `_rot` puts **+θ at negative y**, so the right-handed order is the opposite of what the sign of the angle suggests |
| FPE inside `libfluidThermophysicalModels`, before iteration 1 | `cyclicAMI` with uncovered faces (`sum(weights) min:0`). An uncovered face returns T = 0 and the thermo divides by it. Use plain `cyclic` for an exactly-matching sector |
| `Unknown patchField type MRFnoSlip` | not in this build. Under MRF use `noSlip` on all walls and list the stationary ones in `nonRotatingPatches` |
| `cannot find file constant/turbulenceProperties` | ESI OpenFOAM wants `turbulenceProperties`; `momentumTransport` is the Foundation's name |
| `Missing or invalid Function1 entry: omega` | `MRFProperties` wants `omega` in rad/s, not `rpm` |
| `Entry 'gamma' not found` in `0/T` | the `totalTemperature` BC needs an explicit `gamma 1.4` |
| `cannot find file /root/system/controlDict` | `bash -lc` in this image starts in `/root`; `cd /work` explicitly, `-w` is not enough |

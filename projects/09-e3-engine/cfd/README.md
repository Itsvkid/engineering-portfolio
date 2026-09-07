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
| `rotor37/constant/triSurface/blade.stl` | the trimmed blade, 5.4 MB — kept **deliberately**, so a new session can mesh without a working CAD kernel. `python -m cfd.rotor37_mesh` regenerates it |

**Not committed** — everything else that is generated, because it is large
and reproducible: `constant/polyMesh/` (~100 MB), `system/blockMeshDict`,
`log.*`, the time directories, and any `core` dump. OpenFOAM writes a
~250 MB `core` beside the case whenever a solver takes a floating-point
exception, which during setup is often; it is gitignored, and GitHub will
reject a push that contains one.

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
| `decomposeParDict specifies N but job started with M ranks` | set `numberOfSubdomains` from the same variable as `mpirun -np`. `run_parallel.sh` does |
| ExecutionTime far below ClockTime | virtiofs. Run the case on the container's own filesystem, write only the **log** to the host |
| Run killed for memory | 8 GB host, 6 GB VM. 455k cells 4-way does not fit; the coarse grid level does |

### The MRF traps, which is where most of the time went

None of these produce an error. They produce a **converged, plausible,
wrong answer**, and the only thing that gives them away is a physical
quantity — here the outlet temperature, which must exceed the inlet
because a compressor compresses.

| Symptom | Cause |
|---|---|
| T_out **below** T_in; no work at all | walls set `noSlip`. Under MRF the solution variable is the *absolute* velocity, so a wall turning with the frame needs `rotatingWallVelocity` (`MRFnoSlip` does not exist in this build) |
| T_out still below T_in, mass flow 11× low | the **MRF cellZone spanned the whole domain including the inlet patch**, so the frame gave the incoming flow ~400 m/s of tangential velocity before `totalPressure` was evaluated |
| Mass flow collapses to a quarter of design, residual falls to 0.03 | the **rotating wall patch spanned the whole duct** while the MRF zone covered only the passage — 4 cm of stationary-frame inlet duct with a wall spinning at 1800 rad/s, pumping swirl into the approach flow. Split the hub at the zone boundary: `hub_rotating` inside, `hub_static` outside |

Each masked the next. Instrument the case with the quantity you are
validating against **before** trusting any residual.

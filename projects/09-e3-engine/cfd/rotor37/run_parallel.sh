#!/usr/bin/env bash
# Stage C4 unit 4: run Rotor 37.
#
# Two things this script exists to get right.
#
# 1. The CASE runs on the container's own filesystem, not the host mount.
#    colima mounts the host over virtiofs and OpenFOAM's parallel field I/O
#    across it is pathological: a first attempt reported ExecutionTime 433 s
#    against ClockTime 12,664 s -- 29x more wall clock than CPU, the solver
#    idle on I/O the whole time.
#
# 2. The LOG is written straight to the host so the run can be watched while
#    it happens. It is a small text file appended line by line, so it costs
#    nothing across the mount, and without it there is no way to see a run
#    go wrong until it ends.
set -euo pipefail
NP=${NP:-2}
IMAGE=${IMAGE:-opencfd/openfoam-default:2406}
HERE="$(cd "$(dirname "$0")" && pwd)"

# keep decomposeParDict and the launch consistent -- a mismatch is fatal
# two minutes in, and it is set here rather than inside the container so
# the committed dict always says what was actually run
sed -i.bak "s/^numberOfSubdomains.*/numberOfSubdomains $NP;/" "$HERE/system/decomposeParDict"
rm -f "$HERE/system/decomposeParDict.bak"
rm -f "$HERE"/log.*

docker run --rm -v "$HERE":/host "$IMAGE" bash -lc "
  set -e
  rm -rf /tmp/case && mkdir -p /tmp/case && cd /tmp/case
  cp -r /host/system /host/constant /host/0.orig .
  cp -r 0.orig 0
  decomposePar > /host/log.decompose 2>&1
  mpirun --allow-run-as-root -np $NP rhoSimpleFoam -parallel > /host/log.solve 2>&1 || true
  reconstructPar -latestTime > /host/log.reconstruct 2>&1 || true
  for d in \$(ls -d [0-9]* 2>/dev/null | grep -v '^0\$' | tail -1); do
    cp -r \$d /host/ || true
  done
"
echo "iterations: $(grep -cE '^Time = ' "$HERE/log.solve" 2>/dev/null || echo 0)"
grep ExecutionTime "$HERE/log.solve" 2>/dev/null | tail -1 || true

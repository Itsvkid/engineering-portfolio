#!/usr/bin/env bash
# Stage C4 unit 1: the Sod shock tube in OpenFOAM, for the exact-Riemann check.
#
# Needs a Docker daemon. On this machine that is colima, not Docker Desktop:
#     colima start
# and the OpenFOAM image, which is native arm64:
#     docker pull opencfd/openfoam-default:2406
#
# colima mounts $HOME, so the case must live under $HOME -- which is why it
# is here in the repo (gitignored) and not in a temp directory.
set -euo pipefail
IMAGE=${IMAGE:-opencfd/openfoam-default:2406}
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HERE/run"
docker run --rm -v "$HERE/run":/work -w /work "$IMAGE" bash -lc '
  rm -rf /work/shockTube
  cp -r $FOAM_TUTORIALS/compressible/rhoCentralFoam/shockTube /work/shockTube
  cd /work/shockTube && ./Allrun > allrun.log 2>&1
  echo "rhoCentralFoam exit $?"
  ls -d [0-9]* | tail -1
'
echo "compare with the exact solution:"
echo "    (cd solvers && python -m cfd.shocktube)"

#!/usr/bin/env bash
# Mirror the E3 reference set locally.
#
#   ./fetch-sources.sh
#
# Everything fetched here is a US Government work (NASA NTRS -- public domain,
# "Work of the US Gov. Public Use Permitted") or a civil aviation authority's
# openly published type-acceptance document. Nothing is behind a paywall and
# nothing is obtained without permission.
#
# PDFs are gitignored; this script is the reproducible artefact, not the
# binaries -- the same convention as the STEP exports elsewhere in this
# portfolio and the reference library in the study vault.
#
# These are SCANNED documents. Text extraction will not work on them; they
# have to be read as page images. That is why digitising the flowpath is its
# own phase in WORK-PLAN.md rather than an afternoon's work.

set -uo pipefail
cd "$(dirname "$0")" || exit 1
mkdir -p sources
cd sources || exit 1

UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

get() {  # get <filename> <url>
  if [ -s "$1" ]; then
    printf '  = %-44s (have it)\n' "$1"; return
  fi
  if curl -sS -L -A "$UA" --max-time 600 --fail -o "$1.part" "$2" 2>/dev/null \
     && [ "$(file -b --mime-type "$1.part")" = "application/pdf" ]; then
    mv "$1.part" "$1"
    printf '  + %-44s %s\n' "$1" "$(du -h "$1" | cut -f1)"
  else
    rm -f "$1.part"
    printf '  ! %-44s FAILED\n' "$1"
  fi
}

ntrs() {  # ntrs <filename> <ntrs-id>
  get "$1" "https://ntrs.nasa.gov/api/citations/$2/downloads/$2.pdf"
}

echo "NASA E3 programme -- primary source"
# The one this project is built on: whole-engine design, cycle, weights,
# clearances, and cross-sections of every component including the sumps.
ntrs e3-fps-final-design-CR-168219.pdf          19900019242

echo
echo "NASA E3 programme -- component detail reports"
ntrs e3-hp-compressor-detail-design.pdf         19850002690
ntrs e3-hp-turbine-hardware-CR-167955.pdf       19850002687
ntrs e3-lp-turbine-hardware.pdf                 19850002686
ntrs e3-preliminary-design-CR-135444.pdf        19780023165
ntrs e3-core-design-and-performance.pdf         19900019243

echo
echo "NASA design methods -- the textbooks that are public domain"
# Johnsen & Bullock, 1965. The compressor design method: diffusion factor,
# cascade data, radial equilibrium, loss and deviation, stall. Still the
# reference everything since is measured against.
ntrs nasa-sp36-axial-compressor-design.pdf         19650013744

echo
echo "GE90 -- context only, never a geometry source"
get ge90-100-type-acceptance-NZ.pdf \
  "https://www.aviation.govt.nz/assets/aircraft/type-acceptance-reports/Gen_Electric_GE90-100_Series.pdf"

echo
echo "Done. See REFERENCES.md for what each document gives, with page numbers."
echo "Note: NTRS occasionally rate-limits. Re-run -- files already present are skipped."

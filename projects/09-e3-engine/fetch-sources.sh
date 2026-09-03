#!/usr/bin/env bash
# Mirror every reference this project runs on. 41 documents, grouped by the
# discipline that uses them; REFERENCES.md says what each one gives and
# DATA-INDEX.md says what has been transcribed from it.
#
# Hosts that misbehave: NTRS rate-limits bulk runs (re-run; present files
# are skipped). DTIC (apps.dtic.mil) has maintenance windows that redirect
# every URL to a landing page -- the two AGARD documents come from there
# and simply need a later re-run.
#
#   ./fetch-sources.sh            # fetch what is missing
#   ./fetch-sources.sh --check    # list what is present and what is not
#
# Everything here is a US Government work (NASA NTRS, NACA -- public domain,
# "Work of the US Gov. Public Use Permitted"), a US DoD handbook released
# for public distribution (MIL-HDBK-5J), a UK Aeronautical Research Council
# report hosted openly by Cranfield's AERADE archive, a NATO AGARD/STO
# publication released to the public, an openly published regulation, or
# MIT OpenCourseWare (CC BY-NC-SA). Nothing is paywalled and nothing is
# obtained without permission. The textbooks that matter are cited in
# REFERENCES.md with the legitimate route to each.
#
# PDFs are gitignored; this script is the reproducible artefact. Most of the
# NASA reports are SCANNED -- read them as page images.

set -uo pipefail
cd "$(dirname "$0")" || exit 1
mkdir -p sources
cd sources || exit 1

CHECK=0; [ "${1:-}" = "--check" ] && CHECK=1
UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
have=0; got=0; failed=0

get() {  # get <filename> <url>
  if [ -s "$1" ]; then
    printf '  = %-52s %6s\n' "$1" "$(du -h "$1" | cut -f1)"; have=$((have+1)); return
  fi
  if [ $CHECK = 1 ]; then printf '  ! %-52s MISSING\n' "$1"; failed=$((failed+1)); return; fi
  if curl -sS -L -A "$UA" --max-time 900 --fail -o "$1.part" "$2" 2>/dev/null \
     && is_pdf "$1.part"; then
    mv "$1.part" "$1"
    printf '  + %-52s %6s\n' "$1" "$(du -h "$1" | cut -f1)"; got=$((got+1))
  else
    rm -f "$1.part"
    printf '  ! %-52s FAILED\n' "$1"; failed=$((failed+1))
  fi
}

# A download is a PDF if "%PDF" appears in its first 4 KB. Not `file
# --mime-type`: NASA's 1950s NACA scans carry a few hundred bytes of
# header junk before the %PDF marker, which makes `file` call a perfectly
# good 227-page document application/octet-stream and threw two of them
# away on the first run. Readers tolerate the junk; the check must too.
is_pdf() { head -c 4096 "$1" | grep -aq '%PDF'; }
ntrs() { get "$1" "https://ntrs.nasa.gov/api/citations/$2/downloads/$2.pdf"; }

echo "E3 programme -- the engine being rebuilt"
ntrs e3-fps-final-design-CR-168219.pdf              19900019242
ntrs e3-fps-preliminary-analysis-CR-159584.pdf      19810013521
ntrs e3-preliminary-design-CR-135444.pdf            19780023165
ntrs e3-fan-hardware-design-CR-165148.pdf           19830008070
ntrs e3-fan-quarter-stage-performance.pdf           19850025828
ntrs e3-hp-compressor-detail-design.pdf             19850002690
ntrs e3-combustor-hardware-design.pdf               19900019238
ntrs e3-hp-turbine-hardware-CR-167955.pdf           19850002687
ntrs e3-hp-turbine-cooling-model.pdf                19810018555
ntrs e3-lp-turbine-hardware.pdf                     19850002686
ntrs e3-controls-and-accessories.pdf                19850021645
ntrs e3-component-development-vol2-appA.pdf         19850002683
ntrs e3-core-design-and-performance.pdf             19900019243
ntrs e3-icls-design-and-performance-CR-168211.pdf   19900019245

echo
echo "Design methods -- public-domain textbooks"
ntrs nasa-sp36-axial-compressor-design.pdf          19650013744
ntrs nasa-sp290-turbine-design-vol1-2-3.pdf         19950015924
ntrs naca-tn3916-65-series-cascade-tests.pdf        19930084843
ntrs naca-tn3806-65-series-rotor-vs-cascade.pdf     19930084578
get  arc-rm2974-ainley-mathieson-turbine-loss.pdf \
  "https://reports.aerade.cranfield.ac.uk/bitstream/handle/1826.2/3538/arc-rm-2974.pdf?sequence=1&isAllowed=y"
get  agard-ls167-blading-design-axial-turbomachines.pdf \
  "https://apps.dtic.mil/sti/tr/pdf/ADA211103.pdf"
B="https://ocw.mit.edu/courses/16-50-introduction-to-propulsion-systems-spring-2012"
get  mit16-50-lec29.pdf "$B/42237291b6fe3a5ec7122058e72e8c97_MIT16_50S12_lec29.pdf"
get  mit16-50-lec31-compressor-turbine-matching.pdf "$B/d274f4ab2b1bd47c05a3cdb1c43e9e33_MIT16_50S12_lec31.pdf"

echo
echo "Validation test cases -- prove the method before applying it to the E3"
ntrs nasa-tp1337-rotor37-design-and-performance.pdf 19780025165
ntrs nasa-rotor37-cfd-code-validation.pdf           20100029589
ntrs nasa-tp2879-rotor67-laser-anemometer.pdf       19900001929

echo
echo "Thermal -- cooling and secondary air"
ntrs nasa-tp2232-internal-cooling-heat-transfer-review.pdf 19840013760
ntrs nasa-tmx52801-turbine-cooling-limits-and-future.pdf   19700018642
ntrs nasa-tmx2791-internal-air-cooling.pdf                 19730016202
ntrs nasa-cooling-methods-first-principles.pdf             20030064309
ntrs nasa-full-coverage-film-cooling-study.pdf             19760011294
ntrs nasa-turbomachine-sealing-secondary-flows.pdf         20040086723

echo
echo "Mechanical -- vibration, life, attachments"
ntrs nasa-bladed-disk-vibration.pdf                 19870017475
ntrs nasa-mistuned-bladed-disk-flutter.pdf          19840015855
ntrs nasa-hot-section-fatigue-life-prediction.pdf   19880005071
ntrs nasa-blade-root-fretting-single-crystal.pdf    20000033269
get  nato-en-avt-207-10-blade-hcf-campbell.pdf \
  "https://publications.sto.nato.int/publications/STO%20Educational%20Notes/RTO-EN-AVT-207/EN-AVT-207-10.pdf"

echo
echo "Materials"
# DoD handbook, distribution unlimited. Design allowables for Ti-6Al-4V,
# Ti-8Al-1Mo-1V, Inconel 718 and the rest, with temperature curves.
get  mil-hdbk-5j-metallic-materials.pdf \
  "https://archive.org/download/milhdbk-5-j/MILHDBK5J.pdf"

echo
echo "Combustion"
get  agard-cp422-combustion-and-fuels.pdf "https://apps.dtic.mil/sti/tr/pdf/ADA202495.pdf"

echo
echo "Certification -- the regulations themselves"
get  easa-cs-e-amendment-8.pdf "https://www.easa.europa.eu/en/downloads/141875/en"
get  faa-14cfr-part33-engines.pdf \
  "https://www.govinfo.gov/content/pkg/CFR-2024-title14-vol1/pdf/CFR-2024-title14-vol1-part33.pdf"

echo
echo "GE90 -- context only, never a geometry source"
get  ge90-100-type-acceptance-NZ.pdf \
  "https://www.aviation.govt.nz/assets/aircraft/type-acceptance-reports/Gen_Electric_GE90-100_Series.pdf"

echo
printf 'present %d  fetched %d  failed %d  total %s\n' "$have" "$got" "$failed" "$(du -sh . | cut -f1)"
[ $failed = 0 ] || { echo "Re-run for the failures; hosts rate-limit. Files present are skipped."; exit 1; }

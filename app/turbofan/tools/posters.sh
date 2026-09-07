#!/bin/zsh
# Render the atlas posters, figures and social card from a production build.
# Usage: from the repo root, `zsh app/turbofan/tools/posters.sh`. Needs
# Microsoft Edge (see cdp.mjs). Renders run one at a time on purpose.
set -e
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
OUT=${OUT:-/tmp/atlas-posters}; mkdir -p "$OUT"
cd "$ROOT"
pkill -f "next dev" || true; pkill -f "next start" || true; sleep 1
npx next build > "$OUT/build.log" 2>&1 || { echo "BUILD FAILED, see $OUT/build.log"; exit 1; }
(npx next start -p 3100 > /dev/null 2>&1 &)
until curl -s -o /dev/null http://localhost:3100/turbofan; do sleep 1; done
# One render, one browser, one attempt. An earlier version retried three
# times and left the failed Edge instance running each time; after a few
# failures dozens of them were competing for the software GPU and every
# render timed out, so the script hung for hours having produced two files.
# If a render fails now, the script says so and moves on; run it again for
# the ones that failed.
render() { # name query [W H]
  local name=$1 query=$2 W=${3:-1600} H=${4:-1000}
  W=$W H=$H node "$ROOT/app/turbofan/tools/cdp.mjs" "http://localhost:3100/turbofan?ui=0&$query" "$OUT/$name.png" "wait:6000" "eval:window.dispatchEvent(new Event('resize'))" "wait:2500" > /dev/null 2>&1 || true
  pkill -f "Microsoft Edge.*edge-cdp" 2>/dev/null || true
  local size=$(stat -f %z "$OUT/$name.png" 2>/dev/null || echo 0)
  if [ "$size" -gt 20000 ]; then echo "$name ok ($size)"; else echo "$name FAILED ($size bytes) — rerun"; fi
}
render cutaway-dark "theme=dark&camera=iso"
render cutaway-light "theme=light&camera=iso"
render fan-dark "theme=dark&part=fan-blades&camera=front"
render fan-light "theme=light&part=fan-blades&camera=front"
render exploded-dark "theme=dark&sep=0.5&cut=0&shell=0.25&camera=iso"
render exploded-light "theme=light&sep=0.5&cut=0&shell=0.25&camera=iso"
render rows-dark "theme=dark&systems=gas-generator&cut=0&cam=2.8,1.1,1.3&at=3.15,0.25,0"
render rows-light "theme=light&systems=gas-generator&cut=0&cam=2.8,1.1,1.3&at=3.15,0.25,0"
render og "theme=dark&camera=iso" 1200 630
# Only copy what actually rendered.
P="$ROOT/public"
copy() { [ "$(stat -f %z "$OUT/$1" 2>/dev/null || echo 0)" -gt 20000 ] && cp "$OUT/$1" "$2"; }
cp "$OUT/cutaway-dark.png" $P/figures/turbofan-atlas-cutaway-dark.png; cp "$OUT/cutaway-light.png" $P/figures/turbofan-atlas-cutaway.png
cp "$OUT/fan-dark.png" $P/figures/turbofan-atlas-fan-dark.png; cp "$OUT/fan-light.png" $P/figures/turbofan-atlas-fan.png
cp "$OUT/exploded-dark.png" $P/figures/turbofan-atlas-exploded-dark.png; cp "$OUT/exploded-light.png" $P/figures/turbofan-atlas-exploded.png
cp "$OUT/rows-dark.png" $P/figures/turbofan-atlas-rows-dark.png; cp "$OUT/rows-light.png" $P/figures/turbofan-atlas-rows.png
cp "$OUT/og.png" $P/turbofan-og.png
pkill -f "next start" || true
echo "POSTERS DONE"

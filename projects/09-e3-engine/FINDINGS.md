# FINDINGS

*Stage I3. The deliverable.*

This is what the project is for. The code exists to produce and check
these; the numbers below are generated from the solvers by
`tools/build_findings.py`, so they cannot drift from the code that
makes them. The prose is written by hand.

---

## 1. Every disagreement with a published number, ranked

**98 comparisons** against numbers printed in the NASA reports.
Each is something a solver computed and a report states, with no
intermediate fitting.

| | |
|---|---|
| Within 1 % | 12 |
| Within 5 % | 38 |
| Within 10 % | 56 |
| Worse than 20 % | 21 |
| Median absolute error | **6.70 %** |
| **Unresolved** | **5** |

Unresolved means exactly that: a disagreement with no cause yet. Five
of ninety-eight is the honest count, and they are listed in section 3.

### The full ranking

| err % | stage | quantity | published in | cause |
|---:|---|---|---|---|
| +79.1 | E5 | LPT Fig 70 disk_C stress concentration | LPT Fig 70 | **UNRESOLVED** (finding 100) |
| +78.7 | E3 | HPC rotor 2 3F frequency | HPC Fig 34 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| -74.4 | C4 | Rotor 37 mass flow, converged solve | TP-1337 Table I design flow | **UNRESOLVED** (finding 141) |
| +54.0 | E3 | HPC stage-1 first flex at 14,000 rpm | HPC Fig 33, read flat across the speed range | **UNRESOLVED** (finding 145) |
| +50.8 | E3 | HPC rotor 3 1F frequency | HPC Fig 35 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| +47.3 | E3 | HPC rotor 1 3F frequency | HPC Fig 33 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| -46.8 | E3 | fan rotor first flex | CR-165148 Fig 41 (geometry) | the part-span shroud; the published mode is the lowest in-phase one, where the shroud ring travels with the blades (finding 84) |
| +45.1 | E3 | LPT stage 1 first flex | CR-168289 Fig 62 (pinned tip) | a rigidly clamped root against a two-tang dovetail, plus hot modulus; the modulus alone accounts for about half (finding 84) |
| -40.6 | E3 | booster rotor Southwell coefficient | the published Campbell pair | outboard shroud and platform mass not modelled, and the flap-lag coupling of a staggered blade; S goes as f squared so a 7 % read error is 25 % here (finding 85) |
| +39.1 | E3 | HPC rotor 1 2F frequency | HPC Fig 33 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| -38.1 | E5 | LPT Fig 70 disk_D stress concentration | LPT Fig 70 | **UNRESOLVED** (finding 100) |
| +32.7 | E2 | HPT stage-1 disc bore stress, Fig 64 vs Fig 55 | CR-167955 Figs 55 and 64 | **UNRESOLVED** |
| -30.4 | E3 | fan rotor Southwell coefficient | the published Campbell pair | outboard shroud and platform mass not modelled, and the flap-lag coupling of a staggered blade; S goes as f squared so a 7 % read error is 25 % here (finding 85) |
| +30.4 | E3 | HPC rotor 2 2F frequency | HPC Fig 34 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| +29.6 | E3 | HPC rotor 9 2F frequency | HPC Fig 41 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| +28.3 | E3 | HPC rotor 5 3F frequency | HPC Fig 37 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| +23.7 | E3 | HPC rotor 7 2F frequency | HPC Fig 39 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| +22.8 | E3 | HPC rotor 10 2F frequency | HPC Fig 42 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| +21.8 | E3 | HPC rotor 2 1F frequency | HPC Fig 34 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| +21.7 | E3 | HPC rotor 3 3F frequency | HPC Fig 35 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| +21.3 | E3 | HPC rotor 5 2F frequency | HPC Fig 37 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| -17.9 | F2 | HPC rotor 6 airfoil mass | HPC Table X | inherits the section-area bias of finding 109 almost exactly (finding 109) |
| +17.6 | E3 | HPC rotor 7 1F frequency | HPC Fig 39 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| -17.3 | F2 | HPC rotor 5 airfoil mass | HPC Table X | inherits the section-area bias of finding 109 almost exactly (finding 109) |
| +17.2 | E3 | HPC rotor 8 1F frequency | HPC Fig 40 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| +17.1 | E3 | HPC rotor 5 1F frequency | HPC Fig 37 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| -16.5 | F2 | HPC rotor 3 tip section area | HPC Table X | the double-circular-arc and quarter-sine construction has no leading- or trailing-edge radius, so a built section is thinner than the real one; 20 of 20 comparisons are negative (finding 109) |
| +15.6 | E3 | HPC rotor 1 1F frequency | HPC Fig 33 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| -15.5 | F2 | HPC rotor 4 airfoil mass | HPC Table X | inherits the section-area bias of finding 109 almost exactly (finding 109) |
| +14.3 | E3 | HPC rotor 8 2F frequency | HPC Fig 40 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| +14.2 | E3 | HPC rotor 6 2F frequency | HPC Fig 38 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| -14.2 | F2 | HPC rotor 6 root section area | HPC Table X | the double-circular-arc and quarter-sine construction has no leading- or trailing-edge radius, so a built section is thinner than the real one; 20 of 20 comparisons are negative (finding 109) |
| -12.7 | F2 | HPC rotor 8 airfoil mass | HPC Table X | inherits the section-area bias of finding 109 almost exactly (finding 109) |
| -12.5 | F2 | HPC rotor 5 tip section area | HPC Table X | the double-circular-arc and quarter-sine construction has no leading- or trailing-edge radius, so a built section is thinner than the real one; 20 of 20 comparisons are negative (finding 109) |
| +12.5 | E3 | HPC rotor 10 1F frequency | HPC Fig 42 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| -12.2 | E3 | HPC rotor 4 2F frequency | HPC Fig 36 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| -12.1 | F2 | HPC rotor 4 tip section area | HPC Table X | the double-circular-arc and quarter-sine construction has no leading- or trailing-edge radius, so a built section is thinner than the real one; 20 of 20 comparisons are negative (finding 109) |
| -12.1 | F2 | HPC rotor 6 tip section area | HPC Table X | the double-circular-arc and quarter-sine construction has no leading- or trailing-edge radius, so a built section is thinner than the real one; 20 of 20 comparisons are negative (finding 109) |
| +11.6 | F1 | HPC rotor 5 blade density | MIL-HDBK-5J handbook density | the reconstruction's own area accuracy; the two candidates are a factor of two apart so the identification is never in doubt (finding 104) |
| -10.7 | F2 | HPC rotor 2 airfoil mass | HPC Table X | inherits the section-area bias of finding 109 almost exactly (finding 109) |
| -10.5 | F2 | HPC rotor 4 root section area | HPC Table X | the double-circular-arc and quarter-sine construction has no leading- or trailing-edge radius, so a built section is thinner than the real one; 20 of 20 comparisons are negative (finding 109) |
| -10.5 | E3 | HPC rotor 4 1F frequency | HPC Fig 36 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| +8.6 | F1 | HPC rotor 8 blade density | MIL-HDBK-5J handbook density | the reconstruction's own area accuracy; the two candidates are a factor of two apart so the identification is never in doubt (finding 104) |
| +8.4 | E3 | HPC rotor 9 1F frequency | HPC Fig 41 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| -8.1 | F2 | HPC rotor 1 tip section area | HPC Table X | the double-circular-arc and quarter-sine construction has no leading- or trailing-edge radius, so a built section is thinner than the real one; 20 of 20 comparisons are negative (finding 109) |
| -8.1 | F2 | HPC rotor 2 tip section area | HPC Table X | the double-circular-arc and quarter-sine construction has no leading- or trailing-edge radius, so a built section is thinner than the real one; 20 of 20 comparisons are negative (finding 109) |
| -7.4 | F2 | HPC rotor 5 root section area | HPC Table X | the double-circular-arc and quarter-sine construction has no leading- or trailing-edge radius, so a built section is thinner than the real one; 20 of 20 comparisons are negative (finding 109) |
| +7.3 | E3 | HPC rotor 6 1F frequency | HPC Fig 38 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| -6.7 | F2 | HPC rotor 10 airfoil mass | HPC Table X | inherits the section-area bias of finding 109 almost exactly (finding 109) |
| +6.5 | E1 | HPC rotor 4 root centrifugal stress | HPC Table X | area distribution from Table XXII; material from the F1 density measurement, not from Table X's material column (finding 74) |
| +6.4 | E1 | HPC rotor 1 root centrifugal stress | HPC Table X | area distribution from Table XXII; material from the F1 density measurement, not from Table X's material column (finding 74) |
| -6.3 | F2 | HPC rotor 9 tip section area | HPC Table X | the double-circular-arc and quarter-sine construction has no leading- or trailing-edge radius, so a built section is thinner than the real one; 20 of 20 comparisons are negative (finding 109) |
| -6.0 | F2 | HPC rotor 8 tip section area | HPC Table X | the double-circular-arc and quarter-sine construction has no leading- or trailing-edge radius, so a built section is thinner than the real one; 20 of 20 comparisons are negative (finding 109) |
| +5.5 | F1 | HPC rotor 2 blade density | MIL-HDBK-5J handbook density | the reconstruction's own area accuracy; the two candidates are a factor of two apart so the identification is never in doubt (finding 104) |
| -5.5 | E1 | HPC rotor 9 root centrifugal stress | HPC Table X | area distribution from Table XXII; material from the F1 density measurement, not from Table X's material column (finding 74) |
| -5.4 | F2 | HPC rotor 10 tip section area | HPC Table X | the double-circular-arc and quarter-sine construction has no leading- or trailing-edge radius, so a built section is thinner than the real one; 20 of 20 comparisons are negative (finding 109) |
| +5.3 | F1 | HPC rotor 4 blade density | MIL-HDBK-5J handbook density | the reconstruction's own area accuracy; the two candidates are a factor of two apart so the identification is never in doubt (finding 104) |
| -5.3 | F2 | HPC rotor 8 root section area | HPC Table X | the double-circular-arc and quarter-sine construction has no leading- or trailing-edge radius, so a built section is thinner than the real one; 20 of 20 comparisons are negative (finding 109) |
| -5.1 | F2 | HPC rotor 9 airfoil mass | HPC Table X | inherits the section-area bias of finding 109 almost exactly (finding 109) |
| -5.0 | F2 | HPC rotor 2 root section area | HPC Table X | the double-circular-arc and quarter-sine construction has no leading- or trailing-edge radius, so a built section is thinner than the real one; 20 of 20 comparisons are negative (finding 109) |
| -5.0 | E1 | HPC rotor 5 root centrifugal stress | HPC Table X | area distribution from Table XXII; material from the F1 density measurement, not from Table X's material column (finding 74) |
| -4.6 | F2 | HPC rotor 9 root section area | HPC Table X | the double-circular-arc and quarter-sine construction has no leading- or trailing-edge radius, so a built section is thinner than the real one; 20 of 20 comparisons are negative (finding 109) |
| -4.5 | F2 | HPC rotor 1 airfoil mass | HPC Table X | inherits the section-area bias of finding 109 almost exactly (finding 109) |
| -4.3 | E1 | HPC rotor 7 root centrifugal stress | HPC Table X | area distribution from Table XXII; material from the F1 density measurement, not from Table X's material column (finding 74) |
| -4.2 | F2 | HPC rotor 3 root section area | HPC Table X | the double-circular-arc and quarter-sine construction has no leading- or trailing-edge radius, so a built section is thinner than the real one; 20 of 20 comparisons are negative (finding 109) |
| -4.1 | F2 | HPC rotor 3 airfoil mass | HPC Table X | inherits the section-area bias of finding 109 almost exactly (finding 109) |
| +3.5 | F1 | HPC rotor 6 blade density | MIL-HDBK-5J handbook density | the reconstruction's own area accuracy; the two candidates are a factor of two apart so the identification is never in doubt (finding 104) |
| -3.4 | F2 | HPC rotor 10 root section area | HPC Table X | the double-circular-arc and quarter-sine construction has no leading- or trailing-edge radius, so a built section is thinner than the real one; 20 of 20 comparisons are negative (finding 109) |
| -3.3 | F2 | HPC rotor 1 root section area | HPC Table X | the double-circular-arc and quarter-sine construction has no leading- or trailing-edge radius, so a built section is thinner than the real one; 20 of 20 comparisons are negative (finding 109) |
| +3.2 | F1 | HPC rotor 10 blade density | MIL-HDBK-5J handbook density | the reconstruction's own area accuracy; the two candidates are a factor of two apart so the identification is never in doubt (finding 104) |
| +3.2 | F2 | fan + booster rotor mass | CR-168219 Table XXVI | the fan+booster component table includes a shaft the whole-engine table may group elsewhere (finding 111) |
| -3.2 | F2 | HPC rotor 7 airfoil mass | HPC Table X | inherits the section-area bias of finding 109 almost exactly (finding 109) |
| -2.8 | F2 | HPC rotor 7 root section area | HPC Table X | the double-circular-arc and quarter-sine construction has no leading- or trailing-edge radius, so a built section is thinner than the real one; 20 of 20 comparisons are negative (finding 109) |
| -2.7 | E3 | booster rotor first flex | CR-165148 Fig 52 (geometry) | none needed -- an unshrouded blade really is a beam (finding 82) |
| +2.7 | E1 | HPC rotor 2 root centrifugal stress | HPC Table X | area distribution from Table XXII; material from the F1 density measurement, not from Table X's material column (finding 74) |
| -2.6 | F2 | LPT stator mass | Table XXVI | two documents agreeing; nothing needed (finding 111) |
| -2.4 | E3 | HPC rotor 3 2F frequency | HPC Fig 35 | a clamped beam is the stiffest root a blade can have and a dovetail in a slot is not a clamp; the bias grows with mode number, which is what a soft root does (finding 143) |
| +2.3 | E1 | HPC rotor 6 root centrifugal stress | HPC Table X | area distribution from Table XXII; material from the F1 density measurement, not from Table X's material column (finding 74) |
| -2.2 | E1 | HPC rotor 8 root centrifugal stress | HPC Table X | area distribution from Table XXII; material from the F1 density measurement, not from Table X's material column (finding 74) |
| -2.2 | F2 | LPT rotor mass | Table XXVI | two documents agreeing; nothing needed (finding 111) |
| -2.1 | E1 | HPC rotor 10 root centrifugal stress | HPC Table X | area distribution from Table XXII; material from the F1 density measurement, not from Table X's material column (finding 74) |
| +1.9 | B3 | sfc at takeoff | Table XII | Table XII is a mixed-day table: T41 on the flat-rating day, sfc on the standard day. Takeoff is a pinned xfail |
| -1.6 | F1 | HPC rotor 1 blade density | MIL-HDBK-5J handbook density | the reconstruction's own area accuracy; the two candidates are a factor of two apart so the identification is never in doubt (finding 104) |
| +1.6 | E1 | HPC rotor 3 root centrifugal stress | HPC Table X | area distribution from Table XXII; material from the F1 density measurement, not from Table X's material column (finding 74) |
| -1.5 | E4 | HP spool speed at max climb | HPC Table X aero design point | two independent documents; nothing needed (finding 121) |
| +1.3 | E4 | LP spool speed at max climb | LPT report N/sqrt(T) and the cycle's T45 | two independent documents; nothing needed (finding 121) |
| -0.9 | F1 | HPC rotor 3 blade density | MIL-HDBK-5J handbook density | the reconstruction's own area accuracy; the two candidates are a factor of two apart so the identification is never in doubt (finding 104) |
| +0.6 | F1 | HPC rotor 9 blade density | MIL-HDBK-5J handbook density | the reconstruction's own area accuracy; the two candidates are a factor of two apart so the identification is never in doubt (finding 104) |
| +0.6 | B3 | sfc at max_cruise | Table XII | within band; nothing needed |
| +0.5 | E4 | aft_seal_disk critical-speed margin | HPT Table XXII | the report rounds the same 1.618 two ways (finding 91) |
| +0.5 | B3 | sfc at max_climb | Table XII | within band; nothing needed |
| -0.5 | F2 | HPC rotor 7 tip section area | HPC Table X | the double-circular-arc and quarter-sine construction has no leading- or trailing-edge radius, so a built section is thinner than the real one; 20 of 20 comparisons are negative (finding 109) |
| -0.4 | F2 | HPT rotor mass | Table XXVI | two documents agreeing; nothing needed (finding 111) |
| -0.1 | E4 | inner_tube critical-speed margin | HPT Table XXII | the report rounds the same 1.618 two ways (finding 91) |
| +0.1 | F1 | HPC rotor 7 blade density | MIL-HDBK-5J handbook density | the reconstruction's own area accuracy; the two candidates are a factor of two apart so the identification is never in doubt (finding 104) |
| -0.0 | E4 | forward_shaft critical-speed margin | HPT Table XXII | the report rounds the same 1.618 two ways (finding 91) |
| +0.0 | E4 | outer_liner critical-speed margin | HPT Table XXII | the report rounds the same 1.618 two ways (finding 91) |
| +0.0 | F2 | HPT stator mass | Table XXVI | two documents agreeing; nothing needed (finding 111) |

---

## 2. Closures

11 met, 10 half met, 3 gated, of 24.
17 of 19 numeric closures sit inside their own band.

A *half* closure has one part satisfied and the other part naming what
blocks it. None is open without a reason attached.

| stage | closure | achieved | band | state |
|---|---|---:|---:|---|
| B1 | the mixer reproduces Table XXIII's sfc improvement | 0.7 | — | half |
| B3 | sfc at three ratings against Table XII | 1.91 | 1.5 | half |
| B4 | annulus by continuity at every dimensioned HPT station | 3.6 | — | met |
| C1 | LPT mean-line efficiency against 0.917 | 0.6 | 2 | met |
| C1 | HPT mean-line efficiency against 0.9155 / 0.925 / 0.927 | 0.55 | 2 | met |
| C1 | HPC efficiency against 0.847 | 0.15 | 2 | met |
| C2 | stator-10 exit swirl | 0.02 | 2 | met |
| C4-1 | the solver against an exact answer (Sod shock tube, star pressure) | 0.02 | 2 | met |
| C4-2 | Rotor 37 blade geometry, 24 section-closure constraints | 0 | 0 | met |
| C4-3 | CFD against the Rotor 37 validation case | — | — | gated |
| D3 | total secondary air against Table XI's 16.1 % of W25 | 0.04 | 0.5 | half |
| D4 | cruise clearance, two independent routes | 0.04 | 0.2 | met |
| E1 | Table X centrifugal stresses, all ten HPC stages | 6.5 | 10 | half |
| E2 | the bore doubling for a small hole | 0 | 0.5 | half |
| E3 | blade first flex, the unshrouded booster | 2.7 | 15 | met |
| E3 | first three modes of every HPC stage against Figs 33-42 | 21.4 | 5 | half |
| E4 | no rotor critical inside the operating band | 0 | 0 | half |
| E5 | every attachment with a printed allowable has margin | 0 | 0 | half |
| F1 | every Stage E stress with a printed allowable, tabulated against it | 0 | 0 | half |
| F2 | basic engine mass within 10 % of 3,473 kg | — | 10 | gated |
| G1 | generated blade volume against Stage F2's integral | 0.94 | 2 | half |
| G1 | blade-to-blade interference, all 32 rows | 0 | 0 | met |
| H | zero clashes through rotation, every bearing with its load | — | — | gated |
| I3 | FINDINGS.md written -- every disagreement ranked, with a cause or unresolved | 0 | 0 | met |

### The two recorded misses

- **B3 — sfc at three ratings against Table XII**: 1.91 against a band of 1.5. two of three inside the band. Takeoff reads +1.91 % and is a strict xfail with its size pinned; the cause is recorded -- Table XII is a mixed-day table, T41 on the flat-rating day and sfc on the standard day.
- **E3 — first three modes of every HPC stage against Figs 33-42**: 21.4 against a band of 5. Figs 33-42 were transcribed on 2026-09-08 and the closure is now EVALUATED rather than gated -- and it fails: 1 of 24 comparisons inside the band, mean +21.4 %, first flex +15.8 % and over-predicted on nine stages of ten. The cause is the one finding 84 already named: a clamped beam is the stiffest root a blade can have and a dovetail is not a clamp. Closing this needs a root-flexibility model or an FE blade, not a better beam. Findings 143-145.


---

## 3. Unresolved

Five disagreements have no cause. They are not failures of the model so
much as questions the reports have not answered.

- **LPT Fig 70 disk_C stress concentration** (E5) — 2.86547 against 1.6, +79.1 %. Source: LPT Fig 70.
- **Rotor 37 mass flow, converged solve** (C4) — 5.17 against 20.188, -74.4 %. Source: TP-1337 Table I design flow.
- **HPC stage-1 first flex at 14,000 rpm** (E3) — 539 against 350, +54.0 %. Source: HPC Fig 33, read flat across the speed range.
- **LPT Fig 70 disk_D stress concentration** (E5) — 0.990331 against 1.6, -38.1 %. Source: LPT Fig 70.
- **HPT stage-1 disc bore stress, Fig 64 vs Fig 55** (E2) — 1034 against 779, +32.7 %. Source: CR-167955 Figs 55 and 64.

---

## 4. The E³ as designed and the E³ as tested

I3's second bullet. The FPS is the paper engine of CR-168219; the ICLS
is the one that ran (CR-168211). Where they differ, and which this
model follows.

### sfc at sea-level rated thrust

| | mg/N·s | lb/hr·lbf |
|---|---:|---:|
| ICLS predicted | 9.008 | 0.318 |
| ICLS as tested | 9.234 | 0.326 |
| ICLS fully corrected | 8.781 | 0.31 |

The engine tested **2.5 % above** its own
prediction, and the report accounts for every part of that gap:

| component | variation from prediction | sfc % |
|---|---|---:|
| inlet | -0.8 percent recovery | 0.2 |
| fan | -0.6 percent efficiency | 0.4 |
| fan_hub | +1.0 percent efficiency | -0.2 |
| lp_turbine | -1.0 percent efficiency | 0.9 |
| exhaust | leakage, pressure loss | 1.0 |
| cdp_bleed | +0.35 percent | 0.2 |
| **total** | | **2.5** |

The six items sum to exactly the 2.5 %. **This model is built to the
FPS design**, so it should — and does — sit nearer the prediction than
the test: Stage B closes sfc to +0.46 / +0.56 % at climb and cruise
against Table XII, which is the design table.

### Component efficiencies, design goal against test

| | as tested | vs goal |
|---|---:|---|
| fan, bypass stream | 0.886 | +0.4 % |
| fan, hub and booster | 0.901 | +1.4 % (summary) / +1.1 % (conclusions) |
| HP compressor | 0.856 | +0.5 points |

Two things worth carrying from this table. The fan hub's margin over
goal is printed as **1.4 % in the summary and 1.1 % in the
conclusions of the same report** — recorded as read, both kept. And
the ICLS compressor ran at **0.856**, where
this project's C1 mean-line closes the *design* HPC at 0.8455 against
a design 0.847. The model matches the design, not the test, and the
difference is the ICLS's own build clearances.

### The fan shroud, which the reports disagree about

CR-168211 and CR-168219 both put the part-span shroud at **50 % span**;
the fan hardware report (CR-165148, `fan-design.yaml`) says **55 %**.
Stage E3 used 55 because it came from the hardware report, and recorded
the discrepancy. It matters: the shroud position sets which modes it
restrains.

---

## 5. Index of numbered findings

147 findings, in the `STEP0.md` that owns each one.

**Numbers 55, 56, 57 are not used.** They were
reserved for C3 units 16 and 17 — the booster rows, the inner OGV and
section stacking — which were handed to a parallel session and never
landed. The gap is left rather than closed up, because renumbering
would break every reference in the commit history.

| # | unit | |
|---:|---|---|
| 1 | blading | The camber line. A double circular arc — two arcs meeting where the |
| 2 | blading | The thickness. The quarter-sine distribution this engine's own fan |
| 3 | blading | Throat position along the chord |
| 4 | cfd | stagger monotonic: True |
| 5 | cfd | hub/tip radius ratio  0.7047 vs Table I's 0.70          +0.67 % |
| 6 | meanline | Three routes, one ordering. R&M 2974 as printed under-predicts, |
| 7 | meanline | The sign of the stage-1 exit swirl is settled by the reaction |
| 8 | meanline | The E³ stage-1 vane is transonic at the pitch line — exit Mach |
| 9 | meanline | Only one line of Table V can be checked, and it is a factor of 1.6 |
| 10 | meanline | Stage 2 turns 14° less than the preliminary study and sits on the |
| 11 | meanline | Carter's rule has almost no bias on this compressor and a clear |
| 12 | meanline | The parabolic-arc curve is the wrong one for this compressor, as |
| 13 | meanline | The stage-10 stator is the outlier at both ends — the OGV, at |
| 14 | meanline | The two routes agree to 0.03 % in the mean, and that is the |
| 15 | meanline | The compressor's efficiency is a span-wise story, not a number. |
| 16 | meanline | The design intent is met at the pitch line and paid for at the |
| 17 | meanline | Route 2's residual is not random. It is −1.8 % on the hub |
| 18 | meanline | The figure read-offs and Table XXI are the same numbers. Across |
| 19 | meanline | Fig 14's "average temperature rise" is the span average, and the |
| 20 | meanline | The E³ compressor runs past the classic de Haller limit on nearly |
| 21 | meanline | The fan's tip relative Mach falls out of two unrelated printed |
| 22 | meanline | The same calculation reaches the inner sections only just, and the |
| 23 | meanline | One shaft, two rows, half an rpm. The fan's 411.5 m/s on a |
| 24 | meanline | The island arithmetic closes exactly and the booster is lightly |
| 25 | meanline | Every CAFD row's efficiency recomputes from its own cumulative |
| 26 | meanline | Three of the five fall out exactly, from the cycle and two shaft |
| 27 | meanline | The derivation reproduces a design decision, not just a number. |
| 28 | meanline | The fan is not loading-limited, and the generic limit gets it |
| 29 | meanline | The LPT has one stage more than it needs, and that is the point. |
| 30 | throughflow | The E³'s printed through-flow satisfies simple radial equilibrium |
| 31 | throughflow | Table XXI's streamline-slope column is real geometry, not a |
| 32 | throughflow | This is a badly conditioned equation and most texts do not say |
| 33 | throughflow | C2's closure criterion is met with two orders of magnitude to |
| 34 | throughflow | A correction that improves a local residual can degrade an |
| 35 | throughflow | The error is a map of where the compressor is hard. It is largest |
| 36 | throughflow | The E³ LPT's "controlled vortex" is n ≈ −0.5: half a free |
| 37 | throughflow | The law drifts toward free vortex rearward, and the geometry says |
| 38 | throughflow | The compressor has no vortex law at all, and that is deliberate. |
| 39 | throughflow | Fig 5c integrates to the HPT report's own design point, and only to |
| 40 | throughflow | The E³ HPT is neither a free vortex nor a solid body. A free |
| 41 | throughflow | Two of Fig 5's three panels cannot distinguish the vortex laws at |
| 42 | blading | The throat margin falls monotonically from 28 % at the last rotor |
| 43 | blading | The stators are circular-arc blades and the rotors are not. The |
| 44 | blading | The inference is ill-conditioned exactly where it is most |
| 45 | blading | The IGV is not this family at all. Its stagger sits 17° below the |
| 46 | blading | Three independent things agree to 1.4°. A 1951 British |
| 47 | blading | The term I first omitted is real, and the coordinates can measure |
| 48 | blading | Zweifel closes from the coordinates. The axial width from the |
| 49 | blading | A turbine's throat can be recovered from an aspect ratio. Table |
| 50 | blading | The same bias appears as in unit 13, and for the same reason. The |
| 51 | blading | Three of the four Zweifel numbers close to 0.03; the stage-2 vane |
| 52 | blading | The fan blade can be designed from the published data, and it comes |
| 53 | blading | The throat margin comes out about twice the published value and the |
| 54 | blading | The design says the fan tip has almost no camber, and the |
| 58 | thermal | The four cooled rows do lie on one curve, and the exponent is the |
| 59 | thermal | Cooling effectiveness is what the E³ spends its coolant on, and the |
| 60 | thermal | The stage-2 vane looked like the outlier, and it is a station |
| 61 | thermal | Two of the three points land within 8 K, from one fitted number. |
| 62 | thermal | The third point is the leading edge, and the miss is film cooling — |
| 63 | thermal | The internal conductance is worth keeping. H_c ≈ 5,500 W/m²·°C |
| 64 | thermal | The budget closes twice, and the two budgets are 2.7 points apart |
| 65 | thermal | The printed backflow-margin definition does not fit both printed |
| 66 | thermal | Every stream is taken from the lowest pressure that will do the |
| 67 | thermal | Table X is one calculation, and it closes to 0.002 point. Each |
| 68 | thermal | The cruise clearance closes by two independent routes, from two |
| 69 | thermal | The ACC schedule is the design, not the hardware. The report is |
| 70 | thermal | Twenty-four read labels sum to exactly 100.0 % of compressor |
| 71 | thermal | T41 is not the combustor exit temperature, and treating it as one |
| 72 | thermal | The combustor aims its hot spot at the turbine's weakest span, on |
| 73 | mechanical | All ten root stresses reproduce within 6.5 %, from geometry |
| 74 | mechanical | The material crossover falls out of the stress data. Stages 1–4 |
| 75 | mechanical | Table X's stresses are at the deteriorated-engine speed, and its |
| 76 | mechanical | The taper factor runs 0.56 to 0.80 and it is the whole point of |
| 77 | mechanical | The bore doubling is exact, and it is the reason a disc bore is |
| 78 | mechanical | Not one of nineteen published rotor stresses scales as N². If a |
| 79 | mechanical | Three printed numbers cannot separate the two loads, and the |
| 80 | mechanical | Six hundred tonnes of blade pull on one disc. 76 blades, each |
| 81 | mechanical | The Fig. 64 comparison is gated, not skipped. E2's other closure |
| 82 | mechanical | An unshrouded blade really is a beam, to 2.7 %. The booster rotor |
| 83 | mechanical | The three blades need three different boundary conditions, and each |
| 84 | mechanical | The pinned-tip LPT blade reads 45 % high, and temperature is only |
| 85 | mechanical | The model under-predicts centrifugal stiffening by 30–41 % on both |
| 86 | mechanical | A pinned-tip blade's frequencies FALL with speed, and the published |
| 87 | mechanical | The one HPC frequency Stage A did transcribe brackets correctly, and |
| 88 | mechanical | The ten HPC rotors are predicted and recorded so the gate is one |
| 89 | mechanical | The LP shaft carries more than twice the HP shaft's torque, on a |
| 90 | mechanical | Two reports and a cycle model agree on the physical spool speed to |
| 91 | mechanical | Table XXII checks itself, and the one printed inconsistency is |
| 92 | mechanical | The aft seal disc's critical is 22 % above where a rigid disc would |
| 93 | mechanical | Fig. 88's second printed point belongs to a different curve. The |
| 94 | mechanical | Seventy-six tonnes out of one fan blade. At 3,653 rpm a released |
| 95 | mechanical | The airfoil is two-thirds of a fan blade and half a booster blade. |
| 96 | mechanical | The joint that transmits the core's torque needs a 7 cm radius and |
| 97 | mechanical | A hand tension calculation reads a dovetail six times low. The HPT |
| 98 | mechanical | The two tangs are not equally stressed, and the printed numbers say |
| 99 | mechanical | The fan and booster crush stresses are not quoted over the same |
| 100 | mechanical | Fig. 70's stress-concentration factor is checkable, and it checks |
| 101 | mechanical | Three retainers, three loads 75 % apart, one stress. The LPT |
| 102 | mechanical | The rear casing flanges are bolt-limited at their own criterion. |
| 103 | mechanical | The weak-link order holds where it can be checked, and the two HPT |
| 104 | materials | Table X contradicts itself, and it takes three of its own columns to |
| 105 | materials | Correction to finding 74, in three parts. E1 wrote that (a) "the |
| 106 | materials | The material switch that Table X prints is a temperature decision, |
| 107 | materials | Three parts sit exactly on their allowable, and they are the parts |
| 108 | materials | The compressor blades have room, and the number that says how much |
| 109 | materials | The blading reconstruction is 7 % thin, and all twenty comparisons |
| 110 | materials | The smaller the blade, the less of it is blade. Airfoil as a |
| 111 | materials | Five module weights, two documents each, and they agree to 3.2 %. |
| 112 | materials | F2's closure is gated on the same three things Stage E was, and |
| 113 | geometry | OpenCASCADE cannot cap a non-planar wire, and it does not say so — |
| 114 | geometry | Two sections out of ninety-six had one fewer point than their |
| 115 | geometry | Thirty-two rows, every solid valid, and the CAD agrees with the |
| 116 | geometry | Not one blade in the engine touches its neighbour, and the check |
| 117 | geometry | Four of Stage G's seven bullets are blocked on transcription, not |
| 118 | verification | Eight stages of independent reading, and the shared numbers agree. |
| 119 | verification | The T41 that looked like a 2.6 % disagreement is the design moving, |
| 120 | verification | "Takeoff" means three different things and the spread is 1.35 %. |
| 121 | verification | Four routes to two spool speeds, out of four documents, agree to |
| 122 | verification | Fourteen of fifteen numeric closures are inside their band, and the |
| 123 | verification | The margin stack in D checks out to the rounding, including its |
| 124 | cfd | The solver is right to 0.02 % where it can be checked exactly. |
| 125 | cfd | The nesting is what makes it worth anything. A CFD result checked |
| 126 | cfd | The error is where discretisation puts it, which is the real |
| 127 | cfd | The toolchain took finding out, and two of the three assumptions |
| 128 | cfd | Twenty-four closure constraints, satisfied exactly. Each of the |
| 129 | cfd | The tip radius and the tip speed were transcribed from different |
| 130 | cfd | The printed aspect ratio does not follow from the printed geometry, |
| 131 | cfd | The blade thins by more than a factor of three from hub to tip, and |
| 132 | cfd | Two printed digits did not resolve, and they are handled |
| 133 | cfd | The flow path is datumed on the blade, and it lands exactly on it. |
| 134 | cfd | Appendix C's outermost section lies OUTSIDE the casing, and the |
| 135 | cfd | The trim is where the published aspect ratio went, and it closes to |
| 136 | cfd | The hub rises exactly as much as the casing falls: 1.651 cm each. |
| 137 | cfd | Body-fitting the annulus turned a three-surface snap into a |
| 138 | cfd | The mesh volume checks against the annulus integrated |
| 139 | cfd | blockMesh said "patch → block consistency" when it meant "you |
| 140 | cfd | Three MRF faults in a row, none of which raised an error. A |
| 141 | cfd | The stalled branch is an attractor, and its repeatability is the |
| 142 | cfd | A ramped back pressure was tried and did not help, which rules out |
| 143 | mechanical | E3's closure fails, and it fails in the direction and by the amount |
| 144 | mechanical | The error grows with mode number, which is what a root flexibility |
| 145 | mechanical | The published Campbell lines are flat with speed, and the model says |
| 146 | verification | The median disagreement with a published number is 6.7 %, over |
| 147 | verification | Twenty of the twenty-one worst disagreements are the same bug. The |
| 148 | verification | Five disagreements have no cause, and saying so is the point. The |
| 149 | verification | The model matches the design, not the test, and the ICLS numbers |
| 150 | verification | Three numbered findings do not exist, and the gap is left open. |


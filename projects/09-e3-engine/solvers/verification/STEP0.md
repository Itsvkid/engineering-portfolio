# Step 0 — whole-engine verification (I): tolerance and validation case, written first

Per [METHOD.md](../../METHOD.md). Nothing in a step-0 section is edited
after its run; results and findings are appended below it.

## Unit I1 — cross-discipline consistency

Stage I1's bullets: *the same T41 in B, D and E; the same cooling flows in
B, D and D3; the same metal temperatures in D and E and F; the same masses
in F and G — **as tests, not by inspection**. Spool speeds from four routes
agree. Every "closes when" tolerance re-checked after Stage G's geometry.*

Eight stages of solvers have grown up beside each other, each reading the
reports for itself, and **nothing so far has forced them to agree**. A
quantity that appears in three chapters can enter this project three times;
if one reading drifted — a unit, a rating, a footnote missed — every stage
downstream would still close against its own band and nothing would say so.
Every check below is a place that could have happened and did not have to
be noticed.

There is a second kind of check here and it is the sharper one: quantities
that arrive by **genuinely different routes**. The LP spool speed from the
fan's corrected tip speed and tip diameter, or from the LPT report's
N/√T and the cycle's own T45. The HP speed from HPC Table X's footnote, or
from the HPT report's N/√T and T41. Four measurements of two numbers, out
of four documents, none derived from another.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| T41 at the aero design point, cycle vs HPT report | both describe the same instant of the same cycle | **±0.5 %** | the HPT report's *cycle match* line, not its *earlier requirements* table — that block is labelled as superseded and is chronology, not disagreement |
| T41 at takeoff, three appearances | three documents, and **three definitions of "takeoff"** | **±2 %** across all three; **±0.5 %** between the two that share a definition | the cycle is sea-level static, the cooling design point is Mach 0.3 |
| The cycle still solves to the rating it was given | Table XII's T41 | **exact** | the fuel-air bisection's target; the hinge every downstream stage hangs on |
| D's T41 margin stack | direct adders sum, 2σ events root-sum-square | **±0.5 °C** | the report prints every term and the totals |
| Cooling flows, cycle vs D3's final streams | four streams and their total | **exact** | the cycle's bleeds *are* the final FPS streams; if they are not, one of them was retyped |
| D1's detailed design | 18.87 % of W25 | **±0.05** | eight printed items that must sum to a printed total |
| Masses, F2's integral vs G1's solids | 32 rows | **±2 %** | Stage G's own band, re-run here rather than trusted |
| LP speed, two routes | fan tip speed vs LPT N/√T | **±2 %** | different documents, different physics |
| HP speed, two routes | HPC Table X vs HPT N/√T | **±2 %** | same |
| Spool ratio | the plan's own "LP : HP ≈ 1 : 3.6" | **±3 %** | H4's assumption, checked before H is ever built |
| Every closure re-checked | `data/closures.yaml` | **each closure inside its own band, or a recorded miss** | the third bullet, made machine-readable |

Metal temperatures are the one item that cannot be a numerical identity:
D reads the HPT blade and vane metal, E2 the HPT *rotor* metal from a
different figure, F1 the HPC blade metal from Table X. Three sets, three
figures, one engine. The check is that they are **ordered the way the gas
path is** and that no solver reads a value its own source does not carry.

---

## Unit I1 after the run — nothing above was edited; what follows was added

### Results, 2026-09-07 (`cd solvers && python -m verification.consistency`)

```
1. T41
   max climb, the aero design point
      B cycle       Table XII, via Rating                    1517.2 K
      A HPT report  cycle match                              1517.0 K     spread 0.01 %
   takeoff
      B cycle       Table XII takeoff, sea-level static      1638.2 K
      A HPT report  SLTO +27 F requirement                   1618.0 K
      D cooling     Table VIII, Mach 0.3 sea-level takeoff   1616.2 K     spread 1.35 %
   chronology: T41 fell 40 K at max climb and 30 K at max cruise between the
   HPT report's earlier requirement and the final cycle
   the cycle solves to its rating exactly at all three points (+0.0000 %)
   D's margin stack: direct 35.0/35.0, RSS 20.3/20.5, new engine 55.5/55.5,
   with deterioration 77.7/77.7 C, T41 design 1420.7/1421.0 C

2. Cooling flows                       cycle %   published %   err %
   cpd_nonchargeable                      7.46          7.46    0.00
   cpd_chargeable                         5.33          5.33    0.00
   stage_7_cooling_and_purge              1.95          1.95    0.00
   stage_5_cooling_and_purge              1.40          1.40    0.00
   total                                 16.14         16.14
   D1's detailed design sums to 18.87 against a printed 18.87 % of W25

3. Metal temperatures
   F  hottest HPC blade           655 C     D  hottest cooled HPT row   953 C
   E  HPT stage-1 blade shank     726 C     E  HPT stage-1 disc bore    392 C

4. Spool speed, four routes out of four documents (max climb)
   LP  fan corrected tip speed / tip radius        3,529 rpm
   LP  LPT report N/sqrt(T45)                      3,483 rpm     spread 1.31 %
   HP  HPC Table X, aero design point             12,645 rpm
   HP  HPT report N/sqrt(T41)                     12,449 rpm     spread 1.55 %
   HP:LP = 3.57

5. Masses: 32 rows, worst 0.94 %, all valid

6. Every closure re-checked
   20 closures: 7 met, 10 half, 3 gated
   14 of 15 numeric closures inside their band; the miss is B3's takeoff sfc
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| T41, cycle vs HPT cycle match | **0.01 %** | ±0.5 % | pass |
| T41 at takeoff, all three | 1.35 % | ±2 % | pass |
| T41, the two sharing a definition | **0.11 %** | ±0.5 % | pass |
| Cycle solves to its rating | 0.0000 % | exact | pass |
| D's margin stack | worst 0.2 °C (the RSS rounding) | ±0.5 °C | pass |
| Cooling flows, all four and the total | **0.00 %** | exact | pass |
| D1's detailed sum | 18.87 vs 18.87 | ±0.05 | pass |
| Masses F2 vs G1 | 0.94 % | ±2 % | pass |
| LP speed, two routes | 1.31 % | ±2 % | pass |
| HP speed, two routes | 1.55 % | ±2 % | pass |
| Spool ratio vs the plan's 3.6 | **3.57, 0.8 %** | ±3 % | pass |
| Every closure re-checked | 14 of 15 inside; 1 recorded miss | each inside or recorded | pass |

### Findings

118. **Eight stages of independent reading, and the shared numbers agree.**
     Nothing had forced them to. The four cooling-flow streams the cycle
     bleeds are the four Stage D3 measured, to **0.00 %** — not close, the
     same numbers. T41 at the aero design point is 1517.2 K in a cycle
     model built from fan and combustor data and 1517 K in the HPT report's
     own cycle-match line, **0.01 %**. Stage F2's integral and Stage G1's
     lofted solids agree to 0.94 % over all 32 rows. This unit's value is
     not that it passed; it is that it *could* have failed silently, and
     from now on it cannot.
119. **The T41 that looked like a 2.6 % disagreement is the design moving,
     and the transcription had already said so.** The HPT report's
     requirements table gives 1557 K at max climb where the final cycle
     gives 1517 — a 40 K drop, and 30 K at max cruise. The block is named
     `earlier_requirements`, and the same report's `cycle_match` line
     carries 1517. **Comparing against the wrong block would have
     manufactured a finding out of a design history.** The check is
     against what a report designed to, not against what it was first
     asked for.
120. **"Takeoff" means three different things and the spread is 1.35 %.**
     The cycle's takeoff is sea-level *static*; the HPT requirement is
     SLTO + 27 °F; the cooling design point is **Mach 0.3**, sea-level.
     1638.2, 1618.0 and 1616.2 K. The two that share a definition agree to
     **0.11 %**, and the odd one out is the one with 0.3 of ram in it.
     A number quoted "at takeoff" without its Mach number is not a
     temperature, it is a range.
121. **Four routes to two spool speeds, out of four documents, agree to
     1.6 %.** LP: the fan report's corrected tip speed over its tip radius
     gives 3,529 rpm at max climb; the LPT report's N/√T with the cycle's
     T45 gives 3,483 — **1.31 %**. HP: HPC Table X's footnote gives 12,645
     at the aero design point; the HPT report's N/√T with the cycle's T41
     gives 12,449 — **1.55 %**. And the ratio falls out at **3.57** against
     the work plan's own "LP : HP ≈ 1 : 3.6" for Stage H's assembly motion
     — an assumption written before any of this was computed, checked here
     before H is ever built.
122. **Fourteen of fifteen numeric closures are inside their band, and the
     fifteenth is a pinned miss.** `data/closures.yaml` now carries every
     stage's own *closes when* sentence, its band and the number the
     solvers produce today, so the re-check is a test and not a reading.
     The one miss is B3's takeoff sfc at +1.91 % against ±1.5 %, which is
     a strict xfail with its size pinned and its cause recorded — Table XII
     is a mixed-day table. **Seven closures are met, ten are half met with
     the other half named, three are gated.** No closure in this project is
     open without a reason attached to it.
123. **The margin stack in D checks out to the rounding, including its
     root-sum-square.** T41's design margin is 35.0 °C of direct adders
     plus 20.5 °C of two-sigma events combined RSS, giving 55.5 for a new
     engine and 77.7 with deterioration; T41 design is then 1343 + 77.7 =
     1420.7 against a printed 1421. Every term is printed and every total
     recomputes — the RSS to 0.2 °C, which is the printing. It is the one
     place in the E³ reports where a *statistical* combination is shown
     term by term, and it is worth knowing it is arithmetically sound
     before Stage D's metal temperatures are leaned on.

---

## Unit I3 — `FINDINGS.md`. The deliverable.

The work plan's I3: *every disagreement with a published number, ranked by
size, with a cause or "unresolved"; every place the E³ design and the E³ as
tested differ, and which the model matches.* **Closes when: written. This
is the deliverable.**

| Check | Known answer | Band | Basis |
|---|---|---|---|
| Every disagreement harvested | not a hand-picked list | **generated from the solvers** | a hand-written list contains the disagreements someone remembered; this one re-ranks itself when the code changes |
| `unresolved` used honestly | — | **more than zero, fewer than 20 %** | zero would mean the causes were invented; a large fraction would mean the work had not been done |
| Every entry carries a source | — | **all of them** | a disagreement without the page it disagrees with is an opinion |
| The document is current | — | **regenerating changes nothing** | a stale deliverable is worse than none |

---

## Unit I3 after the run — nothing above was edited; what follows was added

### Results, 2026-09-08 (`python tools/build_findings.py`)

```
98 ranked disagreements across 9 stages
   within 1 %     12
   within 5 %     38
   within 10 %    56
   worse than 20 % 21
   median |error|  6.70 %
   unresolved       5

142 numbered findings indexed; numbers 55-57 unused and recorded as such
23 closures: 10 met, 10 half, 3 gated; 16 of 18 numeric ones inside band
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| Harvested, not hand-picked | 98 from 9 harvesters | generated | pass |
| `unresolved` used | **5 of 98, 5.1 %** | >0 and <20 % | pass |
| Sources on every entry | all 98 | all | pass |
| Document current | regeneration is a no-op | no change | pass |

### Findings

146. **The median disagreement with a published number is 6.7 %, over
     ninety-eight comparisons.** Twelve land inside 1 %, thirty-eight
     inside 5, fifty-six inside 10, and twenty-one are worse than 20. That
     is the project in one number, and it is worth having because no single
     stage's closure says it: each stage compares itself against its own
     band, and only a ranking across all of them shows what the whole thing
     is worth.
147. **Twenty of the twenty-one worst disagreements are the same bug.** The
     top of the ranking is almost entirely E3's blade frequencies — the
     clamped-beam bias, which over-predicts by 16 % on first flex and by
     44 % on third. One modelling limit, named in finding 143, accounts for
     most of the project's worst numbers. Everything else in the ranking is
     an order of magnitude better behaved.
148. **Five disagreements have no cause, and saying so is the point.** The
     Fig. 55 / Fig. 64 disc bore stress, which differs by 33 % between a
     thin-shell and a detailed FE model in the same report; LPT Fig. 70's
     printed Kt, which reproduces on both blade sections and neither disc
     section; the HPC Campbell lines, drawn flat with speed where the model
     says stage 1 should rise 54 % by redline; and Rotor 37's solve, which
     collapses to a quarter of design flow. **Five of ninety-eight is the
     honest count.** A list with none would mean the causes were being
     invented to fill the column.
149. **The model matches the design, not the test, and the ICLS numbers
     show by how much.** The engine as run burned **2.5 % more fuel than
     its own prediction**, and CR-168211 accounts for every part of that in
     six items that sum to exactly 2.5 — the exhaust system and overboard
     leakage 1.0, the LPT's missing efficiency point 0.9, the inlet 0.2.
     This project is built to the FPS *design*, so Stage B closing sfc to
     +0.46 and +0.56 % against Table XII is the right kind of agreement,
     and the ICLS's 2.5 % is not a target it should be trying to hit. The
     same shows in the compressor: C1 closes the design HPC at 0.8455
     against a design 0.847, where the ICLS measured **0.856** at its own
     build clearances.
150. **Three numbered findings do not exist, and the gap is left open.**
     55, 56 and 57 were reserved for C3 units 16 and 17 — the booster rows,
     the inner OGV and section stacking — which were handed to a parallel
     session and never landed. Renumbering would break every reference in
     the commit history, so the gap stays and `FINDINGS.md` says why.

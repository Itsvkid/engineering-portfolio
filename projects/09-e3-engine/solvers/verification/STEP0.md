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

---

## Unit I2 — sensitivity

I2's bullet: *which assumptions move the sfc, the metal temperature and the
disc stress most — one-at-a-time, tabulated.*

Every number here rests on inputs of three kinds: values **published** in
the reports, values **measured** from them, and a few **handbook**
constants that are nobody's measurement. The third kind is the one worth
worrying about, and the only way to know how much is to move each one and
watch.

Each input is raised by **1 % of its own value**, so the results are
elasticities — d(ln output)/d(ln input). An elasticity of 1 means a 1 %
error in that input is a 1 % error in the answer.

**The step-0 validation is that several of these have exact analytic
answers**, and a sensitivity machine that cannot reproduce them is not
worth running on the ones that do not:

| Check | Known answer | Band | Why it is exact |
|---|---|---|---|
| Combustor efficiency → sfc | **−1** | ±0.02 | sfc is fuel flow over thrust and fuel flow goes as 1/η_comb |
| Density → disc bore stress | **+1** | ±0.01 | σ = (3+ν)/4 · ρω²[…] is linear in ρ |
| Rotor speed → disc bore stress | **+2** | ±0.01 | σ goes as ω² |
| Rim radius → disc bore stress | **+2** | ±0.02 | σ goes as b², the a² term being small at a/b = 0.15 |
| Gas + coolant temperature → metal temperature | **sum to +1** | ±0.01 | T_m is a weighted average of the two and of nothing else |
| h_g and H_c → metal temperature | **equal and opposite** | ±0.01 | only their ratio enters the wall balance |
| Handbook share of each answer | — | reported, not bounded | the point of the unit |

---

## Unit I2 after the run — nothing above was edited; what follows was added

### Results, 2026-09-08 (`cd solvers && python -m verification.sensitivity`)

```
sfc at max cruise                        elasticity
   nozzle_coefficient                       -2.455   published
   combustor_efficiency                     -1.017   published
   hpt_efficiency                           -0.327   published
   lpt_efficiency                           -0.302   published
   fan_bypass_efficiency                    -0.253   published
   compressor_efficiency                    -0.059   published
   mixer_effectiveness                      -0.042   published
   (seven more, all below 0.02)

HPT stage-1 blade metal temperature
   gas temperature                          +0.717   published
   coolant temperature                      +0.283   published
   internal conductance H_c (fitted)        -0.180   measured
   gas-side coefficient h_g (Fig 23)        +0.179   published

HPT disc bore stress
   rim radius                               +2.010   measured
   rotor speed                              +2.010   published
   density (Rene 95, handbook)              +1.000   handbook
   Poisson's ratio (handbook)               +0.086   handbook

handbook share:  sfc 0.0 %   metal temperature 0.0 %   disc stress 21.3 %
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| Combustor efficiency → sfc | **−1.017** | −1 ±0.02 | pass |
| Density → disc stress | **+1.000** | +1 ±0.01 | pass |
| Rotor speed → disc stress | **+2.010** | +2 ±0.01 | pass |
| Rim radius → disc stress | **+2.010** | +2 ±0.02 | pass |
| Gas + coolant → metal temperature | **0.717 + 0.283 = 1.000** | 1 ±0.01 | pass |
| h_g and H_c | **+0.179 / −0.180** | equal, opposite ±0.01 | pass |

### Findings

151. **The nozzle coefficient is the most powerful number in the cycle, and
     it is not an efficiency.** Its elasticity on sfc is **−2.455**: a 1 %
     error in a discharge coefficient of 0.996 is a **2.5 %** error in
     specific fuel consumption — eight times the leverage of the HP
     turbine's efficiency and forty times the compressor's. It is published
     (CR-168219 Table XI) so the project is not exposed by it, but it means
     the cycle's accuracy is bounded by one coefficient that gets a single
     line in the source and no discussion at all.
152. **The compressor's efficiency barely moves the fuel burn, and the
     reason is the flat rating.** Its elasticity is **−0.059**, against
     −0.327 for the HP turbine. That looks wrong until you notice what the
     cycle solves: the fuel-air ratio is bisected until T41 matches Table
     XII's. A *less* efficient compressor delivers hotter air to the
     combustor, which then needs *less* fuel to reach the same T41, and the
     two effects very nearly cancel. On a fixed-turbine-temperature cycle,
     compressor efficiency buys thrust and stall margin far more than it
     buys sfc — which is exactly why the E³ spent its compressor effort on
     pressure ratio and clearance rather than on peak efficiency.
153. **Only the disc stress leans on a constant nobody measured, and only
     to 21 %.** The sfc and the metal temperature rest **entirely** on
     published values and one fitted conductance; their handbook exposure
     is zero. The disc bore stress is 21.3 % handbook — but that share is
     almost all density, which for a wrought nickel alloy is known to
     better than 1 %, and Poisson's ratio contributes an elasticity of
     0.086, so being wrong about it by 10 % moves the answer by under 1 %.
     **The project's exposure to its own assumptions is small and it is
     concentrated where it does least damage.**
154. **Six elasticities have exact analytic values and the machine returns
     all six.** Combustor efficiency −1, density +1, speed +2, radius +2,
     the two metal temperatures summing to exactly 1.000, and h_g and H_c
     equal and opposite to three figures. That is the step-0 validation:
     a sensitivity study that cannot reproduce the derivatives you can do
     by hand has no business reporting the ones you cannot.

---

## Unit I4 — the digitising uncertainty register

Stage A3's last line: *State a digitising uncertainty per figure from pixel
size and line weight.*

Unit J2 showed why it matters, and showed it the expensive way. Stage E3's
closure asks for blade frequencies within 5 % of the published Campbell
diagrams and gets 1 of 24. But `hpc-rotor-campbell.yaml` records its own
reading precision — half a minor division — and applied per point that is
**±14 % on a 350 Hz line drawn on a 0–6 kHz axis**. Eleven of the
twenty-four comparisons cannot resolve a 5 % band at all. The closure was
never falsifiable on those points, in either direction, and nothing said so
until a figure was drawn (finding 160).

That question — *can this comparison resolve its own band?* — should not
have to wait for someone to plot it. This unit asks it of every closure in
the project at once.

### What this unit does and does not do

**Does not:** state an uncertainty for all 125 figure citations in `data/`.
That needs each figure measured, and it is honest to say it has not been
done rather than to generate a plausible number per figure.

**Does:** build the register from the uncertainties the data files
**actually record**, pair each with the closures that lean on it, and
compute whether the band is coarser or finer than the reading. And count,
explicitly, how many figure-derived comparisons carry **no** recorded
uncertainty — because that count is the real state of Stage A3's last line
and it belongs in the open.

| Check | Requirement | Why |
|---|---|---|
| Every recorded uncertainty is in the register | from `data/`, not restated here | one source of numbers, applied to uncertainties |
| Each is paired with the closures it governs | by the figure it comes from | an uncertainty nobody's closure uses is inert |
| Resolvability is computed, not judged | band vs reading, per comparison | finding 160, generalised |
| The unstated ones are counted | figure citations with no recorded uncertainty | the honest measure of how far A3's last line has got |
| Nothing is invented | a figure with no recorded uncertainty gets `None`, never an estimate | a plausible uncertainty is worse than a missing one, because it looks measured |

**Closes when** every recorded reading uncertainty appears in the register
with the closures it governs and a resolvability verdict, and the count of
figure-derived values with no stated uncertainty is reported rather than
filled in.

### Result — I4

| | |
|---|---|
| Recorded reading uncertainties | **5** |
| Distinct figure citations in `data/` | **263**, across 14 files |
| Citations in a file that records one | 37 — **14 %**, on the generous count |
| Closures governed by a recorded uncertainty | B4, C1, E3, J1, J5 |
| Comparisons that can resolve their own band | E3: **13 of 24**; first flex **0 of 10** |

### Findings

178. **Stage A3's last line is 14 % done, on the generous count.** The
     plan asks for a digitising uncertainty per figure. `data/` cites
     **263 distinct figures** across fourteen files and records **five**
     reading uncertainties. Counting a citation as covered when its *file*
     records one — which is generous, since one uncertainty rarely governs
     every figure in a file — gives 37 of 263. The true per-figure figure
     is lower.

     This is not a new gap; it is an old gap **measured**. It had been
     carried as an unticked line in a work plan, which is a different thing
     from a number. Unit J2 showed what it costs when it bites: eleven of
     E3's twenty-four comparisons cannot resolve the 5 % band they are
     judged against, and **every one of the ten first-flex modes** is in
     that group.

179. **Four of the five recorded uncertainties are prose, and are left as
     prose.** Only `hpc-rotor-campbell.yaml` records something a machine
     can apply per point — half a minor division, per axis, in kHz. The
     others read *"±0.01 on ratios, ±0.005 on Mach and loss, ±0.3° on
     swirl"*, *"±5 kJ/kg"*, *"±0.3 cm"*. Those are usable by a person and
     not by a resolvability test, and turning them into per-point numbers
     would mean deciding which quantity in a closure each clause governs —
     a decision the source did not make. The register carries them as
     written and computes a verdict only where one can honestly be
     computed. **A register that quantified all five would be more useful
     and less true.**


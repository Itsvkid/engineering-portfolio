# Step 0 — ME TF0.01 (Stage L): tolerance and validation case

Per [METHOD.md](../../METHOD.md). Nothing in a step-0 section is edited
after its run; results and findings are appended below it.

---

## Disclosure: a scoping solve preceded this step 0

METHOD.md says the band is written before the run. **On this unit it was
not, and pretending otherwise would be the exact defect this project
exists to avoid.** The honest record:

On 2026-09-10 the owner asked what a higher-bypass derivative of the E³
would cost, before deciding whether to rename the Turbofan Atlas. Answering
that required running the numbers. A scoping solve was done first, and it
returned:

- BPR 6.7 → 10 on a fixed core: fan 2.112 → **2.524 m**, FPR 1.680 →
  **1.468**, sfc **−4.5 %**, LPT specific work **+7.2 %**
- the LP shaft speed the **fan** wants and the speed the **LPT** wants
  differ by a factor of about **1.46** at BPR 10
- 5 LPT stages needs a fan tip relative Mach of about **1.69**; 7 stages
  needs about **1.47**
- the quarter-stage booster's pitch loading roughly **doubles**

So this file cannot claim those as predictions. **What step 0 can still do
is state bands that could fail**, and four of the five below are checks the
scoping solve never made. A band that is only the scoping answer written
back as a target is marked as such and claims nothing.

## Scope, and how this differs from Stage K

They are easy to read as the same question and they are not:

| | Stage K — growth engine | **Stage L — ME TF0.01** |
|---|---|---|
| whose design | **GE's.** The reports say the FPS was sized for it | **the owner's.** Nothing in the reports describes it |
| what moves | T41, T3, pressure, **speed** — the same machine harder | **bypass ratio**, at fixed core and fixed T41 |
| thrust | 15–20 % higher | **same class** (+4.7 % at max climb, a by-product) |
| evidence | published growth requirements, three ratings | none — every number is derived |
| what it tests | does the hardware have the margin GE claims | what a higher-BPR derivative costs |

Stage K asks *how much harder can this engine be pushed*. Stage L asks
*what if it had been a different engine*. **Stage K is a reading of the
reports; Stage L is a design.** Everything Stage L produces is labelled
derived or assumed and none of it is E³ data.

## What is held fixed, and what "the same core" means

The core is held fixed in the strict sense: **the same corrected flow at
the HPC inlet**, which is what makes it the same compressor running at the
same map point. That is a stronger constraint than holding the physical
flow, and it is the one that has physical meaning.

Held: W25 corrected, T25, P25, HPC pressure ratio, T41, all four Table XI
secondary-air streams, combustor ΔP, HPT and LPT efficiencies, mixer
effectiveness, nozzle coefficient. Free: bypass ratio, fan bypass pressure
ratio, fan diameter, LP shaft speed, LPT stage count.

**The closure that makes the excursion physical is the mixer.** A mixed-flow
engine only runs if the core reaches the mixing plane near the bypass total
pressure — the E³ runs 0.95–0.96 at all three ratings. Without that
constraint the LP turbine can be asked for any expansion at all and the
sweep returns nonsense (the scoping run's first attempt drove LPT pressure
ratio to 29 before the constraint was applied). So at every swept point the
fan pressure ratio is solved so that **p5/p13 equals the E³'s own value**,
and the fan pressure ratio is an *output*, not a choice.

## Bands (step 0)

| # | Check | Band | Could it fail? | Level |
|---|---|---|---|---|
| 1 | **The baseline reproduces the E³ before the excursion leaves it.** Run the sweep machinery at BPR 6.7 and it must return the engine, not something near it | sfc within **0.1 %** of Stage B's max-climb solve; fan diameter within **0.5 %** of the published 2.112 m; fan tip relative Mach within **0.02** of the published 1.41; LPT stage count **5.0 ± 0.15** | **yes** — four independent ways, three against published numbers | **L3** |
| 2 | **The mixer closure holds across the sweep.** At every BPR the fan pressure ratio that matches p5/p13 must exist inside a physical bracket | FPR solves strictly inside **[1.05, 1.90]** at every point, and p5/p13 lands within **1e-4** of the baseline | **yes** — the bracket ends are real | L2 (the target is the model's own baseline) |
| 3 | **The LPT stage count falls out of a loading limit, not a choice.** The limit is the E³'s own mean stage loading, computed from Table II's five printed energy extractions and the pitch radii derived from the transcribed airfoil coordinates | the same formula applied to the E³ must return **5.0 ± 0.15** stages, and Table II's Δh sum must agree with the cycle solver's independent LPT specific work to **1 %** | **yes** — two published routes that were never fitted to each other | **L3** |
| 4 | **The fan tip relative Mach stays inside a stated ceiling.** Ceiling **1.45**, fixed here and not adjusted afterwards: the E³'s own fan runs 1.41, and 1.45 is the most a transonic fan of this family should be asked for without its own validation | the reported largest direct-drive bypass ratio must satisfy M_rel ≤ **1.45** at its stated stage count, or the unit reports that no such point exists | **yes** — it is a pass/fail on a number fixed in advance | L2 (a design rule, not a published limit) |
| 5 | **The core really is untouched.** Every core station must be bit-identical across the sweep | W25 corrected, T25, P25, T3, T41 and fuel flow constant to **1e-6** relative | **yes** — trivially, if the constraint is mis-coded | L2 |

Band 4's ceiling is the one number in this unit chosen by judgement rather
than read. It is stated here so that the largest-sensible-BPR answer is a
consequence of it and can be recomputed against a different ceiling.

## What this unit does not do, stated before the run

1. **No off-design re-match.** Every point is a design-point solve with its
   own pressure ratios. Following one match point through component maps is
   not attempted, so takeoff and cruise are not re-matched and only max
   climb is quoted. A real derivative would need fan and turbine maps that
   this project does not have.
2. **Fan efficiency is held at the E³'s published values** at a lower
   pressure ratio and a different tip Mach. That is optimistic for the fast
   direct-drive cases, where the fan is asked for a high tip speed for
   little work. The unit reports the **sfc sensitivity to fan efficiency**
   next to the result so the reader can price the optimism instead of
   guessing at it.
3. **No mass, no cost, no noise, no mechanical design of the new parts.**
   A bigger fan is a heavier fan and this unit does not weigh it, so the
   sfc numbers are uninstalled and un-penalised.
4. **The LPT stage count assumes the E³'s pitch radius.** The unit reports
   what a radius change buys instead, but does not redesign the annulus.

---

## Unit L1 after the run — nothing above was edited; what follows was added

### Results, 2026-09-11 (`cd solvers && python -m derivative.tf001`)

The sweep, fixed core, mixer-matched, booster restaged to hold OPR 38.4:

| BPR | FPR | D_fan m | sfc | Δsfc | F_n kN | LPT kJ/kg | LPT PR | stages @3539 rpm |
|---|---|---|---|---|---|---|---|---|
| **6.7** | 1.680 | 2.112 | 0.05435 | — | 41.02 | 355.6 | 4.55 | **5.02** |
| 7.5 | 1.613 | 2.219 | 0.05358 | −1.41 % | 41.61 | 363.4 | 4.74 | 5.14 |
| 8.0 | 1.577 | 2.283 | 0.05317 | −2.17 % | 41.93 | 367.6 | 4.85 | 5.20 |
| 8.5 | 1.545 | 2.345 | 0.05280 | −2.85 % | 42.22 | 371.5 | 4.95 | 5.25 |
| 9.0 | 1.517 | 2.406 | 0.05247 | −3.46 % | 42.49 | 375.0 | 5.04 | 5.30 |
| **10.0** | 1.468 | 2.524 | 0.05190 | **−4.50 %** | 42.95 | 381.1 | 5.21 | 5.39 |

### Band results

| Band | Result |
|---|---|
| 1 baseline | **met.** sfc 0.00 %, D_fan 2.112 against a published 2.108 (+0.19 %), M_rel 1.405 against 1.41, stage count **5.02** |
| 2 mixer | **met.** p5/p13 within 1e-4 at all eight points, FPR 1.468–1.680, never within 0.4 of a bracket end |
| 3 stage count | **met.** 5.02 at the E3's own speed, and the two routes to the LPT work agree to **0.49 %** (Table II's printed 353.8 kJ/kg against the solver's 355.6, which comes from the fan power and the spool balance and never saw Table II) |
| 4 M_rel ceiling | **met, and it changed the answer — see finding 208** |
| 5 core invariance | **met.** W25 corrected, T25, P25, T3, T41 and fuel flow constant to 1e-6 across the sweep; bypass flow +49 % |

### Findings

206. **A mixed-flow derivative's fan pressure ratio is an output, not a
     choice.** Holding the core fixed and the mixer matched, the bypass
     pressure ratio that BPR 10 permits is **1.468** — it is not selected,
     it is what puts the core and bypass streams at the same total pressure
     at the mixing plane. Remove the mixer constraint and the sweep is
     meaningless: the first scoping attempt drove the LPT to a pressure
     ratio of 29 and reported a 25 % sfc gain, because a design-point solver
     will let the LP turbine expand to any pressure you do not forbid.

207. **The fan and the LP turbine want the shaft at two different speeds,
     and the gap is the whole design problem.** At the E3's own bypass ratio
     they agree: the LPT wants **3548 rpm** for five stages and the fan wants
     **3523 rpm** at its own tip loading — a ratio of **1.007**, which is why
     the E3 is a direct drive and a good one. At BPR 10 the LPT wants
     **3673** and the fan wants **2510**: a ratio of **1.463**. Nothing else
     in this unit is as informative. Every architecture below is a way of
     paying that 46 %, and the stage count, the tip Mach and the gearbox are
     three prices for one quantity.

208. **The ceiling written down in step 0 rejected the answer the scoping
     solve had reached.** Scoping concluded "BPR 10 direct drive closes at
     7 LPT stages", on a tip relative Mach of 1.47 judged acceptable *after*
     seeing it. Step 0 fixed the ceiling at **1.45** — the E3's own fan runs
     1.41 — and against that number 7 stages **fails**: 3104 rpm puts the
     tip at **1.47**, and BPR 10 needs **8 LPT stages** (2904 rpm, M_rel
     1.39) to stay inside. Two points of difference in a Mach number is one
     whole LPT stage. This is exactly the failure mode METHOD.md's
     band-before-run rule exists to catch, and it caught it on this unit.

209. **The largest sensible direct-drive bypass ratio on this core is 8.44.**
     "Sensible" was defined before it was computed: tip relative Mach at or
     under 1.45, and at most one LPT stage more than the E3's five. The
     answer is a boundary, not an estimate — at BPR 8.7 the same six-stage
     turbine puts the fan past the ceiling. For context the GE90 baseline,
     whose architecture this project transcribes for other reasons, runs a
     **6-stage LPT** at a bypass ratio in this region.

210. **The gearbox answer is no, and the number is why.** The fan and LPT
     speeds are 46 % apart at BPR 10, so a reduction of **1.463:1** buys
     back the five-stage turbine. Gear harder and it barely improves:
     **1.64:1** for four stages, **1.89:1** for three. A real geared fan runs
     about 3:1, and it exists because a large fan sits on a small, very fast
     core. Here the core is small *and* the fan is only 2.5 m, so the two
     speeds were never far apart. Spending a 30,000 hp epicyclic, its oil
     system and its certification case to delete two LP turbine stages is a
     bad trade. **Direct drive with a longer turbine is the right answer for
     this core**, and the reason is the ratio, not a preference.

211. **The quarter stage does not survive, and that is the E3 feature the
     derivative loses.** The fan hub and the bypass are the same rotor, so
     dropping the bypass pressure ratio to 1.468 drops the hub's to
     **1.321**; holding the core supercharged at 1.70 then asks the booster
     for **1.287** where it makes 1.129. Pitch loading goes **0.235 → 0.438**,
     a factor of 1.86 and at the diffusion limit for one subsonic stage, so
     it becomes two. The island — the untrapped splitter that centrifuges
     half to two-thirds of ingested debris away from the core, and one of
     the three things that make the E3 distinctive — is gone, replaced by a
     conventional multi-stage booster. **The cheapest way to see what a
     derivative costs is to ask which published feature stops working.**

212. **The blade stress does not bind; the tip Mach does.** A bigger fan
     turns slower, so AN² barely moves: the BPR 10 eight-stage architecture
     puts the untapered root stress at **288 MPa** against the E3's
     **301 MPa** — *lower*. Every architecture in this unit is limited by
     what the fan tip can be asked to do aerodynamically, not by what the
     blade root can carry. Anyone reaching for AN² first on this problem is
     answering the wrong question.

213. **A loading coefficient is frame-invariant only if both its halves are
     in the same frame, and the published numbers are not.** ψ = Δh/U² is
     the same in corrected and physical variables — but the E3's printed
     411.5 m/s tip speed is **corrected** and the cycle solver's Δh is
     **physical**, and dividing one by the other reads ψ low by exactly θ:
     **0.274 against the true 0.306**, an 11 % error, at max climb. The
     scoping solve made this mistake and quoted 0.274. It cancels out of the
     shaft-speed ratio, because both fans are treated the same way, so the
     46 % result was never affected — but any ψ *quoted* from it was wrong.
     Same class as unit 15's error 2, one discipline over: **check which
     frame a published number is in before dividing by it.**

### What is still not verified

Step 0's four exclusions all stand. Two are worth a number rather than a
sentence:

- **No off-design re-match.** Max climb only. Takeoff and cruise would each
  need their own match through fan and turbine maps this project does not
  have, and the bypass ratio at takeoff is not the bypass ratio at climb
  even on the E3 (7.0 against 6.7).
- **Fan efficiency held at the E3's values.** One point of fan efficiency is
  worth **0.68 % of sfc** here. If the BPR 10 fan pays two points against
  the E3's — plausible, since it is a lower-pressure-ratio fan asked for a
  comparable tip speed — the headline **−4.50 % becomes −3.1 %**. That is
  the honest range: **3 to 4.5 % of sfc for a 19 % bigger fan and three more
  LP turbine stages**, uninstalled, unweighed, and on one operating point.

A bigger fan is also a heavier fan and a bigger nacelle. Neither is counted
here, and both take back some of the 3–4.5 %.

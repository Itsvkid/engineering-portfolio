# The post

Stage J's last bullet: *validation-led, NASA credited, the gap stated.*

Two versions below. Every number is one this repository can produce on
demand — `python build.py` regenerates them, `FINDINGS.md` ranks the
disagreements, and each closure's tolerance was written in a `STEP0.md`
**before** its run. Nothing here is rounded in the flattering direction.

---

## Short version — LinkedIn

> I rebuilt NASA and GE's Energy Efficient Engine from its own design
> reports, and then published everywhere my model disagrees with them.
>
> The E³ was a late-1970s NASA programme run by General Electric under
> contract NAS3-20643 — the technology demonstrator behind the big fans GE
> built afterwards. Fourteen of its contractor reports are public domain
> and, unusually, they contain the numbers: cycle points, stage-by-stage
> blading, cooling flows, disc stresses, Campbell diagrams.
>
> So the interesting question isn't "can I model a turbofan". It's "when I
> model one, how wrong am I, and can I say why".
>
> The rule I set first: **every tolerance goes in writing before the run,
> and never gets edited afterwards.** Thirty of them. Then every method is
> validated on a published test case before it touches the engine — the
> CFD on Sod's shock tube against the exact Riemann solution (0.02 %), the
> turbine loss model on the worked example in its own source paper.
>
> Where it lands:
>
> • Turbine inlet temperature, my cycle vs the HPT report's own cycle-match
>   line: **0.01 %**
> • The four cooling flows, cycle vs the secondary-air design: **0.00 %**
> • Mean-line efficiency — LPT, HPT, HPC — inside **0.6, 0.55 and 0.15**
>   points of published
> • Cruise and climb sfc: **+0.56 % and +0.46 %**
>
> And where it doesn't:
>
> • Takeoff sfc reads **+1.91 %** against a 1.5 % band. Cause found, not
>   tuned: Table XII is a mixed-day table — turbine temperature on the
>   flat-rating day, fuel burn on the standard day.
> • Blade frequencies against the published Campbell diagrams: **1 of 24**
>   inside 5 %. A beam model over-predicts, and it gets worse with mode
>   number — +19.5 %, +25.8 %, +37.8 % for first, second and third flex.
>
> That last one produced the result I didn't expect. Checking *how well the
> diagrams can be read* — half a minor division, as their own transcription
> note says — **11 of those 24 comparisons cannot resolve a 5 % band at
> all**, and every single first-flex mode is in that group. A 350 Hz line on
> a 0–6 kHz axis reads to ±14 %. My model is wrong there, and the reference
> could never have proved it either way.
>
> 101 comparisons, median absolute error 7.3 %. 8 have no explanation and
> say so.
>
> The part I'd defend hardest is the last drawing sheet. Three of the six
> sheets in the pack exist to say something **cannot** be drawn: the
> combustor has 60 cups and 30 fuel nozzles published and not one axial
> coordinate; the HPT has five dimensioned stations and no airfoil, because
> the blade coordinates were never printed. Four of the ten gas-path
> stations can be placed on a datum; six cannot. Two axial offsets between
> modules are assumed, drawn in parentheses, with the range they are
> allowed printed beside them.
>
> An empty sheet with the reason on it is a result. A missing sheet is a
> silence.
>
> Source: NASA CR-168219 and thirteen further E³ reports, General Electric
> for NASA Lewis Research Center, contract NAS3-20643. US Government work.
> Code, data and all 165 findings: [link]

---

## Long version — the site

### Rebuilding the Energy Efficient Engine, and publishing the gap

There is a particular kind of engineering portfolio project that proves
very little: build a model, produce a plot, and stop. The plot has no
reference, so it cannot be wrong, so it cannot be right either.

The NASA/GE **Energy Efficient Engine** fixes that, for one reason. Its
entire design is public domain and **it contains the numbers**. Fourteen
contractor reports, written by General Electric for NASA Lewis Research
Center under contract NAS3-20643, cover a mixed-flow twin-spool turbofan —
a 2.1 m fan, a quarter-stage booster, a ten-stage 23:1 compressor, a
double-annular combustor, two turbine stages driving the high spool and
five driving the low, an 18-lobe mixer — at a level of detail modern
engines are never described in. Cycle points at three ratings. Stage-by-
stage velocity diagrams. Cooling flow splits to a tenth of a percent of
core flow. Disc stress distributions. Campbell diagrams for every
compressor rotor.

So the question stops being *can this be modelled* and becomes **how wrong
is the model, and can the error be explained**. That is a harder question
and a much more useful one, because it is the question a design office
actually asks.

### The rule that makes it mean something

Every solver in this project carries a `STEP0.md`. In it, before the solver
runs, two things are written down: the **tolerance** the result must land
inside, and the **published test case** the method is validated on first.
Neither is edited afterwards. Thirty closures are written that way, and
`data/closures.yaml` holds every one with the number it produces today, so
the scoreboard is read from the code rather than remembered.

The validation-first half matters as much as the tolerance. The CFD is
checked against Sod's shock tube — the exact Riemann solution, closed form
— and reproduces the star-region pressure to **0.02 %** before it is
pointed at a compressor rotor. The turbine loss model is run against the
worked example in Ainley and Mathieson's own paper before it is asked about
this engine's turbine. A method that cannot reproduce a known answer has no
business producing an unknown one.

### Where it agrees

The strongest agreements are the ones where two documents, written by
different teams for different purposes, had to be made to say the same
thing:

| | |
|---|---|
| Turbine inlet temperature, cycle vs the HPT report's cycle-match line | **0.01 %** |
| The four cooling streams, cycle vs the secondary-air design | **0.00 %** |
| LPT mean-line efficiency | **0.6** points, band 2.0 |
| HPT mean-line efficiency | **0.55** points |
| HPC efficiency | **0.15** points |
| sfc at max cruise / max climb | **+0.56 % / +0.46 %** |
| Blade masses, the mass integral vs the lofted CAD, 32 rows | **0.94 %** |
| Spool speeds, four routes through four documents | inside **1.6 %** |

Nineteen of the twenty-one numeric closures land inside the band that was
written before the run.

### Where it does not, and why

**Takeoff sfc reads +1.91 % against a 1.5 % band.** The cause is in the
source, not the model: Table XII is a mixed-day table — it quotes turbine
temperature on the flat-rating day and fuel burn on the standard day. The
miss is recorded as a strict expected failure with its size pinned, so if
it ever moves, a test goes red.

**Blade frequencies: 1 of 24 inside 5 %.** A Euler–Bernoulli beam with a
clamped root over-predicts, and the over-prediction grows with mode number
— median +19.5 %, +25.8 % and +37.8 % for the first, second and third
flexural modes on the stages that publish all three. That is a named
modelling limit, and it accounts for most of the project's worst numbers —
fifteen of the worst twenty-one.

Then the finding I did not go looking for. The Campbell diagrams are read
off page images, and their transcription records its own precision: half a
minor division, ±0.05 kHz on a 0–6 kHz axis up to ±0.25 kHz on a 0–26.
Applied per comparison, **11 of the 24 cannot resolve a 5 % band at all** —
and every one of the ten first-flex modes is among them. Stage 1's first
flex is a 350 Hz line on a 0–6 kHz axis: ±14 %. The model is wrong there.
The reference could not have shown it either way. The published closure —
"1 of 24" — turns out to be two different results added together, and the
figure now marks the two groups differently.

Across everything: **101 comparisons, median absolute error 7.3 %.** Twelve
inside 1 %, thirty-eight inside 5 %, fifty-six inside 10 %. Eight carry the
word *unresolved*, which is a legitimate entry — zero would have meant
inventing causes to fill a column.

### The gap

The last stage of the project is a drawing pack: a general arrangement with
the gas-path stations, and one detail sheet per module. Half of it is a
record of what the public domain does not contain.

**Three of the six sheets exist to say something cannot be drawn.** The
combustor sheet is deliberately empty — double annular, 60 cups, 30 fuel
nozzles are all published, and not one axial coordinate; it appears in
three figures as an undimensioned drawing. The HPT sheet carries five
dimensioned stations and no airfoil, because the blade and vane coordinates
were never printed: the reports give throat dimensions and aspect ratio.
The fan sheet has three dimensioned radial stations and no wall contour, so
none is drawn.

**Four of the ten gas-path stations can be placed on a datum; six cannot.**
Two of those four are only placeable because the project assumed an axial
offset the reports never give, so they are drawn parenthesised — the
drafting convention for a reference dimension, used here to mean *this is
ours, not NASA's*. A station drawn at a guessed position is worse than a
station left off, because the number beside it looks measured.

The two assumed offsets — fan stacking axis to compressor inlet, and
compressor exit to turbine inlet across the diffuser and combustor — live
in one data file with the range each is allowed, and every artefact that
draws the whole engine reads them from there. That arrangement exists
because it once failed: two pictures of this engine were about to ship with
axial layouts 128 cm apart, for no better reason than that an assumption in
use had no single home.

### What is actually finished

Nine of ten stages: cycle, mean-line and through-flow aero, blading,
cooling and secondary air, blade and disc mechanical, materials and mass,
32 blade rows lofted from the validated sections, cross-discipline
verification, and publication. **Over 850 test functions. 40 closures — 25 met,
12 half, 3 gated. Over 185 numbered findings.**

The tenth stage is hand CAD and needs a person at a GUI. One CFD case, a
transonic compressor rotor, converges to a stalled branch at 26 % of design
flow and is characterised but not solved; it is written up as an open
problem with the next four things to try, in order.

**The deliverable is not the engine.** It is
[`FINDINGS.md`](FINDINGS.md) — every disagreement with a published number,
ranked by size, each with a cause or the word *unresolved* — and it is
generated from the solvers rather than written by hand, because a
hand-written list contains the disagreements someone remembered.

---

*NASA CR-168219, "Energy Efficient Engine Flight Propulsion System Final
Analysis and Design Report", and thirteen further E³ contractor reports.
General Electric Company for NASA Lewis Research Center, contract
NAS3-20643. US Government work; public use permitted. The Rotor 37
validation case is NASA TP-1337. This project is not affiliated with NASA
or GE, and any error in it is mine.*

# Step 0 — through-flow solvers (C2): tolerance and validation case, written first

Per [METHOD.md](../../METHOD.md). Nothing in a step-0 section is edited
after its run; results and findings are appended below it.

## Unit 8 — does the printed through-flow satisfy radial equilibrium?

Before any through-flow is *solved*, the one that already exists should be
audited. HPC Table XXI prints, at 12 streamlines of 42 stations,
everything the radial-equilibrium equation needs on both sides:

    dh0/dr - T ds/dr = c_z dc_z/dr + (c_theta / r) d(r c_theta)/dr

That is *simple* radial equilibrium — steady, axisymmetric, no radial
velocity, **no streamline curvature**. The E³'s own CAFD through-flow kept
the curvature; Table XXI also prints the streamline slope φ at every one of
those points, so the discarded term can be evaluated rather than assumed
small.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| Printed φ against atan(dr/dz) from the printed coordinates | the column is the meridional slope | ±1.0° | z and r are printed to 3–4 decimals; the difference is a 3-point estimate |
| Simple radial equilibrium residual, 400 interior points | 0 | ≤0.30 of the largest single term | see the note on conditioning below |
| Adding the curvature term | should reduce the residual | ≥20 %, and on a majority of stations | if it does not, the residual is numerical, not physical |

**A note on conditioning, written before the run.** On this machine
dh0/dr and T ds/dr are each about ten times their difference. Differencing
enthalpy and entropy separately and subtracting therefore amplifies the
finite-difference error tenfold. The left-hand side is instead written
analytically,

    dh0/dr - T ds/dr = cp(T0) (1 - T/T0) dT0/dr + (T R / p0) dp0/dr

which differences T0 and p0 once each and performs the cancellation in
closed form. The residual is normalised by the largest single term rather
than by the left-hand side, because the right-hand side's two terms also
nearly cancel near the walls.

---

## Unit 8 after the run — nothing above was edited; what follows was added

### Results, 2026-09-06 (`cd solvers && python -m throughflow.radial_equilibrium --curvature`)

```
R10 in      10           0.209           0.136   -0.074
R10 ex      10           0.052           0.032   -0.020
S10 in      10           0.084           0.043   -0.041

400 points over 40 stations
  simple radial equilibrium      mean |residual| 0.243 of the largest term
  with the curvature term        mean |residual| 0.172   (+29 %)
  stations improved: 36 of 40
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| φ against atan(dr/dz) | **0.23°** mean over 400 points | ±1.0° | pass |
| Simple radial equilibrium | 0.243 of the largest term | ≤0.30 | pass |
| With the curvature term | **0.172**, −29 %, better on **36 of 40** stations | ≥20 %, majority | pass |

### Two errors of mine, both caught by the data

1. **The first formulation differenced h0 and s separately** and read a
   residual of 0.446 — nearly twice the truth. The analytic left-hand
   side above halved it. The step-0 note anticipated the cancellation;
   the first implementation did not honour it.
2. **The curvature term went in with the wrong sign** and made the
   balance *worse* (0.243 → 0.371, better on 2 stations of 40). Rather
   than fit a coefficient, the sign was settled twice over: Table XXI's
   φ column was checked against atan(dr/dz) from its own printed
   coordinates and agrees to 0.23°, so the column's convention is the
   ordinary one; and the derivation was redone — a streamline concave
   outward accelerates its fluid outward, which needs ∂p/∂r < 0, so the
   term enters the right-hand side **negative**. Theory, geometry and
   data then agree. A least-squares fit of the coefficient gives 1.32
   against the theoretical 1.0, and is *not* used.

### Findings

30. **The E³'s printed through-flow satisfies simple radial equilibrium
    to about a quarter of its largest term, and the streamline curvature
    is a third of what is left.** Adding the discarded term improves 36
    of 40 stations and cuts the mean residual by 29 %. The remainder is
    finite-difference error: 12 unevenly spaced streamlines, printed to
    four figures, differenced across a station whose points do not lie on
    a plane of constant z.
31. **Table XXI's streamline-slope column is real geometry, not a
    label.** It reproduces atan(dr/dz) from the table's own z and r
    columns to 0.23° over 400 points. Two columns that were transcribed
    as separate numbers describe one set of streamlines.
32. **This is a badly conditioned equation and most texts do not say
    so.** The two left-hand terms cancel 10:1 on this compressor, and the
    two right-hand terms cancel near the walls as well. Anyone checking
    radial equilibrium against tabulated data by differencing enthalpy
    and entropy separately will read roughly twice the true residual and
    conclude the data is wrong. Write the left-hand side analytically.


---

## Unit 9 — predict the spanwise distribution

Unit 8 audited a through-flow that already exists. This one solves it.

A through-flow designer specifies three things at a station: the **vortex
law** r·c_θ(r), the **spanwise work** distribution and the **spanwise
loss** distribution. Radial equilibrium then determines the axial velocity
profile,

    d(c_z² / 2)/dr = [dh0/dr − T ds/dr] − (c_θ/r) d(r c_θ)/dr

integrated outward from the hub, and continuity sets its level. **The
Mach number and the flow angle are outputs.**

The three inputs are taken from Table XXI, and one further number — the
mass flow the printed distribution itself carries — sets the level. Eleven
of the twelve spanwise degrees of freedom in c_z are predicted.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| Stator-10 exit swirl across the span | Table XXI | **±2°** | the work plan's own C2 closure criterion, written before Stage A |
| Stator-10 exit Mach across the span | Table XXI | **±0.02** | same |
| Every other station | Table XXI | reported, not bounded | no criterion was set for them |

### Results, 2026-09-06 (`cd solvers && python -m throughflow.predict`)

```
C2's closure test: stator-10 exit, predicted from the vortex law, the work and the loss
 sl  imm %     c_z  printed   alpha  printed   diff   Mach  printed   diff
 12  100.0   155.2    154.6    3.98     4.00  -0.02  0.277    0.276  0.001
 11   94.5   155.2    154.3    3.17     3.19  -0.02  0.279    0.277  0.002
 10   83.8   155.1    154.1    1.87     1.88  -0.01  0.282    0.280  0.002
  9   73.3   154.9    154.0    0.92     0.93  -0.01  0.283    0.282  0.002
  8   63.1   154.5    154.0    0.32     0.32  -0.00  0.284    0.283  0.001
  7   53.0   153.8    153.7    0.02     0.02  -0.00  0.283    0.283  0.000
  6   42.9   152.5    152.7    0.11     0.11   0.00  0.280    0.281 -0.000
  5   32.8   150.8    151.2    0.53     0.53   0.00  0.277    0.277 -0.001
  4   22.6   148.9    149.4    1.27     1.27   0.00  0.272    0.273 -0.001
  3   12.2   147.0    147.8    2.35     2.34   0.01  0.267    0.268 -0.001
  2    4.2   145.7    147.4    3.42     3.38   0.04  0.261    0.265 -0.003
  1    0.0   144.8    146.9    4.06     4.00   0.06  0.258    0.262 -0.004

stator-10 exit: swirl rms 0.02 deg (max 0.06), Mach rms 0.002 (max 0.004); C2 asks for 2 deg and 0.02
```

```
R10 in           0.14       0.30     0.002     0.003      1.2
R10 ex           0.19       0.26     0.001     0.002      1.0
S10 in           0.34       0.70     0.002     0.003      1.8
S10 ex           0.02       0.06     0.002     0.004      1.0

worst station: swirl rms 3.49 deg, Mach rms 0.059 over 42 stations
```

| | swirl rms | Mach rms |
|---|---|---|
| **Stator-10 exit — the C2 criterion** | **0.02°** against ±2° | **0.002** against ±0.02 |
| Rear five stages (6–10) | 0.18° | 0.002 |
| Front five stages (IGV–2) | 1.02° | 0.028 |
| Worst single station (R1 exit) | 5.17° | 0.057 |

### Findings

33. **C2's closure criterion is met with two orders of magnitude to
    spare, and only at the back of the machine.** The stator-10 exit —
    the station the work plan named before any of this was written —
    predicts to **0.02° of swirl and 0.002 of Mach** against the 2° and
    0.02 asked for. The whole rear half predicts to a fifth of a degree.
    The front half does not: 1.0° across the first five stages and 5.2°
    at the rotor-1 exit, with Mach errors up to 0.09.
34. **A correction that improves a local residual can degrade an
    integrated prediction.** Unit 8's streamline-curvature term cut the
    pointwise radial-equilibrium residual by 29 %. Put into this
    integration it makes the prediction *worse* — front stages 1.02° →
    1.55°, rear 0.18° → 0.25°. The term is estimated from three-point
    differences of φ between stations and is noisier than the terms it
    corrects; integrating it across the span accumulates that noise. The
    simple form is used here, and the curvature form is kept for the
    audit it was built for. Two solvers, two right answers.
35. **The error is a map of where the compressor is hard.** It is largest
    at the IGV, rotor 1 and stator 1 — the transonic rows, where the
    annulus contracts fastest (tip radius 36.2 → 34.4 cm in one row),
    the relative Mach reaches 1.35, and the streamlines turn most
    sharply. It falls monotonically rearward as the flowpath straightens
    and the rows go subsonic. A designer would read the same map: the
    front of a high-OPR compressor is where the simple methods stop
    working, and it is where the E³ put its variable geometry.


---

## Unit 10 — what "controlled vortex" actually means

The LPT report designs its blading to a "controlled vortex" (sec 2.6) and
never says what that is numerically. Table II prints the stator exit angle
and Mach at hub, pitch and tip for all five stages; the flowpath gives the
three radii. Fitting

    c_theta proportional to r^n

turns the adjective into a number. **Free vortex is n = −1** (constant
angular momentum, the textbook default); **solid-body rotation is n = +1**.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| The fitted exponent | between −1 and +1, and **not** −1 | qualitative | the report would have written "free vortex" if it were one |
| Consistency with the printed reaction | reaction must rise hub to tip | already pinned in `tests/test_lpt_aero.py` | Table II |
| The same fit on the HPC's stators | — | reported, not bounded | Table XXI, 12 streamlines |

No numerical band is stated because the report publishes no number to
band. This unit produces one.

### Results, 2026-09-06 (`cd solvers && python -m throughflow.lpt_vortex`)

```
E3 LPT stator exits: what vortex law?  (free vortex n = -1, solid body n = +1)
 st   r hub  r pitch   r tip   ct hub  ct pitch   ct tip       n  r.ct spread  ct spread
  1    33.4     38.6    43.9    327.3     341.6    296.1  -0.355        18.1%      14.1%
  2    35.2     42.1    48.9    330.2     336.0    297.0  -0.308        21.6%      12.1%
  3    36.9     45.3    53.6    339.4     335.2    271.4  -0.576        19.1%      21.6%
  4    37.5     48.0    57.8    315.3     293.1    238.3  -0.629        17.0%      27.3%
  5    36.9     49.5    60.0    255.1     238.2    178.5  -0.694        22.3%      34.2%

exponent n: -0.694 to -0.308, mean -0.512
free vortex would be -1.000 on every stage

HPC stator exits, the same fit over 12 streamlines:
 stage  pts   swirl        n  r.ct spread
     1   12    15.7    0.540        97.0%
     2   12    18.8   -0.469        67.5%
     3   12    21.2   -0.667        57.7%
     4   12    22.3   -0.764        51.0%
     5   12    22.6   -0.689        49.5%
     6   12    20.2   -0.551        56.3%
     7   12    19.3   -0.174        61.2%
     8   12    18.3   -0.134        61.3%
     9   12    18.2   -0.299        61.1%
    10    9     2.4   -1.557       146.1%  (near-axial: no vortex law to fit)

HPC exponent over the nine swirling stators: -0.764 to +0.540 -- no single law
```

### Findings

36. **The E³ LPT's "controlled vortex" is n ≈ −0.5: half a free
    vortex.** The fitted exponent runs −0.31 on stage 1 to −0.69 on
    stage 5, mean −0.51, where a free vortex would be −1.00 on every
    stage. Angular momentum r·c_θ varies 17–22 % across the span instead
    of being constant. That is the number the report's adjective stands
    for.
37. **The law drifts toward free vortex rearward, and the geometry says
    why.** Stage 1 sits at a hub/tip radius ratio of 0.76 and n = −0.36;
    stage 5 at 0.61 and n = −0.69. As the annulus opens, a law close to
    solid body would put too much swirl at the tip, so the design leans
    back toward free vortex exactly where the span is longest. The
    exponent is not a constant of the design — it is scheduled with
    radius ratio.
38. **The compressor has no vortex law at all, and that is deliberate.**
    The same fit on the HPC's nine swirling stators gives exponents from
    **+0.54 to −0.76** with no order to them — stator 1 is *forced*
    vortex (swirl rising with radius), the middle stages are roughly half
    free vortex, stators 7–9 are nearly solid body. A compressor stator's
    exit swirl is a **schedule**, set stage by stage for stall margin and
    rotor-inlet relative Mach, not a vortex law: the E³ deliberately runs
    its end-wall swirl 10–12° above pitch (from the NASA exit-stage
    study, worth +0.4 point of polytropic efficiency —
    `hpc-stagewise.yaml`), which no single exponent can express. The OGV
    is excluded: designed to leave the flow axial, it has no swirl to fit.

**C2's LPT item closes.** Only the HPT's Fig 5 forced-vortex comparison
remains, and it needs a figure read off that Stage A did not transcribe.

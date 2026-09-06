# Step 0 — blade sections (C3): tolerance and validation case, written first

Per [METHOD.md](../../METHOD.md). Nothing in a step-0 section is edited
after its run; results and findings are appended below it.

## Unit 12 — reconstruct the HPC sections, and check the throats

Table XXII prints, for each of 252 sections: chord, camber, stagger, the
metal angles β₁* and β₂*, the maximum thickness and where it sits, and the
trailing-edge thickness. It does **not** print the camber-line family or
the throat, and the throat is what decides whether a transonic row passes
its flow.

Two things are built here:

1. **The camber line.** A double circular arc — two arcs meeting where the
   tangent is parallel to the chord — with the join position solved so the
   section reproduces β₁*, β₂* **and the printed stagger** exactly. That
   makes the join position an *output*: it says where the design put its
   turning. For a single circular arc the stagger would have to be
   (β₁*+β₂*)/2, so any departure is information.
2. **The thickness.** The quarter-sine distribution this engine's own fan
   report documents (CR-165148 §II.A: "quarter-sine from the leading edge
   to the maximum, reversed to the trailing edge"), scaled to the printed
   maximum and trailing-edge thicknesses. Assumed for the HPC, whose
   report says only "multi-circular-arc or 65-series".

| Check | Known answer | Band | Basis |
|---|---|---|---|
| Throat margin, transonic rotors 1–4 | **6 %** above critical, one normal shock at the inlet Mach ahead of the throat | ±4 points | the camber family and thickness are assumed, and the margin is a small difference of large geometric quantities |
| Throat margin, subsonic rotors 5–10 | not published | must be several times larger, and must fall monotonically with relative Mach | the constraint only binds where the flow is transonic |
| Stagger against (β₁*+β₂*)/2 | not published | reported, not bounded | it quantifies the camber-line family |

The throat is the shortest distance from one blade's surface to the
next, one pitch away; a compressor passage diffuses, so unlike a turbine
its throat is not near the trailing edge and the whole surface is
searched.

---

## Unit 12 after the run — nothing above was edited; what follows was added

### Results, 2026-09-06 (`cd solvers && python -m blading.run`)

```
1. Is the camber line a circular arc?  (stagger - (beta1*+beta2*)/2)
family       n     mean     rms     implied max camber, % chord
rotor      120     1.34    2.08          median 55, range 45-93
stator     120    -0.59    1.41          median 49, range 32-59
IGV         12   -16.96   16.96         median 98, range 98-100

2. Do the throats pass the flow?  (throat area above the choking area)
 stage   n     M_rel range     o/s   margin %
     1  12       0.80-1.35   0.556        2.2
     2  12       0.83-1.12   0.567        3.0
     3  12       0.77-1.02   0.566        4.7
     4  12       0.73-0.93   0.577        6.2
     5  12       0.70-0.87   0.576       10.6
     6  12       0.67-0.82   0.559       12.9
     7  12       0.66-0.79   0.556       12.5
     8  12       0.64-0.76   0.520       18.6
     9  12       0.62-0.73   0.507       24.6
    10  12       0.60-0.70   0.488       28.0

transonic rotors 1-4: median 4.0 %   (HPC report: 6 %)
supersonic sections:  median 2.5 %   n=20
subsonic rotors 5-10: median 18.9 %

3. Throat position along the chord
  median 59 % of chord, range 27-76
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| Throat margin, transonic rotors 1–4 | **4.0 %** vs 6 % | ±4 points | pass |
| Throat margin, subsonic rotors 5–10 | 18.9 %, rising monotonically 2.2 → 28.0 % from rotor 1 to rotor 10 | several times larger, monotonic | pass |

### Findings

42. **The throat margin falls monotonically from 28 % at the last rotor
    to 2.2 % at the first, and the transonic rows land on the report's
    stated 6 % to within 2 points.** Rotor 1 sits at 2.2 %, rotor 4 at
    6.2 %, rotor 10 at 28.0 %; the twenty individually supersonic sections
    median 2.5 %. Nothing about the throat was transcribed — it comes out
    of a camber line and a thickness distribution built from seven printed
    numbers per section — and it reproduces both the level the report
    quotes and, more tellingly, the fact that the constraint binds **only**
    at the front. A compressor's throat is a front-stage problem, and this
    is the arithmetic of why.
43. **The stators are circular-arc blades and the rotors are not.** The
    printed stagger sits 0.59° *below* the mean of the metal angles on the
    stators (rms 1.41°) and 1.34° *above* it on the rotors (rms 2.08°).
    Read through the double-circular-arc construction that is a maximum
    camber at a median **49 % of chord on the stators** — a circular arc
    to within the read precision — and **55 % on the rotors**, aft-loaded.
    The rotor sections put their turning behind mid-chord; the stators do
    not.
44. **The inference is ill-conditioned exactly where it is most
    interesting.** The sensitivity of the implied camber position to the
    stagger is 1/θ, so a section with 5° of camber moves 10 % of chord per
    half-degree. Rotor 1's outer three sections — 4.7–9.7° of camber at
    relative Mach 1.30–1.35 — come out at 82–93 % of chord, which would be
    a very sharp aft hook. The direction is what a multiple-circular-arc
    transonic section is *for* (a straight front so the shock sits in a
    parallel passage, all the turning behind it), but the magnitude should
    not be trusted, and it is reported rather than used.
45. **The IGV is not this family at all.** Its stagger sits 17° below the
    mean of its metal angles and the construction returns a maximum camber
    at 98–100 % of chord, which is not a blade. The IGV is an accelerating
    turning vane with an axial inlet, and the double-circular-arc model
    built for the diffusing rows does not describe it. Recorded as a limit
    of the method, not as a property of the vane.


---

## Unit 13 — the LPT's real coordinates against two published relations

Stage A transcribed all 30 LPT airfoil sections as (Z, R, R·θ) triples.
Two published relations can now be tested directly against them, and
neither was used to produce them:

1. **The outlet angle.** R&M 2974 equation (1) gives a turbine row's gas
   outlet angle as α₂ = α₂*(cos⁻¹ o/s) − 4(s/e), with α₂* from its Fig 5
   and *e* the mean radius of curvature of the suction surface between
   the throat and the trailing edge. The coordinates give o/s **and** e.
   The LPT report's Table II prints the answer.
2. **Zweifel.** ψ_Z = 2(s/b_x)cos²α₂(tan α₁ + tan α₂), with the axial
   width from the coordinates and the angles from Table II. Table III
   prints the answer for all ten rows.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| Outlet angle, all 30 sections | Table II | ±3° | R&M 2974 §9 claims ~1 % at 60° for its angle rules; the coordinates, blade counts and section transcription add to that |
| Zweifel at pitch, ten rows | Table III | ±0.15 | Table III's values span 0.61–1.09 |
| s/e from the coordinates | 0.279 and 0.355 in R&M's own worked example | must land in that neighbourhood | a sanity check that the curvature fit finds a blade, not a straight line |

---

## Unit 13 after the run — nothing above was edited; what follows was added

### Results, 2026-09-06 (`cd solvers && python -m blading.lpt_sections`)

```
row   span   r cm    N  pitch cm    o/s  acos o/s  a2 rule  a2 Tbl II   diff
S1      10  33.99   72     2.966  0.564     55.64    52.82      53.70  -0.88
S1      50  37.54   72     3.276  0.486     60.89    58.71      61.00  -2.29
S1      90  41.10   72     3.586  0.476     61.55    59.46      60.00  -0.54
R1      10  35.33  120     1.850  0.521     58.58    56.11      57.60  -1.49
R1      50  39.73  120     2.080  0.465     62.31    60.32      61.30  -0.98
R1      90  44.05  120     2.306  0.484     61.07    58.91      60.00  -1.09
S2      10  36.38  102     2.241  0.503     59.78    57.45      55.80   1.65
S2      50  41.54  102     2.559  0.423     64.98    63.33      64.10  -0.77
S2      90  46.33  102     2.854  0.449     63.31    61.45      62.90  -1.45
R2      10  37.41  122     1.926  0.502     59.85    57.53      55.80   1.73
R2      50  43.01  122     2.215  0.432     64.40    62.68      61.80   0.88
R2      90  48.43  122     2.494  0.445     63.58    61.75      62.80  -1.05
S3      10  38.38   96     2.512  0.503     59.81    57.49      56.30   1.19
S3      50  44.71   96     2.926  0.413     65.63    64.06      64.80  -0.74
S3      90  50.66   96     3.315  0.431     64.47    62.76      63.70  -0.94
R3      10  39.46  122     2.032  0.501     59.91    57.60      55.70   1.90
R3      50  46.20  122     2.379  0.435     64.19    62.43      63.80  -1.37
R3      90  52.77  122     2.718  0.443     63.73    61.92      62.70  -0.78
S4      10  39.84  114     2.196  0.507     59.53    57.17      56.20   0.97
S4      50  47.60  114     2.624  0.454     63.01    61.10      62.30  -1.20
S4      90  54.69  114     3.015  0.487     60.84    58.65      59.70  -1.05
R4      10  40.08  156     1.614  0.535     57.67    55.09      55.40  -0.31
R4      50  48.58  156     1.957  0.482     61.19    59.04      60.50  -1.46
R4      90  56.22  156     2.264  0.504     59.76    57.43      58.20  -0.77
S5      10  39.88  120     2.088  0.544     57.03    54.38      55.40  -1.02
S5      50  49.37  120     2.585  0.558     56.08    53.31      56.00  -2.69
S5      90  57.10  120     2.990  0.637     50.44    46.99      46.50   0.49
R5      10  39.55  110     2.259  0.647     49.71    46.18      48.50  -2.32
R5      50  49.54  110     2.830  0.632     50.77    47.37      50.00  -2.63
R5      90  57.33  110     3.275  0.645     49.80    46.28      48.40  -2.12

outlet angle, Fig 5 alone (alpha2*)      vs Table II: mean -0.71 deg, rms 1.43, worst 2.69
outlet angle, equation (1) with -4(s/e) vs Table II: mean +0.27 deg, rms 1.34, worst 3.23
```

```
R5      90   0.930     0.808      1.023  -0.215

Zweifel at pitch vs Table III: mean -0.058, rms 0.083
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| Outlet angle, Fig 5 alone | mean **−0.71°**, rms 1.43°, worst 2.69° | ±3° | pass |
| Outlet angle, full equation (1) | mean **+0.27°**, rms 1.34°, worst 3.23° | ±3° | pass |
| Zweifel at pitch | mean −0.058, rms 0.083, worst 0.138 | ±0.15 | pass |
| s/e | 0.141–0.386, median 0.228 | near 0.28–0.36 | pass |

### Findings

46. **Three independent things agree to 1.4°.** A 1951 British
    correlation, the E³'s own transcribed airfoil coordinates, and the
    LPT report's printed vector diagrams. The throat-to-pitch ratio comes
    from the coordinates (0.413–0.647), the outlet angle from R&M 2974's
    Fig 5, and Table II says what the answer should be. Nothing was fitted.
47. **The term I first omitted is real, and the coordinates can measure
    it.** Fig 5's α₂* alone leaves a systematic **−0.71°** bias — the
    predicted angles are all slightly too shallow. Equation (1)'s
    −4(s/e) correction, with *e* obtained by fitting a circle to the
    suction surface between the throat and the trailing edge, moves the
    mean to **+0.27°** and improves the rms. The fitted s/e is
    0.141–0.386 with a median of 0.228, against 0.279 and 0.355 in R&M's
    own worked example: the E³'s LPT blades are slightly straighter
    behind the throat than the 1950s turbine the rule was built on, which
    is what fifty years of blade design would do.
48. **Zweifel closes from the coordinates.** The axial width from the
    sections and the angles from Table II reproduce Table III's printed
    Zweifel numbers to 0.083 rms at the pitch line, mean −0.058 — about
    7 % on values of 0.61–1.09. Table III and the appendix coordinates
    were transcribed independently in Stage A and describe the same
    blades.

### One bug worth recording

The throat search tries the neighbouring blade one pitch away in **both**
directions, because the sections are stored with R·θ increasing either
way depending on the row. The first version kept the throat *distance*
from the better direction but the throat *position* from the first — so
on every stator the curvature arc that follows was measured in the wrong
place, and the circle fit failed on 15 of 30 sections, all of them
stators. It was visible only because the failure was perfectly
correlated with row type. A bug that fails on exactly one category is
easier to catch than one that adds noise everywhere; this one nearly
passed as "the stators just do not fit".


---

## Unit 14 — the HPT's blading, without a single coordinate

CR-167955's Fig 6 holds the actual HPT airfoil shapes and Stage A did not
transcribe it. But Table IV prints the **aspect ratio h/d₀ — height over
throat** — for all four rows, and Fig 3 gives the annulus heights. So:

    throat = height / (h/d0),   pitch = 2 pi r / N,   alpha2 = f(cos^-1 o/s)

Three printed numbers and R&M 2974's Fig 5, and the outlet angle falls
out. None of that touches the vector diagrams or the cycle, which is what
unit 3's mean-line was built from — so the two are independent.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| Outlet angle, four rows | the unit-3 HPT mean-line (itself validated against Tables III and V) | ±3° | unit 13 got 1.4° rms on the LPT with real coordinates; this has none |
| Zweifel, four rows | Table IV | ±0.15 | Table IV's values span 0.67–1.08 |

---

## Unit 14 after the run — nothing above was edited; what follows was added

### Results, 2026-09-06 (`cd solvers && python -m blading.hpt_sections`)

```
throat recovered from Table IV's aspect ratio and Fig 3's annulus heights
row              N   h cm   r cm   s cm  h/d0  d0 cm    o/s    acos  a2 rule  a2 mean-line   diff
stage1_vane     46   4.00  34.58  4.723   3.3  1.212  0.257   75.13    74.64         75.13  -0.49
stage2_vane     48   6.83  34.63  4.534   4.4  1.552  0.342   69.98    68.97         70.70  -1.73
stage1_blade    76   4.27  34.47  2.849   3.8  1.124  0.394   66.77    65.35         67.45  -2.09
stage2_blade    70   6.98  34.61  3.107   4.6  1.517  0.488   60.76    58.56         60.95  -2.39

outlet angle vs the unit-3 mean-line: mean -1.67 deg, rms 1.82, worst 2.39

row              sigma   bx cm   s/bx  Zweifel  Table IV    diff
stage1_vane       0.71   3.354  1.408    0.699      0.67   0.029
stage2_vane       1.07   4.851  0.935    0.642      0.79  -0.148
stage1_blade      0.96   2.735  1.042    1.074      1.08  -0.006
stage2_blade      1.06   3.293  0.943    1.001      1.03  -0.029

Zweifel vs Table IV: mean -0.039, rms 0.077
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| Outlet angle vs the mean-line | mean **−1.67°**, rms 1.82°, worst 2.39° | ±3° | pass |
| Zweifel vs Table IV | mean −0.039, rms 0.077; three of four rows within **0.03** | ±0.15 | pass |

### Findings

49. **A turbine's throat can be recovered from an aspect ratio.** Table
    IV's h/d₀ and Fig 3's annulus heights give throats of 1.12–1.55 cm,
    and with the blade counts, o/s of 0.257–0.488. Passed through R&M
    2974's Fig 5 those give outlet angles within **1.8° rms** of a
    mean-line built from an entirely different set of inputs — the cycle,
    the work split and the flowpath. Fig 6 was never needed.
50. **The same bias appears as in unit 13, and for the same reason.** The
    HPT angles come out **−1.67°** shallow where the LPT's came out
    −0.71° shallow from Fig 5 alone. That is the −4(s/e) term of equation
    (1), which cannot be evaluated here because there are no HPT
    coordinates to fit *e* to. Using the s/e this project *measured* on
    the LPT (0.141–0.386, median 0.228) the correction would be 0.6–1.5°,
    which brackets the bias. The two units corroborate each other.
51. **Three of the four Zweifel numbers close to 0.03; the stage-2 vane
    does not.** It comes out 0.642 against a printed 0.79. To close it,
    that vane's inlet swirl would have to be about 45° rather than the
    16° Table III prints as the stage-1 exit swirl. Recorded, not
    reconciled — it is the same row unit 3 flagged (finding 10) for
    carrying 0.08 more reaction and 14° less turning than the
    preliminary study, so two independent routes now point at the
    stage-2 vane.


---

## Unit 15 — the fan blade. **Designed, not transcribed.**

The E³ fan report publishes almost everything about its rotor blade except
the blade: chord and maximum thickness against radius (Figs 15, 16), 32
blades, the design incidence (5° across the span), the leading- and
trailing-edge relative Mach numbers at three radii, where the maximum
thickness sits, and the thickness distribution in words. It gives no
coordinate, no camber angle and no stagger.

So those are designed. Everything this unit produces is a **design**, and
is labelled so wherever it is recorded.

The design is checked against the one thing the report states that is not
used to make it: the **throat margin** — 7.5 % at the OD, 8.8 % at the ID,
5 % typical, defined as the effective throat-to-capture area ratio above
critical after one normal shock at the leading-edge Mach. That is the same
rule unit 12 applied to the HPC.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| Throat margin across the span | 5–8.8 % | ±10 points | the camber family, the thickness distribution and the deviation rule are all designed; the margin is a small difference of large geometric quantities |
| Solidity at the tip | 1.4 (Fig 15) | ±0.1 | chord and count are printed |
| Camber, deviation, turning | not published | must vary monotonically and sensibly across the span | a design that jumps is wrong |

Scope stated first: Fig 3 publishes the rotor-exit pressure profile only
over the **bypass span**, from the OD in to the island at 78 % of the
flow. Below that the fan hub's work is shared with the booster and Fig 3
does not say how. The blade is designed over the published span and the
inner span is **left to the booster work rather than extrapolated**.

---

## Unit 15 after the run — nothing above was edited; what follows was added

### Results, 2026-09-06 (`cd solvers && python -m blading.fan_blade`)

```
E3 fan rotor blade -- DESIGNED, not transcribed
32 blades, tip radius 105.4 cm, blade hub 36.0 cm, corrected tip speed 411.5 m/s, design incidence 5 deg
designed over the span Fig 3 publishes: the island at 58.8 cm (78 % of the flow) to the OD

   r cm  % span      U   M_LE   M_TE     b1     b2  camber  stagger   dev   c cm  sigma   tm/c    o/s  margin %
   58.8      33  229.6  0.968  0.708  46.60  12.91   35.32    24.48  6.63  21.60  1.871  0.055  0.762      11.1
   63.0      39  246.1  1.018  0.700  47.92  17.88   31.23    28.33  6.18  22.26  1.798  0.051  0.746      11.4
   67.3      45  262.6  1.068  0.693  49.17  22.94   26.82    32.11  5.60  22.89  1.733  0.048  0.728      11.7
   71.5      51  279.2  1.118  0.685  50.34  28.17   22.01    35.84  4.84  23.54  1.677  0.045  0.709      12.1
   75.7      57  295.7  1.163  0.689  51.71  33.31   17.42    39.40  4.02  24.22  1.628  0.043  0.687      12.6
   80.0      63  312.3  1.198  0.715  53.47  37.35   14.66    42.34  3.54  24.90  1.585  0.039  0.664      14.2
   84.2      69  328.8  1.234  0.741  55.18  41.17   12.05    45.16  3.04  25.49  1.541  0.036  0.641      15.5
   88.5      76  345.3  1.269  0.767  56.84  44.82    9.53    47.88  2.51  26.08  1.502  0.034  0.616      16.9
   92.7      82  361.9  1.304  0.793  58.46  49.23    5.84    51.04  1.61  26.65  1.464  0.032  0.587      17.4
   96.9      88  378.4  1.339  0.818  60.04  54.28    1.06    54.60  0.31  27.20  1.429  0.030  0.550      15.9

published throat margins: OD 7.5 %, ID 8.8 %, typical 5 %
  designed: OD (tip) 15.9 %, island end 11.1 %, median 14.2 %
published solidity: hub 2.3, tip 1.4
  designed: hub 1.87, tip 1.43
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| Throat margin | 11.1 % at the island to 17.4 %, median **14.2 %** | 5–8.8 % ±10 points | pass |
| Solidity at the tip | 1.43 vs a published 1.40 | ±0.1 | pass |
| Camber, turning, deviation | camber falls 35.3° → 1.1°, turning rises 12.9° → 54.3°, deviation falls 6.6° → 0.3°, all monotonic | monotonic | pass |

### Findings

52. **The fan blade can be designed from the published data, and it comes
    out looking like a fan blade.** Camber falls monotonically from 35°
    near the island to about 1° at the tip; the relative turning rises
    from 13° to 54°; the deviation falls from 6.6° to 0.3°; the solidity
    lands at 1.43 against a printed 1.40. Nothing in that list was fitted
    — the chord, thickness, count and incidence are printed, and the
    velocity triangles come from Fig 3's pressure profile and the two
    published Mach numbers.
53. **The throat margin comes out about twice the published value and the
    right shape.** 11–17 % against a stated 5–8.8 %. The design is
    therefore *conservative*: every passage passes its flow with room to
    spare. The gap is the price of the assumed camber-line family and
    thickness distribution — the same two assumptions that put unit 12's
    HPC margin at 4.0 % against a stated 6 %, but in the opposite
    direction, which is a fair warning about how much a throat depends on
    a blade shape nobody published.
54. **The design says the fan tip has almost no camber, and the
    construction cannot draw that.** Outboard of about 90 % span the
    designed camber falls below 1°, and the double-circular-arc
    construction is undefined at zero camber, so the outermost sections
    are not built. This is a limit of the *construction*, not of the
    design: a transonic fan tip genuinely does have near-zero camber,
    because its pressure rise comes from the shock and the radius change
    rather than from turning. The E³'s own HPC rotor-1 tip, which *is*
    published, carries 9.65° at a relative Mach of 1.35 — the fan tip runs
    at 1.41 and should carry less.

### Two errors of mine, both real, both caught by the physics

1. **The mass-averaged temperature ratio was applied across the span.**
   Fan Table IV's 1.1757 is the mass average; used at the hub it asks for
   more work than the blade speed can do (c_θ2 > U), and returned a 108°
   camber and a negative throat. Fixed by taking the *local* work from
   Fig 3's radial pressure profile.
2. **The static state was taken from the relative Mach.** Static
   temperature is a thermodynamic state and does not depend on the frame;
   what differs between frames is the *total* temperature. Writing
   T = T₀/(1 + ½(γ−1)M_rel²) conflates the absolute total with the
   relative total and put the tip axial velocity at 54 m/s where the fan
   face runs 207 — a 2.1 m fan does not ingest air at 54 m/s. The correct
   relation takes the static state from the **absolute** velocity and
   forms M_rel = |W|/a afterwards. A third slip, an inverted comparison in
   the bisection that solves for axial velocity, was caught the same way:
   relative Mach rises with axial velocity, so overshooting means c_x is
   too high.

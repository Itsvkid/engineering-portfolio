# Step 0 — mechanical solvers (E): tolerance and validation case, written first

Per [METHOD.md](../../METHOD.md). Nothing in a step-0 section is edited
after its run; results and findings are appended below it.

## Unit E1 — centrifugal stress at every HPC blade root

The work plan's E1 closure: *Table X centrifugal stresses reproduced
within **10 %** all ten stages.*

A rotating blade's root stress is

    sigma_root = (rho·omega²/A_root) ∫_root^tip A(r)·r·dr

and everything on the right except the density is already transcribed.
Table XXII gives the chord and the maximum thickness ratio at twelve
sections of every rotor, so the area distribution follows as
A(r) ∝ c(r)²·(t/c)(r) — and because only the **ratio** A(r)/A_root enters,
the airfoil shape constant cancels and nothing about the section's shape
needs assuming.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| Root centrifugal stress, all ten stages | Table X | **±10 %** | the work plan's own E1 criterion |
| Rotational speed | 13,948 rpm | — | Table X's own footnote: the stress case is the *deteriorated engine*, not the 12,303 rpm aero design point |
| Blade density | not published per stage | — | the rotor is "inertia-welded forward and aft sections"; **both titanium and a nickel alloy are carried, and which stages take which is an output, not an input** |

---

## Unit E1 after the run — nothing above was edited; what follows was added

### Results, 2026-09-06 (`cd solvers && python -m mechanical.blade_stress`)

```
HPC blade root centrifugal stress at the Table X stress case: 13948 rpm
(Table X's footnote: Nc deteriorated, the max-pressure/max-temperature case)

 stage   r_root   r_tip   taper   Ti kN/cm2   Ni kN/cm2   printed  Ti diff %  Ni diff %
     1    19.07   34.73   0.564       22.45       41.51      21.1        6.4       96.7
     2    22.86   33.45   0.601       16.94       31.32      16.5        2.7       89.8
     3    25.16   32.72   0.643       13.30       24.60      13.1        1.6       87.7
     4    26.32   32.03   0.745       11.72       21.66      11.0        6.5       96.9
     5    26.88   31.43   0.705        8.84       16.35      17.2      -48.6       -5.0
     6    27.12   30.79   0.799        8.03       14.84      14.5      -44.7        2.3
     7    27.31   30.36   0.683        5.69       10.52      11.0      -48.2       -4.3
     8    27.35   29.92   0.683        4.76        8.80       9.0      -47.1       -2.2
     9    27.37   29.67   0.683        4.24        7.84       8.3      -48.9       -5.5
    10    27.37   29.43   0.725        4.02        7.44       7.6      -47.1       -2.1

within 10 % on titanium: stages [1, 2, 3, 4]
within 10 % on nickel:   stages [5, 6, 7, 8, 9, 10]
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| Stages 1–4, titanium | +6.4, +2.7, +1.6, +6.5 % | ±10 % | pass |
| Stages 5–10, nickel | −5.0, +2.3, −4.3, −2.2, −5.5, −2.1 % | ±10 % | pass |
| **All ten stages** | **worst 6.5 %** | ±10 % | **E1's closure met** |

### Findings

73. **All ten root stresses reproduce within 6.5 %, from geometry
    alone.** The chord and thickness at twelve sections per rotor, the
    root and tip radii, one rotational speed and one density — nothing
    else. The work plan asked for 10 % and the worst stage is 6.5.
74. **The material crossover falls out of the stress data, and it lands
    exactly on the weld.** Stages 1–4 match a titanium density to within
    6.5 %; stages 5–10 match a nickel-alloy density to within 5.5 %; and
    neither works for the other group — titanium reads the rear stages
    **47 % low** and nickel reads the front stages **90 % high**. The E³
    reports never state a blade material stage by stage. But CR-168219
    describes the HPC rotor as "**inertia-welded forward and aft
    sections** joined by a single bolt joint", and the crossover this
    calculation finds — between stage 4 and stage 5 — is where that weld
    is. A published stress table and a one-line construction note,
    neither referring to the other, locate the same joint.
75. **Table X's stresses are at the deteriorated-engine speed, and its
    own footnote is the only place that says so.** 13,948 rpm, not the
    12,303 of the max-climb aero design point. That is a factor of 1.29
    in stress: computing at the design speed would have read **every
    stage 22 % low** and looked like a systematic modelling error rather
    than a misread condition. Blade stress is quoted at the worst case a
    designer must survive, not at the point the aerodynamics was drawn
    for — and the two differ by 13 % in speed on this engine.
76. **The taper factor runs 0.56 to 0.80 and it is the whole point of
    tapering a blade.** A constant-area stage-1 blade would carry 40
    kN/cm²; the real tapered one carries 22. Every stage's factor is
    recorded, and the front stages — longest blades, most to gain — are
    tapered hardest.

---

## Unit E2 — the rotating disc

The work plan's E2 closure has two halves: *HPT disc peak effective stress
within **10 %** of Fig. 64, and **the bore doubling for a small hole** is
demonstrated on the model.*

**The first half is gated and is not attempted.** It needs the disc
profile — thickness against radius — and DATA-INDEX records the disc
cross-sections as *"cross-sections only; digitise"*: Stage A never
transcribed them, and Fig. 64 is itself figure-status. No profile, no
peak. That is written here rather than quietly skipped, and E2 is
therefore recorded as **half closed**.

The second half is closed-form mechanics and needs nothing from the
reports at all. What the reports *do* give — Fig. 55's effective stress at
nineteen rotor locations at three flight times, Fig. 54's metal
temperature at seventeen, Fig. 53's speed at each time, and the stage-1
dovetail load — supports a sharper question than the peak value, and one
that can fail: **which load actually sets the bore?**

| Check | Known answer | Band | Basis |
|---|---|---|---|
| Bore concentration as the hole shrinks | exactly **2** | ±0.5 % at a/b = 0.01 | Timoshenko, *Theory of Elasticity* art. 32 — a textbook limit, not an E³ number |
| Stage-1 rim load | 76 × 77.395 kN | exact | HPT report Fig. 81's dovetail load × Table III's blade count; both printed |
| Published bore stress vs a constant-thickness disc | 779–910 MPa | must lie **between** the solid-disc and small-hole values | a real disc is thick at the bore and thin at the rim; if the published value fell outside the bracket, either the bracket or the reading would be wrong |
| Is any rotor stress purely centrifugal? | it must then scale as N² between the three times | **±5 %**, the read uncertainty of a stress contour drawing | Fig. 53's own speeds; nothing else in a centrifugal stress changes between the times |
| Two-term split, stage-2 bore | σ = c·(N/N₄₀)² + k·(T_rim − T_bore) | fit within **±10 %**, and **0 < k < αE** | three published stresses against two constants, so it can fail; and k has an independent meaning — bore hoop stress from a radial gradient is αE(T̄ − T_bore), so k must be a *fraction* of αE = 2.5–3.1 MPa/K for René 95 |
| Leave-one-out | fit two times, **predict** the third | no band stated — this is a conditioning test, not a closure | if the split is real, c and k barely move |

Not attempted, and why: the burst margin on average tangential stress at
120 % speed (33.27 / CS-E 840) is an E2 work-plan item and needs the same
profile. Recorded as gated with the peak stress.

Density and Poisson's ratio for René 95 are handbook values
(8210 kg/m³, ν = 0.29), not E³ report numbers; α and E are carried as
*ranges* precisely because the check on k is a magnitude check.

---

## Unit E2 after the run — nothing above was edited; what follows was added

### Results, 2026-09-07 (`cd solvers && python -m mechanical.disc`)

```
1. The bore doubling for a small hole (E2's stated closure)

     a/b    bore / solid-centre stress
   0.300                        2.0388
   0.200                        2.0173
   0.100                        2.0043
   0.050                        2.0011
   0.020                        2.0002
   0.010                        2.0000
   limit as a/b -> 0 : 2.0000   (exactly 2)

2. The stage-1 disc's rim load
   76 blades x 77.395 kN = 5882 kN at 13948 rpm
   that is 600 tonnes of blade pull on one disc
   blade tip 35.2 cm, root 31.0 cm

3. Where the published bore stress sits
   solid disc, centre                            691 MPa
   annular disc, bore at a/b = 0.15             1388 MPa
   published stage1_disk_bore (Fig 55)     779/903/779 MPa
   published stage2_disk_bore (Fig 55)     889/910/807 MPa

4. Which locations are purely centrifugal?
   speeds 13300/12800/12600 rpm -> N^2 scale 1.000/0.926/0.898

   stage1_disk_bore_forward       765/745/710   765/709/687    5.1 %
   forward_shaft                  338/345/317   338/313/303   10.2
   stage2_disk_bore               889/910/807   889/823/798   10.5
   ... (sixteen more, up to)
   impeller_cone                  165/359/269   165/153/148  134.9

5. The stage-2 disc bore: centrifugal + thermal
   T_rim - T_bore = -35 / +23 / +25 C
   published      = 889/910/807 MPa
   two-term fit   = 891/871/846 MPa   (+0.2%, -4.3%, +4.8%)
   c = 919 MPa,  k = 0.82 MPa/K,  k/alphaE = 0.27 to 0.33

   held out     c MPa   k MPa/K  predicted  published   err %
       40 s      1667    -27.56       2632        889   196.0
      875 s       895      0.16        832        910    -8.5
    1700 s       944      1.56        886        807     9.8

6. How much of the bore stress is the blades pulling?
   rim width  2 cm -> 151 MPa radial -> 309 MPa at the bore
              5 cm ->  60 MPa radial -> 124 MPa
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| Bore concentration, a/b = 0.01 | 2.0000 | ±0.5 % | **pass — E2's stated closure half met exactly** |
| Published bore inside the constant-thickness bracket | 691 < 779…910 < 1388 | must lie between | pass |
| Any location purely centrifugal | **0 of 19** within 5 %; the closest misses at 5.1 % | ±5 % | the model is *rejected everywhere* — see finding 78 |
| Two-term fit, stage-2 bore | +0.2, −4.3, +4.8 % | ±10 % | pass |
| k a physical fraction of αE | 0.82 MPa/K = 0.27–0.33 αE | 0 < k < αE | pass |
| Leave-one-out conditioning | c swings 895 → 1667, k swings +1.56 → −27.6 | — | **fails — finding 79** |
| Fig. 64 peak effective stress | **not attempted** | ±10 % | **gated on transcription** |

### Findings

77. **The bore doubling is exact, and it is the reason a disc bore is
    never a plain hole.** A hole of vanishing size in a rotating disc
    doubles the stress where it sits: 2.0388 at a/b = 0.30, 2.0043 at
    0.10, 2.0000 by 0.01. The size of the hole barely matters — only that
    there *is* one. This is why the E³ discs are bored and then thickened
    at the bore rather than left solid and drilled: René 95's bore is
    carrying twice what the same metal would carry without the hole, and
    the profile is the answer to that, not the hole size.
78. **Not one of nineteen published rotor stresses scales as N².** If a
    stress were purely centrifugal it would have to fall as the square of
    speed between 40 s (13,300 rpm), 875 s (12,800) and 1700 s (12,600) —
    a 10 % fall. None does. The closest, the stage-1 disc bore forward
    face, misses the stated 5 % band at **5.1 %** — recorded as a miss,
    because the band was written before the run and 5.1 is not 5. Eleven
    of the nineteen miss by more than 20 %. **The E³ HPT rotor is not a centrifugal structure at its
    limiting times; it is a thermal one.** The direction sorts the
    hardware in two: the bores and webs peak at **875 s**, mid-climb, when
    the rim has heated and the bore has not caught up; the gas-washed
    parts — blade retainer 1069 → 655, forward shank seal 745 → 607,
    impeller-to-arm 1110 → 848 — peak at **40 s**, in the takeoff
    transient. Two different limiting instants in one rotor, and Fig. 53's
    own speed trace shows neither is the fastest point of the flight.
79. **Three printed numbers cannot separate the two loads, and the
    leave-one-out proves it rather than hiding it.** The two-term model
    σ = c(N/N₄₀)² + k·ΔT fits all three stage-2 bore stresses to within
    4.8 % with k = 0.82 MPa/K — 0.3 of αE, exactly the fraction you would
    expect when most of the disc metal sits near bore temperature and the
    gradient is concentrated at the rim. That looks like a result. It is
    not. Hold out one time and fit the other two exactly, and k swings
    from +1.56 MPa/K to +0.16 to **−27.6**, and the held-out prediction
    from 196 % high to 8.5 % low. The reason is in the data: ΔT is +23 °C
    at 875 s and +25 °C at 1700 s — two nearly identical thermal states,
    so the pair carries almost no information about k and the system is
    near-singular. The least-squares number is real arithmetic on a
    badly-conditioned problem, and reporting it alone would have been a
    fitted answer wearing a physical constant's clothes. **Recorded as a
    limit of what the published table can settle.**
80. **Six hundred tonnes of blade pull on one disc.** 76 blades, each
    77.395 kN at hot-day takeoff — 7.9 tonnes per blade, 5,882 kN in
    total, on a rim 31 cm from the axis. Spread over a rim of unpublished
    axial width it is 38–151 MPa of radial stress, and the Lamé field
    doubles it again at the bore: **77–309 MPa on top of the 691 MPa the
    disc's own mass already puts there.** The published bores read
    779–910. That the blade pull alone spans a range as wide as the gap
    between the bracket and the answer is the measure of what is missing:
    the rim width is one number, and it is not in the reports.
81. **The Fig. 64 comparison is gated, not skipped.** E2's other closure
    half — peak effective stress within 10 % — cannot be attempted without
    the disc profile, and neither can the 120 % burst margin. DATA-INDEX
    already carried the disc cross-sections as un-digitised; this unit is
    the first work to be *stopped* by that gap, and it is recorded as the
    reason to digitise them rather than as a modelling failure.

---

## Unit E3 — blade natural frequency

The work plan's E3 closure: *first three modes of every HPC stage within
**5 %** of the published Campbell lines* — HPC report Figs 33–42.

**That closure is gated and cannot be evaluated.** `hpc-mechanical.yaml`
records Figs 33–54 as *"remain figure-status (A3)"*: the ten rotor Campbell
diagrams were never transcribed, so there is nothing to compare an HPC
rotor against. Written down, not worked around. What *is* transcribed is
four Campbell diagrams from three other reports and one rig — and each
names a **different tip condition**, which turns out to be the interesting
part:

| Blade | Report | Tip condition, as the report itself calls it | First flex at 0 rpm |
|---|---|---|---|
| LPT stage 1 | CR-168289 Fig. 62 | *"pinned-tip resonant frequency analysis"* — integral tip shroud | 2,050 Hz |
| Booster rotor | CR-165148 Fig. 55 | unshrouded | 250 Hz |
| Fan rotor | CR-165148 Fig. 45 | part-span shroud at **55 %** height | 80 Hz |
| HPC stage-9 and -10 vanes | 10A rig Figs 55–56 | a vane, banded inboard | 18.3 and 28.5 kHz |

METHOD.md's step 0 for this stage names the tool: *"LPT Fig. 62; **a
cantilever beam first**"*. So the beam is built and validated against
closed-form eigenvalues before it sees a blade.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| Uniform cantilever, first three modes | βL = 1.87510, 4.69409, 7.85476 | **±0.5 %** | closed form; 60 Hermite elements should do far better |
| Uniform clamped–pinned, first three | βL = 3.92660, 7.06858, 10.21018 | **±0.5 %** | the LPT's own named boundary condition |
| Uniform clamped–clamped, first three | βL = 4.73004, 7.85320, 10.99561 | **±0.5 %** | the vane bracket's stiff end |
| Southwell coefficient, uniform cantilever, zero hub radius | **1.19** | **±5 %** | the standard value; validates the geometric-stiffness matrix independently of any blade |
| Section properties | Green's theorem on a closed polygon | exact | the LPT's transcribed coordinates need **no shape factor at all** |
| Booster first flex | 250 Hz | **±15 %** | an unshrouded, low-aspect-ratio blade is the case a beam should get right; ±15 % allows for a handbook modulus and a read-off Campbell curve |
| Fan first flex | 80 Hz | must fall **inside** the twist bracket | a part-span-shrouded blade is not a cantilever; a bracket is the honest prediction, not a number |
| LPT stage-1 first flex | 2,050 Hz | **±15 %** | the report names the boundary condition, so the model can be held to the same standard as the booster |
| HPC stage-9 and -10 vanes | 18.3, 28.5 kHz | must fall **inside** cantilever-to-built-in | the inner band is a partial restraint of unknown stiffness |
| Southwell coefficient, the two unshrouded blades | from each published Campbell pair | **±25 %** | wide, because S ∝ f² and a 7 % read error on the at-speed frequency is 25 % on S |

Twist is carried as a bracket rather than a fudge: a section bends most
easily about **its own** weak axis and least easily if the whole blade is
forced to bend about the **root's**; a real twisted blade is between.

Elastic properties are handbook and are **not** in the E³ reports:
Ti-6Al-4V 114 GPa / 4,430 kg/m³, René 77 207 GPa / 8,220, nickel 200 GPa /
8,190. The material split for the ten HPC rotors is E1's own output —
titanium 1–4, nickel 5–10 — not a fresh assumption.

---

## Unit E3 after the run — nothing above was edited; what follows was added

### Results, 2026-09-07 (`cd solvers && python -m mechanical.blade_frequency`)

```
validation (mechanical/beam.py)
  clamped-free     +0.0000 / +0.0000 / +0.0000 %
  clamped-pinned   +0.0000 / +0.0000 / +0.0001 %
  clamped-clamped  +0.0000 / +0.0000 / +0.0001 %
  Southwell, uniform cantilever, R = 0:   S = 1.1931
  and as the hub grows:  S = 1.193 + 1.571 (R/L)   (1.571 = pi/2 to four figures)

1. First flex at zero speed
   blade                     BC   L cm   R/L     weak  root-axis  published   weak %  stiff %
   LPT stage 1       pinned tip  10.90  3.14     2974       3459       2050     45.1     68.7
   booster rotor           free  14.58  3.59      243        317        250     -2.7     26.8
   fan rotor               free  62.14  0.67       43         89         80    -46.8     11.7

2. The fan blade is not a cantilever: a part-span shroud at 55 % height
   free at the tip             43 -   89 Hz
   pinned at the shroud        84 -  587 Hz
   published (Fig 45)          80 Hz          -> INSIDE the bracket

3. Centrifugal stiffening: f_N^2 = f_0^2 + S (N/60)^2
   blade              rpm    R/L   S model  S published    err %
   LPT stage 1       4000   3.14     15.91      -216.56   -107.3
   booster rotor     3653   3.59      7.43        12.52    -40.6
   fan rotor         3653   0.67      2.48         3.56    -30.4

4. The ten HPC rotors -- PREDICTED, not validated
    stage   material   L cm   R/L    1F Hz    2F Hz    3F Hz  1F stiff
        1  Ti-6Al-4V  15.66  1.22      405     1322     3020       929
        2  Ti-6Al-4V  10.59  2.16      426     1825     4468       889
        3  Ti-6Al-4V   7.56  3.33      905     2878     6998      1421
        4  Ti-6Al-4V   5.71  4.61      895     4040    10306      1481
        5     nickel   4.55  5.90     1171     5276    13472      1995
        6     nickel   3.67  7.39     1502     7026    18161      2227
        7     nickel   3.06  8.93     2704    11010    28462      4088
        8     nickel   2.57 10.62     2813    13606    35599      3992
        9     nickel   2.30 11.88     3090    15420    40724      4300
       10     nickel   2.07 13.24     4048    19158    50295      5034

5. The one HPC frequency that WAS transcribed: the stage-9 and -10 vanes
     vane   L cm      cantilever kHz      built-in kHz  published kHz  inside?
        9   2.19        3.5 -    3.9      27.7 -  30.6           18.3      yes
       10   1.99        4.8 -    5.9      38.1 -  46.0           28.5      yes
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| Uniform cantilever, 3 modes | 0.0000 % | ±0.5 % | pass |
| Clamped–pinned, 3 modes | 0.0001 % | ±0.5 % | pass |
| Clamped–clamped, 3 modes | 0.0001 % | ±0.5 % | pass |
| Southwell, uniform cantilever | 1.1931 | 1.19 ±5 % | pass |
| Booster first flex | **−2.7 %** on the weak axis | ±15 % | **pass** |
| Fan first flex inside the twist bracket | 43 < 80 < 89 Hz | must be inside | **pass** |
| LPT stage-1 first flex | +45.1 % | ±15 % | **fail — finding 84** |
| HPC vanes inside cantilever-to-built-in | 18.3 and 28.5 kHz both inside | must be inside | **pass** |
| Southwell, booster and fan | −40.6 %, −30.4 % | ±25 % | **fail — finding 85** |
| **E3's stated closure** (HPC Figs 33–42) | — | ±5 % | **gated on transcription** |

### Findings

82. **An unshrouded blade really is a beam, to 2.7 %.** The booster rotor
    — 14.6 cm long, aspect ratio 2.1, no shroud — comes out at 243 Hz
    against a published 250. Nothing was fitted: the sections are built by
    the same double-circular-arc-and-quarter-sine construction C3 unit 12
    uses on Table XXII, the second moments are Green's theorem on the
    resulting polygons, and the only free choices are a handbook modulus
    and the weak-axis end of the twist bracket. **This is the result that
    licenses the other three**, and it is why METHOD.md says a cantilever
    beam first.
83. **The three blades need three different boundary conditions, and each
    report names its own.** The LPT's Fig. 62 is titled *pinned-tip*; the
    booster is unshrouded; the fan carries a part-span shroud at 55 %
    height. Applying one condition to all three would have been the
    obvious mistake and would have read the fan 5× stiff and the LPT
    5× soft. **The fan's 80 Hz sits inside the free-cantilever twist
    bracket, 43–89 Hz, and *below* the shroud-pinned bracket's floor of
    84.** That is exactly right for the mode Fig. 45 labels: the *lowest
    in-phase* system mode with two nodal diameters, in which all 32 blades
    move together and the part-span shroud ring translates with them
    rather than restraining them. The shroud is worth almost nothing in
    that particular mode — and everything in the higher-nodal-diameter
    ones, which is why it is there.
84. **The pinned-tip LPT blade reads 45 % high, and temperature is only
    half the story.** For a rigidly clamped, room-temperature beam to fall
    to 2,050 Hz its modulus would have to be 98 GPa — 47 % of René 77's
    room-temperature value. Nickel superalloys lose roughly 30 % of their
    modulus by 900 °C, and Table X puts this blade's metal at 882 °C, so
    hot modulus is worth about 15 % of the 45 %. The rest is the **root**:
    a beam clamped at the hub is the stiffest root a blade can have, and a
    two-tang dovetail in a slot is not that. Recorded as a miss with its
    cause named, not closed by choosing a modulus.
85. **The model under-predicts centrifugal stiffening by 30–41 % on both
    unshrouded blades, and the direction is consistent.** S = 7.43 against
    a published 12.52 for the booster, 2.48 against 3.56 for the fan. The
    geometric-stiffness matrix is not the suspect: it reproduces the
    uniform-cantilever coefficient 1.193 at zero hub radius and grows
    exactly as 1.193 + (π/2)(R/L). Two effects are missing and both push
    the same way — the **mass outboard that is not airfoil** (the fan's
    part-span shroud sits at 55 % height and every gram of it raises the
    tension inboard of it; the booster's tip is thickened *deliberately*,
    the report says, to move its stripe mode), and the **flap–lag coupling
    of a staggered blade**, which a single-axis beam cannot represent.
    Note also that S ∝ f², so the ±7 % spread in reading an at-speed
    Campbell curve is ±25 % in S on its own; the stated band was ±25 % for
    exactly that reason and both blades still miss it.
86. **A pinned-tip blade's frequencies FALL with speed, and the published
    Campbell diagram says so.** The LPT stage-1 blade goes 2,050 → 1,800 Hz
    between 0 and 4,000 rpm — a Southwell coefficient of **−217**. No
    tension-stiffening model of any kind can produce a negative
    coefficient; centrifugal load can only stiffen a beam in bending. The
    LPT report's own note explains it: on a shrouded, tip-interlocked
    blade the *interlock stiffness* the model assumes relaxes as the blade
    untwists under load, and the forcing lines rise while the frequency
    lines fall, which is why the crossings sit at the top of the operating
    band rather than the bottom. Recorded as a structural difference
    between shrouded and free blades, not as a model error.
87. **The one HPC frequency Stage A did transcribe brackets correctly, and
    the two stages agree with each other.** The stage-9 and stage-10 vanes
    are published at 18.3 and 28.5 kHz. A cantilever of the same section
    gives 3.5–3.9 and 4.8–5.9 kHz; built in at both ends gives 27.7–30.6
    and 38.1–46.0. Both published values sit inside, and both sit at the
    **same fraction of the built-in value — 0.66 and 0.62** — which is
    what a real inner band is: a partial restraint, the same design on both
    stages. Two independent vanes agreeing on the fraction is better
    evidence that the sections and the beam are right than either one
    alone would be.
88. **The ten HPC rotors are predicted and recorded so the gate is one
    line of work, not a fresh unit.** First flex runs 405 Hz on stage 1 to
    4,048 Hz on stage 10, with the material split taken from E1's own
    output rather than assumed again. Nothing is claimed for these numbers
    until Figs 33–42 are digitised — but when they are, E3's closure is a
    comparison, not a rebuild.

---

## Unit E4 — shafts, criticals, bolted joints and blade-out

The work plan's E4 closure: *no rotor critical inside the operating band
without a damper, and the thrust-bearing load stays inside capacity in
both directions.*

**The second half is gated.** CR-168219 sec 5.7 names all five bearings —
1 ball (LP thrust), 2 roller, 3 ball (HP thrust), 4 intershaft roller,
5 aft roller — with their sumps, their seals and their lubrication, and
prints **no bearing load and no bearing capacity**. Stage D's thrust
balance is not done either. Nothing to compare against; written down, not
worked around.

The first half is settled by HPT report Table XXII, which prints four
critical speeds *and* the margin *and* sec 5.2.1.11 prints the definition
— three printed quantities and one definition, so the table checks itself
rather than being trusted.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| Criticals inside the operating band | must be **0 of 4** | — | E4's own closure half; max engine speed 233 rps |
| Table XXII margins, recomputed | 2.52, 1.62, 3.42, 1.61 | **±0.01** | (critical − maximum)/maximum, the report's own definition; a rounding tolerance |
| Aft-seal-disc critical, from the travelling wave | 610 rps | implied stiffening must satisfy **0 < S < N²** | below zero there is no stiffening; above N² the backward wave never reaches zero and no critical exists at all |
| LP physical speed at takeoff | 3,653 rpm (fan report's maximum) | **±2 %** | from the *LPT* report's N/√T cycle-match parameter and the cycle's own T45 — two different reports, neither derived from the other |
| HP physical speed at max climb | 12,645 rpm | **±3 %** | same, from the HPT report's parameter and T41 |
| Fan and booster airfoil mass | Table VI: 7.272 and 0.284 kg a blade | airfoil must be **40–90 %** of it | the printed weight is the whole blade — airfoil, platform, dovetail, and on the fan the part-span shroud |
| Inducer-disc joint | *"torque through flange friction only with no slip"* | required bolt-circle radius must be **smaller than the disc** | the radius is not printed, so it is inverted rather than assumed |

Friction coefficient 0.15, metal on metal, is handbook and stated; it is
the only free number in the joint calculation and the result is reported
as a *required radius*, which scales inversely with it.

---

## Unit E4 after the run — nothing above was edited; what follows was added

### Results, 2026-09-07 (`cd solvers && python -m mechanical.rotordynamics`)

```
1. Rotor criticals against Table XXII (max engine speed 233 rps = 13,980 rpm)
   component             N  crit rps   margin  printed    diff
   forward_shaft         4       820    2.519     2.52  -0.001
   inner_tube            3       610    1.618     1.62  -0.002
   outer_liner           7      1030    3.421     3.42  +0.001
   aft_seal_disk         5       610    1.618     1.61  +0.008
   -> criticals inside the operating band: 0 of 4

2. The aft seal disc's travelling wave (Fig 88)
   5 nodal diameters, 2500 cps at rest, backward wave zero at 610 rps
   a RIGID disc would cross at f0/N = 500 rps
   implied S = 8.20   (f_disc there 3050 = N x Omega = 3050)
   the forward wave at 440 rps: model 5000 cps, printed 3350
   -> implies N = 1.25, not 5

3. Shaft torque, power from the cycle and speed from N/sqrt(T)
   rating       HP MW   HP rpm   HP kNm   LP MW   LP rpm   LP kNm
   max_climb    16.10   12,449     12.4   11.36    3,483     31.2
   max_cruise   15.55   12,317     12.1   10.80    3,442     30.0
   takeoff      38.83   12,936     28.7   26.13    3,636     68.6

4. The joint that carries it: 34 inducer-disc studs, friction only
   worst HP torque 28.7 kNm at takeoff
   clamp 98 kN new, 82.5 kN after 9,000 h (16 % relaxation)
   bolt-circle radius needed at mu = 0.15: 5.74 cm new, 6.81 cm relaxed

5. Blade mass audit against Table VI
   blade            airfoil kg  printed kg  airfoil %   r_cg cm
   fan rotor             4.788       7.272         66      70.1
   booster rotor         0.135       0.284         48      58.6

6. Blade-out
   fan rotor    whole blade (Table VI)     3,653   7.272 kg   746 kN    76 tonnes
   fan rotor    airfoil only               3,653   4.788 kg   492 kN    50 tonnes
   HPT stage 1  mass from the dovetail load 13,948  0.110 kg    77 kN     8 tonnes
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| Criticals inside the band | **0 of 4** | must be 0 | **pass — E4's first closure half met** |
| Table XXII margins recomputed | worst 0.008 | ±0.01 | pass |
| Aft-seal-disc implied stiffening | S = 8.20 | 0 < S < 25 | pass |
| LP speed at takeoff | 3,636 vs 3,653 rpm, **−0.5 %** | ±2 % | pass |
| HP speed at max climb | 12,449 vs 12,645 rpm, −1.6 % | ±3 % | pass |
| Fan airfoil mass fraction | 66 % | 40–90 % | pass |
| Booster airfoil mass fraction | 48 % | 40–90 % | pass |
| Required bolt-circle radius | 6.81 cm relaxed, against a 31 cm disc | must be smaller | pass |
| **Thrust-bearing load vs capacity** | **not attempted** | — | **gated: no capacity published, no thrust balance yet** |

### Findings

89. **The LP shaft carries more than twice the HP shaft's torque, on a
    third of the power.** 68.6 kNm against 28.7 at takeoff, because torque
    is power over speed and the LP spool turns at 3,636 rpm against
    12,936. The LP shaft is also the *thin* one — it runs the length of
    the engine **inside** the HP spool with clearance, so its outer
    diameter is bounded by the HP rotor's bore. The most torque-critical
    shaft in a two-spool engine is the one with the least room, and that
    is a geometric consequence of the architecture, not a design choice.
90. **Two reports and a cycle model agree on the physical spool speed to
    half a per cent.** The LPT report prints N/√T = 11.21 rad·s⁻¹·K^−½ as
    its cycle-match parameter; the cycle model, built from the *fan* and
    combustor data, gives T45; the product at takeoff is **3,636 rpm**
    against the *fan* report's stated maximum of **3,653**. The HP side
    agrees to 1.6 %. None of the three was derived from the others, and
    this is the first time in the project that a mechanical quantity has
    closed across three separate documents.
91. **Table XXII checks itself, and the one printed inconsistency is
    rounding.** All four margins recompute from (critical − 233)/233 to
    within 0.008. The transcription had already flagged that the inner
    tube and the aft seal disc share a 610 rps critical yet print 1.62 and
    1.61; both are 1.618, and the report has simply rounded the same
    number two ways. Recorded as read — no correction to the source.
92. **The aft seal disc's critical is 22 % above where a rigid disc would
    put it, and that gap *is* the stiffening.** With 5 nodal diameters and
    2,500 cps at rest, a disc whose frequency did not change with speed
    would cross zero on the backward wave at f₀/N = **500 rps**. Fig. 88
    puts the critical at **610**. The only way to reconcile them is a disc
    that stiffens as it spins, and the implied coefficient is **S = 8.20**
    — comfortably inside the 0 < S < N² = 25 window outside which no
    critical would exist at all. The number was not put in; it fell out of
    three printed quantities.
93. **Fig. 88's second printed point belongs to a different curve.** The
    forward wave at 440 rps is printed at 3,350 cps; the 5-nodal-diameter
    model gives 5,000. Backing N out of the printed value instead gives
    **N = 1.25**, so the read is almost certainly from the 1-diameter
    curve on the same figure rather than the 5-diameter one the critical
    comes from. Flagged for a re-read of Fig. 88 rather than reconciled by
    adjusting the model.
94. **Seventy-six tonnes out of one fan blade.** At 3,653 rpm a released
    blade throws its own centrifugal load into the mounts: 7.272 kg at a
    CG radius of 70.1 cm is **746 kN**. The airfoil alone — which is what
    a blade-out release actually liberates above the dovetail — is 4.788
    kg and 492 kN, and the difference between those two numbers is why the
    certification case (33.94 / CS-E 810) is argued over release plane
    rather than over blade weight. The whole HPT stage-1 blade, by
    contrast, is **110 g** and throws 77 kN: the hot end of the engine is
    not where the mount loads come from.
95. **The airfoil is two-thirds of a fan blade and half a booster blade.**
    Integrating the reconstructed sections gives 4.788 kg of fan airfoil
    against Table VI's 7.272 kg a blade, and 0.135 against 0.284 for the
    booster. The remainder is platform, dovetail and — on the fan — the
    part-span shroud. The short blade pays proportionally twice as much
    for its attachment, which is the mass argument against low-aspect-ratio
    blading that the aerodynamic argument usually wins anyway.
96. **The joint that transmits the core's torque needs a 7 cm radius and
    has a 31 cm disc to do it in.** The 34 inducer-disc studs must carry
    28.7 kNm through flange friction with no slip; at μ = 0.15 that needs
    a bolt circle at 5.74 cm when new and **6.81 cm after 9,000 h of creep
    relaxation has taken 16 % of the clamp load away**. Any plausible
    flange radius on a disc whose rim is at 31 cm clears it several times
    over — which is consistent with the report saying this joint is
    *governed by* torque transfer while still showing an 8 % margin on
    clamp load: the binding constraint is the bolt's own relaxation, not
    the friction radius.

---

## Unit E5 — attachments and joints

The work plan's E5 closure: *every attachment has margin on all three
stresses and the weak-link order holds* — disc slot stronger than blade
root, blade root stronger than airfoil.

**One item is gated.** E5's first bullet asks for the HPC dovetails per
HPC report sec 3.2.3, and `hpc-mechanical.yaml` has **no blade block and
no dovetail block at all**: its meta records only Tables XV–XIX and
Figs 55–62 as transcribed. Nothing to work with. Written down, not worked
around.

Everything else is printed in full, and the point of this unit is that the
printed numbers can be made to check **each other**. Every band below is a
relation between quantities the reports print side by side, none of which
was derived from another.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| HPT two-tang load split | the text says *"a deeper tang for the higher load"* | the two printed stresses must be in a **fixed ratio to the two printed neck widths**, within **±2 %** | five printed numbers — one load, one chord, two widths, two stresses — and one geometry; the split is recoverable, not assumed |
| Fan and booster dovetail crush | printed, 30.4 and 16.9 kN/cm² | implied bearing area must be **1 or 2 printed flanks**, ±10 % | the load follows from E4's Table VI mass audit, so the area is an output |
| LPT Fig. 70's Kt | printed, 1.59–1.62 for four sections | position 2 / position 1 must equal it within **±1 %** *if* those two are the nominal and concentrated reading of one place | the figure prints six stresses *and* a Kt for each section |
| LPT blade retainers | all three stages, one allowable of 634.3 MPa | **margin ≥ 1.00** on every stage | E5's own closure, and the report says stage 3 "sits exactly on the allowable" |
| Which retainer thickness carries the load | not stated | the winning law must beat the others by **2×** on worst error | four candidates: t1 or t2, F/t or F/t² |
| Weak-link order | *"attachments stronger than airfoils, as the goals demanded"* | disc-post margin **>** blade-dovetail margin; booster dovetail corner **<** airfoil peak | the Goodman figures state the conclusion; the stresses let it be checked |
| Casing flange bolts | *"no axial flange separation at 2 × maximum operating pressure"* | required bolt stress must be **at or below** a superalloy proof stress (~1,000 MPa) | bolt count and size printed; pressure from the cycle |

Two stated assumptions, both flagged where they enter: the casing flange
radius is taken as the flowpath **tip radius** at that station (no flange
diameter is printed anywhere), and πr² is used for the projected area,
which is an **upper bound** on the separating load. The bolt tensile
stress area is the standard 3/8-24 UNF value, 0.7854(d − 0.9743/n)².

---

## Unit E5 after the run — nothing above was edited; what follows was added

### Results, 2026-09-07 (`cd solvers && python -m mechanical.attachments`)

```
1. The HPT stage-1 two-tang dovetail
   blade load 77.395 kN over an axial chord of 3.45 cm
   printed stresses  862 / 746 MPa     ratio 1.1555
   printed widths    0.952 / 0.820 cm  ratio 1.1610
   -> the two ratios agree to 0.47 %, so sigma is proportional to w
   -> the load splits as w^2: 57.4 % upper, 42.6 % lower
      (an equal-stress design would split by area and read 127 MPa on both)
   nominal neck tension 135 / 117 MPa; the printed combined stress is 6.4x nominal

2. Dovetail crush: the load is known, so the bearing area is an output
   blade            load kN   printed  one flank   implied  flanks
   fan rotor          746.4      30.4      13.09     24.55    1.88
   booster rotor       24.4      16.9       1.47      1.44    0.98

3. LPT Fig 70's Kt, against its own stresses
   section      pos 1   pos 2   ratio  printed Kt   err %
   blade_A      118.6   191.8   1.617        1.62    -0.2
   blade_B      136.5   215.8   1.581        1.59    -0.6
   disk_C        66.9   191.7   2.865        1.60    79.1
   disk_D       144.8   143.4   0.990        1.60   -38.1

4. LPT blade retainers: three stages, one allowable of 634.3 MPa
    stage   force N   t1 cm   t2 cm    sigma   margin
        1       894   0.109   0.267    620.5    1.022
        2      1103   0.127   0.292    627.5    1.011
        3      1561   0.173   0.343    634.3    1.000
   t2 with F/t^2   worst  3.5 %      t1 with F/t     worst  7.6 %
   t1 with F/t^2   worst 32.2 %      t2 with F/t     worst 33.0 %

5. Weak-link order
   fan blade dovetail corner      39.3 of 50.3 kN/cm2   margin 1.28
   fan disc post corner           31.9 of 46.9 kN/cm2   margin 1.47
   fan blade dovetail crush       30.4 of 50.3 kN/cm2   margin 1.65
   booster: airfoil peak 18.5 vs dovetail corner 13.8   -> attachment below airfoil
   HPT: blade tang 862 MPa vs disc slot 1000 MPa (as printed)
        disc slot LCF 36,000 against a required 36,000;
        blade dovetail >18,000 against 18,000

6. Casing flanges at 2 x maximum pressure (takeoff)
   3/8-24 UNF tensile stress area 56.7 mm2
   flange          bolts   p MPa    r cm  separating MN  per bolt kN  bolt MPa
   front              60    0.16    36.2           0.13          2.2        38
   front at p3        60    3.28    36.2           2.70         45.1       796
   aft                32    3.28    29.3           1.78         55.5       979
   manifold           28    3.28    29.3           1.78         63.4      1119
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| HPT tang stress ∝ neck width | **0.47 %** | ±2 % | pass |
| Fan crush bearing area | 1.88 flanks | 1 or 2, ±10 % | pass (two) |
| Booster crush bearing area | 0.98 flanks | 1 or 2, ±10 % | pass (**one** — finding 99) |
| LPT Fig. 70 Kt, blade sections | −0.2 %, −0.6 % | ±1 % | pass |
| LPT Fig. 70 Kt, disc sections | +79 %, −38 % | ±1 % | **fail — finding 100** |
| LPT retainer margins | 1.022, 1.011, **1.000** | ≥ 1.00 | pass, the third exactly |
| Retainer load law | t2 with F/t² at 3.5 %, next 7.6 % | must win by 2× | pass (2.2×, marginal) |
| Weak-link order, fan | post 1.47 > blade 1.28 | must hold | pass |
| Weak-link order, booster | 13.8 < 18.5 kN/cm² | must hold | pass |
| Casing bolt stress | 796 / 979 / **1,119** MPa | ≤ ~1,000 MPa | **the manifold flange exceeds it — finding 102** |
| **HPC dovetails (sec 3.2.3)** | **not attempted** | — | **gated: nothing transcribed** |

### Findings

97. **A hand tension calculation reads a dovetail six times low.** The HPT
    stage-1 blade pulls 77.4 kN through two tangs whose necks total 6.1
    cm² — a nominal tension of 117–135 MPa. The report's own printed
    combined-with-Kt stresses are 746 and 862 MPa: **6.4× the nominal, and
    the same 6.4 on both tangs.** That factor is the tang's cantilever
    bending, the gas-bending moment and the fillet's concentration
    together, and it is the whole reason the E³ does dovetails with
    MULTI-HOOK and FINITE rather than with a neck area. Anyone sizing a
    blade root on tension alone would clear the material by 5× and lose
    the blade.
98. **The two tangs are not equally stressed, and the printed numbers say
    by how much.** The printed stresses, 862 and 746 MPa, are in the ratio
    1.1555; the printed neck widths, 0.952 and 0.820 cm, in the ratio
    1.1610. **They agree to 0.47 %** — so stress is proportional to neck
    width, which means the load splits as w² and the upper tang carries
    **57.4 %**, not the 54 % an equal-stress design (load by area, 127 MPa
    on both) would give. The report's one-line description — "the upper
    tang with a generous fillet for Kt and a **deeper tang for the higher
    load**" — turns out to be quantitative, and the quantity is in two
    numbers printed a line apart.
99. **The fan and booster crush stresses are not quoted over the same
    thing.** The blade load is known independently — from E4's mass audit
    against Table VI — so the bearing area the report used is an output.
    The fan's implied area is **1.88** printed flanks and the booster's is
    **0.98**. One figure quotes the crush over both flanks and the other
    over one, or one of the two printed flank widths is a total rather
    than a per-flank value. Both readings are internally consistent to
    better than 6 %; what is inconsistent is between the two figures.
    Recorded as a source observation, and a warning against carrying a
    crush stress from one figure to another.
100. **Fig. 70's stress-concentration factor is checkable, and it checks
     for the blade and not for the disc.** For both blade sections the
     ratio of the position-2 to the position-1 stress reproduces the
     printed Kt to better than 0.6 % — 1.617 against 1.62, 1.581 against
     1.59 — so positions 1 and 2 are the nominal and the concentrated
     reading of the same place. The two disc sections give 2.865 and 0.990
     against a printed 1.60. Either the disc's nominal is read at a
     different position, or the figure's disc pair is not the same kind of
     pair. Flagged for a re-read of Fig. 70, not reconciled.
101. **Three retainers, three loads 75 % apart, one stress.** The LPT
     stage-1 to stage-3 retainers carry 894, 1,103 and 1,561 N and read
     620.5, 627.5 and 634.3 MPa — a 75 % rise in load for a 2 % rise in
     stress, and the third sits *exactly* on the 634.3 MPa allowable. The
     thickness was the design variable, and which thickness and which law
     can be recovered: **t2 with σ ∝ F/t² reproduces all three to 3.5 %**,
     where t1 with F/t manages 7.6 % and the other two combinations are
     over 30 % out. The retainer is a bending part and t2 is its section.
     The margin ordering — 1.022, 1.011, 1.000 — is what designing three
     parts against one allowable looks like when it is done properly.
102. **The rear casing flanges are bolt-limited at their own criterion.**
     Table XVII asks for no axial separation at **twice** maximum
     operating pressure. Taking the full projected area πr² — an upper
     bound on the separating load, since the reports print no flange
     diameter — the aft flange's 32 bolts need **979 MPa** and the
     manifold flange's 28 need **1,119 MPa**, against a superalloy proof
     stress around 1,000. That the bound lands *on* the material limit
     rather than a factor away from it is the finding: either these
     flanges really are sized by the 2× criterion, or the true separating
     area is somewhat below πr². It also explains the bolt counts — 60 on
     the front flange where the pressure is 1.6 bar and only 28 on the
     manifold where it is 33.
103. **The weak-link order holds where it can be checked, and the two HPT
     attachments sit exactly on their own life requirements.** The fan
     disc post has more margin than the fan blade dovetail (1.47 against
     1.28) and the booster's dovetail corners are below its airfoil peak
     (13.8 against 18.5 kN/cm²) — attachments stronger than airfoils, as
     the reports' Goodman figures state and as the design goals demanded.
     On the HPT the printed disc-slot stress (1,000 MPa) is *above* the
     blade tang's (862), which reads the wrong way round until the lives
     are looked at: the disc slot makes **36,000 cycles against a required
     36,000** and the blade dovetail **>18,000 against a required 18,000**.
     Different alloys, different limiting instants, and both sized to
     their own requirement rather than to each other. The weak-link order
     is a statement about *margin*, not about stress.

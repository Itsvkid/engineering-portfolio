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
74. **The material crossover falls out of the stress data.** Stages 1–4
    match a titanium density to within 6.5 %; stages 5–10 match a
    nickel-alloy density to within 5.5 %; and neither works for the other
    group — titanium reads the rear stages **47 % low** and nickel reads
    the front stages **90 % high**. So the density changes between stage 4
    and stage 5.

    > **Corrected 2026-09-07 by unit F1 (finding 105).** Two further
    > claims were made here and both were wrong.
    >
    > ~~"The E³ reports never state a blade material stage by stage."~~
    > **HPC report Table X prints a material for every one of the ten
    > stages, in the same table this unit took its stresses from.** It
    > says Ti-8-1-1 for stages 1–6 and Inco 718 for 7–10. It was not
    > looked for.
    >
    > ~~"The crossover lands exactly on the inertia weld CR-168219
    > describes."~~ **CR-168219 says the rotor is "inertia-welded forward
    > and aft sections joined by a single bolt joint" and never says
    > where the weld is.** The weld's position was inferred from this
    > unit's own crossover and the agreement then presented as
    > corroboration. Circular; withdrawn.
    >
    > The **crossover itself stands**, and unit F1 evidences it far
    > better: Table X's airfoil *weight* and root *area* give the density
    > of every blade as a measurement, independent of the stress column,
    > and it puts the change at stage 5 — and the printed weights at
    > stages 5 and 6 are 1.49× and 1.57× the heaviest a titanium blade of
    > that root section and span could possibly be. See
    > `solvers/materials/STEP0.md` unit F1, findings 104–106.

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

82. **An unshrouded blade really is a beam, to 2.7 %.**
    *RESTATED 2026-09-18 — on Appendix D's printed sections this is
    **250.68 Hz against 250, +0.27 %**, and the published value now sits
    just below the bracket's soft end rather than inside it. See "Unit E3
    re-run on the corrected sections" at the end of this file.*
    The booster rotor
    — 14.6 cm long, aspect ratio 2.1, no shroud — comes out at 243 Hz
    against a published 250. Nothing was fitted: the sections are built by
    the same double-circular-arc-and-quarter-sine construction C3 unit 12
    uses on Table XXII, the second moments are Green's theorem on the
    resulting polygons, and the only free choices are a handbook modulus
    and the weak-axis end of the twist bracket. **This is the result that
    licenses the other three**, and it is why METHOD.md says a cantilever
    beam first.
83. **The three blades need three different boundary conditions, and each
    report names its own.**
    *RESTATED 2026-09-18 — the physical reading below stands, but the fan
    half no longer demonstrates it: on the corrected span the free and
    shroud-pinned brackets OVERLAP at the published 80 Hz. See "Unit E3
    re-run on the corrected sections" at the end of this file.*
    The LPT's Fig. 62 is titled *pinned-tip*; the
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

---

## Unit E3 continued — the closure, evaluated at last

**The gate is lifted.** HPC report Figures 33–42, the ten rotor Campbell
diagrams, were recorded as *"remain figure-status (A3)"* and were the sole
thing standing between unit E3 and its stated closure. They are legible.
They are now transcribed in `data/hpc-rotor-campbell.yaml` — read off the
page images, with the reading uncertainty stated (±0.05 kHz on a 0–6 kHz
axis up to ±0.25 on a 0–26, which is 2–14 % on a first-flex frequency and
is itself comparable to the closure band).

The predictions this is compared against were **made and recorded on
2026-09-07, before the diagrams were opened** (finding 88). Nothing was
adjusted after reading them.

### Results, 2026-09-08

```
 st  fig  1F pred  1F pub   err%  2F pred  2F pub   err%  3F pred  3F pub   err%
  1   33      405     350   15.6     1322     950   39.1     3020    2050   47.3
  2   34      426     350   21.8     1825    1400   30.4     4468    2500   78.7
  3   35      905     600   50.8     2878    2950   -2.4     6998    5750   21.7
  4   36      895    1000  -10.5     4040    4600  -12.2    10306       -      -
  5   37     1171    1000   17.1     5276    4350   21.3    13472   10500   28.3
  6   38     1502    1400    7.3     7026    6150   14.2    18161       -      -
  7   39     2704    2300   17.6    11010    8900   23.7    28462       -      -
  8   40     2813    2400   17.2    13606   11900   14.3    35599       -      -
  9   41     3090    2850    8.4    15420   11900   29.6    40724       -      -
 10   42     4048    3600   12.5    19158   15600   22.8    50295       -      -

  1 of 24 comparisons within E3's 5 % band
  mean +21.4 %, worst +78.7 %
  first flex alone: mean +15.8 %, worst +50.8 %
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| First three modes, every HPC stage | **1 of 24** inside | ±5 % | **E3's closure is NOT met — finding 143** |
| First flex only | mean +15.8 %, 9 of 10 over-predicted | — | a systematic bias, not scatter |

### Findings

143. **E3's closure fails, and it fails in the direction and by the amount
     the LPT blade already warned it would.** One comparison of twenty-four
     lands inside the 5 % band; the mean error is **+21.4 %** and first
     flex alone is **+15.8 %, over-predicted on nine stages of ten**. That
     is not scatter — it is a bias, and it is the same bias finding 84
     recorded when the pinned-tip LPT blade read 45 % high: **a clamped
     beam is the stiffest root a blade can have, and a dovetail in a slot
     is not a clamp.** The band was written before the model existed and
     the predictions before the diagrams were read; neither was moved. A
     clamped Euler–Bernoulli beam reproduces a compressor blade's first
     flex to about 16 %, not to 5, and this is the measurement that says
     so.
144. **The error grows with mode number, which is what a root flexibility
     does.** First flex +15.8 % on average, second flex +20 %, third flex
     +44 % on the four stages that print one. A soft root removes more from
     a high mode than a low one, because the higher modes put more of their
     strain energy near the fixing. If the discrepancy were a material
     property or a section-area error it would scale every mode alike; it
     does not.
145. **The published Campbell lines are flat with speed, and the model says
     they should rise by half.** Every one of the ten diagrams draws its
     mode lines horizontally, drooping slightly on stages 7–10. Unit E3's
     own Southwell analysis (finding 85) gives S ≈ 1.19 + 1.571(R/L), which
     for stage 1 at R/L = 1.22 is S ≈ 3.1 — enough to take first flex from
     350 Hz to about **539 Hz by 14,000 rpm, a 54 % rise that would be
     unmissable on these axes.** It is not there. The droop on the rear
     stages is explicable — they run at 480–655 °C and the modulus falls —
     but stage 1 sits at 113 °C with nothing to offset stiffening. Recorded
     as read and as an open question: either these diagrams plot something
     other than the rotating frequency, or centrifugal stiffening is far
     weaker on a dovetailed compressor blade than beam theory says.

---

## Unit E7 — the flutter screen

The plan's Stage E3 line: *Flutter screen: reduced frequency per row;
flexural and torsional stability plots vs HPC Figs. 43-44.*

Figures 43-44 are not transcribed. What **is** transcribed is better for a
check: **LPT report Table XI** prints a flutter safety factor for every one
of the five LPT rotor stages, in both flexural and torsional modes, and
states the index it is built on --

> relative flow velocity / (half blade chord x blade natural frequency)

-- with the safety factor being *maximum allowable index / calculated
index*, required to be at least 1.

### The problem with checking it, and the way round

**The allowable is not printed.** Only the ratio is. So the index cannot
be compared against a published number directly.

It can be compared **across stages**. If every stage is judged against one
allowable, then for each stage

    SF_published x I_computed = allowable = constant

so the five products must agree with each other, and the value they agree
on is the allowable this project can then report as recovered rather than
read. That is the check.

**Why this survives the E3 bias.** Unit E3's beam over-predicts blade
frequencies, badly (1 of 24 within 5 %). A frequency that is wrong by a
constant factor k gives an index wrong by 1/k, and the product above is
then `allowable/k` for *every* stage -- still constant. **The constancy
test is blind to a uniform bias and sensitive only to a stage-to-stage
one**, which is exactly the part of the model this can honestly examine.
What it cannot do is recover the allowable's absolute value, and the
result below says so.

| Check | Band | Basis |
|---|---|---|
| The five implied allowables agree | **±15 %** about their mean | generous, because the beam is a beam; tight enough that a stage-to-stage error of the size E3 found on the HPC would show |
| Relative velocity | rotor relative **exit** velocity, `cx3 / cos β3` | straight off the C1 velocity triangle, no thermodynamics in the path |
| Half chord | mean of root and tip chord, halved | Table XI's own definition; the aspect-ratio note says the report works at the pitch |
| Torsion | **not modelled** | the beam gives flexural modes only. A torsional index needs GJ and a polar inertia this project has not built. Recorded, not approximated |

**Closes when** the five implied allowables agree inside ±15 %, and the
recovered allowable is reported with the caveat that its absolute value
carries the beam model's bias.

### Result — E7

| | |
|---|---|
| Definition used | rotor relative **exit** velocity, as STEP0 named before the run |
| Implied allowable index | **51.3** (median 52.1) |
| Worst departure | **24.4 %** against a 15 % band — **NOT MET** |
| Spread across five stages | 1.61× |
| Departure shape | **monotone**, 39.7 → 63.8 front to back |
| Torsion | not modelled; Table XI's column carried as published data |

### Findings

173. **Table XI does not say where the relative velocity is taken, and the
     two readings do not agree.** The index is *relative flow velocity /
     (half chord × natural frequency)*, and a turbine rotor has two
     relative velocities. STEP0 chose the **exit** before the run — the
     natural reading for a turbine rotor, and the larger of the two. On
     that reading the five implied allowables spread 1.61× and the worst
     departs 24.4 %: the closure fails. On the **inlet** reading, stages 1
     to 4 agree to **4.2 %** about an allowable index of 27.9 — well
     inside the band — and stage 5 alone departs **+33.3 %**.

     The inlet reading is reported and **not adopted**. Changing a
     definition after the run because the other one fits is the precise
     move this project exists not to make, and the closure stands as
     evaluated. What the two readings say together is worth more than
     either: the index is reproducible on four of five stages under one
     plausible reading of an ambiguous sentence, and **stage 5 is the odd
     stage under both**. Settling which station the report meant needs
     Table XI's own working, which is not printed.

174. **The miss is monotone, which says the model and not the data.** The
     implied allowable climbs stage by stage — 39.7, 46.4, 52.1, 54.4,
     63.8 — rather than scattering about a mean. Since the product is
     `allowable = SF × velocity / (half chord × f)`, a monotone rise means
     the model's frequencies **fall too fast from front to back**: the
     first-flex frequencies drop 2974 → 490 Hz across the five stages,
     a ratio of 6.1, where Table XI's safety factors imply about 3.8.
     The blades carry integral cast tip shrouds with two-tooth seals, and
     the beam models the shroud as a **pin** — no mass, no rotary inertia,
     no torsional restraint. A shroud's mass matters more on the long aft
     blades than the short front ones, which is the right shape for this
     error. That is a hypothesis with a named mechanism, not a cause;
     testing it needs a shroud mass this project has not transcribed.

175. **The constancy test is blind to unit E3's bias by construction, and
     that is why it is worth running.** A frequency wrong by a constant
     factor k makes every index wrong by 1/k and every implied allowable
     `allowable/k` — so the five still agree, and the *agreement* survives
     a model known to over-predict by about 20 %. What does not survive is
     the absolute value: the recovered allowable index of 51.3 carries the
     bias in full and is reported with that caveat attached to it in the
     code. This is the first closure in the project whose test was chosen
     specifically to be insensitive to a known error, and it is worth
     naming as a pattern: **when a model has a uniform bias, look for the
     quantity the bias cancels out of.**

---

## Unit E8 — gas bending

The plan's Stage E1 line: *Gas bending from the C1 loads; tilt to cancel;
compare Table X `max_root_stress`.*

Table X gives the HPC's maximum root stress and its centrifugal part, and
nothing between them. **LPT Table VIII is the better target** and prints
the whole decomposition per stage:

* centrifugal, at pitch and at root
* **uncorrected gas bending at the root** — explicitly *before* the
  stacking tilt
* the leading-edge **resultant**, at pitch and root, which is what the
  blade actually sees

and its own note says why the first exceeds the third: *"'Uncorrected' gas
bending is before the stacking tilt that cancels it against centrifugal
bending."* That sentence is the whole design idea in one line, and it is
checkable.

### Method

Gas load per blade from the C1 mean-line, nothing else:

* tangential force `F_θ = ṁ_blade (c_θ2 − c_θ3)`
* axial force `F_x = ṁ_blade (c_x2 − c_x3) + (p_s2 − p_s3) A_ann / N`
* both applied at mid-span, giving a root moment `F · L / 2`
* resolved onto the **principal axes of the root section**, which come
  from the transcribed coordinates via `polygon_properties`, and the
  bending stress taken as `M/Z` on each with `Z = I / c` to the furthest
  fibre

### The band, and why it is wide

| Check | Band | Basis |
|---|---|---|
| Uncorrected gas bending at root, all five stages | **±25 %** | a mean-line load with a mid-span resultant against a real blade with a spanwise load distribution, a twisted stacking line and a shrouded tip. 25 % is the honest scatter of that method, and it is stated before the run rather than after it |
| The published resultant is below the uncorrected bending | **every stage** | not a tolerance but a sign check on the report's own sentence: if the tilt cancels bending, the resultant must be smaller |
| Direction | gas bending opposes centrifugal bending at the root | the mechanism the tilt exploits |

**Closes when** the uncorrected root gas bending reproduces within 25 % on
all five stages, and the published resultant is below the published
uncorrected value on every stage.

**Not attempted:** the tilt angle that does the cancelling. Table X's own
transcription note records that tilt is *"omitted: stages 8–10 print as
percentage LMI rather than radians"*, and the LPT table does not print it
at all. The cancellation is checked as an inequality, not reproduced.

### Result — E8

| | |
|---|---|
| Uncorrected root gas bending, five LPT stages | worst **17.7 %** against a 25 % band — **MET** |
| Errors | −3.8, −8.3, −9.8, +7.0, +17.7 % — **both signs**, so scatter rather than a missing term |
| The tilt cancels | **holds on all five**, mean **51 %** cancelled |
| Tilt angle | not reproduced; the reports do not print it |

### Findings

176. **The stage exit is counter-swirled, and the swirl change is a sum.**
     The first run under-predicted gas bending by 43–62 % on the four
     front stages and only 8.6 % on the fifth. The cause was a sign: the
     mean-line stores `alpha3` as a **magnitude**, the LPT stages exit with
     counter-swirl, and so the swirl change across the rotor is
     `c_θ2 + c_θ3` and not the difference. Taking the difference
     under-states the load by a factor of 1.4 to 3.8 — largest at the
     front, smallest at stage 5, which is exactly the shape the error had.

     What found it was **Euler's own identity**: `Δh = U · Δc_θ` is not a
     model, so the swirl change taken from the stored angles must reproduce
     the enthalpy drop the mean-line had already solved for. It did not,
     by a factor of three. The sum convention reproduces it to **3.7 % on
     the worst stage**, and `euler_check()` is now a test. The mean-line
     was never wrong; the way this unit read it was. **A convention is
     worth checking against a conservation law before it is trusted, and
     the check costs four lines.**

177. **The stacking tilt cancels about half the gas bending, on every
     stage.** LPT Table VIII prints uncorrected gas bending and the
     leading-edge resultant separately, and its note explains the gap:
     tilt cancels bending against centrifugal bending. Checked as an
     inequality rather than a tolerance — the resultant must sit below the
     uncorrected value — it **holds on all five stages**, cancelling 39 %
     to 61 % with a mean of 51 %. The tilt angle itself is not reproduced:
     Table X's own transcription note records tilt as *omitted, stages
     8–10 print as percentage LMI rather than radians*, and the LPT table
     never prints it. **A design intent stated in one sentence of prose,
     confirmed as an inequality across five stages** — which is as far as
     the published data allows anyone to take it.

---

## Unit E9 — the HPC rotor: the inertia welds and the single bolt joint

Stage E2's line: *the bolted-joint and inertia-weld rotor structure of the
HPC.*

Two neighbouring items are already done and are **not** this one. E5's
`casing_bolting` checks Table XVII's three *casing* flanges against their
printed criterion — that is the static structure. E4's
`bolted_joint_margin` inverts the *HPT* inducer-disk joint. Neither
touches the HPC rotor.

### Reading the sentence carefully

`e3-fps-published.yaml` carries one line on it:

> inertia-welded forward and aft sections joined by a single bolt joint;
> bore cooled by fan discharge air

That describes **two different kinds of joint, in different places**:

* **inertia welds**, plural and internal — the standard construction is
  individual stage discs friction-welded into a drum;
* **one bolt joint**, singular — where the forward drum meets the aft one.

Conflating them is easy and has already cost this project once: unit E1's
finding 74 read a *material* crossover as the weld position and had to be
withdrawn as circular. A material change happens at a **weld**, disc to
disc, and the sentence gives no position for either kind of joint.

### What can be computed

The HPT drives the rotor from the aft end and each stage takes its share
going forward, so **a joint sitting after stage *n* transmits only the
torque the stages ahead of it absorb**. Figure 14's per-stage temperature
rise is that work split, printed. The torque through the joint is
therefore a computable fraction of the HP spool torque for any position —
and the position is what is unknown, so the result is a curve rather than
a number.

| Check | Band | Basis |
|---|---|---|
| The work split sums to Fig 14's own total | **±0.05 °C** | 493.5 °C printed against the ten printed stages |
| Torque through the joint is a strict fraction of HP spool torque | **0 < f < 1**, monotone in position | a joint cannot carry more than the shaft delivers |
| At the aft end the fraction reaches 1 | **exactly** | the last joint before the turbine carries everything |
| The HPC joint's demand against the HPT joint's | **less than 1** at every position | the HPT joint carries the whole HP torque; every HPC joint carries part of it |

**Closes when** the work split reproduces Fig 14's total, the torque
fraction is monotone and bounded, and the HPC joint's demand is shown
below the HPT joint's at every candidate position.

**Not attempted:** the weld position, the bolt count, the bolt size, the
bolt-circle radius, the axial load. None is published for this rotor, and
the unit reports the demand as a function of position rather than
inventing a position to report a number at.

### Result — E9

| | |
|---|---|
| Work split against Fig 14's printed total | **0.000 °C** |
| Torque fraction through a joint | monotone **0.108 → 1.000**, aft of stages 1 to 10 |
| At the aftmost position | **exactly 1.000** of HP torque |
| Every forward joint against the HPT joint | **below 1** at all nine |
| At takeoff, HP torque | 28.67 kN·m |

**Closure: met.** All four checks hold.

### Findings

188. **The rotor has two kinds of joint, and only one of them is
     singular.** The FPS report's single line — *inertia-welded forward
     and aft sections joined by a single bolt joint* — describes **welds,
     plural and internal**, and **one bolt joint** between the two drums.
     The standard construction it implies is stage discs friction-welded
     into a drum, drums bolted together. That distinction matters because
     **a material change happens at a weld, disc to disc, and not at the
     bolt joint**, and conflating the two is what unit E1's finding 74 did
     before it was withdrawn as circular. No position is published for
     either kind.

189. **The torque a rotor joint carries is a computable function of where
     it sits, and the position is the unknown — so the answer is a curve.**
     The HPT drives from the aft end and each stage takes its share going
     forward, so a joint aft of stage *n* transmits only what stages 1..*n*
     absorb. Figure 14's per-stage temperature rise is that split, printed,
     and it sums to its own total to **0.000 °C**. The torque runs
     **3.10 kN·m** aft of stage 1 to **28.67** aft of stage 10, the latter
     being the whole HP torque at takeoff by construction. Every forward
     position is below the HPT inducer-disk joint's demand, which is the
     bound it has to satisfy. Reporting the curve rather than picking a
     position is the honest form here: nothing published fixes the
     position, and a single number would have implied one.

190. **The unresolved material question is worth a factor of 1.67 in joint
     torque.** Unit F1 measured a titanium-to-nickel density crossover
     between stages 4 and 5 from Table X's own weight column; Table X's
     material column prints the change at stage 7; F1 flagged the
     disagreement rather than resolving it. A joint aft of stage 4 carries
     **12.11 kN·m — 42 %** of HP torque; aft of stage 7, **20.24 kN·m —
     71 %**. That is what the open question costs structurally, and it is
     the first time this project has put a number on the consequence of
     that disagreement rather than only on the disagreement. It is an
     argument for neither station.


---


> **Superseded in part, 2026-09-19 (unit E11).** HPC report Figure 30 p.59
> *draws* the one bolt joint, and calibrated against the published annulus it
> sits at **r 23.47 cm, z 43.0 cm** — under the stage-5 blade, at the stage
> 4/5 interface, where the same figure also steps the disc bore from 10.66 to
> 9.14 cm and where unit F1's measured blade density crosses from titanium to
> nickel. Finding 189's "no position is published" stands as a statement about
> the *text*; the position is readable from the figure. On E9's own torque
> curve the joint therefore carries **12.11 kN·m, 42 % of HP torque** — the
> lower of the two branches finding 190 priced. See findings 261 and 257–259.

## Unit E3 re-run on the corrected sections, 2026-09-18

Unit G4 moved the fan and booster rotors off the seven- and five-station
figure read-offs onto CR-165148's printed Appendix B (23 stations) and
Appendix D (14). Findings 82 and 83 were established on the read-off
geometry, so neither was assumed to survive. **Both moved. One got better
and lost its stated form; the other lost its power entirely.**

Nothing below was tuned. The beam, the modulus, the density, the boundary
conditions and the twist bracket are unchanged; only the sections and the
radii the blade is built on have changed.

| Blade | Quantity | Read-off | Appendix | Published |
|---|---|---|---|---|
| booster | first flex, weak axis | 243.0 Hz, **−2.7 %** | **250.68 Hz, +0.27 %** | 250 |
| booster | twist bracket | 243–317 | 250.7–366.3 | — |
| booster | span | 14.58 cm | 14.81 cm | — |
| fan | first flex, free, weak axis | 43.0 Hz | **36.11 Hz** | 80 |
| fan | free twist bracket | 43–89 | **36.1–102.7** | — |
| fan | shroud-pinned bracket | 84–587 | **73.1–652.5** | — |
| fan | span | 62.14 cm | **69.34 cm** | — |

### Findings

- **Finding 82, restated — an unshrouded blade really is a beam, and on
    its own printed sections it is a beam to 0.27 %.** The booster rotor comes out
    at **250.68 Hz against a published 250**, not the 243 the read-off
    gave. Nothing was fitted; the improvement is entirely the sections and
    the radii. **But the claim's old form is gone**: the published value no
    longer sits *strictly inside* the weak-axis/root-axis twist bracket, it
    sits 0.68 Hz below its soft end. That is not a failure and it is not a
    near miss — it is the bracket collapsing onto the answer. The bracket
    is **46 % wide** (250.7 to 366.3 Hz) and the agreement is 0.27 %, two
    orders finer than the bracket can resolve, so "inside the bracket" was
    never the load-bearing statement. The load-bearing statement is the
    number, and the number improved by a factor of ten. The blade behaves
    as though every section bends about its own weak axis, which for a
    stubby low-aspect-ratio blade on a large drum (R/L = 3.5) is what one
    would expect. **This is still the result that licenses the other
    three.**
- **Finding 83, restated — the fan test has not changed sign, it has lost
    its power, and the cause is 7 cm of span.** The old form read: the fan's
    80 Hz sits inside the free bracket 43–89 and *below* the shroud-pinned
    floor of 84, therefore the lowest in-phase mode barely feels the
    part-span shroud. On the corrected geometry the blade is **69.34 cm
    long, not 62.14** — finding 226's span correction — and a longer blade
    is softer, so **both** brackets fall: free to 36.1–102.7 and pinned to
    73.1–652.5. They now **overlap over 73.1–102.7, and the published
    80 Hz lies inside that overlap.** The comparison can no longer
    distinguish a free tip from a shroud-pinned one, because the twist
    bracket has become wider than the gap between the two boundary
    conditions. **The physical reading of finding 83 is untouched** — the
    three blades still need the three boundary conditions their own reports
    name, and applying one to all three is still the obvious mistake. What
    is withdrawn is the claim that this particular comparison *demonstrates*
    the shroud is inert in the lowest in-phase mode. It no longer does.
228. **"Add the shroud's mass" is the right fix for the LPT and the wrong
     fix for the fan, and the fan's own printed shroud dimensions settle
     it.** Unit E7's flutter miss was attributed to the beam pinning a tip
     shroud without its mass, and that diagnosis stands for the LPT, whose
     shrouds are full interlocked tip shrouds on long blades. It does not
     transfer. CR-165148 dimensions the fan's part-span shroud completely
     — 0.89 cm thick, 6.35 cm of chord, 55 % span, 48–82 % of axial chord,
     nearly elliptical — so its mass is a calculation, not an assumption:
     **287 to 365 g**, 5.2–6.6 % of the 5.543 kg airfoil, one pitch of
     material at 55 % span. Put on the beam it is worth
     **−0.91 % to −1.15 %** on the first flex. The **restraint** at the
     same station is worth **×2.02**. The missing physics on a part-span
     shroud is the restraint, not the mass, by a factor of about 90 — and
     a model that would settle finding 83 needs an *elastic* restraint at
     55 % span, or a bladed-disc model, not a heavier beam.
229. **A single-blade beam and a bladed-disc system mode are not the same
     object, and CR-165148 says so on the same figure.** Fig 45 is titled
     *fan blade system and fixed-blade frequencies*; the block transcribed
     from it carries `nodal_diameters_shown: [2]` on the first flex, and at
     3,653 rpm it prints **140 Hz "lowest in phase" against 150 Hz
     "fixed"** — two numbers for one mode, ten per cent apart, because one
     is the 32-blade system and the other is a blade held at its root. At
     zero speed only one number is printed, 80 Hz, and this project has
     been comparing it against a single cantilever. Finding 83 already
     named the mode correctly; what is new is that the *report itself*
     distinguishes the two at speed and the comparison does not. Any future
     fan frequency work should compare against the **fixed-blade** line
     where the report prints one.

---

## Unit E10 — HPT blade rupture life · step 0, 2026-09-18

Written **before** `solvers/mechanical/rupture.py` first ran.

E1's closure has two halves. The first — Table X's ten HPC centrifugal
stresses — closed at 6.5 % in 2026-09-07. The second has read *"HPT blade
rupture life within a factor of 2"* since the work plan was written, and
its gate has read *"no creep data or Larson–Miller constants are sourced"*
since. **That gate is wrong, and the data is inside the report the closure
is about.** CR-167955 Fig 84 p.142 prints eleven (rupture life, metal
temperature) pairs round the stage-2 blade's pitch section at one stated
condition — FPS base, hot-day takeoff, 13,414 rpm — and `hpt-mechanical.yaml`
has carried them, transcribed, since 2026-09-05.

### What is published, and what is not

| | |
|---|---|
| stage-2 blade, limiting rupture point | **341 h at 926 °C**, Fig 84, and Table XXI's own *340 h required* |
| stage-2 pitch metal map, same section, same condition | Fig 35, bulk 929 °C, surface nodes 914–1013 °C |
| stage-1 blade, available life at max takeoff | **264 h** against 250 required (Table XX) |
| stage-1 blade, rupture vs span | Fig 76: 450 / 390 / 345 / 310 / 830 h at 0 / 12.5 / 25 / 50 / 70 % span |
| stage-1 pitch metal map, hot-day takeoff | Fig 27, bulk **953 °C** |
| stage-1 BUCKET-CREEP model | Fig 75 p.129 — a **mesh picture of the cooled pitch section, with no numbers and no scale**. It fixes *where* GE computed (2-D, pitch, hollow, five passages) and nothing else |
| **the Larson–Miller constant for René 150** | **nowhere on disk.** F1 already records that MIL-HDBK-5J carries none of René 77/95/150 or AF115 |
| **the two blades' section areas** | **never published** — G3's finding 222 records the HPT's four airfoil rows as the rows this project cannot build |

So the stress at either limiting section cannot be computed, and the
master curve's *slope* against stress has no source. What the data does
support is a **same-stress** Larson–Miller transfer from the stage-2 blade
to the stage-1 blade, with C taken at the standard 20 for a nickel alloy
and labelled a handbook assumption.

### Bands

| # | Band | Why |
|---|---|---|
| 1 | Fig 84 and Fig 35 are the same section at the same condition, so their metal-temperature ranges agree to **25 K** at both ends | the project's standing metal-temperature tolerance. Two figures eleven pages apart, never compared |
| 2 | the published mission mixes are self-consistent: the damage shares reproduce the printed equivalent hours at max takeoff to **1 %**, on both blades | Table XX and Table XXI are Miner sums and must close on themselves |
| 3 | a Larson–Miller curve calibrated on Fig 84's limiting point predicts the stage-1 blade's life at its published pitch metal temperature within a **factor of 2** of the published 264 h | **E1's own closure band, unchanged** |
| 4 | read as one constant-stress master curve, Fig 84's eleven points do **not** collapse, and the residual is ordered by position: the two hottest points — leading edge and trailing-edge tip — have the two largest positive life residuals | if they did collapse, the eleven points would be a creep curve; if the residual is unordered, it is scatter. This band asserts it is neither |
| 5 | the calibrated curve reproduces the standing rule **50 °C ≈ 10× creep life** to ±20 % | the rule is in the agent's §5 and has never been checked against an E³ number |

### Estimate before computing

Same-stress transfer: LMP = 1199.15 × (20 + log 341) = 27,018; at the
stage-1 pitch metal temperature of 1226.15 K that is log t = 2.03, so
**about 110 h against a published 264 — a factor of 2.4, just outside
band 3.** The expected direction is that the stage-1 blade must be the
*less stressed* of the two, which is physical: stage 2 is the bigger blade
on the bigger annulus (0.151 m² against 0.0895), and AN² alone would make
it 1.7× the stress. So band 3 is expected to **fail**, and the useful
output is the stress ratio it implies.

### Not attempted

Any prediction that needs a stress: the stage-1 and stage-2 section areas
are unpublished, so no centrifugal or gas-bending stress can be formed at
either pitch section, and E8's method — which needs transcribed root
coordinates — cannot be pointed at a row whose coordinates do not exist.
No slope of the master curve against stress is fitted, because fitting one
from a single blade's data would be fitting the answer.

## Unit E10 — after the run · 2026-09-18

`python -m mechanical.rupture`. Nothing above was edited.

| # | Band | Result | Verdict |
|---|---|---|---|
| 1 | Fig 84 and Fig 35 agree to 25 K at both ends | **1 K** cold, **0 K** hot | **pass** |
| 2 | the mission mixes close on themselves to 1 % | shares sum 100.1 % as printed; margins 1.056 and 1.003 | **pass** |
| 3 | stage-1 life within a factor of 2 of 264 h | **109 h, a factor of 2.43** | **MISS — E1 stays half** |
| 4 | the constant-stress residual is ordered by position | the two hottest points carry the two largest positive residuals, **+1.54 and +0.89**; the limiting point carries the most negative, −0.51 | **pass** |
| 5 | 50 °C ≈ 10× creep life to ±20 % | **7.98×** | **miss by a hair — 20.2 % low**, finding 248 |

Band 3 landed where step 0 said it would — the estimate written before the
run was *"about 110 h … a factor of 2.4, just outside"*, and the answer is
109 h and 2.43. **The closure does not close and the band was not widened.**

### Findings

244. **E1's gate was wrong, and the creep data was inside the report the
     closure is about.** The gate has read *"no creep data or
     Larson–Miller constants are sourced"* since the plan was written.
     CR-167955 Fig 84 p.142 prints **eleven (rupture life, metal
     temperature) pairs** on the stage-2 blade's pitch section at one
     stated condition, and `hpt-mechanical.yaml` has carried them
     transcribed since 2026-09-05 — thirteen days before anyone tried to
     use them. This is the fourth time in this project that a stated
     absence has turned out to be a statement about the reader rather than
     about the record. What is *actually* missing is not creep data. It is
     **stress**, and finding 247 says why that one is real.
245. **A rupture map is not a surface map, and Fig 84's coldest point
     proves it.** Fig 84's 867 °C point is labelled *suction side forward*
     and there is no 867 °C node anywhere on Fig 35's **surface** — the
     coldest surface node is 914 °C, a 47 K miss that would read as a
     transcription error in either figure. Fig 35's **interior** nodes run
     866–947 °C, and the coldest is **866 against 867**. BUCKET CREEP runs
     element by element over the whole section, so its life map covers the
     wall interior too, and its labels name a *region* of the section, not
     a point on the skin. Two figures eleven pages apart, in different
     chapters, closing to 1 K and 0 K once that is understood.
246. **The two blades' mission mixes independently agree about how much
     gentler max climb is.** Tables XX and XXI are separate Miner sums on
     separate blades, and the ratio of rupture life at max climb to
     rupture life at max takeoff falls out of each one's own hours and
     damage shares: **8.1× from the stage-1 blade and 7.6× from the
     stage-2 blade**, 6 % apart. The cruise ratios agree far less well —
     57.6× against 43.9×, 31 % apart — which is the expected ordering,
     because cruise carries the least damage (15 % and 18 %) and so the
     least resolution in a column printed to the nearest per cent.
247. **E1's second half misses by a factor of 2.43, and the miss is a
     stress rather than a creep model.** A same-stress Larson–Miller
     transfer from the stage-2 blade's limiting point (341 h at 926 °C,
     LMP 27,020 at C = 20) to the stage-1 blade's published pitch metal
     temperature of 953 °C gives **109 h against a published 264**. The
     direction is the physical one: the stage-1 blade must be the *less*
     stressed of the two, and the ratio the miss implies is
     **σ₁/σ₂ = 0.90–0.94** over a rupture exponent n of 8–15. What that
     cannot be checked against is the thing the E³ never published: the
     HPT's airfoil sections. G3's finding 222 already records the HPT's
     four airfoil rows as the rows this project cannot build, and the same
     absence stops the stress here. An AN² proxy — 0.0895 m² against
     0.151 — would put the ratio at 0.59, but AN² is a *root* stress and
     these are *pitch* sections, so it is an indication and not a
     measurement. Two published stage-1 lives are on the record and 17 %
     apart: Table XX's printed **264 h** and Fig 76's read-off minimum of
     **310 h**, both at hot-day takeoff; the factor is 2.43 against the
     first and 2.85 against the second, so which one is used does not
     change the verdict.

248. **On the E³'s own numbers, 50 °C of metal temperature is worth 8×,
     not 10×.** The standing rule of thumb is in this project's own
     reference sheet and had never been checked against an E³ number.
     Calibrated on Fig 84's limiting point at C = 20 it comes out
     **7.98×** — 20.2 % below the rule, and so 0.2 of a percentage point
     outside the ±20 % band step 0 set. Recorded as a miss rather than
     rounded into a pass, because the interesting part is the direction:
     the rule is a decade *at most*, and at the 1,200 K and few-hundred-hour
     corner where an HP blade actually lives it is nearer 8. The sensitivity
     is all in C, which is the one assumption in the chain.

### What would close it

One number: the ratio of the two blades' pitch-section areas, or either
blade's pitch-section area together with its own centrifugal pull. Neither
is in CR-167955, and the report's own stress work is carried entirely
inside BUCKET CREEP and FINITE, whose meshes (Fig 75) are printed without
a scale. A published René 150 rupture curve would be a second route and is
in no document on disk — F1 already records MIL-HDBK-5J as carrying none
of René 77/95/150 or AF115.

---

## Unit E11 — HPC Figure 30, and the bore radius D6 is gated on · step 0, 2026-09-19

Unit D6 is gated, and finding 193 priced the gate: the disc-face term
`(p3 − p25)·π(r_hub² − r_bore²)` is **+342 to +672 kN forward over bores of
8 to 20 cm, 3.2 to 6.4 times the annulus term that does close**, so the
thrust balance is decided by the one term that cannot be computed. The
missing number is the HPC disc **bore radius**, and unit G3's triage
(finding, 2026-09-18) recorded that **HPC report Figure 30 p.59 draws the
whole ten-stage rotor cross-section** — bores, webs, rims, stub shaft, CDP
seal — undimensioned, over an annulus this project has published at all 21
rows since Stage A.

This unit digitises that figure and carries the bore through to D6.

### Disclosure: a scoping digitisation preceded this step 0

METHOD.md wants the band before the run, and a calibration cannot be
designed without first seeing whether the page is to scale at all. So, as
in Stage L, what the scoping established is written here rather than
presented as a result:

* the ten drawn blade **tip** lines fit a single (scale, offset) in y
  against their published radii to **0.046 cm rms**;
* the same calibration then misses the ten drawn blade **root** lines by up
  to **1.1 cm**, with the miss ordered by blade span — the drawn blades come
  out 2–8 % short;
* adding **one** parameter, an x term, collapses all twenty to **0.054 cm
  rms**. Its value is a **0.40° rotation**, not a second scale;
* the bore radii come out near **9 cm aft and 10.7 cm forward**, and two
  routes to them — the fitted calibration, and a depth below the *published*
  hub radius of the same stage, which uses the scale but not the intercept —
  agree to under **0.08 cm**.

Everything below is a check the scoping did not make.

### The bands, stated before the run

| # | Check | Band | Basis |
|---|---|---|---|
| 1 | **Held-out prediction.** Fit the calibration on the five odd stages' tips and roots, predict the five even stages' | rms **≤ 0.12 cm**, max **≤ 0.25 cm** | an in-sample residual on a three-parameter fit to twenty points proves less than a fit that has never seen half of them. 0.12 cm is twice the in-sample rms |
| 2 | **The scan rotation is real, not a fitting artefact.** Odd-only and even-only fits must return the same angle | **≤ 0.15°** apart | a shear that is absorbing a modelling error would not be stable across disjoint halves of the page |
| 3 | **One scale, not two.** With the rotation taken from the radial fit, the axial scale must match the radial | **≤ 3 %** | a draughtsman's meridional section is isotropic unless it says otherwise; J8's CR-159584 Fig 1 needed 3 % |
| 4 | **Bootstrap uncertainty on a bore radius** | 95 % interval **≤ 0.25 cm** | this is the number that goes into D6, and it goes in as a band |
| 5 | **The disc-face term, summed disc by disc, against the single telescoped form** now that both bores and both areas are measured | the per-disc sum is **80 – 110 %** of `(p3−p25)·π(r_hub,10²−r_bore,10²)`; estimate **≈ 95 %** | the telescoped identity is exact only for a drum of constant face area. The forward discs have smaller faces *and* carry little Δp, so the sum should sit just under |
| 6 | **The D6 verdict survives the measurement** — the disc-face term still dominates the annulus term | **5 – 7 ×**, and the sign forward | finding 193 said 3.2–6.4× over an 8–20 cm bore; a measured 9 cm bore sits at the top of that |

**Closes D6 when** the net axial load on the HP rotor can be formed with the
bore's uncertainty attached and lands inside a stated band. **Does not close
it when** a term other than the bore is still missing — in which case the
gate is rewritten with what is left, and what is left is named.

**Not attempted, and said so before the run:** the disc *webs* and *rims*,
which this figure also draws and which would feed F2's disc masses and E2's
peak stress. F2's own closure records that even with every disc digitised it
would pass by arithmetic and not by evidence, because 320 kg of bearings,
sumps and drives has no printed geometry at all. This unit reads the bore
line and stops.

## Unit E11 — after the run · 2026-09-19

Nothing above this line was edited after the run.

`tools/read_hpc_fig30.py` → `data/hpc-disc-profile.yaml`;
`solvers/mechanical/disc_profile.py`; `tests/test_disc_profile.py`.

| Band | Asked | Got | |
|---|---|---|---|
| 1 Held-out prediction, five stages of ten | rms ≤ 0.12 cm, max ≤ 0.25 | **0.068 / 0.161 cm** | met |
| 2 Rotation stable across disjoint halves | ≤ 0.15° | **0.010°** | met |
| 3 One scale, not two | ≤ 3 % | **1.38 %** | met |
| 4 95 % interval on the bore radius | ≤ 0.25 cm | **0.27 / 0.38 / 0.40 / 0.61 cm** | **missed, by every estimator** |
| 5 Per-disc sum against the telescoped form | 80–110 %, est. 95 % | **99.4 %** | met |
| 6 Disc-face term still dominates | 5–7 ×, forward | **6.15 ×, forward** | met |

### The calibration

| | |
|---|---|
| Fitted on | **20 published radii** — ten rotor blade tips and ten blade roots, `hpc-flowpath.csv` |
| Radial scale | **49.598 px/cm** at 600 dpi = **1 : 4.80** |
| Scan rotation | **−0.416°** |
| In-sample residual | **0.050 cm rms, 0.094 cm max** on a 19–35 cm radius |
| Held out five stages | **0.068 cm rms, 0.161 cm max** |
| Axial scale | **48.916 px/cm**, 1.38 % from the radial |

### The numbers the figure gives that nothing prints

| | |
|---|---|
| Disc bore, stages 2–4 | **10.71, 10.69, 10.66 cm** |
| Disc bore, stages 5–10 | **9.14 → 9.08 cm** |
| CDP seal disc bore | **8.47 cm** |
| Stage 1 | **no bore** — the disc runs forward and inward into the integral stub shaft |
| Bolt joint | **r 23.47 cm, z 43.0 cm** — under the stage-5 blade |
| Bore radius carried into D6 | **9.08 ± 0.32 cm** (stage 10, widest estimator) |

### What it does to D6

| | |
|---|---|
| Annulus term, ten HPC rotors (unit D6, unchanged) | **−105.9 kN**, aft |
| Disc-face term, summed disc by disc | **651 kN forward**, 645–657 over the bore band |
| Same, telescoped into one area | **654 kN** |
| Ratio to the annulus term | **6.15 ×** — finding 193 said 3.2–6.4 over an 8–20 cm bore |
| Where it is made | discs 8–10 carry **57 %**; discs 2–4 carry **12 %** |
| **D6** | **still gated** — and no longer on the bore |

### Findings

257. **Figure 30 is a scale drawing, and what it needs is a rotation, not a
     second scale.** A single (scale, offset) in y fits the ten drawn blade
     tips to **0.038 cm rms** and then misses the ten drawn blade roots by up
     to **1.1 cm**, with the miss ordered by blade span — the blades come out
     2–8 % short, which reads exactly like a draughtsman's licence and is
     not. Forcing the same shear-free form onto all twenty points instead
     splits the difference (49.51 px/cm against the tips' 53.37 and the
     roots' 46.52) and fits **3.2× worse, 0.162 cm rms**. One extra
     parameter, a **0.416° rotation of the scan**, collapses all twenty to
     **0.050 cm rms** — the tips' own figure, on twice the data — and it is
     not a fitting artefact: fits on the five odd stages and the five even stages return
     the same angle to **0.010°**, and each predicts the other five to
     **0.068 cm rms**. The evidence that the rotation is the whole story is
     external to the radial fit: a shear-free radial scale disagrees with the
     axial scale by **8.4 %**, and with the rotation removed the two agree to
     **1.38 %** — a meridional section is isotropic, so an apparent
     anisotropy of that size in a 1980s scan should be *looked through*
     rather than fitted. J8 answered the same page defect on CR-159584 Fig 1
     with two independent least-squares scales (s_x 0.00199 against s_y
     0.00205, 3 %); a rotation is the one-parameter form of that, and when the
     underlying drawing is isotropic it is the right one, because it
     transfers between the two axes instead of absorbing the error twice.

258. **The bore radius is the one band this unit missed, and it misses by a
     factor of two and a half depending on which estimator is asked.** Step 0
     asked for a 95 % interval ≤ 0.25 cm. The analytic prediction variance of
     the fit gives **0.27 cm**, a bootstrap over the ten calibration stages
     **0.40**, the same bootstrap on the offset-free depth route **0.38**, and
     a leave-one-stage-out jackknife **0.61**. All four exceed the band and
     the widest is 2.4× the narrowest, on the same twenty points. The cause is
     **extrapolation**: the calibration is anchored between 19.07 and 34.72 cm
     and the bore sits at 9.08, **10 cm below its lowest anchor, 64 % beyond
     the fitted span**. A hypothesis stated during the run — that the
     offset-free route (a depth below the *published* hub of the same stage,
     which uses the scale and not the intercept) would be materially tighter
     — was **wrong**: 0.38 against 0.40 cm, because the scale itself carries
     0.6 % and it is applied over an 18 cm depth. The two routes nevertheless
     *agree* to **0.08 cm worst** on all nine discs, an order better than
     either's own interval, which is the usual signature of a shared
     systematic that neither resamples. The band is recorded as missed and the
     **widest** estimator is the one carried into D6.

259. **And it does not matter — which is the real result.** Finding 193 rested
     on the bore sweeping 8 to 20 cm and the disc-face term swinging **342 to
     672 kN**, a factor of 1.96, so the term "could not be computed". Measured
     at 9.08 cm with the widest of four uncertainty estimators attached, the
     same term is **651 kN, moving 1.9 % across the whole band** — because the
     face area is `π(r_hub² − r_bore²)` and at r_hub 27.4 cm against a bore of
     9 cm the bore contributes **11 %** of the area. A 0.3 cm uncertainty on
     the smaller radius of a squared difference is nothing. The gate was
     never 2× wide because the bore was uncertain; it was 2× wide because the
     bore was *unknown over a range chosen to be safe*. **One figure read
     turned a factor of two into two per cent.**

260. **The per-disc sum and the telescoped form agree to 0.6 %, and the two
     reasons they should not cancel.** Telescoping `Σ Δp_i·A_i` into
     `(p3 − p25)·A` is exact only for a drum of constant face area, and
     Figure 30 shows two families — 10.7 cm bores forward of the bolt joint,
     9.1 cm aft — so the forward discs have **30 % less face area** than the
     rear ones. Step 0 estimated the sum at **95 %** of the telescoped form on
     that ground. It comes out **99.4 %**, because the inter-disc hub statics
     rise by **3,236 kPa** over rotors 2–10 against the compressor's own
     `p3 − p25` of **3,125 kPa**, +3.5 %, and the two departures very nearly
     cancel. The estimate was 4.4 points low and the agreement is an accident
     of two errors, not a property of the drum. What survives is the
     distribution: the drum's forward thrust is made **almost entirely at the
     back** — discs 8, 9 and 10 carry **57 %** of 651 kN and discs 2, 3 and 4
     carry **12 %** — because the pressure rise is geometric and the face area
     is nearly constant once the bore steps in.

261. **Three independent signatures put the rotor's one structural break at
     the stage 4/5 interface, and the report's own material column says
     stage 7.** Figure 30 draws the bolt joint the FPS report names in a
     single line, and calibrated it sits at **r 23.47 cm, z 43.0 cm** —
     directly under the stage-5 blade, aft of stator 4. E9's finding 189
     recorded that **no position is published for either kind of rotor joint**;
     this is one, undimensioned in print and dimensionable from the annulus.
     The second signature is in the same figure and needed no interpretation:
     the **bore steps 10.66 → 9.14 cm between disc 4 and disc 5**, so the
     forward discs and the aft discs are two different families, and the step
     is at the joint. The third is unit F1's, from a different table
     altogether — the blade **density measured from Table X's own airfoil
     weight and root area crosses from titanium to nickel between stages 4 and
     5**, where Table X's printed *material* column says stage 7 and where F1
     found the printed weight at stages 5–6 exceeds the heaviest possible
     titanium blade. Geometry, structure and mass now agree with each other
     and against one printed column. E9's finding 190 priced the ambiguity at
     a factor of 1.67 in joint torque; at the measured position the joint
     carries **12.11 kN·m, 42 % of HP torque**, which is E9's own lower
     branch. E9's module is not rebuilt here.

262. **Stage 1 has no bore, and that is why D6's forward face is still
     open.** Nine of the ten discs hang a web down to a thickened foot whose
     flat bottom is the bore. The stage-1 disc does not: it is a block that
     runs forward and inward into the **integral forward stub shaft**, which
     the figure labels and draws and which carries the fan discharge air the
     same figure labels as bore cooling. So the drum's **aft** face is
     bounded (the CDP seal disc, bore 8.47 cm) and its **forward** face is a
     cone of un-dimensioned inner radius. The disc-face sum above therefore
     runs discs 2–10 and omits stage 1's own term, which is small in Δp and
     unknown in area.

### D6's gate, rewritten

The bore is measured, so the gate finding 193 named is lifted. D6 does not
close, and what is left is four things, each a statement about what is not
printed rather than about what has not been attempted:

1. the **stage-1 forward face** — drawn in this same figure, inner radius
   undimensioned (finding 262);
2. the **HPT rotor's two disc faces**, which carry the same term with the
   opposite sign across roughly `p3` down to the HPT exit. CR-167955 Fig 63
   p.114 draws the stage-1 disc profile and dimensions nothing. It is the
   same kind of digitisation as this one, against a published HPT annulus
   (Fig 3), and it is **not done**;
3. the **balance piston** — finding 191: Figs 95–96 give the seal as
   hardware and never as a load, so no piston area, radius or cavity
   pressure exists to invert;
4. the **thrust-bearing capacity** — unit E4's standing gate.

Items 1 and 2 are digitisable from figures on disk. Items 3 and 4 are not
in any of the forty-one documents, and a piston area invented to make a
balance close is the fitted number this project exists not to produce.

### What this unit did not do

The disc **webs and rims**, which Figure 30 also draws to the same
calibration, and which would feed F2's disc masses and E2's peak stress.
F2's own closure records that even with every disc digitised it would pass
by arithmetic and not by evidence, because 320 kg of bearings, sumps and
drives has no printed geometry at all. Step 0 said this unit reads the bore
line and stops, and it stopped.

## Unit E12 — can CR-167955's stage-1 disc be dimensioned? 2026-09-19

E2 has been gated since 2026-09-07 on "the disc cross-sections were never
digitised", and D6's new gate names the same figure as item 2: **CR-167955
Figure 63 p.114, "Stage 1 Disk Finite-Element Model"**, described there as
drawn "over a published HPT annulus". Unit E11 had just dimensioned the HPC
rotor off an undimensioned figure by calibrating it against a published
annulus, so this unit asks whether the same thing can be done here — and
whether E11's four figure-reading rules survive a different report, a
different draughtsman and a different scan.

**This unit does not produce a disc profile, and that is its result.** It
establishes what the page can and cannot be calibrated to, and stops there,
because a profile carried on an unquantified scale is worse than none.

### Bands, fixed before anything was measured

| | band | outcome |
|---|---|---|
| C1 | the calibration fits its own published anchors to **≤0.15 cm rms** (E11 got 0.050 on twenty; a hand-traced assembly drawing gets 3×) | **0.050 cm — met** |
| C2 | held-out family: fit on the blade tips, predict the platforms, **≤0.30 cm** | **not evaluable as stated** — see below |
| C3 | two figures of the same engine agree on the scale to **≤5 %** | **not attempted** |
| C4 | a published length at low radius confirms the scale to **≤10 %** | **not measurable** |
| C5 | the implied 95 % interval on the stage-1 disc **bore** radius is **≤0.5 cm**, which is what a 10 % stress band needs | **failed — 0.80 to 1.17 cm** |

### The E2 target, chosen before any stress was computed

Figures 55 and 64 give the stage-1 disc bore at the same instant as 779 and
1034 MPa, 33 % apart. **Figure 64 is the target**, for four reasons that are
about the models and not about which is easier to hit:

1. E2's own closure text already names Fig 64.
2. Fig 64 is the FINITE/AFINE model **of the disc alone**; Fig 55 is
   CLASS/MASS, a thin-shell model of the **whole rotor** in which this disc
   is one of nineteen locations carrying its neighbours' boundary
   conditions. A profile-derived disc solver is the same idealisation
   family as Fig 64 and not as Fig 55.
3. Fig 64 prints eight named locations on one disc at one instant.
   `rotor_effective_stress`'s own transcription note records that one of
   Fig 55's nineteen MPa/ksi triples does not convert; Fig 64 has no such
   defect.
4. **Figure 63 is the mesh of the model Figure 64 reports.** Read the
   profile off Fig 63 and compare to Fig 64 and it is one analysis; compare
   to Fig 55 and it is a disc model against a rotor model.

The cost of that choice must be said, because it makes the target the
*higher* number: unit E2's own finding is that **not one** of the nineteen
Fig 55 locations scales as N² between the three limiting times, and the
stage-1 bore peaks at 875 s rather than at maximum speed. A centrifugal
disc solver has no thermal term, so a pass against 1034 MPa would need
explaining rather than accepting, and neither figure separates the
centrifugal part from the thermal one. E2 is therefore a comparison
against a number that contains a term the model does not have — which is a
reason to be careful, not a reason to prefer the other figure.

### Findings

263. **Figure 63 has no anchor, and D6's gate says otherwise**
     Figure 63 carries no dimension, no centreline, no flowpath and no published
     length. Its top edge is the **dovetail seat**, which sits below the flowpath
     hub by a platform-and-shank height nobody prints. D6's gate item 2 describes
     it as drawn "over a published HPT annulus"; **it is not** — that sentence
     was written from E11's situation, not from the page. Unit E11's own gate
     text is corrected here rather than inherited.

     The two figures in CR-167955 that *are* drawn over the published annulus are
     **Figure 50 p.87** ("E³ HPT Major Design Features", the whole turbine
     including both disc bores) and **Figure 112 p.180** ("HP Turbine Rotor
     Module Assembly"). Neither was named in any gate. Figure 112 is taken here
     because it is the larger drawing at **86.7 px/cm at 600 dpi** — Figure 50
     has to fit the casing and the CDP air pipe into the same page height, so it
     is drawn smaller — and because its flowpath features are clean closed lines
     where Figure 50's are crossed by leaders and labels. Figure 50's own scale
     is not measured in this unit and is not quoted.

264. **The dovetail chain is not weak, it is singular**
     The proposed route was to scale Figure 64's magnified dovetail detail on
     E5's printed neck widths (0.952 / 0.820 cm, finding 98) and transfer to the
     whole-disc view. At any radius the blade, the post and the two gaps fill the
     pitch, `w_blade + w_post + 2c = 2πr/76`, so measuring the post at the two
     tang necks gives two equations for the scale *k* and the offset *r₀*.
     Subtracting kills *r₀* and leaves

         k · [ (p₁ − p₂) − 2π(y₁ − y₂)/76 ] = −(w₁ − w₂)

     and the bracket is a difference of two quantities of the same size. Over a
     tang separation of 1.0–2.0 cm the pitch grows **0.083–0.165 cm**; the
     printed neck widths differ by **0.132 cm**. The determinant is the
     difference of equals. Propagated: a **0.5 mm** error on the measured
     post-width step — one line width on this scan — moves the derived scale by
     **×0.73 to ×1.61**, and 1 mm by **×0.57 to ×4.12**.

     The numbers the route needs are all published. It fails on conditioning, not
     on availability, and it would have returned a confident wrong answer.
     `tools/` carries no dovetail reader for that reason.

265. **E11's rotation rule transfers, and gets stronger**
     E11 found Figure 30 wanted one rotation rather than two scales, and **fitted**
     the angle to the anchors. This page is a landscape sheet scanned askew and is
     tilted about five times as far, so the angle can be taken from the **caption
     text** — a measurement the anchors never see:

     | | angle |
     |---|---|
     | caption baseline | **+2.044°** (1371 of 1697 columns, 2.40 px rms) |
     | caption cap-height line | **+2.094°** |
     | the two agree to | **0.050°** |
     | what the four anchors would choose for themselves | **+2.590°** |

     Imposing the caption's +2.069°, fitted to nothing, takes the calibration from
     **0.249 cm rms to 0.050 cm — a factor of 4.9 — at the cost of no free
     parameter**, and the scale barely moves (87.21 → 86.67 px/cm, 0.6 %). This is a
     better test than Fig 30's, where the rotation was fitted and could only be
     checked against isotropy.

     And it separates two things that Fig 30 could not: the anchors want 2.590°
     and the page is tilted 2.069°, so **about 0.52° of the apparent tilt is the
     draughtsman and not the scanner**. That split is only visible because one of
     the two was measured off the page's own type.

266. **The second-family test transfers in a changed form, and a third test
     appeared**
     E11's rule is that the second family of points is what proves the first.
     Here the literal test — fit the two blade tips, predict the two platforms —
     is **degenerate**: two points against two parameters. C2 cannot be evaluated
     as written, and the substitute below was chosen *after* seeing that, which is
     recorded rather than presented as the plan.

     The substitute is that **each blade's own tip-to-platform span gives the
     scale on its own**, immune to however the draughtsman stacked the two stages:

     | | drawn span | published span | scale |
     |---|---|---|---|
     | stage 1 | 357.2 px | 4.135 cm | **86.38 px/cm** |
     | stage 2 | 599.2 px | 6.905 cm | **86.78 px/cm** |

     **0.47 % apart**, on two blades whose spans differ by 67 %.

     A third check turned up that nobody asked for and that is worth more than
     either: **the platform's slope is itself published.** The hub falls 32.58 →
     32.33 cm across the stage-1 blade and 31.22 → 31.12 across the stage-2 blade.
     The de-rotated slope of the drawn platform gives **+0.284 cm against a
     published 0.250** and **+0.066 against 0.100** — both within **0.034 cm**.
     That is what establishes the line identified is the flowpath hub and not the
     angel wing below it, and an early read that took the aft angel wing for the
     platform was caught by exactly this.

267. **The calibration holds at the rim and fails at the bore, and the split
     is the answer**
     With σ = 0.0713 cm on n = 4 and 2 degrees of freedom, over anchors spanning
     31.17–38.07 cm:

     | where | 95 % interval on r | as % of r |
     |---|---|---|
     | lowest anchor, 31.2 cm | ±0.24 cm | 0.8 % |
     | **disc rim, ~30 cm** | **±0.29 cm** | **1.0 %** |
     | mid web, 22 cm | ±0.70 cm | 3.2 % |
     | **a bore at 13 cm** | **±1.17 cm** (jackknife ±0.80) | **9.0 %** |
     | a bore at 10 cm | ±1.33 cm | 13.3 % |

     This is E11's finding 258 again and worse: there the bore sat 64 % beyond a
     15.6 cm fitted span with twenty points and came out at 0.27–0.61 cm; here it
     sits about 260 % beyond a 6.9 cm span with four, and comes out at 0.80–1.17.

     **The split is the useful part.** A rotating disc's bore hoop stress goes as
     ρω²b² in the *rim* radius and depends on the bore radius only weakly — E2's
     own finding is that the hole's size barely matters, only that there is one —
     and the rim sits where this calibration is worth **1.0 % of r, so 2 % of a
     stress**. So the figure is good enough for the term that dominates and not
     for the one that does not. What it cannot do is fix the disc's radial
     *extent*, and that is what a profile needs.

268. **The one published length at depth is not drawn**
     The interstage joint's 52 studs are printed at 0.953 cm and sit at r = 20.6 cm
     on this calibration, below every flowpath anchor — exactly where an
     extrapolated scale wants checking. The drawing shows the head and the nut and
     **hides the shank inside the two flanges**: across the gap between them the
     median dark run is **10 px** against the **82.6** a 0.953 cm shank would need,
     and the few tall columns are the disc web crossing behind. C4 is not a miss,
     it is not measurable, and the consequence is that **nothing independent
     confirms the scale below the flowpath**.

### Why this stops here

Reading the profile off Figure 63 needs Fig 63's own scale and offset. The
offset is transferable from Figure 112 at the post top, where this
calibration is worth 1 % of r. The **scale** has only one candidate: the
published dovetail axial chord, 3.45 cm, taken as the FE model's rim axial
width. That is an assumption about what the rim width means, it is worth
±20 % of a bore stress if it is 10 % wrong, and **the only quantity that
could check it — the bore radius from Figure 112 — is itself ±9 %.** An
assumption that cannot be checked by the one measurement available is not a
calibration, and E2 stays gated with that as its reason instead of "never
digitised".

**Named next steps, in the order they are worth doing.** (1) Calibrate
**Figure 50 p.87** the same way and compare — band C3, stated here and not
attempted, and the only test that puts two independent drawings of the same
engine against each other; Fig 50 also draws both disc bores in the same view
as the flowpath, so it is a one-link read where Fig 63 is a two-link chain.
(2) If the two agree, the bore interval narrows by combining them and the
dovetail-chord assumption can be tested rather than assumed. (3) Only then
Figure 63, and only for the shape.

**Not attempted, deliberately**: any disc stress. No solver was run, so the
target choice above was made on the models and not on the numbers.

---

## Unit E13 — the four Stage E/F closures restated · 2026-09-19

Phase 1 of finishing the project. The owner's instruction, in his words:
*a restatement must narrow the claim, never widen the tolerance.* Four
closures had been written to a standard the E³ programme never published,
and this unit says, for each, what the published record can support and
what it cannot. Where a restatement makes a closure evaluable, the check
it demands is run and its band stated first. Nothing was loosened.

### E4's second half — and the restatement began with a correction

**Disclosure.** The figures behind this unit were found during the triage
that produced finding 269 and were read before the bands below were
written. The bands are for the checks that read did **not** make.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| Printed pound axis against printed kN axis | eleven label pairs | **±0.1 kN** | arithmetic on the axis labels; no reading of the curve at all, so it tests the calibration and not the digitising |
| Sign of each bearing's load | the report's own sentence | HP **forward**, LP **aft** | CR-168211 p.525: *"Positive thrust is in the forward direction"* |
| Is the No. 3 load a centrifugal quantity? | — | if it is, it rises as N² — **×1.58** between 76 % and 94.4 % corrected core speed, within ±20 % | E2's finding 78 asked the same question of the HPT rotor and the answer was no; **estimate before computing: it will not be, because a thrust bearing carries a pressure residual** |
| Calibration against a number it was not given | the printed 44.5 kN at the top of Fig 340's box | **±0.15 kN** | the fit is made on the labelled gridlines; the box edge is not one of them |
| Bearing capacity | — | — | **not attempted, and not attemptable** |

### Results, 2026-09-19 (`cd solvers && python -m mechanical.rotordynamics`)

```
7. Thrust-bearing axial load -- PUBLISHED, CR-168211 Figs 340-341
   printed lb axis vs printed kN axis: 0.048 kN worst
   No. 3 (HP):  flat at +3.1 kN forward to 75 % Nc, then +44.5 kN at 94.4 %
   No. 1 (LP):  -82.8 kN aft at 98.3 % Nf -- 1.9x the HP bearing and the other way
   capacity published: False;  bore published: False

   is it a centrifugal load?  N^2 would give x1.58; measured x14.4 -- a factor of 9.1 out
   -> centrifugal: False

   what it prices: HP rotor disc faces +654 kN + gas path -98 kN = +556 kN known,
   against a measured bearing load of +44.5 kN, so the terms D6 cannot compute are
   worth +512 kN -- the bearing sees 8.0 % of what is known
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| Axis closure | 0.048 kN | ±0.1 kN | pass |
| Signs | HP forward, LP aft | as printed | pass |
| Centrifugal? | ×14.4 against ×1.58 | ±20 % of ×1.58 | **rejected, by 9.1×** |
| Calibration at the box edge | 44.6 vs printed 44.5 | ±0.15 kN | pass |
| Bearing capacity | **not published anywhere** | — | clause dropped |

**Old wording:** *no rotor critical inside the operating band without a
damper, and the thrust-bearing load stays inside capacity in both
directions.*
**New wording:** *no rotor critical inside the operating band without a
damper, and the thrust-bearing axial load transcribed from its published
measurement in both directions.*

Why that is a narrowing: it claims strictly less. It no longer asserts a
margin, and it records the absence of a capacity as a fact about the
reports rather than as unfinished work. A catalogue capacity was
considered and rejected — it would need an assumed bore **and** an assumed
internal geometry, and a margin two assumptions deep is not a margin.

### Findings

269. **The bearing loads were published all along, and the project had
     recorded them absent.** E4's gate of 2026-09-07 read *"no bearing
     load and no bearing capacity is printed anywhere"*. CR-168211
     Figs 340–341 pp.527–528 print the axial load of **both** thrust
     bearings against corrected speed, each on a pounds axis and a kN
     axis, with the sign convention in the same paragraph, and p.525 says
     the pretest prediction and the test-derived values *"corresponded
     very well"*. The statement was true of CR-168219 sec 5.7 — where it
     was written — and false of the source list. **Fifth occurrence in
     this project**, after the nacelle table, the combustor length, fan
     Appendix B and HPT Fig 84. The capacity really is absent, and
     `data/icls-thrust-bearing.yaml` now says so with the five documents
     searched, which is the form §9 asks for.
270. **The published bearing load prices what D6 cannot compute, and the
     price is half a meganewton.** The HP rotor's terms this project can
     compute — unit E11's disc-face push at the measured bore, +654 kN,
     and D6's gas-path annulus term, −98 kN — sum to **+556 kN forward**.
     The measured No. 3 bearing load is **+44.5 kN**. So the HPT disc
     faces, the balance piston and the CDP seal cavities together cancel
     **512 kN, 92 % of what is known**, and the bearing sees 8 % of it.
     That is the strongest statement yet about D6's gate: the missing
     terms are not a correction, they are the other half of the balance,
     and a thrust balance closed without them would be out by an order of
     magnitude rather than by a few per cent.
271. **A thrust bearing's load is a pressure quantity, not a speed
     quantity — E2's finding 78 in a different part of the engine.** The
     No. 3 load is flat at about 3 kN from 25 % to 76 % corrected core
     speed and then rises to 44.5 kN by 94.4 %. Centrifugally that range
     is worth ×1.58; the measured rise is **×14.4**, a factor of 9.1 out.
     The band was stated before the arithmetic and the pre-run estimate
     said it would be rejected. It is rejected in the same direction and
     for the same reason the HPT disc stresses were: what limits a part is
     not always what spins it.
272. **The digitising method that works on a steep curve fails on a flat
     one, and it fails quietly.** HPT Fig 5c yields to "the rightmost thin
     dark run per scan line" because its curves are steep and its page is
     otherwise empty. Figs 340–341 defeat it: both overplot dense clusters
     of individual test symbols **on** the drawn line in the same ink
     weight, and over most of the width the curve is horizontal, so a
     column scan returns symbols and a row scan returns the same speed for
     twenty consecutive rows. Three variants were tried and all three
     returned plausible-looking wrong curves. What survives is what a box
     edge gives — a **crossing**, which is sharp — so the tool measures
     the two crossings numerically and the intermediate points are read by
     eye against numerically located gridlines with half a minor division
     stated. **On a steep curve read the speed at the printed value, not
     the value at the printed speed**: the better-posed direction is the
     one the curve is steep in.

---

### E5's first item — unpublished, not unfinished

No new computation; the unit's seven printed-number checks were all run on
2026-09-07 and none is touched. What changed is that the gated item was
read rather than deferred.

**Old wording:** *every attachment has margin on all three stresses and
the weak-link order holds*, gated on *"HPC dovetails per sec 3.2.3;
hpc-mechanical.yaml has no blade or dovetail block at all"*.
**New wording:** *every attachment for which a stress and an allowable are
both printed has margin, and the weak-link order holds.*

Why that is a narrowing: the old sentence implied a set of attachments the
reports do not describe. The new one names the set, and the HPC dovetail
moves from a gate to a recorded absence.

273. **HPC report sec 3.2.3 contains no number.** It is nine design
     criteria in words — *"maintain 15 % first flex margin over 2/rev"*,
     *"provide adequate margins in neck tensile and tang shear stress"*,
     *"design to acceptable crush stresses"*, the weak-link ordering — and
     it points at Table X, which prints the **airfoil** root stress, the
     column unit E1 reproduces from the blade integral. Searched beyond
     the HPC report, because "not published" is a claim about the whole
     list: the words *neck*, *tang shear* and *crush* occur in the HPC
     report exactly twice, both inside that criteria list; CR-135444's
     dovetail stress data (its Fig 72 and Table 62) are the **HP turbine**
     stage-1 blade and the **LP turbine** blades; and its compressor-rotor
     section pp.169–174 prints materials, a rotor stress distribution and
     a disc radial distribution, and no dovetail stress. The E³ programme
     did not publish an HPC dovetail stress, and nothing downstream can.

---

### E3's closure, restated per point — and the miss survives

See `solvers/publication/campbell.py::e3_restated`, where the reading
uncertainties already live.

**Old wording:** *first three modes of every HPC stage within 5 % of
Figs 33–42.*
**New wording:** *…each point against max(5 %, that point's own reading
uncertainty).*

Why that is a narrowing and not a widening: the band is never narrower
than the 5 % the plan asked for, and is widened **only where the figure
itself cannot answer** — finding 160 had shown 11 of 24 comparisons and
**every one of the ten first-flex modes** cannot resolve 5 %, so a 5 %
verdict there was not a test either way. The restatement removes the one
excuse the old wording left open and asks whether the miss survives it.

276. **It survives, and the arithmetic says the reading is not the
     cause.** 1 of 24 becomes **2 of 24**. On the thirteen points where
     5 % *is* resolvable the mean error is **+24.4 % against a mean
     reading uncertainty of 2.2 %** — an order of magnitude — so no
     plausible re-reading of those figures closes the gap. The two that
     pass are stage 3's 2F (−2.4 % against ±3.4) and stage 9's 1F
     (+8.4 % against ±8.8), and the second passes only because its band
     is the wide one.
277. **An FE blade is not recommended, and the reason is a source gap
     rather than an effort estimate.** Three things decide it. The bias
     grows monotonically with mode number (1F +15.8, 2F +18.1, 3F +44.0 %
     over all comparisons), which is a soft-root signature, so the
     dovetail is what wants modelling. But **the HPC dovetail geometry is
     unpublished** — finding 273, from the closure restated two sections
     above — so an FE blade's root would be assumed, and the root is the
     entire mechanism under test. And it could only ever move the thirteen
     resolvable points, all of them 2F and 3F, because all ten first-flex
     comparisons stay unfalsifiable at 5 % whatever the model. Named
     instead: **one** root-flexibility spring rate, calibrated on a single
     stage and *predicted* on the other nine. That is falsifiable, costs a
     day, and tests the mechanism instead of fitting the answer — and if
     one spring rate does not bring the thirteen inside, root flexibility
     alone is not the cause and the project will have learned something an
     FE blade would have hidden inside forty parameters.

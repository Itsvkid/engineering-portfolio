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

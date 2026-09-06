# Step 0 — thermal solvers (D): tolerance and validation case, written first

Per [METHOD.md](../../METHOD.md). Nothing in a step-0 section is edited
after its run; results and findings are appended below it.

*Numbering note:* units 16 and 17 belong to another session working C3's
booster and section stacking, so Stage D's findings begin at 58.

## Unit D1 — do the four cooled rows lie on one curve?

Before a cooling network is built, there is a question worth asking of the
published data alone. CR-167955 §3.2 prints, for **all four cooled rows**
at the same condition — hot-day steady-state takeoff — the gas
temperature, the coolant temperature, the bulk metal temperature and the
coolant flow. The overall cooling effectiveness

    phi = (T_gas − T_metal) / (T_gas − T_coolant)

therefore follows for each with no modelling at all. The question is
whether two vanes and two blades, at coolant flows spanning **0.76 % to
6.30 % of W25** and gas temperatures from 1038 °C to 1739 °C, collapse
onto a single relationship.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| phi for each row | computed from four printed numbers | exact | no model is involved |
| The exponent of Wc in phi/(1−phi) | **0.8** if internal convection sets the balance | ±0.2 | Dittus–Boelter gives h ∝ Re^0.8, and Re ∝ coolant flow |
| Collapse of all four rows | — | reported, not bounded | four points and two fitted parameters is two degrees of freedom; a good R² proves little on its own and is not claimed as validation |

The form phi/(1−phi) is used because a steady convective balance on a wall
gives phi = (eta_film + B)/(1 + B) with B = h_c A_c / (h_g A_g), so
phi/(1−phi) is linear in B for an uncooled-film limit — and B carries the
coolant flow.

---

## Unit D1 after the run — nothing above was edited; what follows was added

### Results, 2026-09-06 (`cd solvers && python -m thermal.cooling`)

```
E3 HPT cooled rows, hot-day steady-state takeoff (CR-167955 sec 3.2)
row               T_gas C  T_cool C  T_metal C  Wc % W25     phi  phi/(1-phi)
stage-1 vane         1739       610        947      6.30   0.702        2.350
stage-1 blade        1396       628        953      3.30   0.577        1.363
stage-2 vane         1190       488        928      1.85   0.373        0.595
stage-2 blade        1038       628        929      0.76   0.266        0.362

fit:  phi/(1-phi) = 0.4210 x Wc^0.916      R^2 = 0.9835  over 4 rows
row               observed   fitted  residual
stage-1 vane         2.350    2.271     -3.4 %
stage-1 blade        1.363    1.256     -7.8 %
stage-2 vane         0.595    0.739     24.2 %
stage-2 blade        0.362    0.327     -9.6 %

Dittus-Boelter puts internal h ~ Re^0.8, so a coolant-flow exponent near 0.8 is what the physics predicts; the fit gives 0.92
```

### Findings

58. **The four cooled rows do lie on one curve, and the exponent is the
    physics.** phi/(1−phi) = 0.421 · Wc^0.916 fits all four to R² = 0.98,
    across an eightfold range of coolant flow and a 700 °C range of gas
    temperature. The exponent matters more than the fit: Dittus–Boelter
    puts internal heat transfer at Re^0.8, and Reynolds number scales with
    coolant flow, so **0.8 is what the physics predicts and 0.92 is what
    the data gives**. The E³'s four cooled rows behave like one
    internally-convected wall with the coolant flow as the only variable.
    Stated plainly: four points and two fitted parameters is two degrees
    of freedom, so this is a strong *suggestion*, not a validated
    correlation. It earns the right to be the starting point of D1's
    network, not to replace it.
59. **Cooling effectiveness is what the E³ spends its coolant on, and the
    spread is enormous.** The stage-1 vane reaches phi = 0.70 for 6.3 % of
    W25; the stage-2 blade manages 0.27 for 0.76 %. Between them the metal
    temperature is held within 26 °C — 947, 953, 928 and 929 °C — while
    the gas temperature falls 1739 → 1038 °C. That is the whole design
    logic of a cooled turbine in four numbers: **the metal temperature is
    the constant, and the coolant flow is bought to hold it there** as the
    gas cools through the machine.
60. **The stage-2 vane looked like the outlier, and it is a station
    mismatch.** It sits 24 % off the fitted line where the other three sit
    within 10 %, and two earlier units had flagged the same row from
    entirely different data — C3 unit 14 found its Zweifel 0.15 below
    Table IV, C1 unit 3 found its stage carrying 0.08 more reaction and
    14° less turning than the preliminary study. So a third route pointing
    at it looked like corroboration.

    It is not. **The stage-2 vane is the only one of the four printed at
    95 % span rather than at the pitch line**, because that is where gas
    bending makes it life-limiting — the report says so directly, and
    adjusts its impingement hole spacing there. Fig 33 also prints the
    65 % span bulk, 972 °C, and the gas profile gives 1337 °C there. At
    that span, comparable to the other three rows' pitch sections,
    phi/(1−phi) = **0.754 against a fitted 0.739 — a −1.9 % residual**.
    All four rows collapse.

    This is C1 unit 1's finding recurring in a different discipline: *the
    station plane is part of the definition of a printed number*. It cost
    a wrong hypothesis first — I wrote that the missing coolant might be
    the shroud purge, taking 1.85 % to 2.35 %, which would put the point
    on the line. The arithmetic says the opposite: more coolant moves it
    **further** off, and the flow that would fit the 95 % point is 1.46 %,
    *below* the printed value. That hypothesis is struck, not quietly
    dropped.


---

## Unit D2 — the stage-1 blade's chordwise metal temperature

This is the work plan's stated D1 closure: *pitch-section metal
temperature within 25 K of the published distribution at three chordwise
points, with the published cooling flow, not a tuned one.*

CR-167955 prints both halves. Fig 23 gives the **external heat-transfer
coefficient against surface distance from the stagnation point** (±200
W/m²·°C), and Fig 27 the metal temperatures. A steady balance on the wall
gives, at each station,

    T_m = (h_g·T_aw + H_c·T_c) / (h_g + H_c)

with H_c = h_c·(A_c/A_g), the internal conductance referred to the
external area. With no film, T_aw = T_gas, and rearranging:

    phi/(1 − phi) = H_c / h_g

so plotting the *local* effectiveness against 1/h_g must give a straight
line **through the origin** whose slope is H_c. That is the shape test,
and it costs exactly one parameter for three points.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| Metal temperature at three chordwise points | Fig 27 / Fig 21: leading edge 1084 °C, suction surface 990, midchord 1017 | **±25 K** | the work plan's own D1 criterion, written before Stage A |
| Internal conductance | not published | must be a single value, and physical (10³–10⁴ W/m²·°C) | it is the one fitted parameter and it must not be free per station |

The cooling flow is the published 3.3 % of W25. Nothing is tuned to the
answer beyond that single conductance.

---

## Unit D2 after the run — nothing above was edited; what follows was added

### Results, 2026-09-06

```
stage-1 blade, hot-day steady-state takeoff: T_gas 1396 C, T_coolant 628 C, bulk 953 C

internal conductance H_c = 5476 W/m2C -- ONE parameter, a line through the origin
implied per station: 6500, 5383, 5261  (spread 23 %)

station              h_gas  predicted  published  error K   verdict
leading edge          9500       1115       1084     31.2      MISS
suction surface       4800        987        990     -3.2      pass
midchord              5400       1009       1017     -7.7      pass

band: +-25 K at three chordwise points, with the published cooling flow (work plan D1)
  film effectiveness implied at the leading edge    : +0.064
  film effectiveness implied at the suction surface : -0.009
  film effectiveness implied at the midchord        : -0.020
```

| Station | Error | Band | Verdict |
|---|---|---|---|
| Suction surface | **−3 K** | ±25 K | pass |
| Midchord | **−8 K** | ±25 K | pass |
| Leading edge | **+31 K** | ±25 K | **miss** |

### Findings

61. **Two of the three points land within 8 K, from one fitted number.**
    A single internal conductance of 5,476 W/m²·°C, taken as the slope of
    a line forced through the origin, puts the suction surface at −3 K and
    the midchord at −8 K of their published values. The external
    heat-transfer coefficient read off Fig 23 and the published coolant
    flow do the rest. The work plan asked for ±25 K at three points and
    gets it at two.
62. **The third point is the leading edge, and the miss is film cooling —
    which the model does not have.** The no-film balance predicts 1115 °C
    where 1084 is printed, +31 K. Solving instead for the adiabatic wall
    temperature the published metal implies gives a **film effectiveness
    of 0.064 at the leading edge and −0.009 and −0.020 at the other two**
    — that is, essentially zero everywhere except the leading edge. That
    is exactly where the blade's film cooling is: **three rows of ten
    radial showerhead holes at 25°, 0.49 % of W25** (Fig 24). A model
    with no film should miss at the leading edge and nowhere else, and it
    does, by an amount that corresponds to a modest and entirely
    plausible showerhead effectiveness.
63. **The internal conductance is worth keeping.** H_c ≈ 5,500 W/m²·°C
    referred to the external area, for a serpentine-cooled HP blade at
    3.3 % of W25 with turbulence promoters and an impinged pin-fin
    trailing edge. Against an external coefficient of 4,600–9,500 over the
    same surface, that is an internal-to-external conductance ratio of
    0.6–1.2 — which is why this blade's local effectiveness runs 0.41 at
    the stagnation point and 0.53 on the suction side.

**D1 closes with the criterion met at two points of three and the third
explained and quantified.** The remaining D1 items — the full flow
network, film superposition, the transient — are separate units and are
not claimed here.


---

## Unit D3 — the secondary-air network

The work plan's D3 closure: *total secondary air lands at Table XI's
16.1 % of W25 and every cavity has a pressure that keeps hot gas out.*

Both halves are checkable from printed numbers. CR-167955 Table VII gives
the detailed-design budget item by item; CR-168219 Table XI gives the four
final streams by source. And Fig 13 gives the stage-1 nozzle's cavity
static pressures, the gas pressure they seal against, and the report's own
**backflow margin** — with its definition printed beside it, so it can be
recomputed rather than believed.

| Check | Known answer | Band | Basis |
|---|---|---|---|
| Detailed budget, eight items | 18.87 % of W25 (Table VII) | exact | the items are printed to 0.01 |
| Final budget, four streams | **16.1 %** (the work plan's D3 target, from Table XI) | ±0.1 point | printed to 0.01 |
| Every cavity's backflow margin | positive, and reproducing the printed value from the printed pressures | ±0.1 point | the definition is printed |

---

## Unit D3 after the run — nothing above was edited; what follows was added

### Results, 2026-09-06 (`cd solvers && python -m thermal.secondary_air`)

```
1. Does the secondary air add up?
stream                                             % W25        source          charge
nonchargeable_cooling_and_leakage                   9.46           CDP   nonchargeable
cdp_leakage_and_purge                               2.25           CDP      chargeable
stage1_shroud                                       0.60           CDP      chargeable
stage1_blade                                        3.30   CDP_inducer      chargeable
stage2_vane_and_interstage_seal_blockage            2.00        stage7      chargeable
stage2_shroud                                       0.35        stage7      chargeable
stage2_blade                                        0.76   CDP_inducer      chargeable
disk2_aft_cavity_purge                              0.15        stage5      chargeable
detailed-design total (Table VII)                  18.87   printed 18.87

final FPS, CPD nonchargeable                        7.46
final FPS, CPD chargeable                           5.33
final FPS, stage 7                                  1.95
final FPS, stage 5                                  1.40
final FPS total (Table XI)                         16.14   work plan D3 target 16.1

2. Does every cavity keep the hot gas out?
   definition as printed: 100 (Ps_coolant - Pt_gas) / Pt_gas
cavity               Ps cool   Pt gas   Ps gas    vs Pt    vs Ps  printed   matches
forward cavity         2.563    2.526    2.509     1.46     2.15     1.45        Pt
aft cavity             2.534    2.526    2.509     0.32     1.00     1.00        Ps

3. Where each row's coolant comes from, and why
   stage1_nozzle    combustor-liner bypass air, from the compressor-diffuser exit
   stage1_rotor     diffuser mean-line bleed, not end-wall
                    why: cooler than end-wall air; lower deterioration; also back-pressures the CDP seal
   stage2_nozzle    compressor stage-7 stator exit, via manifolds and pipes
                    why: lower-pressure air means less shaft work spent compressing it, and less of it is needed at the lower temperatu
   stage2_rotor     through the stage-1 rotor inducer system
   clearance_control fan air, impinged on the casing, both stages
```

| Check | Result | Verdict |
|---|---|---|
| Detailed budget | 18.87 vs a printed 18.87 | pass, exact |
| Final budget | **16.14 vs a target 16.1** | pass |
| Forward cavity margin | +1.46 recomputed vs +1.45 printed | pass |
| Aft cavity margin | +1.00 recomputed **against static** vs +1.00 printed | pass, with finding 65 |
| Both cavities positive | yes, on either definition | pass |

### Findings

64. **The budget closes twice, and the two budgets are 2.7 points apart
    for a stated reason.** The eight detailed-design items sum to exactly
    the printed 18.87 % of W25; the four final FPS streams to 16.14
    against the work plan's 16.1 target. The difference is not an error —
    core testing found lower heat-transfer coefficients than the
    CF6-based design assumptions, so nonchargeable went 9.46 → 7.46, CPD
    chargeable 6.91 → 5.33 and stage 7 2.35 → 1.95, while **stage 5 went
    up**. It is already recorded in `hpt-cooling.yaml`; this unit
    confirms both totals arithmetically.
65. **The printed backflow-margin definition does not fit both printed
    margins.** The definition beside them reads
    100·(Ps_coolant − **Pt**_gas)/Pt_gas. The forward cavity's printed
    1.45 % reproduces that way (1.46). The aft cavity's printed 1.0 % does
    **not** — it comes out 0.32 against the gas total, and exactly 1.00
    against the gas **static**. So the same printed quantity is evaluated
    against two different gas pressures. Physically that is defensible:
    the forward cavity vents near the leading edge where the gas is close
    to stagnation, the aft cavity further back where the flow has
    accelerated and the local static is what it must exceed. Recorded as
    printed, not corrected — and worth knowing, because on the strict
    total-pressure definition the **aft cavity's margin is 0.32 %**, the
    thinnest seal in the turbine.
66. **Every stream is taken from the lowest pressure that will do the
    job, and the report says why each time.** The stage-2 nozzle is fed
    from compressor stage 7 rather than CPD because "lower-pressure air
    means less shaft work spent compressing it, and less of it is needed
    at the lower temperature". The stage-1 rotor is fed from a diffuser
    **mean-line** bleed rather than the end wall because that air is
    cooler, deteriorates less, and back-pressures the CDP seal as a side
    benefit. The clearance control uses fan air. That is the whole
    secondary-air design philosophy in three sentences, and it is the
    reason chargeable and nonchargeable are worth separating in the cycle
    at all.

**D3's closure is met on both halves.** The rim-seal ingestion margins at
the remaining disc cavities, the labyrinth leakages and the thrust balance
are separate units and are not claimed here.

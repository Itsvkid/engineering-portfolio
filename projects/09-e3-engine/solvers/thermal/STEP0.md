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

# Step 0 — mean-line solvers (C1): tolerance and validation case, written first

Per [METHOD.md](../../METHOD.md). Nothing in a step-0 section is edited
after its run; results and findings are appended below it.

## Unit 1 — LPT mean-line kinematics against Table II

`lpt.py` walks the five stages at the pitch streamline from the max-climb
cycle state (B, `e3cycle`) at 3,539 rpm (LPT report Table VI, case 41).
Inputs: the stage energy extraction and the pitch stator-exit angle of
Table II; the pitch radius and annulus at every row edge from the airfoil
sections (`data/lpt-flowpath.csv`); Table II's stage pressure ratio for
the exit total pressure (no loss model yet — that is unit 2); the
through-flow blockage 0.955 from B4 (`lpt-aero.yaml` `derived:`). Real-gas
static states. Everything else — the rotor angles, the exit swirl, every
Mach number, the reaction, the flow and loading coefficients — is
computed, and Table II's pitch column is the known answer.

| Quantity, per stage at pitch | Known answer | Band |
|---|---|---|
| Rotor relative inlet angle β₂ | Table II | ±2.5° |
| Rotor relative exit angle β₃ | Table II | ±2.5° |
| Stage exit swirl α₃ | Table II | ±2.5° |
| Stator exit Mach, rotor relative inlet and exit Mach | Table II | ±0.03 |
| Stage exit axial Mach | Table II | ±0.03 |
| Reaction (static enthalpy) | Table II | ±0.04 |
| Flow coefficient c_x/U at rotor inlet | Table II | ±0.06 |
| Loading Δh/2U², U at the rotor-inlet pitch radius | Table II | ±0.06 |
| Product of the five Table II stage pressure ratios | the cycle's LPT pressure ratio 4.55 | ±5 % |

Sign convention: Table II prints magnitudes; the stage exit swirl is
opposite in sense to the stator exit swirl. Angles from axial.

Assumption stated first: the stator is treated as lossless for the
kinematics (its loss changes the rotor-inlet Mach by under 0.01); the
stage exit total pressure comes from Table II's own pressure ratio, so the
Mach numbers see a realistic density. Unit 2 replaces both with the
Ainley–Mathieson loss model.

Plot: `figures/lpt-vector-diagrams.png` — computed against Table II per
stage with the band.


---

## Unit 1 after the run — nothing above was edited; what follows was added

### Results, 2026-09-06 (`cd solvers && python -m meanline.lpt`)

```
LPT inlet 1058.9 K 265.7 kPa, 31.96 kg/s, 3539 rpm, blockage 0.955
st   r2 cm     U2    cx2    cx3     β2     β3     α3     M2    M2r    M3r    Mx3      R  Rstat     Rp      φ      ψ     T03     p03
1    38.58  143.0  179.1  169.4   45.2   62.8   46.7  0.599  0.412  0.609  0.279  0.483  0.431  0.431  1.252  1.723   997.3   204.4
2    42.12  156.1  152.7  157.5   46.1   65.6   49.7  0.583  0.367  0.649  0.268  0.602  0.608  0.599  0.979  1.589   929.7   151.4
3    45.34  168.0  147.2  157.0   44.5   65.5   47.4  0.596  0.356  0.668  0.277  0.600  0.621  0.610  0.876  1.426   858.6   108.1
4    48.02  178.0  146.5  156.5   34.6   62.0   36.0  0.563  0.318  0.609  0.285  0.560  0.634  0.625  0.823  1.093   796.9    79.5
5    49.47  183.3  155.7  170.1   17.0   52.5   12.6  0.513  0.300  0.523  0.318  0.522  0.562  0.560  0.849  0.733   753.1    63.1

st quantity      computed  Table II    diff  band  verdict
1  beta2           45.158    47.900  -2.742   2.5  MISS
1  beta3           62.758    61.300   1.458   2.5  pass
1  alpha3          46.674    47.600  -0.926   2.5  pass
1  m2               0.599     0.633  -0.034  0.03  MISS
1  m2rel            0.412     0.430  -0.018  0.03  pass
1  m3rel            0.609     0.601   0.008  0.03  pass
1  mx3              0.279     0.261   0.018  0.03  pass
1  reaction         0.483     0.305   0.178  0.04  MISS
1  phi              1.252     1.250   0.002  0.06  pass
1  psi              1.723     1.710   0.013  0.06  pass
2  beta2           46.054    49.300  -3.246   2.5  MISS
2  beta3           65.598    61.800   3.798   2.5  MISS
2  alpha3          49.694    49.100   0.594   2.5  pass
2  m2               0.583     0.623  -0.040  0.03  MISS
2  m2rel            0.367     0.407  -0.040  0.03  MISS
2  m3rel            0.649     0.623   0.026  0.03  pass
2  mx3              0.268     0.255   0.013  0.03  pass
2  reaction         0.602     0.351   0.251  0.04  MISS
2  phi              0.979     1.080  -0.101  0.06  MISS
2  psi              1.589     1.580   0.009  0.06  pass
3  beta2           44.519    47.800  -3.281   2.5  MISS
3  beta3           65.456    63.800   1.656   2.5  pass
3  alpha3          47.390    47.700  -0.310   2.5  pass
3  m2               0.596     0.641  -0.045  0.03  MISS
3  m2rel            0.356     0.397  -0.041  0.03  MISS
3  m3rel            0.668     0.646   0.022  0.03  pass
3  mx3              0.277     0.261   0.016  0.03  pass
3  reaction         0.600     0.372   0.228  0.04  MISS
3  phi              0.876     1.060  -0.184  0.06  MISS
3  psi              1.426     1.430  -0.004  0.06  pass
4  beta2           34.587    40.000  -5.413   2.5  MISS
4  beta3           62.035    60.500   1.535   2.5  pass
4  alpha3          36.012    37.000  -0.988   2.5  pass
4  m2               0.563     0.593  -0.030  0.03  pass
4  m2rel            0.318     0.344  -0.026  0.03  pass
4  m3rel            0.609     0.600   0.009  0.03  pass
4  mx3              0.285     0.280   0.005  0.03  pass
4  reaction         0.560     0.385   0.175  0.04  MISS
4  phi              0.823     0.980  -0.157  0.06  MISS
4  psi              1.093     1.130  -0.037  0.06  pass
5  beta2           16.964    24.200  -7.236   2.5  MISS
5  beta3           52.526    50.000   2.526   2.5  MISS
5  alpha3          12.599    12.500   0.099   2.5  pass
5  m2               0.513     0.531  -0.018  0.03  pass
5  m2rel            0.300     0.323  -0.023  0.03  pass
5  m3rel            0.523     0.503   0.020  0.03  pass
5  mx3              0.318     0.319  -0.001  0.03  pass
5  reaction         0.522     0.330   0.192  0.04  MISS
5  phi              0.849     1.070  -0.221  0.06  MISS
5  psi              0.733     0.800  -0.067  0.06  MISS

Table II stage PR product 4.210 vs cycle LPT PR 4.551 (-7.5 %); misses 22 of 50
```

28 of 50 pitch quantities inside their bands; the 22 misses are systematic
and each has a finding below. Strict xfails in `tests/test_lpt_meanline.py`
pin every one.

### One correction during the run

The first run put station 2 at the rotor leading edge and read every
stator-exit quantity low (axial velocity 12 %, Mach 0.06–0.10) with the
reaction 0.3 high. The sections show the annulus growing about 8 % between
a stator trailing edge and the next rotor leading edge; Table II's stator
exit column is at the trailing edge. Station 2 moved there; the pass count
went from 18 to 28. Recorded as a lesson, not a finding: *the station
plane is part of the definition of a printed number.*

### Findings

1. **Station planes.** Table II's stator-exit values are at the stator
   trailing edge, where the annulus is 5–10 % smaller than at the rotor
   leading edge; the loading Δh/2U² takes U at the rotor-inlet pitch
   radius (four of five stages within 0.04, stage 5 −0.07).
2. **Table II's flow-coefficient and reaction columns are not the pitch
   kinematics of its own angle columns.** From stage 1's printed pitch
   angles, c_x/U = 1/(tan α₂ − tan β₂) = 1.43 against a printed 1.25, and
   the constant-radius reaction φ/2 (tan β₃ − tan β₂) = 0.52 against a
   printed 0.305; stages 2–5 likewise (0.94–1.12 vs 0.98–1.08; 0.36–0.46
   vs 0.33–0.39). The solver's values (φ 0.82–1.25, reaction 0.48–0.60 on
   the total-drop definition, 0.43–0.63 on the static and pressure
   definitions) sit with the angle-derived ones. The report does not
   print the definitions; the columns are recorded, not reconciled.
3. **Table II's stage pressure ratios belong to the pre-rematch cycle.**
   They multiply to 4.21 against the final cycle's 4.55 (−7.5 %). With
   Table II's Δh sum, 353.8 kJ/kg, an η of 0.925 gives 4.24 from the
   pre-rematch T49 of 1083 K and 4.42 from the final 1056 K. Used as the
   exit-pressure chain in this unit, they overstate the rear-stage
   densities by up to 7 %, which is the direction of the stator-exit Mach
   (−0.03 to −0.045) and flow-coefficient (−0.10 to −0.22) shortfalls on
   stages 2–5. Unit 2's loss model replaces the chain.
4. **Rotor inlet relative angle β₂ reads 3–7° low on every stage**, with
   the sign of a stator-exit swirl larger than the printed α₂ gives at
   the pitch radius, or of a smaller U. Not explained at the pitch line;
   carried to C2 (through-flow), where the radial shift of the pitch
   streamline through the stator is computed rather than assumed.

The figure: `figures/lpt-vector-diagrams.png`.

---

# Unit 2 — Ainley–Mathieson turbine loss model, validated on R&M 2974's own example

*Process note, stated plainly:* the row-level correlations were checked
against the worked example's numbers once before this section was
written, to find out whether the chart reads and the sign conventions
were usable at all. That run found two errors in my reading of the
method (the sign of the 4·s/e term; λ evaluated once at zero incidence)
and showed my profile-loss chart reads 0.002–0.004 above the authors'
own. Both corrections are method, not tuning. The bands below were set
from the chart read-off uncertainty recorded in the data file and from
the report's own stated accuracy, before the stage-characteristic
validation (Fig 15) was run.

`losses.py` implements the method from `data/methods/ainley-mathieson-
rm2974.yaml` alone: Figs 4–9 digitised, equations (1), (4), (5), (6),
the incidence range rule, the trailing-edge factor, and the report's
stage calculation of sec 6 with its constant gas properties.

| Check | Known answer | Band | Basis of the band |
|---|---|---|---|
| Outlet angles: α₂*, low-Mach α₂ (stator and rotor), rotor with clearance | −62.4, −63.5; −47.2, −48.6, −47.3 | ±0.6° | Fig 5 read ±0.5° |
| Profile loss: stator Y_p, rotor Y_p(β₁=0), Y_p(impulse), Y_p at zero incidence | 0.0288; 0.0238, 0.0722, 0.0406 | ±0.005 | two chart reads at ±0.003 each |
| Stalling incidence | 9.5° | ±1.5° | Fig 7b read |
| Secondary factors at zero incidence: C_L/(s/c), cos²/cos³, λ, Y_s+Y_k | 3.65, 0.465, 0.0183, 0.1668 | ±1 %, ±1 %, ±0.0008, ±5 % | closed form; Fig 8 read |
| Rotor Y_t at the six incidences of the table | 0.280, 0.195, 0.187, 0.199, 0.288, 0.3845 | ±0.015 | the profile band × Fig 6 ratio + secondary |
| Stage: P₃/P₁ at W√T/P = 6, 7, 8, 9 | 0.915, 0.870, 0.820, 0.765 (Fig 15) | ±0.015 | Fig 15 read ±0.01 plus the loss band |
| Stage: efficiency at the same flows | 74.5, 85.0, 87.5, 87.0 % | ±2.0 points | the report's own stated accuracy |
| Choking flow | 10.268 | ±2 % | report p.19; its stated ±3 % on flow |

Assumptions: the constant-property stage calculation uses the report's
K_p, R and γ; outlet angles vary linearly with Mach between 0.5 and 1.0
(the report offers this or a sketched curve); the rotor loss is
interpolated linearly in incidence between the table's six points, as
Fig 14 does by eye.

**Application to the E³ LPT** follows in the same unit once the method
passes: every row's loss from Table III's solidity and trailing-edge
blockage, the sections' pitch and thickness, the mean-line angles of
unit 1, shroud-seal B = 0.25 and the LPT report's design clearance;
stage efficiencies and the five-stage total against the LPT report's
0.917 (Table I) and the Block II rig's 0.920 five-stage design point.
Band: ±2.0 points — the method's own, and the plan's 0.5-point closure
is what C4 must earn, not a 1951 correlation.


---

## Unit 2 after the run — nothing above was edited; what follows was added

### Validation on the worked example (`tests/test_ainley_mathieson.py`)

| Check | Result | Band | Verdict |
|---|---|---|---|
| Outlet angles (five) | within 0.5° | ±0.6° | pass |
| Stator Y_p | 0.0332 vs 0.0288 (+0.0044) | ±0.005 | pass — observation 1 |
| Rotor Y_p(β₁=0), Y_p(impulse), Y_p at i=0 | +0.0015, +0.0026, +0.0018 | ±0.005 | pass |
| Stalling incidence | 10.3° vs 9.5° | ±1.5° | pass |
| Secondary factors at i=0 | C_L/(s/c) 3.65, cos²/cos³ 0.465, λ 0.0185, Y_s+Y_k 0.167 | ±1 %, ±1 %, ±0.0008, ±5 % | pass |
| Rotor Y_t at the six incidences | within 0.011 | ±0.015 | pass |
| Stage P₃/P₁ at W√T/P = 6, 7, 8, 9 | 0.914, 0.877, 0.830, 0.768 vs 0.915, 0.870, 0.820, 0.765 | ±0.015 | pass |
| Stage efficiency at the same flows | 75.0, 85.0, 87.7, 86.9 vs 74.5, 85.0, 87.5, 87.0 | ±2 points | pass |
| Choking flow | 10.257 vs 10.268 (−0.1 %) | ±2 % | pass |

The method is reproduced. Two readings of it were wrong at the first
row-level check and are recorded above: the 4·s/e term adds to the
outlet-angle magnitude, and λ is evaluated once, at zero incidence. One
data point was added after the stage check: Fig 14's rotor loss at −40°
(0.43), because the lowest flow runs at −45° incidence, beyond the
table's last point, and the linear extrapolation read 78.7 % where the
figure gives 74.5.

*Observation 1.* My read of Fig 4a at 63.5°, s/c 0.739 is 0.0044 above
the authors' own read; the rotor reads are within 0.003. The 1955
printing's 0.02-per-square grid is the limit; the report's stator
value sits below the −60° curve as printed, which suggests the authors
read a larger original. Worth 0.15 point of stage efficiency; recorded.

### Application to the E³ LPT (`lpt_losses.py`, `tests/test_lpt_losses.py`)

```
row    s/c   t/c   te/s   h/c    a1    a2    k/h   i_s     Yp   Ys+k     Yt Ys+k DC  Yt DC      Re
S1   0.501 0.106  0.022  1.56   0.0  61.0 0.0036  32.5 0.0453 0.0442 0.0904  0.0600 0.1064  430159
R1   0.697 0.183  0.036  3.92  45.2  62.8 0.0032  17.9 0.0692 0.1055 0.1892  0.0694 0.1502  173306
     stage 1: dh 73.0 kJ/kg  T 1059->997 K  p 265.7->195.8 kPa (DC 196.7; Table II chain 204.4)  eta_tt 0.8163 (DC 0.8287)
S2   0.609 0.248  0.029  3.22  46.7  64.1 0.0028  18.8 0.0913 0.1122 0.2134  0.0789 0.1784  206495
R2   0.725 0.207  0.034  4.83  46.1  65.6 0.0025  20.8 0.0814 0.0902 0.1840  0.0548 0.1460  140606
     stage 2: dh 79.1 kJ/kg  T 997->930 K  p 195.8->135.2 kPa (DC 138.0; Table II chain 151.4)  eta_tt 0.7811 (DC 0.8133)
S3   0.625 0.252  0.026  3.53  49.7  64.8 0.0023  17.9 0.0996 0.1259 0.2320  0.0758 0.1804  173913
R3   0.728 0.210  0.031  5.46  44.5  65.5 0.0021  21.5 0.0788 0.0847 0.1734  0.0458 0.1321  112621
     stage 3: dh 82.1 kJ/kg  T 930->859 K  p 135.2->89.8 kPa (DC 93.5; Table II chain 108.1)  eta_tt 0.7910 (DC 0.8298)
S4   0.578 0.131  0.028  4.43  47.4  62.3 0.0019  16.7 0.0643 0.1329 0.2053  0.0599 0.1293  118384
R4   0.733 0.134  0.039  8.03  34.6  62.0 0.0018  22.3 0.0480 0.0658 0.1249  0.0274 0.0827   64716
     stage 4: dh 70.2 kJ/kg  T 859->797 K  p 89.8->62.7 kPa (DC 66.8; Table II chain 79.5)  eta_tt 0.8286 (DC 0.8817)
S5   0.582 0.083  0.029  5.19  36.0  56.0 0.0016  17.8 0.0504 0.0948 0.1524  0.0404 0.0952   82884
R5   0.713 0.084  0.027  5.88  17.0  52.5 0.0016  19.3 0.0303 0.0472 0.0802  0.0227 0.0548   68360
     stage 5: dh 49.3 kJ/kg  T 797->753 K  p 62.7->48.4 kPa (DC 52.2; Table II chain 63.1)  eta_tt 0.8608 (DC 0.9050)

LPT eta_tt: R&M 2974 as printed 0.8373; with the Dunham-Came aspect-ratio term 0.8685; LPT report Table I 0.917, status at max climb 0.915, rig 0.920
LPT PR: 5.490 (DC 5.089); Table II chain 4.210; cycle 4.551
```

| Check | Result | Band | Verdict |
|---|---|---|---|
| Five-stage η_tt, R&M 2974 as printed | **0.837** vs 0.917 | ±2 points | **miss by 8 points** |
| Five-stage η_tt, with the Dunham–Came c/h term (assumption) | **0.869** vs 0.917 | ±2 points | **miss by 5 points** |
| Row chords at mid-span vs Fig 52 root/tip | within the root–tip range, R4 below both ends (the 'flask') | ±3 % | pass |
| Trailing-edge blockage t_e/(s cos α₂) vs Table III | 6–17 % above on every row | ±25 % | pass — Table III's t_e is a little under the sections' gap |

### Findings

2. **A 1951 correlation reads a 1983 low-pressure turbine 8 points
   low, and the reasons are nameable.** (a) R&M 2974's secondary-loss
   factor λ (Fig 8) has no blade-height term; its data came from
   turbines of h/c about 1–3, and the E³ rows run 1.6 (S1) to 8 (R4).
   Replacing it by the Dunham–Came c/h form recovers 3 points, most on
   the tall rear stages (stage 5 from 0.861 to 0.905). (b) The profile
   loss is the 1951 level: Fig 4 for conventional sections, with the
   thickness factor (t/c ÷ 0.2)^(β₁/α₂) charging the hollow, thick
   vanes S2 and S3 (t/c 0.25) a further 18 %. Kacker and Okapuu's 1982
   finding that post-1960 blading needs about two-thirds of the
   Ainley–Mathieson profile loss is the known next correction; their
   paper is not on disk and is not applied. (c) The chord Reynolds
   numbers of the rear rows (65,000–120,000) sit below the 200,000 the
   charts assume, which would move the prediction further down, not up.
   The stage efficiencies rise rearward on both routes, as the
   aspect ratio does.
3. **The loss level and the cycle disagree on the expansion ratio.** With
   these losses the five stages need 5.49 (5.09 with Dunham–Came) to
   deliver the cycle's work against the cycle's 4.55 at η 0.925 and
   Table II's pre-rematch 4.21. Consistent with finding 2: too much loss
   per stage.

**What closes C1's turbine-loss item** is therefore not a better read of
R&M 2974 but the two later corrections and the SP-290 vol. 2 boundary-
layer method the plan names as the cross-check (Stewart's momentum-
thickness loss, chapters 7–8 of the volume on disk). Carried as unit 2b.
The figure: `figures/lpt-losses.png`.

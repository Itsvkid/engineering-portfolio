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

"""Real, transcribed data from a published NASA report — the OpenFOAM
validation target for project 07's isolated axisymmetric nacelle cowl.

Citation
--------
Re, R. J. and Abeyounis, W. K., "A Wind Tunnel Investigation of Three NACA
1-Series Inlets at Mach Numbers Up to 0.92," NASA Technical Memorandum
110300, Langley Research Center, November 1996. Free, public, NTRS:
https://ntrs.nasa.gov/citations/19970010380

Both tables below were transcribed by rendering the report's PDF pages as
images and reading the printed digits directly (the report's tables are
scanned/rotated and pypdf's text extraction garbles them completely --
readable only as images, not as extracted text). Every value here was read
off a specific, cited table; none were fabricated, estimated, or "corrected"
from a guess. If a re-transcription ever disagrees with a number below,
trust the PDF over this file and fix this file.

Why this specific inlet and condition
--------------------------------------
The report tests three inlets; NACA 1-85-100 with internal contraction
ratio 1.009 is the "original" configuration (also tested in the report's
own references 9 and 10) and has the plainest, most-complete pressure
tabulation. M=0.79, mfr=0.71, alpha=0 deg is a representative subcritical
cruise-like condition — not the highest or lowest mass-flow ratio tested,
which sit closer to where flow separation and shock effects complicate a
first comparison.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Table II — "Design ordinates for NACA 1-85-100 inlet with internal
# contraction ratio of 1.009" (NASA TM 110300, p. 15). External ordinates
# only (this project models the external cowl; see openfoam/README.md for
# why the internal duct is deliberately not modelled here).
#
# L = 18.00 in, RMAX = 9.00 in. Coordinates in percent: X/L is percent of
# cowl length from the highlight (lip); R/RMAX is percent of the maximum
# cowl radius.
# ---------------------------------------------------------------------------

L_INCHES = 18.00
RMAX_INCHES = 9.00

# (X/L, %), (R/RMAX, %)
EXTERNAL_ORDINATES_PERCENT = (
    (0.0, 85.36), (0.20, 86.06), (0.40, 86.33), (0.60, 86.56),
    (1.50, 87.22), (2.00, 87.51), (2.50, 87.80), (3.00, 88.04),
    (4.00, 88.51), (5.00, 88.93), (7.00, 89.69), (10.00, 90.64),
    (15.00, 92.00), (20.00, 93.09), (25.00, 94.02), (30.00, 94.87),
    (35.00, 95.62), (40.00, 96.29), (45.00, 96.91), (50.00, 97.47),
    (60.00, 98.40), (70.00, 99.11), (80.00, 99.62), (90.00, 99.91),
    (100.00, 100.00),
)

# ---------------------------------------------------------------------------
# Table V(a) — "Pressure coefficients on model with NACA 1-85-100 inlet and
# contraction ratio of 1.009", M = 0.79 (NASA TM 110300, p. 18).
# mfr = 0.71, alpha = 0 deg, phi = 0 deg (top meridian), forebody only.
#
# X/L here is percent of the SAME cowl length L (18.00 in) used above, not
# re-zeroed per table — negative values sit ahead of the highlight (on the
# support sting fairing), positive values beyond 100 sit on the cylindrical
# afterbody downstream of the cowl.
# ---------------------------------------------------------------------------

MACH = 0.79
MASS_FLOW_RATIO = 0.71
ANGLE_OF_ATTACK_DEG = 0.0

# (X/L, %), Cp
FOREBODY_CP_TOP = (
    (-3.75, 0.8394), (-3.12, 0.8533), (-1.88, 0.9023), (-1.25, 0.9330),
    (-0.62, 0.9975), (0.00, 0.8942), (0.31, -1.2575), (0.62, -1.3645),
    (1.25, -1.3049), (2.50, -1.0066), (3.12, -0.9599), (4.38, -0.3047),
    (5.00, -0.3447), (7.50, -0.3005), (10.00, -0.2675), (12.50, -0.2542),
    (15.00, -0.2103), (30.00, -0.1640), (40.00, -0.1288), (50.00, -0.1253),
    (60.00, -0.1225), (70.00, -0.1106), (90.00, -0.0874), (122.00, -0.0303),
    (139.00, -0.0187),
)

# Reynolds number range the report states for this Mach range (per foot,
# not a specific altitude — this is a pressurised wind-tunnel test, not a
# free-flight condition). Used in freestream_conditions.py to back out a
# self-consistent static temperature and pressure; see that module's
# docstring for exactly how, and why that's a chosen input, not a second
# measured quantity.
REYNOLDS_PER_FOOT_RANGE = (3.2e6, 4.2e6)

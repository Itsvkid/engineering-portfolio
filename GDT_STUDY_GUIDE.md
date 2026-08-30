# GD&T Study Guide: Geometric Dimensioning & Tolerancing
## ASME Y14.5:2018 Essentials for Aerospace Engineering

**Last updated:** August 2026  
**Focus:** Aerospace/engine design applications  
**Time to competency:** 15–20 hours of study + 5 hours practice

---

## Table of Contents
1. [Why GD&T Matters](#why-gdt-matters)
2. [Fundamentals](#fundamentals)
3. [Datums](#datums)
4. [The Five Categories of Geometric Controls](#five-categories)
5. [Feature Control Frame (FCF)](#feature-control-frame)
6. [Common Aerospace Applications](#aerospace-applications)
7. [Practice Problems](#practice-problems)
8. [Quick Reference & Symbols](#quick-reference)

---

## Why GD&T Matters

### The Problem It Solves
**Without GD&T:**
```
Dimension: Ø50 mm
Problem: How perpendicular must it be to the mounting surface?
         How concentric to the shaft?
         What if the part isn't exactly 50 mm?
```

**With GD&T:**
```
Feature Control Frame:
Ø50 mm ±0.5 mm (size tolerance)
⊥ | A | 0.1 mm (perpendicularity to datum A)
⊙ | A | 0.05 mm (concentricity to datum A)
→ Now the machinist KNOWS what's acceptable
```

### Aerospace Reality
- **Rolls-Royce, Airbus, GE Aviation** all use GD&T
- **Engine nacelles** must control airflow → strict concentricity/perpendicularity
- **Compressor/turbine casings** need runout control (rotor-stator gap critical)
- **Mating surfaces** require position control (bolt holes, flange faces)
- **Manufacturing cost** scales with tolerance tightness → GD&T optimizes cost/performance

**Bottom line:** You can't freelance aerospace CAD without GD&T-annotated drawings. Period.

---

## Fundamentals

### Key Definitions

**Nominal Dimension**
- The ideal/target size (e.g., Ø50 mm)

**Tolerance**
- Acceptable range around nominal (e.g., ±0.5 mm → 49.5 to 50.5 mm)

**Datum**
- A reference point, line, or plane used to measure other features
- Written as single capital letter (A, B, C, etc.)
- Must be a physical feature (hole, surface, edge)

**Datum Reference Frame (DRF)**
- Set of 3 mutually perpendicular datums (Primary, Secondary, Tertiary)
- Establishes coordinate system for the part

**Feature**
- Any part of a component (hole, surface, edge, slot)
- Can be Datum Feature (used as reference) or Toleranced Feature (measured against datum)

**Tolerance Zone**
- 3D space where the feature must exist
- Shape depends on control type (cylinder for position, plane for perpendicularity, etc.)

---

## Datums

### What Makes a Valid Datum?

A datum feature must be:
1. **Accessible** — measurable with CMM, caliper, or gauge
2. **Stable** — not flexible or moving
3. **Repeatable** — same measurement every time
4. **Functional** — related to how the part works in assembly

### Datum Symbols

On a drawing, datums are marked with **datum triangles** (filled or hollow):

```
A — Datum Feature A (marked on the drawing edge/surface)
    ▼ (datum triangle symbol, filled = primary)

B — Datum Feature B
    ▽ (hollow triangle = secondary)

C — Datum Feature C
```

### Primary, Secondary, Tertiary Datums

The **Datum Reference Frame (DRF)** is a coordinate system:

```
         ↑ Z (Perpendicular to primary datum A)
         │
         │
    ─────┼───→ Y (Perpendicular to A and B)
        /
       / X (Along Secondary Datum B)
      /

Primary Datum A (largest, most stable surface)
  ↓
  Establishes one plane

Secondary Datum B (edge or surface perpendicular to A)
  ↓
  Establishes X-axis

Tertiary Datum C (edge perpendicular to A and B)
  ↓
  Establishes Y-axis

Result: Full 3D coordinate system for measuring other features
```

### Datum Feature Modifiers

```
| M | = Maximum Material Condition (MMC)
    At maximum material (smallest hole, largest pin)
    Commonly used for position/perpendicularity of holes

| L | = Least Material Condition (LMC)
    At minimum material (largest hole, smallest pin)
    Rare; used for wall thickness checks

| S | = Regardless of Feature Size (RFS) — DEFAULT
    Tolerance independent of actual feature size
    No modifier = RFS
```

### Example: Datum Selection for an Engine Nacelle

```
Part: Nacelle inlet lip with mounting holes

Feature 1: Outer contour surface (aerodynamic, must be smooth)
  → Primary Datum A (largest, most functional surface)

Feature 2: Mounting face (mates to engine pylon)
  → Secondary Datum B (perpendicular to A)

Feature 3: Center bore (guides engine core)
  → Tertiary Datum C (coaxial with engine centerline)

Result: All bolt holes, inlet geometry, and core bore are
        measured relative to this DRF
```

---

## Five Categories of Geometric Controls

### **Category 1: FORM CONTROLS** (Single feature, no datum required)

#### 1a. **Straightness**
**Symbol:** —

**Definition:** Feature must be a straight line (within tolerance zone)

**Use case:** Engine shaft must be straight enough to rotate smoothly

**On drawing:**
```
Ø20 —| 0.05 mm
```
Means: The centerline of the 20 mm shaft must stay within a 0.05 mm straight tolerance zone.

**Tolerance zone:** Cylinder (diameter = 0.05 mm) along the feature

---

#### 1b. **Flatness**
**Symbol:** ▭

**Definition:** Surface must lie in a single plane

**Use case:** Nacelle mounting face (mates to pylon—must be flat for load distribution)

**On drawing:**
```
Mounting surface ▭| 0.1 mm
```

**Tolerance zone:** Two parallel planes, 0.1 mm apart

---

#### 1c. **Circularity**
**Symbol:** ⊚

**Definition:** Feature must be a perfect circle (no out-of-roundness)

**Use case:** Compressor inlet lip (aerodynamic efficiency)

**On drawing:**
```
Inlet lip Ø100 ⊚| 0.05 mm
```

**Tolerance zone:** Two concentric circles, radial difference = 0.05 mm

---

#### 1d. **Cylindricity**
**Symbol:** ⌀

**Definition:** Feature must be a perfect cylinder (straightness + circularity)

**Use case:** Engine casing bore (rotor-stator gap must be uniform)

**On drawing:**
```
Core bore Ø85 ⌀| 0.1 mm
```

**Tolerance zone:** Two concentric cylinders, radial difference = 0.1 mm

---

### **Category 2: ORIENTATION CONTROLS** (Datum required)

These controls relate features to a datum (direction, angle, perpendicularity).

#### 2a. **Perpendicularity**
**Symbol:** ⊥

**Definition:** Feature must be at 90° to datum

**Use case:** Mounting hole must be perpendicular to nacelle face (load transfer)

**On drawing:**
```
⊥ | A | 0.05 mm

Where:
⊥ = perpendicularity symbol
A = datum (mounting face)
0.05 mm = tolerance zone (parallel planes 0.05 mm apart)
```

**Tolerance zone:** Two parallel planes, perpendicular to datum A

---

#### 2b. **Parallelism**
**Symbol:** ∥

**Definition:** Feature must be parallel to datum

**Use case:** Nacelle inlet top/bottom contours (aerodynamic, must maintain gap)

**On drawing:**
```
Top contour ∥ | A | 0.1 mm
```

**Tolerance zone:** Two parallel planes, 0.1 mm apart, parallel to datum A

---

#### 2c. **Angularity**
**Symbol:** ∠

**Definition:** Feature must be at specific angle to datum (not 90°)

**Use case:** Engine pylon attachment (mounted at specific angle for thrust vectoring)

**On drawing:**
```
Pylon face ∠ | A | 15° ± 0.2°
```

**Tolerance zone:** Two parallel planes at 15°, ±0.2° from datum A

---

### **Category 3: LOCATION CONTROLS** (Datum required)

These controls define WHERE features must be positioned.

#### 3a. **Position**
**Symbol:** ⊕

**Definition:** Feature location within tolerance zone (most common in aerospace)

**Use case:** Bolt holes on engine mounting flange

**On drawing:**
```
⊕ | A | B | C | 0.1 mm | M

Where:
A = primary datum (mounting face, perpendicular)
B = secondary datum (left edge, parallel)
C = tertiary datum (bottom edge, parallel)
0.1 mm = position tolerance
M = at MMC (bolt hole size-dependent)
```

**Tolerance zone:** Cylinder, Ø = 0.1 mm, centered on true position

**Why MMC matters:**
- If hole is at Maximum Material (smallest) → tightest tolerance (0.1 mm)
- If hole is at Least Material (largest) → tolerance can grow
- Formula: Actual Tolerance = Stated Tolerance + (Nominal Size - Actual Size)
- Saves cost: Over-drilled holes get more acceptance

---

#### 3b. **Concentricity**
**Symbol:** ⊙

**Definition:** Feature axis must align with datum axis (coaxial)

**Use case:** Compressor rotor bore and turbine bore (rotor must be centered for balance)

**On drawing:**
```
Rotor bore Ø50 ⊙ | A | 0.05 mm
```

**Tolerance zone:** Cylinder, Ø = 0.05 mm, coaxial with datum A

---

#### 3c. **Symmetry**
**Symbol:** ═

**Definition:** Feature must be symmetric about datum plane

**Use case:** Rare in aerospace (usually use position instead)

---

### **Category 4: PROFILE CONTROLS** (Datum optional, complex shapes)

#### 4a. **Profile of a Line**
**Symbol:** ⌢

**Definition:** 2D profile (slice through part) must match ideal shape

**Use case:** Airfoil cross-section (wing, blade trailing edge)

**On drawing:**
```
Airfoil profile ⌢ | A | 0.2 mm (all around)
```

---

#### 4b. **Profile of a Surface**
**Symbol:** ⌢ (with ALL AROUND modifier)

**Definition:** 3D surface must match ideal shape

**Use case:** Nacelle aerodynamic contour, compressor blade

**On drawing:**
```
Nacelle contour ⌢ | A | B | 0.15 mm (ALL AROUND)
```

**Tolerance zone:** ±0.15 mm from nominal CAD surface (band around ideal geometry)

---

### **Category 5: RUNOUT CONTROLS** (Datum required)

#### 5a. **Circular Runout**
**Symbol:** ↻

**Definition:** Feature out-of-roundness when rotated about datum axis

**Use case:** Compressor rotor surface (rotor-stator gap, critical for performance)

**On drawing:**
```
Compressor rotor Ø120 ↻ | A | 0.05 mm
```

**Tolerance zone:** Circular variation ≤ 0.05 mm at each point as rotor spins

---

#### 5b. **Total Runout**
**Symbol:** ↻↻

**Definition:** Combined out-of-roundness + out-of-flatness when rotated

**Use case:** Complete turbine rotor (controls wobble in all directions)

**On drawing:**
```
Turbine rotor ↻↻ | A | 0.1 mm
```

---

## Feature Control Frame (FCF)

### The Anatomy of an FCF

```
┌─────────────────────────────────────────┐
│  ⊥  │  A  │  B  │  C  │  0.05  │  M   │
└─────────────────────────────────────────┘
  ↓    ↓     ↓     ↓     ↓       ↓
  │    │     │     │     │       └─ Modifier (M = MMC, L = LMC, Ø = RFS default)
  │    │     │     │     └──────────── Tolerance value (mm)
  │    │     │     └────────────────── Tertiary datum (Z direction)
  │    │     └──────────────────────── Secondary datum (Y direction)
  │    └────────────────────────────── Primary datum (X direction)
  └────────────────────────────────────── Geometric control (perpendicularity)
```

### Reading an FCF

**Example 1: Perpendicular Mounting Hole**
```
┌──────────────────────┐
│  ⊥  │  A  │  0.05 M  │
└──────────────────────┘

Means:
- Control: Perpendicularity (⊥)
- Reference: Datum A (nacelle face)
- Tolerance: 0.05 mm
- Modifier: M (Maximum Material Condition)
- English: "The hole axis must be perpendicular to the mounting face (datum A)
            within 0.05 mm, where tolerance can increase if hole is overdrilled"
```

**Example 2: Position with 3-Datum Reference Frame**
```
┌─────────────────────────────────────────┐
│  ⊕  │  A  │  B  │  C  │  0.1  │  M   │
└─────────────────────────────────────────┘

Means:
- Control: Position (⊕)
- Primary datum: A (mounting face, establishes perpendicularity)
- Secondary datum: B (left edge, establishes X-axis)
- Tertiary datum: C (bottom edge, establishes Y-axis)
- Tolerance: 0.1 mm diameter cylinder
- Modifier: M (hole at MMC)
- English: "Bolt hole center must fall within a 0.1 mm diameter cylinder
            centered on true position, relative to the 3-datum reference frame"
```

**Example 3: Profile with All-Around**
```
┌────────────────────────────────┐
│  ⌢  │  A  │  0.2  │ ALL AROUND │
└────────────────────────────────┘

Means:
- Control: Profile of surface (⌢)
- Reference: Datum A (major axis)
- Tolerance: 0.2 mm
- Modifier: ALL AROUND (applies to entire surface)
- English: "The aerodynamic contour must stay within ±0.2 mm of the
            ideal CAD surface, all around the nacelle"
```

---

## Aerospace Applications

### Application 1: Engine Nacelle Assembly

**Part:** Inlet lip + pylon attachment

**Design requirements:**
- Smooth aerodynamic inlet (no roughness → drag reduction)
- Perpendicular mounting face (load transfer)
- Concentric bore (engine core clearance)
- Symmetric bolt holes (balanced load)

**GD&T Solution:**

```
DATUM A: Outer contour surface (aerodynamic, datum triangle filled)
         ↓ controls orientation for all other features

Inlet lip contour:
  ⌢ | A | 0.15 mm (ALL AROUND)
  → Aerodynamic profile within ±0.15 mm of CAD nominal

Mounting face:
  ⊥ | A | 0.05 mm
  → Perpendicular to outer contour for rigid connection

Engine bore (Ø80 mm):
  ⊙ | A | 0.04 mm
  → Concentric with outer contour (rotor-stator gap = 2.5 mm nominal ± 0.1)

Bolt holes (Ø8 mm, 4 holes):
  ⊕ | A | B | 0.1 mm | M
  → Positioned relative to mounting face (A) and left edge (B)
  → Tolerance expands if hole is overdrilled (cost saving)

RESULT: Single drawing, clear manufacturing spec, cost-optimized
```

---

### Application 2: Compressor Rotor

**Part:** Rotor drum with blade dovetails and bore

**Design requirements:**
- Bore must be concentric (rotor balance)
- Blade dovetail slots must be perpendicular (blade loading)
- Rotor must spin true (runout control for stage clearance)

**GD&T Solution:**

```
DATUM A: Center bore (Ø120 mm, axis of rotation)

Bore runout:
  ↻↻ | A | 0.05 mm
  → Total runout (wobble) ≤ 0.05 mm during spin
  → Maintains stage clearance (e.g., blade tip clearance = 1.5 mm ± 0.1)

Dovetail slots:
  ⊥ | A | 0.08 mm
  → Perpendicular to rotor axis (blade load transfer)

Blade attachment threads:
  ⊕ | A | 0.1 mm | M
  → Positioned on rotor axis for balanced blading
```

---

### Application 3: Mounting Flange (Pylon-to-Airframe)

**Part:** 4-bolt flange connecting engine to wing

**Design requirements:**
- Mounting face must be flat (load distribution)
- Bolt holes must be coplanar (even preload)
- Must locate engine at correct angle (thrust vector)

**GD&T Solution:**

```
DATUM A: Mounting face (▭ | 0.05 mm → flatness control)
DATUM B: Left edge (∥ | A | 0.02 mm → orientation to A)
DATUM C: Bottom edge (perpendicular to A and B)

Bolt hole pattern:
  ⊕ | A | B | C | 0.08 mm | M
  → All 4 holes within 0.08 mm of true position
  → Relative to flat datum A (ensures even preload)

Engine centerline attachment:
  ∠ | A | B | C | 15° ± 0.1°
  → Pylon neck angled at 15° for thrust vectoring
  → ±0.1° tolerance maintains aerodynamic alignment
```

---

## Practice Problems

### Problem 1: Nacelle Inlet Lip

**Scenario:** You're designing a nacelle inlet. The aerodynamic team says the inlet must be within ±0.2 mm of the CAD surface for drag control. The inlet mounts to a 50 mm diameter engine core with ±0.1 mm clearance.

**Question:** Write the GD&T callout for:
1. Inlet aerodynamic profile
2. Concentricity with engine core bore

**Solution:**

```
Step 1: Identify datums
- Primary datum A: Engine core bore (Ø50) — most stable/functional
- The inlet profile is secondary (depends on core position)

Step 2: Write FCF for inlet profile
  ⌢ | A | 0.2 mm (ALL AROUND)
  → Profile of surface within ±0.2 mm of CAD, referenced to core bore

Step 3: Write FCF for bore concentricity
  Bore Ø50 ⊙ | A | 0.1 mm
  → Bore concentric with... wait, A is the bore itself!
  
CORRECTION: The bore is datum A, so it doesn't get a concentricity callout.
The inlet contour is positioned relative to the bore via profile control above.

ANSWER:
- Inlet profile: ⌢ | A | 0.2 mm (ALL AROUND)
- Engine core bore: Ø50 ⊙ (no callout needed; it IS the datum)
```

---

### Problem 2: Bolt Hole Pattern

**Scenario:** A mounting flange has 4 bolt holes (Ø8 mm) arranged in a square (50 mm × 50 mm). The mounting face is critical for load transfer. Holes must be within ±0.1 mm of true position.

**Question:** Write the GD&T callout for bolt hole position, including:
1. What's datum A?
2. What's datum B?
3. Should you use MMC?

**Solution:**

```
Step 1: Identify datums
- Datum A (primary): Mounting face (most stable, critical for load)
- Datum B (secondary): Left edge or center bore (perpendicular to A)
- Datum C (tertiary): Bottom edge (perpendicular to A and B) — optional

Step 2: Choose MMC?
- Holes are clearance holes for screws
- If hole is drilled larger → screw still fits
- MMC modifier allows tolerance to grow with hole size
- YES, use MMC (saves cost)

Step 3: Write FCF
  ⊕ | A | B | C | 0.1 mm | M

Step 4: Verify
- Hole at nominal Ø8: tolerance zone = 0.1 mm diameter
- Hole at Ø8.2 (0.2 mm oversize): tolerance zone = 0.3 mm diameter
- Hole at Ø7.8 (0.2 mm undersize): tolerance zone = -0.1 mm (fails)
  → This is intentional; tighter control when material is minimal

ANSWER:
  ⊕ | A | B | C | 0.1 mm | M

  Where:
  A = mounting face (perpendicular primary)
  B = left edge (parallel secondary)
  C = bottom edge (parallel tertiary)
```

---

### Problem 3: Combustor Case

**Scenario:** Combustor casing (Ø200 mm bore) must spin concentrically with engine centerline for uniform fuel distribution. Rotor-stator gap = 3 mm nominal, ±0.15 mm tolerance. Concentricity tolerance = ?

**Question:** Calculate the maximum concentricity tolerance (hint: concentricity tightness ties to gap control).

**Solution:**

```
Step 1: Understand the constraint
- Rotor centerline is datum (center of rotation)
- Combustor bore must be concentric (fuel nozzles positioned around it)
- If bore is off-center → fuel distribution uneven → combustion inefficiency

Step 2: Available tolerance
- Gap = 3 mm ± 0.15 mm → min gap = 2.85 mm, max gap = 3.15 mm
- If rotor is perfect AND bore is off-center by E:
  → new gap = 3 ± E ± rotor runout
- If rotor runout = ±0.05 mm, then E can be ≤ 0.1 mm
  (so total gap error = 0.05 + 0.1 = 0.15 mm)

Step 3: Write FCF
  Combustor bore Ø200 ⊙ | Rotor_Centerline | 0.1 mm

ANSWER:
  ⊙ | Rotor_Centerline | 0.1 mm

  (Concentricity acts as a tighter control than circularity;
   here it ensures bore stays within 0.1 mm of rotor axis,
   protecting the 3 mm gap and fuel distribution uniformity)
```

---

## Quick Reference & Symbols

### GD&T Symbol Chart

| Control | Symbol | Type | Datum Required? | Use Case |
|---------|--------|------|-----------------|----------|
| **Straightness** | — | Form | No | Shaft straightness |
| **Flatness** | ▭ | Form | No | Mounting face |
| **Circularity** | ⊚ | Form | No | Inlet lip roundness |
| **Cylindricity** | ⌀ | Form | No | Casing bore uniformity |
| **Perpendicularity** | ⊥ | Orientation | Yes | Mounting hole angle |
| **Parallelism** | ∥ | Orientation | Yes | Inlet top/bottom gap |
| **Angularity** | ∠ | Orientation | Yes | Pylon attachment angle |
| **Position** | ⊕ | Location | Yes | Bolt hole pattern |
| **Concentricity** | ⊙ | Location | Yes | Rotor bore centering |
| **Symmetry** | ═ | Location | Yes | (Rare in aerospace) |
| **Profile of Line** | ⌢ | Profile | Optional | Airfoil section |
| **Profile of Surface** | ⌢ | Profile | Optional | Nacelle contour |
| **Circular Runout** | ↻ | Runout | Yes | Rotor wobble at one plane |
| **Total Runout** | ↻↻ | Runout | Yes | Full rotor wobble check |

---

### Tolerance Value Guide (Aerospace)

| Feature | Typical Tolerance | Reason |
|---------|------------------|--------|
| Mounting face flatness | 0.02–0.1 mm | Ensures even load transfer |
| Bolt hole position | 0.05–0.2 mm | Depends on bolt grade/preload |
| Bore concentricity | 0.02–0.1 mm | Rotor-stator gap critical |
| Blade dovetail perpendicularity | 0.05–0.15 mm | Blade load transfer |
| Nacelle aerodynamic profile | 0.1–0.3 mm | Drag/efficiency trade-off |
| Rotor total runout | 0.02–0.1 mm | Balance/vibration control |
| Compressor inlet lip circularity | 0.05–0.1 mm | Inlet distortion limits |

---

### Datum Feature Modifier Quick Guide

```
No Modifier (or / S) → Regardless of Feature Size (RFS)
                       Tolerance is FIXED, not tied to actual size
                       Strictest control; highest cost
                       Use when dimension is critical regardless of size

| M | → Maximum Material Condition
       Use when dimension is tied to assembly (e.g., bolt holes)
       Allows tolerance relaxation if hole is overdrilled
       Saves manufacturing cost; most common in aerospace

| L | → Least Material Condition
       Use when wall thickness matters (thin-walled shells)
       Rare in aerospace (usually use form controls instead)
```

---

### Drawing Callout Checklist

Before finalizing GD&T on a drawing, verify:

- [ ] Every datum reference feature is marked with triangle symbol
- [ ] Primary datum is the most stable/functional feature
- [ ] Secondary datum is perpendicular to primary (if 3-axis control needed)
- [ ] Tertiary datum is perpendicular to both (rarely needed)
- [ ] All tolerance values are realistic for manufacturing (check with shop)
- [ ] Modifiers (M, L, RFS) are intentional and justified
- [ ] Profile controls have "ALL AROUND" if applicable
- [ ] Concentricity is used for rotation; position is used for placement
- [ ] Runout is used only for rotating features
- [ ] Form controls (flatness, circularity) have no datums

---

### Common Mistakes to Avoid

❌ **Using concentricity instead of position for bolt holes**
   → Position is for LOCATION; concentricity is for ROTATION
   
❌ **Forgetting datum triangles**
   → Drawing readers won't know what datum you're referencing
   
❌ **Mixing RFS and MMC without intent**
   → RFS (strict) vs. MMC (cost-saving); know which you need
   
❌ **Over-tolerancing** (too tight)
   → Makes parts expensive; manufactures for tight specs
   
❌ **Under-tolerancing** (too loose)
   → Parts may not function; gaps exceed acceptable limits
   
❌ **Using 4+ datums**
   → 3-datum reference frame is almost always sufficient
   → 4+ datums = you're overspecifying

---

## Study Strategy (15–20 Hours)

### Week 1: Foundations (5 hours)
- [ ] Day 1: Read Fundamentals + Datums sections (90 min)
- [ ] Day 2: Watch YouTube "GD&T Fundamentals" (eSub Mechanix, 90 min)
- [ ] Day 3: Read Five Categories section (90 min)
- [ ] Day 4: Sketch out datum reference frame examples (60 min)

### Week 2: Application (5 hours)
- [ ] Day 1: Read Aerospace Applications (90 min)
- [ ] Day 2: Watch "GD&T in Engine Design" or similar (YouTube, 90 min)
- [ ] Day 3: Work through Practice Problems 1–3 (120 min)
- [ ] Day 4: Review quick reference + common mistakes (60 min)

### Week 3: Practice (5 hours)
- [ ] Grab your nacelle CAD from portfolio
- [ ] Create a 2D engineering drawing (SolidWorks or Fusion)
- [ ] Add datums: outer contour (A), mount face (B), bore (C)
- [ ] Write GD&T callouts: profile, perpendicularity, concentricity
- [ ] Screenshot → send to 1 aerospace mentor for review

### Week 4: Verification (5 hours)
- [ ] Practice Problem 4 (self-created from your CAD)
- [ ] Review ASME Y14.5 standard (online PDF) sections 1–8
- [ ] Quiz yourself: "What's the difference between position and location?"
- [ ] Create a drawing for a simple combustor flange using all 5 categories

---

## ASME Y14.5:2018 Reference

**Full title:** "Dimensioning and Tolerancing"

**Key sections for aerospace:**
- Section 1: General principles
- Section 2: Symbols and abbreviations
- Section 3: Datum reference frames
- Section 4: Form controls
- Section 5: Orientation controls
- Section 6: Location controls
- Section 7: Profile controls
- Section 8: Runout controls

**Where to find:** 
- Download PDF from ASME (requires ~$60 membership or purchase)
- University libraries often have physical copies
- YouTube has summaries (eSub Mechanix, Technical Drawings, others)

---

## Next Steps After This Guide

1. **Apply to your portfolio:**
   - Redesign nacelle drawing with full GD&T
   - Add to GitHub/portfolio site
   - Link on Upwork profile

2. **Practice with real parts:**
   - Find aerospace drawings on NASA/ESA public databases
   - Interpret their GD&T → understand design reasoning
   - Create your own callouts for comparison

3. **Get feedback:**
   - Share your GD&T drawings with aerospace engineers
   - LinkedIn aerospace community has reviewers
   - Aerospace companies sometimes review student work (good for job search)

4. **Combine with CAD:**
   - Learn SolidWorks drawing tools (next skill to tackle)
   - SolidWorks has built-in GD&T symbol library
   - Create parametric models + annotated drawings = client-ready deliverables

---

**Good luck with your study! GD&T takes practice, but it's the language of aerospace manufacturing. Master it, and you're 2–3x more valuable to employers and clients.**

*Last updated: August 21, 2026*
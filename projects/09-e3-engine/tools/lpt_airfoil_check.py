#!/usr/bin/env python3
"""Check LPT appendix airfoil sections against themselves and the OCR
layer. Usage: lpt_airfoil_check.py CSV [CSV ...] [--ocr DIR]

CSV columns: surface,z_in,r_in,rtheta_in. Checks per surface: 48 points,
z monotonic after the nose wrap, r monotonic, each coordinate smooth in
index (quadratic extrapolation from the three previous points), the
leading edge shared, the trailing edge closing; and the share of values
found verbatim in the OCR text of the page (OCR page number from the
CSV's header comment '# pdf_page: N' if present)."""
import csv, re, sys, pathlib

args = [a for a in sys.argv[1:] if not a.startswith("--")]
ocr_dir = None
if "--ocr" in sys.argv:
    ocr_dir = pathlib.Path(sys.argv[sys.argv.index("--ocr") + 1])
    args = [a for a in args if a != str(ocr_dir)]

TOL = {"z": 0.012, "r": 0.010, "t": 0.015}
allok = True
for path in map(pathlib.Path, args):
    text = path.read_text()
    page = re.search(r"pdf_page:\s*(\d+)", text)
    rows = list(csv.DictReader(l for l in text.splitlines() if not l.startswith("#")))
    surf = {s: [(float(r["z_in"]), float(r["r_in"]), float(r["rtheta_in"])) for r in rows if r["surface"] == s] for s in ("suction", "pressure")}
    ok = True
    msgs = []
    for s, pts in surf.items():
        expected = 48
        m = re.search(rf"#\s*points:\s*{s}\s*=\s*(\d+)", text)
        if m:
            expected = int(m.group(1))
        if len(pts) != expected:
            ok = False; msgs.append(f"{s}: {len(pts)} points, expected {expected}")
        # drop printed duplicate rows for the smoothness test
        u = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
        z = [p[0] for p in u]; r = [p[1] for p in u]; t = [p[2] for p in u]
        imin = z.index(min(z))
        if imin > 5:
            ok = False; msgs.append(f"{s}: z minimum at index {imin}, nose wrap too long")
        if not all(b >= a for a, b in zip(z[imin:], z[imin + 1:])):
            ok = False; msgs.append(f"{s}: z not monotonic after the nose")
        # r must follow one trend after the nose, ignoring reversals under a thousandth (a wall that crowns by a few mils)
        steps = [b - a for a, b in zip(r[imin:], r[imin + 1:])]
        up = sum(1 for d in steps if d > 0.001); dn = sum(1 for d in steps if d < -0.001)
        if up and dn:
            ok = False; msgs.append(f"{s}: r reverses after the nose ({up} up, {dn} down steps over 0.001 in)")
        def quad(x0, y0, x1, y1, x2, y2, x):
            return (y0 * (x - x1) * (x - x2) / ((x0 - x1) * (x0 - x2)) + y1 * (x - x0) * (x - x2) / ((x1 - x0) * (x1 - x2)) + y2 * (x - x0) * (x - x1) / ((x2 - x0) * (x2 - x1)))
        for name, seq, tol in (("r", r, TOL["r"]), ("t", t, TOL["t"])):
            for i in range(max(3, imin + 3), len(seq)):
                if not (z[i - 3] < z[i - 2] < z[i - 1] < z[i]) or z[i - 1] - z[i - 3] < 0.03:
                    continue  # the nose arc: points too close in z for a quadratic to mean anything
                pred = quad(z[i - 3], seq[i - 3], z[i - 2], seq[i - 2], z[i - 1], seq[i - 1], z[i])
                if abs(seq[i] - pred) > tol:
                    ok = False; msgs.append(f"{s}: {name} at row {i + 1} (z={z[i]:.6f}) = {seq[i]:.6f}, quadratic in z gives {pred:.6f}")
    su, pr = surf["suction"], surf["pressure"]
    if su and pr:
        if su[0] != pr[0]:
            ok = False; msgs.append(f"leading edge differs: {su[0]} vs {pr[0]}")
        gap = ((su[-1][0] - pr[-1][0]) ** 2 + (su[-1][2] - pr[-1][2]) ** 2) ** 0.5
        if gap > 0.06:
            ok = False; msgs.append(f"trailing edge gap {gap:.4f} in")
    hit = ""
    if ocr_dir and page:
        ocr = (ocr_dir / f"p{page.group(1)}.txt").read_text(errors="ignore")
        nums = set(re.findall(r"-?\d+\.\d{6}", ocr))
        vals = [f"{v:.6f}" for pts in surf.values() for p in pts for v in p]
        n = sum(1 for v in vals if v in nums or v.lstrip("-") in nums)
        hit = f"  ocr {n}/{len(vals)}"
    print(f"{path.name}: {'OK ' if ok else 'CHECK'} su {len(su)} pr {len(pr)}{hit}")
    for m in msgs:
        print("   ", m)
    allok &= ok
sys.exit(0 if allok else 1)

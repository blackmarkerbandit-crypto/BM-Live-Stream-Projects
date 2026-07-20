"""
Rear connector panel generator - ATEM SDI Pro ISO flypack.

Stream Deck and laptop live outside the case, so nothing on this panel serves
them. Audio is patched directly at the back of the switcher, so the two 3.5 mm
jacks are gone as well - but their holes are not.

Two variants:

  compact   264 x 92 mm - eight live connectors plus two spare D positions,
                          blanked with Neutrik DBA-BL (~$1 each). The plate is
                          a one-shot; a hole costs nothing to cut today and $50
                          to add later. This is the one to build.

  slim      220 x 92 mm - eight connectors, no spares. Smaller and $3 cheaper.
                          Only choose this if you are certain the panel will
                          never grow.

Connectors are rotated 90 deg so the plate clears a small case's base wall;
see CASE_WALLS. Emits <variant>.dxf (upload this) and <variant>.svg from one
set of numbers, so drawing and cut file cannot disagree.

Units: millimetres. Origin: lower-left of the plate. View: from outside.

    python panel.py
"""

import math

# ---------------------------------------------------------------------------
# Neutrik D-series cutout.
#
# VERIFY BEFORE CUTTING. Neutrik ships an official DXF on every product page
# (Downloads -> DXF). Open NBB75DFI's, measure, and correct these if they
# differ. Everything downstream is driven from here.
# ---------------------------------------------------------------------------
D_BORE = 24.0          # main hole diameter
D_SCREW = 3.2          # M3 clearance
D_SCREW_PITCH = 24.0   # centre-to-centre, screws straddling the bore

# Flange envelope when upright. Used for collision checking only.
D_FLANGE_W = 26.0
D_FLANGE_H = 31.0

MOUNT_DIA = 4.5        # M4 clearance, plate -> case
THICKNESS = 3.0        # aluminium
CORNER_R = 4.0

# Interior base-wall height per case, mm. The plate has to land on this, so it
# is the number that actually picks the case - not the gear footprint.
CASE_WALLS = {
    "Pelican 1450":     111.0,   # 4.37 in
    "Pelican 1500":     109.0,   # 4.31 in
    "Pelican 1520":     125.0,   # 4.93 in
    "Pelican 1535 Air": 132.0,   # 5.21 in
}

# A port is (label, row). A label of None is a spare position: the hole gets
# cut and a DBA-BL blank goes in, but nothing is engraved next to it - whatever
# eventually lands there can be labelled then.
SPARE = None


class Variant:
    def __init__(self, name, w, h, cols, row_top, row_bot, mounts, opening, ports,
                 rotated=True):
        self.name = name
        self.W, self.H = w, h
        self.cols = cols
        self.row_top, self.row_bot = row_top, row_bot
        self.mounts = mounts
        self.opening = opening
        self.ports = ports
        self.rotated = rotated
        # A rotated connector swaps its flange envelope and puts the two screws
        # on the horizontal axis. That is what buys back the height.
        self.fw = D_FLANGE_H if rotated else D_FLANGE_W
        self.fh = D_FLANGE_W if rotated else D_FLANGE_H

    @property
    def connectors(self):
        out = []
        for i, (label, row) in enumerate(self.ports):
            x = self.cols[i % len(self.cols)]
            y = self.row_top if row == "top" else self.row_bot
            out.append((x, y, label))
        return out

    @property
    def spares(self):
        return sum(1 for label, _ in self.ports if label is SPARE)


# Mains sits at the far corner, away from everything it could couple into.
COMPACT = Variant(
    "atem-panel-compact",
    264.0, 92.0,
    cols=[44.0, 88.0, 132.0, 176.0, 220.0],    # 44 mm pitch
    row_top=64.0, row_bot=28.0,                # 36 mm pitch
    mounts=[(12.0, 15.0), (12.0, 46.0), (12.0, 77.0),
            (252.0, 15.0), (252.0, 46.0), (252.0, 77.0)],
    opening=(24.0, 10.0, 240.0, 82.0),
    ports=[
        ("SDI IN 1", "top"), ("SDI IN 2", "top"), ("SDI IN 3", "top"),
        ("SDI IN 4", "top"), ("PGM OUT", "top"),
        (SPARE, "bot"), (SPARE, "bot"), ("NETWORK", "bot"),
        ("USB-C", "bot"), ("AC IN", "bot"),
    ],
)

SLIM = Variant(
    "atem-panel-slim",
    220.0, 92.0,
    cols=[44.0, 88.0, 132.0, 176.0],
    row_top=64.0, row_bot=28.0,
    mounts=[(12.0, 15.0), (12.0, 46.0), (12.0, 77.0),
            (208.0, 15.0), (208.0, 46.0), (208.0, 77.0)],
    opening=(24.0, 10.0, 196.0, 82.0),
    ports=[
        ("SDI IN 1", "top"), ("SDI IN 2", "top"),
        ("SDI IN 3", "top"), ("SDI IN 4", "top"),
        ("PGM OUT", "bot"), ("NETWORK", "bot"),
        ("USB-C", "bot"), ("AC IN", "bot"),
    ],
)


def check(v):
    """Refuse to emit a plate with a collision in it."""
    problems = []
    hw, hh = v.fw / 2, v.fh / 2
    conns = v.connectors
    ox1, oy1, ox2, oy2 = v.opening

    named = [(x, y, lbl or f"spare @ x{x:.0f}") for x, y, lbl in conns]

    for i, (x1, y1, n1) in enumerate(named):
        for x2, y2, n2 in named[i + 1:]:
            if abs(x1 - x2) < v.fw and abs(y1 - y2) < v.fh:
                problems.append(f"flanges overlap: {n1} / {n2}")
        for mx, my in v.mounts:
            if abs(x1 - mx) < hw + MOUNT_DIA and abs(y1 - my) < hh + MOUNT_DIA:
                problems.append(f"mount hole fouls {n1}")
        if not (hw < x1 < v.W - hw and hh < y1 < v.H - hh):
            problems.append(f"{n1} runs off the plate")
        if not (ox1 < x1 - hw and x1 + hw < ox2 and oy1 < y1 - hh and y1 + hh < oy2):
            problems.append(f"case opening does not clear {n1}")

    for mx, my in v.mounts:
        if ox1 - MOUNT_DIA < mx < ox2 + MOUNT_DIA and oy1 - MOUNT_DIA < my < oy2 + MOUNT_DIA:
            problems.append(f"mount hole ({mx}, {my}) lands over the case opening")

    return list(dict.fromkeys(problems))


def fits(v, wall):
    """A plate needs a margin either side to land on and seal against."""
    return v.H + 12.0 <= wall


# ---------------------------------------------------------------------------
# DXF (R12 ASCII - universally accepted by cutting services)
# ---------------------------------------------------------------------------
BULGE_90 = math.tan(math.radians(90) / 4)


def dxf(v):
    out = []
    w = lambda c, val: out.extend((str(c), str(val)))

    w(0, "SECTION"); w(2, "HEADER")
    w(9, "$INSUNITS"); w(70, 4)                 # millimetres
    w(0, "ENDSEC")

    w(0, "SECTION"); w(2, "TABLES")
    w(0, "TABLE"); w(2, "LAYER"); w(70, 2)
    for name, color in (("CUT", 7), ("ENGRAVE", 3)):
        w(0, "LAYER"); w(2, name); w(70, 0); w(62, color); w(6, "CONTINUOUS")
    w(0, "ENDTAB"); w(0, "ENDSEC")

    w(0, "SECTION"); w(2, "ENTITIES")

    def circle(cx, cy, dia):
        w(0, "CIRCLE"); w(8, "CUT")
        w(10, f"{cx:.4f}"); w(20, f"{cy:.4f}"); w(30, "0.0")
        w(40, f"{dia / 2:.4f}")

    def text(cx, cy, s, height=3.0):
        w(0, "TEXT"); w(8, "ENGRAVE")
        w(10, f"{cx:.4f}"); w(20, f"{cy:.4f}"); w(30, "0.0")
        w(40, f"{height:.4f}"); w(1, s)
        w(72, 1); w(73, 2)
        w(11, f"{cx:.4f}"); w(21, f"{cy:.4f}"); w(31, "0.0")

    r = CORNER_R
    verts = [
        (r, 0.0, 0.0), (v.W - r, 0.0, BULGE_90),
        (v.W, r, 0.0), (v.W, v.H - r, BULGE_90),
        (v.W - r, v.H, 0.0), (r, v.H, BULGE_90),
        (0.0, v.H - r, 0.0), (0.0, r, BULGE_90),
    ]
    w(0, "POLYLINE"); w(8, "CUT"); w(66, 1); w(70, 1)
    for x, y, b in verts:
        w(0, "VERTEX"); w(8, "CUT")
        w(10, f"{x:.4f}"); w(20, f"{y:.4f}"); w(30, "0.0")
        if b:
            w(42, f"{b:.6f}")
    w(0, "SEQEND"); w(8, "CUT")

    off = D_SCREW_PITCH / 2
    for cx, cy, label in v.connectors:
        circle(cx, cy, D_BORE)
        if v.rotated:
            circle(cx - off, cy, D_SCREW)
            circle(cx + off, cy, D_SCREW)
        else:
            circle(cx, cy - off, D_SCREW)
            circle(cx, cy + off, D_SCREW)
        # Spares stay unengraved - label them once you know what they became.
        if label:
            text(cx, cy - v.fh / 2 - 4.0, label, 3.0)

    for mx, my in v.mounts:
        circle(mx, my, MOUNT_DIA)

    w(0, "ENDSEC"); w(0, "EOF")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# SVG preview - dimensioned, prints 1:1
# ---------------------------------------------------------------------------
def svg(v):
    M = 46.0
    p = []
    y = lambda val: v.H - val          # DXF origin is bottom-left, SVG top-left

    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{-M} {-M} {v.W + 2 * M} {v.H + 2 * M}" width="100%" '
        f'style="max-width:900px;height:auto" '
        f'font-family="ui-monospace,Consolas,monospace">'
    )
    p.append(
        '<defs><marker id="a" markerWidth="9" markerHeight="9" refX="8" refY="3" '
        'orient="auto"><path d="M0,0 L9,3 L0,6 z" fill="currentColor"/></marker></defs>'
    )
    p.append('<g color="var(--dim,#6B7378)">')

    ox1, oy1, ox2, oy2 = v.opening
    p.append(
        f'<rect x="{ox1}" y="{y(oy2)}" width="{ox2 - ox1}" height="{oy2 - oy1}" '
        f'fill="none" stroke="var(--ref,#C8322B)" stroke-width="0.5" '
        f'stroke-dasharray="4 3" opacity="0.85"/>'
    )
    p.append(
        f'<rect x="0" y="0" width="{v.W}" height="{v.H}" rx="{CORNER_R}" '
        f'fill="var(--plate,#E4E7E8)" stroke="var(--ink,#14171A)" stroke-width="0.8"/>'
    )

    off = D_SCREW_PITCH / 2
    for cx, cy, label in v.connectors:
        sy = y(cy)
        p.append(
            f'<rect x="{cx - v.fw / 2}" y="{sy - v.fh / 2}" width="{v.fw}" height="{v.fh}" '
            f'rx="2" fill="none" stroke="var(--ink,#14171A)" stroke-width="0.3" '
            f'stroke-dasharray="2 2" opacity="0.35"/>'
        )
        p.append(
            f'<circle cx="{cx}" cy="{sy}" r="{D_BORE / 2}" fill="var(--bore,#FFF)" '
            f'stroke="var(--ink,#14171A)" stroke-width="0.7"/>'
        )
        for d in (-off, off):
            sx, syy = (cx + d, sy) if v.rotated else (cx, sy + d)
            p.append(
                f'<circle cx="{sx}" cy="{syy}" r="{D_SCREW / 2}" fill="var(--bore,#FFF)" '
                f'stroke="var(--ink,#14171A)" stroke-width="0.5"/>'
            )
        if label:
            p.append(
                f'<text x="{cx}" y="{sy + v.fh / 2 + 6}" font-size="4.2" '
                f'text-anchor="middle" fill="var(--ink,#14171A)" '
                f'letter-spacing="0.3">{label}</text>'
            )
        else:
            # Hatch the spares so the drawing reads at a glance.
            p.append(
                f'<line x1="{cx - 7}" y1="{sy - 7}" x2="{cx + 7}" y2="{sy + 7}" '
                f'stroke="var(--dim,#6B7378)" stroke-width="0.6" opacity="0.6"/>'
            )
            p.append(
                f'<text x="{cx}" y="{sy + v.fh / 2 + 6}" font-size="4.2" '
                f'text-anchor="middle" fill="var(--dim,#6B7378)" '
                f'letter-spacing="0.3">BLANK</text>'
            )

    for mx, my in v.mounts:
        p.append(
            f'<circle cx="{mx}" cy="{y(my)}" r="{MOUNT_DIA / 2}" fill="var(--bore,#FFF)" '
            f'stroke="var(--ink,#14171A)" stroke-width="0.6"/>'
        )

    def hdim(x1, x2, ypos, label):
        p.append(
            f'<line x1="{x1}" y1="{ypos}" x2="{x2}" y2="{ypos}" stroke="currentColor" '
            f'stroke-width="0.4" marker-start="url(#a)" marker-end="url(#a)"/>'
        )
        p.append(
            f'<text x="{(x1 + x2) / 2}" y="{ypos - 2.5}" font-size="4.6" '
            f'text-anchor="middle" fill="currentColor">{label}</text>'
        )

    def vdim(y1, y2, xpos, label):
        p.append(
            f'<line x1="{xpos}" y1="{y1}" x2="{xpos}" y2="{y2}" stroke="currentColor" '
            f'stroke-width="0.4" marker-start="url(#a)" marker-end="url(#a)"/>'
        )
        mid = (y1 + y2) / 2
        p.append(
            f'<text x="{xpos - 3}" y="{mid}" font-size="4.6" text-anchor="middle" '
            f'fill="currentColor" transform="rotate(-90 {xpos - 3} {mid})">{label}</text>'
        )

    hdim(0, v.W, -12, f"{v.W:.0f}")
    hdim(v.cols[0], v.cols[1], y(v.row_top) - 20, f"{v.cols[1] - v.cols[0]:.0f} pitch")
    hdim(ox1, ox2, v.H + 30, f"case opening {ox2 - ox1:.0f}")
    vdim(0, v.H, -12, f"{v.H:.0f}")
    vdim(y(v.row_top), y(v.row_bot), v.W + 14, f"{v.row_top - v.row_bot:.0f}")
    vdim(y(oy2), y(oy1), v.W + 34, f"opening {oy2 - oy1:.0f}")

    p.append(
        f'<text x="0" y="{v.H + 42}" font-size="4.4" fill="currentColor">'
        f'{THICKNESS:.0f} mm aluminium &#183; bore &#8709;{D_BORE:.0f} &#183; '
        f'screws &#8709;{D_SCREW:.1f} @ {D_SCREW_PITCH:.0f} '
        f'({"horizontal" if v.rotated else "vertical"}) &#183; '
        f'mount &#8709;{MOUNT_DIA:.1f}</text>'
    )
    p.append('</g></svg>')
    return "".join(p)


if __name__ == "__main__":
    for v in (COMPACT, SLIM):
        problems = check(v)
        print(f"{v.name}  {v.W:.0f} x {v.H:.0f} x {THICKNESS:.0f} mm")
        if problems:
            print("  LAYOUT PROBLEMS:")
            for pr in problems:
                print("   -", pr)
            raise SystemExit(1)

        with open(f"{v.name}.dxf", "w", encoding="ascii") as f:
            f.write(dxf(v))
        with open(f"{v.name}.svg", "w", encoding="utf-8") as f:
            f.write(svg(v))

        ox1, oy1, ox2, oy2 = v.opening
        live = len(v.connectors) - v.spares
        print(f"  cutouts       {len(v.connectors)} D positions "
              f"({live} live + {v.spares} blanked)")
        print(f"  case opening  {ox2 - ox1:.0f} x {oy2 - oy1:.0f} mm")
        for case, wall in CASE_WALLS.items():
            ok = "fits" if fits(v, wall) else "TOO TALL"
            print(f"  {case:<18} base wall {wall:>5.0f} mm   {ok}")
        print()

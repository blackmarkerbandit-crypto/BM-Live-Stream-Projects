"""
Lid retainer frame - Feelworld LUT11S in a Pelican 1450 lid.

The LUT11S has no VESA pattern: three 1/4"-20 threads on its edges and nothing
on the back. So it can't be bolted flat. It has to be captured.

This part captures it at the four CORNERS ONLY. That matters: the manufacturer
publishes the 242 x 156 x 23 mm envelope and nothing else - not where the
active area sits, not where the buttons are. A frame that laps the monitor's
face anywhere else would be guessing, and could easily land on a button. Corners
are dead bezel on every monitor ever made, so a corner-capture part depends on
nothing but the envelope, which is known exactly.

The monitor sits on a foam pad on the lid floor; the frame stands off on
spacers and presses its four corners down onto it. Foam takes up the tolerance
and doubles as shock isolation.

    lid floor  ____________________________________
    foam       [######## 5 mm, compressed to 2 ####]
    monitor    [======== 23 mm ===================]
    frame      [--3 mm--]                 <- on 25 mm standoffs
                                             = 3 mm preload into the foam

Emits lut11s-bezel.dxf (upload this) and lut11s-bezel.svg (dimensioned).
Units: millimetres. Origin: lower-left of the frame. View: from the front.

    python bezel.py
"""

import math

# ---------------------------------------------------------------------------
# Monitor. The only figures the manufacturer actually publishes - which is
# precisely why this part only trusts the envelope.
# ---------------------------------------------------------------------------
MON_W, MON_H, MON_D = 242.0, 156.0, 23.0
MON_CLEAR = 1.0        # per side, so it drops in without binding

# ---------------------------------------------------------------------------
# The stack. Standoff = MON_D + FOAM - PRELOAD.
# ---------------------------------------------------------------------------
FOAM = 5.0             # closed-cell, under the monitor
PRELOAD = 3.0          # how far the frame squeezes it
STANDOFF = MON_D + FOAM - PRELOAD      # -> 25 mm
THICKNESS = 3.0        # aluminium, same sheet as the connector plate

LID_DEPTH = 44.0       # Pelican 1450 lid cavity, 1.75 in
LID_W, LID_H = 372.0, 260.0            # lid interior face

# ---------------------------------------------------------------------------
# Frame
# ---------------------------------------------------------------------------
BORDER = 30.0                          # material outside the window
FRAME_W = MON_W + 2 * MON_CLEAR + 2 * BORDER    # -> 304
FRAME_H = MON_H + 2 * MON_CLEAR + 2 * BORDER    # -> 218
CORNER_R = 4.0

TAB = 18.0             # corner tabs, square, lapping onto the monitor face
MOUNT_DIA = 4.5        # M4 clearance, frame -> standoff -> rivnut in the lid

# Window: the monitor envelope plus clearance, with the four corners filled in.
WIN_X0 = BORDER
WIN_Y0 = BORDER
WIN_X1 = FRAME_W - BORDER
WIN_Y1 = FRAME_H - BORDER

MOUNTS = [
    (15.0, 15.0), (FRAME_W / 2, 15.0), (FRAME_W - 15.0, 15.0),
    (15.0, FRAME_H / 2), (FRAME_W - 15.0, FRAME_H / 2),
    (15.0, FRAME_H - 15.0), (FRAME_W / 2, FRAME_H - 15.0),
    (FRAME_W - 15.0, FRAME_H - 15.0),
]


def window_polygon():
    """Rectangle with the four corners filled by square tabs. CCW, 12 vertices."""
    x0, y0, x1, y1, t = WIN_X0, WIN_Y0, WIN_X1, WIN_Y1, TAB
    return [
        (x0 + t, y0), (x1 - t, y0),
        (x1 - t, y0 + t), (x1, y0 + t),
        (x1, y1 - t), (x1 - t, y1 - t),
        (x1 - t, y1), (x0 + t, y1),
        (x0 + t, y1 - t), (x0, y1 - t),
        (x0, y0 + t), (x0 + t, y0 + t),
    ]


def check():
    problems = []

    if STANDOFF <= 0:
        problems.append("standoff height is not positive")
    if THICKNESS + STANDOFF > LID_DEPTH:
        problems.append(
            f"stack {THICKNESS + STANDOFF:.0f} mm exceeds lid depth {LID_DEPTH:.0f} mm")
    if FRAME_W > LID_W or FRAME_H > LID_H:
        problems.append(f"frame {FRAME_W:.0f} x {FRAME_H:.0f} does not fit the lid face")
    if TAB * 3 > min(WIN_X1 - WIN_X0, WIN_Y1 - WIN_Y0):
        problems.append("corner tabs are eating the window")
    if PRELOAD >= FOAM:
        problems.append("preload would bottom out the foam")

    # Mount holes must sit in the border, clear of the window.
    for mx, my in MOUNTS:
        r = MOUNT_DIA / 2
        inside_x = WIN_X0 - r < mx < WIN_X1 + r
        inside_y = WIN_Y0 - r < my < WIN_Y1 + r
        if inside_x and inside_y:
            problems.append(f"mount hole ({mx:.0f}, {my:.0f}) breaks into the window")
        if not (r < mx < FRAME_W - r and r < my < FRAME_H - r):
            problems.append(f"mount hole ({mx:.0f}, {my:.0f}) runs off the frame")

    return list(dict.fromkeys(problems))


# ---------------------------------------------------------------------------
# DXF (R12 ASCII)
# ---------------------------------------------------------------------------
BULGE_90 = math.tan(math.radians(90) / 4)


def dxf():
    out = []
    w = lambda c, v: out.extend((str(c), str(v)))

    w(0, "SECTION"); w(2, "HEADER")
    w(9, "$INSUNITS"); w(70, 4)
    w(0, "ENDSEC")

    w(0, "SECTION"); w(2, "TABLES")
    w(0, "TABLE"); w(2, "LAYER"); w(70, 1)
    w(0, "LAYER"); w(2, "CUT"); w(70, 0); w(62, 7); w(6, "CONTINUOUS")
    w(0, "ENDTAB"); w(0, "ENDSEC")

    w(0, "SECTION"); w(2, "ENTITIES")

    def polyline(verts):
        w(0, "POLYLINE"); w(8, "CUT"); w(66, 1); w(70, 1)
        for v in verts:
            x, y = v[0], v[1]
            b = v[2] if len(v) > 2 else 0.0
            w(0, "VERTEX"); w(8, "CUT")
            w(10, f"{x:.4f}"); w(20, f"{y:.4f}"); w(30, "0.0")
            if b:
                w(42, f"{b:.6f}")
        w(0, "SEQEND"); w(8, "CUT")

    r = CORNER_R
    polyline([
        (r, 0.0, 0.0), (FRAME_W - r, 0.0, BULGE_90),
        (FRAME_W, r, 0.0), (FRAME_W, FRAME_H - r, BULGE_90),
        (FRAME_W - r, FRAME_H, 0.0), (r, FRAME_H, BULGE_90),
        (0.0, FRAME_H - r, 0.0), (0.0, r, BULGE_90),
    ])
    polyline(window_polygon())

    for mx, my in MOUNTS:
        w(0, "CIRCLE"); w(8, "CUT")
        w(10, f"{mx:.4f}"); w(20, f"{my:.4f}"); w(30, "0.0")
        w(40, f"{MOUNT_DIA / 2:.4f}")

    w(0, "ENDSEC"); w(0, "EOF")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# SVG - plan view plus a side elevation of the stack
# ---------------------------------------------------------------------------
def svg():
    M, GAP = 44.0, 78.0                # margin, and room under the plan for the stack
    vw = FRAME_W + 2 * M
    vh = FRAME_H + 2 * M + GAP
    p = []
    y = lambda v: FRAME_H - v

    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-M} {-M} {vw} {vh}" '
        f'width="100%" style="max-width:900px;height:auto" '
        f'font-family="ui-monospace,Consolas,monospace">'
    )
    p.append(
        '<defs><marker id="b" markerWidth="9" markerHeight="9" refX="8" refY="3" '
        'orient="auto"><path d="M0,0 L9,3 L0,6 z" fill="currentColor"/></marker></defs>'
    )
    p.append('<g color="var(--dim,#6B7378)">')

    # Monitor first - it shows through the window, which is a real hole.
    mx0 = (FRAME_W - MON_W) / 2
    my0 = (FRAME_H - MON_H) / 2
    p.append(
        f'<rect x="{mx0}" y="{y(my0 + MON_H)}" width="{MON_W}" height="{MON_H}" rx="3" '
        f'fill="var(--bore,#FFF)" stroke="var(--ref,#C8322B)" stroke-width="0.6" '
        f'stroke-dasharray="5 3" opacity="0.9"/>'
    )
    p.append(
        f'<text x="{FRAME_W / 2}" y="{y(FRAME_H / 2)}" font-size="6" text-anchor="middle" '
        f'fill="var(--ref,#C8322B)" opacity="0.9">LUT11S 242 &#215; 156</text>'
    )

    # Frame material: outer contour and window as one evenodd path, so the
    # window renders as the hole it actually is.
    win = " ".join(
        f'{"M" if i == 0 else "L"}{x},{y(yy)}'
        for i, (x, yy) in enumerate(window_polygon())
    )
    p.append(
        f'<path d="M{CORNER_R},{y(0)} H{FRAME_W - CORNER_R} '
        f'A{CORNER_R},{CORNER_R} 0 0 0 {FRAME_W},{y(CORNER_R)} '
        f'V{y(FRAME_H - CORNER_R)} '
        f'A{CORNER_R},{CORNER_R} 0 0 0 {FRAME_W - CORNER_R},{y(FRAME_H)} '
        f'H{CORNER_R} A{CORNER_R},{CORNER_R} 0 0 0 0,{y(FRAME_H - CORNER_R)} '
        f'V{y(CORNER_R)} A{CORNER_R},{CORNER_R} 0 0 0 {CORNER_R},{y(0)} Z '
        f'{win} Z" '
        f'fill="var(--plate,#E4E7E8)" fill-rule="evenodd" '
        f'stroke="var(--ink,#14171A)" stroke-width="0.9"/>'
    )
    for i, (tx, ty) in enumerate([
        (WIN_X0 + TAB / 2, WIN_Y0 + TAB / 2), (WIN_X1 - TAB / 2, WIN_Y0 + TAB / 2),
        (WIN_X0 + TAB / 2, WIN_Y1 - TAB / 2), (WIN_X1 - TAB / 2, WIN_Y1 - TAB / 2),
    ]):
        p.append(
            f'<text x="{tx}" y="{y(ty) + 2}" font-size="4.6" text-anchor="middle" '
            f'fill="var(--ink,#14171A)">TAB</text>'
        )

    for mx, my in MOUNTS:
        p.append(
            f'<circle cx="{mx}" cy="{y(my)}" r="{MOUNT_DIA / 2}" fill="var(--bore,#FFF)" '
            f'stroke="var(--ink,#14171A)" stroke-width="0.6"/>'
        )

    def hdim(x1, x2, yp, label):
        p.append(
            f'<line x1="{x1}" y1="{yp}" x2="{x2}" y2="{yp}" stroke="currentColor" '
            f'stroke-width="0.4" marker-start="url(#b)" marker-end="url(#b)"/>'
        )
        p.append(
            f'<text x="{(x1 + x2) / 2}" y="{yp - 2.5}" font-size="5" text-anchor="middle" '
            f'fill="currentColor">{label}</text>'
        )

    def vdim(y1, y2, xp, label):
        p.append(
            f'<line x1="{xp}" y1="{y1}" x2="{xp}" y2="{y2}" stroke="currentColor" '
            f'stroke-width="0.4" marker-start="url(#b)" marker-end="url(#b)"/>'
        )
        m = (y1 + y2) / 2
        p.append(
            f'<text x="{xp - 3}" y="{m}" font-size="5" text-anchor="middle" '
            f'fill="currentColor" transform="rotate(-90 {xp - 3} {m})">{label}</text>'
        )

    hdim(0, FRAME_W, -12, f"{FRAME_W:.0f}")
    hdim(WIN_X0, WIN_X1, y(WIN_Y1) - 8, f"window {WIN_X1 - WIN_X0:.0f}")
    vdim(0, FRAME_H, -12, f"{FRAME_H:.0f}")
    vdim(y(WIN_Y1), y(WIN_Y0), FRAME_W + 14, f"window {WIN_Y1 - WIN_Y0:.0f}")

    # ---- side elevation of the stack ----
    ex, ey = 0.0, FRAME_H + 34.0       # top-left of the elevation, SVG coords
    scale = 1.6                        # exaggerate depth so it reads
    bar_w = 150.0

    def layer(z0, depth, label, fill, dashed=False):
        h = depth * scale
        top = ey + (LID_DEPTH - z0 - depth) * scale
        dash = ' stroke-dasharray="3 2"' if dashed else ""
        p.append(
            f'<rect x="{ex}" y="{top}" width="{bar_w}" height="{h}" fill="{fill}" '
            f'stroke="var(--ink,#14171A)" stroke-width="0.5"{dash}/>'
        )
        p.append(
            f'<text x="{ex + bar_w + 6}" y="{top + h / 2 + 1.8}" font-size="5" '
            f'fill="var(--ink,#14171A)">{label}</text>'
        )

    p.append(
        f'<text x="{ex}" y="{ey - 4}" font-size="5.5" fill="currentColor" '
        f'letter-spacing="0.8">STACK &#183; LID CAVITY {LID_DEPTH:.0f} mm</text>'
    )
    p.append(
        f'<rect x="{ex - 2}" y="{ey}" width="{bar_w + 4}" height="{LID_DEPTH * scale}" '
        f'fill="none" stroke="currentColor" stroke-width="0.4" stroke-dasharray="3 3"/>'
    )
    layer(0, FOAM - PRELOAD, f"foam {FOAM:.0f} &#8594; {FOAM - PRELOAD:.0f} compressed",
          "var(--panel-2,#D6DADC)")
    layer(FOAM - PRELOAD, MON_D, f"monitor {MON_D:.0f}", "var(--plate,#E4E7E8)")
    layer(STANDOFF, THICKNESS, f"frame {THICKNESS:.0f}  (on {STANDOFF:.0f} mm standoffs)",
          "var(--bore,#FFF)")
    free = LID_DEPTH - STANDOFF - THICKNESS
    p.append(
        f'<text x="{ex + bar_w + 6}" y="{ey + free * scale / 2 + 1.8}" font-size="5" '
        f'fill="currentColor">{free:.0f} mm free</text>'
    )

    p.append('</g></svg>')
    return "".join(p)


if __name__ == "__main__":
    problems = check()
    if problems:
        print("LAYOUT PROBLEMS:")
        for pr in problems:
            print("  -", pr)
        raise SystemExit(1)

    with open("lut11s-bezel.dxf", "w", encoding="ascii") as f:
        f.write(dxf())
    with open("lut11s-bezel.svg", "w", encoding="utf-8") as f:
        f.write(svg())

    print(f"frame        {FRAME_W:.0f} x {FRAME_H:.0f} x {THICKNESS:.0f} mm aluminium")
    print(f"window       {WIN_X1 - WIN_X0:.0f} x {WIN_Y1 - WIN_Y0:.0f} mm, "
          f"{TAB:.0f} mm corner tabs")
    print(f"standoffs    {len(MOUNTS)} x M4 @ {STANDOFF:.0f} mm")
    print(f"stack        {FOAM - PRELOAD:.0f} foam + {MON_D:.0f} monitor + "
          f"{THICKNESS:.0f} frame = {STANDOFF + THICKNESS:.0f} mm "
          f"in a {LID_DEPTH:.0f} mm lid "
          f"({LID_DEPTH - STANDOFF - THICKNESS:.0f} mm free)")
    print(f"lid face     frame {FRAME_W:.0f} x {FRAME_H:.0f} in {LID_W:.0f} x {LID_H:.0f}")
    print("layout clean; wrote lut11s-bezel.dxf, lut11s-bezel.svg")

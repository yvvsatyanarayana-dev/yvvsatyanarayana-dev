#!/usr/bin/env python3
"""
Convert prepped portrait image into an elite Hyprland / Neovim terminal ASCII SVG:
- Sleek glassmorphic gradient chassis with ambient lighting and specular borders
- Crisp monochrome ASCII art with glowing sweep scan-cursor
- Starship / Neovim powerline statusline at bottom with true SVG chevron segments
- Top titlebar with window controls, active branch badge, and runtime tag
- Strictly valid XML for GitHub Camo caching

Outputs: portrait-ascii.svg
"""

import html
import os
import sys
from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-prepped.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "portrait-ascii.svg")

# Grid dimensions calibrated for 840 x 880 canvas
COLS = int(os.environ.get("COLS", 156))
ART_W = 790.0
CELL_W = ART_W / COLS
CELL_H = CELL_W * 1.76
ROWS = 82
RAMP = " .`:-=+*cs#%@"  # Bright (space) -> dark (dense)

# Image tuning parameters
CONTRAST = 1.14
BRIGHTNESS = 1.02
GAMMA = 1.14
WHITE_FLOOR = 0.82

PAD = 25
TITLEBAR_H = 38
STATUS_H = 46
CANVAS_W = 840
CANVAS_H = 880

BG = "#060911"
BG2 = "#0e1526"
FRAME = "#1e293b"
TITLE_TEXT = "#94a3b8"
INK = "#e2e8f0"
CURSOR = "#38bdf8"

SWEEP_DUR = 4.6
ROW_DUR = SWEEP_DUR / ROWS
STAGGER = ROW_DUR
STATUS_START = SWEEP_DUR + 0.1

STATIC = bool(os.environ.get("STATIC"))


def generate():
    if not os.path.exists(SRC):
        print(f"Error: {SRC} not found. Run prep_photo.py first.", file=sys.stderr)
        sys.exit(1)

    im = Image.open(SRC).convert("L")
    im = ImageEnhance.Brightness(im).enhance(BRIGHTNESS)
    im = ImageEnhance.Contrast(im).enhance(CONTRAST)
    im = im.resize((COLS, ROWS), Image.LANCZOS)
    px = im.load()

    rows_txt = []
    for y in range(ROWS):
        chars = []
        for x in range(COLS):
            lum = px[x, y] / 255.0
            lum = pow(lum, GAMMA)
            if lum >= WHITE_FLOOR:
                chars.append(" ")
                continue
            idx = int((1.0 - lum) * (len(RAMP) - 1) + 0.5)
            idx = max(0, min(len(RAMP) - 1, idx))
            chars.append(RAMP[idx])
        rows_txt.append("".join(chars))

    art_top = TITLEBAR_H + 16
    art_left = (CANVAS_W - ART_W) / 2

    css = f"""
@keyframes blink {{
  0%, 49% {{ opacity: 1; }}
  50%, 100% {{ opacity: 0; }}
}}
.blink {{ animation: blink 1s step-start infinite; }}
.glow-cursor {{
  filter: drop-shadow(0 0 6px #38bdf8);
}}
@media (prefers-reduced-motion: reduce) {{
  * {{ animation: none !important; }}
}}
""".strip()

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
        f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f'<style>{css}</style>',
        '<defs>',
        f'<linearGradient id="pbg" x1="0" y1="0" x2="0" y2="1">',
        f'<stop offset="0%" stop-color="{BG2}"/><stop offset="100%" stop-color="{BG}"/>',
        '</linearGradient>',
        f'<linearGradient id="glassBorder" x1="0" y1="0" x2="1" y2="1">',
        '<stop offset="0%" stop-color="#38bdf8" stop-opacity="0.6"/>',
        '<stop offset="50%" stop-color="#818cf8" stop-opacity="0.2"/>',
        '<stop offset="100%" stop-color="#38bdf8" stop-opacity="0.4"/>',
        '</linearGradient>',
        '</defs>',
        # Glass backdrop and subtle border
        f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="14" fill="url(#pbg)"/>',
        f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{CANVAS_H-1}" rx="14" fill="none" stroke="url(#glassBorder)" stroke-width="1.2"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity="0.9"/>',
    ]

    # Titlebar controls
    for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*18}" cy="{TITLEBAR_H/2}" r="5.5" fill="{dotcol}"/>')

    parts.append(
        f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" font-size="12" '
        f'font-weight="600" text-anchor="middle">satyanarayana@hyprland: ~$ ./portrait.sh</text>'
    )

    # Top right runtime badges
    parts.append(
        f'<g transform="translate({CANVAS_W - PAD - 150}, {TITLEBAR_H/2 - 10})">'
        f'<rect width="70" height="20" rx="5" fill="#1e293b"/>'
        f'<text x="35" y="14" fill="#38bdf8" font-size="10" font-weight="700" text-anchor="middle">⎇ main</text>'
        f'<rect x="76" width="68" height="20" rx="5" fill="#1e293b"/>'
        f'<text x="110" y="14" fill="#34d399" font-size="10" font-weight="700" text-anchor="middle">● active</text>'
        f'</g>'
    )

    # ASCII text rows
    font_size = CELL_H * 0.90
    for ry, line in enumerate(rows_txt):
        y = art_top + ry * CELL_H + CELL_H * 0.74
        row_y = art_top + ry * CELL_H
        delay = ry * STAGGER
        safe = html.escape(line)
        text = (
            f'<text xml:space="preserve" x="{art_left:.1f}" y="{y:.1f}" fill="{INK}" '
            f'font-size="{font_size:.1f}" textLength="{ART_W:.1f}" lengthAdjust="spacing">{safe}</text>'
        )

        if STATIC:
            parts.append(text)
            continue

        parts.append(
            f'<clipPath id="r{ry}"><rect x="{art_left:.1f}" y="{row_y:.1f}" height="{CELL_H:.2f}" width="0">'
            f'<animate attributeName="width" from="0" to="{ART_W:.1f}" begin="{delay:.3f}s" '
            f'dur="{ROW_DUR:.2f}s" fill="freeze"/></rect></clipPath>'
        )
        parts.append(f'<g clip-path="url(#r{ry})">{text}</g>')
        parts.append(
            f'<rect class="glow-cursor" y="{row_y+0.5:.1f}" width="{CELL_W:.1f}" height="{CELL_H-1:.1f}" fill="{CURSOR}" opacity="0">'
            f'<animate attributeName="x" from="{art_left:.1f}" to="{art_left+ART_W:.1f}" begin="{delay:.3f}s" '
            f'dur="{ROW_DUR:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.95" begin="{delay:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{delay+ROW_DUR:.3f}s"/></rect>'
        )

    # Bottom Neovim / Starship Powerline Statusbar
    status_line_y = CANVAS_H - STATUS_H - 12
    parts.append(f'<line x1="0" y1="{status_line_y:.1f}" x2="{CANVAS_W}" y2="{status_line_y:.1f}" stroke="{FRAME}" stroke-opacity="0.9"/>')

    # Draw Powerline Segments
    pl_y = status_line_y + 11
    pl_h = 24
    chev_w = 9

    # Segment 1: NORMAL mode
    s1_x, s1_w, s1_c = PAD, 68, "#6366f1"
    parts.append(f'<rect x="{s1_x}" y="{pl_y}" width="{s1_w}" height="{pl_h}" rx="4" fill="{s1_c}"/>')
    parts.append(f'<text x="{s1_x + s1_w/2}" y="{pl_y + 16}" fill="#ffffff" font-size="11" font-weight="700" text-anchor="middle">NORMAL</text>')
    # Chevron 1
    c1_x = s1_x + s1_w
    parts.append(f'<path d="M{c1_x},{pl_y} L{c1_x+chev_w},{pl_y+pl_h/2} L{c1_x},{pl_y+pl_h} Z" fill="{s1_c}"/>')

    # Segment 2: User / Host
    s2_x, s2_w, s2_c = c1_x + 2, 114, "#0284c7"
    parts.append(f'<rect x="{s2_x}" y="{pl_y}" width="{s2_w}" height="{pl_h}" fill="{s2_c}"/>')
    parts.append(f'<text x="{s2_x + s2_w/2}" y="{pl_y + 16}" fill="#ffffff" font-size="11" font-weight="600" text-anchor="middle">satyanarayana</text>')
    # Chevron 2
    c2_x = s2_x + s2_w
    parts.append(f'<path d="M{c2_x},{pl_y} L{c2_x+chev_w},{pl_y+pl_h/2} L{c2_x},{pl_y+pl_h} Z" fill="{s2_c}"/>')

    # Segment 3: Git branch
    s3_x, s3_w, s3_c = c2_x + 2, 78, "#059669"
    parts.append(f'<rect x="{s3_x}" y="{pl_y}" width="{s3_w}" height="{pl_h}" fill="{s3_c}"/>')
    parts.append(f'<text x="{s3_x + s3_w/2}" y="{pl_y + 16}" fill="#ffffff" font-size="11" font-weight="600" text-anchor="middle">git:(main)</text>')
    # Chevron 3
    c3_x = s3_x + s3_w
    parts.append(f'<path d="M{c3_x},{pl_y} L{c3_x+chev_w},{pl_y+pl_h/2} L{c3_x},{pl_y+pl_h} Z" fill="{s3_c}"/>')

    # Command prompt after powerline: whoami ➜ Satyanarayana
    prompt_x = c3_x + chev_w + 14
    prompt_y = pl_y + 16
    prompt_w = 280

    parts.append(
        f'<clipPath id="status_clip"><rect x="{prompt_x}" y="{pl_y}" width="0" height="{pl_h}">'
        f'<animate attributeName="width" from="0" to="{prompt_w}" begin="{STATUS_START:.2f}s" dur="0.75s" fill="freeze"/>'
        f'</rect></clipPath>'
    )
    parts.append(
        f'<g clip-path="url(#status_clip)">'
        f'<text x="{prompt_x}" y="{prompt_y}" font-size="12">'
        f'<tspan fill="#38bdf8">whoami </tspan>'
        f'<tspan fill="{TITLE_TEXT}">➜ </tspan>'
        f'<tspan fill="#f8fafc" font-weight="700">Satyanarayana</tspan>'
        f'</text></g>'
    )

    # Blinking prompt cursor
    cur_x = prompt_x + len("whoami ➜ Satyanarayana") * 7.4 + 4
    parts.append(
        f'<rect class="blink" x="{cur_x:.1f}" y="{pl_y+4}" width="7" height="16" fill="{CURSOR}" opacity="0">'
        f'<set attributeName="opacity" to="1" begin="{STATUS_START + 0.75:.2f}s"/>'
        f'</rect>'
    )

    parts.append("</svg>")
    svg = "".join(parts)

    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Success: wrote {OUT} ({len(svg)} bytes, canvas {CANVAS_W}x{CANVAS_H})")


if __name__ == "__main__":
    generate()

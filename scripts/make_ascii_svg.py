#!/usr/bin/env python3
"""
Convert a prepped portrait image into a clean, monochrome animated ASCII SVG:
- Single monochromatic light-gray ink for clean, crisp terminal rendering
- Dense character ramp with leading space for clean background knockout
- SMIL typewriter reveal animation: horizontal clip wipe with a block cursor
  riding each row's leading edge, cascading top-to-bottom and freezing once complete
- Terminal titlebar and bottom status line with blinking cursor

Outputs: portrait-ascii.svg (or custom path)
"""

import html
import os
import sys
from PIL import Image, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-prepped.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "portrait-ascii.svg")

# Grid dimensions
COLS = int(os.environ.get("COLS", 170))
ART_W_TARGET = 800
CELL_W = ART_W_TARGET / COLS
CELL_H = CELL_W * 15 / 8
ROWS = round(COLS * 8 / 15)
RAMP = " .`:-=+*cs#%@"  # Bright (space) -> dark (dense)

# Tuning parameters
CONTRAST = 1.12
BRIGHTNESS = 1.02
GAMMA = 1.15
WHITE_FLOOR = 0.82   # Luminance above this becomes space

PAD = 20
TITLEBAR_H = 34
STATUS_H = 32
ART_W = COLS * CELL_W
ART_H = ROWS * CELL_H
CANVAS_W = 840
CANVAS_H = 880

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#c9d1d9"
CURSOR = "#58a6ff"

# Sweep animation timing
ROW_DUR = 5.2 / ROWS
STAGGER = ROW_DUR

STATIC = bool(os.environ.get("STATIC"))


def generate():
    if not os.path.exists(SRC):
        print(f"Error: {SRC} not found. Run prep_photo.py first.", file=sys.stderr)
        sys.exit(1)

    # 1. Load and process image
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

    art_top = TITLEBAR_H + 18

    # 2. Build SVG parts
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
        f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<defs>',
        f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">',
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>',
        '</linearGradient></defs>',
        f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{CANVAS_H-1}" rx="12" fill="none" stroke="{FRAME}" stroke-width="1"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]

    # Titlebar controls
    for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
    parts.append(
        f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" font-size="12" '
        f'text-anchor="middle">satyanarayana@github: ~$ ./portrait.sh</text>'
    )

    # ASCII Rows
    font_size = CELL_H * 0.88
    art_left = (CANVAS_W - ART_W) / 2
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
            f'<rect y="{row_y+1:.1f}" width="{CELL_W:.1f}" height="{CELL_H-1:.1f}" fill="{CURSOR}" opacity="0">'
            f'<animate attributeName="x" from="{art_left:.1f}" to="{art_left+ART_W:.1f}" begin="{delay:.3f}s" '
            f'dur="{ROW_DUR:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.85" begin="{delay:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{delay+ROW_DUR:.3f}s"/></rect>'
        )

    # Status Bar
    status_line_y = CANVAS_H - STATUS_H - 12
    status_y = status_line_y + 24
    parts.append(f'<line x1="0" y1="{status_line_y:.1f}" x2="{CANVAS_W}" y2="{status_line_y:.1f}" stroke="{FRAME}"/>')
    parts.append(
        f'<text x="{PAD}" y="{status_y:.1f}" fill="{TITLE_TEXT}" font-size="13">'
        f'satyanarayana@github:~$ whoami <tspan fill="{INK}">Satyanarayana</tspan></text>'
    )
    status_chars = len("satyanarayana@github:~$ whoami Satyanarayana ")
    parts.append(
        f'<rect x="{PAD + status_chars * 13 * 0.58:.1f}" y="{status_y-12:.1f}" width="8" height="14" fill="{CURSOR}">'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
        f'dur="1s" repeatCount="indefinite"/></rect>'
    )

    parts.append("</svg>")
    svg = "".join(parts)

    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Success: wrote {OUT} ({len(svg)} bytes, canvas {CANVAS_W}x{CANVAS_H})")


if __name__ == "__main__":
    generate()

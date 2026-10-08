#!/usr/bin/env python3
"""
Convert prepped portrait image into an elite Black & White / Obsidian ASCII SVG:
- Deep obsidian backdrop with clean zinc frame
- Crisp monochrome ASCII typography
- Traveling scanline cursor in pure white with soft glow
- Bottom status prompt with smooth typewriter reveal and blinking cursor
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
ROWS = 84
RAMP = " .`:-=+*cs#%@"  # Bright (space) -> dark (dense)

# Image tuning parameters
CONTRAST = 1.14
BRIGHTNESS = 1.02
GAMMA = 1.14
WHITE_FLOOR = 0.82

PAD = 25
TITLEBAR_H = 34
STATUS_H = 36
CANVAS_W = 840
CANVAS_H = 880

BG = "#060606"
BG2 = "#0f0f0f"
FRAME = "#262626"
TITLE_TEXT = "#737373"
INK = "#e5e5e5"
CURSOR = "#ffffff"

SWEEP_DUR = 4.8
ROW_DUR = SWEEP_DUR / ROWS
STAGGER = ROW_DUR
STATUS_START = SWEEP_DUR + 0.15

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
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>',
        '</linearGradient>',
        '<filter id="glow" x="-20%" y="-20%" width="140%" height="140%">',
        '<feGaussianBlur stdDeviation="2" result="blur"/>',
        '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>',
        '</filter>',
        '</defs>',
        f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="url(#pbg)"/>',
        f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{CANVAS_H-1}" rx="12" fill="none" stroke="{FRAME}" stroke-width="1"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity="0.8"/>',
    ]

    # Minimalist monochrome traffic dots
    for i, dotcol in enumerate(["#333333", "#4d4d4d", "#666666"]):
        parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
    parts.append(
        f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" font-size="12" '
        f'text-anchor="middle">satyanarayana@github: ~$ ./portrait.sh</text>'
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
            f'<rect y="{row_y+0.5:.1f}" width="{CELL_W:.1f}" height="{CELL_H-1:.1f}" fill="{CURSOR}" opacity="0" filter="url(#glow)">'
            f'<animate attributeName="x" from="{art_left:.1f}" to="{art_left+ART_W:.1f}" begin="{delay:.3f}s" '
            f'dur="{ROW_DUR:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.9" begin="{delay:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{delay+ROW_DUR:.3f}s"/></rect>'
        )

    # Bottom status bar
    status_line_y = CANVAS_H - STATUS_H - 10
    status_y = status_line_y + 24
    parts.append(f'<line x1="0" y1="{status_line_y:.1f}" x2="{CANVAS_W}" y2="{status_line_y:.1f}" stroke="{FRAME}" stroke-opacity="0.8"/>')

    prompt_prefix = "satyanarayana@github:~$ "
    cmd_text = "whoami "
    name_text = "Satyanarayana"

    prompt_x = PAD
    prompt_w = 400

    parts.append(
        f'<clipPath id="status_clip"><rect x="{prompt_x}" y="{status_line_y+4}" width="0" height="{STATUS_H}">'
        f'<animate attributeName="width" from="0" to="{prompt_w}" begin="{STATUS_START:.2f}s" dur="0.8s" fill="freeze"/>'
        f'</rect></clipPath>'
    )
    parts.append(
        f'<g clip-path="url(#status_clip)">'
        f'<text x="{prompt_x}" y="{status_y:.1f}" font-size="13">'
        f'<tspan fill="{TITLE_TEXT}">{html.escape(prompt_prefix)}</tspan>'
        f'<tspan fill="{TITLE_TEXT}">{html.escape(cmd_text)}</tspan>'
        f'<tspan fill="#ffffff" font-weight="700">{html.escape(name_text)}</tspan>'
        f'</text></g>'
    )

    # Terminal cursor that appears right after typing finishes
    cursor_x = prompt_x + len(prompt_prefix + cmd_text + name_text) * 7.8 + 6
    parts.append(
        f'<rect class="blink" x="{cursor_x:.1f}" y="{status_y-13:.1f}" width="8" height="15" fill="{CURSOR}" opacity="0">'
        f'<set attributeName="opacity" to="1" begin="{STATUS_START + 0.8:.2f}s"/>'
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

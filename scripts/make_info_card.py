#!/usr/bin/env python3
"""
Generate a Neofetch-style terminal info card as an animated SVG:
- macOS/Linux terminal title bar with colored control dots
- Left side: sleek ASCII distro/terminal art
- Right side: styled key-value pairs (Role, Focus, Languages, Frameworks, Databases, Tools)
- Bottom: 8-color terminal palette blocks
- Staggered line-by-line slide/fade animation with glowing blinking cursor

Canvas is 840 x 880 to pair with the ASCII portrait in a side-by-side README table.
Outputs: info-card.svg
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "info-card.svg")

W, H = 840, 880
PAD = 24
TITLEBAR_H = 34

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
TEXT = "#e6edf3"
CYAN = "#22d3ee"
BLUE = "#58a6ff"
GREEN = "#3fb950"
YELLOW = "#f2cc60"
PURPLE = "#bc8cff"
ORANGE = "#ff9345"

# Animation timing
LINE_DUR = 0.35
LINE_STAGGER = 0.08
TOTAL_LINES = 16

STATIC = bool(os.environ.get("STATIC"))

ASCII_ART = [
    r"       /\        ",
    r"      /  \       ",
    r"     /\   \      ",
    r"    /      \     ",
    r"   /   ,,   \    ",
    r"  /   |  |  -\   ",
    r" /_-''    ''-_\  ",
    r"                 ",
    r"   [ PYTHON ]    ",
    r"   [ BACKEND]    ",
    r"   [ SYSTEM ]    ",
]

INFO_ROWS = [
    ("header", "satyanarayana@github", CYAN),
    ("rule", "------------------------------------------", FRAME),
    ("OS", "Arch Linux x86_64", TEXT),
    ("Host", "Cloud / Backend Services", TEXT),
    ("Role", "Backend Developer", GREEN),
    ("Focus", "API Architecture & Reliability", TEXT),
    ("Languages", "Python, C++, SQL, JavaScript", BLUE),
    ("Frameworks", "FastAPI, Flask, React", CYAN),
    ("Databases", "PostgreSQL, MongoDB", YELLOW),
    ("Tools", "Git, Docker, Postman, Linux", PURPLE),
    ("Problem Solving", "LeetCode & HackerRank Solver", ORANGE),
    ("Uptime", "Continuous Learning & Building", TEXT),
]

COLOR_BLOCKS = ["#484f58", "#ff7b72", "#7ee787", "#f2cc60", "#79c0ff", "#d2a8ff", "#56d364", "#ffffff"]


def build_svg():
    css = f"""
@keyframes slideIn {{
  0%   {{ opacity: 0; transform: translateY(10px); }}
  100% {{ opacity: 1; transform: translateY(0); }}
}}
.row {{ opacity: 0; animation: slideIn {LINE_DUR:.2f}s cubic-bezier(0.16, 1, 0.3, 1) both; }}
@keyframes blink {{
  0%, 49% {{ opacity: 1; }}
  50%, 100% {{ opacity: 0; }}
}}
.cursor {{ animation: blink 1s step-start infinite; }}
@media (prefers-reduced-motion: reduce) {{
  .row {{ opacity: 1 !important; transform: none !important; animation: none !important; }}
}}
""".strip()

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f'<style>{css if not STATIC else ""}</style>',
        '<defs>'
        f'<linearGradient id="cardbg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>'
        '</defs>',
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#cardbg)"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}" stroke-width="1"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity="0.6"/>',
    ]

    # Titlebar controls
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i * 18}" cy="{TITLEBAR_H / 2}" r="5.5" fill="{dot}"/>')
    parts.append(
        f'<text x="{W / 2}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" font-size="13" '
        f'text-anchor="middle">satyanarayana@github: ~$ neofetch</text>'
    )

    content_top = TITLEBAR_H + 46
    ascii_x = PAD + 10
    info_x = PAD + 240

    # Draw ASCII logo on the left
    for idx, line in enumerate(ASCII_ART):
        y = content_top + idx * 30
        delay = idx * 0.05
        delay_style = f' style="animation-delay:{delay:.2f}s"' if not STATIC else ''
        art_color = CYAN if "PYTHON" in line else (BLUE if "BACKEND" in line else (PURPLE if "SYSTEM" in line else CYAN))
        parts.append(
            f'<text class="row"{delay_style} x="{ascii_x}" y="{y}" fill="{art_color}" '
            f'font-size="16" font-weight="600" xml:space="preserve">{line}</text>'
        )

    # Draw right column info
    start_delay = 0.25
    y_pos = content_top - 6
    for idx, item in enumerate(INFO_ROWS):
        delay = start_delay + idx * LINE_STAGGER
        delay_style = f' style="animation-delay:{delay:.2f}s"' if not STATIC else ''

        if item[0] == "header":
            user, host = item[1].split("@")
            parts.append(
                f'<g class="row"{delay_style}>'
                f'<text x="{info_x}" y="{y_pos}" font-size="22" font-weight="700">'
                f'<tspan fill="{CYAN}">{user}</tspan>'
                f'<tspan fill="{MUTED}">@</tspan>'
                f'<tspan fill="{BLUE}">{host}</tspan>'
                f'</text></g>'
            )
            y_pos += 26
        elif item[0] == "rule":
            parts.append(
                f'<text class="row"{delay_style} x="{info_x}" y="{y_pos}" fill="{FRAME}" '
                f'font-size="15">{item[1]}</text>'
            )
            y_pos += 34
        else:
            key, val, val_color = item[0], item[1], item[2]
            parts.append(
                f'<g class="row"{delay_style}>'
                f'<text x="{info_x}" y="{y_pos}" font-size="17">'
                f'<tspan fill="{CYAN}" font-weight="600">{key}: </tspan>'
                f'<tspan fill="{val_color}">{val}</tspan>'
                f'</text></g>'
            )
            y_pos += 38

    # Terminal color palette blocks at bottom
    palette_y = content_top + 540
    palette_delay = start_delay + len(INFO_ROWS) * LINE_STAGGER + 0.1
    pal_delay_style = f' style="animation-delay:{palette_delay:.2f}s"' if not STATIC else ''

    parts.append(f'<g class="row"{pal_delay_style}>')
    parts.append(f'<line x1="{PAD}" y1="{palette_y - 28}" x2="{W - PAD}" y2="{palette_y - 28}" stroke="{FRAME}" stroke-opacity="0.4"/>')
    parts.append(f'<text x="{info_x}" y="{palette_y - 8}" fill="{MUTED}" font-size="14">Palette:</text>')

    block_w, block_h, block_gap = 48, 22, 10
    for i, col in enumerate(COLOR_BLOCKS):
        bx = info_x + i * (block_w + block_gap)
        parts.append(f'<rect x="{bx}" y="{palette_y + 4}" width="{block_w}" height="{block_h}" rx="4" fill="{col}"/>')
    parts.append('</g>')

    # Terminal prompt footer with blinking cursor
    foot_y = palette_y + 80
    cursor_delay = palette_delay + 0.2
    cur_delay_style = f' style="animation-delay:{cursor_delay:.2f}s"' if not STATIC else ''

    parts.append(
        f'<g class="row"{cur_delay_style}>'
        f'<text x="{PAD + 20}" y="{foot_y}" font-size="16">'
        f'<tspan fill="{GREEN}">satyanarayana@dev</tspan>'
        f'<tspan fill="{MUTED}">:</tspan>'
        f'<tspan fill="{BLUE}">~</tspan>'
        f'<tspan fill="{TEXT}">$ </tspan>'
        f'</text>'
        f'<rect class="cursor" x="{PAD + 248}" y="{foot_y - 14}" width="9" height="18" fill="{CYAN}"/>'
        f'</g>'
    )

    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    svg = build_svg()
    os.makedirs(os.path.dirname(os.path.abspath(OUT_PATH)), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Success: wrote {OUT_PATH} ({len(svg)} bytes)")

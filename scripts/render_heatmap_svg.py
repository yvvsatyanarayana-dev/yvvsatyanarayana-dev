#!/usr/bin/env python3
"""
Render data/contributions.json as an elite Hyprland / glassmorphism contribution heatmap SVG:
- Glassmorphic chassis with gradient specular border
- Starship / Hyprland terminal titlebar with git branch and status badges
- 53-week x 7-day grid with diagonal elastic scale wave
- Interactive hover transitions on calendar cells
- Pill chips in footer displaying total contributions, streaks, best day, and date range
Outputs: contrib-heatmap.svg
"""

import datetime
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
IN_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "contrib-heatmap.svg")

# Emerald green palette ramp: empty -> level 5
PALETTE = ["#0f172a", "#064e3b", "#047857", "#059669", "#10b981", "#34d399"]

CELL = 12
GAP = 3
STEP = CELL + GAP
PAD = 24
LEFT_LABEL_W = 32
TOP_LABEL_H = 22
TITLEBAR_H = 38

BG = "#060911"
BG2 = "#0e1526"
FRAME = "#1e293b"
MUTED = "#94a3b8"
TEXT = "#f8fafc"
GREEN = "#34d399"
CYAN = "#38bdf8"
GOLD = "#fbbf24"

COL_T = 0.016
ROW_T = 0.042
CELL_DUR = 0.44


def level_for(count):
    if count == 0:
        return 0
    if count <= 2:
        return 1
    if count <= 5:
        return 2
    if count <= 10:
        return 3
    if count <= 20:
        return 4
    return 5


def build_grid(days):
    if not days:
        return []
    first = datetime.date.fromisoformat(days[0]["date"])
    lead_pad = (first.weekday() + 1) % 7
    grid = []
    col = [None] * lead_pad
    for d in days:
        date = datetime.date.fromisoformat(d["date"])
        weekday = (date.weekday() + 1) % 7
        while len(col) < weekday:
            col.append(None)
        col.append((d["date"], d["count"], level_for(d["count"])))
        if len(col) == 7:
            grid.append(col)
            col = []
    if col:
        while len(col) < 7:
            col.append(None)
        grid.append(col)
    return grid


def render(data):
    days = data["days"]
    grid = build_grid(days)
    n_cols = len(grid)
    art_w = n_cols * STEP
    art_h = 7 * STEP

    month_labels = []
    seen_months = set()
    for ci, column in enumerate(grid):
        for cell in column:
            if cell is None:
                continue
            date = datetime.date.fromisoformat(cell[0])
            key = (date.year, date.month)
            if key not in seen_months and date.day <= 7:
                seen_months.add(key)
                month_labels.append((ci, date.strftime("%b")))
            break

    canvas_w = PAD + LEFT_LABEL_W + art_w + PAD
    stats_h = 92
    canvas_h = TITLEBAR_H + TOP_LABEL_H + art_h + stats_h + PAD

    css = f"""
@keyframes cell {{
  0%   {{ opacity: 0; transform: scale(0.2) translateY(-4px); }}
  65%  {{ transform: scale(1.15) translateY(0); }}
  100% {{ opacity: 1; transform: scale(1) translateY(0); }}
}}
.c {{
  transform-box: fill-box;
  transform-origin: center;
  opacity: 0;
  animation: cell {CELL_DUR:.2f}s cubic-bezier(0.2, 0.8, 0.2, 1) both;
  transition: transform 0.15s ease, filter 0.15s ease;
}}
.c:hover {{
  transform: scale(1.35);
  filter: drop-shadow(0 0 6px #34d399);
  stroke: #ffffff;
  stroke-width: 0.8px;
  cursor: pointer;
}}
@media (prefers-reduced-motion: reduce) {{
  .c {{ opacity: 1 !important; transform: none !important; animation: none !important; }}
}}
""".strip()

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'viewBox="0 0 {canvas_w} {canvas_h}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f'<style>{css}</style>',
        '<defs>',
        f'<linearGradient id="hbg" x1="0" y1="0" x2="0" y2="1">',
        f'<stop offset="0%" stop-color="{BG2}"/><stop offset="100%" stop-color="{BG}"/>',
        '</linearGradient>',
        f'<linearGradient id="glassBorder" x1="0" y1="0" x2="1" y2="1">',
        '<stop offset="0%" stop-color="#38bdf8" stop-opacity="0.6"/>',
        '<stop offset="50%" stop-color="#818cf8" stop-opacity="0.2"/>',
        '<stop offset="100%" stop-color="#38bdf8" stop-opacity="0.4"/>',
        '</linearGradient>',
        '</defs>',
        f'<rect width="{canvas_w}" height="{canvas_h}" rx="14" fill="url(#hbg)"/>',
        f'<rect x="0.5" y="0.5" width="{canvas_w-1}" height="{canvas_h-1}" rx="14" fill="none" stroke="url(#glassBorder)" stroke-width="1.2"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity="0.9"/>',
    ]

    # Titlebar controls
    for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*18}" cy="{TITLEBAR_H/2}" r="5.5" fill="{dotcol}"/>')

    parts.append(
        f'<text x="{canvas_w/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
        f'font-weight="600" text-anchor="middle">satyanarayana@hyprland: ~/contributions --graph</text>'
    )

    # Top right runtime badges
    parts.append(
        f'<g transform="translate({canvas_w - PAD - 150}, {TITLEBAR_H/2 - 10})">'
        f'<rect width="70" height="20" rx="5" fill="#1e293b"/>'
        f'<text x="35" y="14" fill="#38bdf8" font-size="10" font-weight="700" text-anchor="middle">⎇ main</text>'
        f'<rect x="76" width="68" height="20" rx="5" fill="#1e293b"/>'
        f'<text x="110" y="14" fill="#34d399" font-size="10" font-weight="700" text-anchor="middle">● 53w grid</text>'
        f'</g>'
    )

    grid_top = TITLEBAR_H + TOP_LABEL_H
    grid_left = PAD + LEFT_LABEL_W

    # Month labels
    for ci, label in month_labels:
        x = grid_left + ci * STEP
        parts.append(f'<text x="{x}" y="{TITLEBAR_H + 15}" fill="{MUTED}" font-size="10" font-weight="600">{label}</text>')

    # Day of week labels
    for wi, wname in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = grid_top + wi * STEP + CELL * 0.78
        parts.append(f'<text x="{PAD}" y="{y:.1f}" fill="{MUTED}" font-size="9" font-weight="600">{wname}</text>')

    # Grid cells
    for ci, column in enumerate(grid):
        gx = grid_left + ci * STEP
        for ri, cell in enumerate(column):
            if cell is None:
                continue
            date_s, count, lvl = cell
            gy = grid_top + ri * STEP
            delay = ci * COL_T + ri * ROW_T
            plural = "s" if count != 1 else ""
            parts.append(
                f'<rect class="c" x="{gx}" y="{gy}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{PALETTE[lvl]}" style="animation-delay:{delay:.3f}s">'
                f'<title>{date_s}: {count} contribution{plural}</title></rect>'
            )

    # Legend Less -> More
    leg_y = grid_top + art_h + 10
    leg_x = canvas_w - PAD - (len(PALETTE) * (CELL - 1) + 76)
    parts.append(f'<text x="{leg_x}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" font-size="10" font-weight="600" text-anchor="end">Less</text>')
    lx = leg_x + 8
    for lvl, color in enumerate(PALETTE):
        parts.append(f'<rect x="{lx}" y="{leg_y}" width="{CELL-1}" height="{CELL-1}" rx="2.2" fill="{color}"/>')
        lx += CELL
    parts.append(f'<text x="{lx + 4}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" font-size="10" font-weight="600">More</text>')

    sep_y = leg_y + CELL + 14
    parts.append(f'<line x1="0" y1="{sep_y}" x2="{canvas_w}" y2="{sep_y}" stroke="{FRAME}" stroke-opacity="0.6"/>')

    cs = data["current_streak"]["length"]
    ls = data["longest_streak"]["length"]
    total = data["total_contributions"]
    best = data["best_day"]
    rng = data["range"]

    ly = sep_y + 24

    # Stat chips in footer
    # Chip 1: Total contributions
    t_text = f"{total:,} CONTRIBUTIONS"
    t_w = len(t_text) * 7.5 + 16
    parts.append(f'<rect x="{PAD}" y="{ly - 14}" width="{t_w}" height="22" rx="6" fill="#064e3b"/>')
    parts.append(f'<text x="{PAD + t_w/2}" y="{ly + 1}" fill="{GREEN}" font-size="11" font-weight="700" text-anchor="middle">{t_text}</text>')

    # Chip 2: Current streak
    c_text = f"🔥 {cs}d CURRENT"
    c_w = len(c_text) * 7.5 + 16
    c_x = PAD + t_w + 10
    parts.append(f'<rect x="{c_x}" y="{ly - 14}" width="{c_w}" height="22" rx="6" fill="#0c4a6e"/>')
    parts.append(f'<text x="{c_x + c_w/2}" y="{ly + 1}" fill="{CYAN}" font-size="11" font-weight="700" text-anchor="middle">{c_text}</text>')

    # Chip 3: Longest streak
    l_text = f"🏆 {ls}d MAX"
    l_w = len(l_text) * 7.5 + 16
    l_x = c_x + c_w + 10
    parts.append(f'<rect x="{l_x}" y="{ly - 14}" width="{l_w}" height="22" rx="6" fill="#312e81"/>')
    parts.append(f'<text x="{l_x + l_w/2}" y="{ly + 1}" fill="#818cf8" font-size="11" font-weight="700" text-anchor="middle">{l_text}</text>')

    # Right side: date range chip
    r_text = f"{rng['start']} → {rng['end']}"
    r_w = len(r_text) * 7.5 + 16
    parts.append(f'<rect x="{canvas_w - PAD - r_w}" y="{ly - 14}" width="{r_w}" height="22" rx="6" fill="#1e293b"/>')
    parts.append(f'<text x="{canvas_w - PAD - r_w/2}" y="{ly + 1}" fill="{MUTED}" font-size="11" font-weight="600" text-anchor="middle">{r_text}</text>')

    # Second footer row: Best day stat
    ly2 = ly + 28
    parts.append(f'<text x="{PAD}" y="{ly2}" font-size="12" fill="{MUTED}">'
                 f'Peak activity: <tspan fill="{GOLD}" font-weight="700">{best["count"]} contributions</tspan> on {best["date"]}</text>')

    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    if not os.path.exists(IN_PATH):
        print(f"Error: {IN_PATH} not found. Run fetch_contributions.py first.", file=sys.stderr)
        sys.exit(1)
    with open(IN_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    svg = render(data)
    os.makedirs(os.path.dirname(os.path.abspath(OUT_PATH)), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Success: wrote {OUT_PATH} ({len(svg)} bytes)")

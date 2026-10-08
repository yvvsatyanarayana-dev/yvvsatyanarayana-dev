#!/usr/bin/env python3
"""
Render the streak / numbers card as a stealth Black & White / Obsidian terminal SVG:
- Deep obsidian chassis with clean zinc borders
- 6 minimalist stat tiles with crisp white typography
- 24-frame mechanical slot-counter count-up
- Monthly contribution bar chart with spotlight-white peak bar
- Interactive hover effects in monochrome
Outputs: stats.svg
"""

import datetime
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data", "contributions.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "stats.svg")

BG = "#060606"
BG2 = "#0f0f0f"
TILE = "#121212"
FRAME = "#262626"
MUTED = "#737373"
INK = "#ffffff"
BAR = "#3a3a3a"
PEAK_BAR = "#ffffff"

W, H = 840, 880
PAD = 20
TITLEBAR_H = 34
COLS, ROWS = 2, 3
GAP = 16
TILE_W = (W - PAD * 2 - GAP * (COLS - 1)) / COLS
TILE_H = 150
TILES_TOP = TITLEBAR_H + PAD + 6
CHART_TOP = TILES_TOP + ROWS * TILE_H + (ROWS - 1) * GAP + GAP

# Timing (seconds)
TILE_STAGGER = 0.12
SLIDE_DUR = 0.55
COUNT_DUR = 1.3
FRAMES = 24
BAR_START = TILE_STAGGER * COLS * ROWS + 0.35
BAR_STAGGER = 0.05
BAR_DUR = 0.65


def short_date(d):
    if not d:
        return "—"
    dt = datetime.date.fromisoformat(d)
    return f"{dt.strftime('%b')} {dt.day}"


def span(s):
    return f'{short_date(s["start"])} – {short_date(s["end"])}' if s and s.get("length") else "—"


def fmt(v, like):
    return f"{v:,.1f}" if isinstance(like, float) else f"{int(round(v)):,}"


def render():
    if not os.path.exists(SRC):
        print(f"Error: {SRC} not found. Run fetch_contributions.py first.", file=sys.stderr)
        sys.exit(1)

    with open(SRC, "r", encoding="utf-8") as f:
        data = json.load(f)

    cur = data.get("current_streak", {"length": 0})
    lng = data.get("longest_streak", {"length": 0})
    best = data.get("best_day", {"count": 0, "date": ""})
    n_days = max(1, len(data.get("days", [])))
    active_days = data.get("active_days", 0)
    total_contrib = data.get("total_contributions", 0)
    avg_per_day = data.get("avg_per_active_day", 0.0)

    tiles = [
        ("current streak", cur["length"], " days", span(cur), INK),
        ("longest streak", lng["length"], " days", span(lng), INK),
        ("contributions", total_contrib, "", "in the last year", INK),
        ("active days", active_days, f" / {n_days}", f"{(active_days / n_days) * 100:.0f}% of the year", INK),
        ("best day", best["count"], "", short_date(best["date"]), INK),
        ("avg / active day", avg_per_day, "", "contributions", INK),
    ]

    css = f"""
.t {{
  opacity: 0;
  animation: slideIn {SLIDE_DUR}s cubic-bezier(0.16, 1, 0.3, 1) both;
}}
.tile-box {{
  transition: stroke 0.25s ease, filter 0.25s ease;
}}
.t:hover .tile-box {{
  stroke: #ffffff;
  stroke-width: 1.2;
  filter: drop-shadow(0 4px 12px rgba(255, 255, 255, 0.12));
}}
@keyframes slideIn {{
  0%   {{ opacity: 0; transform: translateY(16px); }}
  100% {{ opacity: 1; transform: translateY(0); }}
}}
.b {{
  transform-box: fill-box;
  transform-origin: bottom;
  transform: scaleY(0);
  animation: grow {BAR_DUR}s cubic-bezier(0.34, 1.25, 0.64, 1) both;
  transition: filter 0.2s ease;
}}
.b:hover {{
  filter: brightness(1.35) drop-shadow(0 -3px 8px #ffffff);
  cursor: pointer;
}}
@keyframes grow {{
  to {{ transform: scaleY(1); }}
}}
@media (prefers-reduced-motion: reduce) {{
  .t, .b {{ opacity: 1 !important; transform: none !important; animation: none !important; }}
}}
""".strip()

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f'<style>{css}</style>',
        '<defs>',
        f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">',
        f'<stop offset="0%" stop-color="{BG2}"/><stop offset="100%" stop-color="{BG}"/>',
        '</linearGradient>',
        '</defs>',
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]

    # Minimalist monochrome traffic dots
    for i, dot in enumerate(["#333333", "#4d4d4d", "#666666"]):
        parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
    parts.append(
        f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
        f'text-anchor="middle">satyanarayana@github: ~$ ./stats.sh</text>'
    )

    # Stat tiles
    for i, (label, value, suffix, caption, accent) in enumerate(tiles):
        col, row = i % COLS, i // COLS
        x = PAD + col * (TILE_W + GAP)
        y = TILES_TOP + row * (TILE_H + GAP)
        start = i * TILE_STAGGER
        count_start = start + SLIDE_DUR * 0.55

        parts.append(f'<g class="t" style="animation-delay:{start:.2f}s">')
        parts.append(f'<rect class="tile-box" x="{x:.1f}" y="{y}" width="{TILE_W:.1f}" height="{TILE_H}" rx="10" '
                     f'fill="{TILE}" stroke="{FRAME}"/>')
        parts.append(f'<text x="{x+24:.1f}" y="{y+40}" fill="{MUTED}" font-size="22">$ {html.escape(label)}</text>')

        num_y = y + 100
        for k in range(1, FRAMES + 1):
            p = k / FRAMES
            v = value * (1 - (1 - p) ** 3.5)
            t_on = count_start + COUNT_DUR * (k - 1) / FRAMES
            t_off = count_start + COUNT_DUR * k / FRAMES
            anim = f'<set attributeName="opacity" to="1" begin="{t_on:.3f}s"/>'
            if k < FRAMES:
                anim += f'<set attributeName="opacity" to="0" begin="{t_off:.3f}s"/>'
            parts.append(
                f'<text x="{x+24:.1f}" y="{num_y}" opacity="0" font-size="54" font-weight="700" fill="{accent}">'
                f'{fmt(v, value)}<tspan font-size="24" font-weight="400" fill="{MUTED}">{html.escape(suffix)}</tspan>'
                f'{anim}</text>'
            )
        parts.append(f'<text x="{x+24:.1f}" y="{y+132}" fill="{MUTED}" font-size="20">{html.escape(caption)}</text>')
        parts.append('</g>')

    # Monthly bars
    monthly = data.get("monthly", [])
    chart_x, chart_w = PAD, W - PAD * 2
    chart_h = H - PAD - CHART_TOP
    parts.append(f'<g class="t" style="animation-delay:{BAR_START - 0.25:.2f}s">')
    parts.append(f'<rect class="tile-box" x="{chart_x}" y="{CHART_TOP}" width="{chart_w}" height="{chart_h}" rx="10" '
                 f'fill="{TILE}" stroke="{FRAME}"/>')
    parts.append(f'<text x="{chart_x+24}" y="{CHART_TOP+40}" fill="{MUTED}" font-size="22">$ contributions / month</text>')
    parts.append('</g>')

    if monthly:
        plot_top = CHART_TOP + 64
        plot_bot = CHART_TOP + chart_h - 40
        plot_l, plot_r = chart_x + 24, chart_x + chart_w - 24
        slot = (plot_r - plot_l) / len(monthly)
        bar_w = slot * 0.62
        peak = max(m["total"] for m in monthly) or 1
        for i, m in enumerate(monthly):
            h = max(3, (plot_bot - plot_top) * m["total"] / peak)
            bx = plot_l + i * slot + (slot - bar_w) / 2
            fill = PEAK_BAR if m["total"] == peak else BAR
            delay = BAR_START + i * BAR_STAGGER
            parts.append(f'<rect class="b" x="{bx:.1f}" y="{plot_bot - h:.1f}" width="{bar_w:.1f}" height="{h:.1f}" '
                         f'rx="3" fill="{fill}" style="animation-delay:{delay:.2f}s"/>')
            mon = datetime.date.fromisoformat(m["month"] + "-01").strftime("%b")[0]
            parts.append(f'<text x="{bx + bar_w/2:.1f}" y="{plot_bot + 28}" fill="{MUTED}" font-size="18" '
                         f'text-anchor="middle">{mon}</text>')
            if m["total"] == peak:
                parts.append(f'<text class="t" style="animation-delay:{delay + BAR_DUR:.2f}s" x="{bx + bar_w/2:.1f}" '
                             f'y="{plot_bot - h - 10:.1f}" fill="{INK}" font-size="18" font-weight="700" text-anchor="middle">{peak:,}</text>')

    parts.append('</svg>')
    svg = "".join(parts)
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Success: wrote {OUT} ({len(svg)} bytes)")


if __name__ == "__main__":
    render()

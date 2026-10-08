#!/usr/bin/env python3
"""
Render the streak / numbers card as an elite Hyprland / glassmorphism terminal SVG:
- Glassmorphic chassis with gradient specular border and ambient backdrop
- 6 stat tiles with glass styling and colored status pill badges
- Multi-frame mechanical count-up easing
- Monthly contribution bar chart with benchmark gridline and glowing peak indicator
- Interactive CSS hover states
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

BG = "#060911"
BG2 = "#0e1526"
TILE = "#0f172a"
FRAME = "#1e293b"
MUTED = "#94a3b8"
INK = "#f8fafc"
GREEN = "#34d399"
BAR_COLOR = "#059669"
PEAK_COLOR = "#38bdf8"

W, H = 840, 880
PAD = 22
TITLEBAR_H = 38
COLS, ROWS = 2, 3
GAP = 16
TILE_W = (W - PAD * 2 - GAP * (COLS - 1)) / COLS
TILE_H = 148
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

    # (label, value, suffix, caption, accent, badge_text, badge_bg, badge_fg)
    tiles = [
        ("current streak", cur["length"], " days", span(cur), GREEN, "LIVE", "#064e3b", "#34d399"),
        ("longest streak", lng["length"], " days", span(lng), INK, "RECORD", "#312e81", "#818cf8"),
        ("contributions", total_contrib, "", "in the last year", INK, "ANNUAL", "#0c4a6e", "#38bdf8"),
        ("active days", active_days, f" / {n_days}", f"{(active_days / n_days) * 100:.0f}% of the year", INK, "CONSISTENCY", "#78350f", "#fbbf24"),
        ("best day", best["count"], "", short_date(best["date"]), INK, "PEAK", "#831843", "#f472b6"),
        ("avg / active day", avg_per_day, "", "contributions", INK, "RATE", "#134e4a", "#2dd4bf"),
    ]

    css = f"""
.t {{
  opacity: 0;
  animation: slideIn {SLIDE_DUR}s cubic-bezier(0.16, 1, 0.3, 1) both;
}}
.tile-glass {{
  transition: stroke 0.25s ease, filter 0.25s ease;
}}
.t:hover .tile-glass {{
  stroke: #38bdf8;
  stroke-width: 1.5;
  filter: drop-shadow(0 6px 16px rgba(56, 189, 248, 0.2));
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
  filter: brightness(1.3) drop-shadow(0 -3px 8px #34d399);
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
        f'<linearGradient id="glassBorder" x1="0" y1="0" x2="1" y2="1">',
        '<stop offset="0%" stop-color="#38bdf8" stop-opacity="0.6"/>',
        '<stop offset="50%" stop-color="#818cf8" stop-opacity="0.2"/>',
        '<stop offset="100%" stop-color="#38bdf8" stop-opacity="0.4"/>',
        '</linearGradient>',
        f'<linearGradient id="tileBorder" x1="0" y1="0" x2="1" y2="1">',
        '<stop offset="0%" stop-color="#38bdf8" stop-opacity="0.35"/>',
        '<stop offset="100%" stop-color="#1e293b" stop-opacity="0.8"/>',
        '</linearGradient>',
        f'<linearGradient id="peakbar" x1="0" y1="0" x2="0" y2="1">',
        '<stop offset="0%" stop-color="#38bdf8"/><stop offset="100%" stop-color="#0284c7"/>',
        '</linearGradient>',
        f'<linearGradient id="normbar" x1="0" y1="0" x2="0" y2="1">',
        f'<stop offset="0%" stop-color="#34d399"/><stop offset="100%" stop-color="{BAR_COLOR}"/>',
        '</linearGradient>',
        '</defs>',
        f'<rect width="{W}" height="{H}" rx="14" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="none" stroke="url(#glassBorder)" stroke-width="1.2"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity="0.9"/>',
    ]

    # Titlebar controls
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*18}" cy="{TITLEBAR_H/2}" r="5.5" fill="{dot}"/>')
    parts.append(
        f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
        f'font-weight="600" text-anchor="middle">satyanarayana@hyprland: ~$ ./stats.sh</text>'
    )
    # Top right runtime badges
    parts.append(
        f'<g transform="translate({W - PAD - 150}, {TITLEBAR_H/2 - 10})">'
        f'<rect width="70" height="20" rx="5" fill="#1e293b"/>'
        f'<text x="35" y="14" fill="#38bdf8" font-size="10" font-weight="700" text-anchor="middle">⎇ main</text>'
        f'<rect x="76" width="68" height="20" rx="5" fill="#1e293b"/>'
        f'<text x="110" y="14" fill="#34d399" font-size="10" font-weight="700" text-anchor="middle">● synced</text>'
        f'</g>'
    )

    # Stat tiles
    for i, (label, value, suffix, caption, accent, b_text, b_bg, b_fg) in enumerate(tiles):
        col, row = i % COLS, i // COLS
        x = PAD + col * (TILE_W + GAP)
        y = TILES_TOP + row * (TILE_H + GAP)
        start = i * TILE_STAGGER
        count_start = start + SLIDE_DUR * 0.55

        parts.append(f'<g class="t" style="animation-delay:{start:.2f}s">')
        parts.append(f'<rect class="tile-glass" x="{x:.1f}" y="{y}" width="{TILE_W:.1f}" height="{TILE_H}" rx="10" '
                     f'fill="{TILE}" stroke="url(#tileBorder)" stroke-width="1.1"/>')

        # Tile header with label and status pill badge
        parts.append(f'<text x="{x+20:.1f}" y="{y+36}" fill="{MUTED}" font-size="16" font-weight="600">$ {html.escape(label)}</text>')

        # Status badge pill
        bw = len(b_text) * 8 + 14
        bx = x + TILE_W - bw - 16
        parts.append(f'<rect x="{bx:.1f}" y="{y+20}" width="{bw}" height="19" rx="9" fill="{b_bg}"/>')
        parts.append(f'<text x="{bx + bw/2:.1f}" y="{y+33}" fill="{b_fg}" font-size="9.5" font-weight="700" text-anchor="middle">{b_text}</text>')

        # Metric value with mechanical easing
        num_y = y + 96
        for k in range(1, FRAMES + 1):
            p = k / FRAMES
            v = value * (1 - (1 - p) ** 3.5)
            t_on = count_start + COUNT_DUR * (k - 1) / FRAMES
            t_off = count_start + COUNT_DUR * k / FRAMES
            anim = f'<set attributeName="opacity" to="1" begin="{t_on:.3f}s"/>'
            if k < FRAMES:
                anim += f'<set attributeName="opacity" to="0" begin="{t_off:.3f}s"/>'
            parts.append(
                f'<text x="{x+20:.1f}" y="{num_y}" opacity="0" font-size="50" font-weight="700" fill="{accent}">'
                f'{fmt(v, value)}<tspan font-size="22" font-weight="400" fill="{MUTED}">{html.escape(suffix)}</tspan>'
                f'{anim}</text>'
            )
        parts.append(f'<text x="{x+20:.1f}" y="{y+128}" fill="{MUTED}" font-size="14">{html.escape(caption)}</text>')
        parts.append('</g>')

    # Monthly bar chart panel
    monthly = data.get("monthly", [])
    chart_x, chart_w = PAD, W - PAD * 2
    chart_h = H - PAD - CHART_TOP
    parts.append(f'<g class="t" style="animation-delay:{BAR_START - 0.25:.2f}s">')
    parts.append(f'<rect class="tile-glass" x="{chart_x}" y="{CHART_TOP}" width="{chart_w}" height="{chart_h}" rx="10" '
                 f'fill="{TILE}" stroke="url(#tileBorder)" stroke-width="1.1"/>')
    parts.append(f'<text x="{chart_x+20}" y="{CHART_TOP+34}" fill="{MUTED}" font-size="16" font-weight="600">$ contributions / month</text>')

    # Chart header badge
    cb_text = "MONTHLY ACTIVITY"
    cb_w = len(cb_text) * 7.5 + 14
    cb_x = chart_x + chart_w - cb_w - 18
    parts.append(f'<rect x="{cb_x:.1f}" y="{CHART_TOP+18}" width="{cb_w}" height="19" rx="9" fill="#0c4a6e"/>')
    parts.append(f'<text x="{cb_x + cb_w/2:.1f}" y="{CHART_TOP+31}" fill="#38bdf8" font-size="9.5" font-weight="700" text-anchor="middle">{cb_text}</text>')
    parts.append('</g>')

    if monthly:
        plot_top = CHART_TOP + 62
        plot_bot = CHART_TOP + chart_h - 38
        plot_l, plot_r = chart_x + 24, chart_x + chart_w - 24

        # Dotted baseline grid guide
        mid_y = (plot_top + plot_bot) / 2
        parts.append(f'<line x1="{plot_l}" y1="{mid_y:.1f}" x2="{plot_r}" y2="{mid_y:.1f}" stroke="{FRAME}" stroke-dasharray="3 4" stroke-opacity="0.6"/>')

        slot = (plot_r - plot_l) / len(monthly)
        bar_w = slot * 0.62
        peak = max(m["total"] for m in monthly) or 1
        for i, m in enumerate(monthly):
            h = max(4, (plot_bot - plot_top) * m["total"] / peak)
            bx = plot_l + i * slot + (slot - bar_w) / 2
            fill = "url(#peakbar)" if m["total"] == peak else "url(#normbar)"
            delay = BAR_START + i * BAR_STAGGER
            parts.append(f'<rect class="b" x="{bx:.1f}" y="{plot_bot - h:.1f}" width="{bar_w:.1f}" height="{h:.1f}" '
                         f'rx="4" fill="{fill}" style="animation-delay:{delay:.2f}s"/>')
            mon = datetime.date.fromisoformat(m["month"] + "-01").strftime("%b")[0]
            parts.append(f'<text x="{bx + bar_w/2:.1f}" y="{plot_bot + 24}" fill="{MUTED}" font-size="14" font-weight="600" '
                         f'text-anchor="middle">{mon}</text>')
            if m["total"] == peak:
                # Glowing peak badge
                parts.append(f'<g class="t" style="animation-delay:{delay + BAR_DUR:.2f}s">')
                parts.append(f'<rect x="{bx + bar_w/2 - 24:.1f}" y="{plot_bot - h - 22:.1f}" width="48" height="18" rx="4" fill="#0284c7"/>')
                parts.append(f'<text x="{bx + bar_w/2:.1f}" y="{plot_bot - h - 9:.1f}" fill="#ffffff" font-size="11" font-weight="700" text-anchor="middle">{peak:,}</text>')
                parts.append('</g>')

    parts.append('</svg>')
    svg = "".join(parts)
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Success: wrote {OUT} ({len(svg)} bytes)")


if __name__ == "__main__":
    render()

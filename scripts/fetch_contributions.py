#!/usr/bin/env python3
"""
Scrape daily contribution counts from GitHub's public contributions endpoint:
https://github.com/users/<username>/contributions
No token or authentication required.

Outputs data/contributions.json with raw days and derived statistics:
- total contributions
- active days
- average per active day
- current streak & longest streak
- best day
- monthly breakdown
"""

import datetime
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_PROFILE_USER", "yvvsatyanarayana-dev")
URL = f"https://github.com/users/{USERNAME}/contributions"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "..", "data", "contributions.json")


def fetch_days():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 profile-art-bot/1.0",
        "Accept": "text/html,application/xhtml+xml",
    }
    resp = requests.get(URL, headers=headers, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        # Fallback for SVG rects if GitHub ever toggles back to rects
        cells = soup.select("rect.ContributionCalendar-day")

    if not cells:
        print("Error: No calendar day elements found in HTML.", file=sys.stderr)
        sys.exit(1)

    days = []
    # Build tooltip lookup table for faster matching
    tooltips = {}
    for tt in soup.find_all("tool-tip"):
        for_id = tt.get("for")
        if for_id:
            tooltips[for_id] = tt.get_text(strip=True)

    for el in cells:
        date = el.get("data-date")
        if not date:
            continue
        el_id = el.get("id")
        text = tooltips.get(el_id, "")
        
        if not text:
            # Check for direct text or aria-label
            text = el.get("aria-label", "")

        if re.search(r"no contribution", text, re.I):
            count = 0
        else:
            match = re.search(r"(\d+)\s+contribution", text, re.I)
            if match:
                count = int(match.group(1))
            else:
                # Fallback to level heuristic if text parsing fails
                lvl = int(el.get("data-level") or 0)
                count = 1 if lvl > 0 else 0

        level = int(el.get("data-level") or 0)
        days.append({"date": date, "count": count, "level": level})

    days.sort(key=lambda d: d["date"])
    return days, soup


def compute_current_streak(days):
    if not days:
        return 0, None, None
    idx = len(days) - 1
    # If today has 0 contributions, look at yesterday so incomplete days don't prematurely break streaks
    if days[idx]["count"] == 0 and idx > 0:
        idx -= 1
    streak = 0
    end_idx = idx
    while idx >= 0 and days[idx]["count"] > 0:
        streak += 1
        idx -= 1
    start_idx = idx + 1
    if streak == 0:
        return 0, None, None
    return streak, days[start_idx]["date"], days[end_idx]["date"]


def compute_longest_streak(days):
    longest = run = 0
    longest_start = longest_end = None
    run_start_idx = None
    for i, d in enumerate(days):
        if d["count"] > 0:
            if run == 0:
                run_start_idx = i
            run += 1
            if run > longest:
                longest = run
                longest_start = days[run_start_idx]["date"]
                longest_end = days[i]["date"]
        else:
            run = 0
    return longest, longest_start, longest_end


def build_data(days, soup):
    # Try parsing total from header (e.g. '204 contributions in the last year')
    header_total = None
    desc_el = soup.find(id="js-contribution-activity-description")
    if desc_el:
        m = re.search(r"([\d,]+)\s+contribution", desc_el.get_text())
        if m:
            header_total = int(m.group(1).replace(",", ""))

    sum_total = sum(d["count"] for d in days)
    total = header_total if header_total is not None and header_total >= sum_total else sum_total
    active_days = sum(1 for d in days if d["count"] > 0)
    best = max(days, key=lambda d: d["count"]) if days else {"date": "", "count": 0}
    cur_len, cur_start, cur_end = compute_current_streak(days)
    long_len, long_start, long_end = compute_longest_streak(days)

    monthly = {}
    for d in days:
        key = d["date"][:7]
        monthly[key] = monthly.get(key, 0) + d["count"]
    monthly_list = [{"month": k, "total": v} for k, v in sorted(monthly.items())]

    return {
        "username": USERNAME,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]} if days else {"start": "", "end": ""},
        "total_contributions": total,
        "active_days": active_days,
        "avg_per_active_day": round(total / active_days, 1) if active_days else 0,
        "current_streak": {"length": cur_len, "start": cur_start, "end": cur_end},
        "longest_streak": {"length": long_len, "start": long_start, "end": long_end},
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly_list,
        "days": days,
    }


if __name__ == "__main__":
    days, soup = fetch_days()
    data = build_data(days, soup)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Success: wrote {OUT_PATH}")
    print(f"Total contributions: {data['total_contributions']}, "
          f"Current streak: {data['current_streak']['length']} days, "
          f"Longest streak: {data['longest_streak']['length']} days")

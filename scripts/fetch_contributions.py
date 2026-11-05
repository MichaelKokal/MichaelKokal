"""Download the public contribution calendar and save it as data/contributions.json.

GitHub serves the calendar shown on every profile page as plain HTML at
https://github.com/users/<username>/contributions, so no token is needed.
"""

import json
import re
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USER = "MichaelKokal"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"


def fetch_days():
    url = f"https://github.com/users/{USER}/contributions"
    res = requests.get(url, headers={"User-Agent": f"{USER}-profile-art"}, timeout=30)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # Each day's count lives in a <tool-tip for="<cell id>"> next to the cell.
    counts = {}
    for tip in soup.find_all("tool-tip"):
        m = re.match(r"\s*(\d[\d,]*) contributions?", tip.get_text())
        counts[tip.get("for")] = int(m.group(1).replace(",", "")) if m else 0

    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        days.append({
            "date": cell["data-date"],
            "count": counts.get(cell.get("id"), 0),
            "level": int(cell.get("data-level", 0)),
        })
    if not days:
        raise SystemExit("No contribution cells found; GitHub may have changed the page.")
    days.sort(key=lambda d: d["date"])
    return days


def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)

    # The current streak may still be alive if today simply has no commits yet.
    current = 0
    tail = list(reversed(days))
    if tail and tail[0]["count"] == 0:
        tail = tail[1:]
    for d in tail:
        if not d["count"]:
            break
        current += 1
    return current, longest


def main():
    days = fetch_days()
    current, longest = streaks(days)
    best = max(days, key=lambda d: d["count"])

    monthly = OrderedDict()
    for d in days:
        key = d["date"][:7]
        monthly[key] = monthly.get(key, 0) + d["count"]

    data = {
        "user": USER,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"from": days[0]["date"], "to": days[-1]["date"]},
        "total": sum(d["count"] for d in days),
        "active_days": sum(1 for d in days if d["count"]),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly,
        "days": days,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    print(f"{data['total']} contributions, {len(days)} days -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

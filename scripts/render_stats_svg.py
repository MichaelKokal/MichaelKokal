"""Draw contribution stats (big-number tiles plus a monthly bar chart) as stats-panel.svg.

Reads data/contributions.json, so run fetch_contributions.py first. Its size matches the
two GitHub stats cards stacked beside it in the README (each shown 350x175).
"""

import json
from datetime import date
from pathlib import Path

from svg_common import BRIGHT, GREEN, LABEL_H, MUTED, STATIC, esc, panel

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "stats-panel.svg"

WIDTH = 450
HEIGHT = 368
PAD = 16
GAP = 10
TILE_H = 50
BAR = "#26a641"
BAR_EMPTY = "#21262d"
TILE_BG = "#161b22"


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    height = HEIGHT
    best = data["best_day"]
    best_day = date.fromisoformat(best["date"])
    per_day = data["total"] / data["active_days"] if data["active_days"] else 0
    days = lambda n: "day" if n == 1 else "days"

    tiles = [
        ("current streak", data["current_streak"], days(data["current_streak"])),
        ("longest streak", data["longest_streak"], days(data["longest_streak"])),
        ("contributions", f'{data["total"]:,}', "last year"),
        ("active days", data["active_days"], "of 365"),
        ("best day", best["count"], f"{best_day:%b} {best_day.day}"),
        ("per active day", f"{per_day:.1f}", "avg"),
    ]

    parts = []
    n = 0

    def anim(delay):
        return "" if STATIC else f' style="animation-delay:{delay:.2f}s"'

    tile_w = (WIDTH - 2 * PAD - GAP) / 2
    top = LABEL_H + 4
    for i, (label, value, unit) in enumerate(tiles):
        col, row = i % 2, i // 2
        x = PAD + col * (tile_w + GAP)
        y = top + row * (TILE_H + 8)
        color = GREEN if i == 0 else BRIGHT
        value = esc(value)
        parts.append(
            f'<g class="t"{anim(0.25 + i * 0.1)}>'
            f'<rect x="{x:.1f}" y="{y}" width="{tile_w:.1f}" height="{TILE_H}" rx="6" fill="{TILE_BG}"/>'
            f'<text x="{x + 14:.1f}" y="{y + 17}" font-size="10" fill="{MUTED}">{esc(label)}</text>'
            f'<text x="{x + 14:.1f}" y="{y + 40}" xml:space="preserve">'
            f'<tspan font-size="22" font-weight="bold" fill="{color}">{value}</tspan>'
            f'<tspan font-size="11" fill="{MUTED}"> {esc(unit)}</tspan></text></g>'
        )
        n += 1

    # Monthly bar chart under the tiles.
    months = list(data["monthly"].items())[-13:]
    chart_top = top + 3 * (TILE_H + 8) + 12
    parts.append(f'<text x="{PAD}" y="{chart_top}" font-size="10" fill="{MUTED}">contributions per month</text>')
    base = height - 40
    bar_top = chart_top + 22
    span = base - bar_top
    pitch = (WIDTH - 2 * PAD) / len(months)
    bar_w = pitch * 0.62
    peak = max((v for _, v in months), default=0) or 1
    peak_key = max(months, key=lambda kv: kv[1])[0] if months else None
    for i, (key, value) in enumerate(months):
        x = PAD + i * pitch + (pitch - bar_w) / 2
        h = max(2.0, span * value / peak) if value else 2.0
        fill = GREEN if key == peak_key and value else (BAR if value else BAR_EMPTY)
        month = date.fromisoformat(key + "-01")
        tip = f"{value} contributions in {month:%B %Y}"
        parts.append(
            f'<rect class="b"{anim(0.9 + i * 0.06)} x="{x:.1f}" y="{base - h:.1f}" width="{bar_w:.1f}" '
            f'height="{h:.1f}" rx="2" fill="{fill}"><title>{tip}</title></rect>'
        )
        parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{base + 14}" font-size="9" fill="{MUTED}" '
                     f'text-anchor="middle">{month:%b}</text>')
        if key == peak_key and value:
            parts.append(f'<text class="t"{anim(0.9 + i * 0.06 + 0.4)} x="{x + bar_w / 2:.1f}" y="{base - h - 6:.1f}" '
                         f'font-size="10" font-weight="bold" fill="{GREEN}" text-anchor="middle">{value}</text>')

    style = "" if STATIC else """
.t { opacity: 0; animation: rise .45s ease-out forwards; }
.b { transform-box: fill-box; transform-origin: 50% 100%; transform: scaleY(0); animation: grow .6s cubic-bezier(.2,.7,.3,1) forwards; }
@keyframes rise { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
@keyframes grow { to { transform: scaleY(1); } }
"""
    svg = panel(WIDTH, height, "\n".join(parts), style, title="Contribution stats",
                tl="stats.json", tr="last 12 months", bl=f'updated {data["updated"][:10]}')
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT.name} ({WIDTH}x{height})")


if __name__ == "__main__":
    main()

"""Draw data/contributions.json as an animated 53-week contribution heatmap (contrib-heatmap.svg)."""

import json
from datetime import date
from pathlib import Path

from svg_common import GREEN, MUTED, STATIC, TEXT, panel

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

# none -> brightest; level 5 is a neon top end for the busiest days
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

WIDTH = 860
LEFT = 44        # room for the Mon / Wed / Fri labels
RIGHT = 16
PITCH = (WIDTH - LEFT - RIGHT) / 53
CELL = round(PITCH * 0.82, 2)
GRID_TOP = 34
HEIGHT = round(GRID_TOP + 7 * PITCH + 34)


def levels(days):
    """Bucket counts into 0..5 by where they fall among this year's active days."""
    active = sorted(d["count"] for d in days if d["count"])
    if not active:
        return {}

    def q(p):
        return active[min(len(active) - 1, int(p * len(active)))]

    cuts = [q(0.25), q(0.5), q(0.75), q(0.95)]
    return {d["date"]: 0 if not d["count"] else 1 + sum(d["count"] > c for c in cuts) for d in days}


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    days = data["days"]
    level = levels(days)
    offset = (date.fromisoformat(days[0]["date"]).weekday() + 1) % 7   # weeks start on Sunday

    cells, months = [], []
    last_month_col = -10
    for i, d in enumerate(days):
        day = date.fromisoformat(d["date"])
        col, row = divmod(i + offset, 7)
        x = LEFT + col * PITCH
        y = GRID_TOP + row * PITCH
        lvl = level.get(d["date"], 0)
        style = "" if STATIC else f' style="animation-delay:{(col + row) * 0.022:.3f}s"'
        tip = f'{d["count"]} contribution{"s" if d["count"] != 1 else ""} on {day:%b} {day.day}, {day.year}'
        glow = ' filter="url(#glow)"' if lvl >= 4 else ""
        cells.append(
            f'<rect class="c"{style}{glow} x="{x:.2f}" y="{y:.2f}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{PALETTE[lvl]}"><title>{tip}</title></rect>'
        )
        if (row == 0 and day.day <= 7) or (i == 0 and day.day <= 21):
            if col - last_month_col >= 3:
                months.append(f'<text x="{x:.2f}" y="{GRID_TOP - 9}" font-size="10" fill="{MUTED}">{day:%b}</text>')
                last_month_col = col

    weekdays = "".join(
        f'<text x="{LEFT - 8}" y="{GRID_TOP + r * PITCH + CELL - 2:.2f}" font-size="10" '
        f'text-anchor="end" fill="{MUTED}">{name}</text>'
        for r, name in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    )

    foot_y = GRID_TOP + 7 * PITCH + 20
    total = (f'<text x="{LEFT}" y="{foot_y:.2f}" font-size="11" fill="{MUTED}">'
             f'<tspan fill="{TEXT}" font-weight="bold">{data["total"]:,}</tspan> contributions in the last year</text>')
    sw = CELL * 0.85
    legend_x = WIDTH - RIGHT - 6 * (sw + 3) - 30
    legend = [f'<text x="{legend_x - 6:.2f}" y="{foot_y:.2f}" font-size="10" text-anchor="end" fill="{MUTED}">Less</text>']
    for n, color in enumerate(PALETTE):
        legend.append(f'<rect x="{legend_x + n * (sw + 3):.2f}" y="{foot_y - sw + 1:.2f}" width="{sw:.2f}" height="{sw:.2f}" rx="2" fill="{color}"/>')
    legend.append(f'<text x="{legend_x + 6 * (sw + 3) + 3:.2f}" y="{foot_y:.2f}" font-size="10" fill="{MUTED}">More</text>')

    style = "" if STATIC else """
.c { opacity: 0; animation: drop .45s cubic-bezier(.2,.7,.3,1) forwards; }
.f { opacity: 0; animation: fade .6s ease-out 1.4s forwards; }
@keyframes drop { from { opacity: 0; transform: translateY(-7px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fade { to { opacity: 1; } }
"""
    defs = (f'<defs><filter id="glow" x="-60%" y="-60%" width="220%" height="220%">'
            f'<feGaussianBlur stdDeviation="2.2" result="b"/>'
            f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
    body = "\n".join([defs, "".join(months), weekdays, "\n".join(cells), f'<g class="f">{total}{"".join(legend)}</g>'])
    OUT.write_text(panel(WIDTH, HEIGHT, body, style, title=f'{data["total"]:,} contributions in the last year'),
                   encoding="utf-8")
    print(f"wrote {OUT.name} ({data['total']} contributions)")


if __name__ == "__main__":
    main()

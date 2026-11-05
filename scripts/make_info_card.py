"""Write info-card.svg: a neofetch-style panel that prints itself line by line next to the portrait.

Edit LINES below when your details change, then run: python scripts/make_info_card.py
"""

import re
from pathlib import Path

from svg_common import BLUE, GREEN, MUTED, ORANGE, PURPLE, STATIC, TEXT, TITLE_H, esc, window

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"
PORTRAIT = ROOT / "ascii-portrait.svg"

WIDTH = 490
FONT_SIZE = 12.5
LINE_H = 18.5
X = 24
VALUE_X = X + 92

# (key, value). An empty key continues the line above; None draws a blank line.
LINES = [
    ("Now", "SWE Intern @ Mylon Education"),
    ("", "AI policy assistant · FastAPI · pgvector"),
    ("Prev", "Energy Systems Intern @ SYSERCO"),
    ("School", "UIC · B.S. Computer Science · Honors"),
    None,
    ("Stack", "Java · Spring Boot · PostgreSQL"),
    ("", "React · TypeScript · Python · Go"),
    ("Ships on", "GitHub Actions · Azure · Vercel"),
    None,
    ("Highlights", "› Chicago Sky Tracker"),
    ("", "  live flights, 260K+ positions a day"),
    ("", "› Recall: a Redis-compatible server in Go"),
    ("", "› Digital Footprint: 3D travel globe"),
    None,
    ("Open to", "backend & full-stack SWE roles"),
    ("Speaks", "English · Arabic · Spanish"),
    ("Off hours", "dabke · piano · chess · ping pong"),
    ("Web", "portfolio.michaelkokaly.com"),
]

PALETTE_BLOCKS = ["#484f58", "#ff7b72", GREEN, "#e3b341", BLUE, PURPLE, "#39c5cf", TEXT]


def target_height():
    """Match the portrait's on-screen height so both columns end at the same line."""
    m = PORTRAIT.exists() and re.search(r'width="(\d+)" height="(\d+)"', PORTRAIT.read_text(encoding="utf-8"))
    if not m:
        return 560
    return int(m.group(2))   # both panels are drawn at the size the README shows them


def main():
    height = target_height()
    out = []
    y = TITLE_H + 34

    def line(markup, extra=""):
        n = len(out)
        style = "" if STATIC else f' style="animation-delay:{0.35 + n * 0.11:.2f}s"'
        out.append(f'<g class="l"{style}>{markup}{extra}</g>')

    line(f'<text x="{X}" y="{y}" font-size="{FONT_SIZE}"><tspan fill="{GREEN}">$</tspan> '
         f'<tspan fill="{TEXT}">neofetch</tspan></text>')
    y += LINE_H + 6
    line(f'<text x="{X}" y="{y}" font-size="15" font-weight="bold"><tspan fill="{GREEN}">michael</tspan>'
         f'<tspan fill="{TEXT}">@</tspan><tspan fill="{GREEN}">github</tspan></text>')
    y += 10
    line(f'<rect x="{X}" y="{y}" width="{WIDTH - 2 * X}" height="1" fill="#30363d"/>')
    y += LINE_H + 2

    for item in LINES:
        if item is None:
            y += LINE_H * 0.55
            continue
        key, value = item
        key_markup = f'<tspan x="{X}" fill="{BLUE}" font-weight="bold">{esc(key)}</tspan>' if key else ""
        value = esc(value).replace("›", f'<tspan fill="{ORANGE}">›</tspan>')
        line(f'<text y="{y:.1f}" font-size="{FONT_SIZE}" xml:space="preserve">{key_markup}'
             f'<tspan x="{VALUE_X}" fill="{TEXT}">{value}</tspan></text>')
        y += LINE_H

    # Color blocks, like the bottom of real neofetch output.
    y = max(y + 8, height - 52)
    blocks = "".join(
        f'<rect x="{X + i * 26}" y="{y:.1f}" width="22" height="12" rx="2" fill="{c}"/>'
        for i, c in enumerate(PALETTE_BLOCKS)
    )
    line(blocks)
    if y + 34 > height:
        print(f"note: card content is {round(y + 34 - height)}px taller than the portrait; trim LINES to match")
        height = round(y + 34)

    style = "" if STATIC else """
.l { opacity: 0; animation: print .35s ease-out forwards; }
@keyframes print { from { opacity: 0; transform: translateX(-6px); } to { opacity: 1; transform: translateX(0); } }
"""
    OUT.write_text(window(WIDTH, height, "michael@github: ~", "\n".join(out), style), encoding="utf-8")
    print(f"wrote {OUT.name} ({WIDTH}x{height})")


if __name__ == "__main__":
    main()

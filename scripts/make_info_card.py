"""Write info-card.svg: a wide neofetch-style panel that prints itself line by line.

Edit LEFT and RIGHT below when your details change, then run: python scripts/make_info_card.py
"""

from pathlib import Path

from svg_common import BLUE, BORDER, GREEN, LABEL_H, ORANGE, PURPLE, STATIC, TEXT, esc, panel

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"

WIDTH = 860
FONT_SIZE = 12.5
LINE_H = 19
PAD = 24
KEY_W = 92
COL_X = (PAD, WIDTH // 2 + 8)

# (key, value). An empty key continues the line above; None draws a short gap.
LEFT = [
    ("Now", "SWE Intern @ Mylon Education"),
    ("", "AI policy assistant · FastAPI · pgvector"),
    ("Prev", "Energy Systems Intern @ SYSERCO"),
    ("School", "UIC · B.S. Computer Science · Honors"),
    None,
    ("Stack", "Java · Spring Boot · PostgreSQL"),
    ("", "React · TypeScript · Python · Go"),
    ("Ships on", "GitHub Actions · Azure · Vercel"),
]
RIGHT = [
    ("Highlights", "› Chicago Sky Tracker"),
    ("", "  live flights, 260K+ positions a day"),
    ("", "› Recall: a Redis-compatible server in Go"),
    ("", "› Digital Footprint: 3D travel globe"),
    None,
    ("Open to", "backend & full-stack SWE roles"),
    ("Speaks", "English · Arabic · Spanish"),
    ("Off hours", "dabke · piano · chess · ping pong"),
]

PALETTE_BLOCKS = ["#484f58", "#ff7b72", GREEN, "#e3b341", BLUE, PURPLE, "#39c5cf", TEXT]


def main():
    out = []

    def line(markup, order):
        style = "" if STATIC else f' style="animation-delay:{0.3 + order * 0.09:.2f}s"'
        out.append(f'<g class="l"{style}>{markup}</g>')

    y = LABEL_H + 22
    line(f'<text x="{PAD}" y="{y}" font-size="15" font-weight="bold"><tspan fill="{GREEN}">michael</tspan>'
         f'<tspan fill="{TEXT}">@</tspan><tspan fill="{GREEN}">github</tspan>'
         f'<tspan fill="{TEXT}" font-weight="normal" font-size="12.5">  ·  portfolio.michaelkokaly.com</tspan></text>', 0)
    y += 12
    line(f'<rect x="{PAD}" y="{y}" width="{WIDTH - 2 * PAD}" height="1" fill="{BORDER}"/>', 1)
    y0 = y + LINE_H + 4

    bottom = y0
    for c, items in enumerate((LEFT, RIGHT)):
        x, y = COL_X[c], y0
        for row, item in enumerate(items):
            if item is None:
                y += LINE_H * 0.5
                continue
            key, value = item
            key_markup = f'<tspan x="{x}" fill="{BLUE}" font-weight="bold">{esc(key)}</tspan>' if key else ""
            value = esc(value).replace("›", f'<tspan fill="{ORANGE}">›</tspan>')
            line(f'<text y="{y:.1f}" font-size="{FONT_SIZE}" xml:space="preserve">{key_markup}'
                 f'<tspan x="{x + KEY_W}" fill="{TEXT}">{value}</tspan></text>', 2 + row)
            y += LINE_H
        bottom = max(bottom, y)

    # Color blocks, like the bottom of real neofetch output.
    y = bottom + 6
    line("".join(f'<rect x="{PAD + i * 26}" y="{y:.1f}" width="22" height="10" rx="2" fill="{c}"/>'
                 for i, c in enumerate(PALETTE_BLOCKS)), 2 + max(len(LEFT), len(RIGHT)))
    height = round(y + 32)

    style = "" if STATIC else """
.l { opacity: 0; animation: print .35s ease-out forwards; }
@keyframes print { from { opacity: 0; transform: translateX(-6px); } to { opacity: 1; transform: translateX(0); } }
"""
    svg = panel(WIDTH, height, "\n".join(out), style, title="About Michael Kokaly", tl="neofetch", tr="~/.profile")
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT.name} ({WIDTH}x{height})")


if __name__ == "__main__":
    main()

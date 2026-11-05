"""Turn the badge rows in data/tech-stack.md into tech-stack.svg, where the badges print in one by one.

GitHub can't animate the shields.io badge images in a README directly, so this downloads each
badge once and embeds it in a single SVG with the same row labels and order.
Run locally after editing data/tech-stack.md: python scripts/make_tech_stack.py
"""

import base64
import re
from pathlib import Path
from xml.sax.saxutils import escape

import requests
from PIL import ImageFont

from svg_common import STATIC

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "tech-stack.md"
OUT = ROOT / "tech-stack.svg"

WIDTH = 860
ROW_H = 34          # distance between rows
BADGE_H = 18        # shields.io badges are 18px tall
GAP = 5             # space between badges
LABEL_SIZE = 16
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"

# Used only to measure label widths, so the badges start right after each label.
try:
    MEASURE = ImageFont.truetype("segoeuib.ttf", LABEL_SIZE)
except OSError:
    MEASURE = ImageFont.load_default()


def parse_rows():
    rows = []
    for line in SRC.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\*\*(.+?)\*\*", line)
        if m:
            rows.append((m.group(1), re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", line)))
    return rows


def fetch_badge(url):
    svg = requests.get(url, timeout=30, headers={"User-Agent": "profile-tech-stack"}).text
    w, h = re.search(r'<svg[^>]*\bwidth="([\d.]+)"[^>]*\bheight="([\d.]+)"', svg).groups()
    return float(w), float(h), "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def main():
    parts, order = [], 0
    y = 6
    for label, badges in parse_rows():
        label_w = MEASURE.getlength(label) + 8
        x = label_w
        delay = lambda: "" if STATIC else f' style="animation-delay:{0.2 + order * 0.06:.2f}s"'
        parts.append(f'<g class="l"{delay()}><text x="0" y="{y + BADGE_H - 4}" class="label">{escape(label)}</text></g>')
        order += 1
        for alt, url in badges:
            w, h, data = fetch_badge(url)
            w *= BADGE_H / h
            if x + w > WIDTH:                      # wrap onto a new line, like the README did
                x, y = label_w, y + ROW_H - 8
            parts.append(f'<g class="l"{delay()}><image x="{x:.1f}" y="{y}" width="{w:.1f}" height="{BADGE_H}" '
                         f'href="{data}"><title>{escape(alt)}</title></image></g>')
            order += 1
            x += w + GAP
        y += ROW_H
    height = y - ROW_H + BADGE_H + 8

    animation = "" if STATIC else """
.l { opacity: 0; animation: print .35s ease-out forwards; }
@keyframes print { from { opacity: 0; transform: translateX(-6px); } to { opacity: 1; transform: translateX(0); } }"""
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" aria-label="Tech stack">
<title>Tech stack</title>
<style>
.label {{ font: 600 {LABEL_SIZE}px {FONT}; fill: #1f2328; }}
@media (prefers-color-scheme: dark) {{ .label {{ fill: #e6edf3; }} }}{animation}
</style>
{chr(10).join(parts)}
</svg>
"""
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT.name} ({order} items, {WIDTH}x{height})")


if __name__ == "__main__":
    main()

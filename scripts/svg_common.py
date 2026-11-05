"""Small helpers shared by the SVG generators: colors, fonts and the terminal window frame."""

import os
from xml.sax.saxutils import escape

# Set STATIC=1 to write a frozen final frame (handy for quick local previews).
STATIC = os.environ.get("STATIC") == "1"

FONT = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

BG = "#0d1117"
BORDER = "#30363d"
TITLE_BG = "#161b22"
TEXT = "#c9d1d9"
MUTED = "#8b949e"
GREEN = "#39d353"
BLUE = "#58a6ff"
PURPLE = "#d2a8ff"
ORANGE = "#ffa657"

TITLE_H = 30


def esc(text):
    return escape(str(text))


def window(width, height, title, body, style=""):
    """Wrap SVG body markup in a dark terminal window with traffic-light dots."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">
<title>{esc(title)}</title>
<style>
text {{ font-family: {FONT}; }}
{style}
</style>
<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>
<path d="M0.5 {TITLE_H} V10.5 A10 10 0 0 1 10.5 0.5 H{width - 10.5} A10 10 0 0 1 {width - 0.5} 10.5 V{TITLE_H} Z" fill="{TITLE_BG}"/>
<line x1="0.5" y1="{TITLE_H}" x2="{width - 0.5}" y2="{TITLE_H}" stroke="{BORDER}"/>
<circle cx="18" cy="{TITLE_H / 2}" r="5.5" fill="#ff5f56"/>
<circle cx="36" cy="{TITLE_H / 2}" r="5.5" fill="#ffbd2e"/>
<circle cx="54" cy="{TITLE_H / 2}" r="5.5" fill="#27c93f"/>
<text x="{width / 2}" y="{TITLE_H / 2 + 4}" text-anchor="middle" font-size="12" fill="{MUTED}">{esc(title)}</text>
{body}
</svg>
"""

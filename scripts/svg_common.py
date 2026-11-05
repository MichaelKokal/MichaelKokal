"""Small helpers shared by the SVG generators: colors, fonts and the panel frame."""

import os
from xml.sax.saxutils import escape

# Set STATIC=1 to write a frozen final frame (handy for quick local previews).
STATIC = os.environ.get("STATIC") == "1"

FONT = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

BG = "#0d1117"
BORDER = "#30363d"
TEXT = "#c9d1d9"
BRIGHT = "#f0f6fc"
MUTED = "#8b949e"
DIM = "#6e7681"
GREEN = "#39d353"
BLUE = "#58a6ff"
PURPLE = "#d2a8ff"
ORANGE = "#ffa657"

LABEL_H = 26   # room at the top of a panel for its corner labels


def esc(text):
    return escape(str(text))


def panel(width, height, body, style="", title="", tl="", tr="", bl="", br=""):
    """A dark rounded panel with optional small labels in its four corners."""
    def label(x, y, text, anchor):
        if not text:
            return ""
        return f'<text x="{x}" y="{y}" font-size="10" fill="{DIM}" text-anchor="{anchor}">{esc(text)}</text>'

    labels = "".join([
        label(14, 17, tl, "start"), label(width - 14, 17, tr, "end"),
        label(14, height - 10, bl, "start"), label(width - 14, height - 10, br, "end"),
    ])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">
<title>{esc(title)}</title>
<style>
text {{ font-family: {FONT}; }}
{style}
</style>
<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8" fill="{BG}" stroke="{BORDER}"/>
{labels}
{body}
</svg>
"""

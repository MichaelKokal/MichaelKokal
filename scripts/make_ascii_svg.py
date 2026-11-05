"""Turn portrait/prepped.png into one-color ASCII art that types itself in, row by row (ascii-portrait.svg)."""

from pathlib import Path

import numpy as np
from PIL import Image

from svg_common import STATIC, TEXT, TITLE_H, esc, window

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "portrait" / "prepped.png"
OUT = ROOT / "ascii-portrait.svg"

RAMP = " .`:-=+*cs#%@"   # bright (sparse) -> dark (dense)
#       ^ leading space clears the background to nothing

# Drawn at the size the README shows it (370px wide), so the window frame matches the other panels.
COLS = 100
PAD = 15
CHAR_W = (370 - 2 * PAD) / COLS   # width of one character cell
LINE_H = CHAR_W / 0.6             # height of one row (monospace glyphs are ~0.6 as wide as tall)
FONT_SIZE = LINE_H
GAMMA = 1.6          # >1 darkens mid-tones so the face stands out from the sweater
CROP_WIDTH = 0.78    # share of the body width to keep
CROP_ASPECT = 1.22   # crop height / width


def to_rows(img):
    la = np.array(img.convert("LA")).astype(np.float32) / 255.0
    gray, mask = la[..., 0], la[..., 1]

    # Crop to head and shoulders, centered on the head, so the face gets plenty of characters.
    ys, xs = np.where(mask > 0.5)
    y0, x0, x1 = ys.min(), xs.min(), xs.max()
    head_x = xs[ys < y0 + 0.25 * (ys.max() - y0)].mean()
    cw = CROP_WIDTH * (x1 - x0)
    top = max(0, int(y0 - 0.04 * cw))
    left = max(0, int(head_x - cw / 2))
    crop = (slice(top, top + int(cw * CROP_ASPECT)), slice(left, left + int(cw)))
    gray, mask = gray[crop], mask[crop]

    h, w = gray.shape
    rows = round(COLS * (h / w) * (CHAR_W / LINE_H))

    def shrink(a):
        return np.array(Image.fromarray((a * 255).astype(np.uint8)).resize((COLS, rows), Image.LANCZOS)) / 255.0

    v, subject = shrink(gray), shrink(mask) > 0.5

    # Stretch the subject's tones to the full range so the ramp gets used end to end.
    lo, hi = np.percentile(v[subject], 2), np.percentile(v[subject], 98)
    v = np.clip((v - lo) / max(hi - lo, 1e-3), 0, 1) ** GAMMA

    # Light glyphs on a dark panel: denser characters read as brighter, so bright
    # skin gets dense glyphs. Every subject cell gets at least a dot; background is blank.
    idx = np.where(subject, 1 + np.round(v * (len(RAMP) - 2)).astype(int), 0)
    return ["".join(RAMP[i] for i in line).rstrip() for line in idx]


def main():
    rows = to_rows(Image.open(SRC))
    width = round(COLS * CHAR_W + 2 * PAD)
    height = round(TITLE_H + PAD + len(rows) * LINE_H + PAD)

    defs, parts = [], []
    t = 0.3
    for i, row in enumerate(rows):
        if not row.strip():
            continue
        y = TITLE_H + PAD + i * LINE_H
        start = len(row) - len(row.lstrip())
        x0 = PAD + start * CHAR_W
        w = (len(row) - start) * CHAR_W
        text = (f'<text x="{PAD}" y="{y + LINE_H * 0.8:.2f}" textLength="{len(row) * CHAR_W:.2f}" '
                f'lengthAdjust="spacingAndGlyphs" xml:space="preserve"{{clip}}>{esc(row)}</text>')
        if STATIC:
            parts.append(text.format(clip=""))
            continue

        dur = 0.1 + w / 1400
        defs.append(
            f'<clipPath id="r{i}"><rect x="{x0:.2f}" y="{y:.2f}" width="0" height="{LINE_H:.2f}">'
            f'<animate attributeName="width" from="0" to="{w:.1f}" begin="{t:.3f}s" dur="{dur:.3f}s" fill="freeze"/>'
            f'</rect></clipPath>'
        )
        parts.append(text.format(clip=f' clip-path="url(#r{i})"'))
        # A small block cursor rides the edge of the wipe, then disappears.
        parts.append(
            f'<rect x="{x0:.2f}" y="{y + 0.5:.2f}" width="{CHAR_W:.2f}" height="{LINE_H - 1:.2f}" fill="{TEXT}" opacity="0">'
            f'<animate attributeName="x" from="{x0:.1f}" to="{x0 + w:.1f}" begin="{t:.3f}s" dur="{dur:.3f}s"/>'
            f'<set attributeName="opacity" to="0.85" begin="{t:.3f}s" dur="{dur:.3f}s"/></rect>'
        )
        t += 0.05

    body = f'<defs>{"".join(defs)}</defs>\n<g font-size="{FONT_SIZE:.2f}" fill="{TEXT}">\n' + "\n".join(parts) + "\n</g>"
    OUT.write_text(window(width, height, "michael@github: ~/portrait", body), encoding="utf-8")
    print(f"wrote {OUT.name} ({COLS}x{len(rows)} characters, {width}x{height}, types in over {t:.1f}s)")


if __name__ == "__main__":
    main()

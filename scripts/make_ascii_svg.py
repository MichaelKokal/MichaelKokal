"""Turn portrait/prepped.png into one-color ASCII line art that types itself in, row by row (ascii-portrait.svg).

Dark parts of the photo (hair, glasses, shadows) become dense characters, bright skin is left
blank, and detected edges are drawn on top so the outline of the face reads like a sketch.
"""

from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from svg_common import LABEL_H, STATIC, TEXT, esc, panel

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "portrait" / "prepped.png"
OUT = ROOT / "ascii-portrait.svg"

RAMP = " .`:-=+*cs#%@"   # bright (sparse) -> dark (dense)
#       ^ leading space clears the background to nothing

# Drawn at the size the README shows it (370px wide).
WIDTH = 370
COLS = 96
PAD = 15
CHAR_W = (WIDTH - 2 * PAD) / COLS   # width of one character cell
LINE_H = CHAR_W / 0.6               # monospace glyphs are ~0.6 as wide as tall
FONT_SIZE = LINE_H

GAMMA = 1.6          # >1 pushes light tones (skin) toward blank, keeping only the darks
EDGE = 0.8           # how strongly edges are drawn (0..1 on the ramp)
TONE = 0.6           # how much the shading itself counts; lower = more like a line drawing
EDGE_BLUR = 3.5      # smoothing before edge detection; higher = only bold outlines
EDGE_THRESHOLDS = (35, 90)
EDGE_CUTOFF = 0.1    # share of a character cell an edge must cover to be drawn
CROP_WIDTH = 0.74    # share of the body width to keep
CROP_ASPECT = 1.12   # crop height / width

# The face gets its own, finer treatment so small features like the eyes survive.
# FACE_BOX is (left, top, right, bottom) in pixels of portrait/source.png;
# update it if you swap the photo (or set it to None to skip this step).
FACE_BOX = (128, 86, 188, 162)
FACE_SHARPEN = 1.0   # extra local contrast inside the face
FACE_TONE = 0.45     # shading weight inside the face (vs TONE elsewhere); low keeps skin clean
FACE_VALLEY_SIZE = 3.0   # how wide an area a feature is compared against, in photo pixels
FACE_VALLEY_MIN = 10     # how much darker than its surroundings a spot must be to be drawn
FACE_LINE = 1.0          # how strongly those features are drawn (0..1 on the ramp)


def face_weight(shape):
    """1.0 inside FACE_BOX, fading to 0 just outside it, so the two treatments blend smoothly."""
    weight = np.zeros(shape, np.float32)
    if FACE_BOX:
        x0, y0, x1, y1 = FACE_BOX
        weight[y0:y1, x0:x1] = 1.0
        k = max(3, (x1 - x0) // 6) | 1
        weight = cv2.GaussianBlur(weight, (k, k), 0)
    return weight


def to_rows(img):
    la = np.array(img.convert("LA"))
    gray8, mask8 = la[..., 0], la[..., 1]
    face = face_weight(gray8.shape)

    # Sharpen the face so eyes, brows and the smile line stand out from the skin.
    g = gray8.astype(np.float32)
    sharp = np.clip(g + FACE_SHARPEN * (g - cv2.GaussianBlur(g, (0, 0), 1.6)), 0, 255)
    gray8 = (g * (1 - face) + sharp * face).astype(np.uint8)

    # Crop to head and shoulders, centered on the head.
    ys, xs = np.where(mask8 > 127)
    y0, x0, x1 = ys.min(), xs.min(), xs.max()
    head_x = xs[ys < y0 + 0.25 * (ys.max() - y0)].mean()
    cw = CROP_WIDTH * (x1 - x0)
    top = max(0, int(y0 - 0.05 * cw))
    left = max(0, int(head_x - cw / 2))
    crop = (slice(top, top + int(cw * CROP_ASPECT)), slice(left, left + int(cw)))
    gray8, mask8 = np.ascontiguousarray(gray8[crop]), np.ascontiguousarray(mask8[crop])
    face = np.ascontiguousarray(face[crop])

    # Edges of facial features plus the silhouette. The heavy smoothing flattens fine texture
    # (sweater knit, hair strands) so only real outlines survive; inside the face a much
    # lighter smoothing keeps small features like the eyes.
    big = cv2.resize(gray8, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    smooth = cv2.GaussianBlur(cv2.bilateralFilter(big, 9, 50, 9), (0, 0), EDGE_BLUR)
    edges = cv2.Canny(smooth, *EDGE_THRESHOLDS)
    edges |= cv2.Canny(cv2.resize(mask8, big.shape[::-1]), 50, 150)
    # Inside the face, draw "valleys": spots clearly darker than their surroundings, which is
    # what eyes, brows, nostrils and the smile line are (skin texture is too faint to count).
    gf = gray8.astype(np.float32)
    valley = np.clip((cv2.GaussianBlur(gf, (0, 0), FACE_VALLEY_SIZE) - gf - FACE_VALLEY_MIN) / 40, 0, 1) * face

    h, w = gray8.shape
    rows = round(COLS * (h / w) * (CHAR_W / LINE_H))
    size = (COLS, rows)
    v = cv2.resize(gray8, size, interpolation=cv2.INTER_AREA) / 255.0
    subject = cv2.resize(mask8, size, interpolation=cv2.INTER_AREA) > 127
    e = cv2.resize(edges, size, interpolation=cv2.INTER_AREA) / 255.0
    f = cv2.resize(face, size, interpolation=cv2.INTER_AREA)
    lines = cv2.resize(valley, size, interpolation=cv2.INTER_AREA)

    # Stretch the subject's tones to the full range, then turn brightness into "ink".
    lo, hi = np.percentile(v[subject], 2), np.percentile(v[subject], 98)
    tone = TONE * (1 - f) + FACE_TONE * f
    ink = tone * (1 - np.clip((v - lo) / max(hi - lo, 1e-3), 0, 1)) ** GAMMA
    ink = np.where(e > EDGE_CUTOFF, np.maximum(ink, EDGE), ink)
    ink = np.maximum(ink, lines * FACE_LINE)

    idx = np.where(subject, np.round(ink * (len(RAMP) - 1)).astype(int), 0)
    return ["".join(RAMP[i] for i in line).rstrip() for line in idx]


def main():
    rows = to_rows(Image.open(SRC))
    height = round(LABEL_H + 6 + len(rows) * LINE_H + 24)

    defs, parts = [], []
    t = 0.3
    for i, row in enumerate(rows):
        if not row.strip():
            continue
        y = LABEL_H + 6 + i * LINE_H
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

    body = (f'<defs>{"".join(defs)}</defs>\n<g font-size="{FONT_SIZE:.2f}" fill="{TEXT}">\n'
            + "\n".join(parts) + "\n</g>")
    svg = panel(WIDTH, height, body, title="ASCII portrait of Michael Kokaly",
                tl="portrait.txt", tr=f"{COLS}x{len(rows)}", bl="michael@github ~ $ cat portrait.txt")
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT.name} ({COLS}x{len(rows)} characters, {WIDTH}x{height}, types in over {t:.1f}s)")


if __name__ == "__main__":
    main()

"""Get a photo ready for ASCII conversion.

1. Cut out the background so only the person is left.
2. Boost local contrast (CLAHE) so a flatly lit face gets real highlights and shadows.
3. Put the result on pure white (keeping the cut-out mask as transparency), so the
   background turns into blank space in the ASCII art.

Usage: python scripts/prep_photo.py portrait/source.png   ->   portrait/prepped.png
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def main():
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "portrait/source.png")
    out = src.with_name("prepped.png")

    cutout = remove(Image.open(src).convert("RGB"))          # RGBA, background transparent
    rgba = np.array(cutout).astype(np.float32) / 255.0
    rgb, alpha = rgba[..., :3], rgba[..., 3:4]

    gray = cv2.cvtColor((rgb * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray).astype(np.float32) / 255.0

    # Composite onto white using the cut-out mask, and keep the mask as the alpha
    # channel so the ASCII step can tell background apart from white clothing.
    a = alpha[..., 0]
    final = gray * a + 1.0 * (1 - a)
    pixels = np.dstack([final, a]) * 255
    Image.fromarray(pixels.clip(0, 255).astype(np.uint8), "LA").save(out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

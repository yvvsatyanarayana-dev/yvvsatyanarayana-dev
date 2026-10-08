#!/usr/bin/env python3
"""
Prepare a portrait photo for clean ASCII conversion:
1. Isolate the subject / remove background (rembg if available, or high-contrast thresholding).
2. Smooth out noisy texture while keeping sharp edge definition.
3. Enhance local contrast (CLAHE with OpenCV if available, or PIL contrast stretching).
4. Composite onto clean pure white (so background maps cleanly to spaces in ASCII ramp).
5. Output square grayscale source-prepped.png.

Usage:
    python scripts/prep_photo.py [input_image] [output_image]
"""

import importlib
import os
import sys
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))

# Find default input file
default_inputs = ["iam.jpg", "iam.jpeg", "iam.png", "IAM.jpeg", "source-photo.jpg", "source-photo.png", "source-photo.jpeg"]
input_file = None
if len(sys.argv) > 1:
    input_file = sys.argv[1]
else:
    for name in default_inputs:
        candidate = os.path.join(HERE, "..", name)
        if os.path.exists(candidate):
            input_file = candidate
            break
    if not input_file:
        input_file = os.path.join(HERE, "..", "source-photo.jpg")

OUT_PATH = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")


def prep_with_advanced_libraries(inp_path, out_path):
    # Dynamically import optional image segmentation dependencies
    cv2 = importlib.import_module("cv2")
    rembg_mod = importlib.import_module("rembg")
    remove = getattr(rembg_mod, "remove")

    img = Image.open(inp_path).convert("RGBA")
    cut = remove(img)
    rgb = np.array(cut.convert("RGB"))
    alpha = np.array(cut.split()[-1])  # 0 = background
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    # 1. Bilateral smoothing to remove noise while keeping edges sharp
    smooth = gray
    for _ in range(3):
        smooth = cv2.bilateralFilter(smooth, 9, 40, 9)

    # 2. Tone stretch
    foreground_mask = alpha > 64
    if np.any(foreground_mask):
        lo, hi = np.percentile(smooth[foreground_mask], [2, 92])
        if hi > lo:
            tone = np.clip((smooth.astype(np.float32) - lo) / (hi - lo), 0, 1)
        else:
            tone = smooth.astype(np.float32) / 255.0
    else:
        tone = smooth.astype(np.float32) / 255.0

    # 3. Enhance line ridges (difference of Gaussians)
    fine = cv2.GaussianBlur(smooth, (0, 0), 1.5).astype(np.float32)
    coarse = cv2.GaussianBlur(smooth, (0, 0), 6.0).astype(np.float32)
    lines = np.clip((coarse - fine) / 40.0, 0, 1)
    out = np.clip(tone - 0.5 * lines, 0, 1) * 255.0

    # 4. Composite onto white
    mask = cv2.GaussianBlur(alpha.astype(np.float32) / 255.0, (0, 0), 1.0)
    out = out * mask + 255.0 * (1.0 - mask)

    # 5. Crop square
    ys, xs = np.where(alpha > 20)
    if len(xs) > 0 and len(ys) > 0:
        side = max(xs.max() - xs.min(), ys.max() - ys.min()) + 40
        cx, cy = (xs.min() + xs.max()) // 2, (ys.min() + ys.max()) // 2
        canvas = np.full((side, side), 255, np.uint8)
        x0, y0 = cx - side // 2, cy - side // 2
        sx0, sy0 = max(x0, 0), max(y0, 0)
        sx1, sy1 = min(x0 + side, out.shape[1]), min(y0 + side, out.shape[0])
        canvas[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = out[sy0:sy1, sx0:sx1].astype(np.uint8)
        final_img = Image.fromarray(canvas, mode="L")
    else:
        final_img = Image.fromarray(out.astype(np.uint8), mode="L")

    final_img.save(out_path)
    print(f"Prepped using rembg/OpenCV: {out_path} ({final_img.size})")


def prep_with_pil_fallback(inp_path, out_path):
    """Fallback when rembg or opencv is not installed."""
    img = Image.open(inp_path).convert("RGB")
    # Make square
    w, h = img.size
    min_dim = min(w, h)
    left = (w - min_dim) // 2
    top = (h - min_dim) // 2
    img = img.crop((left, top, left + min_dim, top + min_dim))

    # Convert to grayscale
    gray = ImageOps.grayscale(img)
    # Autocontrast and enhance
    enhanced = ImageOps.autocontrast(gray, cutoff=2)
    enhancer = ImageEnhance.Contrast(enhanced)
    enhanced = enhancer.enhance(1.4)
    enhanced = ImageEnhance.Sharpness(enhanced).enhance(1.3)

    enhanced.save(out_path)
    print(f"Prepped using PIL fallback: {out_path} ({enhanced.size})")


def main():
    if not os.path.exists(input_file):
        print(f"Error: Input photo {input_file} not found.", file=sys.stderr)
        print("Please place your photo as 'source-photo.jpg' or 'source-photo.png' in the repo root.", file=sys.stderr)
        sys.exit(1)

    try:
        prep_with_advanced_libraries(input_file, OUT_PATH)
    except ImportError:
        print("Note: rembg/opencv not found in current environment. Using high-quality PIL processing.")
        prep_with_pil_fallback(input_file, OUT_PATH)


if __name__ == "__main__":
    main()

from PIL import Image
import numpy as np

from skimage.filters import threshold_otsu, gaussian
from skimage.measure import find_contours

from skimage.morphology import (
    remove_small_objects,
    closing,
    opening,
    disk
)

import time

# =========================================================
# CONFIG
# =========================================================

INPUT_PNG = "Imagen.png"
OUTPUT_SVG = "Vector.svg"

# =========================================================
# MAXIMUM QUALITY SETTINGS
# =========================================================

# Internal upscale factor
# Higher = sharper edges but MUCH heavier processing
UPSCALE = 8

# Contour simplification
# Lower = more detail
# For maximum detail use 0.3 - 0.8
EPSILON = 0.00001

# Gaussian smoothing
# Lower = sharper
# Higher = smoother
GAUSSIAN_SIGMA = 0.99

# Remove tiny artifacts
MIN_OBJECT_SIZE = 8

# SVG fill color
FILL_COLOR = "#2f2f2f"

# Decimal precision in SVG
SVG_PRECISION = 8

# Minimum contour size
MIN_CONTOUR_POINTS = 50

# =========================================================


def rdp(points, epsilon):
    """
    Ramer-Douglas-Peucker simplification
    """

    if len(points) < 3:
        return points

    start = points[0]
    end = points[-1]

    line = end - start
    line_len = np.hypot(line[0], line[1])

    if line_len == 0:
        dists = np.hypot(*(points - start).T)

    else:
        v = points - start

        cross = np.abs(
            v[:, 0] * line[1] -
            v[:, 1] * line[0]
        )

        dists = cross / line_len

    idx = int(np.argmax(dists))
    dmax = float(dists[idx])

    if dmax > epsilon:

        left = rdp(points[: idx + 1], epsilon)
        right = rdp(points[idx:], epsilon)

        return np.vstack((left[:-1], right))

    return np.vstack((start, end))


def fmt(x):
    return (
        f"{x:.{SVG_PRECISION}f}"
    ).rstrip("0").rstrip(".")


# =========================================================
# LOAD IMAGE
# =========================================================

start_time = time.perf_counter()

img = Image.open(INPUT_PNG).convert("RGBA")

original_w, original_h = img.size

print(f"Original size: {original_w}x{original_h}")

# =========================================================
# HIGH QUALITY UPSCALE
# =========================================================

upscaled_w = original_w * UPSCALE
upscaled_h = original_h * UPSCALE

img = img.resize(
    (upscaled_w, upscaled_h),
    Image.LANCZOS
)

print(f"Upscaled size: {upscaled_w}x{upscaled_h}")

# =========================================================
# TO NUMPY
# =========================================================

arr = np.array(img)

# =========================================================
# ALPHA COMPOSITE
# =========================================================

alpha = arr[..., 3] / 255.0

rgb = arr[..., :3].astype(np.float32)

# Composite over white background
rgb_comp = (
    rgb * alpha[..., None] +
    255 * (1 - alpha[..., None])
)

# =========================================================
# LUMINANCE
# =========================================================

lum = (
    0.2126 * rgb_comp[..., 0] +
    0.7152 * rgb_comp[..., 1] +
    0.0722 * rgb_comp[..., 2]
)

# =========================================================
# HIGH QUALITY SMOOTHING
# =========================================================

lum = gaussian(
    lum,
    sigma=GAUSSIAN_SIGMA,
    preserve_range=True
)

# =========================================================
# OTSU THRESHOLD
# =========================================================

th = threshold_otsu(lum)

mask_dark = lum < th
mask_light = lum > th

# Auto foreground detection
mask = (
    mask_dark
    if mask_dark.sum() < mask_light.sum()
    else mask_light
)

# =========================================================
# MORPHOLOGICAL CLEANUP
# =========================================================

mask = remove_small_objects(
    mask,
    max_size=MIN_OBJECT_SIZE - 1
)

mask = closing(mask, disk(2))
mask = opening(mask, disk(1))

# =========================================================
# IMAGE SIZE
# =========================================================

h, w = mask.shape

# =========================================================
# PADDING
# =========================================================

pad = 6

mask_p = np.pad(
    mask.astype(np.uint8),
    pad,
    mode="constant",
    constant_values=0
)

# =========================================================
# FIND CONTOURS
# =========================================================

contours = find_contours(mask_p, 0.5)

print(f"Contours found: {len(contours)}")

# =========================================================
# SIMPLIFY CONTOURS
# =========================================================

simplified_contours = []

for contour in contours:

    if len(contour) < MIN_CONTOUR_POINTS:
        continue

    simplified = rdp(
        contour,
        EPSILON
    )

    if len(simplified) < 12:
        continue

    simplified_contours.append(simplified)

print(f"Valid contours: {len(simplified_contours)}")

# =========================================================
# BUILD SVG PATHS
# =========================================================

paths = []

for contour in simplified_contours:

    ys = (contour[:, 0] - pad) / UPSCALE
    xs = (contour[:, 1] - pad) / UPSCALE

    xs = np.clip(xs, 0, original_w - 1)
    ys = np.clip(ys, 0, original_h - 1)

    d = [
        f"M {fmt(xs[0])} {fmt(ys[0])}"
    ]

    for x, y in zip(xs[1:], ys[1:]):
        d.append(
            f"L {fmt(x)} {fmt(y)}"
        )

    d.append("Z")

    paths.append(" ".join(d))

combined_d = " ".join(paths)

# =========================================================
# SVG OUTPUT
# =========================================================

svg = f'''<svg
xmlns="http://www.w3.org/2000/svg"
width="{original_w}"
height="{original_h}"
viewBox="0 0 {original_w} {original_h}"
fill="none">

<path
d="{combined_d}"
fill="{FILL_COLOR}"
fill-rule="evenodd"/>

</svg>
'''

# =========================================================
# SAVE SVG
# =========================================================

with open(
    OUTPUT_SVG,
    "w",
    encoding="utf-8"
) as f:

    f.write(svg)

print(f"SVG saved: {OUTPUT_SVG}")
elapsed = time.perf_counter() - start_time

print(f"Processing time: {elapsed:.2f} seconds")
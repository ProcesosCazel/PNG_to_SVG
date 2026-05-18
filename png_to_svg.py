from PIL import Image
import numpy as np
from skimage.filters import threshold_otsu
from skimage.measure import find_contours

# ====== CONFIG ======
INPUT_PNG = "Imagen.png"
OUTPUT_SVG = "Vector.svg"

# Entre más pequeño, más “HD” (más puntos y más pesado)
EPSILON = 0.000001

FILL_COLOR = "#2f2f2f"
# ====================


def rdp(points, epsilon):
    """Ramer–Douglas–Peucker simplification for Nx2 points."""
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
        cross = np.abs(v[:, 0] * line[1] - v[:, 1] * line[0])
        dists = cross / line_len

    idx = int(np.argmax(dists))
    dmax = float(dists[idx])

    if dmax > epsilon:
        left = rdp(points[: idx + 1], epsilon)
        right = rdp(points[idx:], epsilon)
        return np.vstack((left[:-1], right))
    else:
        return np.vstack((start, end))


def fmt(x):
    return (f"{x:.2f}").rstrip("0").rstrip(".")


img = Image.open(INPUT_PNG).convert("RGBA")
arr = np.array(img)

alpha = arr[..., 3] / 255.0
rgb = arr[..., :3].astype(np.float32)

# Composite sobre blanco para umbral estable
rgb_comp = rgb * alpha[..., None] + 255 * (1 - alpha[..., None])

# Luminancia
lum = (
    0.2126 * rgb_comp[..., 0] +
    0.7152 * rgb_comp[..., 1] +
    0.0722 * rgb_comp[..., 2]
)

th = threshold_otsu(lum)

mask = lum < th  # pixeles oscuros
# --- Optional auto-foreground selection ---
# mask_dark = lum < th
# mask_light = lum > th
# mask = mask_dark if mask_dark.sum() < mask_light.sum() else mask_light

h, w = mask.shape

# Padding para contornos cerrados
pad = 2
mask_p = np.pad(mask.astype(np.uint8), pad, mode="constant", constant_values=0)

contours = find_contours(mask_p, 0.5)

# Simplificar contornos
simp = []
for c in contours:
    if len(c) < 25:
        continue
    sc = rdp(c, EPSILON)
    if len(sc) < 12:
        continue
    simp.append(sc)

# Construir un solo path con evenodd para respetar “huecos”
paths = []
for sc in simp:
    ys = sc[:, 0] - pad
    xs = sc[:, 1] - pad

    xs = np.clip(xs, 0, w - 1)
    ys = np.clip(ys, 0, h - 1)

    d = [f"M {fmt(xs[0])} {fmt(ys[0])}"]
    for x, y in zip(xs[1:], ys[1:]):
        d.append(f"L {fmt(x)} {fmt(y)}")
    d.append("Z")
    paths.append(" ".join(d))

combined_d = " ".join(paths)

svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
    f'viewBox="0 0 {w} {h}" fill="none">'
    f'<path d="{combined_d}" fill="{FILL_COLOR}" fill-rule="evenodd"/>'
    f"</svg>"
)

with open(OUTPUT_SVG, "w", encoding="utf-8") as f:
    f.write(svg)

print("OK ->", OUTPUT_SVG)
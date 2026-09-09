from __future__ import annotations

from pathlib import Path
SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg'}


class VectorizationError(RuntimeError):
    pass


def _rdp(points, epsilon: float):
    import numpy as np

    if len(points) < 3:
        return points

    keep = np.zeros(len(points), dtype=bool)
    keep[0] = True
    keep[-1] = True
    stack = [(0, len(points) - 1)]

    while stack:
        start_idx, end_idx = stack.pop()
        if end_idx <= start_idx + 1:
            continue

        start = points[start_idx]
        end = points[end_idx]
        segment = end - start
        seg_len = float(np.hypot(segment[0], segment[1]))
        section = points[start_idx + 1:end_idx]
        if len(section) == 0:
            continue

        if seg_len == 0:
            distances = np.hypot(*(section - start).T)
        else:
            v = section - start
            cross = np.abs(v[:, 0] * segment[1] - v[:, 1] * segment[0])
            distances = cross / seg_len

        rel_idx = int(np.argmax(distances))
        dmax = float(distances[rel_idx])
        if dmax > epsilon:
            idx = start_idx + 1 + rel_idx
            keep[idx] = True
            stack.append((start_idx, idx))
            stack.append((idx, end_idx))

    return points[keep]


def _fmt(value: float, precision: int = 3) -> str:
    return f"{value:.{precision}f}".rstrip('0').rstrip('.')


def _otsu_threshold(gray_image) -> int:
    hist = gray_image.histogram()
    total = sum(hist)
    if total <= 0:
        return 127

    sum_total = sum(i * count for i, count in enumerate(hist))
    sum_bg = 0.0
    weight_bg = 0
    best_variance = -1.0
    best_threshold = 127

    for threshold in range(256):
        count = hist[threshold]
        weight_bg += count
        if weight_bg == 0:
            continue

        weight_fg = total - weight_bg
        if weight_fg == 0:
            break

        sum_bg += threshold * count
        mean_bg = sum_bg / weight_bg
        mean_fg = (sum_total - sum_bg) / weight_fg
        variance = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
        if variance > best_variance:
            best_variance = variance
            best_threshold = threshold

    return best_threshold


def _morphology(mask, radius: int = 1):
    import numpy as np
    from PIL import Image, ImageFilter

    radius = max(1, int(radius))
    size = radius * 2 + 1
    src = Image.fromarray((mask.astype(np.uint8) * 255), mode='L')

    # Closing: fill tiny holes/gaps.
    src = src.filter(ImageFilter.MaxFilter(size=size))
    src = src.filter(ImageFilter.MinFilter(size=size))

    # Opening: remove isolated tiny specks.
    src = src.filter(ImageFilter.MinFilter(size=size))
    src = src.filter(ImageFilter.MaxFilter(size=size))

    return np.asarray(src, dtype=np.uint8) > 127


def _marching_squares(mask):
    """Return closed contours from a boolean image without scikit-image.

    Coordinates are returned in image sample coordinates (x, y), with
    half-pixel interpolation along mask transitions.
    """
    import numpy as np

    if mask.ndim != 2:
        raise ValueError('Mask must be two dimensional')

    padded = np.pad(mask.astype(np.uint8), 1, mode='constant', constant_values=0)

    tl = padded[:-1, :-1]
    tr = padded[:-1, 1:]
    br = padded[1:, 1:]
    bl = padded[1:, :-1]
    code = tl + (tr << 1) + (br << 2) + (bl << 3)

    rows, cols = np.nonzero((code != 0) & (code != 15))

    # Endpoints are integer coordinates on a grid scaled by 2.
    adjacency: dict[tuple[int, int], list[tuple[int, int]]] = {}

    def add_segment(a, b):
        adjacency.setdefault(a, []).append(b)
        adjacency.setdefault(b, []).append(a)

    for r, c in zip(rows.tolist(), cols.tolist()):
        k = int(code[r, c])
        top = (2 * c + 1, 2 * r)
        right = (2 * c + 2, 2 * r + 1)
        bottom = (2 * c + 1, 2 * r + 2)
        left = (2 * c, 2 * r + 1)

        if k == 1:
            add_segment(left, top)
        elif k == 2:
            add_segment(top, right)
        elif k == 3:
            add_segment(left, right)
        elif k == 4:
            add_segment(right, bottom)
        elif k == 5:
            add_segment(left, top)
            add_segment(right, bottom)
        elif k == 6:
            add_segment(top, bottom)
        elif k == 7:
            add_segment(left, bottom)
        elif k == 8:
            add_segment(bottom, left)
        elif k == 9:
            add_segment(top, bottom)
        elif k == 10:
            add_segment(top, right)
            add_segment(bottom, left)
        elif k == 11:
            add_segment(right, bottom)
        elif k == 12:
            add_segment(left, right)
        elif k == 13:
            add_segment(top, right)
        elif k == 14:
            add_segment(left, top)

    visited_edges: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    contours = []

    def edge_key(a, b):
        return (a, b) if a <= b else (b, a)

    for start, neighbors in list(adjacency.items()):
        for first in neighbors:
            ek = edge_key(start, first)
            if ek in visited_edges:
                continue

            points = [start]
            prev = start
            current = first
            visited_edges.add(ek)
            max_steps = max(10, len(adjacency) * 2)

            for _ in range(max_steps):
                points.append(current)
                if current == start:
                    break

                candidates = adjacency.get(current, [])
                if not candidates:
                    break

                next_point = None
                for candidate in candidates:
                    candidate_key = edge_key(current, candidate)
                    if candidate_key not in visited_edges:
                        next_point = candidate
                        break

                if next_point is None:
                    if start in candidates:
                        next_point = start
                    else:
                        break

                visited_edges.add(edge_key(current, next_point))
                prev, current = current, next_point

            if len(points) >= 4 and points[-1] == start:
                arr = np.asarray(points, dtype=np.float64) / 2.0
                # Remove the 1-pixel padding introduced above.
                arr[:, 0] -= 1.0
                arr[:, 1] -= 1.0
                contours.append(arr)

    return contours


def _polygon_area(points) -> float:
    import numpy as np

    if len(points) < 3:
        return 0.0
    x = points[:, 0]
    y = points[:, 1]
    return float(abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) * 0.5)


def image_to_svg(
    input_path: str | Path,
    output_path: str | Path,
    *,
    quality: str = 'Normal',
    fill_color: str = '#2f2f2f',
) -> dict:
    import numpy as np
    from PIL import Image, ImageFilter

    input_path = Path(input_path)
    output_path = Path(output_path)

    if input_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise VectorizationError('Formato no compatible. Selecciona PNG, JPG o JPEG.')

    settings = {
        'Rapida': dict(upscale=1, epsilon=1.0, blur=0.55, min_area=5.0, max_process_dim=2800, precision=3, morph_radius=1),
        'Normal': dict(upscale=2, epsilon=0.55, blur=0.75, min_area=4.0, max_process_dim=3200, precision=3, morph_radius=1),
        'Alta': dict(upscale=2, epsilon=0.30, blur=0.65, min_area=2.5, max_process_dim=4200, precision=4, morph_radius=1),
        'Super alta': dict(upscale=4, epsilon=0.12, blur=0.45, min_area=1.1, max_process_dim=5600, precision=4, morph_radius=1),
    }
    cfg = settings.get(quality, settings['Normal'])

    try:
        with Image.open(input_path) as source:
            source.load()
            source_w, source_h = source.size
            if source_w < 2 or source_h < 2:
                raise VectorizationError('La imagen es demasiado pequena para vectorizarse.')

            # Reduce only the processing copy. The output keeps original dimensions.
            process = source.convert('RGBA')
            max_dim = int(cfg['max_process_dim'])
            if max(process.size) > max_dim:
                scale = max_dim / max(process.size)
                process = process.resize(
                    (max(2, round(process.width * scale)), max(2, round(process.height * scale))),
                    Image.Resampling.LANCZOS,
                )

            process_scale_x = source_w / process.width
            process_scale_y = source_h / process.height

            upscale = int(cfg['upscale'])
            if upscale > 1:
                process = process.resize(
                    (process.width * upscale, process.height * upscale),
                    Image.Resampling.LANCZOS,
                )

            arr = np.asarray(process, dtype=np.uint8)
            alpha = arr[..., 3]
            has_transparency = bool(np.any(alpha < 250))
            alpha_object = alpha > 20
            alpha_fraction = float(alpha_object.mean())

            if has_transparency and 0.001 < alpha_fraction < 0.97:
                mask = alpha_object
            else:
                # Composite on white so normal JPEG and opaque PNG behave consistently.
                white = Image.new('RGBA', process.size, (255, 255, 255, 255))
                comp = Image.alpha_composite(white, process).convert('L')
                comp = comp.filter(ImageFilter.GaussianBlur(radius=float(cfg['blur']) * upscale))

                extrema = comp.getextrema()
                if extrema[1] - extrema[0] < 3:
                    raise VectorizationError('La imagen no tiene suficiente contraste para vectorizarse.')

                threshold = _otsu_threshold(comp)
                gray = np.asarray(comp, dtype=np.uint8)
                dark = gray <= threshold
                light = gray > threshold
                mask = dark if int(dark.sum()) <= int(light.sum()) else light

            mask = _morphology(mask, radius=int(cfg.get('morph_radius', 1)))
            contours = _marching_squares(mask)

    except VectorizationError:
        raise
    except Exception as exc:
        raise VectorizationError(f'No fue posible procesar la imagen: {exc}') from exc

    paths = []
    written = 0
    precision = int(cfg.get('precision', 3))
    scale_x = process_scale_x / upscale
    scale_y = process_scale_y / upscale

    for contour in contours:
        if len(contour) < 5:
            continue

        area_processing = _polygon_area(contour)
        if area_processing < float(cfg['min_area']) * (upscale ** 2):
            continue

        simplified = _rdp(contour, float(cfg['epsilon']) * upscale)
        if len(simplified) < 4:
            continue

        xs = np.clip(simplified[:, 0] * scale_x, 0, source_w)
        ys = np.clip(simplified[:, 1] * scale_y, 0, source_h)

        commands = [f"M {_fmt(xs[0], precision)} {_fmt(ys[0], precision)}"]
        commands.extend(f"L {_fmt(x, precision)} {_fmt(y, precision)}" for x, y in zip(xs[1:], ys[1:]))
        commands.append('Z')
        paths.append(' '.join(commands))
        written += 1

    if not paths:
        raise VectorizationError(
            'No se detectaron contornos utilizables. Prueba una imagen con mayor contraste o fondo mas limpio.'
        )

    combined = ' '.join(paths)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{source_w}" height="{source_h}" '
        f'viewBox="0 0 {source_w} {source_h}">\n'
        f'  <path d="{combined}" fill="{fill_color}" fill-rule="evenodd"/>\n'
        f'</svg>\n'
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding='utf-8')

    return {
        'width': source_w,
        'height': source_h,
        'contours_found': len(contours),
        'contours_written': written,
        'output': str(output_path),
        'quality': quality,
    }

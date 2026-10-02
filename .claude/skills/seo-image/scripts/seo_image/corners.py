"""Corner busy-score measurement and watermark corner choice."""
from PIL import ImageFilter, ImageStat

from .models import CORNERS


def corner_box(corner, size, box_size, margin):
    """Pixel box (x0, y0, x1, y1) for a watermark of `box_size` placed in `corner`."""
    (w, h), (bw, bh) = size, box_size
    x0 = margin if "left" in corner else w - margin - bw
    y0 = margin if "top" in corner else h - margin - bh
    return (x0, y0, x0 + bw, y0 + bh)


def busy_score(image, box):
    """0 for a flat area; higher means busier (grey-level spread plus edge density)."""
    region = image.crop(box).convert("L")
    spread = ImageStat.Stat(region).stddev[0]
    edge_map = region.filter(ImageFilter.FIND_EDGES)
    if min(edge_map.size) > 2:  # the filter leaves the outermost pixels unprocessed
        edge_map = edge_map.crop((1, 1, edge_map.width - 1, edge_map.height - 1))
    edges = ImageStat.Stat(edge_map).mean[0]
    return round(spread + edges, 3)


def measure_corners(image, box_size, margin):
    return {c: busy_score(image, corner_box(c, image.size, box_size, margin)) for c in CORNERS}


def choose_corner(labels, busy, start="bottom-right"):
    """Pick the corner for the watermark, or None to skip.

    labels: {corner: free | subject | face_or_text}; busy: {corner: score}.
    """
    if labels.get(start) == "free":
        return start

    def least_busy(kind):
        names = [c for c in CORNERS if labels.get(c) == kind]
        return min(names, key=lambda c: busy[c]) if names else None

    return least_busy("free") or least_busy("subject")

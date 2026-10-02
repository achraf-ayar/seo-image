"""Subtle text watermark: small, semi-transparent, contrast adapted to the background."""
from PIL import Image, ImageDraw, ImageFont, ImageStat

from .corners import corner_box

MIN_SHORT_SIDE = 200
MARGIN_PCT = 2.0
MIN_FONT_PX = 10


def to_8bit(image):
    """16-bit and float grayscale would clip to white when converted to 8-bit RGB; scale them."""
    if image.mode in ("I", "I;16", "I;16L", "I;16B"):
        return image.point(lambda v: v * (1 / 256)).convert("L")
    if image.mode == "F":
        return image.point(lambda v: v * 255).convert("L")
    return image


def too_small(size):
    return min(size) < MIN_SHORT_SIDE


def margin_for(size):
    return max(2, round(min(size) * MARGIN_PCT / 100))


def _fit(text, size, size_pct):
    short = min(size)
    margin = margin_for(size)
    px = max(MIN_FONT_PX, round(short * size_pct / 100))
    while True:
        font = ImageFont.load_default(size=px)
        stroke = max(1, px // 14)
        l, t, r, b = font.getbbox(text, stroke_width=stroke)
        if (r - l) <= size[0] - 2 * margin or px <= MIN_FONT_PX:
            return font, stroke, (l, t, r, b)
        px -= 1


def text_box_size(text, size, size_pct):
    """Width and height of the watermark box (stroke included)."""
    _, _, (l, t, r, b) = _fit(text, size, size_pct)
    return (r - l, b - t)


def apply_watermark(image, text, corner, opacity, size_pct):
    """Return (watermarked image, box). The box includes the outline."""
    image = to_8bit(image)
    mode = image.mode
    has_alpha = "A" in mode or "transparency" in image.info
    base = image.convert("RGBA")
    font, stroke, (l, t, r, b) = _fit(text, base.size, size_pct)
    box = corner_box(corner, base.size, (r - l, b - t), margin_for(base.size))

    luminance = ImageStat.Stat(base.crop(box).convert("L")).mean[0]
    dark_bg = luminance < 128
    fill = (255, 255, 255) if dark_bg else (20, 20, 20)
    outline = (20, 20, 20) if dark_bg else (255, 255, 255)
    alpha = round(255 * opacity)

    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(
        (box[0] - l, box[1] - t), text, font=font,
        fill=fill + (alpha,), stroke_width=stroke, stroke_fill=outline + (alpha,))
    out = Image.alpha_composite(base, layer)
    if not has_alpha:
        out = out.convert("RGB")
    return out, box

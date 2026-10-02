from PIL import Image, ImageChops

import helpers
from seo_image.watermark import apply_watermark, margin_for, text_box_size, too_small

TEXT = "example.com"


def changed_bbox(a, b):
    return ImageChops.difference(a.convert("RGBA"), b.convert("RGBA")).getbbox(alpha_only=False)


def inside(bbox, box):
    return bbox is not None and bbox[0] >= box[0] and bbox[1] >= box[1] \
        and bbox[2] <= box[2] and bbox[3] <= box[3]


def test_dimensions_unchanged_and_pixels_change_only_inside_box():
    for corner in ("top-left", "top-right", "bottom-left", "bottom-right"):
        src = helpers.pattern_image((500, 400), "gradient")
        out, box = apply_watermark(src, TEXT, corner, 0.6, 2.5)
        assert out.size == src.size and out.mode == "RGB"
        assert inside(changed_bbox(src, out), box)


def test_text_inside_image_with_margin():
    src = helpers.pattern_image((500, 400), "flat")
    m = margin_for(src.size)
    for corner in ("top-left", "top-right", "bottom-left", "bottom-right"):
        _, (x0, y0, x1, y1) = apply_watermark(src, TEXT, corner, 0.6, 2.5)
        assert x0 >= m and y0 >= m and x1 <= 500 - m and y1 <= 400 - m


def test_small_text_relative_to_image():
    w, h = text_box_size(TEXT, (1000, 800), 2.5)
    assert h <= 800 * 0.06 and w <= 1000 * 0.3


def test_contrast_adapts_to_background():
    dark = helpers.pattern_image((400, 300), "dark")
    out, box = apply_watermark(dark, TEXT, "bottom-right", 1.0, 3)
    assert max(out.crop(box).convert("L").getdata()) > 200  # light text on dark
    light = helpers.pattern_image((400, 300), "light")
    out, box = apply_watermark(light, TEXT, "bottom-right", 1.0, 3)
    assert min(out.crop(box).convert("L").getdata()) < 60  # dark text on light


def test_opacity_applied():
    light = helpers.pattern_image((400, 300), "light")
    strong, box = apply_watermark(light, TEXT, "bottom-right", 1.0, 3)
    faint, _ = apply_watermark(light, TEXT, "bottom-right", 0.4, 3)
    assert min(faint.crop(box).convert("L").getdata()) > min(strong.crop(box).convert("L").getdata()) + 50


def test_skip_threshold():
    assert too_small((199, 500)) and too_small((500, 150))
    assert not too_small((200, 200)) and not too_small((1000, 800))


def test_long_text_shrinks_to_fit():
    src = helpers.pattern_image((220, 220), "flat")
    _, (x0, y0, x1, y1) = apply_watermark(src, "a-very-long-subdomain.of.some.example.com", "bottom-right", 0.6, 6)
    assert x0 >= margin_for(src.size) and x1 <= 220 - margin_for(src.size)


def test_alpha_preserved():
    for mode_name in ("RGBA",):
        src = Image.new("RGBA", (400, 300), (0, 0, 0, 0))
        out, box = apply_watermark(src, TEXT, "bottom-right", 0.6, 3)
        assert out.mode == "RGBA" and out.size == src.size
        assert inside(changed_bbox(src, out), box)
        assert out.getpixel((5, 5))[3] == 0  # transparency elsewhere is untouched
        assert max(a for *_, a in out.crop(box).getdata()) > 0


def test_16bit_grayscale_keeps_its_brightness():
    src = Image.new("I", (400, 300), 40000)  # mid-light grey in 16 bits
    out, box = apply_watermark(src, TEXT, "bottom-right", 0.6, 2.5)
    r, g, b = out.convert("RGB").getpixel((10, 10))
    assert abs(r - 156) <= 2 and r == g == b  # 40000 / 256, not clipped to 255
    assert out.size == src.size

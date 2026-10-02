"""Synthetic image builders and utilities shared by the tests."""
import hashlib
import io
import random
import struct

from PIL import Image, ImageCms, ImageDraw, PngImagePlugin

ICC = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
GPS = {1: "N", 2: (48.0, 51.0, 24.0), 3: "E", 4: (2.0, 21.0, 7.0)}


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def pattern_image(size=(400, 300), kind="gradient", mode="RGB"):
    w, h = size
    img = Image.new("RGB", size, (120, 140, 160))
    if kind == "gradient":
        ramp = Image.linear_gradient("L")  # 256x256, black at the top
        red = ramp.rotate(90, expand=True).transpose(Image.Transpose.FLIP_LEFT_RIGHT).resize(size)
        green = ramp.resize(size)
        img = Image.merge("RGB", (red, green, Image.new("L", size, 128)))
    elif kind == "noise":
        img = Image.frombytes("RGB", size, random.Random(1).randbytes(w * h * 3))
    elif kind == "dark":
        img = Image.new("RGB", size, (15, 15, 20))
    elif kind == "light":
        img = Image.new("RGB", size, (245, 245, 240))
    elif kind == "flat":
        pass
    if mode != "RGB":
        img = img.convert(mode)
    return img


def make_image(path, size=(400, 300), kind="gradient", mode="RGB", **save):
    img = pattern_image(size, kind, mode)
    img.save(path, **save)
    return path


def noisy_corner(img, corner, frac=0.3):
    """Fill one corner patch with noise (a busy region)."""
    w, h = img.size
    pw, ph = int(w * frac), int(h * frac)
    x0 = 0 if "left" in corner else w - pw
    y0 = 0 if "top" in corner else h - ph
    patch = Image.frombytes("RGB", (pw, ph), random.Random(2).randbytes(pw * ph * 3))
    img.paste(patch, (x0, y0))
    return img


def make_rotated_gps_jpeg(path, stored=(300, 200), orientation=6, with_gps=True):
    img = pattern_image(stored)
    ex = Image.Exif()
    ex[0x0112] = orientation
    ex[0x010F] = "TestMake"
    if with_gps:
        ex[0x8825] = dict(GPS)
    img.save(path, exif=ex.tobytes(), icc_profile=ICC, quality=90)
    return path


def make_gps_jpeg(path, size=(400, 300)):
    return make_rotated_gps_jpeg(path, size, orientation=1)


def make_rgba(path, size=(400, 300)):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([size[0] // 4, size[1] // 4, size[0] * 3 // 4, size[1] * 3 // 4], fill=(200, 60, 60, 255))
    kw = {"lossless": True} if str(path).endswith(".webp") else {}
    img.save(path, **kw)
    return path


def make_animated_gif(path, size=(120, 120)):
    frames = [Image.new("RGB", size, c) for c in ((255, 0, 0), (0, 255, 0), (0, 0, 255))]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=100, loop=0)
    return path


def make_animated_webp(path, size=(120, 120)):
    frames = [Image.new("RGB", size, c) for c in ((255, 0, 0), (0, 255, 0))]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=100, loop=0)
    return path


def make_corrupt(path):
    open(path, "wb").write(b"this is not an image at all")
    return path


def good_metadata(**over):
    md = {
        "filename_stem": "red-ceramic-mug-on-wooden-shelf",
        "alt": "Red ceramic mug on a wooden shelf",
        "title": "Red ceramic mug on a shelf",
        "description": "A red ceramic mug sits on a wooden shelf. A small plant is beside it.",
        "tags": ["mug", "ceramic", "shelf", "kitchen"],
    }
    md.update(over)
    return md


def analysis_entry(path, corners=None, **md):
    entry = {
        "path": str(path),
        "image_type": "product",
        "primary_subject": "mug",
        "metadata": good_metadata(**md),
    }
    if corners is not False:
        entry["corners"] = corners or {c: "free" for c in
                                      ("top-left", "top-right", "bottom-left", "bottom-right")}
    return entry


XMP = (b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
       b'<rdf:Description xmlns:exif="http://ns.adobe.com/exif/1.0/" exif:GPSLatitude="48,51.4N" '
       b'exif:GPSLongitude="2,21.1E" xmlns:dc="http://purl.org/dc/elements/1.1/"/></rdf:RDF></x:xmpmeta>')
LOCATION_KEYS = (b"GPSLatitude", b"GPSLongitude")


def has_location_text(path):
    data = open(path, "rb").read()
    return any(k in data for k in LOCATION_KEYS)


def make_xmp_jpeg(path, size=(400, 300), icc=True):
    """JPEG with an XMP APP1 segment carrying GPS properties (Pillow cannot write one itself)."""
    buf = io.BytesIO()
    pattern_image(size).save(buf, format="JPEG", quality=90, **({"icc_profile": ICC} if icc else {}))
    data = buf.getvalue()
    payload = b"http://ns.adobe.com/xap/1.0/\x00" + XMP
    segment = b"\xff\xe1" + struct.pack(">H", len(payload) + 2) + payload
    with open(path, "wb") as fh:
        fh.write(data[:2] + segment + data[2:])
    return path


def make_xmp_png(path, size=(400, 300), compressed=False):
    info = PngImagePlugin.PngInfo()
    info.add_itxt("XML:com.adobe.xmp", XMP.decode(), zip=compressed)
    pattern_image(size).save(path, pnginfo=info, icc_profile=ICC)
    return path


def make_xmp_webp(path, size=(400, 300)):
    pattern_image(size).save(path, xmp=XMP, icc_profile=ICC, lossless=True)
    return path


MAKERNOTE = b"MAKERNOTE-GPS-48.85N-2.35E"


def make_thumbnail_makernote_jpeg(path, size=(400, 300), orientation=6):
    """JPEG whose EXIF holds a MakerNote and an embedded JPEG thumbnail (IFD1)."""
    ex = Image.Exif()
    ex[0x0112] = orientation
    ex[0x8769] = {0x927C: MAKERNOTE}
    raw = ex.tobytes()
    head, tiff = raw[:6], bytearray(raw[6:])
    end = "<" if tiff[:2] == b"II" else ">"
    (count,) = struct.unpack_from(end + "H", tiff, 8)
    next_at = 8 + 2 + 12 * count
    thumb = io.BytesIO()
    pattern_image((40, 30)).save(thumb, format="JPEG")
    thumb = thumb.getvalue()
    if len(tiff) % 2:
        tiff.append(0)
    ifd1 = len(tiff)
    struct.pack_into(end + "I", tiff, next_at, ifd1)
    data_at = ifd1 + 2 + 2 * 12 + 4
    tiff += struct.pack(end + "H", 2)
    tiff += struct.pack(end + "HHII", 0x0201, 4, 1, data_at)
    tiff += struct.pack(end + "HHII", 0x0202, 4, 1, len(thumb))
    tiff += struct.pack(end + "I", 0) + thumb
    pattern_image(size).save(path, exif=head + bytes(tiff), icc_profile=ICC, quality=90)
    return path

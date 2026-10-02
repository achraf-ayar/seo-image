"""Saving outputs: byte copy when nothing must change, otherwise a careful re-encode."""
import os
import shutil
from dataclasses import dataclass

import io

from PIL import Image, ImageCms, ImageOps, JpegImagePlugin

from .inputs import GPS_TAG, ORIENTATION_TAG, has_gps, orientation_of

JPEG_QUALITY = 95
EXIF_IFD_TAG = 0x8769
MAKERNOTE_TAG = 0x927C


@dataclass
class Loaded:
    image: Image.Image  # upright pixels
    fmt: str  # jpeg | png | webp
    icc: bytes | None
    exif: bytes | None  # EXIF without GPS and without the orientation tag
    subsampling: int
    lossless: bool


def _webp_lossless(path):
    with open(path, "rb") as fh:
        head = fh.read(64)
    return b"VP8L" in head


def _cmyk_to_rgb(img, icc):
    """Convert CMYK to RGB through its profile when it has a usable one. Returns (image, profile)."""
    srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
    if icc:
        try:
            out = ImageCms.profileToProfile(img, ImageCms.ImageCmsProfile(io.BytesIO(icc)), srgb,
                                            outputMode="RGB")
            return out, srgb.tobytes()
        except (ImageCms.PyCMSError, OSError):
            pass  # a profile that does not describe this data must not travel with the pixels
    return img.convert("RGB"), None


def load_upright(path):
    """Open an image read-only and return upright pixels plus the metadata to keep."""
    with Image.open(path) as img:
        fmt = {"JPEG": "jpeg", "PNG": "png", "WEBP": "webp"}[img.format]
        icc = img.info.get("icc_profile")
        exif = img.getexif()
        subsampling = JpegImagePlugin.get_sampling(img) if fmt == "jpeg" else -1
        img.load()
        upright = ImageOps.exif_transpose(img)
        upright = upright.copy() if upright is img else upright
        if upright.mode == "CMYK":
            upright, icc = _cmyk_to_rgb(upright, icc)
        exif.pop(GPS_TAG, None) if GPS_TAG in exif else None
        if ORIENTATION_TAG in exif:
            del exif[ORIENTATION_TAG]
        try:  # a MakerNote is opaque vendor data that can embed coordinates
            sub = exif.get_ifd(EXIF_IFD_TAG)
            sub.pop(MAKERNOTE_TAG, None)
        except Exception:
            pass
        exif_bytes = exif.tobytes() if len(exif) else None
        return Loaded(upright, fmt, icc, exif_bytes, subsampling,
                      _webp_lossless(path) if fmt == "webp" else True)


def needs_change(path, watermark):
    """True when the output cannot be a byte copy of the source."""
    if watermark:
        return True
    with Image.open(path) as img:
        return has_gps(img, path) or orientation_of(img) != 1


def _encode(loaded, tmp):
    img = loaded.image
    if loaded.fmt == "jpeg":
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        kw = {"quality": JPEG_QUALITY, "optimize": True}
        if loaded.subsampling >= 0:
            kw["subsampling"] = loaded.subsampling
        if loaded.icc:
            kw["icc_profile"] = loaded.icc
        if loaded.exif:
            kw["exif"] = loaded.exif
        img.save(tmp, format="JPEG", **kw)
    elif loaded.fmt == "png":
        kw = {}
        if loaded.icc:
            kw["icc_profile"] = loaded.icc
        if loaded.exif:
            kw["exif"] = loaded.exif
        img.save(tmp, format="PNG", **kw)
    else:
        kw = {"lossless": True, "exact": True} if loaded.lossless else {"quality": JPEG_QUALITY}
        if loaded.icc:
            kw["icc_profile"] = loaded.icc
        if loaded.exif:
            kw["exif"] = loaded.exif
        img.save(tmp, format="WEBP", **kw)


def write_output(src, out_folder, filename, loaded=None, watermark=False):
    """Write one output, replacing a same-named file from an earlier run.

    `loaded` carries already-processed pixels (for example, watermarked). Without it the
    source is copied byte for byte unless it has GPS data or a non-upright orientation.
    Returns the final (width, height).
    """
    os.makedirs(out_folder, exist_ok=True)
    dest = os.path.join(out_folder, filename)
    tmp = os.path.join(out_folder, f".tmp-{os.getpid()}-{filename}")
    try:
        if loaded is None and not needs_change(src, watermark):
            shutil.copyfile(src, tmp)
        else:
            loaded = loaded or load_upright(src)
            _encode(loaded, tmp)
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    with Image.open(dest) as out:
        return out.size

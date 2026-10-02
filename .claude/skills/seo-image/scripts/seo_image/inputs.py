"""Input resolution and inspection (read-only)."""
import glob
import os
import re

from PIL import Image, UnidentifiedImageError

from .models import InspectedImage

FORMATS = {"JPEG": "jpeg", "PNG": "png", "WEBP": "webp"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".avif", ".heic"}
GPS_TAG = 0x8825
ORIENTATION_TAG = 0x0112


def orientation_of(img):
    try:
        return img.getexif().get(ORIENTATION_TAG, 1) or 1
    except Exception:
        return 1


XMP_LOCATION = re.compile(
    rb"GPS(Latitude|Longitude|Altitude|Position|Speed|ImgDirection|DestLatitude|DestLongitude)")


def _xmp_has_location(img, path):
    """True when XMP (stored as text in the file or in decoded PNG/WebP metadata) has GPS keys."""
    chunks = []
    for key, value in img.info.items():
        if "xmp" in str(key).lower() or "xml" in str(key).lower():
            chunks.append(value if isinstance(value, bytes) else str(value).encode("utf-8", "ignore"))
    if path:
        try:
            with open(path, "rb") as fh:
                chunks.append(fh.read())
        except OSError:
            pass
    return any(XMP_LOCATION.search(c) for c in chunks)


def has_gps(img, path=None):
    """True when the file carries location data: EXIF GPS or XMP GPS properties."""
    try:
        exif = img.getexif()
        if GPS_TAG in exif or bool(exif.get_ifd(GPS_TAG)):
            return True
    except Exception:
        pass
    return _xmp_has_location(img, path)


def inspect_image(path):
    """Describe one file. Never raises; problems become a status and a reason."""
    path = str(path)
    info = InspectedImage(path=path, original_filename=os.path.basename(path))
    if not os.path.isfile(path):
        info.status, info.reason = "unreadable", "file not found"
        return info
    try:
        with Image.open(path) as img:
            fmt = FORMATS.get(img.format)
            if getattr(img, "is_animated", False) and getattr(img, "n_frames", 1) > 1:
                info.status = "unsupported"
                info.animated = True
                info.format = fmt
                info.reason = "animated images are unsupported"
                return info
            if fmt is None:
                info.status = "unsupported"
                info.reason = f"unsupported format: {img.format}"
                return info
            info.format = fmt
            img.load()
            w, h = img.size
            orientation = orientation_of(img)
            if orientation in (5, 6, 7, 8):
                w, h = h, w
            info.width, info.height = w, h
            info.upright = orientation == 1
            info.has_gps = has_gps(img, path)
    except UnidentifiedImageError:
        ext = os.path.splitext(path)[1].lower()
        if ext in IMAGE_EXTS:
            info.status, info.reason = "unreadable", "file is corrupt or not a valid image"
        else:
            info.status, info.reason = "unsupported", "not an image file"
    except Exception as exc:  # truncated or damaged files
        info.status, info.reason = "unreadable", f"could not read image: {exc}"
    return info


def expand_inputs(patterns):
    """Expand globs and folders into a de-duplicated, ordered list of paths."""
    found, seen = [], set()

    def add(p):
        key = os.path.realpath(p)
        if key not in seen:
            seen.add(key)
            found.append(p)

    for pat in patterns:
        matches = sorted(glob.glob(os.path.expanduser(pat), recursive=True))
        if not matches:
            if not glob.has_magic(pat):
                add(pat)  # a named file that is missing is reported as "file not found"
            continue
        for m in matches:
            if os.path.isdir(m):
                for name in sorted(os.listdir(m)):
                    full = os.path.join(m, name)
                    if os.path.isfile(full) and not name.startswith("."):
                        add(full)
            else:
                add(m)
    return found

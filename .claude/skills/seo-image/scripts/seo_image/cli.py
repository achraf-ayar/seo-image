"""Command line: `inspect` (resolve and measure) and `apply` (validate, write, report)."""
import argparse
import json
import os
import sys

from PIL import Image

from . import config as cfgmod
from . import corners, domain, inputs, naming, report, rules, watermark, writer
from .errors import FatalError, ImageError
from .models import CORNERS, CORNER_LABELS, Result


# ---------------------------------------------------------------- shared helpers

def _resolve_settings(args):
    cfg = cfgmod.load_config(args.config)
    return cfgmod.resolve_settings(cfg, site=args.site, out=args.out)


def _check_output_folder(out_folder, input_paths):
    """Refuse an output folder that is an input's folder, or that contains an input.

    Either case could let an output replace an original (a rerun replaces same-named
    outputs). A sub-folder of an input's folder, such as the default `seo-images/`, is safe.
    """
    out = os.path.realpath(out_folder)
    for p in input_paths:
        folder = os.path.realpath(os.path.dirname(os.path.abspath(p)))
        if folder == out or folder.startswith(out + os.sep):
            raise FatalError(
                f"output folder {out_folder!r} is, or contains, the input folder "
                f"{folder!r}; choose another output folder so originals cannot be overwritten")


def _measure(path, settings, info):
    """Corner busy scores for `inspect` (informational; apply measures again)."""
    try:
        with Image.open(path) as img:
            img.load()
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
            text = domain.ascii_form(settings.domain) if settings.domain else "example.com"
            box = watermark.text_box_size(text, img.size, settings.size)
            return corners.measure_corners(img.convert("RGB"), box, watermark.margin_for(img.size))
    except Exception:
        return {}


# ---------------------------------------------------------------- inspect

def cmd_inspect(args):
    settings = _resolve_settings(args)
    paths = inputs.expand_inputs(args.paths)
    existing = [p for p in paths if os.path.exists(p)]
    if not existing:
        raise FatalError("no input files matched: " + ", ".join(args.paths))
    _check_output_folder(settings.output_dir, existing)
    images = []
    for p in paths:
        info = inputs.inspect_image(p)
        if info.status == "ok":
            info.corner_busyness = _measure(p, settings, info)
        images.append(info.to_dict())
    print(json.dumps({"settings": settings.to_dict(), "images": images}, indent=2))
    return 0


# ---------------------------------------------------------------- apply

def _load_analysis(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise FatalError(f"cannot read analysis file: {exc}")
    if isinstance(data, dict):
        data = data.get("images", [])
    if not isinstance(data, list) or not data:
        raise FatalError("analysis file must contain a non-empty list of images")
    return data


def _plan_watermark(settings, entry, info):
    """Return (status, reason, corner). Raises ImageError when corners are missing."""
    if settings.domain is None:
        return "none", None, None
    if not settings.watermark_enabled:
        return "disabled", None, None
    if watermark.too_small((info.width, info.height)):
        return "skipped", f"image is smaller than {watermark.MIN_SHORT_SIDE} px on its shorter side", None
    labels = entry.get("corners")
    if not isinstance(labels, dict) or any(labels.get(c) not in CORNER_LABELS for c in CORNERS):
        raise ImageError("corner labels (free, subject, face_or_text) are required when a domain is supplied")
    return "pending", None, labels


def _process(entry, settings, taken, seen_alts, seen_titles):
    path = entry.get("path", "")
    info = inputs.inspect_image(path)
    res = Result(original_filename=info.original_filename, domain=settings.domain)
    if info.status != "ok":
        res.status = "skipped" if info.status == "unsupported" else "failed"
        res.reason = info.reason
        return res

    md = entry.get("metadata")
    if not isinstance(md, dict):
        raise ImageError("metadata is missing for this image")
    problems = rules.validate_metadata(md, entry.get("visible_text") or [], settings.domain)
    problems += rules.duplicate_problems(md, seen_alts, seen_titles)
    if problems:
        raise ImageError("; ".join(problems))

    ext = os.path.splitext(path)[1]
    name = naming.build_filename(md.get("filename_stem", ""), ext, settings.domain)
    wm_status, wm_reason, labels = _plan_watermark(settings, entry, info)
    name = naming.resolve_collision(name, taken, md.get("distinguisher"))

    loaded, corner = None, None
    if wm_status == "pending":
        loaded = writer.load_upright(path)
        text = domain.ascii_form(settings.domain)
        box_size = watermark.text_box_size(text, loaded.image.size, settings.size)
        busy = corners.measure_corners(loaded.image.convert("RGB"), box_size,
                                       watermark.margin_for(loaded.image.size))
        corner = corners.choose_corner(labels, busy, settings.position)
        if corner is None:
            wm_status, wm_reason, loaded = "skipped", "every corner holds a face or text", None
        else:
            loaded.image, _ = watermark.apply_watermark(
                loaded.image, text, corner, settings.opacity, settings.size)
            wm_status = "applied"

    out_folder = settings.output_dir
    width, height = writer.write_output(path, out_folder, name, loaded=loaded)
    if (width, height) != (info.width, info.height):
        raise ImageError(f"output size {width}x{height} differs from {info.width}x{info.height}")

    taken.add(name.lower())
    seen_alts.add(md["alt"].strip().lower())
    seen_titles.add(md["title"].strip().lower())
    res.new_filename = name
    res.alt, res.title = md["alt"].strip(), md["title"].strip()
    res.description = md["description"].strip()
    res.tags = [t.strip() for t in md["tags"]]
    res.watermark_status, res.watermark_reason, res.watermark_position = wm_status, wm_reason, corner
    res.width, res.height = width, height
    return res


def cmd_apply(args):
    settings = _resolve_settings(args)
    entries = _load_analysis(args.analysis)
    paths = [e.get("path", "") for e in entries if isinstance(e, dict)]
    _check_output_folder(settings.output_dir, [p for p in paths if p])
    os.makedirs(settings.output_dir, exist_ok=True)

    taken, seen_alts, seen_titles, results = set(), set(), set(), []
    for entry in entries:
        if not isinstance(entry, dict) or not entry.get("path"):
            results.append(Result(original_filename="(unknown)", status="failed",
                                  reason="analysis entry has no path", domain=settings.domain))
            continue
        try:
            results.append(_process(entry, settings, taken, seen_alts, seen_titles))
        except ImageError as exc:
            results.append(Result(original_filename=os.path.basename(entry["path"]),
                                  status="failed", reason=str(exc), domain=settings.domain))
        except Exception as exc:  # one failing image must not stop the others
            results.append(Result(original_filename=os.path.basename(entry["path"]),
                                  status="failed", reason=f"unexpected error: {exc}",
                                  domain=settings.domain))
    report.write_report(results, settings.output_dir)
    print(report.to_markdown(results))
    return 0


# ---------------------------------------------------------------- entry point

def build_parser():
    p = argparse.ArgumentParser(prog="seo_image")
    sub = p.add_subparsers(dest="command", required=True)
    for name, fn in (("inspect", cmd_inspect), ("apply", cmd_apply)):
        sp = sub.add_parser(name)
        if name == "inspect":
            sp.add_argument("paths", nargs="+")
        else:
            sp.add_argument("analysis")
        sp.add_argument("--site")
        sp.add_argument("--out")
        sp.add_argument("--config", help="path to seo-image.config.json (default: ./seo-image.config.json)")
        sp.set_defaults(func=fn)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except FatalError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

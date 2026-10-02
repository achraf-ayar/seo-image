"""Project config file and settings resolution (flags > config > defaults)."""
import json
import os

from .domain import normalise_domain
from .errors import FatalError
from .models import CORNERS, Settings

CONFIG_NAME = "seo-image.config.json"
TOP_KEYS = {"domain", "output_dir", "watermark"}
WM_KEYS = {"enabled", "position", "opacity", "size"}


def validate_config(cfg):
    if not isinstance(cfg, dict):
        raise FatalError("config must be a JSON object")
    unknown = set(cfg) - TOP_KEYS
    if unknown:
        raise FatalError(f"unknown config keys: {', '.join(sorted(unknown))}")
    if cfg.get("domain") is not None and not isinstance(cfg["domain"], str):
        raise FatalError("config 'domain' must be a string or null")
    if "output_dir" in cfg and not isinstance(cfg["output_dir"], str):
        raise FatalError("config 'output_dir' must be a string")
    wm = cfg.get("watermark", {})
    if not isinstance(wm, dict):
        raise FatalError("config 'watermark' must be an object")
    unknown = set(wm) - WM_KEYS
    if unknown:
        raise FatalError(f"unknown watermark config keys: {', '.join(sorted(unknown))}")
    if "enabled" in wm and not isinstance(wm["enabled"], bool):
        raise FatalError("watermark.enabled must be true or false")
    if "position" in wm and wm["position"] not in CORNERS:
        raise FatalError(f"watermark.position must be one of {', '.join(CORNERS)}")
    for key, lo, hi in (("opacity", 0.1, 1.0), ("size", 1, 6)):
        if key in wm:
            v = wm[key]
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not lo <= v <= hi:
                raise FatalError(f"watermark.{key} must be a number from {lo} to {hi}")
    return cfg


def load_config(path=None):
    path = path or os.path.join(os.getcwd(), CONFIG_NAME)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            cfg = json.load(fh)
    except json.JSONDecodeError as exc:
        raise FatalError(f"config file is not valid JSON: {exc}")
    return validate_config(cfg)


def resolve_settings(config, site=None, out=None, context=None):
    wm = config.get("watermark", {})
    defaults = Settings()
    domain = site if site is not None else config.get("domain")
    return Settings(
        domain=normalise_domain(domain),
        watermark_enabled=wm.get("enabled", defaults.watermark_enabled),
        position=wm.get("position", defaults.position),
        opacity=wm.get("opacity", defaults.opacity),
        size=wm.get("size", defaults.size),
        output_dir=out if out is not None else config.get("output_dir", defaults.output_dir),
        context=context,
    )

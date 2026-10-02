"""Filename rules: normalisation, limits, and collision resolution."""
import os
import re
import unicodedata

from .errors import ImageError

MAX_WORDS = 5
MAX_CHARS = 60

# Camera prefixes are always dropped; the words below only when followed by digits.
CAMERA_ALWAYS = {"img", "dsc", "dscn", "dscf", "dcim", "pxl", "mvimg"}
CAMERA_WITH_DIGITS = {"photo", "image", "pic", "picture"}
COUNTER_WORDS = {"final", "copy", "edited", "edit", "new", "version", "v"}


def _tokens(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t]


def _is_digits(token):
    return token.isdigit()


def _clean_tokens(tokens):
    out = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        nxt = tokens[i + 1] if i + 1 < len(tokens) else None
        if t in CAMERA_ALWAYS or re.fullmatch(r"(img|dsc|dscn|dscf|dcim|pxl)\d+", t):
            i += 1
            while i < len(tokens) and _is_digits(tokens[i]):
                i += 1  # the camera counter that follows
            continue
        if (t in CAMERA_WITH_DIGITS or t in COUNTER_WORDS) and nxt and _is_digits(nxt):
            i += 2
            continue
        if re.fullmatch(r"v\d+", t):
            i += 1
            continue
        if _is_digits(t):
            # keep a number that describes content: it is followed by a word (3-seater)
            if nxt and not _is_digits(nxt):
                out.append(t)
            i += 1
            continue
        out.append(t)
        i += 1
    return out


def _dedupe(tokens):
    seen, out = set(), []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _remove_domain(tokens, domain):
    if not domain:
        return tokens
    d = _tokens(domain)
    if not d:
        return tokens
    out, i = [], 0
    while i < len(tokens):
        if tokens[i:i + len(d)] == d:
            i += len(d)
        else:
            out.append(tokens[i])
            i += 1
    return out


def _cap(tokens):
    tokens = tokens[:MAX_WORDS]
    while len("-".join(tokens)) > MAX_CHARS and len(tokens) > 1:
        tokens = tokens[:-1]
    stem = "-".join(tokens)
    return stem[:MAX_CHARS].rstrip("-")


def build_filename(stem, extension, domain=None):
    """Return a compliant filename built from the agent's stem and the original extension."""
    tokens = _remove_domain(_dedupe(_clean_tokens(_tokens(stem))), domain)
    tokens = _dedupe(tokens)
    result = _cap(tokens)
    if not result:
        raise ImageError("filename has no usable descriptive words")
    ext = extension.lower()
    if ext and not ext.startswith("."):
        ext = "." + ext
    return result + ext


def resolve_collision(name, taken, distinguisher=None):
    """Return a name not in `taken` (a set of lowercase names for this batch)."""
    if name.lower() not in taken:
        return name
    stem, ext = os.path.splitext(name)
    words = stem.split("-")
    if distinguisher:
        extra = [t for t in _dedupe(_clean_tokens(_tokens(distinguisher))) if t not in words]
        candidate_words = words + extra
        candidate = "-".join(candidate_words)
        if extra and len(candidate_words) <= MAX_WORDS and len(candidate) <= MAX_CHARS \
                and (candidate + ext).lower() not in taken:
            return candidate + ext
    n = 2
    while True:
        suffix = f"-{n}"
        base = stem[: MAX_CHARS - len(suffix)].rstrip("-")
        candidate = f"{base}{suffix}{ext}"
        if candidate.lower() not in taken:
            return candidate
        n += 1

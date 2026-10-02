"""Domain normalisation (FR-021)."""
import re

from .errors import FatalError

_LABEL = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")


def normalise_domain(value):
    """Return the clean host name, or raise FatalError. None or '' gives None."""
    if value is None or not str(value).strip():
        return None
    host = str(value).strip()
    host = re.sub(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://", "", host)
    host = host.lstrip("/")
    host = re.split(r"[/?#]", host, maxsplit=1)[0]
    host = host.rsplit("@", 1)[-1]
    host = re.sub(r":\d+$", "", host)
    host = host.strip(".").lower()
    if host.startswith("www."):
        host = host[4:]
    try:
        ascii_host = host.encode("idna").decode("ascii")
    except UnicodeError:
        raise FatalError(f"invalid domain: {value!r}")
    labels = ascii_host.split(".")
    if len(labels) < 2 or not all(_LABEL.match(label) for label in labels) \
            or not (labels[-1].isalpha() and len(labels[-1]) >= 2 or labels[-1].startswith("xn--")):
        raise FatalError(f"invalid domain: {value!r}")
    return host


def ascii_form(domain):
    """The ASCII (punycode) form used when drawing, since the font is Latin only."""
    return domain.encode("idna").decode("ascii")

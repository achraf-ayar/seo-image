"""Metadata rules: deterministic checks on what the agent drafted."""
import re

MAX_ALT = 124  # under 125 characters
MAX_TITLE = 70
MAX_TAGS = 8
BAD_ALT_STARTS = ("image of", "picture of", "photo of")
ABBREVIATIONS = ("e.g", "i.e", "etc", "vs", "approx", "no", "St", "Mr", "Mrs", "Dr")
SHORT_WORDS = 4  # words shorter than this are ignored by the stuffing check
# A host name such as shop.example.net: labels, then a lowercase top-level label. A capitalised
# last label ("shelf.It") is a missing space after a full stop, not a domain.
HOST = re.compile(r"\b(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+(?-i:[a-z]{2,24})\b|\bwww\.|https?://", re.I)
FILE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif", "svg", "heic", "tiff", "bmp", "raw", "txt",
                   "pdf", "html", "htm", "json", "xml", "css", "js", "py", "md", "csv", "doc", "docx",
                   "zip", "mp4", "mov"}


def sentence_count(text):
    """A sentence ends at . ! or ? followed by a space and a capital letter."""
    text = text.strip()
    if not text:
        return 0
    for abbr in ABBREVIATIONS:
        text = re.sub(rf"\b{re.escape(abbr)}\.", abbr.replace(".", "") + "\x00", text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return len([p for p in parts if p.strip()])


def _stuffed(alt):
    counts = {}
    for w in re.findall(r"[a-z]+", alt.lower()):
        if len(w) >= SHORT_WORDS:
            counts[w] = counts.get(w, 0) + 1
    return sorted(w for w, c in counts.items() if c > 2)


def hosts_in(text):
    """Host names mentioned in `text` (file names such as photo.jpg are not hosts)."""
    found = []
    for m in HOST.finditer(text or ""):
        host = m.group(0).rstrip("/:").lower()
        if host.rsplit(".", 1)[-1] in FILE_EXTENSIONS:
            continue
        found.append(host)
    return found


def _unseen_hosts(fields, visible_text):
    visible = " ".join(visible_text or []).lower()
    problems = []
    for label, text in fields:
        for host in hosts_in(text):
            if host not in visible:
                problems.append(f'{label} mentions the domain or site "{host}", which is not visible in the image')
    return problems


def validate_metadata(md, visible_text=(), domain=None):
    """Return a list of human-readable violations (empty means valid)."""
    problems = []
    alt = (md.get("alt") or "").strip()
    title = (md.get("title") or "").strip()
    desc = (md.get("description") or "").strip()
    tags = md.get("tags")

    if not alt:
        problems.append("alt text is empty")
    else:
        if len(alt) > MAX_ALT:
            problems.append(f"alt text is {len(alt)} characters; must be under 125")
        if alt.lower().startswith(BAD_ALT_STARTS):
            problems.append('alt text must not start with "image of", "picture of" or "photo of"')
        for w in _stuffed(alt):
            problems.append(f'alt text repeats the word "{w}" more than twice (keyword stuffing)')

    if not title:
        problems.append("title is empty")
    elif len(title) > MAX_TITLE:
        problems.append(f"title is {len(title)} characters; must be at most {MAX_TITLE}")

    if not desc:
        problems.append("description is empty")
    else:
        n = sentence_count(desc)
        if n < 1 or n > 2:
            problems.append(f"description has {n} sentences; must have 1 or 2")
        if len(desc.split()) < 5:
            problems.append("description is too short to give real context")

    if not isinstance(tags, list):
        problems.append("tags must be a list")
    else:
        clean = [str(t).strip() for t in tags]
        if any(not t for t in clean):
            problems.append("tags must not be empty strings")
        if not 1 <= len(clean) <= MAX_TAGS:
            problems.append(f"{len(clean)} tags; must have 1 to {MAX_TAGS} (3 to 8 is typical, fewer when the image has less to say)")
        lowered = [t.lower() for t in clean]
        if len(set(lowered)) != len(lowered):
            problems.append("tags must be unique (case-insensitive)")
    fields = [("alt text", alt), ("title", title), ("description", desc)]
    if isinstance(tags, list):
        fields += [("a tag", str(t)) for t in tags]
    problems += _unseen_hosts(fields, visible_text)
    return problems


def duplicate_problems(md, seen_alts, seen_titles):
    """Flag alt text or titles already used earlier in the batch."""
    problems = []
    if (md.get("alt") or "").strip().lower() in seen_alts:
        problems.append("alt text is identical to another image in this batch")
    if (md.get("title") or "").strip().lower() in seen_titles:
        problems.append("title is identical to another image in this batch")
    return problems

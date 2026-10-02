"""Principle I / FR-019: the skill never references a specific website or brand."""
import os
import re

SKILL = os.path.join(os.path.dirname(__file__), "..", "..", ".claude", "skills", "seo-image")
ALLOWED_HOSTS = {"example.com", "example.org", "example.net"}
HOST = re.compile(r"\b(?:[a-z0-9-]+\.)+(?:com|org|net|io|co|fr|de|uk|ma|app|dev|shop|store|info|biz|eu|us|ca)\b", re.I)
URL = re.compile(r"https?://[^\s\"')>]+", re.I)
CODE_LIKE = {"os.path", "self.scan", "pil.image"}  # attribute chains that look like hosts
BRANDS = ("amazon", "etsy", "shopify", "wordpress", "woocommerce", "ikea", "nike", "apple", "google",
          "pinterest", "instagram", "facebook")


def skill_files():
    for root, _, files in os.walk(SKILL):
        if "__pycache__" in root:
            continue
        for f in files:
            yield os.path.join(root, f)


def allowed(host):
    host = host.lower()
    return host in ALLOWED_HOSTS or host.endswith(".example") or host.endswith(tuple("." + h for h in ALLOWED_HOSTS))


def test_skill_folder_has_files():
    assert any(f.endswith("SKILL.md") for f in skill_files())


def test_no_hardcoded_domains():
    offenders = []
    for path in skill_files():
        text = open(path, encoding="utf-8").read()
        for m in URL.findall(text):
            host = re.sub(r"^https?://", "", m, flags=re.I).split("/")[0].split(":")[0]
            if not allowed(host):
                offenders.append((path, m))
        for m in HOST.findall(text):
            if not allowed(m) and not m.lower().startswith(("os.", "re.", "json.", "sys.")):
                if path.endswith(".py") and "." in m and m.split(".")[-1] in {"co", "io", "dev", "app", "us", "ca", "de", "uk", "fr", "eu", "info"}:
                    continue  # attribute access such as `self.co`
                offenders.append((path, m))
    assert offenders == []


def test_no_brand_names():
    hits = []
    for path in skill_files():
        text = open(path, encoding="utf-8").read().lower()
        for b in BRANDS:
            if re.search(rf"\b{b}\b", text):
                hits.append((path, b))
    assert hits == []


def test_skill_never_reads_the_semantic_test_data():
    """The fixtures' forbidden lists name real brands and places as canaries for fabrication.
    They are test data only; nothing in the skill may depend on them (Principle I)."""
    for path in skill_files():
        text = open(path, encoding="utf-8").read()
        assert "tests/semantic" not in text and "forbidden_terms" not in text, path

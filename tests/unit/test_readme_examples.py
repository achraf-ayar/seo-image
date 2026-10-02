"""The README examples must be real: images resolve, credits match, text equals report.json."""
import json
import os
import re

import jsonschema
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
README = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
EX = os.path.join(ROOT, "docs", "examples")
IMAGES = os.path.join(ROOT, "docs", "images")
REPORT = json.load(open(os.path.join(EX, "output", "report.json")))
SCHEMA = json.load(open(os.path.join(ROOT, "specs", "001-seo-image-skill", "contracts", "report.schema.json")))
CREDITS = open(os.path.join(EX, "CREDITS.md"), encoding="utf-8").read()


def readme_image_paths():
    paths = re.findall(r'<img[^>]+src="([^"]+)"', README) + re.findall(r"!\[[^\]]*\]\(([^)\s]+)\)", README)
    return paths


def test_every_readme_image_path_resolves():
    paths = readme_image_paths()
    assert len(paths) == 8
    for p in paths:
        assert not p.startswith(("http", "/")), p
        assert os.path.isfile(os.path.join(ROOT, p)), p


def test_every_relative_link_resolves():
    for target in re.findall(r"\]\((?!http)([^)#\s]+)\)", README):
        assert os.path.exists(os.path.join(ROOT, target)), target


def test_no_unused_or_old_placeholder_images():
    used = {os.path.basename(p) for p in readme_image_paths()}
    assert set(os.listdir(IMAGES)) == used
    assert "before-after.png" not in README and "watermark-corners.png" not in README


def test_web_copies_are_small_and_proportional():
    for p in readme_image_paths():
        full = os.path.join(ROOT, p)
        with Image.open(full) as im:
            assert im.width <= 800, p
            assert os.path.getsize(full) < 150 * 1024, p
    for r in REPORT["results"]:
        stem = os.path.splitext(r["original_filename"])[0]
        with Image.open(os.path.join(EX, "originals", r["original_filename"])) as src, \
                Image.open(os.path.join(IMAGES, f"{stem}-original.jpg")) as web:
            assert abs(web.width / web.height - src.width / src.height) < 0.01


def test_report_is_the_skills_own_and_outputs_are_full_quality():
    jsonschema.validate(REPORT, SCHEMA)
    results = REPORT["results"]
    assert len(results) == 4 and all(r["status"] == "ok" for r in results)
    assert {r["domain"] for r in results} == {"example.com"}
    for r in results:
        with Image.open(os.path.join(EX, "originals", r["original_filename"])) as a, \
                Image.open(os.path.join(EX, "output", r["new_filename"])) as b:
            assert a.size == b.size == (r["width"], r["height"])
            assert not b.getexif().get_ifd(0x8825)
    outputs = {f for f in os.listdir(os.path.join(EX, "output")) if f != "report.json"}
    assert outputs == {r["new_filename"] for r in results}


def test_readme_text_matches_report_json_exactly():
    for r in REPORT["results"]:
        assert f'| `{r["original_filename"]}` | `{r["new_filename"]}` |' in README
        assert f'- **Alt:** {r["alt"]}\n' in README
        assert f'- **Title:** {r["title"]}\n' in README
        assert f'- **Description:** {r["description"]}\n' in README
        assert f'- **Tags:** {", ".join(r["tags"])}\n' in README
        assert f'- **Watermark:** {r["watermark_status"]}, {r["watermark_position"]} ({r["domain"]})\n' in README
        assert f'alt="{r["alt"]}"' in README
    # nothing in the example section that is not from the report: count the metadata bullets
    assert README.count("- **Alt:**") == README.count("- **Tags:**") == len(REPORT["results"])


def test_busy_corner_example_explains_the_move():
    moved = [r for r in REPORT["results"] if r["watermark_position"] != "bottom-right"]
    assert [r["original_filename"] for r in moved] == ["IMG_2290.jpg"]
    assert f'**{moved[0]["watermark_position"]}**' in README


def test_credits_match_the_files():
    originals = sorted(os.listdir(os.path.join(EX, "originals")))
    assert len(originals) == 4
    rows = [l for l in CREDITS.splitlines() if l.startswith("| `")]
    assert sorted(re.match(r"\| `([^`]+)`", l).group(1) for l in rows) == originals
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        assert len(cells) == 6 and all(cells), row
        assert "CC0" in cells[3] and cells[4].startswith("https://commons.wikimedia.org/wiki/File:")
    assert "https://creativecommons.org/publicdomain/zero/1.0/" in CREDITS
    for author in ("rawpixel.com", "Jarosław Ceborski", "Saral Shots", "Peter Miranda"):
        assert author in CREDITS
    # every photo in the report is credited
    assert {r["original_filename"] for r in REPORT["results"]} == set(originals)

"""Rebuild the README example images and the README examples section from the real run.

Reads docs/examples/originals/ and docs/examples/output/ (produced by the seo-image skill) plus
docs/examples/output/report.json. Writes web-sized copies (800 px wide, JPEG quality 78) to
docs/images/ and replaces the block between the markers in README.md. The full-quality files in
docs/examples/ are never changed. Needs Pillow.
"""
import json
import os
import re

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EX = os.path.join(ROOT, "docs", "examples")
IMAGES = os.path.join(ROOT, "docs", "images")
README = os.path.join(ROOT, "README.md")
START, END = "<!-- examples:start -->", "<!-- examples:end -->"
WEB_WIDTH, QUALITY = 800, 78

# order and captions of the examples; the metadata itself always comes from report.json
EXAMPLES = [
    ("IMG_4821.jpg", "a) Product shot", None),
    ("DSC_0412.jpg", "b) Room interior", None),
    ("IMG_7305.jpg", "c) Food", None),
    ("IMG_2290.jpg", "d) Busy corner",
     "The bottom-right corner (and the top-right) holds the chalkboard's handwriting, so the "
     "watermark moved to the quietest free corner: **{position}**."),
]


def web_copy(src, dest):
    with Image.open(src) as im:
        im = im.convert("RGB")
        h = round(im.height * WEB_WIDTH / im.width)
        im.resize((WEB_WIDTH, h), Image.LANCZOS).save(dest, "JPEG", quality=QUALITY, optimize=True,
                                                       progressive=True)


def section(results):
    by = {r["original_filename"]: r for r in results}
    lines = []
    for original, heading, why in EXAMPLES:
        r = by[original]
        stem = os.path.splitext(original)[0]
        with Image.open(os.path.join(EX, "originals", original)) as a, \
                Image.open(os.path.join(EX, "output", r["new_filename"])) as b:
            assert a.size == b.size == (r["width"], r["height"]), original
            size = f"{b.width} × {b.height} px"
        web_copy(os.path.join(EX, "originals", original), os.path.join(IMAGES, f"{stem}-original.jpg"))
        web_copy(os.path.join(EX, "output", r["new_filename"]), os.path.join(IMAGES, f"{stem}-output.jpg"))
        alt_before = f"Original photo {original}, before processing"
        wm = f'{r["watermark_status"]}, {r["watermark_position"]} ({r["domain"]})'
        lines += [
            f"#### {heading}", "",
            "| Before | After |", "|:---:|:---:|",
            f'| <img src="docs/images/{stem}-original.jpg" width="380" alt="{alt_before}"> '
            f'| <img src="docs/images/{stem}-output.jpg" width="380" alt="{r["alt"]}"> |',
            f'| `{original}` | `{r["new_filename"]}` |', "",
            f'- **Alt:** {r["alt"]}',
            f'- **Title:** {r["title"]}',
            f'- **Description:** {r["description"]}',
            f'- **Tags:** {", ".join(r["tags"])}',
            f"- **Watermark:** {wm}",
            f"- **Size:** {size}, unchanged", "",
        ]
        if why:
            lines += [why.format(position=r["watermark_position"]), ""]
    return "\n".join(lines).rstrip() + "\n"


def main():
    os.makedirs(IMAGES, exist_ok=True)
    results = json.load(open(os.path.join(EX, "output", "report.json")))["results"]
    text = open(README, encoding="utf-8").read()
    block = f"{START}\n\n{section(results)}\n{END}"
    new, n = re.subn(re.escape(START) + r".*?" + re.escape(END), lambda m: block, text, flags=re.S)
    assert n == 1, "README.md needs one examples block between the markers"
    open(README, "w", encoding="utf-8").write(new)
    print("wrote", sorted(os.listdir(IMAGES)))


if __name__ == "__main__":
    main()

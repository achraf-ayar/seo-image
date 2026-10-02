"""Rebuild the README images from the real pipeline: python docs/make_readme_images.py

Runs the helper on the neutral fixtures (simple drawings, example.com only) and composes
before/after pictures. Needs Pillow.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, ".claude", "skills", "seo-image", "scripts")
FIXTURES = os.path.join(ROOT, "tests", "semantic", "fixtures")
OUT = os.path.join(ROOT, "docs", "images")
FREE = {c: "free" for c in ("top-left", "top-right", "bottom-left", "bottom-right")}
INK, MUTED, BG, ACCENT = (30, 34, 42), (110, 118, 130), (246, 247, 249), (37, 99, 235)


def font(size, bold=False):
    return ImageFont.load_default(size=size)


def run_pipeline(jobs, site="example.com"):
    """jobs: [(fixture name, camera-style original name, metadata, corners)] -> {original: output path}"""
    tmp = tempfile.mkdtemp()
    src_dir, out_dir = os.path.join(tmp, "photos"), os.path.join(tmp, "seo-images")
    os.makedirs(src_dir)
    entries = []
    for fixture, original, md, corners in jobs:
        path = os.path.join(src_dir, original)
        shutil.copy(os.path.join(FIXTURES, fixture + ".png"), path)
        entries.append({"path": path, "image_type": "illustration", "primary_subject": md["alt"],
                        "corners": corners, "metadata": md})
    analysis = os.path.join(tmp, "analysis.json")
    json.dump(entries, open(analysis, "w"))
    env = dict(os.environ, PYTHONPATH=SCRIPTS)
    subprocess.run([sys.executable, "-m", "seo_image", "apply", analysis, "--site", site,
                    "--out", out_dir], check=True, env=env, capture_output=True, cwd=tmp)
    report = json.load(open(os.path.join(out_dir, "report.json")))["results"]
    return src_dir, out_dir, report


def panel(img, title, subtitle, width=560):
    h = round(img.height * width / img.width)
    img = img.convert("RGB").resize((width, h), Image.LANCZOS)
    card = Image.new("RGB", (width, h + 74), BG)
    card.paste(img, (0, 0))
    d = ImageDraw.Draw(card)
    d.text((14, h + 10), title, fill=INK, font=font(22))
    d.text((14, h + 42), subtitle, fill=MUTED, font=font(17))
    return card


def compose(panels, heading, arrows=True, gap=70, pad=36, caption=None):
    w = sum(p.width for p in panels) + gap * (len(panels) - 1) + pad * 2
    h = max(p.height for p in panels) + pad * 2 + 54 + (30 if caption else 0)
    canvas = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(canvas)
    d.text((pad, pad - 6), heading, fill=INK, font=font(28))
    x, y = pad, pad + 54
    for i, p in enumerate(panels):
        canvas.paste(p, (x, y))
        d.rectangle([x, y, x + p.width - 1, y + p.height - 1], outline=(222, 226, 232), width=2)
        x += p.width
        if i < len(panels) - 1:
            if arrows:
                cy = y + panels[0].height // 2 - 40
                d.polygon([(x + 14, cy - 18), (x + gap - 14, cy), (x + 14, cy + 18)], fill=ACCENT)
            x += gap
    if caption:
        d.text((pad, h - pad - 4), caption, fill=MUTED, font=font(17))
    return canvas


def main():
    os.makedirs(OUT, exist_ok=True)
    mug = {"filename_stem": "red mug on shelf", "alt": "Red mug with a handle on a brown shelf next to a green plant",
           "title": "Red mug on a shelf", "description": "A simple drawing of a red mug on a brown shelf. A green plant stands at its left.",
           "tags": ["mug", "shelf", "plant", "illustration"]}
    hills = {"filename_stem": "green hills under blue sky", "alt": "Green hills below a light blue sky with a sun",
             "title": "Hills landscape drawing", "description": "A simple drawing of green hills under a light blue sky. A yellow sun is at the upper right.",
             "tags": ["hills", "landscape", "sun", "sky"]}
    room = {"filename_stem": "blue sofa beside window", "alt": "Blue sofa in front of a beige wall with a window",
            "title": "Blue sofa and window", "description": "A simple drawing of a blue sofa against a beige wall. A window is on the right above a brown floor.",
            "tags": ["sofa", "window", "room"]}
    busy = dict(FREE, **{"bottom-right": "subject"})
    src, out, rep = run_pipeline([
        ("red-mug-on-shelf", "IMG_4821.png", mug, FREE),
        ("hills-landscape", "DSC00417.png", hills, FREE),
        ("living-room", "photo-final-2.png", room, busy),
    ])
    by = {r["original_filename"]: r for r in rep}

    def pair(original):
        r = by[original]
        return (Image.open(os.path.join(src, original)), Image.open(os.path.join(out, r["new_filename"])), r)

    a, b, r = pair("IMG_4821.png")
    compose([panel(a, "Original", r["original_filename"]),
             panel(b, "Publication-ready", f'{r["new_filename"]}  ·  watermark: {r["watermark_position"]}')],
            "One image in, one SEO-ready file out",
            caption="Same size, same quality. The original is never touched; the copy goes to a separate folder.").save(
        os.path.join(OUT, "before-after.png"))

    a1, b1, r1 = pair("DSC00417.png")
    a2, b2, r2 = pair("photo-final-2.png")
    compose([panel(b1, "Free corner", f'bottom-right  ·  {r1["new_filename"]}', 420),
             panel(b2, "Busy corner", f'moved to {r2["watermark_position"]}  ·  {r2["new_filename"]}', 420)],
            "The watermark picks the quietest corner", arrows=False,
            caption="Default is bottom-right. If it holds a face, text or the main subject, the least busy corner is used.").save(
        os.path.join(OUT, "watermark-corners.png"))
    shutil.rmtree(os.path.dirname(src), ignore_errors=True)
    print("wrote", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    main()

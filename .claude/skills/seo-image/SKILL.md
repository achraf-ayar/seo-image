---
name: seo-image
description: Prepare images for website publication. Looks at each image, writes an SEO filename, alt text, title, description and tags from what is visible, optionally adds a subtle domain watermark, and saves new copies in a separate output folder with a report. Use when the user wants images renamed, described or watermarked for a web page.
argument-hint: <image(s) or glob> [--site <domain>] [--context "<page topic>"] [--out <folder>]
---

# seo-image

Turn images into publication-ready files plus accurate metadata. You do the looking; a
deterministic helper does everything mechanical. Originals are never touched: every result is a
new file in an output folder (default `seo-images/`, or `--out`, or `output_dir` in the config).

## Arguments

- `<image(s)>`: one image, several images, or a glob such as `./images/*`.
- `--site <domain>`: adds a watermark with that domain. Without a domain there is no watermark,
  and you must never invent one.
- `--context "<page topic>"`: the topic of the page the images are for (see Context below).
- `--out <folder>`: output folder.

Optional project config `seo-image.config.json` in the project root (see
`seo-image.config.example.json` next to this file): `domain`, `output_dir`, and
`watermark: {enabled, position, opacity, size}`. **Flags override the config**, and the config
overrides the built-in defaults.

## Steps

The helper lives in `scripts/` next to this file. Run it from the project root (the folder that
holds the config file), with Pillow installed (`python3 -c "import PIL"`; if it fails, run
`pip install pillow`).

The two commands (run each as one line; set `PYTHONPATH` in front, as shown):

```bash
PYTHONPATH="${CLAUDE_SKILL_DIR}/scripts" python3 -m seo_image inspect <paths...> [--site D] [--out DIR]
PYTHONPATH="${CLAUDE_SKILL_DIR}/scripts" python3 -m seo_image apply <analysis.json> [--site D] [--out DIR]
```

1. **Inspect.** The `inspect` command prints JSON: the resolved
   settings and, per file, `status` (`ok`, `unsupported`, `unreadable`), displayed `width` and
   `height`, and a `reason` when not ok. Exit code 2 means a fatal problem (invalid domain, unsafe
   output folder, nothing matched): tell the user the message and stop.
2. **Look at every `ok` image** with your own vision (open it with the Read tool). For each one
   work out: the primary subject, key secondary objects, the scene, any visible text, and the
   image type (product, room, food, person, landscape, screenshot, illustration, ...).
3. **Write the analysis JSON** to a temporary file outside the originals' folder, for example
   `${TMPDIR:-/tmp}/seo-image-analysis.json`. It is a list with **one entry per inspected file**,
   in the same order. For files that were not `ok`, write only `{"path": "..."}`; the helper
   reports them as skipped or failed. For `ok` files:

   ```json
   {
     "path": "images/photo.jpg",
     "image_type": "...", "primary_subject": "...", "secondary_objects": ["..."],
     "scene": "...", "visible_text": ["text exactly as shown"],
     "corners": {"top-left": "free", "top-right": "free",
                 "bottom-left": "free", "bottom-right": "subject"},
     "metadata": {
       "filename_stem": "...", "alt": "...", "title": "...",
       "description": "...", "tags": ["..."], "distinguisher": "..."
     }
   }
   ```

   `corners` is needed **only when a domain is supplied** (flag or config). Label each corner
   `free`, `subject` (main subject or other important content is there) or `face_or_text` (a face
   or readable text is there). The helper chooses the position; you only report what is where.
4. **Apply.** The `apply` command prints a Markdown table and
   writes `report.json` in the output folder. Show the user the table, and the output folder.
5. **Fix rejections.** An image with `status: failed` was rejected with a reason (for example alt
   text too long, or a duplicate title). Correct only that entry's metadata and run `apply` again
   for the affected images. A rerun replaces same-named outputs in the output folder; it never
   touches originals. Skipped files (unsupported format, animated image) need no fix: tell the
   user they were skipped and why.

## What to write

- **filename_stem**: descriptive, at most 5 words, lowercase words. No camera names, no
  meaningless numbers, no repeated words, no domain. The helper adds the original extension and
  enforces the limits. Numbers that describe content (`3-seater-sofa`) are fine.
- **alt**: accessibility first, natural, under 125 characters. Do not start with "image of",
  "picture of" or "photo of". No keyword stuffing. Mention the domain only if it is visible in
  the image (then also list it in `visible_text`).
- **title**: short, natural, useful in a media library (at most 70 characters).
- **description**: 1 or 2 sentences of real context, not a keyword list.
- **tags**: usually 3 to 8 relevant, non-redundant tags; fewer (down to 1) if the image has less to
  say. Never pad with filler to reach a number.
- **distinguisher** (optional): one word from this image's own analysis that tells it apart from
  similar images, used only when two filenames collide.

## Rules you must follow

- **Visual evidence first.** Describe only what is visible or explicitly supplied by the user.
  Never invent brands, places, models, materials, prices, names, events or identities. When the
  image is ambiguous, use conservative wording ("a wooden-looking shelf" is not allowed unless
  wood is evident; "a shelf" is).
- **People.** Never identify a person and never infer sensitive characteristics (ethnicity,
  religion, health, age, orientation, and similar). Describe what they are doing or wearing, not
  who they are.
- **Context.** `--context` may refine wording only where the image supports it. If the context
  conflicts with, or is not shown in, the image, ignore that part. Never copy context claims
  into metadata as facts.
- **Batch.** Analyse each image independently with its own unique alt text and title. Never
  reuse another image's metadata. Several similar images still each get their own wording and a
  `distinguisher`.
- **No site references.** Never mention a specific website unless the user supplied it as the
  domain or it is visible in the image.
- Never edit, move or delete the original files, and never write outside the output folder
  (apart from the temporary analysis file).

## Out of scope

Format conversion (WebP/AVIF), compression, social-media or responsive variants, CMS
integration, uploads, embedding metadata into the files, and multiple watermark styles.

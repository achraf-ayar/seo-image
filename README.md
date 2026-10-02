# seo-image

> An AI coding-agent skill that gets images ready for your website: a descriptive filename, alt text,
> title, description and tags written from what is **actually visible**, plus an optional subtle
> domain watermark. Your originals are never touched.

![One image in, one SEO-ready file out](docs/images/before-after.png)

## What you get

| For every image | |
|---|---|
| **Filename** | lowercase, hyphenated, at most 5 words / 60 characters, original extension kept, no camera names, never the domain |
| **Alt text** | under 125 characters, natural, never starts with "image of", no keyword stuffing |
| **Title** and **description** | a short media-library title and 1–2 sentences of real context |
| **Tags** | 3–8 relevant, non-redundant tags (fewer when the image has less to say) |
| **Watermark** | only when you give a domain: small, semi-transparent, readable, away from faces and text |
| **Report** | a Markdown table in chat and `report.json` in the output folder |

```text
| Original      | New file           | Status | Alt                                       | Domain      | Watermark | Position     |
|---------------|--------------------|--------|-------------------------------------------|-------------|-----------|--------------|
| IMG_4821.png  | red-mug-on-shelf.png | ok   | Red mug with a handle on a brown shelf... | example.com | applied   | bottom-right |
```

## How it works

The agent looks at the images; a small, deterministic Python helper does everything mechanical.

```mermaid
flowchart LR
    A["/seo-image photos/* --site example.com"] --> B["inspect<br/>resolve inputs, sizes,<br/>corner busy scores"]
    B --> C["Agent looks at each image<br/>subject, scene, visible text,<br/>which corners are taken"]
    C --> D["apply<br/>validate metadata, name files,<br/>watermark, save, report"]
    D --> E[("seo-images/<br/>new files + report.json")]
    O[("Originals<br/>never modified")] -.-> B
```

- **Visual evidence first.** Metadata describes only what is visible or what you supplied. No
  invented brands, places, models, materials, prices, names or identities, and people are never
  identified.
- **Deterministic where it can be.** Naming, validation, watermarking, saving and reporting are plain
  code with automated tests; understanding the image is the agent's own vision.
- **Generic.** No website, brand or content category is built in. A domain only ever comes from
  `--site` or your config.

### The watermark picks the quietest corner

![The watermark picks the quietest corner](docs/images/watermark-corners.png)

## Install

The skill is the folder `.claude/skills/seo-image/`. Copy it into any project's `.claude/skills/`
(or into `~/.claude/skills/`). It needs Python 3.10+ and Pillow (`pip install pillow`).

## Use

```text
/seo-image <image(s) or glob> [--site <domain>] [--context "<page topic>"] [--out <folder>]
```

Examples: `/seo-image hero.jpg`, `/seo-image ./images/* --site example.com`,
`/seo-image a.png b.png --context "kitchen renovation guide"`.

You get a Markdown table in chat and `report.json` in the output folder (default `seo-images/`):
original and new filename, alt, title, description, tags, domain, watermark status and position.

- Filenames: lowercase, hyphenated, at most 5 words and 60 characters, original extension kept,
  never containing the domain.
- No domain means no watermark. A domain is never invented.
- Supported inputs: JPEG, PNG, WebP. Other files (and animated images) are skipped and reported.
- Outputs are saved upright, with GPS data removed and the colour profile kept. Files that need no
  change are copied byte for byte (and keep all their metadata); a re-encoded file keeps its ICC
  profile and EXIF but not XMP or IPTC fields such as creator or copyright. Metadata is reported only; it is not written into the files.
- Rerunning replaces same-named outputs in the output folder; originals are never touched.

## Config

Optional `seo-image.config.json` in the project root (example:
`.claude/skills/seo-image/seo-image.config.example.json`):

```json
{"domain": "example.com", "output_dir": "seo-images",
 "watermark": {"enabled": true, "position": "bottom-right", "opacity": 0.6, "size": 2.5}}
```

Command-line flags (`--site`, `--out`) override the config; the config overrides the defaults.

## Tests

```bash
pip install pillow pytest jsonschema
pytest                       # unit and integration tests (187)
python tests/semantic/check_report.py seo-images/report.json   # after running on the fixtures
```

Semantic quality (is the metadata faithful to the image?) is checked against reviewed fixtures;
see `tests/semantic/README.md`.

## Design

Specification, plan and tasks are in `specs/001-seo-image-skill/`; the principles are in
`.specify/memory/constitution.md`.

## Rebuild the pictures

The images above are made by the real pipeline from neutral fixtures:
`python docs/make_readme_images.py`.

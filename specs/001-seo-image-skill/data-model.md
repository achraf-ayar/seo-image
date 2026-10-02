# Data Model: SEO Image Skill

Plain JSON records exchanged between the agent and the helper. No database.

## Settings (resolved)
- `domain`: string or null (normalised)
- `watermark.enabled`: bool (default true when a domain exists)
- `watermark.position`: `bottom-right` (default) | `bottom-left` | `top-right` | `top-left`
- `watermark.opacity`: 0.1–1.0 (default 0.6)
- `watermark.size`: percent of the shorter side, 1–6 (default 2.5)
- `output_dir`: path (default `seo-images`)
- `context`: string or null
- Precedence: CLI flag > config file > default.

## InspectedImage (output of `inspect`)
- `path`, `original_filename`, `format` (jpeg|png|webp), `width`, `height` (displayed size, after EXIF orientation), `has_gps` (bool), `animated` (bool)
- `corner_busyness`: `{top-left, top-right, bottom-left, bottom-right}` numbers (0 = flat, higher = busier)
- `status`: `ok` | `unsupported` | `unreadable`, with `reason` when not ok

## Analysis (written by the agent, input to `apply`), one per image
- `path`
- `image_type`: free word (product, room, food, person, landscape, screenshot, illustration, ...)
- `primary_subject`, `secondary_objects[]`, `scene`, `visible_text[]`
- `corners`: `{corner: free | subject | face_or_text}` for all four corners; required only when a domain is supplied and the watermark is enabled
- `metadata`: `{filename_stem, alt, title, description, tags[], distinguisher?}`

## Result (entry in the report), one per input
- `original_filename`, `new_filename` (null if failed)
- `status`: `ok` | `failed` | `skipped`; `reason` when not ok
- `alt`, `title`, `description`, `tags[]`
- `domain`: string or null
- `watermark_status`: `applied` | `none` | `disabled` | `skipped`; `watermark_reason` when skipped
- `watermark_position`: corner or null
- `width`, `height` (output, equal to the inspected dimensions)

## Rules and states
- Image flow: `inspected` → `analysed` → `validated` → `written` (or `failed`/`skipped` from any step, never stopping the batch).
- Filenames are unique within a batch, case-insensitively. Alt text and titles are unique within a batch; a later duplicate fails with a reason.
- A rerun replaces existing outputs of the same name in the output folder. Originals are never touched.
- Animated images are `unsupported` (skipped).

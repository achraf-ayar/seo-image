---

description: "Task list for the SEO Image Skill"
---

# Tasks: SEO Image Skill

**Input**: Design documents from `/specs/001-seo-image-skill/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: INCLUDED. Constitution Principle VI requires an automated test for every deterministic rule, and reviewed fixtures for semantic quality.

**Organization**: Tasks are grouped by user story. Helper code lives in `.claude/skills/seo-image/scripts/seo_image/` (written below as `SKILL_PKG/`), tests in `tests/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story the task belongs to (US1–US5)

## Phase 1: Setup

- [X] T001 Create the directory layout from plan.md: `.claude/skills/seo-image/scripts/seo_image/`, `tests/unit/`, `tests/integration/`, `tests/semantic/fixtures/`
- [X] T002 Add `pyproject.toml` at the repo root declaring Python >=3.10, dependency `pillow`, dev dependencies `pytest` and `jsonschema`, and pytest `pythonpath = [".claude/skills/seo-image/scripts"]`
- [X] T003 [P] Add `SKILL_PKG/__init__.py`, `SKILL_PKG/__main__.py` (calls `cli.main()`), and a stub `SKILL_PKG/cli.py` defining `main()` so the package imports and runs

---

## Phase 2: Foundational (blocks all user stories)

- [X] T004 Define shared types in `SKILL_PKG/models.py` per data-model.md: `Settings`, `InspectedImage` (width and height are the displayed size after EXIF orientation), `Analysis`, `Result`, corner names `top-left|top-right|bottom-left|bottom-right`; statuses `ok|failed|skipped`; watermark statuses `applied|none|disabled|skipped`
- [X] T005 [P] Define error classes in `SKILL_PKG/errors.py`: `FatalError` (exit 2: bad domain, unsafe output folder, no inputs) and `ImageError` (per-image, carries a reason)
- [X] T006 [P] Add synthetic image helpers in `tests/conftest.py`: build JPEG/PNG/WebP files with chosen size and colour/gradient/noise regions; a JPEG with EXIF orientation 6 and a GPS block and an ICC profile; an RGBA PNG and RGBA WebP with transparent regions; an animated GIF and animated WebP; a corrupt file; a file-hash helper
- [X] T007 [P] Update the repo-root `.gitignore`: ignore `seo-images/`, `__pycache__/`, `.pytest_cache/`, and un-ignore the skill folder so it is tracked even though `.claude/` is ignored (`.claude/*`, `!.claude/skills/`, `.claude/skills/*`, `!.claude/skills/seo-image/`)

**Checkpoint**: package imports; pytest collects without errors.

---

## Phase 3: User Story 1 - Prepare a single image (Priority: P1) 🎯 MVP

**Goal**: One image in; a renamed upright copy with validated metadata and a report out; original untouched; semantic quality checkable.

**Independent Test**: Run `inspect` then `apply` on one synthetic image with no domain; the output exists under a compliant name with the displayed dimensions, the original hash is unchanged, the report has all fields with watermark `none`.

### Tests for User Story 1

- [X] T008 [P] [US1] Unit tests for filename normalisation in `tests/unit/test_naming.py`: lowercase, hyphens, ASCII transliteration; camera patterns dropped (`IMG_1234`, `DSC0042`, `photo-01`); pure counters dropped (`final-2`, `copy-3`, bare numbers); content numbers kept (`3-seater-sofa`, `4-burner-stove`, `1950s`); repeated words dropped; at most 5 words and 60 characters on a word boundary; original extension kept lowercased; an empty result raises `ImageError`; the domain never appears in the name
- [X] T009 [P] [US1] Unit tests for metadata rules in `tests/unit/test_rules.py`: alt under 125 characters; alt must not start with "image of", "picture of" or "photo of"; no content word repeated more than twice in alt; title non-empty and at most 70 characters; description is 1–2 sentences using the rule "split on `.`, `!`, `?` followed by a space and a capital letter, ignoring `e.g.`, `i.e.`, `etc.`, `vs.`, `approx.`, `no.`, `St.`, `Mr.`, `Mrs.`, `Dr.`"; tags 3–8 and unique case-insensitively; a domain in alt only if it is in `visible_text`
- [X] T010 [P] [US1] Unit tests for input detection in `tests/unit/test_inputs.py`: JPEG/PNG/WebP detected by content not extension; `inspect` reports displayed dimensions (a rotated EXIF-6 image of 300x200 stored reports 200x300); `has_gps` set correctly; animated GIF and animated WebP get `unsupported`; corrupt files get `unreadable`; each non-ok status carries a reason
- [X] T011 [P] [US1] Unit tests for the writer in `tests/unit/test_writer.py`: bytes copied unchanged (hash equal) only when no watermark, no GPS and upright; a rotated photo is saved upright with the orientation tag reset and displayed dimensions; GPS EXIF removed from the output while the ICC profile is kept; transparency preserved on RGBA PNG/WebP re-encode; the output folder is created; the original hash is unchanged; a rerun replaces the same-named output via a temporary file and rename
- [X] T012 [P] [US1] Integration test in `tests/integration/test_single_image.py`: `inspect` then `apply` on one image; output exists, displayed width and height equal, aspect ratio equal, original hash unchanged, `report.json` validates against `contracts/report.schema.json` with `jsonschema`, watermark `none`, domain null; plus a rotated-photo case (upright output, displayed dimensions, no GPS)
- [X] T013 [P] [US1] Create 6 neutral reviewed fixtures in `tests/semantic/fixtures/`: images (generated or public domain, no real brands) each with `expected.json` holding `must_mention`, `must_not_mention` and a `forbidden_terms` list (names, brands, locations not visible in the image). One fixture MUST show a person and forbid names, identity claims and sensitive-characteristic words
- [X] T014 [P] [US1] Write `tests/semantic/README.md`: how a reviewer runs the skill on each fixture and confirms results against `expected.json`; any fabricated brand, place, model, material, price, name, event or identity fails; includes a reviewer tally table (accurate/natural per alt and description) recorded for SC-007
- [X] T015 [US1] Add `tests/semantic/check_report.py`: takes a `report.json` and the fixtures, flags forbidden terms and missing required terms, and prints the reviewer tally percentage against the 90% target; add `tests/unit/test_check_report.py` covering its flags

### Implementation for User Story 1

- [X] T016 [P] [US1] Implement `SKILL_PKG/naming.py`: `build_filename(stem, extension)` applying research.md §6
- [X] T017 [P] [US1] Implement `SKILL_PKG/rules.py`: `validate_metadata(metadata, visible_text)` returning a list of violations, applying research.md §7 (duplicate alt/title detection is added in T038)
- [X] T018 [P] [US1] Implement `SKILL_PKG/inputs.py`: `inspect_image(path)` returning `InspectedImage` (format by content, displayed dimensions, `has_gps`, `animated`, status and reason)
- [X] T019 [US1] Implement `SKILL_PKG/writer.py`: `save_output(src, out_folder, filename)` per research.md §3 and §12: byte copy only when nothing must change; otherwise re-encode upright with GPS removed, ICC kept, alpha kept; write to a temporary file then rename over any existing same-named output (depends on T005)
- [X] T020 [US1] Implement `SKILL_PKG/report.py`: build `report.json` (shape in `contracts/report.schema.json`) and a Markdown table summary from a list of `Result`
- [X] T021 [US1] Implement `SKILL_PKG/cli.py` subcommands `inspect` and `apply` per `contracts/cli.md` for the single-image path with default output folder `seo-images/` and `--out`; refuse an output folder that is an input's folder or contains one (exit 2); `apply` reads the analysis JSON, validates it with `rules.py`, writes the output and report, prints the Markdown summary; `corners` is not required without a domain
- [X] T022 [US1] Write `.claude/skills/seo-image/SKILL.md`: frontmatter (`name: seo-image`, description, argument hint), then instructions: parse arguments, run `inspect`, view each image with the agent's own vision, write the analysis JSON per `contracts/analysis-input.schema.json` using only visible or user-supplied facts (never invent brands, places, models, materials, prices, names, events or identities; never identify people or infer sensitive traits; conservative wording when unsure), run `apply`, relay the Markdown summary and fix any rejected metadata

**Checkpoint**: US1 works end to end and is the shippable MVP, with reviewed fixtures available.

---

## Phase 4: User Story 2 - Watermark with a domain (Priority: P2)

**Goal**: With a domain, add a subtle watermark, bottom-right by default with fallback and skip rules.

**Independent Test**: Run with `--site` on images with free and busy corners; verify position, bounds and report fields.

### Tests for User Story 2

- [X] T023 [P] [US2] Unit tests for domain normalisation in `tests/unit/test_domain.py`: strips scheme, credentials, port, path, query, fragment and leading `www.`; lowercases; keeps subdomains; accepts internationalised names; rejects values without a dot or with invalid characters via `FatalError`
- [X] T024 [P] [US2] Unit tests for corner choice in `tests/unit/test_corners.py`: bottom-right when `free`; otherwise the `free` corner with the lowest busy score; otherwise the `subject` corner with the lowest busy score; skip when all corners are `face_or_text`; a configured starting position replaces the default
- [X] T025 [P] [US2] Unit tests for the watermark in `tests/unit/test_watermark.py`: output dimensions equal input; text pixels lie fully inside the image with a 2% margin; pixels changed only inside the text box; light outline text on a dark background and dark on a light one; opacity applied; skipped with a reason when the shorter side is under 200 px; alpha channel preserved on RGBA PNG and WebP (transparent pixels outside the text stay transparent)
- [X] T026 [P] [US2] Integration test in `tests/integration/test_watermark_flow.py`: domain given gives report `applied` and the corner; the domain is absent from the filename and from alt text unless it is in `visible_text`; no domain gives `none`; a domain without `corners` in the analysis fails that image with a reason; the watermarked output has no GPS data and keeps the ICC profile

### Implementation for User Story 2

- [X] T027 [P] [US2] Implement `SKILL_PKG/domain.py`: `normalise_domain(value)` per FR-021 and research.md §8
- [X] T028 [P] [US2] Implement `SKILL_PKG/corners.py`: `measure_busyness(image, box)` (grey-level standard deviation plus edge density) and `choose_corner(corners, busyness, start)` per research.md §5
- [X] T029 [US2] Implement `SKILL_PKG/watermark.py`: `apply_watermark(image, text, corner, opacity, size_percent)` using Pillow's scalable default font, margin 2% of the shorter side, adaptive colour, thin contrast outline, alpha preserved (research.md §4); skip below a 200 px shorter side
- [X] T030 [US2] Extend `SKILL_PKG/writer.py` to accept an already-watermarked image and save it with the same re-encode rules as `save_output` (JPEG quality 95, PNG lossless, WebP lossless-or-95; ICC kept; GPS removed; upright)
- [X] T031 [US2] Extend `SKILL_PKG/inputs.py` `inspect` output with `corner_busyness` and wire `--site`, domain normalisation, corner choice and report fields (`watermark_status`, `watermark_reason`, `watermark_position`) into `SKILL_PKG/cli.py`; require `corners` only when a domain is supplied and the watermark is enabled
- [X] T032 [US2] Update `.claude/skills/seo-image/SKILL.md`: mark each corner `free`, `subject` or `face_or_text` in the analysis when a domain is supplied, and mention the domain in alt text only if it is visible in the image

**Checkpoint**: US1 and US2 both work independently.

---

## Phase 5: User Story 3 - Batch processing (Priority: P2)

**Goal**: Many images or a glob; unique names and metadata; failures isolated.

**Independent Test**: Run over a folder with near-identical images and one corrupt file; N report entries, distinct names, failure isolated.

### Tests for User Story 3

- [X] T033 [P] [US3] Unit tests for collisions in `tests/unit/test_collisions.py`: first uses the `distinguisher` word within limits; else `-2`, `-3`; checks names assigned earlier in the same batch only (case-insensitive); an existing file in the output folder is NOT a collision
- [X] T034 [P] [US3] Integration test in `tests/integration/test_batch.py`: glob over 5 images (two with the same stem, one corrupt, one `.gif`, one animated GIF); expects one report entry per input, distinct output names, `failed`/`skipped` entries with reasons, others completed, original hashes unchanged; two images with identical alt text (and separately identical titles) get the later one rejected with a reason
- [X] T035 [P] [US3] Integration test in `tests/integration/test_output_safety.py`: an output folder equal to an input's folder is refused with exit 2; an output folder that contains an input's folder is refused with exit 2; a sub-folder of an input's folder (the default `seo-images/`) is allowed; no files written in the refused cases; no inputs matched exits 2

### Implementation for User Story 3

- [X] T036 [US3] Extend `SKILL_PKG/naming.py` with `resolve_collision(name, taken, distinguisher)` per research.md §6 (batch only)
- [X] T037 [US3] Extend `SKILL_PKG/inputs.py` and `SKILL_PKG/cli.py` to expand globs and multiple paths, de-duplicate inputs, and skip non-image and unsupported files with a reason
- [X] T038 [US3] Wrap per-image work in `SKILL_PKG/cli.py` `apply` in a try/except for `ImageError` so one failure becomes a `failed` entry and the batch continues; add duplicate alt text / title detection to `SKILL_PKG/rules.py` and use it in `apply` (research.md §7)
- [X] T039 [US3] Update `.claude/skills/seo-image/SKILL.md`: analyse each image independently, never reuse another image's metadata, give a `distinguisher` word taken from the image's own analysis when similar images exist

**Checkpoint**: batch runs are safe and complete.

---

## Phase 6: User Story 4 - Project configuration (Priority: P3)

**Goal**: Config defaults, flags override.

**Independent Test**: Config domain used with no flags; `--site` wins; `enabled: false` suppresses the watermark.

### Tests for User Story 4

- [X] T040 [P] [US4] Unit tests for config in `tests/unit/test_config.py`: loads `seo-image.config.json`; validates against `contracts/config.schema.json`; rejects unknown keys and out-of-range opacity (0.1–1.0) or size (1–6); flags override config which overrides defaults; a missing file means defaults
- [X] T041 [P] [US4] Integration test in `tests/integration/test_config_flow.py`: config domain used; `--site other.example` wins; `watermark.enabled: false` gives report `disabled`; `--out` overrides `output_dir`

### Implementation for User Story 4

- [X] T042 [US4] Implement `SKILL_PKG/config.py`: `load_config(project_root)` and `resolve_settings(config, flags)` per data-model.md Settings
- [X] T043 [US4] Wire `resolve_settings` into `SKILL_PKG/cli.py` (`--site`, `--out`) so `inspect` prints the resolved settings and `apply` uses them
- [X] T044 [P] [US4] Add `.claude/skills/seo-image/seo-image.config.example.json` using only the placeholder domain `example.com`, and document precedence in `SKILL.md`

---

## Phase 7: User Story 5 - Context refines wording (Priority: P3)

**Goal**: `--context` only refines wording where the image supports it.

**Independent Test**: A matching context affects wording; a contradicting one is ignored (human reviewed).

- [X] T045 [P] [US5] Add 2 context fixtures to `tests/semantic/fixtures/` (one with a supported context, one with an unsupported context), each with `expected.json` including `context` and `supported: true|false`; extend `tests/semantic/check_report.py` to flag unsupported context terms appearing in the output
- [X] T046 [US5] Update `.claude/skills/seo-image/SKILL.md`: `--context` may refine wording only when the image supports it; visual evidence wins on conflict

---

## Phase 8: Polish & Cross-Cutting

- [X] T047 [P] Add `tests/unit/test_no_hardcoded_sites.py`: scans the skill folder for hard-coded domains or brand names, allowing only `example.com`, `example.org` and the `.example` TLD (Principle I, FR-019)
- [X] T048 [P] Add `tests/integration/test_originals_immutable.py`: hashes every input before and after a mixed run (with and without watermark, with a rotated and a GPS photo) and asserts equality (Principle III)
- [X] T049 [P] Add `tests/integration/test_rerun_determinism.py`: running the same analysis and settings twice gives identical output pixels and identical report metadata, and the second run replaces the first outputs (no `-2` files) while originals are untouched (FR-016, FR-020)
- [X] T050 Walk through every scenario in `quickstart.md` and record outcomes at the end of that file; fix any gaps found
- [X] T051 [P] Add a short `README.md` at the repo root: what the skill does, install location, usage, config, and how to run the tests
- [ ] T052 (suite, timing and SC-001–SC-006 done; SC-007 reviewer tally still to be recorded by a human) Run the full suite (`pytest tests/unit tests/integration`), add a 50-image timing check (`tests/integration/test_batch_timing.py`: 50 synthetic web-size photos processed by `apply` in under 60 seconds), confirm SC-001 to SC-006, and record the reviewer tally from `tests/semantic/README.md` for SC-007

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → user stories → Phase 8.
- **US1** has no story dependencies (MVP). **US2** depends on US1's writer, CLI and report. **US3** depends on US1's naming and CLI. **US4** depends on US1's CLI and US2's domain use. **US5** depends on US1's `SKILL.md` and fixtures.
- US3 and US4 can proceed in parallel once US1 is done (shared `cli.py` edits must be sequenced).
- Within a story: tests first (should fail), then implementation.

## Parallel Examples

- US1: T008–T015 together; then T016, T017, T018 together.
- US2: T023–T026 together; then T027 and T028 together.
- Polish: T047, T048, T049 and T051 together.

## Implementation Strategy

1. Complete Setup and Foundational.
2. Deliver US1 and validate (MVP: a working skill with no watermark, plus reviewed fixtures).
3. Add US2 (watermark), then US3 (batch), then US4 (config), then US5 (context fixtures).
4. Finish with Polish and the quickstart walkthrough.

---

## Phase 9: Convergence

**Purpose**: Remaining work found by `/speckit-converge` on 2026-10-02 (existing tasks are untouched).

- [X] T053 [US1] Make a byte-copied output keep no location data: extend `has_gps` in `SKILL_PKG/inputs.py` and `needs_change` in `SKILL_PKG/writer.py` to detect XMP location properties (`GPSLatitude`, `GPSLongitude`, `GPSAltitude`, and similar `exif:GPS*` keys) in JPEG, PNG (iTXt `XML:com.adobe.xmp`) and WebP (XMP chunk) so those files are re-encoded without them; confirmed today that a PNG and a WebP with XMP GPS are copied with the location intact, per FR-014 (contradicts)
- [X] T054 [P] [US1] Add tests for XMP location stripping in `tests/unit/test_inputs.py` (the `has_gps` flag for each of the three formats) and `tests/unit/test_writer.py` (output bytes contain none of the `GPS` XMP keys, ICC profile kept, dimensions unchanged), plus a no-watermark run in `tests/integration/test_originals_immutable.py` that includes such files, per FR-014 and Constitution VI (missing)
- [X] T055 [P] [US1] Verify and cover the remaining EXIF location paths in `SKILL_PKG/writer.py` `load_upright`: an EXIF thumbnail or MakerNote that holds coordinates must not survive a re-encode; add a test in `tests/unit/test_writer.py` and drop those fields if present, per FR-014 (partial)
- [X] T056 Relax `specs/001-seo-image-skill/contracts/analysis-input.schema.json` so an entry for a file that is not `ok` may contain only `path` (as `SKILL.md` instructs), while an `ok` entry still needs `image_type`, `primary_subject` and `metadata`; add a test in `tests/integration/test_batch.py` that validates the analysis used there against the schema, per FR-017 and plan: contracts (partial)
- [X] T057 [P] Document the behaviour not yet in the contracts: `--config` on `inspect` and `apply` and the `{"images": [...]}` analysis wrapper in `specs/001-seo-image-skill/contracts/cli.md`, and in `specs/001-seo-image-skill/research.md` §8 that internationalised domains are reported as entered but drawn in their ASCII (punycode) form because the bundled font is Latin only, per plan: research §8 (unrequested)
- [X] T058 [P] Add direct unit tests for `SKILL_PKG/report.py` in `tests/unit/test_report.py`: `to_markdown` escapes `|` and newlines and shows `-` for empty cells and the status reason, `write_report` writes valid JSON that validates against `contracts/report.schema.json` and leaves no `.tmp` file, per Constitution VI (partial)

---

## Phase 10: Convergence

**Purpose**: Remaining work found by the second `/speckit-converge` run on 2026-10-02 (earlier tasks are untouched).

- [X] T059 [US1] Fix the command in `.claude/skills/seo-image/SKILL.md`: `SEO="PYTHONPATH=... python3 -m seo_image"` followed by `$SEO inspect ...` fails in a shell (`PYTHONPATH=...: No such file or directory`, because an assignment produced by expansion is not an environment assignment); write the invocation as `PYTHONPATH="${CLAUDE_SKILL_DIR}/scripts" python3 -m seo_image <command> ...` (or export the variable first) in every step, and add a test in `tests/unit/test_skill_instructions.py` that extracts the command lines from `SKILL.md` and runs the first one with `--help` in a shell, per US1/AC1 and plan: skill layout (partial)
- [X] T060 Allow fewer than 3 tags when the image has less to say: change the tag rule in `SKILL_PKG/rules.py` from "3 to 8" to "1 to 8, each non-empty and unique", update `tests/unit/test_rules.py` (1 and 2 tags valid, 0 and 9 invalid), set `minItems` to 1 in `specs/001-seo-image-skill/contracts/analysis-input.schema.json`, and fix the tags bullet in `.claude/skills/seo-image/SKILL.md` that says "never fewer than 3", per FR-007 (partial)
- [X] T061 [P] Reject invented or unseen domains in metadata: extend `validate_metadata` in `SKILL_PKG/rules.py` so a host name (for example `shop.example.net`) in the alt text, title, description or any tag is a violation unless it appears in `visible_text`, whether or not a domain was supplied; add tests in `tests/unit/test_rules.py` (hostname rejected with and without a supplied domain, accepted when listed in `visible_text`, ordinary text such as `e.g.` or `3.5 mm` not flagged), per FR-004, FR-008 and FR-013 (partial)
- [X] T062 [P] Resolve the brand and place names in the fixtures' forbidden lists (`tests/semantic/fixtures/*.json`) against Constitution I: either replace real brand, product and place names with neutral placeholders, or state in `tests/semantic/README.md` that those lists are test data used only to detect fabricated facts and are never read by the skill, and extend `tests/unit/test_no_hardcoded_sites.py` to assert the skill folder never reads `tests/semantic/`, per Constitution I (unrequested)

---

## Phase 11: Convergence

**Purpose**: Remaining work found by the third `/speckit-converge` run on 2026-10-02 (earlier tasks are untouched).

- [X] T063 [US2] Stop 16-bit grayscale images from being blown out by re-encoding: confirmed today that a 16-bit grayscale PNG (Pillow mode `I`/`I;16`, value 40000) comes out of `apply_watermark` in `SKILL_PKG/watermark.py` and `write_output` in `SKILL_PKG/writer.py` as pure white (255, 255, 255) because the values are clipped to 8 bits; scale such images to 8-bit properly (value / 256) before drawing, add a test in `tests/unit/test_watermark.py` and `tests/unit/test_writer.py` that a mid-grey 16-bit PNG keeps its brightness (within 2 levels) and size after watermarking and after a GPS-stripping re-encode, per FR-014 and SC-001 (partial)
- [X] T064 [P] [US2] Handle CMYK JPEGs with colour management: in `SKILL_PKG/writer.py` `_encode`, a CMYK image is converted to RGB without conversion through its embedded profile and may keep that CMYK profile on RGB data; convert through the profile to sRGB when one is present (plain conversion otherwise), embed an sRGB profile or none, and add a test in `tests/unit/test_writer.py` with a CMYK JPEG carrying a profile, per FR-014 (partial)
- [X] T065 [P] Align the metadata promise with what the code does: the Clarifications entry in `specs/001-seo-image-skill/spec.md` says "original metadata carried over where the format allows", but a re-encode keeps only the ICC profile and EXIF (without GPS, orientation and MakerNote) and drops XMP and IPTC fields such as creator and copyright; either carry XMP and IPTC across with the location properties removed (with tests per format in `tests/unit/test_writer.py`), or reword that Clarifications entry and FR-014 in `spec.md`, the README and `research.md` §3 to say that only ICC and non-location EXIF are kept, per FR-014 and the 2026-10-02 clarification on metadata (partial)

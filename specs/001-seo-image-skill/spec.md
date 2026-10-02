# Feature Specification: SEO Image Skill

**Feature Branch**: `001-seo-image-skill`

**Created**: 2026-10-02

**Status**: Draft

**Input**: User description: "Build a reusable AI coding-agent skill named \"seo-image\" that prepares images for website publication: SEO filename, alt text, title, description, tags, optional domain watermark, saved to a separate output folder, with a per-image report."

## Clarifications

### Session 2026-10-02

- Q: Should alt/title/description be embedded in the file metadata or only reported? → A: Report only; the skill does not write EXIF/XMP/IPTC. A file that is copied byte for byte keeps all its original metadata. A file that has to be re-encoded keeps only its ICC profile and its EXIF without location data; XMP and IPTC fields (such as creator or copyright) are not carried over.
- Q: In what form should the per-image report be delivered? → A: Both a Markdown summary in chat and a JSON report file in the output folder.
- Q: When all four corners are busy, what should the watermark do? → A: Use the least-busy corner, but skip the watermark if it would overlap a face or text; report the skip and reason.
- Q: How are filename collisions resolved? → A: Add a distinguishing descriptive word from each image's own analysis; fall back to a numeric suffix (-2, -3) when none is available.
- Q: Which input formats does v1 accept, and what happens to others? → A: JPEG, PNG and WebP, saved in their own format; any other format is skipped and reported as unsupported. Animated GIF/WebP is unsupported and reported as skipped.
- Q: What does "dimensions" mean for photos with an EXIF orientation? → A: Displayed dimensions after orientation is applied; outputs are saved upright with the orientation normalised.
- Q: What happens on a rerun when output files already exist? → A: Collision handling applies within a single batch only; a rerun replaces existing outputs of the same name in the output folder. Originals are never touched.
- Q: What location data does an output keep? → A: GPS/location EXIF is stripped from outputs; the ICC profile is kept.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prepare a single image (Priority: P1)

A site owner invokes `/seo-image <image>` on one image. The skill looks at the image, produces a descriptive filename, alt text, title, description and tags, and saves a renamed copy in an output folder. The original is untouched. A report lists the results.

**Why this priority**: This is the core value: one image in, publication-ready file and accurate metadata out. Everything else builds on it.

**Independent Test**: Run on one image with no domain. Verify a new file exists in the output folder under a compliant filename, the original is byte-identical, dimensions match, and the report holds all metadata fields.

**Acceptance Scenarios**:

1. **Given** a photo of a wooden desk with a laptop and a lamp, **When** the user runs the skill with no options, **Then** the output has a lowercase hyphenated filename of at most about 5 words and 60 characters keeping the original extension, alt text under 125 characters, a title, a 1–2 sentence description, and 3–8 tags, all describing only what is visible.
2. **Given** the same run, **When** it completes, **Then** the original file is unchanged, the new file has identical pixel dimensions and aspect ratio, and the report shows watermark status "none" with no domain.
3. **Given** an image containing visible text, **When** it is processed, **Then** the text may inform the metadata only as read, never altered or embellished.

---

### User Story 2 - Watermark with a domain (Priority: P2)

The user supplies a domain with `--site`. The skill adds a subtle text watermark to the saved copy, in the bottom-right corner by default. If that corner holds important content (faces, text, main subject), it uses the least busy other corner.

**Why this priority**: Watermarking is the second headline feature and depends on the P1 pipeline.

**Independent Test**: Run with `--site` on an image whose bottom-right corner is empty and on one where it holds a subject; check watermark position and that the report matches.

**Acceptance Scenarios**:

1. **Given** an image with a plain bottom-right corner and a domain, **When** processed, **Then** a small, readable, semi-transparent watermark appears bottom-right with a safe margin and contrast suited to the local background, and the report shows status "applied" and position "bottom-right".
2. **Given** an image whose bottom-right corner holds a face or text, **When** processed, **Then** the watermark is placed in the least busy other corner and the report states that corner.
3. **Given** a domain is supplied, **When** filename and alt text are produced, **Then** the domain does not appear in the filename, and appears in alt text only if visible in the image.
4. **Given** no domain is supplied (by flag or config), **When** processed, **Then** no watermark is added and no domain is invented.

---

### User Story 3 - Process many images in a batch (Priority: P2)

The user passes several images or a glob such as `./images/*`. Each image is analysed independently, gets unique metadata, and one failure does not stop the rest.

**Why this priority**: Real sites have many images; batch support makes the skill practical.

**Independent Test**: Run on a folder with several images, including two similar ones and one corrupt file; check unique filenames, results for the good images, and a failure entry for the bad one.

**Acceptance Scenarios**:

1. **Given** a glob matching 10 images, **When** run, **Then** the report contains one entry per image, each with its own metadata.
2. **Given** two images that would receive the same filename, **When** processed, **Then** the collision is resolved so both outputs exist with distinct names and neither overwrites the other.
3. **Given** one unreadable or unsupported file in the batch, **When** run, **Then** the others complete and the report marks that file as failed with a reason.

---

### User Story 4 - Project configuration (Priority: P3)

The user stores defaults in a project config file: domain, watermark enabled, position, opacity and size. Command-line flags override config values.

**Why this priority**: Saves repetition across runs; the skill works without it.

**Independent Test**: Set a domain in config and run with no flags, then run with a different `--site`; check the flag wins.

**Acceptance Scenarios**:

1. **Given** a config with a domain and watermark enabled, **When** the skill runs with no flags, **Then** the config values are used.
2. **Given** the same config and `--site other-domain`, **When** run, **Then** the flag value is used.
3. **Given** config sets watermark disabled and a domain is present, **When** run, **Then** no watermark is applied and the report says it was disabled.

---

### User Story 5 - Context refines wording (Priority: P3)

The user passes `--context "<page topic>"`. The skill uses it only to refine wording where the image supports it.

**Why this priority**: Improves relevance but is optional.

**Independent Test**: Run with a context that matches the image and with one that contradicts it; check only the matching one affects wording.

**Acceptance Scenarios**:

1. **Given** a context consistent with the image, **When** processed, **Then** metadata may use the context's terms.
2. **Given** a context the image does not support, **When** processed, **Then** metadata follows the image and ignores the unsupported claims.

---

### Edge Cases

- Ambiguous or low-quality image: use conservative, generic wording; never guess brands, places, models, materials, prices, names or events.
- Image contains a person: describe visible appearance-neutral facts (such as pose or activity); never identify them or infer sensitive characteristics.
- Image shows a visible domain or logo text: may be mentioned in alt text only because it is visible.
- Screenshot or text-heavy image: alt text summarises purpose rather than transcribing everything.
- All corners busy: least busy corner is used; if it would still overlap a face or text, the watermark is skipped and reported with a reason.
- Very small image (shorter side under 200 px): the watermark is skipped and reported as skipped with a reason.
- Original filename already compliant: still saved to the output folder; original untouched.
- Output folder missing: created. Output folder that is an input's folder, or that contains an input's folder: refused so originals cannot be overwritten. A sub-folder of the input's folder (such as the default `seo-images/` next to the images) is allowed.
- Glob matches no files, or an input path does not exist: clear error, no output.
- Existing file in the output folder from an earlier run, with the same name: replaced by the new output. Only outputs are ever replaced, never originals.
- Non-image files and unsupported image formats matched by a glob: skipped and reported as unsupported, with no effect on the other files.
- Animated images (GIF or animated WebP): unsupported, skipped and reported. Transparent PNG and WebP images keep their transparency, including after watermarking.
- Photo with an EXIF orientation: saved upright, with the orientation normalised and reported dimensions equal to the displayed size.
- Two images in one batch with identical alt text or title: the later one is rejected with a reason so its metadata can be made unique.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The skill MUST be invocable as `/seo-image <image(s)> [--site <domain>] [--context "<page topic>"] [--out <folder>]`, accepting one image, several images, and glob patterns, for JPEG, PNG and WebP inputs; any other format MUST be skipped and reported as unsupported.
- **FR-002**: The skill MUST inspect each image's actual content and identify its primary subject, key secondary objects, scene, visible text and image type.
- **FR-003**: The skill MUST produce a filename that is lowercase and hyphen-separated, at most about 5 words and 60 characters, with no camera names, no meaningless numbers, no repeated words (camera patterns such as `IMG_1234` and pure counters such as `photo-01` or `final-2` are dropped; numbers that describe content, such as `3-seater-sofa`, `4-burner-stove` or `1950s`, are kept), keeping the original extension, and never containing the domain.
- **FR-004**: The skill MUST produce alt text under 125 characters that is natural, does not start with "image of", avoids keyword stuffing, and mentions the domain only if it is visible in the image.
- **FR-005**: The skill MUST produce a short, natural title useful in a media library.
- **FR-006**: The skill MUST produce a description of 1–2 sentences of real context, not a keyword list. A sentence ends at `.`, `!` or `?` followed by a space and a capital letter, ignoring common abbreviations (for example `e.g.`, `approx.`, `vs.`, `St.`).
- **FR-007**: The skill MUST produce 3–8 relevant, non-redundant tags, fewer when the image has less to say.
- **FR-008**: Metadata MUST describe only what is visible or explicitly supplied; the skill MUST NOT invent brands, places, models, materials, prices, names, events or identities, and MUST use conservative wording when the image is ambiguous.
- **FR-009**: The skill MUST NOT identify people or infer sensitive characteristics.
- **FR-010**: When context is supplied, the skill MUST use it only to refine wording where the image supports it; visual evidence MUST prevail on conflict.
- **FR-011**: When a domain is supplied, the skill MUST add a small, readable, semi-transparent text watermark with contrast adapted to the local background and a safe margin from edges. The watermark MUST be skipped, and reported as skipped with a reason, when the image's shorter side is under 200 px.
- **FR-012**: The watermark MUST default to the bottom-right corner; if that corner holds important content (faces, text, main subject), the skill MUST use the least busy other corner. If every corner is busy, the skill MUST use the least busy one, unless the watermark would overlap a face or text, in which case it MUST skip the watermark and report status "skipped" with the reason.
- **FR-013**: When no domain is available, the skill MUST NOT add a watermark and MUST NOT invent a domain.
- **FR-014**: The skill MUST save each result as a new file under the SEO filename in an output folder, preserving the displayed dimensions (after EXIF orientation is applied), aspect ratio and visual quality. Outputs MUST be saved upright with the orientation normalised, MUST have GPS/location EXIF stripped, and MUST keep the ICC colour profile and its other EXIF fields, while XMP and IPTC are not carried over when a file is re-encoded. Alt text, title, description and tags MUST appear only in the report and MUST NOT be written into the file's metadata. When nothing in a file has to change (no watermark, no GPS data, orientation already upright), the file MUST be copied byte for byte.
- **FR-015**: The skill MUST NOT modify, overwrite, rename or delete original files, and MUST refuse an output folder that is an input's folder or that contains an input's folder. The default output folder is `seo-images/` in the working directory and can be overridden with `--out` or the config file.
- **FR-016**: In batch mode, each image MUST be analysed independently with unique metadata, filename collisions within the batch MUST be resolved without overwriting, first by adding a distinguishing descriptive word drawn from each image's own analysis (still within the filename limits), and otherwise by a numeric suffix (-2, -3). Identical alt text or titles within a batch MUST be flagged by rejecting the later image with a reason. A failure on one image MUST NOT stop the others. On a rerun, existing outputs in the output folder with the same name MUST be replaced; originals are never touched.
- **FR-017**: The skill MUST return a report, as a Markdown summary in chat and as a JSON file in the output folder with the same content, with one entry per image containing: original filename, new filename, alt text, title, description, tags, domain, watermark status and watermark position; failed images MUST be reported with a reason.
- **FR-018**: The skill MUST read an optional project config file `seo-image.config.json` in the project root with domain, output folder (`output_dir`) and watermark enabled, position, opacity and size; command-line values (`--site`, `--out`) MUST override config values.
- **FR-019**: The skill MUST NOT reference, default to, or embed any specific website, domain, brand or content category.
- **FR-020**: Mechanical operations (file handling, naming rules, watermarking, validation) MUST behave deterministically: the same input and settings MUST give identical pixels and metadata, and every deterministic rule MUST be covered by an automated test.
- **FR-021**: The supplied domain MUST be normalised before use: trim whitespace; strip scheme, credentials, port, path, query, fragment and a leading `www.`; lowercase; allow subdomains and internationalised names. A value that is not a valid host name with at least one dot MUST stop the run with a clear error before anything is processed.
- **FR-022**: Corner labels in the analysis are required only when a domain is supplied.

### Key Entities

- **Image Job**: One input image with its path, optional context, and resolved settings (domain, watermark options).
- **Image Analysis**: What was seen: primary subject, secondary objects, scene, visible text, image type.
- **SEO Metadata**: Filename, alt text, title, description, tags for one image.
- **Watermark Settings**: Enabled flag, domain text, position, opacity, size; merged from config and flags.
- **Result Report Entry**: Per-image record of original name, new name, metadata, domain, watermark status and position, or failure reason.
- **Project Config**: Optional stored defaults for domain and watermark options.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For any supported image with an optional domain, the user receives a publication-ready file in the output folder with the exact displayed width and height and the same aspect ratio in 100% of successful runs.
- **SC-002**: 100% of generated filenames, alt texts and tag sets satisfy the stated format limits (length, case, separators, tag count, no domain in filename).
- **SC-003**: In a reviewed set of sample images, 0 outputs contain a fabricated brand, place, model, material, price, name, event or identity.
- **SC-004**: In a batch of N images, the report has exactly N entries, all successful outputs have distinct names, and the original files are unchanged in 100% of runs.
- **SC-005**: With a domain supplied, 100% of successful outputs carry a watermark that stays fully inside the image with a margin, and none sit over a detected face, text block or main subject when a freer corner exists.
- **SC-006**: A user can process a single image from command to finished report in under 1 minute of their own effort, with no setup beyond the optional config file.
- **SC-007**: In review, at least 90% of generated alt texts and descriptions are judged accurate and natural (not keyword-stuffed) by a human reviewer, and the reviewer's tally is recorded.

## Assumptions

- Users are site owners or content editors who run the skill from an AI coding-agent session in their project.
- Supported input formats for v1 are JPEG, PNG and WebP, each saved in its own format; other formats are skipped and reported as unsupported rather than converted.
- The output format equals the input format; no conversion or compression is performed.
- The config file is optional.
- Watermark text is the normalised domain (FR-021).
- Tag redundancy (for example `desk` and `desks`) is judged in reviewed-fixture review, not by a deterministic rule.
- Image understanding is done by the agent's own vision; mechanical steps are deterministic code, as the constitution requires.
- Out of scope for v1: embedding metadata (EXIF/XMP/IPTC) in files, format conversion (including to WebP/AVIF), compression, Open Graph/Pinterest/social variants, responsive sizes, CMS integration, uploads, multiple watermark styles.

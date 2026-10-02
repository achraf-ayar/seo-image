# Research: SEO Image Skill

No `NEEDS CLARIFICATION` items remained after `/speckit-clarify`. The decisions below close the open planning questions.

## 1. Division of labour
- **Decision**: Two-step helper. `inspect` resolves inputs and measures corner busyness; the agent views each image and writes an analysis JSON; `apply` validates it and produces outputs and reports.
- **Rationale**: Keeps image understanding in the agent (Principle IV) and every mechanical rule testable.
- **Alternatives**: A single script calling a vision API (adds a network dependency and credentials, violates the agent-vision principle); the agent doing file work by shell commands (not deterministic or testable).

## 2. Language and imaging library
- **Decision**: Python with Pillow; JSON for config and I/O.
- **Rationale**: Already available, handles JPEG/PNG/WebP, supports text drawing with alpha compositing, no YAML dependency needed.
- **Alternatives**: Node with sharp (heavier native install); ImageMagick CLI (external binary, harder to unit test).

## 3. Preserving quality and dimensions
- **Decision**: Copy the file bytes unchanged under the new name only when nothing has to change: no watermark, no GPS data in the file, and orientation already upright. Otherwise re-encode: JPEG quality 95 keeping subsampling; PNG lossless; WebP lossless if the source is lossless, else quality 95. In every re-encode keep the ICC profile and remaining EXIF, remove the GPS block, and keep transparency (alpha) for PNG and WebP.
- **Rationale**: Byte copy guarantees zero loss when possible. Stripping location data (FR-014) and normalising orientation require re-encoding only for the files that need it.
- **What a re-encode keeps**: the ICC profile and EXIF without GPS, orientation or MakerNote. XMP and IPTC (creator, copyright and similar) are not carried over; carrying them across with location removed would need a metadata-rewriting layer that the v1 scope does not call for (Principle V). A byte copy keeps everything. CMYK images are converted to RGB through their profile when it is valid (otherwise plainly) and 16-bit grayscale is scaled to 8-bit before drawing.
- **Location data**: a file counts as carrying location data when its EXIF has a GPS block, or its XMP (JPEG APP1, PNG iTXt including compressed, WebP XMP chunk) has GPS properties (`GPSLatitude`, `GPSLongitude`, `GPSAltitude`, `GPSPosition`, `GPSSpeed`, `GPSImgDirection`, `GPSDest*`). Such files are re-encoded; the re-encode does not carry XMP, drops the EXIF thumbnail (Pillow does not write one) and removes the opaque MakerNote, which can embed coordinates.
- **Alternatives**: Always re-encode (needless loss).
- **EXIF orientation**: "dimensions" are the displayed dimensions. `inspect` reports the displayed size; outputs are saved upright with the orientation tag reset, so the watermark is placed on the displayed image. A rotated photo is therefore re-encoded even without a watermark.

## 4. Watermark rendering
- **Decision**: Text drawn with Pillow's built-in scalable font; font height about 2.5% of the shorter side (config `size` as a percentage, default 2.5, minimum 10 px, no maximum); margin 2% of the shorter side; default opacity 0.6 (config 0.1–1.0). Colour: sample mean luminance of the background under the text box; use white text with a thin dark outline over dark areas, and dark text with a thin light outline over light areas.
- **Rationale**: Readable on any background without heavy visual weight; one style only, per scope.
- **Alternatives**: Fixed colour (fails on mixed backgrounds); shadow plus blur (extra complexity).
- **Small images**: skip when the shorter side is under 200 px; report "skipped" with reason (FR-011).

## 5. Corner selection
- **Decision**: The agent marks each corner as `free`, `subject` or `face_or_text` in the analysis. The helper picks: bottom-right if `free`; otherwise the `free` corner with the lowest busyness; otherwise the `subject` corner with the lowest busyness; otherwise skip. Busyness is the grey-level standard deviation plus edge density inside the watermark's box at that corner. A configured `position` replaces the default starting corner.
- **Rationale**: Semantic judgment (faces, text, subject) comes from vision; the measurable part (busyness) is deterministic. This matches the clarified "skip only if it would overlap a face or text" rule.
- **Alternatives**: Local face/text detection libraries (extra heavy dependencies, duplicates agent vision).

## 6. Filename rules
- **Decision**: Agent proposes a descriptive filename stem. The helper normalises it: lowercase, ASCII transliteration, non-alphanumerics to hyphens, collapse hyphens, drop camera patterns (`img`, `dsc`, `dscn`, `photo`, `image`, `pic` followed by digits) and pure counters (a bare number, or `final`, `copy`, `edited`, `v` followed by a number), but keep numbers that describe content (`3-seater-sofa`, `4-burner-stove`, `1950s`: a number attached to a following word, or a four-digit decade or year ending in `s`), drop repeated words, cap at 5 words and 60 characters on a word boundary, keep the original extension lowercased. Empty results make that image fail with a reason rather than invent a name. The domain is never part of the name.
- **Rationale**: Deterministic enforcement of every format rule regardless of what the agent drafted.
- **Collisions**: use the agent-supplied `distinguisher` word (a word from the image's own analysis) appended while respecting limits; else `-2`, `-3`. Collision checking covers names assigned earlier in the same batch only, case-insensitively. Files already in the output folder from an earlier run are replaced (see §12).

## 7. Metadata validation
- **Decision**: `apply` checks alt under 125 characters and not starting with "image of", "picture of" or "photo of"; title non-empty and at most 70 characters; description 1–2 sentences, where a sentence ends at `.`, `!` or `?` followed by a space and a capital letter, ignoring the abbreviations `e.g.`, `i.e.`, `etc.`, `vs.`, `approx.`, `no.`, `St.`, `Mr.`, `Mrs.`, `Dr.`; 1–8 tags (3–8 is typical; fewer when the image has less to say), unique case-insensitively; alt stuffing check: no content word repeated more than twice; a host name (such as `shop.example.net`) in the alt text, title, description or a tag that does not appear in `visible_text` is rejected whether or not a domain was supplied (file names such as `photo.jpg` and a capitalised last label such as `shelf.It` are not hosts); alt text or title identical (case-insensitive) to one already used by an earlier image in the batch is rejected for the later image. Failing metadata is rejected with a reason so the agent can correct it; the helper never rewrites meaning.
- **Rationale**: Format limits are deterministic; wording quality is left to the agent and checked with reviewed fixtures.
- **Domain in alt**: allowed only if the analysis's `visible_text` contains it (case-insensitive); otherwise rejected.

## 8. Domain handling
- **Decision**: Trim; strip scheme, credentials, port, path, query, fragment and a leading `www.`; lowercase; allow subdomains and IDN (converted to punycode for validity check, displayed as given); require a valid hostname with at least one dot; otherwise stop with a clear error before processing. The report shows an internationalised domain as entered (normalised, lowercase), but the watermark draws its ASCII (punycode) form, because the bundled font covers Latin characters only.
- **Rationale**: Users paste URLs; the watermark should show a clean domain; never invent one.

## 9. Output location
- **Decision**: Default `seo-images/` in the working directory (config `output_dir`, flag `--out`). Refuse if the output folder is an input's folder, or contains one, to guarantee originals cannot be overwritten. A sub-folder of an input's folder (the default `seo-images/` beside the images) cannot hold an original, so it is allowed; refusing it would make the default unusable whenever images sit in the working folder.
- **Rationale**: Principle III; spec edge case.

## 10. Report
- **Decision**: `report.json` in the output folder plus a Markdown table printed for chat, both built from one in-memory structure. Failed or skipped images are entries with `status` and `reason`.

## 11. Configuration
- **Decision**: `seo-image.config.json` in the project root: `domain`, `watermark: {enabled, position, opacity, size}`, `output_dir`. Precedence: CLI flags over config over built-in defaults. Unknown keys are rejected so typos do not silently pass.
- **Alternatives**: YAML/TOML (needs extra parser or newer Python).

## 12. Reruns and determinism
- **Decision**: Collision handling applies within one batch only. A rerun replaces existing outputs of the same name in the output folder (written to a temporary file then renamed, so a failure leaves the old output intact). Originals are never touched. The same analysis and settings must produce identical pixels and metadata.
- **Rationale**: Reruns after fixing metadata should be idempotent rather than pile up `-2` files. Originals stay protected by §9.

## 13. Corners in the analysis
- **Decision**: `corners` is optional in the analysis and required only when a domain is supplied and the watermark is enabled. An image with a domain but without `corners` fails with a reason.

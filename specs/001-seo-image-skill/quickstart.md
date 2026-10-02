# Quickstart: Validating the SEO Image Skill

## Prerequisites
- Python 3.10+ and `pip install pillow pytest`.
- The skill installed at `.claude/skills/seo-image/`.

## Run the automated checks
```bash
pytest tests/unit tests/integration
```
Expected: all pass. Each deterministic rule (filename, alt, tags, domain, config precedence, corner choice, collisions, watermark bounds, byte-identical originals, unchanged dimensions) has at least one test.

## End-to-end scenarios
Use the contracts for exact shapes: [CLI](contracts/cli.md), [analysis input](contracts/analysis-input.schema.json), [report](contracts/report.schema.json), [config](contracts/config.schema.json).

1. **Single image, no domain**: `/seo-image ./images/a.jpg`. Expect: a new file in `seo-images/`, original byte-identical, same width and height, report shows watermark `none`.
2. **With domain**: `/seo-image ./images/a.jpg --site example.com`. Expect: watermark bottom-right inside margins; report `applied`, `bottom-right`; the domain not in the filename.
3. **Busy corner**: an image whose bottom-right is marked `face_or_text`. Expect: another corner used, or `skipped` with a reason if all are face/text.
4. **Batch with collision and a bad file**: a glob over two near-identical images and one corrupt file. Expect: N report entries, distinct names, a `failed` entry for the corrupt one, the others complete.
5. **Config precedence**: config domain set, then `--site other.example`. Expect the flag value in the watermark and report.
6. **Unsupported format**: pass a `.gif`. Expect `skipped`/`failed` with the reason "unsupported", no output.
7. **Output folder that is an input's folder, or contains one**: expect refusal with no files written. A sub-folder of the input's folder is allowed.
8. **Rotated photo**: an image with EXIF orientation 6. Expect an upright output whose size equals the displayed size, GPS data removed, ICC profile kept.
9. **Transparent PNG with a watermark**: expect transparency preserved.
10. **Rerun**: run the same input and analysis twice. Expect identical pixels and metadata, and replaced (not `-2`) outputs.
11. **Duplicate alt text** in a batch: expect the later image rejected with a reason.

## Semantic check (human reviewed)
Run the skill on `tests/semantic/fixtures/`; compare each result against that fixture's reviewed expectations (must-mention and must-not-mention lists). Any fabricated detail is a failure (success criterion SC-003).

## Walkthrough record (2026-10-02)

Run against the implementation. "Test" names the automated test that covers the scenario; scenario 0
is a live run of the real command line on the eight semantic fixtures.

| # | Scenario | Result | Covered by |
|---|----------|--------|------------|
| 0 | Live run, 8 fixtures, `--site https://www.example.com/shop` | 8 of 8 processed after one metadata fix; the duplicate-title guard rejected one image on the first pass; `check_report.py` printed `ok` for all 8; watermark small, readable, bottom-right | manual |
| 1 | Single image, no domain | pass | `integration/test_single_image.py` |
| 2 | With domain | pass | `integration/test_watermark_flow.py` |
| 3 | Busy corner / all corners face or text | pass | `test_watermark_flow.py`, `unit/test_corners.py` |
| 4 | Batch, collision, bad file | pass | `integration/test_batch.py` |
| 5 | Config precedence | pass | `integration/test_config_flow.py` |
| 6 | Unsupported format | pass | `test_batch.py`, `unit/test_inputs.py` |
| 7 | Output folder is, or contains, an input's folder | pass (refused, nothing written) | `integration/test_output_safety.py` |
| 8 | Rotated photo | pass | `test_single_image.py`, `unit/test_writer.py` |
| 9 | Transparent PNG with watermark | pass | `test_watermark_flow.py`, `unit/test_watermark.py` |
| 10 | Rerun | pass | `integration/test_rerun_determinism.py` |
| 11 | Duplicate alt text | pass | `test_batch.py` |

Semantic review (human): the reviewer tally for SC-007 is **not yet recorded**. The mechanical checks
(forbidden and unshown terms) pass on the live run, but only a human can judge "accurate and natural".
Record the tally in `tests/semantic/README.md`.

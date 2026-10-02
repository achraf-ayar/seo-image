# Implementation Plan: SEO Image Skill

**Branch**: `001-seo-image-skill` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-seo-image-skill/spec.md`

## Summary

A Claude Code skill (`/seo-image`) split into two halves with a hard boundary. The **agent** looks at
each image with its own vision and writes an analysis and metadata draft as JSON. A **deterministic
Python helper** (`inspect` and `apply` subcommands) resolves inputs, measures corner busyness,
validates and normalises the metadata, resolves filename collisions, applies the watermark, saves new
files to a separate output folder, and writes the JSON and Markdown report. The agent never edits
files itself; the helper never judges image content.

## Technical Context

**Language/Version**: Python 3.12 (3.10+ supported)

**Primary Dependencies**: Pillow (image I/O, drawing). Standard library for everything else (argparse, json, glob, pathlib).

**Storage**: Files only: input images, optional `seo-image.config.json`, output folder, `report.json`.

**Testing**: pytest (dev dependency `jsonschema` validates reports against the contracts). Unit tests per deterministic rule; integration tests on generated synthetic images; semantic checks against reviewed fixtures.

**Target Platform**: Linux/macOS/Windows wherever the agent runs Python.

**Project Type**: Agent skill with a bundled CLI helper (single project).

**Performance Goals**: Helper handles a 50-image batch of ordinary web photos in under 1 minute excluding agent analysis time.

**Constraints**: Originals never modified (byte-identical). Files are copied byte for byte only when nothing must change; otherwise re-encoded upright, GPS removed, ICC kept. Reruns replace same-named outputs. No network access. No site-specific literals.

**Scale/Scope**: Tens to low hundreds of images per run; formats JPEG, PNG, WebP.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | How the plan satisfies it |
|-----------|--------|---------------------------|
| I. Generic and Reusable | PASS | No domain, brand or category literals; the domain comes only from `--site` or config. Tests use neutral synthetic images. |
| II. Visual Evidence First | PASS | The skill instructions forbid invented facts; `apply` rejects metadata that violates format rules; a reviewed-fixture check covers semantics. |
| III. Originals Are Immutable | PASS | Output folder is separate; `apply` refuses an output folder that is an input's folder or contains one; files are opened read-only; collisions inside a batch never overwrite; a rerun replaces only outputs. |
| IV. Deterministic Code for Deterministic Work | PASS | Helper owns I/O, naming, watermarking and validation. Agent vision owns analysis. The boundary is the JSON handoff. |
| V. Simplicity Over Extensibility | PASS | One package, two subcommands, one watermark style, no plugins. |
| VI. Tested Rules and Reviewed Semantics | PASS | Each rule maps to a test (see quickstart). Semantic fixtures are reviewed by a human. |

Post-design re-check: PASS. No complexity violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-seo-image-skill/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md
│   ├── analysis-input.schema.json
│   ├── report.schema.json
│   └── config.schema.json
└── tasks.md             # created later by /speckit-tasks
```

### Source Code (repository root)

```text
.claude/skills/seo-image/
├── SKILL.md                  # agent instructions: look, write analysis JSON, run helper, relay report
└── scripts/
    └── seo_image/
        ├── __main__.py       # entry: python -m seo_image
        ├── cli.py            # argument parsing, orchestration of inspect/apply
        ├── config.py         # load config, merge with flags (flags win)
        ├── domain.py         # normalise and validate domain
        ├── inputs.py         # expand globs, detect format, read dimensions, skip unsupported
        ├── rules.py          # validate filename, alt, title, description, tags
        ├── naming.py         # slug building, length limits, collision resolution
        ├── corners.py        # corner busyness measurement and position choice
        ├── watermark.py      # draw semi-transparent text with adaptive contrast
        ├── writer.py         # save outputs, byte-copy when no watermark
        └── report.py         # build JSON report and Markdown summary

tests/
├── unit/                     # one file per module above
├── integration/              # end-to-end on synthetic images
└── semantic/
    ├── fixtures/             # reviewed images + expected characteristics
    └── README.md             # how reviewers confirm fixtures
```

**Structure Decision**: One self-contained skill directory, so the skill can be copied to any project. Tests live at the repository root and import the helper from the skill path. Analysis and metadata JSON is the only coupling between agent judgment and deterministic code.

## Complexity Tracking

No constitution violations; nothing to justify.

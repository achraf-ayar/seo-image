# CLI Contract

User-facing command (handled by the agent): `/seo-image <image(s)|glob> [--site <domain>] [--context "<topic>"] [--out <dir>]`

Helper commands (invoked by the agent; run from the project root):

## `python -m seo_image inspect <paths...> [--site D] [--out DIR] [--config FILE]`
- Resolves globs, config, and domain; checks the output location.
- stdout: JSON `{ "settings": Settings, "images": [InspectedImage] }`.
- Exit 0 on success (per-image problems appear as statuses); exit 2 on a fatal input error (invalid domain, unsafe output folder, no inputs matched).

## `python -m seo_image apply <analysis.json> [--site D] [--out DIR] [--config FILE]`
- Reads the analysis, a JSON list (or an object `{"images": [...]}` holding that list), validates metadata, resolves names, writes outputs, writes `<out>/report.json`.
- stdout: Markdown summary table of the report.
- Exit 0 even when some images failed (they appear in the report); exit 2 on fatal errors.
- Never writes outside the output folder; never modifies inputs. Replaces same-named outputs from an earlier run.
- `corners` in the analysis is required only when a domain is supplied.

`--config FILE` points to a config file other than `./seo-image.config.json`. Flags `--site`, `--out` override the config file; `--context` is read by the agent only.

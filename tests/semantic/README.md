# Semantic review

Deterministic rules are tested automatically. Whether generated metadata is **faithful** to the
image cannot be, so it is checked against reviewed fixtures.

## Fixtures

`fixtures/<name>.png` is a neutral, generated illustration (`make_fixtures.py`) with no real
brand or identifiable person. `fixtures/<name>.json` records what a reviewer has confirmed:

- `reviewed`: what the image actually shows.
- `must_mention`: groups of words; at least one word from each group should appear.
- `must_not_mention`: details the image does not show (for example a material or a time of day).
- `forbidden_terms`: names, brands, locations and identity or sensitive-characteristic words that
  must never appear. The person fixture forbids names, roles, gender, age and ethnicity words.
- `context` (context fixtures only): `{"text": "<the --context value to pass>", "supported": true|false, "terms": [...]}`. For an unsupported context, none of `terms` may appear in the output.

Changing a fixture's expectations needs a second reviewer.

### About the forbidden lists

`forbidden_terms` and `must_not_mention` deliberately include real brand, product and place names.
They are **test data**: canaries that reveal a fabricated fact when a model invents a plausible
brand or location for an image that shows none. They are read only by `check_report.py`. The skill
itself contains no brand, site or place names, and `tests/unit/test_no_hardcoded_sites.py` fails if
anything in the skill folder references this folder or its lists (Constitution I).

## Procedure

1. Run `/seo-image tests/semantic/fixtures/*.png` (for the two `*-context-*` fixtures pass the `text` from their json as `--context`).
2. `python tests/semantic/check_report.py seo-images/report.json` flags forbidden terms, details
   not shown, and missing terms. Any fabricated brand, place, model, material, price, name, event
   or identity is a failure (SC-003).
3. For each result, the reviewer judges the alt text and description as **accurate and natural**
   (not keyword-stuffed) and records the verdict below.
4. Pass the tally to the checker:
   `python tests/semantic/check_report.py seo-images/report.json --tally <accurate> <total>`.
   SC-007 needs at least 90%.

## Reviewer tally (SC-007)

| Date | Reviewer | Results reviewed | Accurate and natural | Percentage | Meets 90%? |
|------|----------|------------------|----------------------|------------|------------|
|      |          |                  |                      |            |            |

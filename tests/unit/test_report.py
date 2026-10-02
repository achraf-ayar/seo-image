import json
import os

import jsonschema

from seo_image.models import Result
from seo_image.report import build_report, to_markdown, write_report

SCHEMA = json.load(open(os.path.join(os.path.dirname(__file__), "..", "..", "specs",
                                     "001-seo-image-skill", "contracts", "report.schema.json")))


def ok(**kw):
    base = dict(original_filename="a.jpg", new_filename="red-mug.jpg", alt="Red mug", title="Mug",
                description="A red mug.", tags=["mug", "red", "cup"], domain="example.com",
                watermark_status="applied", watermark_position="bottom-right", width=10, height=8)
    base.update(kw)
    return Result(**base)


def test_markdown_has_header_one_row_per_result_and_a_summary():
    md = to_markdown([ok(), ok(original_filename="b.jpg", new_filename="blue-mug.jpg")]).splitlines()
    assert md[0].startswith("| Original | New file | Status |")
    assert md[1].count("---") == 10
    assert len([l for l in md if l.startswith("| a.jpg") or l.startswith("| b.jpg")]) == 2
    assert md[-1] == "2 of 2 images processed."


def test_markdown_escapes_pipes_and_newlines_and_marks_empty_cells():
    md = to_markdown([ok(alt="Red | blue mug\nline two", tags=None, domain=None, watermark_position=None)])
    row = md.splitlines()[2]
    assert "Red \\| blue mug line two" in row and "\n" not in row
    assert row.count(" | -") >= 3  # empty cells show a dash
    assert "mug, red, cup" not in row


def test_markdown_shows_status_and_watermark_reasons():
    failed = Result(original_filename="bad.jpg", status="failed", reason="file is corrupt")
    skipped = ok(watermark_status="skipped", watermark_reason="every corner holds a face or text",
                 watermark_position=None)
    md = to_markdown([failed, skipped])
    assert "failed: file is corrupt" in md
    assert "skipped (every corner holds a face or text)" in md
    assert md.splitlines()[-1] == "1 of 2 images processed."


def test_report_json_validates_and_keeps_required_nulls(tmp_path):
    results = [ok(), Result(original_filename="bad.jpg", status="failed", reason="x"),
               ok(watermark_status="none", domain=None, watermark_position=None)]
    path = write_report(results, tmp_path)
    data = json.load(open(path))
    jsonschema.validate(data, SCHEMA)
    assert data == build_report(results)
    failed = data["results"][1]
    assert failed["new_filename"] is None and failed["domain"] is None and failed["watermark_position"] is None
    assert failed["reason"] == "x"


def test_write_report_is_atomic_and_replaces_an_older_report(tmp_path):
    (tmp_path / "report.json").write_text("stale")
    write_report([ok()], tmp_path)
    assert sorted(os.listdir(tmp_path)) == ["report.json"]
    assert json.load(open(tmp_path / "report.json"))["results"][0]["original_filename"] == "a.jpg"


def test_unicode_is_kept_in_json(tmp_path):
    path = write_report([ok(alt="Café crème")], tmp_path)
    assert "Café crème" in open(path, encoding="utf-8").read()

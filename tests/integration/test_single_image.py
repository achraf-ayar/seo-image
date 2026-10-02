import json
import os

import jsonschema
from PIL import Image

import helpers

SCHEMA = os.path.join(os.path.dirname(__file__), "..", "..", "specs", "001-seo-image-skill",
                      "contracts", "report.schema.json")


def validate_report(path):
    jsonschema.validate(json.load(open(path)), json.load(open(SCHEMA)))
    return json.load(open(path))["results"]


def test_inspect_then_apply_single_image(tmp_path, run_cli, write_analysis):
    src = helpers.make_image(tmp_path / "IMG_0001.jpg", size=(640, 480))
    before = helpers.sha(src)

    code, out, _ = run_cli("inspect", src)
    assert code == 0
    data = json.loads(out)
    assert data["images"][0]["width"] == 640 and data["settings"]["domain"] is None

    analysis = write_analysis([helpers.analysis_entry(src, corners=False)])
    code, out, _ = run_cli("apply", analysis)
    assert code == 0 and "red-ceramic-mug" in out

    results = validate_report(tmp_path / "seo-images" / "report.json")
    r = results[0]
    assert r["status"] == "ok" and r["watermark_status"] == "none" and r["domain"] is None
    assert r["watermark_position"] is None
    new = tmp_path / "seo-images" / r["new_filename"]
    with Image.open(new) as im, Image.open(src) as orig:
        assert im.size == orig.size == (r["width"], r["height"])
        assert im.size[0] / im.size[1] == 640 / 480
    assert helpers.sha(src) == before
    for key in ("alt", "title", "description", "tags", "original_filename"):
        assert r[key]


def test_rotated_photo_flow(tmp_path, run_cli, write_analysis):
    src = helpers.make_rotated_gps_jpeg(tmp_path / "r.jpg", stored=(300, 200), orientation=6)
    code, out, _ = run_cli("inspect", src)
    assert json.loads(out)["images"][0]["width"] == 200
    code, _, _ = run_cli("apply", write_analysis([helpers.analysis_entry(src, corners=False)]))
    r = validate_report(tmp_path / "seo-images" / "report.json")[0]
    assert (r["width"], r["height"]) == (200, 300)
    with Image.open(tmp_path / "seo-images" / r["new_filename"]) as im:
        assert im.size == (200, 300)
        assert not im.getexif().get_ifd(0x8825)


def test_rejected_metadata_is_reported_not_written(tmp_path, run_cli, write_analysis):
    src = helpers.make_image(tmp_path / "a.jpg")
    entry = helpers.analysis_entry(src, corners=False, alt="Image of a mug")
    code, _, _ = run_cli("apply", write_analysis([entry]))
    assert code == 0
    r = validate_report(tmp_path / "seo-images" / "report.json")[0]
    assert r["status"] == "failed" and "must not start" in r["reason"]
    assert [p for p in os.listdir(tmp_path / "seo-images") if p != "report.json"] == []

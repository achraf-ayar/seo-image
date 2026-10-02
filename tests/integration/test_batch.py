import json
import os

import jsonschema

from PIL import Image

import helpers


ANALYSIS_SCHEMA = json.load(open(os.path.join(os.path.dirname(__file__), "..", "..", "specs",
                                              "001-seo-image-skill", "contracts",
                                              "analysis-input.schema.json")))


def results(tmp_path):
    return json.load(open(tmp_path / "seo-images" / "report.json"))["results"]


def test_inspect_expands_glob_and_reports_every_file(tmp_path, run_cli):
    d = tmp_path / "images"
    d.mkdir()
    helpers.make_image(d / "a.jpg")
    helpers.make_corrupt(d / "bad.jpg")
    helpers.make_animated_gif(d / "anim.gif")
    code, out, _ = run_cli("inspect", "images/*")
    assert code == 0
    imgs = {i["original_filename"]: i for i in json.loads(out)["images"]}
    assert imgs["a.jpg"]["status"] == "ok"
    assert imgs["bad.jpg"]["status"] == "unreadable"
    assert imgs["anim.gif"]["status"] == "unsupported" and imgs["anim.gif"]["reason"]


def test_batch_with_collisions_failures_and_skips(tmp_path, run_cli, write_analysis):
    d = tmp_path / "images"
    d.mkdir()
    a1 = helpers.make_image(d / "a1.jpg", kind="gradient")
    a2 = helpers.make_image(d / "a2.jpg", kind="noise")
    bad = helpers.make_corrupt(d / "bad.jpg")
    gif = helpers.make_animated_gif(d / "anim.gif")
    still = d / "still.gif"
    Image.new("RGB", (40, 40)).save(still)
    hashes = {p: helpers.sha(p) for p in (a1, a2, bad, gif, still)}

    entries = [
        helpers.analysis_entry(a1, corners=False, alt="Red mug on shelf one", title="Mug one",
                               distinguisher="front"),
        helpers.analysis_entry(a2, corners=False, alt="Red mug on shelf two", title="Mug two"),
        {"path": str(bad)}, {"path": str(gif)}, {"path": str(still)},
    ]
    jsonschema.validate(entries, ANALYSIS_SCHEMA)  # minimal entries for skipped files are valid
    code, out, _ = run_cli("apply", write_analysis(entries))
    assert code == 0
    rs = results(tmp_path)
    assert len(rs) == 5
    ok = [r for r in rs if r["status"] == "ok"]
    assert len(ok) == 2
    names = [r["new_filename"] for r in ok]
    assert len(set(n.lower() for n in names)) == 2
    assert names[0] == "red-ceramic-mug-on-wooden.jpg"
    assert names[1] == "red-ceramic-mug-on-wooden-2.jpg"
    for n in names:
        assert (tmp_path / "seo-images" / n).exists()
    by = {r["original_filename"]: r for r in rs}
    assert by["bad.jpg"]["status"] == "failed" and by["bad.jpg"]["reason"]
    assert by["anim.gif"]["status"] == "skipped" and "animated" in by["anim.gif"]["reason"]
    assert by["still.gif"]["status"] == "skipped" and "unsupported" in by["still.gif"]["reason"]
    assert {p: helpers.sha(p) for p in hashes} == hashes
    assert "5" in out.splitlines()[-1] or "2 of 5" in out


def test_distinguisher_used_when_it_fits(tmp_path, run_cli, write_analysis):
    d = tmp_path / "images"
    d.mkdir()
    a1 = helpers.make_image(d / "a1.png")
    a2 = helpers.make_image(d / "a2.png")
    e1 = helpers.analysis_entry(a1, corners=False, filename_stem="red mug", alt="Red mug one", title="One")
    e2 = helpers.analysis_entry(a2, corners=False, filename_stem="red mug", alt="Red mug two", title="Two",
                                distinguisher="handle")
    run_cli("apply", write_analysis([e1, e2]))
    assert [r["new_filename"] for r in results(tmp_path)] == ["red-mug.png", "red-mug-handle.png"]


def test_identical_alt_or_title_rejects_the_later_image(tmp_path, run_cli, write_analysis):
    d = tmp_path / "images"
    d.mkdir()
    a, b, c = (helpers.make_image(d / f"{n}.png") for n in "abc")
    e1 = helpers.analysis_entry(a, corners=False, filename_stem="mug one", alt="Red mug", title="Mug A")
    e2 = helpers.analysis_entry(b, corners=False, filename_stem="mug two", alt="red MUG", title="Mug B")
    e3 = helpers.analysis_entry(c, corners=False, filename_stem="mug three", alt="Blue mug", title="mug a")
    run_cli("apply", write_analysis([e1, e2, e3]))
    rs = results(tmp_path)
    assert [r["status"] for r in rs] == ["ok", "failed", "failed"]
    assert "alt text" in rs[1]["reason"] and "title" in rs[2]["reason"]
    assert sorted(os.listdir(tmp_path / "seo-images")) == ["mug-one.png", "report.json"]


def test_one_failure_never_stops_the_batch(tmp_path, run_cli, write_analysis):
    d = tmp_path / "images"
    d.mkdir()
    good = helpers.make_image(d / "g.png")
    entries = [{"path": str(d / "missing.png")}, {"no": "path"},
               helpers.analysis_entry(d / "missing2.png", corners=False),
               helpers.analysis_entry(good, corners=False, filename_stem="IMG_0001")]
    run_cli("apply", write_analysis(entries))
    rs = results(tmp_path)
    assert [r["status"] for r in rs] == ["failed", "failed", "failed", "failed"]
    entries[-1] = helpers.analysis_entry(good, corners=False)
    run_cli("apply", write_analysis(entries))
    assert [r["status"] for r in results(tmp_path)] == ["failed", "failed", "failed", "ok"]


def test_analysis_schema_rejects_incomplete_ok_entries(tmp_path):
    import pytest
    good = helpers.analysis_entry(tmp_path / "a.png", corners=False)
    jsonschema.validate([good], ANALYSIS_SCHEMA)
    for broken in ({"path": "a.png", "metadata": good["metadata"]},       # no image_type or primary_subject
                   {"path": "a.png", "image_type": "x", "primary_subject": "y"},  # no metadata
                   {"path": "a.png", "extra": 1}):                         # not a valid minimal entry
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate([broken], ANALYSIS_SCHEMA)

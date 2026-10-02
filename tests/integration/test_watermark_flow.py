import json

from PIL import Image, ImageChops

import helpers

FREE = {c: "free" for c in ("top-left", "top-right", "bottom-left", "bottom-right")}


def report(tmp_path):
    return json.load(open(tmp_path / "seo-images" / "report.json"))["results"]


def diff_bbox(a, b):
    return ImageChops.difference(Image.open(a).convert("RGB"), Image.open(b).convert("RGB")).getbbox()


def test_domain_applies_bottom_right_watermark(tmp_path, run_cli, write_analysis):
    src = helpers.make_image(tmp_path / "a.png", size=(600, 400), kind="flat")
    code, out, _ = run_cli("apply", write_analysis([helpers.analysis_entry(src, corners=FREE)]), "--site", "https://www.Example.com/shop")
    assert code == 0
    r = report(tmp_path)[0]
    assert (r["watermark_status"], r["watermark_position"], r["domain"]) == ("applied", "bottom-right", "example.com")
    bbox = diff_bbox(src, tmp_path / "seo-images" / r["new_filename"])
    assert bbox and bbox[0] > 300 and bbox[1] > 300  # lower-right quadrant only
    assert "example" not in r["new_filename"]
    assert Image.open(tmp_path / "seo-images" / r["new_filename"]).size == (600, 400)


def test_no_domain_means_no_watermark(tmp_path, run_cli, write_analysis):
    src = helpers.make_image(tmp_path / "a.png")
    run_cli("apply", write_analysis([helpers.analysis_entry(src, corners=False)]))
    r = report(tmp_path)[0]
    assert (r["watermark_status"], r["domain"], r["watermark_position"]) == ("none", None, None)
    assert helpers.sha(src) == helpers.sha(tmp_path / "seo-images" / r["new_filename"])


def test_busy_default_corner_moves_watermark(tmp_path, run_cli, write_analysis):
    img = helpers.noisy_corner(helpers.pattern_image((600, 400), "flat"), "top-right")
    src = tmp_path / "a.png"
    img.save(src)
    corners = dict(FREE, **{"bottom-right": "face_or_text"})
    run_cli("apply", write_analysis([helpers.analysis_entry(src, corners=corners)]), "--site", "example.com")
    r = report(tmp_path)[0]
    assert r["watermark_status"] == "applied"
    assert r["watermark_position"] in ("top-left", "bottom-left")  # least busy free corners


def test_all_corners_face_or_text_skips_with_reason(tmp_path, run_cli, write_analysis):
    src = helpers.make_image(tmp_path / "a.jpg", size=(600, 400))
    corners = {c: "face_or_text" for c in FREE}
    run_cli("apply", write_analysis([helpers.analysis_entry(src, corners=corners)]), "--site", "example.com")
    r = report(tmp_path)[0]
    assert r["status"] == "ok" and r["watermark_status"] == "skipped" and r["watermark_reason"]
    assert r["watermark_position"] is None
    assert helpers.sha(src) == helpers.sha(tmp_path / "seo-images" / r["new_filename"])


def test_small_image_watermark_skipped(tmp_path, run_cli, write_analysis):
    src = helpers.make_image(tmp_path / "a.png", size=(150, 120))
    run_cli("apply", write_analysis([helpers.analysis_entry(src, corners=FREE)]), "--site", "example.com")
    r = report(tmp_path)[0]
    assert r["watermark_status"] == "skipped" and "200" in r["watermark_reason"]


def test_missing_corners_with_domain_fails_that_image(tmp_path, run_cli, write_analysis):
    src = helpers.make_image(tmp_path / "a.png")
    run_cli("apply", write_analysis([helpers.analysis_entry(src, corners=False)]), "--site", "example.com")
    r = report(tmp_path)[0]
    assert r["status"] == "failed" and "corner" in r["reason"]


def test_alt_with_domain_not_visible_is_rejected_but_visible_is_accepted(tmp_path, run_cli, write_analysis):
    src = helpers.make_image(tmp_path / "a.png")
    bad = helpers.analysis_entry(src, corners=FREE, alt="Mug on a shelf from example.com")
    run_cli("apply", write_analysis([bad]), "--site", "example.com")
    assert report(tmp_path)[0]["status"] == "failed"
    good = helpers.analysis_entry(src, corners=FREE, alt="Mug on a shelf from example.com")
    good["visible_text"] = ["example.com"]
    run_cli("apply", write_analysis([good]), "--site", "example.com")
    assert report(tmp_path)[0]["status"] == "ok"


def test_watermarked_output_has_no_gps_and_keeps_icc(tmp_path, run_cli, write_analysis):
    src = helpers.make_rotated_gps_jpeg(tmp_path / "r.jpg", stored=(600, 400), orientation=6)
    run_cli("apply", write_analysis([helpers.analysis_entry(src, corners=FREE)]), "--site", "example.com")
    r = report(tmp_path)[0]
    assert r["watermark_status"] == "applied" and (r["width"], r["height"]) == (400, 600)
    with Image.open(tmp_path / "seo-images" / r["new_filename"]) as im:
        assert not im.getexif().get_ifd(0x8825)
        assert im.info.get("icc_profile") == helpers.ICC


def test_transparent_png_stays_transparent_after_watermark(tmp_path, run_cli, write_analysis):
    src = helpers.make_rgba(tmp_path / "t.png", size=(500, 400))
    run_cli("apply", write_analysis([helpers.analysis_entry(src, corners=FREE)]), "--site", "example.com")
    r = report(tmp_path)[0]
    with Image.open(tmp_path / "seo-images" / r["new_filename"]) as im:
        im = im.convert("RGBA")
        assert im.getpixel((2, 2))[3] == 0 and im.getpixel((250, 200))[3] == 255


def test_invalid_domain_is_fatal(tmp_path, run_cli, write_analysis):
    src = helpers.make_image(tmp_path / "a.png")
    code, _, err = run_cli("apply", write_analysis([helpers.analysis_entry(src)]), "--site", "not a domain")
    assert code == 2 and "invalid domain" in err
    assert not (tmp_path / "seo-images").exists()

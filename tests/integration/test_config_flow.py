import json

from PIL import Image, ImageChops

import helpers

FREE = {c: "free" for c in ("top-left", "top-right", "bottom-left", "bottom-right")}


def write_config(tmp_path, **cfg):
    (tmp_path / "seo-image.config.json").write_text(json.dumps(cfg))


def report(tmp_path, folder="seo-images"):
    return json.load(open(tmp_path / folder / "report.json"))["results"]


def entry(tmp_path):
    return helpers.analysis_entry(helpers.make_image(tmp_path / "a.png", size=(600, 400), kind="flat"), corners=FREE)


def test_config_domain_used_with_no_flags(tmp_path, run_cli, write_analysis):
    write_config(tmp_path, domain="config.example")
    run_cli("apply", write_analysis([entry(tmp_path)]))
    r = report(tmp_path)[0]
    assert r["domain"] == "config.example" and r["watermark_status"] == "applied"


def test_site_flag_overrides_config(tmp_path, run_cli, write_analysis):
    write_config(tmp_path, domain="config.example")
    run_cli("apply", write_analysis([entry(tmp_path)]), "--site", "other.example")
    assert report(tmp_path)[0]["domain"] == "other.example"
    code, out, _ = run_cli("inspect", tmp_path / "a.png", "--site", "other.example")
    assert json.loads(out)["settings"]["domain"] == "other.example"


def test_disabled_watermark(tmp_path, run_cli, write_analysis):
    write_config(tmp_path, domain="config.example", watermark={"enabled": False})
    src = tmp_path / "a.png"
    run_cli("apply", write_analysis([entry(tmp_path)]))
    r = report(tmp_path)[0]
    assert r["watermark_status"] == "disabled" and r["watermark_position"] is None
    assert helpers.sha(src) == helpers.sha(tmp_path / "seo-images" / r["new_filename"])


def test_output_dir_from_config_and_out_flag(tmp_path, run_cli, write_analysis):
    write_config(tmp_path, output_dir="from-config")
    a = write_analysis([entry(tmp_path)])
    run_cli("apply", a)
    assert (tmp_path / "from-config" / "report.json").exists()
    run_cli("apply", a, "--out", "from-flag")
    assert (tmp_path / "from-flag" / "report.json").exists()


def test_configured_position_and_explicit_config_path(tmp_path, run_cli, write_analysis):
    write_config(tmp_path, domain="config.example", watermark={"position": "top-left"})
    run_cli("apply", write_analysis([entry(tmp_path)]))
    assert report(tmp_path)[0]["watermark_position"] == "top-left"
    other = tmp_path / "other.json"
    other.write_text(json.dumps({"domain": "elsewhere.example"}))
    run_cli("apply", write_analysis([entry(tmp_path)]), "--config", other)
    assert report(tmp_path)[0]["domain"] == "elsewhere.example"


def test_opacity_and_size_from_config_change_the_watermark(tmp_path, run_cli, write_analysis):
    src = tmp_path / "a.png"
    helpers.make_image(src, size=(800, 600), kind="light")
    a = write_analysis([helpers.analysis_entry(src, corners=FREE)])
    write_config(tmp_path, domain="x.example", watermark={"opacity": 1.0, "size": 5})
    run_cli("apply", a, "--out", "strong")
    write_config(tmp_path, domain="x.example", watermark={"opacity": 0.2, "size": 2})
    run_cli("apply", a, "--out", "faint")
    s = tmp_path / "strong" / report(tmp_path, "strong")[0]["new_filename"]
    f = tmp_path / "faint" / report(tmp_path, "faint")[0]["new_filename"]
    bs = ImageChops.difference(Image.open(s).convert("RGB"), Image.open(src).convert("RGB")).getbbox()
    bf = ImageChops.difference(Image.open(f).convert("RGB"), Image.open(src).convert("RGB")).getbbox()
    assert (bs[2] - bs[0]) > (bf[2] - bf[0])  # larger size draws a wider watermark


def test_invalid_config_is_fatal(tmp_path, run_cli, write_analysis):
    write_config(tmp_path, watermark={"opacity": 9})
    code, _, err = run_cli("apply", write_analysis([entry(tmp_path)]))
    assert code == 2 and "opacity" in err
    assert not (tmp_path / "seo-images").exists()

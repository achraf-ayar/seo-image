import json
import os

from PIL import Image

import helpers

FREE = {c: "free" for c in ("top-left", "top-right", "bottom-left", "bottom-right")}


def snapshot(folder):
    out = {}
    for name in sorted(os.listdir(folder)):
        if name == "report.json":
            continue
        out[name] = (helpers.sha(folder / name), Image.open(folder / name).convert("RGBA").tobytes())
    return out


def test_same_input_and_settings_give_identical_output(tmp_path, run_cli, write_analysis):
    files = [helpers.make_image(tmp_path / "a.jpg", size=(500, 400)),
             helpers.make_rotated_gps_jpeg(tmp_path / "b.jpg", stored=(500, 400)),
             helpers.make_rgba(tmp_path / "c.png", size=(500, 400))]
    entries = [helpers.analysis_entry(p, corners=FREE, filename_stem=f"thing {n}", alt=f"Thing {n}", title=f"Title {n}")
               for n, p in zip("abc", files)]
    a = write_analysis(entries)
    run_cli("apply", a, "--site", "example.com", "--out", "run1")
    run_cli("apply", a, "--site", "example.com", "--out", "run2")
    assert snapshot(tmp_path / "run1") == snapshot(tmp_path / "run2")
    assert json.load(open(tmp_path / "run1" / "report.json")) == json.load(open(tmp_path / "run2" / "report.json"))


def test_rerun_replaces_outputs_without_suffixes(tmp_path, run_cli, write_analysis):
    src = helpers.make_image(tmp_path / "a.jpg", size=(500, 400))
    a = write_analysis([helpers.analysis_entry(src, corners=FREE)])
    before = helpers.sha(src)
    run_cli("apply", a, "--site", "example.com")
    first = snapshot(tmp_path / "seo-images")
    stale = tmp_path / "seo-images" / list(first)[0]
    stale.write_bytes(b"stale content")
    run_cli("apply", a, "--site", "example.com")
    second = snapshot(tmp_path / "seo-images")
    assert first == second and len(second) == 1
    assert helpers.sha(src) == before
    assert sorted(os.listdir(tmp_path / "seo-images")) == sorted([*first, "report.json"])

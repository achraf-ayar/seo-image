import time

import helpers

FREE = {c: "free" for c in ("top-left", "top-right", "bottom-left", "bottom-right")}


def test_fifty_web_size_photos_in_under_a_minute(tmp_path, run_cli, write_analysis):
    d = tmp_path / "images"
    d.mkdir()
    entries = []
    for i in range(50):
        p = helpers.make_image(d / f"p{i:02d}.jpg", size=(1600, 1067), kind="gradient", quality=88)
        entries.append(helpers.analysis_entry(p, corners=FREE, filename_stem=f"photo scene {i}x",
                                              alt=f"Scene number {i}", title=f"Scene {i}"))
    a = write_analysis(entries)
    start = time.perf_counter()
    code, _, _ = run_cli("apply", a, "--site", "example.com")
    elapsed = time.perf_counter() - start
    assert code == 0
    assert elapsed < 60, f"50-image batch took {elapsed:.1f}s"
    import json
    results = json.load(open(tmp_path / "seo-images" / "report.json"))["results"]
    assert len(results) == 50 and all(r["status"] == "ok" for r in results)

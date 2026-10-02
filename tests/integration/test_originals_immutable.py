import helpers

FREE = {c: "free" for c in ("top-left", "top-right", "bottom-left", "bottom-right")}


def test_no_original_changes_in_a_mixed_run(tmp_path, run_cli, write_analysis):
    d = tmp_path / "images"
    d.mkdir()
    files = [
        helpers.make_image(d / "plain.jpg", size=(500, 400)),
        helpers.make_rotated_gps_jpeg(d / "rot.jpg", stored=(500, 400), orientation=6),
        helpers.make_gps_jpeg(d / "gps.jpg", size=(500, 400)),
        helpers.make_rgba(d / "alpha.png", size=(500, 400)),
        helpers.make_rgba(d / "alpha.webp", size=(500, 400)),
        helpers.make_image(d / "tiny.png", size=(100, 80)),
        helpers.make_xmp_jpeg(d / "xmp.jpg", size=(500, 400)),
        helpers.make_xmp_png(d / "xmp.png", size=(500, 400)),
        helpers.make_xmp_webp(d / "xmp.webp", size=(500, 400)),
        helpers.make_corrupt(d / "bad.jpg"),
        helpers.make_animated_gif(d / "anim.gif"),
    ]
    before = {p: helpers.sha(p) for p in files}
    listing = sorted(p.name for p in d.iterdir())
    entries = []
    for i, p in enumerate(files):
        if p.suffix in (".gif",) or p.name == "bad.jpg":
            entries.append({"path": str(p)})
        else:
            entries.append(helpers.analysis_entry(p, corners=FREE, filename_stem=f"item {i} photo",
                                                  alt=f"Item number {i} photo", title=f"Item {i}"))
    for extra in ([], ["--site", "example.com"]):
        code, _, _ = run_cli("apply", write_analysis(entries), *extra)
        assert code == 0
        assert {p: helpers.sha(p) for p in files} == before
        assert sorted(p.name for p in d.iterdir()) == listing  # nothing added next to the originals


def test_no_output_keeps_location_data_with_or_without_watermark(tmp_path, run_cli, write_analysis):
    import json
    d = tmp_path / "images"
    d.mkdir()
    files = [helpers.make_xmp_jpeg(d / "a.jpg", size=(500, 400)),
             helpers.make_xmp_png(d / "b.png", size=(500, 400)),
             helpers.make_xmp_webp(d / "c.webp", size=(500, 400)),
             helpers.make_gps_jpeg(d / "e.jpg", size=(500, 400))]
    entries = [helpers.analysis_entry(p, corners=FREE, filename_stem=f"thing {i}", alt=f"Thing {i}", title=f"Title {i}")
               for i, p in enumerate(files)]
    for extra in ([], ["--site", "example.com"]):
        run_cli("apply", write_analysis(entries), *extra, "--out", "out" + str(len(extra)))
        folder = tmp_path / ("out" + str(len(extra)))
        for r in json.load(open(folder / "report.json"))["results"]:
            assert r["status"] == "ok"
            assert not helpers.has_location_text(folder / r["new_filename"])

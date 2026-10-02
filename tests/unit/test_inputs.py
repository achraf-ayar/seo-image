from seo_image.inputs import expand_inputs, inspect_image
import helpers


def test_format_by_content_not_extension(tmp_path):
    p = tmp_path / "x.png"
    helpers.make_image(tmp_path / "real.jpg")
    (tmp_path / "real.jpg").rename(p)
    info = inspect_image(p)
    assert info.status == "ok" and info.format == "jpeg"


def test_formats_and_dimensions(tmp_path):
    for name, fmt in (("a.jpg", "jpeg"), ("a.png", "png"), ("a.webp", "webp")):
        helpers.make_image(tmp_path / name, size=(320, 240))
        info = inspect_image(tmp_path / name)
        assert (info.format, info.width, info.height) == (fmt, 320, 240)


def test_rotated_photo_reports_displayed_size(tmp_path):
    p = helpers.make_rotated_gps_jpeg(tmp_path / "r.jpg", stored=(300, 200), orientation=6)
    info = inspect_image(p)
    assert (info.width, info.height) == (200, 300)
    assert info.has_gps and not info.upright


def test_gps_flag_false_without_gps(tmp_path):
    p = helpers.make_rotated_gps_jpeg(tmp_path / "n.jpg", orientation=1, with_gps=False)
    info = inspect_image(p)
    assert not info.has_gps and info.upright


def test_animated_images_unsupported(tmp_path):
    for p in (helpers.make_animated_gif(tmp_path / "a.gif"), helpers.make_animated_webp(tmp_path / "a.webp")):
        info = inspect_image(p)
        assert info.status == "unsupported" and info.reason


def test_static_gif_unsupported(tmp_path):
    from PIL import Image
    Image.new("RGB", (50, 50)).save(tmp_path / "s.gif")
    assert inspect_image(tmp_path / "s.gif").status == "unsupported"


def test_corrupt_and_non_image(tmp_path):
    helpers.make_corrupt(tmp_path / "bad.jpg")
    info = inspect_image(tmp_path / "bad.jpg")
    assert info.status == "unreadable" and info.reason
    (tmp_path / "notes.txt").write_text("hello")
    info = inspect_image(tmp_path / "notes.txt")
    assert info.status == "unsupported" and info.reason


def test_missing_file(tmp_path):
    info = inspect_image(tmp_path / "nope.jpg")
    assert info.status == "unreadable" and "not found" in info.reason


def test_expand_inputs_globs_dedupes_and_folders(tmp_path):
    for n in ("b.jpg", "a.jpg"):
        helpers.make_image(tmp_path / n, size=(50, 50))
    found = expand_inputs([str(tmp_path / "*.jpg"), str(tmp_path / "a.jpg"), str(tmp_path)])
    assert [p.split("/")[-1] for p in found] == ["a.jpg", "b.jpg"]
    assert expand_inputs([str(tmp_path / "missing.jpg")]) == [str(tmp_path / "missing.jpg")]


def test_xmp_location_detected_in_every_format(tmp_path):
    files = [
        helpers.make_xmp_jpeg(tmp_path / "x.jpg"),
        helpers.make_xmp_png(tmp_path / "x.png"),
        helpers.make_xmp_png(tmp_path / "xz.png", compressed=True),
        helpers.make_xmp_webp(tmp_path / "x.webp"),
    ]
    for p in files:
        info = inspect_image(p)
        assert info.status == "ok" and info.has_gps, p.name


def test_no_location_flag_without_location_data(tmp_path):
    from PIL import Image, PngImagePlugin
    info = PngImagePlugin.PngInfo()
    info.add_itxt("XML:com.adobe.xmp", '<x:xmpmeta xmlns:x="adobe:ns:meta/"><dc:title>mug</dc:title></x:xmpmeta>')
    helpers.pattern_image((100, 80)).save(tmp_path / "t.png", pnginfo=info)
    assert not inspect_image(tmp_path / "t.png").has_gps
    helpers.make_image(tmp_path / "plain.webp")
    assert not inspect_image(tmp_path / "plain.webp").has_gps

import os

from PIL import Image

import helpers
from seo_image.writer import load_upright, write_output


def test_byte_copy_when_nothing_changes(tmp_path):
    src = helpers.make_image(tmp_path / "a.jpg")
    helpers.make_rotated_gps_jpeg(tmp_path / "plain.jpg", orientation=1, with_gps=False)
    for name in ("a.jpg", "plain.jpg"):
        before = helpers.sha(tmp_path / name)
        write_output(tmp_path / name, tmp_path / "out", name)
        assert helpers.sha(tmp_path / "out" / name) == before == helpers.sha(tmp_path / name)


def test_output_folder_created(tmp_path):
    helpers.make_image(tmp_path / "a.png")
    write_output(tmp_path / "a.png", tmp_path / "deep" / "out", "x.png")
    assert (tmp_path / "deep" / "out" / "x.png").exists()


def test_rotated_photo_saved_upright_without_gps_keeping_icc(tmp_path):
    src = helpers.make_rotated_gps_jpeg(tmp_path / "r.jpg", stored=(300, 200), orientation=6)
    before = helpers.sha(src)
    size = write_output(src, tmp_path / "out", "r.jpg")
    assert size == (200, 300)
    with Image.open(tmp_path / "out" / "r.jpg") as out:
        exif = out.getexif()
        assert out.size == (200, 300)
        assert exif.get(0x0112, 1) == 1
        assert not exif.get_ifd(0x8825) and 0x8825 not in exif
        assert out.info.get("icc_profile") == helpers.ICC
        assert exif.get(0x010F) == "TestMake"  # other EXIF kept
    assert helpers.sha(src) == before


def test_gps_stripped_even_when_upright(tmp_path):
    src = helpers.make_gps_jpeg(tmp_path / "g.jpg")
    write_output(src, tmp_path / "out", "g.jpg")
    with Image.open(tmp_path / "out" / "g.jpg") as out:
        assert not out.getexif().get_ifd(0x8825)
        assert out.info.get("icc_profile") == helpers.ICC


def test_png_and_webp_gps_stripped(tmp_path):
    from PIL import Image as I
    ex = I.Exif()
    ex[0x8825] = dict(helpers.GPS)
    for name, kw in (("g.png", {}), ("g.webp", {"lossless": True})):
        helpers.pattern_image((120, 90)).save(tmp_path / name, exif=ex.tobytes(), **kw)
        write_output(tmp_path / name, tmp_path / "out", name)
        with I.open(tmp_path / "out" / name) as out:
            assert not out.getexif().get_ifd(0x8825)


def test_transparency_preserved_on_reencode(tmp_path):
    for name in ("t.png", "t.webp"):
        helpers.make_rgba(tmp_path / name, size=(200, 160))
        loaded = load_upright(tmp_path / name)
        write_output(tmp_path / name, tmp_path / "out", name, loaded=loaded)
        with Image.open(tmp_path / "out" / name) as out:
            assert out.convert("RGBA").getpixel((2, 2))[3] == 0
            assert out.convert("RGBA").getpixel((100, 80))[3] == 255


def test_rerun_replaces_output_and_leaves_no_temp_files(tmp_path):
    src = helpers.make_image(tmp_path / "a.jpg")
    out = tmp_path / "out"
    write_output(src, out, "x.jpg")
    (out / "x.jpg").write_bytes(b"stale")
    write_output(src, out, "x.jpg")
    assert helpers.sha(out / "x.jpg") == helpers.sha(src)
    assert sorted(os.listdir(out)) == ["x.jpg"]


def test_original_never_modified(tmp_path):
    src = helpers.make_rotated_gps_jpeg(tmp_path / "r.jpg")
    before = helpers.sha(src)
    write_output(src, tmp_path / "out", "r.jpg", loaded=load_upright(src))
    assert helpers.sha(src) == before


def test_xmp_location_never_survives_a_copy(tmp_path):
    """FR-014: files whose only location data is XMP are re-encoded, not byte-copied."""
    for name, make in (("x.jpg", helpers.make_xmp_jpeg), ("x.png", helpers.make_xmp_png),
                       ("x.webp", helpers.make_xmp_webp)):
        src = make(tmp_path / name)
        assert helpers.has_location_text(src)
        before = helpers.sha(src)
        size = write_output(src, tmp_path / "out", name)
        out = tmp_path / "out" / name
        assert not helpers.has_location_text(out), name
        with Image.open(out) as im:
            assert im.size == size == (400, 300)
            assert im.info.get("icc_profile") == helpers.ICC
        assert helpers.sha(src) == before


def test_compressed_png_xmp_location_stripped(tmp_path):
    src = helpers.make_xmp_png(tmp_path / "z.png", compressed=True)
    write_output(src, tmp_path / "out", "z.png")
    with Image.open(tmp_path / "out" / "z.png") as im:
        assert not any("xmp" in str(k).lower() or "xml" in str(k).lower() for k in im.info)


def test_makernote_and_exif_thumbnail_dropped_on_reencode(tmp_path):
    src = helpers.make_thumbnail_makernote_jpeg(tmp_path / "m.jpg")
    raw = open(src, "rb").read()
    assert helpers.MAKERNOTE in raw and raw.count(b"\xff\xd8") == 2  # source has both
    write_output(src, tmp_path / "out", "m.jpg")
    out = open(tmp_path / "out" / "m.jpg", "rb").read()
    assert helpers.MAKERNOTE not in out
    assert out.count(b"\xff\xd8") == 1  # no embedded thumbnail
    with Image.open(tmp_path / "out" / "m.jpg") as im:
        assert im.size == (300, 400) and im.info.get("icc_profile") == helpers.ICC


def test_16bit_grayscale_survives_watermark_and_gps_strip(tmp_path):
    from seo_image.watermark import apply_watermark
    ex = Image.Exif()
    ex[0x8825] = dict(helpers.GPS)
    Image.new("I", (400, 300), 40000).save(tmp_path / "g.png", exif=ex.tobytes())
    # GPS-strip re-encode, no watermark: still 16-bit, same value
    write_output(tmp_path / "g.png", tmp_path / "out", "g.png")
    with Image.open(tmp_path / "out" / "g.png") as im:
        assert im.size == (400, 300) and im.getpixel((10, 10)) == 40000
        assert not im.getexif().get_ifd(0x8825)
    # watermark path: brightness kept (8-bit)
    loaded = load_upright(tmp_path / "g.png")
    loaded.image, _ = apply_watermark(loaded.image, "example.com", "bottom-right", 0.6, 2.5)
    write_output(tmp_path / "g.png", tmp_path / "out2", "g.png", loaded=loaded)
    with Image.open(tmp_path / "out2" / "g.png") as im:
        assert im.size == (400, 300) and abs(im.convert("RGB").getpixel((10, 10))[0] - 156) <= 2


def test_cmyk_jpeg_is_converted_to_rgb_without_a_mismatched_profile(tmp_path):
    Image.new("CMYK", (300, 200), (0, 255, 255, 0)).save(tmp_path / "c.jpg")  # red
    Image.new("CMYK", (300, 200), (0, 255, 255, 0)).save(tmp_path / "p.jpg", icc_profile=helpers.ICC)  # RGB profile on CMYK data
    for name in ("c.jpg", "p.jpg"):
        loaded = load_upright(tmp_path / name)
        assert loaded.image.mode == "RGB"
        write_output(tmp_path / name, tmp_path / "out", name, loaded=loaded)
        with Image.open(tmp_path / "out" / name) as im:
            r, g, b = im.convert("RGB").getpixel((10, 10))
            assert r > 200 and g < 60 and b < 60, name
            assert im.info.get("icc_profile") in (None, loaded.icc)
        assert Image.open(tmp_path / name).mode == "CMYK"  # original untouched


def test_reencode_keeps_icc_and_non_location_exif_but_not_xmp(tmp_path):
    """Documents FR-014: a re-encoded file keeps ICC and EXIF (minus location); XMP and IPTC are not carried."""
    from PIL import PngImagePlugin
    info = PngImagePlugin.PngInfo()
    info.add_itxt("XML:com.adobe.xmp", '<x:xmpmeta xmlns:x="adobe:ns:meta/"><dc:creator>someone</dc:creator></x:xmpmeta>')
    ex = Image.Exif()
    ex[0x010F] = "TestMake"
    ex[0x8825] = dict(helpers.GPS)
    helpers.pattern_image((200, 150)).save(tmp_path / "m.png", pnginfo=info, exif=ex.tobytes(), icc_profile=helpers.ICC)
    write_output(tmp_path / "m.png", tmp_path / "out", "m.png")
    with Image.open(tmp_path / "out" / "m.png") as im:
        assert im.info.get("icc_profile") == helpers.ICC
        assert im.getexif().get(0x010F) == "TestMake" and not im.getexif().get_ifd(0x8825)
        assert b"someone" not in open(tmp_path / "out" / "m.png", "rb").read()
    # nothing to change: byte copy keeps everything
    helpers.pattern_image((200, 150)).save(tmp_path / "k.png", pnginfo=info)
    write_output(tmp_path / "k.png", tmp_path / "out", "k.png")
    assert helpers.sha(tmp_path / "out" / "k.png") == helpers.sha(tmp_path / "k.png")

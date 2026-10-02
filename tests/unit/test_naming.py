import pytest

from seo_image.errors import ImageError
from seo_image.naming import build_filename


def stem(name):
    return build_filename(name, ".jpg")[:-4]


def test_lowercase_hyphens_and_extension_kept():
    assert build_filename("Red Ceramic Mug", ".JPG") == "red-ceramic-mug.jpg"
    assert build_filename("red_mug", "png") == "red-mug.png"


def test_ascii_transliteration():
    assert stem("Café crème table") == "cafe-creme-table"


@pytest.mark.parametrize("raw,expected", [
    ("IMG_1234 red mug", "red-mug"),
    ("DSC0042 blue chair", "blue-chair"),
    ("dscn 0042 blue chair", "blue-chair"),
    ("photo-01 red mug", "red-mug"),
    ("red mug final-2", "red-mug"),
    ("red mug copy 3", "red-mug"),
    ("red mug v2", "red-mug"),
    ("red mug 01", "red-mug"),
])
def test_camera_patterns_and_counters_dropped(raw, expected):
    assert stem(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("3-seater-sofa", "3-seater-sofa"),
    ("4 burner stove", "4-burner-stove"),
    ("1950s diner", "1950s-diner"),
    ("4k monitor desk", "4k-monitor-desk"),
])
def test_content_numbers_kept(raw, expected):
    assert stem(raw) == expected


def test_repeated_words_dropped():
    assert stem("mug mug red mug") == "mug-red"


def test_max_five_words():
    assert stem("one two three four five six seven") == "one-two-three-four-five"


def test_max_sixty_characters_on_word_boundary():
    out = stem("extraordinarily-long-words-everywhere-keep-going")
    assert len(out) <= 60
    assert not out.endswith("-")
    long = stem("a" * 80)
    assert len(long) == 60


def test_empty_result_raises():
    with pytest.raises(ImageError):
        build_filename("IMG_1234", ".jpg")
    with pytest.raises(ImageError):
        build_filename("!!!", ".jpg")


def test_domain_never_in_name():
    assert build_filename("example.com red mug", ".jpg", domain="example.com") == "red-mug.jpg"
    assert "example" not in build_filename("red mug example com", ".jpg", domain="example.com")


def test_no_double_hyphens():
    assert "--" not in stem("red -- mug ,, shelf")

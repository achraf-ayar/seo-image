from seo_image.rules import duplicate_problems, sentence_count, validate_metadata
from helpers import good_metadata


def problems(**over):
    return validate_metadata(good_metadata(**over))


def test_valid_metadata_passes():
    assert problems() == []


def test_alt_length_limit():
    assert problems(alt="a" * 124) == []
    assert any("125" in p for p in problems(alt="a" * 125))


def test_alt_bad_starts():
    for start in ("Image of a mug", "picture of a mug", "PHOTO OF a mug"):
        assert any("must not start" in p for p in problems(alt=start))


def test_alt_keyword_stuffing():
    assert any("stuffing" in p for p in problems(alt="mugs mugs mugs cheap mugs shop"))
    assert problems(alt="Red mugs beside other mugs") == []


def test_domain_in_alt_only_if_visible():
    md = good_metadata(alt="Mug on shelf from example.com")
    assert any("domain" in p for p in validate_metadata(md, [], "example.com"))
    assert validate_metadata(md, ["Visit EXAMPLE.com"], "example.com") == []
    assert validate_metadata(good_metadata(), [], "example.com") == []


def test_unseen_hosts_rejected_with_or_without_a_supplied_domain():
    for field, value in (("alt", "Red mug from shop.examplestore.com"),
                         ("title", "Mug at bestmugs.net"),
                         ("description", "A red mug sits on a shelf. Seen at www.mugs.example today."),
                         ("tags", ["mug", "shelf", "mugs.example.org"])):
        md = good_metadata(**{field: value})
        assert any("not visible" in p for p in validate_metadata(md, [], None)), field
        assert any("not visible" in p for p in validate_metadata(md, [], "other.example")), field


def test_hosts_allowed_when_visible_in_the_image():
    md = good_metadata(alt="Sign reading shop.examplestore.com above a mug")
    assert validate_metadata(md, ["SHOP.examplestore.com"], None) == []
    assert any("not visible" in p for p in validate_metadata(md, ["something else"], None))


def test_ordinary_text_is_not_mistaken_for_a_host():
    for text in ("A mug, e.g. a red one. Next to a plant.", "A 3.5 mm jack beside a mug.",
                 "Mug photo.jpg on a shelf", "i.e. a red mug", "It costs approx. five.", "Mr. Mug and Dr. Cup",
                 "Shelf.It sits there", "St. Mug and etc. things", "A mug (about 3.5 inches) on a shelf."):
        md = good_metadata(description=text + " More words follow here.")
        assert not any("not visible" in p for p in validate_metadata(md)), text


def test_title_rules():
    assert any("title" in p for p in problems(title=""))
    assert any("70" in p for p in problems(title="t" * 71))


def test_sentence_counting():
    assert sentence_count("A mug on a shelf.") == 1
    assert sentence_count("A mug on a shelf. It is red! Really?") == 3
    assert sentence_count("A mug, e.g. a red one. Next to a plant.") == 2
    assert sentence_count("Approx. five mugs sit here. Dr. Smith's desk is nearby.") == 2
    assert sentence_count("") == 0


def test_description_limits():
    assert any("sentences" in p for p in problems(description="One thing. Two thing. Three thing here."))
    assert any("empty" in p for p in problems(description=""))
    assert any("short" in p for p in problems(description="Mug."))


def test_tag_rules():
    assert problems(tags=["a"]) == [] and problems(tags=["a", "b"]) == []  # fewer when the image has less to say
    assert problems(tags=["a", "b", "c"]) == [] and problems(tags=list("abcdefgh")) == []
    assert any("1 to 8" in p for p in problems(tags=[]))
    assert any("1 to 8" in p for p in problems(tags=list("abcdefghi")))
    assert any("unique" in p for p in problems(tags=["Mug", "mug", "cup"]))
    assert any("empty" in p for p in problems(tags=["mug", " "]))
    assert any("list" in p for p in problems(tags="mug, cup"))


def test_duplicates_in_batch():
    md = good_metadata()
    assert duplicate_problems(md, set(), set()) == []
    assert len(duplicate_problems(md, {md["alt"].lower()}, set())) == 1
    assert len(duplicate_problems(md, set(), {md["title"].lower()})) == 1

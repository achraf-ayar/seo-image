import pytest

from seo_image.domain import ascii_form, normalise_domain
from seo_image.errors import FatalError


@pytest.mark.parametrize("raw,expected", [
    ("example.com", "example.com"),
    ("  Example.COM ", "example.com"),
    ("https://www.example.com/path/page?x=1#top", "example.com"),
    ("http://user:pw@example.com:8080/", "example.com"),
    ("//example.com/a", "example.com"),
    ("www.example.com", "example.com"),
    ("blog.example.co.uk", "blog.example.co.uk"),
    ("shop.www.example.org", "shop.www.example.org"),
    ("example.com.", "example.com"),
])
def test_normalises(raw, expected):
    assert normalise_domain(raw) == expected


def test_none_and_empty_mean_no_domain():
    assert normalise_domain(None) is None
    assert normalise_domain("   ") is None


def test_internationalised_names_accepted():
    d = normalise_domain("https://Bücher.example")
    assert d == "bücher.example"
    assert ascii_form(d) == "xn--bcher-kva.example"


@pytest.mark.parametrize("bad", ["localhost", "not a domain", "-bad.com", "bad-.com",
                                 "exa mple.com", "example", "example.c", "http://", "a..b.com",
                                 "exa$mple.com", "example.123"])
def test_rejects_invalid(bad):
    with pytest.raises(FatalError):
        normalise_domain(bad)

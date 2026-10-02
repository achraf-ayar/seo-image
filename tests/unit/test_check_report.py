import json
import os

import check_report as cr

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "semantic", "fixtures")


def result(name="red-mug-on-shelf.png", **kw):
    r = {"original_filename": name, "status": "ok", "alt": "Red mug on a shelf",
         "title": "Red mug", "description": "A red mug sits on a shelf.",
         "tags": ["mug", "shelf", "red"], "new_filename": "red-mug-on-shelf.png"}
    r.update(kw)
    return r


def expected(**kw):
    e = {"must_mention": [["mug", "cup"], ["shelf"]], "must_not_mention": ["wood"],
         "forbidden_terms": ["paris"]}
    e.update(kw)
    return e


def test_clean_result_has_no_problems():
    assert cr.check_result(result(), expected()) == []


def test_flags_forbidden_and_unshown_and_missing():
    p = cr.check_result(result(alt="Wood mug in Paris"), expected(must_mention=[["lamp"]]))
    text = " ".join(p)
    assert "paris" in text and "wood" in text and "lamp" in text


def test_word_boundaries():
    assert cr.check_result(result(alt="Red mug on a shelf, woodland"), expected()) == []


def test_unsupported_context_terms_flagged():
    exp = expected(context={"supported": False, "terms": ["winter"]})
    assert any("winter" in p for p in cr.check_result(result(description="A winter mug."), exp))
    exp = expected(context={"supported": True, "terms": ["winter"]})
    assert cr.check_result(result(description="A winter mug on a shelf."), exp) == []


def test_non_ok_result_is_a_problem():
    assert cr.check_result(result(status="failed", reason="x"), expected())


def test_check_report_matches_fixture_files():
    out = cr.check_report({"results": [result()]}, FIXTURES)
    assert out == {"red-mug-on-shelf.png": []}
    out = cr.check_report({"results": [result(name="unknown.png")]}, FIXTURES)
    assert out == {}


def test_person_fixture_forbids_identity_words():
    exp = json.load(open(os.path.join(FIXTURES, "person-figure.json")))
    assert "john" in exp["forbidden_terms"] and "celebrity" in exp["forbidden_terms"]
    bad = result(name="person-figure.png", alt="John, a young man in a blue top",
                 tags=["person", "figure", "illustration"], new_filename="person-figure.png")
    assert any("john" in p for p in cr.check_result(bad, exp))
    good = result(name="person-figure.png", alt="Simple drawing of a person figure in a blue top",
                  description="A simple drawing of a figure with a round head.",
                  tags=["person", "figure", "illustration"], new_filename="person-figure.png")
    assert cr.check_result(good, exp) == []


def test_tally():
    assert cr.tally(9, 10) == (0.9, True)
    assert cr.tally(8, 10)[1] is False


def test_fixtures_are_complete():
    names = {f[:-5] for f in os.listdir(FIXTURES) if f.endswith(".json")}
    assert len(names) >= 6
    for n in names:
        assert os.path.exists(os.path.join(FIXTURES, n + ".png"))
        exp = json.load(open(os.path.join(FIXTURES, n + ".json")))
        assert exp["must_mention"] and exp["forbidden_terms"]


def test_context_fixtures_are_wired_for_the_checker():
    for name, supported in (("mug-context-supported", True), ("hills-context-unsupported", False)):
        exp = json.load(open(os.path.join(FIXTURES, name + ".json")))
        assert exp["context"]["supported"] is supported and exp["context"]["text"] and exp["context"]["terms"]
        assert os.path.exists(os.path.join(FIXTURES, name + ".png"))
    bad = result(name="hills-context-unsupported.png", alt="Green hills under a winter sky",
                 description="Rolling hills and a sun, ideal for ski holidays.",
                 tags=["hills", "sun", "landscape"], new_filename="hills-context-unsupported.png")
    exp = json.load(open(os.path.join(FIXTURES, "hills-context-unsupported.json")))
    found = " ".join(cr.check_result(bad, exp))
    assert "winter" in found and "ski" in found

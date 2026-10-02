from PIL import Image

import helpers
from seo_image.corners import busy_score, choose_corner, corner_box, measure_corners

ALL_FREE = {c: "free" for c in ("top-left", "top-right", "bottom-left", "bottom-right")}
BUSY = {"top-left": 5, "top-right": 1, "bottom-left": 3, "bottom-right": 9}


def labels(**over):
    d = dict(ALL_FREE)
    d.update({k.replace("_", "-"): v for k, v in over.items()})
    return d


def test_bottom_right_is_default_when_free():
    assert choose_corner(ALL_FREE, BUSY) == "bottom-right"


def test_least_busy_free_corner_when_default_is_taken():
    assert choose_corner(labels(bottom_right="subject"), BUSY) == "top-right"
    assert choose_corner(labels(bottom_right="face_or_text", top_right="face_or_text"), BUSY) == "bottom-left"


def test_subject_corner_used_when_no_free_corner():
    lab = {"top-left": "subject", "top-right": "face_or_text", "bottom-left": "subject",
           "bottom-right": "face_or_text"}
    assert choose_corner(lab, BUSY) == "bottom-left"


def test_skip_when_every_corner_is_face_or_text():
    assert choose_corner({c: "face_or_text" for c in ALL_FREE}, BUSY) is None


def test_configured_start_replaces_default():
    assert choose_corner(ALL_FREE, BUSY, start="top-left") == "top-left"
    assert choose_corner(labels(top_left="subject"), BUSY, start="top-left") == "top-right"


def test_corner_box_positions_inside_margin():
    for corner in ALL_FREE:
        x0, y0, x1, y1 = corner_box(corner, (400, 300), (80, 20), 8)
        assert x0 >= 8 and y0 >= 8 and x1 <= 392 and y1 <= 292 and (x1 - x0, y1 - y0) == (80, 20)
    assert corner_box("bottom-right", (400, 300), (80, 20), 8) == (312, 272, 392, 292)
    assert corner_box("top-left", (400, 300), (80, 20), 8) == (8, 8, 88, 28)


def test_busy_score_orders_flat_below_noise():
    flat = helpers.pattern_image((100, 100), "flat")
    noise = helpers.pattern_image((100, 100), "noise")
    box = (0, 0, 100, 100)
    assert busy_score(flat, box) == 0
    assert busy_score(noise, box) > 20


def test_measure_corners_finds_the_noisy_corner():
    img = helpers.noisy_corner(helpers.pattern_image((400, 300), "flat"), "top-left")
    scores = measure_corners(img, (60, 16), 8)
    assert scores["top-left"] == max(scores.values())
    assert scores["bottom-right"] == 0

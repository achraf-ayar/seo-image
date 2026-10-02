from seo_image.naming import resolve_collision


def test_no_collision_returns_name_unchanged():
    assert resolve_collision("red-mug.jpg", set()) == "red-mug.jpg"
    assert resolve_collision("red-mug.jpg", {"blue-mug.jpg"}, "blue") == "red-mug.jpg"


def test_distinguisher_word_used_first():
    assert resolve_collision("red-mug.jpg", {"red-mug.jpg"}, "glossy") == "red-mug-glossy.jpg"


def test_numeric_suffix_when_no_distinguisher():
    taken = {"red-mug.jpg"}
    assert resolve_collision("red-mug.jpg", taken) == "red-mug-2.jpg"
    taken.add("red-mug-2.jpg")
    assert resolve_collision("red-mug.jpg", taken) == "red-mug-3.jpg"


def test_distinguisher_that_would_break_word_limit_falls_back_to_number():
    name = "one-two-three-four-five.jpg"
    assert resolve_collision(name, {name}, "six") == "one-two-three-four-five-2.jpg"


def test_distinguisher_already_in_name_falls_back_to_number():
    assert resolve_collision("red-mug.jpg", {"red-mug.jpg"}, "red") == "red-mug-2.jpg"


def test_taken_distinguished_name_falls_back_to_number():
    taken = {"red-mug.jpg", "red-mug-glossy.jpg"}
    assert resolve_collision("red-mug.jpg", taken, "glossy") == "red-mug-2.jpg"


def test_case_insensitive():
    assert resolve_collision("Red-Mug.jpg", {"red-mug.jpg"}) == "Red-Mug-2.jpg"


def test_numeric_suffix_respects_sixty_characters():
    name = "a" * 60 + ".jpg"
    out = resolve_collision(name, {name})
    assert len(out) - 4 <= 60 and out.endswith("-2.jpg")


def test_existing_file_in_output_folder_is_not_a_collision():
    # `taken` only holds names assigned in this batch; files from earlier runs are replaced.
    assert resolve_collision("red-mug.jpg", set()) == "red-mug.jpg"

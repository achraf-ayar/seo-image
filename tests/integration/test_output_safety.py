import os

import helpers


def test_output_folder_equal_to_input_folder_refused(tmp_path, run_cli, write_analysis):
    d = tmp_path / "images"
    d.mkdir()
    src = helpers.make_image(d / "a.png")
    before = helpers.sha(src)
    code, _, err = run_cli("apply", write_analysis([helpers.analysis_entry(src, corners=False)]),
                           "--out", d)
    assert code == 2 and "output folder" in err
    assert sorted(os.listdir(d)) == ["a.png"] and helpers.sha(src) == before
    code, _, err = run_cli("inspect", src, "--out", d)
    assert code == 2


def test_output_folder_containing_the_input_folder_refused(tmp_path, run_cli, write_analysis):
    d = tmp_path / "images" / "sub"
    d.mkdir(parents=True)
    src = helpers.make_image(d / "a.png")
    code, _, err = run_cli("apply", write_analysis([helpers.analysis_entry(src, corners=False)]),
                           "--out", tmp_path / "images")
    assert code == 2
    assert sorted(os.listdir(tmp_path / "images")) == ["sub"]
    code, _, _ = run_cli("apply", write_analysis([helpers.analysis_entry(src, corners=False)]), "--out", tmp_path)
    assert code == 2


def test_default_subfolder_next_to_images_in_the_working_folder_is_allowed(tmp_path, run_cli, write_analysis):
    src = helpers.make_image(tmp_path / "a.png")  # input lives in the working folder
    code, _, _ = run_cli("apply", write_analysis([helpers.analysis_entry(src, corners=False)]))
    assert code == 0 and (tmp_path / "seo-images" / "report.json").exists()


def test_no_inputs_matched_is_fatal(tmp_path, run_cli):
    code, _, err = run_cli("inspect", "nothing/*.jpg")
    assert code == 2 and "no input files" in err
    code, _, err = run_cli("inspect", "missing.jpg")
    assert code == 2
    assert not (tmp_path / "seo-images").exists()


def test_missing_literal_path_among_others_is_reported(tmp_path, run_cli):
    import json
    src = helpers.make_image(tmp_path / "a.png")
    code, out, _ = run_cli("inspect", src, "missing.jpg")
    imgs = {i["original_filename"]: i for i in json.loads(out)["images"]}
    assert imgs["missing.jpg"]["status"] == "unreadable"

import json
import os

import jsonschema
import pytest

from seo_image.config import load_config, resolve_settings, validate_config
from seo_image.errors import FatalError

SCHEMA = json.load(open(os.path.join(os.path.dirname(__file__), "..", "..", "specs",
                                     "001-seo-image-skill", "contracts", "config.schema.json")))
EXAMPLE = os.path.join(os.path.dirname(__file__), "..", "..", ".claude", "skills", "seo-image",
                       "seo-image.config.example.json")


def test_example_config_matches_schema_and_code():
    cfg = json.load(open(EXAMPLE))
    jsonschema.validate(cfg, SCHEMA)
    validate_config(cfg)
    assert cfg["domain"] == "example.com"


def test_missing_file_means_defaults(tmp_path):
    assert load_config(tmp_path / "nope.json") == {}
    s = resolve_settings({})
    assert (s.domain, s.watermark_enabled, s.position, s.opacity, s.size, s.output_dir) == \
        (None, True, "bottom-right", 0.6, 2.5, "seo-images")


def test_loads_from_working_folder_by_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "seo-image.config.json").write_text('{"domain": "example.com"}')
    assert load_config() == {"domain": "example.com"}


def test_flags_override_config_which_overrides_defaults():
    cfg = {"domain": "config.example", "output_dir": "cfg-out",
           "watermark": {"position": "top-left", "opacity": 0.3, "size": 4}}
    s = resolve_settings(cfg)
    assert (s.domain, s.output_dir, s.position, s.opacity, s.size) == ("config.example", "cfg-out", "top-left", 0.3, 4)
    s = resolve_settings(cfg, site="https://www.flag.example/x", out="flag-out")
    assert (s.domain, s.output_dir, s.position) == ("flag.example", "flag-out", "top-left")


@pytest.mark.parametrize("bad", [
    {"unknown": 1},
    {"watermark": {"colour": "red"}},
    {"watermark": {"opacity": 0.05}},
    {"watermark": {"opacity": 1.5}},
    {"watermark": {"size": 0}},
    {"watermark": {"size": 7}},
    {"watermark": {"position": "middle"}},
    {"watermark": {"enabled": "yes"}},
    {"domain": 5},
    {"output_dir": 5},
    [],
])
def test_rejects_invalid_config(bad):
    with pytest.raises(FatalError):
        validate_config(bad)


@pytest.mark.parametrize("bad", [
    {"unknown": 1}, {"watermark": {"opacity": 0.05}}, {"watermark": {"size": 7}},
    {"watermark": {"position": "middle"}}, {"domain": 5},
])
def test_code_and_schema_agree_on_rejections(bad):
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, SCHEMA)
    with pytest.raises(FatalError):
        validate_config(bad)


def test_invalid_json_is_fatal(tmp_path):
    p = tmp_path / "c.json"
    p.write_text("{not json")
    with pytest.raises(FatalError):
        load_config(p)


def test_invalid_domain_in_config_is_fatal():
    with pytest.raises(FatalError):
        resolve_settings({"domain": "nonsense"})

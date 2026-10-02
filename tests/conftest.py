import json

import pytest

from helpers import analysis_entry


@pytest.fixture
def run_cli(tmp_path, monkeypatch, capsys):
    """Run the helper CLI inside tmp_path and return (exit_code, stdout, stderr)."""
    monkeypatch.chdir(tmp_path)

    def _run(*argv):
        from seo_image import cli
        capsys.readouterr()
        code = cli.main([str(a) for a in argv])
        out = capsys.readouterr()
        return code, out.out, out.err

    return _run


@pytest.fixture
def write_analysis(tmp_path):
    def _write(entries, name="analysis.json"):
        p = tmp_path / name
        p.write_text(json.dumps(entries))
        return p

    return _write


__all__ = ["analysis_entry"]

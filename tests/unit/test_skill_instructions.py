"""The commands written in SKILL.md must actually run in a shell."""
import os
import re
import subprocess

SKILL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".claude", "skills", "seo-image"))
TEXT = open(os.path.join(SKILL_DIR, "SKILL.md"), encoding="utf-8").read()
COMMAND = re.compile(r'^(PYTHONPATH="\$\{CLAUDE_SKILL_DIR\}/scripts" python3 -m seo_image (inspect|apply))\b', re.M)


def test_both_helper_commands_are_documented_as_single_runnable_lines():
    found = {m.group(2) for m in COMMAND.finditer(TEXT)}
    assert found == {"inspect", "apply"}


def test_no_command_is_built_from_a_variable_holding_an_assignment():
    # `VAR="PYTHONPATH=... python3 ..."; $VAR` fails: expansion does not create an env assignment.
    assert not re.search(r'^\w+="PYTHONPATH=', TEXT, re.M)
    assert "$SEO" not in TEXT


def test_documented_commands_run_in_a_shell():
    env = dict(os.environ, CLAUDE_SKILL_DIR=SKILL_DIR)
    for m in COMMAND.finditer(TEXT):
        done = subprocess.run(["bash", "-c", m.group(1) + " --help"], env=env, capture_output=True, text=True)
        assert done.returncode == 0, done.stderr
        assert m.group(2) in done.stdout

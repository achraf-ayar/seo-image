"""Mechanical first pass over a report, so the human reviewer only confirms.

Usage:
    python tests/semantic/check_report.py <report.json> [fixtures_dir] [--tally ACCURATE TOTAL]

A result is matched to a fixture by original filename (`<name>.png` -> `<name>.json`).
It flags forbidden terms (fabricated brands, places, names, identities), must_not_mention
terms (details the image does not show), missing required terms, and context terms that
the image does not support.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FIXTURES = os.path.join(HERE, "fixtures")
TARGET = 0.90


def _text(result):
    parts = [result.get("alt"), result.get("title"), result.get("description"),
             " ".join(result.get("tags") or []), (result.get("new_filename") or "").rsplit(".", 1)[0]]
    return " ".join(p for p in parts if p).lower().replace("-", " ")


def _has(text, term):
    return re.search(rf"\b{re.escape(term.lower())}\b", text) is not None


def check_result(result, expected):
    """Return a list of problems for one result against one fixture's expectations."""
    text = _text(result)
    problems = []
    if result.get("status") != "ok":
        return [f"result status is {result.get('status')}: {result.get('reason')}"]
    for term in expected.get("forbidden_terms", []):
        if _has(text, term):
            problems.append(f"forbidden term present: {term!r}")
    for term in expected.get("must_not_mention", []):
        if _has(text, term):
            problems.append(f"detail not shown by the image: {term!r}")
    for group in expected.get("must_mention", []):
        if not any(_has(text, t) for t in group):
            problems.append(f"missing one of: {', '.join(group)}")
    ctx = expected.get("context")
    if ctx and ctx.get("supported") is False:
        for term in ctx.get("terms", []):
            if _has(text, term):
                problems.append(f"unsupported context term used: {term!r}")
    return problems


def check_report(report, fixtures_dir=DEFAULT_FIXTURES):
    """Return {original_filename: [problems]} for every result that has a fixture."""
    found = {}
    for r in report.get("results", []):
        name = os.path.splitext(r.get("original_filename", ""))[0]
        path = os.path.join(fixtures_dir, name + ".json")
        if os.path.isfile(path):
            found[r["original_filename"]] = check_result(r, json.load(open(path)))
    return found


def tally(accurate, total):
    pct = accurate / total if total else 0.0
    return pct, pct >= TARGET


def main(argv):
    args = list(argv)
    tl = None
    if "--tally" in args:
        i = args.index("--tally")
        tl = (int(args[i + 1]), int(args[i + 2]))
        del args[i:i + 3]
    report = json.load(open(args[0]))
    fixtures = args[1] if len(args) > 1 else DEFAULT_FIXTURES
    outcome = check_report(report, fixtures)
    bad = 0
    for name, problems in outcome.items():
        print(("FAIL " if problems else "ok   ") + name)
        for p in problems:
            print("     -", p)
        bad += bool(problems)
    if not outcome:
        print("no results matched a fixture")
    if tl:
        pct, ok = tally(*tl)
        print(f"reviewer tally: {tl[0]}/{tl[1]} = {pct:.0%} ({'meets' if ok else 'below'} the 90% target)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

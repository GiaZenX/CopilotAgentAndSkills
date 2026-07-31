#!/usr/bin/env python3
"""
report_lint.py — overstatement and cherry-picking markers in research reports (parity risk R9).

The constitution's rule is prose and stays prose: "never p-hack or overstate; report what the data
supports; name threats to validity." Whether a claim is overstated is a judgement about the DATA,
and no pattern can make it. What a pattern CAN do is notice the shapes overstatement takes in
writing — an unhedged causal claim, a superlative with no number behind it, a result reported
without its n, the word "significant" used as a synonym for "large".

SO THIS ONLY EVER WARNS. The user's "maximal härten" decision is explicit that the R2/R9/R13
heuristics warn and are never fail-closed, and that a heuristic which does not earn its keep goes
back to being prose. A lint that blocks a report because it contains the word "proves" would be
worse than nothing: it teaches the writer to avoid the word rather than the claim.

  exit 0 always. Findings go to stdout, one per line, with the sentence that triggered them.

Usage:  python scripts/report_lint.py                    # every tracked report
        python scripts/report_lint.py reports/x.md ...   # named files
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Each pattern names a SHAPE, and each one has a counter-shape that makes it silent: a number, a
# hedge, an n. That is what keeps this from flagging every honest sentence.
MARKERS = (
    ("causal claim without a hedge",
     r"\b(?:proves?|proven|demonstrates conclusively|shows definitively|confirms that|"
     r"beweist|belegt eindeutig)\b",
     "a study supports or is consistent with; it rarely proves. Say what the data supports, or "
     "name the inference step you are making."),
    ("superlative with no number",
     r"\b(?:dramatic(?:ally)?|massive(?:ly)?|huge|enormous|vastly|by far|deutlich besser|"
     r"drastisch|enorm)\b",
     "put the effect size and its interval next to the adjective, or drop the adjective."),
    ("'significant' as a synonym for 'large'",
     r"\bsignificant(?:ly)?\b(?![^\n]{0,40}\bp\s*[<=])|\bsignifikant\b(?![^\n]{0,40}\bp\s*[<=])",
     "statistical significance needs its test and p-value; if you mean 'large', say large."),
    ("result without an n",
     r"\b\d+(?:[.,]\d+)?\s*%(?![^\n]{0,60}\b(?:n\s*=|von\s+\d|of\s+\d|N\s*=))",
     "a percentage without its denominator hides the sample — 80% of 5 is four."),
    ("selective reporting",
     r"\b(?:best[- ]case|cherry[- ]?pick|we focus on the runs where|nur die Läufe|"
     r"the most favou?rable)\b",
     "report the whole set or say explicitly which runs were excluded and why."),
    ("hypothesis stated after the fact",
     r"\b(?:as expected|wie erwartet|as predicted|which confirms our)\b",
     "if the prediction was registered before the run, cite the HYP; if not, say so."),
)
_COMPILED = [(label, re.compile(pattern, re.IGNORECASE), advice)
             for label, pattern, advice in MARKERS]
# A sentence that already carries its uncertainty is doing the thing this lint asks for.
_HEDGED_RX = re.compile(
    r"\b(?:may|might|could|suggests?|indicates?|consistent with|appears? to|we did not|"
    r"limitation|threat to validity|caveat|koennte|deutet darauf|Einschränkung)\b",
    re.IGNORECASE)


def tracked_reports():
    try:
        result = subprocess.run(["git", "-C", ROOT, "ls-files", "reports", "evidence"],
                                capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=60)
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines()
            if line.strip().lower().endswith((".md", ".txt"))]


def lint(rel):
    findings = []
    try:
        with open(os.path.join(ROOT, rel), encoding="utf-8", errors="ignore") as handle:
            text = handle.read()
    except OSError:
        return findings
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith(("#", ">", "|", "-", "*")):
            continue          # headings, quotes, tables and bullets are not claims by themselves
        if _HEDGED_RX.search(line):
            continue          # the sentence already carries its uncertainty
        for label, pattern, advice in _COMPILED:
            match = pattern.search(line)
            if match:
                findings.append((rel, number, label, match.group(0), line.strip()[:110], advice))
                break
    return findings


# WHO RUNS THIS. Until 2026-07-31 nobody did: measured across the whole shipped tree, this file
# was named by no hook, no settings.json, no CI file, no pre-commit config and no SKILL -- a lint
# that had been written, documented and tested and could not fire. `scripts/quality.py` discovers
# every sibling that declares this pair (see `quality.auxiliary_stages`), so the wiring is a
# property of the module rather than a name in a list the research kit's quality.py could not
# carry anyway (it is byte-identical to the dev kit's, which ships no report_lint).
#
# `warn`, not `fail`, and that is the same decision the module docstring makes for its own exit
# code: whether a claim is overstated is a judgement about the DATA. A pipeline that went RED on
# the word "proves" would teach word-avoidance rather than honesty.
#
# quality.py READS this by parsing the file and then runs the checker as a SUBPROCESS
# (`--quality-stage`); it never imports it. So this declaration is data, and nothing in this module
# runs inside the process that owns the pipeline verdict.
QUALITY_STAGE = ("research report lint", "warn")
STAGE_FLAG = "--quality-stage"


def quality_stage():
    """(rc, text) for `scripts/quality.py`: rc 1 when there are markers, so the pipeline WARNS.

    Separate from `main()` because `main()`'s contract is "exit 0 always" and a CI may rely on it.
    A warning does not fail the pipeline either -- the exit code here only tells quality.py
    whether there is anything to say.
    """
    targets = tracked_reports()
    findings = [f for rel in targets for f in lint(rel)]
    if not findings:
        return 0, "[report_lint] %d report(s): no overstatement markers." % len(targets)
    lines = ["[report_lint] %d marker(s) -- ADVISORY, nothing is blocked:" % len(findings)]
    lines += ["  %s:%d  %s (%r)" % (rel, number, label, hit)
              for rel, number, label, hit, _line, _advice in findings[:40]]
    return 1, "\n".join(lines)


def main():
    targets = [a for a in sys.argv[1:] if not a.startswith("-")] or tracked_reports()
    if not targets:
        print("[report_lint] no reports to check.")
        return 0
    findings = [f for rel in targets for f in lint(rel)]
    if not findings:
        print("[report_lint] %d report(s): no overstatement markers." % len(targets))
        return 0
    print("[report_lint] %d marker(s) — ADVISORY, nothing is blocked:" % len(findings))
    for rel, number, label, hit, line, advice in findings[:40]:
        print("  %s:%d  %s (%r)\n      %s\n      -> %s" % (rel, number, label, hit, line, advice))
    if len(findings) > 40:
        print("  … and %d more" % (len(findings) - 40))
    print("\nWhether a claim is overstated is a judgement about the DATA, which no pattern can "
          "make — these are SHAPES overstatement takes in writing. If a marker is wrong here, it "
          "is wrong; the rule it serves ('report what the data supports, name threats to "
          "validity') stays a matter of judgement.")
    return 0          # ALWAYS: a lint that blocks a report teaches word-avoidance, not honesty


if __name__ == "__main__":
    # The pipeline's entry, kept OUT of `main()` so the stand-alone contract ("exit 0 always")
    # stays what the module docstring says it is.
    if STAGE_FLAG in sys.argv[1:]:
        _rc, _text = quality_stage()
        print(_text)
        sys.exit(_rc)
    sys.exit(main())

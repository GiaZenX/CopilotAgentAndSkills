"""The USER-scope defaults this harness installs into `~/.claude/settings.json` (FR-0055).

WHY THIS IS ITS OWN FILE. The shipped defaults and the merger that installs them are one subject:
what the file CLAIMS about itself ("deliberately NOT shipped") and what it actually carries have to
agree, and the merge semantics ("personal values win") is what makes shipping a default safe at
all. Both ends are measured here -- the defaults by parsing them, the merge by running
`user/merge_settings.py` as a PROCESS against a throwaway target, which is the way an installer
runs it.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULTS = os.path.join(ROOT, "user", "claude", "settings.json")
MERGE = os.path.join(ROOT, "user", "merge_settings.py")

# The clause the shipped comment uses to list what it does NOT ship. One spelling, read by the
# tripwire below; a comment that stops using it makes that test fail rather than pass quietly.
NOT_SHIPPED_CLAUSE = "Deliberately NOT shipped"
KEY = "remoteControlAtStartup"


def _defaults():
    with open(DEFAULTS, encoding="utf-8") as handle:
        return json.load(handle)


def _merge(tmp_path, target_body):
    """Run the shipped merger the way the installer runs it, and hand back the merged target."""
    target = os.path.join(str(tmp_path), "home", ".claude", "settings.json")
    if target_body is not None:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as handle:
            json.dump(target_body, handle)
    result = subprocess.run([sys.executable, "-B", MERGE, DEFAULTS, target],
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    with open(target, encoding="utf-8") as handle:
        return json.load(handle), result


def test_the_shipped_defaults_turn_remote_control_off(tmp_path):
    """A fresh installation starts with remote control OFF rather than on the provider default.

    Measured through the merger, not only in the file: a key the shipped defaults carry but the
    merger drops would be a default nobody receives.
    """
    assert _defaults()[KEY] is False
    merged, result = _merge(tmp_path, None)
    assert merged[KEY] is False, merged
    assert KEY in result.stdout, result.stdout


def test_a_machine_that_already_set_remote_control_keeps_its_own_value(tmp_path):
    """Personal values win -- the whole reason a default may be shipped here at all.

    The interesting direction is `true`, because that is the value the shipped default contradicts:
    an installer that overwrote it would be turning a user's own setting off behind their back.
    """
    merged, result = _merge(tmp_path, {KEY: True, "theme": "light"})
    assert merged[KEY] is True, merged
    assert merged["theme"] == "light", merged
    assert KEY in result.stdout.split("preserved existing=")[1], result.stdout


def test_no_key_the_defaults_ship_is_still_listed_as_deliberately_not_shipped():
    """The file's own claim about itself, checked against the file (house rule: no rotting claim).

    Every dotted path the "deliberately NOT shipped" clause names is resolved against the shipped
    defaults and has to be ABSENT. That is what made this round's change two changes rather than
    one: `remoteControlAtStartup` stood in that clause, and shipping it while the sentence stayed
    would have left the file saying the opposite of what it does.
    """
    defaults = _defaults()
    clause = defaults["_comment"].split(NOT_SHIPPED_CLAUSE, 1)
    assert len(clause) == 2, "the comment no longer carries the clause this test reads"
    listed = clause[1].split("):", 1)[1].split(". ")[0]
    names = []
    for part in listed.split(","):
        word = part.strip().split(" ")[0].strip("`.")
        if word and all(segment.isidentifier() for segment in word.split(".")):
            names.append(word)
    assert names, listed
    for dotted in names:
        node, present = defaults, True
        for segment in dotted.split("."):
            if isinstance(node, dict) and segment in node:
                node = node[segment]
            else:
                present = False
                break
        assert not present, (
            "%s is listed as deliberately NOT shipped and the defaults ship it" % dotted)

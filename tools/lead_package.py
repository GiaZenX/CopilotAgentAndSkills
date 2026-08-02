#!/usr/bin/env python3
"""The lead instruction package — ONE definition of what it is and how big it may get.

WHY THIS FILE EXISTS. The budget spec II.5 names FIRST was written down three times and in three
spellings: the spec said "≤25 KB", `tools/validate.py` enforced `25 * 1024`, and a work order
handed on `25 000`. Three numbers for one budget is the shape that decides an argument by whichever
copy the reader happened to open. The number lives here now; `validate.py` imports it, the
shortening net imports the file derivation beside it, and
`test_shortening_net.py:test_the_spec_states_the_byte_budget_it_enforces` measures the sentence in
`docs/HARNESS_V2_SPEC.md` II.5 against this constant rather than against another sentence.

WHY 25 600 AND NOT 25 000. It is the running implementation, and it is the natural reading of the
spec's own "25 KB": a kilobyte in a context-window budget is 1024 bytes. Nothing else about the
number is derivable — it is a ceiling somebody chose — and that is precisely why there may be only
one place to change it.

WHAT IS NOT HERE, deliberately: a per-FILE ceiling. The constitution used to carry one (220 lines,
`validate.py`), and measured it said nothing about size — all three constitutions held it only
because 31 to 46 of their lines ran between 110 and 1 899 characters; reflowed to 100 columns the
same texts are 383/368/394 lines. A compaction pilot then cut 24.9 % of the BYTES while the line
count rose from 20 to 36, so the line ceiling actively pushed against the byte budget standing
beside it. No number for one file of the package follows from anything: any split of 25 600 across
three files would be a second invented constant next to the first. So the package is the subject,
and there is exactly one size statement about a constitution — this one, through the package it is
part of.
"""
import json
import os

# spec II.5, "Lead-Instruktionspaket ≤25 KB" — see the module docstring for why 1024 and not 1000
MAX_BYTES = 25 * 1024


def files(kit_dir):
    """The files a session loads and never unloads, for the kit in `kit_dir`.

    DERIVED FROM THE KIT, not listed: the constitution (it reaches the session through the
    `CLAUDE.md` import shim, so it is loaded whether or not anybody asked for it) plus the agent
    file and SKILL of whichever role `settings/settings.json` names as `agent`. A kit that renames
    its lead therefore moves its own budget subject, and no reader has to be told.

    Files that do not exist are dropped rather than counted as zero, so a kit missing its lead SKILL
    reports the size it really has.
    """
    settings = os.path.join(kit_dir, "settings", "settings.json")
    paths = [os.path.join(kit_dir, "constitution", "AGENTS.md")]
    if os.path.isfile(settings):
        with open(settings, encoding="utf-8") as handle:
            lead = json.load(handle).get("agent")
        if lead:
            paths += [os.path.join(kit_dir, "agents", lead + ".md"),
                      os.path.join(kit_dir, "skills", lead, "SKILL.md")]
    return tuple(path for path in paths if os.path.isfile(path))


def size(kit_dir):
    """Bytes on disk for the whole package — the one measurement the budget is compared against."""
    return sum(os.path.getsize(path) for path in files(kit_dir))

#!/usr/bin/env python3
"""The lead instruction package — ONE definition of what it is and how big it may get.

WHY THIS FILE EXISTS. The budget spec II.5 names FIRST was written down three times and in three
spellings: the spec said "≤25 KB", `tools/validate.py` enforced `25 * 1024`, and a work order
handed on `25 000`. Three numbers for one budget is the shape that decides an argument by whichever
copy the reader happened to open. The subject lives here now; `validate.py` imports it and the
shortening net imports the file derivation beside it.

WHY THERE IS NO CONSTANT ANY MORE, and this is the correction of 2026-08-03. 25 600 was `25 KB`
read at 1024 bytes to the kilobyte — a decision about TYPOGRAPHY, not about content. Nothing else
about it followed from anything: it was never computed against what a kit carries, and until
2026-08-02 it was compared against a total that included a 21 KB file which does not load at all.
Measured after every duplication between the two loaded files was removed that could be measured
(see `tools/test_context_budget.py`), the smallest package is still ~30 KB, and what stands between
30 KB and 25 600 B is not padding: it is rules the parity matrix classifies `behalten`, plus the
work-loop skeleton the constitutions carry BECAUSE the lead SKILL does not load. So the ceiling was
unreachable without deleting rules somebody decided to keep — and it only ever warned. A limit that
is missed by all three subjects, forever, and warns, is not a limit; it is a number people step
over.

WHAT REPLACED IT. The one figure that IS derivable from something is the MEASUREMENT: what each
kit's package weighs today. `tools/lead_package_sizes.json` records it per kit, `validate.py` FAILS
when a package exceeds its own record, and the record moves only through
`python tools/record_lead_package_sizes.py --write --note "<reason>"`, which writes one journal
line per kit into `docs/reviews/phase0-disposition.md`. So the rule is no longer "stay under a
number somebody chose" but "you may not grow without saying why" — the same instrument the section
pin already is, one dimension over. There is deliberately NO slack on top of the measurement: a
margin would be a second invented number beside the one just removed.

WHAT THIS DOES NOT DO, said here rather than discovered later: it does not push a package DOWNWARD.
Nothing in a ratchet asks for less; shrinking is free and re-recording is what makes it stick. The
pressure to shorten comes from II.11/3 and from whoever reads the three sizes in the journal, not
from this file.

WHAT IS NOT HERE, deliberately: a per-FILE ceiling. The constitution used to carry one (220 lines,
`validate.py`), and measured it said nothing about size — all three constitutions held it only
because 31 to 46 of their lines ran between 110 and 1 899 characters; reflowed to 100 columns the
same texts are 383/368/394 lines. A compaction pilot then cut 24.9 % of the BYTES while the line
count rose from 20 to 36, so the line ceiling actively pushed against the byte budget standing
beside it. No number for one file of the package follows from anything, so the package is the
subject and there is exactly one size statement about a constitution — this one, through the
package it is part of.
"""
import io
import json
import os

RECORD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lead_package_sizes.json")


def lead_role(kit_dir):
    """The role `settings/settings.json` binds as the session agent, or None."""
    settings = os.path.join(kit_dir, "settings", "settings.json")
    if not os.path.isfile(settings):
        return None
    with open(settings, encoding="utf-8") as handle:
        return json.load(handle).get("agent") or None


def files(kit_dir):
    """The files a session LOADS and never unloads, for the kit in `kit_dir`.

    DERIVED FROM THE KIT, not listed: the constitution (it reaches the session through the
    `CLAUDE.md` import shim, and Codex reads `AGENTS.md` natively, so it is loaded whether or not
    anybody asked for it) plus the agent file of whichever role `settings/settings.json` names as
    `agent`. A kit that renames its lead therefore moves its own budget subject, and no reader has
    to be told.

    THE LEAD SKILL IS NOT IN HERE ANY MORE, and that correction is the reason this docstring is
    longer than the function. It was counted as loaded on the strength of its own frontmatter. What
    a real measurement showed (2026-08-02, three sessions, two kits, control words at each file's
    end, `--tools ""` so the session could not read anything back): the constitution came through
    the `CLAUDE.md` shim VERBATIM, the agent file came through VERBATIM, and the SKILL was ABSENT.
    The provider's own `init` line lists it under `skills` AND `slash_commands` — registered on
    demand, not injected. Counting 21 572 bytes of dev-team SKILL as loaded made this budget a
    measurement of the wrong subject in both directions at once.

    What replaced the SKILL's content in the start context is not this function's business: it is
    the work-loop skeleton in the constitutions (§5a in dev/research, the office equivalent), which
    is in here because the constitution is.

    Files that do not exist are dropped rather than counted as zero, so a kit missing one of them
    reports the size it really has.
    """
    lead = lead_role(kit_dir)
    paths = [os.path.join(kit_dir, "constitution", "AGENTS.md")]
    if lead:
        paths.append(os.path.join(kit_dir, "agents", lead + ".md"))
    return tuple(path for path in paths if os.path.isfile(path))


def on_demand_files(kit_dir):
    """Instruction files the session can REACH but does not load — the lead SKILL.

    A separate answer to a separate question, and keeping the two apart is the whole point of the
    correction above. The budget weighs what LOADS; other readers ask what carries RULES, and a
    document that only loads when the session invokes it carries rules all the same
    (`tools/test_shortening_net.py::_pinned_files` is the one that asks). Merging the two lists
    either way reopens a hole: merged INTO `files()` the budget lies, merged OUT of the pin the
    lead SKILL becomes deletable with the suite green — which is measured, and is why the pin
    exists.
    """
    lead = lead_role(kit_dir)
    if not lead:
        return ()
    path = os.path.join(kit_dir, "skills", lead, "SKILL.md")
    return (path,) if os.path.isfile(path) else ()


def size(kit_dir):
    """Bytes on disk for the whole package — the one measurement the record is compared against."""
    return sum(os.path.getsize(path) for path in files(kit_dir))


def records(path=RECORD):
    """{kit name: recorded bytes} — the ceilings, read from the file the recorder writes.

    Keyed by the kit DIRECTORY NAME rather than by a path, so the record survives a checkout in
    another location and says nothing about where this repo sits. A missing or unreadable file is
    an empty record, and the callers treat "this kit has no record" as a finding rather than as
    permission — an unrecorded package is exactly the state a ratchet must not wave through.
    """
    try:
        with io.open(path, encoding="utf-8") as handle:
            loaded = json.load(handle)
    except (OSError, ValueError):
        return {}
    return {str(kit): int(value) for kit, value in (loaded.get("sizes") or {}).items()}


def ceiling(kit_dir, path=RECORD):
    """The recorded size this kit's package may not exceed, or None if it has no record."""
    return records(path).get(os.path.basename(os.path.abspath(kit_dir)))

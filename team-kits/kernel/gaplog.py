"""The per-project KIT-GAP LOG -- where a session records what the kit could not do (FR-0062).

THE MEASURED COST THIS EXISTS AGAINST. Twice inside one week a live project ran into a wall the kit
had no route around (BUG-0068, BUG-0070), and both were recovered only because the harness lead read
the project's ENTIRE sessions afterwards. The constitutions say "report the gap", the manager
reports it in the chat, and the chat is gone by the next compaction. What was missing is a place the
report SURVIVES in, and one the lead can read across repos instead of reading sessions.

THE TRUST DIRECTION IS WHY IT IS PER PROJECT AND NOT CENTRAL. The obvious shape -- one file in the
repo that manufactures the kits -- would have project sessions writing into the tree that builds
their own guards, over a path that is only correct on one machine. So the log lives in the project
that hit the gap, and the harvest reads it from outside (`tools/harvest_kit_gaps.py` in the harness
repo). Nothing in a project ever writes to the harness.

THE KERNEL IS THE WRITER, which is the whole reason this is a module and not a sentence in a role
text. `gate_write_scope` refuses every agent write under `project_memory/`, and that stays true: the
role runs a COMMAND and the command writes. The log sits in `.audit/`, the same area the hooks
already log to and one no template ships (`tools/test_hooks.py` -> `STATE_DIRS_NOT_SHIPPED`), so an
agent cannot mint an entry by hand any more than it can mint an attestation.

THE ENTRY IS SMALL AND CARRIES NO VOCABULARY. There is no `kind:`, no severity, no category -- P4-12
is what an enumerated vocabulary in a kit document costs when a real project meets a case it does not
carry and has no way to extend it. What an entry states is what happened, in the words of the run
that hit it: what was being attempted, what the kit answered, and which item it happened under. The
lead triages into `FR`/`BUG` at the other end, where the vocabulary belongs.

WHAT NOTHING HERE ENFORCES, said plainly because the FR says it too: no hook can make a session CALL
this. It is a duty carried by the role texts, the same class as FR-0052 -- so what this module
guarantees is that a gap which IS reported survives, never that every gap is reported.
"""
from __future__ import annotations

import hashlib
import json
import os
import time

from .state import ProjectState, StateError

COMMAND = "report-gap"
LOG_DIR = ".audit"
LOG_NAME = "kit_gaps.jsonl"
# The fields an entry carries, and the two that are not optional. `tried` and `refused` are what
# make an entry triageable at the other end: without the first the lead does not know what the
# project wanted, without the second it does not know which mechanism said no. `item` and `title`
# are convenience for a human reading a list, and `title` is derived from `tried` when it is absent
# rather than demanded twice.
REQUIRED = ("tried", "refused")
OPTIONAL = ("title", "item")
# Per-field bound. A refusal message from this kit's own gates runs to a few hundred characters and
# the longest shipped one is well under this; a pasted transcript is not an entry and is cut with a
# marker rather than silently truncated.
MAX_FIELD = 2000
# The bound on the whole log. Past it the command REFUSES rather than appending, because a log that
# silently drops its newest entries is worse than one that says it is full -- and the way out (the
# lead harvesting and the project pruning through a kit update) is a real one.
MAX_LOG_BYTES = 512 * 1024


def log_path(state: ProjectState) -> str:
    return os.path.join(state.root, LOG_DIR, LOG_NAME)


def _cut(value) -> str:
    text = " ".join(str(value if value is not None else "").split())
    if len(text) <= MAX_FIELD:
        return text
    return text[:MAX_FIELD] + " ...[cut at %d characters]" % MAX_FIELD


def entry_id(fields: dict) -> str:
    """The entry's identity, derived from its CONTENT and not from a counter or a clock.

    TWO THINGS DEPEND ON THIS BEING CONTENT-ADDRESSED. `record` is idempotent, so a role that runs
    the command twice for one wall does not put the same gap on the lead's list twice; and the
    harvest can mark an entry harvested from OUTSIDE the project (`tools/harvest_kit_gaps.py` keys
    its own record by project + this id), which is what lets the lead track what it has already
    triaged without ever writing into the foreign store.

    The CLOCK is deliberately not in it: the same wall hit again next week is the same gap, and a
    second entry for it is noise the lead pays for.
    """
    material = "\x1f".join(_cut(fields.get(name)) for name in sorted(REQUIRED + OPTIONAL))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def entries(root: str) -> list:
    """Every entry the log at `root` holds, oldest first. A line that will not parse is skipped.

    Takes a ROOT and not a `ProjectState`, because the harvest reads FOREIGN projects: a lead
    pointing this at a project on another branch of the disk must not have to construct that
    project's state object, and constructing one would validate a store this reader has no business
    judging.
    """
    found = []
    try:
        with open(os.path.join(root, LOG_DIR, LOG_NAME), encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    parsed = json.loads(line)
                except ValueError:
                    continue
                if isinstance(parsed, dict) and parsed.get("id"):
                    found.append(parsed)
    except OSError:
        return []
    return found


def _kit_version(state: ProjectState) -> str:
    """What the project THINKS it is installed at, read the one way the kernel already reads it.

    `report.installed_identity` and not a second reader of `.claude/kit_version`: the lead's whole
    question at the other end is "which kit release did this happen on", and two readers of that
    file is how the answer starts differing between the briefing and the log. Imported here rather
    than at module scope because `report` imports broadly and this module is also read by a tool
    outside any project.
    """
    try:
        from . import report
        return str(report.installed_identity(state).get("kit_version") or "unknown")
    except Exception:                                   # noqa: BLE001 -- an unknown version is data
        return "unknown"


def record(state: ProjectState, tried: str, refused: str, title: str = "",
           item: str = "") -> dict:
    """Append one gap to this project's log. Idempotent on the entry's content.

    Returns the entry, with `recorded` False when an entry with the same id was already there --
    the caller prints that rather than pretending to have written something, so a role does not
    report a second booking of the same wall.
    """
    fields = {"tried": _cut(tried), "refused": _cut(refused),
              "title": _cut(title) or _cut(tried)[:120], "item": _cut(item)}
    for name in REQUIRED:
        if not fields[name]:
            raise StateError(
                "a kit gap needs `%s`: an entry without it cannot be triaged at the other end -- "
                "the lead would know a wall was hit and not what the project wanted (`tried`) or "
                "which mechanism said no (`refused`). Remedy: run `%s` again with both."
                % (name, COMMAND))
    fields["id"] = entry_id(fields)
    with state.lock:
        already = [one for one in entries(state.root) if one.get("id") == fields["id"]]
        if already:
            result = dict(already[0])
            result["recorded"] = False
            return result
        path = log_path(state)
        try:
            if os.path.exists(path) and os.path.getsize(path) >= MAX_LOG_BYTES:
                raise StateError(
                    "%s has reached its %d byte bound, so nothing was appended -- a log that "
                    "silently dropped its newest entries would be worse than one that says it is "
                    "full. Remedy: this is itself a gap to report to the user; the harness lead "
                    "harvests the log and a kit update is what prunes it."
                    % (os.path.join(LOG_DIR, LOG_NAME), MAX_LOG_BYTES))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            written = dict(fields)
            written["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            written["kit_version"] = _kit_version(state)
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(written, ensure_ascii=False, sort_keys=True) + "\n")
        except OSError as exc:
            raise StateError(
                "the kit-gap log could not be written (%s), so this gap is recorded NOWHERE -- say "
                "it to the user in the same turn. Remedy: report the write failure with the path "
                "%s." % (exc, log_path(state))) from None
    result = dict(written)
    result["recorded"] = True
    return result

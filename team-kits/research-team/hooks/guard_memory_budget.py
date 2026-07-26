#!/usr/bin/env python3
"""
Memory-budget gate — spec II.5, the half the kernel cannot see.

The kernel already enforces the budgets it OWNS: the 4 KB result envelope and the 25 KB session
brief (`kernel/schemas/*.yaml` `max_serialized_bytes`) and the 200-line / 12 KB active item (the
state validator). Agent memory is different — it is written with ordinary Edit/Write calls, so
nothing would notice it growing until a session start had already paid for it. Measured before
this existed: one project's `.claude/agent-memory/` held 159 files and 0.96 MiB, and a single
MEMORY.md had grown to 17.7 KB across 102 entries, mostly one-way trivia.

BUDGETS is a matcher TABLE, because spec II.5 asks for one ("Triggertabelle als
Matcher-Konfiguration, nicht Verfassungsprosa") and because the numbers then live where they are
enforced, enumerable by a test rather than re-derived from control flow.

SHRINKING IS ALWAYS ALLOWED. A budget that only compares against the limit refuses every
intermediate step of the cleanup its own message asks for — a 102-line index going to 101 was
blocked, so the only legal move was one perfect Write. So each axis is judged on its own:
`result <= max(limit, current)`. Per axis, deliberately — "no worse on BOTH axes" refused the
canonical repair for a one-huge-line topic, because wrapping it fixes the byte axis and
necessarily grows the line count. The cost is that a file over its LINE budget may grow in bytes
up to its entry value: bounded, not a ratchet, and the alternative blocks real cleanups.

The content rule — no project ids in memory (II.5 "Projektstatus/Tasks/Entscheidungen/
Sessionfortschritt sind in Agent-Memory verboten", parity row 36) — is a HEURISTIC, and its error
direction is chosen rather than accidental. It matches an id anywhere and then exempts three
shapes only: a URL, an ADJACENT foreignness marker (`upstream PR-1234`, `jira ticket BUG-0007`),
and a CLOSED inline code span. Everything looser was tried and failed in one direction or the
other. Two residues, both deliberate:

  * OVER-blocks a foreign identifier that collides with one of our prefixes and carries no marker
    — "a DEC-2100 controller" reads as a decision id, and so does "invoices are named INV-2024 and
    up". The remedy is to rephrase or to put it in backticks, the message says so, and for a
    memory-hygiene rule refusing too much costs a sentence while letting too much through costs a
    stale fact the next session believes.
  * UNDER-blocks status PROSE ("the refactor is 80% done, next is the login form"), which no
    pattern can catch. So the constitution keeps the prose rule, and the II.11/3 shrink step must
    NOT cut it on the strength of this gate.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import _kernel
except BaseException as exc:  # noqa: BLE001 — a hook that cannot load must not mean "allow"
    sys.stderr.write("[team-kit hook] refused: could not load hook helpers (%r). Remedy: run "
                     "`harness doctor`; a partial checkout or half-finished kit update is the "
                     "usual cause.\n" % (exc,))
    sys.exit(2)

import bisect  # noqa: E402
import glob  # noqa: E402
import re  # noqa: E402

import _compat  # noqa: E402

HOOK = "guard_memory_budget"
# NotebookEdit was deliberately ABSENT, on the grounds that a notebook is not a craft topic and
# would trip the topic COUNT while its content was never modelled. It is back, because the
# reason did not survive contact with the rule that put it there: a guard reading
# `_compat.file_paths()` is asking about a FILE BEING WRITTEN, and that helper resolves
# `notebook_path` like any other. The half-rule is real and unchanged -- `_resulting_text`
# returns None for a notebook, so size and IDs stay unmodelled -- but a `.ipynb` under
# `agent-memory/` is a memory file whether or not this hook can read it, and the count is the
# half that works. Modelling notebook content is phase 3.
FILE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
MEMORY_DIR = "agent-memory"
# ONE definition. Promoting `.markdown`/`.mdx` to craft topics in the BUDGETS table while
# `_check_count` still globbed `**/*.md` silently switched the 20-topic cap off: 20 `.markdown`
# topics counted as zero, so the 21st was waved through. Same for the index rows, which stayed
# exact and let `MEMORY.markdown` fall through to the topic budget (100 lines instead of 40).
# A family defined in one place and used in three cannot drift apart again.
MARKDOWN_SUFFIXES = (".md", ".markdown", ".mdx")
INDEX_STEMS = ("memory",)

# The trigger table (spec II.5). Selection is by PATH COMPONENT plus basename, never by glob
# depth: an earlier cut used fnmatch patterns, and because fnmatch has no `**` they demanded a role
# directory AND an `.md` suffix -- so `agent-memory/notes.md`, a repo-root `agent-memory/` tree and
# every `notes.txt` beside the topics went unchecked. II.5's trigger is `agent-memory/**`, and the
# bloat it was measured against (159 files / 0.96 MiB) is a FILE problem, not a markdown problem.
BUDGETS = (
    # The index carries a BYTE ceiling as well as a line ceiling. II.5 names only "Index <=40
    # Zeilen", but 40 lines of 10 000 characters is a 400 KB file that loads at EVERY spawn --
    # lines alone measure the wrong thing for the one file whose cost is paid most often. 8 KB is
    # 200 bytes per pointer line, which is a generous pointer.
    {"id": "memory-index", "in_memory_dir": True, "stems": INDEX_STEMS,
     "suffixes": MARKDOWN_SUFFIXES,
     "label": "memory INDEX", "max_lines": 40, "max_bytes": 8 * 1024, "forbid_ids": True},
    {"id": "craft-topic", "in_memory_dir": True, "suffixes": MARKDOWN_SUFFIXES,
     "label": "craft topic", "max_lines": 100, "max_bytes": 8 * 1024,
     "forbid_ids": True, "max_per_role": 20},
    # anything else living in agent-memory is not a craft artifact, but it still costs context if
    # it grows: bytes only, no id rule (a pasted fixture may legitimately contain ids).
    {"id": "memory-other", "in_memory_dir": True,
     "label": "memory file", "max_bytes": 8 * 1024},
    # a repo-root MEMORY.md is the human-facing index: budgeted, ids allowed.
    {"id": "root-index", "at_root": True, "stems": INDEX_STEMS, "suffixes": MARKDOWN_SUFFIXES,
     "label": "memory INDEX", "max_lines": 40, "max_bytes": 8 * 1024},
)

# Item ids are project state (spec II.2 `<TYP>-nnnn`, plus the V1 `PRD-` kept by `legacy_ids`).
_ID = r"(?:PR|PRD|RQ|FR|CR|BUG|SR|TSK|PROC|INV|APR|HYP|EXP|DEC|EVD|ARC|WFR|DSN)-\d{4,}"
# IGNORECASE: `tsk-0042` is the same reference typed in a hurry, and the prefixes are specific
# enough that lowercase costs no false positives.
_ITEM_ID_RX = re.compile(r"\b(" + _ID + r")\b", re.ASCII | re.IGNORECASE)
# ...minus the shapes that are NOT our items. Restricting the match to a "referencing position"
# was tried first and under-reached badly: "When TSK-0042 failed, retry with a longer timeout" is
# exactly the leak this rule exists for, and it sits mid-sentence. So the match stays broad and
# the EXEMPTIONS carry the precision -- a URL, an adjacent foreignness marker, and a closed code
# span (which is also how you write the rule itself down without tripping it).
# ADJACENT and specific. A first cut allowed any of `like|wie|named|format|ticket|their|model`
# within 40 characters, which exempted the rule's own canonical leak ("A failure like TSK-0042
# needs a longer timeout") and pure status ("ticket TSK-0042 is still open") -- while relieving
# nothing, because the hardware words only ever precede in the sentences that motivated them.
#
# The markers are also SEPARATE FROM the code-span rule below. Folding "a backtick" in here as one
# more prefix alternative re-opened the whole rule: `finditer` starts a match at the CLOSING
# backtick too, and an unanchored `[^`\n]*` then runs to the last id on the line -- so
# "Use `--retry 3`; the TSK-0042 outage showed 1 is not enough." passed. Craft topics are exactly
# the documents full of inline code, so that is not a corner case, it is most of them.
_FOREIGN_RX = re.compile(
    # BOUNDED. `\S*` backtracks per start position, so one whitespace-free run of concatenated
    # links was quadratic: 42 KB took 5.1s and 200 KB exceeded the host's hook timeout entirely.
    # A killed PreToolUse hook is a non-blocking error, so the write then proceeds UNCHECKED --
    # fail-closed degrading to fail-open, and `fail_closed()` cannot catch a host kill.
    #
    # 1000, not 300: at 300 a realistic 363-character Azure DevOps work-item URL with query
    # parameters was NOT exempt, and signed S3/SAS links, Grafana permalinks and JQL URLs are
    # routinely longer. Measured on the pathological 200 KB single-run input, the URL branch costs
    # 0.43s at 300, 1.06s at 1000 and 2.42s at 2000 -- 1000 covers real URLs and keeps even the
    # contrived worst case near a second.
    r"(?:https?://\S{0,1000}"
    # strong markers: these words do not appear before one of OUR ids in ordinary prose
    r"|\b(?:upstream|vendor|third-party|github|gitlab|jira)[ \t]+"
    r"(?:pr|mr|issue|ticket|bug)?[ \t]*"
    # weak marker: "external" IS ordinary English ("the external SR-0003 service request is ours"),
    # so it only exempts when a foreignness noun follows it
    r"|\b(?:external|foreign)[ \t]+(?:pr|mr|issue|ticket|bug|repo|system)[ \t]+"
    r")" + _ID,
    re.ASCII | re.IGNORECASE)
# A CLOSED inline code span. Both delimiters are required and the id must sit between them, so an
# id quoted as a string ("never write `TSK-0001` into memory") reads as documentation of the rule
# rather than a reference. Two measured imprecisions, both left as they are:
#   * a DOUBLE-backtick span (CommonMark's way to quote text containing a backtick) is NOT exempt,
#     so ``TSK-0042`` blocks. Over-blocking, and the remedy is one character.
#   * pairing is positional, so a stray backtick earlier on the line can pair with the opener of a
#     later span and exempt an id between them. CommonMark pairs the same way, so the rendered
#     file shows that region as code too -- and it now takes two backticks straddling the id
#     instead of one anywhere on the line.
# The exemption is also unconditional on span CONTENT: any text between two backticks is exempt,
# including a full status sentence. This is a hygiene heuristic, not an adversarial control.
_CODE_SPAN_RX = re.compile(r"`[^`\n]*`")


def _budget_for(rel):
    lowered = rel.lower()
    parts = lowered.split("/")
    in_memory = MEMORY_DIR in parts
    name = parts[-1]
    stem = name.rsplit(".", 1)[0] if "." in name else name
    for budget in BUDGETS:
        if budget.get("in_memory_dir") and not in_memory:
            continue
        if budget.get("at_root") and len(parts) != 1:
            continue
        if budget.get("stems") and stem not in budget["stems"]:
            continue
        if budget.get("suffixes") and not name.endswith(budget["suffixes"]):
            continue
        if not budget.get("in_memory_dir") and not budget.get("at_root"):
            continue
        return budget
    return None


def _read(path):
    """The file as it is now, or None when it cannot be measured.

    UNIVERSAL newlines, deliberately: an `old_string` arrives with LF, so reading a CRLF file
    verbatim made every Edit reconstruction fail to match and silently measure the file unchanged
    -- which let a growing edit through. The cost is that the byte count is CRLF-blind (at most
    one byte per line, ~1% of a legal topic, and the LINE budget catches that shape anyway); a
    wrong measurement is better than a wrong decision.

    A decode failure is NOT an error here: a memory file with one cp1252 byte would otherwise make
    every Edit to it exit 2 with an internal-error diagnosis and a remedy pointing at `harness
    doctor`, which would find nothing -- and the file could then never be repaired with Edit.
    """
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except (OSError, UnicodeDecodeError):
        return None


def _resulting_text(data, path):
    """What the file will CONTAIN after this call — budgets are about the result, not the delta.

    Returns None when the shape is not modelled, and the caller then lets it pass: this is a
    budget gate, and refusing an edit we do not model would block legitimate work for no gain.
    """
    tool = data.get("tool_name")
    tool_input = data.get("tool_input") or {}
    if data.get("_file_operations"):
        # a Codex apply_patch: `_compat.load` normalises the TOOL NAME and the paths but leaves
        # the body in tool_input.command, so there is no content to measure. Reported rather than
        # silently read as an empty file, which would have made every budget pass on Codex.
        _kernel.record_note(HOOK, "apply_patch payload for %s: content not modelled, budget not "
                                  "measured on this provider" % path)
        return None
    if tool == "Write":
        return str(tool_input.get("content") or "")
    text = _read(path)
    if text is None:
        return None
    edits = tool_input.get("edits")
    if tool == "MultiEdit" and isinstance(edits, list):
        for edit in edits:
            if not isinstance(edit, dict):
                return None
            text = _apply(text, edit)
            if text is None:
                return None
        return text
    if tool == "Edit":
        return _apply(text, tool_input)
    return None


def _apply(text, edit):
    old = str(edit.get("old_string") or "")
    if not old:
        return None  # unmodelled rather than "no change" -- see the docstring
    new = str(edit.get("new_string") or "")
    return text.replace(old, new) if edit.get("replace_all") else text.replace(old, new, 1)


def _measure(text):
    lines = text.count("\n") + (0 if text.endswith("\n") or not text else 1)
    return lines, len(text.encode("utf-8"))


def _role_base(rel, root):
    """The `<...>/agent-memory/<role>` directory this path belongs to, or None."""
    parts = rel.split("/")
    for index, part in enumerate(parts):
        if part.lower() == MEMORY_DIR and index + 1 < len(parts):
            return os.path.join(root, *parts[:index + 2]), parts[index + 1]
    return None, None


def _check_size(rel, budget, text, current):
    lines, size = _measure(text)
    was_lines, was_size = _measure(current) if current is not None else (None, None)
    # PER AXIS: "no worse than the limit OR the status quo", judged separately. Demanding
    # improvement on BOTH axes refused the canonical repair for a one-huge-line topic -- wrapping
    # it fixes the violated byte axis while the line count necessarily grows.
    over_lines = "max_lines" in budget and lines > budget["max_lines"] and not (
        was_lines is not None and lines <= was_lines)
    over_bytes = "max_bytes" in budget and size > budget["max_bytes"] and not (
        was_size is not None and size <= was_size)
    if not (over_lines or over_bytes):
        return
    _kernel.block(
        HOOK,
        "'%s' would be %d lines / %d bytes; the %s budget is %s (spec II.5). Shrinking an "
        "over-budget file is always allowed — this call would not shrink it."
        % (rel, lines, size, budget["label"],
           " / ".join(filter(None, [
               "%d lines" % budget["max_lines"] if "max_lines" in budget else "",
               "%d bytes" % budget["max_bytes"] if "max_bytes" in budget else ""]))),
        remedy="split it, or cut what is no longer craft — a one-off fact belongs in a test, a "
               "code comment or nowhere. An index is a pointer list: move detail into a topic.")


def _exempt_intervals(text):
    """The exempt spans, MERGED and sorted — so containment is a bisect, not a scan.

    Testing every id against every span is O(ids x spans), and both grow with the file: a memory
    file of "see `x` and TSK-0001" lines took 4.6s at 168 KB and 9.2s end-to-end at 210 KB.
    That matters because the shrink allowance deliberately removes the size bound -- the one input
    class with no ceiling is the large cleanup Write, which is exactly the operation this gate was
    built to encourage.
    """
    spans = sorted([(m.start(), m.end()) for m in _FOREIGN_RX.finditer(text)]
                   + [(m.start(), m.end()) for m in _CODE_SPAN_RX.finditer(text)])
    merged = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [start for start, _ in merged], merged


def _check_ids(rel, budget, text):
    if not budget.get("forbid_ids"):
        return
    # by POSITION, not by string: the same id may appear once exempt (in a URL) and once not
    starts, merged = _exempt_intervals(text)
    found = set()
    for match in _ITEM_ID_RX.finditer(text):
        index = bisect.bisect_right(starts, match.start(1)) - 1
        if index >= 0 and match.end(1) <= merged[index][1]:
            continue
        found.add(match.group(1))
    found = sorted(found)
    if found:
        _kernel.block(
            HOOK,
            "'%s' references project items (%s). Agent memory holds CRAFT — how this role works — "
            "never project status, tasks, decisions or session progress (spec II.5). A note "
            "pinned to an item goes stale the moment the item moves, and the next session reads "
            "it as true." % (rel, ", ".join(found[:5])),
            remedy="put the fact on the item itself (or in evidence/), and keep in memory only "
                   "the generalisable lesson, with no id in it.")


def _check_count(path, rel, budget, root):
    if "max_per_role" not in budget or os.path.exists(path):
        return  # only a NEW topic can push the count over
    base, role = _role_base(rel, root)
    if not base:
        return
    topics = []
    for suffix in MARKDOWN_SUFFIXES:
        for found in glob.glob(os.path.join(base, "**", "*" + suffix), recursive=True):
            matched = _budget_for(os.path.relpath(found, root).replace("\\", "/").lower())
            if matched is not None and matched["id"] == "craft-topic":
                topics.append(found)
    if len(topics) >= budget["max_per_role"]:
        _kernel.block(
            HOOK,
            "%s already has %d craft topics; the budget is %d (spec II.5). Adding another is how "
            "a memory becomes an archive nobody reads."
            % (role, len(topics), budget["max_per_role"]),
            remedy="retire or merge a topic first — the role's memory directory lists them.")


def main():
    data = _kernel.payload(HOOK)
    if str(data.get("hook_event_name") or "PreToolUse") != "PreToolUse":
        sys.exit(0)
    if data.get("tool_name") not in FILE_TOOLS:
        sys.exit(0)
    root = _kernel.find_repo_root(data.get("cwd"))
    for path in _compat.file_paths(data):
        try:
            rel = os.path.relpath(os.path.abspath(path), root).replace("\\", "/")
        except (OSError, ValueError):
            continue  # another drive or a UNC path: by definition not this repo's agent memory
        if rel.startswith("../"):
            continue
        budget = _budget_for(rel)
        if budget is None:
            continue
        _check_count(path, rel, budget, root)
        text = _resulting_text(data, path)
        if text is None:
            continue
        _check_size(rel, budget, text, _read(path))
        _check_ids(rel, budget, text)
    sys.exit(0)


if __name__ == "__main__":
    _kernel.run_gate(HOOK, main)

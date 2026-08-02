#!/usr/bin/env python3
"""
PreToolUse(Write) guard — enforces the single-source-of-truth rule.

Blocks the creation of ad-hoc status/summary/report/result files that the agents kept inventing
instead of recording the finding as a typed item. Reads the Claude Code hook JSON from stdin; exit
code 2 + a stderr message blocks the tool call and tells the model why. Any uncertainty -> exit 0
(never block legitimate work).

WHERE THE CONTENT GOES INSTEAD, in V2 (spec II.2): not into a monolith YAML any more — those are
gone — but into a typed item the STATE KERNEL writes. That changes the advice this guard gives,
not what it blocks: a review/test/acceptance run becomes an Evidence item, a durable choice a
Decision item, a defect a BUG, a scope change a CR, and work still in flight belongs in the
task's own `project_memory/staging/<task-id>/`.
"""
import sys
import os
import re
import fnmatch

# Filename patterns that are always ad-hoc dumps (seen in real runs).
DENY_NAME = [
    "*_summary.md", "*_summary.txt", "*_result.yaml", "*_result.yml", "*_result.json",
    "*_report.md", "*_report.txt", "backend_result_*", "frontend_result_*",
    "delegation_*", "implementation_summary.*", "*_release_summary.md",
    "*_discovery_report.md",
]

ALLOWED_ROOT_DOCS = {
    "readme.md", "claude.md", "contributing.md", "changelog.md", "license", "license.md",
    "code_of_conduct.md", "security.md",
}

# WHERE THE NAME RULE ABOVE DOES NOT APPLY. `DENY_NAME` targets a file an agent INVENTS to hold a
# finding instead of recording a typed item — the remedy it prints is "capture the item". A
# DOCUMENT TRAY is the opposite kind of directory: what lands there arrives from OUTSIDE the
# project (a scanned invoice) or is HANDED to a human (a draft the user sends), so its name is not
# the agent's invention and is no substitute for an item. It closed a measured false alarm: an
# office `outbox/bookkeeper/2026-Q2_report.md` was refused with the advice to book an Evidence
# item instead.
#
# WHICH DIRECTORIES THOSE ARE IS NOT DECIDED HERE, and the first cut deciding it here is what made
# this a defect of its own. This file is byte-identical across all three kits, so a tuple of names
# in it exempted `archive/`, `outbox/` and `inbox/` in kits that ship no tray — and in those kits
# the directory comes into existence through the very `Write` that drops the file in it. Measured
# 2026-08-01 in a dev project, real hook processes, LEAD write, against every hook the dev
# settings.json starts on `Write`: `archive/implementation_summary.md`,
# `outbox/backend_result_x.md`, `inbox/delegation_plan.md` and
# `archive/notes/frontend_result_2.md` were ALLOWED by all of them; identical in research; all
# four rc 2 before the exemption existed.
#
# So the answer comes from the INSTALLED KIT, which SHIPS its tray list as
# `.claude/hooks/document_trays.txt` — inside the hook bundle, beside this guard. That location is
# the point and not a detail: the list is a BEHAVIOUR SOURCE, so whoever can write it decides
# where an integrity rule stands down. Measured 2026-08-01 with the record one level higher, at
# `.claude/document_trays.txt`: `printf 'src' > $(echo .cl*)/document_trays.txt` passed every
# registered shell gate, this guard then allowed `docs/implementation_summary.md`, and
# `gate_dispatch` reported no bundle refusal — the file sat outside `hashing.BUNDLE_SUBTREES`.
# Inside `hooks/` the same forgery moves `hook_bundle_hash`, so the trust gate refuses the next
# spawn. `guard_harness_selfmod` blocks the Edit/Write route either way (`hooks/` prefix).
#
# NO FILE, AN EMPTY ONE OR AN UNREADABLE ONE MEANS NO EXEMPTION — the fail-closed direction, and
# where an installation from before this record lands.
#
# Rules 2 and 3 below still apply inside a tray: an item's id in a filename is still an item's
# content in the wrong place.
TRAYS_FILE = "document_trays.txt"
# What a NAME in that record may be, repeated from `kernel.trays.is_tray_name` for the reason
# every literal in this file is repeated: a guard that cannot import must not stop guarding.
# `test_the_two_readers_of_a_tray_name_agree` pins the two over a battery, so the copy cannot
# drift into a second opinion — and it drifted once already, in exactly the direction that matters
# (the reader dropped only names with a separator, so a record saying `.claude` exempted the
# enforcement layer and one saying `project_memory` exempted the state directory).
STATE_DIRNAME = "project_memory"
# WHAT THIS READER WILL SPEND. It runs on EVERY `Write`, so an unbounded read here is the shape
# `guard_guidelines` carries two caps against. Measured 2026-08-01 on this reader: 0 MB 0.45 s,
# 15 MB 1.21 s, 63 MB 3.11 s — the 60 s at which a host kills a PreToolUse hook is ~1.2 GB away,
# and a killed hook is an ALLOW. The cap is here anyway because the asymmetry with the guard next
# door is not worth defending, and because this file is written by a scaffold rather than by a
# project: a record past it is not a record this harness produced. Past the cap the answer is the
# same as for no record at all, which is NO exemption.
TRAYS_MAX_BYTES = 64_000


def is_tray_name(name):
    """Can this string name a document tray? — `kernel.trays.is_tray_name`, restated."""
    text = str(name or "").strip()
    if not text or text.startswith("."):
        return False
    if "/" in text or "\\" in text:
        return False
    return text.lower() != STATE_DIRNAME


def document_trays(root):
    """The tray names THIS project's installed kit ships — empty when there is no record.

    Read as data, never imported: this guard must keep guarding with no kernel around it, so it
    reads the file the kit shipped rather than the module that wrote it.
    """
    path = os.path.join(root, ".claude", "hooks", TRAYS_FILE)
    try:
        if os.path.getsize(path) > TRAYS_MAX_BYTES:
            return frozenset()
        with open(path, encoding="utf-8-sig") as handle:
            names = [line.strip().lower() for line in handle]
    except OSError:
        return frozenset()
    return frozenset(name for name in names if is_tray_name(name))

# The id prefixes of the typed items (`kernel/backlog_types.ACTIVE_DIRS`). Kept as a literal
# because this guard runs on EVERY Write and decides on the filename alone, so it must not depend
# on a kernel that may be absent, half-installed or unreadable: a guard that cannot load must not
# stop guarding. `import kernel.backlog_types` is stdlib-only again as of 2026-07-28 (its two
# derived maps are computed on first access), so PyYAML is no longer the reason — the resilience
# is. It is a cache with a proof, not a second list — `test_no_adhoc_covers_every_item
# _type` asserts it equals ACTIVE_DIRS, so a new item type cannot silently escape the rule.
ITEM_TYPES = ("apr", "arc", "bug", "cr", "dec", "dsn", "evd", "exp", "fr", "hyp", "inv",
              "pr", "proc", "rq", "sr", "tsk", "wfr")
# V1 ids that migrated projects still carry (spec II.10 keeps them in `legacy_ids`), so a
# `PRD-0002_status.md` written from an old habit is still caught. Also proven, as far as it can
# be: the same test asserts every type in the kernel's V1 migration table is a prefix known here.
LEGACY_ITEM_TYPES = ("adr", "mdr", "pa", "prd")
# The rule is "named after an ITEM ID", so it matches the id shape the kernel actually mints —
# `<TYPE>-<4+ digits>` (`kernel/backlog_types._ID_RE`). Matching a single digit made the guard
# swallow ordinary notes whose name merely starts with two letters (`bug-42.md`, `fr-1.md`),
# against this file's own "never block legitimate work". A name that IS a valid item id stays
# blocked even when it meant something else — that collision is precisely what the rule is for.
ITEM_FILENAME_RE = re.compile(
    r"^(?:%s)-\d{4,}" % "|".join(sorted(ITEM_TYPES + LEGACY_ITEM_TYPES, key=len, reverse=True)))


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _root import find_repo_root
import _audit
import _compat


def block(rel, why):
    _audit.record("guard_no_adhoc", rel)
    _compat.stop(
        "[team-kit guard] Blocked creating '%s': %s.\n"
        "The single source of truth is the typed state, and the kernel is its only writer, "
        "reached through `python scripts/harness.py <command>` from the project root: a review, "
        "test or acceptance run is an Evidence item (kind: review | test | acceptance) and "
        "`python scripts/harness.py evidence` is what records it. A durable choice is a Decision "
        "item, a defect a BUG, a scope change a CR — `python scripts/harness.py capture <TYPE>` "
        "creates each of those from a JSON object on stdin. An architecture statement is an ARC "
        "item, which `capture` deliberately refuses: an ARC is FROZEN through the promotion path "
        "(II.6a) and nothing on that surface freezes one, so for that one name the item AND the "
        "missing command in your report. Work still in flight goes into your task's "
        "project_memory/staging/<task-id>/, product code into src/ and tests/. A recurring REPORT "
        "is a third case and neither of the two above: where a shipped "
        "script renders one, run that script — a hand-written copy of a "
        "generated report is a second, drifting truth beside the data it was rendered from. "
        "Inventing a file for any of it is what this guard refuses.\n" % (rel, why),
        "PreToolUse")


def check(path, cwd, trays=frozenset()):
    try:
        rel = os.path.relpath(path, cwd)
    except Exception:
        rel = path
    # A LEADING `./` IS A PREFIX, NOT A CHARACTER SET, and here that distinction decides a
    # REFUSAL. `lstrip("./")` eats every leading `.` and `/`, so `../archive/x_report.md` — a file
    # in the PARENT directory's archive, outside this repo entirely — arrived as
    # `archive/x_report.md` and fell straight into the tray exemption. The same slip has cost
    # `guard_pm_scope` (`.claude` read as `claude`) and `gate_write_scope` (`.env` read as `env`)
    # a round each, which is why the fix is the prefix rather than another special case.
    rel = rel.replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    outside = rel.startswith("../")
    name = os.path.basename(rel).lower()
    # ...and a file outside the repo is not AT its root either, so rule 3 does not speak for it.
    # The name rules below still do: they judge the filename and nothing about where it sits.
    is_root = not outside and "/" not in rel
    segments = [s for s in rel.split("/") if s]
    in_tray = (not outside) and len(segments) > 1 and segments[0].lower() in trays

    # 1) explicit ad-hoc dump patterns, anywhere OUTSIDE a document tray (see TRAYS_FILE)
    if not in_tray:
        for pat in DENY_NAME:
            if fnmatch.fnmatch(name, pat):
                block(rel, "matches a forbidden ad-hoc report/summary pattern")

    # 2) item status written as a markdown doc (PR-0002_*.md etc.), anywhere
    if name.endswith(".md") and ITEM_FILENAME_RE.match(name):
        block(rel, "an item's content belongs in the item itself, not in a markdown file beside it")

    # 3) loose markdown at the repo root (except the few conventional ones)
    if is_root and name.endswith(".md") and name not in ALLOWED_ROOT_DOCS:
        block(rel, "no loose docs at the repo root; status belongs in a typed item, prose in docs/")


def main():
    data = _compat.load()
    allowed_roles = {role for role in os.environ.get("TEAM_KIT_AGENT_TYPES", "").split(",")
                     if role}
    if allowed_roles and str(data.get("agent_type") or "") not in allowed_roles:
        sys.exit(0)
    # Claude exposes a dedicated Write event. Codex batches Add/Update/Delete/Move operations into
    # one apply_patch call, so inspect only paths actually created by Add File or Move to.
    paths = (_compat.created_file_paths(data) if data.get("_file_operations")
             else _compat.file_paths(data) if data.get("tool_name") == "Write" else [])
    if not paths:
        sys.exit(0)
    cwd = find_repo_root(data.get("cwd"))
    trays = document_trays(cwd)   # read once: a Codex apply_patch carries many paths
    for path in paths:
        check(path, cwd, trays)
    sys.exit(0)


if __name__ == "__main__":
    main()

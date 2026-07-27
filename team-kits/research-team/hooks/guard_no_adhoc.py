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

# The id prefixes of the typed items (`kernel/backlog_types.ACTIVE_DIRS`). Kept as a literal
# because this guard runs on EVERY Write and decides on the filename alone: importing the kernel
# to learn the type names would pull PyYAML into that path, and a guard that cannot load must not
# stop guarding. It is a cache with a proof, not a second list — `test_no_adhoc_covers_every_item
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
    sys.stderr.write(
        "[team-kit guard] Blocked creating '%s': %s.\n"
        "The single source of truth is the typed state, and the kernel is its only writer "
        "(`harness capture ...`): a review, test or acceptance run is an Evidence item (kind: "
        "review | test | acceptance), a durable choice a Decision item, a defect a BUG, a scope "
        "change a CR, an architecture statement an ARC item. Work still in flight goes into your "
        "task's project_memory/staging/<task-id>/, product code into src/ and tests/. "
        "Capture it as the right item instead of inventing a file.\n" % (rel, why)
    )
    sys.exit(2)


def check(path, cwd):
    try:
        rel = os.path.relpath(path, cwd)
    except Exception:
        rel = path
    rel = rel.replace("\\", "/").lstrip("./")
    name = os.path.basename(rel).lower()
    is_root = "/" not in rel

    # 1) explicit ad-hoc dump patterns, anywhere
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
    for path in paths:
        check(path, cwd)
    sys.exit(0)


if __name__ == "__main__":
    main()

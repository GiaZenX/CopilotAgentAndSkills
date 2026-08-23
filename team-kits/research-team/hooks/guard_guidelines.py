#!/usr/bin/env python3
"""
PreToolUse(Edit|Write|MultiEdit|NotebookEdit) — no production code in an area no invariant governs.

Closes the "code written against empty guidelines" gap deterministically and BEFORE the work
(not just at the merge gate). Lives in the code-writers' frontmatter (it must fire for the
specialist subagents, not the PM). When a specialist writes a code file under src/**/frontend/**/
backend/** (or a root code file), some `INV` item of the project must already GOVERN that file —
otherwise the architect has to state the rule first (constitution §2.7).

WHERE THE RULES LIVE NOW. V1 kept them in one `coding_guidelines.yaml` at the state root and this
guard opened it by name; V2 dissolved that monolith into `INV` items (`invariants/active/`), no kit
ships the old template, and `gate_write_scope` refuses every tool write under the state directory —
so the guard was reading a file that could not exist and could not be created, i.e. it was inert in
every V2 project. The architect SKILL had already been rewritten onto `INV` items; this is the gate
catching up with it.

WHAT MAKES AN `INV` THIS FILE'S BUSINESS is a property of the item, never a list of ids: its
`scope`. An invariant's scope says what it governs, and a write is governed when the scope names
the file's LANGUAGE or the file's AREA — WHICH OF THE TWO a given scope means is decided by the
scope, not tried both ways: see `_governs`, and see it before changing anything here, because
trying both ways is how a path like `go/pkg` came to wave every `.go` in the repo through. A guard
that instead knew a set of `INV-nnnn` ids would be the monolith again with more files.

Uncertainty -> exit 0 (never block legitimate work: no project_memory, unknown language, tests…).
A project that keeps NO invariants at all is the same "cannot determine" as V1's missing file:
the rule binds as policy there, and the constitution says so rather than implying a guard.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _root import find_repo_root
import _audit
import _compat

# Alias TOKENS per extension. A scope satisfies the guard when ANY of its underscore/dash/space
# separated tokens equals one of these aliases — so `python` matches, and so do compound project
# words like `html_vanilla_js` (token "js"). A real run hard-coded its compound key into this map
# because an exact match rejected it; token matching keeps the hook generic.
LANG = {
    ".py": ["python", "py"],
    ".ts": ["typescript", "ts"], ".tsx": ["typescript", "tsx", "ts"],
    ".js": ["javascript", "js", "ecmascript", "node", "typescript", "ts"],
    ".jsx": ["javascript", "js", "jsx", "typescript", "ts"],
    ".mjs": ["javascript", "js", "typescript", "ts"],
    ".go": ["go", "golang"], ".rs": ["rust", "rs"], ".java": ["java"], ".rb": ["ruby", "rb"],
    ".php": ["php"],
    ".cs": ["csharp", "dotnet", "cs"], ".kt": ["kotlin", "kt"], ".swift": ["swift"],
    ".c": ["c"], ".h": ["c", "cpp"], ".cpp": ["cpp", "cxx"], ".cc": ["cpp", "cc"],
    ".hpp": ["cpp", "hpp"], ".ino": ["cpp", "embedded", "arduino", "ino"],
}
CODE_TOP = {"src", "frontend", "backend", "lib", "server", "app", "packages", "cmd", "internal", "api",
            "ui", "web", "firmware", "include", "hardware"}
# The typed home of `INV` items, as `kernel.backlog_types.ACTIVE_DIRS["INV"]` spells it. A guard
# must keep guarding when the kernel cannot load (spec II.7: integrity gates are stdlib-first), so
# this is a literal here for the same reason `guard_no_adhoc` keeps its type list as one — and
# `test_the_hooks_that_name_a_typed_directory_spell_it_as_the_kernel_does` pins the two together.
INVARIANTS_DIR = ("invariants", "active")

# WHAT THIS READER WILL SPEND, and why a BLOCKING hook needs it stated at least as loudly as the
# repo script does. `scripts/kit_checks.py` carried a per-file cap with its reason ("a multi-MB
# config would stall the BLOCKING hook path") while the hooks that actually block carried none —
# the inversion is the defect. Measured on this reader: ~0.23 s per MB of invariant store
# (10 MB 4.80 s, 99 MB 22.84 s, 199 MB 46.82 s), so a store of a few hundred MB is a minute in
# which this guard has decided nothing and the session cannot move: the size of the store it reads
# would be setting the cost of every Write (`_compat.HOOK_DEADLINE_SECONDS`).
#
# TWO CAPS, because one of them does not bound the other: a per-ITEM cap says nothing about ten
# thousand items, and a whole-SCAN cap says nothing about the first file being 200 MB. The values
# are the same three readers over (`kit_checks.load_invariants`,
# `gate_test_coverage._governed_source_areas`), and
# `test_the_two_readers_of_a_governed_source_area_agree` pins them together — they diverged the
# day they were written, the script skipping oversized items and the hook reading them.
# An item past the cap simply does not govern anything, which for THIS guard is the closed
# direction: no invariant governs the file, so the write is refused.
INVARIANT_MAX_BYTES = 2_000_000
INVARIANT_SCAN_MAX_BYTES = 8_000_000


def block(lang, rel):
    _audit.record("guard_guidelines", rel)
    _compat.stop(
        "[team-kit guard] Blocked writing '%s': no INV item of this project governs it — no "
        "invariant names the language (%s) and none names an area containing it.\n"
        "The architect MUST state the rules for %s BEFORE code in it is written "
        "(constitution §2.7), as `INV` items with a `check` reference. Ask the PM to task the "
        "architect, then retry.\n" % (rel, lang, lang),
        "PreToolUse")


def _scopes(root):
    """Every active INV item's `scope`, or None when the project keeps no invariants at all.

    None and [] are deliberately different answers: an absent/empty directory is "this project has
    no invariants regime", which is V1's missing-file case and passes, while a project that DOES
    keep invariants and has none for this file is the case the guard exists for.
    """
    directory = os.path.join(root, "project_memory", *INVARIANTS_DIR)
    if not os.path.isdir(directory):
        return None
    try:
        names = [n for n in sorted(os.listdir(directory)) if n.endswith(".yaml")]
    except OSError:
        return None
    if not names:
        return None
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return None      # no parser -> cannot determine -> never block blind
    scopes = []
    spent = 0
    for name in names:
        path = os.path.join(directory, name)
        try:
            size = os.path.getsize(path)
            if size > INVARIANT_MAX_BYTES:
                continue
            spent += size
            if spent > INVARIANT_SCAN_MAX_BYTES:
                break
            with open(path, encoding="utf-8", errors="ignore") as fh:
                item = yaml.safe_load(fh.read())
        except Exception:
            continue     # an item the state validator will report; not this guard's verdict
        if isinstance(item, dict) and item.get("scope") is not None:
            scopes.append(item["scope"])
    return scopes


def _governs(scope, rel, aliases):
    """Does an invariant with this `scope` apply to the file at `rel`?

    A SCOPE IS READ AS ONE THING, and which one is decided by the scope itself: a scope that
    SPELLS A PATH (it carries a separator) is an AREA and is only ever matched as a prefix of the
    file; a scope without one is a bare NAME and is matched both ways -- as the language it names,
    and as a top-level directory of that name.

    THE FIRST CUT APPLIED BOTH RULES TO EVERY SCOPE, and that disarmed the guard it had just
    brought back to life. The language match tokenises on non-letters, so a PATH scope was also a
    list of words -- and any segment that happens to equal a `LANG` alias made that language
    governed REPO-WIDE. Measured as real hook processes: `services/node-api` waved every `.js`
    through (token "node"), `go/pkg` every `.go`, `lib/c-bindings` every `.c`, `docs/rust-notes`
    every `.rs`. It is a class, not four spellings: every segment of every path scope was a
    language vote. Deciding the READING first is what removes the class -- an area says where, a
    name says what, and no scope says both.

    The bare-name case stays deliberately double: `python` cannot be told apart from a directory
    called `python`, and reading it as both is exactly what V1's `languages: python:` did. The
    over-permissive direction is therefore unchanged rather than new.
    """
    text = str(scope or "").strip()
    if not text:
        return False
    normalised = text.replace("\\", "/")
    segments = [s for s in normalised.lower().split("/") if s and s != "."]
    if "/" not in normalised:
        if {t for t in re.split(r"[^a-z+]+", normalised.lower()) if t} & aliases:
            return True
    target = [s for s in rel.lower().split("/") if s]
    return bool(segments) and len(segments) <= len(target) and target[:len(segments)] == segments


def check(data, path, root):
    if not path:
        return
    langs = LANG.get(os.path.splitext(path)[1].lower())
    if not langs:
        return  # not a tracked code language

    try:
        rel = os.path.relpath(path, root).replace("\\", "/")
    except Exception:
        return
    # a leading `./` is a PREFIX, not a character set -- `lstrip("./")` renamed `.claude` to
    # `claude` and `.github` to `github` in the path this guard REPORTS and matches on
    while rel.startswith("./"):
        rel = rel[2:]
    if rel.startswith("../"):
        return
    segs = [s for s in rel.split("/") if s]
    top = segs[0] if segs else ""
    is_code = top in CODE_TOP or len(segs) == 1
    if not is_code:
        return  # only gate production code areas

    scopes = _scopes(root)
    if scopes is None:
        return  # can't determine -> don't block
    aliases = {a.lower() for a in langs}
    if not any(_governs(scope, rel, aliases) for scope in scopes):
        block(langs[0], rel)


def main():
    data = _compat.load()
    allowed_roles = {role for role in os.environ.get("TEAM_KIT_AGENT_TYPES", "").split(",")
                     if role}
    if allowed_roles and str(data.get("agent_type") or "") not in allowed_roles:
        sys.exit(0)
    if data.get("tool_name") not in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        sys.exit(0)
    root = find_repo_root(data.get("cwd"))
    for path in _compat.file_paths(data):
        check(data, path, root)
    sys.exit(0)


if __name__ == "__main__":
    main()

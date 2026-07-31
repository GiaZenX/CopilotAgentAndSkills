#!/usr/bin/env python3
"""
PreToolUse(Bash|PowerShell) — block merge/push while a source area has NO tests.

The real run shipped a frontend with 0 tests, hidden behind a high global backend
coverage number. This gate enforces the floor deterministically: every source area that
exists must have at least some tests — covered here are python (`src/`), JS/TS frontend
(`frontend/`) and C/C++ firmware (`src/`, `lib/`, `firmware/`). NOTE: other declared
stacks (go/rust/dotnet) get their test enforcement from scripts/quality.py (e.g. `go test`,
`cargo test`), not from this hook. The coverage-% threshold itself stays QA's recorded gate
(an Evidence item and `scripts/quality.py`); this hook only catches the "whole area untested"
failure that a global % can mask.

EXTRA areas come from the project's own `INV` items, never from a config monolith: see
`_governed_source_areas`.

Only fires on `git push`/`git merge`, only when real work exists (a PRD entry). Any
uncertainty -> exit 0 (never block legitimate work).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _compat
from _root import find_repo_root, has_root_item
from _compat import wants_push_or_merge
import _audit

CODE_RE = re.compile(r"\.(py|ts|tsx|js|jsx|vue|svelte)$", re.IGNORECASE)
PY_TEST_RE = re.compile(r"(^test_.*\.py$)|(.*_test\.py$)", re.IGNORECASE)
JS_TEST_RE = re.compile(r"\.(test|spec)\.(t|j)sx?$", re.IGNORECASE)
CPP_CODE_RE = re.compile(r"\.(c|cpp|cc|ino)$", re.IGNORECASE)
CPP_TEST_RE = re.compile(r"(^test_.*\.(c|cpp|cc)$)|(.*_test\.(c|cpp|cc)$)|(^test_main\.cpp$)", re.IGNORECASE)


def block(why):
    # through `_compat.stop`, not a bare stderr write — see the same note in gate_pipeline: it is
    # the one funnel, and the funnel is where an unresolvable git verb gets its own sentence.
    _audit.record("gate_test_coverage", why)
    _compat.stop(
        "[team-kit gate] Blocked merge/push: %s\n"
        "Every source area must be tested on its own (the per-area coverage rule, constitution "
        "§6). Have QA add real tests for that area before merging.\n" % why,
        "PreToolUse")


def has_code(root, rel_dir, name_re=CODE_RE, skip=("node_modules", "dist", "build", "__pycache__")):
    d = os.path.join(root, rel_dir)
    if not os.path.isdir(d):
        return False
    for dp, dn, fn in os.walk(d):
        dn[:] = [x for x in dn if x not in skip]
        for f in fn:
            if name_re.search(f) and not PY_TEST_RE.search(f) and not JS_TEST_RE.search(f):
                return True
    return False


def has_tests(root, dirs, test_re, skip=("node_modules", "dist", "build", "__pycache__")):
    for rel_dir in dirs:
        d = os.path.join(root, rel_dir)
        if not os.path.isdir(d):
            continue
        for dp, dn, fn in os.walk(d):
            dn[:] = [x for x in dn if x not in skip]
            for f in fn:
                if test_re.search(f):
                    return True
    return False


def main():
    # BOUNDED read (spec II.4). A raw `json.load(sys.stdin)` will happily buffer a
    # payload of any size, and an oversized one is the shape that turns a hook into
    # a memory event rather than a decision. `_compat.load` caps it at STDIN_LIMIT
    # and exits 2, because a gate that cannot read its input has not judged it.
    data = _compat.load()
    if data.get("tool_name") not in ("Bash", "PowerShell"):
        sys.exit(0)
    # Detection lives in _compat.wants_push_or_merge (single home): applicability is decided on
    # the git SUBCOMMAND of a `git` word the shell would execute -- so no quoting, escaping, line
    # break or wrapper word spells the verb past this gate, and a verb the shell only builds at
    # run time counts as every verb. A commit MESSAGE about a push stays a message (it once
    # re-triggered a full gate), because it is an argument, not a word git was handed.
    if not wants_push_or_merge(((data.get("tool_input") or {}).get("command") or "")):
        sys.exit(0)

    root = find_repo_root(data.get("cwd"))
    pm = os.path.join(root, "project_memory")
    if not os.path.isdir(pm):
        sys.exit(0)
    # only gate once there is real work
    if not has_root_item(root):
        sys.exit(0)

    # python backend area: src/ with code -> needs tests under tests/ or src/
    if has_code(root, "src", CODE_RE) and not has_tests(root, ("tests", "src"), PY_TEST_RE):
        block("source area 'src/' has code but no tests (no test_*.py / *_test.py).")

    # frontend area: frontend/ with components -> needs *.test.* / *.spec.*
    if has_code(root, "frontend", CODE_RE) and not has_tests(root, ("frontend",), JS_TEST_RE):
        block("source area 'frontend/' has code but no UI/unit tests (no *.test.* / *.spec.*).")

    # firmware / C-C++ area: code under src/ | lib/ | firmware/ -> needs tests (PlatformIO test/ or *_test.cpp)
    if any(has_code(root, d, CPP_CODE_RE) for d in ("src", "lib", "firmware")) \
            and not has_tests(root, ("test", "tests", "src", "lib"), CPP_TEST_RE):
        block("C/C++ firmware code exists but has no tests (no test_*.c[pp] / *_test.c[pp] / PlatformIO test/).")

    # EXTRA areas the project's own INVARIANTS govern — the default trio missed a project whose
    # entire codebase lived under compounder/ (never scanned, coverage false-green for weeks).
    for area in _governed_source_areas(root, pm):
        if area in ("src", "frontend", "lib", "firmware"):
            continue  # already enforced above
        if has_code(root, area, CODE_RE) and not has_tests(root, (area, "tests"), PY_TEST_RE) \
                and not has_tests(root, (area,), JS_TEST_RE):
            block("source area '%s/' has code but no tests, and an INV item of this project "
                  "governs it." % area)

    sys.exit(0)


# The typed home of `INV` items, as `kernel.backlog_types.ACTIVE_DIRS["INV"]` spells it — a
# literal for the reason spec II.7 gives (an integrity gate stays stdlib-first and keeps guarding
# when the kernel cannot load), pinned against the kernel by
# `test_the_hooks_that_name_a_typed_directory_spell_it_as_the_kernel_does`.
INVARIANTS_DIR = ("invariants", "active")

# The same two caps as `guard_guidelines` and `scripts/kit_checks.py`, for the reason spelled out
# at length in the first of those: this reader runs on a BLOCKING PreToolUse hook, the host kills
# such a hook at 60 s, and a killed hook is an ALLOW. Measured ~0.23 s per MB of invariant store.
# Pinned across the readers by `test_the_two_readers_of_a_governed_source_area_agree`.
INVARIANT_MAX_BYTES = 2_000_000
INVARIANT_SCAN_MAX_BYTES = 8_000_000


def _governed_source_areas(root, pm):
    """Top-level source directories this project's INVARIANTS govern.

    V1 read a `coverage_areas:` list out of `testing_guidelines.yaml`, a monolith V2 deleted and no
    kit ships a template for -- so the extra areas were unreachable and this loop ran zero times in
    every V2 project. The V2 source is the invariants themselves, and the property that makes one
    an area is its `scope`: an invariant says what it governs, so a scope whose first path segment
    is a real directory of this repo names a source area the project itself declared. No knob, no
    list of ids -- and it answers the same question `scripts/kit_checks.py` asks for the file
    budget, which is why the two are pinned against one INV fixture
    (`test_the_two_readers_of_a_governed_source_area_agree`).

    Anything unreadable yields nothing: an unparsable item is the state validator's finding, and a
    gate that bricked on one would be a worse outcome than the coverage it would have added.
    """
    directory = os.path.join(pm, *INVARIANTS_DIR)
    if not os.path.isdir(directory):
        return []
    try:
        import yaml  # type: ignore[import-untyped]
        names = [n for n in sorted(os.listdir(directory)) if n.endswith(".yaml")]
    except Exception:
        return []
    out = []
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
            continue
        if not isinstance(item, dict):
            continue
        area = str(item.get("scope") or "").strip().replace("\\", "/").lstrip("./")
        area = area.split("/")[0].strip()
        # dot-only names ('..') would walk OUT of the repo (audit repro) — reject them, and take
        # only a segment that IS a directory here: a scope naming a language or a rule is not an
        # area, and asking the filesystem is what tells the two apart without a vocabulary.
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", area) or set(area) == {"."}:
            continue
        if os.path.isdir(os.path.join(root, area)) and area not in out:
            out.append(area)
    return out


if __name__ == "__main__":
    main()

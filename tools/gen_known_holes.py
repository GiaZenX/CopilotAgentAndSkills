#!/usr/bin/env python3
"""
gen_known_holes.py — the `known_hole` enumeration, as data the KERNEL can read.

WHY THIS FILE EXISTS. `python scripts/harness.py doctor` treats the enumeration as authoritative: a capability that
any shipped `known_hole` test names is forced to `unverified`, whatever the wiring says (see
`kernel/report.capability_matrix`, rule 2). That rule was reading the harness's own test suite —
which does not exist in a scaffolded project, so the rule was off in every environment except the
one the tests run in. `report["known_holes"] == []` then read as an affirmative "no known holes"
rather than "could not look", and one unchanged project got different verdicts depending on where
the kernel package happened to sit.

So the enumeration ships as data inside the kernel package, and travels wherever the kernel is
installed — `~/.claude/team-kits/kernel/` via the installer, `<repo>/.claude/kernel/` via the
scaffold.

PYTEST IS ASKED; NOTHING IS PARSED. The first cut walked `ast` decorator nodes, which was already
better than a text regex — a regex counts `# known_hole("spawn_veto")` in a comment, and `tools/`
is ordinary agent writing territory. But a decorator walk is still an ENUMERATION OF SPELLINGS,
and a review found eight that pytest honours and it missed: a marker on a CLASS, module-level
`pytestmark = ...` (bare and in a list), `pytest.param(marks=...)`, the keyword form
`known_hole(capability="x")` that `tools/conftest.py` itself documents, an aliased decorator, an
f-string argument, a constant. Every miss is silent and in the dangerous direction: the test runs
and asserts an open path, the sidecar does not name it, rule 2 never fires, the capability stays
`verified`.

The list of spellings is not the bug — writing a list was. pytest decides what a marker is, so
pytest is asked, through `--collect-only` and `item.iter_markers`. A spelling nobody has thought
of yet is covered for free, and so is any future pytest gains.

Two further properties, both load-bearing:
  * NO TIMESTAMP. The file is pinned by a test that regenerates and diffs; a generated-at field
    would make every run a diff and train people to ignore it.
  * NOTHING IS WRITTEN ON A FAILED COLLECTION. An unreadable source used to `continue` past, so a
    renamed or half-written test file produced a valid, EMPTY sidecar and a green `--check` — the
    same "could not look ≠ nothing found" error the consumer side exists to correct, one storey up
    in the producer. Collection failure is now fatal and writes nothing.

The digest: `render()` also emits a SHA-256 of the payload into `kernel/known_holes_digest.py`, and
`report._known_hole_capabilities` refuses a sidecar that does not match it. Without that, deleting
the file cost every capability while EMPTYING it (`{"capabilities": {}}`) silenced every hole at no
cost — so the cheapest tamper was the profitable one, which is the incentive this whole change set
exists to invert.

Usage:  python tools/gen_known_holes.py            # write it
        python tools/gen_known_holes.py --check    # exit 1 if it is out of date (CI/test)
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = ("tools/test_hooks_v2.py", "tools/test_hooks.py")
TARGET = os.path.join(ROOT, "team-kits", "kernel", "known_holes.json")
DIGEST_TARGET = os.path.join(ROOT, "team-kits", "kernel", "known_holes_digest.py")

# A pytest plugin, not a parser. `iter_markers` is the same call pytest's own `-m known_hole`
# selection goes through, so anything it selects is seen here — including the seven spellings a
# decorator walk missed.
_PLUGIN = '''import json
import os


def pytest_collection_modifyitems(items):
    holes = {}
    for item in items:
        for marker in item.iter_markers("known_hole"):
            capability = marker.args[0] if marker.args else marker.kwargs.get("capability")
            if not isinstance(capability, str) or not capability:
                raise SystemExit(
                    "known_hole marker on %s names no capability -- the marker's contract "
                    "(tools/conftest.py) is that it names the capability doctor must report "
                    "unverified" % item.nodeid)
            name = getattr(item, "originalname", None) or item.name
            holes.setdefault(capability, set()).add(name)
    with open(os.environ["KNOWN_HOLES_OUT"], "w", encoding="utf-8") as handle:
        json.dump({k: sorted(v) for k, v in holes.items()}, handle)
'''


def collect():
    """{capability: [test names]} — from pytest, which is what decides what a marker is."""
    with tempfile.TemporaryDirectory() as work:
        plugin_dir = os.path.join(work, "plug")
        os.makedirs(plugin_dir)
        with open(os.path.join(plugin_dir, "known_hole_probe.py"), "w", encoding="utf-8") as fh:
            fh.write(_PLUGIN)
        out = os.path.join(work, "holes.json")
        env = dict(os.environ, KNOWN_HOLES_OUT=out)
        env["PYTHONPATH"] = plugin_dir + os.pathsep + env.get("PYTHONPATH", "")
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "known_hole_probe",
             "-p", "no:cacheprovider", *SOURCES],
            cwd=ROOT, env=env, capture_output=True, text=True)
        if proc.returncode != 0 or not os.path.exists(out):
            raise SystemExit(
                "[gen_known_holes] pytest could not collect %s (exit %d). An enumeration that "
                "could not be TAKEN is not an empty enumeration, so nothing was written.\n%s\n%s"
                % (", ".join(SOURCES), proc.returncode, proc.stdout[-2000:], proc.stderr[-2000:]))
        with open(out, encoding="utf-8") as handle:
            holes = json.load(handle)
    return {name: sorted(tests) for name, tests in sorted(holes.items())}


def render(capabilities):
    return json.dumps(
        {"schema": 1,
         "generated_from": list(SOURCES),
         "note": "Generated by tools/gen_known_holes.py from pytest's own marker collection — do "
                 "not hand-edit. `python scripts/harness.py doctor` forces every capability named "
                 "here to "
                 "`unverified` (report.py rule 2), and refuses the file outright if it does not "
                 "match kernel/known_holes_digest.py.",
         "capabilities": capabilities},
        indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def render_digest(payload):
    """The digest module — the reason emptying the sidecar is as expensive as deleting it."""
    return (
        '"""Generated by tools/gen_known_holes.py — do not hand-edit.\n'
        "\n"
        "The SHA-256 of `known_holes.json`, kept in CODE so that editing the data alone cannot\n"
        "change what doctor believes. Deleting the sidecar cost every capability; emptying it\n"
        "used to silence every asserted hole for free, which made the cheapest tamper the\n"
        "profitable one. Now any deviation lands in the same place: `known_holes_source: null`.\n"
        '"""\n'
        "KNOWN_HOLES_SHA256 = %r\n" % hashlib.sha256(payload.encode("utf-8")).hexdigest())


def main():
    capabilities = collect()
    fresh = render(capabilities)
    fresh_digest = render_digest(fresh)
    if "--check" in sys.argv:
        stale = []
        for path, want in ((TARGET, fresh), (DIGEST_TARGET, fresh_digest)):
            try:
                with open(path, encoding="utf-8") as handle:
                    current = handle.read()
            except OSError:
                current = None
            if current != want:
                stale.append(os.path.relpath(path, ROOT).replace(os.sep, "/"))
        if stale:
            sys.stderr.write(
                "[gen_known_holes] out of date: %s — a `known_hole` marker was added, removed or "
                "renamed without regenerating, or the file was hand-edited. Run "
                "`python tools/gen_known_holes.py`.\n" % ", ".join(stale))
            return 1
        print("[gen_known_holes] up to date (%d capabilit%s)"
              % (len(capabilities), "y" if len(capabilities) == 1 else "ies"))
        return 0
    for path, text in ((TARGET, fresh), (DIGEST_TARGET, fresh_digest)):
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        print("[gen_known_holes] wrote %s" % os.path.relpath(path, ROOT).replace(os.sep, "/"))
    for name, tests in capabilities.items():
        print("  %-32s %d test(s)" % (name, len(tests)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

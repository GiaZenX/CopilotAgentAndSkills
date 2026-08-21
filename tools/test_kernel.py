"""Tests for the V2 state-kernel core modules (lock + hashing).

Spec anchors: HARNESS_V2_SPEC.md II.4 (Nebenlaeufigkeit & Locking) and II.2
(Hash-Kanonisierung); II.12 "Neue v2.1-Testfaelle" (lock: second process blocks,
stale lock broken after TTL; hashing: canonical JSON).
"""
import json
import os
import subprocess
import sys
import threading
import time

import pytest

TEAM_KITS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "team-kits")
sys.path.insert(0, TEAM_KITS_DIR)

from kernel.hashing import HASH_SCHEMA_VERSION, canonical_json, subject_manifest_hash  # noqa: E402
from kernel.lock import KernelLock, LockLost, LockTimeout, ext_path  # noqa: E402


# -- lock: exclusivity ---------------------------------------------------------

def test_second_acquire_blocks_until_timeout(tmp_path):
    a = KernelLock(str(tmp_path))
    b = KernelLock(str(tmp_path))
    a.acquire(timeout=1)
    t0 = time.monotonic()
    with pytest.raises(LockTimeout) as exc:
        b.acquire(timeout=0.6, poll=0.05)
    assert time.monotonic() - t0 >= 0.5  # it waited, not failed instantly
    assert ".kernel.lock" in str(exc.value)  # message names the lockfile
    a.release()


def test_release_then_reacquire(tmp_path):
    a = KernelLock(str(tmp_path))
    a.acquire(timeout=1)
    a.release()
    b = KernelLock(str(tmp_path))
    b.acquire(timeout=1)
    b.release()


def test_context_manager(tmp_path):
    with KernelLock(str(tmp_path)) as lock:
        assert lock.held
        assert os.path.exists(os.path.join(str(tmp_path), ".kernel.lock"))
    assert not os.path.exists(os.path.join(str(tmp_path), ".kernel.lock"))


# -- lock: stale-break ---------------------------------------------------------

def test_stale_lock_broken_after_ttl(tmp_path):
    dead = KernelLock(str(tmp_path), ttl=0.3)
    dead.acquire(timeout=1)  # simulate a crashed holder: never released
    waiter = KernelLock(str(tmp_path), ttl=0.3)
    waiter.acquire(timeout=5, poll=0.1)  # must succeed once TTL expired
    assert waiter.held
    waiter.release()
    # the dead holder learns it lost the lock on release
    with pytest.raises(LockLost):
        dead.release()


def test_fresh_lock_never_broken(tmp_path):
    holder = KernelLock(str(tmp_path), ttl=60)
    holder.acquire(timeout=1)
    waiter = KernelLock(str(tmp_path), ttl=60)
    with pytest.raises(LockTimeout):
        waiter.acquire(timeout=0.8, poll=0.05)
    holder.release()  # still cleanly ours


def test_corrupt_lockfile_expires_by_mtime(tmp_path):
    lock_file = tmp_path / ".kernel.lock"
    lock_file.write_bytes(b"not json at all")
    old = time.time() - 3600
    os.utime(str(lock_file), (old, old))
    waiter = KernelLock(str(tmp_path), ttl=1)
    waiter.acquire(timeout=3, poll=0.1)  # corrupt+old -> breakable
    waiter.release()


def test_non_finite_lock_payload_treated_as_corrupt(tmp_path):
    # valid JSON, but Infinity ttl would block forever / NaN would break instantly
    lock_file = tmp_path / ".kernel.lock"
    lock_file.write_text('{"acquired_at": 1e999, "ttl": Infinity, "pid": 1}')
    old = time.time() - 3600
    os.utime(str(lock_file), (old, old))
    waiter = KernelLock(str(tmp_path), ttl=1)
    waiter.acquire(timeout=3, poll=0.1)  # corrupt-by-policy + old mtime -> breakable
    waiter.release()


def test_corrupt_but_fresh_lock_not_broken(tmp_path):
    lock_file = tmp_path / ".kernel.lock"
    lock_file.write_bytes(b"not json at all")  # fresh mtime
    waiter = KernelLock(str(tmp_path), ttl=60)
    with pytest.raises(LockTimeout):
        waiter.acquire(timeout=0.6, poll=0.05)


def test_staleness_honors_holders_declared_ttl(tmp_path):
    # holder declared a LONG lease; a waiter with a short ttl must NOT break it
    holder = KernelLock(str(tmp_path), ttl=60)
    holder.acquire(timeout=1)
    time.sleep(0.4)
    impatient = KernelLock(str(tmp_path), ttl=0.2)
    with pytest.raises(LockTimeout):
        impatient.acquire(timeout=0.8, poll=0.05)
    holder.release()


def test_stale_break_restores_freshly_captured_lock(tmp_path, monkeypatch):
    """Fable-Check 4 / BUG-1: a fresh lock slipping in between proof and claim
    must be captured-verified and RESTORED, never broken."""
    import kernel.lock as lockmod

    dead = KernelLock(str(tmp_path), ttl=0.2)
    dead.acquire(timeout=1)
    time.sleep(0.3)  # provably expired lease

    lock_path = os.path.join(str(tmp_path), ".kernel.lock")
    fresh_payload = json.dumps(
        {"lock_schema_version": 1, "pid": 999, "host": "x", "token": "fresh",
         "acquired_at": time.time() + 10, "ttl": 60},
        sort_keys=True,
    ).encode("utf-8")

    real_replace = lockmod.os.replace
    hits = {"n": 0}

    def racing_replace(src, dst):
        # simulate a third party re-locking the path right before the claim
        if hits["n"] == 0 and src.rstrip("\\/").endswith(".kernel.lock"):
            hits["n"] += 1
            with open(src, "wb") as fh:
                fh.write(fresh_payload)
        return real_replace(src, dst)

    monkeypatch.setattr(lockmod.os, "replace", racing_replace)
    waiter = KernelLock(str(tmp_path), ttl=60)
    with pytest.raises(LockTimeout):
        waiter.acquire(timeout=1.0, poll=0.1)
    with open(lock_path, "rb") as fh:
        assert fh.read() == fresh_payload  # fresh lock restored, not broken


# -- lock: concurrency ---------------------------------------------------------

def test_second_process_blocks(tmp_path):
    """II.12: the exclusivity claim across real OS processes, not just threads."""
    holder = KernelLock(str(tmp_path))
    holder.acquire(timeout=1)
    code = (
        "import sys\n"
        "sys.path.insert(0, %r)\n"
        "from kernel.lock import KernelLock, LockTimeout\n"
        "try:\n"
        "    KernelLock(%r).acquire(timeout=0.6, poll=0.05)\n"
        "except LockTimeout:\n"
        "    sys.exit(42)\n"
        "sys.exit(1)\n"
    ) % (TEAM_KITS_DIR, str(tmp_path))
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 42, result.stderr
    holder.release()

def test_threads_serialize_under_lock(tmp_path):
    counter_file = tmp_path / "counter.txt"
    counter_file.write_text("0")
    errors = []

    def work():
        try:
            for _ in range(5):
                with KernelLock(str(tmp_path), ttl=30, poll=0.02):
                    value = int(counter_file.read_text())
                    time.sleep(0.002)  # widen the race window
                    counter_file.write_text(str(value + 1))
        except Exception as e:  # pragma: no cover - diagnostic
            errors.append(e)

    threads = [threading.Thread(target=work) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert int(counter_file.read_text()) == 40


# -- lock: long paths ----------------------------------------------------------

def test_lock_in_deep_path(tmp_path):
    deep = os.path.join(str(tmp_path), "x" * 120, "y" * 120)
    os.makedirs(ext_path(deep), exist_ok=True)
    assert len(deep) > 240
    with KernelLock(deep):
        pass


def test_ext_path_semantics(tmp_path):
    p = str(tmp_path / "f.txt")
    if sys.platform == "win32":
        e = ext_path(p)
        assert e.startswith("\\\\?\\")
        assert ext_path(e) == e  # idempotent
        assert ext_path("\\\\server\\share\\x").startswith("\\\\?\\UNC\\")
    else:
        assert ext_path(p) == p


# -- hashing: canonicalization -------------------------------------------------

def test_key_order_irrelevant():
    assert subject_manifest_hash({"a": 1, "b": 2}) == subject_manifest_hash({"b": 2, "a": 1})


def test_nfc_normalization():
    composed = 'caf' + chr(0xE9)       # e-acute, single codepoint
    decomposed = 'cafe' + chr(0x301)   # e + combining acute
    assert composed != decomposed      # different codepoints ...
    assert subject_manifest_hash({'t': composed}) == subject_manifest_hash({'t': decomposed})


def test_nfc_applies_to_keys():
    composed = 'caf' + chr(0xE9)
    decomposed = 'cafe' + chr(0x301)
    assert subject_manifest_hash({composed: 1}) == subject_manifest_hash({decomposed: 1})


def test_version_participates(monkeypatch):
    before = subject_manifest_hash({"a": 1})
    monkeypatch.setattr("kernel.hashing.HASH_SCHEMA_VERSION", HASH_SCHEMA_VERSION + 1)
    assert subject_manifest_hash({"a": 1}) != before


def test_content_changes_hash():
    assert subject_manifest_hash({"goal": "a"}) != subject_manifest_hash({"goal": "b"})


def test_non_json_type_raises():
    with pytest.raises(TypeError):
        subject_manifest_hash({"when": object()})


def test_nan_raises():
    with pytest.raises(ValueError):
        subject_manifest_hash({"x": float("nan")})


def test_canonical_json_compact_and_unicode():
    text = canonical_json({"b": "über", "a": 1})
    assert text == '{"a":1,"b":"über"}'  # sorted, compact, non-ascii preserved


def test_nfc_sibling_key_collision_raises():
    composed = 'caf' + chr(0xE9)       # e-acute, single codepoint
    decomposed = 'cafe' + chr(0x301)   # e + combining acute -> same key after NFC
    assert composed != decomposed      # distinct dict keys BEFORE normalization
    with pytest.raises(ValueError):
        subject_manifest_hash({composed: 1, decomposed: 2})


def test_non_string_dict_key_raises():
    with pytest.raises(TypeError):
        subject_manifest_hash({1: "x"})


def test_golden_hash_pin():
    """Canonicalization drift tripwire: this exact manifest MUST keep this exact
    hash across Python/lib upgrades -- any intended change to the scheme goes
    through a HASH_SCHEMA_VERSION bump, never a silent drift."""
    manifest = {
        "problem": "p",
        "goal": ": über",
        "acceptance_criteria": [{"id": "AC-1", "text": "café"}],
        "out_of_scope": [],
        "invariants": None,
        "n": 42,
        "f": 1.5,
        "b": True,
    }
    assert subject_manifest_hash(manifest) == (
        "d5dcf6a8aefed485c03f12dabf8bab20607eb2d8a8848972b52b0c7670bc6cea"
    )


# -- validate_state: a freshly scaffolded project must be silent ----------------

def _template_state(tmp_path, kit="dev-team"):
    """A `project_memory/` exactly as the initializer lays it down -- nothing captured yet."""
    import shutil
    src = os.path.join(TEAM_KITS_DIR, kit, "templates", "project_memory")
    dst = str(tmp_path / "project_memory")
    shutil.copytree(src, dst)
    return dst


def test_fresh_template_state_produces_no_finding_at_all(tmp_path):
    """A validator that warns about the empty project it just created teaches everyone to ignore it.

    The staging-orphan scan reads the entries of `staging/` as item ids. Every kit template ships
    `staging/.gitkeep` so git can carry the empty directory, so it reported
    `staging/.gitkeep: orphaned staging dir` in EVERY `python scripts/harness.py validate` and every session brief of
    every fresh project -- permanent noise in the one output that is supposed to mean something.
    Asserting on the whole finding list rather than on the absence of that one string is deliberate:
    any other rule that starts firing on an empty project is the same defect.
    """
    from kernel.report import validate_state
    from kernel.state import ProjectState
    root = _template_state(tmp_path)
    # The tooth: without a non-directory entry under staging/ the assertion below is vacuous, and
    # `.gitkeep` is exactly the entry the shipped template puts there.
    assert os.path.isfile(os.path.join(root, "staging", ".gitkeep"))
    assert validate_state(ProjectState(root)) == []


def test_staging_dir_without_an_active_item_is_still_reported(tmp_path):
    """The other half: silencing the `.gitkeep` noise must not silence a real orphan.

    A staging KEY is a DIRECTORY named after an item, so a directory with no active task or root item
    behind it is the finding the scan exists for.
    """
    from kernel.report import validate_state
    from kernel.state import ProjectState
    root = _template_state(tmp_path)
    os.makedirs(os.path.join(root, "staging", "TSK-9999"))
    findings = validate_state(ProjectState(root))
    assert [(f["severity"], f["item"]) for f in findings] == [("warning", "staging/TSK-9999")]


# ---------------- kernel.layout: who writes what under the state dir ----------------
#
# The whole carve-out `gate_write_scope` now makes rests on `kernel.layout` telling canonical state
# apart from a kit document. These tests measure that claim against the WRITERS rather than against
# the module's own list.

def _pr_fields():
    return {
        "title": "checkout", "class": "feature", "problem": "p", "goal": "g",
        "acceptance_criteria": [{"id": "AC-1", "text": "it works"}],
        "invariants": [], "out_of_scope": [], "priority": "high",
        "user_story": "As a buyer I can pay",
    }


def _files_under(root):
    found = set()
    for directory, _subdirs, names in os.walk(root):
        for name in names:
            found.add(os.path.relpath(os.path.join(directory, name), root)
                      .replace("\\", "/").lower())
    return found


def test_every_kernel_writer_lands_inside_the_declared_area(tmp_path):
    """`layout.kernel_written_subtrees` claims to cover every kernel writer -- so drive them.

    This is the measurement the module's definition rests on: a writer that starts landing outside
    the declared area turns this red, which is the only thing that keeps "the state directory has
    exactly one writer" from becoming a sentence nothing checks. It is deliberately a WALK of the
    files that appeared, not a check of the paths the writers returned: a writer that also drops a
    companion file somewhere else is exactly the case a return value would hide.

    Kit documents and `staging/` are subtracted because they are the two areas the definition
    excludes by name; everything else a kernel operation created must answer `is_kernel_written`.
    """
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from conftest import approve, mint_via_hook
    from kernel import approvals, dispatch, layout
    from kernel.state import ProjectState

    root = _template_state(tmp_path)
    before = _files_under(root)
    state = ProjectState(root)
    state.capture("PR", _pr_fields())
    approve(state, "PR-0001", "scope")
    task = dispatch.create_task(state, {
        "product_requirement": "PR-0001", "derives_from": "PR-0001", "type": "implementation",
        "assigned_role": "backend-developer", "acceptance_refs": ["AC-1"],
        "allowed_scope": ["src/"], "forbidden_scope": [], "required_inputs": [],
        "expected_outputs": [], "dependencies": [],
    })
    state.transition(task["id"], "READY")
    lease = dispatch.create_lease(state, task["id"])
    dispatch.bind_agent(state, task["id"], "agent-1")
    dispatch.spawn_outcome(state, task["id"], ok=True)
    dispatch.submit_result(state, {
        "task_id": task["id"], "role": "backend-developer", "status_proposal": "SUBMITTED",
        "summary": "done", "outputs": [], "evidence": [], "scope_touched": [], "followups": [],
    })
    state.capture("EVD", {"kind": "test", "related": ["PR-0001"], "result": "pass",
                          "summary": "qa", "artifact_refs": ["staging/%s/run.log" % task["id"]]})
    state.generate_index()
    # an approval that is minted and then revoked, so consumed/ and revoked/ both get written
    request = approvals.create_pending_request(state, "delivery", "PR-0001")
    mint_via_hook(state, request)
    approvals.revoke(state, state.read_item("PR-0001")["approval_ref"])
    state.archive(state.capture("DEC", {"title": "d", "context": "c", "decision": "d",
                                        "consequences": "c", "source": "PR-0001"})["id"])
    assert lease["task_id"] == task["id"]

    created = _files_under(root) - before
    assert created, "the drive-through created nothing -- this test would pass vacuously"
    # THE LOAD-BEARING CLAIM: nothing this drive-through produced may come out as a DOCUMENT,
    # because a document is what `gate_write_scope` hands to the write tools.
    documents = sorted(rel for rel in created if layout.is_project_document(root, rel))
    assert documents == [], (
        "these writes came out as kit documents, so a tool write could overwrite them: %s"
        % documents)
    # ...and the declared area really has to COVER them, or `is_project_document` is only right by
    # accident of the dotted/staging exclusions. `.audit/**` is subtracted here and only here: it
    # is written by the audit helper in the hook process, not by a kernel writer, and the module
    # docstring names it as machinery rather than as canonical state.
    outside = sorted(rel for rel in created
                     if not layout.is_kernel_written(root, rel)
                     and not rel.startswith(".")
                     and not rel.startswith(layout.STAGING_DIRNAME + "/"))
    assert outside == [], (
        "these kernel writes landed outside `kernel_written_subtrees`: %s" % outside)


_DIRECTORY_BUILDERS = ("staging_root", "archive_root", "legacy_root", "generated_path")


def _builder_segments():
    """{path segment: the builder that owns it} -- derived by ASKING the builders.

    The builder NAMES are named here because they are what is under test; the SEGMENTS are not,
    so a builder that starts composing a different directory moves this test with it instead of
    leaving a stale literal behind.
    """
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from kernel.state import ProjectState

    probe = ProjectState(os.path.join(os.sep, "probe"))
    answers = {name: getattr(probe, name)() if name != "generated_path"
               else os.path.dirname(probe.generated_path("x"))
               for name in _DIRECTORY_BUILDERS}
    segments = {}
    for name, path in answers.items():
        rel = os.path.relpath(path, probe.root).replace(os.sep, "/")
        assert rel and "/" not in rel and rel != os.pardir, (
            "%s no longer answers a single directory under the state root (%r), so what this "
            "test compares against is not a segment any more" % (name, rel))
        segments[rel] = name
    return segments


def test_no_kernel_module_composes_a_directory_a_builder_already_owns():
    """A path a builder composes is not composed a second time -- as a rule, not as a review.

    THE DEFECT THIS IS THE TRIPWIRE FOR has been found three times in this package, once per
    round, always the same way and always by reading rather than by measuring: the dry run
    composed `archive/<type>/` out of `v2_type.lower()` while `ProjectState.archive_path` keys it
    by the id's own TYPE, so the run created `archive/PROC/` and printed `archive/proc/` -- one
    filesystem hid it and another does not. Then `legacy/` one file further on. Then the session
    brief and the index writer, both composing `generated/` although `generated_path`'s own
    docstring names those two as the writers it exists for, and `staging/` in four places.

    THE RULE IS THE ONE PROPERTY: a string constant that names a directory a builder owns may
    appear in a path composition only inside that builder. Everything else asks the builder.

    WHERE THE RULE IS READ, said here because the paragraph that stood here claimed it for all code
    and this loop opens one directory: the KERNEL PACKAGE. Outside it the same names are composed
    by shipped code that has no `ProjectState` at the point of use -- the hooks' bridge and two
    template scripts -- and by this suite, where an independently composed path is the point rather
    than the defect. The first of those two is a hole with its own measurement and its own
    tripwire: `L24` in `docs/POST_V2_WISHLIST.md`, measured by
    `test_the_path_rule_stops_at_the_kernel_package_and_the_rest_is_counted` below.

    RED the moment a module of this package joins one of those names onto a path again -- which is
    what all four of the occurrences above did, and what no amount of care has stopped so far.
    """
    import ast

    segments = _builder_segments()
    kernel_dir = os.path.join(TEAM_KITS_DIR, "kernel")
    offenders = []
    for name in sorted(os.listdir(kernel_dir)):
        if not name.endswith(".py"):
            continue
        with open(os.path.join(kernel_dir, name), encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), filename=name)
        owner_of = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for inner in ast.walk(node):
                    owner_of[id(inner)] = node.name
        for node in ast.walk(tree):
            # a path composition, not a message: `", ".join(...)` has a literal receiver
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "join"
                    and not isinstance(node.func.value, ast.Constant)):
                continue
            for arg in node.args:
                if not (isinstance(arg, ast.Constant) and arg.value in segments):
                    continue
                if owner_of.get(id(node)) == segments[arg.value]:
                    continue
                offenders.append("%s:%d composes %r, which %s already answers"
                                 % (name, node.lineno, arg.value, segments[arg.value]))
    assert not offenders, "\n".join(offenders)
    # ...and the counter-direction: the builders themselves still compose their own directory, so
    # a rule that simply matched nothing would not pass this.
    assert len(segments) == len(_DIRECTORY_BUILDERS)


def _compositions_outside_the_kernel_package():
    """{module path: [(line, segment)]} for SHIPPED code that composes a builder-owned directory.

    Shipped means: everything under `team-kits/` that a project installs or runs, minus the kernel
    package where the rule holds. This suite is deliberately not in it -- a test composing the path
    it expects is the independent oracle, and folding it in would make the count below a fact about
    the tests rather than about the product.
    """
    import ast

    segments = _builder_segments()
    kernel_dir = os.path.join(TEAM_KITS_DIR, "kernel")
    found = {}
    for current, dirs, files in os.walk(TEAM_KITS_DIR):
        dirs[:] = [name for name in dirs if name != "__pycache__"]
        if os.path.normpath(current) == os.path.normpath(kernel_dir):
            continue
        for name in sorted(files):
            if not name.endswith(".py"):
                continue
            path = os.path.join(current, name)
            with open(path, encoding="utf-8") as handle:
                tree = ast.parse(handle.read(), filename=path)
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "join"
                        and not isinstance(node.func.value, ast.Constant)):
                    continue
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and arg.value in segments:
                        found.setdefault(
                            os.path.relpath(path, TEAM_KITS_DIR).replace(os.sep, "/"),
                            []).append((node.lineno, arg.value))
    return found


# What the reach of the rule above costs today, measured 2026-08-08 with the reader beside this
# line. A count rather than a list of places, and it is pinned in BOTH directions on purpose: the
# entry in the hole list is out of date the moment a new composition appears, and equally out of
# date the moment the last one goes. The places themselves are named in `L24`; naming them here as
# well would be the second statement of one fact, which is the failure mode this whole rule exists
# against.
_COMPOSITIONS_OUTSIDE_THE_PACKAGE = 7


def test_the_path_rule_stops_at_the_kernel_package_and_the_rest_is_counted():
    """The entry is `L24` in `docs/POST_V2_WISHLIST.md`.

    The rule above holds inside the kernel package and is READ there. Shipped code outside it
    composes the same directory names by hand, because at those points there is no `ProjectState`
    to ask: the hooks' bridge decides whether a repo is greenfield by walking around `generated/`,
    and two template scripts address `generated/` and `archive/` directly. Each of them is a second
    spelling of a builder's answer, which is exactly the defect the rule is a tripwire for -- the
    difference is only that closing them would move a kernel-free bootstrap path onto the kernel.

    RED in both directions, which is what a counted residual owes: a new composition outside the
    package, and the last one disappearing without the entry being closed.
    """
    found = _compositions_outside_the_kernel_package()
    places = sum(len(hits) for hits in found.values())
    assert places == _COMPOSITIONS_OUTSIDE_THE_PACKAGE, (
        "shipped code outside the kernel package composes a builder-owned directory in %d "
        "place(s), and L24 records %d: %s"
        % (places, _COMPOSITIONS_OUTSIDE_THE_PACKAGE,
           {name: hits for name, hits in sorted(found.items())}))


def test_the_two_files_a_merge_gate_blocks_on_are_documents_no_writer_produces(tmp_path):
    """The root of B1, stated as the property rather than as two names.

    `gate_memory_complete` blocks merge and push on the content of `product/masterplan.md` and
    `project_config.yaml`. If either were canonical state, the block would have no key -- which is
    exactly the state this package found. The test that matters is therefore the pair: the two
    files the gate reads are documents, AND the drive-through above never produces them.
    """
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from kernel import layout

    root = _template_state(tmp_path)
    for shipped in ("product/masterplan.md", "project_config.yaml"):
        assert os.path.isfile(os.path.join(root, *shipped.split("/"))), shipped
        assert layout.is_project_document(root, shipped), shipped
        assert not layout.is_kernel_written(root, shipped), shipped


@pytest.mark.parametrize("relative", [
    "product/active/PR-0001.yaml",          # a typed item
    "approvals/pending/deadbeef.yaml",      # a mint code in cleartext
    "approvals/APR-0001.yaml",
    "tasks/leases/TSK-0001.lease.yaml",
    "tasks/results/TSK-0001.envelope.yaml",
    "generated/index.yaml",
    "archive/TSK/2026/TSK-0001.yaml",       # a real year, not the probe's
    "architecture/revisions/ARC-0001.r01.drawio.svg",
    ".audit/hook_events.jsonl",             # machinery, not content
    ".kernel.lock",
    "staging/TSK-0001/proposal.md",         # has its own per-key rule
])
def test_canonical_state_and_machinery_are_not_documents(tmp_path, relative):
    """The complement, spelled out where a widening would show up as a green test turning red."""
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from kernel import layout

    root = _template_state(tmp_path)
    assert not layout.is_project_document(root, relative)


# ---------------- the lease is bound to the status it serves ----------------

def _leasable_task(state):
    """A READY task under an approved root -- the fixture the three lease tests share."""
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from conftest import approve
    from kernel import dispatch

    state.capture("PR", _pr_fields())
    approve(state, "PR-0001", "scope")
    task = dispatch.create_task(state, {
        "product_requirement": "PR-0001", "derives_from": "PR-0001", "type": "implementation",
        "assigned_role": "backend-developer", "acceptance_refs": ["AC-1"],
        "allowed_scope": ["src/"], "forbidden_scope": [], "required_inputs": [],
        "expected_outputs": [], "dependencies": [],
    })
    state.transition(task["id"], "READY")
    return task["id"]


def test_the_lease_bearing_statuses_are_the_ones_the_lifecycle_produces(tmp_path):
    """`dispatch.LEASE_BEARING_STATUSES` is a claim about the lifecycle -- so run the lifecycle.

    Without this the tuple is a constant nothing compares against, and a lifecycle that started
    keeping a lease into a third status (or stopped keeping it into IN_PROGRESS) would leave
    `release_lease_for_status_locked` dropping a lease a running child still needs.
    """
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from kernel import dispatch
    from kernel.state import ProjectState

    root = _template_state(tmp_path)
    state = ProjectState(root)
    task_id = _leasable_task(state)
    lease_file = os.path.join(root, "tasks", "leases", task_id + ".lease.yaml")

    dispatch.create_lease(state, task_id)
    assert state.read_item(task_id)["status"] in dispatch.LEASE_BEARING_STATUSES
    assert os.path.isfile(lease_file), "create_lease produced no lease"
    dispatch.bind_agent(state, task_id, "agent-1")
    dispatch.spawn_outcome(state, task_id, ok=True)
    assert state.read_item(task_id)["status"] in dispatch.LEASE_BEARING_STATUSES
    assert os.path.isfile(lease_file), "the running child's lease was dropped"
    dispatch.submit_result(state, {
        "task_id": task_id, "role": "backend-developer", "status_proposal": "SUBMITTED",
        "summary": "done", "outputs": [], "evidence": [], "scope_touched": [], "followups": [],
    })
    assert state.read_item(task_id)["status"] not in dispatch.LEASE_BEARING_STATUSES
    assert not os.path.exists(lease_file)


def test_a_transition_off_a_leased_task_frees_the_lease_and_the_task_is_claimable(tmp_path):
    """The dead end: LEASED -> READY is an explicit back-edge and used to leave a live lease.

    Measured before this: `transition READY` moved the status, the lease file stayed, and
    `create_lease` then refused the READY task with "a lease already exists" for the full TTL while
    `validate` reported nothing. The test drives the EXIT -- it re-leases the task -- rather than
    inspecting a message.
    """
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from kernel import dispatch
    from kernel.state import ProjectState

    root = _template_state(tmp_path)
    state = ProjectState(root)
    task_id = _leasable_task(state)
    first = dispatch.create_lease(state, task_id)
    state.transition(task_id, "READY")
    assert not os.path.exists(os.path.join(root, "tasks", "leases", task_id + ".lease.yaml"))
    second = dispatch.create_lease(state, task_id)
    assert second["nonce"] != first["nonce"]


def test_a_cancelled_task_does_not_keep_a_lease_alive(tmp_path):
    """The same rule from the other end: CANCELLED is terminal, so no child is coming."""
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from kernel import dispatch
    from kernel.state import ProjectState

    root = _template_state(tmp_path)
    state = ProjectState(root)
    task_id = _leasable_task(state)
    dispatch.create_lease(state, task_id)
    state.transition(task_id, "CANCELLED")
    assert dispatch.live_leases(state) == []


def test_a_running_lease_is_reported_with_the_time_it_has_left(tmp_path):
    """`sweep-leases` said only what it released; the wait it left behind had no length."""
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from kernel import dispatch
    from kernel.state import ProjectState

    root = _template_state(tmp_path)
    state = ProjectState(root)
    task_id = _leasable_task(state)
    dispatch.create_lease(state, task_id, ttl=120.0)
    assert dispatch.sweep_expired_leases(state) == ([], [])
    reported = dispatch.live_leases(state)
    assert [entry[0] for entry in reported] == [task_id]
    assert 0 < reported[0][1] <= 120.0


# ---------------- DEC-0038 / BUG-0010: lease honesty ----------------

def test_a_bare_transition_cannot_mint_leased(tmp_path):
    """DEC-0038 AC-1: a lease-bearing status is established by a real lease, never by a transition.

    RED without `assert_lease_backed_transition_locked`: `transition READY -> LEASED` returned
    rc 0 and left a task reading LEASED with no lease file -- untrue bookkeeping that `sweep-leases`
    would later be asked to reconcile. The test measures the STATE, not a message: the task stays
    READY and no lease file appears.
    """
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from kernel import dispatch
    from kernel.state import ProjectState

    root = _template_state(tmp_path)
    state = ProjectState(root)
    task_id = _leasable_task(state)                 # READY, approved root, no lease yet
    with pytest.raises(dispatch.DispatchError, match="real dispatch lease"):
        state.transition(task_id, "LEASED")
    assert state.read_item(task_id)["status"] == "READY"
    assert not os.path.exists(os.path.join(root, "tasks", "leases", task_id + ".lease.yaml"))


def test_the_dispatch_path_still_reaches_leased_after_the_guard(tmp_path):
    """DEC-0038 AC-2 (regression): the guard refuses ONLY the bare transition -- `create_lease`
    still mints LEASED. RED if the guard were placed on the status WRITE instead of the transition
    (it would stop the whole dispatch lifecycle, `create_lease` raising instead of leasing).
    """
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from kernel import dispatch
    from kernel.state import ProjectState

    root = _template_state(tmp_path)
    state = ProjectState(root)
    task_id = _leasable_task(state)
    lease = dispatch.create_lease(state, task_id)
    assert state.read_item(task_id)["status"] == "LEASED"
    assert lease["nonce"]
    assert dispatch.lease_in_force(state, task_id)


def test_sweep_reports_a_leased_task_whose_lease_vanished(tmp_path):
    """DEC-0038 AC-3: a LEASED task with no live lease is REPORTED, never silently reset.

    The lease file is removed by hand -- the only way LEASED-without-lease can arise once the
    transition guard stands (old state / corruption). RED without `leased_without_live_lease`:
    the TTL sweep sees no lease file, so nothing surfaces the anomaly and the untrue bookkeeping
    stays invisible. The task must be NAMED and must NOT be reset.
    """
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from kernel import dispatch
    from kernel.state import ProjectState

    root = _template_state(tmp_path)
    state = ProjectState(root)
    task_id = _leasable_task(state)
    dispatch.create_lease(state, task_id)           # -> LEASED + lease file
    os.remove(os.path.join(root, "tasks", "leases", task_id + ".lease.yaml"))
    assert dispatch.sweep_expired_leases(state) == ([], [])  # no lease file -> nothing to sweep
    assert dispatch.leased_without_live_lease(state) == [task_id]
    assert state.read_item(task_id)["status"] == "LEASED"   # reported, NOT reset


def test_an_in_progress_task_without_a_lease_is_not_flagged(tmp_path):
    """The counter-direction, so the reporter cannot be satisfied by flagging every lease-bearing
    status: a running child legitimately outlives its lease. `sweep_expired_leases` drops an
    expired lease but leaves IN_PROGRESS in place, and that is expected state, not corruption -- so
    it must NOT appear in the report.
    """
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from kernel import dispatch
    from kernel.state import ProjectState

    root = _template_state(tmp_path)
    state = ProjectState(root)
    task_id = _leasable_task(state)
    dispatch.create_lease(state, task_id)                   # -> LEASED + lease file
    dispatch.spawn_outcome(state, task_id, ok=True)         # LEASED -> IN_PROGRESS (keeps the lease)
    os.remove(os.path.join(root, "tasks", "leases", task_id + ".lease.yaml"))  # child outlived it
    assert state.read_item(task_id)["status"] == "IN_PROGRESS"
    assert not dispatch.lease_in_force(state, task_id)
    assert dispatch.leased_without_live_lease(state) == []  # IN_PROGRESS-without-lease is not flagged


def test_sweep_leases_cli_names_a_leased_task_without_a_lease(tmp_path, capsys):
    """AC-3 through the command a role actually runs: `sweep-leases` prints the anomaly line."""
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from kernel import cli, dispatch
    from kernel.state import ProjectState

    root = _template_state(tmp_path)
    state = ProjectState(root)
    task_id = _leasable_task(state)
    dispatch.create_lease(state, task_id)
    os.remove(os.path.join(root, "tasks", "leases", task_id + ".lease.yaml"))
    assert cli.main(["--root", root, "sweep-leases"]) == 0
    out = capsys.readouterr().out
    assert "LEASED without a lease" in out and task_id in out
    assert state.read_item(task_id)["status"] == "LEASED"


# ---------------- a task cannot be created against another root's criteria ----------------

def test_a_cross_root_origin_is_refused_at_creation(tmp_path):
    """B4 at its root: the item the validator would flag can no longer come into existence.

    The pair of assertions is the point -- the creation is refused AND the state stays clean, so
    the merge gate never blocks on something whose only exit was `archive`, a word neither remedy
    contained.
    """
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from kernel import dispatch
    from kernel.report import validate_state
    from kernel.state import ProjectState

    root = _template_state(tmp_path)
    state = ProjectState(root)
    state.capture("PR", _pr_fields())
    state.capture("PR", dict(_pr_fields(), title="another root"))
    state.capture("BUG", {"title": "b", "related_pr": "PR-0002", "observed": "o", "expected": "e",
                          "repro": "r", "severity": "high",
                          "acceptance_criteria": [{"id": "FIX-1", "text": "no crash"}]})
    with pytest.raises(dispatch.DispatchError) as exc:
        dispatch.create_task(state, {
            "product_requirement": "PR-0001", "derives_from": "BUG-0001", "type": "bugfix",
            "assigned_role": "backend-developer", "acceptance_refs": ["FIX-1"],
            "allowed_scope": ["src/"], "forbidden_scope": [], "required_inputs": [],
            "expected_outputs": [], "dependencies": [],
        })
    assert "PR-0002" in str(exc.value) and "PR-0001" in str(exc.value)
    assert [f for f in validate_state(state) if f["severity"] == "error"] == []


def test_a_task_under_its_own_root_is_still_creatable(tmp_path):
    """The other side of the same rule -- a bugfix task under the BUG's OWN root must still work.

    Without this the refusal above could be satisfied by refusing every `derives_from` that is not
    the root itself, which would make every bugfix, CR and EXP task uncreatable.
    """
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from kernel import dispatch
    from kernel.state import ProjectState

    root = _template_state(tmp_path)
    state = ProjectState(root)
    state.capture("PR", _pr_fields())
    state.capture("BUG", {"title": "b", "related_pr": "PR-0001", "observed": "o", "expected": "e",
                          "repro": "r", "severity": "high",
                          "acceptance_criteria": [{"id": "FIX-1", "text": "no crash"}]})
    task = dispatch.create_task(state, {
        "product_requirement": "PR-0001", "derives_from": "BUG-0001", "type": "bugfix",
        "assigned_role": "backend-developer", "acceptance_refs": ["FIX-1"],
        "allowed_scope": ["src/"], "forbidden_scope": [], "required_inputs": [],
        "expected_outputs": [], "dependencies": [],
    })
    assert task["status"] == "DRAFT"


# ---------------- the approval surface a role can actually reach ----------------

def test_the_transition_refusal_names_a_command_that_walks_the_edge(tmp_path):
    """A remedy is only a remedy if running it works -- so this RUNS it.

    The refusal used to say "run the kernel approval flow" and name neither the command nor the
    KIND, and the kind is not guessable: `EXP DESIGNED -> APPROVED` is committed by a `delivery`
    approval, so the obvious `scope` request opens, mints, and still leaves the edge unwalked.
    Here the command is read OUT OF the refusal and executed.
    """
    import re as _re
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from conftest import mint_via_hook
    from kernel import approvals
    from kernel.state import ProjectState

    root = _template_state(tmp_path)
    state = ProjectState(root)
    state.capture("RQ", {"title": "q", "class": "exploratory", "question": "why",
                         "motivation": "m", "acceptance_criteria": [{"id": "AC-1", "text": "x"}],
                         "out_of_scope": [], "priority": "high"})
    state.capture("EXP", {"derives_from": "RQ-0001", "design": "d", "variables": ["v"],
                          "success_criteria": [{"id": "SC-1", "text": "s"}], "evidence_refs": []})
    assert state.read_item("EXP-0001")["status"] == "DESIGNED"
    with pytest.raises(approvals.ApprovalError) as exc:
        state.transition("EXP-0001", "APPROVED")
    named = _re.search(r"request-approval (\w+) (EXP-0001)", str(exc.value))
    assert named, "the refusal names no runnable command:\n%s" % exc.value
    mint_via_hook(state, approvals.create_pending_request(state, named.group(1), named.group(2)))
    assert state.read_item("EXP-0001")["status"] == "APPROVED"


# ============================ growing a kit document: the filing plan (FR-0049 step 5)
def _office_state(tmp_path):
    return _template_state(tmp_path, kit="office-team")


def _rule_flags(**overrides):
    """The six values one filing rule carries, as the manifest builder's own parameter names."""
    rule = {"rule_id": "FP-009", "path_template": "archive/finance/<year>/",
            "document_types": "invoice,credit_note",
            "filename_template": "YYYY-MM-DD_<counterparty>", "retention": "8 Jahre",
            "reason": "Lieferantenrechnungen hatten keine Regel"}
    rule.update(overrides)
    return rule


def _approved_rule(state, **overrides):
    """Mint a filing_rule approval for exactly these values, through the REAL approval hook."""
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from conftest import mint_via_hook
    from kernel import approvals

    manifest = approvals.filing_rule_subject_manifest(**_rule_flags(**overrides))
    mint_via_hook(state, approvals.create_pending_request(
        state, "filing_rule", manifest=manifest,
        approval_expires=time.time() + approvals.LINE_APPROVAL_VALIDITY))
    return manifest


def test_every_kernel_module_that_writes_into_a_document_is_registered(tmp_path):
    """The tripwire under `layout._DOCUMENT_WRITER_MODULES`, measuring BOTH of its ends.

    That tuple is an unavoidable enumeration -- importing every module of the package to look for
    the attribute would pull the whole import graph into a hook's hot path -- so it gets the
    treatment this repo gives every enumeration: a walk of the package finds every module that
    DECLARES `DOCUMENT_WRITES`, and the tuple must be exactly that set. A writer that ships without
    being registered here would be invisible to `partial_writers`, and the write-scope refusal
    would deny a route the harness has; an entry that has stopped writing is the same defect
    mirrored. Both are one failure each.

    The SHAPE of a declaration is checked too, because `partial_writers` indexes it by key: a
    writer whose entries lack `document`, `field` or `command` would raise inside a GATE.
    """
    import importlib
    import pkgutil
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    import kernel
    from kernel import layout

    declaring = set()
    for info in pkgutil.iter_modules(kernel.__path__):
        module = importlib.import_module("kernel." + info.name)
        if getattr(module, "DOCUMENT_WRITES", None):
            declaring.add(info.name)
    assert declaring, "no kernel module declares DOCUMENT_WRITES -- the reader stopped matching"
    assert set(layout._DOCUMENT_WRITER_MODULES) == declaring, (
        "the registry and the writers disagree: registered-but-silent %s, writing-but-unregistered "
        "%s" % (sorted(set(layout._DOCUMENT_WRITER_MODULES) - declaring),
                sorted(declaring - set(layout._DOCUMENT_WRITER_MODULES))))
    for entry in layout._document_writes():
        assert set(entry) >= {"document", "field", "command"}, entry
        assert layout.partial_writers(entry["document"]), entry


def test_a_filing_rule_is_written_only_when_the_user_approved_exactly_it(tmp_path):
    """What the user signs is what lands in the plan -- checked on the ways it could not be.

    The approval binds the six rule fields as the manifest hashes them, and `filing.apply`
    re-derives that manifest from what it is asked to write. So a rule differing in ANY field --
    here the location, the strongest one -- is not covered by the approval for the other, and an
    unapproved call must leave the file byte-identical.
    """
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from kernel import approvals, filing
    from kernel.state import ProjectState, StateError

    root = _office_state(tmp_path)
    state = ProjectState(root)
    before = filing.read_text(filing.plan_path(state))

    unapproved = approvals.filing_rule_subject_manifest(**_rule_flags())
    with pytest.raises(StateError) as exc:
        filing.apply(state, unapproved)
    assert "no user approval" in str(exc.value)
    assert filing.read_text(filing.plan_path(state)) == before, "a refusal must change nothing"

    _approved_rule(state)
    elsewhere = approvals.filing_rule_subject_manifest(
        **_rule_flags(path_template="archive/anderswo/<year>/"))
    with pytest.raises(StateError):
        filing.apply(state, elsewhere)
    assert filing.read_text(filing.plan_path(state)) == before

    approved = approvals.filing_rule_subject_manifest(**_rule_flags())
    result = filing.apply(state, approved)
    assert result["rule"] == filing.rule_from(approved)
    assert filing.existing_rules(state) == [filing.rule_from(approved)]
    # ...and a SECOND run under the still-live approval does not double the id
    with pytest.raises(StateError) as clash:
        filing.apply(state, approved)
    assert "already carries a rule with the id" in str(clash.value)
    assert len(filing.existing_rules(state)) == 1


def test_appending_a_rule_keeps_everything_else_in_the_plan(tmp_path):
    """The plan is a kit DOCUMENT whose comments carry its field list and its retention defaults.

    A `yaml.safe_dump` of a parsed copy would write back a valid file with all of that deleted --
    the kernel silently destroying the one document in the project nothing else rewrites, which is
    the reason `presets._with_preset` is a line edit too. So: every line the file had before is
    still there afterwards, and a second rule appends beside the first instead of replacing it.
    """
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from kernel import filing
    from kernel.state import ProjectState

    root = _office_state(tmp_path)
    state = ProjectState(root)
    kept = [line for line in filing.read_text(filing.plan_path(state)).splitlines()
            if line.strip() and line.strip() != "rules: []"]
    first = _approved_rule(state)
    filing.apply(state, first)
    second = _approved_rule(state, rule_id="FP-010", path_template="archive/vertraege/<jahr>/")
    filing.apply(state, second)
    after = filing.read_text(filing.plan_path(state))
    missing = [line for line in kept if line not in after]
    assert not missing, ("the append deleted lines of a document nothing else can rewrite: %s"
                         % missing)
    assert filing.existing_rules(state) == [filing.rule_from(second), filing.rule_from(first)]


def test_a_plan_this_kernel_cannot_append_to_is_refused_and_left_alone(tmp_path):
    """Fail-closed on a shape the writer cannot place a rule in, rather than rewriting the file.

    Two shapes stand for the class: no `rules:` key at all, and a NON-empty flow list -- legal YAML
    this line editor cannot extend without re-emitting the whole value. In both the plan has to come
    back byte-identical: a document the kernel half-understands is one it must not touch, and the
    refusal points at the user rather than at a retry.
    """
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from kernel import filing
    from kernel.state import ProjectState, StateError

    root = _office_state(tmp_path)
    state = ProjectState(root)
    approved = _approved_rule(state)
    for text in ("# an Aktenplan with no rules key at all\nretention: 8y\n",
                 "rules: [{id: FP-001, path_template: archive/x/}]\n"):
        with open(filing.plan_path(state), "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        with pytest.raises(StateError):
            filing.apply(state, approved)
        assert filing.read_text(filing.plan_path(state)) == text, text


def test_the_question_a_filing_rule_asks_shows_every_field_the_hash_covers(tmp_path):
    """DEC-0048 in its constructive direction: no key in the hash the question does not show.

    The reader is BUG-0041's user, and this question decides where every FUTURE document of a class
    goes -- so it is measured against the manifest itself rather than against a remembered wording:
    every hashed value appears in the question text, and the question is deterministic from the
    request (the approval gate rebuilds it and compares byte for byte).
    """
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from kernel import approvals
    from kernel.state import ProjectState

    root = _office_state(tmp_path)
    state = ProjectState(root)
    manifest = approvals.filing_rule_subject_manifest(**_rule_flags())
    request = approvals.create_pending_request(
        state, "filing_rule", manifest=manifest,
        approval_expires=time.time() + approvals.LINE_APPROVAL_VALIDITY)
    question = approvals.build_question(request)["question"]
    for key, value in (request.get("subject_manifest") or {}).items():
        if key == approvals.EXPIRY_FIELD:
            continue              # rendered as a date by `_render_manifest_value`, not as its float
        for shown in (value if isinstance(value, list) else [value]):
            assert str(shown) in question, (
                "the hash covers %s=%r and the question does not show it:\n%s"
                % (key, shown, question))
    assert approvals.build_question(request)["question"] == question, "not deterministic"


def test_a_write_that_does_not_produce_the_approved_rule_is_rolled_back(tmp_path, monkeypatch):
    """The line edit is a TEXT operation, and the only proof it produced the approved rule is a parse.

    TWO ABLATIONS, and the second is this round's B4. Making the RENDERER lie -- it drops one field
    -- is the shape a quoting, indentation or line-ending bug really has. Mangling `rule_from` is
    the shape the check could NOT see while it compared against that same function: the verifier's
    `id + "-typo"` ablation left the suite green while the plan received a rule nobody signed. The
    read-back now compares against `signed_rule(manifest)` -- the manifest's own values, through
    `RULE_FIELDS`, with no transformation in it -- so both ablations are caught here.

    What must happen is what `presets.record_preset` does one document over: the plan comes back
    byte-identical and the command refuses, because a plan carrying a rule the user never saw is
    worse than no rule at all.
    """
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from kernel import filing
    from kernel.state import ProjectState, StateError

    root = _office_state(tmp_path)
    state = ProjectState(root)
    approved = _approved_rule(state)
    before = filing.read_text(filing.plan_path(state))
    honest_rendered, honest_rule_from = filing._rendered, filing.rule_from
    for what, patch in (
            ("the renderer drops a field",
             lambda: monkeypatch.setattr(
                 filing, "_rendered",
                 lambda rule: honest_rendered({k: v for k, v in rule.items()
                                               if k != "retention"}))),
            ("the builder mangles the id (verifier ablation, B4)",
             lambda: monkeypatch.setattr(
                 filing, "rule_from",
                 lambda manifest: dict(honest_rule_from(manifest),
                                       id=str(manifest["rule_id"]) + "-typo")))):
        monkeypatch.undo()
        patch()
        with pytest.raises(StateError) as exc:
            filing.apply(state, approved)
        assert "did not produce a plan that carries exactly what the user approved" in str(exc.value), what
        assert filing.read_text(filing.plan_path(state)) == before, (
            "%s: the plan was left changed" % what)
    monkeypatch.undo()
    assert filing.apply(state, approved)["rule"] == filing.signed_rule(approved), (
        "the honest path still writes the approved rule")


@pytest.mark.parametrize("template,why", [
    ("<Bereich>/<Jahr>/", "the shape a role really proposes"),
    ("<x>", "a single placeholder segment"),
    ("<a>/finance/2026/", "a placeholder first, literals below it"),
    ("prefix<a>/2026/", "a placeholder anywhere IN the first segment"),
])
def test_a_rule_may_not_start_with_a_placeholder(tmp_path, template, why):
    """A `path_template` that BEGINS with a placeholder names no tray and matches the whole level.

    `gate_filing` translates every `<...>` into "a run of characters inside one segment", so a rule
    whose FIRST segment is one matches every directory at that depth -- including the archive
    folders no rule was ever written for. Measured 2026-08-21 against the shipped gate with `<a>/<b>`
    minted into the plan: `mv inbox/rechnung.pdf archive/erfunden/x.pdf` went from rc 2 to rc 0, i.e.
    the wall was gone for the whole level. That consequence is measured on the running gate by
    `test_a_rule_that_starts_with_a_placeholder_would_open_the_whole_level` (in
    `tools/test_hooks.py`), so this refusal's REASON cannot quietly stop being true either.

    The chain runs inside ONE session, which is what makes this blocking rather than untidy: a role
    proposes `<Bereich>/<Jahr>`, the approval question renders it beside the plan's own examples, and
    the reader BUG-0041 describes signs a wildcard. So the refusal happens where the subject is
    BUILT -- before a question exists at all -- and not at the write.

    IT IS A DEFINITION, NOT A SECOND PARSER of the placeholder syntax: the first segment must carry
    no `<` and no `>`, and every reading of every syntax agrees about a segment that contains
    neither.
    """
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from kernel import approvals

    with pytest.raises(approvals.ApprovalError) as exc:
        approvals.filing_rule_subject_manifest(**_rule_flags(path_template=template))
    assert "placeholder" in str(exc.value), why
    # ...and the German half the USER would have read, because that is the half BUG-0041 is about
    assert "Platzhalter" in (exc.value.user_text or ""), why


@pytest.mark.parametrize("template", [
    "archive/finance/<year>/",           # the shipped example shape
    "archive/<Modell>_<Prozessor>/",     # placeholders below a literal root
    "outbox/<year>/",                    # a literal root that is NOT the archive
])
def test_a_literal_first_segment_is_accepted_however_deep_the_placeholders_go(tmp_path, template):
    """The floor under the refusal above: it must not have become "no placeholders at all".

    The third case is deliberate and is the honest limit of what the kernel checks: a rule rooted
    somewhere other than the filing tray is ACCEPTED here, because which directory is the archive is
    the KIT's fact and not the kernel's. Such a rule matches nothing -- `gate_filing` only asks its
    question about a destination that lands in the archive -- so it is an unusable rule, not an open
    wall, and the difference between those two is the whole point of the refusal above.
    """
    import sys as _sys

    _sys.path.insert(0, TEAM_KITS_DIR)
    from kernel import approvals

    manifest = approvals.filing_rule_subject_manifest(**_rule_flags(path_template=template))
    assert manifest["path_template"] == template.rstrip("/")

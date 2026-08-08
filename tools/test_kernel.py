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

    RED the moment a module joins one of those names onto a path again -- which is what all four
    of the occurrences above did, and what no amount of care has stopped so far.
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
    assert dispatch.sweep_expired_leases(state) == []
    reported = dispatch.live_leases(state)
    assert [entry[0] for entry in reported] == [task_id]
    assert 0 < reported[0][1] <= 120.0


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

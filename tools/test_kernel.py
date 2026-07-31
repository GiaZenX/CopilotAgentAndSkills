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

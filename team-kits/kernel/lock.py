r"""Cross-process state-kernel lock (HARNESS_V2_SPEC.md II.4 "Nebenlaeufigkeit & Locking").

The kernel's single-writer guarantee across sessions/processes. Verified primitives
(spike S1, 2026-07-24, Python 3.13/win32 + POSIX semantics):

- acquire  = atomic O_CREAT|O_EXCL lockfile create (second acquire -> FileExistsError)
- scope    = callers hold the lock across item write AND index regeneration
- stale-break: a lock past its TTL is taken over -- but only after re-reading the
  lockfile to prove it did not change between checks, and via an atomic os.replace
  claim so two waiters can never both break it (and never break a FRESH lock)
- long paths: every file op goes through extended-length (\\?\) paths on Windows
- a session that cannot get the lock waits/retries -- it never silently skips

Fail-closed message discipline (spec II.13): every raised error names the lockfile
and the one concrete remedy.
"""
from __future__ import annotations

import json
import math
import os
import socket
import sys
import time
import uuid


LOCK_SCHEMA_VERSION = 1
_DEFAULT_NAME = ".kernel.lock"


def ext_path(path: str) -> str:
    r"""Return an extended-length (\\?\) absolute path on Windows; identity elsewhere.

    Spec II.4: the kernel uses extended-length paths for open/replace so deep
    staging/archive trees (>260 chars) cannot break state operations (spike S1e/f).
    """
    if sys.platform != "win32":
        return path
    p = os.path.abspath(path)
    if p.startswith("\\\\?\\"):
        return p
    if p.startswith("\\\\"):  # UNC share -> \\?\UNC\server\share\...
        return "\\\\?\\UNC" + p[1:]
    return "\\\\?\\" + p


def _retry_sharing_violation(op, attempts: int = 50, delay: float = 0.01):
    """Ride out Windows sharing-violation windows (a polling waiter holding the
    file open for read makes remove/replace fail with PermissionError; pending
    deletes make creates fail the same way). Only PermissionError is retried --
    every other error raises immediately."""
    for attempt in range(attempts):
        try:
            return op()
        except PermissionError:
            if attempt == attempts - 1:
                raise
            time.sleep(delay)


class LockTimeout(TimeoutError):
    """Raised when the lock could not be acquired within the timeout."""


class LockLost(RuntimeError):
    """Raised on release when the lockfile no longer carries our token.

    Meaning: our TTL expired and another process legitimately broke the lock --
    the caller's writes may have raced and MUST be re-validated.
    """


class KernelLock:
    """Context-manager lock over one state directory (usually project_memory/)."""

    def __init__(
        self,
        lock_dir: str,
        ttl: float = 60.0,
        name: str = _DEFAULT_NAME,
        timeout: float = 30.0,
        poll: float = 0.25,
    ):
        self.lock_dir = os.path.abspath(lock_dir)
        self.lock_path = os.path.join(self.lock_dir, name)
        self.ttl = float(ttl)
        self.timeout = float(timeout)
        self.poll = float(poll)
        self._token = uuid.uuid4().hex
        self._held = False

    # -- public API -----------------------------------------------------------

    @property
    def held(self) -> bool:
        return self._held

    def acquire(self, timeout: float = None, poll: float = None) -> "KernelLock":
        """Block until acquired (wait/retry -- never silently skip) or LockTimeout."""
        timeout = self.timeout if timeout is None else float(timeout)
        poll = self.poll if poll is None else float(poll)
        deadline = time.monotonic() + max(0.0, timeout)
        while True:
            if self._try_acquire():
                return self
            self._maybe_break_stale()
            if time.monotonic() >= deadline:
                raise LockTimeout(
                    "kernel lock busy: %s (holder: %s). Remedy: wait for the other "
                    "kernel operation to finish, or run `python scripts/harness.py doctor` to inspect "
                    "held/stale locks." % (self.lock_path, self._describe_holder())
                )
            time.sleep(poll)

    def release(self) -> None:
        """Release the lock; raise LockLost if it was broken while we held it."""
        if not self._held:
            return
        self._held = False
        payload = self._read_payload()
        if payload is None or payload.get("token") != self._token:
            raise LockLost(
                "kernel lock %s was taken over while held (our TTL of %ss expired). "
                "Writes made under this lock may have raced. Remedy: run the state "
                "validator (`python scripts/harness.py validate`) before continuing."
                % (self.lock_path, self.ttl)
            )
        try:
            _retry_sharing_violation(lambda: os.remove(ext_path(self.lock_path)))
        except FileNotFoundError:
            pass

    def __enter__(self) -> "KernelLock":
        return self.acquire()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()

    # -- internals ------------------------------------------------------------

    def _try_acquire(self) -> bool:
        try:
            fd = os.open(
                ext_path(self.lock_path),
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            )
        except FileExistsError:
            return False
        except PermissionError:
            # Windows pending-delete window (another party just removed/replaced
            # the lockfile): transient -- report busy, the acquire loop retries
            return False
        except FileNotFoundError:
            raise RuntimeError(
                "kernel lock dir missing: %s. Remedy: run the kernel inside an "
                "initialized project (the state directory must exist) or create "
                "the directory first." % self.lock_dir
            ) from None
        try:
            payload = {
                "lock_schema_version": LOCK_SCHEMA_VERSION,
                "pid": os.getpid(),
                "host": socket.gethostname(),
                "token": self._token,
                "acquired_at": time.time(),
                "ttl": self.ttl,
            }
            os.write(fd, json.dumps(payload, sort_keys=True).encode("utf-8"))
        finally:
            os.close(fd)
        self._held = True
        return True

    def _read_payload(self):
        try:
            with open(ext_path(self.lock_path), "rb") as fh:
                return json.loads(fh.read().decode("utf-8"))
        except (OSError, ValueError):
            return None

    def _describe_holder(self) -> str:
        payload = self._read_payload()
        if not payload:
            return "unreadable"
        return "pid %s on %s, age %.1fs, ttl %ss" % (
            payload.get("pid"),
            payload.get("host"),
            max(0.0, time.time() - float(payload.get("acquired_at", 0))),
            payload.get("ttl"),
        )

    def _maybe_break_stale(self) -> None:
        """Take over an EXPIRED lease -- atomically, never a fresh lock.

        The lock is a LEASE: holders write the lockfile once at acquire and
        never renew it; expiry is judged solely from the HOLDER's declared ttl
        (its payload) against acquired_at (corrupt payload: mtime + our ttl).
        Break protocol (phase0-disposition S1 footnote, hardened per
        Fable-Check 4/BUG-1):
        1. read payload + mtime; only an expired lease qualifies
        2. wait a beat, re-read -- byte+mtime identity proves no other waiter
           broke/restored the file in between
        3. claim via os.replace to a contender-unique name (exactly one waiter
           wins; losers see FileNotFoundError and retry acquire)
        4. CAPTURE VERIFICATION: read the claimed file and compare to the
           proven stale bytes -- if a FRESH lock slipped in between step 2 and
           step 3, restore it via exclusive create (never clobbering an even
           newer one) and back off.
        Failed cleanups leave `.stale-*` remnants for `python scripts/harness.py doctor`.
        Clock skew (acquired_at in the future) never breaks -- doctor territory.
        """
        lock = ext_path(self.lock_path)
        try:
            first = self._read_raw(lock)
        except FileNotFoundError:
            return  # released meanwhile -- retry acquire
        if first is None:
            return
        raw1, mtime1 = first
        age, limit = self._staleness(raw1, mtime1)
        if age <= limit:
            return
        time.sleep(0.05)
        try:
            second = self._read_raw(lock)
        except FileNotFoundError:
            return
        if second is None or second[0] != raw1 or second[1] != mtime1:
            return  # changed between reads -> not provably abandoned
        broken = ext_path(
            self.lock_path + ".stale-%s-%s" % (os.getpid(), uuid.uuid4().hex[:8])
        )
        try:
            _retry_sharing_violation(lambda: os.replace(lock, broken))
        except (FileNotFoundError, OSError):
            return  # another waiter won the break -- fine
        try:
            with open(broken, "rb") as fh:
                captured = fh.read()
        except OSError:
            captured = None
        if captured != raw1:
            # we captured something OTHER than the proven stale lock (a fresh
            # lock created between proof and claim) -- restore it without
            # clobbering any even newer lock at the path
            if captured is not None:
                def _restore():
                    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    try:
                        os.write(fd, captured)
                    finally:
                        os.close(fd)
                try:
                    _retry_sharing_violation(_restore)
                    _retry_sharing_violation(lambda: os.remove(broken))
                except FileExistsError:
                    pass  # path re-locked meanwhile: remnant stays for doctor
                except OSError:
                    pass
            return
        try:
            os.remove(broken)
        except OSError:
            pass

    @staticmethod
    def _read_raw(ext_lock_path: str):
        try:
            with open(ext_lock_path, "rb") as fh:
                raw = fh.read()
            mtime = os.stat(ext_lock_path).st_mtime
        except FileNotFoundError:
            raise
        except OSError:
            return None
        return raw, mtime

    def _staleness(self, raw: bytes, mtime: float):
        """Return (age_seconds, ttl_limit), honoring the HOLDER's declared ttl."""
        try:
            payload = json.loads(raw.decode("utf-8"))
            age = time.time() - float(payload["acquired_at"])
            limit = float(payload.get("ttl", self.ttl))
            if not (math.isfinite(age) and math.isfinite(limit)):
                # NaN would make the lease instantly breakable, Infinity would
                # block forever -- treat non-finite payloads as corrupt instead
                # (Fable-Check 4 delta, NIT-NEU)
                raise ValueError("non-finite lock payload values")
            return age, limit
        except (ValueError, KeyError, TypeError):
            # corrupt lockfile: fail-closed on content, but an abandoned corrupt
            # lock must still expire -- judge age by mtime against our own ttl
            return time.time() - mtime, self.ttl

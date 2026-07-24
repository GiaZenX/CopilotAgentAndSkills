"""State-kernel core operations (HARNESS_V2_SPEC.md II.4) -- step 1.4a.

The kernel is the ONLY writer of canonical project state. Every operation:
- runs under the cross-process KernelLock (item write AND index regeneration
  inside the same hold -- no second inconsistent state)
- writes atomically (temp file + os.replace, extended-length paths)
- allocates ids itself (max-scan over active+archive under the lock;
  callers never pick ids)
- enforces the status automata (`transition` is the only status writer)
- invalidates approvals atomically when hashed fields change
  (revision +1, approval_ref cleared, status -> INVALIDATION_TARGET)

Later steps add: approvals/dispatch/submit-result (1.4b), session brief /
validate / doctor (1.4c). PyYAML is fine here (kernel ops, not hook hot path).

Interim notes (Fable-Check 7):
- update_item does not yet reject UNKNOWN extra fields -- the 1.4c validator
  closes that (full schemas over the reference graph)
- ProjectState/KernelLock instances are NOT thread-safe when shared: use one
  instance per thread/operation (the lockFILE serializes across them)
- archive() is two-phase (archive write, then active remove): a crash in
  between leaves the item in both places -- harmless for id max-scan,
  flagged by validate/doctor (1.4c)
"""
from __future__ import annotations

import os
import time

import yaml

from .backlog_types import (
    ACTIVE_DIRS,
    HASHED_FIELDS,
    REQUIRED_FIELDS,
    TransitionError,
    assert_transition,
    format_id,
    initial_status,
    invalidation_target,
    is_terminal,
    parse_id,
)
from .lock import KernelLock, ext_path

_KERNEL_SET = ("id", "status", "revision", "approval_ref", "created")


class StateError(ValueError):
    """Canonical-state operation refused -- message carries the remedy."""


class ProjectState:
    """All operations on one project_memory/ directory."""

    def __init__(self, root: str, lock_ttl: float = 60.0):
        self.root = os.path.abspath(root)
        self.lock = KernelLock(self.root, ttl=lock_ttl)

    # -- paths -----------------------------------------------------------------

    def active_dir(self, item_type: str) -> str:
        try:
            return os.path.join(self.root, *ACTIVE_DIRS[item_type].split("/"))
        except KeyError:
            raise StateError(
                "unknown item type %r. Remedy: use one of %s."
                % (item_type, "/".join(sorted(ACTIVE_DIRS)))
            ) from None

    def active_path(self, item_id: str) -> str:
        item_type, _ = parse_id(item_id)
        return os.path.join(self.active_dir(item_type), item_id + ".yaml")

    def archive_path(self, item_id: str, year: int) -> str:
        item_type, _ = parse_id(item_id)
        # deterministic archive paths (spec II.2): archive/<type>/<year>/<ID>.yaml
        return os.path.join(self.root, "archive", item_type, str(year), item_id + ".yaml")

    # -- io (always under the lock) --------------------------------------------

    @staticmethod
    def _read_yaml(path: str):
        with open(ext_path(path), encoding="utf-8") as fh:
            return yaml.safe_load(fh)

    @staticmethod
    def _write_yaml_atomic(path: str, data: dict) -> None:
        directory = os.path.dirname(path)
        os.makedirs(ext_path(directory), exist_ok=True)
        tmp = path + ".tmp-%s" % os.getpid()
        with open(ext_path(tmp), "w", encoding="utf-8", newline="\n") as fh:
            yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True)
        os.replace(ext_path(tmp), ext_path(path))

    def read_item(self, item_id: str) -> dict:
        path = self.active_path(item_id)
        try:
            item = self._read_yaml(path)
        except FileNotFoundError:
            raise StateError(
                "no active item %s (expected at %s). Remedy: check the id via "
                "generated/index.yaml; archived items live under archive/."
                % (item_id, path)
            ) from None
        if not isinstance(item, dict) or item.get("id") != item_id:
            raise StateError(
                "corrupt item file for %s at %s (id mismatch or non-mapping). "
                "Remedy: `git restore %s` then `harness generate-index`."
                % (item_id, path, os.path.relpath(path, self.root))
            )
        return item

    # -- id allocation ---------------------------------------------------------

    def _max_number(self, item_type: str) -> int:
        highest = 0
        scan_dirs = [self.active_dir(item_type),
                     os.path.join(self.root, "archive", item_type)]
        for base in scan_dirs:
            if not os.path.isdir(ext_path(base)):
                continue
            for _dir, _subdirs, files in os.walk(ext_path(base)):
                for name in files:
                    stem = name[:-5] if name.endswith(".yaml") else name
                    try:
                        found_type, number = parse_id(stem)
                    except ValueError:
                        continue
                    if found_type == item_type:
                        highest = max(highest, number)
        return highest

    def allocate_id(self, item_type: str) -> str:
        """Next id by max-scan over active+archive -- call ONLY under the lock."""
        return format_id(item_type, self._max_number(item_type) + 1)

    # -- operations ------------------------------------------------------------

    def capture(self, item_type: str, fields: dict) -> dict:
        """Create a new item: kernel assigns id/status/revision/approval_ref/created."""
        if item_type not in REQUIRED_FIELDS:
            raise StateError(
                "capture does not handle type %r (ARC/WFR go through the "
                "promotion path; APR through approve). Remedy: use one of %s."
                % (item_type, "/".join(sorted(REQUIRED_FIELDS)))
            )
        provided_kernel_fields = [k for k in _KERNEL_SET if k in fields]
        if provided_kernel_fields:
            raise StateError(
                "fields %s are kernel-set and must not be provided on capture. "
                "Remedy: drop them; the kernel assigns id/status/revision/"
                "approval_ref/created." % ", ".join(provided_kernel_fields)
            )
        missing = [k for k in REQUIRED_FIELDS[item_type] if k not in fields]
        if missing:
            raise StateError(
                "capture %s is missing required fields: %s (spec II.2 "
                "Pflichtfelder). Remedy: provide every listed field."
                % (item_type, ", ".join(missing))
            )
        with self.lock:
            item_id = self.allocate_id(item_type)
            item = {"id": item_id}
            item.update(fields)
            if item_type in _AUTOMATON_TYPES:
                item["status"] = initial_status(item_type)
            elif item_type in _NON_AUTOMATON_INITIAL_STATUS:
                item["status"] = _NON_AUTOMATON_INITIAL_STATUS[item_type]
            # EVD deliberately gets NO status: Evidence never carries its own
            # project status (spec II.2)
            item["revision"] = 1
            item["approval_ref"] = None
            item["created"] = _now_iso()
            # note: this writes the item file and thereby creates the TYPE
            # subdirectory -- item io, not state scaffolding (the state ROOT
            # must already exist; only the installer bootstrap creates it)
            self._write_yaml_atomic(self.active_path(item_id), item)
            self._regenerate_index_locked()
            return item

    def update_item(self, item_id: str, changes: dict) -> dict:
        """Edit an item through the kernel. Changing a hashed field of an item
        with a current approval invalidates it ATOMICALLY (spec II.2)."""
        with self.lock:
            return self._update_item_locked(item_id, changes)

    def _update_item_locked(self, item_id: str, changes: dict) -> dict:
        """update_item body for callers that ALREADY hold the lock (the lock is
        not reentrant); e.g. staging.freeze_design keeps read+update in ONE hold
        (Fable-Check 11/BUG-1: no lost-update window)."""
        item_type, _ = parse_id(item_id)
        forbidden = [k for k in changes if k in ("id", "status", "revision", "approval_ref", "created")]
        if forbidden:
            raise StateError(
                "fields %s change only through their kernel operations "
                "(transition/approve). Remedy: use the dedicated command."
                % ", ".join(forbidden)
            )
        item = self.read_item(item_id)
        hashed = set(HASHED_FIELDS.get(item_type, ()))
        touches_hashed = any(
            key in hashed and item.get(key) != value
            for key, value in changes.items()
        )
        item.update(changes)
        if touches_hashed and item.get("approval_ref"):
            item["revision"] = int(item.get("revision", 1)) + 1
            item["approval_ref"] = None
            item["status"] = invalidation_target(item_type)
        self._write_yaml_atomic(self.active_path(item_id), item)
        self._regenerate_index_locked()
        return item

    def transition(self, item_id: str, to_status: str, approved_retry: bool = False) -> dict:
        item_type, _ = parse_id(item_id)
        with self.lock:
            item = self.read_item(item_id)
            from_status = item.get("status")
            assert_transition(item_type, from_status, to_status)
            if item_type == "TSK" and from_status == "FAILED" and to_status == "READY" \
                    and not approved_retry:
                raise TransitionError(
                    "TSK FAILED -> READY requires an approved retry (spec II.2 "
                    "Querregeln). Remedy: obtain the retry approval, then call "
                    "transition with approved_retry=True."
                )
            item["status"] = to_status
            self._write_yaml_atomic(self.active_path(item_id), item)
            self._regenerate_index_locked()
            return item

    def archive(self, item_id: str) -> str:
        """Move a TERMINAL item to archive/<type>/<year>/ (never delete)."""
        item_type, _ = parse_id(item_id)
        with self.lock:
            item = self.read_item(item_id)
            if item_type in _AUTOMATON_TYPES and not is_terminal(item_type, item.get("status")):
                raise StateError(
                    "%s is %s -- only terminal items are archived (spec II.2). "
                    "Remedy: finish the lifecycle first, or CANCEL/REJECT it "
                    "via transition." % (item_id, item.get("status"))
                )
            item["closed_at"] = _now_iso()
            year = int(item["closed_at"][:4])
            target = self.archive_path(item_id, year)
            self._write_yaml_atomic(target, item)
            os.remove(ext_path(self.active_path(item_id)))
            self._regenerate_index_locked()
            return target

    # -- generated index (atomic within the state operation, spec II.4) --------

    def generate_index(self) -> str:
        with self.lock:
            return self._regenerate_index_locked()

    def _regenerate_index_locked(self) -> str:
        rows = []
        for item_type in sorted(ACTIVE_DIRS):
            base = self.active_dir(item_type)
            if not os.path.isdir(ext_path(base)):
                continue
            for name in sorted(os.listdir(ext_path(base))):
                if not name.endswith(".yaml"):
                    continue
                try:
                    item = self._read_yaml(os.path.join(base, name))
                except Exception:
                    item = None
                if not isinstance(item, dict):
                    rows.append({"id": name[:-5], "type": item_type, "corrupt": True})
                    continue
                row = {
                    "id": item.get("id", name[:-5]),
                    "type": item_type,
                    "title": item.get("title"),
                    "status": item.get("status"),
                    "revision": item.get("revision"),
                    "approval_ref": item.get("approval_ref"),
                }
                if item.get("blocked_by"):
                    row["blocked_by"] = item["blocked_by"]
                rows.append(row)
        index_path = os.path.join(self.root, "generated", "index.yaml")
        self._write_yaml_atomic(index_path, {"generated_at": _now_iso(), "items": rows})
        return index_path


_AUTOMATON_TYPES = frozenset(
    ("PR", "RQ", "FR", "CR", "BUG", "SR", "TSK", "PROC", "HYP", "EXP")
)

# status-bearing types WITHOUT an automaton (spec II.2 Pflichtfelder):
# Decision starts VALID (VALID|SUPERSEDED); INV starts `unverified` -- it only
# becomes verified once its referenced check test exists and is collectable
# (spec II.2 INV.check / review B.2-10)
_NON_AUTOMATON_INITIAL_STATUS = {"DEC": "VALID", "INV": "unverified"}


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")

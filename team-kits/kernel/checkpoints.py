"""Resumable progress a successor MAY adopt -- after verification (DEC-0044, BUG-0042).

WHAT THIS IS FOR. A subagent is a child of the session that asked for it, so a session break kills
every dispatch in flight. Pilot 3 lost three specialists that way and re-paid each of them from
zero: the bookkeeping was honest, but there was no artifact a successor could pick up. A checkpoint
is that artifact -- the running specialist's own record of where it got to, in a place a successor
can find without being told.

WHERE IT LIVES, and the reason is the running gates rather than taste: `project_memory/` is
canonical state and the kernel is its only writer (`gate_write_scope` refuses every tool write into
it), while `project_memory/staging/<item-id>/` is the open proposal area -- what is proposed there
is explicitly NOT state (spec II.4). A checkpoint is a proposal about progress, not a fact about the
project, so it belongs there; and it needs no pointer kept anywhere, because its location is
DERIVED from the task id (`checkpoint_path`) rather than recorded.

WHO WRITES IT, and how far that goes. The kernel, through `record`, because the two fields adoption
later rests on -- the digest over the task's `expected_outputs` and the digest of every named
artefact -- are MEASURED there rather than claimed by the caller. That is a property of the ROUTE and
not a wall around the file: the same staging directory is the one place a dispatched specialist may
write with its own tools, so a hand-written `checkpoint.yaml` in the shape of this schema is possible
and WILL be read. Every rule adoption rests on is therefore enforced a SECOND time in `verify`, on
the record as found -- containment of each artefact path (`contained_artifact`) and the refusal of a
record that measures nothing at all. Both were measured missing on 2026-08-15, and both let a
hand-written record verify: one pointing outside the project, one pointing at nothing.

What no route and no wall can decide is whether the note beside an output is TRUE. That stays the
successor's job, and the verdict text says so instead of letting "verified" be read as "correct".

WHAT VERIFICATION MEASURES, and what it deliberately does not. DEC-0044 names the risk in so many
words -- "a checkpoint that verifies but is semantically stale can still mislead a successor" -- so
`verify` compares against the TASK CONTRACT and not just against the files:

  * identity      -- the record is this task's,
  * contract      -- the task's `expected_outputs` still hash to what the run was measured against,
                     and neither the task's own revision nor its root's has moved since,
  * artefacts     -- every file the record names still exists and still carries the bytes that were
                     measured when it was written.

What NOTHING here measures is whether the work is any GOOD, or whether the note beside an output is
true. That stays the successor's job, and every message this module produces says so rather than
letting "verified" be read as "correct". An unverified or failing checkpoint is treated as ABSENT --
adoption is earned, never assumed -- and re-ordering from scratch remains the fallback.
"""
from __future__ import annotations

import hashlib
import os
import time

from .backlog_types import field_elements, parse_id
from .hashing import canonical_json
from .lock import ext_path
from .presets import repo_root
from .schemas import validate
from .staging import staging_dir
from .state import STAGING_DIRNAME, ProjectState, StateError, _now_iso

CHECKPOINT_FILENAME = "checkpoint.yaml"
# The fields `record` MEASURES and a caller may therefore not send. Same doctrine as
# `state._KERNEL_SET`: a value the kernel computes is not a value the supervised party offers.
KERNEL_MEASURED = ("task_id", "recorded", "recorded_epoch", "task_revision", "root_revision",
                   "expected_outputs_digest")
# How far along ONE expected output is. A vocabulary, so it is written down rather than derived --
# and it is enforced HERE and not in the schema, because the schema validator checks the PRESENCE
# of an entry's keys and not their values (`schemas._check_field`, list branch). Nothing in the
# harness decides anything on the difference: it is what the successor reads to know whether the
# output still needs work. Kept enforced rather than described by
# `test_a_checkpoint_progress_word_outside_the_vocabulary_is_refused` (test_approvals_dispatch).
PROGRESS_STATES = ("partial", "complete")


class CheckpointError(StateError):
    """A checkpoint could not be recorded -- fail-closed, the message carries the remedy."""


def checkpoint_path(state: ProjectState, task_id: str) -> str:
    """Where this task's checkpoint lives -- DERIVED from the id, never recorded anywhere.

    Through `staging.contained_child` for the reason that function exists: the id arrives from a
    command line, and a path composed from a caller's string is a path that can leave the tree.
    """
    parse_id(task_id)          # a checkpoint belongs to an ITEM; a free-text key has no contract
    return os.path.join(staging_dir(state, task_id), CHECKPOINT_FILENAME)


def state_relative(state: ProjectState, path: str) -> str:
    """`path` as the session brief spells a staging pointer -- state-relative, forward slashes."""
    return os.path.relpath(path, state.root).replace(os.sep, "/")


def expected_outputs_digest(task: dict) -> str:
    """The digest of the contract a run was measured against.

    Over `expected_outputs` alone, because that is the field DEC-0044 names: it is what the task
    promised to produce, so a change to it means the successor would be adopting progress towards
    something else. Normalised through `field_elements` for the reason `_criteria_ids` is -- a
    scalar and a one-element list are the same contract and must not hash differently.
    """
    return _digest(canonical_json([str(one) for one in field_elements(task.get("expected_outputs"))]))


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def contained_artifact(project_root: str, artifact: str):
    """The absolute path of an artefact that really stays under `project_root`, else None.

    THE CHOKEPOINT FOR EVERY ARTEFACT PATH, on BOTH sides -- `record` composes it from a caller's
    string and `verify` re-reads it out of a file the checked party may have written by hand. It is
    `staging.contained_child`'s argument applied to a MULTI-segment path: that function refuses
    anything but one segment, so it cannot serve here, and the containment test below is the same
    realpath comparison it makes.

    THE HOLE THIS CLOSES, measured 2026-08-15 in a scaffolded project: with no check at all,
    `../outside-secret.txt`, `../../Windows/win.ini`, `C:\\Windows\\win.ini` and `/c/Windows/win.ini`
    were all recorded rc 0 and then VERIFIED cleanly -- so a checkpoint could point the successor,
    whom the constitution tells to read and judge it, at a file outside the project. Absolute is
    refused before the join because `os.path.join` lets an absolute second argument replace the
    first; `..` and a link that spells one place and leads to another are both caught by realpath.
    `test_a_checkpoint_artefact_outside_the_project_is_refused_and_never_verified` is the red test.
    """
    text = str(artifact or "").replace("\\", "/")
    drive, rest = os.path.splitdrive(text)
    # A PATH THAT NAMES A ROOT IS NOT PROJECT-RELATIVE, and the test is the two ways of naming one
    # rather than `os.path.isabs`: since Python 3.13 `ntpath.isabs("/Windows/win.ini")` is False, so
    # the join would have RE-ROOTED that word into the project silently instead of refusing it --
    # contained, but no longer the path anybody wrote. A drive spec (`C:x` too, which is
    # drive-RELATIVE and which `ntpath.join` lets replace the first argument outright) goes the same
    # way.
    if not rest or drive or rest.startswith("/"):
        return None
    target = os.path.join(project_root, *[part for part in rest.split("/") if part])
    try:
        resolved = os.path.realpath(ext_path(target))
        container = os.path.realpath(ext_path(project_root))
    except OSError:
        return None
    if resolved != container and not resolved.startswith(container + os.sep):
        return None
    return target


def _file_digest(path: str):
    """(sha256, bytes) of a file, or None when it cannot be read at all.

    Chunked, like `staging._file_hash` and for its reason: an artefact is whatever the run produced,
    and reading one whole into memory turns a large build output into a MemoryError inside a
    verification that runs at every dispatch."""
    if path is None:
        return None
    digest, size = hashlib.sha256(), 0
    try:
        with open(ext_path(path), "rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
                size += len(chunk)
    except OSError:
        return None
    return digest.hexdigest(), size


def record(state: ProjectState, task_id: str, body: dict) -> dict:
    """Write this task's checkpoint into its staging directory; returns the stored record.

    REFUSED, each because the record would otherwise claim something nothing backs:
      * a task that is not in a lease-bearing status -- a checkpoint describes a dispatch in
        flight, and one written outside a dispatch belongs to no run,
      * an entry whose `output_index` names no expected output of the task,
      * an entry that names no artefact -- a claim of progress with nothing on disk behind it is
        prose, and `verify` could never do anything but believe it,
      * an artefact that does not exist under the repo root.
    """
    if not isinstance(body, dict):
        raise CheckpointError("the checkpoint body must be a JSON object. Remedy: send "
                              "{\"next_step\": ..., \"outputs\": [...]} on stdin.")
    offered = [name for name in KERNEL_MEASURED if name in body]
    if offered:
        raise CheckpointError(
            "%s is measured by the kernel, not sent by the caller -- a checkpoint whose own "
            "integrity data came from the party being checked would verify itself. Remedy: drop "
            "%s from the body." % (", ".join(offered), "it" if len(offered) == 1 else "them"))
    # deferred: `dispatch` imports nothing from here at module level either (see `create_lease`),
    # so the two stay a pair of leaves rather than a cycle
    from .dispatch import LEASE_BEARING_STATUSES

    with state.lock:
        task = state.read_item(task_id)
        if task.get("status") not in LEASE_BEARING_STATUSES:
            raise CheckpointError(
                "%s is %s -- a checkpoint records a dispatch IN FLIGHT, and outside %s there is no "
                "run for it to describe. Remedy: record it while the task is dispatched; a "
                "finished run hands its work back through `python scripts/harness.py "
                "submit-result`." % (task_id, task.get("status"), "/".join(LEASE_BEARING_STATUSES)))
        root = state.read_item(task["product_requirement"])
        outputs = _measured_outputs(state, task, body.get("outputs"))
        checkpoint = {
            "task_id": task_id,
            "recorded": _now_iso(),
            "recorded_epoch": time.time(),
            "task_revision": int(task.get("revision") or 0),
            "root_revision": int(root.get("revision") or 0),
            "expected_outputs_digest": expected_outputs_digest(task),
            "next_step": str(body.get("next_step") or ""),
            "outputs": outputs,
        }
        validate(checkpoint, "checkpoint")
        path = checkpoint_path(state, task_id)
        os.makedirs(ext_path(os.path.dirname(path)), exist_ok=True)
        state._write_yaml_atomic(path, checkpoint)
        return checkpoint


def _measured_outputs(state: ProjectState, task: dict, offered) -> list:
    """The caller's entries with every artefact MEASURED -- or a refusal naming what was wrong."""
    expected = [str(one) for one in field_elements(task.get("expected_outputs"))]
    entries = offered if isinstance(offered, list) else []
    if not entries:
        raise CheckpointError(
            "a checkpoint with no outputs records no progress. Remedy: send at least one entry "
            "{\"output_index\": <0..%d>, \"progress\": \"partial\"|\"complete\", \"artifacts\": "
            "[<repo-relative path>], \"note\": ...} -- the indexes address %s's expected_outputs "
            "in order." % (len(expected) - 1, task["id"]))
    project = repo_root(state)
    measured = []
    for position, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise CheckpointError("outputs[%d] is not an object. Remedy: see the shape above."
                                  % position)
        try:
            index = int(entry.get("output_index"))
        except (TypeError, ValueError):
            index = -1
        if not 0 <= index < len(expected):
            raise CheckpointError(
                "outputs[%d] names output_index %r, and %s has %d expected_outputs (0..%d) -- a "
                "checkpoint that points outside the task's contract is progress towards something "
                "nobody ordered. Remedy: address the expected output by its position."
                % (position, entry.get("output_index"), task["id"], len(expected),
                   len(expected) - 1))
        progress = str(entry.get("progress") or "")
        if progress not in PROGRESS_STATES:
            raise CheckpointError(
                "outputs[%d] says progress %r, and a checkpoint knows %s. Remedy: use one of them "
                "-- a word nothing understands would reach the successor as an opinion."
                % (position, entry.get("progress"), " or ".join(PROGRESS_STATES)))
        artifacts = [str(one) for one in field_elements(entry.get("artifacts"))]
        if not artifacts:
            raise CheckpointError(
                "outputs[%d] claims progress on %r and names no artefact -- there would be nothing "
                "for the verification to measure, so the successor would have to take the claim on "
                "trust. Remedy: name the file(s) the progress is IN, relative to the project root."
                % (position, expected[index]))
        rows = []
        for artifact in artifacts:
            digest = _file_digest(contained_artifact(project, artifact))
            if digest is None:
                raise CheckpointError(
                    "outputs[%d] names the artefact %r, which the kernel cannot measure under the "
                    "project root (%s): it is either not there, or it does not stay inside it (an "
                    "absolute or root-relative path, a `..`, or a link that leads out). There "
                    "would be nothing to re-measure later, and a successor is told to READ what a "
                    "checkpoint points at. Remedy: name every path relative to the PROJECT root, "
                    "including one inside the state directory (`%s/%s/<key>/...`)."
                    % (position, artifact, project, os.path.basename(state.root),
                       STAGING_DIRNAME))
            rows.append({"path": artifact, "sha256": digest[0], "bytes": digest[1]})
        measured.append({"output_index": index,
                         "progress": progress,
                         "expected_output": expected[index],
                         "note": str(entry.get("note") or ""),
                         "artifacts": rows})
    return measured


class Verdict(object):
    """What was MEASURED about a task's checkpoint -- never more than that.

    `adoptable` is the only field a caller acts on. `reasons` says what stood in the way when it is
    False, and what was measured when it is True; `summary` is the sentence a session may show a
    human, and it is scoped on purpose: a checkpoint that verifies is a checkpoint whose CONTRACT
    and FILES still hold, which is not a statement about the quality of the work behind them.
    """

    def __init__(self, task_id, adoptable, reasons, pointer=None, record=None):
        self.task_id = task_id
        self.adoptable = bool(adoptable)
        self.reasons = list(reasons)
        self.pointer = pointer
        self.record = record

    @property
    def summary(self) -> str:
        if not self.adoptable:
            return ("CHECKPOINT TREATED AS ABSENT for %s: %s. Re-order the work from scratch -- "
                    "adoption is earned, not assumed (DEC-0044)."
                    % (self.task_id, "; ".join(self.reasons)))
        return (
            "CHECKPOINT VERIFIED for %s at %s -- what was measured: %s. NOT measured: whether the "
            "work is correct, and whether the note beside each output is true. Read it, judge it, "
            "and continue from `next_step`; nothing here obliges you to adopt it."
            % (self.task_id, self.pointer, "; ".join(self.reasons)))


def verify(state: ProjectState, task_id: str, _locked: bool = False) -> Verdict:
    """Is this task's checkpoint adoptable? -- the verification step DEC-0044 makes adoption wait for.

    Every failure returns the SAME verdict shape as "there is none", because DEC-0044 makes them the
    same thing: an unverified or failing checkpoint is treated as absent. The reasons still say
    which of the two it was, so a stale record is a fact the session can report rather than a
    silence it has to interpret.

    `_locked=True` skips taking the kernel lock -- ONLY for a caller that already holds it, which is
    `dispatch.create_lease`. The lock is a FILE lock and not reentrant (`kernel.lock.KernelLock`), so
    a nested acquire does not recurse, it waits for its own holder and then times out; the same
    reason `report.validate_state` carries the flag.
    """
    if not _locked:
        with state.lock:
            return _verify_locked(state, task_id)
    return _verify_locked(state, task_id)


def _verify_locked(state: ProjectState, task_id: str) -> Verdict:
    """`verify` body for callers holding the lock (see there)."""
    try:
        task = state.read_item(task_id)
    except StateError as exc:
        return Verdict(task_id, False, ["the task itself could not be read (%s)" % exc])
    path = checkpoint_path(state, task_id)
    if not os.path.isfile(ext_path(path)):
        return Verdict(task_id, False, ["no checkpoint was ever recorded for it"])
    try:
        stored = state._read_yaml(path)
        validate(stored, "checkpoint")
    except Exception as exc:  # noqa: BLE001 -- an unreadable record is an absent one
        return Verdict(task_id, False,
                       ["its checkpoint file could not be read against the contract (%s)"
                        % exc])
    reasons, failures = [], []
    if str(stored.get("task_id")) != str(task_id):
        failures.append("the record belongs to %s, not to %s"
                        % (stored.get("task_id"), task_id))
    digest_now = expected_outputs_digest(task)
    if stored.get("expected_outputs_digest") != digest_now:
        failures.append("the task's expected_outputs have changed since it was written, so the "
                        "progress it records was measured against another contract")
    else:
        reasons.append("the task's expected_outputs are unchanged since it was written")
    if int(stored.get("task_revision") or 0) != int(task.get("revision") or 0):
        failures.append("%s is at revision %s and the record was written against revision %s"
                        % (task_id, task.get("revision"), stored.get("task_revision")))
    root_revision = _root_revision(state, task)
    if root_revision is not None and int(stored.get("root_revision") or 0) != root_revision:
        failures.append("its root is at revision %s and the record was written against "
                        "revision %s" % (root_revision, stored.get("root_revision")))
    moved, files = _artifacts_that_moved(state, stored)
    if moved:
        failures.append("%d of %d artefact(s) no longer carry the bytes measured when it was "
                        "written (%s)" % (len(moved), files, ", ".join(moved)))
    elif files:
        reasons.append("all %d named artefact(s) still carry the bytes measured then" % files)
    else:
        # A RECORD THAT NAMES NO ARTEFACT AT ALL IS ABSENT, and this clause is here because the
        # write path's identical refusal does not cover this one: `record` is a route, not a wall
        # -- the staging directory is the one place a dispatched specialist may write with its own
        # tools, so `outputs: []` can arrive without ever passing `_measured_outputs`. Measured
        # 2026-08-15 before this: such a file verified rc 0, and the artefact clause simply dropped
        # out of the sentence, leaving "expected_outputs are unchanged" to carry a verdict about
        # nothing. `test_a_handwritten_checkpoint_that_measures_nothing_is_absent` is the red test.
        failures.append("it names no artefact at all, so there is nothing for this step to measure "
                        "and nothing for a successor to resume from")
    if failures:
        return Verdict(task_id, False, failures)
    reasons.append("it was recorded at %s" % stored.get("recorded"))
    return Verdict(task_id, True, reasons, pointer=state_relative(state, path), record=stored)


def _root_revision(state: ProjectState, task: dict):
    """The task's root revision NOW, or None when the root cannot be read (then it is not judged)."""
    try:
        return int(state.read_item(task["product_requirement"]).get("revision") or 0)
    except (StateError, KeyError, TypeError, ValueError):
        return None


def _artifacts_that_moved(state: ProjectState, record: dict):
    """([artefacts that no longer match], how many were named) -- containment, existence AND bytes.

    Containment is re-tested HERE and not trusted from the write path, because the record can have
    been written past it (see the module docstring): a path that leaves the project is unusable
    whatever its digest says, so it is reported in the same list as one that is gone.
    """
    project = repo_root(state)
    moved, seen = [], 0
    for entry in record.get("outputs") or []:
        for artifact in (entry or {}).get("artifacts") or []:
            seen += 1
            path = str((artifact or {}).get("path") or "")
            inside = contained_artifact(project, path)
            digest = _file_digest(inside)
            if inside is None:
                moved.append("%s is not inside the project" % path)
            elif digest is None:
                moved.append("%s is gone" % path)
            elif digest[0] != (artifact or {}).get("sha256"):
                moved.append("%s changed" % path)
    return moved, seen

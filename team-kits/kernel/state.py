"""State-kernel core operations (HARNESS_V2_SPEC.md II.4) -- step 1.4a.

The kernel is the ONLY writer of canonical project state. Every operation:
- runs under the cross-process KernelLock (item write AND index regeneration
  inside the same hold -- no second inconsistent state)
- writes atomically (temp file + os.replace, extended-length paths)
- allocates ids itself (max-scan over active+archive under the lock;
  callers never pick ids)
- enforces the status automata, and enforces the USER APPROVAL an edge needs
  when an approval kind commits that edge (`approvals.APPROVAL_TRANSITIONS`
  read backwards). `transition` is the only writer of such a status; the TSK
  dispatch lifecycle writes its own statuses directly, and none of those is a
  status an approval commits -- see `_transition_locked`
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
import re
import time

import yaml

from .backlog_types import (
    ACTIVE_DIRS,
    EVIDENCE_KINDS,
    EVIDENCE_RESULTS,
    HASHED_FIELDS,
    IMMUTABLE_TYPES,
    NONEMPTY_FIELDS,
    PARENT_FIELDS,
    REQUIRED_FIELDS,
    TASK_TYPES,
    TSK_PLAN_FIELDS,
    TransitionError,
    assert_transition,
    confirming_edge,
    format_id,
    initial_status,
    invalidation_target,
    is_terminal,
    parse_id,
)
from .lock import KernelLock, ext_path

_KERNEL_SET = ("id", "status", "revision", "approval_ref", "created")

# WHAT A CONFIRMATION MUST SHOW, per item type: {type: Evidence kind}. WHICH edge this guards is
# not written here -- `backlog_types.confirming_edge` derives it from the type's own automaton, so
# a renamed status moves the rule with it.
#
# THE ROWS ARE THE PROMISES THE SHIPPED TEXTS MAKE, and there is exactly one of them. The three
# constitutions' §2 ("mandatory regression test -- fails pre-fix, passes post; the Evidence for it
# is what moves the bug from FIXED to VERIFIED") is a statement about a MECHANISM, and until
# 2026-07-31 there was none: measured on a fresh state directory, `transition BUG-0001 VERIFIED`
# ran with no Evidence in the project at all and `validate` then reported 0 errors.
#
# WHAT IS DELIBERATELY NOT IN HERE, named because an absence a reader cannot see is the thing this
# file keeps being wrong about: `confirming_edge` also picks out TSK DONE->VALIDATED, PR/RQ
# DELIVERED->ACCEPTED, CR APPROVED->APPLIED and EXP COMPLETED->ANALYZED. Those edges are NOT
# guarded by anything here. The quality-engineer SKILL and the PM SKILL both say QA Evidence is
# what lets a task go DONE -> VALIDATED, and that remains policy the roles follow rather than a
# rule the kernel enforces -- `gate_git` demands the same Evidence at the MERGE, which is a
# different moment. Adding a row is all it takes; inventing one for a type whose required proof no
# shipped text states would be the kernel making up policy.
CONFIRMING_EVIDENCE = {"BUG": "test"}

# HOW THE KERNEL NAMES A FILE IT STORES PER REVISION -- composed and read back in ONE place.
#
# `staging` freezes some items per revision (spec II.6/II.6a): the wireframe `WFR-0001` lives at
# `design/wireframes/WFR-0001.r02.drawio.svg` with the companion `WFR-0001.r02.yaml` beside it.
# FOUR places have to agree on that shape -- three readers (`_frozen_revision_path`: which
# revision IS the item; `iter_active_items`: which files in a directory are items at all;
# `staging._next_frozen_revision`: which number has already been used) and `staging`'s own
# composition of the names -- and for one round they did not: the first read the directory per
# revision while the second read every `*.yaml` as its own item, so a SECOND `freeze_wireframe`
# made `report.validate_state` report `WFR-0001 duplicate id` and `gate_memory_complete` turned
# that into a blocked merge for the whole project (measured 2026-07-28, disposition row 6.5).
#
# The rule is read off the NAME, never off a list of types: an item stored per revision is
# recognised by how the kernel wrote it, so whichever type is frozen that way next arrives here
# already understood. An id carries no dot, which is what lets `[^.]+` separate the base from the
# revision and the revision from the suffixes (`.drawio.svg`, `.yaml`, `.html`).
_REVISION_RE = re.compile(r"(?P<base>[^.]+)\.r(?P<revision>\d+)(?P<suffix>\..*)?\Z", re.ASCII)


def revision_name(item_id: str, revision: int, suffix: str) -> str:
    """The file name of ONE frozen revision -- the only composer, read back by `split_revision`."""
    return "%s.r%02d%s" % (item_id, int(revision), suffix)


def split_revision(name: str):
    """(base, revision, suffix) for a per-revision file name; (None, None, None) otherwise."""
    match = _REVISION_RE.match(name or "")
    if not match:
        return None, None, None
    return match.group("base"), int(match.group("revision")), match.group("suffix") or ""


def _is_item_id(value) -> bool:
    """Does this name an item at all? -- the question `parse_id` answers, without the raise."""
    try:
        parse_id(str(value))
    except ValueError:
        return False
    return True


# The suffix an ITEM file carries. Items are YAML whatever else lies beside them: a frozen
# wireframe revision is a `.drawio.svg` PLUS a `.yaml` companion, a frozen design a `.html` plus a
# `.yaml` manifest, and only the companion is the item.
ITEM_SUFFIX = ".yaml"


def item_revision(name: str):
    """(item id, revision) when `name` is the file of ONE stored revision of an item, else
    (None, None).

    THE predicate, and it is one function because the first cut of this fix had it twice and they
    disagreed within the hour. `_frozen_revision_path` demanded the revision be followed by
    exactly `.yaml`; `iter_active_items` accepted any suffix -- so a hand-placed
    `WFR-0001.r03.backup.yaml` was measured as the ACTIVE item by the second reader while
    `read_anywhere` still resolved `WFR-0001` to `r02`. That is the identical two-readings defect
    disposition row 6.5 is about, one file shape further along, and it is why the question is
    asked here rather than answered in each caller.

    A name that fails any part of it is not a revision file at all: it stays a file in its own
    right, and if its content claims an id another file also claims, the duplicate-id rule says so.
    """
    base, revision, suffix = split_revision(name)
    if revision is None or suffix != ITEM_SUFFIX or not _is_item_id(base):
        return None, None
    return base, revision


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
                "Remedy: `git restore %s` then `python scripts/harness.py generate-index`."
                % (item_id, path, os.path.relpath(path, self.root))
            )
        return item

    def iter_active_items(self, item_type: str):
        """(stem, path) for every file in the type's active dir that IS an active item.

        ONE reading of one directory, for every reader that asks what a project is working on
        now -- the state validator and the session brief through `report._iter_active`, and
        `generated/index.yaml` through `_regenerate_index_locked`. Both used to answer it
        themselves with the older rule "every `*.yaml` in here is an item", which contradicted
        `_frozen_revision_path` next door and cost a merge (see `_REVISION_RE`).

        THE RULE, in one sentence: files whose names differ only in their `.rNN` are REVISIONS
        of one item, and the item is the highest of them. A superseded revision is HISTORY --
        still on disk, still in git, read by nobody who asks what is active, exactly as an
        archived item is. `read_anywhere` resolves the id to that same newest file, so the two
        readings can no longer disagree about which file an id names.

        TWO THINGS IT DELIBERATELY DOES NOT COLLAPSE, because each is a real contradiction the
        validator has to keep reporting rather than resolve by picking one:
          * a plain `<ID>.yaml` beside `<ID>.rNN.yaml` -- one directory then claims two homes
            for one id, and `read_anywhere` silently prefers the plain one;
          * a base that is no item id at all -- the revision rule is about items stored per
            revision, so `notes.r01.yaml` and `notes.r02.yaml` stay two files.
        Both leave the duplicate-id rule to speak, which is the counter-direction that must
        survive: two DIFFERENT items claiming one id is still an error.
        """
        base = self.active_dir(item_type)
        if not os.path.isdir(ext_path(base)):
            return
        newest, plain = {}, []
        for name in sorted(os.listdir(ext_path(base))):
            if not name.endswith(ITEM_SUFFIX):
                continue
            item_id, revision = item_revision(name)
            if item_id is None:
                plain.append(name)
                continue
            if item_id not in newest or revision > newest[item_id][0]:
                newest[item_id] = (revision, name)
        for name in sorted(plain + [name for _revision, name in newest.values()]):
            yield name[: -len(ITEM_SUFFIX)], os.path.join(base, name)

    def _frozen_revision_path(self, item_id: str):
        """The newest `<id>.rNN.yaml` in the type's active dir, or None.

        The kernel freezes some items PER REVISION (`staging.freeze_wireframe` /
        `freeze_design`, spec II.6/II.6a): the canonical file of `WFR-0001` is
        `design/wireframes/WFR-0001.r03.yaml`, and `active_path` -- which composes
        `<id>.yaml` -- names nothing. So `read_anywhere` answered "no such item" for
        every wireframe and every frozen design, and the two readers built on it
        answered with it: `_assert_origins_resolve` REFUSED an Evidence recorded
        against a `WFR` ("does not exist"), and `report._hangs_from` walked no further
        than the id. The designer's review could not be recorded, and once recorded by
        hand it covered nothing.

        The rule is read off the file names, not off a list of types: an item stored
        per revision IS its newest revision, so whichever type is frozen that way next
        arrives here already resolved. `iter_active_items` reads the same names through
        the same `split_revision`, which is what makes that one sentence the whole
        kernel's rather than this method's.

        Deliberately NOT in `active_path`: that path is where a write LANDS, and a write
        must be deterministic -- a frozen revision is immutable, and the way to change
        one is another freeze, not an edit of the file the reader happened to pick.
        """
        item_type, _ = parse_id(item_id)
        base = self.active_dir(item_type)
        if not os.path.isdir(ext_path(base)):
            return None
        best = None
        for name in sorted(os.listdir(ext_path(base))):
            found, revision = item_revision(name)
            if found != item_id:
                continue
            if best is None or revision > best[0]:
                best = (revision, os.path.join(base, name))
        return best[1] if best else None

    def read_anywhere(self, item_id: str):
        """(item, archived) from active/, else from archive/; (None, False) when nowhere.

        The reader for questions that outlive an item's active life. A TSK is
        archived the moment it reaches VALIDATED, so anything that walks from a
        finished piece of work back to the requirement it served -- the merge
        gate resolving Evidence to its root is the case that forced this -- must
        follow that walk into the archive or it stops one hop short of the
        answer.

        LOCKING is not one rule here, because the callers ask two different
        questions. A WRITER or a validator reads to decide what it will then
        write or assert about the store as a whole, so it must hold the lock or
        its premise can change underneath it -- `dispatch` does exactly that.
        The MERGE-GATE path reads single item files to answer a question about
        one item, deliberately lock-free: it runs on the same tool call as
        `gate_memory_complete`, which already takes the lock for
        `validate_state`, and a second acquisition on that event is what turns a
        slow validate into a blocked push. That trade is argued in full at
        `report._delivery_evidence`, where the gate path begins; what makes it
        payable is that a half-written file is no verdict either way: it is read
        as no judgement rather than as consent, and `validate_state` -- taken
        under the lock on the same event -- is what reports it as a finding.
        """
        try:
            item_type, _ = parse_id(item_id)
        except ValueError:
            return None, False   # not an id at all: it names no item, here or anywhere
        try:
            return self.read_item(item_id), False
        except StateError:
            pass
        frozen = self._frozen_revision_path(item_id)
        if frozen is not None:
            item = self._read_yaml(frozen)
            if isinstance(item, dict) and item.get("id") == item_id:
                return item, False
        base = os.path.join(self.root, "archive", item_type)
        if os.path.isdir(ext_path(base)):
            for year in sorted(os.listdir(ext_path(base))):
                candidate = os.path.join(base, year, item_id + ".yaml")
                if os.path.exists(ext_path(candidate)):
                    return self._read_yaml(candidate), True
        return None, False

    def exists_anywhere(self, item_id: str) -> bool:
        """True when the id names an item in active/ OR archive/ -- call under the lock."""
        if os.path.exists(ext_path(self.active_path(item_id))):
            return True
        if self._frozen_revision_path(item_id) is not None:
            return True
        item_type, _ = parse_id(item_id)
        base = os.path.join(self.root, "archive", item_type)
        if not os.path.isdir(ext_path(base)):
            return False
        for year in sorted(os.listdir(ext_path(base))):
            if os.path.exists(ext_path(os.path.join(base, year, item_id + ".yaml"))):
                return True
        return False

    def _assert_origins_resolve(self, item_type: str, fields: dict) -> None:
        """Every field BINDING an item to the work it belongs to must name items that EXIST.

        WHICH fields those are is `PARENT_FIELDS`, derived from the type's field contracts --
        this check must not carry its own list of types. It carried one (`TSK` and `EVD`,
        the two whose binding is a hot gate input), and the cost was that the same two-name
        list had to be kept in step with the reference graph in `report`, which drifted:
        `SR.derives_from` was in neither, so an `SR` could be captured against a phantom
        parent and the merge gate then found no root for the Evidence judging it.

        The bindings this exists for, and why the CHEAP half of the reference check belongs
        on the write path rather than only in the state validator:

        * `TSK.derives_from` is what the dispatch gate resolves `acceptance_refs` against.
          A phantom id, an integer or a free-text note contributes nothing, so a task can
          look derived while being derived from nothing.
        * `EVD.related` is what `gate_git` resolves a merge against. Evidence bound to a
          nonexistent id is bound to nothing -- and since the gate answers "is there
          passing evidence for THIS item", such a record is the shape that looks like proof
          while covering no work at all.

        Called from capture AND from the edit path, for the reason the vocabulary check is:
        a binding refused at capture and then written by an edit is not refused at all. Which
        types can still reach it there is a fact about `IMMUTABLE_TYPES` (an `EVD` is refused
        wholesale a few lines earlier), not a reason for this check to know which type it is
        judging.

        Only the CHEAP half lives here -- ids parse and resolve. Whether the origin belongs
        to this root's tree (BUG.related_pr == root, CR.target_pr == root, EXP->HYP->RQ ==
        root) is a reference-GRAPH question, which spec II.4 assigns to the state validator
        (gate layer 4) rather than to a hot dispatch path.
        """
        for field in PARENT_FIELDS.get(item_type, ()):
            if field not in fields:
                continue
            origins = fields.get(field)
            origins = origins if isinstance(origins, (list, tuple)) else [origins]
            remedy = _BINDING_REMEDY.get(item_type, _BINDING_REMEDY_DEFAULT % field)
            for origin in origins:
                try:
                    parse_id(str(origin))
                except ValueError:
                    raise StateError(
                        "%s %r is not an item id. Remedy: %s -- free text there binds to "
                        "nothing." % (field, origin, remedy)
                    ) from None
                if not self.exists_anywhere(str(origin)):
                    raise StateError(
                        "%s %s does not exist. Remedy: create the item first, or point at the "
                        "right one -- a phantom reference binds to nothing, and the gate that "
                        "reads it would refuse later with a less obvious message."
                        % (field, origin)
                    )

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
        # ...and for a few of them "provided" has to mean "says something": see
        # NONEMPTY_FIELDS for why an empty list there is the same claim as no field.
        # Capture-only, because the types that have such a field are exactly the ones
        # the edit path refuses wholesale (IMMUTABLE_TYPES).
        hollow = [k for k in NONEMPTY_FIELDS.get(item_type, ()) if not fields.get(k)]
        if hollow:
            raise StateError(
                "capture %s: %s must name something -- an empty list there is the "
                "same claim as leaving the field out. Remedy: %s"
                % (item_type, ", ".join(hollow), _NONEMPTY_REMEDY[item_type])
            )
        _assert_closed_vocabularies(item_type, fields)
        self._assert_origins_resolve(item_type, fields)
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
        if item_type in IMMUTABLE_TYPES and changes:
            # A record is superseded, never corrected -- see IMMUTABLE_TYPES for why
            # the type has no other way to change. Measured before this existed: an
            # `EVD` whose `result` was edited from `fail` to `pass` reopened a merge
            # `gate_git` had closed, and an edited `related` bound a failing verdict
            # to a different item; neither left an item behind to notice.
            raise StateError(
                "%s is a %s -- a record of something that already happened, so none of "
                "its fields change (spec II.2). Remedy: record the new run as its own "
                "item (`python scripts/harness.py evidence ...`, run from the project root "
                "and never with --root), which supersedes this one; archive this one "
                "afterwards if it should also leave the active store. Both are visible in "
                "git, an edit is not." % (item_id, item_type)
            )
        # the SANCTIONED edit path has to enforce the same rules as capture: otherwise
        # an orchestrator that hits the capture-time refusal simply re-types the task
        # afterwards, and the design_ref rule stops applying. The same holds for a
        # binding -- `derives_from` rewritten to a phantom id makes the task's
        # acceptance criteria resolve against nothing, exactly as it would at capture.
        _assert_closed_vocabularies(item_type, changes)
        self._assert_origins_resolve(item_type, changes)
        if item_type == "TSK" and item.get("status") != "DRAFT":
            # ... and closing the vocabulary is not enough on its own: a
            # vocabulary-LEGAL re-type dodges the design gate just as well, and
            # widening allowed_scope on a LEASED, BOUND task hands a running
            # specialist the whole repo. The work-order contract is frozen once
            # the task leaves DRAFT (see TSK_PLAN_FIELDS).
            frozen = sorted(set(changes) & TSK_PLAN_FIELDS)
            if frozen:
                raise StateError(
                    "%s is %s -- its work-order fields (%s) are frozen outside "
                    "DRAFT because gates read them (allowed_scope is the "
                    "write-scope gate's only input). Remedy: transition the task "
                    "back to DRAFT to re-plan it, or CANCEL it and create a new "
                    "one -- re-planning has to be visible, not a field write."
                    % (item_id, item.get("status"), ", ".join(frozen))
                )
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
        with self.lock:
            return self._transition_locked(item_id, to_status, approved_retry)

    def _transition_locked(self, item_id: str, to_status: str,
                           approved_retry: bool = False) -> dict:
        """transition body for callers that ALREADY hold the lock (it is not reentrant).

        THE ONLY WRITER OF A STATUS AN APPROVAL COMMITS, which is a narrower claim than the one
        this kernel used to make and is the one it can keep. `approvals.mint` set
        `item["status"]` directly and thereby skipped the automaton -- and would have skipped the
        approval check -- on the single path that moves a root item most often; it comes through
        here now. OTHER WRITERS REMAIN, and they are described rather than listed -- a list here
        said "the TSK dispatch lifecycle, four functions" and the AST finds seven sites, because
        `capture` (the initial status) and `_update_item_locked` (the approval-invalidation reset
        spec II.2 requires to be atomic) write one too. The property that holds is not "there are
        four" but: every status any of them can produce is bounded from a kernel map, and none of
        those values is a status an approval commits.
        `test_no_direct_status_write_can_produce_a_status_an_approval_commits` derives that from
        the running source -- it enumerates the writers itself, bounds each one's possible values
        and compares them against `APPROVAL_TRANSITIONS`, so a new writer needs no edit here and a
        new writer that could produce APPROVED/IN_DELIVERY/ACCEPTED turns it red.

        FOUR things stand between a status and its new value, and they are four because their
        evidence lives in four different places:
          * the AUTOMATON (`assert_transition`) -- is this edge defined at all;
          * the TSK retry rule -- its evidence is a caller argument, because spec II.2 records the
            retry approval as a Querregel and no APR kind has a manifest for it;
          * the APPROVAL (`approvals.assert_transition_approved`) -- derived from
            `APPROVAL_TRANSITIONS`, so which edges it guards follows from which edges an approval
            commits, rather than from a list kept beside it;
          * the CONFIRMING EVIDENCE (`_assert_confirmed`) -- the edge from
            `backlog_types.confirming_edge`, the proof from `CONFIRMING_EVIDENCE`.
        """
        item_type, _ = parse_id(item_id)
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
        # DEFERRED import: `approvals` imports this module at its own module scope, so a top-level
        # import here would be a cycle. By the time any transition runs, both halves are loaded.
        from . import approvals
        approvals.assert_transition_approved(self, item, item_type, from_status, to_status)
        self._assert_confirmed(item_id, item_type, from_status, to_status)
        item["status"] = to_status
        self._write_yaml_atomic(self.active_path(item_id), item)
        self._regenerate_index_locked()
        return item

    def _assert_confirmed(self, item_id, item_type, from_status, to_status):
        """A confirming edge needs the proof `CONFIRMING_EVIDENCE` names, in force RIGHT NOW.

        `report.qa_verdicts` is asked rather than the Evidence store scanned here, and that is the
        whole point of routing through it: it already answers "which Evidence covers this item"
        (`evidence_covers`, including the indirect hop from a task to its root) and "which of
        several counts" (newest per kind supersedes). A second reader of the same store would be a
        second answer to the same question -- and the merge gate reads THIS one, so a BUG that
        cannot be VERIFIED here is exactly a BUG whose merge `gate_git` would also refuse.

        It is lock-safe from inside `_transition_locked` because `report._delivery_evidence` takes
        no lock, by its own design note; the kernel lock is not reentrant, so a reader that did
        would deadlock every transition.
        """
        kind = CONFIRMING_EVIDENCE.get(item_type)
        if not kind or (from_status, to_status) != confirming_edge(item_type):
            return
        from . import report
        verdict = report.qa_verdicts(self, item_id).get(kind)
        if verdict and verdict.get("result") == "pass":
            return
        raise TransitionError(
            "%s %s -> %s needs a %r Evidence that PASSES and covers %s; %s. The regression test "
            "is what turns a fix into a verification -- without it the status says the bug is gone "
            "and nothing measured that. Remedy: run the test that fails before the fix and passes "
            "after it, then record the run: `python scripts/harness.py evidence --kind %s "
            "--result pass --related %s --summary ... --artifact-ref <path to the raw proof>`, "
            "from the project root."
            % (item_id, from_status, to_status, kind, item_id,
               "the current %r verdict is %r" % (kind, verdict.get("result")) if verdict
               else "there is none",
               kind, item_id))

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
            # through `iter_active_items`, not a second listing of the same directory: the index
            # is what the dashboard and every "what is open" reader work from, and with its own
            # copy of the rule it listed a twice-frozen wireframe as two rows carrying one id
            for stem, path in self.iter_active_items(item_type):
                try:
                    item = self._read_yaml(path)
                except Exception:
                    item = None
                if not isinstance(item, dict):
                    rows.append({"id": stem, "type": item_type, "corrupt": True})
                    continue
                row = {
                    "id": item.get("id", stem),
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


# Which field an item names its parent through is `backlog_types.PARENT_FIELDS`,
# derived there from the type's field contract -- the SAME definition the reference
# graph in `report` walks, so a binding the graph resolves and a binding the write
# path checks can no longer be two different sets. What lives here is only the
# REMEDY: one sentence per type whose refusal a role meets mid-command.
_BINDING_REMEDY = {
    "TSK": "name the item this task derives from (the PR/RQ, or the BUG/CR/EXP "
           "whose criteria it serves)",
    "EVD": "name the item this evidence examined (the TSK it judged, or the "
           "PR/RQ/EXP it covers)",
}
_BINDING_REMEDY_DEFAULT = "put the id of the item this one belongs to in `%s`"

# What to DO about an empty NONEMPTY_FIELDS entry, per type -- one sentence naming
# the arguments, because the role hitting this refusal is mid-command.
_NONEMPTY_REMEDY = {
    "EVD": "pass `--related <ITEM-ID>` for the item you examined and "
           "`--artifact-ref <path>` for the raw proof, state-relative "
           "(`staging/<task-id>/coverage.html`). A verdict with nothing to point at "
           "is an assertion, and the merge gate would open on it.",
}

# Fields whose value must come from a CLOSED vocabulary, per type. Every one of
# them is read by a gate to DECIDE something, which is what closing them buys:
# see TASK_TYPES (design_ref rule, II.6) and EVIDENCE_KINDS/EVIDENCE_RESULTS
# (merge gate, II.10a). Anything not listed here is free-form by intent.
_CLOSED_VOCABULARY = {
    ("TSK", "type"): (TASK_TYPES,
                      "the type is a gate input (a UI task needs a design_ref)"),
    ("EVD", "kind"): (EVIDENCE_KINDS,
                      "the kind decides whether this evidence judges a delivery "
                      "or the project, and the merge gate only accepts the former"),
    ("EVD", "result"): (EVIDENCE_RESULTS,
                        "the verdict is what the merge gate reads; an unknown "
                        "value is not a fail, so the gate would go quiet"),
}


def _assert_closed_vocabularies(item_type: str, fields: dict) -> None:
    """Refuse a value outside its field's closed vocabulary (see _CLOSED_VOCABULARY).

    Called from capture AND from the edit path, because a value refused at capture
    and then written by an edit is not refused at all. A free-text value would not
    FAIL the gate that reads it -- it would silently skip it, which is the failure
    both vocabularies exist to prevent.

    On the edit path only `TSK.type` can actually arrive here: an `EVD` is refused
    wholesale a few lines earlier (IMMUTABLE_TYPES), so the two EVD entries below
    are capture-only in practice. That is a fact about EVD and not a reason for
    this check to know which type it is judging -- the same argument the
    neighbouring `_assert_origins_resolve` makes, and the reason a later type with
    a closed field needs no second edit-path wiring.
    """
    for (owner, field), (allowed, why) in _CLOSED_VOCABULARY.items():
        if owner != item_type or field not in fields:
            continue
        if fields.get(field) not in allowed:
            raise StateError(
                "unknown %s %s %r. Remedy: use one of %s -- %s, so a free-text "
                "value would skip that check instead of failing it."
                % (item_type, field, fields.get(field),
                   ", ".join(sorted(allowed)), why)
            )


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")

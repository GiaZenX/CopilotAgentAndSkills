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
    AUTOMATA,
    EVIDENCE_KINDS,
    EVIDENCE_RESULTS,
    HASHED_FIELDS,
    IMMUTABLE_TYPES,
    IMPORT_MARK,
    LEGACY_FIELD,
    NON_AUTOMATON_STATUSES,
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
    map_v1_status,
    parse_id,
)
from .lock import KernelLock, ext_path

_KERNEL_SET = ("id", "status", "revision", "approval_ref", "created")

# Spec II.4's Vorschlagsbereich. Here rather than in `layout` because it is a path SEGMENT the
# writers below compose (`staging_root`), and `layout` -- which imports this module -- re-exports
# it for the predicates that compare a segment.
STAGING_DIRNAME = "staging"

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


# THE ONE EDGE WHOSE GUARD IS A CALLER ARGUMENT RATHER THAN A STORED RECORD (spec II.2
# Querregeln: a failed task may only be retried on an approved retry). Written here as data
# because TWO readers need it and a condition spelled at each of them is two rules: the transition
# path refuses the edge without `approved_retry=True`, and `migration_writable_statuses` may not
# count it as an edge a session walks on its own. `_transition_locked` is the enforcing reader.
RETRY_APPROVAL_EDGE = ("TSK", "FAILED", "READY")


def migration_writable_statuses(item_type: str) -> frozenset:
    """The statuses a MIGRATION may write onto an item directly -- derived, never listed.

    THE PROPERTY: a status this type can REACH from its initial one without ever walking an edge
    whose guard the import cannot satisfy.

    WHICH GUARDS ARE READ, AND WHICH ONE IS NOT. `_transition_locked` names FOUR things that stand
    between a status and its new value, and this walk reads three of them:
      * the AUTOMATON -- the walk is over `automaton.allowed`, so an undefined edge is not walked;
      * the APPROVAL -- `approvals.APPROVAL_TRANSITIONS` read backwards, the same map
        `approvals.required_approval_kinds` refuses an unapproved transition from;
      * the TSK RETRY rule -- `RETRY_APPROVAL_EDGE`, one datum read by this walk and by the
        transition path, rather than a condition spelled twice.
    THE FOURTH IS NOT READ, AND WHAT THAT COSTS IS MEASURED RATHER THAN ASSUMED EITHER WAY:
    `_assert_confirmed` demands the proof `CONFIRMING_EVIDENCE` names on a type's confirming edge,
    and this walk does not consult it. On the shipped maps that costs NOTHING -- the only type
    `CONFIRMING_EVIDENCE` covers is `BUG`, whose confirming edge ends at `VERIFIED`, and `VERIFIED`
    already lies behind the `BUG` scope approval, so the approval bolt excludes it first. So this
    is a guard that is not read rather than a status that escapes, and the difference matters:
    adding a type to `CONFIRMING_EVIDENCE` whose confirming target IS reachable here would turn it
    into the second thing without a line of this file changing.
    `test_state.test_the_migration_write_set_reads_three_of_the_four_edge_guards` is what measures
    that, in both directions, so this paragraph cannot quietly stop matching the maps.

    REACHABILITY RATHER THAN THE EDGE'S OWN TARGET, and that is the correction of 2026-08-04: this
    subtracted the approval TARGETS as a set, which leaves every status further down the same chain
    writable although it sits behind that approval just as much. Measured end to end before it was
    a walk -- a V1 `CR APPLIED` record was written to `archive/CR/<year>/` at `APPLIED`, a status
    no user was ever asked about, with `approval_ref: null` and no request anywhere. Nothing
    outside that file could say so either: `report.validate_state` judges the ACTIVE items, so an
    archived one appears in no finding of any severity.

    WHAT AN ABSENT APPROVAL EDGE MEANS -- and this is a HOLE, named with its mechanism rather than
    described as a guard. This walk reads a missing row in `APPROVAL_TRANSITIONS` as "no approval
    stands in the way". A missing row can mean that, and it can equally mean that the approval kind
    was never built: `approvals.required_approval_kinds` records SR PROPOSED -> ACCEPTED as
    "Reported, not bridged" -- an edge somebody may well have to sign, which has no KIND with a
    manifest, hence no row, hence no guard. So the import writes `SR ACCEPTED` into the archive
    with `approval_ref: null`, which is the same shape as the `CR APPLIED` defect one paragraph
    up, produced by an absence rather than by a subtraction. Nothing here can tell the two readings
    apart, because the harness states the difference only in that prose;
    `test_state.test_which_archive_bound_rows_rest_on_an_absent_approval_edge` derives today's set
    (SR, TSK, FR and HYP rows) and turns red when it changes in either direction. Closing it needs
    an approval KIND, which is a spec decision and not this function's.

    A type with no automaton has no status this kernel can walk to (`DEC`, `INV`), so the answer is
    empty rather than "anything": the import may not decide a record's status on a vocabulary that
    exists only in a comment.

    `approvals.approved_statuses` is the neighbouring question -- which statuses an item holds
    BECAUSE it was approved, for the spawn gates -- and it answers differently on purpose;
    `test_state.test_the_statuses_a_migration_may_write_are_the_ones_reachable_without_an_approval`
    names the types the two disagree about, so neither can be quietly rewritten into the other.
    """
    automaton = AUTOMATA.get(item_type)
    if automaton is None:
        return frozenset()
    from . import approvals
    gated = {edge for (owner, _kind), edge in approvals.APPROVAL_TRANSITIONS.items()
             if owner == item_type}
    if RETRY_APPROVAL_EDGE[0] == item_type:
        gated.add(RETRY_APPROVAL_EDGE[1:])
    reached, frontier = {automaton.initial}, [automaton.initial]
    while frontier:
        current = frontier.pop()
        for edge in automaton.allowed:
            if edge[0] != current or edge in gated or edge[1] in reached:
                continue
            reached.add(edge[1])
            frontier.append(edge[1])
    return frozenset(reached)


def migration_archive_status(item_type: str, v1_type: str, v1_status: str) -> str:
    """The status `capture_migrated_archive` writes, or a refusal -- the archive path's whole rule.

    TWO QUESTIONS, ASKED OF TWO AUTHORITIES, because they are about different things:

      * DOES THIS RECORD BELONG IN THE ARCHIVE -- the `archive_candidate` column of
        `V1_STATUS_MAPPING`, since whether a V1 value means "this life is over" is a fact about the
        V1 vocabulary and about nothing else. It used to be asked of the V2 AUTOMATON instead
        (is the mapped status a terminal), and that is a different question: V1 `TSK DONE` maps to
        `DONE`, which is no terminal of the V2 task automaton because V2 keeps `VALIDATED` for "QA
        confirmed" -- a confirmation V1 never collected. So a task V1 recorded as DONE landed in
        `tasks/active/` at DRAFT, presented as a fresh work order missing ten of eleven contract
        fields: the state of affairs SR-0004 exists to prevent, produced by the exemption written
        to prevent it, for the very rows whose number is its whole argument.
      * MAY THE IMPORT WRITE THAT STATUS AT ALL -- `migration_writable_statuses`, which is the
        approval bolt and which no table may talk its way past: a row that marks a status behind an
        approval edge as archive-bound is refused here, not obeyed.

    THIS IS A DIVERGENCE FROM THE WRITTEN CONTRACT, not an implementation of it: SR-0002 says "nur
    bei Endzustaenden" and SR-0004 "dessen abgebildeter Status ein Endzustand seines Automaten
    ist", i.e. exactly the terminal check the first bullet replaces. The replacement is argued
    above and is what runs; the SRs still say the other thing and are canonical state this module
    may not edit, so the divergence is REPORTED (`capture_migrated_archive`, bolt two) and awaits a
    decision rather than being read as agreement.

    Bounded by construction: whatever it returns is a member of `migration_writable_statuses`, so
    the direct status write it feeds can be read off the kernel's own maps rather than trusted. The
    mapping table is asked for the V2 value (`map_v1_status`) so that the archive path and the dry
    run's classification cannot answer differently.
    """
    v2_type, v2_status, archive_candidate = map_v1_status(v1_type, v1_status)
    if v2_type != item_type:
        raise StateError(
            "%s %r maps to a %s item, not to %s. Remedy: this is a caller bug -- the type the "
            "table answers with is the type the item is written as."
            % (v1_type, v1_status, v2_type, item_type))
    if not archive_candidate:
        raise StateError(
            "the migration archive path takes records spec II.10's table marks as FINISHED, and "
            "%s %r is not one of them. Remedy: import this record the ordinary way -- it lands in "
            "active/ at its initial status with the V1 value kept in `%s`."
            % (v1_type, v1_status, LEGACY_FIELD))
    allowed = migration_writable_statuses(item_type)
    if v2_status not in allowed:
        raise StateError(
            "%s %r maps to %r, which a %s reaches only through an edge a USER APPROVAL commits -- "
            "writing it here would be the automatically generated approval spec II.10 forbids. The "
            "import may write %s. Remedy: import this record the ordinary way -- it lands in "
            "active/ at its initial status with the V1 value kept in `%s`."
            % (v1_type, v1_status, v2_status, item_type,
               "/".join(sorted(allowed)) or "no status of this type (it has no automaton)",
               LEGACY_FIELD))
    return v2_status


def migration_archives(item_type: str, v1_type: str, v1_status: str) -> bool:
    """Would the archive path take this record? -- the ROUTING question, asked of the writer's rule.

    One judge for two callers. `migrate.build_plan` has to route each record and
    `capture_migrated_archive` has to refuse everything that is not routed here, and while the
    routing condition was spelled out at the planner a row could be added that the plan sent to the
    archive and the writer then rejected mid-run -- a plan promising what the run cannot do, which
    is the defect `capture_migrated_archive_preflight` exists to prevent one layer up.
    """
    try:
        migration_archive_status(item_type, v1_type, v1_status)
    except StateError:
        return False
    return True


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

    def staging_root(self) -> str:
        """Spec II.4's proposal area -- the whole of it.

        A builder for the same reason the two below are: `os.path.join(state.root, "staging")` was
        composed by hand in the session brief, in the staging sweep and in `staging.staging_dir`,
        and the name itself a fourth time in `layout`. Four spellings of one directory is how a
        reader of one of them comes to look somewhere the writer does not write; the name lives
        here, beside the writers, and `layout.STAGING_DIRNAME` re-exports it for the predicates
        that compare a path SEGMENT rather than a path.
        """
        return os.path.join(self.root, STAGING_DIRNAME)

    def archive_root(self) -> str:
        """The whole archive subtree.

        A builder of its own, and not merely the head of `archive_path`: everything the kernel
        retires lands somewhere under here, but at a path keyed by TYPE and YEAR
        (`archive_path`) or by staging key (`staging.clear_staging`). `kernel.layout` needs the
        SUBTREE -- asking `archive_path` for a probe would have declared `archive/pr/1970`
        canonical and left `archive/pr/2026` outside it, which is the whole archive of a live
        project.
        """
        return os.path.join(self.root, "archive")

    def archive_path(self, item_id: str, year: int) -> str:
        item_type, _ = parse_id(item_id)
        # deterministic archive paths (spec II.2): archive/<TYPE>/<year>/<ID>.yaml
        return os.path.join(self.archive_root(), item_type, str(year), item_id + ".yaml")

    def legacy_root(self) -> str:
        """The subtree a fully absorbed V1 store is moved into (SR-0005).

        A DIRECTORY builder for the same reason `archive_root` is one: what lands under here keeps
        its own relative path from the state root, so a probe of a file builder would declare one
        name canonical and leave every other outside.

        WHY IT IS A KERNEL-WRITTEN AREA AND NOT A KIT DOCUMENT AREA. `kernel.layout` asks the
        builders themselves what the kernel writes, and that one answer decides three things at
        once: `migrate` stops re-reading these files as V1 sources (SR-0005 asks for exactly that:
        "legacy/ ist ausdruecklich als 'bereits verarbeitet' verzeichnet"), `gate_write_scope`
        refuses a tool write into them -- a moved store is evidence of what the migration read, and
        a hand edit there would be an edit to that evidence -- and the SR-0001 scan skips them
        without needing a name of its own.
        """
        return os.path.join(self.root, "legacy")

    def legacy_path(self, relative_path: str) -> str:
        """Where a V1 document that fully became items is moved to, keeping its own path."""
        parts = [part for part in str(relative_path).replace("\\", "/").split("/") if part]
        return os.path.join(self.legacy_root(), *parts)

    def generated_path(self, name: str) -> str:
        """Where a REGENERABLE rollup lives (`generated/<name>`).

        A builder rather than a `os.path.join` at each call site, because `kernel.layout` asks
        the writers themselves where they write and a path composed inline answers nothing. The
        index below is one such writer; the session brief is the other.
        """
        return os.path.join(self.root, "generated", name)

    # -- io (always under the lock) --------------------------------------------

    @staticmethod
    def _read_yaml(path: str):
        with open(ext_path(path), encoding="utf-8") as fh:
            return yaml.safe_load(fh)

    @staticmethod
    def _write_yaml_atomic(path: str, data: dict) -> None:
        """Write `data` to `path` atomically, leaving NO half-written file behind either way.

        THE TEMP FILE IS CLEANED UP ON FAILURE, and that is not tidiness. `yaml.safe_dump` can
        raise on a payload it cannot represent, and the `.tmp-<pid>` it had already opened then
        stayed in the item directory -- measured in `procedures/active/`, where it is read by
        `migrate.state_fingerprint` (so a later plan digest covers a file nobody wrote on purpose)
        and by `report`'s directory readers. `os.replace` is still what makes the write atomic;
        this only makes the FAILING write leave the directory as it found it.
        """
        directory = os.path.dirname(path)
        os.makedirs(ext_path(directory), exist_ok=True)
        tmp = path + ".tmp-%s" % os.getpid()
        try:
            with open(ext_path(tmp), "w", encoding="utf-8", newline="\n") as fh:
                yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True)
            os.replace(ext_path(tmp), ext_path(path))
        except BaseException:
            try:
                os.remove(ext_path(tmp))
            except OSError:
                pass          # never mask the original failure with the cleanup's own
            raise

    def read_item(self, item_id: str) -> dict:
        path = self.active_path(item_id)
        try:
            item = self._read_yaml(path)
        except FileNotFoundError:
            raise StateError(
                "no active item %s (expected at %s). Remedy: check the id in the "
                "generated index; a finished item lives in the archive rather "
                "than among the active ones." % (item_id, path)
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
        base = os.path.join(self.archive_root(), item_type)
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
        base = os.path.join(self.archive_root(), item_type)
        if not os.path.isdir(ext_path(base)):
            return False
        for year in sorted(os.listdir(ext_path(base))):
            if os.path.exists(ext_path(os.path.join(base, year, item_id + ".yaml"))):
                return True
        return False

    def _assert_origins_resolve(self, item_type: str, fields: dict, also_existing=()) -> None:
        """Every field BINDING an item to the work it belongs to must name items that EXIST.

        `also_existing` is ids a PLANNER has undertaken to create before this body is written, and
        it exists because asking this question at planning time otherwise had no true answer: a V1
        store is a parent chain, so `migrate` planning `PROC-0001` and `PROC-0002 derives_from
        PROC-0001` was told the parent does not exist -- which was true of the state BEFORE the
        run and false of the state the run reaches. It defaults to empty, so every caller that
        writes NOW still asks the unrelaxed question; only a caller that can name the ids it is
        about to write may widen it, and `migrate.build_plan` then also has to order the writes and
        refuse a cycle, because a promise to create A before B and B before A is not keepable.

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
                if str(origin) in set(also_existing):
                    continue
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
                     os.path.join(self.archive_root(), item_type)]
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

    def _assert_capture_shape(self, item_type: str, fields: dict) -> None:
        """What is refused about a NEW item body whatever else is true of it.

        Split out of `capture_preflight` because the migration's archive path (DEC-0004/SR-0002) is
        exempt from the FIELD contract and from nothing else. What stays here is the part the
        exemption may not touch: the type has to be one this kernel captures, and the body may not
        carry a kernel-set field -- the `status` among them, which is the whole reason a caller may
        not hand one in.
        """
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
        _assert_closed_vocabularies(item_type, fields)

    def capture_preflight(self, item_type: str, fields: dict, also_existing=()) -> None:
        """Everything `capture` refuses BEFORE it writes anything -- raised, never written.

        WHY THIS IS ITS OWN METHOD, and it is not tidiness. A caller that wants to know whether a
        body WOULD capture had no way to ask, so it guessed -- and `kernel/migrate.py` guessed
        with the one check it could see (are the required fields present?). Measured against a dev
        project holding a V1 `system_requirements.yaml`: every one of its records names
        `derives_from: PRD-0001`, `PRD` is no V2 type, and `_assert_origins_resolve` refuses it --
        but only at write time. The plan said READY, three items landed, the fourth raised, and the
        run died in the middle with no receipt. A plan that cannot answer the question its own
        writer will ask is not a plan.

        So the write path and every planner ask the SAME function. Anything `capture` learns to
        refuse is refused at planning time on the day it is added here, with no second reader to
        keep in step.

        `also_existing` is passed straight through to `_assert_origins_resolve` and is empty for
        the write path; what it is for is argued there.
        """
        self._assert_capture_shape(item_type, fields)
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
        self._assert_origins_resolve(item_type, fields, also_existing)

    def capture(self, item_type: str, fields: dict) -> dict:
        """Create a new item: kernel assigns id/status/revision/approval_ref/created."""
        self.capture_preflight(item_type, fields)
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

    def capture_migrated_archive_preflight(self, item_type: str, fields: dict, v1_type: str,
                                           v1_status: str, also_existing=()) -> None:
        """Everything `capture_migrated_archive` refuses before it writes -- raised, never written.

        The same split as `capture`/`capture_preflight` and for the same reason: `migrate` has to
        be able to ask the writer's own verdict at PLANNING time, and a planner that asked the
        ordinary `capture_preflight` about an archive-bound record would be told the field contract
        is unmet -- which is exactly the contract this path is exempt from (DEC-0004). A plan that
        measures a check the run does not run is the defect this method exists to prevent.
        """
        self._assert_capture_shape(item_type, fields)
        legacy = fields.get(LEGACY_FIELD)
        if not isinstance(legacy, dict) or not legacy.get("legacy_id"):
            raise StateError(
                "the archive import path is for MIGRATED records only: this body carries no `%s` "
                "with a `legacy_id`, so nothing says where it came from. Remedy: use `capture`, "
                "which enforces the full field contract." % LEGACY_FIELD)
        migration_archive_status(item_type, v1_type, v1_status)
        self._assert_origins_resolve(item_type, fields, also_existing)

    def capture_migrated_archive(self, item_type: str, fields: dict, v1_type: str,
                                 v1_status: str, year: int, also_existing=()) -> dict:
        """Write ONE finished V1 record straight into `archive/<TYPE>/<year>/` (SR-0004/SR-0002).

        WHY THERE IS A SECOND WRITE ENTRY POINT AT ALL. Measured 2026-08-04 across two field
        projects: 260 of 264 tasks in one and 162 of 165 in the other are DONE, and a V1 task
        record is missing TEN of `REQUIRED_FIELDS["TSK"]`'s eleven fields -- `allowed_scope`,
        `expected_outputs`, `assigned_role` and the rest were never collected, not renamed. So the
        import had exactly three options and two of them are worse than this one: writing
        placeholders would hand `gate_write_scope` a sentence instead of leaving it a gap, and
        relaxing the contract in `capture` would make V2's promises untrue for 700+ items with no
        way to see it from outside. DEC-0004 chose the third: the field contract does not apply to
        a record this method writes, because such a record is a PROTOCOL of what happened and not
        a work order anybody will execute again.

        THE THREE BOLTS ON THAT EXEMPTION, written as what this code CHECKS -- and the second one
        is not the bolt SR-0002 asks for. That divergence is stated here rather than smoothed over,
        because a comment that credits a contract with a lock the code does not build is how a
        reader comes to trust the wrong thing:
          * the exemption is reachable through THIS method only. `capture` is untouched and still
            refuses a body missing a required field, so nothing about a normal capture changed.
            (SR-0002's first bolt, built as written.)
          * WHAT THE CODE CHECKS SECOND: the record's V1 status must be one spec II.10's own table
            marks as FINISHED (`archive_candidate`), AND the status it maps to must be one this
            kernel could have walked to without a user approval. Both halves are
            `migration_archive_status`, which is where they are argued; the second is why a V1
            `PRD ACCEPTED` is NOT written here -- it is imported at its initial status like every
            other record, because minting an ACCEPTED PR without an APR is precisely the
            "automatically generated user approval" spec II.10 forbids.
            WHAT SR-0002 ASKS FOR INSTEAD, verbatim: "nur bei Endzustaenden" -- the status must be
            a TERMINAL of the item's own automaton (SR-0004 words it the same way). This code does
            not check that, and the two answers differ in both directions on the shipped tables:
            `TSK DONE` is archived although `DONE` is no terminal of the task automaton, and an
            `SR` mapped to `ACCEPTED` is archived although `SUPERSEDED` is that automaton's only
            terminal. The reason for the replacement is argued at `migration_archive_status`
            (terminality is a property of a live V2 item and says nothing about a 2025 record, and
            reading it that way is what put finished V1 tasks into `tasks/active/`), and the
            replacement is what shipped. SR-0002 and SR-0004 have NOT been rewritten to match --
            they are canonical state and this module may not edit them -- so this is a REPORTED
            contract divergence awaiting a decision, not a re-reading of the contract.
            `test_state.test_the_archive_paths_second_bolt_is_not_the_terminal_check_sr_0002_asks_for`
            measures both directions of it.
          * an item written here is not reactivatable, and that is structural rather than a flag:
            it never exists under `active/`, and this kernel has no operation that moves an item
            out of the archive -- `transition` and `update_item` both resolve through
            `active_path` and answer "no active item". (SR-0002's third bolt, built as written.)

        WHAT THE ITEM RECORDS ABOUT ITS OWN GAPS is stamped HERE, not by the caller, because a
        record of what is missing that the caller composes is a record that can disagree with the
        body it describes: `legacy_fields.missing_required_fields` names every field of the
        contract this body does not carry, and `legacy_fields.kit_version` is what the
        installation says about itself (`report.installed_identity`), so a later reader can tell
        which vocabulary the record was read with.
        """
        self.capture_migrated_archive_preflight(item_type, fields, v1_type, v1_status,
                                                also_existing)
        legacy = fields[LEGACY_FIELD]
        from . import report
        body = dict(fields)
        body[LEGACY_FIELD] = dict(legacy)
        body[LEGACY_FIELD]["missing_required_fields"] = [
            name for name in REQUIRED_FIELDS[item_type] if name not in fields]
        body[LEGACY_FIELD]["kit_version"] = report.installed_identity(self)["kit_version"]
        body[IMPORT_MARK] = True
        with self.lock:
            item_id = self.allocate_id(item_type)
            item = {"id": item_id}
            item.update(body)
            # INSIDE THE LOCK because this call is the archive-path REFUSAL as well as the value,
            # and there is deliberately no second reader of that rule to raise earlier with. An id
            # was allocated by then and nothing was written, so a refusal here leaves the store as
            # it was; the id is not consumed, `allocate_id` re-derives it by max-scan.
            item["status"] = migration_archive_status(item_type, v1_type, v1_status)
            item["revision"] = 1
            item["approval_ref"] = None
            item["created"] = _now_iso()
            self._write_yaml_atomic(self.archive_path(item_id, int(year)), item)
            self._regenerate_index_locked()
            return item

    def capture_migrated_unresolved_preflight(self, item_type: str, fields: dict,
                                              also_existing=()) -> None:
        """Everything `capture_migrated_unresolved` refuses before it writes -- raised, never
        written. Same split, same reason, as the two preflights above."""
        self._assert_capture_shape(item_type, fields)
        legacy = fields.get(LEGACY_FIELD)
        if not isinstance(legacy, dict) or not legacy.get("legacy_id"):
            raise StateError(
                "the unresolved-import path is for MIGRATED records only: this body carries no "
                "`%s` with a `legacy_id`, so nothing says where it came from. Remedy: use "
                "`capture`, which enforces the full field contract." % LEGACY_FIELD)
        # A SENTENCE, not merely something truthy. `str(x) or ""` accepted `True`, a number and a
        # list -- each of which reads as "why" to this check and as nothing at all to the person
        # who later opens the archived item looking for the reason it is there.
        reason = legacy.get("unresolved")
        if not isinstance(reason, str) or not reason.strip():
            raise StateError(
                "the unresolved-import path writes a record NOBODY could translate, so the item "
                "has to say why: `%s.unresolved` is %s and this path needs a sentence. Remedy: "
                "this is a caller bug -- `migrate` composes that sentence out of the fields the "
                "record could not fill."
                % (LEGACY_FIELD, "empty" if isinstance(reason, str) else "%r" % (reason,)))
        self._assert_origins_resolve(item_type, fields, also_existing)

    def capture_migrated_unresolved(self, item_type: str, fields: dict, year: int,
                                    also_existing=()) -> dict:
        """Write ONE V1 record no answer could translate into `archive/<TYPE>/<year>/` (DEC-0009).

        THE SECOND ARCHIVE DOOR, and it is a different question from the first one. The door above
        takes a record whose LIFE IS OVER, as the V1 vocabulary itself recorded it, and writes it at
        the status that life ended in. This one takes a record that is still whatever V1 said it
        was, and whose V2 required fields have no source anywhere -- neither spelled the same, nor
        named by a `--map`, nor covered by a suggestion. DEC-0009's decision is that such a record
        is archived with its reason rather than blocking the whole run, because the alternative was
        measured: five hardening rounds spent on refusal messages for a command that runs three
        times, while the real projects stayed unmigrated beside them.

        THE STATUS IS THE TYPE'S INITIAL ONE, never the mapped V1 value, and that is what keeps
        this door from being a way past the approval bolt `migration_archive_status` builds: an
        initial status is what `capture` itself writes and is reachable without any approval by
        construction. What V1 said is kept in `legacy_fields.legacy_status`, unwalked, exactly as
        on the ordinary import path.

        WHAT IS LOST, named because DEC-0009 names it: a record ONE field decision would have saved
        is archived here, and this kernel has no operation that moves an item back out of the
        archive. The mitigation is not in this method -- it is that `migrate`'s dry run lists every
        record this door would take, with the fields it could not fill, BEFORE anything is written,
        and that the field suggestions (SR-0007) run first.
        """
        self.capture_migrated_unresolved_preflight(item_type, fields, also_existing)
        from . import report
        body = dict(fields)
        body[LEGACY_FIELD] = dict(fields[LEGACY_FIELD])
        body[LEGACY_FIELD]["missing_required_fields"] = [
            name for name in REQUIRED_FIELDS[item_type] if name not in fields]
        body[LEGACY_FIELD]["kit_version"] = report.installed_identity(self)["kit_version"]
        body[IMPORT_MARK] = True
        with self.lock:
            item_id = self.allocate_id(item_type)
            item = {"id": item_id}
            item.update(body)
            if item_type in _AUTOMATON_TYPES:
                item["status"] = initial_status(item_type)
            elif item_type in _NON_AUTOMATON_INITIAL_STATUS:
                item["status"] = _NON_AUTOMATON_INITIAL_STATUS[item_type]
            item["revision"] = 1
            item["approval_ref"] = None
            item["created"] = _now_iso()
            self._write_yaml_atomic(self.archive_path(item_id, int(year)), item)
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
          * the TSK retry rule (`RETRY_APPROVAL_EDGE`) -- its evidence is a caller argument, because
            spec II.2 records the retry approval as a Querregel and no APR kind has a manifest for
            it. The edge is a datum rather than a condition here, because
            `migration_writable_statuses` has to read the same one;
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
        if (item_type,) + (from_status, to_status) == RETRY_APPROVAL_EDGE and not approved_retry:
            raise TransitionError(
                "%s %s -> %s requires an approved retry (spec II.2 "
                "Querregeln). Remedy: obtain the retry approval, then call "
                "transition with approved_retry=True." % RETRY_APPROVAL_EDGE
            )
        # DEFERRED import: `approvals` imports this module at its own module scope, so a top-level
        # import here would be a cycle. By the time any transition runs, both halves are loaded.
        from . import approvals
        approvals.assert_transition_approved(self, item, item_type, from_status, to_status)
        self._assert_confirmed(item_id, item_type, from_status, to_status)
        item["status"] = to_status
        self._write_yaml_atomic(self.active_path(item_id), item)
        # A DISPATCH LEASE IS BOUND TO THE STATUS IT SERVES. Deferred import for the same reason
        # `approvals` is deferred: `dispatch` imports this module. Without this, `transition
        # TSK-0001 READY` off LEASED left a live lease behind that `create_lease` then refused the
        # task on for its whole TTL, and `validate` called that state green -- see
        # `dispatch.release_lease_for_status_locked` for the measurement.
        from . import dispatch
        dispatch.release_lease_for_status_locked(self, item_id, to_status)
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
        """Move a TERMINAL item to archive/<TYPE>/<year>/ (never delete)."""
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
        index_path = self.generated_path("index.yaml")
        self._write_yaml_atomic(index_path, {"generated_at": _now_iso(), "items": rows})
        return index_path


_AUTOMATON_TYPES = frozenset(
    ("PR", "RQ", "FR", "CR", "BUG", "SR", "TSK", "PROC", "HYP", "EXP")
)

# status-bearing types WITHOUT an automaton (spec II.2 Pflichtfelder): the FIRST value of each
# vocabulary in `backlog_types.NON_AUTOMATON_STATUSES`, derived rather than retyped -- the two
# used to be one map here and one sentence in a comment, and the comment was the only place a
# reader could learn that `DEC` also has `SUPERSEDED`.
_NON_AUTOMATON_INITIAL_STATUS = {item_type: values[0]
                                 for item_type, values in NON_AUTOMATON_STATUSES.items()}


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

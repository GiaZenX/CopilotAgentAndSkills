"""The V1 -> V2 import (spec II.10), as a kernel operation rather than a script beside the harness.

WHY IT IS A KERNEL COMMAND AND NOT A TOOL. A migration rewrites canonical state, and every other
writer of canonical state in this harness goes through `ProjectState`: the status automaton, the
approval hashes, the id allocator and the index all hang off it. A migration tool living outside
would be the one write route no gate sees -- `gate_write_scope` refuses tool writes under the state
directory precisely so that there is exactly one, and a second one carrying the word "migration"
would not be a smaller hole for being well meant. So the import is `migrate` on the entry point,
the lead runs it itself, and everything it writes is written by the same `capture` a role uses.

WHAT IT TRANSLATES, as a property rather than as a list of file names. The kernel does not know
what a "V1 file" is and deliberately never learns: it knows what a V1 RECORD is.

    A V1 record is a mapping that identifies itself with a `<TYP>-nnnn` id -- as its key in an
    enclosing mapping, or in its own `id` field -- and carries a `status`. It is TRANSLATABLE
    exactly when `backlog_types.map_v1_status` answers for `(TYP, status)`.

WHERE THE MAPPING LIES IS NOT PART OF THAT DEFINITION, and for one revision the code read it as if
it were: the `id` field was consulted for LIST members only, so a mapping sitting in a value
position under an ordinary key and naming itself in its own `id` field was found by nobody. See
`scan_document` for the measurement and for what the two positions now share.

That table is spec II.10's own, it is machine-readable, and it is the only place in this harness
where a V1 vocabulary is written down. Everything follows from it: `process_definitions.yaml`,
`tasks.yaml` and `product_requirements.yaml` are found because of what is INSIDE them, and a V1
kit whose monolith this code has never seen is found the same way.

WHEN THE TABLE HAS NO ANSWER THERE ARE TWO DIFFERENT FINDINGS, and telling them apart decides
whether a project can be migrated at all. A type the table HAS rows for, with a status it does not
know, is a backlog record this harness does not understand: the run BLOCKS (spec II.10: "unbekannte
Werte -> Block + Decision-Item, nie raten"). A type with no row anywhere is not a backlog record --
a dev project's `acceptance_reports.yaml` keys each report `ACC-nnnn` and each criterion of it
`AC-<n>` with a `status`, and the first cut of this module treated those as unmappable backlog
items and blocked the whole migration of a project whose QA reports were simply QA reports. Such a
record is REPORTED and skipped, never imported and never a blocker. That example is measured, not
imagined: `_is_backlog_type` names the field reading it comes from.

EVERYTHING CARRYING THE ID SHAPE IS REPORTED, whether or not it is translated. That is the whole
promise of the reading half, and it has no depth limit, no "found one, stop looking here" and no
silent skip: a document this command cannot parse for records is named as unsearched, an
unreadable one refuses the run, and a record nested inside another record is found. Silence about
something id-shaped is the one outcome that would make the report unusable, because a reader
cannot tell it from an absence. WHICH FILES THAT COVERS IS NOT DECIDED HERE AND NOT DECIDED TWICE:
`search_coverage` gives every file under the state root exactly one verdict, this command and the
SR-0001 scan in `report` both read it, and what it names as unsearched and what it deliberately
leaves out -- with the residual that leaves -- is argued there rather than restated here.

WHAT IT REFUSES TO DECIDE, and this is the half the command exists for. A V1 record's FIELDS do not
map onto a V2 type's field contract by any rule anybody has written down, in this repo or in the
spec. `REQUIRED_FIELDS["PROC"]` asks for `roles`; a V1 PROC carries `owner`. Guessing that those
are the same field is exactly the kind of quiet decision that makes a migration unreviewable, so
this module does not: a field carries over when BOTH contracts spell it the same way, and every
remaining required field is reported as a decision with the `--map` flag that would settle it. The
dry run prints those flags; the human types them; the executed run is then mechanical. ONE
EXCEPTION, and it is not a decision about the record: a required field whose subject is where the
record CAME FROM is the importer's own fact -- see `PROVENANCE_FIELDS` for why that is a field name
rather than a type, and why leaving it to `--map` would have been a dead end.

WHAT AN IMPORTED ITEM LOOKS LIKE, and why it is not the V1 status. Spec II.10: "importierte Items
behalten ihren regulaeren Anfangsstatus und tragen das FLAG `migration_confirmation_required: true`
+ `approval_ref: null` -- KEIN neuer Status; nur echte Useraktion erzeugt APR". So an imported PROC
arrives in DRAFT even when V1 called it ACTIVE, the V1 value and the whole V1 record are preserved
verbatim under `legacy_fields`, and `map_v1_status`'s answer is recorded there as what the V1
status WOULD mean -- a note, not a position on the automaton. The consequence is worth stating
plainly rather than discovering: this command does not unblock `gate_proc_approved`. It makes the
procedures reachable; the user approves them afterwards, one `request-approval scope` at a time,
and that is the only thing that can mint an APR.

...EXCEPT FOR A RECORD THAT IS ALREADY FINISHED, which is SR-0004 and which the initial-status rule
alone gets wrong. Measured across two field projects: 260 of 264 tasks in one and 162 of 165 in the
other are DONE. Writing all of them into `tasks/active/` at DRAFT buries the four that are alive
under the ones that are not, and says the opposite of what V1 recorded. So a record spec II.10's
mapping table marks as FINISHED (`archive_candidate`) is written straight into
`archive/<TYPE>/<year>/` at its mapped status, by `state.capture_migrated_archive`, and the
per-item FIELD contract does not apply to it (DEC-0004) -- a V1 task is missing ten of eleven
required fields, and no rule turns a line on a list into a work order. Which records qualify, which
bolts hold that exemption in place, and which V1 statuses are deliberately NOT archivable (the ones
only a user approval could have reached) are argued at `state.migration_archive_status`; the year
comes from the record's own dates and is never guessed (`_record_year`).

A V1 PARENT CHAIN IS THE NORMAL SHAPE and is what forced planning into two phases. The bindings
between records are resolved against the state the run WILL have reached rather than the one it
starts in, the writes are ordered so a parent exists before its child, a cycle is refused, and each
binding is rewritten to the id the parent ACTUALLY got -- V2 allocates ids, so the V1 number is not
the V2 number. A binding whose target is in neither the plan nor the store is refused exactly as
before. `_settle_bindings` carries all of it, including the defect it is the correction of.

WHERE THE BOOKKEEPING GOES. One `DEC` item per run, written by the same `capture` as everything
else, naming every source it read (with its content hash), every id range it created, the flags it
was given and everything it left alone. A Decision item is what this harness already uses for "a
choice was made about the state, here is the record of it", it is canonical state, and it survives
in git -- which is what a migration run needs and what a log line on somebody's terminal is not.
Per-record traceability is NOT in that item and deliberately so: it lives in each imported item's
own `legacy_fields`, so the receipt stays bounded by the number of source FILES while a project
with nine hundred records keeps a complete trail.

WHAT HAPPENS TO WHAT IT CANNOT TRANSLATE -- the third way, because throwing it away and dragging it
along are both wrong. A V1 filing log with nine hundred entries has no V2 counterpart and never
will: it is not a backlog, it is a business record. It is left exactly where it is, untouched and
unrenamed, and INVENTORIED in the run's Decision item with its byte size and its content hash, so
a later audit can tell whether the file it is reading is the file the migration saw. That is the
whole of it, and the limit is named here rather than left to be found: spec II.10 also asks for a
fail-closed integrity guard that BLOCKS writes to those retained files, and this module builds no
such guard -- nothing stops a later session from editing them.

NO APPROVAL KIND FITS THIS, which is a finding rather than an omission, and the kinds are named
by asking rather than by counting -- an earlier draft of this paragraph said "the five" over a
vocabulary of six and put `analysis` among the item-bound ones, which it is not. Everything
`approvals.item_derived_kinds()` returns is bound to an ITEM and hashes that item's own fields; a
migration has no item, it creates them. `analysis` is not in that set precisely because its subject
is an analysis question, a read-only scope and a cadence, none of which a migration has. `routine`
is a standing licence for a RECURRING run, so minting one for a one-off would leave the licence
behind afterwards. What `approvals.line_manifest_kinds()` returns is about publishing a commit.
Rather than bend any of them, the consent this command carries is structural: the dry run changes
nothing and prints a DIGEST, and the executing run refuses unless it re-derives that same digest.
What the digest is taken over is stated where it is built (`state_fingerprint`), not here, because
a second statement of a coverage claim is how the first one comes to be wrong. A state that moved
between the reading and the writing cannot be migrated on the strength of the reading -- and a
human who never read the dry run has no digest to type. That is weaker than an APR in one specific
way, and the difference is named here so that no text has to imply otherwise: it proves the STATE
is unchanged, not that a user consented.

NOT ATOMIC, RESUMABLE, AND NEVER SILENT ABOUT A PARTIAL RUN. `capture` takes the kernel lock per
item and the lock is not reentrant, so a run of N records is N locked writes rather than one. Two
things carry that:

  * every record is put through the PREFLIGHT OF THE METHOD THAT WILL WRITE IT
    (`state.capture_preflight`, or `capture_migrated_archive_preflight` for an archive-bound one)
    at PLANNING time, so the plan cannot promise a run the writer will refuse. Measured before that
    existed: a dev project with a V1 `system_requirements.yaml` planned READY, wrote three items and
    died on the fourth, because every record of that store names `derives_from: PRD-0001` and `PRD`
    is no V2 type. Three items in the state, no receipt, and a raw kernel message that never
    mentioned either.
  * what no reading can rule out -- a lock, a disk, an interrupt -- still leaves the run half done,
    so `execute` writes the receipt for what it DID create and refuses with a message that names
    those ids. Idempotency is what makes that safe rather than a transaction: a record counts as
    imported when an item already carries its id in `legacy_fields.legacy_id`, so a second run
    picks up exactly where the first stopped and a completed run reports there is nothing to do.
    That id is the WHOLE key, and it was the pair (source document, id) for a round: renaming the
    V1 file then made every record of it unseen again, so the same records imported a second time
    as new items. A known id arriving under a different path is now a FINDING with both paths in
    it -- see `build_plan` -- because this command cannot tell a moved file from a copied one and
    guessing either way writes something nobody can undo.
"""
from __future__ import annotations

import copy
import datetime
import hashlib
import os
import re
import textwrap

import yaml

from . import layout
from .backlog_types import (
    ACTIVE_DIRS,
    LEGACY_FIELD,
    MIGRATION_FLAG,
    OPTIONAL_FIELDS,
    PARENT_FIELDS,
    REQUIRED_FIELDS,
    ROOT_TYPE_BY_KIT,
    UnknownV1Status,
    format_id,
    map_v1_status,
    suggested_v1_field,
    v1_types,
    widest_status,
)
from .hashing import canonical_json
from .report import ITEM_MAX_BYTES, ITEM_MAX_LINES
from .state import ProjectState, StateError, migration_archives

# The V1 id shape, as a PROPERTY of how V1 numbered records rather than as the shape V2 allocates.
# Wider than `backlog_types._ID_RE` in three directions, each for its own measured reason:
#
#   * the TYPE is not checked against any list. V1 types that V2 renamed (`PRD`) must still parse,
#     and `map_v1_status` is the only judge of whether a type is known -- it is the spec's table.
#   * the number has no fixed width. V1 had no allocator and no formatter.
#   * ...and for the same reason it has an optional DISCRIMINATOR: V1 numbers were typed by hand
#     into an ordered document, so a record inserted between `TSK-0017` and `TSK-0018` was named
#     `TSK-0017b` rather than renumbering everything after it. That is the SAME id shape used the
#     way a hand-kept list uses it, not a different kind of name.
#
# WHAT THE DISCRIMINATOR AND THE FREE WIDTH EACH COST WHILE THEY WERE MISSING is measured rather
# than retold here: `test_migrate.test_a_hand_numbered_v1_id_is_a_record_and_not_a_silence` and
# `test_the_recogniser_reads_every_id_width_a_hand_kept_list_produces` are the two, and both name
# the field reading behind them.
#
# THE COUNTER-DIRECTION, since widening a recogniser is how the opposite defect gets in: the
# separator, the case and the discriminator's position are unchanged, so nothing that is not
# `<UPPERCASE TYPE>-<digits>` starts matching -- a lower-case `unavailable_503` or `tablet_768` in
# a design document is not an id and is not read as one. A record whose id this reads and whose
# type no table knows is reported as `not_an_item` by the same rule as before: it is not imported
# by being recognised.
V1_ID_RE = re.compile(r"([A-Z]{2,4})-(\d+)([A-Za-z][A-Za-z0-9]*)?\Z", re.ASCII)

STATUS_FIELD = "status"
# Both live in `backlog_types` because `state.capture_migrated_archive` reads them too; re-exported
# here under the names this module's callers and tests already use.
CONFIRMATION_FLAG = MIGRATION_FLAG

# THE ONE KIND OF REQUIRED FIELD AN IMPORT MAY ANSWER ITSELF, and it is spelled as a FIELD NAME
# rather than as a type because the name means the same thing in every contract that carries it: a
# field whose subject is where the record CAME FROM, not what the record says. The importer is the
# only writer that knows that, V1 recorded it in no field, and `--map` cannot settle it because
# there is no V1 field to name -- which would leave every `decisions.yaml` in the field permanently
# untranslatable (DEC-0002: 106 measured records). A `--map` for the same field still wins, so a V1
# store that DOES carry its own provenance is not overwritten by this.
#
# Everything else stays a decision. Nothing here infers a field from a similar name, and a required
# field that is about the record's CONTENT is never filled by this module.
PROVENANCE_FIELDS = frozenset(("source",))

# WHAT A YEAR IS IN THIS MODULE, written once and read by both things that produce one: the date
# inside a V1 record, and the `--archive-year` flag. It went unwritten for the flag, and `int` was
# the only judge -- so `--archive-year 12` filed items under `archive/<TYPE>/12/` and a negative
# value produced a directory name a path builder should never have been handed. Four digits is not
# a range somebody picked here; it is the shape `_DATE_RE` already reads a year in, so the flag and
# the record answer the same question in the same terms.
_YEAR_RE = re.compile(r"\d{4}", re.ASCII)
# What a printed archive path says where the year is not settled yet. Its own name because
# `archive_location` is the only composer of that path and two spellings of the placeholder would
# make two shapes of one sentence.
_YEAR_PLACEHOLDER = "<year>"
# A date-shaped value inside a V1 record. Used only to answer "which archive YEAR" and only where
# the record itself carries a date; see `_record_year`.
_DATE_RE = re.compile(r"\b(%s)-\d{2}-\d{2}\b" % _YEAR_RE.pattern, re.ASCII)

# The receipt's own type. `DEC` is the harness's existing "a choice was made about the state"
# item -- it has no automaton to walk, no approval to obtain and no parent to bind, which is
# exactly the shape a run record needs.
RECEIPT_TYPE = "DEC"

_DOCUMENT_SUFFIXES = (".yaml", ".yml")


class MigrationError(StateError):
    """The migration refused. Same exit channel as every other kernel refusal (cli: 1)."""


# -- reading the state directory ------------------------------------------------------------------


def _relative(state: ProjectState, path: str) -> str:
    return os.path.relpath(path, state.root).replace(os.sep, "/")


def documents(state: ProjectState) -> list:
    """Every KIT DOCUMENT under the state root, state-relative, sorted.

    `layout.is_project_document` is the definition and it is not restated here: a document is what
    no kernel path builder can name, minus the dotted machinery and minus `staging/`. That is the
    same predicate `gate_write_scope` refuses tool writes with, so what this command inventories
    and what a role is refused are one answer.
    """
    found = []
    for dirpath, dirs, files in os.walk(state.root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in sorted(files):
            rel = _relative(state, os.path.join(dirpath, name))
            if layout.is_project_document(state.root, rel):
                found.append(rel)
    return sorted(found)


# The four answers `search_coverage` gives, and there is no fifth: every file under the state root
# gets exactly one of them. `SEARCHED` and `UNSEARCHED` are what a reader is told about; `KERNEL`
# and `MACHINERY` are the two areas that are not V1 documents at all and are named here so that
# "not reported" is a decision with a name rather than a branch that fell through.
SEARCHED = "searched"
UNSEARCHED = "unsearched"
KERNEL = "kernel"
MACHINERY = "machinery"


def search_coverage(state: ProjectState) -> list:
    """[(state-relative path, verdict, why)] for EVERY file under the state root, sorted.

    THE RUN-UP OF THE RECORD SEARCH, AS ONE ANSWER FOR ITS TWO READERS. `build_plan` and
    `report._check_no_v1_records_outside_the_archive` both have to decide which files a V1 record
    search may look at, and for one round each decided it for itself. Measured 2026-08-07 with the
    same `PROC-0001` record laid down in seven places of one state: three of them (a kit document,
    one in a subdirectory, one spelled `.yml`) were reported by both, and FOUR -- another suffix, a
    dotted path, `staging/`, and a dotted path again -- were reported by the dry run, by the
    validator, or by neither, in three different combinations. Two readers of one question is how
    they came to contradict each other about one file, which is the thing the round before this was
    supposed to have ended.

    THE VERDICT IS TOTAL, and that is the property rather than the list of exclusions: this walks
    every file and each one comes back with a name for what happened to it. A skip that reports
    nothing has to be spelled as `KERNEL` or `MACHINERY` here, in front of both readers, instead of
    being a `continue` in one of them.

    WHY THE FOUR, in the order they are asked:

      * a DOTTED segment that is not YAML is MACHINERY -- `.kernel.lock`, `.audit/hook_events.jsonl`,
        the `.gitkeep` in every empty item directory. Nothing puts a V1 record there and naming
        them would bury the two answers that matter under one line per directory. This is the
        residual, and it is the same one this module has carried since the dotted walk was added: a
        V1 record in a dotted file that is not YAML is in no report.
      * a DOTTED segment that IS YAML is UNSEARCHED. `.legacy/old_procs.yaml` is a hiding place,
        not machinery.
      * a KERNEL-written path is the kernel's own writing (`layout.is_kernel_written`, asked of the
        writers' path builders) -- items, `generated/`, `approvals/`, `archive/` and the `legacy/`
        the import itself moves absorbed documents into. A V1 record cannot be "twice" in the store
        that holds it once.
      * everything else is a project file: UNSEARCHED when it is not a YAML document (the record
        search reads YAML, and a store renamed to `tasks.yaml.bak` is out of its reach) or when it
        lies under `staging/` (spec II.4's proposal area, which is not state and whose files are
        proposals for items -- searching them would report every staged item body as a V1 record),
        and SEARCHED otherwise.
    """
    coverage = []
    for dirpath, dirs, files in os.walk(state.root):
        dirs[:] = sorted(dirs)
        for name in sorted(files):
            rel = _relative(state, os.path.join(dirpath, name))
            coverage.append((rel,) + _coverage_of(state, rel))
    return sorted(coverage)


def _coverage_of(state: ProjectState, rel: str) -> tuple:
    """(verdict, why) for one state-relative path -- the rule `search_coverage` documents."""
    is_yaml = rel.lower().endswith(_DOCUMENT_SUFFIXES)
    parts = rel.split("/")
    if any(part.startswith(".") for part in parts):
        if not is_yaml:
            return (MACHINERY, "a dotted path that is no YAML document")
        return (UNSEARCHED,
                "it lies under a dotted path, which this harness treats as machinery and does not "
                "search; move it out of there if it holds V1 records")
    if layout.is_kernel_written(state.root, rel):
        return (KERNEL, "written by the kernel itself, so it is not a V1 document")
    if not is_yaml:
        return (UNSEARCHED,
                "it is no YAML document (a V1 record is read out of %s), so nothing here can say "
                "whether it holds one; rename it back if it is a V1 store"
                % " or ".join(_DOCUMENT_SUFFIXES))
    if parts[0] == layout.STAGING_DIRNAME:
        return (UNSEARCHED,
                "it lies under `%s/`, spec II.4's proposal area: what is there is a proposal and "
                "not state, and an item body staged for capture would read as a V1 record; move it "
                "out of there if it is a V1 store" % layout.STAGING_DIRNAME)
    return (SEARCHED, "")


def unsearched_notes(coverage) -> list:
    """[(path, why)] for the files a record search cannot look at -- one wording, both readers."""
    return [(rel, why) for rel, verdict, why in coverage if verdict == UNSEARCHED]


def _file_facts(state: ProjectState, rel: str) -> dict:
    path = os.path.join(state.root, *rel.split("/"))
    with open(path, "rb") as handle:
        raw = handle.read()
    return {"path": rel, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _declared_id(node):
    """The id a mapping states in its OWN `id` field, or None.

    Asked of the mapping and of nothing around it, which is the whole point: the field means the
    same thing wherever the mapping sits, and reading it in one position only is what made the
    third id form a silence (see `scan_document`).
    """
    value = node.get("id")
    if isinstance(value, str) and V1_ID_RE.match(value.strip()):
        return value.strip()
    return None


def _keyed_id(key):
    """The id a mapping is FILED UNDER, or None -- the other half of the same self-identification."""
    if isinstance(key, str) and V1_ID_RE.match(key.strip()):
        return key.strip()
    return None


def scan_document(payload):
    """[(ordinal, id, mapping)] for every self-identifying record in a parsed document.

    THE TWO WAYS A MAPPING NAMES ITSELF, asked of every mapping the walk reaches and never of its
    position: the KEY it is filed under, and its own `id` FIELD. Both are in the module head's
    definition of a V1 record, and both are read here for the same node.

    THIS USED TO BE A RULE ABOUT POSITIONS -- an id-keyed mapping value, or a LIST member with an
    `id` field -- and the third combination fell between them. Measured on the field copy of
    `synaipse` (2026-08-05): `review_reports.yaml` carries `wording_correction_needed: {id: "OQ-1",
    status: closed}`, a mapping in a value position naming itself in its own field, and it appeared
    under no heading of the dry run, in no `validate` finding and in no completeness count -- the
    one outcome this command may not produce. Widening the rule to the PROPERTY finds it and
    changes nothing else: across all three field copies it is the only record the position rule
    missed, and no record the position rule found is lost.

    A MAPPING THAT NAMES ITSELF THE SAME WAY TWICE IS ONE RECORD (`SR-0001: {id: SR-0001, ...}`,
    the ordinary shape of a store that repeats its key inside the entry). One that names itself
    with two DIFFERENT ids yields two entries over the same mapping, so neither name is a silence;
    `build_plan` refuses such a record rather than importing one mapping as two items.

    THE ORDINAL IS THE IDENTITY, not the id. Two records in one document may carry the same V1 id
    -- V1 had no allocator -- and keying the walk's result by id made the LAST one win: measured
    with both shapes in one file, the written item carried record B's fields under record A's
    legacy metadata, an item that never existed in V1, and record A was gone even from
    `legacy_fields.record`. The ordinal is stable because a YAML mapping parses in document order,
    so the record the plan classified is the record the run writes. (Such a document is refused
    outright as well -- see `build_plan` -- because two items claiming one `legacy_id` would break
    the idempotency scan too. The ordinal is what makes the refusal ACCURATE about which records
    collide rather than merely present.)

    THE WALK DOES NOT STOP AT A HIT, and that is a correction. It used to recurse only into values
    that were NOT records, so anything nested inside a record was invisible -- measured: a
    `PROC-0101` with an unknown status sitting inside `PROC-0100` appeared under no heading of the
    dry run at all, neither imported nor blocked nor reported, while the module promised that an
    unknown status blocks. Silence about a record is the one outcome this command may not produce.

    THERE IS NO DEPTH LIMIT, and that is the second correction. The first cut stopped at a
    hand-picked `_SCAN_DEPTH = 3`, and no value of it was defensible: the number was measured
    against nothing, and once the walk stopped skipping record bodies the same bound cut a real
    office `review_findings.yaml` in half (its `findings:` entries sit one level below where 3
    reaches). A limit that decides whether a project can be migrated may not be a number somebody
    liked.

    What the bound was actually guarding against is CYCLES -- `yaml.safe_load` will happily build
    a self-referencing structure out of an anchor -- and that is guarded against directly: every
    container is walked at most once, by identity. A repeated node is a YAML alias and loses
    nothing by being skipped, because the object it aliases was already scanned. The walk is then
    linear in the document, and "everything carrying the V1 id shape is reported" is a promise the
    code keeps at any nesting rather than down to a chosen level.
    """
    records, seen = [], set()

    def walk(node, keyed_as=None):
        if not isinstance(node, (dict, list)):
            return
        first_visit = id(node) not in seen
        if isinstance(node, dict):
            if keyed_as is not None:
                records.append((len(records), keyed_as, node))
            declared = _declared_id(node)
            # `first_visit` only for the DECLARED name: an alias reaches the same mapping under a
            # second key, and that second key is a second name; its own `id` field is not.
            if declared is not None and declared != keyed_as and first_visit:
                records.append((len(records), declared, node))
        if not first_visit:
            return
        seen.add(id(node))
        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, _keyed_id(key))
        else:
            for entry in node:
                walk(entry)

    walk(payload)
    return records


def _declares_status(record) -> bool:
    """Does this self-identifying mapping CLAIM to be a V1 item? -- the one definition, two readers.

    A record with no `status` is a cross-reference table, not a backlog entry, and the two places
    that have to agree on that are the claimant count (an id-keyed note may not make the real
    record a duplicate) and the classification that reports it. They disagreed for one revision,
    and the direction of the disagreement was a whole migration blocked by a table of notes.

    IT ASKS WHETHER THE FIELD IS THERE, NOT WHETHER IT IS READABLE, and that split is the
    correction of 2026-08-04. This used to demand `isinstance(status, str)`, so a record carrying
    `status: 7`, or the unquoted `NO` that PyYAML parses as a boolean, was reported as "carries no
    `status`" -- untrue about the record, and it dropped a record of a KNOWN backlog type out of
    the count of claimants for its own id. What an unreadable status means for the RUN is a
    separate verdict; see `_status_text` and its caller. A YAML null is the absent case: `status:`
    with nothing after it says as little as no key at all.
    """
    return isinstance(record, dict) and record.get(STATUS_FIELD) is not None


def _is_backlog_type(legacy_type: str) -> bool:
    """Is a record of this type a BACKLOG record at all? -- asked of both maps, in one place.

    Two maps answer half of it each and neither alone is the question: `v1_types` says the V1
    status vocabulary is known, `REQUIRED_FIELDS` says the kernel captures items of this type. A
    type in either is a backlog type whose records this harness owes an answer about; a type in
    neither is something else that happens to use the id shape. Spelled once because two branches
    of the classification ask it, and for a revision they asked it in two spellings.

    THE EXAMPLE IS FIELD DATA, and it replaces an invented one that stood in seven places (a
    `PROD-nnnn` product catalogue the office kit does not ship: its template's only entry is
    commented out, is spelled `PRD-A0001` and does not even match the id shape). A dev project's
    `acceptance_reports.yaml` keys each report `ACC-nnnn` and each criterion of it `AC-<n>`, with a
    `status` on the criteria; neither type is one any contract here knows, and treating them as
    unmappable backlog items blocked the whole migration of a project whose QA reports were simply
    QA reports. The counts behind that sentence are recorded once, in the fixture built from it --
    `test_migrate._fill_acceptance_reports` -- rather than here.
    """
    return legacy_type in v1_types() or legacy_type in REQUIRED_FIELDS


def _status_text(record):
    """The V1 status this record states, or None when the value is not text this run can map.

    The mapping table is keyed by a STRING, so a value that is not one cannot be looked up in it
    however plausible it looks -- and spec II.10's rule for a value a known backlog type cannot be
    mapped from is to BLOCK, never to guess. Kept apart from `_declares_status` so that neither
    answer has to stand in for the other.
    """
    status = record.get(STATUS_FIELD) if isinstance(record, dict) else None
    if isinstance(status, str) and status.strip():
        return status.strip()
    return None


def _read_document(state: ProjectState, rel: str):
    """(parsed payload, why the read produced no payload) -- `problem` is None exactly when the
    bytes on disk were turned into a payload.

    THE CONTRACT IS ABOUT THE READ, NOT ABOUT THE PAYLOAD, and the sentence it replaces said
    "exactly one of the two is None": an EMPTY document parses to `None`, so both were, and the
    only thing that told the two apart was that one of them never returned at all. Measured, and
    `test_migrate.test_the_readers_contract_holds_for_an_empty_document_and_for_every_failure`
    is where both directions are recorded.

    WHAT ENDS A READ IS NOT A LIST THIS MODULE KEEPS. It used to be `(OSError, yaml.YAMLError)`,
    and the class that is neither cost the whole reading half: a kit document a Windows editor
    saved as UTF-16 or as ANSI raised `UnicodeDecodeError` (a `ValueError`) straight through the
    plan, the validator and the merge gate. Measured 2026-08-07 on the shipped
    `gate_memory_complete` as a process: rc 2 as an INTERNAL ERROR with a traceback and without
    the file's name in it, `validate` exit 1 printing one codec line and no finding, `build_plan`
    raising. The way to that state is the remedy the neighbouring refusals themselves print --
    repair the file in an editor outside the session. So the rule here is the property: turning a
    foreign file into a payload is a statement about the FILE, and every way it can fail is
    reported as one.

    THE ENCODING QUESTION IS THE YAML READER'S, which is why the bytes go in unchanged. A YAML
    stream declares its own encoding by a BOM, and `yaml.safe_load` implements that when it is
    handed bytes -- so what the format calls a stream reads, and what does not is a `ReaderError`
    naming the offending byte. Decoding here first would have been this module picking a codec,
    which is the guess the same module refuses to make about a status.

    THE REASON NAMES NO PATH -- built rather than asserted, because the assertion was measured
    false: `yaml.safe_load` names its stream in every mark, so reading through an open file made
    the reason carry the absolute path, and `report`'s finding then said the name twice (its
    `item` IS the path). Everything the exception says is kept; the one string this function
    opened the file with is replaced by a placeholder, and the result is folded onto one line
    because its readers print one finding per line.

    ITS CALLERS EACH PUT THE NAME WHERE THEIR OWN READER EXPECTS IT -- `build_plan` in the plan's
    `unreadable` list, `imported_legacy_ids` in the same list with what the blindness would cost,
    `execute` in its refusal, `render` in the wall listing, and
    `report._check_no_v1_records_outside_the_archive` in a per-document finding. That list is a
    claim about the code, so it is checked as one: the previous version of this paragraph counted
    three and there were four, and `test_migrate.test_the_readers_docstring_names_every_caller_it_has`
    reads the call sites out of the modules rather than out of this sentence.
    """
    path = os.path.join(state.root, *rel.split("/"))
    try:
        with open(path, "rb") as handle:
            return yaml.safe_load(handle.read()), None
    except Exception as exc:                 # noqa: BLE001 -- see the docstring: this is the point
        return None, "could not be read (%s: %s)" % (type(exc).__name__,
                                                     _without_path(str(exc), path))


def _without_path(text: str, path: str) -> str:
    """`text` on one line, with the path this module opened replaced by a name for it.

    The path is removed rather than filtered out of a pattern: the caller of `_read_document`
    already holds the document's name, and the only path that can be in there is the one this
    module composed and handed to `open` -- so it is known exactly, not guessed at.

    TWO SPELLINGS OF ONE STRING, both derived from it rather than listed: a message that quotes
    the name writes it as Python writes a string LITERAL, so `FileNotFoundError` on Windows
    carries `C:\\\\dir\\\\file` where the YAML mark carries `C:\\dir\\file`. Removing only the
    first was measured by this function's own test before it shipped.
    """
    spellings = sorted({path, repr(path)[1:-1]}, key=len, reverse=True)
    for spelling in spellings:
        text = text.replace(spelling, "this document")
    return " ".join(text.split())


# -- what is already imported ---------------------------------------------------------------------


def imported_legacy_ids(state: ProjectState):
    """({(source, legacy_id): item id}, [why a kernel file could not be read]) -- the idempotency
    scan, and what it could not see.

    Read off the items themselves rather than from a manifest file. A manifest would be a second
    statement of the same fact, and the failure mode of a second statement is that it is the one
    that is wrong: an item deleted by hand would leave the manifest claiming an import that is not
    there, and a re-run would then skip a record nothing holds. The items ARE the record.

    A FILE IT CANNOT READ IS NAMED, and it used to be a bare `continue`. This map is the whole of
    "has this record already been imported": an item skipped here is an item whose `legacy_id` the
    plan does not know, so the record it came from is planned as NEW and the run writes a second
    item for one V1 record -- silently, and against the one promise a re-run makes. The reason
    joins `build_plan`'s `unreadable`, which is what makes the plan refuse instead.
    """
    seen, unreadable = {}, []
    for dirpath, dirs, files in os.walk(state.root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        rel_dir = _relative(state, dirpath)
        if rel_dir.split("/")[0] == layout.STAGING_DIRNAME:
            continue
        for name in sorted(files):
            if not name.endswith(".yaml"):
                continue
            rel = _relative(state, os.path.join(dirpath, name))
            if not layout.is_kernel_written(state.root, rel):
                continue
            item, problem = _read_document(state, rel)
            if problem:
                unreadable.append(
                    "%s %s -- this run reads every item the kernel wrote to find out which V1 "
                    "records are already imported, so a file it cannot read would let a record be "
                    "imported a second time" % (rel, problem))
                continue
            legacy = (item or {}).get(LEGACY_FIELD) if isinstance(item, dict) else None
            if isinstance(legacy, dict) and legacy.get("legacy_id"):
                seen[(str(legacy.get("legacy_source") or ""),
                      str(legacy["legacy_id"]))] = item.get("id")
    return seen, unreadable


# -- the field decision ----------------------------------------------------------------------------


def parse_field_map(entries) -> dict:
    """`TYPE.v2_field=v1_field` -> {(TYPE, v2_field): v1_field}, or a MigrationError.

    Flag-shaped rather than a body on stdin, unlike `capture`: this is a handful of scalar pairs
    the DRY RUN itself prints, so what a human does with it is paste a line back, and a line is
    what a shell carries best.
    """
    mapping = {}
    for entry in entries or []:
        left, sep, right = str(entry).partition("=")
        item_type, dot, field = left.partition(".")
        if not (sep and dot and item_type and field and right):
            raise MigrationError(
                "--map %r is not a mapping. Remedy: spell it TYPE.v2_field=v1_field, e.g. "
                "`--map PROC.roles=owner`; `python scripts/harness.py migrate --dry-run` "
                "prints the exact flags this state needs." % (entry,))
        if item_type not in REQUIRED_FIELDS:
            raise MigrationError(
                "--map %r names type %r, which the kernel does not capture. Remedy: use one of "
                "%s." % (entry, item_type, "/".join(sorted(REQUIRED_FIELDS))))
        contract = set(REQUIRED_FIELDS[item_type]) | set(OPTIONAL_FIELDS.get(item_type, ()))
        if field not in contract:
            raise MigrationError(
                "--map %r names %s field %r, which is not in that type's contract. Remedy: use "
                "one of %s." % (entry, item_type, field, ", ".join(sorted(contract))))
        mapping[(item_type, field)] = right
    return mapping


def _item_fields(v2_type: str, record: dict, field_map: dict, provenance=None):
    """(fields, missing) -- the V2 item body this V1 record yields, and what it still lacks.

    THE RULE, and it is the whole of the field policy: a field carries over when both contracts
    spell it the same, or when `--map` says which V1 field it is. Nothing is inferred from a
    similar name, a similar type or a position. `missing` is what the dry run turns into flags.

    THE ONE EXCEPTION IS NOT A GUESS ABOUT THE RECORD: a required field in `PROVENANCE_FIELDS` is
    about where the record came from, which is the importer's own fact and nobody else's. See that
    constant for why it is a field name rather than a type. `--map` still wins over it.

    DEEP-COPIED, and this is not hygiene. The same V1 record is read twice -- once for the item's
    own fields and once for the verbatim copy under `legacy_fields` -- and handing out the same
    list object twice made `yaml.safe_dump` write an ANCHOR and an ALIAS (`steps: &id001` /
    `steps: *id001`, measured in a real imported PROC). The file is still valid YAML, but the two
    fields are then ONE object on the way back in, so editing the item's `steps` through the
    kernel would silently rewrite the legacy record that exists to say what V1 held.
    """
    fields, missing = {}, []
    contract = list(REQUIRED_FIELDS[v2_type]) + list(OPTIONAL_FIELDS.get(v2_type, ()))
    required = set(REQUIRED_FIELDS[v2_type])
    for name in contract:
        source = field_map.get((v2_type, name), name)
        if source in record:
            fields[name] = copy.deepcopy(record[source])
        elif name in required and name in PROVENANCE_FIELDS and provenance:
            fields[name] = provenance
        elif name in required:
            missing.append(name)
    return fields, missing


def _field_suggestions(legacy_type: str, record: dict, missing) -> dict:
    """{v2 field: (v1 field, why)} for the missing fields this V1 store has a proposal for.

    TWO CONDITIONS, and the second is what keeps a suggestion from being a guess about THIS record:
    `backlog_types.V1_FIELD_SUGGESTIONS` has to hold a row for the store's own V1 type, and the
    record in front of us has to actually carry that V1 field. A row is a statement about what a
    kit's V1 template shipped; a record that never filled the field is answered by nothing, and
    proposing a flag that would carry nothing is the same silence with a friendlier name.

    A `--map` the human already typed is not in `missing` by then, so it wins by construction
    rather than by a precedence rule spelled here.
    """
    found = {}
    for name in missing:
        suggestion = suggested_v1_field(legacy_type, name)
        if suggestion and suggestion[0] in record:
            found[name] = suggestion
    return found


def _with_legacy(fields: dict, entry: dict, record: dict) -> dict:
    """The COMPLETE item body an import writes -- one definition, two callers.

    `build_plan` measures this shape against the item budget and `execute` writes it. Two
    assemblies of one body is how a plan comes to measure something the run does not write, so
    there is one.
    """
    body = dict(fields)
    body[LEGACY_FIELD] = {
        "legacy_id": entry["legacy_id"],
        "legacy_source": entry["source"],
        "legacy_type": entry["legacy_type"],
        "legacy_status": entry["legacy_status"],
        # what the V1 status WOULD mean in V2 terms -- recorded, never walked: the item starts at
        # its own initial status (spec II.10), and only a user action moves it from there.
        "mapped_status": entry["mapped_status"],
        "archive_candidate": entry["archive_candidate"],
        # WHERE THE RUN PUT IT, which is not the same question as `archive_candidate`: a record can
        # be finished in V1 and still land in active/, and on the shipped tables that happens for
        # two different reasons -- the status is one only a user approval could have reached
        # (`EXP DONE` -> `COMPLETED`), or the type has no automaton for this kernel to walk at all
        # (`ADR SUPERSEDED` -> a `DEC`). Both are `state.migration_archive_status`. The item says
        # which of the two answers it got rather than leaving a reader to re-derive them.
        "written_to": entry["target"],
        "record": copy.deepcopy(record),
    }
    if entry.get("unresolved_fields"):
        # DEC-0009's second archive door writes a record NOBODY could translate, so the item
        # carries the sentence that says so. `state.capture_migrated_unresolved` refuses a body
        # without it, which is why this is composed here and not there: the writer must not be
        # able to invent a reason for a record it never read.
        body[LEGACY_FIELD]["unresolved"] = entry["reason"]
    body[CONFIRMATION_FLAG] = True
    return body


def item_size(fields: dict, v2_type: str = RECEIPT_TYPE):
    """(bytes, lines) the kernel would write for this body -- the measure, without the verdict.

    Its own function so a test can compare it against a REAL captured item instead of against the
    verdict, which only speaks when the budget is already blown. That comparison is what caught the
    placeholders being one byte short; see `_too_large` for what they are now.
    """
    shape = dict(fields)
    shape.update({"id": format_id(v2_type, 9999), "status": widest_status(), "revision": 1,
                  "approval_ref": None, "created": "0000-00-00T00:00:00"})
    dumped = yaml.safe_dump(shape, sort_keys=False, allow_unicode=True)
    return len(dumped.encode("utf-8")), dumped.count("\n")


def _too_large(fields: dict, v2_type: str = RECEIPT_TYPE):
    """The reason this item body would exceed spec II.5's per-item budget, or None.

    Measured on the SHAPE THE KERNEL WILL WRITE -- the caller's fields plus placeholders of the
    kernel-set ones, dumped exactly as `ProjectState._write_yaml_atomic` dumps them -- rather than
    on the fields alone, so the answer is not a guess with a margin on top. The limits are
    `report`'s own constants, the same two numbers `validate` reports against; this exists so that
    a migration refuses to write an item the validator would immediately flag, instead of leaving
    a project with an oversized file no editing route can shrink.

    WHOSE ITEMS THAT COVERS is decided by the CALLER and is deliberately not this function's
    business -- see `_settle_bindings`, where an archive-bound record is not asked, and
    `_receipt_fields`, where the run's own `DEC` is.

    THE PLACEHOLDERS ERR UPWARDS, WHICH IS THE ONLY SAFE DIRECTION, and the previous ones did not:
    they were the literals `id: DEC-0000` and `status: VALID`, which are one byte SHORTER than a
    real `PROC-0001` / `DRAFT` -- measured constant at +1 B over three samples. A budget check that
    under-measures passes exactly the items that then fail `validate`. So the id is the widest this
    type's four-digit allocator produces and the status is the longest any shipped automaton
    carries. THE RESIDUAL, since this is the sentence that was wrong before: past 9999 items of one
    type an id grows by a digit, and this measure is short by that one byte per id.
    """
    size, lines = item_size(fields, v2_type)
    if size > ITEM_MAX_BYTES or lines > ITEM_MAX_LINES:
        return ("would be %d bytes / %d lines; spec II.5 caps an ACTIVE item at %d / %d, and "
                "`python scripts/harness.py validate` reports an active item above that as an "
                "error" % (size, lines, ITEM_MAX_BYTES, ITEM_MAX_LINES))
    return None


# -- the plan ------------------------------------------------------------------------------------


def archive_location(v2_type: str, year=_YEAR_PLACEHOLDER) -> str:
    """The state-relative DIRECTORY an archived item of this type is written into.

    ASKED OF THE PATH BUILDER, never composed a second time here, and that is the correction of a
    defect one filesystem hides: the three places that printed this composed `archive/<type>/` out
    of `v2_type.lower()`, while `ProjectState.archive_path` keys the directory by the id's own type
    -- so the run created `archive/PR/2026/` and told the reader `archive/pr/2026/`. On Windows and
    APFS the two open the same directory; on the case-sensitive filesystems the installers also
    support, the printed one is a path nobody finds. Composing it once, from the builder, is what
    makes the printed path and the created path one answer rather than two.

    `year` stays a placeholder where the caller has no year yet, so both readings come out of the
    same composer.
    """
    probe = ProjectState(os.curdir)
    directory = os.path.dirname(probe.archive_path(format_id(v2_type, 1), year))
    return os.path.relpath(directory, probe.root).replace(os.sep, "/") + "/"


def legacy_location(rel: str) -> str:
    """The state-relative path a fully absorbed V1 document is moved to (SR-0005).

    ASKED OF THE PATH BUILDER, for the same reason `archive_location` is, and it is the same
    defect one file further on: the dry run composed this target by hand (`"legacy/" + path`)
    while `_retire_absorbed_documents` moves the file to `ProjectState.legacy_path`. The two agree
    today -- that is a coincidence between two spellings, not a property, and the archive path
    above is what a coincidence like that looks like once a filesystem stops hiding it.
    """
    probe = ProjectState(os.curdir)
    return os.path.relpath(probe.legacy_path(rel), probe.root).replace(os.sep, "/")


def _archive_year_of(value, where: str):
    """`value` as an archive year, or a MigrationError naming where it came from.

    ONE JUDGE FOR THE TWO PRODUCERS (`_YEAR_RE` is the shape). The flag was checked by `int` alone
    and the record's own date by `_DATE_RE`, so the two disagreed about what a year is -- and the
    one that agreed with nothing is the one that reaches `ProjectState.archive_path`, which builds
    a directory name out of it.
    """
    text = str(value).strip()
    if not _YEAR_RE.fullmatch(text):
        raise MigrationError(
            "%r is not an archive year (%s). An item is filed under archive/<TYPE>/<year>/, and a "
            "year here is four digits -- the same shape this command reads out of a record's own "
            "dates. Remedy: give the four-digit year." % (value, where))
    return int(text)


def build_plan(state: ProjectState, field_map: dict = None, archive_year=None) -> dict:
    """Everything the run would read and do, as data. Reads the disk; writes nothing.

    Carries no timestamp and no absolute path on purpose: the digest below is taken over this
    object, and a plan that changed every second could not be handed back.

    TWO PHASES, and the second one exists because the first cannot answer its own question. The
    document loop classifies each record on its own; `_settle_bindings` then resolves the bindings
    BETWEEN records, orders the writes and asks the writer's verdict. See there for the defect that
    forced the split.
    """
    field_map = field_map or {}
    if archive_year is not None:
        # Refused HERE and not at the record that happens to need it: a flag nothing in this state
        # uses is still a flag the caller meant something by, and learning about it on the next run
        # is learning about it after the reading.
        archive_year = _archive_year_of(archive_year, "--archive-year")
    already, unreadable = imported_legacy_ids(state)
    already_by_id = {}
    for (source, legacy_id), item_id in sorted(already.items()):
        already_by_id.setdefault(legacy_id, []).append((source, item_id))
    inventory, records, carried_values = [], [], {}
    # WHICH FILES ARE SEARCHED IS NOT DECIDED HERE, and it was for a round: `search_coverage` is
    # the one run-up both this command and the validator read, so a file the two would classify
    # differently no longer exists. The inventory below is a different question -- what the run
    # READ and carries a hash of -- and is still `documents`.
    coverage = search_coverage(state)
    unscanned = ["%s (%s)" % pair for pair in unsearched_notes(coverage)]
    searched = {rel for rel, verdict, _why in coverage if verdict == SEARCHED}
    pending, parsed = [], []
    for rel in documents(state):
        inventory.append(_file_facts(state, rel))
        if rel not in searched:
            continue
        payload, problem = _read_document(state, rel)
        if problem:
            unreadable.append("%s %s" % (rel, problem))
            continue
        parsed.append((rel, scan_document(payload)))
    # A LEGACY ID NAMES ONE V1 RECORD, WHEREVER IT LIES -- so the claimants are counted over the
    # WHOLE run and not per document, and the same count is what the store is asked for below.
    # Per document was the first cut and it was half the rule: two documents each holding a
    # `PROC-0001` produced two items for one V1 record, which is the same unresolvable state as two
    # in one file. Reading the ids ahead of the classification loop is what lets the second record
    # be refused as well as the first; the alternative -- refusing whichever came later -- would
    # make the verdict depend on the walk order of a directory.
    #
    # ONLY ITEMS CLAIM AN ID, and "item" is TWO conditions rather than one.
    #
    # A mapping keyed by an id and carrying no status is a cross-reference table, which is why the
    # classification below reports it and never blocks on it -- and counting it as a claimant would
    # have turned exactly that document into a blocker for the whole run, one branch above the one
    # that exists to prevent it. `_declares_status` is the same question both places ask, and it
    # asks whether the field is THERE: a record whose status this run cannot read is still a
    # record, and dropping it out of the count here would let a second record take its id
    # unopposed.
    #
    # AND IT HAS TO BE A BACKLOG TYPE. A collision is a conflict about which ITEM gets the legacy
    # id, and a record of a type no contract knows never becomes an item at all -- `not_an_item` is
    # a FINAL answer about it, so two of them sharing a number conflict about nothing. Measured on
    # the field copy of `synaipse` (2026-08-05), and it is the counter-defect of reading one- and
    # two-digit numbers: `acceptance_reports.yaml` keys six of its acceptance criteria `AC-1` with
    # `status: met`, once per report, and the run refused sixty records -- and with them the whole
    # migration -- over a document whose entries this command never imports and which no `--map`
    # and no renumbering could help, because the ids are the criteria's own numbering inside each
    # report.
    claimants = {}
    # ...AND ONE MAPPING NAMES ITSELF ONCE, which is the same rule seen from the other side.
    # `scan_document` reads both ways a mapping can carry an id, so a mapping whose key and whose
    # own `id` field disagree arrives here twice. Counting the names per MAPPING (by object
    # identity -- `parsed` holds the parsed documents, so the objects stay alive) is what lets the
    # branch below refuse it instead of writing one V1 mapping into the store as two items. Across
    # all three field copies (2026-08-05) no mapping does this, so the branch costs those runs
    # nothing; it exists because the widened reader is what makes the shape reachable at all.
    self_named = {}
    for rel, found in parsed:
        for _ordinal, key, record in found:
            self_named.setdefault(id(record), set()).add(key)
            if _declares_status(record) and _is_backlog_type(V1_ID_RE.match(key).group(1)):
                claimants.setdefault(key, []).append(rel)
    for rel, found in parsed:
        for ordinal, key, record in found:
            entry = {"source": rel, "ordinal": ordinal, "legacy_id": key,
                     "legacy_type": V1_ID_RE.match(key).group(1)}
            names = self_named.get(id(record), {key})
            if len(names) > 1 and _declares_status(record) \
                    and _is_backlog_type(entry["legacy_type"]):
                # A DEFECT INSIDE THE RECORD, so it is decided before the ones about other records.
                # The condition is the claimant rule's own: a mapping that never becomes an item
                # cannot become two, so a criterion or a note wearing two ids is reported by the
                # branches below and blocks nothing.
                entry["verdict"] = "blocked"
                entry["reason"] = (
                    "this one mapping identifies itself with %d different ids (%s): a V1 record "
                    "names itself by the key it is filed under AND by its own `id` field, and "
                    "these disagree. Importing it would put the same V1 mapping in the store as "
                    "two items, and leaving one of the names unread would make it invisible to "
                    "this report. Remedy: in the V1 file, make the `id` field agree with the key, "
                    "or split the mapping into the two records it claims to be. Then re-run the "
                    "dry run." % (len(names), ", ".join("`%s`" % one for one in sorted(names))))
                records.append(entry)
                continue
            if len(claimants.get(key, ())) > 1:
                entry["verdict"] = "blocked"
                # THE REMEDY IS TWO BRANCHES BECAUSE THE SITUATION IS, and printing one of them for
                # both was measured wrong in both directions. "Split the document" was in here and
                # cannot help at all -- the claimants are counted over the WHOLE run, which the
                # comment fifty lines up says and this line contradicted. And "give them distinct
                # ids" is the right answer only when the two records really are two things: the
                # research kit's `fzulg_documentation.yaml` keys the BSFZ application layer by the
                # research question it documents, so every one of its entries collides with the
                # `research_questions.yaml` entry it is ABOUT -- renumbering it would import the
                # documentation as a second, parallel RQ backlog, one item per question that has
                # nothing to do with that question's life. For that shape the walkable answer is to
                # take the document out of the state directory before the run.
                entry["reason"] = (
                    "%s appears %d times in this run, in %s. Two items cannot both carry it as "
                    "`legacy_fields.legacy_id` -- that is the key a re-run recognises an import "
                    "by, and the count is over the whole run, so moving one of them into a "
                    "separate file changes nothing. Remedy: decide which of the two is a BACKLOG "
                    "RECORD. If both are, give one a distinct id in the V1 file. If one of them "
                    "describes the OTHER one under its id -- a second document keyed by the record "
                    "it documents -- it is not a backlog record at all and renumbering it would "
                    "import it as a second item for one subject: move that document out of the "
                    "state directory instead. Then re-run the dry run."
                    % (key, len(claimants[key]), ", ".join(sorted(set(claimants[key])))))
                records.append(entry)
                continue
            if not _declares_status(record):
                # An id-keyed mapping with no status is not a V1 ITEM -- a cross-reference table
                # looks exactly like one. Reported so it is not silently invisible, never
                # imported, and never a reason to block: blocking on it would make a document a
                # project cannot change into a migration it can never run.
                entry["verdict"] = "not_an_item"
                entry["reason"] = "carries no `%s`, so nothing maps it" % STATUS_FIELD
                records.append(entry)
                continue
            status_text = _status_text(record)
            if status_text is None:
                # DECLARED BUT UNREADABLE, which is neither of the two findings above and may not
                # be reported as either. Spec II.10 blocks on a value a known backlog type cannot
                # be mapped from, and this is that case one step earlier: the value is not even
                # text to look up. Which of the two findings it is still depends on the TYPE, by
                # the same rule the branch further down uses (`_is_backlog_type`): a record of a
                # type no contract knows is not a backlog record whatever its status says.
                unreadable_status = repr(record[STATUS_FIELD])
                if _is_backlog_type(entry["legacy_type"]):
                    entry["verdict"] = "blocked"
                    entry["reason"] = (
                        "carries a `%s` this run cannot read: %s is not text, and spec II.10's "
                        "mapping table is keyed by the V1 status STRING -- so nothing maps it and "
                        "nothing here guesses. `%s` is a backlog type, so this blocks rather than "
                        "being reported past. Remedy: quote the value in the V1 file (an unquoted "
                        "`NO`, `YES` or `ON` is a BOOLEAN to a YAML reader, not a status), then "
                        "re-run the dry run."
                        % (STATUS_FIELD, unreadable_status, entry["legacy_type"]))
                else:
                    entry["verdict"] = "not_an_item"
                    entry["reason"] = (
                        "carries a `%s` that is not text (%s), and `%s` is no backlog type this "
                        "harness knows either, so this is a record of some other kind"
                        % (STATUS_FIELD, unreadable_status, entry["legacy_type"]))
                records.append(entry)
                continue
            entry["legacy_status"] = status_text
            if (rel, key) in already:
                entry["verdict"] = "already_imported"
                entry["item_id"] = already[(rel, key)]
                records.append(entry)
                continue
            if key in already_by_id:
                # THE SAME RULE AS ABOVE, ASKED OF THE STORE: a legacy id names one V1 record
                # wherever it lies, so a known one arriving under a NEW path is a finding rather
                # than a new record. Measured before this: renaming the V1 document was enough to
                # make the whole store import a second time -- the idempotency key was the PAIR
                # (source, legacy id), so every record came back as unseen, and the third bolt of
                # DEC-0004 held for each item while the RECORD was reactivatable by a `mv`.
                held = already_by_id[key]
                entry["verdict"] = "blocked"
                entry["reason"] = (
                    "%s is already in this state as %s, imported from %s -- and this run reads it "
                    "from %s. A legacy id names ONE V1 record wherever it lies, so importing it "
                    "again would put a second item in the store for one record and leave a re-run "
                    "unable to tell them apart. Remedy: if this is the same record under a new "
                    "path, it is already imported and this copy needs nothing done to it -- move "
                    "it out of the state directory; if it is a DIFFERENT record that happens to "
                    "share the id, give it a distinct id in the V1 file. Then re-run the dry run."
                    % (key, ", ".join(item_id for _s, item_id in held),
                       ", ".join(source or "(unrecorded)" for source, _i in held), rel))
                records.append(entry)
                continue
            if entry["legacy_type"] not in v1_types():
                # THREE OUTCOMES, NOT TWO, and the middle one is the correction of 2026-08-04.
                # The previous cut asked ONE question -- "does the mapping table know this type"
                # -- and answered "not a backlog record" whenever it did not. Measured against a
                # real dev scaffold with a V1 `bugs.yaml` and a research one with
                # `research_questions.yaml`: `BUG`, `CR`, `FR`, `RQ`, `HYP` and `EXP` are V2 ITEM
                # TYPES with their own `ACTIVE_DIRS` entry, and every one of them was reported as
                # "no V1 backlog type" and the run exited 0. A false all-clear over most of two
                # kits' stores, produced by the fix for the opposite defect.
                #
                # So the question is asked of the right map. `REQUIRED_FIELDS` says whether a type
                # is an ITEM this kernel captures; the mapping table says whether its V1 status
                # vocabulary is known. A type in neither is genuinely something else, and blocking
                # a project's whole migration over such a store is the dead end this branch exists
                # to avoid -- `_is_backlog_type` is that union, carries the measured example, and
                # is what the unreadable-status branch above asks in the same words. A type in the
                # FIRST but not the second is a harness gap, and a harness gap may not present
                # itself as "nothing to do".
                if _is_backlog_type(entry["legacy_type"]):
                    entry["verdict"] = "blocked"
                    entry["reason"] = (
                        "`%s` IS a V2 item type, but spec II.10's mapping table has no row for it, "
                        "so nothing here knows what its V1 statuses mean. This is a HARNESS gap, "
                        "not a project one: the table lives in the enforcement layer, which a "
                        "session may not edit. Remedy: record it with `python scripts/harness.py "
                        "capture DEC` and report it -- the run refuses rather than reporting an "
                        "all-clear over records it cannot read." % entry["legacy_type"])
                else:
                    entry["verdict"] = "not_an_item"
                    entry["reason"] = (
                        "`%s` is no item type this kernel captures and has no row in spec II.10's "
                        "mapping table either, so this is a record of some other kind that happens "
                        "to use the id shape" % entry["legacy_type"])
                records.append(entry)
                continue
            try:
                v2_type, v2_status, archive_candidate = map_v1_status(
                    entry["legacy_type"], entry["legacy_status"])
            except UnknownV1Status as exc:
                entry["verdict"] = "blocked"
                entry["reason"] = str(exc)
                records.append(entry)
                continue
            entry.update({"v2_type": v2_type, "mapped_status": v2_status,
                          "archive_candidate": bool(archive_candidate)})
            if v2_type not in REQUIRED_FIELDS:
                entry["verdict"] = "blocked"
                entry["reason"] = (
                    "%s maps to %s, which `capture` does not create (it is frozen through the "
                    "promotion path). Remedy: record a Decision item and migrate it by hand."
                    % (key, v2_type))
                records.append(entry)
                continue
            # WHERE IT LANDS -- asked of the WRITER's own rule (`state.migration_archives`), never
            # re-derived here. Both halves of that rule (does the table call this record finished,
            # and may the import write the status at all) live at `migration_archive_status`, and
            # the one time this line spelled a condition of its own the plan and the writer could
            # disagree about a row.
            entry["target"] = ("archive"
                               if migration_archives(v2_type, entry["legacy_type"],
                                                     entry["legacy_status"])
                               else "active")
            fields, missing = _item_fields(v2_type, record, field_map,
                                           provenance=_provenance(rel, key))
            entry["carried_fields"] = sorted(fields)
            entry["missing_fields"] = missing
            if missing and entry["target"] == "active":
                # THE TWO ANSWERS A GAP CAN HAVE, and telling them apart is SR-0007 and DEC-0009
                # meeting. A field this store HAS a proposal for is a question with an answer
                # printed beside it, and the run stays unexecutable until a human types it back --
                # a suggestion is not a confirmation. A field NOTHING can propose and no `--map`
                # named is a gap V1 never collected, and DEC-0009 archives that record with the
                # gap as its reason instead of refusing the whole run over it.
                suggested = _field_suggestions(entry["legacy_type"], record, missing)
                entry["record_keys"] = sorted(str(k) for k in record)
                if suggested:
                    entry["suggested_fields"] = {
                        name: list(pair) for name, pair in sorted(suggested.items())}
                unanswered = [name for name in missing if name not in suggested]
                if not unanswered:
                    entry["verdict"] = "needs_decision"
                    records.append(entry)
                    continue
                entry["unresolved_fields"] = unanswered
                entry["target"] = "archive"
                entry["reason"] = (
                    "V1 collected nothing for %s, and no `--map` and no suggestion of this "
                    "harness can name a field that does: the record carries %s. DEC-0009: this is "
                    "archived with that reason rather than blocking the run. Remedy, if you want "
                    "it as a LIVE item instead: add the field(s) to this record in the V1 file "
                    "(in an editor outside the session), or name the V1 field they come from with "
                    "`--map`, then re-run the dry run."
                    % (", ".join(unanswered), ", ".join(entry["record_keys"])))
            if entry["target"] == "archive":
                year, source_of_year = _record_year(record), "the record's own newest date"
                if year is None and archive_year:
                    year, source_of_year = archive_year, "--archive-year"
                if year is None:
                    entry["verdict"] = "blocked"
                    entry["reason"] = (
                        "%s belongs in %s rather than under active (%s), and this "
                        "record carries no date, so nothing here knows which year. Nothing is "
                        "guessed. Remedy: re-run with `--archive-year <YYYY>`, which applies to "
                        "every dated-nowhere record of this run."
                        % (key, archive_location(v2_type),
                           entry.get("reason")
                           or "finished in V1: %r" % entry["legacy_status"]))
                    records.append(entry)
                    continue
                try:
                    entry["archive_year"] = _archive_year_of(year, source_of_year)
                except MigrationError as exc:
                    # A record whose own newest date is a year outside the four-digit shape --
                    # PyYAML parses `0012-01-01` into a real `datetime.date`, and `_record_year`
                    # answers 12. A blocked record rather than a refused run, because it is one
                    # record's data and every other record of the run is unaffected.
                    entry["verdict"] = "blocked"
                    entry["reason"] = "%s belongs in %s, and %s" % (
                        key, archive_location(v2_type), str(exc)[0].lower() + str(exc)[1:])
                    records.append(entry)
                    continue
                entry["archive_year_from"] = source_of_year
            for (map_type, map_field), source_field in field_map.items():
                if map_type == v2_type and source_field in record:
                    carried_values.setdefault(
                        "%s.%s <- %s" % (map_type, map_field, source_field),
                        set()).add(repr(record[source_field]))
            pending.append((entry, record, fields))
            records.append(entry)
    _settle_bindings(state, records, pending)
    return {"documents": inventory,
            "state": state_fingerprint(state),
            # THE WALLS, READ ONCE AND CARRIED IN THE PLAN. `absorbed_documents` needs them (a
            # document a registered gate reads may not be moved out from under that gate) and the
            # dry run prints them, and asking `layout.gated_documents` twice is how the report and
            # the move come to disagree about which files are walls. In the plan rather than beside
            # it, so the digest covers it: installing or removing a gate between the reading and
            # the writing changes what the run may move.
            "gated_documents": layout.gated_documents(
                os.path.dirname(os.path.abspath(state.root)), state.root),
            "root_items_after": _root_items_after(state, records),
            "records": sorted(records, key=lambda e: (e["source"], e["ordinal"])),
            "field_map": {"%s.%s" % key: value for key, value in sorted(field_map.items())},
            "archive_year": int(archive_year) if archive_year else None,
            "carried_values": {pair: sorted(values) for pair, values in carried_values.items()},
            "unscanned": sorted(unscanned),
            "unreadable": sorted(unreadable)}


def _root_items_after(state: ProjectState, records: list) -> dict:
    """{root type: (items left ACTIVE after this run, records of it this run archives)}.

    WHY THE MIGRATION COUNTS THIS AT ALL. DEC-0009 archives a record no answer can fill, and the
    types that meet that most often are exactly the ROOT types: a V1 product requirement carries
    none of `class`, `problem`, `goal`, `invariants`, `out_of_scope`, `priority`. Measured on the
    two dev field copies (2026-08-05): every one of their 38 product requirements is archived, and
    the migrated project then holds no active `PR` file at all.

    That is not a state the kernel refuses -- it is the decision DEC-0009 made -- but it is one a
    reader has to see BEFORE the run, because an archived item cannot be brought back. The kits'
    setup-phase predicate reads the presence of an active root item FILE (`hooks/_root.py`,
    `ROOT_ITEM_GLOBS`; `test_hooks.test_root_item_globs_are_the_kernels_root_types` derives that
    tuple from `ACTIVE_DIRS` + `ROOT_TYPE_BY_KIT`), so a project in this state answers that
    predicate the way a project before its first requirement does.

    Which types are root types is asked of `ROOT_TYPE_BY_KIT`, the same map the entry gate seeds
    from, rather than named here.
    """
    after = {}
    for root_type in sorted(set(ROOT_TYPE_BY_KIT.values())):
        if root_type not in ACTIVE_DIRS:
            continue
        live = len([one for one, _path in state.iter_active_items(root_type)])
        live += len([entry for entry in records
                     if entry.get("v2_type") == root_type
                     and entry["verdict"] == "translatable" and entry.get("target") != "archive"])
        archiving = len([entry for entry in records
                         if entry.get("v2_type") == root_type
                         and entry["verdict"] in _IMPORTING_VERDICTS
                         and entry.get("target") == "archive"])
        after[root_type] = [live, archiving]
    return after


def _provenance(rel: str, legacy_id: str) -> str:
    """What a `PROVENANCE_FIELDS` field is filled with -- one composer, so the receipt and the
    item cannot describe the same import differently."""
    return "V1 import: %s in %s" % (legacy_id, rel)


def _record_year(record):
    """The newest year any date-shaped value in this V1 record carries, or None.

    THE RULE AND ITS LIMIT IN ONE SENTENCE: an item is archived under the year its life ended, and
    no date the record itself carries is later than that -- so the newest one is the answer, and a
    record with no date at all gets NO answer rather than a plausible one (SR-0004: "wo keines
    dasteht ... ist es eine vorgelegte Entscheidung und keine Vermutung"). Read off the VALUES
    rather than off a field name, because V1 spelled the field `completed` in `tasks.yaml`, `date`
    in `filing_log.yaml` and nothing at all in `system_requirements.yaml`.

    WHAT THAT COSTS, stated rather than left to be found: a V1 record carrying a FUTURE date (a
    deadline, a retention date) yields that year, and the archive path then files it under a year
    in which nothing happened. `--archive-year` cannot override it -- that flag answers only the
    records that carry no date at all -- so such a record is filed by its own newest date and the
    dry run prints which year each archive-bound record got and where it came from.

    Walked by identity like `scan_document`, for the same reason: a YAML anchor can make a record
    self-referencing, and a value seen twice adds no year.
    """
    years, seen = set(), set()

    def walk(node):
        if id(node) in seen:
            return
        seen.add(id(node))
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, (list, tuple)):
            for value in node:
                walk(value)
        elif isinstance(node, datetime.date):
            years.add(node.year)
        elif isinstance(node, str):
            years.update(int(found) for found in _DATE_RE.findall(node))
    walk(record)
    return max(years) if years else None


def _rebind(v2_type: str, fields: dict, resolution: dict) -> dict:
    """`fields` with every binding value this plan resolves replaced by the id it resolves to.

    A V1 store names its parents by V1 id, and V2 REALLOCATES: the V1 `PROC-0001` may land as
    `PROC-0004` in a project that already holds three procedures, so carrying `derives_from:
    PROC-0001` over verbatim would bind the child to whatever else happens to be called that. The
    fields this touches are `PARENT_FIELDS`, the same set the kernel checks the binding of, so a
    field that binds and a field that is rewritten cannot become two different lists.
    """
    if not resolution:
        return fields
    bound = dict(fields)
    for field in PARENT_FIELDS.get(v2_type, ()):
        if field not in bound:
            continue
        value = bound[field]
        if isinstance(value, (list, tuple)):
            bound[field] = [resolution.get(str(one), one) for one in value]
        else:
            bound[field] = resolution.get(str(value), value)
    return bound


def _planned_resolution(records: list, pending: list) -> dict:
    """{V1 id: the id a binding on it will name} -- at PLAN time, with stand-ins for what is new.

    WHAT IT IS AND IS NOT. For a record an earlier run already imported this is the real item id,
    read off that item's own `legacy_fields`. For a record THIS run will create the id does not
    exist yet -- the kernel allocates it under the lock -- so the entry is a stand-in of the right
    TYPE and the widest width that type's allocator produces. That is enough for the two questions
    planning asks (does this binding resolve at all, and does the resulting body fit in one item)
    and it is deliberately not enough to be mistaken for the answer: `execute` builds its own map
    from the ids the parents ACTUALLY got, and it is that map the written item carries.

    A V1 id that TWO records in the plan claim resolves to nothing -- an ambiguous parent is not a
    parent -- and the binding then stands or falls on whether the state already holds an item of
    that name.

    WHAT IT DELIBERATELY OVERRIDES, because the choice is real: when a V1 id also names an item
    that already exists for unrelated reasons, this plan's own record wins. The V1 document meant
    the V1 record, and the V1 record is being imported; an unrelated V2 item that happens to share
    the number is a different thing. The dry run names every binding it rewrote.
    """
    claimed, resolution = {}, {}
    for entry in records:
        if entry.get("verdict") == "already_imported":
            claimed.setdefault(entry["legacy_id"], []).append(entry.get("item_id"))
    for entry, _record, _fields in pending:
        claimed.setdefault(entry["legacy_id"], []).append(format_id(entry["v2_type"], 9999))
    for legacy_id, targets in claimed.items():
        if len(targets) == 1 and targets[0]:
            resolution[legacy_id] = targets[0]
    return resolution


def _unsettled_parents(entry: dict, fields: dict, records: list, resolution: dict) -> list:
    """[(field, legacy id, [(verdict, source), ...])] -- bindings this run HOLDS but cannot resolve.

    THE PROPERTY: a binding value that names a record this run read, that the plan has no id for,
    AND about which the run still owes an answer. The middle clause covers two situations that are
    one fact for the reader -- the parent is not translatable yet (it needs a `--map`, it is
    blocked), or two records claim its id so `_planned_resolution` deliberately resolves it to
    nothing.

    THE LAST CLAUSE IS WHERE THE COUNTER-DEFECT WOULD SIT. `not_an_item` is the one verdict that is
    a FINAL answer about a record: it says this mapping is a cross-reference note or a record of
    some other kind, so it will never be an item and a binding to it really does bind to nothing.
    For those the writer's own message is the true one and this returns nothing, or the report
    would send a reader off to settle a record that has nothing to settle.

    Asked over `PARENT_FIELDS`, the same set `_rebind` rewrites and the kernel checks the binding
    of, so "a field that binds" cannot become three different lists. Returns the parents in field
    order; a value the run holds no record for is NOT in here either, for the same reason.
    """
    held = {}
    for other in records:
        if other.get("verdict") == "not_an_item":
            continue
        held.setdefault(other["legacy_id"], []).append(
            (other.get("verdict", "unclassified"), other["source"]))
    unsettled = []
    for field in PARENT_FIELDS.get(entry["v2_type"], ()):
        value = fields.get(field)
        for one in (value if isinstance(value, (list, tuple)) else [value]):
            name = str(one)
            if name in resolution or name not in held or name == entry["legacy_id"]:
                continue
            unsettled.append((field, name, held[name]))
    return unsettled


def _stolen_bindings(state: ProjectState, entry: dict, bound: dict, resolution: dict) -> list:
    """[(field, value)] -- bindings this run would carry over to an item it did NOT resolve to.

    THE DEFECT, and it is silent in every direction a reader could look. A V1 store names its
    parents by V1 id and V2 REALLOCATES, so `_rebind` replaces every value the run resolved. A
    value it did NOT resolve is left verbatim -- and when the store happens to hold an item of that
    name for unrelated reasons, `_assert_origins_resolve` finds it, accepts it, and the child is
    written bound to a different thing. Nothing reports it afterwards: the reference resolves, so
    `validate` has no finding to make, and the item's own `legacy_fields.record` shows the V1 value
    that "matches".

    HOW IT IS REACHED WITHOUT ANY UNUSUAL DATA: the collision refusal's own printed remedy is to
    take the colliding document out of the state directory. Do that, and the parent is no longer a
    record of the run, so `_unsettled_parents` -- which only speaks about records the run HOLDS --
    goes quiet, and every child of that parent falls straight into this hole.

    THE PROPERTY, and all three clauses are load-bearing: a binding value that (1) still carries
    the V1 ID SHAPE after the rewrite, (2) this plan did not resolve, and (3) NAMES AN ITEM THE
    STORE ALREADY HOLDS. Without the third clause this would swallow the case the writer answers
    correctly -- a value that names nothing at all really is free text, and
    `_assert_origins_resolve`'s own message is the true one about it. Without the first, a value
    that was never V1-shaped would be refused for looking unfamiliar.
    """
    stolen = []
    resolved_to = set(resolution.values())
    for field in PARENT_FIELDS.get(entry["v2_type"], ()):
        if field not in bound:
            continue
        value = bound[field]
        for one in (value if isinstance(value, (list, tuple)) else [value]):
            name = str(one).strip()
            if V1_ID_RE.match(name) and name not in resolved_to and _store_holds(state, name):
                stolen.append((field, name))
    return stolen


def _store_holds(state: ProjectState, name: str) -> bool:
    """Does this state already hold an item under that exact id?

    `exists_anywhere` raises for a name the V2 allocator could never have produced -- a V1 type it
    has no directory for, a number of fewer than four digits -- and such a name cannot be the id of
    a stored item, so the answer is False rather than an exception escaping into the planner.
    """
    try:
        return state.exists_anywhere(name)
    except ValueError:
        return False


def _seen_but_not_an_item(entry: dict, fields: dict, records: list) -> str:
    """An ANNOTATION on the writer's refusal, or "" -- never a replacement for it.

    The writer says "derives_from SR-0096 does not exist", which is true of the V2 state and is
    what a reader has to act on. What it cannot say is that the run READ a record of that name and
    classified it as no item at all -- measured on the field copy of `synaipse` (2026-08-05):
    `SR-0096` sits in `system_requirements.yaml` carrying no `status`, so it is a document entry,
    and a reader following the writer's remedy would go looking for a record that is right there.

    `_unsettled_parents` deliberately stays silent about a `not_an_item` parent, because that
    verdict is FINAL and turning it into "settle that record first" would send a reader after
    something with nothing to settle. This adds the fact without moving the remedy.
    """
    held = {other["legacy_id"]: other["source"] for other in records
            if other.get("verdict") == "not_an_item"}
    seen = []
    for field in PARENT_FIELDS.get(entry["v2_type"], ()):
        value = fields.get(field)
        for one in (value if isinstance(value, (list, tuple)) else [value]):
            if str(one) in held:
                seen.append("`%s` (%s in %s)" % (one, field, held[str(one)]))
    if not seen:
        return ""
    return (". NOTE: this run DID read %s and classified it as no item -- it carries no `status`, "
            "or its type is one no contract knows, so it never becomes an item and nothing here "
            "can make the binding resolve. Remedy: give that record a status in the V1 file if it "
            "really is a backlog record, or point this one somewhere else."
            % "; ".join(sorted(set(seen))))


def _settle_bindings(state: ProjectState, records: list, pending: list) -> None:
    """The second half of planning: bindings, write order, and the two ways it can still fail.

    WHY THIS CANNOT HAPPEN IN THE DOCUMENT LOOP -- the defect it is the correction of. The plan
    asked `capture_preflight` the moment it had a body, i.e. against the state BEFORE the run, and
    a V1 parent chain is the normal shape of every V1 store: measured on an office scaffold with
    `PROC-0001` and `PROC-0002 derives_from PROC-0001`, the dry run reported PROC-0001 importable
    and PROC-0002 blocked, `plan_is_executable` was then False, the run refused wholesale, PROC-0001
    was never written -- and the next dry run said the same thing. A stationary state.

    So the question is asked of the state the run WILL have reached: the ids this plan promises are
    handed to the preflight as existing (`also_existing`), and the writes are ordered so that the
    promise is kept. Both counter-directions stay closed and both are measured rather than argued:
    a binding whose target is NOT in the plan and not in the state is still refused, by the same
    check as before; and a CYCLE (A binds B, B binds A) is refused outright, because "create A
    before B and B before A" is a promise no order keeps.
    """
    resolution = _planned_resolution(records, pending)
    creating = {}
    for entry, _record, _fields in pending:
        creating[entry["legacy_id"]] = entry
    order, depth = {}, {}

    def dependencies(entry, fields):
        """The pending entries this one must be written after."""
        found = []
        for field in PARENT_FIELDS.get(entry["v2_type"], ()):
            value = fields.get(field)
            for one in (value if isinstance(value, (list, tuple)) else [value]):
                parent = creating.get(str(one))
                if parent is not None and str(one) in resolution:
                    # A RECORD THAT NAMES ITSELF IS NOT EXCLUDED HERE, and excluding it was a hole
                    # this fix nearly shipped: it would have settled at depth 1, been promised by
                    # the plan, and then died at write time because its own id does not exist yet.
                    # A self-binding is a cycle of length one and is refused as one.
                    found.append(parent)
        return found

    edges = {id(entry): dependencies(entry, fields) for entry, _record, fields in pending}

    def settle(entry, stack):
        """Depth of this entry in the dependency order, or None when it sits on a cycle."""
        key = id(entry)
        if key in depth:
            return depth[key]
        if key in stack:
            return None
        stack = stack | {key}
        levels = []
        for parent in edges[key]:
            level = settle(parent, stack)
            if level is None:
                return None
            levels.append(level)
        depth[key] = 1 + max(levels, default=0)
        return depth[key]

    for entry, record, fields in pending:
        level = settle(entry, frozenset())
        if level is None:
            entry["verdict"] = "blocked"
            entry["reason"] = (
                "%s and the record(s) it binds to form a cycle: each names the other as its "
                "parent, so no write order creates a parent before its child. Remedy: break the "
                "cycle in the V1 file -- one of the two is not really derived from the other -- "
                "then re-run the dry run." % entry["legacy_id"])
            continue
        order[id(entry)] = level

    also_existing = sorted(set(resolution.values()))
    for entry, record, fields in pending:
        if entry.get("verdict") == "blocked":
            continue
        bound = _rebind(entry["v2_type"], fields, resolution)
        entry["rebound_fields"] = sorted(
            field for field in PARENT_FIELDS.get(entry["v2_type"], ())
            if field in fields and bound[field] != fields[field])
        body = _with_legacy(bound, entry, record)
        # THE ORDER OF THE REFUSALS IS THE ORDER OF THE READER'S WORK: a defect INSIDE the record
        # is named before one that is about another record, so settling a parent can never move a
        # record from one refusal straight into the next.
        # `test_a_record_that_is_both_oversized_and_unsettled_reports_its_own_size` is what holds
        # the order; it, not this comment, is where the field reading behind it is recorded.
        #
        # THE BUDGET IS ASKED ONLY WHERE IT IS ENFORCED, and that clause is DEC-0009 read as it is
        # written. `report.validate_state` walks the ACTIVE items (`_iter_active`) and measures
        # each file against spec II.5; nothing measures a file under `archive/`. So an
        # archive-bound record was held back with a reason that was untrue about this harness, and
        # DEC-0009's answer for that class is the archive rather than a human sent to the business
        # data. An ACTIVE-bound oversized record still blocks, because for it the sentence is true.
        # `test_migrate.test_an_archive_bound_record_is_not_held_back_by_a_budget_nothing_measures`
        # is where the field reading behind this lives and where the second direction is measured
        # by running `validate`; the first is
        # `test_migrate.test_a_record_too_large_for_one_item_blocks_instead_of_being_written`.
        oversized = (None if entry["target"] == "archive"
                     else _too_large(body, entry["v2_type"]))
        unsettled = [] if oversized else _unsettled_parents(entry, fields, records, resolution)
        stolen = ([] if (oversized or unsettled)
                  else _stolen_bindings(state, entry, bound, resolution))
        if oversized:
            entry["verdict"] = "blocked"
            entry["reason"] = (
                "the item %s does not fit in one item: an item REFERENCES its detail, and this "
                "V1 record inlines it. Remedy: record a Decision item, split the record in the "
                "V1 file or move its bulk to `staging/`, then re-run the dry run." % oversized)
            continue
        if unsettled:
            # A BINDING TO A RECORD OF THIS RUN IS A PLANNING FACT, NOT A WRITER'S REFUSAL, and
            # letting the writer answer it was measured as an untrue message. `capture_preflight`
            # sees a V1 id -- `PRD-0007` -- and says what is true of it as a V2 value: "is not an
            # item id ... free text there binds to nothing". Measured on the field copy of
            # `portfoliomanaigement` (2026-08-04): 111 of 157 blocked records carried that
            # sentence, and every one of the named parents was a record sitting in
            # `product_requirements.yaml` in the same run, waiting for a `--map`. A reader acting
            # on that message would look for free text that is not there.
            #
            # So the case is decided BEFORE the writer is asked, and only for a value this run
            # actually holds a record for. Anything else still goes to the writer and still gets
            # its message, because then the value really does name nothing.
            entry["verdict"] = "blocked"
            entry["reason"] = (
                "it binds to %s, and %s a record of THIS run rather than free text -- so this "
                "record follows as soon as that one does, and nothing about this record needs "
                "changing. Remedy: settle the record(s) named above (the sections of this report "
                "say what each one still needs), then re-run the dry run."
                % ("; ".join(
                    "`%s` (%s: %s in %s)"
                    % (legacy_id, field, "/".join(sorted({verdict for verdict, _s in held})),
                       ", ".join(sorted({source for _v, source in held})))
                    for field, legacy_id, held in unsettled),
                   "they are" if len(unsettled) > 1 else "it is"))
            continue
        if stolen:
            entry["verdict"] = "blocked"
            entry["reason"] = (
                "its %s still names %s, which this run did not import and did not resolve -- and "
                "an item of that name already exists in this state. Carrying the value over would "
                "bind this record to a DIFFERENT thing that happens to wear the same number: V1 "
                "numbers were typed by hand and V2 numbers are allocated by the kernel, so the two "
                "agreeing is a coincidence and not a reference. Remedy: import the record that "
                "value means (it is named in the sections above if this run read it), or correct "
                "the value in the V1 file, then re-run the dry run."
                % (", ".join(sorted({field for field, _v in stolen})),
                   ", ".join("`%s`" % value for _f, value in stolen)))
            continue
        refused = None
        # THE WRITER'S OWN VERDICT, asked before the plan promises anything, and asked of the
        # SAME method the run will use -- the archive path enforces a different contract
        # (DEC-0004), so asking `capture_preflight` about an archive-bound record would have
        # been a plan measuring something the run does not do.
        try:
            if entry.get("unresolved_fields"):
                state.capture_migrated_unresolved_preflight(
                    entry["v2_type"], body, also_existing)
            elif entry["target"] == "archive":
                state.capture_migrated_archive_preflight(
                    entry["v2_type"], body, entry["legacy_type"], entry["legacy_status"],
                    also_existing)
            else:
                state.capture_preflight(entry["v2_type"], body, also_existing)
        except StateError as exc:
            refused = str(exc)
        if refused:
            entry["verdict"] = "blocked"
            entry["reason"] = (
                "the kernel would refuse this item: %s (asked of the same check that writes "
                "it, so the plan cannot promise what the run cannot do)%s"
                % (refused, _seen_but_not_an_item(entry, fields, records)))
        else:
            entry["verdict"] = "unresolved" if entry.get("unresolved_fields") else "translatable"
            entry["write_order"] = order[id(entry)]


def state_fingerprint(state: ProjectState) -> list:
    """[(state-relative path, sha256)] for every file the digest is a statement about.

    WHAT IT COVERS AND WHAT IT DOES NOT, because the sentence this replaces said "any file under
    the state directory" and that was measured false: the fingerprint used to be the DOCUMENT
    inventory, so a hand-edited `procedures/active/PROC-0001.yaml` left the digest unchanged and
    the run went through on a plan that had never seen it.

    The rule is the dotted-segment one `layout.is_project_document` already uses, and for the same
    reason: everything under the state root EXCEPT paths with a dotted segment. So kit documents,
    every kernel-written item, `generated/` and `staging/` are all in. The exclusion is machinery
    -- the lock and `.audit/hook_events.jsonl`, which grows whenever any gate refuses anything;
    including it would invalidate a plan because an unrelated hook fired between the reading and
    the run, which is a refusal a person cannot act on. THE RESIDUAL, stated rather than implied: a
    file placed under a dotted directory of somebody's own making is invisible here.
    """
    seen = []
    for dirpath, dirs, files in os.walk(state.root):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for name in sorted(files):
            if name.startswith("."):
                continue
            path = os.path.join(dirpath, name)
            with open(path, "rb") as handle:
                seen.append([_relative(state, path), hashlib.sha256(handle.read()).hexdigest()])
    return sorted(seen)


def plan_digest(plan: dict) -> str:
    """The fingerprint the executing run must be handed back.

    Over the WHOLE plan, which is what makes it a statement about the state rather than about the
    records: `state_fingerprint` is in there, so editing anything the fingerprint covers --
    including a file this command would never translate -- invalidates a plan that was presented
    before the edit, and so does changing the `--map` flags. That is deliberate. A migration
    reviewed against one state and run against another is the failure this digest exists for, and
    being too strict costs one more dry run. What the fingerprint does NOT cover is named where it
    is built, not here.
    """
    return hashlib.sha256(canonical_json(plan).encode("utf-8")).hexdigest()


def _by_verdict(plan: dict, verdict: str) -> list:
    return [entry for entry in plan["records"] if entry["verdict"] == verdict]


# The verdicts under which a record BECOMES AN ITEM in this run. `translatable` is the ordinary
# import (active/ or the finished-record archive); `unresolved` is DEC-0009's second archive door.
# Named once because four readers ask it -- the write loop, the receipt, SR-0005's absorption rule
# and the dry run -- and a fifth spelling of the same set is how one of them comes to disagree.
_IMPORTING_VERDICTS = ("translatable", "unresolved")


def _importable(plan: dict) -> list:
    return [entry for entry in plan["records"] if entry["verdict"] in _IMPORTING_VERDICTS]


def plan_is_executable(plan: dict) -> bool:
    """Would `migrate` run this plan, or does something still need a human?

    THREE THINGS STOP IT AND `unresolved` IS NOT ONE OF THEM (DEC-0009): a record nobody can
    translate is archived with its reason, so it is an outcome rather than an obstacle. What
    remains is what no run can proceed past -- a `blocked` record (it cannot be written at all: it
    does not fit in one item, its year is unknown, its id is claimed twice, or the harness has no
    row for it), a `needs_decision` record (a suggestion is on the table and SR-0007 says a
    suggestion is not an answer), and a document that does not parse.
    """
    return not (_by_verdict(plan, "blocked") or _by_verdict(plan, "needs_decision")
                or plan["unreadable"])


# -- the dry run's text --------------------------------------------------------------------------

def _group_decisions(entries) -> dict:
    """{what the answer depends on: [entry, ...]} -- see the caller for why this is grouped."""
    grouped = {}
    for entry in entries:
        key = (entry["source"], entry["v2_type"], tuple(entry["missing_fields"]),
               tuple(entry["record_keys"]))
        grouped.setdefault(key, []).append(entry)
    return grouped


def _group_unresolved(entries) -> dict:
    """{what a human would have to do about it: [entry, ...]} -- grouped for the same reason.

    The key carries the V1 STATUS as well, which the decision key does not: an unresolved record
    is going into the archive, and whether the thing being archived was live or finished is the
    first question a reader has about it.
    """
    grouped = {}
    for entry in entries:
        key = (entry["source"], entry["v2_type"], entry["legacy_status"],
               tuple(entry["unresolved_fields"]), tuple(entry["record_keys"]))
        grouped.setdefault(key, []).append(entry)
    return grouped


def _named_ids(group) -> list:
    """The legacy ids of a grouped section, EVERY one of them, as indented wrapped lines.

    THE SECTIONS THIS SERVES ARE THE ANSWER TO "which records need a human", so a reader has to
    come out of them holding the records rather than a range. They printed `first .. last (n)`,
    which names two ids per group and leaves the rest unsayable -- the spans were not sorted
    either, so nothing about them could be inferred. Sorted and complete is what makes the list
    usable and what makes two runs comparable. The field reading behind that is recorded in
    `test_migrate.test_every_record_that_needs_a_human_is_named_and_not_spanned`.

    Wrapped rather than printed on one line, because the bound here is the number of records a
    project has, which is no bound at all.
    """
    ids = sorted(entry["legacy_id"] for entry in group)
    return ["    " + line for line in textwrap.wrap(", ".join(ids), width=94)]


def _map_flags(plan: dict) -> list:
    """The `--map` flags this state still needs, deduplicated, in command-line order.

    A field this harness has a SUGGESTION for is printed as the flag it would be rather than as a
    placeholder, so confirming the run is a paste and not a transcription (SR-0007). A field with
    no suggestion keeps its placeholder, because the alternative is a flag that looks answered.
    """
    wanted = {}
    for entry in _by_verdict(plan, "needs_decision"):
        for field in entry["missing_fields"]:
            suggested = (entry.get("suggested_fields") or {}).get(field)
            wanted.setdefault((entry["v2_type"], field), suggested[0] if suggested else None)
    return ["--map %s.%s=%s" % (pair[0], pair[1], value or "<v1_field>")
            for pair, value in sorted(wanted.items())]


def _suggestion_lines(plan: dict) -> list:
    """One line per DISTINCT suggestion, with the reason the row carries."""
    seen = {}
    for entry in _by_verdict(plan, "needs_decision"):
        for field, (v1_field, why) in sorted((entry.get("suggested_fields") or {}).items()):
            seen.setdefault((entry["v2_type"], field, v1_field, why), []).append(entry)
    lines = []
    for (v2_type, field, v1_field, why), group in sorted(seen.items()):
        lines.append("  --map %s.%s=%s  (%d record(s)) -- %s"
                     % (v2_type, field, v1_field, len(group), why))
    return lines


def root_item_warnings(plan: dict, written: bool = False) -> list:
    """The "this project keeps no root item" warning, for BOTH halves of the command.

    IT SAYS THE CONSEQUENCE AND NOT ONLY THE STATE. The first version named the state ("the project
    answers the setup-phase predicate the way one before its first requirement does") and left the
    reader to work out what follows from it; what follows is that the gates built on that predicate
    stop applying, and two of them are the ones in front of a merge and a push.
    `test_migrate.test_a_project_left_without_a_root_item_really_does_open_the_merge_gate` is where
    that sentence is measured, against the shipped `gate_git.py` as a process.

    AND IT IS PRINTED WHERE IT IS WRITTEN, TOO. It used to appear in the dry run only, so the run
    that actually produced the state said nothing about it -- and a person who runs `--plan` from a
    scrollback, or from a script, never sees it. `written` only moves the tense; what is said is
    one text, because two texts is how the two halves come to say different things.
    """
    lines = []
    for root_type, (live, archiving) in sorted(plan.get("root_items_after", {}).items()):
        if not archiving or live:
            continue
        lines += ["", "%s THIS PROJECT HOLDS NO ACTIVE %s ITEM: all %d of them %s into the "
                      "archive. WHAT THAT COSTS is not only bookkeeping -- a kit's setup-phase "
                      "predicate (`hooks/_root.py`, `has_root_item`) reads whether an active %s "
                      "file exists, and a gate that asks it DOES NOT APPLY while the answer is no. "
                      "In the dev and research kits the gate in front of `git merge` and `git "
                      "push` is one of those, so neither is refused by it until this project holds "
                      "a root item again. Nothing here refuses that -- it is DEC-0009's decision "
                      "-- and no kernel operation moves an item back out of the archive."
                  % ("THIS RUN IS DONE AND" if written else "AFTER THIS RUN",
                     root_type, archiving, "went" if written else "go", root_type)]
    return lines


def render(plan: dict, state: ProjectState = None) -> str:
    """The dry run, in the three parts the command promises: found, becomes, cannot.

    WHICH DOCUMENTS ARE WALLS is `plan["gated_documents"]` and no longer a second reading taken
    here: the plan already had to know, because the same answer decides which documents may be
    moved to `legacy/`. `state` stays optional and buys only the top-level KEYS of each wall, which
    need the file; without it the walls are named without them rather than guessed at.
    """
    lines = ["MIGRATION DRY RUN -- nothing was written.",
             "plan digest: %s" % plan_digest(plan), ""]

    translatable = _by_verdict(plan, "translatable")
    lines.append("WHAT IT WOULD IMPORT (%d record(s)):" % len(translatable))
    for entry in translatable:
        if entry["target"] == "archive":
            # A DIFFERENT SENTENCE BECAUSE IT IS A DIFFERENT WRITE, and the two things a reader
            # must be able to object to are both in it: the YEAR and where that year came from.
            lines.append(
                "  %-18s %s -> %s at %s (finished in V1: %r). The year comes from "
                "%s. Spec II.2's field contract does not apply to it (DEC-0004); the item names "
                "every required field it lacks."
                % (entry["source"], entry["legacy_id"],
                   archive_location(entry["v2_type"], entry["archive_year"]),
                   entry["mapped_status"], entry["legacy_status"],
                   entry["archive_year_from"]))
        else:
            lines.append(
                "  %-18s %s -> a new %s item at its initial status (V1 %r would mean %s; that "
                "value is kept in `%s`, not walked)"
                % (entry["source"], entry["legacy_id"], entry["v2_type"], entry["legacy_status"],
                   entry["mapped_status"], LEGACY_FIELD))
        if entry.get("rebound_fields"):
            # NAMED, never silent: the value in the V1 file is not the value the item gets, and a
            # reader who is not told that would check the wrong id.
            lines.append(
                "  %-18s   ...its %s point(s) at a record THIS RUN creates, so the written item "
                "carries the id that record actually gets -- not the V1 one."
                % ("", ", ".join(entry["rebound_fields"])))
    if translatable:
        lines.append("  ...each with `%s: true` and `approval_ref: null` (spec II.10): the import "
                     "creates NO approval, and no gate that requires one opens because of it."
                     % CONFIRMATION_FLAG)
    else:
        lines.append("  (none)")

    # THE VALUES A `--map` WOULD ACTUALLY CARRY, and this section exists because of a shape the
    # tool must NOT fix: `--map PROC.roles=owner` puts a V1 SCALAR into a V2 field whose name is
    # plural. No contract in this kernel declares the shape of `roles` -- `REQUIRED_FIELDS` names
    # fields, not types -- so inventing one here would be the kernel deciding something nobody
    # wrote down. What it can do instead is show the human every distinct value the mapping would
    # carry, before it carries it. Distinct values, so the section is bounded by the VARIETY of
    # the data rather than by its size.
    if plan["carried_values"]:
        lines += ["", "FIELD MAPPING IN EFFECT -- values carried VERBATIM, in the shape the V1 "
                      "record holds them (nothing here converts a scalar into a list):"]
        for pair in sorted(plan["carried_values"]):
            lines.append("  %-30s %s" % (pair, ", ".join(plan["carried_values"][pair])))
    already = _by_verdict(plan, "already_imported")
    if already:
        lines.append("")
        lines.append("ALREADY IMPORTED (%d) -- a re-run leaves these alone:" % len(already))
        for entry in already:
            lines.append("  %-18s %s -> %s" % (entry["source"], entry["legacy_id"],
                                               entry["item_id"]))

    decisions = _by_verdict(plan, "needs_decision")
    lines += ["", "WHAT IT CANNOT DECIDE (%d record(s)) -- a field carries over only when both "
                  "contracts spell it the same:" % len(decisions)]
    # ONE LINE PER DECISION, not per record. Records that differ in no way the decision depends on
    # -- same source, same target type, same missing fields, same available keys -- pose ONE
    # question, and printing it once per record turns a sixteen-record import into sixteen
    # identical lines and a nine-hundred-record one into a wall nobody reads. The grouping key is
    # exactly what the answer depends on, so two records that would need DIFFERENT answers can
    # never collapse into one line.
    for _key, group in sorted(_group_decisions(decisions).items()):
        first = group[0]
        lines.append(
            "  %-18s %d record(s) (%s): missing %s; the record carries %s"
            % (first["source"], len(group), first["v2_type"],
               ", ".join(first["missing_fields"]), ", ".join(first["record_keys"])))
        lines += _named_ids(group)
    if decisions:
        suggestions = _suggestion_lines(plan)
        if suggestions:
            # SR-0007: a proposal with its reason, and the boundary stated where the reason is --
            # the run does NOT act on it. Everything below is what the human would be pasting.
            lines.append("  SUGGESTED, from what the kit's own V1 template documents -- NOT "
                         "applied: the run stays unexecutable until you type these back.")
            lines += suggestions
        lines.append("  Remedy: decide each one and say so on the line --")
        lines.append("    python scripts/harness.py migrate --plan <digest> %s"
                     % " ".join(_map_flags(plan)))
        lines.append("  The digest changes when you change the state, so re-run --dry-run after "
                     "any edit and take the digest it prints.")
    else:
        lines.append("  (none)")

    unresolved = _by_verdict(plan, "unresolved")
    if unresolved:
        lines += ["", "WOULD BE ARCHIVED AS UNRESOLVED (%d record(s)) -- DEC-0009: V1 collected "
                      "nothing for these required fields, so the record is archived with that "
                      "reason instead of stopping the run. THESE ARE THE RECORDS THAT NEED A "
                      "HUMAN if you want them as live items:" % len(unresolved)]
        for _key, group in sorted(_group_unresolved(unresolved).items()):
            first = group[0]
            lines.append(
                "  %-18s %d record(s) (%s, V1 %s): no source for %s; the record carries %s"
                % (first["source"], len(group), first["v2_type"], first["legacy_status"],
                   ", ".join(first["unresolved_fields"]), ", ".join(first["record_keys"])))
            lines += _named_ids(group)
        lines.append("  Remedy, per record: add the field in the V1 file, or name the V1 field it "
                     "comes from with `--map`. Doing nothing archives it -- and this kernel has "
                     "no operation that brings an item back out of the archive.")

    lines += root_item_warnings(plan)

    blocked = _by_verdict(plan, "blocked")
    if blocked:
        lines += ["", "BLOCKED (%d) -- the run refuses while any of these stands:" % len(blocked)]
        for entry in blocked:
            lines.append("  %-18s %s: %s" % (entry["source"], entry["legacy_id"], entry["reason"]))
    for problem in plan["unreadable"]:
        lines += ["", "UNREADABLE (the run refuses): %s" % problem]
    for note in plan["unscanned"]:
        lines += ["", "NOT SEARCHED: %s" % note]

    not_items = _by_verdict(plan, "not_an_item")
    if not_items:
        lines += ["", "ID-SHAPED BUT NOT ITEMS (%d) -- read, not imported, not a blocker:"
                  % len(not_items)]
        for entry in not_items:
            lines.append("  %-18s %s: %s" % (entry["source"], entry["legacy_id"], entry["reason"]))

    absorbed = absorbed_documents(plan)
    if absorbed:
        lines += ["", "WOULD MOVE TO legacy/ (%d document(s)) -- SR-0005: every record of these "
                      "became an item, so leaving them here would be the same thing twice in one "
                      "project. The run's Decision item records each with its pre-move hash, and "
                      "`legacy/` is a kernel-written area, so a later run does not read it as a V1 "
                      "source and no tool write reaches it:" % len(absorbed)]
        for path in absorbed:
            lines.append("  %-28s -> %s" % (path, legacy_location(path)))

    still_holding = _documents_still_holding_records(plan)
    if still_holding:
        # SR-0001, REPORTED IN ADVANCE: the same condition `validate` enforces afterwards, asked of
        # the plan. A dry run that said READY while a document would keep V1 backlog records is a
        # dry run that promises a state the validator refuses.
        lines += ["", "WOULD STILL HOLD V1 BACKLOG RECORDS AFTER THE RUN (%d document(s)) -- "
                      "SR-0001's completion criterion, and `validate` reports each of them as an "
                      "error until it is cleared:" % len(still_holding)]
        for path in sorted(still_holding):
            lines.append("  %-28s %d record(s) stay in the file" % (path, still_holding[path]))

    retired = set(absorbed)
    carried = [doc for doc in plan["documents"]
               if doc["path"] not in {entry["source"] for entry in plan["records"]}
               and doc["path"] not in retired]
    lines += ["", "CARRIED, NOT TRANSLATED (%d document(s)) -- left exactly where they are, "
                  "unrenamed and unedited; the run's Decision item records each with this hash:"
              % len(carried)]
    for doc in carried:
        lines.append("  %-28s %8d B  %s" % (doc["path"], doc["bytes"], doc["sha256"][:16]))
    lines.append("  No kernel command writes any of these, before or after the migration "
                 "(`gate_write_scope` refuses a tool write to them for that reason). Nothing here "
                 "blocks writes to them either -- spec II.10 asks for a fail-closed integrity "
                 "guard over retained V1 files and this command does not build one.")

    walls = plan.get("gated_documents") or {}
    if walls:
        lines += ["", "WALLS (%d) -- a registered gate reads these and can refuse work over their "
                      "CONTENT:" % len(walls)]
        for path in sorted(walls):
            # THE REASON IS NOT DISCARDED HERE, and it was: a wall that does not parse and a wall
            # with no keys both printed `-`, which is the reader's-eye version of the silence this
            # whole command is built against -- and this is the one place a wall's own bytes are
            # read, so nothing else would have said it. A wall is not searched for records (it is
            # never moved and never imported), so its state reaches no other heading of this run.
            said = "top-level keys: -"
            if state is not None:
                payload, problem = _read_document(state, path)
                if problem:
                    said = "NOT READ: %s" % problem
                elif isinstance(payload, dict):
                    said = "top-level keys: %s" % (", ".join(sorted(str(k) for k in payload)) or "-")
            lines.append("  %-28s %-24s %s" % (path, walls[path]["hook"], said))
        lines.append("  This command does not rewrite a wall and does not MOVE one: its content is "
                     "prose or configuration a kit ships and a USER fills, in an editor outside "
                     "the session, and taking it to legacy/ would leave its gate reading an absent "
                     "file. Whether a wall is currently UNFILLED is its own gate's verdict -- "
                     "`python scripts/harness.py doctor` and the SessionStart briefing report "
                     "it, and this command does not re-derive it.")

    lines += ["", ("READY: `python scripts/harness.py migrate --plan %s`" % plan_digest(plan))
              if plan_is_executable(plan) and _importable(plan)
              else ("NOTHING TO DO: no record in this state becomes an item."
                    if plan_is_executable(plan) else
                    "NOT EXECUTABLE YET: settle the sections above, then run --dry-run again.")]
    return "\n".join(lines)


def _documents_still_holding_records(plan: dict) -> dict:
    """{document: how many V1 BACKLOG records it would still hold after this run}.

    THE SAME PREDICATE `validate` ENFORCES, asked of the plan instead of the disk -- SR-0001's
    "der Trockenlauf meldet dieselbe Bedingung vorab".

    IMPORTING A RECORD DOES NOT REMOVE IT FROM ITS V1 FILE, and that is the whole reason this
    counts what it counts: the only thing that takes a V1 record out of the working tree is the
    document MOVE (SR-0005). So a document this run absorbs is not in here, and every other
    document is in here with ALL of its backlog records -- the imported ones included, because
    after the run they are the second copy SR-0001 exists to forbid. A `not_an_item` record is not
    a backlog record and `report.validate_state` does not flag it, by the same rule both ends read.
    """
    retired = set(absorbed_documents(plan))
    still = {}
    for entry in plan["records"]:
        if entry["source"] in retired or entry["verdict"] == "not_an_item":
            continue
        still[entry["source"]] = still.get(entry["source"], 0) + 1
    return still


# -- execution -----------------------------------------------------------------------------------


def _receipt_fields(plan: dict, created: list, digest: str, interrupted: str = None,
                    moved: list = None) -> dict:
    """The run's Decision item, in a form that fits inside spec II.5's per-item budget.

    TWO PARTS OF IT GROW WITH THE NUMBER OF DOCUMENTS -- the per-document inventory in `context`
    and the carried-not-translated list in `consequences` -- and the first cut shortened only the
    first. Measured with 310 carried documents: the receipt came to 21 316 B, `validate` exit 1,
    and `consequences` alone was 20 070 characters. The docstring claimed the protection the code
    did not build, in the item whose job is to be the honest record of the run.

    THAT FIX WAS ITSELF SHORT BY ONE FIELD, which is why this is now a loop over a LIST rather than
    two hand-paired strings and one `if`. `decision` carries one line per SOURCE DOCUMENT and had
    no short form at all: measured on an office scaffold with 300 translatable V1 files, the
    receipt came to 17 285 B / 204 lines and `validate` exited 1 -- the fallback fired and did not
    help, because the part that had grown was the part with no short form. The rule is now the one
    property rather than three cases: every part that grows with the INPUT has both forms, and the
    forms are swapped in one at a time, re-measuring the whole item after each swap, until
    `_too_large` says None.

    AND SHORT BY ONE PART AGAIN: `interrupted` is the message of whatever killed a partial run, so
    its length is the failing library's business and not this module's -- an `OSError` carrying a
    path per item is enough on its own. It is the last step of the loop rather than the first,
    because it is the only part that says the state is HALF WRITTEN, and that sentence should
    survive longer than the per-source breakdown does. What its short form drops is the failure
    TEXT; the refusal `execute` raises carries that text verbatim to the command line.

    WHAT IS LEFT WHEN EVERY SHORT FORM IS IN, stated because the previous version of this sentence
    was the untrue one: `title`, `source` and the short bodies are fixed sentences plus counts and
    one digest, so the floor is a constant -- except for the `--map` echo, whose size is the
    command line the human typed. A person who types more `--map` bytes than an item may hold
    still gets a receipt that does not fit, and nothing here shrinks that: it is their own input
    read back, and dropping it would make the receipt silent about what the run was told to do.

    NO SHORT FORM POINTS AT SOMETHING THAT IS NOT THERE, which is the failure mode of every one of
    these fallbacks and which each of them has had: a sentence saying "above" while `context` is
    the short one, and a sentence sending the reader to `generated/index.yaml` for the per-item
    breakdown when the index is regenerated from the ACTIVE items only and an archived import is
    in none of it. What every dropped list is still recoverable from is the plan digest in
    `source`, which is taken over all of it, plus a dry run over the same untouched state.
    """
    per_source = {}
    for entry, item_id in created:
        bucket = per_source.setdefault(entry["source"], [])
        bucket.append(item_id)
    moved = list(moved or [])
    # A MOVED DOCUMENT IS NOT A CARRIED ONE: "carried" means left exactly where it was, and this
    # list is what the receipt promises about the files still in the project.
    retired = {doc["path"] for doc in moved}
    carried = [doc["path"] for doc in plan["documents"]
               if doc["path"] not in set(per_source) and doc["path"] not in retired]

    long_context = "\n".join(
        ["read %d document(s) under the state directory:" % len(plan["documents"])]
        + ["  %s (%d B, sha256 %s)" % (doc["path"], doc["bytes"], doc["sha256"])
           for doc in plan["documents"]])
    short_context = (
        "read %d document(s) under the state directory; the per-document inventory with its "
        "content hashes does not fit in one item (spec II.5) and is NOT written here. The plan "
        "digest in `source` is taken over all of them, and `python scripts/harness.py migrate "
        "--dry-run` prints them in full for as long as the state is unchanged."
        % len(plan["documents"]))

    unresolved = [item_id for entry, item_id in created if entry.get("unresolved_fields")]
    archived = [item_id for entry, item_id in created
                if entry.get("target") == "archive" and not entry.get("unresolved_fields")]
    head = ("imported %d V1 record(s) -- %d into active/ at their V2 initial status, %d finished "
            "in V1 straight into archive/<TYPE>/<year>/ at their mapped status (SR-0004/DEC-0004) "
            "and %d into the same archive at their INITIAL status because no answer could fill "
            "their required fields (DEC-0009; each says which under `%s.unresolved`). Every "
            "archived item names its own gaps under `%s.missing_required_fields`, and every "
            "imported item carries `%s: true`, `approval_ref: null` and its whole V1 record "
            "under `%s`"
            % (len(created), len(created) - len(archived) - len(unresolved), len(archived),
               len(unresolved), LEGACY_FIELD, LEGACY_FIELD, CONFIRMATION_FLAG, LEGACY_FIELD))
    flags = ("field mapping supplied on the command line: %s"
             % (", ".join("%s=%s" % pair for pair in sorted(plan["field_map"].items())) or "none"))
    # NO "above" AND NO PATH IN HERE: this sentence survives into shapes where the per-source
    # breakdown has been dropped, and the refusal `execute` raises is what names the ids.
    half_written = ("The %d item(s) this run created are in the state and were not rolled back; a "
                    "re-run skips them by their legacy id." % len(created))
    long_tail = ([] if not interrupted else
                 ["THE RUN DID NOT FINISH: %s. %s" % (interrupted, half_written)])
    short_tail = ([] if not interrupted else
                  ["THE RUN DID NOT FINISH. What stopped it does not fit in one item (spec II.5) "
                   "and is NOT written here; the refusal the command raised carries it. %s"
                   % half_written])

    long_breakdown = (
        [head + ":"]
        + ["  %s -> %d item(s): %s .. %s"
           % (source, len(per_source[source]), sorted(per_source[source])[0],
              sorted(per_source[source])[-1]) for source in sorted(per_source)])
    short_breakdown = [
        head + ", out of %d source document(s). The per-source breakdown does not fit in one item "
               "(spec II.5) and is NOT written here; each imported item names its own source in "
               "`%s.legacy_source`." % (len(per_source), LEGACY_FIELD)]

    def decision_with(breakdown, tail):
        return "\n".join(breakdown + [flags] + tail)

    def consequences_with(carried_line, moved_line):
        return "\n".join([
            "imported items are NOT approved: the import mints no APR and no gate that requires "
            "one opens because of it. Each needs `python scripts/harness.py request-approval "
            "scope <ID>` and a user answer.",
            "the V1 sources that were NOT fully absorbed are untouched and stay readable; nothing "
            "in this harness blocks a later write to them.",
            moved_line,
            carried_line,
        ])

    # THE MOVE IS THE ONE THING THIS RUN DID TO A SOURCE FILE (SR-0005), so the receipt carries
    # each moved document's pre-move hash: that is what makes the copy under `legacy/` checkable
    # against what the migration actually read.
    long_moved = ("fully absorbed and moved to legacy/ (every record of them became an item): %s"
                  % ("; ".join("%s -> %s (%d B, sha256 %s)"
                               % (doc["path"], doc["moved_to"], doc["bytes"], doc["sha256"])
                               for doc in moved) or "none"))
    short_moved = ("%d document(s) were fully absorbed and moved to legacy/. Neither their paths "
                   "nor their pre-move hashes fit in one item (spec II.5); the plan digest in "
                   "`source` covers what was read, and `legacy/` holds the files themselves."
                   % len(moved))

    # The SHORT form does not say "hash recorded above": once `context` is the short one, no hash
    # is recorded above, and a sentence pointing at a list that is not there is the defect this
    # whole function is a correction of, one sentence further on.
    long_consequences = consequences_with(
        "carried, not translated (left in place, hashes in `context` above): %s"
        % (", ".join(carried) or "none"), long_moved)
    short_consequences = consequences_with(
        "%d document(s) were carried, not translated -- left in place, unrenamed and unedited. "
        "Neither their paths nor their hashes fit in one item (spec II.5); the plan digest in "
        "`source` covers them and the dry run lists them." % len(carried), short_moved)

    fields = {"title": "V1 import: %d record(s) into the V2 item store" % len(created),
              "context": long_context,
              "decision": decision_with(long_breakdown, long_tail),
              "consequences": long_consequences,
              "source": "spec II.10; plan digest %s" % digest}
    # EVERY GROWING PART, GROUPED BY WHAT IT POINTS AT. The loop re-measures the whole item after
    # each step and stops at the first shape that fits, so the ORDER of the steps carries nothing
    # about correctness -- only about which sentence survives longest, and the one that says the
    # state is half written is meant to survive longest of the three.
    # What the GROUPING carries is a coupling that is real and was broken once by shortening these
    # one at a time: the long `consequences` says the hashes are "in `context` above", so it is
    # only true while `context` is the long one. Giving them up together is that sentence's
    # correctness expressed as code rather than as a rule somebody has to remember.
    for step in ({"context": short_context, "consequences": short_consequences},
                 {"decision": decision_with(short_breakdown, long_tail)},
                 {"decision": decision_with(short_breakdown, short_tail)}):
        if not _too_large(fields):
            break
        fields.update(step)
    return fields


def execute(state: ProjectState, plan: dict, digest: str) -> dict:
    """Import every translatable record, then write the run's receipt.

    The caller has already checked the digest -- this function is the write half and nothing else,
    so a test can drive it without a command line.
    """
    if not plan_is_executable(plan):
        raise MigrationError(
            "this state is not migratable as it stands: %d record(s) blocked, %d still waiting "
            "for a field decision to be confirmed, %d document(s) unreadable. Remedy: `python "
            "scripts/harness.py migrate --dry-run` names each one and prints the flags that "
            "settle it."
            % (len(_by_verdict(plan, "blocked")), len(_by_verdict(plan, "needs_decision")),
               len(plan["unreadable"])))
    importable = _importable(plan)
    if not importable:
        # WRITE NOTHING, INCLUDING THE RECEIPT. A receipt for a run that imported nothing is a new
        # item on every invocation, which would make the SECOND run of a finished migration
        # change the state -- the exact property this command promises it does not have. So the
        # empty run is a no-op with an answer, and idempotency is a fact about the code rather
        # than about how carefully somebody types.
        return {"created": [], "receipt": None, "moved": []}
    field_map = {tuple(key.split(".", 1)): value
                 for key, value in plan["field_map"].items()}
    # THE WRITE ORDER IS THE DEPENDENCY ORDER, not the reading order. A V1 store is a parent chain,
    # and a child written before its parent is a child the kernel refuses -- so `_settle_bindings`
    # numbered every record by how deep it sits in that chain and the run walks the levels. Within
    # a level the reading order is kept, so a run is reproducible.
    #
    # `resolved` is what makes the rewrite honest: the V1 parent id is replaced by the id the
    # parent ACTUALLY got, which is not the V1 one in any project that already holds items of that
    # type. It starts from the records an earlier run imported (idempotency: a re-run of a partial
    # migration must bind to those, not to nothing) and grows as this run creates items.
    created, resolved = [], {}
    for entry in plan["records"]:
        if entry["verdict"] == "already_imported" and entry.get("item_id"):
            resolved[entry["legacy_id"]] = entry["item_id"]
    try:
        for entry in sorted(importable,
                            key=lambda e: (e.get("write_order", 0), e["source"], e["ordinal"])):
            payload, problem = _read_document(state, entry["source"])
            if problem:
                raise MigrationError("%s %s" % (entry["source"], problem))
            # BY ORDINAL, not by id: two records in one document may carry one V1 id, and keying
            # this lookup by id wrote record B's fields under record A's legacy metadata. Such a
            # document is refused at planning time, so this is the second line of the same defence
            # rather than the only one -- and it is what makes the plan's classification and the
            # written item provably the same record.
            found = scan_document(payload)
            by_ordinal = {ordinal: record for ordinal, _key, record in found}
            record = by_ordinal.get(entry["ordinal"])
            if record is None or _key_of(found, entry["ordinal"]) != entry["legacy_id"]:
                raise MigrationError(
                    "%s no longer holds %s at position %d; the document changed under the plan. "
                    "Remedy: re-run `python scripts/harness.py migrate --dry-run`."
                    % (entry["source"], entry["legacy_id"], entry["ordinal"]))
            fields, missing = _item_fields(
                entry["v2_type"], record, field_map,
                provenance=_provenance(entry["source"], entry["legacy_id"]))
            if missing and entry["target"] != "archive":
                raise MigrationError(
                    "%s no longer yields %s for %s; the state changed under the plan. Remedy: "
                    "re-run `python scripts/harness.py migrate --dry-run`."
                    % (entry["source"], ", ".join(missing), entry["legacy_id"]))
            body = _with_legacy(_rebind(entry["v2_type"], fields, resolved), entry, record)
            if entry.get("unresolved_fields"):
                item = state.capture_migrated_unresolved(
                    entry["v2_type"], body, entry["archive_year"])
            elif entry["target"] == "archive":
                item = state.capture_migrated_archive(
                    entry["v2_type"], body, entry["legacy_type"], entry["legacy_status"],
                    entry["archive_year"])
            else:
                item = state.capture(entry["v2_type"], body)
            resolved[entry["legacy_id"]] = item["id"]
            created.append((entry, item["id"]))
    except BaseException as exc:
        # A HALF-WRITTEN RUN STILL GETS ITS RECEIPT, and the refusal names the partial state.
        # `capture_preflight` is asked of every record before the plan promises anything, so the
        # expected causes here are the ones no reading can rule out -- a lock another process
        # holds, a disk, an interrupt. What must not happen either way is what was measured before
        # this: items in the store, no `DEC`, and a raw kernel message that never mentions that
        # anything had been written. The receipt is attempted first and its own failure is folded
        # into the message rather than replacing it.
        if not created:
            raise
        note = None
        try:
            receipt = state.capture(RECEIPT_TYPE,
                                    _receipt_fields(plan, created, digest, interrupted=str(exc)))
            note = "recorded as %s" % receipt["id"]
        except BaseException as second:      # noqa: BLE001 -- the first failure must survive
            note = ("and the receipt could NOT be written either (%s), so the only record of "
                    "these ids is this message" % second)
        raise MigrationError(
            "the import stopped after writing %d item(s) (%s) -- %s. Those items are in the state "
            "and are NOT rolled back; a re-run skips them by their `legacy_fields.legacy_id`. The "
            "failure was: %s"
            % (len(created), ", ".join(item_id for _e, item_id in created), note, exc)) from exc
    moved = _retire_absorbed_documents(state, plan, created)
    receipt = state.capture(RECEIPT_TYPE, _receipt_fields(plan, created, digest, moved=moved))
    return {"created": [item_id for _entry, item_id in created], "receipt": receipt["id"],
            "moved": moved}


def absorbed_documents(plan: dict, written=None) -> list:
    """The V1 documents this plan leaves with nothing of its own left -- SR-0005's condition.

    TWO CLAUSES, and each one is a defect the other does not cover:

      * at least one record of the document BECAME AN ITEM. Without it, a kit document that merely
        mentions ids -- `acceptance_reports.yaml` keys its entries `ACC-nnnn` and every one of them
        is a report about a task, not a backlog record -- would satisfy the second clause vacuously
        and be moved out of the project.
      * NO BACKLOG RECORD of it is left untranslated. `not_an_item` records do not hold a document
        back, and that is deliberate rather than lenient: such a record is a cross-reference note
        or a record of some other kind, so it is not a second copy of anything, while ONE of them
        in a store of 265 real ones would otherwise keep the whole store beside its own items for
        ever -- which is exactly the double SR-0005 exists to end, and which `validate` would then
        report as an error nobody could clear.

    ...AND A WALL IS NEVER MOVED, whatever its records did. A wall is a kit document whose CONTENT
    a registered, refusal-capable hook reads (`layout.gated_documents`, carried in the plan), and
    moving one to `legacy/` takes it out from under that gate: the gate then reads an absent file,
    and what a fail-closed gate does with one is its own business and not this command's to
    provoke. SR-0005's reason for the move -- the same thing existing twice -- does not reach this
    case either, because the gate does not read the file for its ITEMS. Reachable by construction
    rather than in the field, which is why it is a clause rather than a note;
    `test_migrate.test_a_document_a_registered_gate_reads_is_never_moved_to_legacy` builds the
    installation that reaches it and is where that reading is recorded.

    `written` is the set of `(source, ordinal)` pairs the RUN actually created, so a document is
    only retired on the strength of writes that happened -- an interrupted run leaves its documents
    where they are. The dry run passes None and asks the plan instead, which is the same question
    about a run that has not happened yet.
    """
    absorbed, unfinished = set(), set(plan.get("gated_documents") or ())
    for entry in plan["records"]:
        source, verdict = entry["source"], entry["verdict"]
        if verdict == "already_imported" or (
                verdict in _IMPORTING_VERDICTS
                and (written is None or (source, entry["ordinal"]) in written)):
            absorbed.add(source)
        elif verdict != "not_an_item":
            unfinished.add(source)
    return sorted(absorbed - unfinished)


def _retire_absorbed_documents(state: ProjectState, plan: dict, created: list) -> list:
    """Move every absorbed V1 document under `legacy/`, with its hash. Returns the receipt rows.

    THE HASH IS TAKEN BEFORE THE MOVE and of the bytes that are moved, so the receipt says what
    was carried rather than what was planned; a document that changed under the plan is caught by
    the digest long before this. The move itself is `os.replace` within one directory tree, which
    is atomic per file -- there is no state in which a document is in both places, and none in
    which it is in neither.
    """
    written = {(entry["source"], entry["ordinal"]) for entry, _item_id in created}
    moved = []
    for rel in absorbed_documents(plan, written):
        facts = _file_facts(state, rel)
        target = state.legacy_path(rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        os.replace(os.path.join(state.root, *rel.split("/")), target)
        facts["moved_to"] = _relative(state, target)
        moved.append(facts)
    return moved


def _key_of(found, ordinal):
    """The legacy id the walk saw at `ordinal`, or None."""
    for position, key, _record in found:
        if position == ordinal:
            return key
    return None

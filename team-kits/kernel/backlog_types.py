"""Item types, status automata and V1 mapping (HARNESS_V2_SPEC.md II.2 / II.10).

Single machine-readable source for:
- the 12 typed items (dev/office root: PR; research root: RQ + HYP/EXP)
- their status automata (chains, explicit terminal edges, TSK back-edges) --
  transitions happen ONLY through `assert_transition` callers (kernel
  `transition`); anything else is a schema error (spec II.2)
- type-dependent approval invalidation targets (PR/RQ/CR/PROC -> DRAFT,
  BUG -> TRIAGED, SR -> PROPOSED, EXP -> DESIGNED; HYP deliberately absent --
  it carries no approval_ref and rides on the RQ scope approval)
- the `<TYP>-nnnn` id convention
- the binding V1 -> V2 status mapping (spec II.10; unknown values RAISE --
  the kernel layer turns that into a block + Decision item, never a guess)

Terminal edges are the conservative explicit set below; widening any of them
is a SPEC change, not an implementation decision (spec II.2). BLOCKED is a
flag (`blocked_by`), never a status.
"""
from __future__ import annotations

import re


# -- status automata -----------------------------------------------------------

def _edges(chain, terminal_from):
    """Build the allowed-transition set: consecutive chain edges + terminal edges."""
    allowed = set(zip(chain, chain[1:]))
    for terminal, sources in terminal_from.items():
        for src in sources:
            allowed.add((src, terminal))
    return allowed


class _Automaton:
    def __init__(self, chain, terminals, terminal_from, extra_edges=(), extra_states=()):
        self.chain = tuple(chain)
        self.terminals = frozenset(terminals)
        self.states = frozenset(chain) | self.terminals | frozenset(extra_states)
        self.allowed = _edges(chain, terminal_from) | set(extra_edges)
        # construction-time self-checks (Fable-Check 5): terminals never have
        # outgoing edges, and every edge endpoint is a registered state -- a
        # typo in an edge fails loudly here instead of becoming a dead edge
        for src, dst in self.allowed:
            if src in self.terminals:
                raise AssertionError("terminal state %r must not have outgoing edges" % src)
            if src not in self.states or dst not in self.states:
                raise AssertionError("edge (%r -> %r) references unregistered state" % (src, dst))

    @property
    def initial(self):
        return self.chain[0]


_PR_LIKE = _Automaton(
    chain=("DRAFT", "APPROVED", "IN_DELIVERY", "DELIVERED", "ACCEPTED"),
    terminals=("ACCEPTED", "REJECTED", "SUPERSEDED"),
    terminal_from={
        "REJECTED": ("DRAFT", "APPROVED", "IN_DELIVERY", "DELIVERED"),
        "SUPERSEDED": ("DRAFT", "APPROVED", "IN_DELIVERY", "DELIVERED"),
        # ACCEPTED only via the chain (DELIVERED -> ACCEPTED)
    },
)

AUTOMATA = {
    "PR": _PR_LIKE,
    "RQ": _PR_LIKE,
    "FR": _Automaton(
        chain=("OPEN", "TRIAGED"),
        terminals=("MERGED", "CONVERTED", "REJECTED"),
        terminal_from={  # a triage OUTCOME requires a triage first
            "MERGED": ("TRIAGED",),
            "CONVERTED": ("TRIAGED",),
            "REJECTED": ("TRIAGED",),
        },
    ),
    "CR": _Automaton(
        chain=("DRAFT", "APPROVED", "APPLIED"),
        terminals=("APPLIED", "REJECTED"),
        terminal_from={"REJECTED": ("DRAFT", "APPROVED")},
    ),
    "BUG": _Automaton(
        chain=("OPEN", "TRIAGED", "APPROVED", "FIXED", "VERIFIED"),
        terminals=("VERIFIED", "REJECTED", "DUPLICATE"),
        terminal_from={
            "REJECTED": ("OPEN", "TRIAGED", "APPROVED", "FIXED"),
            "DUPLICATE": ("OPEN", "TRIAGED", "APPROVED", "FIXED"),
            # VERIFIED only via the chain (FIXED -> VERIFIED)
        },
    ),
    "SR": _Automaton(
        chain=("PROPOSED", "ACCEPTED"),
        terminals=("SUPERSEDED",),
        terminal_from={"SUPERSEDED": ("PROPOSED", "ACCEPTED")},
    ),
    "TSK": _Automaton(
        chain=("DRAFT", "READY", "LEASED", "IN_PROGRESS", "SUBMITTED", "DONE", "VALIDATED"),
        terminals=("VALIDATED", "CANCELLED"),
        terminal_from={
            "CANCELLED": ("DRAFT", "READY", "LEASED", "IN_PROGRESS", "SUBMITTED", "DONE", "FAILED"),
            # VALIDATED only via the chain (DONE -> VALIDATED, QA evidence)
        },
        extra_edges=(
            # explicit back-edges (spec II.2 Querregeln)
            ("LEASED", "READY"),          # lease timeout / spawn failure
            ("IN_PROGRESS", "FAILED"),
            ("SUBMITTED", "FAILED"),
            ("DONE", "FAILED"),
            ("FAILED", "READY"),          # ONLY on approved retry (kernel checks)
        ),
        extra_states=("FAILED",),         # non-terminal, non-chain side state
    ),
    "PROC": _Automaton(
        chain=("DRAFT", "APPROVED", "ACTIVE"),
        terminals=("RETIRED",),
        terminal_from={"RETIRED": ("DRAFT", "APPROVED", "ACTIVE")},
    ),
    "HYP": _Automaton(
        chain=("PROPOSED", "TESTING"),
        terminals=("SUPPORTED", "REFUTED", "INCONCLUSIVE"),
        terminal_from={
            "SUPPORTED": ("TESTING",),
            "REFUTED": ("TESTING",),
            "INCONCLUSIVE": ("TESTING",),
        },
    ),
    "EXP": _Automaton(
        chain=("DESIGNED", "APPROVED", "RUNNING", "COMPLETED", "ANALYZED"),
        terminals=("ANALYZED", "ABORTED"),
        terminal_from={"ABORTED": ("DESIGNED", "APPROVED", "RUNNING", "COMPLETED")},
    ),
}

# -- approval invalidation (spec II.2 table; atomic op lives in the kernel) ----

INVALIDATION_TARGET = {
    "PR": "DRAFT",
    "RQ": "DRAFT",
    "CR": "DRAFT",
    "PROC": "DRAFT",
    "BUG": "TRIAGED",
    "SR": "PROPOSED",
    "EXP": "DESIGNED",
    # HYP deliberately absent: no approval_ref, rides on the RQ scope approval
}

# -- id convention + storage dirs ---------------------------------------------

ACTIVE_DIRS = {
    "PR": "product/active",
    "FR": "inbox/active",
    "CR": "changes/active",
    "BUG": "bugs/active",
    "SR": "system/active",
    "TSK": "tasks/active",
    "PROC": "procedures/active",
    "INV": "invariants/active",
    "APR": "approvals",
    "RQ": "research/active",
    "HYP": "hypotheses/active",
    "EXP": "experiments/active",
    "DEC": "decisions/active",   # Decision items (id prefix: implementation choice)
    "EVD": "evidence",           # Evidence (no own project status; id prefix: impl. choice)
    "ARC": "architecture/active",
    "WFR": "design/wireframes",  # frozen on scope approval (II.6a)
    "DSN": "design/revisions",   # frozen design revisions (II.6; promotion path)
}

# The item a project HANGS FROM, per kit -- the one the entry gate seeds at onboarding and the one
# `_root.has_root_item` looks for to decide a repo is past setup. A kit is absent here when it has no
# such item: the office kit is led by procedures and master data, its constitution knows no PR
# anywhere, and the "PR" this map used to claim for it sent the entry gate to write a PR-0001 no
# office role would ever read.
ROOT_TYPE_BY_KIT = {"dev-team": "PR", "research-team": "RQ"}

_ID_RE = re.compile(r"([A-Z]{2,4})-(\d{4,})", re.ASCII)


def format_id(item_type: str, number: int) -> str:
    if item_type not in ACTIVE_DIRS:
        raise KeyError("unknown item type %r" % item_type)
    return "%s-%04d" % (item_type, number)


def parse_id(item_id: str):
    """Return (type, number) or raise ValueError with a remedy."""
    # fullmatch + ASCII: `$` would match before a trailing newline and \d would
    # accept non-ASCII digits (Fable-Check 6/BUG-2)
    m = _ID_RE.fullmatch(item_id or "")
    if not m or m.group(1) not in ACTIVE_DIRS:
        raise ValueError(
            "invalid item id %r -- expected <TYP>-nnnn with TYP one of %s. "
            "Remedy: use kernel-assigned ids only."
            % (item_id, "/".join(sorted(ACTIVE_DIRS)))
        )
    return m.group(1), int(m.group(2))


# -- transition API ------------------------------------------------------------

class TransitionError(ValueError):
    """Illegal status transition -- a schema error per spec II.2."""


def initial_status(item_type: str) -> str:
    auto = AUTOMATA.get(item_type)
    if auto is None:
        raise TransitionError(
            "unknown item type %r. Remedy: use one of %s."
            % (item_type, "/".join(sorted(AUTOMATA)))
        )
    return auto.initial


def is_terminal(item_type: str, status: str) -> bool:
    return status in AUTOMATA[item_type].terminals


def assert_transition(item_type: str, from_status: str, to_status: str) -> None:
    """Raise TransitionError unless (from -> to) is an allowed edge."""
    auto = AUTOMATA.get(item_type)
    if auto is None:
        raise TransitionError(
            "unknown item type %r. Remedy: use one of %s."
            % (item_type, "/".join(sorted(AUTOMATA)))
        )
    for status in (from_status, to_status):
        if status not in auto.states:
            raise TransitionError(
                "unknown status %r for %s (states: %s). BLOCKED is a flag "
                "(blocked_by), never a status. Remedy: use `python scripts/harness.py transition` "
                "with a defined status." % (status, item_type, ", ".join(sorted(auto.states)))
            )
    if (from_status, to_status) not in auto.allowed:
        raise TransitionError(
            "illegal transition %s: %s -> %s (allowed from %s: %s). Remedy: "
            "run the required intermediate kernel operations; direct jumps are "
            "schema errors (spec II.2)."
            % (
                item_type,
                from_status,
                to_status,
                from_status,
                ", ".join(sorted(dst for src, dst in auto.allowed if src == from_status)) or "-",
            )
        )


def invalidation_target(item_type: str) -> str:
    """Target status when hashed fields of an approved item change (spec II.2)."""
    try:
        return INVALIDATION_TARGET[item_type]
    except KeyError:
        raise KeyError(
            "%s has no approval invalidation target (it carries no approval_ref)"
            % item_type
        ) from None


# -- per-type field contracts (spec II.2 "Pflichtfelder") ----------------------

# Kernel-set on capture (callers never provide these): id, status, revision,
# approval_ref, created. The lists below are the CALLER-provided required
# fields; optionality noted per spec (user_story, related_pr, derives_from on
# PROC, design_ref conditional on TSK).
# STATUS-DEPENDENT duties enforced by the 1.4c validator, NOT at capture:
# FR.triage_result (from TRIAGED), PROC.approved_hash (from APPROVED),
# PR.user_story (required unless class == technical_enabler),
# INV text/value (exactly one of the two required).
REQUIRED_FIELDS = {
    "PR": ("title", "class", "problem", "goal", "acceptance_criteria",
           "invariants", "out_of_scope", "priority"),
    "RQ": ("title", "class", "question", "motivation", "acceptance_criteria",
           "out_of_scope", "priority"),
    "FR": ("title", "request_text"),
    "CR": ("title", "target_pr", "target_revision", "change_description",
           "acceptance_criteria"),
    "BUG": ("title", "related_pr", "observed", "expected", "repro", "severity",
            "acceptance_criteria"),
    "SR": ("title", "derives_from", "contract", "affected_components"),
    "TSK": ("product_requirement", "root_revision", "derives_from", "type",
            "assigned_role", "acceptance_refs", "required_inputs",
            "allowed_scope", "forbidden_scope", "expected_outputs",
            "dependencies"),
    "PROC": ("title", "steps", "roles"),
    "INV": ("scope", "source", "check"),
    "HYP": ("derives_from", "statement", "testable_prediction"),
    "EXP": ("derives_from", "design", "variables", "success_criteria",
            "evidence_refs"),
    "DEC": ("title", "context", "decision", "consequences", "source"),
    # `result` beyond the spec's field list, and additively: the spec fixes what
    # Evidence must SAY about itself, while a gate has to know what it says about
    # the work. Without a verdict field the store cannot distinguish "QA ran and
    # passed" from "QA ran and failed", and `gate_git` would open a merge on the
    # existence of a failing report -- the false-accept an earlier audit found in
    # the V1 report files, one level in.
    "EVD": ("kind", "related", "result", "summary", "artifact_refs"),
}

# The OTHER half of the same contract: fields spec II.2 declares for a type and
# lets it omit. Machine-readable for the reason `schemas.item_field_contracts`
# reports every DECLARED field rather than only the required ones -- whether a
# field means anything to the reference graph is a question about the FIELD, and
# an item's freedom to leave it out is a question about the ITEM. Reading only
# `REQUIRED_FIELDS` answers the first question with the second one, and that is
# how `PROC.derives_from` (spec II.2: "derives_from (optional)") and
# `FR.related_pr` ("related_pr (optional)") stayed outside the graph: a PROC
# captured against a phantom parent was reported by nobody and an Evidence
# recorded on it never reached its root, the identical damage the `SR` and the
# `ARC`/`WFR`/`DSN` rounds were about.
# The comment above lists the same four fields in prose; this is that sentence
# in a form the derivation can read.
OPTIONAL_FIELDS = {
    "PR": ("user_story",),      # optional for class == technical_enabler
    "FR": ("related_pr",),
    "PROC": ("derives_from",),
    "TSK": ("design_ref",),     # required only when the UI scope has a frozen design
}

# Required fields for which an EMPTY value is the same lie as absence. A list-valued
# field is normally allowed to be empty -- a PR with no invariants has none -- so this
# is the exception, and it exists only where the emptiness would leave a gate deciding
# on nothing:
#   * `EVD.related` is the binding the merge gate resolves. Bound to nothing, the
#     record judges nothing; `report.qa_verdicts_by_subject` can only file it under its
#     own id, so it neither opens nor closes the merge it was recorded for.
#   * `EVD.artifact_refs` is the only field of an Evidence that points OUT of the
#     record. `result` is the claim and `summary` is prose about the claim, so with no
#     reference the record IS the assertion it exists to prove -- while `gate_git`
#     opens a merge on it and its own remedy text presents the reference as the proof.
#     What the kernel can check is that the verdict names where to look; whether the
#     artefact holds up is the auditor's job, and it cannot even start without a path.
NONEMPTY_FIELDS = {"EVD": ("related", "artifact_refs")}

# -- the reference graph: through which field an item names what it belongs to --
#
# A field BINDS an item when its value is the ID of the item this one hangs from.
# WHICH FIELD NAMES do that is a decision about the state model and is made here,
# once, in `_BINDING_FIELD_NAMES`. WHICH TYPES carry one is NOT a second decision:
# it follows from the type's FIELD CONTRACT, so the map below is DERIVED rather
# than listed beside it.
#
# THE CONTRACT HAS TWO SOURCES AND THE DERIVATION READS BOTH IN FULL, because
# reading half of one of them is how this went wrong three times, one type
# further along each time:
#   * the CAPTURE-time contract, which covers exactly the types `capture`
#     creates. It is `REQUIRED_FIELDS` PLUS `OPTIONAL_FIELDS` -- a contract is
#     the set of fields a type HAS, and `REQUIRED_FIELDS` is by construction
#     only the fields an item may not omit.
#   * `kernel/schemas/*.yaml` is the contract of the types the kernel FREEZES
#     (ARC/WFR/DSN, spec II.6a) -- `schemas.item_field_contracts`, which reports
#     required and optional fields alike, for this same reason. Those items
#     never pass `capture`, so `REQUIRED_FIELDS` says nothing about them at all.
#
# Round one: `report._parents_of` enumerated the derived types (TSK/BUG/CR/HYP/
# EXP) and `SR` -- given a REQUIRED `derives_from` in this lockstep, and the
# natural subject of a review -- was not in the list, so an Evidence recorded
# against an `SR` resolved to no root and `gate_git` refused the merge with
# "nothing judges this work" at the role that had just judged exactly this work.
# Round two: the map was derived, but from `REQUIRED_FIELDS` alone, and `ARC`,
# `WFR` and `DSN` -- each of which declares its parent binding in its schema --
# reproduced the identical refusal for the architect and the designer. Reading
# both sources is what makes this a definition: a type joins the graph the day
# some contract of its own gives it a binding field. (Knowing the field was half
# of it for `WFR`/`DSN`: those are stored per revision, so their ids resolved to
# no file at all -- `state._frozen_revision_path` is the other half.)
# Round three: both sources were read, but the capture-time one only through
# `REQUIRED_FIELDS` -- so `PROC.derives_from` and `FR.related_pr`, optional by
# spec II.2 and item ids when present, were bindings the graph did not walk.
#
# `EVD.related` is in here for the same reason it is in `NONEMPTY_FIELDS`: it is
# the id of the work the record is ABOUT, which is the same hop the graph walks.
# `DSN.root` is the frozen design revision's binding to the PR/RQ it was frozen
# against (`staging.freeze_design`); the name is generic, the meaning is not.
_BINDING_FIELD_NAMES = ("product_requirement", "derives_from", "related_pr",
                        "target_pr", "related", "root")


def _contract_fields() -> dict:
    """{item type -> set of field names its contracts declare}, over BOTH sources, in full."""
    from .schemas import item_field_contracts
    fields = {item_type: set(names) for item_type, names in REQUIRED_FIELDS.items()}
    for item_type, names in OPTIONAL_FIELDS.items():
        fields.setdefault(item_type, set()).update(names)
    for item_type, declared in item_field_contracts().items():
        fields.setdefault(item_type, set()).update(declared)
    return fields


def _declared_required_fields() -> dict:
    """{item type -> the fields SOME contract of its own requires}, over both sources.

    `REQUIRED_FIELDS` is what a CALLER must hand `capture`; this is what an item must CARRY, and
    the two differ exactly for the types no caller captures. The state validator judges files, not
    capture calls, so it reads this: its field-duty loop ran zero times for `ARC`, `WFR` and `DSN`
    -- the three types whose duties are declared in `kernel/schemas/` -- while spec II.8 assigns
    it "ARC ohne derives_from -> Validator-Flag" by name.
    """
    from .schemas import item_required_fields
    required = {item_type: tuple(names) for item_type, names in REQUIRED_FIELDS.items()}
    for item_type, names in item_required_fields().items():
        required[item_type] = tuple(dict.fromkeys(required.get(item_type, ()) + tuple(names)))
    return required


def _parent_fields() -> dict:
    return {
        item_type: tuple(f for f in _BINDING_FIELD_NAMES if f in fields)
        for item_type, fields in sorted(_contract_fields().items())
        if not fields.isdisjoint(_BINDING_FIELD_NAMES)
    }


# `PARENT_FIELDS` (the reference graph) and `DECLARED_REQUIRED_FIELDS` (what the state VALIDATOR
# holds a stored item to -- see `_declared_required_fields`) are DERIVED, and both derivations
# read `kernel/schemas/*.yaml`, which needs PyYAML. Computing them at module scope would make
# `import kernel.backlog_types` a PyYAML import and six file reads, and that import is the one
# path a hook can take to learn the type names without pulling the parser in:
# `guard_no_adhoc` keeps its type list as a LITERAL for exactly that reason ("a guard that cannot
# load must not stop guarding"), and spec II.7 says integrity gates are stdlib-first with no
# PyYAML import load on the hot path. So the values are computed on FIRST ACCESS instead. The
# consumers inside the kernel (`state`, `report`) bind them with a normal `from ... import` and
# pay the cost once at their own import, where PyYAML is already loaded anyway.
_DERIVED = {"PARENT_FIELDS": _parent_fields, "DECLARED_REQUIRED_FIELDS": _declared_required_fields}
_derived_cache: dict = {}


def __getattr__(name: str):
    """Module-level lazy attributes (PEP 562) -- also serves `from .backlog_types import X`."""
    if name in _DERIVED:
        if name not in _derived_cache:
            _derived_cache[name] = _DERIVED[name]()
        return _derived_cache[name]
    raise AttributeError("module %r has no attribute %r" % (__name__, name))


def __dir__():
    return sorted(list(globals()) + list(_DERIVED))

# Fields whose change INVALIDATES a current approval (spec II.2 subject
# manifests + Freigabe-Invalidierung): revision +1, approval_ref cleared,
# status -> INVALIDATION_TARGET -- atomically, in the kernel edit path.
# Implementation notes: `design_refs` (PR/RQ) is the item field carrying the
# scope manifest's "verbindliche Designreferenzen" (frozen WFR/DSN refs);
# PROC hashes `roles` IN ADDITION to the V1 steps-only hash -- a role change
# is approval-relevant (additive hardening over V1).
HASHED_FIELDS = {
    "PR": ("problem", "goal", "acceptance_criteria", "invariants",
           "out_of_scope", "design_refs"),
    "RQ": ("question", "motivation", "acceptance_criteria", "out_of_scope",
           "design_refs"),
    "CR": ("target_pr", "target_revision", "change_description",
           "acceptance_criteria"),
    "BUG": ("observed", "expected", "repro", "severity", "acceptance_criteria"),
    "SR": ("derives_from", "contract", "affected_components"),
    "PROC": ("steps", "roles"),
    "EXP": ("design", "variables", "success_criteria"),
}


# -- TSK.type vocabulary -------------------------------------------------------

# The spec names TSK.type as a required field without fixing its values. Left
# free-form it is unusable as a GATE input: the design_ref rule (II.6 "UI-Tasks
# bei vorhandenem bestaetigtem Design ohne design_ref gesperrt") has to decide
# "is this a UI task", and matching a free-text field against a sample list
# fails OPEN on every synonym the orchestrator invents ("ui-implementation",
# "frontend-work", ...). So the vocabulary is CLOSED here and validated at
# capture: an unknown type is refused early and visibly, instead of quietly
# skipping a gate later. Widening the list is a spec decision, not a guess at
# call time.
TASK_TYPES = frozenset((
    "analysis",         # read-only investigation (rides an APR.kind: analysis)
    "design",           # WFR/DSN authoring
    "architecture",     # ARC authoring
    "implementation",   # non-UI production code
    "bugfix",           # BUG is a first-class root type (II.2) and its fix work
                        # is not "implementation" of a new requirement
    "ui",               # user-facing surface -- the design_ref-bearing type
    "test",             # QA/regression work
    "review",           # audit/review pass
    "docs",
    "ops",              # devops/pipeline/release work
    "research",         # research-kit execution work
))

# The subset for which a confirmed design makes design_ref mandatory (II.6).
UI_TASK_TYPES = frozenset(("ui",))


# -- Evidence contract (spec II.2 "Evidence") ----------------------------------

# Evidence carries no project STATUS, and that is exactly why it has to carry a
# VERDICT: it is the only item type whose whole purpose is to say whether
# something held. `gate_git` opens a merge on it, so both fields below are gate
# inputs and both are CLOSED for the same reason TASK_TYPES is -- an unrecognised
# value does not fail a check, it SKIPS one. An unknown `result` is not a `fail`
# and an unknown `kind` is not QA, so in either direction the gate would go quiet
# on precisely the value nobody validated. Widening either set is a spec
# decision, not a guess at call time.
EVIDENCE_KINDS = frozenset(("test", "review", "acceptance", "audit"))

# The kinds that judge the PROJECT rather than one delivery. `audit` is the whole
# list and the reason is specific to it: an audit run judges the repo-wide scope
# (II.10a Auditor-Routine: one Evidence per run, related to that scope), so
# accepting it as a delivery's QA would open a merge on a report that never looked
# at the branch.
PROJECT_EVIDENCE_KINDS = frozenset(("audit",))

# The kinds a merge of an item may rest on -- DERIVED, and that is the point. Two
# hand-written lists of the same words drift in one direction only: a kind added to
# EVIDENCE_KINDS and forgotten here would become a verdict the merge gate never
# reads, i.e. a role recording it in good faith while the gate reports "no QA
# Evidence". Subtracting the declared exception makes a new kind judge deliveries by
# DEFAULT, which is the reading a reviewer can check against the one sentence above.
QA_EVIDENCE_KINDS = EVIDENCE_KINDS - PROJECT_EVIDENCE_KINDS

# A verdict is binary on purpose. "inconclusive" is the tempting third value and
# it is the one a gate cannot act on: it would have to be read as pass or as
# fail, and whichever was chosen the other reading would be the silent one. A run
# that could not decide is a `fail` whose `summary` says why -- spec II.10a
# already rules that a partial run is not merge evidence.
EVIDENCE_RESULTS = frozenset(("pass", "fail"))

# Types that are a RECORD of something that already happened rather than a piece of
# living state. What separates them from every other type is that they have no
# automaton and no future: an item with a status is a thing whose story continues, so
# editing a detail of it is part of that story, while a record's only claim is that a
# run produced this verdict at this time. Change any field of it and the claim is
# simply false -- there is no revision, no approval to invalidate, nothing that would
# make the change visible. So the kernel refuses the edit outright (state.py edit path)
# and a superseding record is the only way forward. This is what lets `gate_git` say
# "retired by recording the re-run, never by editing" and mean it: without the refusal
# a FAIL becomes a PASS in place, with no new item and no trace in the store.
IMMUTABLE_TYPES = frozenset(("EVD",))

# The work-order contract of a TSK: everything a gate reads to decide what this
# task may do. FROZEN once the task leaves DRAFT (enforced in the kernel edit
# path), because these fields are gate INPUTS and a task past DRAFT is either
# queued, leased or being worked by a live specialist:
#   * `allowed_scope`/`forbidden_scope` are gate layer 3's only inputs -- widening
#     them on a LEASED, BOUND task hands a running specialist the whole repo,
#     with no approval and no revision bump,
#   * `type` decides whether the design_ref rule applies (II.6),
#   * `assigned_role` is what the dispatch gate matches the spawn against,
#   * `acceptance_refs`/`dependencies` are what makes the task checkable at all.
# Re-planning is legitimate -- it just has to be VISIBLE: bring the task back to
# DRAFT (or cancel and re-create it), which is a status transition through the
# automaton rather than a quiet field write.
TSK_PLAN_FIELDS = frozenset((
    "product_requirement", "root_revision", "derives_from", "type", "assigned_role",
    "acceptance_refs", "required_inputs", "allowed_scope", "forbidden_scope",
    "expected_outputs", "dependencies",
))


# -- V1 -> V2 status mapping (spec II.10; machine-readable, never guess) -------

V1_STATUS_MAPPING = {
    # (v1_type, v1_status) -> (v2_type, v2_status, archive_candidate)
    # The spec's II.10 table lists only the NON-identity rows; the identity
    # rows below (TSK IN_PROGRESS/DONE/VALIDATED, PRD APPROVED/ACCEPTED,
    # PROC APPROVED/ACTIVE/RETIRED) are an ADDITIVE completion covering the
    # V1 vocabulary actually measured in the 2026-07-24 review (report par. 4) --
    # without them every plain DONE import would block.
    ("TSK", "TODO"): ("TSK", "READY", False),
    ("TSK", "IN_PROGRESS"): ("TSK", "IN_PROGRESS", False),
    ("TSK", "DONE"): ("TSK", "DONE", False),
    ("TSK", "VALIDATED"): ("TSK", "VALIDATED", True),
    ("PRD", "PROPOSED"): ("PR", "DRAFT", False),
    ("PRD", "APPROVED"): ("PR", "APPROVED", False),
    ("PRD", "TESTED"): ("PR", "DELIVERED", False),
    ("PRD", "ACCEPTED"): ("PR", "ACCEPTED", True),
    ("PRD", "DONE"): ("PR", "ACCEPTED", True),
    ("SR", "DRAFT"): ("SR", "PROPOSED", False),
    ("SR", "ACTIVE"): ("SR", "ACCEPTED", False),
    ("SR", "DONE"): ("SR", "ACCEPTED", True),
    ("PROC", "PROPOSED"): ("PROC", "DRAFT", False),
    ("PROC", "APPROVED"): ("PROC", "APPROVED", False),
    ("PROC", "ACTIVE"): ("PROC", "ACTIVE", False),
    ("PROC", "RETIRED"): ("PROC", "RETIRED", True),
}


class UnknownV1Status(ValueError):
    """No mapping for a V1 status -- the migration tool must BLOCK and raise a
    Decision item, never guess (spec II.10)."""


def map_v1_status(v1_type: str, v1_status: str):
    """Return (v2_type, v2_status, archive_candidate); the V1 original is
    preserved by the caller in `legacy_fields` (lossless, spec II.10)."""
    try:
        return V1_STATUS_MAPPING[(v1_type, v1_status)]
    except KeyError:
        raise UnknownV1Status(
            "no V1->V2 mapping for %s status %r. Remedy: the migration blocks "
            "here -- record a Decision item and extend the mapping table "
            "deliberately (spec II.10: never guess)." % (v1_type, v1_status)
        ) from None

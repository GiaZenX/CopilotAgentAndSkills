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

ROOT_TYPE_BY_KIT = {"dev-team": "PR", "office-team": "PR", "research-team": "RQ"}

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
                "(blocked_by), never a status. Remedy: use `harness transition` "
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
    "EVD": ("kind", "related", "summary", "artifact_refs"),
}

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

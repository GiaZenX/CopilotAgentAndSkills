"""Two-phase approval provenance (HARNESS_V2_SPEC.md II.2) -- step 1.4b.

A manual `approved_by: user` proves nothing. The kernel:
1. writes an immutable PENDING request (request_id, item, revision,
   content hash, kind, expiry, per-request MINT CODE) and generates the
   COMPLETE approval question deterministically -- text, header AND the three
   options, marker `[APR-REQ:<id>]` in the text
2. the PreToolUse hook (phase 2) enforces exact string equality of marked
   questions against `build_question`
3. `mint` creates the APR ONLY when the answer equals the kernel-generated
   approval label VERBATIM, including its per-request mint code
   (`Freigeben [7f3a2c]`); never for expired/mismatched requests; the item
   must still be at the requested revision AND content hash (out-of-band
   edits kill the mint)

MINT CODE, and why (empirical finding 2026-07-24, spike S2b): Claude Code
2.1.219 reports answers as `toolUseResult.answers = {question: answer_STRING}`
-- a clicked option and text typed into the always-present "Other" row are
INDISTINGUISHABLE (verified against real session transcripts). The spec's
original demand ("bind the token to the option identity, never the string")
is therefore not implementable on this platform. The mint code restores the
practical guarantee: the label carries per-request entropy that lives ONLY in
the option, so casual free text ("ok", "ja", "freigeben") can never mint.
Residual, documented honestly: a user who deliberately transcribes the code
mints -- but that user IS the approving authority, and the MODEL cannot
produce `answers` at all (the platform writes them, and the PreToolUse hook
pins the question the user saw).
The guarantee is CONDITIONAL on two things NEITHER library code NOR any
in-process check can establish (measured 2026-07-25, see
_assert_minting_caller): (i) only the PostToolUse hook reaches `mint` -- but the
hook is meant to be run with a payload on stdin, so anyone able to execute
`python <hooks>/gate_approval.py < forged.json` mints, and the forged payload is
assembled from the readable pending request; and (ii) `approvals/pending/` is
kernel-only territory (the codes sit there in cleartext, and the question text
even names the path). BOTH need a Bash/PowerShell-level guard, because
`guard_harness_selfmod` gates only Edit|Write|MultiEdit. Until that guard
exists, `approval_provenance` is `unverified` and the enforcement mode is
`audited` -- and `python scripts/harness.py doctor` must compute that rather than assert it.

Bundling (user decision 2026-07-24): one analysis/scope APR may cover several
analysis tasks LISTED in its subject manifest.
"""
from __future__ import annotations

import inspect
import os
import re
import sys
import time
import uuid

from .backlog_types import AUTOMATA, HASHED_FIELDS, parse_id
from .hashing import subject_manifest_hash
from .state import ProjectState, StateError, _now_iso

APR_KINDS = ("analysis", "scope", "delivery", "acceptance", "routine", "push", "preset",
             "kit_update")
# kinds that are time-boxed rather than content-invalidated (spec II.2 APR field
# list: "expires (routine/analysis)")
# `push` expires like the others, and for the sharpest reason of the three: a
# push token that outlives its session is a standing permission to publish.
# `preset` on the same ground as `push` and one step further: what it authorises
# is the installation of the roles a project may spawn, i.e. a change to the
# enforcement layer itself (BUG-0041). An unused one that lingers is a standing
# permission to rewrite that layer, so it carries a clock like the other three.
# `kit_update` is the same argument at its strongest: it authorises REPLACING that
# layer -- hooks, kernel, settings and constitution -- with another release
# (FR-0006), and an unused one lingering past the conversation is a standing
# permission to do that.
EXPIRING_KINDS = frozenset(("routine", "analysis", "push", "preset", "kit_update"))
# kinds that may authorise a specialist dispatch through the ROOT item's
# approval_ref ALONE, i.e. on nothing but the fact that the root presents them.
# analysis/routine deliberately excluded and NOT because they authorise nothing:
# they are read-only permissions bound to something OTHER than the root's content
# (II.2/II.3), so each has its own route in `dispatch` that checks that binding --
# the listed task for `analysis`, the role and the read-only scope for `routine`.
# Granting them the blanket route instead would authorise unlimited IMPLEMENTATION
# work under a still-DRAFT root, and because their manifests are not item-derived
# no content hash could catch an out-of-band edit of that root either.
ROOT_DISPATCH_KINDS = frozenset(("scope", "delivery"))

# WHAT A `routine` APPROVAL IS BOUND TO. Spec II.2: "`routine` (z. B. Auditor-Takt) ist gebunden
# an Rolle, Read-only-Scope, Trigger, Ablaufdatum und jederzeit widerrufbar"; II.10a: the approval
# "hasht Rolle, Read-only-Scope, Trigger, Takt und Ablaufdatum". `expires` is not in this tuple
# because `create_pending_request` puts it into the manifest itself for every EXPIRING_KIND -- it
# is the one field the caller must NOT be able to leave out or spell differently.
#
# REQUIRED AT CREATION, not merely read later, and that is the point of naming them here: a
# routine manifest that carries none of them is a standing permission bound to nothing, and the
# user would be asked to sign it. `dispatch` reads the same names back out of the MINTED request
# and fails closed on a missing one, so the two ends read one contract rather than two lists.
# The one of them a gate can act on -- the role a routine dispatch must be spawned as -- named
# once and then PART OF the contract below, so the key `dispatch` reads and the key
# `create_pending_request` demands cannot become two spellings of one field.
ROUTINE_ROLE_FIELD = "role"
ROUTINE_MANIFEST_FIELDS = (ROUTINE_ROLE_FIELD, "scope", "trigger", "cadence")
# The fifth thing II.10a hashes, and the one the CALLER does not write: `create_pending_request`
# puts it into the manifest itself for every EXPIRING_KIND, `proven_expiry` reads it back from
# there (the only tamper-evident copy), `mint` carries it into the APR as a display value, and the
# approval question renders it. Five readers of one key, spelled once.
EXPIRY_FIELD = "expires"
_CHANGE_LABEL = "Ändern"
_REJECT_LABEL = "Ablehnen"
# HOW MUCH OF A HASH A HUMAN IS SHOWN, in one place: `build_question` prints this many characters
# of the subject-manifest hash, and `_render_manifest_value` shortens a hashed VALUE to the same
# length so one question does not show two conventions. A digest is recognised by BEING one --
# hex, and at least as long as the shortest algorithm anything here uses (sha1) -- rather than by
# the field name carrying it, which would be a list that the next hashed field is missing from.
DIGEST_SHOWN = 12
_DIGEST = re.compile(r"\A[0-9a-f]{40,}\Z")

# THE TWO EXITS FROM A REFUSED MINT, in the language of the person who clicked. A branch picks the
# one its own situation allows; there is no third, and no branch may invent one (BUG-0039). Which
# one is NOT interchangeable: sending a user back to re-ask a question whose request is already
# gone is a loop, and that mismatch between a state and its advice is the defect TSK-0057/BUG-0036
# closed one report earlier. German because these strings are read by the user, like the approval
# question `build_question` writes a few functions down.
NEXT_ASK_AGAIN = ("Dein Assistent muss die Freigabe-Frage noch einmal stellen — unverändert, Wort "
                  "für Wort so, wie das Programm sie ausgibt.")
NEXT_START_OVER = ("Dein Assistent muss den Freigabe-Vorgang neu starten; diese Anfrage ist "
                   "verbraucht und kann nichts mehr freigeben.")


def approve_label(mint_code: str) -> str:
    """The ONE answer string that mints -- entropy-carrying by design."""
    return "Freigeben [%s]" % mint_code

# WHICH TRANSITION AN APPROVAL COMMITS, per (item_type, kind). Read forwards it is the status
# side-effect of a successful mint -- everything else only sets approval_ref (spec II.2/II.3).
# Read BACKWARDS it is the answer to "which transitions may only be walked when a user approved
# them", and `required_approval_kinds` reads it that way. One table, both directions: a pair added
# here arrives gated at `transition` with no second list to keep in step.
APPROVAL_TRANSITIONS = {
    ("PR", "scope"): ("DRAFT", "APPROVED"),
    ("RQ", "scope"): ("DRAFT", "APPROVED"),
    ("PR", "delivery"): ("APPROVED", "IN_DELIVERY"),
    ("RQ", "delivery"): ("APPROVED", "IN_DELIVERY"),
    ("PR", "acceptance"): ("DELIVERED", "ACCEPTED"),
    ("RQ", "acceptance"): ("DELIVERED", "ACCEPTED"),
    ("CR", "scope"): ("DRAFT", "APPROVED"),
    ("BUG", "scope"): ("TRIAGED", "APPROVED"),
    ("PROC", "scope"): ("DRAFT", "APPROVED"),
    ("EXP", "delivery"): ("DESIGNED", "APPROVED"),
}

# fields hashed into the subject manifest per kind for ITEM-bound approvals
# (spec II.2 subject_manifest lists)
#
# WHAT THIS COVERS AND WHAT IT DOES NOT. A scope approval reads as "the user signed this item's
# content", and the honest question is how much of that content the manifest actually carries.
# `backlog_types.HASHED_FIELDS[item_type]` is the kernel's own answer to "which fields of this
# type are approval-relevant", so the coverage of a manifest is the overlap between the two --
# a DERIVATION, not a count, and the count this comment first carried ("for two types it does
# not") was wrong. Measured 2026-07-31 over all TEN (item type, kind) pairs in
# `APPROVAL_TRANSITIONS`: exactly two of them cover their type's hashed fields in full -- PR/scope
# 6 of 6 and RQ/scope 5 of 5 -- and the other EIGHT cover one field or none:
#   BUG/scope 1 of 5 . CR/scope 1 of 4 . PROC/scope 0 of 2 (steps, roles) . EXP/delivery 0 of 3 .
#   PR|RQ delivery and acceptance 0 of 6|5, because those manifests name fields (`risks`,
#   `delivered_commit`, ...) that no type's contract declares at all.
# `SR` is not in that list because it is in no pair: nothing approves an SR, which is the
# neighbouring finding in `required_approval_kinds`.
# The consequence is exact: a change THROUGH THE KERNEL still invalidates (`HASHED_FIELDS` bumps
# the revision, and the revision IS in every manifest), while an out-of-band edit past the kernel
# leaves the hash matching -- the one thing the content hash exists to catch. Widening this tuple
# is not a fix that can be slipped in: every stored hash would change and every live approval
# would die, so it is a spec decision with a migration attached. Named here so nobody reads the
# hash as wider than it is.
_SCOPE_FIELDS = ("problem", "goal", "question", "motivation",
                 "acceptance_criteria", "invariants", "out_of_scope",
                 "design_refs")


class ApprovalError(StateError):
    """Approval-protocol violation -- message carries the remedy.

    `user_text` is the SAME refusal addressed to the person who clicked, and it exists because the
    message above is addressed to a role: it names spec sections, file paths and request ids, and
    pilot 3 (BUG-0039) is what a user gets out of that -- nothing. The branch that refuses writes
    it, so the sentence is as specific as the branch is; the alternative, one text chosen by
    whoever reports the error, is the blanket reason BUG-0036 cost a round.

    Optional in the signature and NOT optional where it matters:
    `tools/test_hooks_v2.py::test_every_approval_refusal_the_hook_can_surface_speaks_to_the_user`
    derives the reachable raise sites from the approval hook's own calls and fails on one without.
    """

    def __init__(self, message, user_text=None):
        super().__init__(message)
        self.user_text = user_text


def _pending_dir(state: ProjectState) -> str:
    return os.path.join(state.root, "approvals", "pending")


def _consumed_dir(state: ProjectState) -> str:
    return os.path.join(state.root, "approvals", "consumed")


def _revoked_dir(state: ProjectState) -> str:
    return os.path.join(state.root, "approvals", "revoked")


def _request_path(state: ProjectState, request_id: str, consumed: bool = False,
                  revoked: bool = False) -> str:
    if revoked:
        base = _revoked_dir(state)
    else:
        base = _consumed_dir(state) if consumed else _pending_dir(state)
    return os.path.join(base, request_id + ".yaml")


def push_subject_manifest(remote: str, branch: str, head: str) -> dict:
    """R1 (parity row 29, a MINIMUM-KEEP rule): what a push approval is bound to.

    "Push nur nach expliziter Userfreigabe" was prose only, so it died with every
    context window. It is now the same two-phase protocol as an APR, with the
    same mint code -- Amendment 2026-07-24 records why the option IDENTITY cannot
    carry it (spike S2b: a clicked option and typed text are indistinguishable in
    the payload), so the entropy lives in the option LABEL.

    Bound to remote + branch + HEAD, which makes the token single-use without any
    "used" flag to keep honest: approve HEAD abc123, push it, and the next commit
    moves HEAD so the same approval no longer matches. Re-running the identical
    push is a git no-op, so nothing is lost by allowing it. The alternative --
    a consumed marker -- would be one more piece of writable state deciding an
    enforcement question, which is the mistake the ledger gate spent four rounds
    unlearning.
    """
    return {
        "remote": str(remote or ""),
        "branch": str(branch or ""),
        "head": str(head or ""),
    }


def preset_subject_manifest(preset: str, roles, removes) -> dict:
    """What a preset change is bound to: the OUTCOME the user is asked to sign (BUG-0041).

    The user is not shown a preset NAME and asked to trust it -- `duo` and `team` say nothing to
    the person pilot 3 measured. The manifest carries the resulting specialist set and, separately,
    the roles this project has installed that the new preset drops, because a downgrade takes work
    capacity away and that is the half a name hides completely.

    BOUND TO THE OUTCOME AND NOT TO THE STEP: `kernel.presets.change_manifest` derives these same
    three values from the kit staging and the installed role manifest, and `set-preset` re-derives
    them and refuses unless the hash still matches. So an approval signed for one role set cannot
    install another -- not after a kit staging changed underneath it, and not for a preset the
    user was never shown.
    """
    return {
        "preset": str(preset or ""),
        "roles": list(roles or []),
        "removes": list(removes or []),
    }


# THE OTHER HALF OF THE KIND SPLIT, and the reason B2 was a wall: `item_derived_kinds` names the
# kinds a command line can open because it can carry an item id, and `cli` asked ONLY for those.
# `push` is in `APR_KINDS`, has its manifest builder above, and `gate_push_token` refuses
# every push without one -- but nothing could create the request, so no project could ever push.
# Measured 2026-08-02 before this: `approvals/pending/` never held a push request, and the gate's
# own remedy pointed at a command the parser did not have.
#
# A kind belongs here when its subject is a handful of facts a COMMAND LINE can put together --
# typed on it, or resolved from the project by `cli.LINE_MANIFEST_RESOLVERS` (the shape `head` has
# always had, and the one `preset`'s role lists need: a role typing them would be typing what the
# kit's own preset file decides). The CLI reads the flags off the builder's SIGNATURE (the pattern
# `cli.freeze_parameters` already uses for the freeze bodies), so a second line kind arrives on
# the command line with the right flags and no edit there.
def kit_update_subject_manifest(kit, from_version, from_content, to_version, to_content) -> dict:
    """What a kit update is bound to: the two RELEASES, each as the kit's own identity statement.

    THE VERSION STAMP ALONE WOULD NOT DO IT, and the case is not hypothetical: the session briefing
    has been able to report "the same version stamp over different content" since 2026-08-02 and
    nothing could act on that reading. `content:` is the hash `tools/bump_kit_version.py` writes
    over everything a scaffold reads or installs, so the pair (version, content) is what tells two
    trees apart that call themselves one release -- and it is what makes an approval survive
    exactly as long as the staging it was given for.

    BOTH ENDS, because "update A to B" and "update C to B" are different decisions: the FROM side is
    what the user is told the project is losing. `kernel.kitupdate.change_manifest` derives all five
    values from the two VERSION files and `update-kit` re-derives them before it acts, refusing
    unless the hash still matches (`tools/test_kitupdate.py::test_an_approval_for_one_release_pair_
    does_not_cover_another`).
    """
    return {
        "kit": str(kit or ""),
        "from_version": str(from_version or ""),
        "from_content": str(from_content or ""),
        "to_version": str(to_version or ""),
        "to_content": str(to_content or ""),
    }


LINE_MANIFEST_BUILDERS = {"push": push_subject_manifest, "preset": preset_subject_manifest,
                          "kit_update": kit_update_subject_manifest}

# How long an approval minted from a command-line manifest stays valid. Every kind in this map is
# in `EXPIRING_KINDS`, so `create_pending_request` demands a date -- and the caller must not be the
# one to choose how long, or the supervised party decides how long its own permission lasts.
# One hour, on the reason every kind here shares: each is ALREADY bound to content that moves -- a
# push token to HEAD (see `push_subject_manifest`), a preset approval to the role set it names, a
# kit update to the two release identities -- so this clock only bounds how long an UNUSED one
# lingers, and an unused authorisation that outlives the working session is a standing permission
# to publish, to reinstall the project's roles, or to replace its enforcement layer.
LINE_APPROVAL_VALIDITY = 3600.0


def line_manifest_kinds() -> tuple:
    """The APR kinds whose subject manifest a COMMAND LINE can build -- see LINE_MANIFEST_BUILDERS."""
    return tuple(sorted(LINE_MANIFEST_BUILDERS))


def item_subject_manifest(item: dict, kind: str) -> dict:
    """Deterministic manifest for an item-bound approval kind."""
    if kind == "scope":
        manifest = {k: item.get(k) for k in _SCOPE_FIELDS if k in item}
        manifest["item"] = item["id"]
        manifest["revision"] = item.get("revision")
        return manifest
    if kind == "acceptance":
        return {
            "item": item["id"],
            "revision": item.get("revision"),
            "delivered_commit": item.get("delivered_commit"),
            "evidence_refs": item.get("evidence_refs", []),
        }
    if kind == "delivery":
        return {
            "item": item["id"],
            "root_revision": item.get("revision"),
            "system_requirements": item.get("system_requirements", []),
            "architecture": item.get("architecture_refs", []),
            "tasks": item.get("planned_tasks", []),
            "risks": item.get("risks", []),
        }
    raise ApprovalError(
        "kind %r is not item-derived (analysis/routine/push take an explicit "
        "manifest -- for push, build it with `push_subject_manifest`). Remedy: "
        "pass `manifest=` to create_pending_request." % kind,
        user_text="Es wurde keine Freigabe erteilt: die gespeicherte Freigabe-Anfrage nennt eine "
                  "Freigabe-Art, zu der das Programm keinen Inhalt bilden kann. " + NEXT_START_OVER
    )


# -- which transitions a Freigabe GUARDS (spec II.2 Statusautomaten + Freigaben) ----------------

def required_approval_kinds(item_type: str, from_status: str, to_status: str) -> frozenset:
    """The approval kinds that COMMIT this transition -- i.e. the ones whose mint walks it.

    DERIVED BY INVERTING `APPROVAL_TRANSITIONS`, and that is the whole design. That map already
    answers "which approval kind commits which edge" -- `mint` walks the edge with it the moment
    the user approves -- so the same table read the other way round answers "which edge may only
    be walked when such an approval exists". A constant of the shape `{"APPROVED": "scope"}` would
    be a SECOND statement of the same fact, and every second statement in this kernel has fallen
    behind its original: a new (item type, kind) pair added above therefore arrives here gated,
    and a pair removed there stops gating, with nothing to remember.

    AN EDGE NO KIND MAPS TO IS NOT APPROVAL-BOUND, and that is the same derivation rather than a
    list of exemptions. Checked against spec II.2 rather than assumed, the answers are:
      * no edge of the TSK automaton -- no kind's manifest describes a task's progress; those
        edges are moved by the lease lifecycle and `submit_result`, and the one rule that does
        guard a TSK edge (FAILED -> READY only on an approved retry) lives in `state.transition`
        because its evidence is a caller argument, not an APR.
      * SR (PROPOSED -> ACCEPTED) -- an SR is a technical contract under a root, and no manifest
        in `item_subject_manifest` describes one. Reported, not bridged: if accepting an SR is to
        need a user approval, it needs a KIND with a manifest first, and that is a spec decision.
      * no edge INTO a terminal state except `ACCEPTED` -- discarding work is not approving it,
        and gating a terminal would make an item unabandonable. The cost of that is real and is
        named where a role reads it (`scripts/harness.py`): a root item can still be dropped.
      * nothing on DEC or INV -- they are `_NON_AUTOMATON_INITIAL_STATUS`, so `assert_transition`
        refuses every transition on them before this is ever asked.

    WHAT "COMMITS" IS NOT, and the difference is measurable: the map pairs a kind with an edge, it
    does not promise that the kind's manifest describes the item's content. For `PROC` and `SR` it
    does not (see `_SCOPE_FIELDS`), so a scope approval there binds to `{item, revision}` -- the
    gate still holds, the CONTENT hash behind it is thinner than the name suggests.
    """
    return frozenset(kind for (typ, kind), edge in APPROVAL_TRANSITIONS.items()
                     if typ == item_type and edge == (from_status, to_status))


# The item field the kernel stamps with `approved_content_hash` at mint time. Spec II.2 lists it
# among a PROC's fields; nothing there forbids another type carrying it, and the kernel writes it
# wherever it is computable (see `approved_content_hash`) rather than for one type by name.
APPROVED_CONTENT_HASH_FIELD = "approved_hash"


def approved_statuses(item_type: str) -> frozenset:
    """The statuses an item stands in BECAUSE a user approved it, and has not left again.

    DERIVED FROM `APPROVAL_TRANSITIONS` AND THE TYPE'S OWN CHAIN, for the reason
    `required_approval_kinds` gives one function up: a hand-written `("APPROVED", "ACTIVE")` beside
    the automaton is a second statement of what the automaton already says, and every second
    statement in this kernel has fallen behind its original. Read this way the answer is one
    sentence of graph: an approval walks the item onto some status of its chain, and every LATER
    chain status is still that same approved run of the item -- `PROC` DRAFT -> APPROVED -> ACTIVE
    is exactly the "approved, then in use" pair the office gate needs, with nothing enumerated.

    A TERMINAL IS SUBTRACTED ONLY WHEN NO APPROVAL PUT IT THERE, and getting that condition wrong
    made this function contradict its own first sentence for five types out of six. Subtracting
    every terminal is right for `RETIRED` (a procedure the project stopped running, and a gate that
    let a work order execute it would read a tombstone as a permission) and wrong for `ACCEPTED`,
    which is exactly the status an `acceptance` approval commits -- so a blanket subtraction
    answered "a PR is not in an approved status" about the one status a user signed for. `PROC` is
    the only type whose terminals all lie OFF its chain, which is why the mistake was latent: its
    consumer today is the office spawn gate, and there the two readings agree.

    A type nothing approves, or one with no automaton at all (`DEC`, `INV`), answers with the empty
    set -- there is no status it holds because of an approval.
    """
    auto = AUTOMATA.get(item_type)
    if auto is None:
        return frozenset()
    reached = set()
    approved_targets = set()
    for (typ, _kind), (_source, target) in APPROVAL_TRANSITIONS.items():
        if typ != item_type:
            continue
        approved_targets.add(target)
        if target in auto.chain:
            reached.update(auto.chain[auto.chain.index(target):])
    return frozenset(reached) - (auto.terminals - approved_targets)


def approved_content_hash(item_type: str, item: dict):
    """The canonical hash over the fields whose change invalidates this item's approval, or None.

    THE SUBJECT IS `HASHED_FIELDS`, which is the kernel's own answer to "which fields of this type
    are approval-relevant". So this is not a second opinion about what an approval covers -- it is
    the same list, hashed, and a type that declares none (`INV`, `DEC`, `FR`, `TSK`, `EVD`) has
    nothing to record and gets None.

    WHY IT EXISTS BESIDE `subject_manifest_hash(item_subject_manifest(...))`, which looks like the
    same thing and is not: the scope manifest carries `_SCOPE_FIELDS`, and the comment there
    measures the overlap -- for `PROC` it is 0 of 2, so an approved PROC's `steps` and `roles` sit
    outside every hash the approval record itself keeps. Widening `_SCOPE_FIELDS` would change
    every stored hash and kill every live approval, which is the migration that comment refuses to
    slip in. A SEPARATE field changes no stored hash at all: the approval record stays exactly as
    it was, and the item gains a stamp of what was approved.

    WHAT THAT BUYS, stated no wider than it is: an out-of-band edit -- one that goes past the
    kernel, so no revision is bumped and no approval is invalidated -- leaves the stamp behind
    disagreeing with the content. `gate_proc_approved` refuses a spawn on that disagreement and
    `report.validate_state` reports it. It is NOT read by `assert_apr_in_force`, so such an edit
    does not by itself stop a dispatch or a transition; that would be a widening of the
    authorisation path and is named here rather than done quietly.

    AND WHAT IT DOES NOT BUY, because the sentence above is exactly the shape that gets read as
    more: this is an UNKEYED hash of public content by a public function, so anyone who can write
    the item file can write the matching stamp with it. Measured: edit an approved PROC's steps,
    recompute, write both -- spawn rc 0 and `validate` rc 0, no finding anywhere. It detects an
    edit that did not bother, not an edit that did. The same limit `proven_expiry` records for the
    approval manifest, and it closes the same way: by keeping the state directory kernel-only for
    tool writes (gate layer 3), never by arithmetic.
    """
    fields = HASHED_FIELDS.get(item_type)
    if not fields:
        return None
    return subject_manifest_hash({name: item.get(name) for name in fields})


def assert_apr_in_force(state: ProjectState, apr: dict, item: dict) -> dict:
    """Raise unless this approval authorises anything about this item RIGHT NOW; return its request.

    ONE definition of "in force", because two readers need it and they used to be one reader with
    a private copy: the dispatch gate asking whether a root's current approval still authorises a
    spawn (`dispatch._assert_root_approval_locked`), and the status automaton asking whether an
    approval of the required kind exists for an edge (`assert_transition_approved`). The questions
    differ -- which APR is looked at, and whether the kind is fixed -- but the validity test is the
    same one, and a copy of it would drift exactly as `report._parents_of` did.

    The five ways an approval that EXISTS still grants nothing, in the order a reader wants them:
    it was revoked; its provenance cannot be proven (`consumed_request` -- a hand-written APR is
    just a file); it belongs to another item; its clock ran out; the item's hashed content moved
    since it was minted. The messages stay fact-first and remedy-second, and the callers add their
    own consequence ("dispatch blocked", "transition refused") around them -- a message that names
    one caller's consequence inside a shared check is how the last such helper became two.
    """
    apr_ref = apr.get("id")
    if apr.get("revoked"):
        raise ApprovalError(
            "approval %s is revoked. Remedy: obtain a fresh approval." % apr_ref)
    # provenance first: an approval that cannot show its minted request is not a user approval at
    # all, whatever else it says (spec II.12)
    request = consumed_request(state, apr)
    if str(apr.get("item") or "") != item["id"]:
        raise ApprovalError(
            "approval %s belongs to %r, not to %s. Remedy: obtain an approval for this item."
            % (apr_ref, apr.get("item"), item["id"]))
    expires = proven_expiry(request)
    if expires is not None and expires < time.time():
        raise ApprovalError(
            "approval %s expired (spec II.10a: an expired approval blocks). Remedy: renew the "
            "approval." % apr_ref)
    kind = apr.get("kind")
    if kind in ("scope", "acceptance", "delivery"):
        current = subject_manifest_hash(item_subject_manifest(item, kind))
        if current != apr.get("subject_manifest_hash"):
            raise ApprovalError(
                "content hash of %s no longer matches approval %s -- an out-of-band edit "
                "invalidated the approval (spec II.4 gate 4). Remedy: re-approve the current "
                "revision, or `git restore %s` to return to the approved content."
                % (item["id"], apr_ref,
                   os.path.relpath(state.active_path(item["id"]), state.root)))
    return request


def assert_transition_approved(state: ProjectState, item: dict, item_type: str,
                               from_status: str, to_status: str):
    """Refuse a transition the user has to authorise and did not. Returns the APR, or None.

    THE HOLE THIS CLOSES, measured 2026-07-29 in a scaffolded project: `python
    scripts/harness.py transition PR-0002 APPROVED` walked a root item out of its DRAFT past all
    eight PreToolUse gates, with a specialist's `agent_type` in the payload as readily as without
    one -- while `gate_git` refuses a merge for an item still in its initial status ON THE GROUND
    THAT NOTHING APPROVED THE WORK. A status the supervised party can set itself proves nothing,
    so the gate that reads it was resting on a value its own subject could write.

    Called from `state._transition_locked`, i.e. from EVERY transition including the one `mint`
    performs -- there is deliberately no parameter that turns it off. Spec II.4 is explicit that
    bootstrap "ist kein Config-Flag (der Lead könnte sein eigenes Gate umgehen)", and a `force=` a
    caller may pass is that flag with a different name. The mint passes this check the ordinary
    way, because it writes the APR and consumes its request BEFORE it walks the edge.

    THE SEARCH IS OVER THE APPROVAL STORE, not over `item.approval_ref`, and the two are different
    questions. `approval_ref` holds the LAST approval minted for an item -- an item legitimately
    collects several of different kinds, and the newest one overwrites the field -- so reading it
    would answer "was the most recent approval of this kind" instead of "is an approval of this
    kind in force", which is what spec II.2 binds to (kind + item + revision + content hash).

    WHAT THAT LEAVES OPEN, named because the same property is what makes it possible: the SEQUENCE
    spec II.3 builds is not enforced. An approval binds to (kind, item, revision, content hash)
    and to nothing about WHEN it was given, so all three of a root's approvals can be minted while
    the item is still DRAFT -- `delivery` and `acceptance` have no status effect there (their
    source states are APPROVED and DELIVERED), `scope` then walks DRAFT -> APPROVED, and
    IN_DELIVERY / DELIVERED / ACCEPTED follow with no further question. Measured 2026-07-31, each
    step rc 0, and since `request-approval` shipped the whole sequence is reachable FROM A ROLE'S
    COMMAND LINE -- three request/answer cycles in DRAFT, then three transitions. Before that
    command it needed a library call, which is worth saying plainly: closing the entry hole made
    this one walkable.
    It is not a forgery: a user really answered three questions. It is that the questions were
    answerable at a moment when their subject could not have been meaningful -- `delivery`'s
    manifest names `system_requirements`, `architecture_refs`, `planned_tasks`, `risks` and
    `acceptance`'s names `delivered_commit`, `evidence_refs`, and NO command on this surface
    produces any of them, so what the user signs in DRAFT is byte-identical to what they would
    sign after delivery.

    THE OBVIOUS CLOSURE -- "an approval authorises an edge only if it was minted while the item
    stood in that edge's SOURCE status" -- is derivable and NOT taken here, on ONE ground: the
    minting status would have to live inside the HASHED manifest to be tamper-evident, and adding
    a field to a manifest changes every stored hash and kills every live approval, so it is a spec
    decision with a migration attached rather than an implementation detail.
    A second ground was offered and does not hold, so it is retracted rather than left standing:
    "it would forbid a legitimate re-approval". It would not. The rule binds only
    `assert_transition_approved`, which runs when an edge is WALKED; re-approving an already
    walked edge authorises nothing either way, and after an invalidation `INVALIDATION_TARGET`
    puts the item back into the source status anyway. What the rule would really forbid is
    pre-minting -- which is the thing to forbid.
    """
    kinds = required_approval_kinds(item_type, from_status, to_status)
    if not kinds:
        return None
    rejected = []
    approvals_dir = os.path.join(state.root, "approvals")
    names = sorted(os.listdir(approvals_dir)) if os.path.isdir(approvals_dir) else []
    for name in names:
        if not (name.startswith("APR-") and name.endswith(".yaml")):
            continue
        try:
            apr = state._read_yaml(os.path.join(approvals_dir, name))
        except Exception:
            continue        # an unreadable approval authorises nothing (fail-closed)
        if not isinstance(apr, dict) or apr.get("kind") not in kinds:
            continue
        if str(apr.get("item") or "") != item["id"]:
            continue
        try:
            assert_apr_in_force(state, apr, item)
        except ApprovalError as exc:
            # named rather than swallowed: a revoked or content-invalidated approval is the case a
            # role hits most often, and "no approval at all" would send it looking for the wrong
            # thing
            rejected.append("%s (%s): %s" % (apr.get("id") or name[:-5], apr.get("kind"), exc))
            continue
        return apr
    # THE REMEDY NAMES THE COMMAND AND THE KIND, and the second half is not decoration: the KIND
    # is derived per edge, and a role that guesses it guesses wrong on the edges where the name of
    # the status does not match the name of the kind. `EXP DESIGNED -> APPROVED` is committed by a
    # `delivery` approval, and "run the approval flow" sent a role to `request-approval scope EXP-…`
    # -- a request that opens, mints, and still does not walk the edge. Spelled from `kinds`, so an
    # (item type, kind) pair added to APPROVAL_TRANSITIONS arrives here correctly named.
    wanted = sorted(kinds)
    raise ApprovalError(
        "%s %s -> %s is the transition a %s approval commits, and none is in force for %s at "
        "revision %s -- refused (fail-closed). A status the supervised party can set itself is a "
        "status no gate may read as approval.%s Remedy: run `python scripts/harness.py "
        "request-approval %s %s`%s and relay the printed question to the user VERBATIM -- their "
        "answer mints the approval AND walks this transition, so there is nothing left to "
        "transition by hand afterwards."
        % (item["id"], from_status, to_status, "/".join(wanted), item["id"],
           item.get("revision"),
           (" The approvals that name this item do not count: %s." % "; ".join(rejected))
           if rejected else "",
           wanted[0], item["id"],
           "" if len(wanted) == 1
           else " (or %s in place of %s -- either kind commits this edge)"
                % ("/".join(wanted[1:]), wanted[0]))
    )


def item_derived_kinds() -> tuple:
    """The APR kinds whose subject manifest can be built from an ITEM ALONE.

    Asked of `item_subject_manifest` rather than restated: that function is what decides it, by
    raising for every kind it cannot derive. `cli` needs exactly this set (a command line can
    carry an item id; it cannot carry an analysis question, a read-only scope and a cadence), and
    the alternative spelling -- `APR_KINDS - EXPIRING_KINDS` -- is a THIRD statement of the same
    split that happens to agree today. One probe item, no list.
    """
    probe = {"id": "PR-0001", "revision": 1}
    derived = []
    for kind in APR_KINDS:
        try:
            item_subject_manifest(probe, kind)
        except Exception:
            # EVERY exception, not just ApprovalError, and the difference is the whole CLI. This
            # runs inside `build_parser()`, so anything escaping it kills every command including
            # `doctor` -- measured with a manifest that reads a field the probe lacks: `KeyError:
            # 'contract'` out of `build_parser()` and out of `main([..., "doctor"])`. A diagnosis
            # command that dies on the thing it diagnoses is the failure `cli.py`'s own docstring
            # is written against. A kind that cannot be built from an id alone is simply not
            # item-derived, which is what this function was asked.
            continue
        derived.append(kind)
    return tuple(derived)


def create_pending_request(
    state: ProjectState,
    kind: str,
    item_id: str = None,
    manifest: dict = None,
    ttl_seconds: float = 24 * 3600.0,
    approval_expires: float = None,
) -> dict:
    """Phase 1 of the protocol: persist the immutable pending request.

    `ttl_seconds` bounds how long the QUESTION stays answerable; `approval_expires`
    (epoch seconds, routine/analysis only per spec II.10a) bounds how long the
    resulting APPROVAL stays valid. Two different clocks -- conflating them would
    either expire live approvals or leave routine approvals standing forever.
    """
    if kind not in APR_KINDS:
        raise ApprovalError(
            "unknown APR kind %r. Remedy: use one of %s." % (kind, "/".join(APR_KINDS))
        )
    if kind in EXPIRING_KINDS and approval_expires is None:
        # spec II.2: a routine approval "ist gebunden an Rolle, Read-only-Scope,
        # Trigger, Ablaufdatum und jederzeit widerrufbar", and II.10a: an expired
        # routine approval blocks the audit dispatch. With an OPTIONAL expiry the
        # natural call mints an approval that never expires -- a standing spawn
        # permission, i.e. the one thing the revocable time-boxed design exists
        # to prevent. So it is required.
        raise ApprovalError(
            "kind %r must carry an expiry (spec II.2 Ablaufdatum / II.10a: an "
            "expired routine approval blocks the dispatch). Remedy: pass "
            "approval_expires=<epoch seconds>." % kind
        )
    if approval_expires is not None and kind not in EXPIRING_KINDS:
        raise ApprovalError(
            "only %s approvals carry an expiry (spec II.2); kind %r does not. "
            "Remedy: drop approval_expires -- a scope or delivery approval is "
            "invalidated by content change, not by the clock."
            % ("/".join(sorted(EXPIRING_KINDS)), kind)
        )
    with state.lock:
        revision = None
        if item_id is not None:
            item = state.read_item(item_id)
            revision = item.get("revision")
            if manifest is None:
                manifest = item_subject_manifest(item, kind)
        if manifest is None:
            raise ApprovalError(
                "kind %r needs an explicit manifest (analysis: question/scope/"
                "expected result/listed tasks; routine: %s plus the expiry; push: "
                "remote/branch/head via `push_subject_manifest`). Remedy: pass "
                "`manifest=`." % (kind, "/".join(ROUTINE_MANIFEST_FIELDS))
            )
        if kind == "routine":
            # see ROUTINE_MANIFEST_FIELDS: a routine bound to nothing is a standing spawn
            # permission, which is the one thing the revocable time-boxed design exists to
            # prevent -- so it is refused before the user is ever asked to sign it
            missing = [field for field in ROUTINE_MANIFEST_FIELDS if not manifest.get(field)]
            if missing:
                raise ApprovalError(
                    "a routine approval must name %s (spec II.2: bound to role, read-only "
                    "scope, trigger and cadence; II.10a hashes all four) -- %s missing. "
                    "Remedy: pass them in `manifest=`; an unbound routine would be a standing "
                    "spawn permission."
                    % ("/".join(ROUTINE_MANIFEST_FIELDS), ", ".join(missing))
                )
        if approval_expires is not None:
            # spec II.10a: the routine approval HASHES role, read-only scope,
            # trigger, cadence AND the expiry date -- so the expiry has to sit
            # inside the hashed manifest, not merely beside it. Otherwise the
            # date could be moved without invalidating the approval.
            manifest = dict(manifest, **{EXPIRY_FIELD: float(approval_expires)})
        request = {
            "request_id": uuid.uuid4().hex,
            "kind": kind,
            "item": item_id,
            "revision": revision,
            "subject_manifest": manifest,
            "subject_manifest_hash": subject_manifest_hash(manifest),
            "created": _now_iso(),
            "expires_at_epoch": time.time() + ttl_seconds,
            # entropy that lives ONLY in the approval option label (S2b)
            "mint_code": uuid.uuid4().hex[:6],
        }
        state._write_yaml_atomic(_request_path(state, request["request_id"]), request)
        return request


def _render_manifest_value(field: str, value) -> str:
    """One manifest value as the user reads it in the approval question.

    A list is joined rather than repr'd (`['a', 'b']` in a sentence a human has to judge is
    noise), and a missing value is shown as missing rather than as `None`.

    The EXPIRY is rendered as a date, in UTC. As an epoch float it is the one field a human
    cannot judge at all, and it is the field that decides how long a standing spawn permission
    lasts. UTC rather than local time because this string is compared CHARACTER FOR CHARACTER by
    the PreToolUse gate, in a different process: a machine whose timezone changed between the
    request and the answer would otherwise render a different question and the approval could not
    be completed.

    A DIGEST IS SHORTENED, for the expiry's reason and to the same length the sentence around it
    already uses for one: `build_question` prints the subject-manifest hash as twelve characters
    and an ellipsis, so a hashed VALUE reading out in full made the question unreadable exactly
    where a non-technical user has to judge it -- measured on the `kit_update` manifest, whose two
    content hashes are 128 of its ~180 characters. It is a property of the value, not a list of
    fields that carry one, and it is deterministic, which is all the PreToolUse comparison needs.
    The full value stays in the pending request the question names.
    """
    if field == EXPIRY_FIELD:
        try:
            return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(float(value)))
        except (TypeError, ValueError, OSError, OverflowError):
            return "unreadable (%r)" % (value,)
    if isinstance(value, (list, tuple)):
        return " / ".join(str(entry) for entry in value) or "-"
    if value is None:
        return "-"
    return "%s…" % str(value)[:DIGEST_SHOWN] if _DIGEST.match(str(value)) else str(value)


def _push_target_form(manifest: dict) -> str:
    """A push approval as the human reads it: WHAT gets published, and where.

    The generic target would read "push" and the human would be asked to authorise publishing
    without being told what. The manifest is already in the request and is hash-covered, so naming
    it here is deterministic (the PreToolUse gate compares this text character for character) and it
    is the whole point of the rule: "explizite Userfreigabe" means the user knew what they released.
    """
    return "push -> %s/%s @ %s" % (manifest.get("remote", "?"), manifest.get("branch", "?"),
                                   str(manifest.get("head", "?"))[:8])


def _preset_target_form(manifest: dict) -> str:
    """A preset change as the person deciding it reads it: the team AFTERWARDS, and what goes.

    THE GENERIC FORM WAS LITERALLY TRUE AND STILL MISREAD (FR-0027). It rendered the manifest's own
    keys -- `[preset: duo, removes: -, roles: <six names>]` -- and on the upgrade solo->duo most of
    those names are already installed, so a non-technical user reads a list of arrivals and a dash.
    Named as the team the project HAS afterwards, the same list is what the approval actually
    guarantees, and "entfernt" is the half a preset NAME hides completely.

    WHAT IT DELIBERATELY DOES NOT SAY IS WHICH ROLES ARE NEW (DEC-0048), and that is not a wording
    choice. The added set is the target minus what is installed, and WHICH OF THE TARGET ROLES ARE
    ALREADY INSTALLED is the one thing the hashed manifest does not carry. The removed ones it does:
    `removes` is derived from the installation too (`kernel.presets._plan`), so the hash moves with
    the installed state -- just not with the part a delta would be computed from.

    Measured against the shipped dev-team presets: `duo` requested from a solo installation and from
    one that has all the target roles but two produces the SAME subject_manifest_hash while the
    added set differs, and `set-preset` accepts that one approval in either state
    (`test_the_added_roles_are_not_what_a_preset_approval_binds` measures both halves -- the
    manifest, and a real minted approval that still applies after the installation moved). A delta
    printed here would be the one sentence in this question the user signs and the hash does not
    cover.
    """
    return ("die Rollen-Aufstellung '%s' -- danach im Team: %s; entfernt: %s"
            % (str(manifest.get("preset") or "?"),
               ", ".join(str(role) for role in (manifest.get("roles") or [])) or "keine",
               ", ".join(str(role) for role in (manifest.get("removes") or [])) or "keine"))


# WHICH KINDS GET A FORM BUILT FOR READING, keyed by kind because that is what such a form belongs
# to: each of these manifests is a different subject, and the readable shape of one says nothing
# about another. The generic branch in `build_question` renders the manifest's own keys and stays
# the honest default for every kind with no entry here -- so an entry may only ever shorten the
# distance between what the hash covers and what the user reads, never add to it.
# `test_every_target_form_names_a_live_apr_kind` keeps an entry from outliving its kind.
TARGET_FORMS = {"push": _push_target_form, "preset": _preset_target_form}


def build_question(request: dict) -> dict:
    """The COMPLETE approval question, deterministic from the request alone.

    The model must relay this verbatim; the PreToolUse hook enforces string
    equality of question text, header AND all options for marked questions.
    """
    target = request["item"] if request["item"] else request["kind"]
    form = None if request["item"] else TARGET_FORMS.get(request["kind"])
    if form is not None:
        target = form(request.get("subject_manifest") or {})
    elif request["kind"] == "routine" or request["item"] is None:
        # WHAT THE HASH COVERS IS WHAT THE USER IS SHOWN, and the condition is that property rather
        # than the kinds it happens to hold for today. A request whose subject is a MANIFEST -- a
        # routine permission hanging from an item it is not about, or any kind with no item at all
        # -- renders that manifest, because the generic line would otherwise ask the user to sign a
        # bare kind name. This used to name `routine` alone, so every future item-less kind
        # inherited the bare line; `preset` is the one that would have asked a non-technical user
        # to approve the word "team" (BUG-0041). A kind with an entry in `TARGET_FORMS` never
        # reaches here, which is why this branch may widen without changing those questions.
        # A routine approval is a STANDING, recurring spawn permission, and
        # what the dispatch route binds it to is the manifest -- the role first of all. Asked as
        # "Freigabe erbeten: routine für PR-0001" the user was signing a role they were never
        # shown, for a period they were never shown either.
        # EVERY KEY OF THE HASHED MANIFEST is rendered, sorted, rather than the four of
        # `ROUTINE_MANIFEST_FIELDS`: those are what a CALLER must provide, while the manifest also
        # carries the expiry the kernel adds -- and for a time-boxed permission that is the field
        # the user most needs to judge. Reading the manifest itself makes "what the hash covers"
        # literally what is shown, and a key added on either side appears with no second edit.
        # Deterministic from the request alone, which the PreToolUse gate needs (it rebuilds this
        # text and compares it character for character), and it carries no mint code -- that lives
        # only in the option label.
        manifest = request.get("subject_manifest") or {}
        rendered = "[%s]" % ", ".join(
            "%s: %s" % (field, _render_manifest_value(field, manifest[field]))
            for field in sorted(manifest))
        # The kind is already the first half of the sentence this goes into, so an item-less
        # request shows the manifest ALONE -- naming the kind again in front of it says the word
        # twice and reads like a machine to the person who has to judge it. With an item, the
        # item stays in front of the manifest: that is what a routine approval hangs from.
        target = ("%s %s" % (target, rendered)) if request["item"] else rendered
    question = (
        "Freigabe erbeten: %s für %s (Revision %s, subject_manifest sha256 %s…). "
        "Details: approvals/pending/%s.yaml [APR-REQ:%s]"
        % (
            request["kind"],
            target,
            request["revision"] if request["revision"] is not None else "-",
            request["subject_manifest_hash"][:DIGEST_SHOWN],
            request["request_id"],
            request["request_id"],
        )
    )
    return {
        "question": question,
        "header": "Freigabe",
        "multiSelect": False,
        "options": [
            {
                "label": approve_label(request["mint_code"]),
                "description": "Erteilt die %s-Freigabe für %s in exakt dieser Revision "
                "(nur diese Option prägt die Freigabe)." % (request["kind"], target),
            },
            {
                "label": _CHANGE_LABEL,
                "description": "Keine Freigabe -- Änderungswünsche folgen im Chat.",
            },
            {
                "label": _REJECT_LABEL,
                "description": "Keine Freigabe -- der Vorgang wird verworfen.",
            },
        ],
    }


APPROVAL_HOOK = "gate_approval.py"


def _is_same_file(left, right) -> bool:
    if not left or not right:
        return False
    try:
        return (os.path.normcase(os.path.realpath(left))
                == os.path.normcase(os.path.realpath(right)))
    except OSError:
        return False


def _assert_minting_caller() -> None:
    """The mint must come from the approval hook, RUN AS the approval hook.

    Three conditions, each closing a measured accidental path (phase-2 review
    2026-07-25):
    1. a `_kernel` bridge module is loaded, and the hook path we accept is
       derived from ITS `__file__`;
    2. the immediate caller's file IS that hook -- realpath+normcase, so a
       crafted `compile(src, "<real hook path>")` filename does not suffice;
    3. `__main__` is that same file, so importing the hook as a module and
       calling its handler, or `runpy.run_path`, does not either.

    WHAT THIS IS WORTH, measured rather than hoped: no ACCIDENTAL path mints. A
    deliberate one does, and cheaply -- every input above is in-process state the
    caller may rewrite. Assigning `sys.modules["__main__"].__file__`, or
    registering a synthetic `_kernel` module whose `__file__` points at a path
    that need not even exist, satisfies all three; so does a two-file directory
    containing any `gate_approval.py` next to an EMPTY `_kernel.py`; and the hook
    is meant to be run with a payload on stdin, so
    `python <hooks>/gate_approval.py < forged.json` mints outright, with the
    forged `answers` + `questions` echo assembled from the readable pending
    request. The cheapest of these never runs the hook, so it does not even leave
    the hook's audit note.

    So user condition (i) ("only the PostToolUse hook may call mint") is NOT
    established by library code, and cannot be: this is in-process state
    checking in-process state. It needs a guard that stops an agent from invoking
    the hooks, or python against the kernel, at all -- a Bash/PowerShell-level
    check, since `guard_harness_selfmod` gates only Edit|Write|MultiEdit. Until
    that exists, `python scripts/harness.py doctor` must report `approval_provenance: unverified`
    and the mode stays `audited`.

    Deliberately the LAST check in `mint`: every content refusal (wrong label,
    expired request, out-of-band edit, replay) is reported on its own terms
    first, so a caller-provenance failure never masks the real reason. No APR is
    written before it either way.
    """
    bridge = getattr(sys.modules.get("_kernel"), "__file__", None)
    if not bridge:
        raise ApprovalError(
            "an approval can only be minted from the %s hook, and this process "
            "has no hook bridge loaded at all -- refused. Remedy: approvals "
            "happen through the AskUserQuestion flow; nothing else creates an "
            "APR." % APPROVAL_HOOK,
            user_text="Es wurde keine Freigabe erteilt: der Versuch kam nicht aus dem "
                      "Freigabe-Dialog, und nur von dort zählt ein Ja. " + NEXT_START_OVER
        )
    expected = os.path.join(os.path.dirname(bridge), APPROVAL_HOOK)
    frames = inspect.stack()
    # [0] this function, [1] mint, [2] whoever called mint
    caller = frames[2].filename if len(frames) > 2 else ""
    entry = getattr(sys.modules.get("__main__"), "__file__", None)
    if not _is_same_file(caller, expected) or not _is_same_file(entry, expected):
        raise ApprovalError(
            "only %s may mint an approval, run as itself -- this call came from "
            "%s (entry point %s) and was refused. A mint is a USER decision; any "
            "other caller would be manufacturing one. Remedy: approvals happen "
            "through the AskUserQuestion flow."
            % (expected, caller or "<unknown>", entry or "<none>"),
            user_text="Es wurde keine Freigabe erteilt: die Freigabe wurde von einer anderen "
                      "Stelle als dem Freigabe-Dialog angefordert. " + NEXT_START_OVER
        )


def _stored_approvals(state: ProjectState):
    """Every readable APR record in the store, in name order -- the ONE scan of it.

    Three readers need it (the replay guard in `mint`, `_gone_request_user_text` telling a user her
    yes is already recorded, and `live_line_approval`), and a second copy of a store scan is how
    `report._parents_of` became two. An unreadable file is skipped: it proves nothing either way,
    and every caller here is asking "is there one that grants this", never "is the store sound".
    """
    approvals_dir = os.path.join(state.root, "approvals")
    if not os.path.isdir(approvals_dir):
        return
    for name in sorted(os.listdir(approvals_dir)):
        if not (name.startswith("APR-") and name.endswith(".yaml")):
            continue
        try:
            record = state._read_yaml(os.path.join(approvals_dir, name))
        except Exception:
            continue        # an unreadable approval proves nothing either way (fail-closed)
        if isinstance(record, dict):
            yield record


def _approval_of_request(state: ProjectState, request_id: str):
    """The APR minted from this request, or None."""
    for existing in _stored_approvals(state):
        if existing.get("request_id") == request_id:
            return existing
    return None


def live_line_approval(state: ProjectState, kind: str, manifest: dict):
    """A minted, unrevoked, unexpired approval of `kind` whose REQUEST carries exactly `manifest`.

    The one definition of "this line-manifest approval is in force", because there were two: the
    push gate carried this scan and `set-preset` would have been the second copy of it, down to the
    detail that decides whether a lapsed permission still works -- reading the expiry off the
    HASH-COVERED side (`proven_expiry`) rather than off the APR file. `gate_push_token` now asks
    this function.

    The APR file carries only the hash; coverage is read from the consumed REQUEST, which is where
    the manifest lives and which `revoke` MOVES out of the way (`consumed_request`). So a
    hand-written APR proves nothing, and a revoked one stops matching even though its file still
    exists. The expiry is dropped from the STORED manifest before hashing because
    `create_pending_request` puts it there and no caller can know the minute it was minted;
    everything else must match key for key.
    """
    wanted_hash = subject_manifest_hash(dict(manifest))
    for apr in _stored_approvals(state):
        if apr.get("kind") != kind or apr.get("revoked"):
            continue
        try:
            request = consumed_request(state, apr)
            expires = proven_expiry(request)
        except ApprovalError:
            continue        # unprovable provenance or an unreadable expiry grants nothing
        stored = dict(request.get("subject_manifest") or {})
        stored.pop(EXPIRY_FIELD, None)
        if subject_manifest_hash(stored) != wanted_hash:
            continue
        if expires is not None and expires <= time.time():
            continue
        return apr
    return None


def _gone_request_user_text(state: ProjectState, request_id: str) -> str:
    """What to tell the USER about a request that is no longer pending -- read off the store.

    THREE OUTCOMES, TOLD APART BY WHERE THE REQUEST WENT: `mint` moves it to
    `approvals/consumed/` and `revoke` to `approvals/revoked/`, so its location is the answer and
    nothing has to be inferred from the absence alone. Measured while building BUG-0039's fix: with
    one blanket sentence here, a second click on an already-minted question told the user her
    approval had not happened and sent her to start over -- an alarm as wrong as the silence the
    fix is about, in the other direction
    (`test_a_second_click_on_an_already_minted_question_does_not_alarm_the_user`).
    """
    if os.path.exists(_request_path(state, request_id, consumed=True)):
        apr = _approval_of_request(state, request_id)
        return ("Deine Freigabe zu dieser Frage ist bereits erteilt%s — es fehlt nichts, und du "
                "musst nichts wiederholen."
                % (" (%s)" % apr.get("id") if isinstance(apr, dict) and apr.get("id") else ""))
    if os.path.exists(_request_path(state, request_id, revoked=True)):
        return ("Es wurde keine Freigabe erteilt: die Freigabe zu dieser Frage wurde "
                "zurückgezogen. " + NEXT_START_OVER)
    return ("Es wurde keine Freigabe erteilt: zu dieser Frage ist keine Freigabe-Anfrage mehr "
            "offen — sie ist abgelaufen oder wurde nie angelegt. " + NEXT_START_OVER)


def mint(state: ProjectState, request_id: str, answer: str) -> dict:
    """Phase 3: create the APR -- only for the verbatim approval label.

    `answer` is the raw string from `toolUseResult.answers[<question>]`. It
    mints ONLY if it equals `approve_label(request["mint_code"])` exactly.
    The platform gives no structural option identity (spike S2b), so the
    per-request mint code carries the proof instead: any other text --
    "Ändern", "Ablehnen", "ok", a plain "Freigeben" typed into "Other" --
    never mints.
    """
    with state.lock:
        path = _request_path(state, request_id)
        try:
            request = state._read_yaml(path)
        except FileNotFoundError:
            raise ApprovalError(
                "no pending approval request %s (consumed, expired-and-cleaned, "
                "or never created). Remedy: run the kernel approval flow again "
                "-- an invented request ID never mints. (A hand-WRITTEN pending "
                "file with a self-chosen mint_code would mint; keeping the "
                "pending-request area kernel-only is the write-scope gate's job, "
                "and the state validator flags hand edits.)" % request_id,
                user_text=_gone_request_user_text(state, request_id)
            ) from None
        if time.time() > float(request["expires_at_epoch"]):
            raise ApprovalError(
                "approval request %s expired. Remedy: create a fresh request "
                "and ask again -- expired requests never mint." % request_id,
                user_text="Es wurde keine Freigabe erteilt: die Freigabe-Anfrage war schon "
                          "abgelaufen, als deine Antwort ankam. " + NEXT_START_OVER
            )
        # format check, not mere presence: `mint_code: null` / "" would yield a
        # guessable label like "Freigeben [None]" (Opus check 2026-07-24)
        if not re.fullmatch(r"[0-9a-f]{6}", str(request.get("mint_code") or ""), flags=re.ASCII):
            raise ApprovalError(
                "pending request %s carries no valid mint_code (pre-amendment "
                "or hand-written file) -- refusing to mint (fail-closed). "
                "Remedy: create a fresh approval request." % request_id,
                user_text="Es wurde keine Freigabe erteilt: die gespeicherte Freigabe-Anfrage "
                          "trägt keinen gültigen Freigabe-Code. " + NEXT_START_OVER
            )
        expected = approve_label(request["mint_code"])
        if answer != expected:
            raise ApprovalError(
                "answer %r does not mint: only the exact approval label of "
                "THIS request mints (it carries a per-request code shown in "
                "the option). Casual free text never approves. The pending "
                "request stays until TTL." % (answer,),
                user_text="Es wurde keine Freigabe erteilt: der angeklickte Text gehört nicht zu "
                          "dieser Freigabe-Anfrage — jede Frage trägt ihren eigenen Code in "
                          "eckigen Klammern, und nur der Freigeben-Knopf DIESER Frage zählt. "
                          + NEXT_ASK_AGAIN
            )
        item = None
        if request["item"] is not None:
            item = state.read_item(request["item"])
            if item.get("revision") != request["revision"]:
                raise ApprovalError(
                    "item %s moved to revision %s since the request (requested "
                    "%s) -- out-of-band change, no mint. Remedy: re-run the "
                    "approval flow on the current revision."
                    % (request["item"], item.get("revision"), request["revision"]),
                    user_text="Es wurde keine Freigabe erteilt: der Vorgang wurde geändert, "
                              "nachdem die Frage gestellt wurde — du hättest eine andere Fassung "
                              "freigegeben als die, die jetzt vorliegt. " + NEXT_START_OVER
                )
            if request["kind"] in ("scope", "acceptance", "delivery"):
                current_hash = subject_manifest_hash(
                    item_subject_manifest(item, request["kind"])
                )
                if current_hash != request["subject_manifest_hash"]:
                    raise ApprovalError(
                        "subject manifest of %s changed since the request -- "
                        "no mint. Remedy: re-run the approval flow."
                        % request["item"],
                        user_text="Es wurde keine Freigabe erteilt: der Inhalt des Vorgangs hat "
                                  "sich geändert, nachdem die Frage gestellt wurde. "
                                  + NEXT_START_OVER
                    )
        # idempotency guard (Fable-Check 8/#2): a crash between APR write and
        # request consume would leave the request pending -- a replayed mint
        # must not create a SECOND approval for the same request
        existing = _approval_of_request(state, request_id)
        if existing is not None:
            raise ApprovalError(
                "request %s already minted %s -- replay blocked. "
                "Remedy: run `python scripts/harness.py validate` to reconcile the "
                "half-consumed request." % (request_id, existing.get("id")),
                # THE ONE BRANCH THAT MUST NOT SAY "no approval was created", because one was:
                # this is the crash window between the APR write and the request consume (see the
                # ordering note below). An alarm here would be as wrong as the silence BUG-0039 is
                # about, in the other direction.
                user_text="Deine Freigabe zu dieser Frage steht bereits (%s) — es fehlt nichts "
                          "und du musst nichts wiederholen. Dein Assistent sollte einmal den "
                          "Zustand prüfen lassen, damit der Vorgang die Freigabe auch sichtbar "
                          "trägt." % existing.get("id")
            )
        # LAST gate before the approval exists: provenance of the CALLER (see
        # _assert_minting_caller). Everything above refuses on content grounds and
        # says so; this refuses on "who is asking".
        _assert_minting_caller()
        apr_id = state.allocate_id("APR")
        apr = {
            "id": apr_id,
            "kind": request["kind"],
            "item": request["item"],
            "revision": request["revision"],
            # only the HASH, exactly as spec II.2 lists the APR fields. An
            # earlier cut stored the manifest here too, so a bundled analysis
            # approval could answer "do you cover TSK-0007?" -- but the consumed
            # request already carries the manifest and is kept forever ("move,
            # never delete"), so the copy created a second canonical home AND
            # let a HAND-WRITTEN APR answer that question with no minted request
            # behind it. Coverage is read from the consumed request instead
            # (kernel/dispatch.py), which carries the provenance with it.
            "subject_manifest_hash": request["subject_manifest_hash"],
            "request_id": request_id,
            "mint_code": request["mint_code"],
            "approved_at": _now_iso(),
            # DERIVED DISPLAY VALUE, not the authority: spec II.2 lists `expires`
            # among the APR fields and humans/dashboards read it here, but every
            # gate reads `proven_expiry(request)` instead -- the hash-covered copy
            # inside the minted manifest. Duty for the 1.4c validator: assert the
            # two agree, so a human can never read "valid until 2030" from a
            # record the gate correctly refuses.
            EXPIRY_FIELD: (request.get("subject_manifest") or {}).get(EXPIRY_FIELD),
            "revoked": False,
        }
        state._write_yaml_atomic(
            os.path.join(state.root, "approvals", apr_id + ".yaml"), apr
        )
        # CONSUME BEFORE THE ITEM MOVES, and the order is load-bearing rather than tidy. The
        # transition below runs the same `assert_transition_approved` every other caller runs
        # (there is no bypass parameter -- spec II.4), and that check proves an approval through
        # its CONSUMED request. Written afterwards, as it used to be, the mint would refuse its
        # own transition: the approval it had just created would still be unprovable.
        # What the reordering costs, stated rather than glossed: a crash between here and the item
        # write leaves a fully valid approval whose item carries no `approval_ref`. That item is
        # transitionable (the approval is real -- the user did approve) but NOT dispatchable
        # (`_assert_root_approval_locked` reads `approval_ref`), so the window fails closed on the
        # side that grants a spawn. NOTHING REPORTS THE PAIR, and that is worth knowing rather than
        # implying: `report.validate_state` walks items that HAVE an approval_ref, so an approval
        # whose item forgot it produces no finding -- only the two files in git say so. The old
        # order could not be kept either way, because a check that reads the store cannot be
        # satisfied by a store write that has not happened yet.
        state._write_yaml_atomic(_request_path(state, request_id, consumed=True), request)
        os.remove(path)
        if item is not None:
            item["approval_ref"] = apr_id
            item_type, _ = parse_id(apr["item"])
            # STAMP WHAT WAS APPROVED. The mint is the only moment at which a user has just said
            # yes to this exact content, so it is the only honest producer of that stamp -- and
            # before this line there was none at all: `report.validate_state` demanded a PROC's
            # `approved_hash` as an ERROR while the sole writer of it was a V1 script that opened a
            # deleted monolith and died. A rule whose only route to compliance is a command that
            # cannot run is a rule the project can never satisfy.
            # It is deliberately NOT a `--update` flag on a script either: "run this to make the
            # tamper check pass again" is the same permission the check exists to withhold.
            content_hash = approved_content_hash(item_type, item)
            if content_hash is not None:
                item[APPROVED_CONTENT_HASH_FIELD] = content_hash
            edge = APPROVAL_TRANSITIONS.get((item_type, request["kind"]))
            state._write_yaml_atomic(state.active_path(item["id"]), item)
            if edge and item.get("status") == edge[0]:
                # THROUGH the automaton, not around it. `state.transition` is documented as the
                # only status writer and this line used to disprove it: a direct `item["status"] =`
                # skipped `assert_transition` and would skip the approval check too, which is one
                # bypass in the one place a bypass would be invisible.
                item = state._transition_locked(item["id"], edge[1])
        state._regenerate_index_locked()
        return apr


def revoke(state: ProjectState, apr_id: str) -> dict:
    """Withdraw an approval — recorded where the APR file is NOT the evidence.

    The flag on the approval stays, because it is what a human reads. But the
    fact that actually blocks is the MOVE of the minted request out of
    `approvals/consumed/`: `consumed_request` then finds no provenance and
    refuses, so flipping `revoked` back to false achieves nothing.
    """
    with state.lock:
        path = os.path.join(state.root, "approvals", apr_id + ".yaml")
        try:
            apr = state._read_yaml(path)
        except FileNotFoundError:
            raise ApprovalError(
                "no approval %s. Remedy: check the id against the generated index, "
                "which lists every approval this project holds." % apr_id
            ) from None
        # ORDER MATTERS, do not "clean this up": the flag is written FIRST and is
        # checked first in both authorisation routes, so a crash between the two
        # writes can leave the flag without the move -- never the move without the
        # flag, which would be an approval that still authorises.
        apr["revoked"] = True
        state._write_yaml_atomic(path, apr)
        request_id = str(apr.get("request_id") or "")
        if request_id:
            consumed = _request_path(state, request_id, consumed=True)
            if os.path.exists(consumed):
                request = state._read_yaml(consumed)
                request["revoked_at"] = _now_iso()
                state._write_yaml_atomic(
                    _request_path(state, request_id, revoked=True), request)
                os.remove(consumed)
        # The APR file is a rendered item (`backlog_types.ACTIVE_DIRS["APR"]`), and `revoked` is a
        # field the index does not carry -- so before this line the board went on showing the
        # approval as in force while the file said otherwise, and nothing said the view was behind
        # (TSK-0071 verifier finding B2). The regeneration is on the rare branch: revoking is a
        # user act, and it already writes two files here.
        state._regenerate_index_locked()
        return apr


def pending_request(state: ProjectState, request_id: str) -> dict:
    """A PENDING approval request, or ApprovalError — the reader the hooks use.

    The PreToolUse(AskUserQuestion) gate resolves `[APR-REQ:<id>]` back to its
    request and rebuilds `build_question(request)` for the string comparison, so
    that lookup needs one public, fail-closed home rather than a hook reaching
    into a private path helper. The TTL check lives here too, for the same reason.
    """
    try:
        request = state._read_yaml(_request_path(state, request_id))
    except FileNotFoundError:
        raise ApprovalError(
            "no pending approval request %s (consumed, expired-and-cleaned, or "
            "never created). Remedy: run the kernel approval flow again -- an "
            "invented request id never mints." % request_id,
            user_text=_gone_request_user_text(state, request_id)
        ) from None
    except Exception as exc:
        raise ApprovalError(
            "pending request %s is unreadable (%s) -- fail-closed. Remedy: "
            "re-run the approval flow." % (request_id, type(exc).__name__),
            user_text="Es wurde keine Freigabe erteilt: die gespeicherte Freigabe-Anfrage lässt "
                      "sich nicht mehr lesen. " + NEXT_START_OVER
        ) from None
    if not isinstance(request, dict):
        raise ApprovalError(
            "pending request %s is not a mapping -- fail-closed." % request_id,
            user_text="Es wurde keine Freigabe erteilt: die gespeicherte Freigabe-Anfrage hat "
                      "nicht die Form, die das Programm erwartet. " + NEXT_START_OVER
        )
    if time.time() > float(request.get("expires_at_epoch") or 0):
        raise ApprovalError(
            "approval request %s expired -- expired requests never mint. "
            "Remedy: create a fresh request and ask again." % request_id,
            user_text="Es wurde keine Freigabe erteilt: die Freigabe-Frage war abgelaufen, als du "
                      "geantwortet hast. " + NEXT_START_OVER
        )
    return request


def open_requests(state: ProjectState) -> list:
    """Every approval request this project is still WAITING ON -- answerable right now.

    "Still open" is asked of `pending_request` per file rather than re-tested here, so the TTL and
    the unreadable case have one spelling: a request whose clock ran out is not something a user
    can still answer, and counting it would make the approval hook announce a request nobody could
    complete. Both ends of that -- the expired file is excluded HERE, and the hook that reads this
    goes quiet BECAUSE of it -- are measured in
    `tools/test_hooks_v2.py::test_an_expired_request_is_not_open_and_a_reworded_relay_goes_silent`,
    whose docstring also carries what the exclusion costs.

    WHAT READS THIS AND WHY IT IS STATE AND NOT SPELLING: `gate_approval` announces a non-mint when
    an approval is outstanding and the question that got answered was not that request's. That
    trigger has to survive a relay in the model's own words -- "Ja, freigeben" / "Nein" -- which is
    exactly what a test on the LABEL's wording does not
    (`tools/test_hooks_v2.py::test_a_relay_in_the_models_own_words_still_reaches_the_user`).
    """
    directory = _pending_dir(state)
    if not os.path.isdir(directory):
        return []
    requests = []
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".yaml"):
            continue
        try:
            requests.append(pending_request(state, name[: -len(".yaml")]))
        except ApprovalError:
            continue
    return requests


def declining_labels(request: dict) -> tuple:
    """The labels of THIS request's own question that do NOT approve.

    Read off `build_question`, so a renamed or added option arrives here with no second edit and no
    list of spellings. That is a claim about the DERIVATION and not about today's two words, so it
    is measured against a kernel whose question renames one of them:
    `tools/test_hooks_v2.py::test_a_renamed_decline_option_needs_no_second_edit`. What it is FOR:
    telling a DELIBERATE decline from a click that meant yes and achieved nothing. The first needs
    no notice -- the user chose it, on the kernel's own question, and a message there is noise on a
    correct outcome; the second is BUG-0039.

    Anything that is not one of these strings exactly -- free text, the approve label with a
    trailing space, a list -- is NOT a decline and is announced. That direction is the deliberate
    one: an unnecessary notice costs a sentence, a missing one cost pilot 3 a lost approval
    (`tools/test_hooks_v2.py::test_only_the_requests_own_decline_options_stay_quiet`).
    """
    approve = approve_label(request["mint_code"])
    return tuple(str(option["label"]) for option in build_question(request)["options"]
                 if str(option["label"]) != approve)


def consumed_request(state: ProjectState, apr: dict) -> dict:
    """The minted request behind an approval — its PROVENANCE (spec II.12).

    "manuell geschriebene APR ohne Provider-gepraegten Token -> Block": an
    approval file on its own proves nothing, because anything that can write
    YAML can write one. What cannot be forged is a CONSUMED REQUEST: the kernel
    is the only writer of `approvals/consumed/`, it lands there only through
    `mint`, and mint only runs on the verbatim approval label carrying that
    request's mint code. So every authorisation check resolves the approval back
    to its request and compares the two.

    Raises ApprovalError when the request is missing or disagrees with the
    approval — fail-closed, because "cannot prove provenance" must never read as
    "approved".

    REVOCATION lives here too, not in the APR file: `revoke` MOVES the request to
    `approvals/revoked/`, so a revoked approval simply has no consumed request
    and this refuses. Keeping `revoked: true` only inside the APR made revocation
    the least protected fact in the record — flipping one boolean back
    resurrected a withdrawn permission, and II.2 makes revocability load-bearing
    for exactly the kind that carries standing permissions.
    """
    request_id = str(apr.get("request_id") or "")
    if not request_id:
        raise ApprovalError(
            "approval %s names no request_id -- refusing to treat it as a user "
            "approval (spec II.12: a hand-written APR without a provider-minted "
            "token blocks). Remedy: obtain the approval through the kernel "
            "approval flow." % apr.get("id")
        )
    try:
        request = state._read_yaml(_request_path(state, request_id, consumed=True))
    except FileNotFoundError:
        revoked = os.path.exists(_request_path(state, request_id, revoked=True))
        raise ApprovalError(
            "approval %s %s -- it grants nothing (spec II.12/II.10a). Remedy: %s"
            % (apr.get("id"),
               "was REVOKED" if revoked else "has no consumed request %s, so its "
               "provenance cannot be proven" % request_id,
               "obtain a fresh approval." if revoked else
               "obtain the approval through the kernel approval flow; `python scripts/harness.py "
               "validate` reports approvals without a request.")
        ) from None
    except Exception as exc:
        raise ApprovalError(
            "consumed request %s for approval %s is unreadable (%s) -- "
            "fail-closed. Remedy: `git restore` the approvals directory."
            % (request_id, apr.get("id"), type(exc).__name__)
        ) from None
    if not isinstance(request, dict):
        raise ApprovalError(
            "consumed request %s is not a mapping -- fail-closed." % request_id
        )
    for field in ("mint_code", "subject_manifest_hash", "kind", "item", "revision"):
        if request.get(field) != apr.get(field):
            raise ApprovalError(
                "approval %s disagrees with its minted request on %s -- the "
                "approval was altered after minting, so it grants nothing "
                "(fail-closed). Remedy: re-run the approval flow."
                % (apr.get("id"), field)
            )
    # the hash is RECOMPUTED from the request's own manifest, not merely compared
    # between two stored copies: both stored hashes survive an edit of the
    # manifest, and the expiry lives inside that manifest (II.10a hashes the
    # Ablaufdatum), so without this an expired approval could be resurrected by
    # editing one field
    if subject_manifest_hash(request.get("subject_manifest")) != request.get(
            "subject_manifest_hash"):
        raise ApprovalError(
            "consumed request %s does not hash to its own recorded hash -- the "
            "minted record was tampered with, so the approval grants nothing "
            "(fail-closed). Remedy: re-run the approval flow." % request_id
        )
    return request


def proven_expiry(request: dict):
    """The approval's expiry, taken from the HASH-COVERED side.

    Read from the request's `subject_manifest`, not from `request.approval_expires`
    and never from the APR file. All three carry the same value, but only the
    manifest is inside the hash that `consumed_request` RECOMPUTES, so only there
    is the value tamper-evident. Reading it anywhere else made expiry a one-line
    edit away from resurrecting a lapsed permission, while II.10a demands the
    opposite ("Abgelaufene ... Routinefreigabe blockiert den Audit-Dispatch
    (fail-closed)").

    Honest limit: an editor that changes the manifest AND recomputes the hash in
    the request AND matches it in the approval file still passes -- the hash
    function is public. What is gone is every SINGLE-field edit. The remaining
    surface is closed by making the state directory kernel-only for tool writes
    (gate layer 3), not by arithmetic.
    """
    expires = (request.get("subject_manifest") or {}).get(EXPIRY_FIELD)
    if expires is None:
        return None
    try:
        return float(expires)
    except (TypeError, ValueError):
        raise ApprovalError(
            "minted request %s carries an unreadable expiry %r -- fail-closed; "
            "an approval whose validity cannot be read grants nothing. Remedy: "
            "re-run the approval flow." % (request.get("request_id"), expires)
        ) from None


def read_apr(state: ProjectState, apr_id: str) -> dict:
    path = os.path.join(state.root, "approvals", apr_id + ".yaml")
    try:
        return state._read_yaml(path)
    except FileNotFoundError:
        raise ApprovalError(
            "no approval %s. Remedy: the item's approval_ref is stale -- run "
            "`python scripts/harness.py validate`." % apr_id
        ) from None

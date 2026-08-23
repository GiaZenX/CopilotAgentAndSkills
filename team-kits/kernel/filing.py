"""Growing the Aktenplan -- the half of the office filing loop that had no walkable route.

THE DEAD END THIS EXISTS TO END (FR-0049 step 5). `filing_plan.yaml` is the single machine-readable
truth for where a document belongs, and `gate_filing` refuses every filing no rule of it covers. A
document of a class the plan does not know yet is therefore not filed at all -- correctly. What was
missing is what happens NEXT: the plan is a kit DOCUMENT (`layout.is_project_document`), so no
kernel path builder names it, `gate_write_scope` refuses every tool write to it, and the only
remaining route was the entry gate's session, which ran before the kit was installed. Inside a
project the answer was "ask the user to open a text editor" -- the same dead end BUG-0041 measured
for the preset, where the reported gap landed with the one party unable to close it.

So this is `presets.py`'s shape applied to the other document: the USER decides the new rule by
answering a kernel-composed approval question, and the KERNEL performs the write. Nothing here
widens what a session may write -- `add-filing-rule` is an ordinary command line naming neither
`.claude` nor the state directory, and the field it owns is declared in `DOCUMENT_WRITES` so the
write-scope gate's refusal names the route instead of denying one that exists.

WHAT THE USER APPROVES IS WHAT IS WRITTEN, and it is enforced twice rather than promised (DEC-0048).
The approval binds the rule's fields as the manifest hashes them, `apply` re-derives that manifest
from the command line and refuses unless a live approval carries exactly it -- and after the write
the file is PARSED BACK and the appended rule compared field for field against THE MANIFEST KEYS,
with the original bytes restored on any deviation.

THAT LAST COMPARISON IS AGAINST THE MANIFEST AND NOT AGAINST `rule_from`, and the difference is a
measured one. Until 2026-08-21 the check read `written[0] != rule_from(manifest)` -- the same
expression the WRITER had used -- so writer and check moved together: a verifier ablation that made
`rule_from` append "-typo" to the id left every test green while the plan received a rule the user
had not signed. `RULE_FIELDS` below is now a TABLE both sides read, and only the writer transforms;
the check reads the manifest values straight, so a transformation bug on the writing side has
nothing to hide behind.

WHAT IT DELIBERATELY DOES NOT DO:
  * it never EDITS or removes an existing rule. Appending cannot make a filing that was legal
    illegal; rewriting a `path_template` can orphan a whole branch of an archive that was filed
    under it, and that is a migration (a PROC with a dry run), not a one-line command.
  * it writes ONLY the approved fields. The plan's header lists more a rule MAY carry
    (`required_metadata`, `collision_policy`, `examples`); a value nobody was shown is a value
    nobody approved, so this command invents none of them.
  * it is not a filing. `gate_filing` still decides every move, against the plan as it stands when
    the move happens -- which is what makes this command safe to be a small one.
"""
from __future__ import annotations

import os
import re

import yaml

from . import approvals
from .state import ProjectState, StateError

# The APR kind that authorises this operation. One name, three readers: the vocabulary, the
# manifest builder and the refusal below.
KIND = "filing_rule"
COMMAND = "add-filing-rule"
PLAN = "filing_plan.yaml"
RULES = "rules"
# The names `uncovered_document_sources` compares across: the profile document and its list of what
# the business receives and produces. `RULE_TYPES` is the field BOTH sides of that comparison
# spell -- a rule declares the `document_types` it files, a source declares the ones it produces --
# and it is written here once, so `RULE_FIELDS` below and the coverage reader cannot come to spell
# it differently.
PROFILE = "business_profile.yaml"
SOURCES = "document_sources"
RULE_TYPES = "document_types"

# THE ONE PART OF A KIT DOCUMENT THIS COMMAND WRITES, declared where the writing happens -- the
# same contract `presets.DOCUMENT_WRITES` declares for `project_config.yaml`, and read by
# `kernel.layout.partial_writers` so the write-scope gate's refusal can name the route. `field` is
# the list this command appends to and nothing else in the file.
DOCUMENT_WRITES = ({"document": PLAN, "field": RULES, "command": COMMAND},)

# WHAT A RULE THIS COMMAND WRITES CONSISTS OF, as (name in the plan, key in the signed manifest).
# ONE declaration, TWO readers, and that is the whole of B4: `rule_from` BUILDS the rule out of it
# and `apply` READS the written file back against it, taking the values from the manifest rather
# than from the builder. A table has no transformation in it to get wrong, so the two readers cannot
# drift the way an expression and its own copy did.
#
# The id shape is NOT re-declared here. It is `approvals.RULE_ID_RX`, checked where the subject is
# built, and a second copy of it lived here for one round and had already drifted ({1,31} against
# {0,31}) without a single caller noticing -- which is exactly what a dead second answer does.
RULE_FIELDS = (("id", "rule_id"), ("path_template", "path_template"),
               (RULE_TYPES, RULE_TYPES),
               ("filename_template", "filename_template"), ("retention", "retention"))
# The top-level `rules:` key of the plan, and the two shapes an APPEND has to tell apart: the
# shipped template's empty FLOW list (`rules: []`, which a block item cannot be appended to) and a
# block list already carrying items. Anything else -- a flow list with entries, a `rules:` nested
# under something, two of them -- is refused rather than guessed at.
_RULES_LINE_RX = re.compile(r"\A(?P<head>rules[ \t]*:)(?P<tail>.*)\Z")
_EMPTY_FLOW_RX = re.compile(r"\A[ \t]*\[[ \t]*\][ \t]*(?:#.*)?\Z")
_ONLY_COMMENT_RX = re.compile(r"\A[ \t]*(?:#.*)?\Z")
# How deep an appended rule is indented under `rules:`. Two spaces, matching the commented examples
# the shipped template carries -- a block sequence may also sit at column 0, and picking the
# template's own spelling is what keeps a hand-written plan and a kernel-written rule looking like
# one file.
_INDENT = "  "


def plan_path(state: ProjectState) -> str:
    return os.path.join(state.root, PLAN)


def read_text(path: str) -> str:
    """The file as it stands, line endings included -- `presets.read_text`'s reason, verbatim.

    Universal-newline reading would hand back `\\n` for a CRLF file, and this writer puts the file
    back minus nothing: a silent CRLF-to-LF rewrite of a kit document is a change nobody asked for
    and nothing would report.
    """
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return handle.read()


def existing_rules(state: ProjectState) -> list:
    """The plan's current rules, or a StateError naming why there are none to append to.

    Deliberately NOT `gate_filing.rules`: that reader answers a GATE's question (is there anything
    to file against) and treats every reason alike, because fail-closed does not care why. This one
    has to tell an empty plan -- which is the normal state of a fresh project and the case this
    command exists for -- from an unreadable one, where appending would destroy what it cannot read.
    """
    path = plan_path(state)
    if not os.path.isfile(path):
        raise StateError(
            "%s does not exist in this project, so there is no filing plan to add a rule to. "
            "Remedy: this is an infrastructure gap, not a retry -- report it and name the file; "
            "the plan is written once, by the entry gate, before the kit is installed." % PLAN)
    try:
        document = yaml.safe_load(read_text(path))
    except Exception as exc:                            # noqa: BLE001 -- any parse failure is one
        raise StateError(
            "%s could not be parsed (%s), so a rule cannot be appended to it without risking the "
            "rules that are already in it -- refused, nothing was changed. Remedy: report the gap "
            "and name the file." % (PLAN, exc)) from None
    if document is None:
        document = {}
    if not isinstance(document, dict):
        raise StateError(
            "%s is not a mapping, so it carries no `%s:` list to append to -- refused, nothing was "
            "changed. Remedy: report the gap and name the file." % (PLAN, RULES))
    found = document.get(RULES)
    if found is None:
        found = []
    if not isinstance(found, list):
        raise StateError(
            "%s's `%s:` is %s and not a list -- refused, nothing was changed. Remedy: report the "
            "gap and name the file." % (PLAN, RULES, type(found).__name__))
    return found


def uncovered_document_sources(state: ProjectState) -> list:
    """[(what the user called it, [document type, ...])] the plan carries no rule for.

    THE DERIVATION, and it is the plan's own vocabulary on both sides: `business_profile.yaml`'s
    `document_sources:` names every kind of paper the business has WITH the `document_types` it
    produces, and a rule declares the `document_types` it files. A source is covered when every one
    of its types stands in some rule's list. Nothing here knows a drawer name, a business shape or
    a document class -- the two lists are the user's, and this only compares them.

    WHY IT EXISTS -- BUG-0061. In pilot 4 the onboarding interview asked about company, channels,
    assortment, tax and revenue sources and never about what the business RECEIVES or keeps about
    itself, so the initial plan had no supplier, sales, company or review rule and the owner had to
    demand each one after the fact. The interview text is where that is fixed (the two templates
    carry it); this is what makes the result CHECKABLE afterwards rather than trusted. ONE caller
    asks it today -- the office kit's SessionStart briefing, `_kernel.filing_coverage_briefing` --
    so a project whose sessions never start is told nothing, and no gate refuses anything over it.

    A PROFILE THAT NAMES NO SOURCES YIELDS NOTHING, and that is the honest answer rather than a
    silent pass: an empty list is a profile nobody walked, which is a fact about the INTERVIEW and
    not about the plan -- `gate_filing` already fails closed on a plan with no rules, so the
    project with neither is stopped by that, at the first document, with its own message.

    NEVER RAISES: both files may be missing, unparseable or shaped differently in a project this
    kernel did not write. A comparison that cannot be made is no finding -- the callers are a
    briefing and a report, and neither may turn an unreadable file into an accusation.
    """
    try:
        profile = yaml.safe_load(read_text(os.path.join(state.root, PROFILE))) or {}
        sources = profile.get(SOURCES) or []
        rules = yaml.safe_load(read_text(plan_path(state))) or {}
        rules = rules.get(RULES) or []
    except Exception:  # noqa: BLE001 -- see the contract above
        return []
    if not isinstance(sources, list) or not isinstance(rules, list):
        return []
    filed = set()
    for rule in rules:
        if isinstance(rule, dict):
            declared = rule.get(RULE_TYPES) or []
            declared = declared if isinstance(declared, list) else [declared]
            filed.update(str(one) for one in declared)
    uncovered = []
    for source in sources:
        if not isinstance(source, dict):
            continue
        wanted = source.get(RULE_TYPES) or []
        wanted = [str(one) for one in (wanted if isinstance(wanted, list) else [wanted])]
        missing = [one for one in wanted if one not in filed]
        if missing:
            uncovered.append((str(source.get("what") or "").strip() or "(unnamed source)", missing))
    return uncovered


def rule_from(manifest: dict) -> dict:
    """The rule as it will stand in the plan, built from the manifest the USER signed.

    THE WRITER'S SIDE OF `RULE_FIELDS`, and the only side that transforms anything: a list is copied
    so the plan does not end up sharing the manifest's object. The key ORDER is the order the plan's
    own header lists the fields in, so an appended rule reads like the ones a human wrote. What
    checks the WRITE is `signed_rule`, which reads the same table and transforms nothing.
    """
    return {field: (list(manifest[key]) if isinstance(manifest[key], list) else manifest[key])
            for field, key in RULE_FIELDS}


def signed_rule(manifest: dict) -> dict:
    """The rule the user's approval covers, read STRAIGHT off the manifest keys.

    The second expression `apply` compares the written file against. It is deliberately the dullest
    possible reader of `RULE_FIELDS` -- no formatting, no copying, no defaults -- because its whole
    job is to be a statement the writer cannot be wrong in the same way as
    (`tools/test_kernel.py::test_a_write_that_does_not_produce_the_approved_rule_is_rolled_back`).
    """
    return {field: manifest[key] for field, key in RULE_FIELDS}


def _rendered(rule: dict) -> str:
    """One rule as an indented YAML block sequence item.

    `safe_dump` and not a hand-built string: a `path_template` carrying a colon, a `#`, or a
    non-ASCII counterparty name is ordinary in an Aktenplan and each of them needs quoting the
    dumper already knows about. `sort_keys=False` keeps `rule_from`'s order; `allow_unicode` keeps
    an Umlaut readable instead of escaping it into something the user cannot recognise in their
    own plan; `default_flow_style=None` puts a leaf list inline (`[invoice, credit_note]`), which
    is how the plan's own commented examples write `document_types` — a kernel-written rule that
    reads like the hand-written ones beside it is one the user can still check.
    """
    body = yaml.safe_dump([rule], default_flow_style=None, allow_unicode=True, sort_keys=False)
    return "".join(_INDENT + line + "\n" for line in body.rstrip("\n").splitlines())


def _with_rule(text: str, rule: dict) -> str:
    """`text` with one rule appended to `rules:`, and NOTHING else about the file touched.

    A line edit rather than a YAML round-trip, for `presets._with_preset`'s reason: this file's
    comments carry the field list, the placeholder syntax and the retention defaults with their
    source, and `yaml.safe_dump` of a parsed copy would write back a valid file with all of it
    deleted -- the kernel silently destroying the one document in the project nothing else rewrites.

    THE NEW RULE GOES FIRST IN THE LIST, directly under the `rules:` key. Position carries no
    meaning to any reader -- `gate_filing.check` asks whether ANY rule matches -- and inserting at
    a known place is the difference between one rule about where the key is and a second rule about
    where the list ends, which the shipped template makes a trap: its commented examples stand
    AFTER `rules: []`, so "append at the end of the block" would put a rule behind them or inside
    the comment block depending on how the project edited it since.
    """
    lines = text.splitlines(keepends=True)
    hits = []
    for index, line in enumerate(lines):
        match = _RULES_LINE_RX.match(line.rstrip("\r\n"))
        if match:
            hits.append((index, match))
    if len(hits) != 1:
        raise StateError(
            "%s carries %d top-level `%s:` key(s); this kernel appends to exactly one and refuses "
            "to guess which. Remedy: report the gap and name the file." % (PLAN, len(hits), RULES))
    index, match = hits[0]
    tail = match.group("tail")
    if not _ONLY_COMMENT_RX.match(tail) and not _EMPTY_FLOW_RX.match(tail):
        raise StateError(
            "%s writes its `%s:` as `%s`, and this kernel appends only to an empty list (`%s: []`, "
            "the shipped template) or to a block list written under the key. Refused rather than "
            "rewritten -- nothing was changed. Remedy: report the gap and name the file."
            % (PLAN, RULES, (RULES + ":" + tail).strip(), RULES))
    ending = lines[index][len(lines[index].rstrip("\r\n")):] or "\n"
    comment = tail.partition("#")[1:] if "#" in tail else ("", "")
    head = match.group("head") + (" " + "".join(comment) if comment[0] else "")
    body = _rendered(rule)
    if ending.endswith("\r\n"):
        body = body.replace("\n", "\r\n")
    lines[index] = head + ending + body
    return "".join(lines)


def apply(state: ProjectState, manifest: dict) -> dict:
    """Append the approved rule to the filing plan -- the operation FR-0049 step 5 asked for.

    ORDER, and every step is deliberate. The plan is read first, so a plan this kernel cannot read
    is a refusal rather than a rewrite. The approval is checked before anything is written. The
    write is verified by PARSING THE FILE BACK and comparing the appended rule field for field
    against `signed_rule(manifest)` -- the MANIFEST's own values, not the builder's output -- with
    the original bytes restored on any deviation. Same doctrine as `presets.record_preset`, and for
    the same reason: a line edit is a text operation, and the only proof that it produced the
    approved rule is asking YAML what the file now says. See the module docstring for what checking
    it against `rule_from` instead let through.

    A RULE ID THAT IS ALREADY IN THE PLAN IS REFUSED. A line approval stays live until its clock
    runs out (`approvals.LINE_APPROVAL_VALIDITY`), so running this command twice would otherwise
    append the same rule twice -- and a plan carrying one id on two rules is one nobody can amend
    by naming it.
    """
    with state.lock:
        rules = existing_rules(state)
        rule = rule_from(manifest)
        clash = [r for r in rules if isinstance(r, dict) and str(r.get("id")) == rule["id"]]
        if clash:
            raise StateError(
                "%s already carries a rule with the id %r, so this one would make the id name two "
                "rules -- refused, nothing was changed. Remedy: if the existing rule is wrong, "
                "that is an amendment the user makes in the plan itself (this command only ever "
                "APPENDS); if the new class is a different one, ask for it under its own id."
                % (PLAN, rule["id"]))
        if approvals.live_line_approval(state, KIND, manifest) is None:
            raise StateError(
                "no user approval covers this filing rule, so nothing was changed. What it would "
                "do: file %s under %s. Remedy: ask for it first -- `python scripts/harness.py "
                "request-approval %s` prints the question the kernel composed, the USER approves "
                "by answering it, and then this command writes exactly what they approved."
                % (", ".join(rule["document_types"]) or "documents",
                   rule["path_template"], KIND))
        path = plan_path(state)
        before = read_text(path)
        state._write_text_atomic(path, _with_rule(before, rule))
        try:
            written = existing_rules(state)
        except StateError:
            written = None
        signed = signed_rule(manifest)
        if written is None or list(written[1:]) != list(rules) or written[0] != signed:
            state._write_text_atomic(path, before)
            raise StateError(
                "appending the rule to %s did not produce a plan that carries exactly what the user "
                "approved; the file was restored unchanged and no rule was added. Remedy: report "
                "the gap and name the file." % PLAN)
        return {"rule": written[0], "rules": len(written)}

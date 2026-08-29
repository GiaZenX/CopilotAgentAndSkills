#!/usr/bin/env python3
"""
PreToolUse(Bash|PowerShell|Edit|Write|MultiEdit|NotebookEdit) — a document does not enter the archive
on ONE reading. FR-0035, in the user's own words: nothing is moved until a name has been assigned to
it and a second, independent run arrives at the same answer.

WHAT THIS ADDS TO `gate_filing`, which is the gate it stands behind in the same chained command.
`gate_filing` asks whether the DESTINATION is a place the plan knows. That question is answered by
the plan alone, so a proposal nobody reviewed passed it exactly like any other move — measured
2026-08-25 in a scaffolded office project, a shell move and a direct write into a plan-covered
archive path both rc 0 through the full registered chain with no review record of any kind. This
gate asks the second question: does the project hold TWO independent readings that put THIS document
at THIS path under THIS name.

WHEN IT ASKS, AND WHY THAT IS A PROPERTY AND NOT A LIST: `an_entry` decides it, and its own header
carries the measurement that shaped it. In short — every landing under `archive/` except the one
case where no classification was made, a document staying under the same rule with the same
filename. An archive-internal RENAME is a classification and is asked about; nothing else in this
kit asks about it, and `guard_fs_tripwire` deliberately does not (its header records why).

WHOSE DECISION THE POLICY IS. Not this file's: HOW MANY readings a class needs is read off the
filing plan, per rule, and the plan is the user's (FR-0028 — the office kit gets rules, never
hardcoded bindings). Two, unless the rule says otherwise, and "otherwise" is the one answer YAML
itself reads as the boolean false; see `readings_required`, which also carries why a release is ONE
reading and never none. A plan that says nothing therefore asks for two everywhere, which is the
safe side and the side a project starts on.
`test_a_plan_rule_can_release_its_own_class_from_the_second_reading` measures all three states.

WHAT "INDEPENDENT" IS MEASURED ON, said here in full because the refusals below are shorter than
this: two readings are independent when a hook attested that two DIFFERENT RUNS wrote them, the run
being the provider's own `agent_id` for the writing call. It is NOT measured on whether the second
run had seen the first — nothing in the hook layer observes a Read, the records lie in `staging/`
where every role may look, and no refusal here should be read as saying otherwise. `_readings`
carries the whole of that argument and the one unmeasured assumption behind it.

WHAT IT DOES NOT SEE, on the same footing as `gate_filing`'s own residue and for the same reason: a
write performed INSIDE another program (`python -c "shutil.move(...)"`, a script that files by
itself) names no destination this reader can read, so it is not judged here either. The shell
reading is `_filing`'s, shared with the gate ahead of it and with the tripwire, so "where does this
land" cannot mean two things on the two sides of the wall.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import _kernel
except BaseException as exc:  # noqa: BLE001 — a hook that cannot load must not mean "allow"
    sys.stderr.write("[team-kit hook] refused: could not load hook helpers (%r). Remedy: run "
                     "`python scripts/harness.py doctor`; a partial checkout or half-finished kit update is the "
                     "usual cause.\n" % (exc,))
    sys.exit(2)

import _compat  # noqa: E402
import _filing  # noqa: E402
import _readings  # noqa: E402
import gate_filing  # noqa: E402

HOOK = "gate_second_reading"
# The plan field a rule uses to release its own class from the SECOND reading. Its VALUES are not
# enumerated anywhere: `readings_required` reads the one answer YAML gives as a boolean false and
# treats everything else — absent, true, a word, a list — as "not released".
SECOND_READING = "second_reading"
# The two answers `readings_required` gives, named because both appear in refusals the user reads
# and a number that lives in two places is the one that stops matching the code.
REQUIRED_READINGS = 2
RELEASED_READINGS = 1


def readings_required(rule):
    """How many independent readings this plan rule demands before one of its documents is filed.

    TWO BY DEFAULT, and the only way to say otherwise is a value the plan's own YAML reads as the
    boolean false — so the spellings that release a rule (`false`, `no`, `off`, `False`) are
    PyYAML's and not a tuple in this file. Every other value, the field being absent included, is
    "not released": a plan that says nothing has released nothing, and a typo must not read as a
    release.

    A RELEASE IS ONE READING, NOT NONE, and that is a correction of this round's own first cut. The
    user's question was "two runs for every document, or only for the classes the plan marks" — one
    run against two, never zero — and reading `false` as "ask nothing" made the released class a
    laundry: measured 2026-08-29, a document already filed under a SECURED rule could be renamed
    into a released folder with no reading of any kind, because the gate stood down entirely there.
    A released class still has to have been READ once by an attested run; what the user gave up is
    the second opinion, not the record.
    `test_a_plan_rule_can_release_its_own_class_from_the_second_reading` measures all three states.
    """
    return (RELEASED_READINGS if (rule or {}).get(SECOND_READING, True) is False
            else REQUIRED_READINGS)


def landing_path(root, landing):
    """The repo-relative path this landing creates INSIDE the archive, or None.

    Every base the token could be meant against is read and the first that lands in the archive
    counts — the same fail-closed direction `gate_filing.check` takes for the same reason: an
    over-block asks the clerk for a reading, a missed reading files a document on one opinion.
    """
    for base in landing.bases:
        relative = _filing.position(root, base, landing.token)
        if relative and _filing.under(os.path.dirname(relative), _filing.ARCHIVE):
            return _readings.as_landing(relative)
    return None


def rule_identity(rules, path):
    """The covering rules of a path, as the one thing that identifies a rule: its `path_template`.

    Sorted and compared as a set, so "the same rule" means the same filing decision and not the same
    object — two rules whose templates both cover a place are one answer for it.
    """
    return sorted(str(rule.get(gate_filing.PATH_TEMPLATE)) for rule in covering(rules, path))


def an_entry(rules, path, sources):
    """Is this landing an ENTRY into the archive — a filing decision the plan has to be asked about?

    ONE WAY PAST, and everything else is in. What is NOT an entry: the document comes from inside
    the archive, is covered by the SAME `path_template`s, and keeps the SAME filename. Arriving from
    outside, landing under a different rule, landing under a different name, and having no source at
    all (a redirect, a tool write — content out of nothing) are each an entry.

    READ THAT EXEMPTION LITERALLY, because it is WIDER than "a folder being tidied", which is what
    this sentence used to say. The comparison below is the RULE and the NAME; it is not the FOLDER.
    So a move that changes only the value of a placeholder — `…/incoming_invoices/2026/x.pdf` to
    `…/2027/x.pdf` — matches the same template under the same name and is exempt, although the year
    IS part of the classification and no reader was asked about the new one (measured 2026-08-29
    through the full chain, rc 0; and such a move can land on top of a different document that DID
    pass its readings, without the byte-binding in `check` ever running, because this function
    stands the gate down first). That is a gap this code does not close and this docstring does not
    pretend it does. It is still strictly narrower than the predecessor, under which EVERY
    archive-internal move was free.

    THE HOLE THIS CLOSES, measured 2026-08-29 through the full registered chain with NO released
    rule. The predecessor asked only whether the source was inside the archive, so once a document
    had passed its two readings the whole archive was a free namespace: the legitimate filing rc 0,
    then `mv archive/finance/.../2026-03-04_ACME_invoice.pdf archive/hr/2026/…_employment_contract
    .pdf` rc 0, then back to its own rule under `2099-12-31_FORGED_invoice.pdf` rc 0 — three moves,
    one reading pair, no reader ever asked. A rename inside the archive IS a classification, and the
    gate that exists because one classification is not enough has to be asked about it.

    AND NOTHING ELSE CATCHES IT, which is why the predecessor's docstring pointing at
    `guard_fs_tripwire` was worse than no sentence: that guard deliberately allows every move that
    stays inside the archive (its own header records the 2026-08-03 measurement that made refusing
    them a defect), so what it hands over here is not a wall but an opening.
    `test_an_archive_internal_rename_is_a_filing_decision_and_needs_its_own_readings` measures it.
    """
    if not sources:
        return True
    for source in sources:
        if not _filing.under(source, _filing.ARCHIVE):
            return True
        if os.path.basename(source) != os.path.basename(path):
            return True
        if rule_identity(rules, source) != rule_identity(rules, path):
            return True
    return False


def covering(rules, path):
    """The plan rules whose path_template covers the DIRECTORY this landing lands in.

    `gate_filing.rule_matches` is asked rather than re-implemented: one reader of the plan, so a
    change to what a `<placeholder>` means cannot make the two gates disagree about which rule a
    document falls under.
    """
    directory = os.path.dirname(path)
    return [rule for rule in rules
            if gate_filing.rule_matches(rule.get(gate_filing.PATH_TEMPLATE), directory)]


def sources_of(root, landing):
    """The landing's source tokens as repo-relative positions — the spelling a reading uses.

    Resolved and not taken as typed: the command names its source against the shell's working
    directory (`inbox/a.pdf`, `../inbox/a.pdf`), and a reading names it against the project root. A
    token that resolves nowhere inside the project contributes nothing, which loses a join and never
    invents one.

    ONE TOKEN CAN RESOLVE TWICE, because a relative word may be meant against the repo root or
    against the shell's cwd (`_filing.reading_bases`), and only one of the two is the document the
    shell will really move. Where the filesystem can tell them apart it is asked: a position that
    EXISTS wins over one that does not. Without that, a reading about a root-level `scan.pdf` would
    count for a `cd inbox && mv scan.pdf …` that moves `inbox/scan.pdf` — a narrow case, but one
    where two readings would authorise a document nobody read. Where NONE of the readings exist —
    a glob, a variable, a source that is not there — nothing is returned and `check` refuses for
    want of a document rather than guessing which one was meant.
    """
    found = []
    for token in landing.sources:
        for base in landing.bases:
            relative = _filing.position(root, base, token)
            if relative and relative not in found:
                found.append(_readings.as_landing(relative))
    real = [one for one in found
            if os.path.exists(os.path.join(root, one.replace("/", os.sep)))]
    return real or []


def related(found, path, sources):
    """Every reading that is ABOUT this document — the ones that agree, and the ones that do not.

    Two joins, because a disagreement breaks the first one: a reading naming this destination, and a
    reading naming a source this move takes away. Without the second join a move to reader A's path
    would report "one reading" and never show the user reader B's answer, which is the half of
    FR-0035 that says both readings are put side by side.
    """
    wanted = set(sources)
    return [one for one in found if one.destination == path or one.source in wanted]


def document_digest(root, source, seen):
    """sha256 of the document a reading is ABOUT, as it lies right now — or "" when it cannot be had.

    The same reader and the same bound the attestation used (`_readings.digest`,
    `MAX_DOCUMENT_BYTES`), so "the document has not changed" is one comparison and not two answers.
    `seen` memoises within one call: a drop of twenty readings about one document must not hash it
    twenty times inside a blocking gate.
    """
    if not source:
        return ""
    if source not in seen:
        seen[source] = _readings.digest(os.path.join(root, source.replace("/", os.sep)),
                                        _readings.MAX_DOCUMENT_BYTES) or ""
    return seen[source]


def refuse(path, sources, rule_ids, needed, found, agreeing, bound):
    """The one refusal, with the readings the user has to decide between spelled out.

    FOUR REASONS, told apart because each sends the reader somewhere else: the readings are missing
    or too few; they exist but come from one run; they exist and no longer describe the document
    being filed; or they were never bound to a document at all.

    THE LAST TWO USED TO BE ONE SENTENCE, and it was fiction for half the cases it covered.
    `check` drops a reading from `bound` for TWO reasons — a digest that does not match, and a digest
    that was never taken — and this branched only on the count, so a reading whose document was not
    there when it was attested, or was too large to hash, was reported as "a document replaced since
    then". Measured 2026-08-29: a source that never existed and a document past
    `_readings.MAX_DOCUMENT_BYTES` both got the swap sentence. The refusal was right and the
    diagnosis was invented, which sends a role hunting for a swap that never happened.
    `test_a_reading_that_could_not_be_bound_says_so_instead_of_reporting_a_swap` measures both ends.
    """
    runs = sorted({one.run for one in bound})
    lines = [one.named() for one in sorted(related(found, path, sources),
                                           key=lambda one: (one.destination, one.run))]
    unbound = [one for one in agreeing if not one.source_digest]
    stale = [one for one in agreeing if one.source_digest and one not in bound]
    if stale:
        why = ("%s is being filed to %s, and the document is not the one the readings were made "
               "about: %d of %d attested readings no longer match its bytes. A reading is bound to "
               "the document as it lay when it was written, so a document replaced since then has "
               "been read by nobody."
               % (", ".join(sources) or "this document", path, len(stale), len(agreeing)))
    elif unbound:
        why = ("%s is being filed to %s, and %d of %d attested readings could not be bound to a "
               "document at all: when each was attested the document was not there to read, or it "
               "was larger than the %d bytes this gate hashes. Nothing here says the document was "
               "replaced — it says the binding was never made, so there is nothing to check it "
               "against."
               % (", ".join(sources) or "this document", path, len(unbound), len(agreeing),
                  _readings.MAX_DOCUMENT_BYTES))
    elif len(bound) >= needed and len(runs) < needed:
        why = ("%d classification readings name %s, and the attestations put all of them on %d run "
               "(%s). A second reading by the run that made the first is not a second reading."
               % (len(bound), path, len(runs), ", ".join(runs)))
    else:
        why = ("%s needs %d independent classification reading(s) before it is filed and the "
               "project holds %d that name it and the document being moved (%s). The document is "
               "not moved and not renamed."
               % (path, needed, len(bound), ", ".join(sources) or "no readable source"))
    _kernel.block(
        HOOK,
        "%s The filing plan asks for %d reading(s) here (rule %s; `%s: false` would ask for %d, and "
        "never for none).%s"
        % (why, needed, "/".join(rule_ids) or "?", SECOND_READING, RELEASED_READINGS,
           ("\nRecorded for this document:\n  " + "\n  ".join(lines)) if lines
           else "\nNo attested reading names this document at all."),
        remedy="have a SECOND run classify the document — one that was not given the first answer — "
               "and let it write its own `%s` record into `project_memory/staging/<TSK-ID>/`, "
               "naming the document's own path as `source` and the full archive path INCLUDING the "
               "filename as `destination`. Where the two readings differ, nothing is filed: put "
               "BOTH answers to the USER and file what they decide. A record counts only once "
               "`record_filing_reading` has attested WHICH RUN wrote those exact bytes and what the "
               "document looked like then, so a record no reader could see being written — one "
               "produced inside another program — one edited after it was attested, one whose "
               "document has been replaced since, and one whose document could not be read at all "
               "when it was attested, are not readings. What that attestation shows is "
               "the run and not the reader's attention: it cannot see whether the second run read "
               "the first record, and this gate does not claim it can." % _readings.SCHEMA)


def refuse_without_a_source(path, rule_ids, needed):
    """A landing that names no document cannot be tied to a reading OF one — so it is refused.

    A redirect and a tool write create content out of nothing; a move whose source this reader
    cannot place names nothing it can join on. Leaning on the readings that happen to name the
    TARGET is what made a filing authorised by consent to a FOREIGN document — measured 2026-08-29,
    full chain, with two agreeing readings about `inbox/scan.pdf` in the project: `echo forged >`
    that target rc 0 and a direct `Write` to it rc 0. Filing in this kit MOVES a document (§2.5);
    that is the route this refusal points at.
    `test_a_landing_with_no_document_behind_it_is_refused` measures both halves.
    """
    _kernel.block(
        HOOK,
        "something is being created at %s without a document behind it — no source this reader can "
        "place, so there is nothing a classification reading could be about. The filing plan asks "
        "for %d independent reading(s) here (rule %s), and a reading names the document it read."
        % (path, needed, "/".join(rule_ids) or "?"),
        remedy="file by MOVING the document from the tray it arrived in, after the reading(s) that "
               "rule asks for have been recorded as `%s` naming it. Content that belongs in the "
               "archive without ever having been a document in a tray is not a filing — say what it "
               "is and let the USER decide where it goes." % _readings.SCHEMA)


def check(root, landings):
    rules, _reason = gate_filing.rules(root)
    if not rules:
        return   # no plan to file against: `gate_filing` refuses this call, and says why
    state = _kernel.state_dir(root)
    field = _readings.contract(lambda name: _kernel.kernel_module(name, root))
    found = _readings.readings(state, field) if field else []
    judged, digests = [], {}
    for landing in landings:
        path = landing_path(root, landing)
        if path is None or path in judged:
            continue
        sources = sources_of(root, landing)
        if not an_entry(rules, path, sources):
            continue
        judged.append(path)
        covered = covering(rules, path)
        if not covered:
            continue   # no rule covers it: that is `gate_filing`'s refusal and stays its message
        # THE HIGHEST DEMAND AMONG THE COVERING RULES, which is the fail-closed direction where two
        # templates overlap: one rule the user released cannot release a place a second rule secures.
        # Pinned by `test_where_two_rules_cover_one_place_the_higher_demand_wins`, whose fixture is
        # the first in the suite with overlapping templates — until it existed `max` and `min` were
        # indistinguishable here and this sentence was a claim nothing could falsify.
        needed = max(readings_required(rule) for rule in covered)
        rule_ids = [str(rule.get("id") or "?") for rule in covered]
        if not sources:
            refuse_without_a_source(path, rule_ids, needed)
        # EVERY DOCUMENT THE TOKEN COULD NAME has to be covered, not one of them. A reading counts
        # for THIS filing only if it is about THIS document going to THIS place — the destination
        # alone made the records a licence for a target rather than for a document — and where a
        # relative word resolves to two existing files (the repo root and the shell's cwd both being
        # plausible, `sources_of`), this reader cannot tell which the shell will move. Demanding the
        # readings for both is the fail-closed answer; the alternative is picking one and being
        # wrong about a document nobody read. The price is an over-refusal where a same-named file
        # sits at the repo root, and the refusal names the source it found nothing for.
        for source in sources:
            agreeing = [one for one in found
                        if one.destination == path and one.source == source]
            bound = [one for one in agreeing
                     if one.source_digest
                     and one.source_digest == document_digest(root, one.source, digests)]
            if len({one.run for one in bound}) < needed:
                refuse(path, [source], rule_ids, needed, found, agreeing, bound)


def main():
    # No `hook_event_name` guard, for `gate_filing`'s reason: this gate is registered on PreToolUse
    # and nowhere else, so the event is settled by settings.json.
    data = _kernel.payload(HOOK)
    tool = data.get("tool_name")
    if tool not in ("Bash", "PowerShell", "Edit", "Write", "MultiEdit", "NotebookEdit"):
        sys.exit(0)
    cwd = str(data.get("cwd") or "")
    root = _kernel.find_repo_root(cwd)
    bases = _filing.reading_bases(root, cwd)
    if tool in ("Bash", "PowerShell"):
        command = str((data.get("tool_input") or {}).get("command") or "")
        check(root, _filing.landings(command, bases))
    else:
        check(root, [_filing.Landing(path, [], bases) for path in _compat.file_paths(data)])
    sys.exit(0)


if __name__ == "__main__":
    _kernel.run_gate(HOOK, main)

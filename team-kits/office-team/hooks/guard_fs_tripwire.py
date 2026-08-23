#!/usr/bin/env python3
"""
PreToolUse(Bash|PowerShell) — deletes under inbox/ or archive/, and moves that take a document OUT
of archive/, are blocked unless the USER approved that exact correction.

Business documents are irreplaceable: "originals are moved, never deleted" must not depend on
discipline. Filing INTO archive/ stays free (`gate_filing` is what makes that opening safe);
deleting anything under inbox/ or archive/, or moving something out of archive/, blocks.
Reorganisation inside the archive runs as a user-approved migration PROC — if this guard fires on
legitimate reorg, that is the signal to get the user's OK first, not to work around it.

THE ONE DOOR IN THAT WALL, and why it exists (FR-0050). The wall was right as a default and wrong
as a life sentence: a document filed in the wrong place stayed wrong, because nothing inside the
kit could move it back and nothing could remove a duplicate scan. The user's steering was "löschen
und verschieben darf möglich sein, aber erst nach Freigabe", so the correction runs on the kit's
own approval machinery rather than on a new one: the clerk opens the question with `python
scripts/harness.py request-approval filing_correction --document <path> [--destination <path>]
--reason <why>`, the USER mints it by answering, and `open_the_door` below lets through the one
operation that approval names — the same document, the same version of it, the same destination or
the same deletion.

WHAT THE DOOR IS WORTH, AS THE FOUR CONDITIONS IT REALLY CHECKS, because a shorter sentence here
was measured false. The door opens for a COMMAND LINE, so all four are about the line:

  1. this guard placed EVERYTHING on it — every invocation, every operand of one, and every
     REDIRECT TARGET, which is none of the two and had to be read on its own (`>` is shell syntax,
     so no reader of arguments can see it), WHEREVER on the line the redirect stands. An invocation
     it does not read (`python -c "os.remove(...)"`, `tar --remove-files`, an `echo`, a `tee` behind
     a pipe), an operand or a redirect target the shell rewrites (`$A`, a glob, `~/…`), one that
     names no place in this project, a `cd` it cannot follow, a redirect writing INTO a tray of
     record: any one of them and NOTHING on the line is let through. Each of those rode through
     beside an approved operation before the condition existed (verifier findings F1/F2 and round 2
     R1, all measured rc 0), and a redirect written FIRST hid its own invocation from every reader
     until `_filing._tokens` stopped ending the argument list at it (round 3, V1/V2);
  2. it asks for at most `CORRECTION_CAP` corrections — see that constant for why a bound is part
     of the protection rather than a limitation of it;
  3. every operation on it carries a LIVE user approval (minted, unrevoked, unexpired, provenance
     provable) naming exactly that operation;
  4. and the approval binds the document's BYTES (`kernel.hashing.document_content_hash`), so what
     it covers is those bytes at that position while they lie there: once the approved command has
     run there is nothing at the source to hash and the approval matches nothing. That is the push
     token's derivation, not a "used" flag anyone has to keep honest — and it means a byte-identical
     file put back at that position is covered again, which the question the user signs says
     ("gilt nur für genau diese Fassung") rather than promising a one-shot.

Everything else this guard refuses, it goes on refusing — a different document under the same
approval, a different destination, a deletion where a move was approved, one approved document
beside one that is not.

AND WHAT IT NEVER SAW IT STILL NEVER SEES, which is the honest limit of all four conditions: they
decide whether the DOOR opens, never what the WALL notices. A `python -c "os.remove(...)"` or a
bare `> inbox/x.pdf` ALONE on its own command line is refused by nothing here, exactly as before
this door existed — the trays' own residual list at the end of this docstring is where those live.
What the conditions buy is that none of them can be carried through by something the guard DID
see.

WHAT IS RECORDED, stated no wider than it is: the durable record of a correction is the minted
request the kernel keeps forever under `approvals/consumed/` — it carries the document, the version
hash, the destination or its absence, the reason the user was shown, and the mint code. This guard
adds one line to `project_memory/.audit/hook_events.jsonl` naming the approval it honoured and the
command it let through; that file is local diagnostics (see `_audit`), and it says the call was
ALLOWED, never that it succeeded — a PreToolUse hook runs before the command and cannot know.

WHAT "OUT OF ARCHIVE" MEANS, and this is the correction of 2026-08-03. The question is about the
RESOLVED POSITION of the source and of the destination, not about the string `archive/` appearing
in a token. Reading the token was wrong in both directions at once, measured against these hooks: a
move from one archive folder to another was refused (the source token carried the word), and a move
that really emptied the archive was allowed as soon as the source token did not. The audited
project had written the second spelling into an APPROVED procedure, because it was the shape that
got its work done, and two of the refusals in its audit log are moves that never left the archive
at all.

So the fix is not a pattern for that spelling. Source and destination are resolved against the
working directory the command line actually left behind (`_filing`, shared with `gate_filing`, so
the two sides of the wall cannot disagree about where it stands), which reads every spelling whose
TEXT IS THE PATH the same way — a relative path after a `cd` or a `pushd`, a `../` climb, a
wrapper payload. The spellings whose text is NOT the path are the residual, and they are listed at
the end of this docstring rather than implied to be covered.

The DELETE rule keeps its token reading and gains the resolved one on top: the two are a union, so
a `cd archive/x && rm y.pdf` is caught while nothing that was refused before becomes allowed. It is
deliberately NOT the same replacement as the move rule — there is no legitimate delete under these
trays to protect, so there is no false positive to remove.

WHAT THIS DOES NOT SEE, so each stays a decision rather than a discovery:

  * a removal performed inside another program (`python -c "os.remove(...)"`);
  * a token, or a `cd` argument, the shell rewrites before use — a variable, a glob, `~`. `_filing`
    resolves none of them and this guard blocks on none; uncertainty -> exit 0 is this guard's
    contract, and a guess about an unresolvable name would break it;
  * an output REDIRECT into a tray of record ON ITS OWN (`echo x > inbox/y.pdf`), which truncates a
    document of record as surely as a delete. This guard's two rules key on a delete VERB and on a
    move OUT of the archive, and a redirect is neither, so nothing here refuses it — `gate_filing`
    catches the `archive/` half (it reads redirect targets among the paths a command CREATES) and
    the `inbox/` half is refused by nothing. Named here rather than closed, because closing it is a
    new WALL rule for every office project and not a property of this round's door; what the door
    does do is refuse such a redirect when it rides on a line asking for a correction (R1);
  * a COPIER told to relocate IS now read as one: a source-deleting flag (`robocopy /MOVE`, `rsync
    --remove-source-files` and its alias `--remove-sent-files`) makes `_filing.relocating` true, so
    emptying the archive with it is refused (BUG-0002, `SOURCE_DELETING_FLAGS`). What stays open is
    the neighbouring case that deletes in the DESTINATION rather than the source — `robocopy inbox
    archive/… /MIR` (which /PURGEs the archive) is not a move OUT of it and this rule does not see it;
    that is a delete INSIDE the archive, and the delete rule keys on verbs (`DELETE_VERBS`), not on a
    robocopy flag;
  * `tar --remove-files` archives the source and then DELETES it, emptying the archive as surely as a
    move — but `tar` is not a copy verb (`_filing` reads copy/move by calling convention and tar has
    none), so `moved_out_of_the_archive` never sees it. Named as a residual in
    docs/POST_V2_WISHLIST.md rather than bolted on here, because catching it means a second,
    non-copier deletion path this guard does not have.
"""
import os
import re
import sys


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _audit
import _compat  # noqa: F401 — UTF-8 stream pinning (import side effect)
import _filing
import _root


# The two trays whose contents are DOCUMENTS OF RECORD: what arrived (inbox) and what is filed
# (archive). `outbox/` is the kit's third tray and is deliberately not here — it holds drafts the
# project produces and may discard, so a delete there is ordinary work.
INBOX = "inbox"
PROTECTED_TRAYS = (_filing.ARCHIVE, INBOX)
# The verbs that DESTROY. Read twice on purpose (see the module docstring): once against the raw
# command text, once against what each operand resolves to. The regex is BUILT from the same two
# tuples rather than re-typed — a verb or a tray added to one reading and not the other is exactly
# the half-blind guard this round is correcting.
DELETE_VERBS = ("rm", "rmdir", "del", "erase", "rd", "remove-item", "ri")
DELETE_RX = re.compile(r"\b(%s)\b[^\n;|&]*\b(%s)(\b|[/\\])"
                       % ("|".join(DELETE_VERBS), "|".join(PROTECTED_TRAYS)), re.I)
# shell redirects into the ledger bypass the Edit/Write guard (audit finding: `echo >> ledger/x.csv`).
# The TARGET is read through `_filing.redirect_targets`, which resolves quoting and lifts wrapper
# payloads the same way the write-scope gate reads a state path — a raw scan of the command text saw
# neither `led'g'er/x.csv` nor `"ledger"/x.csv`, both of which name this file (BUG-0003). This
# pattern therefore runs against an already-resolved single word, not the raw line.
LEDGER_CSV_RX = re.compile(r"\bledger[/\\][^\s]*\.csv", re.I)
# The exemption is for INVOKING the script, not for MENTIONING it. A substring test let
# `echo garbage >> ledger/2026.csv # via ledger_add.py` through -- a comment disabled the rule.
LEDGER_ADD_RX = re.compile(r"(?:^|[;&|(]|\bpython[0-9.]*\s+|\bpy\s+)\s*\S*ledger_add\.py\b", re.I)
# WHAT ONE CORRECTION COSTS THE DOOR TO DECIDE, as a budget rather than as a stopwatch reading: a
# file read for the version the approval binds, plus a dictionary lookup. The figure is deliberately
# an order of magnitude above anything measured on a developer host, because it has to hold on the
# slowest machine this kit runs on -- and being wrong in the SLOW direction only makes the cap
# smaller, i.e. only ever refuses earlier. The per-round measurements sit in
# docs/reviews/2026-08-18-tsk0077-measurements.md, not here: a number measured for one round belongs
# in that round's report, never in a second copy beside the code.
CORRECTION_COST_SECONDS = 0.2
# HOW MUCH OF THE HOOK'S DEADLINE THIS ONE DECISION MAY SPEND. A tenth, because the door is not
# what the process is: starting the interpreter, reading the payload, walking the command line and
# reading the approval store all come first, and the size of that store is not something the door
# controls at all (see the report's residue on it). A gate that finishes exactly on the deadline has
# not finished.
CORRECTION_BUDGET_SHARE = 0.1


def budget_cap():
    """The most corrections the door could consider and still decide inside its budget.

    THE BUDGET IS `_compat.HOOK_DEADLINE_SECONDS` and is not restated here (R4). What passing it
    costs is no longer a kill -- BUG-0062 measured that away, and that constant carries the finding
    -- but a door that decides for two minutes is a session that stands still for two minutes with
    the user watching. Measured before any bound existed (verifier finding F3): one `rm` naming 8000
    archive documents took 114 s where the wall alone took 0.54 s.

    This is a CEILING, not the cap. `CORRECTION_CAP` is smaller and is chosen for a product reason;
    what this function exists for is that the choice cannot quietly drift past what the budget
    supports -- `tools/test_hooks.py::test_the_cap_stays_inside_the_budget_it_exists_for` recomputes
    it and goes red if it ever does.
    """
    return int(_compat.HOOK_DEADLINE_SECONDS * CORRECTION_BUDGET_SHARE / CORRECTION_COST_SECONDS)


# HOW MANY CORRECTIONS THE DOOR WILL EVEN CONSIDER ON ONE COMMAND LINE. 25 for a reason about the
# WORK and not about the clock: a correction is a single-document act -- the clerk asks the user per
# document and the question the user signs names one -- so a line past this is not the shape the
# door is for. Above it the door does not open and the wall answers as it always did, so the cap can
# only ever REFUSE. That it also sits under `budget_cap()` is the safety half, and it is measured
# rather than assumed.
CORRECTION_CAP = 25
# THE WAY OUT, in both refusals, because a refusal that names no route is what made a mis-filed
# document permanent (FR-0050). It is written once: the two refusals differ in what they refuse and
# not in how a correction is obtained, and a second copy of this sentence is how the delete half and
# the move half would come to name two different commands.
CORRECTION_REMEDY = (
    "Remedy, if this really has to happen: it needs the USER, not a workaround. Run `python "
    "scripts/harness.py request-approval filing_correction --document <path-from-the-project-root> "
    "--destination <where-it-should-land> --reason <why>` -- leave `--destination` out to ask for a "
    "DELETION instead -- and relay the printed question to the user VERBATIM with AskUserQuestion. "
    "Their Freigeben answer mints the approval, and this guard then lets through exactly the "
    "operation it names: the same document, the same version of its bytes, the same destination. "
    "Then run that correction ON A LINE OF ITS OWN (a `cd` in front of it is fine): the approval "
    "covers one correction and not the command line around it, so anything else on the line -- "
    "another program, an operand the shell rewrites, a second document -- refuses the whole call. "
    "The approval stops covering the document as soon as those bytes are no longer at that "
    "position, so ask again if the command did not run.\n")


def writes_the_ledger(command):
    """Does any output redirect in `command` write to a `ledger/*.csv`? — reading every value a
    shell could hand the target (`_compat.shell_readings`), so the POSIX backslash spelling resolves
    too, exactly as the write-scope gate answers the same question for a state path."""
    return any(LEDGER_CSV_RX.search(reading)
               for target in _filing.redirect_targets(command)
               for reading in _compat.shell_readings(target))


def in_a_protected_tray(root, base, token):
    """The repo-relative path this token names, if it lies in a tray of record — else None."""
    relative = _filing.position(root, base, token)
    return relative if any(_filing.under(relative, tray) for tray in PROTECTED_TRAYS) else None


def _landing(destination, is_directory, source):
    """Where the document ENDS UP: the destination, or a file inside it when that names a folder.

    `mv archive/…/x.pdf outbox/` and `mv archive/…/x.pdf outbox/x.pdf` are one operation spelled
    two ways, and the approval names the position the document ends up at. Without this the first
    spelling asked for an approval on `outbox`, which is a folder and not the document — measured
    2026-08-18 in the refusal text of that very command ("moves archive/1-Finanzen/2026/x.pdf to
    outbox"). None stays None: a destination outside the repository has no position to approve.
    """
    if destination is None:
        return None
    if not is_directory:
        return destination
    name = os.path.basename(str(source).replace("\\", "/").rstrip("/"))
    return (destination + "/" + name) if name else destination


def _protected_readings(root, bases, token):
    """Every position inside a tray of record this ONE operand could be meant against."""
    readings = []
    for base in bases:
        relative = in_a_protected_tray(root, base, token)
        if relative and relative not in readings:
            readings.append(relative)
    return readings


def _move_readings(root, move):
    """{source token: [(source, landing, shown), …]} for the documents this move takes out of
    archive/ — every base tried, and source and destination always read against the SAME one."""
    readings, order = {}, []
    for base in move.bases:
        destination, is_directory = _filing.resolve(root, base, move.destination)
        if _filing.under(destination, _filing.ARCHIVE):
            continue
        for source in move.sources:
            relative = _filing.position(root, base, source)
            if not _filing.under(relative, _filing.ARCHIVE):
                continue
            landing = _landing(destination, is_directory or move.destination_is_directory, source)
            reading = (relative, landing, landing or destination or move.destination)
            if source not in readings:
                readings[source] = []
                order.append(source)
            if reading not in readings[source]:
                readings[source].append(reading)
    return [readings[source] for source in order]


class Line(object):
    """What one command line does, as far as THIS guard can place it.

    `deletes` and `moves` are the operations the two rules judge, one entry per document, each
    holding every position that document could be meant at (several bases may be in play, and only
    one of them is the real file — see `read_the_line`). `unplaced` is the first thing on the line
    this guard could NOT place, or None.

    WHY THE THIRD FIELD EXISTS AT ALL, and it is the correction of verifier finding F1. The refusal
    only ever needed the first two: something protected is being destroyed, so refuse. The DOOR
    needs the third, because a user approval names ONE correction and the door decides about the
    whole COMMAND LINE. With "every operation I recognised is approved" as the pass condition, an
    approved move carried through everything the reader did not recognise beside it — measured by
    the verifier as rc 0, where the wall alone answered rc 2, for a `python -c "os.remove(...)"` of
    another archive file, a `tar --remove-files`, a `rm $A`, and `rm inbox/a.pdf ~/archive/x.pdf`
    (F2). None of those is newly seen now; what changed is that they stop the DOOR instead of
    riding through it.
    """

    def __init__(self, deletes, moves, unplaced):
        self.deletes = deletes
        self.moves = moves
        self.unplaced = unplaced


def read_the_line(root, command, bases):
    """The whole command line, invocation by invocation — see `Line`.

    THE WALK IS OVER EVERY INVOCATION, not over the ones a filter kept (`_filing.invocations`).
    Each is placed as exactly one of four things and there is no fifth: a directory change this
    reader could compute; a relocation/copy; a delete; or something else. "Something else" is the
    honest answer for a program that does its own file handling (`python -c`, `tar`), and it is what
    keeps an approval from covering it.

    AN OPERAND HAS TO BE PLACEABLE IN TWO DIFFERENT SENSES, and each caught a case the other did
    not, which is why both are here:

      * its TEXT has to be the path (`_filing.rewritten_by_the_shell`). `rm inbox/a.pdf
        ~/archive/secret.pdf` places the first operand and resolves the second to a position under
        the project -- but the SHELL expands the `~` and deletes a file in the user's home, so the
        position the guard resolved is not the file that goes (F2). Same for a variable, a glob, a
        `%VAR%`;
      * and it has to RESOLVE to a position inside the project. `../archive/x.pdf` and
        `/etc/passwd` are ordinary text that names no place this guard can speak about; each was
        simply dropped, so an approved operand beside them made the line "fully approved".

    THE RAW-TEXT DELETE READING IS THE LAST WORD, per invocation: if `DELETE_RX` fires and the
    resolving reader placed no PROTECTED position in that invocation, the two readings disagree
    about what is being destroyed and the guard believes the one that says something is. That is an
    over-refusal by construction -- `rm outbox/archive-copy.txt` is a perfectly ordinary delete the
    text makes look protected -- and it costs a correction on that line, never a document.

    AN UNPLACEABLE OPERAND CLOSES THE DOOR AND NEVER HIDES AN OPERATION, and this paragraph is here
    because the first cut of it did exactly that: it `continue`d past an invocation carrying one, so
    the operations that invocation DID place never reached the caller and the WALL stopped seeing
    them. `mv archive/fin/a.pdf /tmp/gone.pdf` -- a move that empties the archive to a destination
    outside the project, the plainest case this guard exists for -- went from rc 2 to rc 0, caught by
    `tools/test_hooks.py::test_fs_tripwire_blocks_move_out_of_archive`, a test older than this door.
    So `unplaced` is recorded and the reading CONTINUES: the refusal keeps everything it ever saw,
    and only `open_the_door` consults `unplaced`.
    """
    deletes, moves, unplaced = [], [], None

    def unreadable(reason):
        return reason if unplaced is None else unplaced

    def unplaceable(operands, current):
        """The first operand of this invocation this guard cannot speak about, or None."""
        for operand in operands:
            if _filing.rewritten_by_the_shell(operand):
                return "%s -- the shell rewrites it before the command sees it" % operand
            if not any(_filing.position(root, base, operand) for base in current):
                return "%s -- it names no place inside this project" % operand
        return None

    for text, tokens, current in _filing.invocations(command, bases):
        # A REDIRECT IS PART OF WHAT THE LINE DOES, and it is not an operand of anything: `>` is
        # shell syntax, so the argument readers below cannot see it. `> inbox/b.pdf` TRUNCATES a
        # document of record to nothing, which is the class these trays exist for -- and behind an
        # approved move the whole line answered rc 0 (verifier round 2, R1). A target in a tray is
        # never an approvable OPERATION either: a `filing_correction` binds bytes that exist at a
        # position, and the bytes a redirect will write do not exist when the user is asked. So it
        # closes the door, like anything else this guard cannot place.
        #
        # READ BEFORE THE TOKEN CHECK BELOW, and that ordering is the whole of verifier round 3.
        # `_tokens` cuts an invocation at its first redirect operator, so an invocation whose
        # redirect comes FIRST has no tokens at all -- `> outbox/log.txt rm archive/…/y.pdf` is one
        # tokenless invocation carrying a delete. Skipped before this scan, the line knew of no
        # operation AND of nothing unplaced, so the delete rule was disabled outright: HEAD rc 2,
        # measured rc 0 (V1), and the same shape rode an approved move through the door (V2).
        for target in _filing.redirects_of(text):
            if _filing.rewritten_by_the_shell(target):
                unplaced = unreadable("a redirect target the shell rewrites before use (%s)"
                                      % str(target)[:80])
            elif any(in_a_protected_tray(root, base, target) for base in current):
                unplaced = unreadable(
                    "a redirect that writes into a tray of record (%s) -- no approval can name the "
                    "bytes a redirect has not written yet" % str(target)[:80])
            elif not any(_filing.position(root, base, target) for base in current):
                unplaced = unreadable("a redirect target this guard cannot place (%s)"
                                      % str(target)[:80])
        if not tokens:
            # AN INVOCATION WITH NO COMMAND WORD IS NOW EXACTLY ONE THING: redirects and whitespace.
            # `_tokens` cuts the redirects OUT rather than ending the argument list at them, so
            # anything else would have produced a word -- and the scan above has already judged
            # every one of those redirects. Marking it unplaced on top was measured as pure
            # over-refusal (`… && > outbox/log.txt`, a fully placed redirect outside the trays,
            # became rc 2 with no protection behind the refusal), so it is not done.
            continue
        names_chdir, computed = _filing.directory_change(tokens)
        if names_chdir:
            if not computed:
                unplaced = unreadable("a directory change this guard cannot follow (%s)"
                                      % " ".join(str(token) for token in tokens)[:80])
            continue
        move = _filing.move_of(tokens, current)
        if move is not None:
            operands = list(move.sources) + ([move.destination] if move.destination else [])
            beyond = unplaceable(operands, current)
            if beyond:
                unplaced = unreadable("a copy/move operand this guard cannot place (%s)"
                                      % beyond[:100])
            if _filing.relocating(move) and move.destination:
                moves += _move_readings(root, move)
            continue
        operands = _filing.operands_of(tokens, DELETE_VERBS)
        if operands is not None:
            beyond = unplaceable(operands, current)
            if beyond:
                unplaced = unreadable("a delete operand this guard cannot place (%s)" % beyond[:100])
            placed = [readings for readings in
                      (_protected_readings(root, current, operand) for operand in operands)
                      if readings]
            if DELETE_RX.search(text) and not placed:
                unplaced = unreadable(
                    "a delete that names a tray of record in its text while this guard could place "
                    "no protected operand in it (%s)" % text.strip()[:80])
            deletes += placed
            continue
        unplaced = unreadable("an invocation this guard does not read as a filing operation (%s)"
                              % str(tokens[0])[:80])
    return Line(deletes, moves, unplaced)


def correction_authority(root):
    """(kernel approvals module, {operation key: approval}) for this call — or None. ONE store read.

    THE KERNEL BRIDGE IS IMPORTED HERE AND NOWHERE ELSE IN THIS PROCESS, and that placement is the
    whole reason this guard may ask an approval question at all. `_filing`'s docstring records why
    the bridge stays out of this hook: importing it arms an excepthook that turns any escaping error
    into exit 2, which is right for a fail-closed gate and is NOT this guard's contract —
    uncertainty leaves the command alone. This runs only on a branch that has ALREADY decided to
    refuse, so there the two contracts agree: anything that goes wrong while looking for an approval
    means none was found, and the refusal stands. `disarm()` puts the interpreter's own excepthook
    back before returning.

    ONCE PER CALL, NOT ONCE PER OPERAND, and that is verifier finding F3 rather than an optimisation.
    Opening the state and scanning the approval store per operand made a REFUSAL cost time
    proportional to the line: 8000 documents on one `rm` took 114 s where the wall alone took 0.54 s.
    That was written when a kill at the registration's deadline was believed to be what came next;
    BUG-0062 measured that no registration of this kit names one and none is killed, so what 114 s
    really buys is a session frozen on one command with no sign of why. The store is read once into
    a map here; the door then does dictionary lookups.

    ANY failure is None on purpose — no kernel, no state directory, an unreadable store. "I could
    not check" and "there is no approval" have to be one answer in a guard, and it is the one that
    keeps the documents.
    """
    try:
        import _kernel
        try:
            if not os.path.isdir(_kernel.state_dir(root)):
                return None
            approvals = _kernel.kernel_module("approvals", root)
            hashing = _kernel.kernel_module("hashing", root)
            live = approvals.live_correction_approvals(_kernel.open_state(root))
            return approvals, hashing, live
        finally:
            _kernel.disarm()
    except BaseException:       # noqa: BLE001 — see the contract above
        return None


def open_the_door(root, line):
    """(corrections let through, why not, which operation) — ONE decision about the WHOLE line.

    Four things have to hold, and the first two are about the line rather than about any operation:
    the guard placed everything on it (`Line.unplaced`), it asks for no more corrections than
    `CORRECTION_CAP`, a live user approval exists for every operation, and each approval names that
    operation exactly — the document, the version of it that lies there now, and the destination or
    its absence.

    THE CAP IS A REFUSAL AND NOT A TRUNCATION. Above it the door does not open at all, so the wall
    answers as it always did; what the cap buys is that it answers FAST. It is a bound on the work a
    PreToolUse hook may do while deciding, and the reason is the one `correction_authority` gives:
    past the provider's deadline a refusal becomes a pass.

    THE FIRST UNCOVERED OPERATION ENDS IT, and it is also the one the refusal NAMES. Every
    operation costs a file read (the version hash), so carrying on after the answer is settled is
    time spent on a call that is already refused — and naming the FIRST operation instead of the
    uncovered one sent a role back to the user for an approval it already held
    (`tools/test_hooks.py::test_a_refusal_names_the_document_that_is_missing_its_approval`).

    AN EMPTY ANSWER IS "THE DOOR DID NOT OPEN", NEVER "THE DOOR OPENED FOR NOTHING". This function
    is only ever asked when one of the two rules has fired, so a line it can name no operation on is
    a line whose two readings disagree — the raw-text delete reading saw something the resolving one
    could not place. Returning `[]` there made `if honoured is None` in `main` fall through to the
    ALLOW, which is verifier round 3's V1 in its second half.

    IT IS THE FIRST CHECK AND IT IS MEASURED DIRECTLY, because on a real command line the `unplaced`
    branch below now answers every case that reaches it first: after `_filing._tokens` stopped
    ending the argument list at a redirect, no line was left that has no operation AND nothing
    unplaced. So the branch is kept for what it MEANS rather than for a chain that reaches it, and
    `tools/test_hooks.py::test_the_door_answers_an_empty_line_as_closed_not_as_open` asks this
    function for that shape outright instead of pretending a command line produces it.
    """
    operations = [(readings, False) for readings in line.deletes] \
        + [(readings, True) for readings in line.moves]
    if not operations:
        return None, ("this guard could place no operation on this command line at all, so there is "
                      "nothing a user approval could cover — its own two readings of the line "
                      "disagree about what is being destroyed, and it believes the one that says "
                      "something is"), None
    if line.unplaced:
        return None, ("this command line also does something this guard could not place: %s. An "
                      "approval names ONE correction and cannot cover what nobody can read, so "
                      "nothing on this line is let through. Run the approved correction on a line "
                      "of its own." % line.unplaced), None
    if len(operations) > CORRECTION_CAP:
        return None, ("this command line would correct %d documents at once, and the door opens for "
                      "at most %d — a gate that is still deciding when its deadline passes is read "
                      "as a gate that allowed the call, so the work it may do is bounded. Ask for "
                      "the corrections in smaller batches."
                      % (len(operations), CORRECTION_CAP)), None
    authority = correction_authority(root)
    if authority is None:
        return None, ("no user approval could be looked up for this project at all (no state "
                      "directory, or it could not be read)"), None
    approvals, hashing, live = authority
    honoured, versions = [], {}
    for readings, is_move in operations:
        found = None
        for reading in readings:
            document, target = (reading[0], reading[1]) if is_move else (reading, "")
            if is_move and not target:
                continue      # a destination outside the project has no position to approve
            if document not in versions:
                versions[document] = hashing.document_content_hash(
                    os.path.join(root, document)) or ""
            if not versions[document]:
                continue      # bytes that cannot be read cannot be the bytes anybody approved
            approval = live.get(approvals.correction_operation_key(
                document, target, versions[document]))
            if approval is not None:
                found = (approval, document, target)
                break
        if found is None:
            offender = (readings[0][0], readings[0][2]) if is_move else (readings[0], "")
            return None, ("%s carries no live user approval for exactly this correction"
                          % offender[0]), offender
        honoured.append(found)
    return honoured, None, None


def record_corrections(command, honoured):
    """Journal the corrections this call was let through on — see the module docstring's last
    paragraph for what that record does and does not claim.

    CALLED ONCE, AFTER EVERY CHECK HAS PASSED, and that is not tidiness. A command line can delete
    one document and move another out, and the two used to be judged in sequence: writing the note
    inside the first branch put "allowed under APR-000n" into the journal for a call the SECOND
    branch then refused. A record of a passage that never happened is worse than no record
    (`tools/test_hooks.py::test_a_refused_call_leaves_no_note_claiming_a_correction_was_let_through`).

    AND NOTHING IS WRITTEN FOR AN EMPTY LIST, which is the same rule one shape further down. With
    no correction honoured the sentence came out as "allowed under user approval : " -- an empty id
    list and an empty operation list, a claim of a passage under an approval that does not exist
    (verifier round 3, V4). The caller no longer reaches here with an empty list; this is the second
    lock, because the first one has now been picked twice
    (`tools/test_hooks.py::test_a_journal_line_never_claims_a_passage_under_no_approval_at_all`).
    """
    if not honoured:
        return
    _audit.record_event(
        "guard_fs_tripwire", "correction-allowed",
        "allowed under user approval %s: %s | %s"
        % (", ".join(str((approval.get("id") or "?")) for approval, _d, _t in honoured),
           "; ".join("%s -> %s" % (document, target or "DELETED")
                     for _a, document, target in honoured),
           command[:120]))


def main():
    # BOUNDED read (spec II.4). A raw `json.load(sys.stdin)` will happily buffer a
    # payload of any size, and an oversized one is the shape that turns a hook into
    # a memory event rather than a decision. `_compat.load` caps it at STDIN_LIMIT
    # and exits 2, because a gate that cannot read its input has not judged it.
    data = _compat.load()
    if data.get("tool_name") not in ("Bash", "PowerShell"):
        sys.exit(0)
    cmd = str((data.get("tool_input") or {}).get("command") or "")
    cwd = str(data.get("cwd") or "")
    root = _root.find_repo_root(cwd)
    bases = _filing.reading_bases(root, cwd)
    if writes_the_ledger(cmd) and not LEDGER_ADD_RX.search(cmd):
        _audit.record("guard_fs_tripwire", "shell redirect into ledger: %s" % cmd[:120])
        _compat.stop(
            "[team-kit guard] A blind shell redirect into ledger/*.csv is BLOCKED — `>>` writes "
            "whatever it is handed, with no schema, no arithmetic check and no way to tell a row "
            "from a fragment. Editing the ledger IS allowed (user decision V2 I.3/1): use Edit, or "
            "`python scripts/ledger_add.py ...` for a new entry. Either way the whole file is "
            "re-validated afterwards and a failure marks the ledger invalid.\n", "PreToolUse")
    # ONE READING OF THE LINE, ONE DECISION ABOUT IT. The two rules keep their own refusal texts --
    # they refuse different things and a role has to be told which -- but whether the DOOR opens is
    # a question about the whole command line and is asked once (`open_the_door`). Asking it per
    # rule is what let an approved delete carry an unapproved move through, and the journal note
    # then claimed a passage the second rule refused.
    line = read_the_line(root, cmd, bases)
    breaks_the_delete_rule = bool(DELETE_RX.search(cmd) or line.deletes)
    if not breaks_the_delete_rule and not line.moves:
        sys.exit(0)
    honoured, refused, offender = open_the_door(root, line)
    # `not honoured`, NOT `honoured is None`. An empty list is a door that opened for nothing, and
    # `[] is not None` walked straight past this branch into the ALLOW while one of the two rules had
    # fired -- verifier round 3, V1: a leading redirect made the line tokenless, so no operation was
    # placed, and `rm archive/…/y.pdf` behind it went from rc 2 to rc 0. `open_the_door` no longer
    # RETURNS that shape, so this is the second lock on one door and no test can tell it from the
    # first -- it is here because the first lock has now been picked twice, not because anything
    # measures it.
    if not honoured:
        if breaks_the_delete_rule:
            _audit.record("guard_fs_tripwire",
                          "delete on inbox/archive (%s): %s"
                          % (refused, cmd[:120]))
            _compat.stop(
                "[team-kit guard] Deleting under inbox/ or archive/ is BLOCKED — business documents "
                "are moved (with a filing/migration manifest), never deleted. Duplicates get a "
                "_dupNN suffix and a flag.\nWhy this call is not covered by a user approval: %s.\n"
                % refused + CORRECTION_REMEDY, "PreToolUse")
        # the move the refusal NAMES is the one that is missing its approval; a refusal about the
        # line as a whole (unplaced, cap) has no such operation and names the first move instead
        source, shown = offender if (offender and offender[1]) \
            else (line.moves[0][0][0], line.moves[0][0][2])
        _audit.record("guard_fs_tripwire",
                      "move out of archive (%s -> %s): %s" % (source, shown, cmd[:120]))
        _compat.stop(
            "[team-kit guard] Moving files OUT of archive/ is BLOCKED — the archive is the "
            "system of record. This command moves %s to %s, which is outside it. "
            "Reorganisation runs as a user-approved migration PROC (dry-run -> OK -> move + "
            "manifest); ask the manager/user instead of working around this. A move that STAYS "
            "inside archive/ is not this rule and is not blocked, whichever way it is spelled.\n"
            "Why this call is not covered by a user approval: %s.\n"
            % (source, shown, refused) + CORRECTION_REMEDY, "PreToolUse")
    record_corrections(cmd, honoured)
    sys.exit(0)


if __name__ == "__main__":
    main()

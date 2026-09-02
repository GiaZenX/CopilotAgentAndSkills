#!/usr/bin/env python3
"""
Shared helper: the second pair of eyes on a LEDGER ROW — which rows are still unread, which readings
are about them, and which rows nobody has to read again. `gate_second_booking` is the only caller;
it is a module of its own for `_readings`' reason, that a store's reader and its writer must not
spell its shape twice.

THE MEASURED ERROR THIS CATCHES, and it is one this kit already produced (BUG-0072, live 2026-08-29
in the user's own office project): `scripts/einvoice_extract.py` returned 14.28 where the invoice
said 214.20 net. Nothing in the pipeline would have stopped it — the bookkeeper's own arithmetic
cross-check did, by hand. The layer that exists, `ledger_add.validate_row`'s
`net x (1 + vat) = gross`, is loud and it is not enough: it judges a triple against ITSELF, so a
triple that reconciles and came off the WRONG DOCUMENT, a transposition that still adds up, and a
category read off the wrong line all pass it. Those are the three the user named, and the only thing
that separates them from a correct booking is a reader who went back to the paper.

WHAT IS ENFORCED AND WHAT IS NOT, in the shape FR-0035 settled for filing and for the same reason:
PROVENANCE is measurable and blindness is not. What this holds is that as many DIFFERENT runs as the
row's category asks for each recorded, in their own `booking_reading` record, the figures they read
off that document — and that the row agrees with every one of them. What it cannot see is whether
the second run had already been shown the first record: nothing in the hook layer observes a Read,
and the records lie in `staging/` where every role may look. `_readings` carries the whole of that
argument and the one unmeasured assumption behind the run identity.

WHICH ROWS ARE JUDGED, and this is the migration answer rather than a flag: a row whose exact CSV
fields already stand in the file as `HEAD` has it. Those rows were booked before this layer existed
or were let through by it; either way they are in the version history that this kit's own
bookkeeping doctrine calls the audit trail (`scripts/ledger_add.py`'s header: "git history plus the
Evidence trail is what makes it auditable"). Nothing is enumerated and no baseline file is written:
the baseline IS `HEAD`, and what moves `HEAD` is judged exactly as far as
`gate_ledger_valid.requires_a_sound_ledger` recognises a commit — no further. A mechanism that
refused every row a real ledger already carries would be worse than none, which is what FR-0065 says
in as many words.

THAT REACH IS A MEASURED LIMIT AND NOT A GUARANTEE, and this paragraph used to claim the opposite
("no snapshot can be minted"). It is `H11`'s class and `gate_write_scope` names it about itself: a
command line that starts a SCRIPT is judged on the script's NAME, not on what the script does. So
`printf '...git commit -m books' > release.sh` followed by `bash release.sh` puts an unread row into
`HEAD` at rc 0 — grandfathered from then on — and the same vehicle appends a second "run" to the
attestation store. Both chains are measured in `H99` (`docs/POST_V2_WISHLIST.md`); every DIRECT
spelling of either write is rc 2.

WHERE THAT LEAVES A HOLE, named because it is not closed: when `git` cannot answer at all — not
installed, or a project that is not a work tree — this layer cannot tell an old row from a new one
and it STANDS DOWN for that ledger rather than refusing every row in it. Refusing would deadlock the
one project that most needs the way out (the first commit is what would grandfather the rows, and
the refusal would be on the commit), which is the failure `gate_ledger_valid`'s own header records
as "a corrupt marker with no ledger present deadlocked the repo". `H89` in
`docs/POST_V2_WISHLIST.md` carries the measurement.
`test_a_ledger_git_cannot_answer_for_stands_the_booking_gate_down_and_says_so` measures the
stand-down; `test_a_row_already_in_head_is_not_booked_again` measures the grandfathering.
"""
import csv
import io
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import _compat  # noqa: E402
import _readings  # noqa: E402

# THE CONTRACT. Its per-entry keys are NOT listed here — `_readings.contract_of` reads them off
# `kernel/schemas/booking_reading.yaml`, and what this module adds is a meaning for exactly one of
# them (`SOURCE`, the document) plus the rule that every OTHER declared key is the name of a ledger
# COLUMN whose value the row has to match. That is what makes the comparison a derivation: a column
# the schema starts declaring joins the comparison the day it ships.
SCHEMA = "booking_reading"
SOURCE = "source"
STORE_DIR = ".books"
BOOKING = _readings.Contract(SCHEMA, SOURCE, STORE_DIR, (SOURCE,))

# The columns of a ledger row a reader is NOT asked for, each with the reason it is not a reading.
# THIS IS THE OTHER HALF OF THE SCHEMA and the only place the exemptions are stated;
# `tools/test_hooks.py::test_a_booking_reading_asks_for_exactly_the_ledger_columns_a_document_carries`
# holds the two together in BOTH directions, against the shipped `scripts/ledger_add.py`'s own
# `COLUMNS` — a new ledger column that is neither declared in the schema nor exempted here turns it
# red on the day it ships, and so does an exemption for a column the schema requires anyway.
NOT_READ_OFF_THE_DOCUMENT = {
    "id": "assigned by the script when the row is written, so it does not exist when the document "
          "is read",
    "payment_date": "a bank fact (Zufluss/Abfluss), not something the invoice states",
    "invoice_no": "legitimately EMPTY on a receipt, and a per-entry key this reader tests for a "
                  "value would drop such a reading entirely rather than compare it; a duplicate "
                  "invoice number is already `ledger_add.validate_cross`'s finding",
    "reverses": "a relation between two bookings, not a property of the paper",
    "note": "the bookkeeper's own prose",
}
# The keys compared as NUMBERS rather than as text, because the ledger stores them canonicalised to
# two decimals (`ledger_add` writes `"%.2f"`) while a reader writes what the document says: `214.2`
# and `214.20` are one answer and a text comparison would call them a disagreement. Every other key
# compares as TEXT, case included — `invoice_no`-shaped values ("007") must not collapse into
# numbers, which is why this is a named set and not "whatever parses as a number".
# `test_the_ledger_canonicalises_exactly_the_columns_the_booking_comparison_reads_as_numbers`
# measures both halves against the shipped script.
AMOUNT_KEYS = ("net", "vat_rate", "gross")
# The tolerance the ledger's own arithmetic check uses (`ledger_add.validate_row`: `> 0.011`). Named
# once, here, because a second number would be a second definition of "the same amount".
AMOUNT_TOLERANCE = 0.011

# THE CAP FOR THE WHOLE RUN, and it is this process's own promise -- nothing outside it bounds this
# gate, because the registration deliberately names no `timeout` (a window is a kill window, and a
# killed gate is a silent ALLOW). `gate_ledger_valid` carries the same constant for the same reason
# and its header argues it; what is different HERE is the arithmetic that fixes the number.
#
# WHY IT IS SMALLER THAN THE NEIGHBOUR'S: the two gates run SEQUENTIALLY IN ONE PROCESS (`_gate.py`
# chains them), so their budgets ADD UP against the one deadline the hooks give themselves
# (`_compat.HOOK_DEADLINE_SECONDS`), and the sum is what the host sees. The arithmetic is NOT
# spelled here -- it used to be, and it carried a copy of a number that belongs to another file:
# `tools/test_hooks_v2.py::test_the_two_ledger_gates_budgets_together_fit_inside_the_hook_deadline`
# reads all three constants off the modules instead, so raising either budget past the sum turns it
# red rather than leaving a comment that stopped being true.
#
# WHAT IT IS AGAINST, measured as the shipped hook process: the row/reading join is LINEAR IN BOTH,
# and this module's own limits multiply past any deadline -- 8 MB of ledger is about 55 000 rows and
# `_readings.MAX_FILES` allows 400 reading files. `by_source` and `_policy` took the ordinary shape
# (many documents) from 1.53 s to 0.56 s at 1920 rows x 399 readings; what they cannot help is the
# WORST case, every reading about ONE document, which still costs 2.0 ms per row on this host
# (0.41 s at 120 rows, 1.41 s at 480, 3.82 s at 1920) and more on a slower one. The kill line is
# therefore reachable by a large enough uncommitted batch, and being killed is the one outcome this
# hook cannot turn into a refusal -- which is what the budget is, and not a performance target.
TOTAL_BUDGET = 15
LEDGER_DIR = "ledger"
# The user's vocabulary document, and it lives in the STATE directory and not at the project root —
# `_state_dir` is what composes the path, because a hook that spelled `project_memory/` itself is one
# more copy of a kernel constant. Measured while it did: the release lever read as absent for every
# category, so a released one still asked for two readings.
MASTER_DATA = "master_data.yaml"
CATEGORIES = "categories"
CATEGORY = "category"
KEY = "key"
# How long `git` gets to answer. It is asked twice per project and once per ledger file, all of them
# reads of an object store; a git that has not answered in this long is one that cannot answer, and
# the stand-down above is what that means.
GIT_TIMEOUT = 10
# The bound on a ledger file this reader will open. `gate_ledger_valid` runs the project's validator
# over the same files under its own budget; this one only has to decompose them into rows, and a CSV
# past this is one no office ledger has — it is read up to nothing and reported as unjudged.
MAX_LEDGER_BYTES = 8 * 1024 * 1024


class Reading(object):
    """One run's reading of ONE document into ledger fields, with the run the attestation names."""

    def __init__(self, record, run, values, source_digest=""):
        self.record = record          # state-relative path of the file it was read from
        self.run = run
        self.values = values          # {key: what this reader read}, the schema's keys
        self.source_digest = source_digest
        self.source = _readings.as_landing(values.get(SOURCE))

    def named(self, keys):
        """The one line this reading contributes to a refusal the USER has to decide."""
        said = ", ".join(
            "%s %s" % (key, self.values.get(key) if _readings.stated(self.values.get(key)) else "?")
            for key in keys if key != SOURCE)
        return "%s: %s (run %s, %s)" % (self.source or "?", said, self.run, self.record)


def readings(state, field, keys):
    """Every ATTESTED booking reading in this project.

    A staged record whose current bytes carry no attestation yields nothing, for `_readings.readings`'
    reason: an unattested record is a file somebody wrote, and nothing here can say which run wrote
    it, which is the one thing the whole check rests on.
    """
    known = _readings.attestations(state, BOOKING)
    found = []
    for path, sha, entries in _readings.staged_records(state, field, keys):
        run, sources = known.get((path, sha or ""), ("", {}))
        if not run:
            continue
        for entry in entries:
            source = _readings.as_landing(entry.get(SOURCE))
            found.append(Reading(path, run, dict(entry), str(sources.get(source) or "")))
    return found


def _number(text):
    """The value as a finite number, or None. `ledger_add.read_amount`'s answer, minus its messages.

    DOT DECIMALS ONLY, and deliberately no comma rescue: the ledger refuses a comma decimal outright
    (its reports parse with a bare `float()`), so accepting one here would let a reading agree with a
    row it could never have produced. A reading nobody can parse falls through to the text
    comparison, which disagrees and puts both values in front of the user.
    """
    value = str(text if text is not None else "").strip()
    if not value or "," in value:
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    return number if number == number and abs(number) != float("inf") else None


def disagreements(reading, row, keys):
    """[(key, what the row says, what this reader read)] — every compared key the two differ on.

    NAMED RATHER THAN COUNTED, because the refusal this feeds is the one the USER decides: "two
    readings disagree with the row" sends a bookkeeper back to the paper with no idea what to look
    at, while "net: row 14.28, read 214.20" is BUG-0072 on one line. `agrees` is the predicate and
    this is its explanation; both walk the same keys through the same comparison, so a key one of
    them judges and the other does not cannot exist.
    """
    return [(key, row.get(key), reading.values.get(key))
            for key in keys
            if key != SOURCE and not agrees(reading, row, (key,))]


def agrees(reading, row, keys):
    """Does this reading say the same thing as this row, for every compared key?

    `SOURCE` is not compared here: it is the JOIN, and a reading about another document is not a
    disagreeing reading, it is a reading about something else.
    """
    for key in keys:
        if key == SOURCE:
            continue
        mine, theirs = reading.values.get(key), row.get(key)
        if key in AMOUNT_KEYS:
            left, right = _number(mine), _number(theirs)
            if left is None or right is None or abs(left - right) > AMOUNT_TOLERANCE:
                return False
        elif str(mine if mine is not None else "").strip() != \
                str(theirs if theirs is not None else "").strip():
            return False
    return True


_POLICY_CACHE = {}


def _policy(root):
    """{category key: its entry} from `master_data.yaml`, parsed ONCE per process.

    It used to be read and parsed per ROW, inside a gate that walks every uncommitted row of every
    ledger file -- a YAML parse per row, in a blocking hook, for a file that cannot change while the
    call is being judged. `TOTAL_BUDGET` is what bounds the walk; this is what keeps the ordinary
    case far away from it.

    NEVER RAISES: an unreadable or absent file yields an empty policy, which is the strict side
    (`readings_required(None)` asks for two). Standing down over a file that will not parse would
    make deleting it the way out.
    """
    if root in _POLICY_CACHE:
        return _POLICY_CACHE[root]
    found = {}
    try:
        import yaml  # type: ignore[import-untyped]
        with open(os.path.join(_state_dir(root), MASTER_DATA),
                  encoding="utf-8-sig") as handle:
            document = yaml.safe_load(handle) or {}
        for side in (document.get(CATEGORIES) or {}).values():
            for one in side or []:
                key = str((one or {}).get(KEY) or "").strip() if isinstance(one, dict) else ""
                if key:
                    found[key] = one
    except BaseException:  # noqa: BLE001 -- see the contract above
        found = {}
    _POLICY_CACHE[root] = found
    return found


def required_for(root, category):
    """How many independent readings a row of this CATEGORY needs -- the USER's lever, not this file's.

    Read off `master_data.yaml`, which is the document the user owns for the ledger's vocabulary,
    exactly as the filing plan is the one they own for the archive. The lever is spelled
    `second_reading` there too, and what it means is `_readings.readings_required`'s answer and not a
    second one: `false` asks for ONE reading and never for none, and every other value -- absent,
    `true`, a word, a list -- asks for two. A category the file does not carry (one the bookkeeper
    proposed and nobody has approved yet) is not found here and therefore asks for two.
    """
    return _readings.readings_required(_policy(root).get(str(category or "").strip()))


def ledger_rows(path):
    """([(line label, row dict, signature)], reason it could not be read).

    The SIGNATURE is the row's own fields in the file's own header order, which is what makes "this
    row is already in HEAD" a comparison of content rather than of bytes: a CRLF checkout, a
    re-ordered file and a re-saved file all keep it, and changing any value in the row loses it.
    """
    try:
        if os.path.getsize(path) > MAX_LEDGER_BYTES:
            return [], "larger than %d bytes, so it was not decomposed into rows" % MAX_LEDGER_BYTES
        with open(path, encoding="utf-8-sig", newline="") as handle:
            return _rows_from(handle.read()), ""
    except OSError as exc:
        return [], "could not be read (%s)" % type(exc).__name__


def _rows_from(text):
    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration:
        return []
    found = []
    for number, fields in enumerate(reader, start=2):
        if not any(field.strip() for field in fields):
            continue
        row = {name: (fields[index] if index < len(fields) else "")
               for index, name in enumerate(header)}
        found.append(("line %d (%s)" % (number, (row.get("id") or "").strip() or "no id"),
                      row, "\x1f".join(fields)))
    return found


_GIT_CACHE = {}


def _git(root, argv):
    """(returncode, stdout) for one git read, or None when git could not be asked at all."""
    try:
        result = _compat.run_captured(["git"] + argv, cwd=root, timeout=GIT_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return None
    return result.returncode, result.stdout or ""


def committed_signatures(root, rel):
    """The signatures of the rows this file has in `HEAD`, or None when git cannot answer.

    None and an EMPTY SET are two different answers and the caller treats them so: an empty set is
    "git looked and this file has no rows there", which makes every row in the working tree a new
    booking — a fresh project's first ledger, and the case where the layer has to bite. None is "git
    could not be asked", which is the stand-down the module header names as `H89`.
    """
    inside = _GIT_CACHE.get(root)
    if inside is None:
        answer = _git(root, ["rev-parse", "--is-inside-work-tree"])
        inside = bool(answer and answer[0] == 0 and answer[1].strip() == "true")
        _GIT_CACHE[root] = inside
    if not inside:
        return None
    # `HEAD:./<path>` and not `HEAD:<path>`: the second is resolved against the git TOPLEVEL, and an
    # office project need not be at it. The `./` form is resolved against the working directory,
    # which is the project root this reader was handed.
    answer = _git(root, ["show", "HEAD:./" + rel])
    if answer is None:
        return None
    if answer[0] != 0:
        return set()   # no HEAD yet, or this file is not in it: every row is a new booking
    return {signature for _label, _row, signature in _rows_from(answer[1])}


def by_source(found):
    """{document: [reading, ...]} — the join side, built ONCE instead of walked per row.

    The scan it replaces was linear in BOTH the rows and the readings, and this module's own limits
    multiply that past any deadline (see `TOTAL_BUDGET`). Indexing does not make the WORST case
    cheap — a project whose readings are all about one document still compares every one of them
    against every row of that document, which is the case the budget is for — but it removes the
    cost a project pays for having a lot of OTHER documents, which is the ordinary shape.
    """
    index = {}
    for one in found:
        if one.source:
            index.setdefault(one.source, []).append(one)
    return index


def _unread(root, rows, found, keys, deadline=None):
    """([(label, why, [readings about this document], compared keys)], rows never looked at).

    THE JOIN IS THE DOCUMENT and the test is AGREEMENT, in that order, because the two produce
    different sentences: a row nobody read at all sends the bookkeeper to the paper, a row two runs
    read differently sends the USER a decision between two answers.

    `deadline` is a `time.monotonic()` value this walk stops at. What is LEFT is returned rather than
    dropped: "we did not get to look" is not "it is fine", and the caller turns it into a refusal.
    """
    findings, digests, index = [], {}, by_source(found)
    for position, (label, row, _signature) in enumerate(rows):
        if deadline is not None and time.monotonic() > deadline:
            return findings, [one[0] for one in rows[position:]]
        source = _readings.as_landing(row.get(SOURCE))
        needed = required_for(root, row.get(CATEGORY))
        about = index.get(source, []) if source else []
        bound = [one for one in about
                 if one.source_digest
                 and one.source_digest == _document_digest(root, one.source, digests)]
        agreeing = [one for one in bound if agrees(one, row, keys)]
        runs = {one.run for one in agreeing}
        if len(runs) >= needed:
            continue
        if not about:
            why = ("no `%s` record names %s, so nobody has read this document into these figures "
                   "but the run that booked it" % (SCHEMA, source or "any document"))
        elif not bound:
            why = ("%d reading(s) name %s and none of them is bound to the document as it lies now "
                   "— when each was attested the document was not there to read, or it has been "
                   "replaced since" % (len(about), source))
        elif not agreeing:
            differs = ", ".join(
                "%s (row %s, read %s)" % (key, theirs if theirs not in (None, "") else "-",
                                          mine if mine not in (None, "") else "-")
                for key, theirs, mine in disagreements(bound[0], row, keys))
            why = ("%d attested reading(s) name %s and NONE of them says what this row says — a "
                   "DISAGREEMENT about the content, not a missing reading. The row and the first "
                   "reading differ on: %s" % (len(bound), source, differs or "nothing this reader "
                                              "can name, which is a defect in this gate"))
        else:
            why = ("%s is booked on %d independent reading(s) and needs %d (the attestations put "
                   "them on: %s)" % (source, len(runs), needed, ", ".join(sorted(runs)) or "-"))
        findings.append((label, why, bound or about, keys))
    return findings, []


def _document_digest(root, source, seen):
    """sha256 of the document a reading is about, as it lies now — memoised within one call.

    The same reader and the same bound the attestation used, so "the document has not changed" is one
    comparison and not two answers. A drop of twenty readings about one invoice must not hash it
    twenty times inside a blocking gate.
    """
    if not source:
        return ""
    if source not in seen:
        seen[source] = _readings.digest(os.path.join(root, source.replace("/", os.sep)),
                                        _readings.MAX_DOCUMENT_BYTES) or ""
    return seen[source]


def ledger_files(root):
    """Every CSV under `ledger/`. `gate_ledger_valid._ledger_csvs_in` is the reader, not a copy of it:
    which files are this project's books must not be able to mean two things on the two sides of the
    wall, and that module's own header carries why it lists the directory instead of globbing it."""
    import gate_ledger_valid  # noqa: PLC0415 — imported here so this module stays importable alone
    return gate_ledger_valid._ledger_csvs_in(root)


def unread_rows(root, kernel_module):
    """(rows not read enough, files that could not be judged, files this layer stood down for).

    THREE ANSWERS AND NOT TWO, because the third one must not refuse and the second one must. A file
    the reader could not decompose, and a project whose reading contract is unreachable, are
    infrastructure faults over money data: they leave "we did not look" indistinguishable from "it is
    fine", so they are refusals with their own sentence — the same call `judge()` makes one gate
    over. A ledger `git` cannot be asked about is the DIFFERENT case: this layer's whole reach is
    "rows that are not yet in HEAD", so without git there is no question to answer, only a wall
    across every commit — including the commit that would have grandfathered the rows. That one
    stands down and is recorded, and it is `H89` in `docs/POST_V2_WISHLIST.md`.
    """
    field, keys = _readings.contract_of(kernel_module, BOOKING)
    if not field:
        return {}, {"": "the %s contract could not be read, so no reading can be recognised at all"
                        % SCHEMA}, {}
    found = readings(_state_dir(root), field, keys)
    verdicts, unjudged, stood_down = {}, {}, {}
    deadline = time.monotonic() + TOTAL_BUDGET
    for absolute in ledger_files(root):
        if time.monotonic() > deadline:
            unjudged[os.path.relpath(absolute, root).replace("\\", "/")] = _spent()
            continue
        rel = os.path.relpath(absolute, root).replace("\\", "/")
        rows, reason = ledger_rows(absolute)
        if reason:
            unjudged[rel] = reason
            continue
        committed = committed_signatures(root, rel)
        if committed is None:
            stood_down[rel] = ("`git` could not be asked which of these rows are already committed, "
                               "so a row booked before this rule existed cannot be told from one "
                               "booked now — nothing in this file was judged")
            continue
        fresh = [one for one in rows if one[2] not in committed]
        findings, unreached = _unread(root, fresh, found, keys, deadline)
        if findings:
            verdicts[rel] = findings
        if unreached:
            unjudged[rel] = "%s %d of its %d uncommitted row(s) were never looked at (from %s on)" % (
                _spent(), len(unreached), len(fresh), unreached[0])
    return verdicts, unjudged, stood_down


def _spent():
    """The one sentence a budget refusal is built from. Named once because two callers say it."""
    return ("the %d s this check gives itself for the WHOLE ledger ran out, so" % TOTAL_BUDGET)


def _state_dir(root):
    import _kernel  # noqa: PLC0415 — see `ledger_files`
    return _kernel.state_dir(root)

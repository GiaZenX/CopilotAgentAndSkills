#!/usr/bin/env python3
"""
Shared helper: the independent READINGS a decision is judged against, and who the PROVIDER says
wrote each one. FOUR hooks use it, in two pairs — `record_filing_reading`/`gate_second_reading` for
the FILING of a document (FR-0035), `record_booking_reading`/`gate_second_booking` for the BOOKING
of a ledger row (FR-0065) — and it exists as one module because a store whose writer and reader
spell its shape separately is the drift `_filing` was split out to prevent. What differs between the
two pairs is named by a `Contract` and nothing else; the semantics of the filing keys stay here,
the semantics of the booking keys live in `_bookings`.

WHAT "INDEPENDENT" MEANS HERE, stated as the property that is measured and not as the one that
would be nice. A reading counts as a reading only when an attestation names the RUN that wrote those
exact bytes AND what the document it is about looked like then; readings are independent of each
other when their attestations name DIFFERENT runs (how many a filing needs is the plan's answer, not
this module's — `gate_second_reading.readings_required`). The run comes from `agent_id` in the hook
payload — the field the PROVIDER fills to identify
a spawn instance (`_compat._CALLER_FIELDS`), so it is not something the writing agent states about
itself; what would let an agent state it anyway is writing the store, and that is a separate
question with its own paragraph below. The session instance is not a spawn and carries none, so it
is ONE run under `SESSION_RUN`: a lead that writes both records writes them as one run and is
refused.

WHAT THIS CANNOT SEE, and the refusal texts say the same thing rather than a shorter version of it:
whether the second run READ the first record before answering. Nothing in the hook layer observes a
Read, the record lies in `staging/` where every role may look, and the attestation store itself is
readable. So what is enforced is PROVENANCE — two runs each recorded an answer, and the answers
agree — not blindness. `test_two_readings_from_one_run_are_not_two_readings` is what holds the
provenance half; nothing holds the blindness half, because nothing builds it.

THE ONE UNMEASURED ASSUMPTION, named with its direction: `tools/provider_observations.json` ->
`agent_identity` records that a subagent's `agent_id` is the same value across that subagent's own
calls; it does NOT record whether two spawns of the same role get two different ids. If a provider
reused one id across two spawns, two genuine readings would read as one run and be REFUSED — the
over-refusal direction. The dangerous direction needs one run to be handed two ids, which is the
opposite of what was measured.

WHERE THE STORE LIVES AND WHY THERE. `project_memory/.filing/readings.jsonl` — inside the canonical
state directory and outside `staging/`, which is exactly the area `gate_write_scope` refuses every
tool write to and every write-capable shell line that names it. That is what makes an attestation
something an agent cannot mint for itself; it is the same protection `kit_state.json` has and it
has the same named limit — a shell line that names the path NOWHERE, because a SCRIPT it starts
does the writing, is refused by nothing here (`H11`). A GLOB is not that case and was named as
one for a round: measured rc 2 through the registered chain. `test_an_agent_cannot_write_the_attestation_store_through_the_registered_chain`
measures the covered half.
"""
import hashlib
import json
import os
import time

# The contract's name, and the three per-entry keys this module gives a MEANING to. The list field
# is not spelled here — `contract()` reads it off the schema — but these three are, and that is not
# an oversight: no schema can say which key is "the place the document goes", so a reader that
# derived them from the file would be guessing at semantics it needs to be certain about. What
# `contract()` does instead is REFUSE to answer unless the schema declares all three as required
# per-entry keys, so the two statements cannot drift apart without the gate falling closed.
SCHEMA = "filing_reading"
SOURCE = "source"
DESTINATION = "destination"
DOCUMENT_CLASS = "document_class"
READ_KEYS = (SOURCE, DESTINATION, DOCUMENT_CLASS)
STORE_DIR = ".filing"
STORE_NAME = "readings.jsonl"
STAGING = "staging"


class Contract(object):
    """One KIND of reading: the schema that declares its shape, the key that names the DOCUMENT it
    is about, and the directory its attestations live in.

    IT EXISTS BECAUSE THERE ARE TWO OF THEM AND NOT BECAUSE THERE MIGHT BE. FR-0035 built the
    four-eyes rule for FILING; FR-0065 asked for the same rule on BOOKING, whose figures end at the
    Finanzamt. Everything below the semantics — recognising a staged record, binding it to a run and
    to the document's bytes, first-line-wins in the store — is the same question twice, and a second
    copy of it is the drift this module was split out of two hooks to prevent.

    `read_keys` EMPTY means "whatever the schema declares as `item_required`". That is the booking
    contract's answer: there the declared keys ARE the comparison, so a tuple here would be a second
    statement of the schema. The filing contract names its three, for the reason directly above.
    """

    def __init__(self, schema, source_key, store_dir, read_keys=()):
        self.schema = schema
        self.source_key = source_key
        self.store_dir = store_dir
        self.read_keys = tuple(read_keys)


FILING = Contract(SCHEMA, SOURCE, STORE_DIR, READ_KEYS)
# The run identity of the SESSION INSTANCE. It is not a spawn and carries no `agent_id`
# (`tools/provider_observations.json` -> `agent_identity`), so every call it makes is this one run.
SESSION_RUN = "session"
# Bounds on the scan, because both callers run on every tool call of their event and an unbounded
# walk over a staging tree is a session that stands still (`_compat.HOOK_DEADLINE_SECONDS` is the
# budget both hooks share). A staging directory past these bounds is read up to them and the
# readings beyond are simply not found — which refuses the move rather than allowing it.
MAX_FILES = 400
MAX_BYTES = 1024 * 1024
# The bound on hashing a DOCUMENT (see `source_digests`). Generous next to `MAX_BYTES`, because this
# one is a scanned invoice and not a YAML record, and small enough that a blocking gate can do it:
# ~64 ms at 1 GB/s, inside the same shared budget. A document past it gets no digest, and the gate
# refuses the filing and says so rather than filing it unbound.
MAX_DOCUMENT_BYTES = 64 * 1024 * 1024


class Reading(object):
    """One reader's answer for one document, with the run the attestation names."""

    def __init__(self, record, run, source, destination, document_class, source_digest=""):
        self.record = record                  # state-relative path of the file it was read from
        self.run = run
        self.source = source
        self.destination = destination
        self.document_class = document_class
        # sha256 of the DOCUMENT as it lay when this reading was attested — see `source_digests`
        self.source_digest = source_digest

    def named(self):
        """The one line this reading contributes to a refusal the USER has to decide."""
        return "%s -> %s (%s; run %s, %s)" % (
            self.source or "?", self.destination or "?", self.document_class or "no class given",
            self.run, self.record)


def as_landing(text):
    """A path spelled the way the two sides of the comparison are compared.

    Separators and a leading `./` are spelling; everything else is content, CASE INCLUDED. A
    case-different destination is therefore a DISAGREEMENT and refuses the move even where the
    filesystem would treat the two as one file — the fail-closed direction, and the one that keeps
    the archive's own spelling decided by the readers rather than by the host.
    """
    value = str(text or "").replace("\\", "/").strip()
    while value.startswith("./"):
        value = value[2:]
    return value.rstrip("/")


def run_identity(data):
    """WHO made this call, as the PROVIDER names it — never as the caller claims.

    `agent_id` identifies the spawn instance and nothing an agent writes reaches it. A payload
    without one is the session instance (see `SESSION_RUN`); `agent_type` is deliberately NOT
    consulted, because it names a ROLE and two spawns of one role share it — reading it would make
    "two runs" mean "two roles" and let one run answer twice by changing hats.
    """
    return str(data.get("agent_id") or "").strip() or SESSION_RUN


def store_path(state, spec=FILING):
    return os.path.join(state, spec.store_dir, STORE_NAME)


def digest(path, limit=None):
    """sha256 of the file's BYTES, or None when it cannot be read or is past `limit`.

    The bytes and not the parsed content: an attestation says who wrote THIS file, so an edit after
    the fact has to invalidate it. That is also why the gate looks the digest up rather than the
    path — a record edited after it was attested has no attestation for its current bytes and stops
    counting as a reading.
    """
    try:
        if limit is not None and os.path.getsize(path) > limit:
            return None
        with open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    except OSError:
        return None


def source_digests(root, entries, spec=FILING):
    """{source path: sha256 of the DOCUMENT as it lies now} for the entries of one reading record.

    WHY THE ATTESTATION BINDS THE DOCUMENT AND NOT ONLY ITS PATH. Two readings agree that
    `inbox/scan.pdf` belongs at a place under a name. Nothing in this kit stops that file from being
    REPLACED afterwards — measured 2026-08-29 through the full registered chain, three ways, all
    rc 0: `echo forged > inbox/scan_0001.pdf`, a tool `Write` over it, and `cp other.pdf` onto it
    (`guard_fs_tripwire` refuses a DELETE under `inbox/`, not an overwrite). Without this the two
    readings would then authorise a document neither reader ever saw.

    COMPUTED HERE AND NOT BY A ROLE, which is what makes it usable at all: the `filing-reviewer` is
    shipped with `Read, Grep, Glob, Write` and no command-running tool, so a `source_sha256` FIELD in
    the record would be a field that role cannot produce. The hook has the filesystem; the role does
    not. `test_a_document_swapped_after_the_readings_is_not_the_document_they_read` measures it.

    A source that cannot be hashed — missing, unreadable, past `MAX_DOCUMENT_BYTES` — gets no entry,
    and the gate refuses a filing whose readings carry none rather than filing it unbound.
    """
    found = {}
    for entry in entries:
        source = as_landing(entry.get(spec.source_key))
        if not source or source in found:
            continue
        digested = digest(os.path.join(root, source.replace("/", os.sep)), MAX_DOCUMENT_BYTES)
        if digested:
            found[source] = digested
    return found


# The plan field a rule uses to release its own class from the SECOND reading. Its VALUES are not
# enumerated anywhere: `readings_required` reads the one answer YAML gives as a boolean false and
# treats everything else — absent, true, a word, a list — as "not released".
SECOND_READING = "second_reading"
# The two answers `readings_required` gives, named because both appear in refusals the user reads
# and a number that lives in two places is the one that stops matching the code.
REQUIRED_READINGS = 2
RELEASED_READINGS = 1


def readings_required(rule):
    """How many independent readings this policy entry demands. TWO unless it says otherwise.

    ONE FUNCTION, TWO CALLERS, and the entry is whichever document the user owns for that decision:
    a `filing_plan.yaml` RULE for a document entering the archive (`gate_second_reading`), a
    `master_data.yaml` CATEGORY for a row entering the ledger (`gate_second_booking`). An entry that
    does not exist — a category nobody put in the vocabulary — is `None` here and asks for two,
    which is the side a project starts on and the side an invented category lands on.

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


def contract_of(kernel_module, spec=FILING):
    """(name of the record's LIST FIELD, the per-entry keys it owes) — read off the schema.

    `kernel_module` is `_kernel.kernel_module` — passed in rather than imported, so the failure to
    reach the kernel belongs to the caller, which is the one that knows whether failing means
    "refuse" or "record nothing". `(None, ())` when the schema is unreachable, declares no list
    field, or declares one whose required per-entry keys do not include all of the contract's own
    `read_keys`. Every caller reads that as "no reading can be recognised", which refuses rather
    than allows.

    THE KEYS COME BACK WITH THE NAME because for the booking contract they ARE the answer: what a
    booking reading must state is the schema's business, and a hook that spelled the list again
    would be a second contract nothing compares against the first.
    """
    try:
        schemas = kernel_module("schemas")
        schema = schemas.load_schema(spec.schema) or {}
    except BaseException:  # noqa: BLE001 — an unreachable contract is not an empty one
        return None, ()
    for name, declared in (schema.get("fields") or {}).items():
        keys = tuple((declared or {}).get("item_required") or ())
        if (declared or {}).get("type") == "list" and set(keys).issuperset(spec.read_keys):
            return name, keys
    return None, ()


def contract(kernel_module):
    """The FILING contract's list field, or None — `contract_of`'s answer for the one caller pair
    that only ever asks about filing (`gate_second_reading`, `record_filing_reading`)."""
    return contract_of(kernel_module, FILING)[0]


def stated(value):
    """Has this entry actually ANSWERED for a key? Present, not null, not blank.

    NOT TRUTHINESS, and the difference is a measured defect rather than a nicety: FR-0065's booking
    readings carry `vat_rate`, and a kleinunternehmer or reverse-charge invoice reads `0` there. YAML
    parses that as the integer zero, which is falsy — so a truth test dropped every such reading, the
    row it belonged to could never be covered, and the project would have been walled off its own
    commits with a refusal pointing at a record that was there. An empty string and a missing key
    stay "not answered", which is the case the check exists for.
    """
    return value is not None and str(value).strip() != ""


def staged_records(state, field, keys=READ_KEYS):
    """[(state-relative path, sha256, [entry dicts])] for every staged file that IS a reading record.

    Recognised by SHAPE and not by filename: a mapping under `staging/<item>/` carrying the schema's
    list field, whose entries carry all of the schema's per-entry keys. A file that carries the list
    with entries missing a key contributes the entries that are complete and drops the rest — a
    half-written record must not silently become a reading, and must not stop the complete ones in
    the same file from being one either.
    """
    if not field:
        return []
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return []
    found, seen = [], 0
    root = os.path.join(state, STAGING)
    for item in sorted(os.listdir(root)) if os.path.isdir(root) else []:
        directory = os.path.join(root, item)
        if not os.path.isdir(directory):
            continue
        for name in sorted(os.listdir(directory)):
            if seen >= MAX_FILES:
                return found
            path = os.path.join(directory, name)
            if not name.endswith((".yaml", ".yml")) or not os.path.isfile(path):
                continue
            seen += 1
            try:
                if os.path.getsize(path) > MAX_BYTES:
                    continue
                with open(path, encoding="utf-8-sig") as handle:
                    parsed = yaml.safe_load(handle) or {}
            except BaseException:  # noqa: BLE001 — a file that will not parse is not a reading
                continue
            if not isinstance(parsed, dict):
                continue
            entries = [e for e in (parsed.get(field) or [])
                       if isinstance(e, dict) and all(stated(e.get(key)) for key in keys)]
            if entries:
                found.append((os.path.join(STAGING, item, name).replace("\\", "/"),
                              digest(path), entries))
    return found


def attestations(state, spec=FILING):
    """{(state-relative path, sha256): (run, {source: sha256})} — the store as it stands.

    FIRST LINE WINS for one (path, digest). An attestation is a statement about who wrote those
    bytes and about what the documents it names looked like at that moment; a later call that finds
    the same bytes still unattested-by-itself must not be able to overwrite either half.
    """
    found = {}
    try:
        with open(store_path(state, spec), encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                key = (str(entry.get("record") or ""), str(entry.get("sha256") or ""))
                sources = entry.get("sources")
                if key[0] and key[1] and key not in found:
                    found[key] = (str(entry.get("run") or ""),
                                  sources if isinstance(sources, dict) else {})
    except OSError:
        pass
    return found


def attest(state, records, run, root, spec=FILING):
    """Append an attestation for every record whose current bytes have none. Best effort.

    Best effort on purpose: this runs on PostToolUse, where an exit code decides nothing, and a
    failure here does not let a filing through — it removes a reading, and `gate_second_reading`
    refuses a filing it cannot see two readings for.

    Each line binds TWO things: who wrote the record (`run`, from the payload) and what the
    documents it names looked like at that moment (`sources`, from the filesystem). See
    `source_digests` for why the second half is here and not a field of the record.
    """
    known = attestations(state, spec)
    new = [(path, sha, entries) for path, sha, entries in records
           if sha and (path, sha) not in known]
    if not new:
        return []
    try:
        os.makedirs(os.path.join(state, spec.store_dir), exist_ok=True)
        with open(store_path(state, spec), "a", encoding="utf-8") as handle:
            for path, sha, entries in new:
                handle.write(json.dumps({
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "record": path, "sha256": sha, "run": run,
                    "sources": source_digests(root, entries, spec),
                }, ensure_ascii=False) + "\n")
    except OSError:
        return []
    return [(path, sha) for path, sha, _entries in new]


def readings(state, field):
    """Every ATTESTED reading in this project, as `Reading` objects.

    A staged record whose current bytes carry no attestation yields nothing: an unattested record is
    a file somebody wrote, and this module has no way to say which run wrote it, which is the one
    thing the whole check rests on.
    """
    known = attestations(state)
    found = []
    for path, sha, entries in staged_records(state, field):
        run, sources = known.get((path, sha or ""), ("", {}))
        if not run:
            continue
        for entry in entries:
            source = as_landing(entry.get(SOURCE))
            found.append(Reading(path, run, source, as_landing(entry.get(DESTINATION)),
                                 str(entry.get(DOCUMENT_CLASS) or ""),
                                 str(sources.get(source) or "")))
    return found

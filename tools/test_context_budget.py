#!/usr/bin/env python3
"""What loads at every session start, and how big it may get — the two halves of one question.

THREE DECISIONS ARE MEASURED HERE.

  1. THE SIZE STATEMENT IS BYTES, IT IS PER KIT, AND IT IS A MEASUREMENT RATHER THAN A CHOICE.
     `tools/validate.py` used to fail a constitution over 220 LINES. Measured, that limit said
     nothing about size: all three constitutions held it only because 31 to 46 of their lines ran
     between 110 and 1 899 characters — reflowed to 100 columns the same texts are 383 / 368 / 394
     lines — and a compaction pilot cut 24.9 % of the bytes while its line count rose from 20 to
     36. So the line ceiling pushed AGAINST the byte budget standing beside it. It is gone, and
     nothing per-file replaced it, because no split across three files follows from anything.
     THE FIXED BYTE CEILING IS GONE TOO (2026-08-03): 25 600 was "25 KB" read at 1024 B, was never
     computed against what a kit carries, was missed by all three kits by 6 to 10 KB even after
     de-duplication, and only ever warned — three releases of being read and stepped over. What
     remains is a RATCHET: `tools/lead_package_sizes.json` records what each package weighs,
     `validate.py` fails a package that exceeds its own record, and
     `tools/record_lead_package_sizes.py --write --note "…"` is the only way the record moves. The
     tests below measure the DERIVATION (the record IS `lead_package.size`) and the running rule
     (the real validator over a real copy), never the digit.

  2. THE §2 HOOK TABLE LEFT THE SESSION-FIXED LOAD WITHOUT LEAVING THE PROJECT. It is
     `hooks/ENFORCEMENT.md` now, and a relocation is only worth anything if BOTH halves hold: the
     target must really not load with the session, and the content must be reachable at the moment
     it is needed. The first half is measured as three separate absences (import chain, preloaded
     skills, session-start injection) rather than asserted about the platform; the second is
     measured by making every refusal a shipped hook writes carry the file's path, and then reading
     that path out of REAL hook processes.

  3. WHAT DOES NOT LOAD TAKES THE WHOLE APPARATUS WITH IT, so a text may not claim reach without
     naming the session it holds for. The kits' enforcement is registered in the PROJECT's own
     `.claude/`, and a client session started in a mode that does not load those settings runs none
     of it while the file tools stay writable in the project — measured against the running client
     for three such modes (`docs/reviews/2026-08-30-tsk0094-client-start-modes-measurements.md`).
     Until 2026-08-30 the three constitutions said `gate_write_scope` "refuses every tool write
     there", "WRITE-LOCKED against every tool write" and "WHAT RUNS HERE, complete in both
     directions" with no such qualifier at all. The checks in section 3 below hold the corrected
     form: they are about the TEXT, which is the artifact in question, and the reach they measure
     it against is the registration surface the two checks above already read.

WHAT THIS MODULE DOES NOT ESTABLISH, said here rather than discovered later: that Claude Code or
Codex loads exactly the files this repo believes it loads. Nothing in a test can measure a
provider's context assembly. What is measured is that this repo's own three routes into a session —
the `CLAUDE.md`/`AGENTS.md` import chain, the agents' `skills:` frontmatter, and what
`session_status.py` injects — do not carry the reference. A fourth route invented by a provider
would be outside this instrument, and outside every other one in the repo.
"""
import ast
import glob
import io
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lead_package                                             # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEAM_KITS = os.path.join(ROOT, "team-kits")
SPEC = os.path.join(ROOT, "docs", "HARNESS_V2_SPEC.md")
KITS = ("dev-team", "office-team", "research-team")


def _kit_dir(kit):
    return os.path.join(TEAM_KITS, kit)


def _reference_name(kit):
    """`_compat.REFERENCE_NAME` for this kit, by AST — the filename the refusals interpolate.

    Read from the module rather than spelled here so that a rename moves this whole module with it
    instead of leaving it measuring a file nothing points at.
    """
    path = os.path.join(_kit_dir(kit), "hooks", "_compat.py")
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=path)
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id == "REFERENCE_NAME" \
                and isinstance(node.value, ast.Constant):
            return node.value.value
    raise AssertionError("%s defines no REFERENCE_NAME" % path)


def _reference_path(kit):
    return os.path.join(_kit_dir(kit), "hooks", _reference_name(kit))


# ============================================================ 1. the one size statement
def _spec_bullet(opening):
    """The II.5 bullet that OPENS with this text, up to the next bullet — one statement, whole.

    A fixed character window was what the previous cut of this check used, and it is the wrong
    subject twice over: too short and the statement's second half is unwatched, too long and it
    reads the neighbouring rule. A markdown bullet declares its own end (the next line starting
    `- ` at the same indent), so the statement is taken as the document writes it.
    """
    with io.open(SPEC, encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    start = next((index for index, line in enumerate(lines)
                  if line.startswith("- " + opening)), None)
    assert start is not None, "II.5 carries no bullet opening with %r" % opening
    end = next((index for index in range(start + 1, len(lines))
                if lines[index].startswith("- ") or lines[index].startswith("## ")), len(lines))
    return "\n".join(lines[start:end])


# A CEILING IS A RELATION TO A NUMBER, and that is the definition this predicate encodes rather
# than the three spellings the tree happened to carry ("≤25 KB", `25 * 1024`, "25 000"). Any
# comparison operator followed by a figure is one, whichever unit or grouping follows it.
_STATED_CEILING = re.compile(r"(?:≤|<=|<|max\.?|höchstens|maximal)\s*[\d   ]*\d")


def _states_a_ceiling(text):
    """Does this statement name a fixed upper bound? — the running predicate, one definition."""
    return bool(_STATED_CEILING.search(text))


def test_the_spec_states_the_size_rule_the_validator_enforces():
    """II.5 must describe the rule `validate.py` runs, and the rule stopped being a number.

    WHAT CHANGED AND WHY THIS TEST CHANGED WITH IT. The previous version demanded that II.5 spell
    `lead_package.MAX_BYTES`, which was right while a constant existed and was the wrong question
    the moment the constant turned out to derive from nothing but reading "25 KB" at 1024 bytes.
    The ceiling is now per kit and IS the recorded measurement, so what the spec owes the reader is
    a LOCATION, not a figure — house rule: naming a place beats quoting a number that rots.

    THREE ASSERTIONS, and the middle one is the one that would go red if somebody put a fresh
    invented number back:

      * the statement names the record file, derived from `lead_package.RECORD` rather than typed
        here, so moving the record moves what the spec has to say;
      * the statement states NO fixed ceiling — `_states_a_ceiling` is the running predicate and
        `test_the_ceiling_detector_reads_a_bound_however_it_is_spelled` drives it with the
        spellings this tree really used;
      * it names the command that moves the record, because a ratchet nobody can raise on purpose
        is a ratchet somebody raises by editing the JSON.
    """
    statement = _spec_bullet("Lead-Instruktionspaket")
    record = os.path.basename(lead_package.RECORD)
    assert record in statement, (
        "II.5's lead-package statement does not name %s, so the number it governs lives nowhere a "
        "reader is sent: %r" % (record, statement))
    assert not _states_a_ceiling(statement), (
        "II.5 states a fixed upper bound for the lead package again. The ceiling is the recorded "
        "measurement per kit; a second invented number beside it is the defect this round "
        "removed:\n%s" % statement)
    assert "record_lead_package_sizes.py" in statement, (
        "II.5 does not say how the record moves — without the command the record reads as a fact "
        "rather than as a decision somebody has to make:\n%s" % statement)
    # ...and the per-FILE line budget stays gone: the old prose said "≤150 Zeilen" for the
    # constitution and the lead SKILL, and leaving that in beside the size rule would restore the
    # contradiction an earlier round removed.
    with io.open(SPEC, encoding="utf-8") as handle:
        body = re.sub(r"\s+", " ", handle.read()).split("## II.5 ", 1)[1].split("## II.6", 1)[0]
    assert "≤150 Zeilen" not in body.replace(" ", "") or "gestrichen" in body, (
        "II.5 still carries the per-file line budget as a live requirement")


@pytest.mark.parametrize("text,bounded", [
    ("Lead-Instruktionspaket ≤ 25 600 B (= 25 KB zu 1024 B)", True),
    ("Lead-Instruktionspaket <= 25600 B", True),
    ("Das Paket ist maximal 25 KB gross", True),
    ("höchstens 30 KB", True),
    ("Die Grenze ist pro Kit die aufgezeichnete Messung in lead_package_sizes.json", False),
    ("Sie wurde von allen drei Kits um mehrere KB verfehlt", False),
    ("Ein Aufschlag auf die Messung wäre eine zweite gegriffene Zahl", False),
])
def test_the_ceiling_detector_reads_a_bound_however_it_is_spelled(text, bounded):
    """The floor under the assertion above: a detector that answers "no bound" to everything would
    let 25 600 walk straight back into the spec with the suite green.

    The positive cases are the three spellings this repo really carried plus the German wording a
    rewrite would reach for; the negative cases are sentences from the statement as it now stands,
    including two that mention numbers and units WITHOUT bounding anything — because a detector
    that flagged those would force the spec to stop explaining itself.
    """
    assert _states_a_ceiling(text) is bounded, text


def test_the_recorded_ceiling_is_the_measurement_and_not_a_typed_number():
    """The derivation itself: for every shipped kit the record equals what the package weighs.

    THIS IS THE TEST THAT MAKES THE NUMBER DERIVABLE rather than chosen. A ratchet whose record can
    hold any figure is a ceiling somebody picked again, one file over — so the record is asserted
    to BE `lead_package.size`, which is the same function `validate.py` compares against. It goes
    red on the two ways that breaks: an edit to a kit's constitution or agent file without
    `python tools/record_lead_package_sizes.py --write --note "..."`, and a hand-edited JSON.

    The subject is derived from the tree (every directory that ships a constitution), so a fourth
    kit is covered on the day it exists and a record naming a kit that is gone is a finding rather
    than a leftover.
    """
    shipped = {os.path.basename(os.path.dirname(os.path.dirname(path)))
               for path in glob.glob(os.path.join(TEAM_KITS, "*", "constitution", "AGENTS.md"))}
    recorded = lead_package.records()
    assert set(recorded) == shipped, (
        "the record covers %s and the tree ships %s — an unrecorded package is the one place a "
        "lead package could grow unwatched" % (sorted(recorded), sorted(shipped)))
    drifted = {kit: (recorded[kit], lead_package.size(_kit_dir(kit))) for kit in sorted(shipped)
               if recorded[kit] != lead_package.size(_kit_dir(kit))}
    assert not drifted, (
        "the recorded ceiling is no longer the measurement it claims to be (kit: recorded, "
        "measured) — run python tools/record_lead_package_sizes.py --write --note \"...\": %s"
        % drifted)


def test_every_file_the_package_weighs_checks_out_lf():
    """A CRLF checkout must not inflate the byte-size-checked package past its record (BUG-0025).

    THE RECORD IS TAKEN ON AN LF TREE and `validate.py` compares it against `lead_package.size`,
    which is `os.path.getsize` — raw on-disk bytes, not CRLF-normalized (unlike `kit_hash`, which
    replaces `\\r\\n` before it digests, so the kit content hash is unaffected either way). So a
    Windows clone with the default `core.autocrlf=true` adds one byte per line to every `.md` the
    package weighs and pushes it over its record. Measured end to end: dev-team goes 30674 -> 31006
    against a 30674 record, `tools/validate.py` exits 1 with "lead instruction package … > …
    recorded (spec II.5)", and `install.sh` runs validate BEFORE it installs any hook — so a plain
    Windows clone installs nothing, handover_guard included.

    The mechanism that prevents it is `.gitattributes` pinning these files to `eol=lf`, which
    overrides `core.autocrlf`. This test asks git's OWN attribute resolution (`git check-attr`, the
    running machinery reading the working-tree `.gitattributes`) about every file the package
    actually weighs — derived from `lead_package.files`, not listed — so pinning by an enumeration
    of extensions that forgets one (which is how BUG-0025 shipped: `*.py`/`*.sh`/VERSION and not
    `.md`) turns this red for the file it forgot.
    """
    git = shutil.which("git")
    if not git:
        pytest.skip("git not on PATH")
    if subprocess.run([git, "rev-parse", "--is-inside-work-tree"], cwd=ROOT,
                      capture_output=True, text=True).returncode != 0:
        pytest.skip("not a git work tree (exported source)")
    weighed = [path for kit in KITS for path in lead_package.files(_kit_dir(kit))]
    assert weighed, "the package weighs nothing — the subject derived to nothing"
    wrong = {}
    for path in weighed:
        rel = os.path.relpath(path, ROOT)
        result = subprocess.run([git, "check-attr", "eol", "--", rel], cwd=ROOT,
                                capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=60)
        assert result.returncode == 0, result.stderr
        resolved = result.stdout.strip().rsplit(": ", 1)[-1]
        if resolved != "lf":
            wrong[rel] = resolved
    assert not wrong, (
        "these files feed the byte-size check but do not check out LF, so a core.autocrlf=true "
        "clone would inflate the lead package past its recorded size and abort install.sh before "
        "any hook is installed (BUG-0025): %s" % wrong)


def test_no_file_the_package_weighs_carries_crlf_on_disk():
    """The other half of its neighbour, and a SEPARATE test because it needs no git at all.

    THE ATTRIBUTE IS WHAT GIT PROMISES; THIS IS WHAT IS THERE. The two come apart, and git cannot
    report it: it normalizes on the way IN, so a file an editor saved with CRLF reads as unmodified
    and keeps its `eol=lf` attribute while carrying CRLF on disk. Measured on this working tree
    2026-09-02: 47 tracked text files were in exactly that state, NONE of them in a lead package --
    so nothing was wrong, and nothing could have said so either.

    WHAT IT WOULD COST is the whole of BUG-0025 once more, in the direction nobody watches: the size
    RECORD is taken from these bytes (`tools/record_lead_package_sizes.py`), and the ceiling is an
    EQUALITY (`test_the_recorded_ceiling_is_the_measurement_and_not_a_typed_number`) -- so a record
    taken over a CRLF file is a number no LF checkout can ever match, and it would be CI that goes
    red rather than the machine that wrote it. The kit content hash is unaffected either way
    (`kernel.hashing.kit_hash` normalizes CRLF before it digests), which is why this lives here and
    not there.

    SEPARATE, and that is measured rather than tidy: folded into its neighbour, the assertion never
    ran in a clone without `.git` -- the two `pytest.skip`s there stand ahead of it, and a mutation
    that put CRLF into a shipped constitution came back "1 skipped".
    """
    weighed = [path for kit in KITS for path in lead_package.files(_kit_dir(kit))]
    assert weighed, "the package weighs nothing — the subject derived to nothing"
    crlf = {os.path.relpath(path, ROOT).replace(os.sep, "/"): body.count(b"\r\n")
            for path, body in ((path, io.open(path, "rb").read()) for path in weighed)
            if b"\r\n" in body}
    assert not crlf, (
        "these files feed the byte-size check and carry CRLF on disk, so the size recorded here is "
        "one an LF checkout cannot reproduce: %s" % crlf)


OBSERVATIONS = json.load(io.open(os.path.join(ROOT, "tools", "provider_observations.json"),
                                 encoding="utf-8"))


def _lead(kit):
    return lead_package.lead_role(_kit_dir(kit))


@pytest.mark.parametrize("kit", KITS)
def test_the_budget_weighs_what_a_session_was_measured_to_receive(kit):
    """The budget's subject is a MEASUREMENT, and for a round it was a belief.

    `files()` counted the lead SKILL because the SKILL's own frontmatter said Claude preloads it.
    Measured (2026-08-02, `tools/provider_observations.json` → `session_context`): the constitution
    and the agent file arrive verbatim, the SKILL does not, and the provider's `init` line lists it
    under `skills` and `slash_commands`. For dev-team that is 21 572 of 49 758 bytes weighed
    against a budget they never enter — a measurement of the wrong subject, and the reason the
    shortening was being aimed at a file that costs no context at all.

    WHAT THIS TEST CAN DO AND WHAT IT CANNOT: it cannot observe a context window. It holds the
    derivation to the record, and the record carries its own provenance. Both halves are asserted,
    because dropping the SKILL from `files()` is only right if it lands in `on_demand_files()` —
    the pin's subject (`test_shortening_net.py::_pinned_files`) reads that one, and a file in
    neither list is a file nothing watches."""
    kit_dir = _kit_dir(kit)
    lead = _lead(kit)
    assert lead, kit
    loaded = {os.path.relpath(path, kit_dir).replace(os.sep, "/")
              for path in lead_package.files(kit_dir)}
    on_demand = {os.path.relpath(path, kit_dir).replace(os.sep, "/")
                 for path in lead_package.on_demand_files(kit_dir)}
    expected_loaded = {name.replace("<lead>", lead)
                       for name in OBSERVATIONS["session_context"]["loaded"]}
    expected_on_demand = {name.replace("<lead>", lead)
                          for name in OBSERVATIONS["session_context"]["registered_not_loaded"]}
    assert loaded == expected_loaded, kit
    assert on_demand == expected_on_demand, kit
    assert not loaded & on_demand, "%s: a file cannot be both" % kit


@pytest.mark.parametrize("kit", KITS)
def test_an_instruction_that_does_not_load_is_reachable_from_one_that_does(kit):
    """The other half of taking the SKILL out of the package, and without it the correction would
    have been a demotion: a procedure that does not load and is not asked for is a procedure that
    does not exist. One observed session never opened it.

    So the LOADED text has to hand over the invocation, in BOTH provider vocabularies — the Claude
    slash command and the Codex path — because a lead that only knows one of them is a lead on the
    wrong provider. Derived from the role `settings.json` binds, so renaming the lead moves this
    with it rather than leaving it checking a name nobody uses.

    The old text failed this while looking like it passed it: it named the Codex DIRECTORY inside
    the sentence "Claude preloads the skill", which is a description of a load, not an
    instruction to fetch anything."""
    kit_dir = _kit_dir(kit)
    lead = _lead(kit)
    loaded_text = "\n".join(io.open(path, encoding="utf-8").read()
                            for path in lead_package.files(kit_dir))
    for invocation in ("`/%s`" % lead, ".agents/skills/%s/SKILL.md" % lead):
        assert invocation in loaded_text, (
            "%s: nothing that LOADS tells the lead how to open its own procedure (%s missing). "
            "The SKILL is registered on demand, so an unmentioned SKILL is an unread one."
            % (kit, invocation))


def _occurrences(haystack, needle):
    index = haystack.find(needle)
    while index != -1:
        yield index
        index = haystack.find(needle, index + 1)


def _skills_reachable(kit):
    """{role: (agent .md, SKILL.md)} for every skill an agent's `skills:` frontmatter names.

    Both files, because the correction has two halves that live in different places: the SKILL is
    what makes the false claim, and the AGENT FILE is the one that actually loads — so it is the
    only place where naming the retrieval route can reach anybody.

    THE SUBJECT IS DERIVED, not listed. "The 23 files that carry the sentence" would be a rule
    about today's tree; what the rule is about is the ROUTE — a skill a session can be handed
    through frontmatter — so a skill added tomorrow is covered the day its agent names it, and a
    skill nobody names is nobody's claim.
    """
    yaml = pytest.importorskip("yaml")
    reachable = {}
    for path in sorted(glob.glob(os.path.join(_kit_dir(kit), "agents", "*.md"))):
        with io.open(path, encoding="utf-8") as handle:
            raw = handle.read()
        front = yaml.safe_load(raw.split("---", 2)[1]) if raw.count("---") >= 2 else {}
        for skill in (front or {}).get("skills") or []:
            candidate = os.path.join(_kit_dir(kit), "skills", str(skill), "SKILL.md")
            if os.path.isfile(candidate):
                reachable[str(skill)] = (path, candidate)
    return reachable


@pytest.mark.parametrize("kit", KITS)
def test_no_skill_a_session_can_reach_claims_to_be_preloaded(kit):
    """Twenty-three shipped SKILLs said `Preloaded into the X subagent.` and the frontmatter route
    they meant delivers nothing.

    MEASURED (`provider_observations.json` → `session_context.any_role_bound_as_session_agent`): a
    scaffolded dev project with `agent: backend-developer` and `--tools ""`, one session, a control
    word in the agent file and a counter-control word at the end of the SKILL — the agent file's
    word came back, the SKILL's did not.

    THE LIMIT IS PART OF THE CORRECTION, not a footnote to it: what was measured is the
    SESSION-agent path, and the sentence claimed the SUBAGENT-SPAWN path. Same mechanism, same
    result as for the lead, and still not measured — two attempts at a real child ended with the
    child refusing the work order before it answered. So the texts now say what holds and name the
    open half, and the record carries why it stayed open.

    Both directions are asserted, and the positive one is where the first cut of this test was
    wrong in a way worth recording: it demanded the retrieval route inside the SKILL, which is the
    one document a session that needs the route does not have. The route belongs in the AGENT
    FILE — the half of the pair that was measured to arrive — and that is also where the same
    false claim stood in thirteen files ("in your preloaded **X** skill").
    """
    forbidden = OBSERVATIONS["session_context"]["claims_of_loading"]
    reachable = _skills_reachable(kit)
    assert reachable, "%s: no agent names a skill — the subject derived to nothing" % kit
    for role, (agent, path) in sorted(reachable.items()):
        with io.open(path, encoding="utf-8") as handle:
            skill_text = handle.read()
        with io.open(agent, encoding="utf-8") as handle:
            agent_text = handle.read()
        # WHITESPACE IS COLLAPSED FIRST, and that is not tidiness — it is the spelling this whole
        # correction exists for. Two of the twenty-three SKILLs wrapped the sentence mid-phrase
        # ("Preloaded\n  into the devops-engineer subagent."), which is what 100-column prose does
        # by default, and it is why the first survey counted twenty-one. A guard that compares
        # against a single-spaced phrase repeats the very miss it was written to end: measured on
        # `dev-team/skills/devops-engineer/SKILL.md`, the wrapped sentence passed and the same
        # sentence on one line failed.
        lowered = re.sub(r"\s+", " ", (skill_text + "\n" + agent_text).lower())
        # A NEGATED phrase is the opposite claim, and the corrected texts are full of them — "NOT
        # loaded at session start" is the sentence this test exists to produce, so a plain
        # substring search would fail every file it just fixed. The negation is read as such
        # rather than by dropping the phrase from the inventory, which would leave the positive
        # spelling unwatched.
        #
        # THE WINDOW DICTATES A SENTENCE FORM, and it is a cost rather than a solved problem: the
        # negation has to stand IMMEDIATELY before the phrase. "The SKILL is NOT, despite the name,
        # preloaded into the subagent" is a correct sentence and goes red here; write it without
        # the interjection. What the window does NOT cost is protection — any UNNEGATED occurrence
        # flags the file, so "this file is not the one that is preloaded; the SKILL is preloaded"
        # is caught on its second half (measured). The error direction is the safe one.
        claims = [phrase for phrase in forbidden
                  if any(not re.search(r"\b(not|never|no)\W{0,3}$", lowered[max(0, index - 12):index])
                         for index in _occurrences(lowered, phrase))]
        assert not claims, (
            "%s: %s / %s says %s, and a session bound to that role was measured NOT to receive "
            "the skill (tools/provider_observations.json)."
            % (kit, os.path.relpath(agent, ROOT), os.path.relpath(path, ROOT), claims))
        for invocation in ("`/%s`" % role, ".agents/skills/%s/SKILL.md" % role):
            assert invocation in agent_text, (
                "%s: %s does not name %s — the SKILL is registered rather than loaded, so the file "
                "that DOES load has to say how to fetch it."
                % (kit, os.path.relpath(agent, ROOT), invocation))


def _claim_survives(text):
    """The guard's own predicate, over one string — so the probes below drive the running rule."""
    forbidden = OBSERVATIONS["session_context"]["claims_of_loading"]
    lowered = re.sub(r"\s+", " ", text.lower())
    return [phrase for phrase in forbidden
            if any(not re.search(r"\b(not|never|no)\W{0,3}$", lowered[max(0, index - 12):index])
                   for index in _occurrences(lowered, phrase))]


@pytest.mark.parametrize("spelling", [
    "Preloaded into the devops-engineer subagent.",
    "Preloaded\n  into the devops-engineer subagent.",
    "Preloaded into\n  the records-clerk subagent.",
    "How it works. Preloaded\ninto\nthe reviewer subagent.",
])
def test_the_guard_reads_the_claim_however_the_line_is_wrapped(spelling):
    """THE MISS THIS GUARD WAS BUILT TO END, one level up — in the guard.

    Two of the twenty-three SKILLs broke the phrase across a line, which is what 100-column prose
    does by default, and a `grep "Preloaded into"` counted twenty-one. The guard then compared
    against the same single-spaced phrase: measured on
    `dev-team/skills/devops-engineer/SKILL.md`, the wrapped sentence passed the guard and the
    identical sentence on one line failed it. Whoever reflowed the paragraph would have brought the
    claim back with nothing going red.

    The probes run the RUNNING predicate rather than a copy of it, and the last one carries two
    breaks inside one phrase so "collapse a single newline" is not enough to pass."""
    assert _claim_survives(spelling) == ["preloaded into"], spelling


@pytest.mark.parametrize("text,expected", [
    ("The SKILL is NOT preloaded into the subagent.", []),
    ("It is never preloaded into anything.", []),
    ("This file is not the one that is preloaded; the SKILL is preloaded into the subagent.",
     ["is preloaded", "preloaded into"]),
])
def test_the_guard_reads_a_negation_as_the_opposite_claim(text, expected):
    """The other direction, and its cost stated as a case rather than as prose: a negation
    IMMEDIATELY before the phrase clears it, an unnegated occurrence ANYWHERE flags the file — so a
    text that denies the claim once and makes it once is caught on the second half.

    What is deliberately NOT covered is an interjected negation ("is NOT, despite the name,
    preloaded into…"): it goes red although it is correct. That costs a sentence form, not a
    protection, and the trade is the safe one."""
    assert sorted(_claim_survives(text)) == sorted(expected), text


def test_the_reachable_subject_survives_the_shapes_a_kit_can_have(tmp_path):
    """Three edge cases of the DERIVATION, none of which exists in the shipped kits today and each
    of which would silently empty or crash it tomorrow: an agent with no `skills:` at all, a
    `skills:` entry naming a directory that ships no `SKILL.md`, and one skill named by two agents.

    The third is the one with a wrong-looking alternative: a dict keyed by role collapses the two
    agents into one entry, so only ONE of them would ever be checked for the retrieval route. It is
    asserted here as the behaviour that holds today AND as the limit it carries — `project-auditor`
    ships in all three kits and is named by one agent in each, so the case is one edit away.
    """
    kit = tmp_path / "probe-team"
    (kit / "agents").mkdir(parents=True)
    (kit / "skills" / "alpha").mkdir(parents=True)
    (kit / "skills" / "empty").mkdir(parents=True)
    (kit / "skills" / "alpha" / "SKILL.md").write_text("alpha body\n", encoding="utf-8")
    (kit / "agents" / "plain.md").write_text("---\nname: plain\n---\nno skills here\n",
                                             encoding="utf-8")
    (kit / "agents" / "one.md").write_text(
        "---\nname: one\nskills: [alpha, empty]\n---\nbody\n", encoding="utf-8")
    (kit / "agents" / "two.md").write_text(
        "---\nname: two\nskills: [alpha]\n---\nbody\n", encoding="utf-8")

    saved = _kit_dir.__globals__["TEAM_KITS"]
    try:
        _kit_dir.__globals__["TEAM_KITS"] = str(tmp_path)
        reachable = _skills_reachable("probe-team")
    finally:
        _kit_dir.__globals__["TEAM_KITS"] = saved

    # the agent without `skills:` contributes nothing and raises nothing
    assert set(reachable) == {"alpha"}
    # a `skills:` entry with no shipped SKILL.md is dropped rather than pointing at a missing file
    assert "empty" not in reachable
    # a skill named twice resolves to ONE pair — the LAST agent wins, and that is the limit
    agent, skill = reachable["alpha"]
    assert os.path.basename(agent) == "two.md", (
        "a skill named by two agents no longer collapses to one pair — if that changed on purpose, "
        "the retrieval-route assertion now has to hold for every naming agent, not just one")
    assert os.path.basename(skill) == "SKILL.md"


def test_the_size_rule_is_a_byte_comparison_over_the_files_the_kit_names(tmp_path):
    """The floor under the rule: `size()` counts bytes of the files `files()` derives, `ceiling()`
    reads the record keyed by the kit's DIRECTORY NAME, and the comparison is strict.

    Built over a synthetic kit so the boundary can be hit exactly. The lead is taken from
    `settings.json` here as it is in production, so a derivation that ignored the setting and
    hard-coded a role name would report 0 for this kit and pass every "within record" assertion.
    """
    kit = tmp_path / "probe-team"
    (kit / "constitution").mkdir(parents=True)
    (kit / "settings").mkdir(parents=True)
    (kit / "agents").mkdir(parents=True)
    (kit / "skills" / "chief").mkdir(parents=True)
    (kit / "settings" / "settings.json").write_text(json.dumps({"agent": "chief"}),
                                                    encoding="utf-8")
    (kit / "constitution" / "AGENTS.md").write_text("c" * 1000, encoding="utf-8")
    (kit / "agents" / "chief.md").write_text("a" * 1000, encoding="utf-8")
    (kit / "skills" / "chief" / "SKILL.md").write_text("s" * 1000, encoding="utf-8")

    assert [os.path.basename(p) for p in lead_package.files(str(kit))] == \
        ["AGENTS.md", "chief.md"]
    # the SKILL is a file of this kit's lead and is deliberately NOT weighed — it does not load
    assert [os.path.basename(p) for p in lead_package.on_demand_files(str(kit))] == ["SKILL.md"]
    assert lead_package.size(str(kit)) == 2000

    record = tmp_path / "sizes.json"
    record.write_text(json.dumps({"sizes": {"probe-team": 2000}}), encoding="utf-8")
    # exactly at the record is NOT over it, one byte past it is
    assert lead_package.ceiling(str(kit), str(record)) == 2000
    assert not lead_package.size(str(kit)) > lead_package.ceiling(str(kit), str(record))
    (kit / "agents" / "chief.md").write_text("a" * 1001, encoding="utf-8")
    assert lead_package.size(str(kit)) > lead_package.ceiling(str(kit), str(record))

    # A KIT THE RECORD DOES NOT NAME ANSWERS None, never 0 and never "unlimited". Both wrong
    # answers pass a `>` comparison silently — 0 makes every package a finding, a large default
    # makes none — so the caller has to see the absence and `validate.py` fails on it.
    assert lead_package.ceiling(str(tmp_path / "other-team"), str(record)) is None
    assert lead_package.records(str(tmp_path / "no-such-file.json")) == {}

    # a lead the settings do not name contributes nothing — the subject follows the kit
    (kit / "settings" / "settings.json").write_text(json.dumps({}), encoding="utf-8")
    assert lead_package.size(str(kit)) == 1000
    assert lead_package.on_demand_files(str(kit)) == ()


def _validate_over_a_copy(tmp_path, mutate):
    """Run the SHIPPED `tools/validate.py` as a process over a copy of the tree, outside the repo.

    A copy, because the subject is a constitution this repo must not have: the only honest way to
    ask "does the validator still fail this" is to build the file it would fail and hand it to the
    program. `validate.py` derives its ROOT from its own location, so the copy needs `team-kits/`
    and `tools/*.py` and nothing else; the git-tracking check degrades to "moot" without a `.git`,
    which it is written to do.

    THE RECORD COMES ALONG, and forgetting it is not a small omission: `tools/*.py` misses
    `lead_package_sizes.json`, the copy would then have no record for any kit, and every case below
    would fail with "has no recorded size" — the right exit code for the wrong reason, which is the
    shape of a test that measures its own fixture.
    """
    root = tmp_path / "tree"
    (root / "tools").mkdir(parents=True)
    shutil.copytree(TEAM_KITS, str(root / "team-kits"),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for path in glob.glob(os.path.join(ROOT, "tools", "*.py")):
        shutil.copy(path, str(root / "tools" / os.path.basename(path)))
    shutil.copy(lead_package.RECORD, str(root / "tools" / os.path.basename(lead_package.RECORD)))
    mutate(root)
    result = subprocess.run([sys.executable, str(root / "tools" / "validate.py")],
                            capture_output=True, text=True, encoding="utf-8", errors="replace",
                            timeout=600)
    return result.stdout + result.stderr


def _four_hundred_short_lines(root, kit="office-team"):
    """Replace one kit's constitution with 400 lines nobody could call long.

    The office kit, because its package is the smallest: 400 lines of this width leave the whole
    package far UNDER its record, so the same fixture answers both directions — the line count must
    not matter, and the byte total must.
    """
    path = root / "team-kits" / kit / "constitution" / "AGENTS.md"
    head = path.read_text(encoding="utf-8").splitlines()[0]
    body = [head] + ["rule %03d: keep this short." % index for index in range(399)]
    path.write_text("\n".join(body) + "\n", encoding="utf-8")
    return path


def _grow_past_the_record(root, kit, over=1):
    """Append `over` bytes more than this kit's record allows, and return what it will then weigh."""
    kit_dir = os.path.join(str(root), "team-kits", kit)
    target = lead_package.ceiling(_kit_dir(kit)) + over
    path = os.path.join(kit_dir, "constitution", "AGENTS.md")
    with io.open(path, "a", encoding="utf-8") as handle:
        handle.write("x" * (target - lead_package.size(kit_dir)))
    return target


_LINE_COMPLAINT = re.compile(r"office-team: constitution has \d+ lines")


def _mentions_size(kit, output, failures_only=False):
    """The validator's line about this kit's package size, or None.

    `failures_only` IS THE HALF THIS CHECK WAS MISSING, and it was measured: with the size rule
    reverted to a `print("  [warn] …")` the positive tests below stayed GREEN, because appending
    bytes to a constitution also trips "VERSION not bumped" and `"VALIDATION FAILED" in output` was
    therefore true for a reason that has nothing to do with the package. `validate.py` prints each
    entry of `fails` as a line opening `  - `, so asking for that prefix asks which CHANNEL the
    complaint came out of — which is the whole subject of this round.
    """
    pattern = re.compile(r"%s: lead instruction package is (\d+) bytes (?:\(> (\d+) recorded|and "
                         r"has no recorded size)" % kit)
    for line in output.splitlines():
        if failures_only and not line.startswith("  - "):
            continue
        match = pattern.search(line)
        if match:
            return match
    return None


def test_a_constitution_of_four_hundred_short_lines_is_not_a_finding(tmp_path):
    """A shorter text may not be a finding — neither for its line count nor for its size.

    Under the old rule this exact tree failed with "office-team: constitution has 400 lines
    (> 220)" — a text 12 KB smaller than the one it replaced, rejected for being SHORTER per line.
    Under the RATCHET it must not be a finding either, and that is the direction worth stating: a
    record is a ceiling, so shrinking is free and needs no permission.

    THE CONTROL IS BUILT INTO THE SAME RUN, and it had to be rebuilt this round. It used to be "the
    unshortened kits are still reported", which was only true while every kit was over a ceiling
    nobody met; now every kit sits exactly ON its record and a validator that had stopped weighing
    packages altogether would produce the same silence as a correct one. So dev-team is pushed one
    byte over in the same tree: the run must report THAT kit and stay silent about office.
    """
    def mutate(root):
        _four_hundred_short_lines(root)
        _grow_past_the_record(root, "dev-team")

    output = _validate_over_a_copy(tmp_path, mutate)
    assert not _LINE_COMPLAINT.search(output), (
        "the validator still judges a constitution by its line count:\n%s"
        % "\n".join(line for line in output.splitlines() if "lines" in line))
    assert not _mentions_size("office-team", output), (
        "the shortened package is under its record and was reported anyway:\n%s" % output)
    assert _mentions_size("dev-team", output, failures_only=True), (
        "the validator did not FAIL any package at all — the fixture proves nothing:\n%s" % output)


def test_a_lead_package_over_its_record_fails_with_the_two_figures_it_compared(tmp_path):
    """The half that is RED without this round's change: the size rule now FAILS instead of warning.

    Under the previous rule this tree exited 0 with a `[warn]` line and shipped. The assertions are
    over the real process: the exit code has to be non-zero, the message has to name the kit's own
    recorded ceiling (read from `lead_package.ceiling`, not copied here) and the measured size (what
    `lead_package.size` computes over that same tree), so the validator and the recorder cannot
    disagree about what the package IS or about what it may weigh.
    """
    grown = {}

    def mutate(root):
        grown["office-team"] = _grow_past_the_record(root, "office-team")

    output = _validate_over_a_copy(tmp_path, mutate)
    # ON THE FAILURE CHANNEL, not merely somewhere in the output. Measured with the rule reverted
    # to `print("  [warn] …")`: growing a constitution also trips "VERSION not bumped", so
    # `"VALIDATION FAILED" in output` was true and this test stayed GREEN through the exact
    # regression it exists for.
    match = _mentions_size("office-team", output, failures_only=True)
    assert match, (
        "a package one byte over its record was not FAILED — a size rule that only warns is the "
        "one this round replaced:\n%s" % output)
    assert int(match.group(2)) == lead_package.ceiling(_kit_dir("office-team")), match.group(0)
    assert int(match.group(1)) == grown["office-team"], match.group(0)
    assert not _LINE_COMPLAINT.search(output), output


def test_a_lead_package_with_no_record_is_a_failure_and_not_a_free_pass(tmp_path):
    """The hole a ratchet must not have: the kit nobody has recorded yet.

    "No record" is the only state in which a `size > ceiling` comparison has nothing to compare
    against, and the tempting implementations both fail open — `None` compared with `>` raises on
    Python 3 (a crash the validator would report as something else entirely) and a default of
    `sys.maxsize` would let that one kit grow without limit forever. Measured here on the real
    program: deleting one kit from the record file makes THAT kit a failure and leaves the other
    two alone.
    """
    def mutate(root):
        path = str(root / "tools" / os.path.basename(lead_package.RECORD))
        with io.open(path, encoding="utf-8") as handle:
            record = json.load(handle)
        record["sizes"].pop("research-team")
        with io.open(path, "w", encoding="utf-8") as handle:
            json.dump(record, handle)

    output = _validate_over_a_copy(tmp_path, mutate)
    # NOTHING ELSE IN THIS TREE IS BROKEN — no file was touched, so "VERSION not bumped" cannot
    # stand in for the failure this asks about, and the failure list must be exactly this one.
    assert _mentions_size("research-team", output, failures_only=True), (
        "an unrecorded package was not FAILED — that kit could then grow unwatched:\n%s" % output)
    for other in ("dev-team", "office-team"):
        assert not _mentions_size(other, output), (
            "%s is recorded and within it and was reported anyway:\n%s" % (other, output))


def test_the_recorder_reports_a_drift_before_it_records_one(tmp_path):
    """The command that moves the record, run as a PROCESS over a copy — the other half of the
    instrument, and the half nothing would otherwise measure.

    Three properties, because a recorder that gets any of them wrong turns the ratchet into a
    formality: without `--write` it reports and exits non-zero (so a forgotten re-record is visible
    in a script), with `--write` and no `--note` it refuses (the journal line is the point), and
    with both it writes a record that makes the validator green again AND leaves a journal line
    naming the direction and the two figures.
    """
    root = tmp_path / "tree"
    (root / "tools").mkdir(parents=True)
    (root / "docs" / "reviews").mkdir(parents=True)
    shutil.copytree(TEAM_KITS, str(root / "team-kits"),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for path in glob.glob(os.path.join(ROOT, "tools", "*.py")):
        shutil.copy(path, str(root / "tools" / os.path.basename(path)))
    shutil.copy(lead_package.RECORD, str(root / "tools" / os.path.basename(lead_package.RECORD)))
    shutil.copy(os.path.join(ROOT, "docs", "reviews", "phase0-disposition.md"),
                str(root / "docs" / "reviews" / "phase0-disposition.md"))
    grown = _grow_past_the_record(root, "dev-team", over=64)

    def run(*argv):
        return subprocess.run([sys.executable,
                               str(root / "tools" / "record_lead_package_sizes.py")] + list(argv),
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=600)

    reported = run()
    assert reported.returncode == 1, reported.stdout + reported.stderr
    assert "GREW" in reported.stdout and str(grown) in reported.stdout, reported.stdout

    refused = run("--write")
    assert refused.returncode == 2, refused.stdout + refused.stderr
    assert lead_package.records(str(root / "tools" / os.path.basename(lead_package.RECORD))) \
        ["dev-team"] != grown, "the record moved although the note was missing"

    accepted = run("--write", "--note", "a probe grew the package on purpose")
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    assert lead_package.records(str(root / "tools" / os.path.basename(lead_package.RECORD))) \
        ["dev-team"] == grown
    journal = io.open(str(root / "docs" / "reviews" / "phase0-disposition.md"),
                      encoding="utf-8").read()
    assert "a probe grew the package on purpose" in journal and "GREW" in journal, (
        "the recorder wrote a record and no journal line")
    # and the validator is green again over the very tree the recorder just recorded
    after = subprocess.run([sys.executable, str(root / "tools" / "validate.py")],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=600)
    assert not _mentions_size("dev-team", after.stdout + after.stderr), \
        after.stdout + after.stderr


# ================================================ 2. the relocation: what no longer loads
def test_the_relocated_table_is_outside_every_route_this_repo_has_into_a_session(tmp_path):
    """The first condition on the relocation, measured as three absences rather than claimed once.

    A session's fixed load, as far as this repo controls it, has exactly three sources:

      * THE IMPORT CHAIN. The scaffold writes `CLAUDE.md` as a two-line shim over `AGENTS.md`, and
        an `@path` line is what pulls a further file in. The chain is followed transitively, and
        what is compared is the target's BASENAME rather than a resolved path: in a project the
        constitution sits at the repo root and the reference under `.claude/hooks/`, so the
        realistic mistake is `@.claude/hooks/ENFORCEMENT.md` — a spelling that resolves to nothing
        inside the kit source and would walk straight past a check that resolved before comparing.
      * THE PRELOADED SKILLS. Every agent's frontmatter `skills:` names what arrives with that
        role. A skill directory is loaded through its `SKILL.md`; the reference is not one.
      * THE SESSION-START HOOK. `session_status.py` is the only thing that injects text into a
        starting session, and it is run here AS A PROCESS against a scaffolded project outside this
        repo — because what a session receives is a program's output, not a function's return.

    The reference's own CONTENT is what is searched for, not its filename: a hook that pasted the
    table into the briefing without naming the file would defeat a filename check completely.
    """
    for kit in KITS:
        reference = _reference_path(kit)
        assert os.path.isfile(reference), reference

        # (a) the import chain, followed transitively from the shim the scaffold writes
        chain, seen, imported_names = \
            [os.path.join(_kit_dir(kit), "constitution", "AGENTS.md")], set(), set()
        while chain:
            current = chain.pop()
            if current in seen or not os.path.isfile(current):
                continue
            seen.add(current)
            with io.open(current, encoding="utf-8") as handle:
                for line in handle:
                    imported = re.match(r"^@(\S+)", line.strip())
                    if imported:
                        imported_names.add(os.path.basename(
                            imported.group(1).replace("\\", "/")))
                        chain.append(os.path.join(os.path.dirname(current), imported.group(1)))
        assert _reference_name(kit) not in imported_names, (
            "%s: the constitution's import chain pulls the reference into every session" % kit)

        # (b) the preloaded skills — a skill is loaded through SKILL.md, and the reference is not
        # inside any skill directory at all
        yaml = pytest.importorskip("yaml")
        for path in sorted(glob.glob(os.path.join(_kit_dir(kit), "agents", "*.md"))):
            with io.open(path, encoding="utf-8") as handle:
                raw = handle.read()
            front = yaml.safe_load(raw.split("---", 2)[1]) if raw.count("---") >= 2 else {}
            for skill in (front or {}).get("skills") or []:
                skill_dir = os.path.join(_kit_dir(kit), "skills", str(skill))
                assert not os.path.abspath(reference).startswith(os.path.abspath(skill_dir)), (
                    "%s: the reference sits inside preloaded skill %s" % (kit, skill))

    # (c) the session-start hook, as a real process over a real project
    with io.open(_reference_path("dev-team"), encoding="utf-8") as handle:
        rows = [line for line in handle.read().splitlines()
                if line.startswith("| `") and len(line) > 200]
    assert rows, "the reference carries no table rows to look for"

    home, repo = tmp_path / "home", tmp_path / "repo"
    (repo / ".claude").mkdir(parents=True)
    (home / ".claude").mkdir(parents=True)
    (repo / "CLAUDE.md").write_text("<!-- agents-and-skills:team-kit dev-team -->\n@AGENTS.md\n",
                                    encoding="utf-8")
    shutil.copy(os.path.join(_kit_dir("dev-team"), "constitution", "AGENTS.md"),
                str(repo / "AGENTS.md"))
    shutil.copytree(os.path.join(_kit_dir("dev-team"), "hooks"), str(repo / ".claude" / "hooks"),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    environment = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo), HOME=str(home),
                       USERPROFILE=str(home),
                       CLAUDE_CONFIG_DIR=os.path.join(str(home), ".claude"))
    environment.pop("TEAM_KIT_PROVIDER", None)
    result = subprocess.run(
        [sys.executable, str(repo / ".claude" / "hooks" / "session_status.py")],
        input=json.dumps({"cwd": str(repo), "hook_event_name": "SessionStart",
                          "session_id": "s"}),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=environment, timeout=120)
    assert result.returncode == 0, result.stderr
    briefing = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    assert briefing.strip(), "the session-start hook said nothing — the control is worthless"
    for row in rows:
        assert row not in briefing, "the session briefing carries a row of the relocated table"


def test_the_reference_describes_every_mechanism_the_constitution_names(tmp_path):
    """The second condition, first half: the content really is there, for every mechanism.

    "Relocated" is only true if nothing was left behind on the way. The constitution keeps the
    NAMES (that floor is `test_shortening_net.py::
    test_every_registered_hook_is_anchored_in_its_kits_constitution`); this is the other end — each
    of those names is IN THE TABLE the refusals point at, so a role sent there finds its mechanism
    rather than an index.

    THE WHOLE ROW COUNTS, NOT ITS FIRST CELL, and that is a property of the table rather than a
    convenience: six of the dev mechanisms (`gate_dispatch`, `gate_write_scope`, `gate_approval`,
    `gate_push_token`, `gate_shell_hygiene`, `guard_memory_budget`) are described inside the row of
    the older guard they extend — "Plus (V2, spec II.4) `gate_dispatch`: …" — because that is where
    the rule they belong to is. Asking for a left-cell entry would demand a restructuring of the
    table, which is the shortening's decision and not this round's. THE LIMIT that leaves: a name
    that appears only as a cross-reference inside somebody else's row counts as described. What
    this test can still catch is the case it was written for — a mechanism the constitution names
    and the reference lost entirely on the way out.
    """
    for kit in KITS:
        with io.open(os.path.join(_kit_dir(kit), "constitution", "AGENTS.md"),
                     encoding="utf-8") as handle:
            constitution = handle.read()
        with io.open(_reference_path(kit), encoding="utf-8") as handle:
            rows = [line for line in handle.read().splitlines() if line.startswith("|")]
        described = set()
        for row in rows:
            described |= set(re.findall(r"`([a-z][a-z0-9_]+)`", row))
        shipped = {name[:-3] for name in os.listdir(os.path.join(_kit_dir(kit), "hooks"))
                   if name.endswith(".py") and not name.startswith("_")}
        named = {name for name in shipped
                 if re.search(r"\b%s\b" % re.escape(name), constitution)}
        assert named, "%s: the constitution names no mechanism at all" % kit
        missing = sorted(named - described)
        assert not missing, (
            "%s: the constitution names these mechanisms and the reference the refusals point at "
            "describes none of them: %s" % (kit, ", ".join(missing)))


# ================================ 2b. the reference is reachable from the refusal that needs it
def _preamble():
    sys.path.insert(0, os.path.join(_kit_dir("dev-team"), "hooks"))
    import _kernel
    return _kernel.GATE_PREAMBLE


def test_no_shipped_hook_refuses_outside_the_one_funnel():
    """Universality, by AST over every shipped hook of every kit.

    The pointer is appended in `_compat.stop`, so "every refusal names the reference" is only true
    while `stop` is the only way a hook refuses. A hook that writes stderr and exits 2 by hand is
    exactly the shape that was there before this round — six guards in dev and research, seven in
    office, nine refusal sites — and each of them would have been a refusal that leaves the reader
    with no idea where to look.

    THE ONE EXEMPTION IS DERIVED, not listed: `_kernel.GATE_PREAMBLE` is the verbatim block every
    V2 gate opens with, and its `sys.exit(2)` fires when `import _kernel` FAILED — routing that
    through a helper of the module that just failed to load is the one place a funnel must not
    reach. So the preamble text is subtracted from the source before the walk, which means a gate
    that carries it stays covered everywhere else in the file.
    """
    preamble = _preamble().rstrip("\n")
    offenders = []
    for kit in KITS:
        hooks = os.path.join(_kit_dir(kit), "hooks")
        for name in sorted(os.listdir(hooks)):
            if not name.endswith(".py") or name.startswith("_"):
                continue        # `_`-prefixed modules cannot be registered (`_gate.py` refuses)
            with io.open(os.path.join(hooks, name), encoding="utf-8") as handle:
                source = handle.read()
            body = source.replace(preamble, "")
            for node in ast.walk(ast.parse(body, filename=name)):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                        and node.func.attr == "exit" \
                        and isinstance(node.func.value, ast.Name) and node.func.value.id == "sys" \
                        and node.args and isinstance(node.args[0], ast.Constant) \
                        and node.args[0].value == 2:
                    offenders.append("%s/%s" % (kit, name))
    assert not offenders, (
        "these hooks refuse without going through `_compat.stop`, so their message cannot carry "
        "the reference: %s" % ", ".join(sorted(set(offenders))))


def _refusal(name, payload, project, kit="dev-team"):
    hooks = os.path.join(_kit_dir(kit), "hooks")
    environment = dict(os.environ, CLAUDE_PROJECT_DIR=str(project),
                       HARNESS_KERNEL_PATH=TEAM_KITS)
    return subprocess.run([sys.executable, os.path.join(hooks, name)],
                          input=json.dumps(payload), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=environment, timeout=120)


def test_a_real_refusal_hands_the_reader_the_reference(tmp_path):
    """And the proof that the funnel EMITS it, from real hook processes.

    Three refusals, one per way a shipped hook reaches `stop()`, because a funnel that is universal
    on paper and silent in practice is the failure this pair of tests exists to make impossible:

      * a legacy guard's own `block()` (`guard_no_adhoc` on an invented status file) — the six
        guards this round rerouted;
      * a gate through `_kernel.block` (`guard_harness_selfmod` on the settings file) — the V2
        path, which every `gate_*` shares;
      * the bounded-read overflow inside `_compat.load` itself, which refuses before any hook logic
        runs and was the one refusal with no gate behind it to name a file.

    What is asserted is the file NAME rather than a sentence: the wording of the note is prose and
    will be reworded, the name is the thing a reader needs to open.
    """
    reference = _reference_name("dev-team")
    (tmp_path / ".claude").mkdir(parents=True)
    (tmp_path / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
    (tmp_path / "project_memory").mkdir(parents=True)

    legacy = _refusal("guard_no_adhoc.py",
                      {"tool_name": "Write", "cwd": str(tmp_path),
                       "tool_input": {"file_path": str(tmp_path / "IMPLEMENTATION_SUMMARY.txt"),
                                      "content": "done"}}, tmp_path)
    assert legacy.returncode == 2, legacy.stdout + legacy.stderr
    assert reference in legacy.stderr, legacy.stderr

    v2 = _refusal("guard_harness_selfmod.py",
                  {"tool_name": "Write", "cwd": str(tmp_path),
                   "tool_input": {"file_path": str(tmp_path / ".claude" / "settings.json"),
                                  "content": "{}"}}, tmp_path)
    assert v2.returncode == 2, v2.stdout + v2.stderr
    assert reference in v2.stderr, v2.stderr

    sys.path.insert(0, os.path.join(_kit_dir("dev-team"), "hooks"))
    import _compat
    overflow = _refusal("guard_harness_selfmod.py",
                        {"tool_name": "Write", "cwd": str(tmp_path),
                         "tool_input": {"file_path": str(tmp_path / ".claude" / "settings.json"),
                                        "content": "x" * (_compat.STDIN_LIMIT + 1024)}}, tmp_path)
    assert overflow.returncode == 2 and "stdin bound" in overflow.stderr, overflow.stderr
    assert reference in overflow.stderr, overflow.stderr


def test_the_reference_note_points_at_the_file_beside_the_hook_that_printed_it(tmp_path):
    """The path in the note must be the INSTALLED one, not a path in this repo.

    A pointer is only worth the bytes it costs if it resolves where the reader is. The refusal is
    produced from a COPY of the hook bundle in a scratch project, and the path the message prints
    must name that copy — which is what a project's `.claude/hooks/` is — and must be a file that
    is really there.
    """
    project = tmp_path / "repo"
    (project / ".claude").mkdir(parents=True)
    shutil.copytree(os.path.join(_kit_dir("dev-team"), "hooks"),
                    str(project / ".claude" / "hooks"),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (project / ".claude" / "settings.json").write_text("{}", encoding="utf-8")

    environment = dict(os.environ, CLAUDE_PROJECT_DIR=str(project),
                       HARNESS_KERNEL_PATH=TEAM_KITS)
    result = subprocess.run(
        [sys.executable, str(project / ".claude" / "hooks" / "guard_no_adhoc.py")],
        input=json.dumps({"tool_name": "Write", "cwd": str(project),
                          "tool_input": {"file_path": str(project / "PR-0001_status.md"),
                                         "content": "x"}}),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=environment, timeout=120)
    assert result.returncode == 2, result.stdout + result.stderr
    expected = os.path.join(str(project / ".claude" / "hooks"), _reference_name("dev-team"))
    assert expected in result.stderr, (
        "the refusal points somewhere other than the bundle it ran out of:\n%s" % result.stderr)
    assert os.path.isfile(expected)


# ============== 3. a claim of reach names the session it holds for (FR-0063) ==============
#
# A TOTALITY OVER WHAT THIS APPARATUS REACHES. This is a FORMULATION rather than a concept, the way
# `test_hooks.py::_SURFACE_DENIAL_RX` is one, and for the same measured reason: "every"/"no" is how
# this corpus says almost anything, so what separates a claim of REACH from all of them is the noun
# the quantifier governs — the apparatus's own two subjects, a tool write and a mechanism that runs.
# Both ends of the formulation are driven by `test_the_reach_reader_sees_the_claims_it_was_written_
# for`: the three sentences that shipped before 2026-08-30 must still read as claims, and ordinary
# prose must not. WHAT IT DOES NOT SEE is a claim that says the same thing in other nouns ("every
# write a tool performs"): a single sentence rewritten that way leaves the reader silently, and only
# the per-text floor in the first test catches a whole text doing it. Measured by this round's
# verifier, and open.
_TOTAL_REACH_RX = re.compile(r"\b(?:every|any|all|no)\s+(?:tool write|mechanism that runs)", re.I)

# THE BOUND IS A PROPERTY: a sentence that says whether this project's SETTINGS LOAD. Deliberately
# not a flag — three members of that class are measured and the client can gain a fourth, so a
# spelling here would be the same enumeration defect one level down. That half is not trusted
# either: `test_no_statement_of_the_bound_names_a_flag` reads it.
_SETTINGS_RX = re.compile(r"project'?s? settings", re.I)
_LOADING_RX = re.compile(r"\bload(?:s|ed|ing)?\b", re.I)

# A POINTER TO THE SECTION THAT CARRIES THE BOUND, in the file the sentence stands in. §0 is the
# constitution's first section and, since this round, the reference's floor note.
# `test_the_bound_lives_in_the_section_the_pointers_name` is what keeps it from aiming at nothing.
_BOUND_SECTION = "0"
_BOUND_POINTER = "§" + _BOUND_SECTION

# A CLIENT FLAG as a reader sees it in these texts: a long option word. `-f` is not in here on
# purpose — a single dash is `-p`, `-q` and half the shell examples in this tree, and a rule that
# fired on those would be noise rather than a check.
_FLAG_RX = re.compile(r"(?<![\w-])--[A-Za-z][\w-]+")


def _enforcement_story(kit):
    """The two texts that STATE this kit's enforcement: the constitution and the reference.

    The same union `test_shortening_net.py::test_no_enforcement_text_claims_a_hook_that_no_
    registration_starts` uses for the "must not lie" direction, and for its reason: the
    constitution is what a session always carries, the reference is what a role is handed at the
    moment it has been refused. Both are read here; nothing else is, and that is a NAMED limit —
    the same absolute claim still stands in the three LEAD agent files, in one specialist agent
    file, in one role SKILL, in `README.md` and in the two global entry files under `user/`, none
    of which this round corrected. The direction of that residue is the uncomfortable one: those
    lead files load at every session start and every spawn, while the reference carrying the floor
    loads nothing at all.
    """
    return (os.path.join(_kit_dir(kit), "constitution", "AGENTS.md"), _reference_path(kit))


def _sentences(text):
    """The text as sentences, with a markdown line break treated as a space.

    A sentence, not a paragraph: the unit was a whole block until a measured defect showed that a
    file-wide reader was satisfied by a phrase four hundred lines away
    (`test_hooks.py::_markdown_blocks`), and the same argument taken one step further says the
    claim and its bound belong in one sentence. The price is that a bound stated in the NEXT
    sentence does not count, which is why the pointer below exists as the second way to satisfy it.
    """
    return re.split(r"(?<=[.!?])\s+", re.sub(r"[ \t]*\n[ \t]*", " ", text))


def _claims_total_reach(sentence):
    return bool(_TOTAL_REACH_RX.search(sentence))


def _states_the_bound(sentence):
    """Does this sentence say whether the project's settings load? — the running predicate."""
    return bool(_SETTINGS_RX.search(sentence) and _LOADING_RX.search(sentence))


def _section(text, number):
    """The `## <number>.` section of a markdown text, heading included, or None."""
    lines = text.splitlines()
    start = next((index for index, line in enumerate(lines)
                  if re.match(r"^##+\s*%s\." % re.escape(number), line)), None)
    if start is None:
        return None
    stop = next((index for index in range(start + 1, len(lines))
                 if lines[index].startswith("## ")), len(lines))
    return "\n".join(lines[start:stop])


def test_every_claim_of_reach_names_the_session_it_holds_for():
    """The correction of 2026-08-30, in the form that cannot silently be taken back.

    THE DEFECT, measured against the running client (TSK-0094): a start mode that does not load the
    project settings removes every registration this kit owns, while the file tools keep writing
    inside the project. Three shipped sentences claimed the opposite without a word of condition —
    `gate_write_scope` "refuses every tool write there", the state directory "WRITE-LOCKED against
    every tool write", and the hook inventory "complete in both directions". A role that reads one
    of them believes a fence that a session can simply start without.

    WHAT IS DEMANDED is the smallest thing that cannot be true while the condition is hidden: the
    sentence says whether the project's settings load, or it points at the section of its own file
    that does. Not that the claim is CORRECT — no reader here can decide that — but that it is
    bounded, which is the half that went missing.

    WHAT THE PREDICATE IS, so nothing is credited to it that it does not do: `_states_the_bound` is
    a CO-OCCURRENCE over one sentence — the project's settings and their loading are both named in
    it. It reads neither POLARITY nor ATTACHMENT, and both were driven by this round's verifier: a
    §0 rewritten to say the settings load anyway and every mechanism below still runs passes, and
    so does a sentence whose condition belongs to a DIFFERENT claim standing beside the absolute
    one. So this turns a MISSING condition into a red test and leaves a WRONG one to a reader. The
    pointer (`§0`) is that same instrument one file wider and inherits exactly the same blindness —
    `test_the_bound_lives_in_the_section_the_pointers_name` establishes that §0 addresses the
    condition, not that it answers it correctly.
    """
    naked, seen = [], {}
    for kit in KITS:
        for path in _enforcement_story(kit):
            where = os.path.relpath(path, ROOT).replace(os.sep, "/")
            with io.open(path, encoding="utf-8") as handle:
                text = handle.read()
            seen[where] = 0
            for sentence in _sentences(text):
                if not _claims_total_reach(sentence):
                    continue
                seen[where] += 1
                if _states_the_bound(sentence) or _BOUND_POINTER in sentence:
                    continue
                naked.append("%s: %s" % (where, sentence.strip()[:220]))
    assert not naked, (
        "these sentences claim what the apparatus reaches without saying whether this project's "
        "settings load, and without pointing at %s where that stands:\n  %s"
        % (_BOUND_POINTER, "\n  ".join(naked)))
    # A FLOOR PER TEXT, because everything above is vacuously true over an empty set — and because
    # a GLOBAL floor was measured worthless in exactly this round: rewording the single reach claim
    # of two of these files ("ANY tool write into" -> "each and every write a tool performs into")
    # dropped both texts out of the reader while the sum stayed comfortably over any total. The
    # reader is a two-noun formulation and this is the tripwire on its far end. Going red does not
    # say which of the two happened, and the message must not pretend to: a text that stops
    # claiming a totality is a legitimate change, and the answer is a second look either way.
    silent = sorted(where for where, count in seen.items() if not count)
    assert not silent, (
        "these enforcement texts carry no claim of reach at all — either they stopped claiming "
        "one, or the reader stopped seeing the words they use:\n  " + "\n  ".join(silent))


def test_the_bound_lives_in_the_section_the_pointers_name():
    """A pointer is worth the section it resolves to, and three copies are worth their identity.

    Two halves, and the second is why three copies of one statement are safe here at all: §0 of
    every one of the six texts addresses the condition, and the reference's floor note is
    BYTE-IDENTICAL across the three kits. A statement that lives in three files drifts into three
    statements; the identity assertion is what keeps it one.

    ADDRESSES, not "states correctly" — the same co-occurrence predicate as its sibling, with the
    same blindness to polarity, and this docstring said the stronger word until the verifier of this
    round inverted §0 byte-identically in all three kits and measured it green.
    """
    floors = {}
    for kit in KITS:
        for path in _enforcement_story(kit):
            with io.open(path, encoding="utf-8") as handle:
                section = _section(handle.read(), _BOUND_SECTION)
            where = os.path.relpath(path, ROOT).replace(os.sep, "/")
            assert section, "%s carries no %s section for its pointers to resolve to" % (
                where, _BOUND_POINTER)
            assert any(_states_the_bound(sentence) for sentence in _sentences(section)), (
                "%s %s does not say whether this project's settings load, so every sentence "
                "pointing at it points at nothing:\n%s" % (where, _BOUND_POINTER, section[:400]))
        floors[kit] = _section(io.open(_reference_path(kit), encoding="utf-8").read(),
                               _BOUND_SECTION)
    assert len(set(floors.values())) == 1, (
        "the floor note differs between kits, so it is three statements: %s"
        % ", ".join(sorted(floors)))


def test_no_statement_of_the_bound_names_a_flag():
    """The boundary is a PROPERTY of the start mode, never one spelling of it.

    Three members of the class are measured and they agree on nothing except this property — one
    drops the secret-read denial, another brings a shell and writes outside the working directory.
    A sentence that named a flag would teach a reader to check for that flag, which is the
    enumeration defect one level down and the reason the measurement document itself was named away
    from one. So: a sentence that states the bound names no long option. Ordinary command lines
    keep their flags — the rule is about the sentence that carries the boundary, not about the
    paragraph it stands in.
    """
    offenders = []
    for kit in KITS:
        for path in _enforcement_story(kit):
            with io.open(path, encoding="utf-8") as handle:
                for sentence in _sentences(handle.read()):
                    if not _states_the_bound(sentence):
                        continue
                    for flag in _FLAG_RX.findall(sentence):
                        offenders.append("%s: %s (in %r)"
                                         % (os.path.relpath(path, ROOT).replace(os.sep, "/"),
                                            flag, sentence.strip()[:160]))
    assert not offenders, (
        "these sentences state the start-mode boundary and name a flag as its subject — say the "
        "property (settings that do not load), not a spelling of it:\n  " + "\n  ".join(offenders))


# The three claims as they SHIPPED until 2026-08-30, each CUT at the point where the rest of the
# sentence is a kit-specific file list or the inventory itself — the CLAIM is verbatim, the tail is
# not, and saying "verbatim" of the whole was itself a small false statement (found by this round's
# verifier). They are the control of the reader above: the corpus assertion is vacuously true once
# they are gone, and a reader nobody re-measures is how they survived four releases.
_CLAIMS_AS_THEY_SHIPPED = (
    "`gate_write_scope` refuses every tool write there, and every shell pipeline whose COMMAND "
    "LINE names the path.",
    "**The state directory is WRITE-LOCKED against every tool write, and has exactly ONE writer:** "
    "`gate_write_scope` refuses every tool write under `project_memory/` bar `staging/<task-id>/`.",
    "WHAT RUNS HERE, complete in both directions — no mechanism that runs is missing from this "
    "list, and no name on it is one no registration starts: `clear_handover_marker`.",
)

# Sentences from the same texts that are NOT claims of reach, so "call everything a claim" is not a
# way out: a rule about the ONE writer, and a statement about where a refusal points.
_NOT_CLAIMS_OF_REACH = (
    "The kernel is the only writer of `project_memory/`.",
    "Every refusal a gate writes prints the path of this file, so the moment you need the table is "
    "the moment you are handed its location.",
)


def test_the_reach_reader_sees_the_claims_it_was_written_for():
    """Both ends of the formulation, driven over sentences instead of trusted.

    A reader that answered "no claim" to everything would make the corpus check above green over
    any text at all; one that answered "claim" to everything would demand the bound in every
    sentence of six documents. Both directions are driven here, and so is the bound predicate — the
    corrected sentence is recognised as bounded, and the same sentence with the qualifier taken out
    is not.
    """
    for sentence in _CLAIMS_AS_THEY_SHIPPED:
        assert _claims_total_reach(sentence), (
            "the reader no longer sees the shape it was written for: %r" % sentence)
        assert not _states_the_bound(sentence) and _BOUND_POINTER not in sentence, (
            "the pre-round sentence reads as bounded, so the check would have passed over the "
            "defect it was written for: %r" % sentence)
    for sentence in _NOT_CLAIMS_OF_REACH:
        assert not _claims_total_reach(sentence), (
            "the reader calls ordinary prose a claim of reach: %r" % sentence)

    corrected = ("No role writes a state file with an editor, yours included: in a session that "
                 "loads this project's settings, `gate_write_scope` refuses every tool write "
                 "there, and every shell pipeline whose COMMAND LINE names the path.")
    assert _claims_total_reach(corrected) and _states_the_bound(corrected), corrected
    assert not _states_the_bound(corrected.replace("in a session that loads this project's "
                                                   "settings, ", "")), (
        "the bound predicate answers yes to the sentence with the qualifier removed")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))

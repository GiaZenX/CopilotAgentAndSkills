#!/usr/bin/env python3
"""What loads at every session start, and how big it may get — the two halves of one question.

TWO DECISIONS ARE MEASURED HERE.

  1. THE SIZE STATEMENT IS BYTES, AND THERE IS ONLY ONE OF IT. `tools/validate.py` used to fail a
     constitution over 220 LINES. Measured, that limit said nothing about size: all three
     constitutions held it only because 31 to 46 of their lines ran between 110 and 1 899
     characters — reflowed to 100 columns the same texts are 383 / 368 / 394 lines — and a
     compaction pilot cut 24.9 % of the bytes while its line count rose from 20 to 36. So the line
     ceiling pushed AGAINST the byte budget standing beside it. It is gone, and nothing per-file
     replaced it, because no split of the package budget across three files follows from anything.
     What remains is `tools/lead_package.py`: one number, one derivation of which files it applies
     to, read by `validate.py` and asserted against the sentence in the spec.

  2. THE §2 HOOK TABLE LEFT THE SESSION-FIXED LOAD WITHOUT LEAVING THE PROJECT. It is
     `hooks/ENFORCEMENT.md` now, and a relocation is only worth anything if BOTH halves hold: the
     target must really not load with the session, and the content must be reachable at the moment
     it is needed. The first half is measured as three separate absences (import chain, preloaded
     skills, session-start injection) rather than asserted about the platform; the second is
     measured by making every refusal a shipped hook writes carry the file's path, and then reading
     that path out of REAL hook processes.

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
def test_the_spec_states_the_byte_budget_the_validator_enforces():
    """II.5 must spell the number `validate.py` compares against — the third spelling is how this
    budget came to exist as "25 KB", `25 * 1024` and "25 000" at the same time.

    The AUTHORITY is the constant, not the prose: the document is searched for the value
    `lead_package.MAX_BYTES` renders to, so moving the constant moves what the spec has to say.
    Both spellings are accepted (`25600` and the thin-space grouped `25 600` the German prose uses)
    because which one a sentence carries is typography, and a check that dictated it would be
    asserting a style rather than a fact.

    IN THE SENTENCE THAT STATES THE BUDGET, not merely somewhere in II.5. Measured on a copy: a
    version whose budget line read "≤25 KB" again still passed a section-wide search, because the
    paragraph explaining why no PER-FILE number replaces the line ceiling mentions 25 600 in
    passing. A number that is present but not where the rule is stated is exactly the drift this
    check exists against.
    """
    with io.open(SPEC, encoding="utf-8") as handle:
        prose = re.sub(r"\s+", " ", handle.read())
    section = prose.split("## II.5 ", 1)
    assert len(section) == 2, "the spec has no II.5 section to read"
    body = section[1].split("## II.6", 1)[0]
    plain = str(lead_package.MAX_BYTES)
    grouped = "%s %s" % (plain[:-3], plain[-3:])
    statement = body.split("Lead-Instruktionspaket", 1)
    assert len(statement) == 2, "II.5 no longer states a Lead-Instruktionspaket budget at all"
    statement = statement[1][:200]
    assert plain in statement or grouped in statement, (
        "the sentence stating the lead-package budget does not carry the number the validator "
        "enforces (%s): %r" % (plain, statement))
    # ...and the number is not merely mentioned somewhere: the old prose said "≤150 Zeilen" for the
    # constitution and the lead SKILL, and leaving that in beside the byte budget would restore the
    # contradiction this round removed.
    assert "≤150 Zeilen" not in body.replace(" ", "") or "gestrichen" in body, (
        "II.5 still carries the per-file line budget as a live requirement")


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


def test_the_budget_is_a_byte_comparison_over_the_files_the_kit_names(tmp_path):
    """The floor under the number: `size()` counts bytes of the files `files()` derives, and the
    comparison is strict.

    Built over a synthetic kit so the boundary can be hit exactly. The lead is taken from
    `settings.json` here as it is in production, so a derivation that ignored the setting and
    hard-coded a role name would report 0 for this kit and pass every "under budget" assertion.
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

    # exactly at the ceiling is NOT over it, one byte past it is
    (kit / "constitution" / "AGENTS.md").write_text(
        "c" * (lead_package.MAX_BYTES - 1000), encoding="utf-8")
    assert lead_package.size(str(kit)) == lead_package.MAX_BYTES
    assert not lead_package.size(str(kit)) > lead_package.MAX_BYTES
    (kit / "constitution" / "AGENTS.md").write_text(
        "c" * (lead_package.MAX_BYTES - 999), encoding="utf-8")
    assert lead_package.size(str(kit)) > lead_package.MAX_BYTES

    # a lead the settings do not name contributes nothing — the subject follows the kit
    (kit / "settings" / "settings.json").write_text(json.dumps({}), encoding="utf-8")
    assert lead_package.size(str(kit)) == lead_package.MAX_BYTES - 999
    assert lead_package.on_demand_files(str(kit)) == ()


def _validate_over_a_copy(tmp_path, mutate):
    """Run the SHIPPED `tools/validate.py` as a process over a copy of the tree, outside the repo.

    A copy, because the subject is a constitution this repo must not have: the only honest way to
    ask "does the validator still fail this" is to build the file it would fail and hand it to the
    program. `validate.py` derives its ROOT from its own location, so the copy needs `team-kits/`
    and `tools/*.py` and nothing else; the git-tracking check degrades to "moot" without a `.git`,
    which it is written to do.
    """
    root = tmp_path / "tree"
    (root / "tools").mkdir(parents=True)
    shutil.copytree(TEAM_KITS, str(root / "team-kits"),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for path in glob.glob(os.path.join(ROOT, "tools", "*.py")):
        shutil.copy(path, str(root / "tools" / os.path.basename(path)))
    mutate(root)
    result = subprocess.run([sys.executable, str(root / "tools" / "validate.py")],
                            capture_output=True, text=True, encoding="utf-8", errors="replace",
                            timeout=600)
    return result.stdout + result.stderr


def _four_hundred_short_lines(root, kit="office-team"):
    """Replace one kit's constitution with 400 lines nobody could call long.

    The office kit, because its package is the smallest: 400 lines of this width leave the whole
    package UNDER the budget, so the same fixture answers both directions — the line count must not
    matter, and the byte total must.
    """
    path = root / "team-kits" / kit / "constitution" / "AGENTS.md"
    head = path.read_text(encoding="utf-8").splitlines()[0]
    body = [head] + ["rule %03d: keep this short." % index for index in range(399)]
    path.write_text("\n".join(body) + "\n", encoding="utf-8")
    return path


_LINE_COMPLAINT = re.compile(r"office-team: constitution has \d+ lines")
_BUDGET_COMPLAINT = re.compile(r"office-team: lead instruction package is (\d+) bytes \(> (\d+)")


def test_a_constitution_of_four_hundred_short_lines_is_not_a_finding(tmp_path):
    """The half that is RED without this round's change.

    Under the old rule this exact tree failed with "office-team: constitution has 400 lines
    (> 220)" — a text 12 KB smaller than the one it replaced, rejected for being SHORTER per line.
    The assertion is over the validator's real output, and the second half of it is the control:
    the run must still have measured this kit's package, or "no line complaint" would only mean the
    validator never looked.
    """
    output = _validate_over_a_copy(tmp_path, lambda root: _four_hundred_short_lines(root))
    assert not _LINE_COMPLAINT.search(output), (
        "the validator still judges a constitution by its line count:\n%s"
        % "\n".join(line for line in output.splitlines() if "lines" in line))
    assert not _BUDGET_COMPLAINT.search(output), (
        "the shortened package is under the budget and was reported anyway:\n%s" % output)
    # the control: the two kits that were NOT shortened are still measured and still over
    assert re.search(r"dev-team: lead instruction package is \d+ bytes", output), (
        "the validator did not weigh any package at all — the fixture proves nothing:\n%s" % output)


def test_a_lead_package_over_the_budget_is_reported_with_the_number_from_the_definition(tmp_path):
    """The other half: the budget must actually bite, and the figure it bites at must be the one
    `lead_package.MAX_BYTES` holds.

    The same 400-line constitution as above, padded past the ceiling. Two things are read off the
    message — the threshold (it must be the constant, not a copy of it) and the measured size (it
    must be what `lead_package.size` computes over that same tree, so the validator and the pin
    cannot disagree about what the package IS).
    """
    def mutate(root):
        path = _four_hundred_short_lines(root)
        kit = os.path.dirname(os.path.dirname(str(path)))
        short = lead_package.size(kit)
        with io.open(str(path), "a", encoding="utf-8") as handle:
            handle.write("x" * (lead_package.MAX_BYTES - short + 1))

    output = _validate_over_a_copy(tmp_path, mutate)
    match = _BUDGET_COMPLAINT.search(output)
    assert match, "a package one byte over the budget was not reported:\n%s" % output
    assert int(match.group(2)) == lead_package.MAX_BYTES, match.group(0)
    assert int(match.group(1)) == lead_package.MAX_BYTES + 1, match.group(0)
    assert not _LINE_COMPLAINT.search(output), output


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


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))

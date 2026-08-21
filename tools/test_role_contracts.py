#!/usr/bin/env python3
"""What a specialist hands back, HOW it hands it back, and what a role text may claim.

FOUR SUBJECTS, ONE HABIT: each is asked of the running code and never of a list in this file.

  * THE HAND-BACK CONTRACT. `kernel/schemas/result_envelope.yaml` is the only definition of what a
    specialist gives the orchestrator; `dispatch.submit_result` validates against it before it moves
    a task, and the schema is `strict`, so a ninth key is a refusal and not a courtesy. Six office
    SKILLs still prescribed the V1 shape (`summary`, `proc`, plus per-role keys). Measured before
    the repair, by handing that shape to `kernel.schemas.validate`: eight errors — two unknown
    fields and six missing required ones. The field names therefore come from `load_schema` here,
    and the ROLES that owe the contract come from the same predicate `gate_subagent_output` uses
    (an `agents/<role>.md` exists), minus the kit's session agent.

  * WHO CAN WALK THE HAND-BACK. `submit-result` is a COMMAND LINE, and some shipped specialists
    grant no tool that runs one. Pilot 3 met that three times and reported it as a gap (BUG-0048).
    `kernel.dispatch.hand_back_path` is now the one answer — derived per role from its own
    definition — and the checks below hold the shipped contract texts to it. WHICH roles those are
    is deliberately not written here: AC-1 asks for a derivation, and a count or a name list in
    this docstring is the thing that rots the day a role ships. The measurement of the day belongs
    in the round's report; each test names its own floor instead.

  * A DUTY THAT NEEDS A FEATURE. Role texts tell their role to consult its craft memory, and some
    of them enabled no role memory at all, so there was nothing to consult (BUG-0047). What COUNTS
    as that duty is not a sentence copied here: it is the pattern the Codex generator rewrites
    (`gen_provider_artifacts.MEMORY_DUTY_RX`), because Codex has no such feature — so the running
    code already owns the definition and this file borrows it.

  * A CLAIM ABOUT THE PIPELINE. The QA SKILL said the merge pipeline enforces "coverage >= threshold
    globally AND per source area". `scripts/quality.py` builds ONE `--cov=` base and ONE
    `--cov-fail-under=`, which is read off its AST below rather than off its prose. That made the
    line the failure mode this repo is built against — a text promising protection the code does not
    build — and the correction is pinned here so it cannot quietly return.

WHAT THESE CHECKS DO NOT DO, said here rather than discovered later. They read the shipped SKILL
TEXT, which is the artifact the role receives, so they can tell a missing field name from a present
one and cannot tell a good instruction from a bad one. The second test judges only the sentences
that ENUMERATE the envelope — a sentence naming no envelope field at all (records-clerk's line about
`product_requirement`) is prose about the contract, not a prescription of it, and is deliberately out
of scope. And the coverage test's negative half matches the shipped spelling and near paraphrases of
it, not every possible false claim; its positive half — the block must still name the mechanism that
DOES hold per area — is what carries the weight when someone rewrites the sentence.
"""
import ast
import glob
import io
import json
import os
import re
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEAM_KITS = os.path.join(ROOT, "team-kits")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, TEAM_KITS)

import lead_package                                                  # noqa: E402


# A backticked span is a NAME only when it is a plain lower-case identifier. `INV`, `UNCLEAR` and
# `verdict: PASS|FAIL` are backticked in shipped output blocks and none of them is an envelope key —
# an item type, a status word and a printed line respectively. Restricting to the spelling a YAML
# key actually has is what keeps this reader from inventing offenders out of prose.
_BACKTICKED_RX = re.compile(r"`([^`]+)`")
_IDENTIFIER_RX = re.compile(r"^[a-z][a-z0-9_]*$")
_SENTENCE_SPLIT_RX = re.compile(r"(?<=\.)\s+")


def _reading_view(text):
    """The text as it READS — a field name in a wrapped list does not stop at the line break."""
    return re.sub(r"\s+", " ", text).strip()


def _kit_dirs():
    """Every shipped kit, taken from the tree by the file that makes it one."""
    return sorted(os.path.dirname(os.path.dirname(path)) for path in
                  glob.glob(os.path.join(TEAM_KITS, "*", "constitution", "AGENTS.md")))


def _specialist_skills():
    """(kit dir, role, SKILL.md) for every role that can be SPAWNED and ships a skill.

    DERIVED THE WAY THE GATE DERIVES IT. `gate_subagent_output` calls a stopping subagent "one of
    ours" when `.claude/agents/<agent_type>.md` exists, so the same question is asked of the kit
    source. The kit's session agent (`settings/settings.json` `agent`, through
    `lead_package.lead_role`) is excluded because it is bound as the lead and never stops as a
    subagent — a kit that renames its lead moves this set with it, and no reader has to be told.
    """
    for kit in _kit_dirs():
        lead = lead_package.lead_role(kit)
        for path in sorted(glob.glob(os.path.join(kit, "skills", "*", "SKILL.md"))):
            role = os.path.basename(os.path.dirname(path))
            if role == lead:
                continue
            if not os.path.isfile(os.path.join(kit, "agents", role + ".md")):
                continue
            yield kit, role, path


def _output_section(path):
    """The `## Output to the …` section of a SKILL, as one reading view.

    The heading wording differs by kit (`to the PM` / `to the manager`), so what is matched is the
    heading's SUBJECT — the hand-back — and not either spelling.
    """
    with io.open(path, encoding="utf-8") as handle:
        text = handle.read()
    match = re.search(r"(?m)^##\s+Output to the .*$", text)
    if not match:
        return None
    rest = text[match.end():]
    following = re.search(r"(?m)^##\s", rest)
    return _reading_view(rest[:following.start()] if following else rest)


def _envelope_fields():
    from kernel.schemas import load_schema
    return load_schema("result_envelope")["fields"]


def _valid_envelope():
    """A minimal envelope the kernel accepts — the probe base for the key test below."""
    return {"task_id": "TSK-0001", "role": "probe", "status_proposal": "SUBMITTED",
            "summary": "probe", "outputs": [], "evidence": [], "scope_touched": [],
            "followups": []}


def _kernel_accepts_key(name):
    """Does the KERNEL accept `name` as a top-level envelope key? Asked by running the validator.

    Not by comparing against the fields dict: the question is what `submit_result` will do with the
    key a SKILL told a role to hand over, and that answer is produced by `schemas.validate`, which
    is the code that runs.
    """
    from kernel.schemas import validate, SchemaError
    probe = _valid_envelope()
    probe[name] = "probe" if name not in probe else probe[name]
    try:
        validate(probe, "result_envelope")
    except SchemaError:
        return False
    return True


# ============================================================ 1. the hand-back contract
def test_the_specialist_set_is_the_one_the_gate_would_judge():
    """A floor under both tests below: they are vacuous over a set that stopped matching.

    Twenty-two specialists ship today across three kits (8 dev, 8 office, 7 research, minus each
    kit's lead — the leads carry no hand-back section because they never hand back). The floor sits
    under that so a renamed role cannot trip it, and far enough over zero that losing the derivation
    cannot pass unnoticed.
    """
    found = list(_specialist_skills())
    assert len(found) >= 18, [role for _kit, role, _path in found]
    leads = {lead_package.lead_role(kit) for kit in _kit_dirs()}
    assert leads and None not in leads, leads
    assert not [role for _kit, role, _path in found if role in leads], "a lead leaked into the set"


def test_every_specialist_skill_hands_back_the_whole_result_envelope():
    """Every specialist's output section names every field the envelope schema REQUIRES.

    THE LIST IS THE SCHEMA'S, not this file's: `result_envelope.yaml` is what
    `dispatch.submit_result` validates against and what the orchestrator types as `submit-result`
    flags, so a SKILL that names a different set sends the role to a refusal.

    MEASURED RED before the repair of 2026-08-03, over a copy of the tree outside this repo with the
    six V1 blocks restored: bookkeeper, compliance-researcher, marketing-planner, product-editor and
    shop-curator were each missing seven of the eight fields (they named only `summary`), and
    office-developer six (it happened to spell `outputs`, meaning its dashboard paths). The other
    sixteen specialists — including the two office roles already converted, records-clerk and
    project-auditor — were green in the same run, which is what makes this a check on the six and
    not on the reader.
    """
    required = tuple(name for name, spec in _envelope_fields().items() if (spec or {}).get("required"))
    assert len(required) >= 6, required
    offenders = []
    for kit, role, path in _specialist_skills():
        section = _output_section(path)
        if section is None:
            offenders.append("%s/%s: no `## Output to the …` section at all"
                             % (os.path.basename(kit), role))
            continue
        absent = [name for name in required if ("`%s`" % name) not in section]
        if absent:
            offenders.append("%s/%s: %s" % (os.path.basename(kit), role, ", ".join(absent)))
    assert not offenders, (
        "these specialist SKILLs describe a hand-back that is not the result envelope "
        "(kernel/schemas/result_envelope.yaml requires %s):\n  %s"
        % (", ".join(required), "\n  ".join(offenders)))


def test_no_specialist_skill_prescribes_an_envelope_key_the_kernel_rejects():
    """A field name a SKILL hands a role must survive the validator that receives it.

    WHICH sentences are read: the ones that ENUMERATE the envelope, defined as naming at least one
    of its fields. That definition is what separates a prescription from prose about it —
    records-clerk's closing sentence names `product_requirement` and no envelope field, and it is
    explaining why `proc` is NOT a key rather than asking for one.

    WHAT REJECTION MEANS is asked of `kernel.schemas.validate` with a probe envelope, so the answer
    comes from the code `submit_result` calls rather than from a copy of the field list here.

    MEASURED RED before the repair, same restored copy as the sibling test: 30 offending
    (role, key) pairs over the six office SKILLs, 19 distinct spellings — `proc` in all six, plus
    `booked`, `open_items`, `unclear`, `category_proposals`, `anomalies`, `entries_added_updated`,
    `flags`, `tasks_for_user`, `plan_changes`, `drafts`, `accounts_needed`, `tools`, `verified`,
    `products`, `guideline_additions`, `findings`, `copy_proposals`, `open_questions`.
    """
    fields = set(_envelope_fields())
    judged, offenders = 0, []
    for kit, role, path in _specialist_skills():
        section = _output_section(path) or ""
        for sentence in _SENTENCE_SPLIT_RX.split(section):
            names = [span for span in _BACKTICKED_RX.findall(sentence)
                     if _IDENTIFIER_RX.match(span)]
            if not (set(names) & fields):
                continue        # prose about the contract, not an enumeration of it
            for name in names:
                judged += 1
                if not _kernel_accepts_key(name):
                    offenders.append("%s/%s: `%s`" % (os.path.basename(kit), role, name))
    assert not offenders, (
        "these SKILLs enumerate a hand-back key the kernel refuses (the envelope schema is "
        "strict, so `submit-result` rejects it):\n  %s" % "\n  ".join(sorted(set(offenders))))
    # A floor: every assertion above is vacuously true over a reader that found no names.
    assert judged >= 100, "only %d enumerated key names found — the reader stopped matching" % judged


def test_the_envelope_key_reader_can_tell_a_stranger_from_a_field():
    """The floor under `_kernel_accepts_key`, so "return True" is not a way out.

    Without it the offending half of the test above rests on nothing once the tree is green: a
    reader that accepted everything would look identical. The probe uses the two spellings the
    repaired tree actually contains — a real field and the V1 key that was removed from six SKILLs.
    """
    assert _kernel_accepts_key("summary") is True
    assert _kernel_accepts_key("scope_touched") is True
    assert _kernel_accepts_key("proc") is False
    assert _kernel_accepts_key("open_questions") is False


# ================================================== 2. who can walk the hand-back (BUG-0048)
def _specialist_roles(kit):
    """Every role of `kit` that can be SPAWNED, by the predicate `gate_subagent_output` uses.

    The same derivation as `_specialist_skills` and deliberately NOT that function: a role owes the
    hand-back contract because it can be dispatched, not because it happens to ship a SKILL.
    """
    lead = lead_package.lead_role(kit)
    return sorted(os.path.basename(path)[:-3]
                  for path in glob.glob(os.path.join(kit, "agents", "*.md"))
                  if os.path.basename(path)[:-3] != lead)


def _hand_back(kit, role):
    from kernel import dispatch
    return dispatch.hand_back_path(os.path.join(kit, "agents"), role)


def _settings_command_line_tools(kit):
    """The tools this kit registers `gate_write_scope` on as a COMMAND LINE, off its own wiring.

    Two PreToolUse groups register that gate: the one that judges file writes and the one that
    judges a shell line. Which is which is decided by the gate's OWN `FILE_TOOLS` tuple rather
    than by a matcher spelling here — the group disjoint from it is the command-line group.
    """
    with io.open(os.path.join(kit, "settings", "settings.json"), encoding="utf-8") as handle:
        settings = json.load(handle)
    file_tools = {name.lower() for name in _gate_tuple("FILE_TOOLS")}
    found = set()
    for group in settings["hooks"]["PreToolUse"]:
        if not any(os.path.basename(entry["command"].split()[-1].strip('"')) ==
                   "gate_write_scope.py" for entry in group["hooks"]):
            continue
        tools = [part for part in (group.get("matcher") or "").split("|") if part]
        if not {name.lower() for name in tools} & file_tools:
            found.update(tools)
    return found


def _gate_tuple(name):
    """A module-level tuple of the shipped `gate_write_scope`, read off its AST.

    PARSED, not imported: the hook's import of `_kernel` resolves against a project, and a gate
    that fails closed on an absent kernel would make this reader measure the fixture. Parsed, not
    grepped, for the reason this repo keeps re-learning — a string search finds the tuple in a
    docstring too.
    """
    path = os.path.join(TEAM_KITS, "dev-team", "hooks", "gate_write_scope.py")
    with io.open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=path)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return tuple(ast.literal_eval(node.value))
    raise AssertionError("gate_write_scope no longer defines %s" % name)


def test_the_command_running_tools_are_one_fact_in_three_places():
    """The kernel, the gate and every kit's wiring must name the SAME command-running tools.

    THE UNAVOIDABLE ENUMERATION AND ITS TRIPWIRE. Which provider tools run a command line is
    provider knowledge; nothing in this repo can derive it, so it is written down — once in
    `kernel.dispatch.COMMAND_TOOLS`, because the kernel is what has to ACT on it, and once in
    `gate_write_scope.SHELL_TOOLS`, because that gate must keep routing in a project whose kernel
    is unreachable. This measures BOTH ends and the kits' own `settings.json` matcher as a third,
    so a tool added to one of them cannot sit there alone: the kernel would keep telling a role it
    may run a command the gate never judges, or the reverse.
    """
    sys.path.insert(0, TEAM_KITS)
    from kernel import dispatch
    kernel_side = {name.lower() for name in dispatch.COMMAND_TOOLS}
    gate_side = {name.lower() for name in _gate_tuple("SHELL_TOOLS")}
    assert kernel_side and kernel_side == gate_side, (kernel_side, gate_side)
    for kit in _kit_dirs():
        wired = {name.lower() for name in _settings_command_line_tools(kit)}
        assert wired == kernel_side, (os.path.basename(kit), wired, kernel_side)


def test_every_shipped_specialist_is_told_a_path_its_toolset_can_walk():
    """AC-1 of BUG-0048: contract and toolset agree for EVERY shipped specialist, derived.

    TWO HALVES, and both read the shipped artefacts rather than a list:

      * the KERNEL's answer per role is `self` exactly when that role's own frontmatter grants a
        command-running tool. A role added tomorrow is judged the day it ships.
      * a role the kernel puts on the `lead` path may not be handed a command line by its OWN
        texts (its `agents/<role>.md` and its SKILL) — those are addressed to that one role, so a
        `python scripts/harness.py …` in them is a demand it cannot meet. The corpus reader is the
        invocation the shim installs (`kernel.cli.INVOCATION`), so a renamed entry point moves this
        with it.

    MEASURED before the repair over the shipped tree: eight roles come back `lead` and none of
    them names the entry point in its own texts — the contradiction pilot 3 hit lived in the
    CONSTITUTION, which is every role's text at once, and that is the sibling test below.
    """
    sys.path.insert(0, TEAM_KITS)
    from kernel import cli, dispatch
    call = re.compile(re.escape(cli.INVOCATION) + r"\s+[a-z]")
    shell_less, offenders = [], []
    for kit in _kit_dirs():
        for role in _specialist_roles(kit):
            granted = dispatch.role_tools(os.path.join(kit, "agents"), role)
            assert granted, "%s/%s ships no readable `tools:` frontmatter" % (kit, role)
            runs = {name.lower() for name in granted} & {
                name.lower() for name in dispatch.COMMAND_TOOLS}
            expected = dispatch.HAND_BACK_SELF if runs else dispatch.HAND_BACK_LEAD
            answered = _hand_back(kit, role)
            assert answered == expected, (kit, role, answered, expected, granted)
            if answered != dispatch.HAND_BACK_LEAD:
                continue
            shell_less.append("%s/%s" % (os.path.basename(kit), role))
            for path in (os.path.join(kit, "agents", role + ".md"),
                         os.path.join(kit, "skills", role, "SKILL.md")):
                if not os.path.isfile(path):
                    continue
                with io.open(path, encoding="utf-8") as handle:
                    if call.search(_reading_view(handle.read())):
                        offenders.append("%s/%s: %s" % (os.path.basename(kit), role,
                                                        os.path.basename(path)))
    assert not offenders, (
        "these role texts hand a command line to a role whose own definition grants no tool that "
        "runs one (BUG-0048). Either give the role the tool or name the path it CAN walk:\n  %s"
        % "\n  ".join(offenders))
    # A floor: every assertion above is vacuous over a tree where no role is shell-less.
    assert len(shell_less) >= 4, shell_less


def _role_definition(kit, role):
    """(frontmatter mapping, body) of a shipped role definition."""
    import yaml
    path = os.path.join(kit, "agents", role + ".md")
    with io.open(path, encoding="utf-8") as handle:
        text = handle.read()
    end = text.find("\n---", 3)
    assert text.startswith("---") and end > 0, path
    return yaml.safe_load(text[3:end]) or {}, text[end:]


def test_the_memory_duty_is_only_prescribed_where_the_role_has_memory():
    """A role told to consult its craft memory must be a role that HAS one (BUG-0047).

    THE DUTY IS DEFINED BY RUNNING CODE, not by a sentence copied into this file:
    `gen_provider_artifacts.MEMORY_DUTY_RX` is the pattern the Codex generator rewrites, because
    Codex has no per-role memory — so that pattern already IS this repo's answer to "does this
    text prescribe the memory duty", and a reworded duty that escaped it would escape the Codex
    rewrite too. The other side is the role's own frontmatter, read as YAML rather than searched
    for a spelling.

    MEASURED before the repair over the shipped tree: two offenders, dev `devops-engineer` and
    research `researcher` — both carrying the sentence, neither carrying the frontmatter key, so
    both were told to consult a directory the provider never gives them. The kit's OTHER five
    duty-carrying roles were green in the same run, which is what makes this a check on the two
    and not on the reader.
    """
    sys.path.insert(0, TEAM_KITS)
    import gen_provider_artifacts
    prescribed, offenders = [], []
    for kit in _kit_dirs():
        for path in sorted(glob.glob(os.path.join(kit, "agents", "*.md"))):
            role = os.path.basename(path)[:-3]
            front, body = _role_definition(kit, role)
            if not gen_provider_artifacts.MEMORY_DUTY_RX.search(_reading_view(body)):
                continue
            prescribed.append("%s/%s" % (os.path.basename(kit), role))
            if not front.get(gen_provider_artifacts.MEMORY_FRONTMATTER_KEY):
                offenders.append("%s/%s" % (os.path.basename(kit), role))
    assert not offenders, (
        "these role texts prescribe the craft-memory duty to a role whose own definition enables "
        "no role memory, so there is nothing to consult and nowhere the update lands (`%s:` is "
        "the key). Either enable it or drop the duty:\n  %s"
        % (gen_provider_artifacts.MEMORY_FRONTMATTER_KEY, "\n  ".join(offenders)))
    # A floor: the assertion above is vacuous over a reader that stopped matching the duty at all.
    assert len(prescribed) >= 6, prescribed


def test_the_lead_of_every_kit_with_a_shell_less_role_carries_the_relay(kit=None):
    """The OTHER half of the `lead` path, and it needs its own reader (BUG-0048).

    A relay has two ends. The specialist's end is checked twice above; the lead's end — actually
    running `submit-result --from` on the envelope the specialist staged — lived only in the lead
    role texts, and nothing went red when it was removed from all three: a section pin notices a
    CHANGE, never a GAP, and the constitution paragraph is the specialist's text, not the lead's.

    WHAT IS ASKED, both ends derived: for every kit in which ANY dispatched role resolves to
    `dispatch.HAND_BACK_LEAD`, that kit's own lead — `lead_package.lead_role`, the same source
    `_specialist_skills` excludes by — must name the relay in its role text, and "name the relay"
    is the FLAG the kernel's parser actually carries (read off `build_parser`, so a rename moves
    this with it) standing behind the invocation `kernel.cli` installs. A kit whose roles all carry
    a shell owes nothing, and says so by not entering the loop.

    MEASURED RED in a clone outside this repo with the `--from` bullet cut from all three lead role
    texts: three offenders. `kit` is a parameter only so the failure names one; the loop is over
    the derived set.
    """
    sys.path.insert(0, TEAM_KITS)
    from kernel import cli, dispatch
    flags = [option for action in cli.build_parser()._subparsers._group_actions[0]
             .choices["submit-result"]._actions for option in action.option_strings]
    relay = next(option for option in flags if option.lstrip("-") == "from")
    judged, offenders = 0, []
    for directory in _kit_dirs():
        if kit and os.path.basename(directory) != kit:
            continue
        if not [role for role in _specialist_roles(directory)
                if _hand_back(directory, role) == dispatch.HAND_BACK_LEAD]:
            continue
        judged += 1
        lead = lead_package.lead_role(directory)
        with io.open(os.path.join(directory, "agents", lead + ".md"), encoding="utf-8") as handle:
            text = _reading_view(handle.read())
        if not re.search(re.escape(cli.INVOCATION) + r"[^`]*" + re.escape(relay) + r"\b", text):
            offenders.append("%s/%s" % (os.path.basename(directory), lead))
    assert not offenders, (
        "these kits dispatch a role that cannot run a command, and their lead's own text never "
        "says how to book its result in (`%s %s`). The specialist's half of the relay is written "
        "and the lead's half is not:\n  %s" % (cli.INVOCATION, relay, "\n  ".join(offenders)))
    assert judged >= 1, "no kit ships a shell-less dispatched role — this check judged nothing"


def _constitution_block(kit, pattern):
    """The paragraph of a kit constitution that matches `pattern`, as one reading view."""
    path = os.path.join(kit, "constitution", "AGENTS.md")
    with io.open(path, encoding="utf-8") as handle:
        text = handle.read()
    for block in re.split(r"\n\s*\n", text):
        if re.search(pattern, block):
            return _reading_view(block)
    return None


def test_the_checkpoint_duty_binds_only_the_roles_that_could_run_it():
    """The constitution may not demand a COMMAND of every dispatched role (BUG-0048).

    THE DEMAND IS REAL AND IT IS THE ONE PLACE THAT ADDRESSES EVERY ROLE AT ONCE: §6 tells "a
    dispatched role" to run `python scripts/harness.py checkpoint <TSK-ID>`, and eight shipped
    specialists grant no tool that runs a command line. So the run-up to that command has to name
    WHICH roles it binds, and the block has to say what happens to the others.

    WHAT IS ASKED OF THE TEXT, defined rather than spelled: the two values the KERNEL emits in the
    dispatch header (`dispatch.HAND_BACK_SELF` / `HAND_BACK_LEAD`), each in a code span — the
    qualifier in front of the command, and the fallback somewhere in the same block. Renaming
    either value in the kernel moves this requirement with it; a block that keeps the demand and
    drops the qualifier goes red.

    MEASURED RED before the repair, over a copy of the tree outside this repo carrying the shipped
    "A dispatched role therefore CHECKPOINTS — `python scripts/harness.py checkpoint <TSK-ID>`":
    three offenders, one per kit, on the run-up half.
    """
    sys.path.insert(0, TEAM_KITS)
    from kernel import cli, dispatch
    demand = re.escape(cli.INVOCATION) + r"\s+checkpoint\b"
    offenders, judged = [], 0
    for kit in _kit_dirs():
        shell_less = [role for role in _specialist_roles(kit)
                      if _hand_back(kit, role) == dispatch.HAND_BACK_LEAD]
        if not shell_less:
            continue
        block = _constitution_block(kit, demand)
        assert block, "%s no longer states the checkpoint duty at all" % os.path.basename(kit)
        judged += 1
        run_up = block[:re.search(demand, block).start()]
        if ("`%s`" % dispatch.HAND_BACK_SELF) not in run_up:
            offenders.append("%s: the demand is unqualified — %s cannot run it"
                             % (os.path.basename(kit), ", ".join(shell_less)))
        if ("`%s`" % dispatch.HAND_BACK_LEAD) not in block:
            offenders.append("%s: the block names no outcome for the roles it does not bind"
                             % os.path.basename(kit))
    assert not offenders, (
        "the constitution demands a command line of roles whose toolset grants no way to run "
        "one:\n  %s" % "\n  ".join(offenders))
    assert judged >= 3, "only %d kits judged — every kit lost its shell-less roles?" % judged


# ============================================================ 3. a claim about the pipeline
def _quality_py():
    return os.path.join(TEAM_KITS, "dev-team", "templates", "repo", "scripts", "quality.py")


def _coverage_bases_and_floors():
    """(coverage bases, floor flags) `quality.py` can hand pytest, read off its AST.

    The BASE is the operand `--cov=` is concatenated with; if the script ever measured several
    areas, there would be several distinct operands (or one built inside a loop). Reading the AST
    rather than the file text is the point: the shipped module's own docstring says "tests+coverage"
    and says nothing about how many bases that is.
    """
    with io.open(_quality_py(), encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=_quality_py())
    function = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == "check_python")
    bases, floors = set(), set()
    for node in ast.walk(function):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add) \
                and isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
            if node.left.value == "--cov=":
                bases.add(ast.dump(node.right))
            elif node.left.value.startswith("--cov-fail-under"):
                floors.add(node.left.value)
    return bases, floors


def _block_naming_the_coverage_threshold():
    """The QA SKILL's markdown block that states the coverage floor, as one reading view.

    A BLOCK and not a sentence: the correction and the pointer to what really holds per area are two
    sentences of one numbered step, and a sentence-sized window would have demanded both in the same
    breath — which is how a check starts dictating prose instead of judging a claim. The step is the
    unit, not the paragraph: the shipped `## Do` list runs its numbered items together without blank
    lines, so a paragraph-sized window reached into step 3 and read QA's own per-area coverage MAP
    (a thing it writes into its Evidence) as a claim about the pipeline.
    """
    path = os.path.join(TEAM_KITS, "dev-team", "skills", "quality-engineer", "SKILL.md")
    with io.open(path, encoding="utf-8") as handle:
        text = handle.read()
    for block in re.split(r"(?m)^(?=\d+\.\s)", text):
        if re.search(r"coverage\s*(?:≥|>=)\s*threshold", block):
            return _reading_view(block)
    raise AssertionError("the QA SKILL no longer names the coverage threshold at all")


def test_the_qa_coverage_claim_matches_what_quality_py_measures():
    """The QA SKILL may not promise a coverage floor per source area, because there is none.

    THE FACT COMES FROM THE RUNNING CODE: `check_python` concatenates `--cov=` with exactly ONE
    operand and passes exactly one `--cov-fail-under=`, so the pipeline measures one base against
    one number. `gate_test_coverage` is what holds per AREA, and its own docstring says what that
    is: "this hook only catches the 'whole area untested' failure that a global % can mask".

    MEASURED RED before the repair, over a copy outside this repo carrying the shipped line
    "coverage >= threshold globally AND per source area (src/, frontend/src/ ...)": one offender.

    WHAT THIS CANNOT DO: it matches the shipped spelling and close paraphrases of it, not every way
    a false claim could be phrased. The half that survives a rewrite is the second assertion — the
    block that names the threshold must, in the same breath, name the mechanism that really holds
    per area, so a reader who deletes the correction also deletes the pointer and this goes red.
    """
    bases, floors = _coverage_bases_and_floors()
    assert len(bases) == 1, (
        "quality.py builds %d coverage bases — the SKILL text below was written against one" % len(bases))
    assert len(floors) == 1, floors

    block = _block_naming_the_coverage_threshold()
    # AN AFFIRMED PER-AREA THRESHOLD, defined rather than spelled: a mention of "per (source) area"
    # whose run-up talks about a threshold, floor or percentage AND carries no negation. Both halves
    # are needed and both were measured. Without the threshold half, "what holds per AREA is weaker"
    # — the sentence that states the correction — reads as the defect. Without the negation half,
    # "there is NO percentage floor per source area" does. What survives is the shape of the old
    # claim: a floor, bound to areas, asserted.
    liars = []
    for match in re.finditer(r"per[\s-](?:source[\s-])?area", block):
        run_up = block[max(0, match.start() - 80):match.start()]
        if not re.search(r"threshold|floor|percentage|%", run_up):
            continue
        if re.search(r"\b(?:no|not|never|nothing|without)\b", run_up):
            continue
        liars.append(block[max(0, match.start() - 80):match.end()])
    assert not liars, (
        "the QA SKILL binds the coverage threshold to source areas and quality.py measures ONE "
        "base against ONE floor:\n  %s" % "\n  ".join(liars))
    assert "gate_test_coverage" in block, (
        "the QA SKILL states the coverage floor without naming what DOES hold per source area — "
        "a reader then reads the silence as 'nothing', which is as wrong as the old over-claim")


# ================================== 4. the filing pipeline's two artifacts (FR-0049)
def _pipeline_schemas():
    """(schema name, writer role, required per-entry keys) for every schema that names its writer.

    DERIVED FROM THE SCHEMAS, not listed here: a schema declares `writer_role` when it describes an
    artifact a ROLE produces, so a third pipeline artifact joins this check the day it names its
    writer and a schema that describes something else (`result_envelope`, `session_brief`) stays out
    without being excluded anywhere.
    """
    from kernel.schemas import _SCHEMA_DIR, load_schema
    for name in sorted(os.listdir(_SCHEMA_DIR)):
        if not name.endswith(".yaml"):
            continue
        schema = load_schema(name[:-5]) or {}
        role = schema.get("writer_role")
        if role:
            yield name[:-5], role, schema


def test_the_pipeline_texts_name_the_fields_their_own_schema_declares():
    """A role told to write an artifact must be told its FIELDS -- from the schema, once.

    THE DEFECT SHAPE THIS IS AGAINST is the one `test_every_specialist_skill_hands_back_the_whole_
    result_envelope` was written for: six office SKILLs prescribed a hand-back shape the kernel
    rejects, because the shape lived in prose beside the contract instead of being read off it. The
    filing pipeline has the same structure twice over -- the clerk WRITES the proposal list and the
    reviewer READS it, so a drift in either text is two roles describing different objects.

    WHAT IS ASKED: the writer's own SKILL names every top-level field the schema requires and every
    per-entry key of its list (`item_required`), each in a code span; and where the schema declares a
    VOCABULARY for an entry key (`item_enums` -- the three verdicts), the SKILL names each word.
    Nothing here asks for a sentence: a check on prose would start dictating it.

    MEASURED RED in a copy of the tree outside this repo with the `filing_verdicts` step cut out of
    the reviewer's SKILL: one offender, five missing names.
    """
    judged, offenders = 0, []
    for name, role, schema in _pipeline_schemas():
        paths = [path for path in glob.glob(os.path.join(TEAM_KITS, "*", "skills", role,
                                                         "SKILL.md"))]
        assert paths, "%s names %s as its writer and no kit ships that role's SKILL" % (name, role)
        wanted = [field for field, spec in (schema.get("fields") or {}).items()
                  if (spec or {}).get("required")]
        for field, spec in (schema.get("fields") or {}).items():
            wanted += list((spec or {}).get("item_required") or [])
            for values in ((spec or {}).get("item_enums") or {}).values():
                wanted += list(values)
        assert len(wanted) >= 8, (name, wanted)
        for path in paths:
            with io.open(path, encoding="utf-8") as handle:
                text = _reading_view(handle.read())
            judged += 1
            absent = [word for word in wanted if ("`%s`" % word) not in text]
            if absent:
                offenders.append("%s (%s): %s" % (role, name, ", ".join(sorted(set(absent)))))
    assert not offenders, (
        "these role texts prescribe an artifact whose contract they do not spell out, so the two "
        "ends of the pipeline can drift apart (the contracts are team-kits/kernel/schemas/):\n  %s"
        % "\n  ".join(offenders))
    assert judged >= 2, "only %d pipeline SKILLs judged -- the derivation stopped matching" % judged


def _question_tools(kit):
    """The tools this kit registers its user-question guard on, off its own wiring.

    Same derivation as `_settings_command_line_tools`: which tool ASKS THE USER is provider
    knowledge, and the place this repo already writes it down is the registration that puts a guard
    on that event. Reading it here means a provider's second question tool arrives with the rule
    applied rather than with a list to update.
    """
    with io.open(os.path.join(kit, "settings", "settings.json"), encoding="utf-8") as handle:
        settings = json.load(handle)
    found = set()
    for group in settings["hooks"].get("PreToolUse", []):
        if not any(os.path.basename(entry["command"].split()[-1].strip('"')) ==
                   "guard_question_context.py" for entry in group["hooks"]):
            continue
        found.update(part for part in (group.get("matcher") or "").split("|") if part)
    return found


def test_no_role_text_names_a_user_question_tool_its_own_definition_denies():
    """A role told to ask the user must BE able to ask the user (the BUG-0048 shape, one tool over).

    MEASURED on the shipped tree before this round: ONE offender. `records-clerk.md` told the clerk
    to "Relay the printed question VERBATIM with AskUserQuestion" for the FR-0050 correction door,
    and that role's frontmatter grants `Read, Grep, Glob, Bash, Edit, Write` -- no question tool at
    all. A subagent's reply reaches the MANAGER and not the user, so the instruction could not be
    followed by any route: the correction the user is supposed to decide would have been decided by
    a paraphrase, or not at all. Every kit's own constitution says the same thing from the other
    side (one customer-facing role), which is exactly why the contradiction survived reading.

    THE RULE IS "DOES NOT NAME IT", not "does not prescribe it", and that is deliberate over-strict:
    telling a prescription from a description is a judgement about prose, and a text that needs to
    describe the manager's half can say "the manager asks the user" instead. The cost is a wording;
    the alternative is a predicate nobody can measure. The tool set comes from the kit's own
    registration (`_question_tools`) and the grants from the role's frontmatter, so neither end is a
    list in this file.
    """
    judged, offenders = 0, []
    for kit in _kit_dirs():
        tools = _question_tools(kit)
        assert tools, "%s registers no user-question guard at all" % os.path.basename(kit)
        for path in sorted(glob.glob(os.path.join(kit, "agents", "*.md"))):
            role = os.path.basename(path)[:-3]
            front, _body = _role_definition(kit, role)
            granted = {str(name).strip() for name in (front.get("tools") or "").split(",")} \
                if isinstance(front.get("tools"), str) else {str(name) for name
                                                             in (front.get("tools") or [])}
            texts = [path, os.path.join(kit, "skills", role, "SKILL.md")]
            for text_path in texts:
                if not os.path.isfile(text_path):
                    continue
                judged += 1
                with io.open(text_path, encoding="utf-8") as handle:
                    text = handle.read()
                for tool in sorted(tools - granted):
                    if re.search(r"\b%s\b" % re.escape(tool), text):
                        offenders.append("%s/%s: %s names %s"
                                         % (os.path.basename(kit), role,
                                            os.path.basename(text_path), tool))
    assert not offenders, (
        "these role texts name a tool that ASKS THE USER, and the role's own definition grants no "
        "such tool -- a subagent's reply reaches the lead, never the user, so the instruction "
        "cannot be followed by any route. Either grant the tool or route the question through the "
        "lead:\n  %s" % "\n  ".join(sorted(set(offenders))))
    assert judged >= 20, "only %d role texts read -- the walk stopped matching" % judged

#!/usr/bin/env python3
"""What a specialist hands back, and what a role SKILL may claim about the pipeline.

TWO SUBJECTS, ONE HABIT: both are asked of the running code and never of a list in this file.

  * THE HAND-BACK CONTRACT. `kernel/schemas/result_envelope.yaml` is the only definition of what a
    specialist gives the orchestrator; `dispatch.submit_result` validates against it before it moves
    a task, and the schema is `strict`, so a ninth key is a refusal and not a courtesy. Six office
    SKILLs still prescribed the V1 shape (`summary`, `proc`, plus per-role keys). Measured before
    the repair, by handing that shape to `kernel.schemas.validate`: eight errors — two unknown
    fields and six missing required ones. The field names therefore come from `load_schema` here,
    and the ROLES that owe the contract come from the same predicate `gate_subagent_output` uses
    (an `agents/<role>.md` exists), minus the kit's session agent.

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


# ============================================================ 2. a claim about the pipeline
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

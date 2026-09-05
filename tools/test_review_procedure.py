#!/usr/bin/env python3
"""The review procedure and the reading a work order gets — held in the texts that carry them.

FOUR SUBJECTS, and every one of them is asked of the text a ROLE really receives, parsed into the
unit that text is written in (a `##` section, a numbered step, a bullet) and never as a string
search over a whole file. Two checks of generation 3 were satisfied by a window that also matched
their own prose; a section reader cannot be, because the block it returns is a block somebody wrote
as a block.

  * THE RETROSPECTIVE IS A STEP, NOT A MOOD (PR-0006 AC-1, FR-0084). The auditing role of every kit
    gets one step of its `## Do` list that poses a numbered list of QUESTIONS, and that step is ONE
    text across the kits. Which role that is comes from the shipped hook that schedules it
    (`hooks/_routine.AUDIT_ROLE`), so a kit that renames the role moves this subject with it.

  * A DUTY THAT STANDS ONLY IN A SKILL MAY NEVER ARRIVE. The kits' own role definitions record the
    measurement: a role's `skills:` frontmatter delivers nothing to a session bound to it, and the
    SUBAGENT-spawn path is unmeasured (`tools/provider_observations.json`). So the occasion rule is
    held in the role DEFINITION too — the file a spawn does load — and held there as one text.

  * THE ORDER GETS A READING BEFORE IT IS SENT (AC-2, AC-3). Every kit's LEAD skill carries one
    section that lays out the ways a work-order line goes wrong as NUMBERED forms, each with the
    decision that recorded its case; the same section carries the smaller-plan reading, and the work
    loop points at it, because a step outside the sequence is a step nobody runs. Which skill is the
    lead's comes from `lead_package.on_demand_files`, off each kit's own `settings.json`.

  * A POINTER IN THIS REPO'S OWN ROLE TEXTS RESOLVES (AC-4). `.claude/agents/` is read by no other
    suite: `test_repo_hygiene._texts_that_answer_for_a_claim` walks `team-kits/` and `docs/`, and
    `.claude/hooks/test_gates.py` judges the UNQUALIFIED half of the same claim inside its own
    directory. So the three harness role texts had no reader at all, and the rules DEC-0070 puts
    into them are pointers by construction.

WHAT THIS MODULE DOES NOT ESTABLISH, said here rather than discovered later. It reads instruction
PROSE, so it can tell a missing step from a present one and cannot tell whether anybody performed
it — no gate reads free text, which is why the blocks below have to state their own limit and why
that statement is what the honesty checks measure. The honesty READER is the one
`test_role_contracts` already owns; its VOCABULARY is widened here by the names of the hook files a
kit ships (`_mechanism_words`), because a word boundary does not fall inside `gate_dispatch` and
that is the spelling these blocks use. It stays finite all the same: an overclaim phrased without
naming any mechanism at all is not caught here either, and that limit is the one the protocol
names.
"""
import ast
import glob
import io
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEAM_KITS = os.path.join(ROOT, "team-kits")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, TEAM_KITS)

import lead_package                                                        # noqa: E402
from test_repo_hygiene import _defined_in, _test_citations                 # noqa: E402
from test_role_contracts import (_enforcement_claims, _enforcement_words,  # noqa: E402
                                 _kit_dirs, _markdown_sections, _reading_view)

# The decision whose rules and whose worked example these texts carry. It is an ANCHOR in the sense
# `test_role_contracts._rule_anchors` uses: the block is identified by the pointer it exists to
# carry, so a dead id makes this reader go looking for a block that is no longer there instead of
# quietly matching a heading whose wording drifted. That it resolves is asserted where it is read.
VERDICT_DECISION = "DEC-0070"


def _rule_pointer_rx(decision):
    """A pointer that names WHICH rule of `decision` the statement beside it carries.

    NOT DECORATION, and the correction that put it here was measured on the shipped text before a
    verifier could ask: a role text cites ONE decision from several statements -- the rules it was
    given, plus the worked example the same decision also is -- so a reader that counts every
    MENTION answers "are the rules still there" with a number that deleting one rule does not move.
    Counting the pointers that name a rule is what makes that deletion visible; the floor test below
    drives the reader over both shapes. A line break is allowed inside the pointer because these
    texts wrap.
    """
    return re.compile(r"`%s`,?\s*\n?\s*rule\s+(?P<number>\d+)" % re.escape(decision))


# WHICH rules of that decision this role text was given, by their number in it. AC-4 names them,
# and an enumeration is what a numbered rule is -- so it carries a tripwire at BOTH ends: a number
# here that no bullet carries is a rule nobody reads any more, and a bullet carrying a number that
# is not here is a rule nobody decided to put in this file. Verifier round 1 (B3) measured why a
# floor is not enough: deleting rule 2 and duplicating rule 1 keeps the count at three.
ORCHESTRATOR_RULES = (1, 2, 5)


# A step of a `## Do` list, and a bullet of a role definition — the units these texts are written
# in. Both are anchored at the start of a line, so a mention inside a sentence is not a step.
_STEP_SPLIT_RX = re.compile(r"(?m)^(?=\d+\. )")
_FORM_SPLIT_RX = re.compile(r"(?m)^(?=\d+\. \*\*)")
_BULLET_SPLIT_RX = re.compile(r"(?m)^(?=- )")
# A line that poses a question inside a numbered sub-list: indented, numbered, ending in `?`.
_QUESTION_RX = re.compile(r"(?m)^[ \t]+\d+\..*\?[ \t]*$")
# An occasion marker `(a)` … `(d)` — the shape the occasions are listed in.
_OCCASION_RX = re.compile(r"\([a-z]\) ")


# ============================================================ the store, and the pointers into it
def _item_ids(pattern):
    return {os.path.basename(path)[:-len(".yaml")] for path in glob.glob(pattern)}


def _items_in_the_store():
    """Every item id this repo holds, off the KERNEL's own layout rather than a path typed here.

    `ProjectState.active_dir` and `archive_root` are the builders every kernel write uses, so a
    store that reorganises moves this reader with it. The archive is globbed by SHAPE rather than
    per type, because the archive directory of a type is not spelled the same way for every type
    (`archive/dec/<year>/` beside `archive/FR/<year>/`) and this reader has no business knowing
    which is which.
    """
    from kernel import backlog_types
    from kernel.state import ProjectState
    store = ProjectState(os.path.join(ROOT, "project_memory"))
    found = set()
    for prefix in backlog_types.ACTIVE_DIRS:
        found |= _item_ids(os.path.join(store.active_dir(prefix), "%s-*.yaml" % prefix))
    found |= _item_ids(os.path.join(store.archive_root(), "*", "*", "*-*.yaml"))
    return found


def _handback_field():
    """The envelope field a run's own words come back in — off the schema the kernel validates with.

    THE ANCHOR FOR A REQUIREMENT THAT IS OTHERWISE ONLY FORM (verifier round 1, R2): the three lines
    for the user are the one half of the retrospective a form check cannot see — deleting them in
    all three kits left every count intact. They have a DESTINATION, and the destination is a field
    of a running contract, so naming it is what a check can hold.
    """
    from kernel.schemas import load_schema
    fields = load_schema("result_envelope")["fields"]
    assert "summary" in fields, (
        "the result envelope no longer carries a `summary` field; the retrospective's three lines "
        "point at it by name, so the rename has to move both")
    return "summary"


def _decision_type():
    """The item type a recorded choice becomes, off the kernel's own type vocabulary."""
    from kernel import backlog_types
    assert "DEC" in backlog_types.ACTIVE_DIRS, backlog_types.ACTIVE_DIRS
    return "DEC"


def _item_id_rx():
    """The id shape, over the kernel's own type vocabulary — a definition, never a typed list."""
    from kernel import backlog_types
    return re.compile(r"\b(?:%s)-\d{4}\b"
                      % "|".join(sorted(backlog_types.ACTIVE_DIRS, key=len, reverse=True)))


def _item_citations(text):
    """Every item id `text` names, as match objects — WITHOUT the delimited-literal exemption.

    `test_repo_hygiene._dec_citations` exempts an id inside a longer delimited span, because a
    SHIPPED KIT file exhibits ids as data: template stores, migration fixtures, a quoted refusal
    message. The three files this reader is pointed at carry no such data. Every id in them is a
    pointer, including one inside a path — `project_memory/staging/TSK-0120/…` rots at exactly the
    moment the item id does, and that is the rot this check exists for. Narrowing this reader to
    bare prose would drop the pointers that are hardest to notice.
    """
    return list(_item_id_rx().finditer(text))


def _mechanism_words(kit_dir):
    """The kit's enforcement vocabulary PLUS the names of the hooks it REGISTERS.

    WHY THE NAMES ARE IN HERE, and it was measured rather than reasoned (verifier round 1, R1):
    `test_role_contracts._enforcement_words` yields `gate`, `guard`, `hook` — bare words — and a
    word boundary does not fall inside `gate_dispatch`, because an underscore is a word character.
    An overclaim written as "gate_dispatch refuses an order that skipped either reading", inserted
    into all three lead skills, therefore passed the honesty check while the bare-word form failed
    it. The blocks this module guards name their mechanics in exactly that spelling, so the
    vocabulary they are read with has to contain it.

    REGISTERED, NOT SHIPPED, and that is verifier round 2 (N2). The first cut globbed `hooks/*.py`
    and swept in every helper beside the hooks (`_root`, `_compat`, `_stdlib_guard`); a plausible
    new file `hooks/reading.py`, registered nowhere, then turned two untouched and honest blocks
    red. The direction was the safe one, but the message would have blamed the text for a stranger's
    file name. What makes a name part of the enforcement apparatus is that the kit RUNS it, and
    `settings.json` is where that stands — the same source the base vocabulary already comes from.

    EVERY `.py` WORD OF THE COMMAND LINE, not its last one, and that is verifier round 3 (N3). A
    registration is a command line, and a kit's runner takes the hooks it drives as ARGUMENTS
    (`_gate.py gate_ledger_valid.py gate_second_booking.py`), so reading only the last word dropped
    the runner and every chained hook but one — measured, "guard_agent_spawn refuses an order that
    skipped either reading" passed the honesty check in all three lead skills.

    WHAT THIS DOES NOT LOOK AT: the filesystem. A registration naming a file the kit does not ship
    contributes its name here and is neither a crash nor a signal — whether a registered hook exists
    is a different question, and `test_shortening_net` is where it is asked.
    """
    names = set(_enforcement_words(kit_dir))
    with io.open(os.path.join(kit_dir, "settings", "settings.json"), encoding="utf-8") as handle:
        settings = json.load(handle)
    for groups in settings.get("hooks", {}).values():
        for group in groups:
            for entry in group.get("hooks", []):
                for word in entry["command"].split():
                    base = os.path.basename(word.strip('"'))
                    if base.endswith(".py"):
                        names.add(base[:-len(".py")].lower())
    return names


def _harness_role_texts():
    """(relative path, text) for this repo's own role definitions — the ones no other suite reads."""
    for path in sorted(glob.glob(os.path.join(ROOT, ".claude", "agents", "harness-*.md"))):
        with io.open(path, encoding="utf-8") as handle:
            yield os.path.relpath(path, ROOT).replace(os.sep, "/"), handle.read()


def test_every_item_pointer_the_harness_role_texts_write_resolves():
    """A rule in a role text answers for itself by naming its item; the item has to be there.

    THE ROLE TEXTS OF THIS REPO HAD NO READER. `test_repo_hygiene` sweeps `team-kits/` and `docs/`;
    `.claude/hooks/test_gates.py` sweeps its own directory. `.claude/agents/` is in neither, and
    DEC-0070 asks for three rules in `harness-lead.md` that ARE pointers — a rule whose reason
    cannot be opened is a rule that reads as decided and is not.
    """
    store = _items_in_the_store()
    assert len(store) >= 200, (
        "only %d items found — the store layout moved and every pointer below is being judged "
        "against an almost empty set" % len(store))
    judged, offenders = 0, []
    for rel, text in _harness_role_texts():
        for hit in _item_citations(text):
            judged += 1
            if hit.group(0) not in store:
                offenders.append("%s:%d %s" % (rel, text[:hit.start()].count("\n") + 1,
                                               hit.group(0)))
    assert not offenders, (
        "these role texts point at an item this store does not hold, so the reason they name "
        "cannot be read:\n  " + "\n  ".join(offenders))
    assert judged >= 10, (
        "only %d item pointers judged across .claude/agents/ — the reader stopped matching, and "
        "then the assertion above is vacuously true" % judged)


def test_every_test_pointer_the_harness_role_texts_write_resolves():
    """The same rule for the other pointer currency: a named test must be a test that exists.

    The reader is `test_repo_hygiene._test_citations`, which has its own floor test there; what is
    new here is the corpus. A role text that answers for a property by naming a test, and names one
    nobody can run, puts the claim back where it started and makes it read as measured.
    """
    offenders = []
    for rel, text in _harness_role_texts():
        for offset, path, name in _test_citations(text):
            defined = _defined_in(path)
            if defined is None or name not in defined:
                offenders.append("%s:%d cites %s::%s — %s"
                                 % (rel, text[:offset].count("\n") + 1, path, name,
                                    "no such suite file" if defined is None else "no such test"))
    assert not offenders, (
        "these role texts answer for a claim with a test nobody can run:\n  "
        + "\n  ".join(offenders))


def test_the_item_pointer_reader_can_tell_an_id_from_the_prose_around_it():
    """The floor under the sweep, so "match everything" and "match nothing" both fail here.

    Each probe is a shape that really stands in the three files: a backticked id, a bare one in
    prose, an id inside a path, and the two non-ids the reader must stay quiet on — a type name
    without a number, and a number that is not an id.
    """
    def found(text):
        return [hit.group(0) for hit in _item_citations(text)]

    assert found("(`DEC-0070`, rule 1)") == ["DEC-0070"]
    assert found("the whole trade DEC-0003 makes") == ["DEC-0003"]
    assert found("`project_memory/staging/TSK-0120/merge-protocol.md`") == ["TSK-0120"]
    assert found("the contract is `SR-0008`, the occasion `DEC-0008`") == ["SR-0008", "DEC-0008"]
    assert found("a DEC without a number is not a pointer") == []
    assert found("about five hours of a generation's critical path") == []


# ================================================== 1. the retrospective the auditing role runs
def _audit_role(kit_dir):
    """The role a kit's own scheduling hook names as the one it audits with.

    Read off `hooks/_routine.AUDIT_ROLE` — the constant the shipped hook decides on — so a kit that
    renames the role moves this subject rather than leaving this file measuring a dead name.
    """
    path = os.path.join(kit_dir, "hooks", "_routine.py")
    with io.open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "AUDIT_ROLE"
                for target in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("%s decides on no AUDIT_ROLE constant" % path)


def _do_steps(path):
    """The numbered steps of a skill's `## Do` section, raw — the unit that section is written in.

    Raw and not a reading view, because these steps are compared BYTE for byte across kits below
    and a whitespace-flattened slice would call two differently wrapped copies the same text.
    """
    with io.open(path, encoding="utf-8") as handle:
        text = handle.read()
    blocks = [block for block in _markdown_sections(text) if block.startswith("## Do")]
    assert len(blocks) == 1, (path, len(blocks))
    return [step.rstrip("\n") for step in _STEP_SPLIT_RX.split(blocks[0])[1:]]


def _question_steps(path):
    """The steps that pose a numbered list of questions — the retrospective, found by its shape.

    No heading word and no phrase: a step whose sub-list is questions is doing one thing, and that
    shape survives a rewording of the step's own lead-in.
    """
    return [step for step in _do_steps(path) if len(_QUESTION_RX.findall(step)) >= 4]


def _auditing_role_files():
    """(kit dir, role definition, skill) for every kit that ships the role its hook schedules."""
    for kit in _kit_dirs():
        role = _audit_role(kit)
        definition = os.path.join(kit, "agents", role + ".md")
        skill = os.path.join(kit, "skills", role, "SKILL.md")
        if os.path.isfile(definition) and os.path.isfile(skill):
            yield kit, definition, skill


def test_the_auditing_role_of_every_kit_runs_a_retrospective_and_it_is_one_text():
    """FR-0084: reflection is a STEP bound to occasions, in every kit, in one wording.

    MEASURED RED on the tree before this round: no `## Do` step of any kit's auditing skill posed a
    question list at all, so `_question_steps` returned nothing for all three — reflection existed
    where a procedure demanded a measurement and nowhere else, which is the measurement FR-0084 was
    filed on.

    WHAT IS HELD: exactly one such step per kit, the same text in all of them, at least four
    occasions named in it, and its own honest limit. WHAT IS NOT: whether the auditor answered the
    questions, or answered them with a measurement. Nothing can read that — the answers are free
    text in an Evidence item.
    """
    steps, judged = {}, 0
    for kit, _definition, skill in _auditing_role_files():
        name = os.path.basename(kit)
        found = _question_steps(skill)
        assert len(found) == 1, (
            "%s: %d steps of the auditing skill pose a question list, expected exactly one — the "
            "retrospective is one step, and two of them means one of the two is not it"
            % (name, len(found)))
        judged += 1
        steps[name] = found[0]
        occasions = _OCCASION_RX.findall(found[0])
        assert len(occasions) >= 4, (
            "%s: the retrospective step names %d occasions; it is bound to occasions and not to a "
            "cadence, so the occasions are the half that makes it a step at all"
            % (name, len(occasions)))
        assert "`%s`" % _handback_field() in found[0], (
            "%s: the retrospective step no longer names the field its three lines for the user go "
            "into, so the half that reaches the user is gone and every count above is unchanged"
            % name)
    assert judged >= 3, "only %d kits judged — the auditing role is shipped by more" % judged
    assert len(set(steps.values())) == 1, (
        "the kits' retrospective steps have drifted apart; this block is one text: %s"
        % sorted(steps))


def test_the_retrospective_step_states_the_limit_it_runs_under():
    """The step describes a trigger nothing fires, so the step has to say so (SR-0008).

    A reader who finds four occasions and no limit assumes something watches for them. Nothing
    does: the duty register reports the run due once per period and no hook and no gate detects an
    occasion. Both directions are asked — every mention of the enforcement layer stands in a clause
    that negates it, and at least one such mention is there — with the same reader
    `test_role_contracts.test_the_answering_rule_claims_no_enforcement_it_does_not_have` uses, and
    the same finite vocabulary it names as its own limit.

    THE READING VIEW, not the raw block: a line break is a clause boundary to that reader, so a
    negation and the word it negates would have to share a source line by accident of wrapping.
    """
    judged = 0
    for kit, _definition, skill in _auditing_role_files():
        words = _mechanism_words(kit)
        assert words, "%s registers no hooks — the vocabulary came out empty" % kit
        for step in _question_steps(skill):
            judged += 1
            affirmed, negated = _enforcement_claims(_reading_view(step), words)
            assert not affirmed, (
                "%s: the retrospective step names the enforcement layer without a negation, and "
                "nothing fires this step:\n  %s" % (os.path.basename(kit), "\n  ".join(affirmed)))
            assert negated, (
                "%s: the retrospective step states no limit at all, so a reader assumes a trigger "
                "behind it" % os.path.basename(kit))
    assert judged >= 3, judged


def _pointing_bullets(path, pointer):
    """The bullets of a role definition that carry `pointer`, raw."""
    with io.open(path, encoding="utf-8") as handle:
        text = handle.read()
    return [bullet.rstrip("\n") for bullet in _BULLET_SPLIT_RX.split(text)[1:]
            if pointer in bullet]


def test_the_occasion_rule_stands_in_the_file_a_spawn_actually_loads():
    """A duty that lives only in a SKILL may never reach a subagent — the kits say so themselves.

    Every one of these role definitions carries the measurement in its own last paragraph: a role's
    `skills:` frontmatter delivers nothing to a session bound to it, and the subagent-spawn path is
    unmeasured. So the occasion half of the retrospective is held in the definition too, as one
    text across the kits, and it points at the decision it is the shape of.

    MEASURED RED before this round: no bullet of any of the three role definitions carried the
    pointer, so this test found nothing to judge in any kit.
    """
    assert VERDICT_DECISION in _items_in_the_store(), (
        "%s is not in this store any more; the bullets below point at it, so the anchor has to "
        "move with it" % VERDICT_DECISION)
    bullets, judged = {}, 0
    for kit, definition, _skill in _auditing_role_files():
        name = os.path.basename(kit)
        found = _pointing_bullets(definition, "`%s`" % VERDICT_DECISION)
        assert len(found) == 1, (
            "%s: %d bullets of the auditing role definition point at %s, expected exactly one"
            % (name, len(found), VERDICT_DECISION))
        judged += 1
        bullets[name] = found[0]
        affirmed, negated = _enforcement_claims(_reading_view(found[0]), _mechanism_words(kit))
        assert not affirmed and negated, (
            "%s: the occasion bullet claims a trigger nothing builds (affirmed=%s, negated=%s)"
            % (name, affirmed, negated))
    assert judged >= 3, judged
    assert len(set(bullets.values())) == 1, (
        "the kits' occasion bullets have drifted apart; this is one text: %s" % sorted(bullets))


# ============================== 2. the reading a work order gets before it is sent (AC-2, AC-3)
def _lead_skill(kit_dir):
    """The kit's lead SKILL, off `settings.json` through `lead_package`, or None."""
    found = lead_package.on_demand_files(kit_dir)
    return found[0] if found else None


def _numbered_forms(block):
    """The numbered, bold-opened items of `block` — the forms a work-order line can take."""
    return [item.rstrip("\n") for item in _FORM_SPLIT_RX.split(block)[1:]]


def _order_reading_sections(path):
    """The `##` sections that lay out numbered forms, each answering for itself with an item.

    FOUND BY SHAPE, not by a heading word: a section whose numbered items each point at the record
    of the case that produced them is doing this one job, and no other section of a lead skill is
    written that way. The heading may be reworded without this reader losing it, and a section that
    keeps the heading while losing the pointers is found missing — which is the direction that
    matters, because the pointers are the part that rots.
    """
    with io.open(path, encoding="utf-8") as handle:
        text = handle.read()
    out = []
    for block in _markdown_sections(text):
        forms = _numbered_forms(block)
        if len(forms) >= 5 and all(_item_citations(form) for form in forms):
            out.append(block.rstrip("\n"))
    return out


def test_every_kit_lead_is_given_the_ways_a_work_order_line_goes_wrong():
    """FR-0010/AC-3: the forms are a PROCEDURE in the lead's own text, each with its case.

    THE SUBJECT IS DERIVED: whichever role a kit's `settings.json` binds as its session agent writes
    that kit's work orders, and `lead_package.on_demand_files` is the procedure document that role
    opens. A kit that renames its lead moves this subject with it.

    MEASURED RED before this round: `_order_reading_sections` returned nothing for all three lead
    skills — the five forms lived in three decision items of the workshop and in no shipped text.

    WHAT IS HELD: one such section per lead skill, the same text in all three, every form pointing
    at an item this store holds, and the smaller-plan reading beside them with its three conditions.
    WHAT IS NOT: whether the lead performed either reading. No gate reads a work order's wording,
    which is why the section states that itself and why the statement is measured below.
    """
    store = _items_in_the_store()
    sections, judged = {}, 0
    for kit in _kit_dirs():
        skill = _lead_skill(kit)
        assert skill, "%s binds no session agent, so nothing owns its work orders" % kit
        name = os.path.basename(kit)
        found = _order_reading_sections(skill)
        assert len(found) == 1, (
            "%s: %d sections of the lead skill lay out the forms of a work-order line, expected "
            "exactly one" % (name, len(found)))
        judged += 1
        sections[name] = found[0]
        for form in _numbered_forms(found[0]):
            dangling = [hit.group(0) for hit in _item_citations(form)
                        if hit.group(0) not in store]
            assert not dangling, (
                "%s: a form points at an item this store does not hold (%s), so the case behind it "
                "cannot be read" % (name, ", ".join(dangling)))
        conditions = _BULLET_SPLIT_RX.split(found[0])[1:]
        assert len(conditions) >= 3, (
            "%s: the smaller-plan reading carries %d conditions. Without them a critic that never "
            "agrees, and one that judges instead of planning, are both still allowed"
            % (name, len(conditions)))
        assert "`%s`" % _decision_type() in found[0], (
            "%s: the section no longer names the item type the choice is recorded as, so the "
            "comparison is made and forgotten and the same question comes back next round" % name)
    assert judged >= 3, "only %d lead skills judged" % judged
    assert len(set(sections.values())) == 1, (
        "the kits' order-reading sections have drifted apart; this is one text: %s"
        % sorted(sections))


# What a line of this prose looks like when it has ENDED a sentence, after the markup that can
# trail one is taken off. The set is the punctuation a sentence closes with, not a list of
# spellings somebody collected: a line that stops anywhere else is a line the next line continues.
_SENTENCE_END = ".!?"
_TRAILING_MARKUP = "*`\"')_ \t"


def _ends_a_sentence(line):
    stripped = line.rstrip(_TRAILING_MARKUP)
    return bool(stripped) and stripped[-1] in _SENTENCE_END


def _statement_around(lines, index):
    """The index at which the bold-lead statement containing line `index` begins.

    A statement of this prose opens with a bold lead-in -- the same unit `test_role_contracts`
    reads the constitutions by -- so the nearest such line at or above `index` is where it starts.
    """
    while index > 0 and not lines[index].lstrip().startswith("**"):
        index -= 1
    return index


def _torn_sentence_above(block, names):
    """Does ANY bold-lead statement naming `names` cut into the sentence above it?

    THE DEFECT THIS EXISTS FOR (verifier round 1, B1): the pointer was inserted between
    `Verify outputs against REALITY` and its own parenthesis, so the sentence lost its second half
    and the parenthesis opened a paragraph. Nothing saw it -- the test beside this one asks only
    whether the heading is named ANYWHERE in the work loop, and a torn sentence names it just as
    well as an intact one. The question a reader CAN answer is the POSITION: an inserted statement
    belongs where the line above it has finished saying something.

    EVERY MENTION, NOT THE FIRST, and that is verifier round 2 (N1): with `next(...)` a clean
    pointer at the top made a second, torn one further down invisible. Measured there, rc 0.

    WHAT IT STILL CANNOT SEE, said here and in the protocol rather than left to the next round: an
    insertion that is NOT bold-led. `_statement_around` climbs to the nearest bold lead-in, which is
    the shape a statement of this prose has, so an unbolted paragraph dropped into the middle of a
    sentence climbs past its own start and is judged at somebody else's boundary.
    """
    lines = block.splitlines()
    for named, line in enumerate(lines):
        if names not in line:
            continue
        start = _statement_around(lines, named)
        if start > 0 and not _ends_a_sentence(lines[start - 1]):
            return True
    return False


def test_the_order_reading_is_a_step_of_the_work_loop_and_not_an_appendix():
    """A step outside the sequence is a step nobody runs (FR-0005), and it does not tear one.

    The work loop is where a lead reads what to do next, so the section has to be named THERE, by
    its heading, before the order goes out. Measured red before this round in the trivial
    direction: there was no section and no pointer.

    THE SECOND HALF IS THE VERIFIER'S FINDING B1: naming the heading somewhere in the work loop is
    not enough, because a pointer dropped into the middle of a sentence names it just as well. So
    the POSITION is asked too -- the line above the pointer has to have finished a sentence. What
    this cannot judge is whether the position is the RIGHT one among the boundaries; that is a
    reading, and it is named as such in the protocol.
    """
    judged = 0
    for kit in _kit_dirs():
        skill = _lead_skill(kit)
        with io.open(skill, encoding="utf-8") as handle:
            text = handle.read()
        loops = [block for block in _markdown_sections(text) if block.startswith("## Work loop")]
        assert len(loops) == 1, (skill, len(loops))
        heading = _order_reading_sections(skill)[0].splitlines()[0].lstrip("# ").rstrip()
        assert heading in _reading_view(loops[0]), (
            "%s: the work loop never names %r, so the reading has no place in the sequence"
            % (os.path.basename(kit), heading))
        assert not _torn_sentence_above(loops[0], heading), (
            "%s: the pointer at the order reading is inserted where the line above it has not "
            "finished a sentence, so it cuts that sentence in half" % os.path.basename(kit))
        judged += 1
    assert judged >= 3, judged


def test_the_position_reader_can_tell_a_sentence_boundary_from_the_middle_of_one():
    """The floor under the position check, so "always fine" and "never fine" both fail here.

    The probes are the two real positions of verifier round 1: the office kit's torn sentence
    (`Verify outputs against REALITY` continues into a parenthesis on the next line) and the dev
    kit's clean one (`... with a confirmed design.`), plus the markup a line of this prose really
    ends with.
    """
    torn = ("   files to read, and the scope it may write. Verify outputs against REALITY\n"
            "   **Before this order goes out it gets ONE reading**, the section below —\n"
            "   \"Before the order goes out\".\n")
    clean = ("   and `design_ref` for a UI task with a confirmed design.\n"
             "   **Before this order goes out it gets ONE reading**, the section below —\n"
             "   \"Before the order goes out\".\n")
    assert _torn_sentence_above(torn, "Before the order goes out")
    assert not _torn_sentence_above(clean, "Before the order goes out")
    assert _torn_sentence_above(clean + torn, "Before the order goes out"), (
        "a clean mention above a torn one must not hide it -- verifier round 2, N1")
    assert _ends_a_sentence("never trust \"done\" strings.")
    assert _ends_a_sentence("before the spawn — never the specialist.**")
    assert _ends_a_sentence("open it with `/parallel-streams`.")
    assert not _ends_a_sentence("Verify outputs against REALITY")
    assert not _ends_a_sentence("the trigger, the cadence and the read")
    assert not _ends_a_sentence("")


def test_the_order_reading_claims_no_enforcement_it_does_not_have():
    """The section is about honest orders, so it may not overclaim about itself (SR-0008).

    Nothing refuses an order that skipped either reading: the dispatch gate validates the header
    against the lease and free prompt prose is evidence of nothing. Both halves are asked, as in the
    retrospective's limit above — no affirmed mention of the enforcement layer, and at least one
    negated one, so a reader can neither assume a mechanism nor be left without the limit.
    """
    judged = 0
    for kit in _kit_dirs():
        words = _mechanism_words(kit)
        for section in _order_reading_sections(_lead_skill(kit)):
            judged += 1
            affirmed, negated = _enforcement_claims(_reading_view(section), words)
            assert not affirmed, (
                "%s: the order-reading section names the enforcement layer without a negation:\n"
                "  %s" % (os.path.basename(kit), "\n  ".join(affirmed)))
            assert negated, (
                "%s: the order-reading section states no limit, so a reader assumes something "
                "refuses an order that skipped it" % os.path.basename(kit))
    assert judged >= 3, judged


# The wish whose second half this paragraph is: EVERY plan names in one line the alternative it
# rejected. It is the ANCHOR of the paragraph in the same sense `VERDICT_DECISION` is the anchor of
# the rules — the pointer the paragraph exists to carry, so a dead id sends this reader looking for
# a block that is no longer there rather than matching a heading whose wording drifted.
PLAN_WISH = "FR-0084"


def _rejection_paragraphs(path):
    """The bold-lead paragraphs of a constitution that answer for themselves with `PLAN_WISH`."""
    with io.open(path, encoding="utf-8") as handle:
        text = handle.read()
    return [unit for unit in _lead_in_units(text)
            if PLAN_WISH in {hit.group(0) for hit in _item_citations(unit)}]


def test_every_constitution_asks_a_plan_for_the_way_it_rejected():
    """FR-0084, second half: the rejected-alternative line is a duty of EVERY plan, in every kit.

    WHY THE CONSTITUTION AND NOT A SKILL: the duty binds whoever BUILDS, and a kit ships many
    building roles whose procedure documents are not this stream's to write. The constitution is the
    one text every role of a kit is sent to, it is the place the wish itself names, and it is the
    text that reaches a scaffolded project as its `AGENTS.md`.

    MEASURED RED before verifier round 1 closed it: the duty stood as a single bullet in this repo's
    own implementer role text and in none of the three kits — `grep -rn "rejected" team-kits/*/
    constitution/` found nothing, and no test named it.

    ONE TEXT IN ALL THREE, held twice over: here, and by
    `tools/test_role_contracts.py::test_a_paragraph_the_constitutions_share_is_one_text`, which
    takes any bold lead-in shared by two constitutions and demands the third and byte-equality.

    WHAT THIS CANNOT DO: see whether a plan really carried the line. No gate reads a specialist's
    prose, which is why the paragraph says so itself and why that statement is measured below.
    """
    assert PLAN_WISH in _items_in_the_store(), (
        "%s is not in this store any more; the paragraph points at it" % PLAN_WISH)
    paragraphs, judged = {}, 0
    for kit in _kit_dirs():
        name = os.path.basename(kit)
        found = _rejection_paragraphs(os.path.join(kit, "constitution", "AGENTS.md"))
        assert len(found) == 1, (
            "%s: %d constitution paragraphs answer for the rejected-alternative duty with %s, "
            "expected exactly one" % (name, len(found), PLAN_WISH))
        paragraphs[name] = found[0]
        judged += 1
    assert judged >= 3, judged
    assert len(set(paragraphs.values())) == 1, (
        "the kits' rejected-alternative paragraphs have drifted apart; this is one text: %s"
        % sorted(paragraphs))


def test_the_rejected_alternative_rule_claims_no_enforcement_it_does_not_have():
    """The duty has no gate behind it, so the paragraph that states it may not suggest one.

    Same reader and same two halves as the other honesty checks in this module: no affirmed mention
    of the enforcement layer, and at least one negated mention, so a reader can neither assume a
    mechanism nor be left without the limit.
    """
    judged = 0
    for kit in _kit_dirs():
        words = _mechanism_words(kit)
        for paragraph in _rejection_paragraphs(os.path.join(kit, "constitution", "AGENTS.md")):
            judged += 1
            affirmed, negated = _enforcement_claims(_reading_view(paragraph), words)
            assert not affirmed, (
                "%s: the rejected-alternative paragraph names the enforcement layer without a "
                "negation:\n  %s" % (os.path.basename(kit), "\n  ".join(affirmed)))
            assert negated, (
                "%s: the rejected-alternative paragraph states no limit, so a reader assumes a "
                "plan check behind it" % os.path.basename(kit))
    assert judged >= 3, judged


# ================================================ 3. this repo's own orchestrator rules (AC-4)
def _lead_role_text():
    path = os.path.join(ROOT, ".claude", "agents", "harness-lead.md")
    with io.open(path, encoding="utf-8") as handle:
        return path, handle.read()


def _numbered_rules(text, decision):
    """{rule number: bullet} for every bullet of `text` that points at a numbered rule."""
    pointer = _rule_pointer_rx(decision)
    found = {}
    for bullet in _BULLET_SPLIT_RX.split(text)[1:]:
        hit = pointer.search(bullet)
        if hit:
            found[int(hit.group("number"))] = bullet
    return found


def _mechanism_terms(bullet):
    """The backticked terms of `bullet` that are NOT item ids — what the rule is ABOUT.

    A rule that says which mechanism it binds names it; one reworded into a slogan does not. That
    is the half a pointer cannot carry: the pointer says WHY the rule exists and survives any
    rewriting of the sentence around it, which is exactly how verifier round 1 replaced rule 5 with
    "Send whatever, whenever" and kept the test green.
    """
    identifier = _item_id_rx()
    return [span.group(1) for span in re.finditer(r"`([^`]+)`", bullet)
            if not identifier.fullmatch(span.group(1).strip())]


def test_the_lead_role_text_carries_the_orchestrator_rules_with_their_pointers():
    """DEC-0070 (1), (2) and (5) live in the role text, because no other surface holds them.

    WHY HERE AND NOT IN A GATE: the decision says it itself — rule 5 is enforced "by the harness-lead
    role text (an implementer edits it, gate 1 refuses the lead)". A rule in a role text is a rule
    somebody reads, and what a check can hold is that each rule is THERE, that its reason can be
    opened, and that it still names the mechanism it is about.

    MEASURED RED before this round: `harness-lead.md` carried no bullet pointing at the decision at
    all — the three rules stood in the decision item and in a round log, which is the state PR-0006
    was filed on.

    TWO CORRECTIONS ARE BUILT INTO THIS, and both were measured on the shipped text rather than
    argued. The first was mine: counting MENTIONS gave a number that deleting one rule could not
    move, because a fourth bullet names the same decision as the retrospective's worked example.
    The second is verifier round 1 (B3): counting RULE POINTERS is still a count — deleting rule 2
    and duplicating rule 1 kept three of them, and rule 5 could be replaced by a slogan as long as
    its pointer stayed. So the numbers are read as a SET and compared with the rules this file was
    given, and each rule must still name a mechanism in backticks.

    WHAT THIS STILL CANNOT DO: judge whether the sentence around the pointer says the right thing.
    A rewording that keeps both the number and a mechanism name passes, and that limit is named in
    the protocol rather than left for the next round to find.
    """
    assert VERDICT_DECISION in _items_in_the_store(), (
        "%s is not in this store any more" % VERDICT_DECISION)
    path, text = _lead_role_text()
    where = os.path.relpath(path, ROOT)
    found = _numbered_rules(text, VERDICT_DECISION)
    assert set(found) == set(ORCHESTRATOR_RULES), (
        "%s carries the rules %s of %s; it was given %s. A missing one is a rule nobody reads any "
        "more, an extra one is a rule nobody decided to put here"
        % (where, sorted(found), VERDICT_DECISION, sorted(ORCHESTRATOR_RULES)))
    bare = [number for number, bullet in found.items() if not _mechanism_terms(bullet)]
    assert not bare, (
        "%s: rule(s) %s point at %s and name no mechanism at all, so the pointer is the whole of "
        "the rule and the sentence around it can say anything"
        % (where, sorted(bare), VERDICT_DECISION))


def test_the_rule_reader_can_tell_a_rule_from_a_mention_and_a_slogan_from_a_rule():
    """The floor under the reading above, so every way of not reading it fails here.

    The probes are the shapes that really stand in `harness-lead.md` plus the two mutations
    verifier round 1 used: the bare mention beside the rules (the worked example, not a rule) and a
    rule reworded into a slogan while its pointer stays.
    """
    pointer = _rule_pointer_rx(VERDICT_DECISION)
    assert pointer.search("(`%s`, rule 1). Before a spawn" % VERDICT_DECISION)
    assert pointer.search(
        "round, not a stream** (`%s`,\n  rule 2). Each narrowing" % VERDICT_DECISION)
    assert not pointer.search("(`%s` is the worked example). Four occasions" % VERDICT_DECISION)
    assert not pointer.search("the rule 5 of a decision nobody named")
    assert not pointer.search("(`DEC-0063`, rule 2) is another decision entirely")

    numbers = _numbered_rules(
        "- **one** (`%s`, rule 1) with `check-scopes`\n"
        "- **two** (`%s`, rule 5) with `ListAgents`\n"
        "- **not a rule** (`%s` is the worked example)\n"
        % (VERDICT_DECISION, VERDICT_DECISION, VERDICT_DECISION), VERDICT_DECISION)
    assert sorted(numbers) == [1, 5], sorted(numbers)
    assert _mechanism_terms(numbers[1]) == ["check-scopes"]
    assert _mechanism_terms("- **Send whatever, whenever** (`%s`, rule 5)." % VERDICT_DECISION) == []
    assert _mechanism_terms("- **x** (`%s`, rule 5) and `SR-0008`." % VERDICT_DECISION) == [], (
        "an item id is a pointer, not the mechanism a rule binds")
    assert not pointer.search("(`DEC-0063`, rule 2) is another decision entirely")


# WHICH generation-3 lesson each worker text was given, named by the RECORD that holds its case:
# the wish for the plan's rejected alternative, the verdict for "a named test must be able to fail",
# the merge round for the rig that writes binary and stays in its own directory. An enumeration, and
# it carries a tripwire at both ends -- a record here that no statement of that file cites is a
# lesson that has gone missing, and one that no longer resolves in the store is a dead entry. It
# does NOT claim to be every pointered statement of those files; they carry others, older than this
# round.
LESSONS_BY_ROLE = {
    "harness-implementer": ("FR-0084", VERDICT_DECISION, "TSK-0120"),
    "harness-verifier": ("TSK-0120",),
}

# A statement of these texts opens with a bold lead-in, as a bullet or as a paragraph -- the same
# unit `test_role_contracts._LEAD_IN_RX` reads the constitutions by.
_UNIT_START_RX = re.compile(r"(?m)^(?:- )?\*\*")


def _lead_in_units(text):
    """Every bold-lead statement of `text`, as its own block, stopping at the next `##` heading."""
    starts = [match.start() for match in _UNIT_START_RX.finditer(text)]
    units = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(text)
        block = text[start:end]
        heading = re.search(r"(?m)^##\s", block)
        units.append((block[:heading.start()] if heading else block).rstrip("\n"))
    return units


def test_every_harness_role_text_answers_for_the_lessons_it_was_given():
    """AC-4: each generation-3 lesson is a STATEMENT of its own, answering for itself.

    The lessons themselves are prose and stay prose — "mutate it and watch it go red" is a habit,
    not a property a check can read. What a check can hold is that each lesson is still THERE as its
    own statement and still names the record its case comes from.

    MEASURED RED before this round: two of the three files named no record at all.

    THE CORRECTION OF VERIFIER ROUND 1 (B2) IS THE READING ITSELF. The first cut asked whether the
    verdict was named ANYWHERE in the file — a string search over the whole text, against this
    module's own docstring — and the implementer text named it once, in a heading. Measured there:
    all three lessons deleted with the heading kept, one of three deleted, and a lesson replaced by
    nonsense while the pointer stayed were all rc 0. Now the unit is the bold-lead statement, each
    lesson carries its own record, and no two lessons may hide behind one statement.

    WHAT THIS STILL CANNOT DO: read what the statement SAYS. A lesson reworded around its own
    pointer passes, and that limit is named in the protocol.
    """
    store = _items_in_the_store()
    judged = 0
    for rel, text in _harness_role_texts():
        expected = LESSONS_BY_ROLE.get(os.path.basename(rel)[:-len(".md")])
        if not expected:
            continue
        units = _lead_in_units(text)
        carriers = {}
        for record in expected:
            assert record in store, (
                "%s is named as a lesson's record and is not in this store" % record)
            carriers[record] = [unit for unit in units
                                if record in {hit.group(0) for hit in _item_citations(unit)}]
        missing = sorted(record for record, found in carriers.items() if not found)
        assert not missing, (
            "%s no longer carries a statement answering for %s — the lesson is gone, or it lost the "
            "record its case comes from" % (rel, ", ".join(missing)))
        shared = [one for one in units
                  if sum(1 for found in carriers.values() if one in found) > 1]
        assert not shared, (
            "%s: one statement carries several lessons' records, so deleting a lesson would not "
            "show here:\n  %s" % (rel, "\n  ".join(_reading_view(one)[:90] for one in shared)))
        judged += 1
    assert judged == len(LESSONS_BY_ROLE), (
        "%d of %d worker role texts judged — a file named here was not found"
        % (judged, len(LESSONS_BY_ROLE)))


def test_the_statement_reader_splits_a_role_text_where_its_statements_begin():
    """The floor under the reading above, so "one unit" and "no units" both fail here.

    The probes are the two shapes these files really use — a bullet and a paragraph, both opening
    with a bold lead-in — plus the heading that must not be swallowed into the statement above it.
    """
    text = ("intro prose nobody reads as a statement\n\n"
            "- **first lesson** (`FR-0084`) says a thing.\n"
            "- **second lesson** (`DEC-0070`) says another.\n\n"
            "## Next section\n\n"
            "**a paragraph lesson** (`TSK-0120`) with its own record.\n")
    units = _lead_in_units(text)
    assert len(units) == 3, units
    assert units[0].startswith("- **first lesson**") and "second lesson" not in units[0]
    assert "## Next section" not in units[1], "a statement stops at the next heading"
    assert units[2].startswith("**a paragraph lesson**")
    assert _lead_in_units("no bold lead-in anywhere here.\n") == []


# ==================================== 4. the two limits, measured on a project outside this repo
def test_no_occasion_makes_the_audit_run_due_and_that_is_the_seam(tmp_path):
    """The retrospective's trigger, measured: the duty register knows PERIODS and no occasions.

    `test_routine_feed` already measures that a run in the period clears the duty and that the
    period boundary is the ISO week; what is measured HERE is the other half, which the
    retrospective step claims about itself: an OCCASION changes nothing. Two projects on the same
    day, one of them having just delivered a goal and recorded evidence for it — the occasion the
    step's second trigger names — give the identical duty in both directions: due while no run is
    recorded, clear while one is.

    THIS TEST IS WRITTEN TO GO RED. The wiring belongs to `hooks/_routine.py` and
    `session_status.py`, which this stream may not write, so it is a SEAM: the day an occasion
    makes the run due, the two projects part company here, and the honest-limit sentence in every
    kit's auditing skill and role definition is what has to be corrected.
    """
    import datetime
    from kernel.state import ProjectState
    from conftest import walk_to_status
    from test_parallel_streams import PR_FIELDS
    from test_routine_feed import event, routine_module

    today = datetime.date.today()
    judged = 0
    for kit in ("dev-team", "office-team", "research-team"):
        routine = routine_module(kit)
        roots = {}
        for name in ("plain", "delivered"):
            root = tmp_path / kit / name / "project_memory"
            os.makedirs(str(root), exist_ok=True)
            roots[name] = os.path.dirname(str(root))
        state = ProjectState(os.path.join(roots["delivered"], "project_memory"))
        walk_to_status(state, state.capture("PR", dict(PR_FIELDS)), "DELIVERED")

        due = {name: routine.routine_duties(root, today)[0] for name, root in roots.items()}
        assert all(one and routine.AUDIT_ROLE in one[0]["what"] for one in due.values()), due
        assert due["plain"][0]["what"] == due["delivered"][0]["what"], (
            "%s: a delivered goal changed what the duty register says, so this seam has moved: %s"
            % (kit, due))

        for name, root in roots.items():
            path = os.path.join(root, "project_memory", ".audit", "hook_events.jsonl")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with io.open(path, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(event(routine.AUDIT_ROLE, datetime.datetime.now())) + "\n")
        cleared = {name: routine.routine_duties(root, today)[0] for name, root in roots.items()}
        assert not any(cleared.values()), (
            "%s: a run in this period must clear the duty in both projects: %s" % (kit, cleared))
        judged += 1
    assert judged >= 3, judged


def test_nothing_reads_what_a_work_order_LINE_says(tmp_path):
    """The limit the order-reading section states about itself, measured on the running dispatch.

    An order whose `expected_outputs` names a building block NO requirement of its goal names — the
    mechanical trigger of the smaller-plan reading — is captured, leased and dispatched by the
    kernel like any other. The reading is therefore the lead's and nothing else's, which is what
    the section says and what `docs/POST_V2_WISHLIST.md` carries as `H157`.

    THIS TEST IS WRITTEN TO GO RED the day a reader over an order's wording is built; then the
    section's limit sentence is the one to correct.
    """
    from kernel.state import ProjectState
    from conftest import drive_task_to, walk_to_status
    from test_parallel_streams import PR_FIELDS, TSK_FIELDS

    root = tmp_path / "pilot" / "project_memory"
    os.makedirs(str(root), exist_ok=True)
    state = ProjectState(str(root))
    goal = state.capture("PR", dict(PR_FIELDS))
    walk_to_status(state, goal, "APPROVED")
    unrequested = "src/capture_migrated_archive.py"
    assert not [criterion for criterion in goal["acceptance_criteria"]
                if unrequested in criterion["text"]], goal["acceptance_criteria"]
    order = state.capture("TSK", dict(TSK_FIELDS, product_requirement=goal["id"],
                                      derives_from=goal["id"], root_revision=goal["revision"],
                                      expected_outputs=[unrequested]))
    drive_task_to(state, order["id"], "LEASED")
    assert state.read_item(order["id"])["status"] == "LEASED", state.read_item(order["id"])


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))

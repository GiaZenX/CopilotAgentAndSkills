"""The skill contract of a kit: one procedure per role, any number of shared REFERENCE skills.

TWO QUESTIONS, and they were one until this round because there was only ever one answer. Every
shipped role declared exactly one skill named after itself, so "which skill does this role open"
had no content. `FR-0068`/`FR-0070` put two SHARED skills beside the roles and `FR-0071` states the
consequence: the moment a second skill exists, the role text names them all and the role reaches
for the habitual one. So the file below measures

  * the DISTINCTION -- a procedure skill belongs to exactly one role and is named after it; a
    reference skill belongs to nobody, which is a property (no role's `skills:` frontmatter names
    it) and not a naming convention, and there is no third kind; and
  * the DERIVATION -- `kernel.references` computes the reference skills of a work order from the
    task, with the tripwire running in BOTH directions: a shipped reference skill that no task
    could ever reach is dead weight and fails here, and an order that could name a skill the kit
    does not ship fails here too.

Plus the duties that come with vendoring somebody else's file (Apache-2.0 §4): the licence copy
travels inside the skill directory, the modifications are marked, and `NOTICES.md` and the tree
cannot drift apart.

WHAT NONE OF THIS CAN DO, said here rather than discovered later: nothing in this suite reaches the
network, so no test compares a vendored file against its upstream bytes. What makes that checkable
at all is the provenance in each vendored `SKILL.md` frontmatter (`source_commit`,
`source_blob_sha1`) -- a later round re-fetches and diffs; this file only holds the marks and the
frontmatter to each other.
"""
import glob
import io
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEAM_KITS = os.path.join(ROOT, "team-kits")
sys.path.insert(0, TEAM_KITS)

from conftest import approve, drive_task_to  # noqa: E402 -- shared suite helpers
from kernel import backlog_types, dispatch, references  # noqa: E402
from kernel.state import ProjectState  # noqa: E402

yaml = pytest.importorskip("yaml")


def _kit_dirs():
    """Every shipped kit, taken from the tree by the file that makes it one."""
    return sorted(os.path.dirname(os.path.dirname(path)) for path in
                  glob.glob(os.path.join(TEAM_KITS, "*", "constitution", "AGENTS.md")))


def _frontmatter(path):
    with io.open(path, encoding="utf-8") as handle:
        text = handle.read()
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    front = yaml.safe_load(text[3:end])
    return (front if isinstance(front, dict) else {}), text[end + 4:]


def _roles(kit_dir):
    """{role: declared skills} for every role the kit ships an agent file for."""
    out = {}
    for path in sorted(glob.glob(os.path.join(kit_dir, "agents", "*.md"))):
        role = os.path.splitext(os.path.basename(path))[0]
        front, _body = _frontmatter(path)
        declared = front.get("skills") or []
        out[role] = [str(one) for one in declared] if isinstance(declared, list) else [str(declared)]
    return out


def _skills(kit_dir):
    """{skill name: SKILL.md path} for every skill directory the kit ships."""
    return {os.path.basename(os.path.dirname(path)): path
            for path in sorted(glob.glob(os.path.join(kit_dir, "skills", "*", "SKILL.md")))}


def _reference_skills(kit_dir):
    """The skills NO role's frontmatter names — the property, read off the tree.

    This is the definition the constitution states, asked of the shipped files rather than of a
    list: a skill several roles may open is one that belongs to nobody. It is deliberately NOT
    "the ones carrying `reference_for`", because that would make the test below tautological — the
    two answers are computed from different places and are then required to agree.
    """
    owned = {name for declared in _roles(kit_dir).values() for name in declared}
    return {name: path for name, path in _skills(kit_dir).items() if name not in owned}


# ================================================== 1. one procedure skill per role
def test_a_role_declares_exactly_its_own_procedure_skill():
    """1:1 and named like the role — the rule the constitution's §1a states, over every kit.

    Not "at least its own": a role that lists a second skill in its frontmatter has taken a shared
    reference into private ownership, which is exactly the move `FR-0071` is about, and it would
    silently remove that skill from `_reference_skills` and therefore from the tripwire below.

    THE PROPERTY IS MEASURED OVER EVERY KIT AND ITS TEXT STANDS IN ONE, which is a mismatch worth
    stating rather than leaving to be discovered: only `dev-team`'s constitution carries §1a today,
    while all three kits now ship a reference skill (`humanizer`, FR-0072 -- the office and research
    copies arrived without a constitution sentence, because the constitutions are stream E's text
    and not the skill round's; `TSK-0105` carries that seam). The tree satisfies the rule in all
    three regardless (measured: every shipped role declares exactly its own skill), and narrowing
    the test to dev-team would let the other two drift into a shape the rule forbids while nothing
    said so.
    """
    seen = 0
    for kit_dir in _kit_dirs():
        shipped = _skills(kit_dir)
        for role, declared in sorted(_roles(kit_dir).items()):
            seen += 1
            assert declared == [role], (
                "%s/%s declares skills %r — a role declares exactly one skill and it carries the "
                "role's own name (constitution §1a); a shared skill is named by NO role."
                % (os.path.basename(kit_dir), role, declared))
            assert role in shipped, (
                "%s/%s names its own skill and the kit ships no skills/%s/SKILL.md"
                % (os.path.basename(kit_dir), role, role))
    assert seen >= 25, "only %d roles read — the derivation stopped matching" % seen


def test_every_shipped_skill_is_either_a_role_procedure_or_a_declared_reference():
    """No third kind. A skill nobody owns and that declares nothing is dead weight nobody notices.

    The two answers come from opposite ends — ownership from the AGENT files, the declaration from
    the SKILL's own frontmatter — and this is where they are made to agree. A skill directory that
    is neither owned by the role of the same name nor carries `reference_for` is the state in which
    a file ships, costs a copy on every install, and can never be reached by anything.
    """
    total_references = 0
    for kit_dir in _kit_dirs():
        kit = os.path.basename(kit_dir)
        shared = _reference_skills(kit_dir)
        declared = references.declarations(os.path.join(kit_dir, "skills"))
        total_references += len(shared)
        assert set(shared) == set(declared), (
            "%s: the skills no role owns %r and the skills declaring `reference_for` %r are not "
            "the same set — one of them is a file nothing can reach, the other a declaration on a "
            "skill that already belongs to a role"
            % (kit, sorted(shared), sorted(declared)))
    assert total_references >= 2, (
        "no kit ships a reference skill any more — everything below this line is vacuous")


# ================================================== 2. the derivation, both directions
def _orders(kit_dir):
    """Every (role, task type) pair a work order in this kit could carry — the whole input space.

    Roles from the kit's own agent files, types from the CLOSED vocabulary the kernel validates a
    TSK against (`backlog_types.TASK_TYPES`). Both ends derived, so a kit that gains a role or the
    kernel a task type widens this without anybody editing it.
    """
    for role in sorted(_roles(kit_dir)):
        for task_type in sorted(backlog_types.TASK_TYPES):
            yield role, task_type


def test_every_shipped_reference_skill_can_be_named_by_some_task():
    """DIRECTION ONE: a skill no derivation can ever reach is dead weight, and it fails here.

    Asked of the RUNNING derivation over the entire input space rather than of the declaration
    text: a `reference_for` naming a role the kit does not ship, or a task type outside the
    kernel's closed vocabulary, produces exactly this failure — the declaration is there and no
    order can satisfy it.
    """
    for kit_dir in _kit_dirs():
        kit, skills = os.path.basename(kit_dir), os.path.join(kit_dir, "skills")
        reachable = set()
        for role, task_type in _orders(kit_dir):
            reachable.update(references.for_task(skills, role, task_type))
        unreachable = sorted(set(_reference_skills(kit_dir)) - reachable)
        assert not unreachable, (
            "%s ships these reference skills and no (role, task type) a work order can carry ever "
            "names them, so they are copied into every project and reached by nothing: %s. Fix the "
            "`reference_for:` block in each — its `roles` must be roles this kit ships and its "
            "`task_types` must come from kernel.backlog_types.TASK_TYPES."
            % (kit, ", ".join(unreachable)))


def test_no_order_can_name_a_reference_skill_the_kit_does_not_ship():
    """DIRECTION TWO: every name an order emits has to resolve to a shipped SKILL.md.

    Same input space, opposite question, asked through `references.resolve` — the reader a consumer
    of the header would use — rather than by comparing two lists in this file.

    WHAT IT CAN AND CANNOT CATCH TODAY, because the honest answer is not "everything". As long as
    the derivation reads its names from the skill DIRECTORIES, an emitted name resolves by
    construction and this test cannot fail on the shipped tree. It is a floor under that
    construction, and it goes red the moment a name enters the derivation from anywhere else —
    measured, not asserted: a `for_task` that adds one literal name goes red here (`M6` of this
    round's mutation run), which is exactly the "map beside the directory" design this round chose
    against. The direction-two failure that CAN happen today — a shipped TEXT sending a role to a
    skill nobody ships — is a different reader and lives in
    `test_every_skill_retrieval_route_a_shipped_kit_file_spells_resolves`.
    """
    judged = 0
    for kit_dir in _kit_dirs():
        skills = os.path.join(kit_dir, "skills")
        for role, task_type in _orders(kit_dir):
            for name in references.for_task(skills, role, task_type):
                judged += 1
                assert references.resolve(skills, name), (
                    "%s: an order for role %r of type %r names the reference skill %r and the kit "
                    "ships no skills/%s/SKILL.md"
                    % (os.path.basename(kit_dir), role, task_type, name, name))
    assert judged, "no order named anything — the derivation returned nothing anywhere"


_CODEX_ROUTE = re.compile(r"\.agents/skills/([a-z0-9][a-z0-9-]*)/SKILL\.md")


def _route_mentions(kit_dir):
    """{skill name: [files]} for every skill-retrieval route spelled in this kit's shipped files.

    THE SPELLING THIS READS is the Codex path form, and the one it does NOT read is the Claude
    slash command — measured, not chosen: `` `/hooks` ``, `` `/model` `` and `` `/schedule` `` all
    stand in the shipped constitutions and PM skills as the PROVIDER's own commands, so a reader of
    that form reports three built-ins as missing skills in every kit. The path form names a skill
    directory and can name nothing else, which is what makes it readable at all. The cost is
    stated rather than hidden: a file that offers only the slash spelling is not covered here.
    """
    out = {}
    for path in sorted(glob.glob(os.path.join(kit_dir, "**", "*"), recursive=True)):
        if not os.path.isfile(path):
            continue
        try:
            with io.open(path, encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError:
            continue
        for hit in _CODEX_ROUTE.finditer(text):
            out.setdefault(hit.group(1), []).append(os.path.relpath(path, ROOT))
    return out


def test_every_skill_retrieval_route_a_shipped_kit_file_spells_resolves():
    """A text that sends a role to a skill has to send it somewhere.

    The other half of the tripwire, and the one that catches the failure a DERIVATION cannot: a
    ROLE FILE, a constitution or another skill naming a skill by its retrieval path.

    ITS SUBJECT IS THE KIT SOURCE, NOT AN INSTALLED PROJECT, and that difference is not academic
    -- it is where the first cut of this round was wrong. `.agents/skills/` in a project is
    GENERATED (`test_the_codex_mirror_is_generated_per_skill_directory` pins its subject against
    the generator), so a text may spell a route that resolves perfectly
    against `team-kits/<kit>/skills/` and reaches nothing in the project it was installed into.
    Two shipped SKILLs and the dev constitution said "Codex reads `.agents/skills/<name>/SKILL.md`"
    about skills the mirror never produced, and this test was green over all three. It stays a
    reader of the source tree -- running a scaffold per assertion is not a suite's job -- and the
    Codex-side claim is carried by the pin named above instead of by this one.

    A count of routes deliberately does not appear here: it would be a number nothing checks.
    """
    for kit_dir in _kit_dirs():
        shipped = _skills(kit_dir)
        mentions = _route_mentions(kit_dir)
        assert mentions, "%s: no retrieval route anywhere — the reader stopped matching" % kit_dir
        dangling = {name: files for name, files in mentions.items() if name not in shipped}
        assert not dangling, (
            "%s: these files spell a skill-retrieval route the kit does not ship, so a role that "
            "follows it opens nothing: %s"
            % (os.path.basename(kit_dir),
               "; ".join("%s -> %s" % (name, ", ".join(sorted(set(files))))
                         for name, files in sorted(dangling.items()))))


def test_the_route_reader_finds_the_spelling_it_claims_and_leaves_the_slash_form_alone(tmp_path):
    """The floor under the reader above: "find everything" and "find nothing" both fail here.

    The last two probes are the measured reason the slash form is out of scope — those are the
    provider's own commands, and reading them would report a missing skill in all three kits.
    """
    kit = tmp_path / "probe-team"
    (kit / "agents").mkdir(parents=True)
    (kit / "skills" / "alpha").mkdir(parents=True)
    (kit / "skills" / "alpha" / "SKILL.md").write_text("body\n", encoding="utf-8")
    (kit / "agents" / "one.md").write_text(
        "open `.agents/skills/alpha/SKILL.md`, and `/hooks` and `/model` are the provider's\n",
        encoding="utf-8")
    (kit / "agents" / "two.md").write_text(
        "Codex reads .agents/skills/ghost/SKILL.md\n", encoding="utf-8")
    found = _route_mentions(str(kit))
    assert sorted(found) == ["alpha", "ghost"], found
    assert "hooks" not in found and "model" not in found, found


_MIRROR_TEMPLATE = ".agents/skills/%s"


def _mirror_loop_iterators():
    """What every `.agents/skills/%s` producer in the generator ITERATES, read from its own AST.

    THE QUESTION IS ABOUT THE INSTALLED PROJECT and it is asked of the code that builds it, not of
    a scaffold run: `team-kits/gen_provider_artifacts.py` is what writes the Codex mirror, and the
    only thing three shipped texts needed from it was "which skills end up there". Every site that
    composes the mirror path is found by the string it composes with, and the enclosing `for` or
    comprehension is asked for the NAME it walks.

    THE GENERATOR HAS TWO CLASSES OF SITE and the reader keeps them apart instead of averaging
    them, because only one of them decides what lands in a project: one composes the paths the next
    run WRITES, the other inventories what a previous run LEFT so it can be removed. WHICH class a
    site is in is decided by the FUNCTION it stands in, not by the spelling of what it iterates.
    That is a correction with a measured hole behind it: the first cut exempted a site whose loop
    walked a call named `listdir`, so a third mirror site written literally as
    `for x in os.listdir(<skills>)` would have passed green anywhere in the file. `removal` here is
    `legacy_owned_outputs`, whose whole documented job is the previous generation's inventory --
    one function, one job, and the test below holds that exemption at BOTH ends.

    WHAT THIS READER DOES NOT DO, so the assertion below is not read as more than it is: it
    compares a NAME, not a value -- it cannot tell what the iterated call returns, and a generator
    that renamed the derivation while keeping the behaviour would go red here. That is the safe
    direction (a look, not a silent pass), and the alternative -- tracing the binding -- is the
    dataflow analysis `test_backlog_types` already names as the place a reader stops being one.
    """
    import ast

    path = os.path.join(TEAM_KITS, "gen_provider_artifacts.py")
    with io.open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), path)
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    found = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and node.value == _MIRROR_TEMPLATE):
            continue
        walker, iterated, function = node, None, ""
        while walker in parents:
            walker = parents[walker]
            if iterated is None and isinstance(walker, ast.For):
                iterated = walker.iter
            elif iterated is None and isinstance(
                    walker, (ast.GeneratorExp, ast.ListComp, ast.SetComp, ast.DictComp)):
                # the `comprehension` node hangs BELOW the comprehension, not above its element,
                # so climbing past it is how the first cut of this reader saw one producer where
                # the generator has two (measured: the `desired_dirs.update(...)` genexp was lost)
                iterated = walker.generators[0].iter if walker.generators else None
            elif isinstance(walker, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # ...and the climb does NOT stop at the loop any more: which function a site stands
                # in is what separates the producers from the removal inventory, so the walk runs
                # all the way up. Stopping at the loop is what made the exemption a NAME.
                function = walker.name
                break
        if iterated is None:
            found.append((node.lineno, function, "no loop"))
        elif isinstance(iterated, ast.Name):
            found.append((node.lineno, function, iterated.id))
        else:
            called = iterated.func if isinstance(iterated, ast.Call) else iterated
            found.append((node.lineno, function,
                          getattr(called, "attr", "") or getattr(called, "id", "")))
    return found


_MIRROR_DERIVATION = "native_skill_sources"
_MIRROR_REMOVAL = "legacy_owned_outputs"


def test_the_codex_mirror_is_generated_per_skill_directory():
    """What three shipped texts may promise a Codex session, held against the generator.

    MEASURED FIRST, then built: a real scaffold of the dev kit at preset `team` left twelve
    directories in `.claude/skills/` (eleven kit skills plus a dropped-in design system) and nine in
    `.agents/skills/` -- exactly the installed roles, because the mirror walked the ROLE list and a
    reference skill belongs to no role (constitution §1a). TSK-0104 changed the subject to the
    skills DIRECTORY (`native_skill_sources`), which is why those texts now say Codex gets a native
    copy. This is the basis of that sentence, pinned instead of the sentence.

    HELD AT BOTH ENDS, because an exemption with only one end is how the previous cut rotted: every
    producing site must walk the one derivation, AND the removal inventory must still contain a
    mirror site -- if `legacy_owned_outputs` stopped composing that path, the exemption below would
    be excusing nothing while still excusing anything written into that function.
    """
    sites = _mirror_loop_iterators()
    producers = [site for site in sites if site[1] != _MIRROR_REMOVAL]
    removal = [site for site in sites if site[1] == _MIRROR_REMOVAL]
    assert len(producers) >= 2, (
        "only %d site outside `%s` composes `%s` in gen_provider_artifacts.py -- the mirror moved "
        "and the Codex claims in the kit texts rest on nothing"
        % (len(producers), _MIRROR_REMOVAL, _MIRROR_TEMPLATE))
    strangers = [site for site in producers if site[2] != _MIRROR_DERIVATION]
    assert not strangers, (
        "these sites decide what a project's Codex mirror gets and they do not walk `%s`: %s -- "
        "either they are a second answer to 'which skills end up there', or the derivation was "
        "renamed and the three texts promising a native copy have to be re-measured"
        % (_MIRROR_DERIVATION, strangers))
    assert removal, (
        "`%s` no longer composes `%s`, so the exemption above now excuses a function that does "
        "nothing with the mirror -- and any future site written into it" % (_MIRROR_REMOVAL,
                                                                           _MIRROR_TEMPLATE))


def test_a_skill_file_that_is_not_utf8_never_reaches_the_dispatch(tmp_path):
    """A file the reader cannot DECODE is one it says nothing about — not one that kills the run.

    THE MEASURED CHAIN, and it starts at a place this round itself created: `FR-0045` invites the
    user to unpack their own design-system export into the installed skills directory, and
    `declarations` walks every directory there. A `SKILL.md` saved as ANSI by a Windows editor
    raised `UnicodeDecodeError` out of `declarations`, through `for_task`, out of `create_lease` —
    every dispatch in that project dead with a stacktrace over a file nobody in the apparatus
    wrote. The reader's own docstring promised the opposite ("withholding a hint, never granting a
    permission") while catching `OSError` alone.

    Driven at both levels: the reader, and a real lease composed over that directory, because the
    docstring's promise is about what reaches the DISPATCH.
    """
    import shutil

    skills = tmp_path / "skills"
    (skills / "acme-design").mkdir(parents=True)
    # cp1252 -- what a Windows editor writes when somebody saves as "ANSI"
    (skills / "acme-design" / "SKILL.md").write_bytes(
        "---\nname: acme-design\ndescription: Grüße\n---\nbody\n".encode("cp1252"))
    (skills / "good").mkdir(parents=True)
    (skills / "good" / "SKILL.md").write_text(
        "---\nname: good\nreference_for:\n  roles: [frontend-developer]\n"
        "  task_types: [ui]\n---\nbody\n", encoding="utf-8")
    assert sorted(references.declarations(str(skills))) == ["good"]
    assert references.for_task(str(skills), "frontend-developer", "ui") == ["good"]

    root = tmp_path / "project_memory"
    root.mkdir()
    shutil.copytree(str(skills), references.skills_dir(str(tmp_path)))
    state = ProjectState(str(root))
    pr = state.capture("PR", dict(PR_FIELDS))
    approve(state, pr["id"], "scope")
    task = dispatch.create_task(state, dict(TSK_FIELDS, product_requirement=pr["id"]))
    drive_task_to(state, task["id"], "READY")
    lease = dispatch.create_lease(state, task["id"])
    assert lease[dispatch.REFERENCES_KEY] == ["good"], lease


def test_the_declaration_reader_survives_the_shapes_a_kit_can_have(tmp_path):
    """Five shapes of the DERIVATION, none of which is in the shipped tree and each of which would
    empty or crash it tomorrow: a skills directory that does not exist, a SKILL.md with no
    frontmatter, a `reference_for` that is not a mapping, one that is empty, and the single-string
    spelling of a list.

    The empty declaration is the one with a wrong-looking alternative: dropping it from
    `declarations` would look tidier and would hide it from
    `test_every_shipped_reference_skill_can_be_named_by_some_task`, which is the one test whose
    whole job is to find it.
    """
    skills = tmp_path / "skills"
    for name, text in (
            ("plain", "no frontmatter here\n"),
            ("notmap", "---\nname: notmap\nreference_for: yes\n---\nbody\n"),
            ("empty", "---\nname: empty\nreference_for: {}\n---\nbody\n"),
            ("onestr", "---\nname: onestr\nreference_for:\n  roles: product-designer\n"
                       "  task_types: ui\n---\nbody\n"),
            ("full", "---\nname: full\nreference_for:\n  roles: [a, b]\n"
                     "  task_types: [ui]\n---\nbody\n")):
        (skills / name).mkdir(parents=True)
        (skills / name / "SKILL.md").write_text(text, encoding="utf-8")
    assert references.declarations(str(tmp_path / "nothing-here")) == {}
    assert references.for_task(str(tmp_path / "nothing-here"), "a", "ui") == []
    found = references.declarations(str(skills))
    assert sorted(found) == ["empty", "full", "notmap", "onestr"], sorted(found)
    assert found["notmap"][references.ROLES_KEY] == set()
    assert found["empty"][references.TASK_TYPES_KEY] == set()
    assert found["onestr"][references.ROLES_KEY] == {"product-designer"}
    assert references.for_task(str(skills), "product-designer", "ui") == ["onestr"]
    assert references.for_task(str(skills), "a", "ui") == ["full"]
    # BOTH axes, not either: the role matches and the type does not, so nothing is named.
    assert references.for_task(str(skills), "a", "docs") == []
    assert references.resolve(str(skills), "full")
    assert references.resolve(str(skills), "ghost") is None


# ================================================== 3. the derivation reaches the work order
PR_FIELDS = {
    "title": "Checkout flow", "class": "normal", "problem": "no checkout",
    "goal": "working checkout", "acceptance_criteria": [{"id": "AC-1", "text": "order completes"}],
    "invariants": [], "out_of_scope": [], "priority": "high",
}
TSK_FIELDS = {
    "derives_from": "PR-0001", "type": "ui", "assigned_role": "frontend-developer",
    "acceptance_refs": ["AC-1"], "required_inputs": [], "allowed_scope": ["src/"],
    "forbidden_scope": ["secrets/"], "expected_outputs": ["src/x.py"], "dependencies": [],
}


def _project(tmp_path, task_fields):
    """A scaffolded-enough project: the dev kit's skills where the installer puts them, one task."""
    import shutil

    root = tmp_path / "project_memory"
    root.mkdir()
    shutil.copytree(os.path.join(TEAM_KITS, "dev-team", "skills"),
                    references.skills_dir(str(tmp_path)))
    state = ProjectState(str(root))
    pr = state.capture("PR", dict(PR_FIELDS))
    approve(state, pr["id"], "scope")
    task = dispatch.create_task(state, dict(task_fields, product_requirement=pr["id"]))
    drive_task_to(state, task["id"], "READY")
    return state, task


def test_the_dispatch_header_names_the_reference_skills_the_task_derives(tmp_path):
    """The wiring, driven end to end: a real lease over a real installed skill tree.

    THE HEADER IS WHERE IT HAS TO LAND, because that is the one part of the spawn prompt that
    reaches the specialist verbatim — the same reason `hand_back` and `checkpoint` ride there. And
    it has to grant nothing: `parse_header` names the three keys the dispatch gate decides on, and
    this is not one of them, which is asserted below rather than argued.
    """
    state, task = _project(tmp_path, TSK_FIELDS)
    lease = dispatch.create_lease(state, task["id"])
    assert lease[dispatch.REFERENCES_KEY] == ["frontend-design", "webapp-testing"], lease
    header = dispatch.dispatch_header(lease)
    body = json.loads(header[len(dispatch.HEADER_PREFIX):])
    assert body[dispatch.REFERENCES_KEY] == ["frontend-design", "webapp-testing"], body
    parsed = dispatch.parse_header("objective: x\n" + header)
    assert dispatch.REFERENCES_KEY not in parsed, (
        "the reference list reached the gate's decision surface — it is a pointer, not a grant")


def test_a_task_of_another_type_gets_a_different_order(tmp_path):
    """The point of deriving from the TASK, measured as a difference rather than asserted.

    Same role, same project, `docs` instead of `ui`: no reference at all, and therefore no key in
    the header. If both orders named the same skills the derivation would be decoration.
    """
    state, task = _project(tmp_path, dict(TSK_FIELDS, type="docs"))
    lease = dispatch.create_lease(state, task["id"])
    assert dispatch.REFERENCES_KEY not in lease, lease
    assert dispatch.REFERENCES_KEY not in dispatch.dispatch_header(lease)


def test_a_project_without_installed_skills_dispatches_silently(tmp_path):
    """A dispatch composed where no skill directory exists says nothing rather than failing.

    The same fail-quiet direction `hand_back_path` takes for an unreadable definition: a POINTER
    may withhold a hint, never block a dispatch. Measured because the reverse — an exception out of
    `create_lease` — would take the whole apparatus down over a cosmetic feature.
    """
    root = tmp_path / "project_memory"
    root.mkdir()
    state = ProjectState(str(root))
    pr = state.capture("PR", dict(PR_FIELDS))
    approve(state, pr["id"], "scope")
    task = dispatch.create_task(state, dict(TSK_FIELDS, product_requirement=pr["id"]))
    drive_task_to(state, task["id"], "READY")
    lease = dispatch.create_lease(state, task["id"])
    assert dispatch.REFERENCES_KEY not in lease, lease


# ================================================== 4. what vendoring somebody else's file owes
LICENCE_FILE = "LICENSE.txt"
NOTICES = os.path.join(ROOT, "NOTICES.md")
_MARK = re.compile(r"\[(MOD-\d+)\]")


def _vendored():
    """(kit dir, name, SKILL.md) for every VENDORED skill — the property, not a list of two names.

    A vendored skill is one whose directory carries its own licence copy. Nothing else in a kit's
    skills tree does, because everything else in it is this project's own text, so the file that
    discharges the licence duty is also the marker that the duty applies.
    """
    for kit_dir in _kit_dirs():
        for name, path in sorted(_skills(kit_dir).items()):
            if os.path.isfile(os.path.join(os.path.dirname(path), LICENCE_FILE)):
                yield kit_dir, name, path


def test_every_vendored_skill_is_listed_here_and_every_listing_resolves():
    """`NOTICES.md` and the tree, held to each other in both directions.

    A table that lists a skill the tree no longer has is an attribution for nothing; a vendored
    skill the table does not list is the omission the table exists to prevent. Both are one
    comparison, and the subject on the tree side is derived from the licence copy rather than typed
    out here.
    """
    with io.open(NOTICES, encoding="utf-8") as handle:
        notices = handle.read()
    found = list(_vendored())
    assert found, "no vendored skill found — this whole section is vacuous"
    for kit_dir, name, path in found:
        relative = os.path.relpath(os.path.dirname(path), ROOT).replace(os.sep, "/")
        assert relative in notices, (
            "%s is vendored (it carries a %s) and NOTICES.md does not name %s"
            % (name, LICENCE_FILE, relative))
    for hit in re.finditer(r"`(team-kits/[a-z-]+/skills/[a-z0-9-]+)/`", notices):
        directory = os.path.join(ROOT, hit.group(1).replace("/", os.sep))
        assert os.path.isfile(os.path.join(directory, "SKILL.md")), hit.group(1)
        assert os.path.isfile(os.path.join(directory, LICENCE_FILE)), (
            "NOTICES.md lists %s and its licence copy is gone — the copy is what discharges the "
            "duty in an installed project, the table only records it" % hit.group(1))


def test_every_vendored_skill_carries_the_provenance_a_later_round_can_re_fetch():
    """The frontmatter that makes the upstream comparison possible at all.

    No test here reaches the network, so this is the whole of what the suite can hold: the source,
    the commit and the blob hash the adaptation started from, plus the `modified` flag Apache-2.0
    §4(b) is about. Without them "unchanged except where marked" is a sentence nobody can check.
    """
    for _kit_dir, name, path in _vendored():
        front, _body = _frontmatter(path)
        for key in ("source", "source_commit", "source_blob_sha1", "license", "modified"):
            assert front.get(key), "%s: SKILL.md frontmatter carries no `%s:`" % (name, key)
        assert re.fullmatch(r"[0-9a-f]{40}", str(front["source_blob_sha1"])), name
        assert re.fullmatch(r"[0-9a-f]{40}", str(front["source_commit"])), name
        assert front["modified"] is True, name


def test_every_modification_mark_is_listed_and_every_listed_one_is_marked():
    """Apache-2.0 §4(b) as a property instead of as a promise: the marks and the list are one set.

    A body mark with no entry in the "Modifications" section is a change whose reason nobody wrote
    down; an entry with no mark in the body is a change that was reverted, moved or never made and
    left a claim behind. Both are the rot this file is here to make visible.

    WHAT IT CANNOT SEE, and it is the larger half: an EDIT that carries no mark at all. Only the
    upstream bytes could catch that, and they are one network call away from a suite that makes
    none — which is why the frontmatter above records exactly what to re-fetch.
    """
    for _kit_dir, name, path in _vendored():
        _front, body = _frontmatter(path)
        head, _sep, listing = body.partition("\n## Modifications")
        assert listing, "%s: no `## Modifications` section — nothing states what was changed" % name
        marked = set(_MARK.findall(head))
        listed = set(_MARK.findall(listing))
        assert marked, "%s: the body carries no [MOD-n] mark at all" % name
        assert marked == listed, (
            "%s: marked in the body %s, listed under Modifications %s — the two have to be one set"
            % (name, sorted(marked), sorted(listed)))


def test_no_shipped_skill_claims_to_be_loaded_at_session_start():
    """The preloading claim, asked of EVERY shipped skill and not only of the reachable ones.

    `test_context_budget.py::test_no_skill_a_session_can_reach_claims_to_be_preloaded` derives its
    subject from the agents' `skills:` frontmatter, which is exactly the set a reference skill is
    NOT in — so the day this kit shipped skills nobody names, that guard stopped covering them.
    The predicate is the running one from that file rather than a second copy of it.
    """
    from test_context_budget import _claim_survives

    for kit_dir in _kit_dirs():
        for name, path in sorted(_skills(kit_dir).items()):
            with io.open(path, encoding="utf-8") as handle:
                text = handle.read()
            assert not _claim_survives(text), (
                "%s/%s claims to be loaded at session start, and a session bound to a role was "
                "measured NOT to receive a skill (tools/provider_observations.json)"
                % (os.path.basename(kit_dir), name))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))


# -- delivery: the installer has to put a reference skill on disk (H83) ---------------------------

@pytest.mark.parametrize("twin", ("powershell", "bash"))
def test_a_reference_skill_reaches_every_preset_and_not_only_team(tmp_path, twin):
    """The half of `FR-0071` that is not a derivation: the file has to BE there.

    THE MEASURED FAILURE (`H83`), against real installer runs into a throwaway HOME: the skill loop
    of both twins filtered skill DIRECTORIES through the preset's ROLE list. Preset `team` (`all`
    internally, so the filter never fires) landed all eleven dev skills including both reference
    ones; preset `solo` landed five and neither of them. It failed as SILENT ABSENCE rather than as
    a dangling pointer, because `kernel.references` reads the PROJECT's own `.claude/skills` -- a
    work order in such a project simply names nothing, and no one is told a capability is missing.

    WHAT IS ASSERTED IS THE PROPERTY AND BOTH OF ITS ENDS: every skill the kit ships for no role of
    its own arrives at every preset, AND a role skill outside the preset still does not -- without
    the second half this would be satisfied by an installer that copies everything, which is the
    subtractive behaviour `test_scaffold_sh_preset_and_provider_e2e` exists to hold.

    Driven through the REAL installer in both twins, because the cut is written twice and a proof
    against one spelling says nothing about the other.

    EACH PRESET GETS ITS OWN FRESH PROJECT, and that is not tidiness -- it is what makes this test
    able to fail at all. The first cut installed `team`, then `duo`, then `solo` into ONE project,
    and the mutation that restores the old role filter stayed GREEN: the subtractive removal walks
    the ROLE manifest (`.claude/team_kit_roles.txt`), so the reference skills the `team` run had
    already landed were never taken away again, and the later runs found them lying there.
    """
    pytest.importorskip("yaml")
    from test_kitupdate import _run_installer, _staging  # the twin harness, not a second one

    home, staging = _staging(tmp_path)
    kit_dir = os.path.join(str(staging), "dev-team")
    shipped = set(_skills(kit_dir))
    shared = set(_reference_skills(kit_dir))
    assert shared, "dev-team ships no reference skill — this test would be vacuous"

    template = os.path.join(kit_dir, "templates", "project_memory", "project_config.yaml")
    with io.open(template, encoding="utf-8") as handle:
        config = handle.read()

    for preset in ("team", "duo", "solo"):
        repo = tmp_path / ("project-" + preset)
        config_path = repo / "project_memory" / "project_config.yaml"
        os.makedirs(os.path.dirname(str(config_path)), exist_ok=True)
        with io.open(str(config_path), "w", encoding="utf-8", newline="\n") as handle:
            handle.write(config.replace('name: ""', 'name: "Probe"').replace("stacks: [TODO]",
                                                                            "stacks: [python]"))
        result = _run_installer(staging, repo, "dev-team", home, twin, *(
            ("-Preset", preset) if twin == "powershell" else (preset,)))
        assert result.returncode == 0, result.stdout + result.stderr
        landed = {name for name in os.listdir(str(repo / ".claude" / "skills"))
                  if os.path.isdir(str(repo / ".claude" / "skills" / name))}
        assert shared <= landed, (
            "preset %s (%s) landed %s — the shared reference skills %s belong to no role and "
            "therefore to every preset (H83)"
            % (preset, twin, sorted(landed), sorted(shared - landed)))
        installed_roles = {os.path.splitext(name)[0]
                           for name in os.listdir(str(repo / ".claude" / "agents"))
                           if name.endswith(".md")}
        strays = (landed - shared) - installed_roles
        assert not strays, (
            "preset %s (%s) landed the procedure skill(s) %s of roles it did not install — the cut "
            "stopped being a cut" % (preset, twin, sorted(strays)))
        if preset != "team":
            assert landed < shipped, (
                "preset %s (%s) landed every shipped skill, so this run proves nothing about the "
                "filter" % (preset, twin))
        # THE CODEX SIDE OF THE SAME DELIVERY, measured here rather than only pinned against the
        # generator's AST (`test_the_codex_mirror_is_generated_per_skill_directory`): the mirror
        # walked the ROLE list, so a reference skill was missing there as well -- the second chain
        # in `H83`. The template this project is built from ships `providers: [claude, codex]`, so
        # the mirror is really produced by this run.
        mirror = str(repo / ".agents" / "skills")
        mirrored = {name for name in os.listdir(mirror)
                    if os.path.isfile(os.path.join(mirror, name, "SKILL.md"))}
        assert mirrored == landed, (
            "preset %s (%s): the Codex mirror carries %s while the project carries %s — the two "
            "providers see different skills" % (preset, twin, sorted(mirrored), sorted(landed)))

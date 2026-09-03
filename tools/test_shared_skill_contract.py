"""A SHARED skill's contract, held at both ends: its declaration resolves, and its copies are one file.

THE OCCASION is `humanizer` (FR-0072), the first reference skill shipped by all three kits, and the
two questions it raised that `tools/test_reference_skills.py` does not answer:

  * A DEAD ENTRY in the declaration. `test_every_shipped_reference_skill_can_be_named_by_some_task`
    asks whether SOME (role, task type) of a kit reaches the skill, so a `reference_for` that names
    one real role beside a role nobody ships -- a capability that does not exist yet, a role that was
    renamed -- stays green: the real role carries the skill and the dead name is never read. The
    house rule for an unavoidable list is a tripwire at BOTH ends, and this file is the "dead" end:
    every role a declaration names is shipped by a kit that ships the skill, and every task type is
    in the kernel's closed vocabulary. (The "not needed" end -- a name that never fires -- is the
    reachability test above.)

  * MIRRORING. `test_hooks._assert_mirrored` holds the hooks and the project scripts byte-identical
    across kits, and nothing held the skills: a skill directory that ships in two kits could drift
    by one byte and both suites stay green. Same shape of exception map, applied to every file of
    every reference skill directory -- and one half more than the hooks rule has: the SET of files
    is held too, against the kits that ship the skill, so a file one copy carries alone is a
    defect and not an unpaired entry the rule skips (`_shipping_kits` says why that half exists).

Both are read off the part that RUNS: the declaration through `kernel.references.declarations` (the
reader the dispatch uses), the roles off the agent files, the vocabulary off `backlog_types`.
"""
import io
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEAM_KITS = os.path.join(ROOT, "team-kits")
sys.path.insert(0, TEAM_KITS)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kernel import backlog_types, references  # noqa: E402
from test_reference_skills import _kit_dirs, _reference_skills, _roles  # noqa: E402 -- one derivation

pytest.importorskip("yaml")

# A file inside a skill directory that is ALLOWED TO DIFFER between kits, keyed by
# `<skill>/<relative path>`, with the reason. Empty on purpose: today every skill two kits ship is
# meant to be one directory. The same shape and the same both-ends rule as
# `test_hooks.KIT_SPECIFIC_HOOKS` -- an entry whose copies have stopped differing is an exception
# nobody needs and fails below. An entry never allows a file to be MISSING from a kit that ships
# the skill; that is a different defect and `_assert_one_directory` says so.
KIT_SPECIFIC_SKILL_FILES = {}


# ================================================== 1. the declaration, dead-entry end
def _declared_everywhere(kit_dirs):
    """{skill: {kit: declaration}} for every reference skill any of `kit_dirs` ships."""
    out = {}
    for kit_dir in kit_dirs:
        for name, rule in references.declarations(os.path.join(kit_dir, "skills")).items():
            out.setdefault(name, {})[os.path.basename(kit_dir)] = rule
    return out


def _dead_roles(name, per_kit, roles_by_kit):
    """The roles the declaration names that NO kit shipping this skill ships -- the dead entries.

    "A kit shipping this skill" and not "every kit": a shared skill names the roles of three kits
    at once, and the office editor is not dead because the dev kit lacks it. A role is dead when
    the union over the shipping kits does not carry it either.
    """
    shipped = set()
    for kit in per_kit:
        shipped |= set(roles_by_kit.get(kit, ()))
    declared = set()
    for rule in per_kit.values():
        declared |= rule[references.ROLES_KEY]
    return sorted(declared - shipped)


def _foreign_types(per_kit):
    """The task types the declaration names outside `backlog_types.TASK_TYPES`."""
    declared = set()
    for rule in per_kit.values():
        declared |= rule[references.TASK_TYPES_KEY]
    return sorted(declared - set(backlog_types.TASK_TYPES))


def test_every_role_a_reference_skill_names_is_shipped_by_a_kit_that_ships_the_skill():
    """A declaration naming a role nobody ships carries an entry nothing can ever read.

    Why the existing reachability test cannot see it: it is satisfied by ONE live pair per kit, so
    the dead name hides behind the live one. Measured red on a copy outside the repo with the
    `humanizer` declaration widened by a role no kit ships (`correspondence`, the FR-0033 capability
    that does not exist yet) -- this test red, the reachability test green in the same run.
    """
    kit_dirs = _kit_dirs()
    roles_by_kit = {os.path.basename(kit_dir): set(_roles(kit_dir)) for kit_dir in kit_dirs}
    judged = 0
    for name, per_kit in sorted(_declared_everywhere(kit_dirs).items()):
        judged += 1
        dead = _dead_roles(name, per_kit, roles_by_kit)
        assert not dead, (
            "%s (shipped by %s) declares `reference_for.roles` %s and none of those kits ships an "
            "agent by that name -- a dead entry, or a role written before it exists. Name only "
            "roles the shipping kits carry; a capability that does not exist yet is a seam item, "
            "not a declaration." % (name, ", ".join(sorted(per_kit)), dead))
    assert judged >= 3, "only %d reference skills read -- the derivation stopped matching" % judged


def test_every_task_type_a_reference_skill_names_is_in_the_kernel_vocabulary():
    """The other axis: a type outside the closed vocabulary is one no task can ever carry.

    Same blind spot in the reachability test, same reason -- a live type beside a foreign one
    keeps it green. Measured red on the copy with `copy` added to the humanizer's `task_types`.
    """
    kit_dirs = _kit_dirs()
    judged = 0
    for name, per_kit in sorted(_declared_everywhere(kit_dirs).items()):
        judged += 1
        foreign = _foreign_types(per_kit)
        assert not foreign, (
            "%s declares `reference_for.task_types` %s, which kernel.backlog_types.TASK_TYPES does "
            "not contain -- no work order can be typed with it, so the entry never fires."
            % (name, foreign))
    assert judged >= 3, "only %d reference skills read -- the derivation stopped matching" % judged


def _kits_owed(per_kit, roles_by_kit):
    """The kits a declaration OBLIGES to ship the skill: every kit that ships a role it names.

    The declaration is the only statement of where a shared skill belongs, and it makes it by
    naming roles -- a skill that names the office editor and is missing from the office kit
    reaches that editor nowhere. This is the presence rule one level above `_assert_one_directory`:
    that one holds the FILES against the kits that ship the directory, this one holds the
    DIRECTORY against the kits the declaration speaks to, so a whole copy vanishing from one kit is
    a finding here and not a silent shrinking of the shipping set the file rule reads.
    """
    declared = set()
    for rule in per_kit.values():
        declared |= rule[references.ROLES_KEY]
    return sorted(kit for kit, roles in roles_by_kit.items() if declared & set(roles))


def test_a_reference_skill_ships_in_every_kit_that_ships_a_role_it_names():
    """A copy that vanishes from one kit leaves the mirror rule silently: the file rule only reads
    the kits that still ship the directory. Measured on a copy outside the repo with
    `office-team/skills/humanizer/` deleted: this test red naming office-team; the dead-role test
    above red as well, but only because the office roles happen to be office-only -- a skill
    naming roles every kit ships would vanish from one kit with that test green, which is why this
    one exists. The OTHER way a copy leaves the mirror rule, a role file taking the skill into
    ownership (`office-team/agents/humanizer.md` with `skills: [humanizer]`), is held by
    `test_reference_skills.test_every_shipped_skill_is_either_a_role_procedure_or_a_declared_reference`
    (measured red on the same copy while the mirror test stayed green).
    """
    kit_dirs = _kit_dirs()
    roles_by_kit = {os.path.basename(kit_dir): set(_roles(kit_dir)) for kit_dir in kit_dirs}
    judged = 0
    for name, per_kit in sorted(_declared_everywhere(kit_dirs).items()):
        judged += 1
        missing = sorted(set(_kits_owed(per_kit, roles_by_kit)) - set(per_kit))
        assert not missing, (
            "%s names roles that %s ship, and %s ship no skills/%s/ -- a shared skill is shipped by "
            "every kit whose roles it names; restore the copy (byte-identical) or drop those roles "
            "from the declaration" % (name, ", ".join(missing), ", ".join(missing), name))
    assert judged >= 3, "only %d reference skills read -- the derivation stopped matching" % judged

def test_the_dead_entry_readers_see_what_they_are_for(tmp_path):
    """The floor under the two tests above: both readers, driven over a probe kit, report the
    dead role and the foreign type, and report nothing for a declaration that is whole."""
    kit = tmp_path / "probe-team"
    (kit / "agents").mkdir(parents=True)
    (kit / "agents" / "writer.md").write_text("---\nname: writer\nskills: [writer]\n---\n",
                                             encoding="utf-8")
    (kit / "skills" / "shared").mkdir(parents=True)
    (kit / "skills" / "shared" / "SKILL.md").write_text(
        "---\nname: shared\nreference_for:\n  roles: [writer, ghost]\n"
        "  task_types: [docs, copy]\n---\nbody\n", encoding="utf-8")
    declared = _declared_everywhere([str(kit)])
    assert sorted(declared) == ["shared"], declared
    roles_by_kit = {"probe-team": set(_roles(str(kit)))}
    assert _dead_roles("shared", declared["shared"], roles_by_kit) == ["ghost"]
    assert _foreign_types(declared["shared"]) == ["copy"]
    # ...and a second kit shipping `writer` without the skill is a kit the declaration obliges
    two_kits = dict(roles_by_kit, **{"other-team": {"writer"}})
    assert _kits_owed(declared["shared"], two_kits) == ["other-team", "probe-team"]
    # ...and a whole declaration reports nothing on either axis
    (kit / "skills" / "shared" / "SKILL.md").write_text(
        "---\nname: shared\nreference_for:\n  roles: [writer]\n  task_types: [docs]\n---\nbody\n",
        encoding="utf-8")
    declared = _declared_everywhere([str(kit)])
    assert _dead_roles("shared", declared["shared"], roles_by_kit) == []
    assert _foreign_types(declared["shared"]) == []


# ================================================== 2. a skill several kits ship is ONE directory
def _shipping_kits(kit_dirs):
    """{skill: {kit}} -- which kits ship each REFERENCE skill, by the directory's NAME.

    This is the set every file of the skill is held against below, and it is derived from the
    skill directories, not from the files inside them: a table keyed by file alone cannot see a
    file that one kit's copy carries and the others lack, because that file has one entry and
    nothing to be compared with. That was the first cut of this rule (`if len(copies) < 2:
    continue`), and it stayed green with an `extra.md` planted in one copy of `humanizer` --
    `test_the_mirror_rule_fails_on_a_drift_on_a_lone_file_and_on_an_idle_exception` holds the
    case now.

    REFERENCE skills only, by the property that defines them (no role's frontmatter names it --
    `test_reference_skills._reference_skills`), and not every skill two kits happen to ship: a
    role's procedure skill is that kit's text about that kit's role, and `project-auditor`,
    `project-manager` and `research-engineer` differ between kits by construction. Measured before
    this cut: read over all skills, the rule reported those three and nothing else.
    """
    out = {}
    for kit_dir in kit_dirs:
        for name in _reference_skills(kit_dir):
            out.setdefault(name, set()).add(os.path.basename(kit_dir))
    return out


def _skill_files_by_path(kit_dirs):
    """{"<skill>/<relative file>": {kit: bytes}} over every file of every REFERENCE skill directory.

    EVERY file of the directory, not `SKILL.md` alone: a reference skill may ship a `references/`
    folder or a licence copy beside its entry point, and a mirror rule that read one file would
    hold the entry point while the folder drifted -- the suffix-filter hole
    `test_hooks._kit_files_by_name` records. Walked with `os.walk`, not `glob("**/*")`, because a
    glob's `*` skips dotfiles while the installer's `cp -R` ships them; measured red on a copy
    outside the repo with a `.office-only` planted in one copy of `humanizer` (the glob cut stayed
    green on it).
    """
    out = {}
    for kit_dir in kit_dirs:
        kit = os.path.basename(kit_dir)
        skills = os.path.join(kit_dir, "skills")
        for name in sorted(_reference_skills(kit_dir)):
            for folder, dirs, files in os.walk(os.path.join(skills, name)):
                dirs[:] = sorted(d for d in dirs if d != "__pycache__")
                for filename in sorted(files):
                    path = os.path.join(folder, filename)
                    key = os.path.relpath(path, skills).replace(os.sep, "/")
                    with io.open(path, "rb") as handle:
                        out.setdefault(key, {})[kit] = handle.read()
    return out


def _assert_one_directory(by_path, shipping, exceptions):
    """The mirror rule over one {path: {kit: bytes}} table, against {skill: {kit}}.

    Two halves, in this order. PRESENCE: every file of a skill exists in exactly the kits that
    ship the skill -- a file one copy carries alone is not a mirror with one side, it is a
    directory that has stopped being one, and no entry in the exception map covers that (the map
    says a file may DIFFER, never that it may be missing). The map has the SHAPE of
    `test_hooks.KIT_SPECIFIC_HOOKS` and not its rule: the hooks rule has no presence half at all
    (`format_on_write.py` ships in two kits and is nobody's finding there, because which hooks a
    kit ships is decided by its registration -- H120 in docs/POST_V2_WISHLIST.md). CONTENT: the copies are
    byte-identical unless the map names the file with a reason, and a listed file whose copies
    have stopped differing -- or that fewer than two kits ship at all -- is an exception nobody
    needs and fails as well.
    """
    for key, copies in sorted(by_path.items()):
        skill = key.split("/", 1)[0]
        assert set(copies) == shipping[skill], (
            "skills/%s exists in %s, but `%s` is shipped by %s -- a shared skill is ONE directory "
            "in every kit that ships it; mirror the file into every copy or remove it from every "
            "copy (an entry in KIT_SPECIFIC_SKILL_FILES allows a file to differ, not to be "
            "missing)" % (key, ", ".join(sorted(copies)), skill, ", ".join(sorted(shipping[skill]))))
        if key in exceptions:
            continue
        assert len(set(copies.values())) == 1, (
            "skills/%s exists in %s and the copies are NOT identical -- re-mirror it (copy, then "
            "compare hashes), or add it to KIT_SPECIFIC_SKILL_FILES with the reason"
            % (key, ", ".join(sorted(copies))))
    for key in sorted(exceptions):
        copies = by_path.get(key, {})
        assert len(copies) >= 2 and len(set(copies.values())) > 1, (
            "skills/%s is listed as kit-specific and has nothing to differ from (%d cop%s, all "
            "identical) -- drop the exception so the file stays pinned"
            % (key, len(copies), "y" if len(copies) == 1 else "ies"))


def test_a_skill_shipped_by_several_kits_is_one_directory_in_all_of_them():
    """Same files, same bytes, in every kit that ships the skill, unless the map says why not.

    Measured red on a copy outside the repo twice: with one byte changed in the office kit's
    `humanizer/SKILL.md` (content half), and with a `references/extra.md` planted in the office
    copy alone (presence half -- the first cut of this test stayed green on that, see
    `_shipping_kits`). The reference-skill suite stayed green on both copies once they were
    STAMPED (`bump_kit_version.py`; unstamped, its two installer tests go red on any edited byte
    through the VERSION hash guard, which is not a mirror rule) -- that is the gap this test
    exists for.
    """
    kit_dirs = _kit_dirs()
    shipping = _shipping_kits(kit_dirs)
    assert any(len(kits) >= 2 for kits in shipping.values()), (
        "no reference skill is shipped by more than one kit -- this test would be vacuous")
    _assert_one_directory(_skill_files_by_path(kit_dirs), shipping, KIT_SPECIFIC_SKILL_FILES)


def test_the_mirror_rule_fails_on_a_drift_on_a_lone_file_and_on_an_idle_exception():
    """The floor under the mirror test, driven over hand-built tables at every end: a drifted
    copy with no entry fails, an identical pair WITH an entry fails, a drifted pair with an entry
    passes; a file one shipping kit carries alone fails whether listed or not; and an entry for a
    file only one kit ships is idle and fails."""
    two = {"alpha": {"dev-team", "office-team"}}
    same = {"alpha/SKILL.md": {"dev-team": b"one", "office-team": b"one"}}
    drift = {"alpha/SKILL.md": {"dev-team": b"one", "office-team": b"two"}}
    _assert_one_directory(same, two, {})
    with pytest.raises(AssertionError, match="NOT identical"):
        _assert_one_directory(drift, two, {})
    with pytest.raises(AssertionError, match="nothing to differ from"):
        _assert_one_directory(same, two, {"alpha/SKILL.md": "a reason"})
    _assert_one_directory(drift, two, {"alpha/SKILL.md": "a reason"})
    # a file only ONE of the two shipping kits carries: the lone-file case, listed or not
    lone = dict(same, **{"alpha/references/extra.md": {"office-team": b"only here"}})
    with pytest.raises(AssertionError, match="ONE directory"):
        _assert_one_directory(lone, two, {})
    with pytest.raises(AssertionError, match="ONE directory"):
        _assert_one_directory(lone, two, {"alpha/references/extra.md": "office only"})
    # a skill one kit ships is whole by itself, and an exception on it has nothing to differ from
    one = {"solo": {"dev-team"}}
    _assert_one_directory({"solo/SKILL.md": {"dev-team": b"one"}}, one, {})
    with pytest.raises(AssertionError, match="nothing to differ from"):
        _assert_one_directory({"solo/SKILL.md": {"dev-team": b"one"}}, one, {"solo/SKILL.md": "idle"})


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))

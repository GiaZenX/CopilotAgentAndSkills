"""The design-system contract (`FR-0045`): what a dropped-in export must carry to be usable.

WHERE THE SCHEMA COMES FROM. Not from a guess and not from a community description — the user
delivered a real Claude Design export (184 entries, ~2 MiB) and it was inspected read-only twice,
2026-08-23 and again in the round that built this. The widely repeated triple (a `design.html`,
a `screenshots/` folder, a `design-notes.md`) does not exist. What an export IS, is a skill, and
its spine is three files with three jobs: `SKILL.md` as the entry point a provider registers,
`readme.md` as the human half, `_ds_manifest.json` as the machine index. Measured on that export:
33 components, 309 tokens, 6 themes, 14 fonts, 30 cards, and 105 path-shaped values in the manifest
of which every single one resolved inside the bundle.

WHY THE TESTS BUILD A MINIMAL BUNDLE INSTEAD OF SHIPPING THE REAL ONE. The export is the user's own
design system, not this project's, and vendoring it would be taking his property into a kit that
gets copied into other people's repositories. So the SCHEMA is frozen here and the bundle stays
where it is. What that costs is stated rather than hidden: these tests prove the check's behaviour
on the shape, not that the shape still matches next year's exporter. The round's own measurement
against the real archive is in the protocol under `project_memory/staging/TSK-0100/`.
"""
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "team-kits", "dev-team", "templates", "repo", "scripts",
                      "kit_design_system_check.py")

sys.path.insert(0, os.path.join(ROOT, "tools"))
from conftest import load_kit_module  # noqa: E402 -- the suite's one loader for shipped scripts

check = load_kit_module("kit_design_system_check", SCRIPT)


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def bundle(root, name="acme-design"):
    """A minimal export that satisfies the whole spine — the base every mutation below removes from.

    Minimal on purpose: everything it carries is something the check demands, so a mutation that
    removes one part isolates one finding. The manifest names one real file, which is what makes
    the "every path the index names exists" property testable at all.
    """
    directory = os.path.join(root, name)
    _write(os.path.join(directory, "SKILL.md"),
           "---\nname: acme-design\ndescription: the Acme design system\n"
           "user-invocable: true\n---\nRead readme.md.\n")
    _write(os.path.join(directory, "readme.md"), "# Acme\n\nBrand voice, provenance, licensing.\n")
    _write(os.path.join(directory, "tokens", "colors.css"), ":root { --bg: #101010; }\n")
    _write(os.path.join(directory, "components", "core", "Badge.jsx"), "export const Badge = 1;\n")
    _write(os.path.join(directory, "_ds_manifest.json"), json.dumps({
        "namespace": "AcmeDesignSystem_ab12",
        "source": "spa",
        "globalCssPaths": ["tokens/colors.css"],
        "tokens": [{"name": "--bg", "value": "#101010", "kind": "color",
                    "definedIn": "tokens/colors.css"}],
        "components": [{"name": "Badge", "sourcePath": "components/core/Badge.jsx"}],
        "themes": [], "templates": [], "startingPoints": [],
    }, indent=2))
    return directory


def run(target=None, cwd=None):
    arguments = [sys.executable, "-B", SCRIPT] + ([target] if target else [])
    done = subprocess.run(arguments, capture_output=True, text=True, cwd=cwd or ROOT, timeout=120)
    return done.returncode, done.stdout + done.stderr


def test_the_whole_spine_is_accepted(tmp_path):
    """The base case, through the real script — without it every refusal below proves nothing."""
    code, output = run(bundle(str(tmp_path)))
    assert code == 0, output
    assert "ok " in output, output


# Each case removes ONE thing and names the word the refusal has to contain. The word is the part
# that was taken away, because a refusal that does not name it sends the user back to the whole
# archive: "something is wrong with your export" is the message this check exists to replace.
MUTATIONS = {
    "entry point gone": ("SKILL.md", "SKILL.md is missing"),
    "human half gone": ("readme.md", "readme.md is missing"),
    "machine index gone": ("_ds_manifest.json", "_ds_manifest.json is missing"),
    "a directory lost in the unpack": ("tokens", "the bundle does not contain"),
}


@pytest.mark.parametrize("case", sorted(MUTATIONS))
def test_a_bundle_missing_a_spine_part_is_refused_and_the_part_is_named(tmp_path, case):
    relative, expected = MUTATIONS[case]
    directory = bundle(str(tmp_path))
    victim = os.path.join(directory, relative)
    shutil.rmtree(victim) if os.path.isdir(victim) else os.remove(victim)
    code, output = run(directory)
    assert code == 2, output
    assert expected in output, (case, output)


def test_an_entry_point_without_frontmatter_is_refused(tmp_path):
    """A `SKILL.md` a provider cannot register is not an entry point, and the file is still there.

    The one refusal that is about CONTENT rather than presence, and the reason it is worth having:
    the name a role opens the bundle by lives in that block, so a bundle whose SKILL.md is plain
    prose is unreachable by name while looking complete in a directory listing.
    """
    directory = bundle(str(tmp_path))
    _write(os.path.join(directory, "SKILL.md"), "just prose\n")
    code, output = run(directory)
    assert code == 2, output
    assert "carries no frontmatter block" in output, output


@pytest.mark.parametrize("mutate,expected", [
    (lambda data: data.pop("namespace"), "no usable `namespace`"),
    (lambda data: data.update(tokens=[]), "lists no `tokens`"),
    (lambda data: data.pop("tokens"), "no `tokens` list"),
])
def test_a_manifest_that_cannot_be_consumed_is_refused(tmp_path, mutate, expected):
    """The two manifest fields a consumer cannot work without, each removed on its own.

    `components`, `themes`, `fonts` and the rest are deliberately NOT demanded: the real export
    ships two of its own lists empty, so "non-empty" is not a property of a valid export and a
    check that required it would refuse the very file it was frozen from.
    """
    directory = bundle(str(tmp_path))
    path = os.path.join(directory, "_ds_manifest.json")
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    mutate(data)
    _write(path, json.dumps(data))
    code, output = run(directory)
    assert code == 2, output
    assert expected in output, output


def test_a_manifest_that_is_not_readable_json_is_refused(tmp_path):
    directory = bundle(str(tmp_path))
    _write(os.path.join(directory, "_ds_manifest.json"), "{oops")
    code, output = run(directory)
    assert code == 2 and "not readable JSON" in output, output


def test_the_path_reader_reads_the_KEY_and_not_the_look_of_the_value():
    """The floor under the completeness property: what makes a value a path is the key over it.

    Both error directions are probed, because either one breaks the check silently. Reading a font
    family or a CSS shorthand as a filename refuses a perfect export for a file nobody claimed
    existed; reading nothing turns the "every named file is there" property into a no-op that
    passes over a half-unpacked archive.

    TWO OF THE VALUES BELOW EXIST ONLY TO MAKE THE PROBE DISCRIMINATE, and they are here because a
    first cut of it did not: every value it carried either had a slash AND hung under a path key, or
    had neither, so the reader "a string containing a slash is a path" produced the identical set
    and this test passed over the wrong implementation (measured in the mutation run of this round).
    The token `16px/1.5` is a real CSS shorthand with a slash and no file behind it, and
    `styles.css` is a real bundle-root asset that is a path with no slash in it.
    """
    manifest = {
        "fonts": [{"family": "Bricolage Grotesque", "cssPath": "tokens/fonts.css",
                   "files": ["assets/fonts/a.woff2"]}],
        "themes": [{"selector": '[data-accent="amber"]', "label": "Accent Amber"}],
        "components": [{"name": "Badge", "sourcePath": "components/core/Badge.jsx"}],
        "tokens": [{"name": "--type-body", "value": "16px/1.5", "kind": "font"}],
        "globalCssPaths": ["tokens/colors.css", "styles.css"],
        "namespace": "AcmeDesignSystem_ab12",
    }
    found = {value: trail for trail, value in check.path_values(manifest)}
    assert sorted(found) == ["assets/fonts/a.woff2", "components/core/Badge.jsx", "styles.css",
                             "tokens/colors.css", "tokens/fonts.css"], sorted(found)
    assert "Bricolage Grotesque" not in found and "AcmeDesignSystem_ab12" not in found
    assert '[data-accent="amber"]' not in found and "16px/1.5" not in found


def test_a_wrapper_folder_is_told_that_the_bundle_is_one_level_down(tmp_path):
    """The commonest unpack result, and the least useful refusal before this.

    "Unpack into a new folder" leaves the export one level below where the user points, and the
    three "X is missing" lines that produced described a folder whose contents were perfectly fine.
    The finding now names the child instead, and the summary line stopped prescribing a re-export —
    a wrapper is a good export pointed at from too high, not a broken one.
    """
    wrapper = tmp_path / "unpacked"
    wrapper.mkdir()
    bundle(str(wrapper))
    code, output = run(str(wrapper))
    assert code == 2, output
    assert "WRAPPER folder" in output and "acme-design" in output, output
    assert "is missing" not in output, (
        "the wrapper hint has to REPLACE the three missing-file lines, not stand beside them")


def test_the_wrapper_hint_never_hides_a_real_missing_part(tmp_path):
    """The other direction, and the one that would make the hint dangerous.

    A hint that fired whenever a manifest was absent would swallow every genuine finding of a
    bundle that simply lost its index. It is bound to a NAMED shape — no spine here, exactly one
    child that carries the index — so a folder with two such children, or one whose own manifest is
    merely missing, still gets the real answer.

    THE THIRD PROBE IS THE ONE THAT MAKES THIS TEST DISCRIMINATE, and it is here because the first
    two did not: with `wrapper_child`'s own guard deleted, both of them still passed (measured).
    Neither of them carries a directory that IS a bundle and also has a child that is one — which
    is the only shape the guard decides. Without it a perfectly good export containing a nested one
    is refused as a wrapper.
    """
    lonely = tmp_path / "lonely"
    lonely.mkdir()
    directory = bundle(str(lonely))
    os.remove(os.path.join(directory, "_ds_manifest.json"))
    code, output = run(directory)
    assert code == 2 and "_ds_manifest.json is missing" in output, output
    assert "WRAPPER" not in output, output

    two = tmp_path / "two"
    two.mkdir()
    bundle(str(two), "first-design")
    bundle(str(two), "second-design")
    code, output = run(str(two))
    assert code == 2, output
    assert "WRAPPER" not in output, (
        "two candidate children is not the shape the hint names — it must not guess one")
    assert "is missing" in output, output

    nested = tmp_path / "nested"
    nested.mkdir()
    outer = bundle(str(nested))
    bundle(outer, "vendored-subsystem")
    code, output = run(outer)
    assert code == 0, ("a complete bundle that CONTAINS one is still a bundle, not a wrapper:\n"
                       + output)
    assert "WRAPPER" not in output, output


def test_the_sweep_finds_a_bundle_where_the_installer_puts_skills(tmp_path):
    """Discovery mode, against the two skill roots the scaffold itself writes into."""
    project = tmp_path / "proj"
    (project / "project_memory").mkdir(parents=True)
    bundle(str(project / ".claude" / "skills"))
    code, output = run(cwd=str(project))
    assert code == 0, output
    assert "acme-design" in output, output


def test_a_project_with_no_design_system_is_not_a_failure(tmp_path):
    """"None dropped in" is the normal case, and saying so with rc 2 would train the reader to
    ignore this check. It also has to tell the user what to do when a bundle IS there and the sweep
    misses it — the manifest is the discovery key, so a bundle that lost it is invisible here."""
    project = tmp_path / "proj"
    (project / "project_memory").mkdir(parents=True)
    code, output = run(cwd=str(project))
    assert code == 0, output
    assert "no design system dropped in" in output, output
    assert "name its folder on the command line" in output, output


def test_naming_a_folder_whose_manifest_is_gone_says_which_part_is_gone(tmp_path):
    """The boundary of the sweep, closed in the mode where it can be closed.

    A bundle without `_ds_manifest.json` is not FOUND by discovery — that file is the key nothing
    else in a skills directory has. Named explicitly, it is refused for exactly the missing file,
    which is the answer the sweep's own message sends the reader to."""
    directory = bundle(str(tmp_path))
    os.remove(os.path.join(directory, "_ds_manifest.json"))
    project = tmp_path / "proj"
    (project / "project_memory").mkdir(parents=True)
    swept_code, swept = run(cwd=str(project))
    assert swept_code == 0 and "no design system dropped in" in swept, swept
    code, output = run(directory)
    assert code == 2 and "_ds_manifest.json is missing" in output, output


def test_a_role_procedure_skill_is_never_mistaken_for_a_design_system(tmp_path):
    """The false-positive direction: the kit's own skills sit in the same directory.

    Driven over the REAL shipped dev-team skills rather than a fixture, because that is the tree a
    project actually has after an install — eleven directories, each with a SKILL.md, and not one
    of them may be swept up as a broken export.
    """
    project = tmp_path / "proj"
    (project / "project_memory").mkdir(parents=True)
    shutil.copytree(os.path.join(ROOT, "team-kits", "dev-team", "skills"),
                    project / ".claude" / "skills")
    code, output = run(cwd=str(project))
    assert code == 0, output
    assert "no design system dropped in" in output, output


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))

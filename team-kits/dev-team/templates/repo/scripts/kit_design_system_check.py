#!/usr/bin/env python3
"""
kit_design_system_check.py — KIT-OWNED check of a DROPPED-IN design system. DO NOT EDIT IN THE PROJECT.

The user exports their design system from Claude Design and drops the unpacked folder into the
project's skill directory. This script says whether what landed there is usable as the designer's
design-system contract, and when it is not it NAMES the missing part instead of letting the
designer discover it three phases later.

  python scripts/kit_design_system_check.py                     # every bundle it can find
  python scripts/kit_design_system_check.py <path to a folder>  # exactly this one

THE SCHEMA IS FROZEN FROM A REAL EXPORT, not from an invented triple. Measured 2026-08-23 and
again in this round on the user's own 184-entry export (`FR-0045`): the community-claimed shape
(design.html + screenshots/ + design-notes.md) does not exist. What a design-system export really
is, is a SKILL, and its spine is three files, each with one job:

  SKILL.md           the ENTRY POINT -- what a provider registers and what a role opens by name
  readme.md          the HUMAN half -- brand voice, provenance of every asset, licensing caveats
  _ds_manifest.json  the MACHINE half -- namespace, tokens, components, themes, fonts, cards

Beside those three the check asks one derived property rather than a further file list: every path
the manifest NAMES has to exist in the bundle. That is what makes the manifest an index instead of
a description, and it is the half that catches a partial unpack -- measured on the real export,
105 path-shaped values, all of them resolving.

WHAT IT IS NOT. It does not judge the CONTENT of the design (that is the designer's job and the
user's taste), it does not open the components, and it is not a gate: nothing refuses a task
because this exited 2. It is the loud, early answer to "is this thing usable at all".

WHAT COUNTS AS A BUNDLE, and the boundary is deliberate: a directory carrying `_ds_manifest.json`.
That file is the one nothing else in a project's skill directory has, so discovery cannot mistake a
role's procedure skill for an export. The cost is stated rather than hidden: an unpack that lost
the manifest is not FOUND by the sweep at all. Name the folder on the command line and it is
refused for exactly that -- which is why the two modes differ, and why the designer's skill tells
the role to name the folder when the sweep reports nothing.

Every kit update OVERWRITES this file (like kit_checks.py), so fixes reach existing projects.
"""
import json
import os
import sys

MANIFEST = "_ds_manifest.json"
ENTRY_POINT = "SKILL.md"
# The human half, matched case-INSENSITIVELY on purpose: the real export writes `readme.md` while
# its own SKILL.md tells the reader to open `README.md`. Both spellings are the same file on the
# two filesystems this kit runs on, and refusing a bundle over a capital letter would be a refusal
# about nothing.
README = "readme.md"
# The manifest keys a CONSUMER cannot do without: the namespace every component and token is
# rendered under, and the tokens themselves. `components`, `themes`, `fonts` and the rest are read
# when present and not demanded -- the real export ships two of its own lists empty
# (`startingPoints`, `templates`), so "non-empty" is not a property of a valid export. A
# design system with no tokens at all is the one case where the file would be an index over
# nothing, which is why that single list must not be empty.
REQUIRED_STRING_KEYS = ("namespace",)
REQUIRED_LIST_KEYS = ("tokens",)
NON_EMPTY_LIST_KEYS = ("tokens",)
# Where a dropped-in bundle is looked for. The two skill roots the scaffold itself writes into --
# Claude's and the Codex mirror's -- because a design system IS a skill and the drop-in point is
# the same directory the kit's own skills live in.
SKILL_ROOTS = (os.path.join(".claude", "skills"), os.path.join(".agents", "skills"))


def repo_root(start):
    """The project root — the nearest ancestor holding `project_memory/`."""
    here = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(here, "project_memory")):
            return here
        parent = os.path.dirname(here)
        if parent == here:
            return None
        here = parent


def _entries(directory):
    """{lowercased name: real name} of one directory level — one reader for the case question."""
    try:
        return {name.lower(): name for name in os.listdir(directory)}
    except OSError:
        return {}


def path_values(node, trail=""):
    """Every string in the manifest that NAMES A FILE, with the key trail that led to it.

    WHAT MAKES A VALUE A PATH is the KEY it hangs under, not the look of the string: a key whose
    name ends in `path`/`paths` (`sourcePath`, `cssPath`, `globalCssPaths`, `path`) or is exactly
    `files`. Guessing from the value instead — "it contains a slash", "it ends in .css" — would
    read a font family or a CSS selector as a filename and refuse a valid bundle for a file nobody
    ever claimed existed. The manifest names its own paths; this reads the naming.
    """
    if isinstance(node, dict):
        for key, value in node.items():
            yield from path_values(value, str(key))
    elif isinstance(node, list):
        for item in node:
            yield from path_values(item, trail)
    elif isinstance(node, str):
        leaf = trail.lower()
        if leaf.endswith("path") or leaf.endswith("paths") or leaf == "files":
            yield trail, node


def wrapper_child(directory, present):
    """The single child directory holding the bundle, when THIS directory is only a wrapper.

    The commonest unpack result and the least useful refusal: three "X is missing" lines about a
    folder whose contents are perfectly fine one level down. It is a NAMED shape and not a general
    search -- the spine has to be absent here and present in exactly one child -- so the answer
    stays "the export is there, you pointed at its container" and never becomes a hunt through a
    tree. A second level is deliberately not walked: past one hop this stops being a hint about a
    known mistake and becomes a search whose failure nobody can describe.
    """
    if MANIFEST.lower() in present:
        return None
    children = [name for name in sorted(present.values())
                if os.path.isdir(os.path.join(directory, name))
                and os.path.isfile(os.path.join(directory, name, MANIFEST))]
    return children[0] if len(children) == 1 else None


def inspect(directory):
    """[] when `directory` is a usable design system, else the findings — each naming what is missing.

    A LIST AND NOT A BOOLEAN, and not the first failure either: a half-unpacked export is missing
    several things at once, and reporting them one run at a time turns one fix into four.
    """
    findings = []
    directory = os.path.abspath(directory)
    if not os.path.isdir(directory):
        return ["%s is not a directory" % directory]
    present = _entries(directory)
    inner = wrapper_child(directory, present)
    if inner:
        return ["this is a WRAPPER folder, not the bundle: the export is one level down, in %r. "
                "Point this check at that folder, or move its contents up one level. (Unpacking "
                "into a new folder is what produces this, and it is why the sweep found nothing: "
                "a bundle is recognised by %s lying directly inside the skill directory.)"
                % (inner, MANIFEST)]
    for name in (ENTRY_POINT, README, MANIFEST):
        if name.lower() not in present:
            findings.append(
                "%s is missing — %s" % (name, {
                    ENTRY_POINT: "the entry point a provider registers and a role opens by name",
                    README: "the human half: brand voice, asset provenance, licensing caveats",
                    MANIFEST: "the machine-readable spine (namespace, tokens, components)",
                }[name]))
    if ENTRY_POINT.lower() in present:
        with open(os.path.join(directory, present[ENTRY_POINT.lower()]),
                  encoding="utf-8", errors="replace") as handle:
            text = handle.read()
        if not (text.startswith("---") and text.find("\n---", 3) > 0):
            findings.append("%s carries no frontmatter block — a provider registers a skill by the "
                            "`name:` in it, so without one nothing can open this bundle by name"
                            % ENTRY_POINT)
    if MANIFEST.lower() not in present:
        return findings
    manifest_path = os.path.join(directory, present[MANIFEST.lower()])
    try:
        with open(manifest_path, encoding="utf-8") as handle:
            manifest = json.load(handle)
    except (OSError, ValueError) as error:
        findings.append("%s is not readable JSON (%s)" % (MANIFEST, error))
        return findings
    if not isinstance(manifest, dict):
        findings.append("%s is a %s, not an object" % (MANIFEST, type(manifest).__name__))
        return findings
    for key in REQUIRED_STRING_KEYS:
        value = manifest.get(key)
        if not isinstance(value, str) or not value.strip():
            findings.append("%s has no usable `%s` — every token and component is rendered under "
                            "it" % (MANIFEST, key))
    for key in REQUIRED_LIST_KEYS:
        value = manifest.get(key)
        if not isinstance(value, list):
            findings.append("%s has no `%s` list" % (MANIFEST, key))
        elif key in NON_EMPTY_LIST_KEYS and not value:
            findings.append("%s lists no `%s` at all — the index would be an index over nothing"
                            % (MANIFEST, key))
    dangling = []
    for trail, value in path_values(manifest):
        if not os.path.isfile(os.path.join(directory, value.replace("/", os.sep))):
            dangling.append("%s (named under `%s`)" % (value, trail))
    if dangling:
        findings.append("%s names %d file(s) the bundle does not contain, so the export is "
                        "incomplete: %s" % (MANIFEST, len(dangling), ", ".join(sorted(dangling)[:8])
                                            + (" …" if len(dangling) > 8 else "")))
    return findings


def candidates(root):
    """Every dropped-in bundle under the project's skill roots — a directory carrying the manifest."""
    found = []
    for relative in SKILL_ROOTS:
        base = os.path.join(root, relative)
        for name in sorted(_entries(base).values()):
            directory = os.path.join(base, name)
            if os.path.isfile(os.path.join(directory, MANIFEST)):
                found.append(directory)
    return found


def main(argv):
    if len(argv) > 1:
        targets, sweep = [os.path.abspath(argv[1])], False
    else:
        root = repo_root(os.getcwd())
        if not root:
            print("no project_memory/ above %s — run this from inside the project" % os.getcwd())
            return 2
        targets, sweep = candidates(root), True
        if not targets:
            print("no design system dropped in (looked for a folder carrying %s under %s).\n"
                  "That is not a failure: most projects have none. If you DID unpack one and it is "
                  "not listed, name its folder on the command line — a bundle whose manifest is "
                  "missing is not found by this sweep, and naming it says which part is gone."
                  % (MANIFEST, " and ".join(SKILL_ROOTS)))
            return 0
    failed = 0
    for directory in targets:
        findings = inspect(directory)
        if findings:
            failed += 1
            print("REFUSED  %s" % directory)
            for finding in findings:
                print("   - %s" % finding)
        else:
            print("ok       %s" % directory)
    if failed:
        print("\n%d of %d bundle(s) unusable as delivered. Each finding above names what to do; "
              "there is no single remedy, because a wrapper folder is a perfectly good export "
              "pointed at from one level too high, while a dangling index is an unpack that did "
              "not finish." % (failed, len(targets)))
        return 2
    if not sweep:
        print("\nUsable as the design-system contract. The designer reads it through its own "
              "SKILL.md entry point; nothing here judges the design itself.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

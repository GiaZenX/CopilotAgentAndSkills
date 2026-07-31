#!/usr/bin/env python3
"""
write_kit_state.py — record WHICH hook bundle this project installed (spec II.8 hook trust).

WHY THIS FILE EXISTS. `python scripts/harness.py doctor` reports a `hook_trust` capability by comparing the hash of
`.claude/hooks/**` against the hash the project recorded in `.claude/kit_state.json`. Nothing ever
wrote that file. So the comparison ran against an absent value on every project that has ever
existed, `hook_trust` was permanently `unverified`, and `enforcement: hard` was unreachable for a
reason nobody could act on — a check that cannot pass is not a check.

The scaffold is the only thing that knows what it installed, so the scaffold records it, through
this one script rather than twice in PowerShell and once in sh. THE HASH IS NOT COMPUTED HERE
either: `kernel.hashing.hook_bundle_hash` is the single definition, shared with `python scripts/harness.py doctor`
and with the Codex trust binding, because two implementations of one hash is exactly the defect
this repo just spent a review round removing.

THE STATE MACHINE, and why the scaffold may not simply write `active`:

    (scaffold installs hooks)  ->  restart_required
    (a hook actually RUNS in a new session, hash still matches)  ->  active
    (hash no longer matches whatever was recorded)  ->  hooks_trust_required

`restart_required` is the honest verdict at scaffold time: Claude Code reads settings.json at
SESSION START, so the hooks this scaffold just installed are not running in the session that ran
it. Writing `active` here would report enforcement that demonstrably is not in effect yet. The
flip to `active` belongs to `kit_trust_state.py`, a SessionStart hook whose own execution is the
evidence — it can only run if hooks run.

Unknown keys are PRESERVED. `kit_state.json` also carries the installer `bootstrap` marker
(`_kernel.bootstrap_active`), and an installer that silently dropped another installer's marker
would be a bootstrap hole with extra steps.

Usage:  python team-kits/write_kit_state.py --repo <path> --kit <name> [--kit-version <v>]
"""
import argparse
import json
import os
import re
import sys
import tempfile

# The recorder imports the kernel out of the staging it verifies, and runs as part of a scaffold —
# the two trees it touches are exactly the two whose bytecode content is asserted elsewhere: the
# staging ships none (that is why `kit_hash` may skip it) and the installed bundle carries none as
# long as every route that starts code inside it refuses to cache (that is why `hook_bundle_hash`
# may hash all of it, and why this script reports any `.pyc` it finds there as a stranger). This
# line is one of those routes, and a recorder that wrote bytecode would be falsifying its own
# report. `kernel.hashing.BYTECODE_SUFFIXES` states the rule this is one instance of, and points at
# the checks that enumerate the instances — no comment here or there is that enumeration.
sys.dont_write_bytecode = True


def kernel_hashing():
    """The kernel's hashing module — a sibling of this script, exactly as for the hooks."""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    from kernel import hashing
    return hashing


def shown(names):
    """A few of these paths, spelled the way a user can act on them.

    Every check in this file names paths relative to `.claude` — `hooks/gate_x.py`, and for the
    import path also bare `yaml.py` — which reads as a hooks-directory path to anyone who does not
    know the base. One helper so the base is stated once and all three messages truncate alike.
    """
    return (", ".join(".claude/" + name for name in names[:8])
            + (" …" if len(names) > 8 else ""))


def read_existing(path):
    try:
        with open(path, encoding="utf-8-sig") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--kit", required=True)
    parser.add_argument("--kit-version", default="")
    args = parser.parse_args(argv)

    # THE SOURCE IS THIS SCRIPT'S OWN LOCATION, and nothing the caller says can move it. A
    # `--kit-root` flag existed here for exactly one round and was the second bypass in a row:
    # `--kit . --kit-root <repo>/.claude` compared the installed bundle against ITSELF and blessed
    # any tampering at all, rc 0. The function's honest question is "does the installation match
    # the kit", and a caller-supplied answer to "which kit" turns it into "does the installation
    # match whatever you point at". The scaffold therefore invokes the recorder that lives IN the
    # staging it installed from, so the two agree by construction rather than by argument.
    here = os.path.dirname(os.path.abspath(__file__))
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.kit or ""):
        sys.stderr.write("[write_kit_state] --kit %r is not a kit name\n" % args.kit)
        return 1
    hashing = kernel_hashing()

    # ...AND THE KIT BESIDE US MUST BE A KIT. `here` is only "where this file sits", which an
    # attacker moves by running a copy of it next to a tree they authored — the third form of the
    # same laundering: `mkdir <staging>/x/hooks` with an empty directory made every installed gate
    # a mere "stranger" and recorded trust, and a mirror of the TAMPERED bundle under a real kit
    # name did it without a word on stderr. So the source must carry the stamp `bump_kit_version`
    # writes over every kit file, and it must still hash to it.
    #
    # This does not make the recorder unforgeable — an attacker who can run scripts can also
    # regenerate a stamp, and `tools/conftest.py` now carries a `known_hole` saying exactly that,
    # so `python scripts/harness.py doctor` reports `hook_trust` as unverified rather than claiming otherwise. What
    # THIS check covers is the PROVENANCE OF THE SOURCE: the tree the installation is compared
    # against must be a kit this harness stamped, and must still hash to its own stamp. Foreign
    # bodies in the TARGET are a different question and were open for a round while this sentence
    # claimed "every cheap route fails closed" — see the importable-stranger refusal below, which
    # is what makes the two together cover the routes that cost one file and one command.
    kit_dir = os.path.join(here, args.kit)
    recorded = hashing.recorded_kit_hash(kit_dir)
    if recorded is None:
        sys.stderr.write(
            "[write_kit_state] %s carries no VERSION stamp, so it is not a kit this harness "
            "built — refusing to record trust against it.\n" % kit_dir)
        return 1
    if hashing.kit_hash(kit_dir) != recorded:
        sys.stderr.write(
            "[write_kit_state] %s does not hash to the `content:` in its own VERSION — the kit "
            "source has been edited since it was stamped. Remedy: re-install the harness "
            "(`install.ps1`/`install.sh`).\n" % kit_dir)
        return 1

    claude_dir = os.path.join(args.repo, ".claude")
    digest = hashing.hook_bundle_hash(claude_dir)
    if digest is None:
        # No hash, no trust record, either way: writing a state with a null hash would give
        # `_hook_bundle_trust` something to read and nothing to compare, which is the shape that
        # produced "verified" from an empty project in the first place.
        #
        # BUT THERE ARE TWO WAYS TO GET NO HASH and they are different accidents, so they get
        # different exit codes and different sentences. `hook_bundle_hash` answers None both when no
        # subtree exists and when a file inside one could not be read (a broken link in
        # `.claude/hooks` is the cheap way to produce that), and reporting the second as "there is
        # no bundle here" sends the reader looking for a missing installation instead of at the file
        # that would not open. Which case this is, is decided by asking the disk about the subtrees
        # the hash is defined over — `BUNDLE_SUBTREES`, not a second spelling of them here.
        #
        # rc 2 is reserved for the empty case, matching the two codes the rest of this file uses: 1
        # is "I looked and refuse", 2 is "there was nothing to look at". Both scaffolds only check
        # `rc != 0`, so what mattered first was that neither is 0 — "I recorded nothing" used to read
        # to them as "recorded", and `--repo <proj>/.claude` reaches the empty branch by a plausible
        # typo, leaving a scaffold that reported success over a project with no trust record.
        installed = [name for name in hashing.BUNDLE_SUBTREES
                     if os.path.isdir(os.path.join(claude_dir, name))]
        if installed:
            sys.stderr.write(
                "[write_kit_state] the enforcement bundle under %s (%s) holds a file that could "
                "not be read — refusing to record trust for a bundle that cannot be measured. "
                "Remedy: look for a broken link or an unreadable file there, then re-run the "
                "scaffold.\n" % (claude_dir, ", ".join(installed)))
            return 1
        sys.stderr.write("[write_kit_state] no enforcement bundle under %s — nothing recorded\n"
                         % claude_dir)
        return 2

    # IT MUST BE THE KIT'S BUNDLE, not merely whatever is on disk. Recording trust is otherwise an
    # ordinary shell command: edit a hook, let the next session drop to `hooks_trust_required`,
    # re-run this script, and the tampered bundle is back to `restart_required` → `active` without
    # a user, a `/hooks` review or any confirmation — precisely what spec II.8 forbids for a
    # changed bundle. Running the real SCAFFOLD is safe because it re-copies the kit files and so
    # undoes the tampering; this check is how the recorder inherits that property.
    # The two source trees the scaffold installs from, named once: all three checks below compare
    # the installation against exactly these, and three copies of the same join is three chances
    # for one of them to end up pointing somewhere else.
    kit_hooks = os.path.join(here, args.kit, "hooks")
    kernel_dir = os.path.join(here, "kernel")
    try:
        modified = hashing.modified_bundle_files(kit_hooks, kernel_dir, claude_dir)
    except hashing.BundleSourceMissing as exc:
        # A comparison that could not be MADE must not read as a comparison that passed — the
        # first version skipped an absent source and returned "no differences".
        sys.stderr.write(
            "[write_kit_state] %s. Refusing to record trust: without the kit's own files there is "
            "nothing to check the installed bundle against. Remedy: run the copy of this script "
            "that lives in the staging the scaffold installed from.\n" % exc)
        return 1
    if modified:
        sys.stderr.write(
            "[write_kit_state] these installed files are not the '%s' kit's: %s — refusing to "
            "record trust. This script blesses what the scaffold installed; it is not a way to "
            "re-trust a modified enforcement layer. Remedy: re-run the scaffold, which reinstalls "
            "the kit files, then review the change in /hooks.\n" % (args.kit, shown(modified)))
        return 1

    # A FOREIGN FILE THAT WOULD IMPORT IS A REFUSAL; anything else is a note. The line between the
    # two is not "how suspicious does it look" but whether Python's import machinery would load
    # code from it (`hashing.resolves_to_module`), because that is exactly the property that turns
    # a stray file into part of the enforcement layer: `.claude/hooks` is `sys.path[0]` for every
    # gate process and `.claude` itself is on the path while the kernel is imported, so a planted
    # `yaml.py` in either owns the parser `kernel.state` imports at module scope.
    #
    # Recording trust rewrites the bundle hash AROUND such a file, which is why rc 0 here was the
    # cheapest attack in the repo — cheaper than the residual `known_hole`, which at least demands
    # a self-stamped staging: write one file, run the recorder, and one SessionStart later the
    # bundle is `active` with the intruder inside it. Measured on 2026-07-27 for `hooks/yaml.py`,
    # `hooks/yaml/__init__.py`, `hooks/yaml.pyc` and `.claude/yaml.py`; the last one was recorded
    # without even a warning line.
    importables = hashing.foreign_importables(claude_dir, kit_hooks, kernel_dir)
    if importables:
        sys.stderr.write(
            "[write_kit_state] the enforcement layer holds importable code the '%s' kit did not "
            "ship: %s — refusing to record trust. Any of these is a module for every gate "
            "process (`.claude/hooks` is sys.path[0]; `.claude` is on the path while the kernel "
            "is imported), so recording a bundle hash around them would bless code the kit never "
            "delivered. Remedy: remove them, then re-run the scaffold.\n"
            % (args.kit, shown(importables)))
        return 1

    # Reported, never fatal: what is left cannot be imported, and the usual cause is an older
    # kit's data file the scaffold never pruned. Still named, because recording trust rewrites the
    # bundle hash around it and `hook_trust` will not mention it afterwards.
    refused = set(importables)
    strangers = [name for name in hashing.strangers_in_the_bundle(claude_dir, kit_hooks,
                                                                  kernel_dir)
                 if name not in refused]
    if strangers:
        sys.stderr.write(
            "[write_kit_state] the enforcement layer also holds files the '%s' kit did not ship: "
            "%s. Nothing there is importable, so this is a report, not a refusal. Remedy: remove "
            "them, or confirm they belong.\n" % (args.kit, shown(strangers)))

    path = os.path.join(args.repo, ".claude", "kit_state.json")
    data = read_existing(path)
    data.update({
        "kit": args.kit,
        "kit_version": args.kit_version or data.get("kit_version", ""),
        "hook_bundle_hash": digest,
        "state": "restart_required",
    })
    # unique temp name: a fixed `.tmp` is shared scratch, and the SessionStart hook writes the
    # same file. `os.replace` is atomic; the write into the temp file is not.
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", prefix="kit_state.")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    os.replace(tmp, path)
    print("[write_kit_state] .claude/kit_state.json -> restart_required (%s)" % digest[:12])
    return 0


if __name__ == "__main__":
    sys.exit(main())

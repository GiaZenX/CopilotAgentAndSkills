#!/usr/bin/env python3
"""
write_kit_state.py — record WHICH hook bundle this project installed (spec II.8 hook trust).

WHY THIS FILE EXISTS. `harness doctor` reports a `hook_trust` capability by comparing the hash of
`.claude/hooks/**` against the hash the project recorded in `.claude/kit_state.json`. Nothing ever
wrote that file. So the comparison ran against an absent value on every project that has ever
existed, `hook_trust` was permanently `unverified`, and `enforcement: hard` was unreachable for a
reason nobody could act on — a check that cannot pass is not a check.

The scaffold is the only thing that knows what it installed, so the scaffold records it, through
this one script rather than twice in PowerShell and once in sh. THE HASH IS NOT COMPUTED HERE
either: `kernel.hashing.hook_bundle_hash` is the single definition, shared with `harness doctor`
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


def kernel_hashing():
    """The kernel's hashing module — a sibling of this script, exactly as for the hooks."""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    from kernel import hashing
    return hashing


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
    claude_dir = os.path.join(args.repo, ".claude")
    digest = hashing.hook_bundle_hash(claude_dir)
    if digest is None:
        # No bundle, no trust record. Writing a state with a null hash would give
        # `_hook_bundle_trust` something to read and nothing to compare, which is the shape that
        # produced "verified" from an empty project in the first place.
        sys.stderr.write("[write_kit_state] no enforcement bundle under %s — nothing recorded\n"
                         % claude_dir)
        return 0

    # IT MUST BE THE KIT'S BUNDLE, not merely whatever is on disk. Recording trust is otherwise an
    # ordinary shell command: edit a hook, let the next session drop to `hooks_trust_required`,
    # re-run this script, and the tampered bundle is back to `restart_required` → `active` without
    # a user, a `/hooks` review or any confirmation — precisely what spec II.8 forbids for a
    # changed bundle. Running the real SCAFFOLD is safe because it re-copies the kit files and so
    # undoes the tampering; this check is how the recorder inherits that property.
    try:
        modified = hashing.modified_bundle_files(os.path.join(here, args.kit, "hooks"),
                                                 os.path.join(here, "kernel"), claude_dir)
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
            "the kit files, then review the change in /hooks.\n"
            % (args.kit, ", ".join(modified[:8]) + (" …" if len(modified) > 8 else "")))
        return 1

    # Reported, never fatal: a stranger in `.claude/hooks` is usually an older kit's hook the
    # scaffold never pruned. Named because that directory is `sys.path[0]` for every gate process,
    # so a stray `yaml.py` there shadows PyYAML for the kernel — and because recording trust
    # rewrites the bundle hash around it, `hook_trust` will not mention it afterwards.
    strangers = hashing.strangers_in_the_bundle(
        claude_dir, os.path.join(here, args.kit, "hooks"), os.path.join(here, "kernel"))
    if strangers:
        sys.stderr.write(
            "[write_kit_state] the enforcement layer also holds files the '%s' kit did not ship: "
            "%s. They are on sys.path for every hook process. Remedy: remove them, or confirm "
            "they belong and re-run.\n"
            % (args.kit, ", ".join(strangers[:8]) + (" …" if len(strangers) > 8 else "")))

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

"""Canonical subject-manifest hashing (HARNESS_V2_SPEC.md II.2 "Hash-Kanonisierung").

Canonical JSON -- sorted keys, NFC-normalized unicode, compact separators, explicit
hash_schema_version -- deliberately NOT yaml.safe_dump: PyYAML dump output is
version-dependent and un-normalized (the V1 proc_hash.py breakage class this
replaces; verified in the 2026-07-24 review).

Fail-closed: non-JSON types and NaN/Infinity raise instead of being coerced --
a hash over silently-mangled content would defeat approval invalidation.
"""
from __future__ import annotations

import hashlib
import json
import os
import unicodedata


HASH_SCHEMA_VERSION = 1

# WHAT THE ENFORCEMENT BUNDLE IS: the code that decides whether a call is allowed. Both of these
# subtrees, and only these — named rather than "everything under .claude", because that directory
# also holds files that change during ordinary use (`kit_state.json` is rewritten by the very hook
# that reads this hash) and a bundle whose hash changes every session cannot be trusted against.
BUNDLE_SUBTREES = ("hooks", "kernel")
# Artifacts of running the hooks, not part of the bundle: a first Codex session would otherwise
# change the hash it had just been trusted against, by doing nothing but running.
BUNDLE_IGNORED_DIRS = ("__pycache__",)
BUNDLE_IGNORED_SUFFIXES = (".pyc", ".pyo")


def hook_bundle_hash(claude_dir: str):
    """SHA-256 over the installed enforcement bundle, or None when there is nothing to hash.

    THE definition, singular, deliberately. There were two — this one and a second in
    `gen_provider_artifacts` — over the same directory, and they disagreed: that one walked the
    tree and hashed every file, this one hashed only top-level `*.py`. Whichever answer
    `harness doctor` gave, it could not be the value the Codex trust binding was built from, so
    `hook_trust` compared two things that were never the same measurement. Two implementations of
    one concept is the defect; picking the "better" one and leaving both would only have delayed
    it. Callers that need extra guarantees (a missing directory is fatal for the Codex artifact
    generator, a reparse point is a security question there) keep those checks around the call.

    SCOPE IS `.claude/hooks` PLUS `.claude/kernel`, not the hooks alone. The gates are thin; the
    decisions live in the kernel they import. Hashing only the hooks would have let `hook_trust`
    report `verified` over a bundle whose `report.validate_state` had been rewritten to return
    `[]` — a claim far wider than the measurement, which is the one thing the capability matrix
    exists to prevent. A subtree that is absent contributes nothing rather than failing: not every
    kit ships both, and "missing" is a different question from "changed".

    Properties that make this hash mean "the executable bundle", each load-bearing:
      * RECURSIVE and ALL FILE TYPES. A hook can read a `.json` config or a `.txt` allowlist next
        to it; a top-level-`*.py`-only hash calls an edited allowlist "unchanged".
      * the RELATIVE PATH participates — INCLUDING the subtree name, so moving a file between
        `hooks/` and `kernel/` changes the hash — NUL-separated from the content. Concatenating
        name+content with no delimiter lets two different bundles produce one byte stream.
      * `__pycache__` and `.pyc`/`.pyo` are skipped — see BUNDLE_IGNORED_*.

    One copy of this algorithm survives on purpose: the inline verifier that
    `gen_provider_artifacts.hook_bundle_verifier_b64` embeds in the Codex hook command, which
    cannot import anything (its bytes are what Codex hashes). It is pinned to this function by a
    test that runs both over an adversarial tree.
    """
    return _hash_subtrees([(name, os.path.join(claude_dir, name)) for name in BUNDLE_SUBTREES])


class BundleSourceMissing(ValueError):
    """A source tree to compare against is absent — see `modified_bundle_files`."""


KIT_SKIP_DIRS = frozenset(("__pycache__", ".ruff_cache", ".mypy_cache", ".pytest_cache"))
# Shared scaffold/generator inputs that decide what a kit installs, hashed with it. A kit whose
# own files are untouched but whose scaffold changed is a different installation.
KIT_SHARED_FILES = (
    "gen_provider_artifacts.py", "init_project_memory.ps1", "init_project_memory.sh",
    "model_tiers.yaml", "preset_config.py", "registry.yaml", "scaffold_team.ps1",
    "scaffold_team.sh", "write_kit_state.py",
)


def kit_hash(kit_dir: str) -> str:
    """SHA-256 over a kit's own files plus the shared harness inputs, CRLF-normalized.

    Lives in the KERNEL, which ships, because two things need it and only one of them used to be
    able to reach it: `tools/bump_kit_version.py` writes it into `<kit>/VERSION` as `content:`,
    and `write_kit_state.py` checks that the kit it is about to compare against is that kit. The
    tools directory does not travel to a staging, so a copy there would have been the third
    duplicated hash in this file's history.

    CRLF normalization keeps the value identical across Windows and Linux checkouts of one commit.
    The kit's own top-level VERSION is excluded — it carries the result.
    """
    digest = hashlib.sha256()
    for dirpath, dirnames, filenames in os.walk(kit_dir):
        dirnames[:] = sorted(d for d in dirnames if d not in KIT_SKIP_DIRS)
        for name in sorted(filenames):
            if (name == "VERSION" and dirpath == kit_dir) or name.endswith(".pyc"):
                continue
            path = os.path.join(dirpath, name)
            digest.update(os.path.relpath(path, kit_dir).replace("\\", "/").encode("utf-8"))
            with open(path, "rb") as handle:
                digest.update(handle.read().replace(b"\r\n", b"\n"))
    root = os.path.dirname(os.path.abspath(kit_dir))
    for relative in KIT_SHARED_FILES:
        path = os.path.join(root, relative)
        if not os.path.isfile(path):
            continue
        digest.update(("@shared/" + relative).encode("utf-8"))
        with open(path, "rb") as handle:
            digest.update(handle.read().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def recorded_kit_hash(kit_dir: str):
    """The `content:` hash `<kit>/VERSION` claims, or None when there is no such stamp."""
    try:
        with open(os.path.join(kit_dir, "VERSION"), encoding="utf-8-sig") as handle:
            for line in handle:
                if line.startswith("content:"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return None


def modified_bundle_files(kit_dir: str, kernel_dir: str, claude_dir: str):
    """Kit files whose INSTALLED copy differs from the source — empty when the bundle is the kit's.

    RAISES `BundleSourceMissing` when a source tree is absent, and that is the whole difference
    between this function and the one it replaced. The first version simply skipped a missing
    source and returned `[]`, so "could not compare" and "compared, all equal" were the same
    answer — fail-open at the bottom of a fail-closed layer. Demonstrated end to end: replace two
    gates with `sys.exit(0)`, watch the next session drop to `hooks_trust_required`, run the
    recorder with a `--kit-root` that does not exist, and one session later `harness doctor`
    reports `hook_trust: verified` over a bundle whose spawn veto is a no-op. A typo in the flag
    reaches the same place by accident.

    Exists so `write_kit_state.py` can refuse to bless a bundle that is not the kit's. Without it,
    recording trust was a plain shell command an agent could run: edit a hook, watch the next
    session report `hooks_trust_required`, re-run the recorder, and the tampered bundle is
    `restart_required` → `active` on the following start — no user, no `/hooks`, no confirmation,
    which is exactly what spec II.8 requires for a changed bundle. Running the real SCAFFOLD is
    safe by comparison, because it re-copies the kit files and thereby undoes the tampering it
    would otherwise bless; this is how the recorder inherits that property.

    FILE BY FILE, not hash against hash. A whole-bundle hash comparison was tried first and was
    wrong: the scaffold copies over `.claude/hooks` without pruning, so any file a project has
    accumulated — an older kit's hook, a rename left behind — made the two hashes differ, and the
    scaffold then threw on a perfectly untampered install. The question this answers is "is the
    kit's enforcement code as the kit shipped it", and an extra file is a different question.

    Note what that other question is NOT: `hook_trust` does not cover it. The recorder rewrites
    the bundle hash INCLUDING the stranger, so the next report calls that bundle trusted. It
    matters more than it sounds, because GATE_PREAMBLE puts the hooks directory on `sys.path[0]`
    — a `.claude/hooks/yaml.py` shadows PyYAML for the kernel in every gate process. So the
    recorder NAMES strangers on stderr, and closing it properly means the scaffold pruning what it
    did not install, which belongs to phase 3.

    Sources match what the scaffold installs: `$kit/hooks/*` (top-level files) and the whole
    `kernel/` tree. A source file MISSING from the install counts as modified.
    """
    modified = []
    for subtree, root, flat in (("hooks", kit_dir, True), ("kernel", kernel_dir, False)):
        if not os.path.isdir(root):
            # Keyed on WHAT IS INSTALLED, not on what was asked for. Missing source while
            # something is installed is the dangerous half: it is the shape in which "could not
            # compare" used to be reported as "compared, all equal". Missing source with nothing
            # installed is a kit that ships no such subtree, and there is nothing to be wrong
            # about. (In practice the recorder cannot even start without a kernel beside it, so
            # that second branch is defensive rather than load-bearing — it is kept because the
            # condition should describe the situation, not the current call graph.)
            if os.path.isdir(os.path.join(claude_dir, subtree)):
                raise BundleSourceMissing(
                    "%s/ is installed but there is no source to compare it against at %s — "
                    "refusing to answer 'unmodified' about a comparison that did not happen"
                    % (subtree, root))
            continue
        for relative, source in _bundle_files(root, flat):
            installed = os.path.join(claude_dir, subtree, relative.replace("/", os.sep))
            if source is None:            # the source itself is a symlinked directory
                modified.append(subtree + "/" + relative)
                continue
            try:
                with open(source, "rb") as left, open(installed, "rb") as right:
                    if left.read() != right.read():
                        modified.append(subtree + "/" + relative)
            except OSError:
                modified.append(subtree + "/" + relative)
    return sorted(modified)


def strangers_in_the_bundle(claude_dir: str, kit_dir: str, kernel_dir: str):
    """Installed enforcement files the kit did not ship — reported, not refused.

    Separate from `modified_bundle_files` because the answer is different: a stranger is usually
    an older kit's hook the scaffold never pruned, which is a mess rather than an attack. It is
    still worth naming, since `.claude/hooks` is `sys.path[0]` for every gate process.
    """
    known = set()
    for subtree, root, flat in (("hooks", kit_dir, True), ("kernel", kernel_dir, False)):
        if os.path.isdir(root):
            known.update(subtree + "/" + rel for rel, _ in _bundle_files(root, flat))
    found = []
    for subtree in BUNDLE_SUBTREES:
        installed_root = os.path.join(claude_dir, subtree)
        if not os.path.isdir(installed_root):
            continue
        # NOT flat, even for `hooks`: `modified_bundle_files` is flat because the scaffold
        # installs only top-level files, but a STRANGER can be a package — and
        # `hooks/yaml/__init__.py` shadows PyYAML for the kernel exactly as `hooks/yaml.py` does,
        # while a flat scan cannot see it.
        for relative, _path in _bundle_files(installed_root, False):
            name = subtree + "/" + relative
            if name not in known:
                found.append(name)
    return sorted(found)


SYMLINK_MARKER = "<symlink>"


def _bundle_files(root: str, flat: bool):
    """(relative posix path, absolute path or None) for every entry the bundle takes from `root`.

    A SYMLINKED DIRECTORY yields `(name + "/" + SYMLINK_MARKER, None)` and is not descended into.
    `os.walk` does not follow directory links by default, so before this such a link was invisible
    to the hash, to the stranger scan and to doctor — while Python imports through it perfectly
    well. Measured: `.claude/hooks/yaml -> <elsewhere>` shadows PyYAML for the kernel in every
    gate process, and `.claude/hooks/_compat -> <elsewhere>` makes `guard_harness_selfmod` wave
    through a write to `.claude/hooks/` — with the bundle hash UNCHANGED and `hook_trust` still
    `verified`. Following the link instead would invite cycles and would hash whatever it points
    at; naming it is enough, because a name in the hash is a hash that changes.
    """
    if flat:
        for name in sorted(os.listdir(root)):
            path = os.path.join(root, name)
            if os.path.islink(path):
                yield name + "/" + SYMLINK_MARKER, None
            elif os.path.isfile(path) and not name.endswith(BUNDLE_IGNORED_SUFFIXES):
                yield name, path
        return
    for current, dirs, files in os.walk(root):
        linked = sorted(d for d in dirs if os.path.islink(os.path.join(current, d)))
        dirs[:] = sorted(d for d in dirs
                         if d not in BUNDLE_IGNORED_DIRS and d not in linked)
        for name in linked:
            path = os.path.join(current, name)
            yield os.path.relpath(path, root).replace(os.sep, "/") + "/" + SYMLINK_MARKER, None
        for name in sorted(files):
            if name.endswith(BUNDLE_IGNORED_SUFFIXES):
                continue
            path = os.path.join(current, name)
            yield os.path.relpath(path, root).replace(os.sep, "/"), path


def _hash_subtrees(subtrees, flat_first=False):
    """SHA-256 over named subtrees; `flat_first` treats the first one non-recursively.

    Enumeration is delegated to `_bundle_files` rather than repeated here. The two used to walk
    separately and the difference was not academic: the copy in this function had no symlink
    handling, so a link planted in `.claude/hooks` left the hash untouched while the stranger scan
    (once fixed) reported it — one directory, two answers, which is the defect this module was
    written to end.
    """
    digest = hashlib.sha256()
    seen = False
    for index, (subtree, root) in enumerate(subtrees):
        if not os.path.isdir(root):
            continue
        for relative, path in _bundle_files(root, flat_first and index == 0):
            digest.update((subtree + "/" + relative).encode("utf-8") + b"\0")
            if path is not None:
                try:
                    with open(path, "rb") as handle:
                        digest.update(handle.read())
                except OSError:
                    # a file that cannot be read is not a bundle that can be trusted
                    return None
            digest.update(b"\0")
            seen = True
    return digest.hexdigest() if seen else None


def _nfc(obj):
    """Recursively NFC-normalize every string (keys and values).

    Fail-closed on the two silent-collision classes (Fable-Check 4, BUG-2/3):
    non-string dict keys (json.dumps would coerce {1: x} into {"1": x}) and
    sibling keys that collide after NFC normalization (a dict comprehension
    would silently merge them -- two different manifests, one hash).
    """
    if isinstance(obj, str):
        return unicodedata.normalize("NFC", obj)
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if not isinstance(k, str):
                raise TypeError(
                    "subject_manifest dict key %r is not a string -- canonical "
                    "hashing is only defined over JSON objects (string keys). "
                    "Remedy: convert the key explicitly before hashing." % (k,)
                )
            nk = unicodedata.normalize("NFC", k)
            if nk in out:
                raise ValueError(
                    "subject_manifest contains sibling keys that collide after "
                    "NFC normalization (%r) -- refusing to hash a silently "
                    "merged manifest. Remedy: deduplicate the keys." % nk
                )
            out[nk] = _nfc(v)
        return out
    if isinstance(obj, (list, tuple)):
        return [_nfc(v) for v in obj]
    if obj is None or isinstance(obj, (bool, int, float)):
        return obj
    raise TypeError(
        "subject_manifest contains non-JSON type %r -- hashes are only defined "
        "over plain JSON data (str/int/float/bool/None/list/dict). Remedy: "
        "serialize the value explicitly before hashing." % type(obj).__name__
    )


def canonical_json(obj) -> str:
    """Deterministic JSON text: sorted keys, NFC unicode, compact, no NaN."""
    return json.dumps(
        _nfc(obj),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )


def subject_manifest_hash(manifest) -> str:
    """SHA-256 hex over the canonical envelope {hash_schema_version, subject_manifest}.

    The version field participates in the hash: a future canonicalization change
    bumps HASH_SCHEMA_VERSION and thereby visibly invalidates old approvals
    instead of silently colliding with them.
    """
    envelope = {
        "hash_schema_version": HASH_SCHEMA_VERSION,
        "subject_manifest": manifest,
    }
    return hashlib.sha256(canonical_json(envelope).encode("utf-8")).hexdigest()

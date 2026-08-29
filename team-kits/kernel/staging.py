"""Staging lifecycle + freeze operations (HARNESS_V2_SPEC.md II.4/II.6/II.6a) -- 1.6.

Specialists (and the orchestrator for small-WFRs) propose into
staging/<task_id>/ or staging/<ROOT-ID>/ -- non-canonical, never loaded at
session start. The KERNEL alone promotes:

- freeze_wireframe: on scope mint, staging WFR -> design/wireframes/
  WFR-nnnn.rNN.drawio.svg + schema-validated companion (diagram_hash,
  scope_apr_ref); the DSN derives from the frozen WFR (II.6a)
- freeze_architecture: staging ARC -> architecture/revisions/ + companion in
  architecture/active/ (II.6a; no own automaton -- state = location +
  approval_ref)
- freeze_design: staging DSN html -> design/revisions/ + manifest (file hash +
  root revision + timestamp), updates the root's design_refs (II.6)
- archive_staging / clear_staging: after approval the dir is EMPTIED, after
  rejection ARCHIVED (never silently deleted -- history-prune means archive)

Fail-closed validation: .drawio.svg must parse as XML (well-formedness; a true
browser render check is phase-2 tooling -- the companions' `render_check: True`
currently attests EXACTLY that well-formedness, nothing more) and companions
must pass their schema.
Crash notes: a crash between the frozen copy and the staging clear leaves both
copies -- harmless (the canonical copy exists; a re-freeze produces rNN+1);
`python scripts/harness.py validate`/doctor surface leftovers.
Wiring note: WHO calls freeze at mint time is phase-2 hook/orchestrator logic;
the kernel provides the operations.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import time
import xml.etree.ElementTree as ET

from .backlog_types import ACTIVE_DIRS, field_elements, parse_id
from .lock import ext_path
from .schemas import validate
from .state import (
    STAGING_DIRNAME,
    ProjectState,
    StateError,
    _now_iso,
    names_a_drive,
    revision_name,
    split_revision,
)


class StagingError(StateError):
    """Staging/freeze operation refused -- message carries the remedy."""


# The ONE directory a `design_refs` entry can point into, named where the entry is PRODUCED.
# `freeze_design` (below) is the only function in the harness that appends to `design_refs`, and
# it appends a path under `ACTIVE_DIRS[DESIGN_REF_TYPE]` -- so the constant is what that function
# composes its own target from, and `dispatch` reads it rather than carrying a second copy.
#
# WFR IS NOT IN HERE, and the first cut of this was wider than any producer: `freeze_wireframe`
# writes a frozen wireframe but never touches `design_refs`, so no entry pointing into
# `design/wireframes/` is ever created -- accepting one would have been a rule about a shape
# nothing produces. Spec II.2 does say the scope manifest's design references include approved
# wireframes (II.6a), so the ABSENCE OF THAT PRODUCER is an open gap and not a decision taken
# here; the day `freeze_wireframe` appends, it appends through this constant and the resolver
# follows. ARC stays out for a different reason: an architecture revision is not a design
# reference (II.6 makes `design_ref` the binding IMPLEMENTATION reference for a UI task).
DESIGN_REF_TYPE = "DSN"


def frozen_design_dirs():
    """The state-relative directories a FROZEN design reference may point into."""
    return (ACTIVE_DIRS[DESIGN_REF_TYPE],)


def architecture_revisions_dir(state: ProjectState) -> str:
    """Where `freeze_architecture` lands a frozen ARC diagram.

    A builder rather than an inline join, for the reason `ProjectState.generated_path` is one:
    `kernel.layout` asks each writer where it writes, and this is the one canonical directory no
    other builder in the kernel composes -- it is under `architecture/` but beside, not inside,
    `ACTIVE_DIRS["ARC"]`.
    """
    return os.path.join(state.root, "architecture", "revisions")


def contained_child(base: str, name: str, what: str) -> str:
    """`base/name`, refused unless `name` is ONE segment that really stays inside `base`.

    THE CHOKEPOINT FOR EVERY PATH A FREEZE COMPOSES FROM A CALLER'S STRING, and it exists because
    the day those strings became reachable from a command line they became a `shutil.rmtree` on any
    directory. Every freeze ends in `clear_staging(..., mode="promoted")`, which is
    `rmtree(<root>/staging/<key>)`, and `staging_dir` used to be a bare `os.path.join` -- so
    `{"staging_key": "../.."}` on stdin deleted the whole repository, and `".."` deleted the whole
    state directory. The body travels on STDIN, so no hook sees it: `gate_write_scope` reads command
    LINES, and all three of those command lines pass all eight registered shell gates.

    TWO CHECKS, AS DEFENCE IN DEPTH, and that wording is what the measurement supports rather than
    the stronger one this paragraph first carried ("neither alone is the answer"). The SEGMENT
    check refuses the text that names another place -- a separator, `.`, `..`, a drive letter
    (`ntpath.join("D:\\\\a", "C:x")` returns `C:x`, so an absolute second argument silently replaces
    the first on Windows). The REALPATH check refuses the link that goes somewhere else while
    spelling ONE segment; a junction needs no admin rights to create, and
    `gate_write_scope._repo_relative` resolves the target side for exactly this reason.

    WHAT THE TEST ACTUALLY DISTINGUISHES, so nobody reads the pair as two measured teeth: against
    the six escape shapes `test_no_freeze_parameter_can_reach_outside_the_state_root` feeds, EACH
    HALF ALONE catches all of them -- deleting the realpath check, the drive-letter clause, the
    `.`/`..` clause or the backslash normalisation each leaves that test GREEN. Only the whole
    guard going away turns it red. The junction is the one case that needs the realpath half and
    the escape list contains no such form; it was verified by hand and not pinned. That is the
    mechanism to fix, and the fix is a junction in the fixture -- a symlink guard without a test
    has rotted twice in this repo, and a docstring claiming two independent teeth would have been
    the third time.

    A LATENT EDGE, not exploitable today and written down before it becomes one: the containment
    check accepts `resolved == container`, so a name Windows normalises AWAY (`".."` with trailing
    spaces, `"..."`, `"   "`) passes the segment check and resolves to the container itself.

    THE SENTENCE THAT USED TO FOLLOW HERE HAS EXPIRED, and it is written down rather than quietly
    repaired: "every caller today appends a FILE NAME afterwards" was true until `submit-result
    --from` (BUG-0048) began OPENING the composed path directly. Measured 2026-08-17 for both
    normalised-away names on this host: `--from '...'` and `--from '.. '` reach `open()` on the
    staging DIRECTORY and stop there with a permission error (rc 2, nothing read, nothing written)
    — so the edge is still not exploitable, for a different reason than before. The condition
    under which it becomes one is unchanged and now has two ways in: a caller that hands this
    result to a DIRECTORY operation, or a host on which opening a directory succeeds. Either needs
    `resolved != container` here.

    `what` names the parameter in the refusal, because the role typed it.
    """
    text = str(name or "")
    normalised = text.replace("\\", "/")
    if (not normalised or "/" in normalised or normalised in (".", "..")
            or names_a_drive(text)):
        raise StagingError(
            "%s %r is not a single name inside %s -- refused. A staging key and a staged file name "
            "are NAMES, not paths: the kernel joins them onto the state directory and then empties "
            "what it promoted, so a value that walks out of that directory deletes or copies "
            "somewhere nobody asked for. Remedy: pass the bare name (e.g. `TSK-0007`, "
            "`preview.html`)." % (what, text, base))
    target = os.path.join(base, text)
    resolved = os.path.realpath(ext_path(target))
    container = os.path.realpath(ext_path(base))
    if resolved != container and not resolved.startswith(container + os.sep):
        raise StagingError(
            "%s %r resolves to %s, which is outside %s -- refused. A link may spell one name and "
            "lead anywhere. Remedy: remove the link, or stage the artefact in the real directory."
            % (what, text, resolved, container))
    return target


def staging_dir(state: ProjectState, key: str) -> str:
    return contained_child(state.staging_root(), key, "staging key")


def _file_hash(path: str) -> str:
    digest = hashlib.sha256()
    with open(ext_path(path), "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_xml_wellformed(path: str) -> None:
    try:
        ET.parse(ext_path(path))
    except ET.ParseError as exc:
        raise StagingError(
            "%s is not well-formed XML (%s) -- promotion blocked (fail-closed, "
            "spec II.6a). Remedy: fix the .drawio.svg in the draw.io extension "
            "and retry." % (os.path.basename(path), exc)
        ) from None
    except FileNotFoundError:
        raise StagingError(
            "staged file %s does not exist. Remedy: check the staging dir."
            % path
        ) from None


def _next_frozen_revision(target_dir: str, item_id: str) -> int:
    """Max-parse over EVERY file carrying this item's `.rNN` (frozen file AND
    companion/manifest, whatever the suffix): a manually deleted frozen revision must
    never cause an rNN number to be REUSED (Fable-Check 11/NIT-1).

    Through `state.split_revision`, the same reader `_frozen_revision_path` and
    `iter_active_items` use, so "which number has been used" and "which revision IS the
    item" cannot come apart -- and the names this module COMPOSES (`revision_name`) are
    read back by that same rule.
    """
    highest = 0
    if os.path.isdir(ext_path(target_dir)):
        for name in os.listdir(ext_path(target_dir)):
            found, revision, _suffix = split_revision(name)
            if found == item_id:
                highest = max(highest, revision)
    return highest + 1


def freeze_wireframe(
    state: ProjectState, staging_key: str, wfr_id: str, scope_apr_ref: str,
    derives_from: list, title: str,
) -> dict:
    """Freeze staging/<key>/<WFR-id>.drawio.svg into design/wireframes/ (II.6a)."""
    parse_id(wfr_id)
    source = os.path.join(staging_dir(state, staging_key), wfr_id + ".drawio.svg")
    with state.lock:
        _assert_xml_wellformed(source)
        target_dir = os.path.join(state.root, "design", "wireframes")
        revision = _next_frozen_revision(target_dir, wfr_id)
        frozen = os.path.join(target_dir, revision_name(wfr_id, revision, ".drawio.svg"))
        companion = {
            "id": wfr_id,
            "title": title,
            "derives_from": list(derives_from),
            "revision": revision,
            "diagram_hash": _file_hash(source),
            "render_check": True,
            "scope_apr_ref": scope_apr_ref,
        }
        validate(companion, "wfr_companion")
        os.makedirs(ext_path(target_dir), exist_ok=True)
        shutil.copyfile(ext_path(source), ext_path(frozen))
        state._write_yaml_atomic(
            os.path.join(target_dir, revision_name(wfr_id, revision, ".yaml")), companion
        )
        clear_staging(state, staging_key, mode="promoted", _locked=True)
        state._regenerate_index_locked()
        return {"frozen": frozen, "companion": companion}


def freeze_architecture(
    state: ProjectState, staging_key: str, arc_id: str, title: str, scope: str,
    derives_from: list, approval_ref: str = None, assets: dict = None,
    packaging: dict = None,
) -> dict:
    """Freeze staging ARC into architecture/revisions/ + active companion (II.6a).

    `packaging` is the optional {method: ...} block the packaging gate reads. It is
    a PARAMETER rather than something the architect writes afterwards because this
    is the only path that creates an ARC item: `capture` refuses the type, and
    `project_memory/**` is kernel-only for tool writes. Without it the gate had a
    reader and no producer, which blocks every merge with no way out.
    """
    parse_id(arc_id)
    source = os.path.join(staging_dir(state, staging_key), arc_id + ".drawio.svg")
    with state.lock:
        _assert_xml_wellformed(source)
        revisions_dir = architecture_revisions_dir(state)
        revision = _next_frozen_revision(revisions_dir, arc_id)
        frozen = os.path.join(revisions_dir, revision_name(arc_id, revision, ".drawio.svg"))
        companion = {
            "id": arc_id,
            "title": title,
            "scope": scope,
            "derives_from": list(derives_from),
            "revision": revision,
            "approval_ref": approval_ref,
            "diagram_hash": _file_hash(source),
            "assets": assets or {"mode": "self_contained"},
            "render_check": True,
        }
        if packaging is not None:
            # absent, not null: the schema is strict and `packaging` is optional,
            # so a `None` value would fail validation instead of meaning "not
            # stated here"
            companion["packaging"] = packaging
        validate(companion, "arc_companion")
        os.makedirs(ext_path(revisions_dir), exist_ok=True)
        shutil.copyfile(ext_path(source), ext_path(frozen))
        active_dir = os.path.join(state.root, "architecture", "active")
        os.makedirs(ext_path(active_dir), exist_ok=True)
        shutil.copyfile(ext_path(source), ext_path(os.path.join(active_dir, arc_id + ".drawio.svg")))
        state._write_yaml_atomic(os.path.join(active_dir, arc_id + ".yaml"), companion)
        clear_staging(state, staging_key, mode="promoted", _locked=True)
        state._regenerate_index_locked()
        return {"frozen": frozen, "companion": companion}


def freeze_design(
    state: ProjectState, staging_key: str, dsn_id: str, root_id: str, source_name: str,
) -> dict:
    """Freeze a self-contained HTML preview into design/revisions/ and point the
    root's design_refs at it (II.6). NOTE: updating design_refs is a hashed-field
    change -- on an approved root this invalidates the approval by design.
    Everything happens in ONE lock hold (Fable-Check 11/BUG-1): the refs are
    computed from the FRESH root read, so no parallel append is lost."""
    parse_id(dsn_id)
    # `source_name` is the ONLY freeze parameter that names a file rather than deriving it from an
    # id (`parse_id` bounds `wfr_id`/`arc_id` to `<TYP>-nnnn`, so those two compose nothing a caller
    # chose). It goes through the same chokepoint: an absolute value would have replaced the staging
    # directory outright under `os.path.join`, and the copy would have frozen any file on the disk
    # into `design/revisions/` and pointed the root's `design_refs` at it.
    source = contained_child(staging_dir(state, staging_key), source_name, "staged file name")
    with state.lock:
        if not os.path.exists(ext_path(source)) or os.path.getsize(ext_path(source)) == 0:
            raise StagingError(
                "staged design %s is missing or empty. Remedy: let the designer "
                "re-stage the self-contained preview." % source
            )
        root = state.read_item(root_id)
        # composed from the same constant the resolver reads, so "the directory a freezer writes
        # into" is one fact rather than a literal here and a tuple there
        revisions_dir = os.path.join(state.root, *ACTIVE_DIRS[DESIGN_REF_TYPE].split("/"))
        revision = _next_frozen_revision(revisions_dir, dsn_id)
        frozen = os.path.join(revisions_dir, revision_name(dsn_id, revision, ".html"))
        os.makedirs(ext_path(revisions_dir), exist_ok=True)
        shutil.copyfile(ext_path(source), ext_path(frozen))
        manifest = {
            "id": dsn_id,
            "revision": revision,
            "file_hash": _file_hash(frozen),
            "root": root_id,
            "root_revision": root.get("revision"),
            "frozen_at": _now_iso(),
        }
        # validated like the two companions, for the reason the manifest has a schema at all:
        # `root` is this item's parent binding, and `backlog_types.PARENT_FIELDS` derives the
        # reference graph from the declared contracts. An unvalidated dict would let the written
        # record and the declared contract drift, and the graph would walk the declaration.
        validate(manifest, "dsn_manifest")
        state._write_yaml_atomic(
            os.path.join(revisions_dir, revision_name(dsn_id, revision, ".yaml")), manifest
        )
        clear_staging(state, staging_key, mode="promoted", _locked=True)
        # hashed design_refs change through the kernel edit path -- invalidates
        # an existing approval atomically (spec II.6a scope-manifest semantics)
        #
        # THROUGH `field_elements`, because this line WRITES what it read: `list()` over a scalar
        # is that scalar's letters, and `_update_item_locked` then put them in the canonical item
        # (BUG-0038). It is the one site of its class that damages the STATE instead of only
        # mis-answering a question, which is why the normalisation is here and not only in the
        # readers -- `backlog_types.REFERENCE_LIST_FIELDS` carries the class.
        # `test_staging_cli.test_a_scalar_design_ref_survives_the_freeze_as_one_reference`.
        refs = field_elements(root.get("design_refs"))
        refs.append("%s/%s" % (ACTIVE_DIRS[DESIGN_REF_TYPE],
                               revision_name(dsn_id, revision, ".html")))
        updated_root = state._update_item_locked(root_id, {"design_refs": refs})
        return {"frozen": frozen, "manifest": manifest, "root": updated_root}


def clear_staging(state: ProjectState, key: str, mode: str, _locked: bool = False) -> str:
    """promoted -> EMPTY the dir; rejected -> ARCHIVE it (never silent delete)."""
    if mode not in ("promoted", "rejected"):
        raise StagingError("mode must be promoted|rejected, got %r" % mode)
    if not _locked:
        with state.lock:
            return clear_staging(state, key, mode, _locked=True)
    source = staging_dir(state, key)
    if not os.path.isdir(ext_path(source)):
        return source
    if mode == "rejected":
        year = time.strftime("%Y")
        target = os.path.join(state.archive_root(), STAGING_DIRNAME, year, key)
        os.makedirs(ext_path(os.path.dirname(target)), exist_ok=True)
        if os.path.isdir(ext_path(target)):
            raise StagingError(
                "archive target %s already exists -- refusing to overwrite. "
                "Remedy: inspect and merge manually." % target
            )
        shutil.move(ext_path(source), ext_path(target))
        return target
    shutil.rmtree(ext_path(source))
    return source

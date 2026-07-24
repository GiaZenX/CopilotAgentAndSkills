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
`harness validate`/doctor surface leftovers.
Wiring note: WHO calls freeze at mint time is phase-2 hook/orchestrator logic;
the kernel provides the operations.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import time
import xml.etree.ElementTree as ET

from .backlog_types import parse_id
from .lock import ext_path
from .schemas import validate
from .state import ProjectState, StateError, _now_iso


class StagingError(StateError):
    """Staging/freeze operation refused -- message carries the remedy."""


def staging_dir(state: ProjectState, key: str) -> str:
    return os.path.join(state.root, "staging", key)


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
    """Max-parse over EVERY file carrying the <id>.rNN. prefix (frozen file AND
    companion/manifest): a manually deleted frozen revision must never cause an
    rNN number to be REUSED (Fable-Check 11/NIT-1)."""
    highest = 0
    prefix = item_id + ".r"
    if os.path.isdir(ext_path(target_dir)):
        for name in os.listdir(ext_path(target_dir)):
            if not name.startswith(prefix):
                continue
            digits = name[len(prefix):].split(".", 1)[0]
            if digits.isdigit():
                highest = max(highest, int(digits))
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
        frozen = os.path.join(target_dir, "%s.r%02d.drawio.svg" % (wfr_id, revision))
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
            os.path.join(target_dir, "%s.r%02d.yaml" % (wfr_id, revision)), companion
        )
        clear_staging(state, staging_key, mode="promoted", _locked=True)
        state._regenerate_index_locked()
        return {"frozen": frozen, "companion": companion}


def freeze_architecture(
    state: ProjectState, staging_key: str, arc_id: str, title: str, scope: str,
    derives_from: list, approval_ref: str = None, assets: dict = None,
) -> dict:
    """Freeze staging ARC into architecture/revisions/ + active companion (II.6a)."""
    parse_id(arc_id)
    source = os.path.join(staging_dir(state, staging_key), arc_id + ".drawio.svg")
    with state.lock:
        _assert_xml_wellformed(source)
        revisions_dir = os.path.join(state.root, "architecture", "revisions")
        revision = _next_frozen_revision(revisions_dir, arc_id)
        frozen = os.path.join(revisions_dir, "%s.r%02d.drawio.svg" % (arc_id, revision))
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
    source = os.path.join(staging_dir(state, staging_key), source_name)
    with state.lock:
        if not os.path.exists(ext_path(source)) or os.path.getsize(ext_path(source)) == 0:
            raise StagingError(
                "staged design %s is missing or empty. Remedy: let the designer "
                "re-stage the self-contained preview." % source
            )
        root = state.read_item(root_id)
        revisions_dir = os.path.join(state.root, "design", "revisions")
        revision = _next_frozen_revision(revisions_dir, dsn_id)
        frozen = os.path.join(revisions_dir, "%s.r%02d.html" % (dsn_id, revision))
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
        state._write_yaml_atomic(
            os.path.join(revisions_dir, "%s.r%02d.yaml" % (dsn_id, revision)), manifest
        )
        clear_staging(state, staging_key, mode="promoted", _locked=True)
        # hashed design_refs change through the kernel edit path -- invalidates
        # an existing approval atomically (spec II.6a scope-manifest semantics)
        refs = list(root.get("design_refs") or [])
        refs.append("design/revisions/%s.r%02d.html" % (dsn_id, revision))
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
        target = os.path.join(state.root, "archive", "staging", year, key)
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

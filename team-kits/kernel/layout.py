"""WHO writes what under the state directory -- one definition, several readers.

THE DEAD END THIS EXISTS TO END, measured 2026-08-02 in a scaffolded dev project: every write
route into `project_memory/` was refused with "only the kernel writes it", and for
`product/masterplan.md`, `project_config.yaml` and (office) `filing_plan.yaml` the kernel has no
writer and never will -- they are prose and configuration, not typed items. Meanwhile
`gate_memory_complete` blocks merge and push while the masterplan still carries its template line.
A gate whose condition no reachable operation can satisfy is not enforcement, it is a wall.

THE PROPERTY, not the three file names. The state directory holds two kinds of file:

  * CANONICAL STATE -- everything a KERNEL WRITER produces. Its name is composed by a kernel path
    builder out of a kernel-allocated id, its content goes through the status automaton, the
    approval hashes and the index. A tool write here really would bypass all three, and
    `approvals/pending/**` in particular holds mint codes in cleartext.
  * KIT DOCUMENTS -- the prose and configuration a kit ships into `templates/project_memory/`.
    No kernel path builder can name one, so no kernel command can write one; they are ordinary
    project files that happen to live under the state directory, and they are scoped like
    ordinary project files.

`kernel_written_subtrees` answers the first half by ASKING THE WRITERS' OWN PATH BUILDERS with a
probe id, rather than by listing directories: `state.active_path`, `state.archive_path`,
`state.generated_path`, `approvals._request_path`, `dispatch._lease_path`,
`dispatch._envelope_path`, `staging.architecture_revisions_dir`. A writer that starts landing
somewhere new is a writer whose builder is asked here too.

That claim is MEASURED rather than asserted: `test_every_kernel_writer_lands_inside_the_declared
_area` in `tools/test_kernel.py` drives capture, freeze, lease, submit, mint, revoke, archive and
index regeneration in a real state directory and requires every file they create to answer
`is_kernel_written`. It goes red the day a writer lands outside, which is the only way this
module's definition can stay true.

WHAT IS DELIBERATELY NOT A DOCUMENT, and why the two exclusions are properties rather than names:
  * a DOTTED path segment -- `.kernel.lock`, `.audit/hook_events.jsonl`, `.gitkeep`. Nothing whose
    name begins with a dot is content a role writes; those are machinery, and the audit log in
    particular is the evidence the repeat-block escalation counts.
  * `staging/` -- spec II.4's explicitly non-canonical proposal area. It is not a document either:
    it has its OWN per-task-key rule in the write-scope gate, and answering "document" here would
    replace that rule with a weaker one.
"""
from __future__ import annotations

import os

from .backlog_types import ACTIVE_DIRS, format_id
from .state import ProjectState

# spec II.4's Vorschlagsbereich -- named once, read by `is_project_document` and by the gate
STAGING_DIRNAME = "staging"

# Probe values handed to the path builders. They name nothing that has to exist: a path builder
# composes a name, it does not open a file, so `TSK-0001` and a zero request id are enough to make
# every builder say WHERE it writes.
_PROBE_TASK_ID = "TSK-0001"
_PROBE_REQUEST_ID = "0" * 32
_PROBE_YEAR = 1970


def _relative(root: str, path: str) -> str:
    """`path` relative to the state root, lower-cased with forward slashes.

    Lower-cased because the FS on Windows and APFS are case-insensitive while a lexical
    comparison is not -- `gate_write_scope._norm` folds for exactly that reason, and a predicate
    that answered differently from the gate that calls it would be a hole with a docstring on it.
    """
    return os.path.relpath(path, root).replace("\\", "/").lower()


def kernel_written_subtrees(root: str) -> tuple:
    """Every state-relative DIRECTORY a kernel writer lands a file in, sorted.

    Asked of the builders themselves (see the module docstring). `root` only decides what the
    answers are made relative to; nothing here touches the disk.
    """
    # Local import: `approvals`, `dispatch` and `staging` all import `state`, and this module
    # imports them -- keeping it inside the call keeps the package's import graph a tree.
    from . import approvals, dispatch, staging

    state = ProjectState(root)
    # DIRECTORY builders answer with the directory itself; FILE builders answer with a file whose
    # dirname is taken below. `archive_root` is in the first group deliberately: `archive_path`
    # keys by type AND year, so a probe of it would declare `archive/pr/1970` canonical and leave
    # every real year outside.
    directories = {state.archive_root(), staging.architecture_revisions_dir(state)}
    paths = set()
    for item_type in ACTIVE_DIRS:
        probe = format_id(item_type, 1)
        paths.add(state.active_path(probe))
    paths.add(state.generated_path("index.yaml"))
    for flags in ({}, {"consumed": True}, {"revoked": True}):
        paths.add(approvals._request_path(state, _PROBE_REQUEST_ID, **flags))
    paths.add(dispatch._lease_path(state, _PROBE_TASK_ID))
    paths.add(dispatch._envelope_path(state, _PROBE_TASK_ID))
    directories.update(os.path.dirname(path) for path in paths)
    return tuple(sorted(_relative(state.root, directory) for directory in directories))


def is_kernel_written(root: str, relative_path: str) -> bool:
    """Does this state-relative path lie in an area a kernel writer produces?"""
    rel = str(relative_path or "").replace("\\", "/").strip("/").lower()
    if not rel:
        return True                       # the state directory itself is not a document
    for subtree in kernel_written_subtrees(root):
        if rel == subtree or rel.startswith(subtree + "/"):
            return True
    return False


def is_project_document(root: str, relative_path: str) -> bool:
    """Is this state-relative path a KIT DOCUMENT -- prose or config with no kernel writer?

    The complement of `is_kernel_written`, minus the two areas the module docstring names: a
    dotted segment is machinery and `staging/` has its own rule.
    """
    rel = str(relative_path or "").replace("\\", "/").strip("/").lower()
    if not rel:
        return False
    parts = rel.split("/")
    if any(part.startswith(".") for part in parts):
        return False
    if parts[0] == STAGING_DIRNAME:
        return False
    return not is_kernel_written(root, rel)

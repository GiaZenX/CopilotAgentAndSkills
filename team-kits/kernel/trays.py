#!/usr/bin/env python3
"""Which top-level directories of a kit are DOCUMENT TRAYS — one definition, one shipped record.

WHY THIS IS NOT A CONSTANT IN THE HOOK. `guard_no_adhoc` refuses ad-hoc status/summary/result
files by NAME, and that rule has to stand down inside a tray: what lands there arrives from
OUTSIDE the project (a scanned invoice) or is HANDED to a human (a draft the user sends), so its
name is not the agent's invention and is no substitute for a typed item. The first cut of that
exemption put the tray names in the hook — and the hook is byte-identical across all three kits,
so the exemption applied in kits that ship no tray at all. Measured 2026-08-01 in a dev project as
real hook processes: `archive/implementation_summary.md`, `outbox/backend_result_x.md`,
`inbox/delegation_plan.md` and `archive/notes/frontend_result_2.md` were ALLOWED by every hook the
dev settings.json starts on a `Write`; identical in research; all four rc 2 before.

WHY THE RECORD IS A SHIPPED HOOK-DIRECTORY FILE and not something a scaffold writes beside the
bundle. It is a BEHAVIOUR SOURCE — whoever writes it decides where an integrity rule stands down —
so it has to sit inside what `hook_bundle_hash` measures. Measured 2026-08-01 with the record one
level too high at `.claude/document_trays.txt`: `printf 'src' > $(echo .cl*)/document_trays.txt`
passed every registered shell gate (that command line names the enforcement layer nowhere), the
guard then allowed `docs/implementation_summary.md`, and `gate_dispatch` reported NO bundle
refusal, because the file lay outside `BUNDLE_SUBTREES`. Inside `hooks/` the same forgery moves
the bundle hash, so the trust gate refuses the next spawn.

Shipping it rather than generating it at install time also means no new scaffold step: both
scaffolds already copy every file in `<kit>/hooks/`, prune what the kit does not ship, back the
directory up and roll it back. `write_kit_state` sees a file the kit shipped, so it is neither a
stranger nor a modification.

WHAT MAKES A DIRECTORY A TRAY is what the kit SHIPS in it: nothing but a folder-guide seed. A tray
exists to be filled at runtime, so the kit can have authored none of its contents — which is
exactly what separates `inbox/`, `outbox/` and `archive/` from `scripts/` (shipped full of code)
and `.claude/` (shipped full of configuration). Measured over the shipped kits: office has three,
dev and research none.
"""
import os
import tempfile

TRAYS_FILE = "document_trays.txt"
# The stem of a folder-guide seed. A tray is allowed to ship one and nothing else; the extension
# is irrelevant (`README.txt`, `README.md`), the stem is what says "this file explains the empty
# directory it sits in" rather than "this file is content".
SIGNPOST_STEM = "readme"
# The canonical state directory. Named here because `is_tray_name` has to refuse it, and repeated
# as a literal in `guard_no_adhoc` for the reason that guard repeats every literal: it must keep
# guarding when no kernel can be imported. `test_the_two_readers_of_a_tray_name_agree` pins the
# two together over a battery that includes exactly this name.
STATE_DIRNAME = "project_memory"


def is_tray_name(name):
    """Can this string name a document tray?

    ONE PREDICATE FOR BOTH ENDS, because the two ends carried different halves of it and each half
    was a hole in the other. The stamper skipped hidden directories and the reader only dropped
    names carrying a separator, so a record saying `.claude` made `.claude/x_report.md` pass and
    one saying `project_memory` made `project_memory/staging/T-1/x_summary.md` pass — both
    measured 2026-08-01. Stated as the property instead: a tray is ONE ordinary top-level
    directory of the working tree. Not a path, not a hidden directory (nothing about a dotted name
    says "fill me with documents", and `.claude` is the enforcement layer), and not the state
    directory, whose single writer is the kernel and inside which no name rule may stand down.
    """
    text = str(name or "").strip()
    if not text or text.startswith("."):
        return False
    if "/" in text or "\\" in text:
        return False
    return text.lower() != STATE_DIRNAME


def document_trays(kit_dir):
    """Sorted tray names this kit ships in `<kit>/templates/repo`."""
    template = os.path.join(kit_dir, "templates", "repo")
    trays = []
    try:
        entries = sorted(os.listdir(template))
    except OSError:
        return trays
    for name in entries:
        directory = os.path.join(template, name)
        if not is_tray_name(name) or not os.path.isdir(directory):
            continue
        shipped = [f for _dir, _subs, files in os.walk(directory) for f in files]
        if shipped and all(os.path.splitext(f)[0].lower() == SIGNPOST_STEM for f in shipped):
            trays.append(name.lower())
    return trays


def record_path(kit_dir):
    """Where a kit keeps its tray record — inside the hook bundle, beside the guard that reads it."""
    return os.path.join(kit_dir, "hooks", TRAYS_FILE)


def stamp_document_trays(kit_dir):
    """Write `<kit>/hooks/document_trays.txt` from the kit's own template tree; return the names.

    ALWAYS WRITES, even when the list is empty. The file's PRESENCE is what the scaffold's prune
    keys on, and its absence in an installation is a bundle-hash difference like any other — so a
    kit with no tray ships an empty record rather than no record, and a kit switch replaces one
    record with the other instead of leaving the previous kit's list behind.
    """
    trays = document_trays(kit_dir)
    path = record_path(kit_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=os.path.dirname(path), prefix=TRAYS_FILE + ".")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            for name in trays:
                stream.write(name + "\n")
        os.replace(temporary, path)
    except BaseException:
        try:
            os.remove(temporary)
        except OSError:
            pass
        raise
    return trays

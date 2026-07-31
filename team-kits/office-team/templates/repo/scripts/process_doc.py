#!/usr/bin/env python3
"""
process_doc.py — render the Verfahrensdokumentation DRAFT from the PROC items.

The GoBD expect a Verfahrensdokumentation (how documents are received, processed, stored). The
office kit gets one nearly for free: every approved PROC already IS a documented procedure. This
renders docs/verfahrensdokumentation.md deterministically — a DRAFT for the Steuerberater to
review, clearly labelled as such.

Usage: python scripts/process_doc.py

THE SOURCE IS `procedures/active/PROC-nnnn.yaml`, one file per procedure. V1 read a single
`process_definitions.yaml` at the state root; V2 deleted that store, so this script raised
FileNotFoundError in every project that installed it -- a renderer that cannot run is a
Verfahrensdokumentation that does not exist. `filing_plan.yaml` is unchanged: it is reference
material, not an item store, and still lives at the state root.
"""
import datetime
import os
import sys

# see harness.py: `.claude/hooks` + `.claude/kernel` are the hashed enforcement bundle, and no
# harness process may cache bytecode into a tree the harness hashes
sys.dont_write_bytecode = True

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(REPO_ROOT, ".claude", "hooks")


def _fail(message, remedy):
    sys.stderr.write("[process_doc] %s\nRemedy: %s\n" % (message, remedy))
    return 2


def _procedures(state):
    """{id: item} for every active PROC, read through the kernel's own item reader."""
    directory = state.active_dir("PROC")
    if not os.path.isdir(directory):
        return {}
    found = {}
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".yaml"):
            continue
        try:
            item = state._read_yaml(os.path.join(directory, name))
        except Exception:
            continue
        if isinstance(item, dict):
            found[str(item.get("id") or name[:-5])] = item
    return found


def main(argv=None):
    if not os.path.isfile(os.path.join(BRIDGE, "_kernel.py")):
        return _fail("this project has no enforcement layer at %s, so the state kernel that "
                     "reads the procedures is not installed." % BRIDGE,
                     "re-run the team scaffold for this repo.")
    sys.path.insert(0, BRIDGE)
    try:
        import _kernel  # type: ignore[import-not-found]
    except BaseException as exc:  # noqa: BLE001 — a broken bridge names itself, never tracebacks
        return _fail("the hook helpers next to the kernel could not be loaded (%r)." % (exc,),
                     "a partial checkout or a half-finished kit update is the usual cause; "
                     "re-run the team scaffold for this repo.")
    _kernel.disarm()
    try:
        state = _kernel.open_state(REPO_ROOT)
    except Exception as exc:
        return _fail("the state kernel could not be reached (%s: %s)." % (type(exc).__name__, exc),
                     "run `python scripts/harness.py doctor`; it names what is missing.")

    procs = _procedures(state)
    plan = {}
    plan_path = os.path.join(state.root, "filing_plan.yaml")
    if os.path.isfile(plan_path):
        try:
            plan = state._read_yaml(plan_path) or {}
        except Exception:
            plan = {}
    if not isinstance(plan, dict):
        plan = {}

    lines = ["# Verfahrensdokumentation (ENTWURF — generiert aus den Prozessdefinitionen)", "",
             "> Entwurf zur Prüfung durch die Steuerberatung — keine Steuer- oder Rechtsberatung.",
             "> Generiert: %s · Quelle: die aktiven PROC-Items des Projekts"
             % datetime.date.today().isoformat(),
             "", "## Ablage (Aktenplan)", "",
             "Namensregel: `%s`" % (plan.get("naming_rule") or "—"), ""]
    for node in (plan.get("tree") or []):
        if isinstance(node, dict):
            lines.append("- `%s` — Belegarten: %s — Aufbewahrung: %s"
                         % (node.get("path"), ", ".join(node.get("doc_types") or []),
                            node.get("retention") or "—"))
    lines += ["", "## Prozesse", ""]
    for pid in sorted(procs):
        body = procs.get(pid) or {}
        roles = body.get("roles") or []
        lines += ["### %s — %s (%s)" % (pid, body.get("title") or "", body.get("status") or "?"),
                  "",
                  "- Auslöser: %s" % (body.get("trigger") or "—"),
                  "- Ausführende Rollen: %s" % (", ".join(str(r) for r in roles) or "—"),
                  "- Schritte:"]
        for step in (body.get("steps") or []):
            lines.append("  1. %s" % step)
        lines += ["- Ergebnisse: %s" % ", ".join(str(o) for o in (body.get("outputs") or [])),
                  "- Rückfragepunkte: %s" % ", ".join(str(a) for a in (body.get("approval_points")
                                                                       or [])),
                  ""]
    out_dir = os.path.join(REPO_ROOT, "docs")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "verfahrensdokumentation.md")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    print("[process_doc] %s written (%d processes)" % (out, len(procs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

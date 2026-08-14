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
Verfahrensdokumentation that does not exist.

THE ABLAGE SECTION IS READ THROUGH THE GATE, `.claude/hooks/gate_filing.rules`, and that import is
the point of it. This script had its own reader for a `naming_rule:` + `tree:` shape, and the gate
reads `rules:` + `path_template:` -- which is the shape the shipped template carries and the shape
the entry gate is told to write. Measured 2026-08-03 against a real 26-node Aktenplan: the gate
refused every filing ("lists no rules yet") while this renderer printed all 26 nodes, and against
the SHIPPED template it printed an em dash and an empty list while the gate refused. Two readers of
one document, each silently wrong in the other's direction. The gate wins because it is the one
with a blocking contract; there is now one reader and this script is a caller of it.

AND IT NO LONGER DEGRADES QUIETLY. An empty or unreadable plan used to render as `Namensregel: —`,
which is a Verfahrensdokumentation that omits the Ablage without saying so -- the exact document a
Steuerberater is handed to describe how filing works. It now writes the gate's OWN reason into the
section and exits 1: the file is still produced (a draft with one honest gap beats no draft), and
the exit code says it is not complete.
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


def _plain(value):
    """One field as one line of prose, whatever YAML shape it arrived in."""
    if isinstance(value, (list, tuple)):
        return ", ".join(_plain(item) for item in value)
    if isinstance(value, dict):
        return "; ".join("%s=%s" % (key, _plain(item)) for key, item in value.items())
    return str(value)


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
        # the filing plan's ONE reader (see the module docstring). Imported after `_kernel`, whose
        # import arms the exit-2 excepthook that `disarm()` below takes back off again.
        import gate_filing  # type: ignore[import-not-found]
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
    rules, reason = gate_filing.rules(REPO_ROOT)
    # HOW MANY THINGS A FIELD HOLDS, taken from the kernel that owns the field contracts rather
    # than answered again here: a bare string is ONE role and one step, and iterating it wrote
    # `r, e, c, o, r, d, s, -, c, l, e, r, k` into the Steuerberatung's document (BUG-0015).
    _elements = _kernel.kernel_module("backlog_types", REPO_ROOT).field_elements

    lines = ["# Verfahrensdokumentation (ENTWURF — generiert aus den Prozessdefinitionen)", "",
             "> Entwurf zur Prüfung durch die Steuerberatung — keine Steuer- oder Rechtsberatung.",
             "> Generiert: %s · Quelle: die aktiven PROC-Items des Projekts"
             % datetime.date.today().isoformat(),
             "", "## Ablage (Aktenplan)", ""]
    if rules is None:
        lines += ["> **UNVOLLSTÄNDIG:** %s. Dieser Entwurf beschreibt die Ablage NICHT — "
                  "`gate_filing` verweigert aus demselben Grund jede Ablage." % reason, ""]
    else:
        lines.append("Quelle: `project_memory/%s` — eine Zeile je Regel, alle Felder der Regel."
                     % gate_filing.PLAN)
        lines.append("")
        # Every field EXCEPT the path is rendered without being named: which fields a rule carries
        # is the plan's business (its header states them), and a list of them here would be a
        # second schema that goes stale the day a project adds `owner:` to its rules.
        for rule in rules:
            fields = " · ".join(
                "%s: %s" % (key, _plain(value)) for key, value in rule.items()
                if key != gate_filing.PATH_TEMPLATE and value not in (None, "", [], {}))
            lines.append("- `%s`%s" % (rule.get(gate_filing.PATH_TEMPLATE),
                                       " — " + fields if fields else ""))
    lines += ["", "## Prozesse", ""]
    for pid in sorted(procs):
        body = procs.get(pid) or {}
        lines += ["### %s — %s (%s)" % (pid, body.get("title") or "", body.get("status") or "?"),
                  "",
                  "- Auslöser: %s" % (_plain(_elements(body.get("trigger"))) or "—"),
                  "- Ausführende Rollen: %s" % (_plain(_elements(body.get("roles"))) or "—"),
                  "- Schritte:"]
        for step in _elements(body.get("steps")):
            lines.append("  1. %s" % _plain(step))
        lines += ["- Ergebnisse: %s" % _plain(_elements(body.get("outputs"))),
                  "- Rückfragepunkte: %s" % _plain(_elements(body.get("approval_points"))),
                  ""]
    out_dir = os.path.join(REPO_ROOT, "docs")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "verfahrensdokumentation.md")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    print("[process_doc] %s written (%d processes)" % (out, len(procs)))
    if rules is None:
        sys.stderr.write(
            "[process_doc] the Ablage section is EMPTY: %s. The draft was written and says so; "
            "it is not complete until the filing plan carries rules.\n" % reason)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

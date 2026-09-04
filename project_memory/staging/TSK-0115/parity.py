"""MEASURE: do kernel/board.py and the dev-team generate_dashboard.py disagree on the same numbers?

Both are run against the SAME copy of the main repo's project_memory (rig.build), through their
real entry points (ProjectState.generate_index writes index+board; scripts/generate_dashboard.py
reads that index). Then the two pages are parsed -- the board as DOM, the dashboard as the JSON
block its page script reads -- and every quantity both express is compared. Three perturbations
of the archive follow, because that is the one place each page counts on its own.

Output: a markdown report on stdout (copied into the design package by hand, with the numbers).
"""
import json
import os
import re
import shutil
import sys
from html.parser import HTMLParser

import rig

sys.dont_write_bytecode = True
from kernel.backlog_types import AUTOMATA  # noqa: E402  (rig put team-kits on sys.path)

RIG = os.path.join(rig.SCRATCH, "rig")
SOURCE_PM = os.path.join(rig.MAIN, "project_memory")

# The dev-team generator's own curation, read from the module it ships rather than retyped: the
# comparison needs to know which kernel types each dev view sums.
sys.path.insert(0, os.path.join(rig.TEAM_KITS, "dev-team", "templates", "repo", "scripts"))


class Board(HTMLParser):
    """The numbers the kernel board's page carries, read off its DOM attributes."""

    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.type_items = {}       # {type: data-items}
        self.columns = {}          # {(type, status): data-count}
        self.tabs = {}             # {tab: count}
        self.archived_total = None
        self.archived_text = ""
        self.generated_at = None
        self.cards = []            # [(type, status, id, classes)]
        self.warnings = []
        self._type = None
        self._status = None
        self._tab = None
        self._in_count = False
        self._in_archived = False
        self._in_warning = False
        self._buf = ""
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "")
        if tag == "section" and cls == "type":
            self._type = a["data-type"]
            self.type_items[self._type] = int(a["data-items"])
        elif tag == "div" and cls.startswith("column"):
            self._status = a["data-status"]
            self.columns[(self._type, self._status)] = int(a["data-count"])
        elif tag == "button" and cls == "card":
            self.cards.append((self._type, self._status, a["data-open"], cls))
        elif tag == "button" and cls == "tab":
            self._tab = a["data-tab"]
        elif tag == "span" and cls == "count" and self._tab:
            self._in_count = True
        elif tag == "span" and cls == "archived":
            self.archived_total = int(a["data-archived"])
            self._in_archived = True
        elif tag == "time" and "data-generated-at" in a:
            self.generated_at = a["data-generated-at"]
        elif tag == "li" and "data-warning" in a:
            self._in_warning = True
            self._buf = ""

    def handle_data(self, data):
        if self._in_count:
            self.tabs[self._tab] = int(data.strip())
            self._in_count = False
            self._tab = None
        if self._in_archived:
            self.archived_text += data
        if self._in_warning:
            self._buf += data

    def handle_endtag(self, tag):
        if tag == "span" and self._in_archived:
            self._in_archived = False
        if tag == "li" and self._in_warning:
            self.warnings.append(self._buf.strip())
            self._in_warning = False


def dashboard_data(pm):
    html = open(os.path.join(pm, "generated", "dashboard.html"), encoding="utf-8").read()
    block = re.search(r'<script type="application/json" id="dashboard-data">(.*?)</script>',
                      html, re.DOTALL).group(1)
    return json.loads(block.replace("<\\/", "</"))


def run_both(pm):
    rig.kernel_index(pm)
    r = rig.dev_dashboard(RIG)
    if r.returncode != 0:
        raise SystemExit("dashboard failed: %s%s" % (r.stdout, r.stderr))
    board = Board(open(os.path.join(pm, "generated", "board.html"), encoding="utf-8").read())
    return board, dashboard_data(pm), r.stdout.strip()


def kernel_archive_by_type(board):
    return dict((m.group(1), int(m.group(2))) for m in re.finditer(r"([A-Z]{2,4}) (\d+)", board.archived_text))


def compare(board, data, label):
    import generate_dashboard as gd
    lines = ["", "### %s" % label, ""]
    lines.append("| Größe | kernel/board.py | generate_dashboard.py | gleich? |")
    lines.append("|---|---|---|---|")
    # 1. per dev view: the sum of the kernel's per-type counts (minus terminals where the view hides them)
    views = {v["id"]: v for v in data["views"]}
    for view in gd.VIEWS:
        expected = 0
        for t in view.types:
            for (typ, status), n in board.columns.items():
                if typ != t:
                    continue
                if view.hide_done and status in getattr(AUTOMATA.get(t), "terminals", frozenset()):
                    continue
                expected += n
        got = views.get(view.id, {}).get("total")
        lines.append("| Summe Ansicht `%s` (%s%s) | %s | %s | %s |" % (
            view.label, "+".join(view.types), ", ohne terminale" if view.hide_done else "",
            expected, got, "ja" if expected == got else "**NEIN**"))
    # 2. per-item status for every item the dashboard carries (it caps at 50 per view)
    kernel_status = {card[2]: card[1] for card in board.cards}
    dash_items = {it["id"]: it for v in data["views"] for it in v["items"]}
    mism = [(i, kernel_status.get(i), it["status"]) for i, it in dash_items.items()
            if kernel_status.get(i) != it["status"]]
    lines.append("| Status je Item (%d Items, die das Dashboard trägt) | — | — | %s |" % (
        len(dash_items), "ja, 0 Abweichungen" if not mism else "**NEIN** %r" % mism[:5]))
    # 3. blocked: rows the index flags vs what each face shows
    dash_blocked = sorted(i for i, it in dash_items.items() if it.get("blocked_by"))
    lines.append("| Items mit `blocked_by` (Dashboard-Payload) | kein Merkmal auf der Karte (Klasse `card` trägt keins) | %d %s | Board zeigt es nur im Detail-Feldkatalog |" % (
        len(dash_blocked), dash_blocked[:6]))
    # 4. archive
    kt = kernel_archive_by_type(board)
    dt = {t: sum(years.values()) for t, years in data["archive"]["by_type"].items()}
    lines.append("| Archiv gesamt | %s | %s | %s |" % (board.archived_total, data["archive"]["total"],
                                                    "ja" if board.archived_total == data["archive"]["total"] else "**NEIN**"))
    lines.append("| Archiv je Typ | %s | %s | %s |" % (kt, dt, "ja" if kt == dt else "**NEIN**"))
    # 5. tab counts vs total rows
    total_rows = sum(board.type_items.values())
    dash_rows = sum(v["total"] for v in data["views"])
    lines.append("| Aktive Items gesamt | Board-Reiter %d (Sektionen %d) | Summe der Ansichten %d (Delivery ohne terminale) | %s |" % (
        board.tabs.get("board"), total_rows, dash_rows, "ja" if board.tabs.get("board") == total_rows else "**NEIN**"))
    # 6. timestamps
    lines.append("| Zeitstempel | %s (einer für Index+Board) | %s (eigene Uhr beim Lauf) | %s |" % (
        board.generated_at, data["generated_at"], "ja" if board.generated_at == data["generated_at"] else "**NEIN** (zwei Auslöser)"))
    return lines


def perturb(pm, name):
    """Add one file to the archive that only one of the two counters sees."""
    if name == "archive/staging":
        # the layout `staging.clear_staging(mode="rejected")` really writes: archive/staging/<year>/<key>/
        d = os.path.join(pm, "archive", "staging", "2026", "TSK-0999")
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "proposal.yaml"), "w").write("id: proposal\n")
    elif name == "non-id yaml under TSK":
        open(os.path.join(pm, "archive", "TSK", "2026", "notes.yaml"), "w").write("note: x\n")
    elif name == "BUG id under archive/TSK":
        open(os.path.join(pm, "archive", "TSK", "2026", "BUG-0999.yaml"), "w").write("id: BUG-0999\n")


def main():
    out = ["# Parität kernel/board.py gegen generate_dashboard.py", "",
           "Beide gegen dieselbe Kopie von `project_memory/` des Hauptrepos (Stand der Kopie: %s), Code aus dem Worktree g3-board." % rig.MAIN]
    pm = rig.build(RIG, SOURCE_PM)
    board, data, stdout = run_both(pm)
    out.append("")
    out.append("Dashboard-stdout: `%s`" % stdout.splitlines()[0])
    out.append("Board-Reiter: %s; Archiv-Text: `%s`" % (board.tabs, board.archived_text.strip()))
    out.append("Board-Sektionen (data-items): %s" % board.type_items)
    out.append("Board-Warnungen: %d" % len(board.warnings))
    out += compare(board, data, "Unverändertes Archiv")
    for name in ("archive/staging", "non-id yaml under TSK", "BUG id under archive/TSK"):
        perturb(pm, name)
        board, data, _ = run_both(pm)
        out += compare(board, data, "Störung: %s (kumulativ)" % name)
    text = "\n".join(out)
    print(text)
    with open(os.path.join(rig.SCRATCH, "parity-result.md"), "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    shutil.copy(os.path.join(pm, "generated", "board.html"), os.path.join(rig.SCRATCH, "board-current.html"))
    shutil.copy(os.path.join(pm, "generated", "dashboard.html"), os.path.join(rig.SCRATCH, "dashboard-current.html"))


if __name__ == "__main__":
    main()

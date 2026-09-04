"""Which half of the M-1 rule carries the fix -- measured, not assumed."""
import io
import os
import shutil
import subprocess
import sys

SRC = "C:/Offline Repos/v2-testbed/_worktrees/g3-board"
COPY = "C:/Offline Repos/v2-testbed/_round-scratch/TSK-0115/rework1/halves"
BOARD = os.path.join(COPY, "team-kits", "kernel", "board.py")
MINW = ".node-face > *, .focus-list .rec > *, .ms-face > *, .card > * { min-width: 0; }"
WRAP = (".node-face .title, .rec .title, .rec .note, .ms-face .title, .card .title, .goals {\n"
        "  overflow-wrap: anywhere; }")

if os.path.isdir(COPY):
    shutil.rmtree(COPY)
shutil.copytree(SRC, COPY, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
if os.path.isfile(os.path.join(COPY, ".git")):
    os.remove(os.path.join(COPY, ".git"))
original = io.open(BOARD, encoding="utf-8").read()

for label, drop in (("both halves in place", []), ("without min-width", [MINW]),
                    ("without overflow-wrap", [WRAP]), ("without either", [MINW, WRAP])):
    text = original
    for one in drop:
        assert one in text, one[:40]
        text = text.replace(one, "/* dropped */", 1)
    io.open(BOARD, "w", encoding="utf-8", newline="\n").write(text)
    run = subprocess.run([sys.executable, "-B",
                          "C:/Offline Repos/v2-testbed/_round-scratch/TSK-0115/rework1/probe_m1.py"],
                         env=dict(os.environ, PROBE_TREE=COPY), capture_output=True, text=True,
                         timeout=900)
    worst = [line for line in run.stdout.splitlines() if line.startswith("worst")]
    print("%-24s %s" % (label, worst[0] if worst else run.stdout[-200:]))
io.open(BOARD, "w", encoding="utf-8", newline="\n").write(original)
print("copy restored")

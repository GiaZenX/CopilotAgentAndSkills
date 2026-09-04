"""N-10: how much of the memory budget's margin the fixture DEPTH is responsible for."""
import io
import os
import shutil
import subprocess
import sys

SRC = "C:/Offline Repos/v2-testbed/_worktrees/g3-board"
COPY = "C:/Offline Repos/v2-testbed/_round-scratch/TSK-0115/rework1/n10copy"
BOARD = os.path.join(COPY, "team-kits", "kernel", "board.py")
PROBE = "C:/Offline Repos/v2-testbed/_round-scratch/TSK-0115/rework1/probe_m3.py"
FIELDS = {"kind": ('"kind": _flat(request.get("kind")) or "?",',
                   '"kind": str(request.get("kind") or "") or "?",'),
          "item": ('"item": _flat(request.get("item")),',
                   '"item": str(request.get("item") or ""),')}

if os.path.isdir(COPY):
    shutil.rmtree(COPY)
shutil.copytree(SRC, COPY, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
if os.path.isfile(os.path.join(COPY, ".git")):
    os.remove(os.path.join(COPY, ".git"))
board_src = io.open(BOARD, encoding="utf-8").read()
probe_src = io.open(PROBE, encoding="utf-8").read()
probe_copy = os.path.join(COPY, "probe.py")

for depth in (18, 21):
    io.open(probe_copy, "w", encoding="utf-8", newline="\n").write(
        probe_src.replace("range(1, 21)", "range(1, %d)" % depth))
    for field, (fixed, defect) in FIELDS.items():
        io.open(BOARD, "w", encoding="utf-8", newline="\n").write(
            board_src.replace(fixed, defect, 1))
        run = subprocess.run([sys.executable, "-B", probe_copy],
                             env=dict(os.environ, PROBE_TREE=COPY), capture_output=True,
                             text=True, timeout=1800)
        line = [one for one in run.stdout.splitlines() if one.startswith(field)]
        print("depth %2d, bound dropped on %-5s -> %s" % (depth, field,
                                                          line[0] if line else run.stdout[-160:]))
io.open(BOARD, "w", encoding="utf-8", newline="\n").write(board_src)
print("copy restored")

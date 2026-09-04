"""The cost of the SAME files with the bound dropped on one field at a time."""
import io
import os
import shutil
import subprocess
import sys

SRC = "C:/Offline Repos/v2-testbed/_worktrees/g3-board"
COPY = "C:/Offline Repos/v2-testbed/_round-scratch/TSK-0115/rework1/m3copy"
BOARD = os.path.join(COPY, "team-kits", "kernel", "board.py")
FIELDS = {
    "request_id": ('"request_id": _flat(request.get("request_id")) or',
                   '"request_id": str(request.get("request_id") or "") or'),
    "kind": ('"kind": _flat(request.get("kind")) or "?",',
             '"kind": str(request.get("kind") or "") or "?",'),
    "item": ('"item": _flat(request.get("item")),',
             '"item": str(request.get("item") or ""),'),
}
if os.path.isdir(COPY):
    shutil.rmtree(COPY)
shutil.copytree(SRC, COPY, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
if os.path.isfile(os.path.join(COPY, ".git")):
    os.remove(os.path.join(COPY, ".git"))
original = io.open(BOARD, encoding="utf-8").read()
for field, (fixed, defect) in FIELDS.items():
    assert fixed in original, field
    io.open(BOARD, "w", encoding="utf-8", newline="\n").write(
        original.replace(fixed, defect, 1))
    run = subprocess.run(
        [sys.executable, "-B",
         "C:/Offline Repos/v2-testbed/_round-scratch/TSK-0115/rework1/probe_m3.py"],
        env=dict(os.environ, PROBE_TREE=COPY), capture_output=True, text=True, timeout=1800)
    line = [one for one in run.stdout.splitlines() if one.startswith(field)]
    print("bound dropped on %-11s -> %s" % (field, line[0] if line else run.stdout[-200:]))
io.open(BOARD, "w", encoding="utf-8", newline="\n").write(original)
print("copy restored")

"""N-13 and N-14: which assertion actually catches what, at the request-file test."""
import io
import os
import re
import shutil
import subprocess
import sys

SRC = "C:/Offline Repos/v2-testbed/_worktrees/g3-board"
COPY = "C:/Offline Repos/v2-testbed/_round-scratch/TSK-0115/rework1/n13copy"
TEST = os.path.join(COPY, "tools", "test_board.py")
BOARD = os.path.join(COPY, "team-kits", "kernel", "board.py")
NODE = ("tools/test_board.py::test_a_request_file_nothing_could_write"
        "_costs_neither_the_page_nor_the_write")

ARRIVAL = re.compile(r"    # THE FIXTURE HAS TO ARRIVE\..*?sorted\(parsed\)\n", re.DOTALL)
MEMORY = re.compile(r"    assert peak < _MEMORY_BUDGET, \(\n.*?\n.*?\n", re.DOTALL)
KIND_FIX = '"kind": _flat(request.get("kind")) or "?",'
KIND_BAD = '"kind": str(request.get("kind") or "") or "?",'
ITEM_FIX = '"item": _flat(request.get("item")),'
ITEM_BAD = '"item": str(request.get("item") or ""),'

if os.path.isdir(COPY):
    shutil.rmtree(COPY)
shutil.copytree(SRC, COPY, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
if os.path.isfile(os.path.join(COPY, ".git")):
    os.remove(os.path.join(COPY, ".git"))
test_src = io.open(TEST, encoding="utf-8").read()
board_src = io.open(BOARD, encoding="utf-8").read()
assert ARRIVAL.search(test_src) and MEMORY.search(test_src)


def run(test_text, board_text, label):
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(test_text)
    io.open(BOARD, "w", encoding="utf-8", newline="\n").write(board_text)
    out = subprocess.run([sys.executable, "-B", "-m", "pytest", NODE, "-q", "--no-header",
                          "-p", "no:cacheprovider"], cwd=COPY, capture_output=True, text=True,
                         timeout=1800)
    tail = [one for one in out.stdout.splitlines() if "passed" in one or "failed" in one]
    print("%-58s %s" % (label, tail[-1] if tail else out.stdout[-160:]))


bombs_loose = board_src.replace(KIND_FIX, KIND_BAD, 1).replace(ITEM_FIX, ITEM_BAD, 1)
# N-13: does the arrival block catch anything the rest does not?
run(test_src, board_src, "N-13 everything in place")
run(ARRIVAL.sub("", test_src), board_src, "N-13 without the arrival block")
run(test_src, bombs_loose, "N-13 bombs loose, arrival block in place")
run(ARRIVAL.sub("", test_src), bombs_loose, "N-13 bombs loose, no arrival block")
# N-14: does the memory bound catch anything the page-size bound does not, at this call site?
run(MEMORY.sub("", test_src), bombs_loose, "N-14 bombs loose, no memory bound")
run(MEMORY.sub("", test_src), board_src, "N-14 no memory bound, code fixed")
io.open(TEST, "w", encoding="utf-8", newline="\n").write(test_src)
io.open(BOARD, "w", encoding="utf-8", newline="\n").write(board_src)
print("copy restored")

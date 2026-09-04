"""N-12: a weak fixture must fail as a FIXTURE, not pass as a product."""
import io
import os
import re
import shutil
import subprocess
import sys

SRC = "C:/Offline Repos/v2-testbed/_worktrees/g3-board"
COPY = "C:/Offline Repos/v2-testbed/_round-scratch/TSK-0115/rework1/n12copy"
TEST = os.path.join(COPY, "tools", "test_board.py")
BOARD = os.path.join(COPY, "team-kits", "kernel", "board.py")
NODE = ("tools/test_board.py::test_a_request_file_nothing_could_write"
        "_costs_neither_the_page_nor_the_write")
STRENGTH = re.compile(r"        flattened = _flattened_length.*?\(flattened, plain\)\)\n", re.DOTALL)
KIND = ('"kind": _flat(request.get("kind")) or "?",', '"kind": str(request.get("kind") or "") or "?",')
ITEM = ('"item": _flat(request.get("item")),', '"item": str(request.get("item") or ""),')

if os.path.isdir(COPY):
    shutil.rmtree(COPY)
shutil.copytree(SRC, COPY, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
if os.path.isfile(os.path.join(COPY, ".git")):
    os.remove(os.path.join(COPY, ".git"))
test_src = io.open(TEST, encoding="utf-8").read()
board_src = io.open(BOARD, encoding="utf-8").read()
assert STRENGTH.search(test_src)
loose = board_src.replace(KIND[0], KIND[1], 1).replace(ITEM[0], ITEM[1], 1)


def run(levels, with_strength, board_text, label):
    text = test_src.replace("_BOMB_LEVELS = 21", "_BOMB_LEVELS = %d" % levels, 1)
    if not with_strength:
        text = STRENGTH.sub("", text)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    io.open(BOARD, "w", encoding="utf-8", newline="\n").write(board_text)
    out = subprocess.run([sys.executable, "-B", "-m", "pytest", NODE, "-q", "--no-header",
                          "-p", "no:cacheprovider"], cwd=COPY, capture_output=True, text=True,
                         timeout=1800)
    tail = [one for one in out.stdout.splitlines() if "passed" in one or "failed" in one]
    said = [one for one in out.stdout.splitlines() if "could not even double" in one]
    print("%-56s %s%s" % (label, tail[-1] if tail else "?",
                          "   <- the fixture said so" if said else ""))


run(8, False, loose, "levels 8, no strength check, both defences removed")
run(3, False, loose, "levels 3, no strength check, both defences removed")
run(8, True, loose, "levels 8, WITH strength check, both defences removed")
run(3, True, loose, "levels 3, WITH strength check, both defences removed")
run(21, True, board_src, "levels 21, WITH strength check, code fixed")
io.open(TEST, "w", encoding="utf-8", newline="\n").write(test_src)
io.open(BOARD, "w", encoding="utf-8", newline="\n").write(board_src)
print("copy restored")

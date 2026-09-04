"""N-13: with the fixture derivation broken, does the arrival block change WHAT fails or IF?"""
import io
import os
import re
import shutil
import subprocess
import sys

SRC = "C:/Offline Repos/v2-testbed/_worktrees/g3-board"
COPY = "C:/Offline Repos/v2-testbed/_round-scratch/TSK-0115/rework1/n13bcopy"
TEST = os.path.join(COPY, "tools", "test_board.py")
NODE = ("tools/test_board.py::test_a_request_file_nothing_could_write"
        "_costs_neither_the_page_nor_the_write")
ARRIVAL = re.compile(r"    # THE FIXTURE HAS TO ARRIVE\..*?sorted\(parsed\)\n", re.DOTALL)

if os.path.isdir(COPY):
    shutil.rmtree(COPY)
shutil.copytree(SRC, COPY, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
if os.path.isfile(os.path.join(COPY, ".git")):
    os.remove(os.path.join(COPY, ".git"))
src = io.open(TEST, encoding="utf-8").read()
broken = src.replace("for level in range(1, _BOMB_LEVELS):", "for level in range(1, 18):", 1)
broken = broken.replace('lines.append("%s: *a%d" % (field, _BOMB_LEVELS - 1))',
                        'lines.append("%s: *a20" % field)', 1)
assert broken != src

for label, text in (("derivation broken, arrival block in place", broken),
                    ("derivation broken, arrival block removed", ARRIVAL.sub("", broken))):
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    out = subprocess.run([sys.executable, "-B", "-m", "pytest", NODE, "-q", "--no-header",
                          "-p", "no:cacheprovider"], cwd=COPY, capture_output=True, text=True,
                         timeout=900)
    tail = [one for one in out.stdout.splitlines() if "passed" in one or "failed" in one]
    which = sorted({one.split("assert")[0].strip()[:60]
                    for one in out.stdout.splitlines() if one.startswith("E ")})
    print("%-46s %s" % (label, tail[-1] if tail else "?"))
    for one in which[:3]:
        print("        %s" % one)
io.open(TEST, "w", encoding="utf-8", newline="\n").write(src)
print("copy restored")

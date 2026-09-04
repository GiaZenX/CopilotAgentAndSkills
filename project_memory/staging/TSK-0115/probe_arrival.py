"""Does the new arrival assertion fire when the fixture stops delivering its attack?"""
import io
import os
import shutil
import subprocess
import sys

SRC = "C:/Offline Repos/v2-testbed/_worktrees/g3-board"
COPY = "C:/Offline Repos/v2-testbed/_round-scratch/TSK-0115/rework1/arrivalcopy"
TEST = os.path.join(COPY, "tools", "test_board.py")
NODE = ("tools/test_board.py::test_a_request_file_nothing_could_write"
        "_costs_neither_the_page_nor_the_write")
if os.path.isdir(COPY):
    shutil.rmtree(COPY)
shutil.copytree(SRC, COPY, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
if os.path.isfile(os.path.join(COPY, ".git")):
    os.remove(os.path.join(COPY, ".git"))
original = io.open(TEST, encoding="utf-8").read()

cases = {
    "the derivation put back as a literal, loop lowered":
        [("for level in range(1, _BOMB_LEVELS):", "for level in range(1, 18):"),
         ('lines.append("%s: *a%d" % (field, _BOMB_LEVELS - 1))', 'lines.append("%s: *a20" % field)')],
    "untouched": [],
}
for label, edits in cases.items():
    text = original
    for old, new in edits:
        assert old in text, old[:40]
        text = text.replace(old, new, 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    run = subprocess.run([sys.executable, "-B", "-m", "pytest", NODE, "-q", "--no-header",
                          "-p", "no:cacheprovider"], cwd=COPY, capture_output=True, text=True,
                         timeout=900)
    tail = [one for one in run.stdout.splitlines() if "passed" in one or "failed" in one]
    print("%-52s %s" % (label, tail[-1] if tail else run.stdout[-200:]))
io.open(TEST, "w", encoding="utf-8", newline="\n").write(original)
print("copy restored")

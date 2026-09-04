"""M-4: the seam as §7.5 wrote it, applied literally in a copy outside the repo."""
import io
import os
import shutil
import subprocess
import sys

SRC = "C:/Offline Repos/v2-testbed/_worktrees/g3-board"
COPY = "C:/Offline Repos/v2-testbed/_round-scratch/TSK-0115/rework1/m4copy"
APPR = os.path.join(COPY, "team-kits", "kernel", "approvals.py")
NODES = [
    "tools/test_hooks_v2.py::test_the_approval_hook_speaks_on_the_channels_this_record_measured",
    "tools/test_hooks_v2.py::test_an_expired_request_is_not_open_and_a_reworded_relay_goes_silent",
    "tools/test_board.py::test_the_board_and_the_session_brief_agree_on_the_open_requests",
]

if os.path.isdir(COPY):
    shutil.rmtree(COPY)
shutil.copytree(SRC, COPY, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
if os.path.isfile(os.path.join(COPY, ".git")):
    os.remove(os.path.join(COPY, ".git"))
original = io.open(APPR, encoding="utf-8").read()

for label, signature in (("as the seam was written: a REQUIRED second argument",
                          "def open_requests(state: ProjectState, now) -> list:"),
                         ("as it has to be written: an OPTIONAL one",
                          "def open_requests(state: ProjectState, now=None) -> list:")):
    io.open(APPR, "w", encoding="utf-8", newline="\n").write(
        original.replace("def open_requests(state: ProjectState) -> list:", signature, 1))
    print("\n--- %s" % label)
    for node in NODES:
        run = subprocess.run([sys.executable, "-B", "-m", "pytest", node, "-q", "--no-header",
                              "-p", "no:cacheprovider"], cwd=COPY, capture_output=True, text=True,
                             timeout=900)
        tail = [one for one in run.stdout.splitlines() if "passed" in one or "failed" in one]
        print("    %-70s %s" % (node.split("::")[-1][:70], tail[-1] if tail else "?"))
io.open(APPR, "w", encoding="utf-8", newline="\n").write(original)
print("\ncopy restored")

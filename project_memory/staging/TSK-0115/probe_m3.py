"""M-3: what one request file costs per FIELD, before and after -- allocation and wall clock."""
import os
import shutil
import sys
import time
import tracemalloc

sys.dont_write_bytecode = True
WT = os.environ.get("PROBE_TREE", "C:/Offline Repos/v2-testbed/_worktrees/g3-board")
sys.path.insert(0, os.path.join(WT, "team-kits"))
from kernel.state import ProjectState                      # noqa: E402

HERE = "C:/Offline Repos/v2-testbed/_round-scratch/TSK-0115/rework1"
PR = {"title": "x", "class": "normal", "problem": "p", "goal": "g",
      "acceptance_criteria": [{"id": "AC-1", "text": "t"}], "invariants": [],
      "out_of_scope": ["z"], "priority": "high"}


def bomb(field):
    plain = {"request_id": "r1", "kind": "scope", "item": "PR-0001"}
    plain.pop(field)
    lines = ["%s: %s" % (k, v) for k, v in sorted(plain.items())]
    lines += ["expires_at_epoch: 4102444800", "a0: &a0 [x, x]"]
    for level in range(1, 21):
        lines.append("a%d: &a%d [*a%d, *a%d]" % (level, level, level - 1, level - 1))
    lines.append("%s: *a20" % field)
    return "\n".join(lines) + "\n"


def one(label, text):
    root = os.path.join(HERE, "m3-" + label)
    if os.path.isdir(root):
        shutil.rmtree(root)
    os.makedirs(os.path.join(root, "project_memory"))
    state = ProjectState(os.path.join(root, "project_memory"))
    state.capture("PR", PR)
    page = os.path.join(state.root, "generated", "board.html")
    plain_size = os.path.getsize(page)
    if text is not None:
        pending = os.path.join(state.root, "approvals", "pending")
        os.makedirs(pending, exist_ok=True)
        with open(os.path.join(pending, "r1.yaml"), "w", encoding="utf-8") as fh:
            fh.write(text)
    tracemalloc.start()
    started = time.time()
    state.capture("PR", dict(PR, title="second"))
    took = time.time() - started
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    print("%-14s %6.2f s | peak %9.2f MB | page %12d B (plain %d)"
          % (label, took, peak / 1024.0 / 1024, os.path.getsize(page), plain_size))


one("no request", None)
for field in ("item", "request_id", "kind"):
    one(field, bomb(field))

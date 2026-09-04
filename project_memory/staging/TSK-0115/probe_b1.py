"""B-1 before/after: a pending request file the kernel cannot write, on the shipped renderer."""
import os
import shutil
import sys
import time

sys.dont_write_bytecode = True
WT = os.environ.get("PROBE_TREE", "C:/Offline Repos/v2-testbed/_worktrees/g3-board")
sys.path.insert(0, os.path.join(WT, "team-kits"))
from kernel.state import ProjectState                      # noqa: E402

HERE = "C:/Offline Repos/v2-testbed/_round-scratch/TSK-0115/rework1"
PR = {"title": "x", "class": "normal", "problem": "p", "goal": "g",
      "acceptance_criteria": [{"id": "AC-1", "text": "t"}], "invariants": [],
      "out_of_scope": ["z"], "priority": "high"}


def bomb_text():
    lines = ["request_id: r1", "kind: scope", "expires_at_epoch: 4102444800", "a0: &a0 [x, x]"]
    for level in range(1, 21):
        lines.append("a%d: &a%d [*a%d, *a%d]" % (level, level, level - 1, level - 1))
    lines.append("item: *a20")
    return "\n".join(lines) + "\n"


def one(label, text):
    root = os.path.join(HERE, "store-" + label)
    if os.path.isdir(root):
        shutil.rmtree(root)
    os.makedirs(os.path.join(root, "project_memory"))
    state = ProjectState(os.path.join(root, "project_memory"))
    state.capture("PR", PR)
    pending = os.path.join(state.root, "approvals", "pending")
    os.makedirs(pending, exist_ok=True)
    with open(os.path.join(pending, "r1.yaml"), "w", encoding="utf-8") as fh:
        fh.write(text)
    page = os.path.join(state.root, "generated", "board.html")
    before = os.path.getmtime(page)
    time.sleep(1.1)
    start = time.time()
    try:
        state.capture("PR", dict(PR, title="second"))
        raised = ""
    except Exception as exc:                                # noqa: BLE001
        raised = "%s: %s" % (type(exc).__name__, exc)
    took = time.time() - start
    rebuilt = os.path.getmtime(page) > before
    print("%-12s state write %.2f s | board rebuilt: %-5s | %d bytes | raised: %s"
          % (label, took, rebuilt, os.path.getsize(page), raised or "-"))
    return rebuilt


CASES = {
    "huge-epoch": "request_id: r1\nkind: scope\nitem: PR-0001\nexpires_at_epoch: 99999999999\n",
    "float-1e30": "request_id: r1\nkind: scope\nitem: PR-0001\nexpires_at_epoch: 1e30\n",
    "alias-bomb": bomb_text(),
}
print("bomb file is %d bytes" % len(CASES["alias-bomb"].encode("utf-8")))
ok = True
for label, text in CASES.items():
    ok = one(label, text) and ok
print("ALL REBUILT:", ok)
sys.exit(0 if ok else 1)

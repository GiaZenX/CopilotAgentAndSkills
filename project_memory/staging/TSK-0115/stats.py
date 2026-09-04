"""What the real state of the main repo holds, counted from index.yaml + the kernel's own maps.

Answers, for the design brief: how many items are blocked, waiting on the user (open approval
requests), in flight (non-initial, non-terminal automaton status), fresh (initial status), done but
not archived (terminal in active/), and how the record types (no automaton) distribute.
"""
import collections
import os
import sys
import time

import yaml

WT = "C:/Offline Repos/v2-testbed/_worktrees/g3-board"
sys.path.insert(0, os.path.join(WT, "team-kits"))
sys.dont_write_bytecode = True
from kernel.backlog_types import ACTIVE_DIRS, AUTOMATA  # noqa: E402

PM = sys.argv[1] if len(sys.argv) > 1 else "C:/Offline Repos/AgentAndSkills/project_memory"


def lane(item_type, status):
    auto = AUTOMATA.get(item_type)
    if auto is None:
        return "record"
    if status == auto.initial:
        return "new"
    if status in auto.terminals:
        return "done-unarchived"
    if status in auto.states:
        return "in-flight"
    return "off-vocabulary"


def main():
    with open(os.path.join(PM, "generated", "index.yaml"), encoding="utf-8") as fh:
        index = yaml.safe_load(fh)
    rows = index["items"]
    print("index generated_at:", index["generated_at"], "rows:", len(rows))
    per_type_status = collections.Counter((r["type"], str(r.get("status"))) for r in rows)
    for key, count in sorted(per_type_status.items()):
        print("  %-4s %-14s %3d  lane=%s" % (key[0], key[1], count, lane(key[0], key[1])))
    lanes = collections.Counter(lane(r["type"], r.get("status")) for r in rows)
    print("lanes:", dict(lanes))
    blocked = [r for r in rows if r.get("blocked_by")]
    print("blocked rows:", len(blocked), [(r["id"], r["blocked_by"]) for r in blocked][:10])
    pending_dir = os.path.join(PM, "approvals", "pending")
    open_requests = []
    if os.path.isdir(pending_dir):
        for name in sorted(os.listdir(pending_dir)):
            if not name.endswith(".yaml"):
                continue
            with open(os.path.join(pending_dir, name), encoding="utf-8") as fh:
                req = yaml.safe_load(fh)
            expired = time.time() > float(req.get("expires_at_epoch", 0))
            open_requests.append((req.get("request_id"), req.get("kind"), req.get("item"), expired))
    print("approval requests in pending/:", open_requests)
    archive = os.path.join(PM, "archive")
    counts = {}
    for item_type in sorted(ACTIVE_DIRS):
        d = os.path.join(archive, item_type)
        n = 0
        for _dp, _dn, files in os.walk(d):
            n += sum(1 for f in files if f.endswith(".yaml"))
        if n:
            counts[item_type] = n
    print("archive per type:", counts, "total", sum(counts.values()))
    print("archive dirs:", sorted(os.listdir(archive)) if os.path.isdir(archive) else None)
    types_with_dir = [t for t in sorted(ACTIVE_DIRS) if os.path.isdir(os.path.join(PM, ACTIVE_DIRS[t]))]
    print("types with a directory:", types_with_dir)


if __name__ == "__main__":
    main()

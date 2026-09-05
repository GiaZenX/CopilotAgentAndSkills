"""Re-cut G4-4's order: TSK-0124 ordered "measured under 16 CPU burners", and that rig preceded
two of the four hard power-offs of 2026-09-04 by 2-3 min (Windows Kernel-Power 41; the measurement
is logged in staging/generation-4-streams.md). The kernel refuses a field write on a READY order
(work-order fields are frozen because gates read them) and names the route: CANCEL the order and
CAPTURE the corrected one, so the re-planning is visible. Every field except the changed
expected_outputs lines is carried over verbatim from the item on disk; every state write goes
through `kernel.cli` on its own subprocess line (no shell loop -- gate 1 refuses those).

Usage: python -B recut_tsk0124.py  -> prints the new id; then the lead renames the staging and
scratch directories to the new id and tells the stream.
"""
import os
import re
import subprocess
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OLD_ID = "TSK-0124"
ITEM = os.path.join(ROOT, "project_memory", "tasks", "active", OLD_ID + ".yaml")
ENV = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "team-kits"))
KERNEL = [sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory"]

OLD = "measured under 16 CPU burners and solo."
NEW = ("measured solo AND under a load class this host tolerates: the load rig runs ONLY in the "
       "window the lead names after every other generation-4 stream has reported, never beside "
       "another stream's suite, with at most HALF of the host's logical CPUs as burners, at "
       "below-normal priority, inside a window of at most 120 s -- the 16-burner rig preceded "
       "two of the four hard power-offs of 2026-09-04 by 2-3 min (Windows Kernel-Power 41 at "
       "17:38, 22:58, 23:06, 23:14; measured in staging/generation-4-streams.md). Until that "
       "window the rig is REDESIGNED and its design (burner count, priority, cap, the kill "
       "path) stands in the protocol; it does not run.")
HOST_RULE = ("Host rule (2026-09-04, four hard power-offs): no command of this stream saturates "
             "every logical CPU of the host, and no load measurement starts without the lead "
             "naming its window; a rig that burns CPU states burner count, priority and cap in "
             "the protocol BEFORE its first run. Everything else in this order continues now, "
             "beside the other three streams. Successor of TSK-0124 (CANCELLED for this re-cut; "
             "its worktree g4-hygiene, patch and protocol carry over under the new id).")


def kernel(*args):
    result = subprocess.run(KERNEL + list(args), cwd=ROOT, env=ENV,
                            capture_output=True, text=True, encoding="utf-8")
    print("$ kernel", " ".join(args[:3]), "->", result.returncode)
    print((result.stdout or "").strip()[-600:])
    if result.returncode != 0:
        print((result.stderr or "").strip()[-1500:])
        sys.exit("kernel refused: " + " ".join(args[:2]))
    return result.stdout


with open(ITEM, encoding="utf-8") as fh:
    item = yaml.safe_load(fh)

outputs = list(item["expected_outputs"])
hits = [i for i, line in enumerate(outputs) if OLD in line]
if len(hits) != 1:
    sys.exit("expected exactly one AC-4 line carrying %r, found %d" % (OLD, len(hits)))
outputs[hits[0]] = outputs[hits[0]].replace(OLD, NEW)
outputs.append(HOST_RULE)

argv = ["create-task",
        "--product-requirement", item["product_requirement"],
        "--derives-from", item["derives_from"],
        "--type", item["type"], "--assigned-role", item["assigned_role"]]
for ac in item["acceptance_refs"]:
    argv += ["--acceptance-ref", ac]
for path in item["allowed_scope"]:
    argv += ["--allowed-scope", path]
for path in item["forbidden_scope"]:
    argv += ["--forbidden-scope", path]
for path in item.get("seam_scope") or []:
    argv += ["--seam-scope", path]
for line in item["required_inputs"]:
    argv += ["--required-input", line]
for line in outputs:
    argv += ["--expected-output", line]

# 1. the old order leaves the board first, so the new one is the only open hygiene order
kernel("transition", OLD_ID, "CANCELLED")
# 2. the corrected order
out = kernel(*argv)
match = re.search(r"TSK-\d{4}", out)
if not match:
    sys.exit("no id in create-task output")
new_id = match.group(0)
# 3. READY, then the cut measured again over the four open orders (DEC-0070 rule 1)
kernel("transition", new_id, "READY")
kernel("check-scopes", "--only", "TSK-0121", "TSK-0122", "TSK-0123", new_id)
print("NEW_ID", new_id)

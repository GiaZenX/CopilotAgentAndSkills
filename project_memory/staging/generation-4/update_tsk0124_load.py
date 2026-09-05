"""Rewrite TSK-0124's AC-4 line through the kernel: the 16-burner load rig is what preceded the
host's hard power-offs on 2026-09-04 (four Kernel-Power 41 events, two of them 2-3 min after a
rig start; staging/generation-4-streams.md). The item ordered "measured under 16 CPU burners" --
so the order, not a message, is what changes (DEC-0070 (4): an order sentence in a message stops
nobody). Body goes through `kernel.cli update` on stdin; nothing here writes state directly."""
import json
import os
import subprocess
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ITEM = os.path.join(ROOT, "project_memory", "tasks", "active", "TSK-0124.yaml")

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
             "beside the other three streams.")

with open(ITEM, encoding="utf-8") as fh:
    item = yaml.safe_load(fh)

outputs = list(item["expected_outputs"])
hits = [i for i, line in enumerate(outputs) if OLD in line]
if len(hits) != 1:
    sys.exit("expected exactly one AC-4 line carrying %r, found %d" % (OLD, len(hits)))
outputs[hits[0]] = outputs[hits[0]].replace(OLD, NEW)
if not any(line.startswith("Host rule") for line in outputs):
    outputs.append(HOST_RULE)

body = json.dumps({"expected_outputs": outputs})
env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "team-kits"))
result = subprocess.run(
    [sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory", "update", "TSK-0124"],
    cwd=ROOT, env=env, input=body, capture_output=True, text=True, encoding="utf-8")
sys.stdout.write(result.stdout)
sys.stderr.write(result.stderr)
sys.exit(result.returncode)

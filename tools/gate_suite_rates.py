#!/usr/bin/env python3
"""What this host charges the gate suite for a process, right now.

WHY IT IS A TOOL AND NOT A SCRATCH SCRIPT. A wall time for `.claude/hooks/test_gates.py` says
nothing on its own: the same tree, the same command and the same host measured 511.66 s and
1116.36 s in one day, because what bounds that suite is how many processes this host will start per
second and that moved by 3.6x between two hours (docs/reviews/2026-08-29-tsk0090-measurements.md,
section 4). Run this immediately before a run whose wall time is going to be reported, and report
the two together -- otherwise the next round compares a number against one taken on a different
machine wearing the same name.

    python tools/gate_suite_rates.py            the three rates, at the widths the suite uses
    python tools/gate_suite_rates.py --scan     the same rates across widths (section 3's table)

The subjects are the suite's OWN helpers, imported from it, so this measures what a run of it pays
and not an imitation of it.
"""
import concurrent.futures
import os
import queue
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = os.path.join(ROOT, ".claude", "hooks")
SCAN_WIDTHS = (1, 4, 10, 16, 24, 32)


def suite():
    """The gate suite as a module -- the helpers below are the ones a run of it really uses."""
    sys.path.insert(0, HOOKS)
    import test_gates
    return test_gates


def pooled(work, count, width):
    """`count` runs of `work`, `width` of them at a time, each holding a slot of its own."""
    slots = queue.Queue()
    for index in range(width):
        slots.put(index)

    def held(_subject):
        slot = slots.get()
        try:
            return work(slot)
        finally:
            slots.put(slot)

    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=width) as pool:
        list(pool.map(held, range(count)))
    elapsed = time.monotonic() - started
    return elapsed, count / elapsed


def main(argv):
    gates = suite()
    holder = tempfile.mkdtemp(prefix="gate-rates-", dir=gates._base_outside_the_home_directory())
    cells = tempfile.mkdtemp(prefix="gate-rates-cells-")
    try:
        started = time.monotonic()
        project = gates.build_project(os.path.join(holder, "project"))
        print("build_project                     %6.2fs" % (time.monotonic() - started))
        trees = [gates._sandbox(cells, index) for index in range(max(SCAN_WIDTHS))]
        shell = next((candidate for candidate in gates._posix_shells()
                      if gates._sees_this_filesystem(candidate, trees[0])), None)
        if shell is None:
            print("no shell on this host reads back a file this process writes: %s"
                  % (gates._posix_shells(),))
            return 1
        payload = gates.write_payload(project, "docs/note.md")

        def gate(_slot):
            return gates.run(project, "gate_lead_write_scope.py", payload)

        def line(slot):
            return gates._changes_the_protected_file(shell, trees[slot], gates.RELATIVE_WRITE)

        def bare(slot):
            return subprocess.run([shell, "-c", ":"], cwd=trees[slot],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        shipped = gates.AT_ONCE
        subjects = [("gate process", gate, 120, shipped[gates.GATE_PROCESSES]),
                    ("shell line (sed -i)", line, 400, shipped[gates.SHELL_LINES]),
                    ("bare shell", bare, 400, shipped[gates.SHELL_LINES])]
        for name, work, count, width in subjects:
            widths = SCAN_WIDTHS if "--scan" in argv else (width,)
            for one in widths:
                elapsed, rate = pooled(work, count, one)
                print("%-22s width=%-3d %6.2fs  %6.1f/s%s"
                      % (name, one, elapsed, rate, "  (the width this suite uses)"
                         if one == width else ""))
    finally:
        gates._removed(cells)
        gates._removed(holder)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

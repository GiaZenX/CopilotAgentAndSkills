#!/usr/bin/env python3
"""The margins the gate suite's deadline tests assert on, taken repeatedly.

WHAT IT IS FOR. `test_gate1_answers_before_its_registration_gives_up` compares a real runtime
against a registered budget and this host's own timing noise. Green or red is one bit; what says
whether the measurement is still a measurement is how much room was left. This takes the same
quantities through the suite's OWN helpers, so what it prints is what those assertions compare.

    python tools/gate_suite_margins.py 12               with nothing of this suite beside it
    python tools/gate_suite_margins.py 12 --neighbours  with the cell phase running beside it

THE SECOND FORM IS A COUNTER-MEASUREMENT, not a mode anybody should ship: measured for TSK-0090,
the band the floor is shown in fell under this host's noise in 4 of 12 runs under that load and in
0 of 12 without it (docs/reviews/2026-08-29-tsk0090-measurements.md, section 6). It is here so the
next round can reproduce that rather than take it on trust.
"""
import os
import pathlib
import shutil
import sys
import tempfile
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = os.path.join(ROOT, ".claude", "hooks")
EVERY = 7  # one subject in seven, so the neighbour load starts long before the first measurement


def suite():
    sys.path.insert(0, HOOKS)
    import test_gates
    return test_gates


def once(gates, project, work):
    """One pass of the quantities `test_gate1_answers_before_its_registration_gives_up` compares."""
    work = pathlib.Path(work)
    longer, measured = gates._registrations(project, work)
    copy = os.path.join(str(work), "deadline-long")
    shutil.copytree(project, copy)
    gates._set_registered_timeout(copy, longer)
    rc, err, elapsed = gates._refused_for_the_deadline(copy, longer)
    bare, noise = gates._cost_of_a_gate_that_answers_at_once(project, work)
    share, floor = gates._reserve_numbers()
    case = gates._floor_case(bare, share, floor)
    return {"registration": longer, "elapsed": elapsed, "margin": longer - elapsed,
            "refused for the deadline": rc == 2 and "registration allows" in err,
            "bare start": bare, "noise": noise,
            "band": None if case is None else case[2],
            "band over noise": None if case is None else case[2] - noise,
            "verdict cost": measured}


def neighbours(gates, project, cells, stop):
    """The cell phase's two kinds, over and over, as the load the counter-measurement is about."""
    trees = [gates._sandbox(cells, index)
             for index in range(gates.AT_ONCE[gates.SHELL_LINES])]
    outside = os.path.join(cells, "elsewhere")
    os.makedirs(outside, exist_ok=True)
    outside = outside.replace(os.sep, "/")
    shell = next((candidate for candidate in gates._posix_shells()
                  if gates._can_arbitrate(candidate, trees[0], outside)), None)
    if shell is None:
        return
    subjects = sorted(gates.TILDE_SUBJECTS)[::EVERY]
    shapes = sorted(gates.LINE_SHAPES)[::EVERY]

    def tilde(subject):
        return ((gates.TILDE_STATES[subject[0]] % {"out": '"%s"' % outside})
                + 'sed -i "s/a/b/" %s' % gates.TILDE_SUBJECTS[subject])

    while not stop.is_set():
        gates._all_at_once([
            ("shell", gates.SHELL_LINES,
             lambda slot, subject: gates._changes_the_protected_file(
                 shell, trees[slot], tilde(subject), outside), subjects),
            ("gate", gates.GATE_PROCESSES,
             lambda _slot, label: gates.run(
                 project, "gate_lead_write_scope.py",
                 gates.bash_payload(project, gates._line(gates.LINE_SHAPES[label][0],
                                                         outside, project))), shapes)])


def main(argv):
    iterations = int(argv[0]) if argv else 12
    gates = suite()
    holder = tempfile.mkdtemp(prefix="gate-margins-",
                              dir=gates._base_outside_the_home_directory())
    cells = tempfile.mkdtemp(prefix="gate-margins-cells-")
    stop = threading.Event()
    try:
        project = gates.build_project(os.path.join(holder, "project"))
        if "--neighbours" in argv:
            threading.Thread(target=neighbours, args=(gates, project, cells, stop),
                             daemon=True).start()
            time.sleep(5)
        print("iteration  registration  elapsed  margin  refused  bare  noise  band  band-noise")
        rows = []
        for index in range(iterations):
            work = tempfile.mkdtemp(prefix="gate-margin-run-")
            try:
                row = once(gates, project, work)
            finally:
                gates._removed(work)
            rows.append(row)
            print("%9d  %12d  %7.2f  %6.2f  %7s  %4.2f  %5.2f  %s  %s"
                  % (index, row["registration"], row["elapsed"], row["margin"],
                     row["refused for the deadline"], row["bare start"], row["noise"],
                     "none" if row["band"] is None else "%.2f" % row["band"],
                     "none" if row["band over noise"] is None
                     else "%.2f" % row["band over noise"]), flush=True)
        stop.set()
        margins = [row["margin"] for row in rows]
        over = [row["band over noise"] for row in rows if row["band over noise"] is not None]
        print("\nmargin to the registration: worst %.2fs, best %.2fs over %d runs"
              % (min(margins), max(margins), len(margins)))
        print("every run refused for the deadline: %s"
              % all(row["refused for the deadline"] for row in rows))
        print("band minus this host's noise: worst %s, runs with no band at all: %d"
              % ("none" if not over else "%.2f" % min(over), len(rows) - len(over)))
        print("runs whose band was UNDER the noise: %d of %d"
              % (sum(1 for value in over if value <= 0), len(rows)))
    finally:
        stop.set()
        gates._removed(cells)
        gates._removed(holder)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

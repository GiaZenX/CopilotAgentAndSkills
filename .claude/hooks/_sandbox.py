#!/usr/bin/env python3
"""Sandbox discipline for anything that measures these gates by RUNNING their payloads.

WHY THIS IS CODE AND NOT A PARAGRAPH IN A WORK ORDER. Every payload these gates are measured with
names its target RELATIVELY (`sed -i "s/a/b/" team-kits/kernel/state.py`), and a line meant to
PROVE a refusal is dangerous exactly when the proof fails: if the gate does not refuse it, something
runs it. `team-kits/kernel/state.py` of this repo has been destroyed that way repeatedly
(`docs/POST_V2_WISHLIST.md` H37 carries the damages). The discipline that keeps a measurement off
this tree was written
as a promise in a work order twice and was wrong both times, so it lives here, next to the suite,
where `test_gates.py` measures it.

WHAT IT ANSWERS, AND WHY EACH OF THE THREE IS A DIFFERENT QUESTION:

  * WHERE DOES A CHILD SHELL STAND -- `pin()`. Not `cwd`: a word that does not name a directory
    is resolved out of the shell's OWN state, and pieces of that state arrive through the
    ENVIRONMENT (`~-` reads `OLDPWD`, a bare `~` reads `HOME`, a relative word a `cd` cannot find
    is looked up along `CDPATH`). A measurement started in the tree it measures hands that tree on
    in `OLDPWD`, and one line with a perfectly correct `cwd` then rewrites it. So `pin()` sets the
    directory state instead of inheriting it, in `os.environ`, which is what every child gets.
  * WHAT MAY NOT MOVE -- `protected_files()`. Derived from the gate's OWN authority
    (`_harness.ProtectedArea`), not from a scan over the payload lines: a scan of the lines was
    what the round before used, and it broke at the quoting inside a word, so three of the four
    protected files a round's own lines named were never hashed at all.
  * WHERE MAY A REPAIR WRITE -- `restore_from_index()`. A helper that puts an index version of a
    file into a clone checked the PROCESS and not the TARGET, which makes it the one unguarded
    write-back path in an apparatus whose whole subject is unguarded write-backs.

Nothing here is a hook. It is imported by `test_gates.py` and by the ad-hoc scripts a round writes,
so that both stand on the same answer.
"""
import hashlib
import os
import subprocess
import sys

HOOKS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HOOKS))

# THE NAMES THROUGH WHICH A PARENT HANDS A CHILD SHELL A DIRECTORY OTHER THAN ITS `cwd`, grouped by
# the ROLE the directory plays and not by the spelling of the name -- because the roles want
# different values, and one round found that out the expensive way.
#
# WHERE THE SHELL STANDS AND WHERE IT CAME FROM (`~+` reads `PWD`, `~-` reads `OLDPWD`). The sandbox
# itself, so a word resolved through them lands on the tree under measurement, which is where a
# payload is supposed to land.
THE_SHELLS_POSITION = ("PWD", "OLDPWD")
# WHOSE DIRECTORY IT IS (`~` reads `HOME`, and a bare `cd` goes there). Inside the sandbox, but NOT
# the tree: a home directory is where a user's own files live, and making it the tree says "this
# repo lives under the home directory" -- which this one does not. Measured 2026-08-08 with `HOME`
# set to the tree: `~/team-kits/kernel/state.py` IS the protected file, so gate 1's deliberate
# position on the empty prefix (H33) read as 30 holes in
# `test_gate1_places_a_tilde_word_where_the_shell_puts_it`, and a bare `cd` and `cd ~` stopped
# leaving the tree, which flipped 32 cells of `test_the_shell_writes_where_the_table_of_line_shapes
# _says`. The leaf has to EXIST for that `cd`, so `sandbox_environment` makes it.
THE_USERS_OWN_PLACE = ("HOME",)
HOME_LEAF = ".a-home-beside-the-tree"
POINTED_AT_THE_SANDBOX = THE_SHELLS_POSITION + THE_USERS_OWN_PLACE
# A name that holds a LIST has no one-directory value, and every entry of it is a place a word could
# still resolve to -- a `cd` word a shell cannot find below `cwd` is looked up along `CDPATH`, and
# `~N` counts into a stack -- so a list is dropped rather than pointed anywhere.
DROPPED = ("CDPATH", "DIRSTACK")

# Of the names above, the ones no shell on this host was measured to read back OUT of the
# environment: `bash` re-derives `PWD` from `getcwd()` when it starts and builds `~N` from that
# rather than from `DIRSTACK`, so neither of them can point a child anywhere. They are handled
# anyway -- handling a name costs nothing, and a shell that does not re-derive would read it -- but
# nothing here claims a measured chain for them. `test_gates.py::test_the_measurement_sandbox_
# leaves_a_child_shell_no_directory_word_that_names_another_tree` partitions the two groups above
# BY MEASUREMENT and refuses both ends: a name in here that turns out to carry a tree after all,
# and a name outside it that carries none and is therefore handled for nothing.
NOT_MEASURED_TO_CARRY_A_TREE = ("PWD", "DIRSTACK")

# Set by `pin()`. A repair may write under this and nowhere else.
_SANDBOX = None


def posix(path):
    """The spelling a POSIX shell on this host reads for `path`."""
    return os.path.abspath(path).replace("\\", "/")


def _inside(path, base):
    """Is `path` `base` itself or under it -- answered on the resolved paths."""
    path, base = os.path.realpath(path), os.path.realpath(base)
    try:
        return os.path.commonpath([path, base]) == base
    except ValueError:  # different drives
        return False


def sandbox_environment(where, environment=None):
    """`environment` with every directory name a child shell could read kept inside `where`.

    THREE GROUPS AND NOT ONE, because they are three different operations. A dropped name has to
    LEAVE, and leaving is what a caller that merges this back into `os.environ` cannot express
    (`pin()`) -- a `dict.update` puts a value on top and takes none away. And the home directory has
    to be inside the sandbox WITHOUT being the tree, for the reason written at `THE_USERS_OWN_PLACE`.
    """
    out = dict(os.environ if environment is None else environment)
    here = posix(where)
    home = os.path.join(os.path.abspath(where), HOME_LEAF)
    os.makedirs(home, exist_ok=True)
    for name in DROPPED:
        out.pop(name, None)
    for name in THE_SHELLS_POSITION:
        out[name] = here
    for name in THE_USERS_OWN_PLACE:
        out[name] = posix(home)
    return out


def pin(sandbox, where=None):
    """Stand in `where` (under `sandbox`) with every directory state a shell reads set to it.

    REFUSES RATHER THAN CORRECTS, in four directions, because each of them is a way for a payload
    to reach this repo: a sandbox inside this repo, a sandbox that CONTAINS this repo (a payload
    that writes a directory writes what is in it), a working directory outside the sandbox, and a
    directory state left inherited. The first three are positions; the fourth is the one that was
    missed, and it is the only one `cwd` cannot express.
    """
    global _SANDBOX
    sandbox = os.path.abspath(sandbox)
    if _inside(sandbox, ROOT) or _inside(ROOT, sandbox):
        sys.exit("REFUSED: %s is not outside %s, so a payload run in it could name this tree"
                 % (sandbox, ROOT))
    target = os.path.abspath(os.path.join(sandbox, where) if where else sandbox)
    os.makedirs(target, exist_ok=True)
    os.chdir(target)
    here = os.getcwd()
    if not _inside(here, sandbox):
        sys.exit("REFUSED: this process stands in %s, which is not under %s" % (here, sandbox))
    pinned = sandbox_environment(here)
    # WHAT `sandbox_environment` LEFT OUT IS WHAT LEAVES, derived rather than named a second time:
    # `os.environ.update` alone puts values on top and removes nothing, so a dropped name would
    # survive in the very process that pinned itself.
    for name in [name for name in os.environ if name not in pinned]:
        del os.environ[name]
    os.environ.update(pinned)
    _SANDBOX = sandbox
    return here


def _protected_areas(area):
    """Every place `ProtectedArea` derives its answer from, read off the object rather than typed.

    The object's own attributes ARE the areas -- one more of them (a fifth area, a producer this
    gate gained) is walked on the day it appears, which a list here could not be.
    """
    out = []
    for name in area.__slots__:
        if name == "root":
            continue
        value = getattr(area, name)
        out.extend([value] if isinstance(value, str) else sorted(value))
    return out


def protected_files(root=ROOT):
    """Every file of `root` the gate's own authority refuses to somebody.

    THE AUTHORITY DECIDES, NOT THIS FILE. `ProtectedArea.verdict` is what gate 1 answers with, so
    a carve-out it makes (`project_memory/staging/**`) is a carve-out here without being named, and
    an area it gains is watched without being added. What this adds is only WHERE to look: walking
    the whole repo would spend its time in `.git`, which no area covers.
    """
    sys.path.insert(0, HOOKS)
    import _harness
    area = _harness.ProtectedArea(root)
    out = set()
    for base in _protected_areas(area):
        if os.path.isfile(base):
            paths = [base]
        else:
            paths = [os.path.join(here, name)
                     for here, _dirs, names in os.walk(base) for name in names]
        for path in paths:
            if area.verdict(path)[0] is not None:
                out.add(os.path.abspath(path))
    return sorted(out)


def _digest(path):
    """What this file holds, or None when there is none."""
    try:
        with open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    except OSError:
        return None


class watch(object):
    """Hash what `root` protects around a measurement run and refuse to end quietly if it moved.

    THE LIST IS THE PROTECTED SET AND NOT WHAT THE LINES SAY. A watch list derived from the payload
    lines answers only for the spellings its own scan can read, and the round before proved that
    the hard way: its scan broke at the quoting inside a word and at a join that threw the repo
    root away, so it hashed one of the four protected files its own lines had named. The protected
    set does not depend on how a line spells its target, which is exactly the property a watch list
    needs.
    """

    def __init__(self, root=ROOT, extra=()):
        self.root = root
        self.paths = sorted(set(protected_files(root))
                            | {os.path.join(root, *name.split("/")) for name in extra})
        assert self.paths, "%s protects no file, so this watch is watching nothing" % root

    def __enter__(self):
        self.before = {path: _digest(path) for path in self.paths}
        return self

    def __exit__(self, *_):
        moved = [path for path in self.paths if _digest(path) != self.before[path]]
        if moved:
            raise SystemExit("REPO DAMAGED by this measurement run: %s" % moved)
        sys.stderr.write("[sandbox] %d protected files of %s unchanged\n"
                         % (len(self.paths), self.root))
        return False


def restore_from_index(clone, relative, root=ROOT):
    """Put the index version of `root/relative` into `clone`, which must be under the pinned sandbox.

    THE TARGET IS CHECKED, NOT THE PROCESS. Standing in the sandbox says nothing about where a
    write goes: this helper takes its destination as an argument, so a wrong argument writes
    wherever it points -- the working tree of this repo included, which is the one thing an
    apparatus for measuring writes into this repo must not be able to do.
    """
    if _SANDBOX is None:
        sys.exit("REFUSED: no sandbox is pinned, so there is nowhere this may write")
    target = os.path.abspath(os.path.join(clone, *relative.split("/")))
    if not _inside(os.path.dirname(target), _SANDBOX):
        sys.exit("REFUSED: %s is not under the pinned sandbox %s" % (target, _SANDBOX))
    done = subprocess.run(["git", "show", ":" + relative], cwd=root, capture_output=True)
    if done.returncode != 0:
        sys.exit("REFUSED: %s is not in the index of %s: %s"
                 % (relative, root, done.stderr[-300:]))
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "wb") as handle:
        handle.write(done.stdout)
    return target

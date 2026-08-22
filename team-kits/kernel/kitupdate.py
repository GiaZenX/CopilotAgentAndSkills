"""Updating the KIT an installed project runs -- and stopping the session that ran the update.

THE FLOW THIS RESTORES (FR-0006, DEC-0001). V1 told the lead "on the user's OK, run the scaffold".
V2 turned that into "ASK THE USER TO RUN it -- you cannot run either yourself", which was a SIDE
EFFECT of `gate_write_scope` refusing every write-capable command line that names the enforcement
layer, not a decision about the update flow. Measured 2026-08-16 against a project scaffolded
OUTSIDE this repo at an older stamp: both installer spellings are rc 2 at that gate, and the
SessionStart briefing handed the lead exactly that sentence. That is the shape of the preset dead
end BUG-0041 closed, and it is closed the same way -- the KERNEL runs the kit's own installer, on
the user's minted approval, and nothing about the gate's permission changes.

WHY IT RUNS THE KIT'S OWN INSTALLER, and why a kit update may use it where a preset change may
not: `kernel.presets` argues the first half (a scaffold is the ownership manifest, the backup, the
rollback, the symlink pre-flight, the tier-alias rewrite, the model re-stamp, the provider
artifacts and the trust record -- a second implementation would be a second answer to "what is
installed"). Its `assert_installable` then REFUSES a scaffold against a staging that has moved on,
because that would be a kit update wearing a preset change's clothes. This module is that refused
operation, made its own step with its own user decision -- which is what that refusal's remedy
already told the reader to do.

THE RESTART IS PART OF THE COMMAND, not advice, and that is the half V1 lacked. What changes
under a running session is measured rather than assumed (2026-08-16, real scaffold over a live
project): `.claude/hooks` and `.claude/kernel` are the new kit's from the moment the installer
finishes -- the provider re-reads a hook FILE on every call -- while the REGISTRATION in
`settings.json`, the agent set and the session agent are what the session started with. The
process running this command has its own kernel deleted and re-copied underneath it (measured:
`.claude/kernel/hashing.py` absent for 5 ms, 1.58 s into a 3.4 s run), so every module a failure
branch here needs is imported at module scope -- an import AFTER the installer starts is an import
out of a tree the installer is replacing. `.claude/HANDOVER_PENDING` therefore has to exist when
this command returns, whatever happened to the installer, and `ensure_restart_is_forced` is what
makes that true by construction rather than by the installer having got that far.

WHO READS THAT MARKER, named because a marker nothing reads is a comment in file form: the global
`~/.claude/hooks/handover_guard.py` refuses spawns, product-code writes and further work-engine
calls while it exists, and `gate_dispatch` refuses a specialist spawn on it in every kit -- the
second one so the stop does not depend on a user-global installation the project cannot see.
Nothing else reads it: `gate_write_scope`, `gate_git` and the rest are unaffected, and this module
claims no more than that (`tools/test_kitupdate.py::test_the_marker_this_command_leaves_really_
stops_the_session`).
"""
from __future__ import annotations

import json
import os
import re
import subprocess

from . import approvals, presets
from .hashing import BundleSourceMissing, hook_bundle_hash, kit_hash, modified_bundle_files
from .state import ProjectState, StateError

# The APR kind that authorises this operation, and the command that consumes it. One name, three
# readers: the vocabulary, the manifest builder and the refusals below.
KIND = "kit_update"
COMMAND = "update-kit"

# WHERE THE TWO RELEASES STATE THEIR IDENTITY. Both files are `kernel.hashing`'s doing -- the
# staged one is what `tools/bump_kit_version.py` stamps, the installed one is the copy the scaffold
# takes of it -- so the same reader answers both.
INSTALLED_VERSION_FILE = presets.KIT_VERSION_FILE       # .claude/kit_version
STAGED_VERSION_FILE = presets.STAGED_VERSION_FILE       # VERSION
# What `.claude/kit_update_pending.repo` is: the repo templates a scaffold found DIVERGED and kept.
# Reported after a run rather than acted on -- merging them is the lead's work, and the session
# briefing nags until the file is gone.
PENDING_TEMPLATES = os.path.join(".claude", "kit_update_pending.repo")

# THE MARKERS A SESSION START CONSUMES, which is the property rather than a list of file names: an
# installer writes one, a SessionStart hook removes it, so its presence proves that no session has
# started since the last install. That makes it the exact definition of "this project is waiting
# for a restart, not for another update" -- and running a second installer over it would destroy
# the first one's announcement (the scaffold's own "never overwrite an unconsumed marker" rule).
# Each entry names the consumer that makes the property true, and both are measured as processes
# by `tools/test_kitupdate.py::test_every_marker_this_command_refuses_on_is_consumed_by_a_session_
# start`, which is what keeps an entry from outliving its consumer.
RESTART_MARKERS = (
    {"path": os.path.join(".claude", "HANDOVER_PENDING"),
     "consumer": "clear_handover_marker.py, on a SessionStart whose source is `startup`"},
    {"path": os.path.join(".claude", "kit_updated_from"),
     "consumer": "session_status.py, which announces the transition once and deletes it"},
)
# The one this command WRITES when the installer did not get that far -- the first of the two, by
# the same identity the guard reads it under. Named once; `RESTART_MARKERS` carries the reason.
HANDOVER_MARKER = RESTART_MARKERS[0]["path"]

# WHAT THIS COMMAND DOES NOT RE-READ after the installer, in the words every outcome carries. Same
# rule as `presets.UNREAD` and for the same measured reason: a scope stated in some messages is a
# scope the others deny. The readings below are the version stamp, the ownership manifest, the hook
# bundle and the two markers; the role skills, the provider artifacts, the repo templates and the
# constitution are not among them.
UNREAD = ("the role skills, the generated provider artifacts, the repo templates and the "
          "constitution were not re-read, so a missing or a half-copied one would not show here")

_NUMBER = re.compile(r"\d+")
# The two lines a kit's VERSION file carries; `identity` reads exactly these and nothing else.
_STAMP_FIELDS = ("version", "content")


def version_order(version: str):
    """The comparable key of a kit's `version:` value, or None when it carries no number.

    THE ONE DEFINITION OF "WHICH KIT IS NEWER", and it used to be two: this rule lived in the
    hooks' `_compat` where only the session briefing could reach it, so the command that REFUSES a
    downgrade would have been a second copy of the rule the briefing OFFERS one on. The hooks now
    ask this function through `_kernel.kit_update_verdict`, so the briefing and the refusal cannot
    disagree about a direction.

    Every part of the stamp that orders it is a number, so the key is the numbers in the order they
    appear -- a property of the format rather than a parse of it. A fourth component sorts correctly
    with no edit here, and a hand-edited stamp answers None, which callers read as "cannot say which
    is newer" and never as equal.
    """
    return tuple(int(number) for number in _NUMBER.findall(str(version or ""))) or None


def identity(text: str) -> dict:
    """{"version", "content"} -- a kit's own two statements about which release it is.

    Both, and not the version alone: `content:` is the hash `bump_kit_version` stamps over
    everything a scaffold reads or installs, so the pair is what tells two kits apart that carry
    one stamp -- the "KIT CONTENT MISMATCH" the session briefing has always been able to name and
    nothing could act on. A key that is absent is simply absent; the callers decide what that means.
    """
    values = {}
    for line in str(text or "").splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() in _STAMP_FIELDS and key.strip() not in values:
            values[key.strip()] = value.strip()
    return values


def _stamp(path: str) -> dict:
    try:
        return identity(presets.read_text(path))
    except OSError:
        return {}


# The verdicts `relation` answers with. A closed set, because it is a comparison of two order keys
# plus the readability of the two files -- every branch of that comparison has a name here, and
# `assert_updatable` answers each of them exactly once.
UP_TO_DATE = "up_to_date"
UPDATE_AVAILABLE = "update_available"
DOWNGRADE = "downgrade"
CONTENT_MISMATCH = "content_mismatch"
UNREADABLE_ORDER = "unreadable_order"
UNREADABLE = "unreadable"
NOT_STAGED = "not_staged"


def relation(root: str, kit: str) -> dict:
    """How the STAGED kit stands to the one this project installed -- the whole comparison, once.

    THREE READERS OF THIS ONE ANSWER: the approval question (through `change_manifest`), the
    command that acts on it, and the SessionStart briefing that OFFERS the update. The briefing used
    to compute its own, which is how a project could be told "KIT UPDATE AVAILABLE" by one file
    while another refused it.

    NEVER RAISES: an absent staging, an unreadable stamp and a hand-edited one are answers here, not
    errors, because the briefing must be able to ask without a try/except deciding what it prints.
    `assert_updatable` is where a verdict becomes a refusal.
    """
    directory = os.path.join(presets.staging_root(), kit)
    installed = _stamp(os.path.join(root, INSTALLED_VERSION_FILE))
    staged = _stamp(os.path.join(directory, STAGED_VERSION_FILE))
    answer = {"kit": kit, "kit_dir": directory, "from": installed, "to": staged}
    if not os.path.isdir(directory):
        return dict(answer, verdict=NOT_STAGED)
    if not installed or not staged:
        return dict(answer, verdict=UNREADABLE)
    if installed == staged:
        return dict(answer, verdict=UP_TO_DATE)
    here, there = version_order(installed.get("version")), version_order(staged.get("version"))
    if here is None or there is None:
        return dict(answer, verdict=UNREADABLE_ORDER)
    if there > here:
        return dict(answer, verdict=UPDATE_AVAILABLE)
    if there < here:
        return dict(answer, verdict=DOWNGRADE)
    return dict(answer, verdict=CONTENT_MISMATCH)


def _shown(stamp: dict) -> str:
    return stamp.get("version") or "no readable version stamp"


def assert_updatable(answer: dict) -> None:
    """Refuse every verdict that is not an update -- BEFORE anything moves.

    Each refusal says what the project has, what is staged, and what the remedy is; none of them
    is a retry of this command, because none of the causes is a transient. The DOWNGRADE branch is
    the one with teeth: a scaffold run from an older staging PRUNES the hooks this project has and
    leaves its newer kernel in place, so it is not an update in the other direction but a broken
    installation (measured 2026-08-02 against a real staging, the case the briefing has named
    since; `tools/test_kitupdate.py::test_an_older_staging_is_refused_before_the_installer_starts`).
    """
    verdict = answer["verdict"]
    if verdict == UPDATE_AVAILABLE:
        return
    if verdict == NOT_STAGED:
        raise StateError(
            "the kit '%s' is not staged on this machine (%s), so there is no release to update "
            "to -- nothing was changed. Remedy: this is an infrastructure gap, not a retry; report "
            "it and name the directory. The kits are installed once per machine, outside any "
            "project." % (answer["kit"], answer["kit_dir"]))
    if verdict == UNREADABLE:
        raise StateError(
            "the two kit stamps cannot both be read (this project: %s, staged: %s), so which "
            "release is which cannot be established -- refused (fail-closed); nothing was changed. "
            "Remedy: report the gap and name the two files, %s and %s."
            % (_shown(answer["from"]), _shown(answer["to"]),
               INSTALLED_VERSION_FILE.replace(os.sep, "/"), STAGED_VERSION_FILE))
    if verdict == UP_TO_DATE:
        raise StateError(
            "this project already runs the staged '%s' kit (%s), so there is no update to install "
            "-- nothing was changed. Remedy: none is needed. Re-applying the SAME release is a "
            "repair, not an update, and this command is not it: it is a scaffold run from a shell "
            "outside this session." % (answer["kit"], _shown(answer["to"])))
    if verdict == DOWNGRADE:
        raise StateError(
            "the staged '%s' kit (%s) is OLDER than the one this project runs (%s) -- refused; "
            "nothing was changed. Installing it would prune the files this project's release added "
            "and leave the newer ones standing, which is a broken installation rather than an "
            "update in the other direction. Remedy: tell the user their staging is behind and let "
            "them update it (the harness installer) first."
            % (answer["kit"], _shown(answer["to"]), _shown(answer["from"])))
    if verdict == CONTENT_MISMATCH:
        raise StateError(
            "the staged '%s' kit and the one this project runs carry the SAME version stamp (%s) "
            "and DIFFERENT content -- one of the two was changed without a version bump. Refused; "
            "nothing was changed. Remedy: that is a finding to report, not an update to run."
            % (answer["kit"], _shown(answer["to"])))
    raise StateError(
        "which of the two kit stamps is newer cannot be determined (this project: %s, staged: %s) "
        "-- refused (fail-closed); nothing was changed. Remedy: at least one stamp carries no "
        "readable version; report it to the user and let them decide, and do not install on a "
        "guess." % (_shown(answer["from"]), _shown(answer["to"])))


def assert_the_staging_is_its_own_stamp(directory: str) -> None:
    """The staged tree must still hash to the `content:` its own VERSION claims.

    WHY IT IS CHECKED HERE AND NOT ONLY AT THE END: `write_kit_state.py` makes the same comparison
    as the last step of the scaffold, and a failure there fails the run, which rolls it back. That
    is a rollback of an enforcement layer this project depends on, over a fact that was knowable
    before the first file moved -- 20 ms of hashing (measured over the three shipped kits,
    2026-08-16). The approval also names this hash, so a staging edited between the question and
    the command is refused rather than installed
    (`tools/test_kitupdate.py::test_a_staging_edited_after_the_question_is_refused`).
    """
    claimed = _stamp(os.path.join(directory, STAGED_VERSION_FILE)).get("content")
    if not claimed:
        raise StateError(
            "the staged kit at %s carries no `content:` hash in its %s, so it is not a kit this "
            "harness stamped -- refused; nothing was changed. Remedy: re-install the harness "
            "(`install.ps1`/`install.sh`), which stamps the staging." % (directory,
                                                                         STAGED_VERSION_FILE))
    try:
        measured = kit_hash(directory)
    except OSError as exc:
        raise StateError(
            "the staged kit at %s could not be hashed (%s), so it cannot be checked against its "
            "own stamp -- refused (fail-closed); nothing was changed. Remedy: report the gap and "
            "name the directory." % (directory, exc)) from None
    if measured != claimed:
        raise StateError(
            "the staged kit at %s does not hash to the `content:` in its own %s (%s vs %s) -- its "
            "source has been edited since it was stamped. Refused; nothing was changed. Remedy: "
            "re-install the harness (`install.ps1`/`install.sh`); installing an unstamped tree "
            "would put files into this project's enforcement layer that no release covers."
            % (directory, STAGED_VERSION_FILE, measured[:12], claimed[:12]))


def waiting_for_a_restart(root: str) -> list:
    """The restart markers this project still carries -- see `RESTART_MARKERS` for what that proves."""
    return [marker for marker in RESTART_MARKERS
            if os.path.exists(os.path.join(root, marker["path"]))]


def assert_no_restart_is_pending(root: str) -> None:
    """An install has already happened here and no session has started since -- refuse.

    Not a caution: running the installer again over an unconsumed marker overwrites the record of
    what the FIRST update did (`kit_updated_from` is the from-version the next session announces,
    and the scaffold refuses to overwrite it), and it asks a session that was already told to stop
    to do more work. The way out is the restart both markers are waiting for.
    """
    pending = waiting_for_a_restart(root)
    if not pending:
        return
    raise StateError(
        "this project is already waiting for a session restart -- refused; nothing was changed. %s "
        "still exists, and it is removed by %s. Remedy: end this session and start a new one in "
        "this folder; the update state is picked up there. If the marker is stale because no "
        "restart will happen, that is a gap to report, not a command to retry."
        % ("; ".join(marker["path"].replace(os.sep, "/") for marker in pending),
           "; ".join(marker["consumer"] for marker in pending)))


def _plan(state: ProjectState) -> dict:
    """Everything one kit update needs to know, resolved ONCE -- and every check that has no side
    effect, ahead of every one that has.

    `apply` and the approval question are two readers of this one derivation: if each resolved the
    kit and the two stamps for itself, the question could name a release the command then does not
    install, which is what the approval hash exists to prevent (the shape
    `approvals.preset_subject_manifest` argues for the preset case).
    """
    root = presets.repo_root(state)
    kit = presets.installation(root)["kit"]
    answer = relation(root, kit)
    assert_updatable(answer)
    assert_the_staging_is_its_own_stamp(answer["kit_dir"])
    assert_no_restart_is_pending(root)
    return dict(answer, root=root, manifest=approvals.kit_update_subject_manifest(
        kit, answer["from"].get("version"), answer["from"].get("content"),
        answer["to"].get("version"), answer["to"].get("content")))


def change_manifest(state: ProjectState) -> dict:
    """What an update would DO here, in the shape the approval hashes -- re-derived at apply."""
    return _plan(state)["manifest"]


# -- what a run leaves behind -------------------------------------------------------------------

def _bundle_reading(root: str, kit_dir: str) -> str:
    """WHICH kit's enforcement bundle is installed right now -- the reader the stamp cannot be.

    TWO READERS, BECAUSE THE STAMP IS STALE FOR THE WINDOW THIS MATTERS IN. The installer copies
    `.claude/hooks` and `.claude/kernel` LONG before it writes `.claude/kit_version` (measured
    2026-08-16 against the real scaffold with the timeout shortened: at 1.6 s the bundle was
    already the staged kit's while the stamp still named the old release and `kit_state.json` still
    recorded the old bundle hash -- so every kernel-backed gate refused, and a caller that asked the
    stamp alone would have reported "nothing was installed"). The answers are properties, not
    guesses:

      staged   -- the installed bundle is byte-identical to the staged kit's files
      recorded -- it is not, but it still hashes to what `.claude/kit_state.json` vouched for, i.e.
                  nothing has moved
      neither  -- it is neither: a half-copied bundle, or one that was edited
      unreadable -- it cannot be measured at all, which is the fail-closed answer and the state
                  every integrity gate refuses on

    `tools/test_kitupdate.py::test_an_aborted_update_is_not_reported_off_the_stamp_alone` is the
    measurement that keeps the pair honest.
    """
    claude = os.path.join(root, ".claude")
    try:
        if not modified_bundle_files(os.path.join(kit_dir, "hooks"),
                                     os.path.join(os.path.dirname(kit_dir), "kernel"), claude):
            return "staged"
    except (BundleSourceMissing, OSError):
        pass                        # no source to compare against: the other two readings still hold
    measured = hook_bundle_hash(claude)
    if measured is None:
        return "unreadable"
    try:
        with open(os.path.join(claude, "kit_state.json"), encoding="utf-8-sig") as handle:
            recorded = (json.load(handle) or {}).get("hook_bundle_hash")
    except (OSError, ValueError):
        recorded = None
    return "recorded" if recorded and recorded == measured else "neither"


def _installed_state(root: str, kit_dir: str) -> dict:
    """What this project says it runs, and what it actually runs -- read, never assumed."""
    return {"stamp": _stamp(os.path.join(root, INSTALLED_VERSION_FILE)),
            "bundle": _bundle_reading(root, kit_dir)}


_BUNDLE_WORDS = {
    "staged": "the enforcement bundle on disk is the STAGED kit's",
    "recorded": "the enforcement bundle on disk is still the one this project recorded trust for",
    "neither": "the enforcement bundle on disk is NEITHER the staged kit's nor the one this "
               "project recorded trust for, i.e. half-copied or edited",
    "unreadable": "the enforcement bundle on disk cannot be measured at all, which is the state "
                  "every integrity gate refuses on",
}


def _describe(reading: dict) -> str:
    return "stamp %s, and %s" % (_shown(reading["stamp"]), _BUNDLE_WORDS[reading["bundle"]])


def _marker_path(root: str) -> str:
    return os.path.join(root, HANDOVER_MARKER)


def _restart_marker_as_found(root: str) -> str:
    """What the marker says about this project right now -- READ, and nothing written.

    THE BRANCH THIS EXISTS FOR, and it is a correction of this same round: the "nothing moved"
    outcome used to ensure the marker like every other one, and the resulting sentence was measured
    FALSE by the very command that wrote it. The chain (real scaffold, real approval, a preset typo
    in `project_config.yaml` -- a cause the PM can fix in-session through the kernel): the installer
    refuses touching nothing, the marker is written anyway, `gate_dispatch` then refuses every spawn
    with "an installer changed this project's kit files", the user-global guard closes the rest, and
    `assert_no_restart_is_pending` refuses the RETRY. The session was dead over a typo, with no
    route out that this harness has. A project nothing happened to needs no restart, so it gets no
    marker -- and both halves of what this returns are read off the disk rather than asserted, so a
    hardcoded sentence cannot pass (`tools/test_kitupdate.py::test_an_installer_that_refused_
    without_touching_anything_leaves_no_marker_and_can_be_retried`).
    """
    if os.path.exists(_marker_path(root)):
        return ("the restart marker %s is in place, so this session is stopped either way"
                % HANDOVER_MARKER.replace(os.sep, "/"))
    return ("no restart marker was set (%s does not exist), so this session is not stopped and this "
            "command can be run again once the cause above is dealt with"
            % HANDOVER_MARKER.replace(os.sep, "/"))


def ensure_restart_is_forced(root: str, kit: str) -> str:
    """Make the handover marker exist, and say what was found or written -- never claim it.

    PUBLIC because a second caller lives outside this package: `user/bridge/update_kit.py`, the
    bootstrap for a stock whose kernel predates this module (BUG-0059), runs the same installer and
    owes the same stop sign. Vendoring the marker's path and text there would be a second answer to
    "what stops a session whose kit changed underneath it".

    THE WINDOW THIS EXISTS FOR, measured 2026-08-16 against the real scaffold: between 2.4 s and
    3.4 s of a 3.4 s run the update was materially complete -- new stamp, new bundle, trust record
    rewritten -- and the marker was still absent, because the installer writes it as its very last
    act. A run killed there leaves a session whose kit has changed and whose only stop sign was
    never raised. So the marker is ensured by this command instead of being inherited from the
    installer's luck, and the result is READ BACK: a marker that could not be written is the one
    thing this command may not be quiet about.

    CALLED ONLY WHERE THE INSTALLATION REALLY MOVED -- the success path and the branch that measured
    a change. The other branch reads instead of writing, for the reason
    `_restart_marker_as_found` carries.
    """
    path = _marker_path(root)
    if os.path.exists(path):
        return "the restart marker %s is in place" % HANDOVER_MARKER.replace(os.sep, "/")
    try:
        ProjectState._write_text_atomic(path, _MARKER_TEXT % (kit, COMMAND))
    except OSError as exc:
        return ("THE RESTART MARKER %s COULD NOT BE WRITTEN (%s), so nothing stops this session "
                "from carrying on under a kit that has changed underneath it -- end the session "
                "now" % (HANDOVER_MARKER.replace(os.sep, "/"), exc))
    if not os.path.exists(path):
        return ("THE RESTART MARKER %s IS STILL ABSENT after writing it, so nothing stops this "
                "session from carrying on under a kit that has changed underneath it -- end the "
                "session now" % HANDOVER_MARKER.replace(os.sep, "/"))
    return ("the restart marker %s was not left by the installer and was written by this command"
            % HANDOVER_MARKER.replace(os.sep, "/"))


_MARKER_TEXT = (
    "# agents-and-skills handover marker (BUG-0016, DEC-0032)\n"
    "# The '%s' kit was updated in this session by `%s`. Until the session is restarted the\n"
    "# kit's dispatch gate refuses specialist spawns here, and the user-global handover guard --\n"
    "# where the harness installed one -- refuses work-engine commands and product writes too.\n"
    "# A SessionStart(startup) hook clears this file on the next real restart.\n")


def _pending_templates(root: str) -> str:
    """The diverged repo templates the run recorded, if any -- the lead's follow-up work."""
    path = os.path.join(root, PENDING_TEMPLATES)
    try:
        with open(path, encoding="utf-8-sig") as handle:
            lines = [line.strip() for line in handle if line.strip().startswith("-")]
    except OSError:
        return ""
    return ("%d repo template(s) differ from the new kit's and were KEPT; they are listed in %s, "
            "and the session briefing nags until that file is worked through and deleted"
            % (len(lines), PENDING_TEMPLATES.replace(os.sep, "/")))


def _after_a_failed_install(root, kit, kit_dir, was, command, reason):
    """Refuse with the state the run actually left -- read through both readers, never asserted.

    The defect this shape exists for is `presets._after_a_failed_install`'s, in the sharper
    position: there the abort left role files missing, here it can leave the project's whole
    enforcement layer half-replaced. Nothing here is claimed. The installation is READ BACK
    (`_installed_state`), and the three outcomes are told apart by that reading:

      unchanged -- say so, with the limit of what was read, and set NO marker: a project nothing
                  happened to needs no restart, and a marker written there stops the session over a
                  cause the PM could fix in the next minute (`_restart_marker_as_found` carries the
                  measured chain). The marker state is read out, not asserted;
      anything else -- run the installer ONCE more, which is the operation that COMPLETES the
                  update the user approved (unlike the preset case there is nothing to restore: the
                  scaffold rolls its own changes back when it REFUSES, and a run that was killed is
                  finished rather than undone), then read again and say what is there now.

    The repair run's own exit code decides nothing -- it is a note in the message. What stops the
    first run usually stops the second, and a reading taken only when the repair returned cleanly
    is the over-alarming half of this same defect (`presets` measured it; the branch is the same).

    RETURNS the refusal so the call sites read `raise _after_a_failed_install(...)`.
    """
    if _installed_state(root, kit_dir) == was:
        return StateError(
            "%s Nothing about the installation moved: %s -- and %s; %s. Remedy: deal with what the "
            "installer said above, then run this command again; report the gap if it is not yours "
            "to fix, and pass that limit on with it."
            % (reason, _describe(was), _restart_marker_as_found(root), UNREAD))
    repair_note = ""
    try:
        again = subprocess.run(command, cwd=root, capture_output=True,
                               timeout=presets.INSTALLER_TIMEOUT, **presets.CHILD_TEXT)
        if again.returncode != 0:
            repair_note = " (the completing run itself exited %d)" % again.returncode
    except (OSError, subprocess.SubprocessError) as exc:
        repair_note = " (the completing run could not be completed: %s)" % exc
    repaired = _installed_state(root, kit_dir)
    marker = ensure_restart_is_forced(root, kit)
    return StateError(
        "%s THE INSTALLATION HAD ALREADY MOVED: it was [%s], and after running the installer once "
        "more to complete it, it is [%s]%s. %s; %s. Remedy: report BOTH readings to the user and "
        "stop -- this session may not work under them either way; the backups of the run are under "
        ".claude/backups/, and a repair scaffold is a step for a shell outside this session."
        % (reason, _describe(was), _describe(repaired), repair_note, marker, UNREAD))


def apply(state: ProjectState) -> dict:
    """Install the staged kit over this project, on the user's approval -- FR-0006's command.

    ORDER, and every step of it is deliberate. Everything that can refuse without a side effect
    runs first (`_plan`: which kit, which direction, is the staging its own stamp, is a restart
    already pending), then the approval is re-derived and checked against the minted one, then the
    state to compare against is READ, then the interpreter for the installer is looked up -- a pure
    PATH lookup whose refusal says "nothing was changed", which is a sentence that has to be true
    when it is printed rather than restored afterwards (`presets.apply` carries the measurement
    that made this ordering a rule). Only then does anything move.

    WHAT THIS DOES NOT DO, and the caller prints it: it cannot make the new kit's registration take
    effect in the RUNNING session. That is why the marker is ensured on every path out of here that
    MEASURED a change -- and on no other: see `_restart_marker_as_found`.
    """
    with state.lock:
        plan = _plan(state)
        manifest = plan["manifest"]
        if approvals.live_line_approval(state, KIND, manifest) is None:
            raise StateError(
                "no user approval covers this kit update, so nothing was changed. What it would "
                "do: install the '%s' kit %s over the %s this project runs, replacing its hooks, "
                "kernel, roles, settings and constitution. Remedy: ask for it first -- `python "
                "scripts/harness.py request-approval %s` prints the question, and the USER approves "
                "by answering it; then run `python scripts/harness.py %s` again."
                % (plan["kit"], _shown(plan["to"]), _shown(plan["from"]), KIND, COMMAND))
        root, kit_dir = plan["root"], plan["kit_dir"]
        # BEFORE the installer: this is what every failure branch compares against, and after the
        # first copied file there is no way back to it.
        was = _installed_state(root, kit_dir)
        # ...AND THE INTERPRETER SEARCH BELONGS AHEAD OF IT TOO. One number for how long a child
        # may run (`presets.INSTALLER_TIMEOUT`), read through that module rather than copied.
        command = presets.installer_command(plan["kit"])
        try:
            result = subprocess.run(command, cwd=root, capture_output=True,
                                    timeout=presets.INSTALLER_TIMEOUT, **presets.CHILD_TEXT)
        except (OSError, subprocess.SubprocessError) as exc:
            raise _after_a_failed_install(
                root, plan["kit"], kit_dir, was, command,
                "the kit's installer did not complete (%s)." % exc) from None
        if result.returncode != 0:
            raise _after_a_failed_install(
                root, plan["kit"], kit_dir, was, command,
                "the kit's installer refused (exit %d). It said:\n%s\n"
                % (result.returncode,
                   ((result.stderr or "") + (result.stdout or "")).strip()[-1200:]))
        now = _installed_state(root, kit_dir)
        return {"kit": plan["kit"], "from": _shown(plan["from"]), "to": _shown(plan["to"]),
                "installed": _describe(now),
                "marker": ensure_restart_is_forced(root, plan["kit"]),
                "pending_templates": _pending_templates(root)}
